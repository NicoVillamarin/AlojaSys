from django.core.management.base import BaseCommand
from apps.reservations.models import Payment
from apps.payments.models import Refund
from apps.payments.tasks import generate_payment_receipt_pdf


class Command(BaseCommand):
    help = 'Regenera todos los PDFs de comprobantes para incluir los números serios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar los cambios',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limitar el número de comprobantes a procesar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN - No se regenerarán PDFs'))
        
        self.stdout.write('🔄 Regenerando PDFs de comprobantes...')
        
        # Procesar pagos
        payments = Payment.objects.filter(receipt_number__isnull=False)
        if limit:
            payments = payments[:limit]
        
        self.stdout.write(f"📄 Regenerando {payments.count()} PDFs de pagos...")
        
        for payment in payments:
            try:
                if not dry_run:
                    # Regenerar PDF del pago
                    generate_payment_receipt_pdf.delay(payment.id, 'payment')
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ PDF regenerado para pago {payment.id} ({payment.receipt_number})")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error regenerando PDF para pago {payment.id}: {e}")
                )
        
        # Procesar devoluciones
        refunds = Refund.objects.filter(receipt_number__isnull=False)
        if limit:
            refunds = refunds[:limit]
        
        self.stdout.write(f"🔄 Regenerando {refunds.count()} PDFs de devoluciones...")
        
        for refund in refunds:
            try:
                if not dry_run:
                    # Regenerar PDF de la devolución
                    generate_payment_receipt_pdf.delay(refund.id, 'refund')
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ PDF regenerado para devolución {refund.id} ({refund.receipt_number})")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error regenerando PDF para devolución {refund.id}: {e}")
                )
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n🎉 ¡Regeneración de PDFs completada!'))
            self.stdout.write('Los PDFs se están generando en segundo plano. Espera unos minutos.')
        else:
            self.stdout.write(self.style.WARNING('\n💡 Ejecuta sin --dry-run para regenerar los PDFs'))















