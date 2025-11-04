from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Dict, Any

from django.db import transaction

from apps.otas.models import (
    OtaProvider,
    OtaRoomTypeMapping,
    OtaRatePlanMapping,
    OtaSyncJob,
    OtaSyncLog,
    OtaConfig,
)

import json
import time
import requests


@dataclass
class AriPushResult:
    success: bool
    pushed: int = 0
    errors: int = 0
    details: Dict[str, Any] | None = None


class OtaAdapterBase:
    """Interfaz base de adaptadores ARI."""
    provider = "base"

    def __init__(self, is_mock: bool = True, config: OtaConfig | None = None):
        self.is_mock = is_mock
        self.config = config

    def is_available(self) -> bool:
        return True

    def push_ari(self, payload: Dict[str, Any]) -> AriPushResult:
        # En mock simplemente retorna éxito con conteo
        return AriPushResult(success=True, pushed=len(payload.get("items", [])), details={"mock": True})

    # Pull de reservas (interfaz)
    def pull_reservations(self, since: datetime) -> Dict[str, Any]:
        # En mock, generamos 1 reserva sintética para demo
        return {
            "items": [
                {
                    "external_id": f"demo-{since.strftime('%H%M%S')}",
                    "guest_name": "Demo Guest",
                    "check_in": (since.date() + timedelta(days=2)).isoformat(),
                    "check_out": (since.date() + timedelta(days=4)).isoformat(),
                    "room_type": "DOUBLE",
                    "rate_plan": "STANDARD",
                }
            ]
        }


class BookingAdapter(OtaAdapterBase):
    provider = OtaProvider.BOOKING

    def is_available(self) -> bool:
        # Disponible si tenemos al menos base_url; credenciales pueden ser opcionales en TEST
        return bool(self.config and self.config.booking_base_url)

    def push_ari(self, payload: Dict[str, Any]) -> AriPushResult:
        if self.is_mock or not self.is_available():
            return super().push_ari(payload)
        # Llamada HTTP "real" (sandbox). Si falla, hacemos fallback a mock.
        base_url: str = (self.config.booking_base_url or "").rstrip("/")
        # Si el usuario usa httpbin para pruebas, posteamos a /post; si no, a un path genérico
        path = "/post" if "httpbin.org" in base_url else "/ari/push"
        url = f"{base_url}{path}"

        headers = {
            "Content-Type": "application/json",
            "X-Provider": "booking",
            "X-Mode": (self.config.booking_mode or "test") if self.config else "test",
        }
        # Algunas integraciones usan bearer o basic; no logueamos secretos
        if self.config and self.config.booking_client_id and self.config.booking_client_secret:
            headers["X-Client-Id"] = self.config.booking_client_id

        body = {
            "hotel_id": self.config.booking_hotel_id if self.config else None,
            "mode": self.config.booking_mode if self.config else "test",
            "items": payload.get("items", []),
        }

        # Backoff simple (2 intentos)
        for attempt in range(2):
            try:
                resp = requests.post(url, data=json.dumps(body), headers=headers, timeout=10)
                ok = 200 <= resp.status_code < 300
                details = {
                    "mock": False,
                    "status": resp.status_code,
                    "endpoint": url,
                }
                if ok:
                    return AriPushResult(success=True, pushed=len(payload.get("items", [])), errors=0, details=details)
                # si 429/5xx, reintentar una vez
                if resp.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.0)
                    continue
                return AriPushResult(success=False, pushed=0, errors=len(payload.get("items", [])), details=details)
            except Exception:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                break

        # Fallback
        return AriPushResult(success=True, pushed=len(payload.get("items", [])), details={"mock": True, "fallback": True})

    def pull_reservations(self, since: datetime) -> Dict[str, Any]:
        if self.is_mock or not self.is_available():
            return super().pull_reservations(since)
        base_url: str = (self.config.booking_base_url or "").rstrip("/")
        path = "/get" if "httpbin.org" in base_url else "/reservations/changes"
        url = f"{base_url}{path}"
        params = {"since": since.isoformat()}
        headers = {"X-Provider": "booking"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if 200 <= resp.status_code < 300:
                return {"items": []}  # echo sin formato real
        except Exception:
            pass
        return super().pull_reservations(since)


class AirbnbAdapter(OtaAdapterBase):
    provider = OtaProvider.AIRBNB

    def is_available(self) -> bool:
        return bool(self.config and self.config.airbnb_base_url)

    def push_ari(self, payload: Dict[str, Any]) -> AriPushResult:
        if self.is_mock or not self.is_available():
            return super().push_ari(payload)

        base_url: str = (self.config.airbnb_base_url or "").rstrip("/")
        path = "/post" if "httpbin.org" in base_url else "/ari/push"
        url = f"{base_url}{path}"

        headers = {
            "Content-Type": "application/json",
            "X-Provider": "airbnb",
            "X-Mode": (self.config.airbnb_mode or "test") if self.config else "test",
        }
        if self.config and self.config.airbnb_client_id and self.config.airbnb_client_secret:
            headers["X-Client-Id"] = self.config.airbnb_client_id

        body = {
            "account_id": self.config.airbnb_account_id if self.config else None,
            "mode": self.config.airbnb_mode if self.config else "test",
            "items": payload.get("items", []),
        }

        for attempt in range(2):
            try:
                resp = requests.post(url, data=json.dumps(body), headers=headers, timeout=10)
                ok = 200 <= resp.status_code < 300
                details = {"mock": False, "status": resp.status_code, "endpoint": url}
                if ok:
                    return AriPushResult(success=True, pushed=len(payload.get("items", [])), errors=0, details=details)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.0)
                    continue
                return AriPushResult(success=False, pushed=0, errors=len(payload.get("items", [])), details=details)
            except Exception:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                break

        return AriPushResult(success=True, pushed=len(payload.get("items", [])), details={"mock": True, "fallback": True})

    def pull_reservations(self, since: datetime) -> Dict[str, Any]:
        if self.is_mock or not self.is_available():
            return super().pull_reservations(since)
        base_url: str = (self.config.airbnb_base_url or "").rstrip("/")
        path = "/get" if "httpbin.org" in base_url else "/reservations/changes"
        url = f"{base_url}{path}"
        params = {"since": since.isoformat()}
        headers = {"X-Provider": "airbnb"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if 200 <= resp.status_code < 300:
                return {"items": []}
        except Exception:
            pass
        return super().pull_reservations(since)


def get_adapter(provider: str, hotel_id: int) -> OtaAdapterBase:
    cfg: OtaConfig | None = (
        OtaConfig.objects.filter(hotel_id=hotel_id, provider=provider, is_active=True).first()
    )
    if provider == OtaProvider.BOOKING:
        # Si no hay config o faltan datos, operar en modo mock para no fallar
        is_mock = not (cfg and cfg.booking_base_url)
        return BookingAdapter(is_mock=is_mock, config=cfg)
    if provider == OtaProvider.AIRBNB:
        is_mock = not (cfg and cfg.airbnb_base_url)
        return AirbnbAdapter(is_mock=is_mock, config=cfg)
    return OtaAdapterBase(config=cfg)


@transaction.atomic
def build_mock_ari_payload(
    hotel_id: int,
    provider: str,
    date_from: date,
    date_to: date,
) -> Dict[str, Any]:
    # Construimos un payload minimal con mapeos activos
    room_types = list(
        OtaRoomTypeMapping.objects.filter(hotel_id=hotel_id, provider=provider, is_active=True)
        .values("room_type_code", "provider_code")
    )
    rate_plans = list(
        OtaRatePlanMapping.objects.filter(hotel_id=hotel_id, provider=provider, is_active=True)
        .values("rate_plan_code", "provider_code", "currency")
    )

    items: list[Dict[str, Any]] = []
    for rt in room_types:
        for rp in rate_plans:
            items.append({
                "room_type": rt["provider_code"],
                "rate_plan": rp["provider_code"],
                "currency": rp["currency"],
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                # En real: disponibilidad diaria y precio por noche
                "availability": 1,
                "price": 10000,
            })

    return {"hotel_id": hotel_id, "provider": provider, "items": items}


def push_ari_for_hotel(job: OtaSyncJob, hotel_id: int, provider: str, date_from: date, date_to: date) -> Dict[str, Any]:
    from django.utils import timezone
    import traceback
    
    try:
        adapter = get_adapter(provider, hotel_id)
        payload = build_mock_ari_payload(hotel_id, provider, date_from, date_to)

        # Log de request
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PUSH_ARI_REQUEST",
            payload={"provider": provider, "items": len(payload.get("items", []))},
        )

        result = adapter.push_ari(payload)

        # Log de response
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PUSH_ARI_RESPONSE",
            payload={"pushed": result.pushed, "errors": result.errors, **(result.details or {})},
        )

        job.stats = {
            **(job.stats or {}),
            "pushed": result.pushed,
            "errors": result.errors,
        }
        return job.stats
    except Exception as e:
        # Registrar error en log con detalles completos
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="PUSH_ARI_SERVICE_ERROR",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "timestamp": timezone.now().isoformat(),
            },
        )
        raise  # Re-lanzar para que el task lo maneje


def pull_reservations_for_hotel(job: OtaSyncJob, hotel_id: int, provider: str, since: datetime) -> Dict[str, Any]:
    from django.utils import timezone
    import traceback
    
    try:
        adapter = get_adapter(provider, hotel_id)

        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PULL_RES_REQUEST",
            payload={"provider": provider, "since": since.isoformat()},
        )

        data = adapter.pull_reservations(since)
        items = data.get("items", [])

        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.INFO,
            message="PULL_RES_RESPONSE",
            payload={"count": len(items)},
        )

        job.stats = {
            **(job.stats or {}),
            "fetched": len(items),
            "created": 0,
            "updated": 0,
            "skipped": len(items),  # por ahora no aplicamos cambios
        }
        return job.stats
    except Exception as e:
        # Registrar error en log con detalles completos
        OtaSyncLog.objects.create(
            job=job,
            level=OtaSyncLog.Level.ERROR,
            message="PULL_RES_SERVICE_ERROR",
            payload={
                "hotel_id": hotel_id,
                "provider": provider,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "timestamp": timezone.now().isoformat(),
            },
        )
        raise  # Re-lanzar para que el task lo maneje


