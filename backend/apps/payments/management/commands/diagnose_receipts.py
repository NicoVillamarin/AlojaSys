from django.core.management.base import BaseCommand
from apps.reservations.models import Payment
from apps.payments.models import Refund


class Command(BaseCommand):
    help = 'Diagnostica el estado de los números de comprobante'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DIAGNÓSTICO DE COMPROBANTES')
        self.stdout.write('='*50)
        
        # Estadísticas de pagos
        total_payments = Payment.objects.count()
        payments_with_receipt_number = Payment.objects.filter(receipt_number__isnull=False).count()
        payments_without_receipt_number = Payment.objects.filter(receipt_number__isnull=True).count()
        payments_empty_receipt_number = Payment.objects.filter(receipt_number='').count()
        
        self.stdout.write(f'\n📄 PAGOS (Señas):')
        self.stdout.write(f'   - Total de pagos: {total_payments}')
        self.stdout.write(f'   - Con número de comprobante: {payments_with_receipt_number}')
        self.stdout.write(f'   - Sin número de comprobante (NULL): {payments_without_receipt_number}')
        self.stdout.write(f'   - Con número vacío (""): {payments_empty_receipt_number}')
        
        # Mostrar algunos ejemplos
        if total_payments > 0:
            self.stdout.write(f'\n📋 EJEMPLOS DE PAGOS:')
            sample_payments = Payment.objects.all()[:5]
            for payment in sample_payments:
                receipt_number = payment.receipt_number or 'NULL'
                self.stdout.write(f'   - Pago {payment.id}: receipt_number = "{receipt_number}"')
        
        # Estadísticas de devoluciones
        total_refunds = Refund.objects.count()
        refunds_with_receipt_number = Refund.objects.filter(receipt_number__isnull=False).count()
        refunds_without_receipt_number = Refund.objects.filter(receipt_number__isnull=True).count()
        refunds_empty_receipt_number = Refund.objects.filter(receipt_number='').count()
        
        self.stdout.write(f'\n🔄 DEVOLUCIONES:')
        self.stdout.write(f'   - Total de devoluciones: {total_refunds}')
        self.stdout.write(f'   - Con número de comprobante: {refunds_with_receipt_number}')
        self.stdout.write(f'   - Sin número de comprobante (NULL): {refunds_without_receipt_number}')
        self.stdout.write(f'   - Con número vacío (""): {refunds_empty_receipt_number}')
        
        # Mostrar algunos ejemplos
        if total_refunds > 0:
            self.stdout.write(f'\n📋 EJEMPLOS DE DEVOLUCIONES:')
            sample_refunds = Refund.objects.all()[:5]
            for refund in sample_refunds:
                receipt_number = refund.receipt_number or 'NULL'
                self.stdout.write(f'   - Devolución {refund.id}: receipt_number = "{receipt_number}"')
        
        self.stdout.write('\n' + '='*50)






