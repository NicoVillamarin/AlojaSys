import logging
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

        url = self.API_URL_TEMPLATE.format(phone_number_id=self.config.phone_number_id)
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.debug("Mensaje enviado a Meta Cloud API. resp=%s", response.text)
            return response.json()
        except requests.RequestException as exc:
            logger.error("Error enviando mensaje a Meta Cloud API: %s", exc, exc_info=True)
            return None

