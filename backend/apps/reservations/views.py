from django.shortcuts import render
from rest_framework import viewsets, permissions, filters, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from apps.rooms.models import Room, RoomStatus
from apps.rooms.serializers import RoomSerializer
from .models import Reservation, ReservationStatus, RoomBlock, ReservationNight
from .serializers import (
    ReservationSerializer,
    PaymentSerializer,
    ChannelCommissionSerializer,
    ReservationChargeSerializer,
)
from rest_framework.decorators import action, api_view
from decimal import Decimal
from django.db.models import Sum
from .services.pricing import compute_nightly_rate, recalc_reservation_totals
from django.shortcuts import get_object_or_404
from .middleware import get_current_user


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
        # log explícito con autor
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CHECK_IN,
            changed_by=request.user if request.user.is_authenticated else None,
        )
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
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CHECK_OUT,
            changed_by=request.user if request.user.is_authenticated else None,
        )
        return Response({"detail": "Check-out realizado."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
            return Response({"detail": "Solo se pueden cancelar reservas pendientes o confirmadas."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"]) 
        from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
        ReservationChangeLog.objects.create(
            reservation=reservation,
            event_type=ReservationChangeEvent.CANCEL,
            changed_by=request.user if request.user.is_authenticated else None,
        )
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


@api_view(['GET'])
def pricing_quote(request):
    room_id = int(request.query_params.get("room_id"))
    guests = int(request.query_params.get("guests", 1))
    check_in = date.fromisoformat(request.query_params.get("check_in"))
    check_out = date.fromisoformat(request.query_params.get("check_out"))

    room = Room.objects.get(id=room_id)
    nights = []
    total = Decimal('0.00')

    current = check_in

    while current < check_out:
        parts = compute_nightly_rate(room, guests)
        nights.append({
            'date': current,
            'base_rate': parts['base_rate'],
            'extra_guest_fee': parts['extra_guest_fee'],
            'discount': parts['discount'],
            'tax': parts['tax'],
            'total_night': parts['total_night'],
        })
        total += parts['total_night']
        current += timedelta(days=1)

    return Response({
        'room_id': room_id,
        'guests': guests,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'total': total,
    })

@api_view(['GET'])
def pricing_daily_summary(request):
    hotel_id_str = request.query_params.get("hotel_id")
    start_date_str = request.query_params.get("start_date")
    end_date_str = request.query_params.get("end_date")
    mode = request.query_params.get("mode", "check_in")
    metric = request.query_params.get("metric", "gross")
    
    # Validación básica de parámetros
    if not hotel_id_str or not start_date_str or not end_date_str:
        return Response(
            {"detail": "Parámetros requeridos: hotel_id, start_date, end_date"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        hotel_id = int(hotel_id_str)
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except (ValueError, TypeError):
        return Response(
            {"detail": "Parámetros inválidos. Formatos: hotel_id=int, fechas=YYYY-MM-DD"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if mode == "check_in":
        qs = Reservation.objects.filter(
            hotel_id=hotel_id,
            check_in__range=[start_date, end_date],
            status__in=[ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN, ReservationStatus.CHECK_OUT],
        )
        # Gross por día (suma de total_price en fecha de check-in)
        per = qs.values('check_in').annotate(revenue=Sum('total_price')).order_by('check_in')
        daily_map = {r['check_in']: (r['revenue'] or Decimal('0.00')) for r in per}
        total = sum(daily_map.values()) if daily_map else Decimal('0.00')

        # Net: restar comisiones imputadas al día de check-in
        if metric == "net":
            from apps.reservations.models import ChannelCommission
            comm_per = ChannelCommission.objects.filter(
                reservation__in=qs
            ).values('reservation__check_in').annotate(comm=Sum('amount'))
            for row in comm_per:
                d = row['reservation__check_in']
                comm = row['comm'] or Decimal('0.00')
                daily_map[d] = (daily_map.get(d, Decimal('0.00')) - comm)
            total = sum(daily_map.values()) if daily_map else Decimal('0.00')

        daily = [{'date': d, 'revenue': v} for d, v in sorted(daily_map.items())]
    else:
        # Modo devengo por noche usando ReservationNight
        qs = ReservationNight.objects.filter(
            hotel_id=hotel_id,
            date__range=[start_date, end_date],
        )
        total = qs.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00')
        per = qs.values('date').annotate(revenue=Sum('total_night')).order_by('date')
        daily = [{'date': r['date'], 'revenue': r['revenue']} for r in per]
    
    return Response({
        'hotel_id': hotel_id,
        'period': {'start_date': start_date, 'end_date': end_date},
        'mode': mode,
        'metric': metric,
        'total': total,
        'daily': daily,
    })


@api_view(['GET'])
def reservation_pricing_summary(request, pk: int):
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response({"detail": "Reserva no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    nights = reservation.nights.order_by('date').values(
        'date', 'base_rate', 'extra_guest_fee', 'discount', 'tax', 'total_night'
    )
    charges = reservation.charges.order_by('date').values('date', 'description', 'amount')
    payments = reservation.payments.order_by('date').values('date', 'method', 'amount')

    from django.db.models import Sum
    from decimal import Decimal
    totals = {
        'nights_total': reservation.nights.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00'),
        'charges_total': reservation.charges.aggregate(s=Sum('amount'))['s'] or Decimal('0.00'),
        'payments_total': reservation.payments.aggregate(s=Sum('amount'))['s'] or Decimal('0.00'),
    }
    nights_count = reservation.nights.count()
    adr = (totals['nights_total'] / nights_count).quantize(Decimal('0.01')) if nights_count else Decimal('0.00')
    # Comisión por canal (si existe)
    commission = reservation.commissions.order_by('-created_at').first()
    commission_amount = commission.amount if commission else Decimal('0.00')

    net_total = (reservation.total_price or Decimal('0.00')) - commission_amount
    balance = (totals['payments_total'] or Decimal('0.00')) - (reservation.total_price or Decimal('0.00'))
    data = {
        'reservation_id': reservation.id,
        'hotel_id': reservation.hotel_id,
        'room_id': reservation.room_id,
        'guest_name': reservation.guest_name,
        'check_in': reservation.check_in,
        'check_out': reservation.check_out,
        'status': reservation.status,
        'nights': list(nights),
        'charges': list(charges),
        'payments': list(payments),
        'totals': {
            **totals,
            'total_price': reservation.total_price,
            'adr': adr,
            'nights_count': nights_count,
            'commission_amount': commission_amount,
            'net_total': net_total,
            'balance': balance,
        }
    }
    return Response(data)


# ----- Charges / Payments / Commission -----

@api_view(['GET', 'POST'])
def reservation_charges(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        ser = ReservationChargeSerializer(reservation.charges.order_by('-date'), many=True)
        return Response(ser.data)
    # POST
    ser = ReservationChargeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    charge = reservation.charges.create(**ser.validated_data)
    recalc_reservation_totals(reservation)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.CHARGE_ADDED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"+ {ser.validated_data.get('description', '')} ${ser.validated_data.get('amount')}"
    )
    return Response(ReservationChargeSerializer(charge).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def reservation_charge_delete(request, pk: int, charge_id: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    charge = get_object_or_404(reservation.charges, pk=charge_id)
    charge.delete()
    recalc_reservation_totals(reservation)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.CHARGE_REMOVED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"- cargo #{charge_id}"
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
def reservation_payments(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        ser = PaymentSerializer(reservation.payments.order_by('-date'), many=True)
        return Response(ser.data)
    # POST
    ser = PaymentSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    payment = reservation.payments.create(**ser.validated_data)
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.PAYMENT_ADDED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"+ pago ${ser.validated_data.get('amount')} ({ser.validated_data.get('method')})"
    )
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def reservation_commission(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'GET':
        comm = reservation.commissions.order_by('-created_at').first()
        if not comm:
            return Response({'detail': 'Sin comisión'}, status=status.HTTP_200_OK)
        return Response(ChannelCommissionSerializer(comm).data)

    # POST: { "channel": "booking", "rate_percent": 15.0 }
    ser = ChannelCommissionSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    rate = data.get('rate_percent') or Decimal('0.00')
    amount = (reservation.total_price or Decimal('0.00')) * (Decimal(rate) / Decimal('100'))
    comm, created = reservation.commissions.get_or_create(
        channel=data.get('channel', 'direct'),
        defaults={'rate_percent': rate, 'amount': amount},
    )
    if not created:
        comm.rate_percent = rate
        comm.amount = amount
        comm.save(update_fields=['rate_percent', 'amount'])
    from apps.reservations.models import ReservationChangeLog, ReservationChangeEvent
    ReservationChangeLog.objects.create(
        reservation=reservation,
        event_type=ReservationChangeEvent.COMMISSION_UPDATED,
        changed_by=request.user if request.user.is_authenticated else None,
        message=f"commission {comm.channel} {comm.rate_percent}% (${comm.amount})"
    )
    return Response(ChannelCommissionSerializer(comm).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def reservation_history(request, pk: int):
    reservation = get_object_or_404(Reservation, pk=pk)

    status_changes_qs = reservation.status_changes.select_related("changed_by").order_by("-changed_at")
    changes_qs = reservation.change_logs.select_related("changed_by").order_by("-changed_at")

    def serialize_user(u):
        if not u:
            return None
        return {"id": u.id, "username": getattr(u, "username", None), "email": getattr(u, "email", None)}

    timeline = []
    for sc in status_changes_qs:
        timeline.append({
            "type": "status_change",
            "changed_at": sc.changed_at,
            "changed_by": serialize_user(sc.changed_by),
            "detail": {"from": sc.from_status, "to": sc.to_status},
        })
    for cl in changes_qs:
        timeline.append({
            "type": "change_log",
            "changed_at": cl.changed_at,
            "changed_by": serialize_user(cl.changed_by),
            "detail": {
                "event_type": cl.event_type,
                "fields_changed": cl.fields_changed,
                "message": cl.message,
            },
        })
    timeline.sort(key=lambda x: x["changed_at"], reverse=True)
    return Response({"reservation_id": reservation.id, "timeline": timeline})