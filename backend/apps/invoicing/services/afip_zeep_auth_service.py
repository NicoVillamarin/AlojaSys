"""
Autenticación AFIP WSAA usando Zeep (SOAP) con firma PKCS#7.
Mantiene misma interfaz pública que AfipAuthService.get_token_and_sign.
"""

import os
import base64
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional, Tuple

from django.core.cache import cache
from django.utils import timezone as dj_tz

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from zeep import Client
from zeep.transports import Transport
import requests
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)


class AfipZeepAuthService:
    WSAA_WSDL_HOMO = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL"
    WSAA_WSDL_PROD = "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL"
    SERVICE = "wsfe"

    def __init__(self, config):
        self.config = config
        self.is_production = config.environment == 'production'
        self.wsaa_wsdl = self.WSAA_WSDL_PROD if self.is_production else self.WSAA_WSDL_HOMO
        self.token_cache_key = f"afip_token_{config.hotel.id}_{config.environment}"
        self.sign_cache_key = f"afip_sign_{config.hotel.id}_{config.environment}"

    def get_token_and_sign(self) -> Tuple[str, str]:
        # Cache
        cached_token = cache.get(self.token_cache_key)
        cached_sign = cache.get(self.sign_cache_key)
        if cached_token and cached_sign:
            return cached_token, cached_sign

        # Persistencia si no venció
        if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
            exp = getattr(self.config, 'afip_token_expiration', None)
            if exp and exp > dj_tz.now():
                ttl = max(60, min(11 * 60 * 60, int((exp - dj_tz.now()).total_seconds())))
                cache.set(self.token_cache_key, self.config.afip_token, ttl)
                cache.set(self.sign_cache_key, self.config.afip_sign, ttl)
                return self.config.afip_token, self.config.afip_sign

        # Lock sencillo para evitar tormenta de logins
        lock_key = f"afip_wsaa_lock_{self.config.hotel.id}_{self.config.environment}"
        got_lock = cache.add(lock_key, True, timeout=120)
        try:
            if not got_lock:
                # Espera breve por si otro proceso persiste el TA
                token_sign = self._wait_for_existing_ta(timeout_seconds=90, interval_seconds=5)
                if token_sign is not None:
                    return token_sign

            try:
                token, sign, gen_dt, exp_dt = self._request_ta_with_zeep()
            except Exception as e:
                # Fallback robusto: usar cliente por requests del servicio existente
                logger.warning(f"Fallo WSAA Zeep ({e}); intentando fallback por requests")
                try:
                    from .afip_auth_service import AfipAuthService  # import local para evitar ciclos
                    token, sign = AfipAuthService(self.config).get_token_and_sign()
                    gen_dt = dj_tz.now()
                    exp_dt = gen_dt + timedelta(hours=12)
                except Exception as e2:
                    raise AfipZeepAuthError(f"Fallback por requests también falló: {e2}")

            # Cache y persistencia
            now = dj_tz.now()
            cache_timeout = int(min(11 * 60 * 60, max(60, (exp_dt - now).total_seconds()))) if exp_dt and exp_dt > now else 11 * 60 * 60
            cache.set(self.token_cache_key, token, cache_timeout)
            cache.set(self.sign_cache_key, sign, cache_timeout)

            try:
                self.config.afip_token = token
                self.config.afip_sign = sign
                self.config.afip_token_generation = gen_dt or now
                self.config.afip_token_expiration = exp_dt or (now + timedelta(hours=12))
                if hasattr(self.config, 'is_active'):
                    self.config.is_active = True
                self.config.save(update_fields=['afip_token','afip_sign','afip_token_generation','afip_token_expiration','is_active'])
            except Exception as e:
                logger.warning(f"No se pudo persistir TA en BD: {e}")

            return token, sign
        finally:
            if got_lock:
                cache.delete(lock_key)

    def _wait_for_existing_ta(self, timeout_seconds: int, interval_seconds: int) -> Optional[Tuple[str, str]]:
        from time import sleep
        deadline = dj_tz.now() + timedelta(seconds=timeout_seconds)
        while dj_tz.now() < deadline:
            cached_token = cache.get(self.token_cache_key)
            cached_sign = cache.get(self.sign_cache_key)
            if cached_token and cached_sign:
                return cached_token, cached_sign
            if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
                exp = getattr(self.config, 'afip_token_expiration', None)
                if not exp or exp > dj_tz.now():
                    return self.config.afip_token, self.config.afip_sign
            sleep(interval_seconds)
        return None

    def _request_ta_with_zeep(self) -> Tuple[str, str, Optional[datetime], Optional[datetime]]:
        # Construir TRA
        now = datetime.now(dt_timezone.utc)
        generation_time = (now - timedelta(minutes=10)).astimezone().isoformat(timespec='seconds')
        expiration_time = (now + timedelta(minutes=10)).astimezone().isoformat(timespec='seconds')
        unique_id = int(now.timestamp())
        tra = f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>{unique_id}</uniqueId>
    <generationTime>{generation_time}</generationTime>
    <expirationTime>{expiration_time}</expirationTime>
  </header>
  <service>{self.SERVICE}</service>
</loginTicketRequest>"""

        # Firmar CMS PKCS#7 (DER) embebiendo datos
        signed_cms_b64 = self._sign_xml_to_pkcs7_b64(tra)

        # Consumir WSAA con Zeep
        session = requests.Session()
        session.verify = True
        transport = Transport(session=session, timeout=30)
        client = Client(self.wsaa_wsdl, transport=transport)

        try:
            result = client.service.loginCms(in0=signed_cms_b64)
        except Exception as e:
            raise AfipZeepAuthError(f"Error llamando WSAA/loginCms: {e}")

        # 'result' puede venir como bytes (ya decodificados), base64 o XML escapado
        if result is None:
            raise AfipZeepAuthError("Respuesta de WSAA vacía")

        decoded: Optional[bytes]
        if isinstance(result, (bytes, bytearray)):
            # Zeep puede retornar bytes que representan:
            # - XML en bytes
            # - Base64 en bytes
            # - XML escapado en bytes
            raw_bytes = bytes(result)
            decoded = None
            # Caso 1: ¿ya es XML?
            if raw_bytes.strip()[:1] == b'<' or b'<loginTicketResponse' in raw_bytes:
                decoded = raw_bytes
            # Caso 2: ¿es base64 de XML?
            if decoded is None:
                try:
                    trial = base64.b64decode(raw_bytes, validate=False)
                    if trial and (trial.strip()[:1] == b'<' or b'<loginTicketResponse' in trial):
                        decoded = trial
                except Exception:
                    pass
            # Caso 3: decodificar a texto y reintentar (utf-8 o latin-1)
            if decoded is None:
                for enc in ('utf-8', 'latin-1'):
                    try:
                        raw_text = raw_bytes.decode(enc, errors='ignore').strip()
                        if raw_text:
                            try:
                                trial2 = base64.b64decode(raw_text, validate=False)
                                if trial2 and (trial2.strip()[:1] == b'<' or b'<loginTicketResponse' in trial2):
                                    decoded = trial2
                                    break
                            except Exception:
                                pass
                            # Intentar des-escapar HTML
                            try:
                                import html
                                unesc = html.unescape(raw_text)
                                if unesc and (unesc.lstrip()[:1] == '<'):
                                    decoded = unesc.encode('utf-8')
                                    break
                            except Exception:
                                pass
                    except Exception:
                        pass
            # Fallback: si no logramos decodificar, usar los bytes tal cual (probable Fault manejado arriba)
            decoded = decoded or raw_bytes
        else:
            raw = str(result).strip()
            if not raw:
                raise AfipZeepAuthError("Respuesta de WSAA vacía")
            # Intentar base64 primero, sino des-escapar HTML
            try:
                decoded = base64.b64decode(raw)
            except Exception:
                import html
                raw_unesc = html.unescape(raw)
                decoded = raw_unesc.encode('utf-8', errors='ignore')

        # Extraer token/sign y tiempos
        try:
            root = ET.fromstring(decoded)
        except Exception as e:
            preview = (decoded or b'')[:300]
            raise AfipZeepAuthError(f"No se pudo parsear loginTicketResponse: {e} | Preview: {preview}")

        token_el = root.find('.//token')
        sign_el = root.find('.//sign')
        if token_el is None or sign_el is None or not token_el.text or not sign_el.text:
            raise AfipZeepAuthError("Token o sign no presentes en respuesta de WSAA")

        gen_el = root.find('.//generationTime')
        exp_el = root.find('.//expirationTime')
        gen_dt = None
        exp_dt = None
        try:
            from django.utils.dateparse import parse_datetime
            if gen_el is not None and gen_el.text:
                gen_dt = parse_datetime(gen_el.text)
            if exp_el is not None and exp_el.text:
                exp_dt = parse_datetime(exp_el.text)
        except Exception:
            pass

        return token_el.text, sign_el.text, gen_dt, exp_dt

    def _sign_xml_to_pkcs7_b64(self, xml_content: str) -> str:
        cert_path = self.config.certificate_path
        key_path = self.config.private_key_path
        if not os.path.exists(cert_path):
            raise AfipZeepAuthError(f"Certificado no encontrado: {cert_path}")
        if not os.path.exists(key_path):
            raise AfipZeepAuthError(f"Clave privada no encontrada: {key_path}")

        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        with open(key_path, 'rb') as f:
            key_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data)
        private_key = serialization.load_pem_private_key(key_data, password=None)

        builder = pkcs7.PKCS7SignatureBuilder().set_data(xml_content.encode('utf-8')).add_signer(
            cert,
            private_key,
            hashes.SHA256()
        )
        cms_der = builder.sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
        return base64.b64encode(cms_der).decode('utf-8')


class AfipZeepAuthError(Exception):
    pass


