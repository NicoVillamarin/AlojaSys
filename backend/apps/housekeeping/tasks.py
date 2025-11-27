import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.housekeeping.models import HousekeepingTask, TaskStatus, HousekeepingConfig

logger = logging.getLogger(__name__)


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
        started_at__isnull=False
    ).select_related('hotel', 'hotel__housekeeping_config', 'room', 'assigned_to')
    
    processed_count = 0
    marked_overdue = 0
    auto_completed = 0
    
    for task in in_progress_tasks:
        try:
            # Obtener configuración del hotel
            config = getattr(task.hotel, 'housekeeping_config', None)
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
                    task.save(update_fields=['is_overdue', 'updated_at'])
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
                        task.save(update_fields=['status', 'completed_at', 'updated_at'])
                        auto_completed += 1
                        logger.info(
                            f"Tarea {task.id} auto-completada por vencimiento. "
                            f"Tiempo transcurrido: {elapsed_minutes} min"
                        )
                
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Error procesando tarea {task.id} para verificación de vencimiento: {e}", exc_info=True)
    
    logger.info(
        f"Verificación de tareas vencidas completada. "
        f"Procesadas: {processed_count}, Marcadas como vencidas: {marked_overdue}, Auto-completadas: {auto_completed}"
    )
    
    return {
        'processed': processed_count,
        'marked_overdue': marked_overdue,
        'auto_completed': auto_completed
    }
