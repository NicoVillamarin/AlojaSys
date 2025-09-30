from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType, RoomStatus
from apps.reservations.models import Reservation, ReservationStatus
from .models import DashboardMetrics

class DashboardMetricsModelTest(TestCase):
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Hotel Test",
            email="test@hotel.com",
            phone="123456789"
        )
        
        # Crear habitaciones
        self.room1 = Room.objects.create(
            name="101",
            hotel=self.hotel,
            floor=1,
            room_type=RoomType.SINGLE,
            number=101,
            base_price=Decimal('100.00'),
            capacity=1,
            max_capacity=1,
            status=RoomStatus.AVAILABLE
        )
        
        self.room2 = Room.objects.create(
            name="102",
            hotel=self.hotel,
            floor=1,
            room_type=RoomType.DOUBLE,
            number=102,
            base_price=Decimal('150.00'),
            capacity=2,
            max_capacity=2,
            status=RoomStatus.OCCUPIED
        )
        
        # Crear reservas
        self.reservation1 = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room1,
            guests=1,
            guests_data=[{'name': 'Juan Pérez', 'email': 'juan@test.com', 'is_primary': True}],
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            status=ReservationStatus.CONFIRMED,
            total_price=Decimal('200.00')
        )
        
        self.reservation2 = Reservation.objects.create(
            hotel=self.hotel,
            room=self.room2,
            guests=2,
            guests_data=[
                {'name': 'María García', 'email': 'maria@test.com', 'is_primary': True},
                {'name': 'Carlos García', 'email': 'carlos@test.com', 'is_primary': False}
            ],
            check_in=date.today(),
            check_out=date.today() + timedelta(days=3),
            status=ReservationStatus.CHECK_IN,
            total_price=Decimal('450.00')
        )
    
    def test_calculate_metrics(self):
        """Test que las métricas se calculan correctamente"""
        metrics = DashboardMetrics.calculate_metrics(self.hotel, date.today())
        
        # Verificar métricas de habitaciones
        self.assertEqual(metrics.total_rooms, 2)
        self.assertEqual(metrics.available_rooms, 1)
        self.assertEqual(metrics.occupied_rooms, 1)
        
        # Verificar métricas de reservas
        self.assertEqual(metrics.total_reservations, 2)
        self.assertEqual(metrics.confirmed_reservations, 1)
        self.assertEqual(metrics.check_in_today, 2)  # 2 reservas que empiezan hoy
        
        # Verificar métricas de huéspedes
        self.assertEqual(metrics.total_guests, 3)  # 1 + 2 huéspedes
        self.assertEqual(metrics.guests_checked_in, 2)  # Solo la reserva con CHECK_IN
        
        # Verificar métricas financieras
        self.assertEqual(metrics.total_revenue, Decimal('450.00'))  # Solo la reserva con CHECK_IN
        self.assertEqual(metrics.average_room_rate, Decimal('450.00'))  # 450 / 1 habitación ocupada
        
        # Verificar tasa de ocupación
        self.assertEqual(metrics.occupancy_rate, Decimal('50.00'))  # 1 ocupada de 2 totales
    
    def test_metrics_unique_constraint(self):
        """Test que no se pueden crear métricas duplicadas para el mismo hotel y fecha"""
        DashboardMetrics.calculate_metrics(self.hotel, date.today())
        
        # Intentar crear otra métrica para el mismo hotel y fecha
        with self.assertRaises(Exception):
            DashboardMetrics.objects.create(
                hotel=self.hotel,
                date=date.today(),
                total_rooms=1
            )
    
    def test_metrics_string_representation(self):
        """Test la representación en string del modelo"""
        metrics = DashboardMetrics.calculate_metrics(self.hotel, date.today())
        expected = f"{self.hotel.name} - {date.today()}"
        self.assertEqual(str(metrics), expected)

class DashboardMetricsViewTest(TestCase):
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Hotel Test",
            email="test@hotel.com",
            phone="123456789"
        )
        
        self.room = Room.objects.create(
            name="101",
            hotel=self.hotel,
            floor=1,
            room_type=RoomType.SINGLE,
            number=101,
            base_price=Decimal('100.00'),
            capacity=1,
            max_capacity=1,
            status=RoomStatus.AVAILABLE
        )
    
    def test_dashboard_summary_endpoint(self):
        """Test del endpoint de resumen del dashboard"""
        from django.test import Client
        client = Client()
        
        response = client.get(f'/api/dashboard/summary/?hotel_id={self.hotel.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('hotel_id', data)
        self.assertIn('hotel_name', data)
        self.assertIn('total_rooms', data)
        self.assertIn('occupancy_rate', data)
        self.assertEqual(data['hotel_id'], self.hotel.id)
        self.assertEqual(data['hotel_name'], self.hotel.name)
    
    def test_dashboard_summary_missing_hotel_id(self):
        """Test del endpoint de resumen sin hotel_id"""
        from django.test import Client
        client = Client()
        
        response = client.get('/api/dashboard/summary/')
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'hotel_id es requerido')
    
    def test_dashboard_trends_endpoint(self):
        """Test del endpoint de tendencias del dashboard"""
        from django.test import Client
        client = Client()
        
        response = client.get(f'/api/dashboard/trends/?hotel_id={self.hotel.id}&days=7')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 7)  # 7 días de datos
        
        # Verificar que cada día tiene las métricas esperadas
        for day_data in data:
            self.assertIn('date', day_data)
            self.assertIn('occupancy_rate', day_data)
            self.assertIn('total_revenue', day_data)
