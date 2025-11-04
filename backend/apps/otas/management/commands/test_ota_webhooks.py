"""
Comando de prueba para webhooks de OTAs (Booking / Airbnb)
Simula webhooks y verifica que se procesen correctamente
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.test import RequestFactory
from rest_framework.test import APIClient
from django.test.utils import override_settings
from datetime import date, timedelta
import json

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from apps.otas.models import OtaConfig, OtaRoomMapping, OtaProvider, OtaSyncJob, OtaSyncLog
from apps.otas.views import booking_webhook, airbnb_webhook


class Command(BaseCommand):
    help = "Prueba los endpoints webhooks de OTAs (Booking / Airbnb)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hotel-id",
            type=int,
            help="ID del hotel para las pruebas",
        )
        parser.add_argument(
            "--room-id",
            type=int,
            help="ID de la habitación para las pruebas",
        )
        parser.add_argument(
            "--skip-hmac",
            action="store_true",
            help="Omitir verificación HMAC (útil para pruebas)",
        )

    def handle(self, *args, **options):
        hotel_id = options.get("hotel_id")
        room_id = options.get("room_id")
        skip_hmac = options.get("skip_hmac", False)

        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA WEBHOOKS OTA ===\n"))

        # Obtener hotel y habitación
        if not hotel_id or not room_id:
            self.stdout.write(self.style.WARNING("Buscando hotel y habitación existentes..."))
            hotel = Hotel.objects.first()
            if not hotel:
                self.stdout.write(self.style.ERROR("❌ No hay hoteles en la base de datos"))
                return
            room = Room.objects.filter(hotel=hotel).first()
            if not room:
                self.stdout.write(self.style.ERROR(f"❌ No hay habitaciones en el hotel {hotel.name}"))
                return
            hotel_id = hotel.id
            room_id = room.id
        else:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)

        self.stdout.write(f"📍 Hotel: {hotel.name} (ID: {hotel_id})")
        self.stdout.write(f"📍 Habitación: {room.name} (ID: {room_id})\n")

        # Crear/obtener OtaConfig y OtaRoomMapping para Booking
        booking_config, _ = OtaConfig.objects.get_or_create(
            hotel=hotel,
            provider=OtaProvider.BOOKING,
            defaults={"is_active": True, "label": "Booking Test"},
        )
        booking_mapping, _ = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.BOOKING,
            defaults={
                "external_id": "BK_ROOM_001",
                "is_active": True,
            },
        )
        self.stdout.write(f"✅ Config Booking: {booking_config.id}")
        self.stdout.write(f"✅ Mapping Booking: {booking_mapping.id} (external_id: {booking_mapping.external_id})\n")

        # Factory para crear requests simulados
        factory = RequestFactory()
        
        # ===== PRUEBA 1: Webhook Booking - Nueva Reserva =====
        self.stdout.write(self.style.SUCCESS("=== PRUEBA 1: Webhook Booking - Nueva Reserva ===\n"))

        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        external_id = f"BK_RES_{int(timezone.now().timestamp())}"

        webhook_data = {
            "event_id": f"evt_{int(timezone.now().timestamp())}",
            "reservation_id": external_id,
            "hotel_id": hotel_id,
            "ota_room_id": booking_mapping.external_id,
            "check_in": str(check_in),
            "check_out": str(check_out),
            "guests": 2,
            "notes": "Reserva de prueba desde webhook",
        }

        # Contar reservas antes
        reservas_antes = Reservation.objects.filter(
            hotel=hotel,
            external_id=external_id,
        ).count()

        self.stdout.write(f"📊 Reservas con external_id={external_id} antes: {reservas_antes}")

        # Simular request
        request = factory.post(
            "/api/otas/webhooks/booking/",
            data=json.dumps(webhook_data),
            content_type="application/json",
        )
        if skip_hmac:
            # En modo DEBUG, no necesitamos firma
            request._body = request.body

        # Ejecutar webhook
        with override_settings(DEBUG=True):  # Permitir sin HMAC en DEBUG
            response = booking_webhook(request)

        self.stdout.write(f"\n📤 Request enviado:")
        self.stdout.write(f"   - event_id: {webhook_data['event_id']}")
        self.stdout.write(f"   - reservation_id: {webhook_data['reservation_id']}")
        self.stdout.write(f"   - check_in: {check_in}, check_out: {check_out}")

        self.stdout.write(f"\n📥 Response recibido:")
        self.stdout.write(f"   - Status: {response.status_code}")
        self.stdout.write(f"   - Data: {json.dumps(response.data, indent=2)}")

        # Verificar reservas después
        reservas_despues = Reservation.objects.filter(
            hotel=hotel,
            external_id=external_id,
        ).count()
        self.stdout.write(f"\n📊 Reservas con external_id={external_id} después: {reservas_despues}")
        self.stdout.write(f"   ⬆️  Diferencia: {reservas_despues - reservas_antes}")

        if reservas_despues > reservas_antes:
            reservation = Reservation.objects.get(external_id=external_id)
            self.stdout.write(f"\n✅ Reserva creada:")
            self.stdout.write(f"   - ID: {reservation.id}")
            self.stdout.write(f"   - external_id: {reservation.external_id}")
            self.stdout.write(f"   - channel: {reservation.channel}")
            self.stdout.write(f"   - status: {reservation.status}")
            self.stdout.write(f"   - check_in: {reservation.check_in}, check_out: {reservation.check_out}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No se creó la reserva"))

        # Verificar logs
        jobs = OtaSyncJob.objects.filter(provider=OtaProvider.BOOKING, stats__webhook=True).order_by("-started_at")[:1]
        if jobs.exists():
            job = jobs.first()
            self.stdout.write(f"\n📝 Job creado:")
            self.stdout.write(f"   - ID: {job.id}")
            self.stdout.write(f"   - Status: {job.status}")
            self.stdout.write(f"   - Stats: {job.stats}")

            logs = job.logs.all().order_by("created_at")
            if logs.exists():
                self.stdout.write(f"\n📋 Logs ({logs.count()}):")
                for log in logs[:5]:
                    payload_str = json.dumps(log.payload, indent=2) if log.payload else "{}"
                    self.stdout.write(f"   [{log.level.upper()}] {log.message}")
                    if log.payload:
                        self.stdout.write(f"      Payload: {json.dumps(log.payload, indent=6)}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No se creó job de webhook"))

        # ===== PRUEBA 2: Webhook Booking - Idempotencia (Duplicado) =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 2: Webhook Booking - Idempotencia ===\n"))

        # Enviar el mismo webhook otra vez
        request2 = factory.post(
            "/api/otas/webhooks/booking/",
            data=json.dumps(webhook_data),
            content_type="application/json",
        )
        if skip_hmac:
            request2._body = request2.body

        with override_settings(DEBUG=True):
            response2 = booking_webhook(request2)

        self.stdout.write(f"📥 Response (duplicado):")
        self.stdout.write(f"   - Status: {response2.status_code}")
        self.stdout.write(f"   - Data: {json.dumps(response2.data, indent=2)}")

        reservas_despues_dup = Reservation.objects.filter(
            hotel=hotel,
            external_id=external_id,
        ).count()
        self.stdout.write(f"\n📊 Reservas después del duplicado: {reservas_despues_dup}")

        if reservas_despues_dup == reservas_despues:
            self.stdout.write(self.style.SUCCESS("   ✅ Idempotencia funcionando (no se creó duplicado)"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ Idempotencia falló (se creó duplicado)"))

        # ===== PRUEBA 3: Webhook Booking - Actualizar Reserva Existente =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 3: Webhook Booking - Actualizar Reserva ===\n"))

        if reservas_despues > 0:
            reservation = Reservation.objects.get(external_id=external_id)
            old_check_out = reservation.check_out
            new_check_out = old_check_out + timedelta(days=1)

            webhook_update = {
                "event_id": f"evt_update_{int(timezone.now().timestamp())}",
                "reservation_id": external_id,
                "hotel_id": hotel_id,
                "ota_room_id": booking_mapping.external_id,
                "check_in": str(check_in),
                "check_out": str(new_check_out),
                "guests": 3,
                "notes": "Actualización desde webhook",
            }

            request3 = factory.post(
                "/api/otas/webhooks/booking/",
                data=json.dumps(webhook_update),
                content_type="application/json",
            )
            if skip_hmac:
                request3._body = request3.body

            with override_settings(DEBUG=True):
                response3 = booking_webhook(request3)

            self.stdout.write(f"📥 Response (actualización):")
            self.stdout.write(f"   - Status: {response3.status_code}")
            self.stdout.write(f"   - Data: {json.dumps(response3.data, indent=2)}")

            reservation.refresh_from_db()
            self.stdout.write(f"\n📊 Reserva actualizada:")
            self.stdout.write(f"   - check_out anterior: {old_check_out}")
            self.stdout.write(f"   - check_out nuevo: {reservation.check_out}")
            self.stdout.write(f"   - guests: {reservation.guests}")

            if reservation.check_out == new_check_out:
                self.stdout.write(self.style.SUCCESS("   ✅ Actualización funcionando"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ Actualización falló"))

        # ===== PRUEBA 4: Webhook Airbnb =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 4: Webhook Airbnb ===\n"))

        airbnb_config, _ = OtaConfig.objects.get_or_create(
            hotel=hotel,
            provider=OtaProvider.AIRBNB,
            defaults={"is_active": True, "label": "Airbnb Test"},
        )
        airbnb_mapping, _ = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.AIRBNB,
            defaults={
                "external_id": "AB_ROOM_001",
                "is_active": True,
            },
        )

        check_in_ab = date.today() + timedelta(days=10)
        check_out_ab = check_in_ab + timedelta(days=3)
        external_id_ab = f"AB_RES_{int(timezone.now().timestamp())}"

        webhook_data_ab = {
            "event_id": f"evt_ab_{int(timezone.now().timestamp())}",
            "reservation_id": external_id_ab,
            "hotel_id": hotel_id,
            "ota_room_id": airbnb_mapping.external_id,
            "check_in": str(check_in_ab),
            "check_out": str(check_out_ab),
            "guests": 4,
            "notes": "Reserva Airbnb desde webhook",
        }

        request4 = factory.post(
            "/api/otas/webhooks/airbnb/",
            data=json.dumps(webhook_data_ab),
            content_type="application/json",
        )
        if skip_hmac:
            request4._body = request4.body

        with override_settings(DEBUG=True):
            response4 = airbnb_webhook(request4)

        self.stdout.write(f"📥 Response Airbnb:")
        self.stdout.write(f"   - Status: {response4.status_code}")
        self.stdout.write(f"   - Data: {json.dumps(response4.data, indent=2)}")

        reserva_ab = Reservation.objects.filter(external_id=external_id_ab).first()
        if reserva_ab:
            self.stdout.write(f"\n✅ Reserva Airbnb creada:")
            self.stdout.write(f"   - ID: {reserva_ab.id}")
            self.stdout.write(f"   - channel: {reserva_ab.channel}")
            self.stdout.write(f"   - external_id: {reserva_ab.external_id}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No se creó reserva Airbnb"))

        # ===== RESUMEN FINAL =====
        self.stdout.write(self.style.SUCCESS("\n=== RESUMEN ===\n"))

        total_webhook_jobs = OtaSyncJob.objects.filter(stats__webhook=True).count()
        self.stdout.write(f"📊 Total jobs de webhooks: {total_webhook_jobs}")

        total_webhook_logs = OtaSyncLog.objects.filter(
            message__startswith="WEBHOOK"
        ).count()
        self.stdout.write(f"📝 Total logs de webhooks: {total_webhook_logs}")

        self.stdout.write(self.style.SUCCESS("\n✅ Pruebas completadas!\n"))

