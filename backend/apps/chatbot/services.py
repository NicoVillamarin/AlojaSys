import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.chatbot.models import ChatSession, ChatbotProviderAccount
from apps.chatbot.providers import get_adapter_for_config
from apps.core.models import Hotel
from apps.notifications.models import NotificationType
from apps.notifications.services import NotificationService
from apps.reservations.models import (
    Reservation,
    ReservationChannel,
    ReservationStatus,
    RoomBlock,
)
from apps.reservations.serializers import ReservationSerializer
from apps.reservations.services.pricing import (
    generate_nights_for_reservation,
    recalc_reservation_totals,
    quote_reservation_total,
)
from apps.rooms.models import Room, RoomStatus


logger = logging.getLogger(__name__)


class WhatsappChatbotService:
    """
    Servicio encargado de manejar las conversaciones entrantes desde WhatsApp.
    Implementa un flujo simple para tomar una reserva con los datos mínimos
    y crearla en estado pending dentro del PMS.
    """

    DATE_FORMAT_HINT = "AAAA-MM-DD o DD/MM/AAAA (por ejemplo 2025-01-18 o 18/01/2025)"

    def handle_incoming_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un webhook entrante y devuelve la respuesta que debe enviarse al huésped.
        El payload esperado puede variar según el proveedor; buscamos claves genéricas.
        """
        from_number = self._normalize_phone(
            payload.get("from") or payload.get("sender") or payload.get("contact")
        )
        to_number = self._normalize_phone(payload.get("to") or payload.get("receiver"))
        phone_number_id = (payload.get("phone_number_id") or "").strip() or None
        message_text = (payload.get("message") or payload.get("body") or "").strip()

        # --------------------------------------------------------------
        # Meta "Webhook test" (payload de ejemplo con IDs dummy)
        # --------------------------------------------------------------
        # El test de Meta suele enviar:
        # - phone_number_id=123456123
        # - display_phone_number=16505551111
        # - from=16315551181
        # - body="this is a text message"
        #
        # Esos valores NO son un número real conectado a tu WABA, por lo que
        # no se puede (ni se debe) intentar responder vía Graph API.
        if (
            (phone_number_id == "123456123" or to_number == "+16505551111")
            and from_number == "+16315551181"
            and message_text.lower() == "this is a text message"
        ):
            logger.info(
                "Webhook Meta (TEST) recibido. Se ignora para evitar respuestas a IDs dummy. "
                "to=%s phone_number_id=%s from=%s",
                to_number,
                phone_number_id,
                from_number,
            )
            return {"ok": True, "ignored": True, "reason": "meta_webhook_test"}

        # En webhooks reales de Meta, a veces el "to" puede venir como display_phone_number o faltar
        # en ciertos tests; permitimos identificar el número por `phone_number_id`.
        if not from_number or (not to_number and not phone_number_id):
            logger.warning("Webhook inválido: faltan números. payload=%s", payload)
            # Para proveedores con reintentos (como Meta), es mejor responder 200 y loguear,
            # evitando que el proveedor reintente indefinidamente por un payload no procesable.
            return {"ok": True, "ignored": True, "reason": "missing_numbers"}

        hotel = self._resolve_hotel(to_number, phone_number_id=phone_number_id)
        if not hotel:
            # Meta "Webhook test" suele usar valores dummy (por ejemplo +16505551111 / 123456123).
            # En ese caso, lo registramos como info para no confundir con un problema real.
            is_meta_dummy_test = (
                (to_number == "+16505551111")
                or (phone_number_id == "123456123")
            )
            log_fn = logger.info if is_meta_dummy_test else logger.warning
            log_fn(
                "WhatsApp entrante sin hotel configurado. to=%s phone_number_id=%s",
                to_number,
                phone_number_id,
            )
            # OJO: el "Webhook test" de Meta suele enviar IDs/números dummy que no coinciden
            # con ningún hotel. En lugar de responder 400 (que Meta interpreta como fallo),
            # devolvemos 200 y marcamos el evento como ignorado.
            return {"ok": True, "ignored": True, "reason": "hotel_not_configured"}

        session = self._get_or_create_session(hotel, from_number)
        logger.info(
            "Procesando mensaje WhatsApp hotel=%s phone=%s state=%s",
            hotel.id,
            from_number,
            session.state,
        )

        # Comandos / intents globales
        normalized_message = message_text.lower()

        # Reiniciar / nueva reserva
        restart_keywords = [
            "reiniciar",
            "reset",
            "empezar de nuevo",
            "empezar otra vez",
            "otra reserva",
            "nueva reserva",
            "hacer otra",
            "de nuevo",
        ]
        if any(kw in normalized_message for kw in restart_keywords):
            self._restart_session(session)
            return {
                "ok": True,
                "reply": "Perfecto, empezamos una nueva reserva. ¿Cuál es la fecha de check-in? "
                f"Usa el formato {self.DATE_FORMAT_HINT}.",
                "state": session.state,
            }

        if not message_text:
            return {
                "ok": True,
                "reply": "¿Podés indicarme la fecha de check-in? "
                f"Recordá usar el formato {self.DATE_FORMAT_HINT}.",
                "state": session.state,
            }

        reply = self._process_state(session, message_text)
        self._send_provider_reply(session, reply)
        return {
            "ok": True,
            "reply": reply,
            "state": session.state,
            "session_id": session.id,
        }

    # ------------------------------------------------------------------ #
    # Estados
    # ------------------------------------------------------------------ #

    def _process_state(self, session: ChatSession, message_text: str) -> str:
        handlers = {
            ChatSession.State.ASKING_CHECKIN: self._handle_checkin,
            ChatSession.State.ASKING_CHECKOUT: self._handle_checkout,
            ChatSession.State.ASKING_GUESTS: self._handle_guests,
            ChatSession.State.ASKING_GUEST_NAME: self._handle_guest_name,
            ChatSession.State.ASKING_GUEST_EMAIL: self._handle_guest_email,
            ChatSession.State.CONFIRMATION: self._handle_confirmation,
            ChatSession.State.COMPLETED: self._handle_completed,
        }
        handler = handlers.get(session.state)
        if not handler:
            logger.info("Sesión en estado %s, sin handler. Reiniciando.", session.state)
            self._restart_session(session)
            return (
                "Vamos a comenzar una nueva reserva. ¿Cuál es la fecha de check-in? "
                f"Recuerda el formato {self.DATE_FORMAT_HINT}."
            )
        return handler(session, message_text)

    def _handle_completed(self, session: ChatSession, message_text: str) -> str:
        """
        Cuando la conversación ya finalizó, evitamos "reiniciar" automáticamente.
        Guiamos al huésped para iniciar una nueva solicitud o finalizar.
        """
        normalized = (message_text or "").strip().lower()
        reservation_id = session.context.get("reservation_id")
        reservation_label = f"Reserva N° {reservation_id}" if reservation_id else "Tu reserva"

        if normalized in {"gracias", "muchas gracias", "ok", "okey", "perfecto"}:
            return (
                f"De nada, un placer ayudarte. {reservation_label} ya quedó registrada.\n"
                "Si querés hacer otra reserva, escribí: nueva reserva."
            )

        return (
            f"{reservation_label} ya quedó registrada.\n"
            "Si querés hacer otra reserva, escribí: nueva reserva.\n"
            "Si necesitás ayuda, podés responder: ayuda."
        )

    def _handle_checkin(self, session: ChatSession, message_text: str) -> str:
        check_in = self._parse_date(message_text)
        if not check_in:
            normalized = (message_text or "").strip().lower()
            # Saludos o dudas: responder más amigable
            if any(
                kw in normalized
                for kw in ["hola", "buenas", "buen día", "buen dia", "no entiendo", "ayuda"]
            ):
                return (
                    "Hola, soy el asistente de reservas del hotel. "
                    "Para empezar necesito la fecha de check-in.\n"
                    f"Podés escribirla en formato {self.DATE_FORMAT_HINT}."
                )
            return (
                "No pude entender la fecha de check-in. "
                f"Por favor indicámela en el formato {self.DATE_FORMAT_HINT}."
            )
        if check_in < date.today():
            return "La fecha de check-in debe ser futura. Indicáme otra fecha."
        session.context = {**session.context, "check_in": check_in.isoformat()}
        session.state = ChatSession.State.ASKING_CHECKOUT
        session.last_message_at = timezone.now()
        session.save(update_fields=["context", "state", "last_message_at", "updated_at"])
        return "Genial. ¿Cuál es la fecha de check-out?"

    def _handle_checkout(self, session: ChatSession, message_text: str) -> str:
        check_out = self._parse_date(message_text)
        if not check_out:
            return f"¿En qué fecha te retirarías? Formato {self.DATE_FORMAT_HINT}."

        check_in = self._get_context_date(session, "check_in")
        if not check_in:
            self._restart_session(session)
            return (
                "Reinicié la conversación para evitar errores. ¿Cuál es la fecha de check-in?"
            )

        if check_out <= check_in:
            return "La fecha de check-out debe ser posterior al check-in. Indicáme otra fecha."

        session.context = {**session.context, "check_out": check_out.isoformat()}
        session.state = ChatSession.State.ASKING_GUESTS
        session.last_message_at = timezone.now()
        session.save(update_fields=["context", "state", "last_message_at", "updated_at"])
        return "Perfecto. ¿Cuántas personas se hospedarán?"

    def _handle_guests(self, session: ChatSession, message_text: str) -> str:
        try:
            guests = int(re.sub(r"[^\d]", "", message_text)) if message_text else 0
        except ValueError:
            guests = 0
        if guests <= 0:
            return "Necesito un número de huéspedes. Por ejemplo: 2."
        if guests > 8:
            return "Por ahora puedo tomar hasta 8 huéspedes por este canal. Indicá un número menor."

        session.context = {**session.context, "guests": guests}
        session.state = ChatSession.State.ASKING_GUEST_NAME
        session.last_message_at = timezone.now()
        session.save(update_fields=["context", "state", "last_message_at", "updated_at"])
        return "Gracias. ¿A nombre de quién registramos la reserva?"

    def _handle_guest_name(self, session: ChatSession, message_text: str) -> str:
        if len(message_text) < 3:
            return "El nombre parece demasiado corto. ¿Podés indicarlo nuevamente?"
        session.guest_name = message_text.strip().title()
        session.state = ChatSession.State.ASKING_GUEST_EMAIL
        session.last_message_at = timezone.now()
        session.save(update_fields=["guest_name", "state", "last_message_at", "updated_at"])
        return (
            "¿Tenés un email de contacto? Si no querés indicarlo, respondé 'sin email'."
        )

    def _handle_guest_email(self, session: ChatSession, message_text: str) -> str:
        normalized = message_text.strip().lower()
        if normalized not in {"sin email", "sin", "no", "ninguno"}:
            session.guest_email = message_text.strip()
        else:
            session.guest_email = ""
        session.state = ChatSession.State.CONFIRMATION
        session.last_message_at = timezone.now()
        session.save(
            update_fields=["guest_email", "state", "last_message_at", "updated_at"]
        )
        check_in = self._get_context_date(session, "check_in")
        check_out = self._get_context_date(session, "check_out")
        guests = session.context.get("guests")
        check_in_str = self._format_date_for_guest(check_in)
        check_out_str = self._format_date_for_guest(check_out)

        # Confirmar disponibilidad y cotizar EXACTO antes de pedir confirmación
        quote_text = ""
        if check_in and check_out and guests:
            room = self._find_available_room(session.hotel, check_in, check_out, int(guests))
            if not room:
                self._restart_session(session)
                return (
                    "Por el momento no encontré disponibilidad automática para esas fechas.\n"
                    "Probemos con otras fechas: ¿cuál sería tu check-in?"
                )

            quote = quote_reservation_total(
                hotel=session.hotel,
                room=room,
                guests=int(guests),
                check_in=check_in,
                check_out=check_out,
                channel=ReservationChannel.WHATSAPP,
                promotion_code=(session.context or {}).get("promotion_code"),
                voucher_code=(session.context or {}).get("voucher_code"),
            )
            total = quote.get("total")
            nights_count = quote.get("nights_count") or 0
            if total is not None and nights_count:
                total_label = f"$ {float(total):,.2f}"
                session.context = {
                    **(session.context or {}),
                    "quote_total": str(total),
                    "quote_nights": nights_count,
                }
                session.save(update_fields=["context", "updated_at"])
                quote_text = (
                    f"\nTotal exacto ({nights_count} noche(s)): {total_label}.\n"
                    "Incluye las tarifas/reglas/impuestos configurados en el sistema."
                )

        summary = (
            f"Perfecto {session.guest_name or ''}. Reservaríamos del "
            f"{check_in_str} al {check_out_str} para {guests} huésped(es). "
            f"{quote_text}\n\n"
            "¿Confirmás? Respondé SI para crear la reserva o NO para reiniciar."
        )
        return summary

    def _handle_confirmation(self, session: ChatSession, message_text: str) -> str:
        normalized = message_text.strip().lower()
        if normalized in {"no", "n", "cancelar"}:
            self._restart_session(session)
            return "No hay problema, empecemos de nuevo. ¿Cuál es la fecha de check-in?"
        if normalized not in {"si", "sí", "s", "ok", "confirmo"}:
            return "Necesito que respondas SI para crear la reserva o NO para reiniciar."

        reservation = self._create_pending_reservation(session)
        if not reservation:
            self._restart_session(session)
            return (
                "No encontré disponibilidad automática para ese rango. "
                "Un agente del hotel te contactará en breve."
            )

        # Guardamos la reserva en contexto para poder referenciarla luego (post-conversación)
        session.context = {**(session.context or {}), "reservation_id": reservation.id}
        session.state = ChatSession.State.COMPLETED
        session.is_active = False
        session.last_message_at = timezone.now()
        session.save(update_fields=["context", "state", "is_active", "last_message_at", "updated_at"])

        check_in = self._get_context_date(session, "check_in")
        check_out = self._get_context_date(session, "check_out")
        check_in_str = self._format_date_for_guest(check_in)
        check_out_str = self._format_date_for_guest(check_out)
        hotel_name = getattr(session.hotel, "name", "") or "el hotel"

        return (
            "¡Listo! Tu reserva quedó registrada.\n"
            f"Reserva N° {reservation.id}\n"
            f"Hotel: {hotel_name}\n"
            f"Fechas: {check_in_str} al {check_out_str}\n\n"
            "En breve te confirmamos disponibilidad y próximos pasos. "
            "Si querés hacer otra reserva, escribí: nueva reserva."
        )

    # Nota: eliminamos la estimación "aproximada" y usamos cotización exacta vía pricing engine.

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _get_or_create_session(self, hotel: Hotel, guest_phone: str) -> ChatSession:
        """
        Obtiene la sesión activa para (hotel, guest_phone) o la crea de forma atómica.

        Usamos get_or_create dentro de una transacción para evitar la condición de
        carrera con el UniqueConstraint `unique_active_chatbot_session_per_guest`.
        """
        # Fast path: la mayoría de las veces ya existirá una sesión activa
        session = (
            ChatSession.objects.filter(hotel=hotel, guest_phone=guest_phone, is_active=True)
            .order_by("-updated_at")
            .first()
        )
        if session:
            return session

        try:
            with transaction.atomic():
                session, _created = ChatSession.objects.get_or_create(
                    hotel=hotel,
                    guest_phone=guest_phone,
                    is_active=True,
                    defaults={
                        "state": ChatSession.State.ASKING_CHECKIN,
                        "context": {},
                    },
                )
                return session
        except IntegrityError:
            # Otra transacción creó la sesión en paralelo; la buscamos de nuevo.
            return (
                ChatSession.objects.filter(hotel=hotel, guest_phone=guest_phone, is_active=True)
                .order_by("-updated_at")
                .first()
            )

    def _restart_session(self, session: ChatSession) -> None:
        session.context = {}
        session.state = ChatSession.State.ASKING_CHECKIN
        session.is_active = True
        session.last_message_at = timezone.now()
        session.save(
            update_fields=["context", "state", "is_active", "last_message_at", "updated_at"]
        )

    def _parse_date(self, message_text: str) -> Optional[date]:
        """
        Intenta extraer una fecha desde texto libre.

        Soporta:
        - AAAA-MM-DD (ISO) dentro del texto
        - DD/MM/AAAA y DD-MM-AAAA dentro del texto
        - DD/MM (sin año): asume el año actual o el próximo si ya pasó
        - "17 de diciembre de 2025" (mes en español, con/sin "de", con/sin año)
        - "mañana" / "pasado mañana"
        """
        if not message_text:
            return None

        text = (message_text or "").strip()
        if not text:
            return None

        lower = text.lower()
        today = date.today()

        # Relativos comunes
        if "pasado mañana" in lower or "pasado manana" in lower:
            return today + timedelta(days=2)
        if "mañana" in lower or "manana" in lower:
            return today + timedelta(days=1)

        # 1) ISO (AAAA-MM-DD o AAAA/MM/DD) en cualquier parte del texto
        iso_match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", lower)
        if iso_match:
            y, m, d = (int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            try:
                return date(y, m, d)
            except ValueError:
                pass

        # 2) Numérico D/M/Y con separadores / o - (DD/MM/AAAA, DD-MM-AAAA)
        dmy_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", lower)
        if dmy_match:
            d, m, y_raw = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
            y = (2000 + y_raw) if y_raw < 100 else y_raw
            try:
                return date(y, m, d)
            except ValueError:
                pass

        # 3) Numérico D/M sin año (DD/MM o DD-MM)
        dm_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", lower)
        if dm_match:
            d, m = int(dm_match.group(1)), int(dm_match.group(2))
            y = today.year
            try:
                candidate = date(y, m, d)
                if candidate < today:
                    candidate = date(y + 1, m, d)
                return candidate
            except ValueError:
                pass

        # 4) "17 de diciembre de 2025" (mes en español)
        month_map = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "setiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
        }
        # Permitimos: "17 de diciembre", "17 diciembre", "17 de diciembre de 2025"
        month_regex = r"(" + "|".join(month_map.keys()) + r")"
        m_match = re.search(
            rf"\b(\d{{1,2}})\s*(?:de\s*)?{month_regex}\s*(?:de\s*)?(\d{{4}})?\b",
            lower,
        )
        if m_match:
            d = int(m_match.group(1))
            m_name = m_match.group(2)
            y_str = m_match.group(3)
            m = month_map.get(m_name)
            if m:
                y = int(y_str) if y_str else today.year
                try:
                    candidate = date(y, m, d)
                    if not y_str and candidate < today:
                        candidate = date(y + 1, m, d)
                    return candidate
                except ValueError:
                    pass

        # 5) "el 17" / "día 17" (solo día del mes; asumimos mes/año actual o el próximo)
        day_only = re.search(r"\b(?:el|día|dia)\s+(\d{1,2})\b", lower)
        if day_only:
            day = int(day_only.group(1))
            # buscamos la próxima fecha válida con ese día
            y = today.year
            m = today.month
            for _ in range(0, 14):  # hasta ~14 meses para cubrir edge-cases
                try:
                    candidate = date(y, m, day)
                    if candidate > today:
                        return candidate
                except ValueError:
                    pass
                m += 1
                if m > 12:
                    m = 1
                    y += 1

        # 6) "este viernes" / "el viernes" / "próximo viernes"
        weekday_map = {
            "lunes": 0,
            "martes": 1,
            "miercoles": 2,
            "miércoles": 2,
            "jueves": 3,
            "viernes": 4,
            "sabado": 5,
            "sábado": 5,
            "domingo": 6,
        }
        wd_match = re.search(
            r"\b(?:este|esta|el|la|próximo|proximo)\s+(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b",
            lower,
        )
        if wd_match:
            wd_token = wd_match.group(1)
            # normalizamos acentos para el dict
            wd_norm = (
                wd_token.replace("é", "e")
                .replace("á", "a")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
            )
            target = weekday_map.get(wd_token) or weekday_map.get(wd_norm)
            if target is not None:
                days_ahead = (target - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)

        # Fallback antiguo: si el texto es SOLO una fecha exacta, probamos formatos clásicos
        cleaned = text.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
        return None

    def _get_context_date(self, session: ChatSession, key: str) -> Optional[date]:
        value = session.context.get(key)
        if not value:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _format_date_for_guest(self, value: Optional[date]) -> str:
        """
        Formatea la fecha para el huésped en formato DD/MM/AAAA.
        Si no hay fecha válida, devuelve cadena vacía.
        """
        if not value:
            return ""
        try:
            return value.strftime("%d/%m/%Y")
        except Exception:
            return str(value)

    def _normalize_phone(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        digits = re.sub(r"[^\d+]", "", value)
        if digits.startswith("00"):
            digits = "+" + digits[2:]
        if not digits.startswith("+") and digits:
            digits = "+" + digits
        return digits

    def _resolve_hotel(
        self, phone_number: Optional[str], phone_number_id: Optional[str] = None
    ) -> Optional[Hotel]:
        if not phone_number:
            # En algunos payloads de Meta (por ejemplo tests) puede no venir el "to" real.
            # Permitimos resolver por phone_number_id cuando está disponible.
            if phone_number_id:
                return (
                    Hotel.objects.filter(whatsapp_enabled=True)
                    .filter(
                        Q(whatsapp_phone_number_id=phone_number_id)
                        | Q(whatsapp_provider_account__phone_number_id=phone_number_id)
                    )
                    .order_by("id")
                    .first()
                )
            return None
        normalized_target = self._normalize_phone(phone_number)
        if not normalized_target:
            return None

        direct_hotels = Hotel.objects.filter(whatsapp_enabled=True).exclude(whatsapp_phone="")
        for candidate in direct_hotels:
            if self._normalize_phone(candidate.whatsapp_phone) == normalized_target:
                return candidate

        # Fallback: si tenemos phone_number_id, resolvemos por el identificador interno.
        # Esto es más robusto que el display_phone_number y también permite soportar
        # payloads de prueba de Meta.
        if phone_number_id:
            hotel = (
                Hotel.objects.filter(whatsapp_enabled=True)
                .filter(
                    Q(whatsapp_phone_number_id=phone_number_id)
                    | Q(whatsapp_provider_account__phone_number_id=phone_number_id)
                )
                .order_by("id")
                .first()
            )
            if hotel:
                return hotel

        accounts = ChatbotProviderAccount.objects.filter(is_active=True).exclude(phone_number="")
        for account in accounts:
            if self._normalize_phone(account.phone_number) != normalized_target:
                continue
            return (
                Hotel.objects.filter(
                    whatsapp_enabled=True,
                    whatsapp_provider_account=account,
                )
                .order_by("id")
                .first()
            )
        return None

    def _create_pending_reservation(self, session: ChatSession) -> Optional[Reservation]:
        check_in = self._get_context_date(session, "check_in")
        check_out = self._get_context_date(session, "check_out")
        guests = session.context.get("guests")
        if not (check_in and check_out and guests):
            logger.warning("Contexto incompleto para la reserva. session=%s", session.id)
            return None

        room = self._find_available_room(session.hotel, check_in, check_out, guests)
        if not room:
            logger.info(
                "Sin disponibilidad automática hotel=%s rango=%s/%s huéspedes=%s",
                session.hotel_id,
                check_in,
                check_out,
                guests,
            )
            return None

        payload = {
            "hotel": session.hotel_id,
            "room": room.id,
            "guests": guests,
            "guests_data": [
                {
                    "name": session.guest_name or "Huésped WhatsApp",
                    "phone": session.guest_phone,
                    "email": session.guest_email,
                    "is_primary": True,
                }
            ],
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "status": ReservationStatus.PENDING,
            "channel": ReservationChannel.WHATSAPP,
            "notes": "Reserva creada automáticamente vía WhatsApp",
        }

        serializer = ReservationSerializer(data=payload)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            logger.error("Error validando reserva WhatsApp: %s", exc)
            return None

        with transaction.atomic():
            reservation = serializer.save()
            generate_nights_for_reservation(reservation)
            recalc_reservation_totals(reservation)

        self._notify_staff(reservation, session)
        return reservation

    def _find_available_room(
        self, hotel: Hotel, check_in: date, check_out: date, guests: int
    ) -> Optional[Room]:
        active_status = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECK_IN,
        ]
        rooms = (
            Room.objects.filter(hotel=hotel, is_active=True)
            .exclude(status=RoomStatus.OUT_OF_SERVICE)
            .order_by("max_capacity", "id")
        )
        for room in rooms:
            max_capacity = room.max_capacity or room.capacity or 1
            if guests > max_capacity:
                continue
            overlap = Reservation.objects.filter(
                room=room,
                status__in=active_status,
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).exists()
            if overlap:
                continue
            blocked = RoomBlock.objects.filter(
                room=room,
                is_active=True,
                start_date__lt=check_out,
                end_date__gt=check_in,
            ).exists()
            if blocked:
                continue
            return room
        return None

    def _notify_staff(self, reservation: Reservation, session: ChatSession) -> None:
        try:
            NotificationService.create(
                notification_type=NotificationType.WHATSAPP_RESERVATION_RECEIVED,
                title="Nueva reserva pendiente vía WhatsApp",
                message=(
                    f"Reserva #{reservation.id} creada automáticamente para "
                    f"{reservation.guest_name} ({session.guest_phone}). "
                    f"Check-in {reservation.check_in} - Check-out {reservation.check_out}."
                ),
                hotel_id=reservation.hotel_id,
                reservation_id=reservation.id,
                metadata={
                    "source": "whatsapp",
                    "guest_phone": session.guest_phone,
                    "guest_name": reservation.guest_name,
                },
            )
        except Exception as exc:
            logger.error(
                "No se pudo crear la notificación de WhatsApp. reservation=%s error=%s",
                reservation.id,
                exc,
            )

    def _build_provider_config(self, hotel: Hotel) -> Optional[Dict[str, Any]]:
        if hotel.whatsapp_provider_account and hotel.whatsapp_provider_account.is_active:
            account = hotel.whatsapp_provider_account
            return {
                "provider": account.provider,
                "api_token": account.api_token,
                "phone_number_id": account.phone_number_id,
                "business_id": account.business_id,
                "phone_number": account.phone_number,
            }
        if hotel.whatsapp_provider and hotel.whatsapp_api_token:
            return {
                "provider": hotel.whatsapp_provider,
                "api_token": hotel.whatsapp_api_token,
                "phone_number_id": hotel.whatsapp_phone_number_id,
                "business_id": hotel.whatsapp_business_id,
                "phone_number": hotel.whatsapp_phone,
            }
        return None

    def _send_provider_reply(self, session: ChatSession, message: str) -> None:
        config = self._build_provider_config(session.hotel)
        if not config:
            logger.debug(
                "Hotel %s sin configuración de proveedor WhatsApp, no se envía mensaje.",
                session.hotel_id,
            )
            return

        adapter = get_adapter_for_config(config)
        if not adapter:
            logger.error(
                "No se encontró adaptador para el proveedor %s", config.get("provider")
            )
            return

        try:
            adapter.send_message(session.guest_phone, message)
        except Exception as exc:
            logger.error(
                "Error enviando respuesta vía proveedor WhatsApp. hotel=%s error=%s",
                session.hotel_id,
                exc,
                exc_info=True,
            )

