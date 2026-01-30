from datetime import date
from decimal import Decimal
from typing import Optional
from apps.rooms.models import Room
from apps.rates.models import RateRule, RatePlan, PromoRule, TaxRule, DiscountType, PriceMode

def _is_rule_applicable(rule: RateRule, room: Room, on_date: date, channel: Optional[str] = None) -> bool:
    if not (rule.start_date <= on_date <= rule.end_date):
        return False
    
    weekdays = on_date.weekday()
    dow_map = [rule.apply_mon, rule.apply_tue, rule.apply_wed, rule.apply_thu, rule.apply_fri, rule.apply_sat, rule.apply_sun]
    if not dow_map[weekdays]:
        return False
    
    # Target Match 
    if rule.target_room_id and rule.target_room_id != room.id:
        return False
    if rule.target_room_type and rule.target_room_type != room.room_type:
        return False
    
    # Channel Match (si la regla define canal, debe coincidir)
    if rule.channel and channel and rule.channel != channel:
        return False
    if rule.channel and channel is None:
        return False
    if rule.closed:
        return False
    
    return True

def get_applicable_rule(room: Room, on_date: date, channel: Optional[str] = None, include_closed: bool = True) -> Optional[RateRule]:
    """Devuelve la primera regla aplicable por prioridad de plan y regla.

    - include_closed=True: considera reglas cerradas (para restricciones CTA/CTD, min/max stay, closed).
    - include_closed=False: ignora reglas con closed=True (similar a pricing).
    """
    plans_qs = RatePlan.objects.filter(hotel=room.hotel, is_active=True).order_by('-priority', 'id').prefetch_related('rules')
    for plan in plans_qs:
        rules = sorted(plan.rules.all(), key=lambda r: r.priority, reverse=True)
        for rule in rules:
            if not (rule.start_date <= on_date <= rule.end_date):
                continue
            weekday = on_date.weekday()
            dow_map = [rule.apply_mon, rule.apply_tue, rule.apply_wed, rule.apply_thu, rule.apply_fri, rule.apply_sat, rule.apply_sun]
            if not dow_map[weekday]:
                continue
            if rule.target_room_id and rule.target_room_id != room.id:
                continue
            if rule.target_room_type and rule.target_room_type != room.room_type:
                continue
            if rule.channel and channel and rule.channel != channel:
                continue
            if rule.channel and channel is None:
                continue
            if not include_closed and rule.closed:
                continue
            return rule
    return None

def compute_rate_for_date(
    room: Room,
    guests: int,
    on_date: date,
    channel: Optional[str] = None,
    promotion_code: Optional[str] = None,
    voucher_code: Optional[str] = None,
    price_source: Optional[str] = None,
) -> Decimal:
    """
    Calcula el pricing por noche.

    price_source:
      - "primary" (default): usa room.base_price
      - "secondary": usa room.secondary_price si existe; si no, hace fallback a base_price
    """
    if str(price_source or "").lower() == "secondary" and room.secondary_price is not None:
        base_room_price = room.secondary_price
    else:
        base_room_price = room.base_price
    base_room_price = base_room_price or Decimal("0.00")
    included_capacity = room.capacity or 1
    guest = max(int(guests or 1), 1)
    extra_guests = max(guest - included_capacity, 0)
    
    # Buscar planes activos en el hotel por prioridad
    plans_qs = RatePlan.objects.filter(hotel=room.hotel, is_active=True).order_by('-priority', "id")
    candidate_rules = []
    for plan in plans_qs:
        rules = [
            r for r in plan.rules.all()
            if _is_rule_applicable(r, room, on_date, channel)
        ]
        candidate_rules.extend([(plan.priority, r.priority, r) for r in rules])
    
    candidate_rules.sort(key=lambda x: (x[0], x[1]), reverse=True)

    base_rate = base_room_price
    extra_guest_fee = (room.extra_guest_fee or Decimal('0.00')) * Decimal(extra_guests)

    used_occupancy_price = False

    for _, _, rule in candidate_rules:
        # Occupancy price match exacto
        occ = rule.occupancy_prices.filter(occupancy=guest).first()
        if occ:
            base_rate = occ.price
            extra_guest_fee = Decimal('0.00')
            used_occupancy_price = True
            break
        
        # Sin price por ocupación, usar base_amount si existe
        if rule.base_amount is not None:
            if rule.price_mode == PriceMode.ABSOLUTE:
                base_rate = rule.base_amount
            else:
                base_rate = (base_room_price + rule.base_amount).quantize(Decimal('0.01'))

        # Override de extra_guest_fee si fue provisto
        if rule.extra_guest_fee_amount is not None:
            extra_guest_fee = (rule.extra_guest_fee_amount or Decimal("00.0")) * Decimal(extra_guests)
        
        # Tomoamos esa regla y salimos (ya que estan ordenadas por prioridad)
        break

    # Aplicar promociones (solo si se ingresó código)
    discount = Decimal('0.00')
    if promotion_code:
        promos_qs = PromoRule.objects.filter(
            hotel=room.hotel,
            is_active=True,
            start_date__lte=on_date,
            end_date__gte=on_date,
            code__iexact=str(promotion_code),
        ).order_by('-priority')
    else:
        promos_qs = PromoRule.objects.none()
    applied_promos = []
    applied_promos_detail = []
    for promo in promos_qs:
        # Promos de alcance por reserva no se aplican aquí (se prorratean fuera)
        if promo.scope == PromoRule.PromoScope.PER_RESERVATION:
            continue
        # DOW
        if not [promo.apply_mon, promo.apply_tue, promo.apply_wed, promo.apply_thu, promo.apply_fri, promo.apply_sat, promo.apply_sun][on_date.weekday()]:
            continue
        # Target
        if promo.target_room_id and promo.target_room_id != room.id:
            continue
        if promo.target_room_type and promo.target_room_type != room.room_type:
            continue
        # Channel
        if promo.channel and channel and promo.channel != channel:
            continue
        if promo.channel and channel is None:
            continue
        # Code
        if promo.code and promotion_code and promo.code.lower() != str(promotion_code).lower():
            continue
        if promo.code and not promotion_code:
            continue

        subtotal_before_discount = (base_rate + (Decimal('0.00') if used_occupancy_price else extra_guest_fee))
        if promo.discount_type == DiscountType.PERCENT:
            row_discount = (subtotal_before_discount * (promo.discount_value / Decimal('100'))).quantize(Decimal('0.01'))
        else:
            row_discount = Decimal(promo.discount_value).quantize(Decimal('0.01'))
        if row_discount > 0:
            discount += row_discount
            applied_promos.append(promo.id)
            applied_promos_detail.append({
                'id': promo.id,
                'name': promo.name,
                'code': promo.code,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
                'amount': float(row_discount)
            })
            if not promo.combinable:
                break

    # Aplicar vouchers (solo si se ingresó código)
    voucher_discount = Decimal('0.00')
    applied_vouchers = []
    applied_vouchers_detail = []
    if voucher_code:
        from apps.payments.models import RefundVoucher
        try:
            voucher = RefundVoucher.objects.get(
                code__iexact=str(voucher_code),
                hotel=room.hotel,
                status='active'
            )
            if voucher.can_be_used():
                # El voucher se aplica como descuento fijo
                voucher_discount = min(voucher.remaining_amount, (base_rate + (Decimal('0.00') if used_occupancy_price else extra_guest_fee) - discount))
                if voucher_discount > 0:
                    applied_vouchers.append(voucher.id)
                    applied_vouchers_detail.append({
                        'id': voucher.id,
                        'code': voucher.code,
                        'amount': float(voucher_discount),
                        'remaining_amount': float(voucher.remaining_amount)
                    })
        except RefundVoucher.DoesNotExist:
            pass

    # Total de descuentos (promociones + vouchers)
    total_discount = discount + voucher_discount

    # Impuestos sobre (base + extra - descuento total)
    tax = Decimal('0.00')
    taxable_base = (base_rate + (Decimal('0.00') if used_occupancy_price else extra_guest_fee) - total_discount)
    if taxable_base < 0:
        taxable_base = Decimal('0.00')
    taxes_qs = TaxRule.objects.filter(hotel=room.hotel, is_active=True).order_by('-priority')
    applied_taxes_detail = []
    for t in taxes_qs:
        if t.channel and channel and t.channel != channel:
            continue
        if t.channel and channel is None:
            continue
        # calcular por alcance/tipo
        if t.amount_type == TaxRule.TaxAmountType.PERCENT:
            base_for_tax = taxable_base
            row_tax = (base_for_tax * (t.percent / Decimal('100'))).quantize(Decimal('0.01'))
        else:
            if t.scope == TaxRule.TaxScope.PER_NIGHT:
                row_tax = Decimal(t.fixed_amount).quantize(Decimal('0.01'))
            elif t.scope == TaxRule.TaxScope.PER_GUEST_PER_NIGHT:
                # guests no llega aquí; asumimos extra_guests+incluidos=guest. Necesitamos el número de guests
                # Como compute_rate_for_date recibe guests, usamos 'guest'
                row_tax = (Decimal(t.fixed_amount) * Decimal(guest)).quantize(Decimal('0.01'))
            else:
                # per_reservation será prorrateado fuera; aquí lo ignoramos
                row_tax = Decimal('0.00')
        if row_tax > 0:
            applied_taxes_detail.append({
                'id': t.id,
                'name': t.name,
                'percent': float(t.percent) if t.amount_type == TaxRule.TaxAmountType.PERCENT else None,
                'type': t.amount_type,
                'scope': t.scope,
                'amount': float(row_tax),
            })
        tax += row_tax

    total_night = (taxable_base + tax).quantize(Decimal('0.01'))
    return {
        "base_rate": base_rate.quantize(Decimal('0.01')),
        "extra_guest_fee": (Decimal("0.00") if used_occupancy_price else extra_guest_fee).quantize(Decimal("0.01")),
        "discount": total_discount,  # Total de descuentos (promociones + vouchers)
        "promotion_discount": discount,  # Solo descuentos de promociones
        "voucher_discount": voucher_discount,  # Solo descuentos de vouchers
        "tax": tax,
        "total_night": total_night,
        "applied_promos": applied_promos,
        "applied_promos_detail": applied_promos_detail,
        "applied_vouchers": applied_vouchers,
        "applied_vouchers_detail": applied_vouchers_detail,
        "applied_taxes_detail": applied_taxes_detail,
    }
            