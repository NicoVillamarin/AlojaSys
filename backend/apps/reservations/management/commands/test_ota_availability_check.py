"""
Comando de prueba para validación de disponibilidad en OTAs antes de confirmar reservas.
Verifica que el sistema detecte conflictos con reservas de OTAs antes de confirmar.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel
from apps.otas.models import OtaConfig, OtaRoomMapping, OtaProvider
from apps.otas.services.availability_checker import OtaAvailabilityChecker
from apps.reservations.serializers import ReservationSerializer


class Command(BaseCommand):
    help = "Prueba la validación de disponibilidad en OTAs antes de confirmar reservas"

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

    def handle(self, *args, **options):
        hotel_id = options.get("hotel_id")
        room_id = options.get("room_id")

        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA VALIDACIÓN DISPONIBILIDAD OTA ===\n"))

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

        # Crear/obtener OtaConfig para Booking
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
        self.stdout.write(f"✅ Mapping Booking: {booking_mapping.id}\n")

        # ===== PRUEBA 1: Verificar disponibilidad sin conflictos =====
        self.stdout.write(self.style.SUCCESS("=== PRUEBA 1: Disponibilidad sin conflictos ===\n"))

        check_in = date.today() + timedelta(days=15)
        check_out = check_in + timedelta(days=2)

        results = OtaAvailabilityChecker.check_availability_for_room(
            room=room,
            check_in=check_in,
            check_out=check_out
        )

        self.stdout.write(f"📅 Fechas: {check_in} → {check_out}")
        self.stdout.write(f"📊 Resultados de verificación ({len(results)}):")
        for result in results:
            status = "✅ Disponible" if result.is_available else "❌ No disponible"
            self.stdout.write(f"   - {result.provider}: {status}")
            if result.error:
                self.stdout.write(f"      Error: {result.error}")
            if result.details:
                self.stdout.write(f"      Detalles: {result.details}")

        # ===== PRUEBA 2: Crear reserva desde OTA y verificar conflicto =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 2: Crear reserva OTA y verificar conflicto ===\n"))

        # Crear una reserva "desde Booking" (con external_id y channel=booking)
        # Usar capacidad de la habitación para evitar errores de validación
        guests_count = min(room.max_capacity or 1, 2)
        ota_reservation = Reservation(
            hotel=hotel,
            room=room,
            external_id=f"BK_TEST_{int(timezone.now().timestamp())}",
            channel=ReservationChannel.BOOKING,
            check_in=check_in,
            check_out=check_out,
            status=ReservationStatus.CONFIRMED,
            guests=guests_count,
            guests_data=[{"source": "booking"}],
            notes="Reserva de prueba desde Booking.com",
        )
        # Usar skip_clean para evitar validaciones de capacidad/solapamiento
        ota_reservation.save(skip_clean=True)

        self.stdout.write(f"✅ Reserva OTA creada:")
        self.stdout.write(f"   - ID: {ota_reservation.id}")
        self.stdout.write(f"   - external_id: {ota_reservation.external_id}")
        self.stdout.write(f"   - channel: {ota_reservation.channel}")
        self.stdout.write(f"   - check_in: {ota_reservation.check_in}, check_out: {ota_reservation.check_out}\n")

        # Verificar disponibilidad ahora (debería detectar el conflicto)
        results_with_conflict = OtaAvailabilityChecker.check_availability_for_room(
            room=room,
            check_in=check_in,
            check_out=check_out
        )

        self.stdout.write(f"📊 Verificación después de crear reserva OTA:")
        has_conflict = False
        for result in results_with_conflict:
            status = "✅ Disponible" if result.is_available else "❌ No disponible"
            self.stdout.write(f"   - {result.provider}: {status}")
            if not result.is_available:
                has_conflict = True
                self.stdout.write(f"      Error: {result.error}")
                if result.details:
                    self.stdout.write(f"      Detalles: {result.details}")

        if has_conflict:
            self.stdout.write(self.style.SUCCESS("\n✅ Conflicto detectado correctamente"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No se detectó conflicto (puede ser que no haya OTA configurada)"))

        # ===== PRUEBA 3: Intentar crear reserva con conflicto =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 3: Intentar crear reserva con conflicto ===\n"))

        # Intentar crear una reserva directa (sin external_id) en las mismas fechas
        try:
            serializer = ReservationSerializer(data={
                "hotel": hotel.id,
                "room": room.id,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "guests": 2,
                "status": ReservationStatus.CONFIRMED,  # Modo estricto
                "channel": ReservationChannel.DIRECT,
            })
            
            if serializer.is_valid():
                reservation = serializer.save()
                self.stdout.write(self.style.WARNING("⚠️  Reserva creada (no se detectó conflicto)"))
                reservation.delete()  # Limpiar
            else:
                self.stdout.write(f"❌ Error de validación: {serializer.errors}")
                if "La habitación no está disponible en las OTAs" in str(serializer.errors):
                    self.stdout.write(self.style.SUCCESS("✅ Validación funcionando: rechazó la reserva por conflicto OTA"))
        except ValidationError as e:
            if "no está disponible en las OTAs" in str(e):
                self.stdout.write(self.style.SUCCESS(f"✅ Validación funcionando: {e}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error inesperado: {e}"))

        # ===== PRUEBA 4: Validar en modo no estricto (permite con advertencia) =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 4: Validación en modo no estricto ===\n"))

        # Fechas diferentes para no conflictuar
        check_in_2 = date.today() + timedelta(days=20)
        check_out_2 = check_in_2 + timedelta(days=1)

        is_valid, warnings = OtaAvailabilityChecker.validate_before_confirmation(
            room=room,
            check_in=check_in_2,
            check_out=check_out_2,
            strict=False  # Modo no estricto
        )

        self.stdout.write(f"📊 Validación (modo no estricto):")
        self.stdout.write(f"   - Válido: {is_valid}")
        self.stdout.write(f"   - Advertencias: {len(warnings)}")
        if warnings:
            for warning in warnings:
                self.stdout.write(f"      - {warning}")

        # ===== PRUEBA 5: Actualizar reserva existente (debe excluir su propio ID) =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 5: Actualizar reserva existente ===\n"))

        # Crear reserva directa en fechas diferentes
        guests_count_2 = min(room.max_capacity or 1, 2)
        direct_reservation = Reservation(
            hotel=hotel,
            room=room,
            check_in=check_in_2,
            check_out=check_out_2,
            status=ReservationStatus.PENDING,
            guests=guests_count_2,
            guests_data=[{"name": "Test Guest"}],  # Agregar guests_data para evitar error de validación
            channel=ReservationChannel.DIRECT,
        )
        direct_reservation.save(skip_clean=True)

        self.stdout.write(f"✅ Reserva directa creada (ID: {direct_reservation.id})")

        # Verificar disponibilidad excluyendo esta reserva
        results_excluded = OtaAvailabilityChecker.check_availability_for_room(
            room=room,
            check_in=check_in_2,
            check_out=check_out_2,
            exclude_reservation_id=direct_reservation.id
        )

        self.stdout.write(f"📊 Verificación excluyendo reserva {direct_reservation.id}:")
        for result in results_excluded:
            status = "✅ Disponible" if result.is_available else "❌ No disponible"
            self.stdout.write(f"   - {result.provider}: {status}")

        # Intentar confirmar la reserva (debe permitir porque excluimos su propio ID)
        try:
            serializer = ReservationSerializer(
                direct_reservation,
                data={"status": ReservationStatus.CONFIRMED},
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                self.stdout.write(self.style.SUCCESS("✅ Reserva confirmada correctamente (no hubo conflicto)"))
            else:
                self.stdout.write(f"⚠️  Error: {serializer.errors}")
        except ValidationError as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Validación rechazó: {e}"))

        # ===== LIMPIEZA =====
        self.stdout.write(self.style.SUCCESS("\n=== LIMPIEZA ===\n"))
        
        # Guardar IDs antes de eliminar
        ota_reservation_id = ota_reservation.id
        direct_reservation_id = direct_reservation.id if direct_reservation else None
        
        try:
            ota_reservation.refresh_from_db()
            ota_reservation.delete()
            self.stdout.write(f"✅ Reserva OTA eliminada (ID: {ota_reservation_id})")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  No se pudo eliminar reserva OTA (ID: {ota_reservation_id}): {e}"))
        
        if direct_reservation_id:
            try:
                direct_reservation.refresh_from_db()
                direct_reservation.delete()
                self.stdout.write(f"✅ Reserva directa eliminada (ID: {direct_reservation_id})")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  No se pudo eliminar reserva directa (ID: {direct_reservation_id}): {e}"))

        # ===== RESUMEN FINAL =====
        self.stdout.write(self.style.SUCCESS("\n=== RESUMEN ===\n"))

        self.stdout.write("✅ Pruebas completadas!")
        self.stdout.write("\nFuncionalidades probadas:")
        self.stdout.write("  - Verificación de disponibilidad sin conflictos")
        self.stdout.write("  - Detección de conflictos con reservas de OTAs")
        self.stdout.write("  - Validación estricta antes de confirmar")
        self.stdout.write("  - Modo no estricto (solo advertencias)")
        self.stdout.write("  - Exclusión de reserva propia al actualizar")

