from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Room
from .serializers import RoomSerializer

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer

    def get_queryset(self):
        qs = Room.objects.select_related("hotel").filter(is_active=True).order_by("floor", "name")
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