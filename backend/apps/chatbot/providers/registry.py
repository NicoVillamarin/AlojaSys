from typing import Optional

from apps.chatbot.providers.base import ProviderConfig, WhatsappProviderAdapter
from apps.chatbot.providers.meta import MetaCloudAdapter


def get_adapter_for_config(config_dict) -> Optional[WhatsappProviderAdapter]:
    if not config_dict:
        return None
    config = ProviderConfig(**config_dict)
    provider_code = config.provider

    if provider_code == "meta_cloud":
        return MetaCloudAdapter(config)

    # Otros proveedores pueden agregarse aquí
    return None

