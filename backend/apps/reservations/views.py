from django.shortcuts import render
from rest_framework import viewsets, permissions, filters, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import date
from django.core.exceptions import ValidationError
from apps.rooms.models import Room, RoomStatus
from apps.rooms.serializers import RoomSerializer
from .models import Reservation, ReservationStatus, RoomBlock
from .serializers import ReservationSerializer
from rest_framework.decorators import action

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Reservation.objects.select_related("hotel", "room").order_by("-created_at")
        hotel_id = self.request.query_params.get("hotel")
        room_id = self.request.query_params.get("room")
        status_param = self.request.query_params.get("status")
        if hotel_id and hotel_id.isdigit():
            qs = qs.filter(hotel_id=hotel_id)
        if room_id and room_id.isdigit():
            qs = qs.filter(room_id=room_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            # Convertir ValidationError a formato JSON
            if hasattr(e, 'message_dict'):
                # Error de validación de campo específico
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'messages'):
                # Error de validación general
                return Response({'__all__': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Error simple
                return Response({'__all__': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            # Convertir ValidationError a formato JSON
            if hasattr(e, 'message_dict'):
                # Error de validación de campo específico
                return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'messages'):
                # Error de validación general
                return Response({'__all__': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Error simple
                return Response({'__all__': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        reservation = self.get_object()
        today = date.today()
        if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]:
            return Response({"detail": "La reserva debe estar confirmada para hacer check-in."}, status=status.HTTP_400_BAD_REQUEST)
        if not (reservation.check_in <= today < reservation.check_out):
            return Response({"detail": "El check-in solo puede realizarse dentro del rango de la reserva."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = ReservationStatus.CHECK_IN
        reservation.room.status = RoomStatus.OCCUPIED
        reservation.room.save(update_fields=["status"])
        reservation.save(update_fields=["status"]) 
        return Response({"detail": "Check-in realizado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status != ReservationStatus.CHECK_IN:
            return Response({"detail": "La reserva debe estar en check-in para hacer check-out."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = ReservationStatus.CHECK_OUT
        # Verificar si hay otra reserva activa hoy para la misma room
        today = date.today()
        overlapping_active = Reservation.objects.filter(
            room=reservation.room,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
            check_in__lt=today,
            check_out__gt=today,
        ).exclude(pk=reservation.pk).exists()
        if not overlapping_active:
            reservation.room.status = RoomStatus.AVAILABLE
            reservation.room.save(update_fields=["status"])
        reservation.save(update_fields=["status"]) 
        return Response({"detail": "Check-out realizado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return Response({"detail": "Solo se pueden cancelar reservas pendientes o confirmadas."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"]) 
        return Response({"detail": "Reserva cancelada."}, status=status.HTTP_200_OK)


class AvailabilityView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RoomSerializer
    queryset = Room.objects.all()  #

    def get(self, request):
        hotel_id = request.query_params.get("hotel")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")
        if not (hotel_id and start_str and end_str):
            return Response({"detail": "Parámetros requeridos: hotel, start, end"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start = date.fromisoformat(start_str)
            end = date.fromisoformat(end_str)
        except ValueError:
            return Response({"detail": "Fechas inválidas (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)
        if start > end:
            return Response({"detail": "la fecha de check-in debe ser anterior a la fecha de check-out"}, status=status.HTTP_400_BAD_REQUEST)

        active_status = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
        ]

        rooms = (
            Room.objects.select_related("hotel")
            .filter(hotel_id=hotel_id)
            .exclude(status=RoomStatus.OUT_OF_SERVICE)
            .exclude(
                reservations__status__in=active_status,
                reservations__check_in__lt=end,
                reservations__check_out__gt=start,
            )
            .exclude(
                room_blocks__is_active=True,
                room_blocks__start_date__lt=end,
                room_blocks__end_date__gt=start,
            )
            .distinct()
        )

        page = self.paginate_queryset(rooms)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)