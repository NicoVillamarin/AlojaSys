"""
Vistas para el módulo de Cobros - Historial unificado de pagos
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.reservations.models import Reservation, Payment
from apps.payments.models import PaymentIntent, BankTransferPayment, Refund
from apps.core.models import Hotel
from .serializers_collections import PaymentCollectionSerializer


class PaymentCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para el módulo de Cobros
    Proporciona un historial unificado de todos los pagos/cobros
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentCollectionSerializer
    
    def get_queryset(self):
        """Obtiene todos los pagos/cobros del hotel del usuario"""
        # TODO: Filtrar por hotel del usuario autenticado
        hotel_id = self.request.query_params.get('hotel_id')
        
        # Obtener todas las reservas del hotel
        reservations = Reservation.objects.filter(hotel_id=hotel_id) if hotel_id else Reservation.objects.all()
        reservation_ids = reservations.values_list('id', flat=True)
        
        # Combinar todos los tipos de pagos
        payments = []
        
        # 1. Pagos online (PaymentIntent) - Primero para poder detectar duplicados
        online_payments = PaymentIntent.objects.filter(
            reservation_id__in=reservation_ids
        ).select_related('reservation', 'reservation__hotel')
        
        # Crear un set de (reservation_id, amount, date) para PaymentIntents aprobados
        # para detectar duplicados en Payments manuales
        online_payment_keys = set()
        for payment in online_payments:
            if payment.status in ['approved', 'created']:  # Solo considerar aprobados o creados
                # Usar monto y fecha para identificar duplicados
                payment_date = payment.created_at.date()
                online_payment_keys.add((
                    payment.reservation_id,
                    float(payment.amount),
                    payment_date
                ))
        
        # 2. Pagos manuales (Payment) - Excluir los que tienen PaymentIntent asociado
        manual_payments = Payment.objects.filter(
            reservation_id__in=reservation_ids
        ).select_related('reservation', 'reservation__hotel')
        
        for payment in manual_payments:
            # Verificar si hay un PaymentIntent duplicado
            # Un Payment manual se considera duplicado si:
            # - Hay un PaymentIntent aprobado para la misma reserva
            # - Con el mismo monto (o muy similar, tolerancia de 0.01)
            # - En la misma fecha (o fecha cercana, tolerancia de 1 día)
            payment_date = payment.date
            payment_amount = float(payment.amount)
            
            is_duplicate = False
            for (res_id, amount, date) in online_payment_keys:
                if (res_id == payment.reservation_id and
                    abs(amount - payment_amount) < 0.01 and  # Mismo monto (tolerancia 0.01)
                    abs((date - payment_date).days) <= 1):  # Misma fecha o 1 día de diferencia
                    is_duplicate = True
                    break
            
            # Solo agregar si no es duplicado
            if not is_duplicate:
                payments.append({
                    'id': f"manual_{payment.id}",
                    'type': 'manual',
                    'reservation_id': payment.reservation_id,
                    'hotel_id': payment.reservation.hotel_id,
                    'hotel_name': payment.reservation.hotel.name,
                    'amount': payment.amount,
                    'method': payment.method,
                    'status': 'approved',  # Los pagos manuales se consideran aprobados
                    'date': payment.date,
                    'created_at': payment.created_at,
                    'description': f"Pago {payment.method}",
                    'reference': None,
                    'currency': 'ARS',
                    'guest_name': payment.reservation.guest_name,
                    'room_name': payment.reservation.room.name,
                    'check_in': payment.reservation.check_in,
                    'check_out': payment.reservation.check_out,
                })
        
        for payment in online_payments:
            # Mapear estados de PaymentIntent a estados estándar
            status_mapping = {
                'created': 'pending',
                'pending': 'pending', 
                'approved': 'approved',
                'rejected': 'rejected',
                'cancelled': 'cancelled'
            }
            mapped_status = status_mapping.get(payment.status, payment.status)
            
            payments.append({
                'id': f"online_{payment.id}",
                'type': 'online',
                'reservation_id': payment.reservation_id,
                'hotel_id': payment.reservation.hotel_id,
                'hotel_name': payment.reservation.hotel.name,
                'amount': payment.amount,
                'method': 'mercado_pago',
                'status': mapped_status,
                'date': payment.created_at.date(),
                'created_at': payment.created_at,
                'description': payment.description or "Pago online",
                'reference': payment.mp_payment_id,
                'currency': payment.currency,
                'guest_name': payment.reservation.guest_name,
                'room_name': payment.reservation.room.name,
                'check_in': payment.reservation.check_in,
                'check_out': payment.reservation.check_out,
            })
        
        # 3. Transferencias bancarias (BankTransferPayment)
        bank_transfers = BankTransferPayment.objects.filter(
            reservation_id__in=reservation_ids
        ).select_related('reservation', 'reservation__hotel')
        
        for transfer in bank_transfers:
            if transfer.status == 'confirmed':  # Solo transferencias confirmadas
                payments.append({
                    'id': f"transfer_{transfer.id}",
                    'type': 'bank_transfer',
                    'reservation_id': transfer.reservation_id,
                    'hotel_id': transfer.reservation.hotel_id,
                    'hotel_name': transfer.reservation.hotel.name,
                    'amount': transfer.amount,
                    'method': 'bank_transfer',
                    'status': 'approved',
                    'date': transfer.transfer_date,
                    'created_at': transfer.created_at,
                    'description': f"Transferencia bancaria - {transfer.bank_name or 'Banco'}" if transfer.bank_name else "Transferencia bancaria",
                    'reference': transfer.payment_reference,
                    'currency': 'ARS',
                    'guest_name': transfer.reservation.guest_name,
                    'room_name': transfer.reservation.room.name,
                    'check_in': transfer.reservation.check_in,
                    'check_out': transfer.reservation.check_out,
                    'cbu_iban': transfer.cbu_iban,
                    'bank_name': transfer.bank_name,
                })
        
        # 4. Reservas pendientes sin pagos (para mostrar en el historial de cobros)
        pending_reservations = Reservation.objects.filter(
            id__in=reservation_ids,
            status='pending'  # Solo reservas pendientes
        ).select_related('hotel', 'room')
        
        for reservation in pending_reservations:
            payments.append({
                'id': f"pending_{reservation.id}",
                'type': 'pending',
                'reservation_id': reservation.id,
                'hotel_id': reservation.hotel_id,
                'hotel_name': reservation.hotel.name,
                'amount': reservation.total_price or 0,
                'method': 'pending',
                'status': 'pending',
                'date': reservation.created_at.date(),
                'created_at': reservation.created_at,
                'description': f"Reserva {reservation.id} - {reservation.room.name}",
                'reference': None,
                'currency': 'ARS',
                'guest_name': reservation.guest_name,
                'room_name': reservation.room.name,
                'check_in': reservation.check_in,
                'check_out': reservation.check_out,
                'is_pending_payment': True,  # Flag para identificar reservas pendientes
            })
        
        # Ordenar por fecha (más reciente primero)
        payments.sort(key=lambda x: x['created_at'], reverse=True)
        
        return payments
    
    def list(self, request, *args, **kwargs):
        """Lista todos los cobros con filtros"""
        payments = self.get_queryset()
        
        # Aplicar filtros
        payments = self._apply_filters(payments, request.query_params)
        
        # Paginación
        page = self.paginate_queryset(payments)
        if page is not None:
            return self.get_paginated_response(page)
        
        return Response(payments)
    
    def _apply_filters(self, payments, query_params):
        """Aplica filtros a la lista de pagos"""
        # Filtro por tipo
        payment_type = query_params.get('type')
        if payment_type:
            payments = [p for p in payments if p['type'] == payment_type]
        
        # Filtro por método
        method = query_params.get('method')
        if method:
            payments = [p for p in payments if p['method'] == method]
        
        # Filtro por estado
        status_filter = query_params.get('status')
        if status_filter:
            payments = [p for p in payments if p['status'] == status_filter]
        
        # Filtro por fecha desde
        date_from = query_params.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                payments = [p for p in payments if p['date'] >= date_from]
            except ValueError:
                pass
        
        # Filtro por fecha hasta
        date_to = query_params.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                payments = [p for p in payments if p['date'] <= date_to]
            except ValueError:
                pass
        
        # Filtro por monto mínimo
        min_amount = query_params.get('min_amount')
        if min_amount:
            try:
                min_amount = Decimal(min_amount)
                payments = [p for p in payments if p['amount'] >= min_amount]
            except (ValueError, TypeError):
                pass
        
        # Filtro por monto máximo
        max_amount = query_params.get('max_amount')
        if max_amount:
            try:
                max_amount = Decimal(max_amount)
                payments = [p for p in payments if p['amount'] <= max_amount]
            except (ValueError, TypeError):
                pass
        
        # Filtro por búsqueda general
        search = query_params.get('search')
        if search:
            search_lower = search.lower()
            payments = [p for p in payments if (
                search_lower in str(p['reservation_id']).lower() or
                search_lower in p['guest_name'].lower() or
                search_lower in p['room_name'].lower() or
                search_lower in p['description'].lower() or
                (p.get('reference') and search_lower in str(p['reference']).lower())
            )]
        
        return payments
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtiene estadísticas de cobros"""
        payments = self.get_queryset()
        
        # Estadísticas por tipo
        type_stats = {}
        for payment in payments:
            payment_type = payment['type']
            if payment_type not in type_stats:
                type_stats[payment_type] = {'count': 0, 'total': Decimal('0')}
            type_stats[payment_type]['count'] += 1
            type_stats[payment_type]['total'] += payment['amount']
        
        # Estadísticas por método
        method_stats = {}
        for payment in payments:
            method = payment['method']
            if method not in method_stats:
                method_stats[method] = {'count': 0, 'total': Decimal('0')}
            method_stats[method]['count'] += 1
            method_stats[method]['total'] += payment['amount']
        
        # Estadísticas por mes
        monthly_stats = {}
        for payment in payments:
            month_key = payment['date'].strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'count': 0, 'total': Decimal('0')}
            monthly_stats[month_key]['count'] += 1
            monthly_stats[month_key]['total'] += payment['amount']
        
        # Totales generales
        total_payments = len(payments)
        total_amount = sum(payment['amount'] for payment in payments)
        avg_amount = total_amount / total_payments if total_payments > 0 else Decimal('0')
        
        return Response({
            'summary': {
                'total_payments': total_payments,
                'total_amount': float(total_amount),
                'average_amount': float(avg_amount),
            },
            'by_type': type_stats,
            'by_method': method_stats,
            'by_month': monthly_stats,
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Exporta los cobros en formato CSV"""
        payments = self.get_queryset()
        payments = self._apply_filters(payments, request.query_params)
        
        # Crear CSV
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cobros.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Tipo', 'Reserva', 'Hotel', 'Huésped', 'Habitación',
            'Check-in', 'Check-out', 'Monto', 'Método', 'Estado', 'Fecha',
            'Descripción', 'Referencia', 'CBU/IBAN', 'Banco'
        ])
        
        for payment in payments:
            writer.writerow([
                payment['id'],
                payment['type'],
                payment['reservation_id'],
                payment['hotel_name'],
                payment['guest_name'],
                payment['room_name'],
                payment['check_in'],
                payment['check_out'],
                payment['amount'],
                payment['method'],
                payment['status'],
                payment['date'],
                payment['description'],
                payment.get('reference', ''),
                payment.get('cbu_iban', ''),
                payment.get('bank_name', ''),
            ])
        
        return response
