from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.reservations.models import Payment as ReservationPayment
from apps.users.permissions import IsHotelStaff

from .models import CashSession, CashMovement, CashSessionStatus, CashMovementType
from .serializers import (
    CashSessionSerializer,
    CashSessionOpenSerializer,
    CashSessionCloseSerializer,
    CashMovementSerializer,
)


def _sum_decimal(qs, field: str) -> Decimal:
    val = qs.aggregate(total=Sum(field)).get("total")
    return val if val is not None else Decimal("0.00")


def calculate_cash_expected(*, session: CashSession, until_dt=None) -> dict:
    """
    Calcula:
    - cash_payments_total: pagos en efectivo dentro del rango de la sesión
    - movements_in_total / movements_out_total: movimientos manuales
    - expected: opening + cash_payments + in - out
    """
    until_dt = until_dt or session.closed_at or timezone.now()

    payments_qs = (
        ReservationPayment.objects.filter(
            reservation__hotel_id=session.hotel_id,
            method="cash",
            currency=session.currency,
            created_at__gte=session.opened_at,
            created_at__lte=until_dt,
        )
        .exclude(status="failed")
        .only("amount")
    )
    cash_payments_total = _sum_decimal(payments_qs, "amount")

    movements_qs = CashMovement.objects.filter(session_id=session.id, currency=session.currency).only("amount")
    movements_in_total = _sum_decimal(movements_qs.filter(movement_type=CashMovementType.IN), "amount")
    movements_out_total = _sum_decimal(movements_qs.filter(movement_type=CashMovementType.OUT), "amount")

    expected = (session.opening_amount or Decimal("0.00")) + cash_payments_total + movements_in_total - movements_out_total
    return {
        "cash_payments_total": cash_payments_total,
        "movements_in_total": movements_in_total,
        "movements_out_total": movements_out_total,
        "expected": expected,
    }


class CanManageCashbox(permissions.BasePermission):
    """
    Permisos para Caja:
    - GET: cashbox.view_cashsession (o superuser)
    - POST (open): cashbox.open_cashsession (o superuser)
    - PUT/PATCH/DELETE (no se exponen): cashbox.change_cashsession / delete_cashsession
    Acciones:
    - close: cashbox.close_cashsession
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        # Acciones personalizadas
        action = getattr(view, "action", None)
        if action == "close":
            return request.user.has_perm("cashbox.close_cashsession")
        if action == "current":
            return request.user.has_perm("cashbox.view_cashsession") or request.user.has_perm("cashbox.view_cashbox_reports")

        # Métodos estándar
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_perm("cashbox.view_cashsession") or request.user.has_perm("cashbox.view_cashbox_reports")
        if request.method == "POST":
            return request.user.has_perm("cashbox.open_cashsession") or request.user.has_perm("cashbox.add_cashsession")

        return request.user.has_perm("cashbox.change_cashsession")

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        # Reutilizar control por hotel + después permisos
        hotel_permission = IsHotelStaff()
        if not hotel_permission.has_object_permission(request, view, obj):
            return False
        return self.has_permission(request, view)


class CashSessionViewSet(viewsets.ModelViewSet):
    queryset = CashSession.objects.all().select_related("hotel", "opened_by", "closed_by")
    serializer_class = CashSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsHotelStaff, CanManageCashbox]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel_id") or self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by("-opened_at")

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        # En list devolvemos datos tal cual (sin cálculos por item para no penalizar)
        return resp

    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()
        data = calculate_cash_expected(session=session)
        ser = self.get_serializer(session)
        payload = dict(ser.data)
        payload.update(
            {
                "cash_payments_total": str(data["cash_payments_total"]),
                "movements_in_total": str(data["movements_in_total"]),
                "movements_out_total": str(data["movements_out_total"]),
                "expected_amount_current": str(data["expected"]),
            }
        )
        return Response(payload)

    def create(self, request, *args, **kwargs):
        """
        Crear sesión = abrir caja.
        """
        open_ser = CashSessionOpenSerializer(data=request.data)
        open_ser.is_valid(raise_exception=True)
        hotel_id = open_ser.validated_data["hotel_id"]
        currency = open_ser.validated_data.get("currency") or "ARS"
        opening_amount = open_ser.validated_data.get("opening_amount") or Decimal("0.00")
        notes = open_ser.validated_data.get("notes") or ""

        # Evitar 2 cajas abiertas para el mismo hotel+moneda
        existing = CashSession.objects.filter(
            hotel_id=hotel_id, currency=currency, status=CashSessionStatus.OPEN
        ).first()
        if existing:
            return Response(
                {"detail": "Ya existe una caja abierta para este hotel/moneda.", "session_id": existing.id},
                status=status.HTTP_409_CONFLICT,
            )

        session = CashSession.objects.create(
            hotel_id=hotel_id,
            currency=currency,
            opened_by=request.user,
            opening_amount=opening_amount,
            notes=notes,
            status=CashSessionStatus.OPEN,
        )
        ser = self.get_serializer(session)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def current(self, request):
        hotel_id = request.query_params.get("hotel_id") or request.query_params.get("hotel")
        currency = request.query_params.get("currency") or "ARS"
        if not hotel_id:
            return Response({"detail": "hotel_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        session = (
            CashSession.objects.filter(hotel_id=hotel_id, currency=currency, status=CashSessionStatus.OPEN)
            .select_related("hotel", "opened_by", "closed_by")
            .first()
        )
        if not session:
            return Response({"detail": "No hay caja abierta"}, status=status.HTTP_404_NOT_FOUND)

        data = calculate_cash_expected(session=session)
        ser = self.get_serializer(session)
        payload = dict(ser.data)
        payload.update(
            {
                "cash_payments_total": str(data["cash_payments_total"]),
                "movements_in_total": str(data["movements_in_total"]),
                "movements_out_total": str(data["movements_out_total"]),
                "expected_amount_current": str(data["expected"]),
            }
        )
        return Response(payload)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_object()
        if session.status != CashSessionStatus.OPEN:
            return Response({"detail": "La caja no está abierta."}, status=status.HTTP_409_CONFLICT)

        close_ser = CashSessionCloseSerializer(data=request.data)
        close_ser.is_valid(raise_exception=True)
        closing_amount = close_ser.validated_data["closing_amount"]
        notes = close_ser.validated_data.get("notes") or ""

        with transaction.atomic():
            closed_at = timezone.now()
            calc = calculate_cash_expected(session=session, until_dt=closed_at)
            expected = calc["expected"]
            difference = (closing_amount - expected) if closing_amount is not None else None

            session.closed_at = closed_at
            session.closed_by = request.user
            session.closing_amount = closing_amount
            session.expected_amount = expected
            session.difference_amount = difference
            session.status = CashSessionStatus.CLOSED
            if notes:
                session.notes = (session.notes or "").strip()
                session.notes = (session.notes + "\n" if session.notes else "") + notes
            session.save(
                update_fields=[
                    "closed_at",
                    "closed_by",
                    "closing_amount",
                    "expected_amount",
                    "difference_amount",
                    "status",
                    "notes",
                    "updated_at",
                ]
            )

        ser = self.get_serializer(session)
        payload = dict(ser.data)
        payload.update(
            {
                "cash_payments_total": str(calc["cash_payments_total"]),
                "movements_in_total": str(calc["movements_in_total"]),
                "movements_out_total": str(calc["movements_out_total"]),
                "expected_amount_current": str(calc["expected"]),
            }
        )
        return Response(payload, status=status.HTTP_200_OK)


class CashMovementViewSet(viewsets.ModelViewSet):
    queryset = CashMovement.objects.all().select_related("session", "hotel", "created_by")
    serializer_class = CashMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsHotelStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_id = self.request.query_params.get("hotel_id") or self.request.query_params.get("hotel")
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        session_id = self.request.query_params.get("session_id") or self.request.query_params.get("session")
        if session_id:
            qs = qs.filter(session_id=session_id)
        return qs.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """
        Crea un movimiento manual (ingreso/egreso) dentro de una sesión abierta.
        Requiere: session, hotel, movement_type, amount, currency (opcional), description (opcional)
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        session_id = ser.validated_data["session"].id
        session = get_object_or_404(CashSession, id=session_id)
        if session.status != CashSessionStatus.OPEN:
            return Response({"detail": "La caja no está abierta."}, status=status.HTTP_409_CONFLICT)

        movement = CashMovement.objects.create(
            session=session,
            hotel=session.hotel,
            movement_type=ser.validated_data["movement_type"],
            currency=ser.validated_data.get("currency") or session.currency,
            amount=ser.validated_data["amount"],
            description=ser.validated_data.get("description") or "",
            created_by=request.user,
        )
        out = self.get_serializer(movement)
        return Response(out.data, status=status.HTTP_201_CREATED)

