from decimal import Decimal
from datetime import timedelta, date
from apps.reservations.models import ReservationNight
from apps.rates.services.engine import compute_rate_for_date
from apps.rates.models import PromoRule, DiscountType, TaxRule
from django.db import models
from django.conf import settings

def quote_reservation_total(
    *,
    hotel,
    room,
    guests: int,
    check_in: date,
    check_out: date,
    channel=None,
    promotion_code: str | None = None,
    voucher_code: str | None = None,
) -> dict:
    """
    Cotización EXACTA (sin persistir nada) usando el mismo motor que se aplica al crear la reserva:
    - RatePlan/RateRule/occupancy prices
    - PromoRule por noche + PromoRule PER_RESERVATION prorrateada
    - TaxRule por noche + (opcional) TaxRule PER_RESERVATION prorrateada

    Devuelve:
      {
        "nights": [ {date, base_rate, extra_guest_fee, discount, tax, total_night, ...} ],
        "nights_count": int,
        "total": Decimal,
      }
    """
    if not (hotel and room and check_in and check_out):
        return {"nights": [], "nights_count": 0, "total": Decimal("0.00")}
    if check_out <= check_in:
        return {"nights": [], "nights_count": 0, "total": Decimal("0.00")}

    current = check_in
    nights = []

    # 1) Calcular cada noche con engine (sin promos por reserva, se prorratean después)
    while current < check_out:
        base_parts = compute_rate_for_date(
            room,
            guests,
            current,
            channel,
            promotion_code,
            voucher_code,
        )
        nights.append({"date": current, **base_parts})
        current += timedelta(days=1)

    # 2) Promos por reserva (PER_RESERVATION) solo si hay promotion_code explícito
    per_res_promos = PromoRule.objects.none()
    if promotion_code:
        per_res_promos = PromoRule.objects.filter(
            hotel=hotel,
            is_active=True,
            scope=PromoRule.PromoScope.PER_RESERVATION,
            code__iexact=str(promotion_code),
        )
        if channel:
            per_res_promos = per_res_promos.filter(
                models.Q(channel__isnull=True) | models.Q(channel=channel)
            )
        else:
            per_res_promos = per_res_promos.filter(channel__isnull=True)

    # base imponible por noche (sin descuentos prorrateados)
    bases = []
    for n in nights:
        subtotal = (
            Decimal(n["base_rate"])
            + (
                Decimal("0.00")
                if n.get("extra_guest_fee") == Decimal("0.00") and n.get("extra_guest_fee") == 0
                else Decimal(n["extra_guest_fee"])
            )
        )
        bases.append(subtotal)
    total_base = sum(bases) if bases else Decimal("0.00")

    total_res_discount = Decimal("0.00")
    applied_any = False
    for promo in per_res_promos.order_by("-priority"):
        applicable = False
        for n in nights:
            d = n["date"]
            if not (promo.start_date <= d <= promo.end_date):
                continue
            if not [
                promo.apply_mon,
                promo.apply_tue,
                promo.apply_wed,
                promo.apply_thu,
                promo.apply_fri,
                promo.apply_sat,
                promo.apply_sun,
            ][d.weekday()]:
                continue
            applicable = True
            break
        if not applicable:
            continue
        if total_base <= 0:
            break
        if promo.discount_type == DiscountType.PERCENT:
            total_res_discount = (Decimal(total_base) * (promo.discount_value / Decimal("100"))).quantize(
                Decimal("0.01")
            )
        else:
            total_res_discount = Decimal(promo.discount_value).quantize(Decimal("0.01"))
        applied_any = total_res_discount > 0
        if applied_any and not promo.combinable:
            break

    prorated = []
    if applied_any and total_base > 0:
        for idx, n in enumerate(nights):
            proportion = (bases[idx] / total_base) if total_base > 0 else Decimal("0.00")
            extra_discount = (total_res_discount * proportion).quantize(Decimal("0.01"))
            discount = Decimal(n["discount"]) + extra_discount
            taxable = (
                Decimal(n["base_rate"])
                + (
                    Decimal("0.00")
                    if n.get("extra_guest_fee") == Decimal("0.00") and n.get("extra_guest_fee") == 0
                    else Decimal(n["extra_guest_fee"])
                )
                - discount
            )
            if taxable < 0:
                taxable = Decimal("0.00")
            # Para exactitud de impuestos por noche, dependemos de lo que ya devolvió el engine
            total_night = (taxable + Decimal(n["tax"])).quantize(Decimal("0.01"))
            prorated.append({**n, "discount": discount, "total_night": total_night})
    else:
        prorated = nights

    # 3) Impuestos por reserva (PER_RESERVATION) si está habilitado
    if getattr(settings, "ENABLE_RESERVATION_TAX_PRORATION", False):
        per_res_taxes = TaxRule.objects.filter(
            hotel=hotel, is_active=True, scope=TaxRule.TaxScope.PER_RESERVATION
        )
        if channel:
            per_res_taxes = per_res_taxes.filter(models.Q(channel__isnull=True) | models.Q(channel=channel))
        else:
            per_res_taxes = per_res_taxes.filter(channel__isnull=True)

        total_res_tax = Decimal("0.00")
        applied_per_res_tax = None
        bases_after_discount = []
        for n in prorated:
            subtotal = (
                Decimal(n["base_rate"])
                + (
                    Decimal("0.00")
                    if n.get("extra_guest_fee") == Decimal("0.00") and n.get("extra_guest_fee") == 0
                    else Decimal(n["extra_guest_fee"])
                )
                - Decimal(n["discount"])
            )
            bases_after_discount.append(max(subtotal, Decimal("0.00")))
        total_taxable = sum(bases_after_discount) if bases_after_discount else Decimal("0.00")

        for t in per_res_taxes.order_by("-priority"):
            if t.amount_type == TaxRule.TaxAmountType.PERCENT:
                total_res_tax = (total_taxable * (t.percent / Decimal("100"))).quantize(Decimal("0.01"))
            else:
                total_res_tax = Decimal(t.fixed_amount).quantize(Decimal("0.01"))
            if total_res_tax > 0:
                applied_per_res_tax = t
                break

        if applied_per_res_tax and bases_after_discount and sum(bases_after_discount) > 0:
            total_taxable_sum = sum(bases_after_discount)
            new_prorated = []
            for idx, n in enumerate(prorated):
                proportion = (bases_after_discount[idx] / total_taxable_sum) if total_taxable_sum > 0 else Decimal("0.00")
                extra_tax = (total_res_tax * proportion).quantize(Decimal("0.01"))
                tax = Decimal(n["tax"]) + extra_tax
                total_night = (Decimal(n["total_night"]) + extra_tax).quantize(Decimal("0.01"))
                new_prorated.append({**n, "tax": tax, "total_night": total_night})
            prorated = new_prorated

    total = sum((Decimal(n["total_night"]) for n in prorated), Decimal("0.00")).quantize(Decimal("0.01"))
    return {"nights": prorated, "nights_count": len(prorated), "total": total}

def compute_nightly_rate(room, guests, on_date=None, channel=None) -> dict:
    # Si no se provee fecha, usar lógica anterior como aproximación
    if on_date is None:
        base = room.base_price or Decimal('0.00')
        included = room.capacity or 1
        extra_guests = max((guests or 1) - included, 0)
        extra = (room.extra_guest_fee or Decimal('0.00')) * Decimal(extra_guests)
        return {
            'base_rate': base,
            'extra_guest_fee': extra,
            'discount': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'total_night': (base + extra).quantize(Decimal('0.01')),
        }
    return compute_rate_for_date(room, guests, on_date, channel)

def generate_nights_for_reservation(reservation):
    from apps.rates.services.engine import compute_rate_for_date
    ReservationNight.objects.filter(reservation=reservation).delete()
    current = reservation.check_in
    nights = []
    # Primero calcular sin aplicar promos de alcance por reserva para obtener bases
    while current < reservation.check_out:
        base_parts = compute_rate_for_date(
            reservation.room,
            reservation.guests,
            current,
            reservation.channel,
            reservation.promotion_code,
            getattr(reservation, 'voucher_code', None)
        )
        nights.append({ 'date': current, **base_parts })
        current += timedelta(days=1)

    # Aplicar promos por reserva SOLO si hay promotion_code explícito
    # Evita descuentos "fantasma" cuando no se ingresó cupón
    per_res_promos = PromoRule.objects.none()
    if reservation.promotion_code:
        per_res_promos = PromoRule.objects.filter(
            hotel=reservation.hotel,
            is_active=True,
            scope=PromoRule.PromoScope.PER_RESERVATION,
            code__iexact=str(reservation.promotion_code),
        )
        # Filtrar por canal si corresponde
        if reservation.channel:
            per_res_promos = per_res_promos.filter(models.Q(channel__isnull=True) | models.Q(channel=reservation.channel))
        else:
            per_res_promos = per_res_promos.filter(channel__isnull=True)

    # Determinar base imponible por noche sin descuento
    bases = []
    for n in nights:
        subtotal = (n['base_rate'] + (Decimal('0.00') if n.get('extra_guest_fee') == Decimal('0.00') and n.get('extra_guest_fee') == 0 else n['extra_guest_fee']))
        bases.append(subtotal)
    total_base = sum(bases) if bases else Decimal('0.00')

    # Calcular descuento total por reserva y prorratear
    total_res_discount = Decimal('0.00')
    applied_any = False
    for promo in per_res_promos.order_by('-priority'):
        # Verificar rango de fechas y DOW en al menos una noche
        applicable = False
        for idx, n in enumerate(nights):
            d = n['date']
            if not (promo.start_date <= d <= promo.end_date):
                continue
            if not [promo.apply_mon, promo.apply_tue, promo.apply_wed, promo.apply_thu, promo.apply_fri, promo.apply_sat, promo.apply_sun][d.weekday()]:
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
        # No combinar si no es combinable
        if applied_any and not promo.combinable:
            break

    # Prorrateo y recálculo de impuestos por noche
    prorated = []
    if applied_any and total_base > 0:
        for idx, n in enumerate(nights):
            proportion = (bases[idx] / total_base) if total_base > 0 else Decimal('0.00')
            extra_discount = (total_res_discount * proportion).quantize(Decimal('0.01'))
            discount = Decimal(n['discount']) + extra_discount
            taxable = (n['base_rate'] + (Decimal('0.00') if n.get('extra_guest_fee') == Decimal('0.00') and n.get('extra_guest_fee') == 0 else n['extra_guest_fee']) - discount)
            if taxable < 0:
                taxable = Decimal('0.00')
            # Recalcular impuestos acumulando los TaxRule en engine podría duplicar lógica; asumimos tax proporcional
            # Para exactitud, dejamos tax igual si no podemos recalcular aquí. Opcional: invocar una función para tax.
            # Como simplificación, mantenemos tax original pero ajustamos total.
            total_night = (taxable + n['tax']).quantize(Decimal('0.01'))
            prorated.append({ **n, 'discount': discount, 'total_night': total_night })
    else:
        prorated = nights

    # Calcular y prorratear impuestos por reserva (deshabilitado por defecto para evitar doble imposición)
    if getattr(settings, 'ENABLE_RESERVATION_TAX_PRORATION', False):
        per_res_taxes = TaxRule.objects.filter(hotel=reservation.hotel, is_active=True, scope=TaxRule.TaxScope.PER_RESERVATION)
        if reservation.channel:
            per_res_taxes = per_res_taxes.filter(models.Q(channel__isnull=True) | models.Q(channel=reservation.channel))
        else:
            per_res_taxes = per_res_taxes.filter(channel__isnull=True)

        total_res_tax = Decimal('0.00')
        applied_per_res_tax = None
        if per_res_taxes.exists():
            # base imponible total luego de descuentos prorrateados
            bases_after_discount = []
            for n in prorated:
                subtotal = (n['base_rate'] + (Decimal('0.00') if n.get('extra_guest_fee') == Decimal('0.00') and n.get('extra_guest_fee') == 0 else n['extra_guest_fee']) - Decimal(n['discount']))
                bases_after_discount.append(max(subtotal, Decimal('0.00')))
            total_taxable = sum(bases_after_discount) if bases_after_discount else Decimal('0.00')
            for t in per_res_taxes.order_by('-priority'):
                if t.amount_type == TaxRule.TaxAmountType.PERCENT:
                    total_res_tax = (total_taxable * (t.percent / Decimal('100'))).quantize(Decimal('0.01'))
                else:
                    total_res_tax = Decimal(t.fixed_amount).quantize(Decimal('0.01'))
                if total_res_tax > 0:
                    applied_per_res_tax = t
                    break

        # Prorratear impuesto por reserva
        if 'bases_after_discount' in locals() and applied_per_res_tax and bases_after_discount and sum(bases_after_discount) > 0:
            total_taxable_sum = sum(bases_after_discount)
            new_prorated = []
            for idx, n in enumerate(prorated):
                proportion = (bases_after_discount[idx] / total_taxable_sum) if total_taxable_sum > 0 else Decimal('0.00')
                extra_tax = (total_res_tax * proportion).quantize(Decimal('0.01'))
                tax = Decimal(n['tax']) + extra_tax
                total_night = (Decimal(n['total_night']) + extra_tax).quantize(Decimal('0.01'))
                tax_details = list(n.get('applied_taxes_detail') or [])
                tax_details.append({
                    'id': applied_per_res_tax.id,
                    'name': applied_per_res_tax.name,
                    'percent': float(applied_per_res_tax.percent) if applied_per_res_tax.amount_type == TaxRule.TaxAmountType.PERCENT else None,
                    'type': applied_per_res_tax.amount_type,
                    'scope': applied_per_res_tax.scope,
                    'amount': float(extra_tax),
                })
                nn = { **n, 'tax': tax, 'total_night': total_night, 'applied_taxes_detail': tax_details }
                new_prorated.append(nn)
            prorated = new_prorated

    # Guardar noches
    for n in prorated:
        filtered_parts = {k: v for k, v in n.items() if k in [
            'base_rate', 'extra_guest_fee', 'discount', 'tax', 'total_night'
        ]}
        ReservationNight.objects.create(
            reservation=reservation,
            hotel=reservation.hotel,
            room=reservation.room,
            date=n['date'],
            **filtered_parts,
        )

def recalc_reservation_totals(reservation):
    from django.db.models import Sum
    nights_total = reservation.nights.aggregate(s=Sum('total_night'))['s'] or Decimal('0.00')
    charges_total = reservation.charges.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    total = (nights_total + charges_total).quantize(Decimal('0.01'))
    # Evitar disparar post_save de nuevo para no entrar en recursión
    type(reservation).objects.filter(pk=reservation.pk).update(total_price=total)
    # Asegurar que el objeto en memoria refleje el total para respuestas inmediatas
    try:
        reservation.total_price = total
    except Exception:
        pass