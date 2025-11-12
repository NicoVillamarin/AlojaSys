from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import CleaningStaff, HousekeepingTask, TaskStatus, HousekeepingConfig
from .serializers import CleaningStaffSerializer, HousekeepingTaskSerializer, HousekeepingConfigSerializer
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
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
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
        # Actualizar estado de limpieza de la habitación si el modelo lo soporta
        try:
            from apps.rooms.models import CleaningStatus
            if hasattr(task.room, "cleaning_status"):
                task.room.cleaning_status = CleaningStatus.IN_PROGRESS
                task.room.save(update_fields=["cleaning_status"])
        except Exception:
            pass
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
            if hasattr(task.room, "cleaning_status"):
                task.room.cleaning_status = CleaningStatus.CLEAN
                task.room.save(update_fields=["cleaning_status"])
        except Exception:
            pass
        return Response({"detail": "Tarea completada."})


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

