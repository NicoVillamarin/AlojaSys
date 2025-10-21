"""
Servicio de Conciliación Bancaria
Maneja el procesamiento automático de conciliaciones bancarias
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import List, Dict, Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.models import Hotel
from apps.reservations.models import Payment, Reservation
from ..models import (
    BankReconciliation, BankTransaction, ReconciliationMatch, BankReconciliationLog,
    BankReconciliationConfig, ReconciliationStatus, MatchType, ReconciliationEventType
)
from apps.payments.models import PaymentIntent, BankTransferPayment


class BankReconciliationService:
    """Servicio principal para conciliación bancaria"""
    
    def __init__(self, hotel: Hotel):
        self.hotel = hotel
        self.config = self._get_or_create_config()
    
    def _get_or_create_config(self) -> BankReconciliationConfig:
        """Obtiene o crea la configuración de conciliación para el hotel"""
        config, created = BankReconciliationConfig.objects.get_or_create(
            hotel=self.hotel,
            defaults={
                'csv_columns': ['fecha', 'descripcion', 'importe', 'moneda', 'referencia'],
                'notification_emails': []
            }
        )
        return config
    
    def create_reconciliation(self, csv_file, reconciliation_date: date, created_by=None) -> BankReconciliation:
        """Crea una nueva conciliación bancaria"""
        try:
            # Validar y parsear CSV
            transactions_data = self._parse_csv(csv_file)
            
            # Crear conciliación
            reconciliation = BankReconciliation.objects.create(
                hotel=self.hotel,
                reconciliation_date=reconciliation_date,
                csv_file=csv_file,
                csv_filename=csv_file.name,
                csv_file_size=csv_file.size,
                total_transactions=len(transactions_data),
                created_by=created_by
            )
            
            # Crear transacciones bancarias
            self._create_bank_transactions(reconciliation, transactions_data)
            
            # Log del evento
            self._log_event(
                reconciliation,
                ReconciliationEventType.CSV_UPLOADED,
                f"CSV subido con {len(transactions_data)} transacciones",
                created_by=created_by,
                csv_filename=csv_file.name
            )
            
            return reconciliation
            
        except Exception as e:
            # Log del error
            if 'reconciliation' in locals():
                self._log_event(
                    reconciliation,
                    ReconciliationEventType.ERROR,
                    f"Error al crear conciliación: {str(e)}",
                    created_by=created_by
                )
            raise ValidationError(f"Error al procesar CSV: {str(e)}")
    
    def create_reconciliation_from_base64(self, csv_file_base64: str, csv_filename: str, 
                                        reconciliation_date: date, created_by=None) -> BankReconciliation:
        """Crea una nueva conciliación bancaria desde archivo base64"""
        try:
            import base64
            from django.core.files.base import ContentFile
            
            # Decodificar base64
            if ',' in csv_file_base64:
                header, data = csv_file_base64.split(',', 1)
            else:
                data = csv_file_base64
            
            csv_content = base64.b64decode(data)
            
            # Crear archivo temporal sin name para evitar conflicto
            csv_file = ContentFile(csv_content)
            
            # Validar y parsear CSV
            transactions_data = self._parse_csv_from_content(csv_content.decode(self.config.csv_encoding))
            
            # Crear conciliación
            reconciliation = BankReconciliation.objects.create(
                hotel=self.hotel,
                reconciliation_date=reconciliation_date,
                csv_file=csv_file,
                csv_filename=csv_filename,
                csv_file_size=len(csv_content),
                total_transactions=len(transactions_data),
                created_by=created_by
            )
            
            # Crear transacciones bancarias
            self._create_bank_transactions(reconciliation, transactions_data)
            
            # Log del evento
            self._log_event(
                reconciliation,
                ReconciliationEventType.CSV_UPLOADED,
                f"CSV subido con {len(transactions_data)} transacciones",
                created_by=created_by,
                csv_filename=csv_filename
            )
            
            return reconciliation
            
        except Exception as e:
            # Log del error
            if 'reconciliation' in locals():
                self._log_event(
                    reconciliation,
                    ReconciliationEventType.ERROR,
                    f"Error al crear conciliación: {str(e)}",
                    created_by=created_by
                )
            raise ValidationError(f"Error al procesar CSV: {str(e)}")
    
    def process_reconciliation(self, reconciliation_id: int) -> BankReconciliation:
        """Procesa una conciliación bancaria automáticamente"""
        reconciliation = BankReconciliation.objects.get(id=reconciliation_id)
        
        try:
            # Marcar como procesando
            reconciliation.status = ReconciliationStatus.PROCESSING
            reconciliation.processing_started_at = timezone.now()
            reconciliation.save()
            
            # Log del inicio
            self._log_event(
                reconciliation,
                ReconciliationEventType.PROCESSING_STARTED,
                "Iniciando procesamiento de conciliación",
                csv_filename=reconciliation.csv_filename
            )
            
            # Obtener transacciones bancarias
            bank_transactions = reconciliation.transactions.all()
            
            # Obtener pagos pendientes del hotel
            pending_payments = self._get_pending_payments()
            
            # Procesar cada transacción
            matched_count = 0
            pending_review_count = 0
            unmatched_count = 0
            error_count = 0
            
            for bank_transaction in bank_transactions:
                try:
                    # Detectar reversiones
                    if bank_transaction.amount < 0:
                        self._handle_reversal(bank_transaction, reconciliation)
                        continue
                    
                    # Buscar matches
                    matches = self._find_matches(bank_transaction, pending_payments)
                    
                    if matches:
                        best_match = max(matches, key=lambda x: x['confidence_score'])
                        
                        if best_match['confidence_score'] >= self.config.auto_confirm_threshold:
                            # Auto-confirmar
                            self._confirm_match(bank_transaction, best_match, reconciliation)
                            matched_count += 1
                            
                        elif best_match['confidence_score'] >= self.config.pending_review_threshold:
                            # Marcar para revisión manual
                            self._create_pending_match(bank_transaction, best_match, reconciliation)
                            pending_review_count += 1
                            
                        else:
                            # Sin match suficiente
                            unmatched_count += 1
                            self._log_event(
                                reconciliation,
                                ReconciliationEventType.UNMATCHED,
                                f"Transacción sin match suficiente: {bank_transaction.amount}",
                                bank_transaction_id=bank_transaction.id,
                                details={'confidence': best_match['confidence_score']}
                            )
                    else:
                        # Sin matches encontrados
                        unmatched_count += 1
                        self._log_event(
                            reconciliation,
                            ReconciliationEventType.UNMATCHED,
                            f"Transacción sin matches: {bank_transaction.amount}",
                            bank_transaction_id=bank_transaction.id
                        )
                        
                except Exception as e:
                    error_count += 1
                    self._log_event(
                        reconciliation,
                        ReconciliationEventType.ERROR,
                        f"Error procesando transacción {bank_transaction.id}: {str(e)}",
                        bank_transaction_id=bank_transaction.id
                    )
            
            # Actualizar estadísticas
            reconciliation.matched_transactions = matched_count
            reconciliation.pending_review_transactions = pending_review_count
            reconciliation.unmatched_transactions = unmatched_count
            reconciliation.error_transactions = error_count
            reconciliation.status = ReconciliationStatus.COMPLETED
            reconciliation.processing_completed_at = timezone.now()
            reconciliation.save()
            
            # Log de finalización
            self._log_event(
                reconciliation,
                ReconciliationEventType.PROCESSING_COMPLETED,
                f"Procesamiento completado: {matched_count} matches, {pending_review_count} pendientes, {unmatched_count} sin match",
                details={
                    'matched': matched_count,
                    'pending_review': pending_review_count,
                    'unmatched': unmatched_count,
                    'errors': error_count
                }
            )
            
            # Enviar notificaciones si es necesario
            self._send_notifications(reconciliation)
            
            return reconciliation
            
        except Exception as e:
            reconciliation.status = ReconciliationStatus.FAILED
            reconciliation.processing_notes = str(e)
            reconciliation.save()
            
            self._log_event(
                reconciliation,
                ReconciliationEventType.ERROR,
                f"Error fatal en procesamiento: {str(e)}"
            )
            raise
    
    def _parse_csv(self, csv_file) -> List[Dict]:
        """Parsea el archivo CSV bancario"""
        try:
            csv_file.seek(0)
            content = csv_file.read().decode(self.config.csv_encoding)
            csv_file.seek(0)
            
            return self._parse_csv_from_content(content)
            
        except Exception as e:
            raise ValidationError(f"Error al parsear CSV: {str(e)}")
    
    def _parse_csv_from_content(self, content: str) -> List[Dict]:
        """Parsea el contenido CSV desde string"""
        try:
            reader = csv.DictReader(io.StringIO(content), delimiter=self.config.csv_separator)
            transactions = []
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Validar columnas requeridas
                    required_columns = self.config.csv_columns
                    for col in required_columns:
                        if col not in row:
                            raise ValidationError(f"Columna '{col}' no encontrada en fila {row_num}")
                    
                    # Parsear datos
                    transaction_date = self._parse_date(row['fecha'])
                    amount = self._parse_amount(row['importe'])
                    currency = row.get('moneda', 'ARS')
                    
                    # Convertir moneda si es necesario
                    if currency != self.config.default_currency:
                        amount = self._convert_currency(amount, currency, transaction_date)
                    
                    transactions.append({
                        'transaction_date': transaction_date,
                        'description': row['descripcion'].strip(),
                        'amount': amount,
                        'currency': self.config.default_currency,
                        'reference': row.get('referencia', '').strip()
                    })
                    
                except Exception as e:
                    raise ValidationError(f"Error en fila {row_num}: {str(e)}")
            
            return transactions
            
        except Exception as e:
            raise ValidationError(f"Error al parsear CSV: {str(e)}")
    
    def _parse_date(self, date_str: str) -> date:
        """Parsea una fecha desde string"""
        try:
            # Intentar diferentes formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return timezone.datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha no reconocido: {date_str}")
        except Exception as e:
            raise ValidationError(f"Error parseando fecha '{date_str}': {str(e)}")
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parsea un monto desde string"""
        try:
            # Limpiar string y convertir
            cleaned = amount_str.strip().replace(',', '').replace('$', '')
            return Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception as e:
            raise ValidationError(f"Error parseando monto '{amount_str}': {str(e)}")
    
    def _convert_currency(self, amount: Decimal, from_currency: str, transaction_date: date) -> Decimal:
        """Convierte moneda usando el tipo de cambio configurado"""
        if from_currency == 'USD' and self.config.currency_rate:
            # Verificar si el tipo de cambio es reciente
            if (self.config.currency_rate_date and 
                abs((transaction_date - self.config.currency_rate_date).days) <= 7):
                return amount * self.config.currency_rate
            else:
                # TODO: Obtener tipo de cambio actual de API externa
                pass
        
        return amount
    
    def _create_bank_transactions(self, reconciliation: BankReconciliation, transactions_data: List[Dict]):
        """Crea las transacciones bancarias en la base de datos"""
        for data in transactions_data:
            BankTransaction.objects.create(
                reconciliation=reconciliation,
                **data
            )
    
    def _get_pending_payments(self) -> Dict[str, List]:
        """Obtiene todos los pagos pendientes del hotel"""
        # Obtener reservas del hotel
        reservations = Reservation.objects.filter(hotel=self.hotel)
        reservation_ids = reservations.values_list('id', flat=True)
        
        # Pagos manuales pendientes (Payment)
        manual_payments = Payment.objects.filter(
            reservation_id__in=reservation_ids
        ).select_related('reservation')
        
        # PaymentIntents pendientes
        payment_intents = PaymentIntent.objects.filter(
            hotel=self.hotel,
            status__in=['pending', 'created']
        ).select_related('reservation')
        
        # BankTransferPayments pendientes
        bank_transfers = BankTransferPayment.objects.filter(
            hotel=self.hotel,
            status__in=['uploaded', 'pending_review']
        ).select_related('reservation')
        
        return {
            'manual_payments': list(manual_payments),
            'payment_intents': list(payment_intents),
            'bank_transfers': list(bank_transfers)
        }
    
    def _find_matches(self, bank_transaction: BankTransaction, pending_payments: Dict[str, List]) -> List[Dict]:
        """Encuentra matches para una transacción bancaria"""
        matches = []
        
        # Buscar en pagos manuales
        for payment in pending_payments['manual_payments']:
            match = self._calculate_match(bank_transaction, payment, 'payment')
            if match:
                matches.append(match)
        
        # Buscar en PaymentIntents
        for payment_intent in pending_payments['payment_intents']:
            match = self._calculate_match(bank_transaction, payment_intent, 'payment_intent')
            if match:
                matches.append(match)
        
        # Buscar en BankTransferPayments
        for bank_transfer in pending_payments['bank_transfers']:
            match = self._calculate_match(bank_transaction, bank_transfer, 'bank_transfer')
            if match:
                matches.append(match)
        
        return matches
    
    def _calculate_match(self, bank_transaction: BankTransaction, payment, payment_type: str) -> Optional[Dict]:
        """Calcula el match entre una transacción bancaria y un pago"""
        # Obtener datos del pago
        if payment_type == 'payment':
            payment_amount = payment.amount
            payment_date = payment.date
            payment_id = payment.id
            reservation_id = payment.reservation_id
        elif payment_type == 'payment_intent':
            payment_amount = payment.amount
            payment_date = payment.created_at.date()
            payment_id = payment.id
            reservation_id = payment.reservation_id
        elif payment_type == 'bank_transfer':
            payment_amount = payment.amount
            payment_date = payment.transfer_date
            payment_id = payment.id
            reservation_id = payment.reservation_id
        else:
            return None
        
        # Calcular diferencias
        amount_diff = abs(bank_transaction.amount - payment_amount)
        date_diff = abs((bank_transaction.transaction_date - payment_date).days)
        
        # Verificar tolerancias y calcular confianza
        confidence = self._calculate_confidence(amount_diff, date_diff, payment_amount)
        
        if confidence > 0:
            return {
                'payment_id': payment_id,
                'payment_type': payment_type,
                'reservation_id': reservation_id,
                'confidence_score': confidence,
                'amount_difference': amount_diff,
                'date_difference_days': date_diff,
                'match_type': self._get_match_type(amount_diff, date_diff, payment_amount)
            }
        
        return None
    
    def _calculate_confidence(self, amount_diff: Decimal, date_diff: int, payment_amount: Decimal) -> float:
        """Calcula la confianza del match basado en tolerancias"""
        # Match exacto
        if (amount_diff == 0 and date_diff <= self.config.exact_match_date_tolerance):
            return 100.0
        
        # Match fuzzy
        amount_tolerance = payment_amount * (self.config.fuzzy_match_amount_tolerance_percent / 100)
        if (amount_diff <= amount_tolerance and date_diff <= self.config.fuzzy_match_date_tolerance):
            # Calcular confianza basada en proximidad
            amount_score = max(0, 100 - (amount_diff / amount_tolerance) * 20)
            date_score = max(0, 100 - (date_diff / self.config.fuzzy_match_date_tolerance) * 20)
            return (amount_score + date_score) / 2
        
        # Match parcial
        amount_tolerance = payment_amount * (self.config.partial_match_amount_tolerance_percent / 100)
        if (amount_diff <= amount_tolerance and date_diff <= self.config.partial_match_date_tolerance):
            # Calcular confianza más baja
            amount_score = max(0, 60 - (amount_diff / amount_tolerance) * 30)
            date_score = max(0, 60 - (date_diff / self.config.partial_match_date_tolerance) * 30)
            return (amount_score + date_score) / 2
        
        return 0.0
    
    def _get_match_type(self, amount_diff: Decimal, date_diff: int, payment_amount: Decimal) -> str:
        """Determina el tipo de match"""
        if amount_diff == 0 and date_diff <= self.config.exact_match_date_tolerance:
            return MatchType.EXACT
        
        amount_tolerance = payment_amount * (self.config.fuzzy_match_amount_tolerance_percent / 100)
        if amount_diff <= amount_tolerance and date_diff <= self.config.fuzzy_match_date_tolerance:
            return MatchType.FUZZY
        
        return MatchType.PARTIAL
    
    def _confirm_match(self, bank_transaction: BankTransaction, match: Dict, reconciliation: BankReconciliation):
        """Confirma un match automáticamente"""
        with transaction.atomic():
            # Crear el match
            reconciliation_match = ReconciliationMatch.objects.create(
                reconciliation=reconciliation,
                bank_transaction=bank_transaction,
                payment_id=match['payment_id'],
                payment_type=match['payment_type'],
                reservation_id=match['reservation_id'],
                match_type=match['match_type'],
                confidence_score=match['confidence_score'],
                amount_difference=match['amount_difference'],
                date_difference_days=match['date_difference_days'],
                is_confirmed=True
            )
            
            # Actualizar transacción bancaria
            bank_transaction.is_matched = True
            bank_transaction.match_confidence = match['confidence_score']
            bank_transaction.match_type = match['match_type']
            bank_transaction.matched_payment_id = match['payment_id']
            bank_transaction.matched_payment_type = match['payment_type']
            bank_transaction.matched_reservation_id = match['reservation_id']
            bank_transaction.amount_difference = match['amount_difference']
            bank_transaction.date_difference_days = match['date_difference_days']
            bank_transaction.save()
            
            # Confirmar el pago si es necesario
            self._confirm_payment(match['payment_id'], match['payment_type'])
            
            # Log del evento
            self._log_event(
                reconciliation,
                ReconciliationEventType.AUTO_MATCHED,
                f"Match automático confirmado: {bank_transaction.amount}",
                bank_transaction_id=bank_transaction.id,
                payment_id=match['payment_id'],
                payment_type=match['payment_type'],
                reservation_id=match['reservation_id'],
                confidence_score=match['confidence_score']
            )
    
    def _create_pending_match(self, bank_transaction: BankTransaction, match: Dict, reconciliation: BankReconciliation):
        """Crea un match pendiente de revisión manual"""
        with transaction.atomic():
            # Crear el match
            reconciliation_match = ReconciliationMatch.objects.create(
                reconciliation=reconciliation,
                bank_transaction=bank_transaction,
                payment_id=match['payment_id'],
                payment_type=match['payment_type'],
                reservation_id=match['reservation_id'],
                match_type=match['match_type'],
                confidence_score=match['confidence_score'],
                amount_difference=match['amount_difference'],
                date_difference_days=match['date_difference_days'],
                is_confirmed=False
            )
            
            # Actualizar transacción bancaria
            bank_transaction.match_confidence = match['confidence_score']
            bank_transaction.match_type = match['match_type']
            bank_transaction.matched_payment_id = match['payment_id']
            bank_transaction.matched_payment_type = match['payment_type']
            bank_transaction.matched_reservation_id = match['reservation_id']
            bank_transaction.amount_difference = match['amount_difference']
            bank_transaction.date_difference_days = match['date_difference_days']
            bank_transaction.save()
            
            # Log del evento
            self._log_event(
                reconciliation,
                ReconciliationEventType.PENDING_REVIEW,
                f"Match pendiente de revisión: {bank_transaction.amount}",
                bank_transaction_id=bank_transaction.id,
                payment_id=match['payment_id'],
                payment_type=match['payment_type'],
                reservation_id=match['reservation_id'],
                confidence_score=match['confidence_score']
            )
    
    def _confirm_payment(self, payment_id: int, payment_type: str):
        """Confirma un pago según su tipo"""
        if payment_type == 'payment_intent':
            payment_intent = PaymentIntent.objects.get(id=payment_id)
            payment_intent.status = 'approved'
            payment_intent.save()
            
        elif payment_type == 'bank_transfer':
            bank_transfer = BankTransferPayment.objects.get(id=payment_id)
            bank_transfer.mark_as_confirmed()
    
    def _handle_reversal(self, bank_transaction: BankTransaction, reconciliation: BankReconciliation):
        """Maneja una reversión (monto negativo)"""
        bank_transaction.is_reversal = True
        bank_transaction.save()
        
        # TODO: Crear Refund asociado
        # Por ahora solo logueamos el evento
        
        self._log_event(
            reconciliation,
            ReconciliationEventType.REVERSAL_DETECTED,
            f"Reversión detectada: {bank_transaction.amount}",
            bank_transaction_id=bank_transaction.id
        )
    
    def _send_notifications(self, reconciliation: BankReconciliation):
        """Envía notificaciones si es necesario"""
        if not self.config.email_notifications:
            return
        
        # Verificar si hay muchos pagos sin conciliar
        unmatched_percentage = (reconciliation.unmatched_transactions / reconciliation.total_transactions) * 100
        
        if unmatched_percentage > self.config.notification_threshold_percent:
            # TODO: Enviar email de notificación
            pass
    
    def _log_event(self, reconciliation: BankReconciliation, event_type: ReconciliationEventType, 
                   description: str, created_by=None, **kwargs):
        """Crea un log de auditoría"""
        log_kwargs = dict(kwargs)
        if 'csv_filename' not in log_kwargs:
            log_kwargs['csv_filename'] = reconciliation.csv_filename
        BankReconciliationLog.objects.create(
            reconciliation=reconciliation,
            event_type=event_type,
            event_description=description,
            created_by=created_by,
            **log_kwargs
        )
