from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    provider: str
    api_token: str
    phone_number_id: Optional[str] = None
    business_id: Optional[str] = None
    phone_number: Optional[str] = None


class WhatsappProviderAdapter:
    """
    Clase base para los adaptadores de proveedores (Meta, Twilio, etc.).
    """

    timeout = 10

    def __init__(self, config: ProviderConfig):
        self.config = config

    def send_message(self, to_number: str, message: str):
        raise NotImplementedError("Debe implementarse en la subclase.")

