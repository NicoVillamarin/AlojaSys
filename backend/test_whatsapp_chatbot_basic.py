from datetime import date, timedelta

from rest_framework.test import APITestCase

from apps.core.models import Hotel
from apps.rooms.models import Room, RoomType
from apps.reservations.models import Reservation, ReservationStatus


class WhatsappChatbotBasicFlowTests(APITestCase):
    """
    Prueba básica end-to-end del flujo de WhatsApp contra el webhook HTTP.

    No usa ningún proveedor real, solo verifica que:
    - Se resuelve el hotel por número de WhatsApp.
    - Se crea/actualiza la ChatSession internamente.
    - Al confirmar, se crea una Reservation en estado pending.
    """

    def setUp(self):
        # Crear hotel mínimo con WhatsApp habilitado
        self.hotel = Hotel.objects.create(
            name="Hotel WhatsApp Test",
            email="test@example.com",
            phone="+5491100000000",
            address="Calle Falsa 123",
        )
        self.hotel.whatsapp_enabled = True
        self.hotel.whatsapp_phone = "+5491111111111"
        self.hotel.save()

        # Crear una habitación disponible para el rango de fechas
        self.room = Room.objects.create(
            name="101",
            hotel=self.hotel,
            floor=1,
            room_type=RoomType.SINGLE,
            number=101,
            description="Test room",
            base_price=100,
            capacity=2,
            max_capacity=2,
            extra_guest_fee=0,
        )

        self.webhook_url = "/api/chatbot/whatsapp/webhook/"
        self.guest_phone = "+5492222222222"
        self.to_number = self.hotel.whatsapp_phone

        # Fechas futuras para evitar validaciones por pasado
        today = date.today()
        self.check_in = today + timedelta(days=30)
        self.check_out = today + timedelta(days=32)

    def _post(self, message: str):
        return self.client.post(
            self.webhook_url,
            {
                "from": self.guest_phone,
                "to": self.to_number,
                "message": message,
            },
            format="json",
        )

    def test_full_conversation_creates_pending_reservation(self):
        """
        Simula toda la conversación hasta crear una reserva pending.
        """
        # Paso 1: check‑in
        resp1 = self._post(self.check_in.isoformat())
        self.assertEqual(resp1.status_code, 200)
        # Debe preguntar por la fecha de check-out
        self.assertIn("fecha de check-out", resp1.data.get("reply", "").lower())

        # Paso 2: check‑out
        resp2 = self._post(self.check_out.isoformat())
        self.assertEqual(resp2.status_code, 200)
        # Debe pedir la cantidad de personas
        self.assertIn("personas", resp2.data.get("reply", "").lower())

        # Paso 3: cantidad de huéspedes
        resp3 = self._post("2")
        self.assertEqual(resp3.status_code, 200)
        self.assertIn("¿a nombre de quién", resp3.data.get("reply", "").lower())

        # Paso 4: nombre huésped
        resp4 = self._post("Juan Test")
        self.assertEqual(resp4.status_code, 200)
        self.assertIn("email de contacto", resp4.data.get("reply", "").lower())

        # Paso 5: sin email
        resp5 = self._post("sin email")
        self.assertEqual(resp5.status_code, 200)
        self.assertIn("¿confirmás", resp5.data.get("reply", "").lower())

        # Paso 6: confirmación
        resp6 = self._post("si")
        self.assertEqual(resp6.status_code, 200)
        reply6 = resp6.data.get("reply", "").lower()
        self.assertIn("reserva", reply6)
        self.assertIn("pendiente", reply6)

        # Verificar que se creó exactamente una reserva pending
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.hotel, self.hotel)
        self.assertEqual(reservation.room, self.room)
        self.assertEqual(reservation.guests, 2)
        self.assertEqual(reservation.check_in, self.check_in)
        self.assertEqual(reservation.check_out, self.check_out)


