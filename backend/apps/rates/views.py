from rest_framework import viewsets, permissions
from django.db import models
from .models import PriceMode, RatePlan, RateRule, PromoRule, TaxRule
from .serializers import RatePlanSerializer, RateRuleSerializer, PromoRuleSerializer, TaxRuleSerializer
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.rooms.models import Room
from apps.rates.services.engine import compute_rate_for_date
from apps.reservations.models import ReservationChannel
from decimal import Decimal
from apps.rates.models import PromoRule, DiscountType

class RatePlanViewSet(viewsets.ModelViewSet):
    queryset = RatePlan.objects.all().select_related("hotel")
    serializer_class = RatePlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class RateRuleViewSet(viewsets.ModelViewSet):
    serializer_class = RateRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = RateRule.objects.all().select_related("plan", "target_room")
        hotel_id = self.request.query_params.get("hotel_id")
        plan_id = self.request.query_params.get("plan_id")
        on_date = self.request.query_params.get("on_date")

        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        if hotel_id:
            qs = qs.filter(plan__hotel_id=hotel_id)
        if on_date:
            try:
                d = datetime.strptime(on_date, "%Y-%m-%d").date()
                qs = qs.filter(start_date__lte=d, end_date__gte=d)
            except ValueError:
                pass
        return qs.order_by("-priority", "start_date")


class PromoRuleViewSet(viewsets.ModelViewSet):
    queryset = PromoRule.objects.all().select_related("hotel", "plan", "target_room")
    serializer_class = PromoRuleSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaxRuleViewSet(viewsets.ModelViewSet):
    queryset = TaxRule.objects.all().select_related("hotel")
    serializer_class = TaxRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def preview_rate(request):
    room_id = request.query_params.get("room_id")
    date_str = request.query_params.get("date")
    guests_str = request.query_params.get("guests", "1")
    channel = request.query_params.get("channel")  # opcional
    promo_code = request.query_params.get("promotion_code")  # opcional

    if not room_id or not date_str:
        return Response({"detail": "room_id y date son obligatorios (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        on_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"detail": "date inválida. Formato esperado YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guests = max(int(guests_str), 1)
    except ValueError:
        return Response({"detail": "guests debe ser entero >= 1."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = Room.objects.select_related("hotel").get(pk=room_id)
    except Room.DoesNotExist:
        return Response({"detail": "room_id no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    data = compute_rate_for_date(room, guests, on_date, channel, promo_code)
    return Response({
        "room_id": room.id,
        "hotel_id": room.hotel_id,
        "date": on_date.isoformat(),
        "guests": guests,
        "channel": channel,
        "pricing": data,
    })

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def rate_choices(request):
    room_types = [{"value": v, "label": l} for v, l in Room._meta.get_field("room_type").choices]
    price_modes = [{"value": v, "label": l} for v, l in PriceMode.choices]
    channels = [{"value": v, "label": l} for v, l in ReservationChannel.choices]
    deposit_types = [
        {"value": "none", "label": "Sin adelanto"},
        {"value": "percentage", "label": "Porcentaje"},
        {"value": "fixed", "label": "Monto fijo"},
    ]
    deposit_dues = [
        {"value": "confirmation", "label": "Al confirmar"},
        {"value": "days_before", "label": "Días antes del check-in"},
        {"value": "check_in", "label": "Al check-in"},
    ]
    tax_amount_types = [{"value": v, "label": l} for v, l in TaxRule.TaxAmountType.choices]
    tax_scopes = [{"value": v, "label": l} for v, l in TaxRule.TaxScope.choices]
    return Response({
        "room_types": room_types,
        "price_modes": price_modes,
        "channels": channels,
        "deposit_types": deposit_types,
        "deposit_dues": deposit_dues,
        "tax_amount_types": tax_amount_types,
        "tax_scopes": tax_scopes,
    })

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def preview_rate_range(request):
    room_id = request.query_params.get("room_id")
    start_str = request.query_params.get("start")
    end_str = request.query_params.get("end")
    guests_str = request.query_params.get("guests", "1")
    channel = request.query_params.get("channel")
    promo_code = request.query_params.get("promotion_code")

    if not room_id or not start_str or not end_str:
        return Response({"detail": "room_id, start y end son obligatorios (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        assert start <= end
    except Exception:
        return Response({"detail": "Rango de fechas inválido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        guests = max(int(guests_str), 1)
    except ValueError:
        return Response({"detail": "guests debe ser entero >= 1."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = Room.objects.select_related("hotel").get(pk=room_id)
    except Room.DoesNotExist:
        return Response({"detail": "room_id no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    current = start
    raw_days = []
    while current <= end:
        raw_days.append({
            "date": current,
            "pricing": compute_rate_for_date(room, guests, current, channel, promo_code),
        })
        current += timedelta(days=1)

    # Manejar promos de alcance por reserva: calcular descuento total y prorratear
    bases = []
    for d in raw_days:
        p = d["pricing"]
        bases.append(p["base_rate"] + p["extra_guest_fee"] - p["discount"])  # base neta sin impuestos
    total_base = sum(bases) if bases else Decimal('0.00')

    per_res_promos = PromoRule.objects.filter(hotel=room.hotel, is_active=True, scope=PromoRule.PromoScope.PER_RESERVATION)
    if channel:
        per_res_promos = per_res_promos.filter(models.Q(channel__isnull=True) | models.Q(channel=channel))
    else:
        per_res_promos = per_res_promos.filter(channel__isnull=True)
    if promo_code:
        per_res_promos = per_res_promos.filter(models.Q(code__isnull=True) | models.Q(code__iexact=str(promo_code)))
    else:
        per_res_promos = per_res_promos.filter(code__isnull=True)

    total_res_discount = Decimal('0.00')
    applied_any = False
    applied_per_res_promo = None
    for promo in per_res_promos.order_by('-priority'):
        applicable = False
        for d in raw_days:
            dd = d['date']
            if not (promo.start_date <= dd <= promo.end_date):
                continue
            if not [promo.apply_mon, promo.apply_tue, promo.apply_wed, promo.apply_thu, promo.apply_fri, promo.apply_sat, promo.apply_sun][dd.weekday()]:
                continue
            applicable = True
            break
        if not applicable:
            continue
        if total_base <= 0:
            break
        if promo.discount_type == DiscountType.PERCENT:
            total_res_discount = (Decimal(total_base) * (promo.discount_value / Decimal('100'))).quantize(Decimal('0.01'))
        else:
            total_res_discount = Decimal(promo.discount_value).quantize(Decimal('0.01'))
        applied_any = total_res_discount > 0
        if applied_any and not applied_per_res_promo:
            applied_per_res_promo = promo
        if applied_any and not promo.combinable:
            break

    days = []
    if applied_any and total_base > 0:
        for idx, d in enumerate(raw_days):
            p = d['pricing']
            proportion = (bases[idx] / total_base) if total_base > 0 else Decimal('0.00')
            extra_discount = (total_res_discount * proportion).quantize(Decimal('0.01'))
            discount = p['discount'] + extra_discount
            taxable = (p['base_rate'] + p['extra_guest_fee'] - discount)
            if taxable < 0:
                taxable = Decimal('0.00')
            # Mantener el mismo cálculo de impuestos proporcional (sin recalcular reglas específicas)
            total_night = (taxable + p['tax']).quantize(Decimal('0.01'))
            details = list(p.get('applied_promos_detail') or [])
            if applied_per_res_promo:
                details.append({
                    'id': applied_per_res_promo.id,
                    'name': applied_per_res_promo.name,
                    'code': applied_per_res_promo.code,
                    'scope': 'per_reservation',
                    'amount': float(extra_discount),
                })
            days.append({
                "date": d['date'].isoformat(),
                "pricing": { **p, 'discount': discount, 'total_night': total_night, 'applied_promos_detail': details },
            })
    else:
        days = [{ "date": d['date'].isoformat(), "pricing": d['pricing'] } for d in raw_days]

    return Response({
        "room_id": room.id,
        "hotel_id": room.hotel_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "guests": guests,
        "channel": channel,
        "days": days,
    })

def get_applicable_rule(room, on_date, channel):
    # similar a engine: devuelve la primera regla aplicable por prioridad plan/regla
    plans = RatePlan.objects.filter(hotel=room.hotel, is_active=True).order_by("-priority", "id").prefetch_related("rules")
    for plan in plans:
        for rule in sorted(plan.rules.all(), key=lambda r: r.priority, reverse=True):
            if not (rule.start_date <= on_date <= rule.end_date):
                continue
            dow = on_date.weekday()
            if not [rule.apply_mon, rule.apply_tue, rule.apply_wed, rule.apply_thu, rule.apply_fri, rule.apply_sat, rule.apply_sun][dow]:
                continue
            if rule.target_room_id and rule.target_room_id != room.id:
                continue
            if rule.target_room_type and rule.target_room_type != room.room_type:
                continue
            if rule.channel and channel and rule.channel != channel:
                continue
            if rule.channel and not channel:
                continue
            return rule
    return None