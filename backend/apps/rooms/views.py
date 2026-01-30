from rest_framework import viewsets, status
from rest_framework.response import Response
from datetime import date
from .models import Room, RoomStatus
from .serializers import RoomSerializer
from apps.reservations.models import ReservationStatus

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer

    def get_queryset(self):
        qs = Room.objects.select_related("hotel", "base_currency", "secondary_currency").filter(is_active=True).order_by("floor", "name")
        hotel_id = self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        # Filtro por capacidad mínima de huéspedes
        min_capacity = self.request.query_params.get("min_capacity")
        if min_capacity:
            try:
                min_capacity = int(min_capacity)
                qs = qs.filter(max_capacity__gte=min_capacity)
            except (ValueError, TypeError):
                pass  # Ignorar valores inválidos
        
        # Filtro por estado de habitación
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filtro por estado de limpieza (cleaning_status)
        cleaning_status_filter = self.request.query_params.get("cleaning_status")
        if cleaning_status_filter:
            qs = qs.filter(cleaning_status=cleaning_status_filter)
        
        # Filtro por fechas de disponibilidad (check_in y check_out)
        check_in_str = self.request.query_params.get("check_in")
        check_out_str = self.request.query_params.get("check_out")
        
        if check_in_str and check_out_str:
            try:
                check_in_date = date.fromisoformat(check_in_str)
                check_out_date = date.fromisoformat(check_out_str)
                
                # Validar que check_in sea anterior a check_out
                if check_in_date >= check_out_date:
                    # Si las fechas son inválidas, retornar queryset vacío
                    return qs.none()
                
                # Estados de reserva que ocupan la habitación
                active_status = [
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.CHECK_IN,
                ]
                
                # Excluir habitaciones con reservas activas en el rango de fechas
                # Una reserva ocupa la habitación si:
                # - check_in de la reserva < check_out solicitado Y
                # - check_out de la reserva > check_in solicitado
                qs = qs.exclude(
                    reservations__status__in=active_status,
                    reservations__check_in__lt=check_out_date,
                    reservations__check_out__gt=check_in_date,
                )
                
                # Excluir habitaciones con bloqueos activos en el rango de fechas
                # Importar RoomBlock aquí para evitar importaciones circulares
                from apps.reservations.models import RoomBlock
                qs = qs.exclude(
                    room_blocks__is_active=True,
                    room_blocks__start_date__lt=check_out_date,
                    room_blocks__end_date__gt=check_in_date,
                )
                
                # Usar distinct() para evitar duplicados por las relaciones
                qs = qs.distinct()
                
            except (ValueError, TypeError):
                # Si las fechas son inválidas, ignorar el filtro
                pass
        
        return qs

    def destroy(self, request, *args, **kwargs):
        """
        Eliminación suave: marcar la habitación como inactiva para evitar errores por FKs protegidas.
        """
        room = self.get_object()
        if not room.is_active:
            return Response(status=status.HTTP_204_NO_CONTENT)
        room.is_active = False
        room.save(update_fields=["is_active", "updated_at"]) if hasattr(room, "updated_at") else room.save(update_fields=["is_active"]) 
        return Response(status=status.HTTP_204_NO_CONTENT)