#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.reservations.models import Reservation, ReservationStatus
from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Payment
from apps.payments.models import RefundPolicy
from apps.payments.services.refund_processor import RefundProcessor

def test_refund_flow():
    print("🧪 PROBANDO FLUJO DE REEMBOLSOS")
    print("=" * 50)
    
    # 1. Verificar datos base
    hotel = Hotel.objects.first()
    room = Room.objects.first()
    refund_policy = RefundPolicy.objects.first()
    
    print(f"Hotel: {hotel.name if hotel else 'No encontrado'}")
    print(f"Habitación: {room.name if room else 'No encontrada'}")
    print(f"Política de devolución: {refund_policy.name if refund_policy else 'No encontrada'}")
    
    if not hotel or not room:
        print("❌ Faltan datos base (hotel o habitación)")
        return
    
    # 2. Crear reserva de prueba
    print("\n📋 CREANDO RESERVA DE PRUEBA")
    reservation = Reservation.objects.create(
        hotel=hotel,
        room=room,
        guest_name='Test Guest',
        guest_email='test@example.com',
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=3),
        total_price=Decimal('100.00'),
        status=ReservationStatus.CONFIRMED
    )
    
    # 3. Crear pago de prueba
    payment = Payment.objects.create(
        reservation=reservation,
        method='cash',
        amount=Decimal('50.00'),
        date=date.today()
    )
    
    print(f"✅ Reserva creada: ID {reservation.id}")
    print(f"   Estado: {reservation.status}")
    print(f"   Check-in: {reservation.check_in}")
    print(f"   Total: ${reservation.total_price}")
    print(f"   Pago: ${payment.amount} ({payment.method})")
    
    # 4. Probar cálculo de cancelación
    print("\n💰 PROBANDO CÁLCULO DE CANCELACIÓN")
    try:
        from apps.reservations.views import ReservationViewSet
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.first()
        
        # Simular request de cálculo
        factory = RequestFactory()
        request = factory.post(f'/api/reservations/{reservation.id}/cancel/', 
                             {'confirm': False}, 
                             content_type='application/json')
        request.user = user
        
        viewset = ReservationViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        
        response = viewset.cancel(request, pk=reservation.id)
        
        if response.status_code == 200:
            data = response.data
            print("✅ Cálculo exitoso:")
            print(f"   Total pagado: ${data['financial_summary']['total_paid']}")
            print(f"   Penalidad: ${data['financial_summary']['penalty_amount']}")
            print(f"   Devolución: ${data['financial_summary']['refund_amount']}")
            print(f"   Neto: ${data['financial_summary']['net_refund']}")
        else:
            print(f"❌ Error en cálculo: {response.status_code}")
            print(response.data)
            
    except Exception as e:
        print(f"❌ Error en cálculo: {e}")
    
    # 5. Probar cancelación real
    print("\n🔄 PROBANDO CANCELACIÓN REAL")
    try:
        # Simular request de confirmación
        request = factory.post(f'/api/reservations/{reservation.id}/cancel/', 
                             {'confirm': True}, 
                             content_type='application/json')
        request.user = user
        
        response = viewset.cancel(request, pk=reservation.id)
        
        if response.status_code == 200:
            data = response.data
            print("✅ Cancelación exitosa:")
            print(f"   Estado final: {data['reservation']['status']}")
            print(f"   Reembolso procesado: {data.get('refund_processed', False)}")
        else:
            print(f"❌ Error en cancelación: {response.status_code}")
            print(response.data)
            
    except Exception as e:
        print(f"❌ Error en cancelación: {e}")
    
    # 6. Verificar reembolsos creados
    print("\n📊 VERIFICANDO REEMBOLSOS CREADOS")
    from apps.payments.models import Refund
    refunds = Refund.objects.filter(reservation=reservation)
    print(f"Reembolsos creados: {refunds.count()}")
    for refund in refunds:
        print(f"   ID: {refund.id} | Monto: ${refund.amount} | Estado: {refund.status}")
        print(f"   Método: {refund.refund_method} | Razón: {refund.reason}")
    
    print("\n🎯 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_refund_flow()
