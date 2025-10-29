from django.core.management.base import BaseCommand
from apps.payments.models import ReceiptNumberSequence
from apps.reservations.models import Payment


class Command(BaseCommand):
    help = 'Fuerza la actualización de números de comprobante para TODOS los pagos'

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
        
        self.stdout.write('🔄 FORZANDO actualización de números de comprobante...')
        
        # Obtener TODOS los pagos, sin importar si ya tienen receipt_number
        payments = Payment.objects.all().order_by('created_at')
        
        self.stdout.write(f"📄 Procesando {payments.count()} pagos...")
        
        processed = 0
        errors = 0
        
        for payment in payments:
            try:
                # Determinar el tipo de comprobante según si es seña o pago total
                if payment.is_deposit:
                    receipt_type = ReceiptNumberSequence.ReceiptType.DEPOSIT  # "S"
                else:
                    receipt_type = ReceiptNumberSequence.ReceiptType.PAYMENT  # "P"
                
                # Generar nuevo número de comprobante (sobrescribirá el existente)
                receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=payment.reservation.hotel,
                    receipt_type=receipt_type
                )
                
                old_receipt_number = payment.receipt_number
                
                if not dry_run:
                    payment.receipt_number = receipt_number
                    payment.save(update_fields=['receipt_number'])
                
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Pago {payment.id} ({'Seña' if payment.is_deposit else 'Pago'}): '{old_receipt_number}' -> '{receipt_number}'")
                )
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error con pago {payment.id}: {e}")
                )
        
        # Mostrar resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN'))
        self.stdout.write('='*50)
        self.stdout.write(f"📄 Pagos procesados: {processed}")
        self.stdout.write(f"❌ Errores: {errors}")
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n🎉 ¡Actualización forzada completada!'))
        else:
            self.stdout.write(self.style.WARNING('\n💡 Ejecuta sin --dry-run para aplicar los cambios'))

