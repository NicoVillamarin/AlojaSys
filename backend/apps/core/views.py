from .serializers import HotelSerializer
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from apps.rooms.models import Room, RoomStatus
from apps.reservations.models import Reservation, ReservationStatus, RoomBlock
from .models import Hotel


class HotelViewSet(viewsets.ModelViewSet):
    serializer_class = HotelSerializer
    def get_queryset(self):
        qs = Hotel.objects.select_related("city", "city__state", "city__state__country").order_by("name")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        country = self.request.query_params.get("country")
        if city and city.isdigit():
            qs = qs.filter(city_id=city)
        if state and state.isdigit():
            qs = qs.filter(city__state_id=state)
        if country:
            qs = qs.filter(city__state__country__code2=country.upper())
        return qs

class StatusSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hotel_id = request.query_params.get("hotel")
        if not (hotel_id and hotel_id.isdigit()):
            return Response({"detail": "Parámetro requerido: hotel=<id>"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            hotel = Hotel.objects.select_related("city", "city__state", "city__state__country").get(pk=hotel_id)
        except Hotel.DoesNotExist:
            return Response({"detail": "Hotel no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Fecha local (si querés por timezone del hotel, podés ajustar aquí)
        today = timezone.localdate()

        rooms_qs = Room.objects.filter(hotel=hotel)
        total_rooms = rooms_qs.count()
        available = rooms_qs.filter(status=RoomStatus.AVAILABLE).count()
        occupied = rooms_qs.filter(status=RoomStatus.OCCUPIED).count()
        maintenance = rooms_qs.filter(status=RoomStatus.MAINTENANCE).count()
        out_of_service = rooms_qs.filter(status=RoomStatus.OUT_OF_SERVICE).count()

        arrivals_today = Reservation.objects.filter(
            hotel=hotel,
            check_in=today,
            status__in=[ReservationStatus.CONFIRMED],
        ).count()

        inhouse_today = Reservation.objects.filter(
            hotel=hotel,
            check_in__lte=today,
            check_out__gt=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        ).count()

        departures_today = Reservation.objects.filter(
            hotel=hotel,
            check_out=today,
            status=ReservationStatus.CHECK_IN,
        ).count()

        # Lista compacta de reservas actuales
        current_reservations = list(
            Reservation.objects.filter(
                hotel=hotel,
                check_in__lte=today,
                check_out__gt=today,
                status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
            )
            .select_related("room")
            .order_by("room__name")
            .values("id", "room__name", "guest_name", "status", "check_in", "check_out")
        )

        # Bloqueos que solapan hoy (opcional)
        blocks_today = RoomBlock.objects.filter(
            hotel=hotel,
            is_active=True,
            start_date__lte=today,
            end_date__gt=today,
        ).count()

        return Response({
            "hotel": {
                "id": hotel.id,
                "name": hotel.name,
                "city": hotel.city.name if hotel.city else None,
                "check_in_time": hotel.check_in_time,
                "check_out_time": hotel.check_out_time,
            },
            "rooms": {
                "total": total_rooms,
                "available": available,
                "occupied": occupied,
                "maintenance": maintenance,
                "out_of_service": out_of_service,
            },
            "today": {
                "date": today,
                "arrivals": arrivals_today,
                "inhouse": inhouse_today,
                "departures": departures_today,
                "blocks": blocks_today,
            },
            "current_reservations": current_reservations,
        }, status=status.HTTP_200_OK)