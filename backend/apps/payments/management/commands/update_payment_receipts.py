from django.core.management.base import BaseCommand
from apps.payments.models import ReceiptNumberSequence
from apps.reservations.models import Payment


class Command(BaseCommand):
    help = 'Actualiza números de comprobante serios para pagos/señas existentes'

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
            help='Limitar el número de comprobantes a procesar (útil para pruebas)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN - No se realizarán cambios'))
        
        self.stdout.write('🔄 Actualizando números de comprobante para pagos/señas...')
        
        # Obtener pagos sin número de comprobante
        payments_query = Payment.objects.filter(
            receipt_number__isnull=True
        ).order_by('created_at')
        
        if limit:
            payments_query = payments_query[:limit]
            self.stdout.write(f"📊 Procesando solo {limit} comprobantes (límite establecido)")
        
        payments_count = payments_query.count()
        self.stdout.write(f"📄 Encontrados {payments_count} pagos sin número de comprobante")
        
        if payments_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todos los pagos ya tienen número de comprobante'))
            return
        
        # Procesar pagos
        processed = 0
        errors = 0
        
        for payment in payments_query:
            try:
                # Determinar el tipo de comprobante según si es seña o pago total
                if payment.is_deposit:
                    receipt_type = ReceiptNumberSequence.ReceiptType.DEPOSIT  # "S"
                else:
                    receipt_type = ReceiptNumberSequence.ReceiptType.PAYMENT  # "P"
                
                receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=payment.reservation.hotel,
                    receipt_type=receipt_type
                )
                
                if not dry_run:
                    payment.receipt_number = receipt_number
                    payment.save(update_fields=['receipt_number'])
                
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Pago {payment.id} ({'Seña' if payment.is_deposit else 'Pago'}) -> {receipt_number}")
                )
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error con pago {payment.id}: {e}")
                )
        
        # Mostrar resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE ACTUALIZACIÓN'))
        self.stdout.write('='*50)
        self.stdout.write(f"📄 Pagos procesados: {processed}")
        self.stdout.write(f"❌ Errores: {errors}")
        self.stdout.write(f"📊 Total encontrados: {payments_count}")
        
        if not dry_run:
            # Mostrar estadísticas finales
            total_payments = Payment.objects.filter(receipt_number__isnull=False).count()
            total_without = Payment.objects.filter(receipt_number__isnull=True).count()
            
            self.stdout.write(f"\n📈 ESTADÍSTICAS FINALES:")
            self.stdout.write(f"   - Pagos CON número de comprobante: {total_payments}")
            self.stdout.write(f"   - Pagos SIN número de comprobante: {total_without}")
            
            if total_without == 0:
                self.stdout.write(self.style.SUCCESS('\n🎉 ¡Todos los pagos tienen número de comprobante serio!'))
            else:
                self.stdout.write(self.style.WARNING(f'\n⚠️  Aún quedan {total_without} pagos sin número de comprobante'))
        else:
            self.stdout.write(self.style.WARNING('\n💡 Ejecuta sin --dry-run para aplicar los cambios'))

