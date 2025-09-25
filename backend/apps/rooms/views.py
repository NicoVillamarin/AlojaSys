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