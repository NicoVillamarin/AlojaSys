import logging
from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.models import Hotel
from apps.housekeeping.models import HousekeepingTask, TaskStatus, HousekeepingConfig
from apps.housekeeping.services import TaskGeneratorService

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_tasks():
    """
    Tarea Celery principal para generación automática de tareas diarias de housekeeping.

    - Recorre todos los hoteles activos.
    - Respeta la configuración `HousekeepingConfig.create_daily_tasks`.
    - Usa `TaskGeneratorService.create_daily_tasks_for_hotel`, que ya evita duplicados
      vía `skip_if_exists`, por lo que puede ejecutarse múltiples veces al día sin problemas.
    """
    logger.info("Iniciando generación automática de tareas diarias de housekeeping para todos los hoteles...")

    today = date.today()
    total_stats = {
        "hotels_processed": 0,
        "tasks_created": 0,
        "tasks_skipped": 0,
        "errors": 0,
    }

    hotels = Hotel.objects.filter(is_active=True)

    for hotel in hotels:
        try:
            config = getattr(hotel, "housekeeping_config", None)
            if not config:
                logger.info(f"Hotel {hotel.id} no tiene configuración de housekeeping, se omite.")
                continue

            if not config.create_daily_tasks:
                logger.info(f"Generación automática deshabilitada para hotel {hotel.id}, se omite.")
                continue

            stats = TaskGeneratorService.create_daily_tasks_for_hotel(hotel, target_date=today)

            total_stats["hotels_processed"] += 1
            total_stats["tasks_created"] += stats.get("tasks_created", 0)
            total_stats["tasks_skipped"] += stats.get("tasks_skipped", 0)
            total_stats["errors"] += stats.get("errors", 0)

        except Exception as e:
            logger.error(f"Error generando tareas diarias para hotel {getattr(hotel, 'id', 'unknown')}: {e}", exc_info=True)
            total_stats["errors"] += 1

    logger.info(
        "Generación automática de tareas diarias completada: "
        f"hoteles procesados={total_stats['hotels_processed']}, "
        f"tareas creadas={total_stats['tasks_created']}, "
        f"tareas omitidas={total_stats['tasks_skipped']}, "
        f"errores={total_stats['errors']}"
    )

    return total_stats


@shared_task
def schedule_daily_tasks():
    """
    Scheduler fino que respeta daily_generation_time + timezone de cada hotel.

    - Se debe ejecutar frecuentemente (ej: cada 5-15 minutos) vía CELERY_BEAT_SCHEDULE.
    - Para cada hotel con HousekeepingConfig:
        - Calcula la hora local actual.
        - Si está dentro de una ventana alrededor de daily_generation_time, dispara
          la generación de tareas diarias solo para ese hotel.
    - Se apoya en `skip_if_exists` de TaskGeneratorService para evitar duplicados,
      por lo que es seguro que corra varias veces en la misma ventana.
    """
    logger.info("⏰ Ejecutando scheduler de tareas diarias de housekeeping...")

    from zoneinfo import ZoneInfo

    now_utc = timezone.now()
    processed_hotels = 0

    configs = HousekeepingConfig.objects.select_related("hotel").all()

    for config in configs:
        hotel = config.hotel
        if not hotel.is_active:
            continue

        if not config.create_daily_tasks:
            continue

        # Obtener hora local del hotel
        try:
            hotel_tz = ZoneInfo(hotel.timezone) if hotel.timezone else None
        except Exception:
            hotel_tz = None

        local_now = timezone.localtime(now_utc, hotel_tz) if hotel_tz else now_utc
        local_time = local_now.time()

        target_time = config.daily_generation_time

        # Ventana de disparo: +/- 10 minutos alrededor de daily_generation_time
        window_minutes = 10
        delta_minutes = (
            (local_time.hour * 60 + local_time.minute)
            - (target_time.hour * 60 + target_time.minute)
        )

        if -window_minutes <= delta_minutes <= window_minutes:
            logger.info(
                f"Hotel {hotel.id} dentro de ventana de generación diaria "
                f"(hora local {local_time}, objetivo {target_time}). "
                "Generando tareas diarias..."
            )
            stats = TaskGeneratorService.create_daily_tasks_for_hotel(hotel, target_date=local_now.date())
            processed_hotels += 1
            logger.info(
                f"Hotel {hotel.id} - generación diaria: "
                f"{stats.get('tasks_created', 0)} creadas, "
                f"{stats.get('tasks_skipped', 0)} omitidas, "
                f"{stats.get('errors', 0)} errores"
            )

    logger.info(f"Scheduler de tareas diarias completado. Hoteles procesados: {processed_hotels}")
    return {"processed_hotels": processed_hotels}


@shared_task(bind=True)
def check_overdue_tasks(self):
    """
    Tarea Celery para verificar y marcar tareas de housekeeping vencidas.
    Se ejecuta periódicamente y verifica tareas en progreso que hayan excedido su tiempo estimado.
    """
    logger.info("Iniciando verificación de tareas vencidas de housekeeping...")
    
    # Obtener todas las tareas en progreso
    in_progress_tasks = HousekeepingTask.objects.filter(
        status=TaskStatus.IN_PROGRESS,
        started_at__isnull=False,
    ).select_related("hotel", "hotel__housekeeping_config", "room", "assigned_to")
    
    processed_count = 0
    marked_overdue = 0
    auto_completed = 0
    
    for task in in_progress_tasks:
        try:
            # Obtener configuración del hotel
            config = getattr(task.hotel, "housekeeping_config", None)
            if not config:
                continue
            
            # Calcular tiempo transcurrido desde que se inició
            if not task.started_at:
                continue
            
            elapsed_time = timezone.now() - task.started_at
            elapsed_minutes = int(elapsed_time.total_seconds() / 60)
            
            # Obtener tiempo máximo configurado (usar estimated_minutes de la tarea o config)
            max_duration = task.estimated_minutes or config.max_task_duration_minutes
            
            # Verificar si está vencida
            if elapsed_minutes > max_duration:
                # Marcar como vencida si no está marcada
                if not task.is_overdue:
                    task.is_overdue = True
                    task.save(update_fields=["is_overdue", "updated_at"])
                    marked_overdue += 1
                    logger.info(
                        f"Tarea {task.id} marcada como vencida. "
                        f"Tiempo transcurrido: {elapsed_minutes} min, "
                        f"Tiempo máximo: {max_duration} min"
                    )
                
                # Auto-completar si está configurado
                if config.auto_complete_overdue:
                    grace_period = config.overdue_grace_minutes
                    if elapsed_minutes > (max_duration + grace_period):
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = timezone.now()
                        task.save(update_fields=["status", "completed_at", "updated_at"])
                        auto_completed += 1
                        logger.info(
                            f"Tarea {task.id} auto-completada por vencimiento. "
                            f"Tiempo transcurrido: {elapsed_minutes} min"
                        )
                
                processed_count += 1
                
        except Exception as e:
            logger.error(
                f"Error procesando tarea {task.id} para verificación de vencimiento: {e}",
                exc_info=True,
            )
    
    logger.info(
        "Verificación de tareas vencidas completada. "
        f"Procesadas: {processed_count}, Marcadas como vencidas: {marked_overdue}, "
        f"Auto-completadas: {auto_completed}"
    )
    
    return {
        "processed": processed_count,
        "marked_overdue": marked_overdue,
        "auto_completed": auto_completed,
    }


@shared_task
def rebalance_housekeeping_workload():
    """
    Tarea periódica para rebalancear la carga de trabajo entre el personal de housekeeping.

    - Recorre hoteles activos con `enable_auto_assign=True`.
    - Respeta el parámetro `rebalance_every_minutes` de HousekeepingConfig
      como frecuencia sugerida (aunque la programación real se hace en CELERY_BEAT_SCHEDULE).
    """
    logger.info("🔄 Iniciando tarea de rebalanceo de carga de housekeeping...")

    hotels = Hotel.objects.filter(is_active=True, housekeeping_config__enable_auto_assign=True).select_related(
        "housekeeping_config"
    )

    results = []
    for hotel in hotels:
        config = hotel.housekeeping_config
        # Aquí podríamos usar rebalance_every_minutes para decidir si saltar el hotel
        # en función de la última ejecución almacenada; por simplicidad, dejamos que
        # la frecuencia real venga desde CELERY_BEAT_SCHEDULE.
        stats = TaskGeneratorService.rebalance_workload_for_hotel(hotel)
        results.append(stats)

    logger.info(f"Rebalanceo de housekeeping completado para {len(results)} hoteles.")
    return results
