from __future__ import annotations

from typing import Optional

from apps.enterprises.features import has_feature


HOUSEKEEPING_FEATURE_KEY = "housekeeping_advanced"


def is_housekeeping_enabled_for_enterprise(enterprise) -> bool:
    """
    Determina si el módulo de housekeeping está habilitado para una empresa
    (según plan comercial + overrides).
    """
    if not enterprise:
        return False
    return bool(has_feature(enterprise, HOUSEKEEPING_FEATURE_KEY))


def is_housekeeping_enabled_for_hotel(hotel) -> bool:
    """
    Determina si el módulo de housekeeping está habilitado para el hotel.
    Regla: se toma desde la Enterprise del hotel (plan/feature flags).
    """
    if not hotel:
        return False
    enterprise = getattr(hotel, "enterprise", None)
    return is_housekeeping_enabled_for_enterprise(enterprise)


def is_housekeeping_enabled_for_hotel_id(hotel_id: Optional[int]) -> bool:
    """
    Variante utilitaria para cuando solo tenemos el hotel_id.
    """
    if not hotel_id:
        return False
    try:
        from apps.core.models import Hotel
    except Exception:
        return False

    hotel = (
        Hotel.objects.select_related("enterprise")
        .only("id", "enterprise_id", "enterprise__plan_type", "enterprise__enabled_features")
        .filter(id=hotel_id)
        .first()
    )
    return is_housekeeping_enabled_for_hotel(hotel)


