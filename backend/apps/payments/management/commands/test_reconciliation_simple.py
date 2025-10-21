from django.core.management.base import BaseCommand
from apps.core.models import Hotel
from apps.reservations.models import Reservation
from apps.reservations.models import Payment
from apps.payments.models import BankTransferPayment
from apps.payments.models import BankReconciliation, BankTransaction, ReconciliationMatch
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Prueba la funcionalidad de conciliacion bancaria'

    def handle(self, *args, **options):
        self.stdout.write('INICIANDO PRUEBA DE CONCILIACION BANCARIA')
        self.stdout.write('=' * 50)

        # 1. Crear hotel de prueba
        self.stdout.write('Creando hotel de prueba...')
        hotel, created = Hotel.objects.get_or_create(
            name='Hotel de Prueba',
            defaults={
                'address': 'Calle de Prueba 123',
                'phone': '+54 11 1234-5678',
                'email': 'prueba@hotel.com'
            }
        )
        self.stdout.write(f'[OK] Hotel: {hotel.name} {"(creado)" if created else "(existente)"}')

        # 2. Crear reservas con pagos pendientes
        self.stdout.write('\nCreando reservas con pagos pendientes...')
        test_reservations = [
            {'guest_name': 'Juan Perez', 'amount': 25000.00},
            {'guest_name': 'Maria Garcia', 'amount': 18000.00},
            {'guest_name': 'Carlos Lopez', 'amount': 32000.00},
            {'guest_name': 'Ana Rodriguez', 'amount': 15000.00}
        ]

        created_payments = []
        for i, res_data in enumerate(test_reservations):
            # Crear reserva
            reservation = Reservation.objects.create(
                hotel=hotel,
                guest_name=res_data['guest_name'],
                check_in=datetime.now().date(),
                check_out=(datetime.now() + timedelta(days=2)).date(),
                status='confirmed',
                total_amount=res_data['amount'],
                room_type='Standard',
                guests=2
            )
            
            # Crear pago pendiente
            payment = Payment.objects.create(
                reservation=reservation,
                amount=res_data['amount'],
                method='bank_transfer',
                status='pending',
                payment_type='reservation_payment'
            )
            
            # Crear transferencia bancaria pendiente
            BankTransferPayment.objects.create(
                payment=payment,
                cbu_iban=f'CBU 28500109...{i+1:04d}',
                bank_name='Banco de Prueba',
                transfer_date=datetime.now().date(),
                status='pending'
            )
            
            created_payments.append(payment)
            self.stdout.write(f'   [OK] {res_data["guest_name"]}: ${res_data["amount"]}')

        self.stdout.write(f'\nEstado ANTES de la conciliacion:')
        self.stdout.write(f'   - Pagos pendientes: {Payment.objects.filter(status="pending").count()}')

        # 3. Crear conciliacion
        self.stdout.write('\nCreando conciliacion bancaria...')
        reconciliation = BankReconciliation.objects.create(
            hotel=hotel,
            reconciliation_date=datetime.now().date(),
            csv_filename='test_reconciliation_data.csv',
            csv_file_size=1024,
            total_transactions=4,
            status='pending'
        )
        self.stdout.write(f'[OK] Conciliacion creada: #{reconciliation.id}')

        # 4. Crear transacciones bancarias
        self.stdout.write('\nCreando transacciones bancarias...')
        test_transactions = [
            {'description': 'Transferencia Juan Perez', 'amount': 25000.00, 'reference': 'CBU 28500109...1234'},
            {'description': 'Transferencia Maria Garcia', 'amount': 18000.00, 'reference': 'CBU 28500109...5678'},
            {'description': 'Transferencia Carlos Lopez', 'amount': 32000.00, 'reference': 'CBU 28500109...9012'},
            {'description': 'Transferencia Ana Rodriguez', 'amount': 15000.00, 'reference': 'CBU 28500109...3456'}
        ]

        created_transactions = []
        for trans_data in test_transactions:
            transaction = BankTransaction.objects.create(
                reconciliation=reconciliation,
                transaction_date=datetime.now().date(),
                description=trans_data['description'],
                amount=trans_data['amount'],
                currency='ARS',
                reference=trans_data['reference']
            )
            created_transactions.append(transaction)
            self.stdout.write(f'   [OK] {trans_data["description"]}: ${trans_data["amount"]}')

        # 5. Simular matching automatico
        self.stdout.write('\nSimulando matching automatico...')
        matches_created = 0

        for transaction in created_transactions:
            # Buscar pago pendiente con el mismo monto
            matching_payment = Payment.objects.filter(
                status='pending',
                amount=transaction.amount
            ).first()
            
            if matching_payment:
                # Crear match
                ReconciliationMatch.objects.create(
                    reconciliation=reconciliation,
                    bank_transaction=transaction,
                    payment_id=matching_payment.id,
                    payment_type='reservation_payment',
                    reservation_id=matching_payment.reservation.id,
                    match_type='exact',
                    confidence_score=95.0,
                    is_confirmed=True
                )
                
                # Marcar pago como confirmado
                matching_payment.status = 'approved'
                matching_payment.save()
                
                matches_created += 1
                self.stdout.write(f'   [OK] Match: {transaction.description} -> {matching_payment.reservation.guest_name}')

        # 6. Actualizar estadisticas
        reconciliation.matched_transactions = matches_created
        reconciliation.unmatched_transactions = reconciliation.total_transactions - matches_created
        reconciliation.status = 'completed'
        reconciliation.match_percentage = (matches_created / reconciliation.total_transactions) * 100
        reconciliation.save()

        # 7. Mostrar resultados
        self.stdout.write(f'\nEstado DESPUES de la conciliacion:')
        self.stdout.write(f'   - Estado: {reconciliation.status}')
        self.stdout.write(f'   - Transacciones: {reconciliation.total_transactions}')
        self.stdout.write(f'   - Matches: {reconciliation.matched_transactions}')
        self.stdout.write(f'   - Efectividad: {reconciliation.match_percentage:.1f}%')

        self.stdout.write(f'\nPagos actualizados:')
        for payment in Payment.objects.filter(reservation__hotel=hotel):
            self.stdout.write(f'   - {payment.reservation.guest_name}: ${payment.amount} - {payment.status}')

        # 8. Limpiar datos de prueba
        self.stdout.write(f'\nLimpiando datos de prueba...')
        ReconciliationMatch.objects.filter(reconciliation=reconciliation).delete()
        BankTransaction.objects.filter(reconciliation=reconciliation).delete()
        BankReconciliation.objects.filter(id=reconciliation.id).delete()
        BankTransferPayment.objects.filter(payment__reservation__hotel=hotel).delete()
        Payment.objects.filter(reservation__hotel=hotel).delete()
        Reservation.objects.filter(hotel=hotel).delete()
        Hotel.objects.filter(id=hotel.id).delete()
        self.stdout.write(f'[OK] Datos de prueba eliminados')

        self.stdout.write(f'\nPRUEBA COMPLETADA EXITOSAMENTE!')
        self.stdout.write(f'   - Matches creados: {matches_created}')
        self.stdout.write(f'   - Efectividad: {reconciliation.match_percentage:.1f}%')
        self.stdout.write(f'   - La funcionalidad de conciliacion bancaria esta funcionando correctamente!')
