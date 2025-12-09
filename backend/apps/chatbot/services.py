import logging
import re
from datetime import date, datetime
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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
        message_text = (payload.get("message") or payload.get("body") or "").strip()

        if not (from_number and to_number):
            logger.warning("Webhook inválido: faltan números. payload=%s", payload)
            return {
                "ok": False,
                "reply": "No pudimos identificar el remitente. Intentalo nuevamente más tarde.",
            }

        hotel = self._resolve_hotel(to_number)
        if not hotel:
            logger.warning("WhatsApp entrante sin hotel configurado. to=%s", to_number)
            return {
                "ok": False,
                "reply": "Este número no tiene WhatsApp configurado en AlojaSys.",
            }

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

        # Salir cordialmente cuando ya se completó
        if session.state == ChatSession.State.COMPLETED and normalized_message in {"gracias", "muchas gracias"}:
            return {
                "ok": True,
                "reply": "De nada, un placer ayudarte. Si querés hacer otra reserva, solo escribí 'nueva reserva'.",
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
        summary = (
            f"Perfecto {session.guest_name or ''}. Reservaríamos del "
            f"{check_in_str} al {check_out_str} para {guests} huésped(es). "
            "¿Confirmás? Responde SI para crear la reserva o NO para reiniciar."
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

        session.state = ChatSession.State.COMPLETED
        session.is_active = False
        session.last_message_at = timezone.now()
        session.save(update_fields=["state", "is_active", "last_message_at", "updated_at"])

        return (
            f"Listo! Creamos la reserva #{reservation.id} en estado pendiente. "
            "El equipo del hotel se comunicará para confirmar el pago."
        )

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
        cleaned = message_text.strip()
        # soportamos AAAA-MM-DD y DD/MM/AAAA
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
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

    def _resolve_hotel(self, phone_number: Optional[str]) -> Optional[Hotel]:
        if not phone_number:
            return None
        normalized_target = self._normalize_phone(phone_number)
        if not normalized_target:
            return None

        direct_hotels = Hotel.objects.filter(whatsapp_enabled=True).exclude(whatsapp_phone="")
        for candidate in direct_hotels:
            if self._normalize_phone(candidate.whatsapp_phone) == normalized_target:
                return candidate

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

