"""
Servicios para la generación automática de tareas de housekeeping.
"""
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from datetime import date

from apps.housekeeping.models import (
    HousekeepingTask,
    HousekeepingConfig,
    TaskTemplate,
    Checklist,
    TaskChecklistCompletion,
    TaskType,
    TaskStatus,
)
from apps.rooms.models import Room, CleaningStatus

logger = logging.getLogger(__name__)


class TaskGeneratorService:
    """
    Servicio para generar tareas de housekeeping automáticamente.
    """

    @staticmethod
    def find_relevant_checklist(hotel, room_type: Optional[str], task_type: str) -> Optional[Checklist]:
        """
        Encuentra el checklist más relevante para una habitación y tipo de tarea.
        
        Prioridad:
        1. Checklist específico para room_type y task_type
        2. Checklist específico para task_type (sin room_type)
        3. Checklist por defecto del hotel
        """
        try:
            # 1. Buscar checklist específico para room_type y task_type
            if room_type:
                checklist = Checklist.objects.filter(
                    hotel=hotel,
                    room_type=room_type,
                    task_type=task_type,
                    is_active=True
                ).first()
                if checklist:
                    return checklist

            # 2. Buscar checklist específico para task_type (sin room_type)
            checklist = Checklist.objects.filter(
                hotel=hotel,
                room_type__isnull=True,
                task_type=task_type,
                is_active=True
            ).first()
            if checklist:
                return checklist

            # 3. Buscar checklist por defecto del hotel
            checklist = Checklist.objects.filter(
                hotel=hotel,
                is_default=True,
                is_active=True
            ).first()
            if checklist:
                return checklist

            return None
        except Exception as e:
            logger.error(f"Error buscando checklist relevante para hotel {hotel.id}, room_type {room_type}, task_type {task_type}: {e}")
            return None

    @staticmethod
    def get_config_priority(hotel, task_type: str) -> int:
        """
        Obtiene la prioridad configurada para un tipo de tarea.
        """
        try:
            config = getattr(hotel, 'housekeeping_config', None)
            if not config:
                # Crear configuración por defecto si no existe
                config = HousekeepingConfig.objects.create(hotel=hotel)
            
            if task_type == TaskType.CHECKOUT:
                return config.checkout_priority
            elif task_type == TaskType.DAILY:
                return config.daily_priority
            else:
                return 0
        except Exception as e:
            logger.error(f"Error obteniendo prioridad para hotel {hotel.id}, task_type {task_type}: {e}")
            return 0

    @staticmethod
    def get_room_zone(room: Room) -> Optional[str]:
        """
        Obtiene la zona de limpieza de una habitación si está asignada.
        Por ahora, usa el piso de la habitación como zona.
        """
        try:
            # Si la habitación tiene piso, usar el piso como zona
            if room.floor:
                return f"Piso {room.floor}"
            
            return None
        except Exception as e:
            logger.error(f"Error obteniendo zona para habitación {room.id}: {e}")
            return None

    @staticmethod
    def get_current_shift(hotel, config) -> Optional[str]:
        """
        Determina el turno actual basado en la hora y las ventanas de tiempo configuradas.
        
        Returns:
            'morning', 'afternoon', 'night', o None
        """
        try:
            from zoneinfo import ZoneInfo
            from apps.housekeeping.models import Shift
            
            # Obtener hora actual en la zona horaria del hotel
            hotel_tz = None
            if hotel.timezone:
                try:
                    hotel_tz = ZoneInfo(hotel.timezone)
                except Exception:
                    pass
            
            if hotel_tz:
                aware_now = timezone.now()
                local_now = timezone.localtime(aware_now, hotel_tz)
                current_time = local_now.time()
            else:
                current_time = timezone.now().time()
            
            # Verificar ventanas de tiempo
            morning_start = config.morning_window_start
            morning_end = config.morning_window_end
            afternoon_start = config.afternoon_window_start
            afternoon_end = config.afternoon_window_end
            
            if morning_start and morning_end:
                if morning_start <= current_time <= morning_end:
                    return Shift.MORNING
            
            if afternoon_start and afternoon_end:
                if afternoon_start <= current_time <= afternoon_end:
                    return Shift.AFTERNOON
            
            # Si no está en ninguna ventana, es turno noche
            return Shift.NIGHT
            
        except Exception as e:
            logger.error(f"Error determinando turno actual para hotel {hotel.id}: {e}")
            return None

    @staticmethod
    def is_staff_available_now(staff, hotel, current_time) -> bool:
        """
        Verifica si el personal está disponible en este momento según sus horarios de trabajo.
        
        Args:
            staff: Instancia de CleaningStaff
            hotel: Instancia del hotel (para zona horaria)
            current_time: Hora actual (time object)
        
        Returns:
            True si el personal está en su horario de trabajo, False en caso contrario
        """
        try:
            # Si no tiene horarios configurados, considerar disponible
            if not staff.work_start_time or not staff.work_end_time:
                return True
            
            # Verificar si la hora actual está dentro del horario de trabajo
            start_time = staff.work_start_time
            end_time = staff.work_end_time
            
            # Manejar turnos que cruzan medianoche (ej: 22:00 - 06:00)
            if start_time > end_time:
                # Turno nocturno que cruza medianoche
                return current_time >= start_time or current_time <= end_time
            else:
                # Turno normal
                return start_time <= current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error verificando disponibilidad de personal {staff.id}: {e}")
            return True  # En caso de error, considerar disponible

    @staticmethod
    def find_best_staff(
        hotel,
        room: Room,
        task_type: str,
        config,
        current_shift: Optional[str] = None
    ) -> Optional['CleaningStaff']:
        """
        Encuentra el mejor personal para asignar a una tarea.
        
        Criterios (en orden de prioridad):
        1. Disponibilidad horaria (si tiene work_start_time/work_end_time configurados)
        2. Zona de limpieza (si prefer_by_zone=True)
        3. Turno actual (shift)
        4. Carga de trabajo (menos tareas pendientes)
        5. Disponibilidad (is_active=True)
        """
        try:
            from apps.housekeeping.models import CleaningStaff, TaskStatus
            from django.db.models import Count, Q
            from zoneinfo import ZoneInfo
            
            # Obtener hora actual en la zona horaria del hotel
            hotel_tz = None
            if hotel.timezone:
                try:
                    hotel_tz = ZoneInfo(hotel.timezone)
                except Exception:
                    pass
            
            if hotel_tz:
                aware_now = timezone.now()
                local_now = timezone.localtime(aware_now, hotel_tz)
                current_time = local_now.time()
            else:
                current_time = timezone.now().time()
            
            # Obtener zona de la habitación
            room_zone = TaskGeneratorService.get_room_zone(room)
            
            # Base queryset: solo personal activo del hotel
            staff_qs = CleaningStaff.objects.filter(
                hotel=hotel,
                is_active=True
            )
            
            if not staff_qs.exists():
                logger.warning(f"No hay personal de limpieza activo para hotel {hotel.id}")
                return None
            
            # Anotar carga de trabajo (tareas pendientes + en progreso)
            staff_qs = staff_qs.annotate(
                pending_tasks_count=Count(
                    'tasks',
                    filter=Q(tasks__status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            )
            
            # Criterio 1: Disponibilidad horaria (filtrar personal disponible ahora)
            available_staff = []
            for staff in staff_qs:
                if TaskGeneratorService.is_staff_available_now(staff, hotel, current_time):
                    available_staff.append(staff.id)
            
            if available_staff:
                staff_qs = staff_qs.filter(id__in=available_staff)
            # Si nadie tiene horarios configurados, continuar con todos
            
            # Criterio 2: Zona de limpieza (si está habilitado)
            if config.prefer_by_zone and room_zone:
                # Buscar personal asignado a zonas que coincidan con la zona de la habitación
                zone_staff = staff_qs.filter(
                    Q(zone=room_zone) | 
                    Q(cleaning_zones__name__icontains=room_zone.split()[0] if room_zone else '')
                ).distinct()
                
                if zone_staff.exists():
                    staff_qs = zone_staff
            
            # Criterio 3: Turno actual (shift) - solo si no se usaron horarios específicos
            if current_shift and not available_staff:
                shift_staff = staff_qs.filter(shift=current_shift)
                if shift_staff.exists():
                    staff_qs = shift_staff
            
            # Criterio 4: Seleccionar el que tenga menos carga de trabajo
            best_staff = staff_qs.order_by('pending_tasks_count', 'id').first()
            
            if best_staff:
                logger.debug(
                    f"Personal asignado: {best_staff} "
                    f"(carga: {best_staff.pending_tasks_count}, turno: {best_staff.shift}, "
                    f"horario: {best_staff.work_start_time}-{best_staff.work_end_time}, zona: {room_zone})"
                )
            
            return best_staff
            
        except Exception as e:
            logger.error(f"Error encontrando mejor personal para habitación {room.id}: {e}", exc_info=True)
            return None

    @classmethod
    def create_task(
        cls,
        hotel,
        room: Room,
        task_type: str,
        created_by=None,
        skip_if_exists: bool = True,
        use_template: bool = True,
        use_checklist: bool = True,
        auto_assign_staff: bool = True,
    ) -> Optional[HousekeepingTask]:
        """
        Crea una tarea de housekeeping para una habitación.
        
        Args:
            hotel: Instancia del hotel
            room: Instancia de la habitación
            task_type: Tipo de tarea (TaskType.CHECKOUT, TaskType.DAILY, etc.)
            created_by: Usuario que crea la tarea (opcional)
            skip_if_exists: Si True, no crea la tarea si ya existe una del mismo tipo hoy
            use_template: Si True, usa información de TaskTemplate para notas
            use_checklist: Si True, asigna checklist relevante automáticamente
        
        Returns:
            HousekeepingTask creada o None si no se pudo crear
        """
        try:
            # Verificar si ya existe una tarea del mismo tipo hoy
            if skip_if_exists:
                today = date.today()
                existing = HousekeepingTask.objects.filter(
                    hotel=hotel,
                    room=room,
                    task_type=task_type,
                    created_at__date=today,
                ).exclude(status=TaskStatus.CANCELLED).exists()
                
                if existing:
                    logger.info(f"Ya existe una tarea {task_type} para habitación {room.id} hoy")
                    return None

            # Obtener configuración
            config = getattr(hotel, 'housekeeping_config', None)
            if not config:
                config = HousekeepingConfig.objects.create(hotel=hotel)

            # Obtener prioridad
            priority = cls.get_config_priority(hotel, task_type)

            # Obtener zona
            zone = cls.get_room_zone(room)

            # Obtener notas de plantilla y calcular duración estimada
            notes = None
            estimated_minutes = None
            if use_template:
                templates = TaskTemplate.objects.filter(
                    hotel=hotel,
                    room_type=room.room_type,
                    task_type=task_type,
                    is_active=True
                ).order_by('order')
                
                if templates.exists():
                    template_names = [t.name for t in templates]
                    notes = f"Tareas según plantilla: {', '.join(template_names)}"
                    # Calcular duración total sumando las duraciones de los templates
                    estimated_minutes = sum(t.estimated_minutes for t in templates)
            
            # Si no se calculó desde templates, usar duración por defecto de la configuración
            if estimated_minutes is None:
                # Intentar obtener desde config.durations (JSON)
                if hasattr(config, 'durations') and isinstance(config.durations, dict):
                    duration_key = f"{task_type}_{room.room_type}"
                    estimated_minutes = config.durations.get(duration_key)
                
                # Si aún no hay, usar valores por defecto según tipo de tarea
                if estimated_minutes is None:
                    default_durations = {
                        TaskType.CHECKOUT: 60,  # 1 hora para checkout
                        TaskType.DAILY: 30,     # 30 minutos para diaria
                        TaskType.MAINTENANCE: 120,  # 2 horas para mantenimiento
                    }
                    estimated_minutes = default_durations.get(task_type, 60)

            # Obtener checklist relevante si está habilitado
            checklist = None
            if use_checklist:
                checklist = cls.find_relevant_checklist(
                    hotel=hotel,
                    room_type=room.room_type,
                    task_type=task_type
                )

            # Asignar personal automáticamente si está habilitado
            assigned_staff = None
            if auto_assign_staff and config.enable_auto_assign:
                current_shift = cls.get_current_shift(hotel, config)
                assigned_staff = cls.find_best_staff(
                    hotel=hotel,
                    room=room,
                    task_type=task_type,
                    config=config,
                    current_shift=current_shift
                )

            # Crear la tarea
            task = HousekeepingTask.objects.create(
                hotel=hotel,
                room=room,
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                zone=zone,
                notes=notes,
                checklist=checklist,
                assigned_to=assigned_staff,
                created_by=created_by,
                estimated_minutes=estimated_minutes,
            )

            # Si hay checklist, inicializar los completions
            if checklist:
                checklist_items = checklist.items.filter(is_active=True)
                for item in checklist_items:
                    TaskChecklistCompletion.objects.get_or_create(
                        task=task,
                        checklist_item=item,
                        defaults={'completed': False}
                    )

            # Crear notificación para el personal asignado o usuarios con permisos de housekeeping
            if assigned_staff:
                try:
                    from apps.notifications.services import NotificationService
                    from apps.notifications.models import NotificationType
                    from apps.users.models import UserProfile
                    from django.contrib.auth.models import User
                    
                    # Obtener nombre del personal
                    staff_name = f"{assigned_staff.first_name} {assigned_staff.last_name or ''}".strip() or "Personal de limpieza"
                    
                    # Obtener usuario del sistema si existe
                    user_id = None
                    if assigned_staff.user:
                        user_id = assigned_staff.user.id
                        # Crear notificación para el usuario específico
                        NotificationService.create_housekeeping_task_notification(
                            task_type=task_type,
                            room_name=room.name or f"Habitación {room.id}",
                            staff_name=staff_name,
                            hotel_id=hotel.id,
                            user_id=user_id,
                            task_id=task.id
                        )
                    else:
                        # Si no tiene usuario asociado, crear notificaciones para usuarios con permisos de housekeeping del hotel
                        # Buscar usuarios que tengan acceso al hotel y permisos de housekeeping
                        from django.contrib.auth.models import Permission
                        from django.contrib.contenttypes.models import ContentType
                        
                        # Obtener el permiso de housekeeping
                        try:
                            hk_content_type = ContentType.objects.get(app_label='housekeeping', model='housekeepingtask')
                            hk_permission = Permission.objects.get(
                                codename='access_housekeeping',
                                content_type=hk_content_type
                            )
                            
                            # Buscar usuarios con el permiso (a través de grupos o directamente)
                            housekeeping_users = User.objects.filter(
                                Q(is_superuser=True) |
                                Q(groups__permissions=hk_permission) |
                                Q(user_permissions=hk_permission) |
                                Q(profile__is_housekeeping_staff=True)
                            ).filter(
                                Q(profile__hotels=hotel) | Q(is_superuser=True)
                            ).distinct()
                        except (Permission.DoesNotExist, ContentType.DoesNotExist):
                            # Si no existe el permiso, buscar solo por is_housekeeping_staff
                            housekeeping_users = User.objects.filter(
                                Q(is_superuser=True) |
                                Q(profile__is_housekeeping_staff=True)
                            ).filter(
                                Q(profile__hotels=hotel) | Q(is_superuser=True)
                            ).distinct()
                        
                        if housekeeping_users.exists():
                            # Crear notificación para cada usuario con permisos
                            for user in housekeeping_users:
                                NotificationService.create_housekeeping_task_notification(
                                    task_type=task_type,
                                    room_name=room.name or f"Habitación {room.id}",
                                    staff_name=staff_name,
                                    hotel_id=hotel.id,
                                    user_id=user.id,
                                    task_id=task.id
                                )
                        else:
                            # Si no hay usuarios específicos, crear notificación general (sin user_id)
                            NotificationService.create_housekeeping_task_notification(
                                task_type=task_type,
                                room_name=room.name or f"Habitación {room.id}",
                                staff_name=staff_name,
                                hotel_id=hotel.id,
                                user_id=None,
                                task_id=task.id
                            )
                except Exception as notif_error:
                    # No fallar la creación de tarea si la notificación falla
                    logger.warning(f"Error creando notificación para tarea {task.id}: {notif_error}")

            logger.info(f"Tarea {task_type} creada para habitación {room.id} (ID: {task.id})")
            return task

        except Exception as e:
            logger.error(f"Error creando tarea {task_type} para habitación {room.id}: {e}", exc_info=True)
            return None

    @classmethod
    def create_daily_tasks_for_hotel(cls, hotel, target_date: Optional[date] = None) -> dict:
        """
        Crea tareas diarias para todas las habitaciones ocupadas de un hotel.
        
        Args:
            hotel: Instancia del hotel
            target_date: Fecha objetivo (por defecto hoy)
        
        Returns:
            Dict con estadísticas de creación
        """
        if target_date is None:
            target_date = date.today()

        stats = {
            'total_rooms': 0,
            'tasks_created': 0,
            'tasks_skipped': 0,
            'errors': 0,
        }

        try:
            config = getattr(hotel, 'housekeeping_config', None)
            if not config:
                logger.warning(f"No hay configuración de housekeeping para hotel {hotel.id}")
                return stats

            # Verificar si está habilitada la generación automática
            if not config.create_daily_tasks:
                logger.info(f"Generación automática de tareas diarias deshabilitada para hotel {hotel.id}")
                return stats

            # Obtener habitaciones ocupadas
            from apps.rooms.models import RoomStatus
            occupied_rooms = Room.objects.filter(
                hotel=hotel,
                status=RoomStatus.OCCUPIED
            ).select_related('hotel')

            stats['total_rooms'] = occupied_rooms.count()

            # Verificar reglas de servicio
            skip_on_checkin = config.skip_service_on_checkin
            skip_on_checkout = config.skip_service_on_checkout

            for room in occupied_rooms:
                try:
                    # Verificar si debe saltarse el servicio
                    should_skip = False
                    
                    if skip_on_checkin or skip_on_checkout:
                        from apps.reservations.models import Reservation, ReservationStatus
                        today_reservations = Reservation.objects.filter(
                            room=room,
                            hotel=hotel,
                            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                        )
                        
                        for res in today_reservations:
                            if skip_on_checkin and res.check_in == target_date:
                                should_skip = True
                                break
                            if skip_on_checkout and res.check_out == target_date:
                                should_skip = True
                                break
                    
                    if should_skip:
                        stats['tasks_skipped'] += 1
                        continue

                    # Crear tarea diaria
                    task = cls.create_task(
                        hotel=hotel,
                        room=room,
                        task_type=TaskType.DAILY,
                        skip_if_exists=True,
                        use_template=True,
                        use_checklist=True,
                    )

                    if task:
                        stats['tasks_created'] += 1
                    else:
                        stats['tasks_skipped'] += 1

                except Exception as e:
                    logger.error(f"Error creando tarea diaria para habitación {room.id}: {e}", exc_info=True)
                    stats['errors'] += 1

            logger.info(
                f"Generación de tareas diarias para hotel {hotel.id}: "
                f"{stats['tasks_created']} creadas, {stats['tasks_skipped']} omitidas, {stats['errors']} errores"
            )

        except Exception as e:
            logger.error(f"Error en generación de tareas diarias para hotel {hotel.id}: {e}", exc_info=True)
            stats['errors'] += 1

        return stats

