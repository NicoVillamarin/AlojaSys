"""
Script de prueba para endpoints REST del módulo OTA.

Prueba todos los endpoints:
- GET /api/otas/
- POST /api/otas/sync/
- GET /api/otas/mappings/
- POST /api/otas/mappings/
- GET /api/otas/logs/
"""
from django.core.management.base import BaseCommand
from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json

from apps.core.models import Hotel
from apps.rooms.models import Room
from apps.otas.models import OtaConfig, OtaRoomMapping, OtaProvider

User = get_user_model()


class Command(BaseCommand):
    help = "Prueba endpoints REST del módulo OTA"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hotel-id",
            type=int,
            default=1,
            help="ID del hotel para las pruebas",
        )
        parser.add_argument(
            "--room-id",
            type=int,
            default=1,
            help="ID de la habitación para las pruebas",
        )

    def handle(self, *args, **options):
        hotel_id = options.get("hotel_id")
        room_id = options.get("room_id")

        self.stdout.write(self.style.SUCCESS("\n=== PRUEBA ENDPOINTS REST OTA ===\n"))

        # Obtener hotel y habitación
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            room = Room.objects.get(id=room_id)
            self.stdout.write(f"📍 Hotel: {hotel.name} (ID: {hotel_id})")
            self.stdout.write(f"📍 Habitación: {room.name} (ID: {room_id})\n")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            return

        # Crear o obtener usuario para autenticación
        user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com', 'is_staff': True}
        )
        if not user.password:
            user.set_password('testpass123')
            user.save()

        # Crear cliente de prueba de DRF con override de ALLOWED_HOSTS
        with override_settings(ALLOWED_HOSTS=['*']):
            client = APIClient()
            client.force_authenticate(user=user)  # Autenticar el cliente
            
            def get_results(data):
                """Extrae resultados de respuesta paginada o lista directa."""
                if isinstance(data, dict) and 'results' in data:
                    return data['results']
                elif isinstance(data, list):
                    return data
                else:
                    return []

            # ===== PRUEBA 1: GET /api/otas/ =====
            self.stdout.write(self.style.SUCCESS("=== PRUEBA 1: GET /api/otas/ ===\n"))

            response = client.get("/api/otas/")
            self.stdout.write(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"✅ Endpoint funcionando - {count} canales encontrados")
                if results:
                    for config in results[:3]:  # Mostrar solo los primeros 3
                        self.stdout.write(f"   - ID: {config.get('id')} | Provider: {config.get('provider')} | Hotel: {config.get('hotel_name')}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {response.content.decode()[:200]}"))

            # Probar con filtros
            self.stdout.write("\n📋 Probando filtros:")
            response = client.get("/api/otas/?provider=ical")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"   - Filtro provider=ical: {count} resultados")

            response = client.get("/api/otas/?is_active=true")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"   - Filtro is_active=true: {count} resultados")

            # ===== PRUEBA 2: GET /api/otas/mappings/ =====
            self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 2: GET /api/otas/mappings/ ===\n"))

            response = client.get("/api/otas/mappings/")
            self.stdout.write(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"✅ Endpoint funcionando - {count} mapeos encontrados")
                if results:
                    for mapping in results[:3]:  # Mostrar solo los primeros 3
                        self.stdout.write(
                            f"   - ID: {mapping.get('id')} | Room: {mapping.get('room_name')} | "
                            f"Provider: {mapping.get('provider')} | Sync: {mapping.get('sync_direction')}"
                        )
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {response.content.decode()[:200]}"))

            # ===== PRUEBA 3: POST /api/otas/mappings/ =====
            self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 3: POST /api/otas/mappings/ ===\n"))

            # Verificar si ya existe un mapeo para esta room+provider
            existing = OtaRoomMapping.objects.filter(room_id=room_id, provider=OtaProvider.ICAL, is_active=True).first()
            if existing:
                self.stdout.write(f"⚠️  Ya existe un mapeo activo (ID: {existing.id}) - probando actualización...")
                mapping_data = {
                    "hotel": hotel_id,
                    "room": room_id,
                    "provider": OtaProvider.ICAL,
                    "external_id": "test-external-123",
                    "ical_in_url": "https://httpbin.org/get",
                    "sync_direction": "both",
                    "is_active": True,
                }
                response = client.put(
                    f"/api/otas/mappings/{existing.id}/",
                    json.dumps(mapping_data),
                    content_type="application/json"
                )
                self.stdout.write(f"Status PUT: {response.status_code}")
                if response.status_code in [200, 201]:
                    data = json.loads(response.content)
                    self.stdout.write(f"✅ Mapeo actualizado - ID: {data.get('id')}")
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Respuesta: {response.content.decode()[:200]}"))
            else:
                # Crear nuevo mapeo
                mapping_data = {
                    "hotel": hotel_id,
                    "room": room_id,
                    "provider": OtaProvider.ICAL,
                    "external_id": "test-external-123",
                    "ical_in_url": "https://httpbin.org/get",
                    "sync_direction": "both",
                    "is_active": True,
                }
                response = client.post(
                    "/api/otas/mappings/",
                    json.dumps(mapping_data),
                    content_type="application/json"
                )
                self.stdout.write(f"Status POST: {response.status_code}")
                if response.status_code == 201:
                    data = json.loads(response.content)
                    self.stdout.write(f"✅ Mapeo creado - ID: {data.get('id')}")
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Respuesta: {response.content.decode()[:200]}"))

            # Probar duplicado (debe fallar)
            self.stdout.write("\n📋 Probando validación de duplicados...")
            response = client.post(
                "/api/otas/mappings/",
                json.dumps(mapping_data),
                content_type="application/json"
            )
            if response.status_code == 400:
                self.stdout.write(self.style.SUCCESS("✅ Validación de duplicados funcionando (rechazó duplicado)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Status inesperado: {response.status_code}"))

            # ===== PRUEBA 4: GET /api/otas/logs/ =====
            self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 4: GET /api/otas/logs/ ===\n"))

            response = client.get("/api/otas/logs/")
            self.stdout.write(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"✅ Endpoint funcionando - {count} logs encontrados")
                if results:
                    for log in results[:3]:  # Mostrar solo los primeros 3
                        self.stdout.write(
                            f"   - [{log.get('level', '').upper()}] {log.get('message', '')[:50]}... "
                            f"(Job: {log.get('job')})"
                        )
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {response.content.decode()[:200]}"))

            # Probar con filtros
            self.stdout.write("\n📋 Probando filtros:")
            response = client.get(f"/api/otas/logs/?hotel={hotel_id}")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"   - Filtro hotel={hotel_id}: {count} resultados")

            response = client.get("/api/otas/logs/?level=error")
            if response.status_code == 200:
                data = json.loads(response.content)
                results = get_results(data)
                count = len(results) if isinstance(data, list) else data.get('count', len(results))
                self.stdout.write(f"   - Filtro level=error: {count} resultados")

            # ===== PRUEBA 5: POST /api/otas/sync/ =====
            self.stdout.write(self.style.SUCCESS("\n=== PRUEBA 5: POST /api/otas/sync/ ===\n"))

            # Sincronización sin parámetros (todos los mapeos)
            sync_data = {}
            response = client.post(
                "/api/otas/sync/",
                json.dumps(sync_data),
                content_type="application/json"
            )
            self.stdout.write(f"Status (sin params): {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(f"✅ Endpoint funcionando")
                self.stdout.write(f"   - Status: {data.get('status')}")
                self.stdout.write(f"   - Message: {data.get('message')}")
                if data.get('stats'):
                    stats = data['stats']
                    self.stdout.write(f"   - Stats: {stats}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {response.content.decode()[:200]}"))

            # Sincronización con provider específico
            self.stdout.write("\n📋 Probando sync con provider específico...")
            sync_data = {"provider": "ical"}
            response = client.post(
                "/api/otas/sync/",
                json.dumps(sync_data),
                content_type="application/json"
            )
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(f"✅ Sync con provider=ical: {data.get('status')}")

            # Sincronización con hotel específico
            self.stdout.write("\n📋 Probando sync con hotel específico...")
            sync_data = {"hotel_id": hotel_id}
            response = client.post(
                "/api/otas/sync/",
                json.dumps(sync_data),
                content_type="application/json"
            )
            if response.status_code == 200:
                data = json.loads(response.content)
                self.stdout.write(f"✅ Sync con hotel_id={hotel_id}: {data.get('status')}")

            # ===== RESUMEN =====
            self.stdout.write(self.style.SUCCESS("\n=== RESUMEN ===\n"))
            self.stdout.write("✅ Todas las pruebas completadas")
            self.stdout.write("\nEndpoints probados:")
            self.stdout.write("  ✓ GET /api/otas/ - Lista canales OTA con filtros")
            self.stdout.write("  ✓ GET /api/otas/mappings/ - Lista mapeos")
            self.stdout.write("  ✓ POST /api/otas/mappings/ - Crea/actualiza mapeos con validación")
            self.stdout.write("  ✓ GET /api/otas/logs/ - Lista logs con filtros")
            self.stdout.write("  ✓ POST /api/otas/sync/ - Sincronización manual\n")
