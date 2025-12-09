import logging

from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chatbot.services import WhatsappChatbotService


logger = logging.getLogger(__name__)


class WhatsappWebhookView(APIView):
    """
    Endpoint para recibir webhooks de WhatsApp.

    Soporta dos modos de uso:
    - Desarrollo / pruebas internas: payload JSON simple con campos `from`, `to`, `message`
      (es el que usa `whatsapp_chat_cli.py`).
    - Producción / sandbox Meta Cloud API: payload oficial de Meta con `entry/changes/...`.
    """

    permission_classes = [permissions.AllowAny]

    # ------------------------------------------------------------------
    # Verificación de Webhook (Meta WhatsApp Cloud API)
    # ------------------------------------------------------------------
    def get(self, request, *args, **kwargs):
        """
        Meta llama con un GET para verificar el webhook:

        ?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=RANDOM

        Si el verify_token coincide, debemos responder con el `hub.challenge`
        en texto plano (no JSON).
        """
        mode = request.query_params.get("hub.mode")
        verify_token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        expected_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "alojasys-whatsapp-verify")

        if mode == "subscribe" and verify_token == expected_token and challenge:
            # Responder texto plano, como espera Meta
            return HttpResponse(challenge)

        logger.warning(
            "Intento de verificación de webhook WhatsApp inválido. mode=%s token=%s",
            mode,
            verify_token,
        )
        return Response({"detail": "Invalid webhook verification"}, status=status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Recepción de mensajes
    # ------------------------------------------------------------------
    def post(self, request, *args, **kwargs):
        service = WhatsappChatbotService()

        payload = request.data

        # Detección rápida de payload Meta WhatsApp Cloud
        if isinstance(payload, dict) and payload.get("object") == "whatsapp_business_account":
            normalized = self._normalize_meta_payload(payload)
        else:
            # Modo simple (CLI u otros proveedores genéricos)
            normalized = payload

        result = service.handle_incoming_message(normalized)
        http_status = status.HTTP_200_OK if result.get("ok", True) else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_meta_payload(self, payload):
        """
        Extrae `from`, `to` y `message` del JSON de Meta WhatsApp Cloud API.
        Ignora otros tipos de eventos que no sean mensajes de texto.
        """
        try:
            entry = (payload.get("entry") or [])[0]
            changes = (entry.get("changes") or [])[0]
            value = changes.get("value") or {}

            messages = value.get("messages") or []
            if not messages:
                logger.info("Webhook Meta sin mensajes para procesar. payload=%s", payload)
                # Devolvemos un payload mínimo para que el servicio responda algo neutro.
                return {}

            msg = messages[0]
            msg_type = msg.get("type")

            if msg_type == "text":
                text = (msg.get("text") or {}).get("body", "")
            elif msg_type == "button":
                # Para mensajes de botones tomamos el texto del botón presionado
                text = (msg.get("button") or {}).get("text", "")
            else:
                # Otros tipos (imagen, audio, etc.): por ahora los tratamos como no soportados
                text = ""

            from_number = msg.get("from")
            metadata = value.get("metadata") or {}
            to_number = metadata.get("display_phone_number") or metadata.get("phone_number_id")

            return {
                "from": from_number,
                "to": to_number,
                "message": text,
            }
        except Exception as exc:  # pragma: no cover - defensivo
            logger.error("Error normalizando payload Meta WhatsApp: %s payload=%s", exc, payload, exc_info=True)
            return {}

