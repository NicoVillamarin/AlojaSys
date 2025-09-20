# AlojaSys
Sistema de gestión hotelera (PMS + APIs) pensado para escalar por módulos y múltiples hoteles.

## Stack
- Backend: Django 4 + Django REST Framework, PostgreSQL, Redis, Celery
- Frontend: React (Vite), TailwindCSS, TanStack Query
- DevOps: Docker Compose

## Funcionalidades actuales
- Hoteles (multi-hotel):
  - Modelo `Hotel` con `city`, `timezone`, `check_in_time`, `check_out_time`
  - API CRUD `/api/hotels/`
  - Resumen operativo: `/api/status/summary/?hotel=<id>`
- Ubicaciones:
  - `Country`, `State`, `City` (FKs encadenadas)
  - API: `/api/countries/`, `/api/states/?country=`, `/api/cities/?state=`
- Habitaciones (Rooms):
  - Modelo `Room` con FK a `Hotel`, `room_type`, `capacity`, `base_price`, `status` operativo
  - API CRUD `/api/rooms/`
  - Enriquecido con:
    - `current_reservation` (reserva activa hoy)
    - `future_reservations` (reservas con `check_out > hoy`)
- Reservas (Reservations):
  - Validación de solapamientos por room + hotel
  - Cálculo de noches/`total_price`
  - Acciones operativas:
    - `POST /api/reservations/{id}/check_in/`
    - `POST /api/reservations/{id}/check_out/`
    - `POST /api/reservations/{id}/cancel/`
  - Auto check-in al crear/editar si `status=confirmed` y hoy ∈ [check_in, check_out)
- Bloqueos de habitación (operativos):
  - `RoomBlock` (maintenance/hold/out_of_service) con rango de fechas
- Disponibilidad (por fechas):
  - `GET /api/reservations/availability/?hotel=<id>&start=YYYY-MM-DD&end=YYYY-MM-DD`
  - Excluye reservas activas y bloqueos solapados (y rooms out_of_service)
- Autenticación (dev):
  - Login de DRF: `/api/auth/login/`

## Automatización (Celery)
- Worker y Beat levantados con Docker
- Tarea diaria: `sync_room_occupancy_for_today`
  - Marca `occupied` cuando corresponde y libera rooms en check-out
  - Próximo: respetar `check_in_time`/`check_out_time` del hotel (scheduler listo)

## Endpoints principales
- API Root (router unificado): `/api/`
  - `hotels`, `rooms`, `reservations`, `countries`, `states`, `cities`
- Rutas especiales (fuera de router):
  - Resumen hotel: `/api/status/summary/?hotel=<id>`
  - Disponibilidad: `/api/reservations/availability/?hotel=<id>&start=YYYY-MM-DD&end=YYYY-MM-DD`

## Levantar el proyecto
Requisitos: Docker Desktop.

1. Variables de entorno (crear un `.env` en la raíz)
```
DB_NAME=hotel
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend
REDIS_URL=redis://redis:6379/0
```

2. Build & Up
```
docker compose up -d --build
```

3. URLs
- Backend: `http://localhost:8000/`
- API Root: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`
- Frontend (dev): `http://localhost:5173/`

4. Celery (logs)
```
docker compose logs -f celery
docker compose logs -f celery_beat
```

## Desarrollo
- Migraciones
```
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```
- Superusuario
```
docker compose exec backend python manage.py createsuperuser
```
- Seed rápido (ejemplo desde shell) – crear ciudad y asignarla al hotel por defecto
```
docker compose exec backend python manage.py shell
```
```python
from apps.locations.models import Country, State, City
from apps.core.models import Hotel
ar,_=Country.objects.get_or_create(code2="AR",code3="ARG",name="Argentina")
ba,_=State.objects.get_or_create(country=ar,name="Buenos Aires")
caba,_=City.objects.get_or_create(state=ba,name="CABA")
Hotel.objects.filter(city__isnull=True).update(city=caba)
exit()
```

## Estructura (resumen)
```
backend/
  apps/
    core/          # Hotel + status summary
    rooms/         # Rooms + serializers enriquecidos
    reservations/  # Reservations + acciones + disponibilidad + RoomBlock + tasks Celery
    locations/     # Country/State/City
  hotel/           # config Django + celery app
frontend/          # React (Vite)
```

## Decisiones de diseño
- Separación “operativo actual” (Room.status) vs “disponibilidad futura” (reservas/bloqueos)
- Multi-hotel desde el inicio (FKs y filtros por hotel)
- Automatización con Celery + Redis (worker y beat en Docker)
- Endpoints REST claros y navegables, con filtros básicos

## Próximos pasos sugeridos
- Respetar `check_in_time`/`check_out_time` por hotel en el auto check-in/out
- JWT y roles (admin/recepción)
- Reportes y dashboard extendidos
- Notificaciones (email/WhatsApp) y multi-idioma