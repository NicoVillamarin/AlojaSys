from datetime import datetime, time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from .models import (
    CleaningStaff, HousekeepingTask, TaskStatus, HousekeepingConfig,
    CleaningZone, TaskTemplate, Checklist, ChecklistItem, TaskChecklistCompletion
)
from .serializers import (
    CleaningStaffSerializer, HousekeepingTaskSerializer, HousekeepingConfigSerializer,
    CleaningZoneSerializer, TaskTemplateSerializer, ChecklistSerializer,
    ChecklistItemSerializer, TaskChecklistCompletionSerializer
)
from .permissions import HousekeepingAccessPermission, HousekeepingManageAllPermission
from django.db.models import Q


class CleaningStaffViewSet(viewsets.ModelViewSet):
    queryset = CleaningStaff.objects.all()
    serializer_class = CleaningStaffSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs


class HousekeepingTaskViewSet(viewsets.ModelViewSet):
    queryset = HousekeepingTask.objects.all()
    serializer_class = HousekeepingTaskSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset().select_related("hotel", "room", "assigned_to")
        hotel_id = self.request.query_params.get("hotel")
        status_param = self.request.query_params.get("status")
        assigned_to = self.request.query_params.get("assigned_to")
        room_id = self.request.query_params.get("room")
        task_type = self.request.query_params.get("task_type")
        priority = self.request.query_params.get("priority")
        created_from_raw = self.request.query_params.get("created_from")
        created_to_raw = self.request.query_params.get("created_to")
        completed_from_raw = self.request.query_params.get("completed_from")
        completed_to_raw = self.request.query_params.get("completed_to")

        def parse_datetime_param(value, end_of_day=False):
            if not value:
                return None
            dt = parse_datetime(value)
            if dt:
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt, timezone.get_current_timezone())
                return dt
            date_value = parse_date(value)
            if date_value:
                base_time = time.max if end_of_day else time.min
                dt = datetime.combine(date_value, base_time)
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return None

        created_from = parse_datetime_param(created_from_raw)
        created_to = parse_datetime_param(created_to_raw, end_of_day=True)
        completed_from = parse_datetime_param(completed_from_raw)
        completed_to = parse_datetime_param(completed_to_raw, end_of_day=True)

        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            if len(statuses) == 1:
                qs = qs.filter(status=statuses[0])
            elif statuses:
                qs = qs.filter(status__in=statuses)
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        if room_id:
            qs = qs.filter(room_id=room_id)
        if task_type:
            qs = qs.filter(task_type=task_type)
        if priority:
            try:
                qs = qs.filter(priority=int(priority))
            except (TypeError, ValueError):
                pass
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)
        if completed_from:
            qs = qs.filter(completed_at__gte=completed_from)
        if completed_to:
            qs = qs.filter(completed_at__lte=completed_to)
        # Restricción: si es staff de limpieza (sin permiso de gestionar todo), limitar a sus hoteles y tareas asignadas
        user = self.request.user
        manage_all = user.is_superuser or user.has_perm("housekeeping.manage_all_tasks")
        if not manage_all:
            profile = getattr(user, "profile", None)
            if profile:
                qs = qs.filter(hotel__in=profile.hotels.all()).filter(
                    Q(assigned_to__user=user) | Q(assigned_to__isnull=True)
                )
        return qs

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el método destroy para validar que no se pueden eliminar
        tareas que ya están en progreso o completadas.
        Solo se pueden eliminar tareas pendientes o canceladas.
        """
        task = self.get_object()
        
        # Validar que la tarea no esté en progreso o completada
        if task.status == TaskStatus.IN_PROGRESS:
            return Response(
                {"detail": "No se puede eliminar una tarea que está en progreso. Debe completarla o cancelarla primero."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.status == TaskStatus.COMPLETED:
            return Response(
                {"detail": "No se puede eliminar una tarea completada. Las tareas completadas son parte del historial."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.status != TaskStatus.PENDING:
            return Response(
                {"detail": "Solo se pueden eliminar tareas pendientes."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Solo permitir eliminar tareas pendientes
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        task = self.get_object()
        user = request.user
        if not (user.is_superuser or user.has_perm("housekeeping.manage_all_tasks")):
            # Solo puede iniciar si le fue asignada
            if not task.assigned_to or task.assigned_to.user_id != user.id:
                return Response({"detail": "No puede iniciar tareas no asignadas."}, status=status.HTTP_403_FORBIDDEN)
        if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            return Response({"detail": "Estado inválido para iniciar."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = timezone.now()
        task.save(update_fields=["status", "started_at", "updated_at"])
        # Actualizar estado de limpieza de la habitación
        try:
            from apps.rooms.models import CleaningStatus
            task.room.cleaning_status = CleaningStatus.IN_PROGRESS
            task.room.save(update_fields=["cleaning_status"])
        except Exception as e:
            # Log del error pero no fallar la operación
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error actualizando cleaning_status de habitación {task.room.id}: {str(e)}")
        return Response({"detail": "Tarea iniciada."})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        user = request.user
        if not (user.is_superuser or user.has_perm("housekeeping.manage_all_tasks")):
            # Solo puede completar si le fue asignada
            if not task.assigned_to or task.assigned_to.user_id != user.id:
                return Response({"detail": "No puede completar tareas no asignadas."}, status=status.HTTP_403_FORBIDDEN)
        if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            return Response({"detail": "Estado inválido para completar."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = TaskStatus.COMPLETED
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at", "updated_at"])
        # Marcar habitación como limpia
        try:
            from apps.rooms.models import CleaningStatus
            task.room.cleaning_status = CleaningStatus.CLEAN
            task.room.save(update_fields=["cleaning_status"])
        except Exception as e:
            # Log del error pero no fallar la operación
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error actualizando cleaning_status de habitación {task.room.id}: {str(e)}")
        return Response({"detail": "Tarea completada."})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancela una tarea en progreso o pendiente.
        Esto permite al usuario cancelar una tarea si se inició por error.
        """
        task = self.get_object()
        user = request.user
        
        # Solo superusuarios o usuarios con permiso de gestionar todo pueden cancelar
        if not (user.is_superuser or user.has_perm("housekeeping.manage_all_tasks")):
            return Response(
                {"detail": "No tiene permisos para cancelar tareas."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status == TaskStatus.COMPLETED:
            return Response(
                {"detail": "No se puede cancelar una tarea ya completada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if task.status == TaskStatus.CANCELLED:
            return Response(
                {"detail": "La tarea ya está cancelada."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        was_in_progress = task.status == TaskStatus.IN_PROGRESS
        room = task.room
        
        task.status = TaskStatus.CANCELLED
        task.save(update_fields=["status", "updated_at"])
        
        # Si estaba en progreso, actualizar el estado de la habitación
        if was_in_progress:
            try:
                from apps.rooms.models import CleaningStatus
                # Verificar si hay otras tareas en progreso para esta habitación
                other_in_progress = HousekeepingTask.objects.filter(
                    room=room,
                    status=TaskStatus.IN_PROGRESS
                ).exists()
                
                if not other_in_progress:
                    # No hay otras tareas en progreso, verificar si hay tareas pendientes
                    has_pending = HousekeepingTask.objects.filter(
                        room=room,
                        status=TaskStatus.PENDING
                    ).exists()
                    
                    if has_pending:
                        # Hay tareas pendientes, mantener estado como sucia
                        room.cleaning_status = CleaningStatus.DIRTY
                    else:
                        # No hay tareas pendientes ni en progreso, marcar como limpia
                        room.cleaning_status = CleaningStatus.CLEAN
                    
                    room.save(update_fields=["cleaning_status"])
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error actualizando cleaning_status de habitación {room.id} al cancelar tarea: {str(e)}")
        
        return Response({"detail": "Tarea cancelada."})


class HousekeepingConfigViewSet(viewsets.ModelViewSet):
    queryset = HousekeepingConfig.objects.all()
    serializer_class = HousekeepingConfigSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset().select_related("hotel")
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs

    @action(detail=False, methods=["get"], url_path=r'by-hotel/(?P<hotel_id>[^/.]+)')
    def by_hotel(self, request, hotel_id=None):
        """
        Devuelve (o crea por defecto) la configuración de housekeeping para un hotel.
        """
        from apps.core.models import Hotel
        hotel = Hotel.objects.filter(id=hotel_id).first()
        if not hotel:
            return Response({"detail": "Hotel no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        config, _ = HousekeepingConfig.objects.get_or_create(hotel=hotel)
        data = self.get_serializer(config).data
        return Response(data)


class CleaningZoneViewSet(viewsets.ModelViewSet):
    queryset = CleaningZone.objects.all()
    serializer_class = CleaningZoneSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        return qs


class TaskTemplateViewSet(viewsets.ModelViewSet):
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel")
        room_type = self.request.query_params.get("room_type")
        task_type = self.request.query_params.get("task_type")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        if room_type:
            qs = qs.filter(room_type=room_type)
        if task_type:
            qs = qs.filter(task_type=task_type)
        return qs


class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("items")
        hotel_id = self.request.query_params.get("hotel")
        room_type = self.request.query_params.get("room_type")
        task_type = self.request.query_params.get("task_type")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        if room_type:
            qs = qs.filter(room_type=room_type)
        if task_type:
            qs = qs.filter(task_type=task_type)
        return qs.filter(is_active=True)

    @action(detail=False, methods=["get"], url_path="relevant")
    def relevant(self, request):
        """
        Obtiene checklists relevantes para una tarea basándose en hotel, room_type y task_type.
        Retorna checklists que coincidan con estos criterios o sean generales (sin room_type/task_type).
        
        Prioridad de coincidencia:
        1. Checklist específico para room_type + task_type (más específico)
        2. Checklist específico para room_type solamente
        3. Checklist específico para task_type solamente
        4. Checklist general (sin restricciones)
        """
        from django.db.models import Q
        
        hotel_id = request.query_params.get("hotel")
        room_type = request.query_params.get("room_type")
        task_type = request.query_params.get("task_type")
        
        if not hotel_id:
            return Response({"detail": "hotel es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Base query
        qs = Checklist.objects.filter(
            hotel_id=hotel_id,
            is_active=True
        ).prefetch_related("items")
        
        conditions = Q()
        
        # Checklist general (sin restricciones de room_type ni task_type)
        # Maneja tanto NULL como string vacío
        conditions |= (Q(room_type__isnull=True) | Q(room_type='')) & (Q(task_type__isnull=True) | Q(task_type=''))
        
        # Checklist que coincida exactamente con room_type y task_type
        if room_type and task_type:
            conditions |= Q(room_type=room_type, task_type=task_type)
        
        # Checklist específico solo por room_type (sin restricción de task_type)
        # Esto incluye checklists específicos del room_type aunque tengan otro task_type
        if room_type:
            conditions |= Q(room_type=room_type)
        
        # Checklist específico solo por task_type (sin restricción de room_type)
        if task_type:
            conditions |= ((Q(room_type__isnull=True) | Q(room_type='')) & Q(task_type=task_type))
        
        qs = qs.filter(conditions).order_by("-is_default", "name")
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        checklist_id = self.request.query_params.get("checklist")
        if checklist_id:
            qs = qs.filter(checklist_id=checklist_id)
        return qs


class TaskChecklistCompletionViewSet(viewsets.ModelViewSet):
    queryset = TaskChecklistCompletion.objects.all()
    serializer_class = TaskChecklistCompletionSerializer
    permission_classes = [IsAuthenticated, HousekeepingAccessPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        task_id = self.request.query_params.get("task")
        if task_id:
            qs = qs.filter(task_id=task_id)
        return qs

    def update(self, request, *args, **kwargs):
        """Actualiza el estado de completado y registra quién y cuándo lo completó"""
        instance = self.get_object()
        completed = request.data.get("completed", False)
        
        if completed and not instance.completed:
            instance.completed = True
            instance.completed_by = request.user
            instance.completed_at = timezone.now()
        elif not completed:
            instance.completed = False
            instance.completed_by = None
            instance.completed_at = None
        
        instance.notes = request.data.get("notes", instance.notes)
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

