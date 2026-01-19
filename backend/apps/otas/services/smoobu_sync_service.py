from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Optional
import hashlib
import os
import uuid
import logging

import requests
from django.utils import timezone
from django.db.models import Q

from apps.otas.models import OtaConfig, OtaProvider, OtaRoomMapping, SmoobuExportedBooking
from apps.reservations.models import Reservation, ReservationStatus, RoomBlock
from apps.rates.services.engine import get_applicable_rule, compute_rate_for_date
from apps.rooms.models import Room

logger = logging.getLogger(__name__)


@dataclass
class SmoobuClient:
    base_url: str
    api_key: str
    dry_run: bool = False

    def _headers(self) -> Dict[str, str]:
        return {"Api-Key": self.api_key, "Content-Type": "application/json"}

    def create_booking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            # Simula respuesta mínima de Smoobu
            return {"id": f"dry-{uuid.uuid4().hex[:10]}", "dry_run": True, "payload": payload}
        resp = requests.post(f"{self.base_url}/api/reservations", json=payload, headers=self._headers(), timeout=20)
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"Smoobu create_booking failed: HTTP {resp.status_code} {resp.text}")
        return resp.json() if resp.text else {}

    def update_booking(self, booking_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            return {"id": booking_id, "dry_run": True, "payload": payload}
        resp = requests.put(f"{self.base_url}/api/reservations/{booking_id}", json=payload, headers=self._headers(), timeout=20)
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"Smoobu update_booking failed: HTTP {resp.status_code} {resp.text}")
        return resp.json() if resp.text else {}

    def delete_booking(self, booking_id: str) -> None:
        if self.dry_run:
            return
        resp = requests.delete(f"{self.base_url}/api/reservations/{booking_id}", headers=self._headers(), timeout=20)
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"Smoobu delete_booking failed: HTTP {resp.status_code} {resp.text}")

    def push_rates(self, apartment_ids: list[int], operations: list[Dict[str, Any]]) -> Dict[str, Any]:
        if self.dry_run:
            return {"success": True, "dry_run": True, "apartments": apartment_ids, "operations": operations}
        body = {"apartments": apartment_ids, "operations": operations}
        resp = requests.post(f"{self.base_url}/api/rates", json=body, headers=self._headers(), timeout=30)
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"Smoobu push_rates failed: HTTP {resp.status_code} {resp.text}")
        return resp.json() if resp.text else {"success": True}


class SmoobuSyncService:
    """
    Sync AlojaSys -> Smoobu (bloqueos + precios) usando Smoobu API.

    - Disponibilidad: se empuja creando "blocked bookings" (channelId=11 por defecto).
    - Precios/min_stay: se empuja con POST /api/rates.
    """

    @staticmethod
    def _get_active_config(hotel_id: int) -> Optional[OtaConfig]:
        return OtaConfig.objects.filter(hotel_id=hotel_id, provider=OtaProvider.SMOOBU, is_active=True).first()

    @staticmethod
    def _client_for_hotel(hotel_id: int) -> Optional[SmoobuClient]:
        cfg = SmoobuSyncService._get_active_config(hotel_id)
        if not cfg:
            return None
        creds = cfg.credentials or {}
        api_key = creds.get("api_key")
        if not api_key:
            return None
        base_url = (creds.get("base_url") or os.environ.get("SMOOBU_BASE_URL") or "https://login.smoobu.com").rstrip("/")
        dry_run = bool(creds.get("dry_run")) or (os.environ.get("SMOOBU_DRY_RUN", "0") in ("1", "true", "yes"))
        return SmoobuClient(base_url=base_url, api_key=api_key, dry_run=dry_run)

    @staticmethod
    def _blocked_channel_id(hotel_id: int) -> int:
        cfg = SmoobuSyncService._get_active_config(hotel_id)
        if not cfg:
            return 11
        creds = cfg.credentials or {}
        try:
            return int(creds.get("blocked_channel_id") or 11)
        except Exception:
            return 11

    @staticmethod
    def _checksum(*parts: Any) -> str:
        raw = "|".join("" if p is None else str(p) for p in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:64]

    @staticmethod
    def _apartment_id_for_room(room_id: int) -> Optional[int]:
        m = OtaRoomMapping.objects.filter(provider=OtaProvider.SMOOBU, room_id=room_id, is_active=True).first()
        if not m or not m.external_id:
            return None
        try:
            return int(str(m.external_id))
        except Exception:
            return None

    @staticmethod
    def sync_block_for_reservation(reservation: Reservation) -> Dict[str, Any]:
        """
        Exporta una reserva local (directa) como bloqueo en Smoobu.
        """
        if reservation.external_id:
            # Reservas OTA (incluyendo las que llegan desde Smoobu) NO se re-exportan.
            return {"status": "skipped", "reason": "external_id_present"}

        if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN]:
            # No bloquea inventario si está cancelada/no_show/check_out.
            return {"status": "skipped", "reason": f"status:{reservation.status}"}

        apartment_id = SmoobuSyncService._apartment_id_for_room(reservation.room_id)
        if not apartment_id:
            return {"status": "skipped", "reason": "no_smoobu_mapping"}

        client = SmoobuSyncService._client_for_hotel(reservation.hotel_id)
        if not client:
            return {"status": "skipped", "reason": "no_smoobu_config"}

        blocked_channel_id = SmoobuSyncService._blocked_channel_id(reservation.hotel_id)
        desired_checksum = SmoobuSyncService._checksum("res", reservation.id, apartment_id, reservation.check_in, reservation.check_out)

        exported = SmoobuExportedBooking.objects.filter(reservation=reservation).first()
        if exported and exported.is_active and exported.checksum == desired_checksum:
            return {"status": "ok", "action": "noop", "smoobu_booking_id": exported.smoobu_booking_id}

        # Payload mínimo para "blocked booking"
        payload = {
            "arrivalDate": reservation.check_in.isoformat(),
            "departureDate": reservation.check_out.isoformat(),
            "apartmentId": apartment_id,
            "channelId": blocked_channel_id,
            "notice": f"Bloqueo desde AlojaSys (RES-{reservation.id})",
        }

        if exported and exported.smoobu_booking_id:
            logger.info(
                "SMOOBU_BLOCK_UPDATE reservation_id=%s hotel_id=%s room_id=%s apartment_id=%s channel_id=%s booking_id=%s dry_run=%s",
                reservation.id,
                reservation.hotel_id,
                reservation.room_id,
                apartment_id,
                blocked_channel_id,
                exported.smoobu_booking_id,
                getattr(client, "dry_run", False),
            )
            client.update_booking(str(exported.smoobu_booking_id), payload)
            exported.apartment_id = str(apartment_id)
            exported.checksum = desired_checksum
            exported.last_synced = timezone.now()
            exported.is_active = True
            exported.save(update_fields=["apartment_id", "checksum", "last_synced", "is_active", "updated_at"])
            return {"status": "ok", "action": "updated", "smoobu_booking_id": exported.smoobu_booking_id}

        logger.info(
            "SMOOBU_BLOCK_CREATE reservation_id=%s hotel_id=%s room_id=%s apartment_id=%s channel_id=%s dry_run=%s",
            reservation.id,
            reservation.hotel_id,
            reservation.room_id,
            apartment_id,
            blocked_channel_id,
            getattr(client, "dry_run", False),
        )
        res = client.create_booking(payload)
        smoobu_id = str(res.get("id") or res.get("data", {}).get("id") or "")
        if not smoobu_id:
            # fallback: si la API retorna otra estructura, guardamos placeholder para no romper
            smoobu_id = f"unknown:{reservation.id}"

        SmoobuExportedBooking.objects.update_or_create(
            reservation=reservation,
            defaults={
                "hotel_id": reservation.hotel_id,
                "room_id": reservation.room_id,
                "kind": SmoobuExportedBooking.Kind.RESERVATION,
                "apartment_id": str(apartment_id),
                "smoobu_booking_id": smoobu_id,
                "checksum": desired_checksum,
                "last_synced": timezone.now(),
                "is_active": True,
            },
        )
        return {"status": "ok", "action": "created", "smoobu_booking_id": smoobu_id}

    @staticmethod
    def sync_block_for_room_block(block: RoomBlock) -> Dict[str, Any]:
        if not block.is_active:
            return {"status": "skipped", "reason": "inactive"}

        apartment_id = SmoobuSyncService._apartment_id_for_room(block.room_id)
        if not apartment_id:
            return {"status": "skipped", "reason": "no_smoobu_mapping"}

        client = SmoobuSyncService._client_for_hotel(block.hotel_id)
        if not client:
            return {"status": "skipped", "reason": "no_smoobu_config"}

        blocked_channel_id = SmoobuSyncService._blocked_channel_id(block.hotel_id)
        desired_checksum = SmoobuSyncService._checksum("rb", block.id, apartment_id, block.start_date, block.end_date, block.block_type)

        exported = SmoobuExportedBooking.objects.filter(room_block=block).first()
        if exported and exported.is_active and exported.checksum == desired_checksum:
            return {"status": "ok", "action": "noop", "smoobu_booking_id": exported.smoobu_booking_id}

        payload = {
            "arrivalDate": block.start_date.isoformat(),
            "departureDate": block.end_date.isoformat(),
            "apartmentId": apartment_id,
            "channelId": blocked_channel_id,
            "notice": f"Bloqueo desde AlojaSys (RoomBlock-{block.id})",
        }

        if exported and exported.smoobu_booking_id:
            logger.info(
                "SMOOBU_BLOCK_UPDATE room_block_id=%s hotel_id=%s room_id=%s apartment_id=%s channel_id=%s booking_id=%s dry_run=%s",
                block.id,
                block.hotel_id,
                block.room_id,
                apartment_id,
                blocked_channel_id,
                exported.smoobu_booking_id,
                getattr(client, "dry_run", False),
            )
            client.update_booking(str(exported.smoobu_booking_id), payload)
            exported.apartment_id = str(apartment_id)
            exported.checksum = desired_checksum
            exported.last_synced = timezone.now()
            exported.is_active = True
            exported.save(update_fields=["apartment_id", "checksum", "last_synced", "is_active", "updated_at"])
            return {"status": "ok", "action": "updated", "smoobu_booking_id": exported.smoobu_booking_id}

        logger.info(
            "SMOOBU_BLOCK_CREATE room_block_id=%s hotel_id=%s room_id=%s apartment_id=%s channel_id=%s dry_run=%s",
            block.id,
            block.hotel_id,
            block.room_id,
            apartment_id,
            blocked_channel_id,
            getattr(client, "dry_run", False),
        )
        res = client.create_booking(payload)
        smoobu_id = str(res.get("id") or res.get("data", {}).get("id") or "")
        if not smoobu_id:
            smoobu_id = f"unknown:block:{block.id}"

        SmoobuExportedBooking.objects.update_or_create(
            room_block=block,
            defaults={
                "hotel_id": block.hotel_id,
                "room_id": block.room_id,
                "kind": SmoobuExportedBooking.Kind.ROOM_BLOCK,
                "apartment_id": str(apartment_id),
                "smoobu_booking_id": smoobu_id,
                "checksum": desired_checksum,
                "last_synced": timezone.now(),
                "is_active": True,
            },
        )
        return {"status": "ok", "action": "created", "smoobu_booking_id": smoobu_id}

    @staticmethod
    def cancel_export_for_reservation(reservation: Reservation) -> Dict[str, Any]:
        exported = SmoobuExportedBooking.objects.filter(reservation=reservation, is_active=True).first()
        if not exported:
            return {"status": "skipped", "reason": "no_exported_record"}
        client = SmoobuSyncService._client_for_hotel(reservation.hotel_id)
        if not client:
            return {"status": "skipped", "reason": "no_smoobu_config"}
        try:
            client.delete_booking(str(exported.smoobu_booking_id))
        finally:
            exported.is_active = False
            exported.last_synced = timezone.now()
            exported.save(update_fields=["is_active", "last_synced", "updated_at"])
        return {"status": "ok", "action": "deleted", "smoobu_booking_id": exported.smoobu_booking_id}

    @staticmethod
    def cancel_export_for_room_block(block: RoomBlock) -> Dict[str, Any]:
        exported = SmoobuExportedBooking.objects.filter(room_block=block, is_active=True).first()
        if not exported:
            return {"status": "skipped", "reason": "no_exported_record"}
        client = SmoobuSyncService._client_for_hotel(block.hotel_id)
        if not client:
            return {"status": "skipped", "reason": "no_smoobu_config"}
        try:
            client.delete_booking(str(exported.smoobu_booking_id))
        finally:
            exported.is_active = False
            exported.last_synced = timezone.now()
            exported.save(update_fields=["is_active", "last_synced", "updated_at"])
        return {"status": "ok", "action": "deleted", "smoobu_booking_id": exported.smoobu_booking_id}

    @staticmethod
    def push_rates_for_room(room_id: int, days_ahead: int = 90) -> Dict[str, Any]:
        room = Room.objects.select_related("hotel").filter(id=room_id, is_active=True).first()
        if not room:
            return {"status": "skipped", "reason": "room_not_found"}
        hotel_id = room.hotel_id
        apartment_id = SmoobuSyncService._apartment_id_for_room(room_id)
        if not apartment_id:
            return {"status": "skipped", "reason": "no_smoobu_mapping"}
        client = SmoobuSyncService._client_for_hotel(hotel_id)
        if not client:
            return {"status": "skipped", "reason": "no_smoobu_config"}

        start = timezone.now().date()
        end = start + timedelta(days=days_ahead)

        ops: list[Dict[str, Any]] = []
        current = start
        # Agrupar fechas con mismo precio/min_stay
        run_start = None
        run_price = None
        run_min = None

        while current < end:
            parts = compute_rate_for_date(room, 1, current, channel=None, promotion_code=None, voucher_code=None)
            price = float(parts["base_rate"])
            rule = get_applicable_rule(room, current, channel=None, include_closed=True)
            min_stay = int(rule.min_stay) if (rule and rule.min_stay) else 1

            if run_start is None:
                run_start = current
                run_price = price
                run_min = min_stay
            elif price != run_price or min_stay != run_min:
                # cerrar run anterior
                ops.append(
                    {
                        "dates": [f"{run_start.isoformat()}:{current.isoformat()}"],
                        "daily_price": run_price,
                        "min_length_of_stay": run_min,
                    }
                )
                run_start = current
                run_price = price
                run_min = min_stay

            current += timedelta(days=1)

        if run_start is not None:
            ops.append(
                {
                    "dates": [f"{run_start.isoformat()}:{end.isoformat()}"],
                    "daily_price": run_price,
                    "min_length_of_stay": run_min,
                }
            )

        client.push_rates([apartment_id], ops)
        return {"status": "ok", "apartment_id": apartment_id, "operations": len(ops)}

    @staticmethod
    def sync_hotel(hotel_id: int, days_ahead: int = 90) -> Dict[str, Any]:
        """
        Sync completo para un hotel:
        - Exporta bloqueos por reservas directas
        - Exporta bloqueos por RoomBlocks
        - (Opcional) Empuja rates por habitación mapeada
        """
        client = SmoobuSyncService._client_for_hotel(hotel_id)
        if not client:
            logger.warning("SMOOBU_SYNC_SKIP hotel_id=%s reason=no_smoobu_config", hotel_id)
            return {"status": "skipped", "reason": "no_smoobu_config"}

        today = timezone.now().date()
        end = today + timedelta(days=days_ahead)

        # Reservas directas que ocupan inventario (no OTA)
        # Nota: algunas creaciones pueden guardar external_id="" en vez de NULL; tratamos ambos como "directa".
        res_qs = (
            Reservation.objects.filter(
                hotel_id=hotel_id,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECK_IN],
                check_in__lt=end,
                check_out__gt=today,
            )
            .filter(Q(external_id__isnull=True) | Q(external_id=""))
            .select_related("room")
        )

        blocks_qs = RoomBlock.objects.filter(
            hotel_id=hotel_id,
            is_active=True,
            start_date__lt=end,
            end_date__gt=today,
        ).select_related("room")

        stats: Dict[str, Any] = {
            "exported_reservations": 0,
            "exported_room_blocks": 0,
            "rate_push_rooms": 0,
            "skipped": 0,
            "errors": 0,
            "skip_reasons": {},
        }

        logger.info(
            "SMOOBU_SYNC_START hotel_id=%s days_ahead=%s dry_run=%s base_url=%s blocked_channel_id=%s direct_reservations=%s room_blocks=%s",
            hotel_id,
            days_ahead,
            getattr(client, "dry_run", False),
            getattr(client, "base_url", None),
            SmoobuSyncService._blocked_channel_id(hotel_id),
            res_qs.count(),
            blocks_qs.count(),
        )

        for r in res_qs:
            try:
                out = SmoobuSyncService.sync_block_for_reservation(r)
                if out.get("status") == "ok":
                    stats["exported_reservations"] += 1 if out.get("action") in ("created", "updated", "noop") else 0
                else:
                    stats["skipped"] += 1
                    reason = str(out.get("reason") or "unknown")
                    stats["skip_reasons"][reason] = int(stats["skip_reasons"].get(reason, 0)) + 1
                    logger.info(
                        "SMOOBU_BLOCK_SKIP reservation_id=%s hotel_id=%s room_id=%s reason=%s",
                        r.id,
                        r.hotel_id,
                        r.room_id,
                        reason,
                    )
            except Exception as e:
                stats["errors"] += 1
                logger.exception("SMOOBU_BLOCK_ERROR reservation_id=%s hotel_id=%s error=%s", r.id, r.hotel_id, str(e))

        for b in blocks_qs:
            try:
                out = SmoobuSyncService.sync_block_for_room_block(b)
                if out.get("status") == "ok":
                    stats["exported_room_blocks"] += 1 if out.get("action") in ("created", "updated", "noop") else 0
                else:
                    stats["skipped"] += 1
                    reason = str(out.get("reason") or "unknown")
                    stats["skip_reasons"][reason] = int(stats["skip_reasons"].get(reason, 0)) + 1
                    logger.info(
                        "SMOOBU_BLOCK_SKIP room_block_id=%s hotel_id=%s room_id=%s reason=%s",
                        b.id,
                        b.hotel_id,
                        b.room_id,
                        reason,
                    )
            except Exception as e:
                stats["errors"] += 1
                logger.exception("SMOOBU_BLOCK_ERROR room_block_id=%s hotel_id=%s error=%s", b.id, b.hotel_id, str(e))

        # Rates: por ahora solo para rooms mapeadas. (Se puede desactivar por env si querés)
        if os.environ.get("SMOOBU_PUSH_RATES", "0") in ("1", "true", "yes"):
            mapped_rooms = (
                OtaRoomMapping.objects.filter(hotel_id=hotel_id, provider=OtaProvider.SMOOBU, is_active=True)
                .exclude(external_id__isnull=True)
                .exclude(external_id="")
                .values_list("room_id", flat=True)
                .distinct()
            )
            for room_id in mapped_rooms:
                try:
                    rr = SmoobuSyncService.push_rates_for_room(int(room_id), days_ahead=days_ahead)
                    if rr.get("status") == "ok":
                        stats["rate_push_rooms"] += 1
                except Exception:
                    stats["errors"] += 1

        logger.info(
            "SMOOBU_SYNC_DONE hotel_id=%s exported_reservations=%s exported_room_blocks=%s rate_push_rooms=%s skipped=%s errors=%s skip_reasons=%s",
            hotel_id,
            stats.get("exported_reservations"),
            stats.get("exported_room_blocks"),
            stats.get("rate_push_rooms"),
            stats.get("skipped"),
            stats.get("errors"),
            stats.get("skip_reasons"),
        )

        return {"status": "ok", **stats}

