from django.core.management.base import BaseCommand
from apps.reservations.models import Payment
from apps.reservations.serializers import PaymentSerializer


class Command(BaseCommand):
    help = 'Verifica un pago específico y su serialización'

    def add_arguments(self, parser):
        parser.add_argument('payment_id', type=int, help='ID del pago a verificar')

    def handle(self, *args, **options):
        payment_id = options['payment_id']
        
        try:
            payment = Payment.objects.get(id=payment_id)
            
            self.stdout.write(f'🔍 VERIFICANDO PAGO {payment_id}')
            self.stdout.write('='*40)
            self.stdout.write(f'ID: {payment.id}')
            self.stdout.write(f'receipt_number en BD: "{payment.receipt_number}"')
            self.stdout.write(f'receipt_number es None: {payment.receipt_number is None}')
            self.stdout.write(f'receipt_number es vacío: {payment.receipt_number == ""}')
            
            # Serializar el pago
            serializer = PaymentSerializer(payment)
            data = serializer.data
            
            self.stdout.write(f'\n📋 DATOS DEL SERIALIZER:')
            self.stdout.write(f'receipt_number: "{data.get("receipt_number")}"')
            self.stdout.write(f'todos los campos: {list(data.keys())}')
            
            # Verificar si el campo está en la respuesta
            if 'receipt_number' in data:
                self.stdout.write('✅ El campo receipt_number está en el serializer')
            else:
                self.stdout.write('❌ El campo receipt_number NO está en el serializer')
                
        except Payment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ No se encontró el pago con ID {payment_id}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))








