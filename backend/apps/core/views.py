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
        enterprise = self.request.query_params.get("enterprise")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        country = self.request.query_params.get("country")
        if enterprise and enterprise.isdigit():
            qs = qs.filter(enterprise_id=enterprise)
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
        
        # Calcular capacidades
        total_capacity = sum(room.capacity for room in rooms_qs)
        max_capacity = sum(room.max_capacity for room in rooms_qs)

        arrivals_today = Reservation.objects.filter(
            hotel=hotel,
            check_in=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
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
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
        ).count()

        # Lista compacta de reservas actuales
        reservations_qs = Reservation.objects.filter(
            hotel=hotel,
            check_in__lte=today,
            check_out__gt=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        ).select_related("room").order_by("room__name")
        
        # Procesar las reservas para extraer el nombre del huésped principal
        current_reservations = []
        for reservation in reservations_qs:
            guest_name = ""
            if reservation.guests_data and isinstance(reservation.guests_data, list):
                # Buscar el huésped principal
                primary_guest = next((guest for guest in reservation.guests_data if guest.get('is_primary', False)), None)
                if not primary_guest and reservation.guests_data:
                    # Si no hay huésped principal marcado, tomar el primero
                    primary_guest = reservation.guests_data[0]
                guest_name = primary_guest.get('name', '') if primary_guest else ''
            
            current_reservations.append({
                "id": reservation.id,
                "room__name": reservation.room.name,
                "guest_name": guest_name,
                "status": reservation.status,
                "check_in": reservation.check_in,
                "check_out": reservation.check_out
            })
        
        # Calcular huéspedes actuales sumando los guests de las reservas activas
        active_reservations = Reservation.objects.filter(
            hotel=hotel,
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CONFIRMED],
            check_in__lte=today,
            check_out__gt=today,
        )
        current_guests = sum(reservation.guests for reservation in active_reservations)

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
                "total_capacity": total_capacity,
                "max_capacity": max_capacity,
                "current_guests": current_guests,
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


class GlobalSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Fecha local
        today = timezone.localdate()
        
        # Obtener todos los hoteles activos
        hotels = Hotel.objects.filter(is_active=True)
        
        # Calcular métricas globales de habitaciones
        rooms_qs = Room.objects.filter(hotel__in=hotels)
        total_rooms = rooms_qs.count()
        available = rooms_qs.filter(status=RoomStatus.AVAILABLE).count()
        occupied = rooms_qs.filter(status=RoomStatus.OCCUPIED).count()
        maintenance = rooms_qs.filter(status=RoomStatus.MAINTENANCE).count()
        out_of_service = rooms_qs.filter(status=RoomStatus.OUT_OF_SERVICE).count()
        
        # Calcular capacidades globales
        total_capacity = sum(room.capacity for room in rooms_qs)
        max_capacity = sum(room.max_capacity for room in rooms_qs)
        
        # Calcular métricas globales de reservas
        arrivals_today = Reservation.objects.filter(
            hotel__in=hotels,
            check_in=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        ).count()
        
        inhouse_today = Reservation.objects.filter(
            hotel__in=hotels,
            check_in__lte=today,
            check_out__gt=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        ).count()
        
        departures_today = Reservation.objects.filter(
            hotel__in=hotels,
            check_out=today,
            status__in=[ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
        ).count()
        
        # Calcular huéspedes actuales globales
        active_reservations = Reservation.objects.filter(
            hotel__in=hotels,
            check_in__lte=today,
            check_out__gt=today,
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
        ).select_related('hotel', 'room')
        
        current_guests = sum(reservation.guests for reservation in active_reservations)
        
        # Bloqueos globales de hoy
        blocks_today = RoomBlock.objects.filter(
            hotel__in=hotels,
            is_active=True,
            start_date__lte=today,
            end_date__gt=today,
        ).count()
        
        # Lista de reservas actuales globales (limitada para performance)
        current_reservations = []
        for reservation in active_reservations[:50]:  # Limitar a 50 para performance
            current_reservations.append({
                "id": reservation.id,
                "guest_name": reservation.guest_name,
                "room": reservation.room.name,
                "hotel_name": reservation.hotel.name,
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
                "status": reservation.status,
                "total_price": float(reservation.total_price),
                "guests": reservation.guests,
            })
        
        return Response({
            "summary_type": "global",
            "hotels_count": hotels.count(),
            "rooms": {
                "total": total_rooms,
                "available": available,
                "occupied": occupied,
                "maintenance": maintenance,
                "out_of_service": out_of_service,
                "total_capacity": total_capacity,
                "max_capacity": max_capacity,
                "current_guests": current_guests,
            },
            "today": {
                "date": today.isoformat(),
                "arrivals": arrivals_today,
                "inhouse": inhouse_today,
                "departures": departures_today,
                "blocks": blocks_today,
            },
            "current_reservations": current_reservations,
        }, status=status.HTTP_200_OK)