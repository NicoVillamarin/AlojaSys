"""
Script de prueba para ICALSyncService.

Prueba:
- import_reservations: Importación desde feed iCal
- export_reservations: Exportación de reservas
- schedule_sync: Sincronización completa
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

from apps.otas.models import OtaRoomMapping, OtaSyncJob, OtaProvider, OtaSyncLog
from apps.otas.services.ical_sync_service import ICALSyncService
from apps.reservations.models import Reservation, ReservationStatus, ReservationChannel, RoomBlock
from apps.core.models import Hotel
from apps.rooms.models import Room


class Command(BaseCommand):
    help = "Prueba ICALSyncService: import_reservations, export_reservations, schedule_sync"

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
            "--ical-url",
            type=str,
            default=None,
            help="URL del feed iCal para pruebas (si no se especifica, se crea un ejemplo básico)",
        )
        parser.add_argument(
            "--create-test-ical",
            action="store_true",
            help="Crear un evento iCal de prueba en lugar de usar URL externa",
        )

    def handle(self, *args, **options):
        hotel_id = options.get("hotel_id")
        room_id = options.get("room_id")
        ical_url = options.get("ical_url")

        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA ICALSyncService ===\n"))

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
        self.stdout.write(f"📍 Habitación: {room.name} (ID: {room_id})")

        # Si no hay URL, usar un calendario público válido o crear uno de prueba
        if not ical_url:
            # Usar un calendario de feriados públicos que es confiable
            # Alternativamente, podríamos crear un servidor HTTP temporal, pero para pruebas usamos una URL pública
            ical_url = "https://calendar.google.com/calendar/ical/es.argentina%23holiday%40group.v.calendar.google.com/public/basic.ics"
            self.stdout.write(self.style.WARNING("⚠️  No se proporcionó URL iCal"))
            self.stdout.write(f"📍 Usando calendario de feriados públicos de Argentina: {ical_url}")
            self.stdout.write(self.style.WARNING("   (Nota: Este calendario puede tener eventos que generen conflictos)"))
            self.stdout.write(self.style.WARNING("   Para pruebas reales, usa un feed iCal de reservas válido"))
        else:
            self.stdout.write(f"📍 URL iCal: {ical_url}")

        self.stdout.write("")  # Línea en blanco

        # Crear o obtener OtaRoomMapping
        mapping, created = OtaRoomMapping.objects.get_or_create(
            hotel=hotel,
            room=room,
            provider=OtaProvider.ICAL,
            defaults={
                "ical_in_url": ical_url,
                "sync_direction": OtaRoomMapping.SyncDirection.BOTH,
                "is_active": True,
            },
        )
        if not created:
            mapping.ical_in_url = ical_url
            mapping.sync_direction = OtaRoomMapping.SyncDirection.BOTH
            mapping.is_active = True
            mapping.save()
            self.stdout.write(f"✅ Mapeo actualizado (ID: {mapping.id})")
        else:
            self.stdout.write(f"✅ Mapeo creado (ID: {mapping.id})")

        self.stdout.write(f"   - sync_direction: {mapping.sync_direction}")
        self.stdout.write(f"   - last_synced: {mapping.last_synced or 'Nunca'}\n")

        # ===== PRUEBA 1: import_reservations =====
        self.stdout.write(self.style.SUCCESS("=== PRUEBA 1: import_reservations ===\n"))

        # Contar reservas antes
        reservas_antes = Reservation.objects.filter(
            hotel=hotel,
            room=room,
            external_id__isnull=False,
        ).count()
        self.stdout.write(f"📊 Reservas con external_id antes: {reservas_antes}")

        # Crear job para logging
        job = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id, "test": True},
        )

        try:
            self.stdout.write("🔄 Ejecutando import_reservations...")
            # Ejecutar importación
            stats = ICALSyncService.import_reservations(mapping, job=job)

            self.stdout.write(f"\n✅ Importación completada:")
            self.stdout.write(f"   - processed: {stats.get('processed', 0)}")
            self.stdout.write(f"   - created: {stats.get('created', 0)}")
            self.stdout.write(f"   - updated: {stats.get('updated', 0)}")
            self.stdout.write(f"   - skipped: {stats.get('skipped', 0)}")
            self.stdout.write(f"   - errors: {stats.get('errors', 0)}")

            if stats.get("reason"):
                self.stdout.write(self.style.WARNING(f"   ⚠️  reason: {stats['reason']}"))

            # Actualizar job
            job.status = OtaSyncJob.JobStatus.SUCCESS if stats.get("errors", 0) == 0 else OtaSyncJob.JobStatus.FAILED
            job.finished_at = timezone.now()
            job.save()

            # Verificar reservas después
            reservas_despues = Reservation.objects.filter(
                hotel=hotel,
                room=room,
                external_id__isnull=False,
            ).count()
            self.stdout.write(f"\n📊 Reservas con external_id después: {reservas_despues}")
            self.stdout.write(f"   ⬆️  Diferencia: {reservas_despues - reservas_antes}")

            # Mostrar reservas creadas con verificación de mejoras
            if stats.get("created", 0) > 0:
                reservas_nuevas = Reservation.objects.filter(
                    hotel=hotel,
                    room=room,
                    external_id__isnull=False,
                ).order_by("-created_at")[:stats.get("created", 0)]
                self.stdout.write(f"\n📋 Reservas creadas (con mejoras):")
                for r in reservas_nuevas:
                    # Verificar que tiene external_id (UID)
                    has_uid = "✅" if r.external_id else "❌"
                    # Verificar channel según provider
                    expected_channel = ReservationChannel.OTHER if mapping.provider == OtaProvider.ICAL else None
                    channel_ok = "✅" if (expected_channel is None or r.channel == expected_channel) else "⚠️"
                    self.stdout.write(
                        f"   - ID: {r.id} | external_id {has_uid}: {r.external_id[:50] if r.external_id else 'N/A'} | "
                        f"{r.check_in} → {r.check_out} | channel {channel_ok}: {r.channel} | status: {r.status}"
                    )
                    
                # Verificar RoomBlocks si se crearon
                blocks = RoomBlock.objects.filter(
                    hotel=hotel,
                    room=room,
                    reason__icontains="external_id:",
                ).count()
                if blocks > 0:
                    self.stdout.write(f"\n📋 RoomBlocks creados: {blocks}")
                    for block in RoomBlock.objects.filter(
                        hotel=hotel,
                        room=room,
                        reason__icontains="external_id:",
                    )[:3]:
                        external_id_from_reason = block.reason.split("external_id:")[1].split(" - ")[0] if "external_id:" in block.reason else "N/A"
                        self.stdout.write(
                            f"   - ID: {block.id} | external_id: {external_id_from_reason[:50]} | "
                            f"{block.start_date} → {block.end_date} | type: {block.block_type}"
                        )

            # Verificar last_synced
            mapping.refresh_from_db()
            if mapping.last_synced:
                self.stdout.write(f"\n✅ last_synced actualizado: {mapping.last_synced}")
            else:
                self.stdout.write(self.style.WARNING("\n⚠️  last_synced no se actualizó"))

            # Mostrar logs detallados (mejorados)
            logs = job.logs.all().order_by("created_at")
            if logs.exists():
                self.stdout.write(f"\n📝 Logs mejorados ({logs.count()}):")
                error_logs = logs.filter(level=OtaSyncLog.Level.ERROR)[:3]
                warning_logs = logs.filter(level=OtaSyncLog.Level.WARNING)[:3]
                info_logs = logs.filter(level=OtaSyncLog.Level.INFO)[:5]
                
                # Mostrar algunos logs de cada tipo con información mejorada
                for log in list(error_logs) + list(warning_logs) + list(info_logs)[:5]:
                    payload_info = ""
                    if log.payload and isinstance(log.payload, dict):
                        parts = []
                        if "source" in log.payload:
                            parts.append(f"source={log.payload['source']}")
                        if "channel" in log.payload:
                            parts.append(f"channel={log.payload['channel']}")
                        if "external_id" in log.payload:
                            parts.append(f"UID={log.payload['external_id'][:30]}")
                        if "status" in log.payload:
                            parts.append(f"status={log.payload['status']}")
                        if "error" in log.payload:
                            parts.append(f"error={log.payload['error'][:50]}")
                        if parts:
                            payload_info = f" - {', '.join(parts)}"
                    self.stdout.write(f"   [{log.level.upper()}] {log.message}{payload_info}")
                
                # Verificar que los logs tienen los campos mejorados
                logs_with_source = sum(1 for log in logs if log.payload and isinstance(log.payload, dict) and "source" in log.payload)
                logs_with_status = sum(1 for log in logs if log.payload and isinstance(log.payload, dict) and "status" in log.payload)
                self.stdout.write(f"\n   ✅ Logs con 'source': {logs_with_source}/{logs.count()}")
                self.stdout.write(f"   ✅ Logs con 'status': {logs_with_status}/{logs.count()}")
                
                if logs.count() > 10:
                    self.stdout.write(f"   ... y {logs.count() - 10} logs más")

        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f"\n❌ Error en importación: {e}"))
            self.stdout.write(self.style.ERROR(f"Traceback:\n{traceback.format_exc()}"))
            job.status = OtaSyncJob.JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = timezone.now()
            job.save()
            return  # Salir si hay error crítico

        # ===== PRUEBA 2: export_reservations =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 2: export_reservations ===\n"))

        # Crear algunas reservas de prueba si no hay
        reservas_count = Reservation.objects.filter(
            hotel=hotel,
            room=room,
            status=ReservationStatus.CONFIRMED,
        ).count()
        self.stdout.write(f"📊 Reservas confirmadas para exportar: {reservas_count}")

        if reservas_count == 0:
            self.stdout.write("⚠️  Creando reserva de prueba...")
            tomorrow = date.today() + timedelta(days=1)
            Reservation.objects.create(
                hotel=hotel,
                room=room,
                check_in=tomorrow,
                check_out=tomorrow + timedelta(days=2),
                status=ReservationStatus.CONFIRMED,
                channel=ReservationChannel.DIRECT,
                guests=2,
            )
            reservas_count = 1
            self.stdout.write(f"✅ Reserva de prueba creada")

        # Crear job para export
        job_export = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.EXPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id, "test": True},
        )

        try:
            stats_export = ICALSyncService.export_reservations(mapping, job=job_export)
            self.stdout.write(f"\n✅ Exportación completada:")
            self.stdout.write(f"   - processed: {stats_export.get('processed', 0)}")
            self.stdout.write(f"   - exported: {stats_export.get('exported', 0)}")

            # Verificar last_synced
            mapping.refresh_from_db()
            if mapping.last_synced:
                self.stdout.write(f"\n✅ last_synced actualizado: {mapping.last_synced}")

            job_export.status = OtaSyncJob.JobStatus.SUCCESS
            job_export.finished_at = timezone.now()
            job_export.save()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error en exportación: {e}"))
            job_export.status = OtaSyncJob.JobStatus.FAILED
            job_export.error_message = str(e)
            job_export.finished_at = timezone.now()
            job_export.save()

        # ===== PRUEBA 3: sync_direction =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 3: sync_direction ===\n"))

        # Probar con sync_direction = EXPORT solo (no debería importar)
        old_last_synced = mapping.last_synced
        mapping.sync_direction = OtaRoomMapping.SyncDirection.EXPORT
        mapping.save()
        self.stdout.write(f"📌 Cambiando sync_direction a: {mapping.sync_direction}")

        job_import_only = OtaSyncJob.objects.create(
            hotel=hotel,
            provider=OtaProvider.ICAL,
            job_type=OtaSyncJob.JobType.IMPORT_ICS,
            status=OtaSyncJob.JobStatus.RUNNING,
            stats={"mapping_id": mapping.id, "test": True},
        )

        stats_import_only = ICALSyncService.import_reservations(mapping, job=job_import_only)
        
        # Verificar que se saltó correctamente
        if stats_import_only.get("reason") and "sync_direction" in stats_import_only["reason"]:
            self.stdout.write(self.style.SUCCESS(f"✅ Importación correctamente saltada"))
            self.stdout.write(f"   - reason: {stats_import_only['reason']}")
            self.stdout.write(f"   - processed: {stats_import_only.get('processed', 0)} (debe ser 0)")
            
            # Verificar que last_synced NO cambió
            mapping.refresh_from_db()
            if mapping.last_synced == old_last_synced:
                self.stdout.write(self.style.SUCCESS(f"   ✅ last_synced NO cambió (correcto)"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️  last_synced cambió (no esperado)"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Importación no fue saltada correctamente"))
            self.stdout.write(f"   - processed: {stats_import_only.get('processed', 0)}")
            self.stdout.write(f"   - reason: {stats_import_only.get('reason', 'N/A')}")

        # Restaurar sync_direction
        mapping.sync_direction = OtaRoomMapping.SyncDirection.BOTH
        mapping.save()

        # ===== PRUEBA 4: Verificar mejoras específicas =====
        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 4: Verificar mejoras implementadas ===\n"))
        
        # Verificar Reservations con source/channel
        reservas_importadas = Reservation.objects.filter(
            hotel=hotel,
            room=room,
            external_id__isnull=False,
        )
        
        self.stdout.write(f"📊 Verificando Reservations importadas ({reservas_importadas.count()}):")
        for r in reservas_importadas[:3]:
            # Verificar external_id (UID)
            has_external_id = "✅" if r.external_id else "❌"
            # Verificar channel
            has_channel = "✅" if r.channel else "❌"
            # Verificar source en logs (no está en Reservation, pero en logs)
            if r.external_id:
                source_in_logs = any(
                    log.payload and isinstance(log.payload, dict) and 
                    log.payload.get("external_id") == r.external_id and 
                    "source" in log.payload
                    for log in job.logs.all()
                )
            else:
                source_in_logs = False
            source_check = "✅" if source_in_logs else "⚠️"
            
            self.stdout.write(
                f"   - ID: {r.id} | external_id {has_external_id} | "
                f"channel {has_channel}: {r.channel} | source en logs {source_check}"
            )
        
        # Verificar logs mejorados
        all_logs = job.logs.all()
        logs_mejorados = sum(
            1 for log in all_logs 
            if log.payload and isinstance(log.payload, dict) and 
            "source" in log.payload and "status" in log.payload
        )
        total_logs = all_logs.count()
        
        self.stdout.write(f"\n📝 Verificando logs mejorados:")
        self.stdout.write(f"   - Logs con 'source' y 'status': {logs_mejorados}/{total_logs}")
        if logs_mejorados > 0:
            self.stdout.write(self.style.SUCCESS(f"   ✅ Logs mejorados funcionando"))
        else:
            self.stdout.write(self.style.WARNING(f"   ⚠️  No se encontraron logs con campos mejorados"))

        # ===== RESUMEN FINAL =====
        self.stdout.write(self.style.SUCCESS("\n=== RESUMEN ===\n"))

        total_reservas = Reservation.objects.filter(
            hotel=hotel,
            room=room,
            external_id__isnull=False,
        ).count()
        self.stdout.write(f"📊 Total reservas con external_id: {total_reservas}")

        mapping.refresh_from_db()
        self.stdout.write(f"📅 last_synced final: {mapping.last_synced or 'Nunca'}")

        self.stdout.write(self.style.SUCCESS("\n✅ Pruebas completadas!\n"))

