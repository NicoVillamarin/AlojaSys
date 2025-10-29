from django.core.management.base import BaseCommand
from apps.payments.models import ReceiptNumberSequence
from apps.reservations.models import Payment
from apps.payments.models import Refund


class Command(BaseCommand):
    help = 'Genera números de comprobante serios para comprobantes existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar los cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN - No se realizarán cambios'))
        
        self.stdout.write('🔄 Iniciando generación de números de comprobante...')
        
        # Procesar pagos (señas)
        payments_without_receipt_number = Payment.objects.filter(
            receipt_number__isnull=True
        ).order_by('created_at')
        
        self.stdout.write(f"📄 Encontrados {payments_without_receipt_number.count()} pagos sin número de comprobante")
        
        for payment in payments_without_receipt_number:
            try:
                # Determinar el tipo de comprobante según si es seña o pago total
                if payment.is_deposit:
                    receipt_type = ReceiptNumberSequence.ReceiptType.DEPOSIT  # "S"
                else:
                    receipt_type = ReceiptNumberSequence.ReceiptType.PAYMENT  # "P"
                
                # Generar número de comprobante para pago
                receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=payment.reservation.hotel,
                    receipt_type=receipt_type
                )
                
                if not dry_run:
                    payment.receipt_number = receipt_number
                    payment.save(update_fields=['receipt_number'])
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Pago {payment.id} ({'Seña' if payment.is_deposit else 'Pago'}) -> {receipt_number}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error con pago {payment.id}: {e}")
                )
        
        # Procesar devoluciones
        refunds_without_receipt_number = Refund.objects.filter(
            receipt_number__isnull=True
        ).order_by('created_at')
        
        self.stdout.write(f"🔄 Encontrados {refunds_without_receipt_number.count()} devoluciones sin número de comprobante")
        
        for refund in refunds_without_receipt_number:
            try:
                # Generar número de comprobante para devolución
                receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=refund.reservation.hotel,
                    receipt_type=ReceiptNumberSequence.ReceiptType.REFUND
                )
                
                if not dry_run:
                    refund.receipt_number = receipt_number
                    refund.save(update_fields=['receipt_number'])
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Devolución {refund.id} -> {receipt_number}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error con devolución {refund.id}: {e}")
                )
        
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Generación de números de comprobante completada!'))
        
        # Mostrar estadísticas
        total_payments = Payment.objects.filter(receipt_number__isnull=False).count()
        total_refunds = Refund.objects.filter(receipt_number__isnull=False).count()
        
        self.stdout.write(f"📊 Estadísticas finales:")
        self.stdout.write(f"   - Pagos con número de comprobante: {total_payments}")
        self.stdout.write(f"   - Devoluciones con número de comprobante: {total_refunds}")

