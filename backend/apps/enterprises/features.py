from __future__ import annotations

from typing import Dict

from .models import Enterprise


# Definición centralizada de features por plan.
# Las claves se usan tanto en backend como en frontend.
PLAN_DEFAULT_FEATURES: Dict[str, Dict[str, bool]] = {
    "basic": {
        "afip": False,
        "mercado_pago": False,
        "whatsapp_bot": False,
        "otas": False,
        "housekeeping_advanced": False,
        "bank_reconciliation": False,
    },
    "medium": {
        "afip": True,
        "mercado_pago": True,
        "whatsapp_bot": True,
        "otas": False,
        "housekeeping_advanced": False,
        "bank_reconciliation": False,
    },
    "full": {
        "afip": True,
        "mercado_pago": True,
        "whatsapp_bot": True,
        "otas": True,
        "housekeeping_advanced": True,
        "bank_reconciliation": True,
    },
    "custom": {},
}


def get_effective_features(enterprise: Enterprise) -> Dict[str, bool]:
    """
    Devuelve el diccionario de features efectivos para una empresa,
    combinando los defaults del plan con los overrides en enabled_features.
    """
    if enterprise is None:
        return {}

    plan_key = (enterprise.plan_type or "").lower()
    base = PLAN_DEFAULT_FEATURES.get(plan_key, {})
    overrides = enterprise.enabled_features or {}

    # Comenzamos con los defaults del plan y aplicamos overrides explícitos.
    effective: Dict[str, bool] = dict(base)
    for key, value in overrides.items():
        # Solo considerar valores booleanos; ignorar nulls u otros tipos.
        if isinstance(value, bool):
            effective[key] = value
    return effective


def has_feature(enterprise: Enterprise, feature_name: str) -> bool:
    """
    Helper simple para consultar si una empresa tiene activa una funcionalidad.
    """
    return bool(get_effective_features(enterprise).get(feature_name))


