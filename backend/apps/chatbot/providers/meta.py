import logging
import re
from typing import Any, Dict, Optional

import requests

from apps.chatbot.providers.base import ProviderConfig, WhatsappProviderAdapter


logger = logging.getLogger(__name__)


class MetaCloudAdapter(WhatsappProviderAdapter):
    API_URL_TEMPLATE = "https://graph.facebook.com/v18.0/{phone_number_id}/messages"

    def send_message(self, to_number: str, message: str) -> Optional[Dict[str, Any]]:
        if not message:
            logger.debug("Mensaje vacío, no se envía a Meta.")
            return None

        if not self.config.phone_number_id:
            logger.error("MetaCloudAdapter sin phone_number_id configurado.")
            return None

        # Meta Cloud API espera el número en formato E.164 SIN '+' ni espacios (solo dígitos).
        # Ej: "+1 555 012 3075" -> "15550123075"
        cleaned_to = re.sub(r"\D", "", to_number or "")
        if cleaned_to.startswith("00"):
            cleaned_to = cleaned_to[2:]
        if not cleaned_to:
            logger.error("MetaCloudAdapter: número de destino inválido. to=%r", to_number)
            return None

        url = self.API_URL_TEMPLATE.format(phone_number_id=self.config.phone_number_id)
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": cleaned_to,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            try:
                response.raise_for_status()
            except requests.HTTPError:
                # Log detallado del cuerpo de error que devuelve Meta para poder diagnosticar
                # códigos como 400 (por ejemplo, mensajes de plantilla no aprobados,
                # destinatario inválido, etc.).
                logger.error(
                    "Meta Cloud API devolvió error HTTP %s. body=%s",
                    response.status_code,
                    response.text,
                )
                # Re-lanzamos para que el caller mantenga el comportamiento actual.
                response.raise_for_status()

            logger.debug("Mensaje enviado a Meta Cloud API. resp=%s", response.text)
            return response.json()
        except requests.RequestException as exc:
            logger.error("Error enviando mensaje a Meta Cloud API: %s", exc, exc_info=True)
            return None

