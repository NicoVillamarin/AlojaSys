"""
Servicio de autenticación con AFIP WSAA
Maneja la autenticación y obtención de tokens para los servicios de AFIP
"""

import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12, pkcs7
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class AfipAuthService:
    """
    Servicio para autenticación con AFIP WSAA
    """
    
    # URLs de AFIP
    WSAA_HOMOLOGATION_URL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
    WSAA_PRODUCTION_URL = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
    WSAA_SOAP_NS = "http://wsaa.view.sua.dvad.gov.ar/"
    
    # Servicios AFIP
    WSFEv1_SERVICE = "wsfe"
    
    def __init__(self, config):
        """
        Inicializa el servicio de autenticación
        
        Args:
            config: Instancia de AfipConfig
        """
        self.config = config
        self.is_production = config.environment == 'production'
        self.wsaa_url = self.WSAA_PRODUCTION_URL if self.is_production else self.WSAA_HOMOLOGATION_URL
        
        # Cache keys
        self.token_cache_key = f"afip_token_{config.hotel.id}_{config.environment}"
        self.sign_cache_key = f"afip_sign_{config.hotel.id}_{config.environment}"
        
    def get_token_and_sign(self) -> Tuple[str, str]:
        """
        Obtiene token y sign válidos para AFIP
        
        Returns:
            Tuple[str, str]: (token, sign)
            
        Raises:
            AfipAuthError: Si hay error en la autenticación
        """
        # 1) Verificar cache primero
        cached_token = cache.get(self.token_cache_key)
        cached_sign = cache.get(self.sign_cache_key)
        if cached_token and cached_sign:
            logger.info(f"Token AFIP obtenido desde cache para hotel {self.config.hotel.id}")
            return cached_token, cached_sign

        # 2) Verificar persistencia en BD (no expirado)
        try:
            from django.utils import timezone as dj_tz
            if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
                exp = getattr(self.config, 'afip_token_expiration', None)
                if exp and exp > dj_tz.now():
                    # Repoblar cache y reutilizar
                    remaining = int((exp - dj_tz.now()).total_seconds())
                    # limitar el TTL para evitar valores negativos o excesivos
                    ttl = max(60, min(11 * 60 * 60, remaining))
                    cache.set(self.token_cache_key, self.config.afip_token, ttl)
                    cache.set(self.sign_cache_key, self.config.afip_sign, ttl)
                    logger.info(
                        f"Token AFIP reutilizado desde BD para hotel {self.config.hotel.id}, vence en {remaining}s"
                    )
                    return self.config.afip_token, self.config.afip_sign
        except Exception as e:
            logger.warning(f"No se pudo reutilizar TA desde BD: {e}")
        
        # 3) Evitar tormenta de logins: lock distribuido
        lock_key = f"afip_wsaa_lock_{self.config.hotel.id}_{self.config.environment}"
        got_lock = cache.add(lock_key, True, timeout=120)  # 2 minutos
        try:
            if not got_lock:
                logger.info("Otro proceso está obteniendo TA; esperando reutilización...")
                # Esperar a que otro proceso persista el TA
                token_sign = self._wait_for_existing_ta(timeout_seconds=90, interval_seconds=5)
                if token_sign is not None:
                    token, sign = token_sign
                    return token, sign
                # Si no apareció, intentar igualmente generar nosotros
                logger.info("TA no apareció; intentando generar uno nuevo nosotros")

            # Generar nuevo token
            token, sign, gen_dt, exp_dt = self._generate_new_token()
            
            # Guardar en cache hasta expiración (cap a 11h)
            from django.utils import timezone as dj_tz
            now = dj_tz.now()
            if exp_dt and exp_dt > now:
                cache_timeout = int(min(11 * 60 * 60, (exp_dt - now).total_seconds()))
            else:
                cache_timeout = 11 * 60 * 60
            cache.set(self.token_cache_key, token, cache_timeout)
            cache.set(self.sign_cache_key, sign, cache_timeout)

            # Persistir en BD
            try:
                update_fields = []
                if hasattr(self.config, 'afip_token'):
                    self.config.afip_token = token; update_fields.append('afip_token')
                if hasattr(self.config, 'afip_sign'):
                    self.config.afip_sign = sign; update_fields.append('afip_sign')
                if hasattr(self.config, 'afip_token_generation') and gen_dt:
                    self.config.afip_token_generation = gen_dt; update_fields.append('afip_token_generation')
                if hasattr(self.config, 'afip_token_expiration') and exp_dt:
                    self.config.afip_token_expiration = exp_dt; update_fields.append('afip_token_expiration')
                if update_fields:
                    self.config.save(update_fields=update_fields or None)
            except Exception as e:
                logger.warning(f"No se pudo persistir TA en BD: {e}")
            
            logger.info(f"Token AFIP generado exitosamente para hotel {self.config.hotel.id}")
            return token, sign
            
        except Exception as e:
            logger.error(f"Error generando token AFIP para hotel {self.config.hotel.id}: {str(e)}")
            raise AfipAuthError(f"Error en autenticación AFIP: {str(e)}")
        finally:
            if got_lock:
                cache.delete(lock_key)

    def _wait_for_existing_ta(self, timeout_seconds: int = 60, interval_seconds: int = 5) -> Optional[Tuple[str, str]]:
        """
        Espera a que aparezca un TA en cache/BD durante un tiempo, útil cuando WSAA
        responde alreadyAuthenticated pero otra instancia está persistiendo el TA.
        """
        from time import sleep
        from django.utils import timezone as dj_tz
        deadline = dj_tz.now() + timedelta(seconds=timeout_seconds)
        while dj_tz.now() < deadline:
            # Intentar leer desde cache
            cached_token = cache.get(self.token_cache_key)
            cached_sign = cache.get(self.sign_cache_key)
            if cached_token and cached_sign:
                logger.info("TA encontrado en cache durante espera")
                return cached_token, cached_sign
            # Intentar desde BD
            if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
                exp = getattr(self.config, 'afip_token_expiration', None)
                if not exp or exp > dj_tz.now():
                    logger.info("TA encontrado en BD durante espera")
                    return self.config.afip_token, self.config.afip_sign
            sleep(interval_seconds)
        return None
    
    def _generate_new_token(self) -> Tuple[str, str, Optional[datetime], Optional[datetime]]:
        """
        Genera un nuevo token y sign desde AFIP
        
        Returns:
            Tuple[str, str]: (token, sign)
        """
        try:
            # Crear el XML de login
            login_xml = self._create_login_xml()
            
            # Enviar request a AFIP
            response = self._send_login_request(login_xml)
            
            # Parsear respuesta
            token, sign, gen_dt, exp_dt = self._parse_login_response(response)
            
            return token, sign, gen_dt, exp_dt
            
        except Exception as e:
            logger.error(f"Error en generación de token: {str(e)}")
            raise
    
    def _create_login_xml(self) -> str:
        """
        Crea el XML de login para WSAA
        
        Returns:
            str: XML de login
        """
        # Tiempos en ISO-8601 con offset -03:00 (AFIP requiere ventana de tiempo y formato ISO)
        # Según manual: ventana de ±10 minutos para evitar problemas de sincronización
        now = datetime.now(dt_timezone.utc)
        generation_time = (now - timedelta(minutes=10)).astimezone().isoformat(timespec='seconds')
        expiration_time = (now + timedelta(minutes=10)).astimezone().isoformat(timespec='seconds')
        
        # uniqueId numérico (debe ser entero simple)
        unique_id = int(now.timestamp())
        
        # Crear XML de login (TRA) - sin BOM y con encoding explícito
        login_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
    <header>
        <uniqueId>{unique_id}</uniqueId>
        <generationTime>{generation_time}</generationTime>
        <expirationTime>{expiration_time}</expirationTime>
    </header>
    <service>{self.WSFEv1_SERVICE}</service>
</loginTicketRequest>"""
        
        # Limpiar cualquier BOM o caracteres extraños
        login_xml = login_xml.encode('utf-8').decode('utf-8')
        
        return login_xml
    
    def _send_login_request(self, login_xml: str) -> str:
        """
        Envía el request de login a AFIP
        
        Args:
            login_xml: XML de login
            
        Returns:
            str: Respuesta XML de AFIP
        """
        try:
            # Pequeño delay para evitar conflictos de TA
            import time
            time.sleep(2)
            
            # Construir CMS (PKCS#7) firmado del XML (TRA)
            signed_cms_b64 = self._sign_xml(login_xml)
            
            # Log del TRA y CMS
            logger.info(f"TRA (Login XML) generado: {len(login_xml)} chars")
            logger.debug(f"TRA content:\n{login_xml}")
            logger.info(f"CMS firmado (Base64): {len(signed_cms_b64)} chars")
            logger.debug(f"CMS preview (primeros 100 chars): {signed_cms_b64[:100]}")
            
            # Headers para el request (según manual: SOAPAction: urn:LoginCms)
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'urn:LoginCms'
            }
            
            # Body del request SOAP - sin BOM y con encoding explícito
            soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsaa="{self.WSAA_SOAP_NS}">
    <soapenv:Header/>
    <soapenv:Body>
        <wsaa:loginCms>
            <wsaa:in0>{signed_cms_b64}</wsaa:in0>
        </wsaa:loginCms>
    </soapenv:Body>
</soapenv:Envelope>"""
            
            # Limpiar cualquier BOM o caracteres extraños del SOAP
            soap_body = soap_body.encode('utf-8').decode('utf-8')
            
            logger.info(f"Enviando SOAP request a {self.wsaa_url}")
            logger.debug(f"SOAP Body completo:\n{soap_body[:800]}")
            
            # Enviar request con timeout más largo
            # Timeouts y reintentos controlados
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=2)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            response = session.post(
                self.wsaa_url,
                data=soap_body,
                headers=headers,
                timeout=(10, 20)  # (connect, read)
            )
            # WSAA puede devolver 500 con SOAP Fault; no cortar aquí
            # Decodificar contenido de forma robusta y limpiar BOM/espacios/control
            content_bytes = response.content or b""
            # Intento 1: UTF-8 estricto
            try:
                text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Intento 2: Latin-1 estricto
                text = content_bytes.decode('latin-1')
            
            # Remover caracteres de control y BOM al inicio, y recortar hasta el primer '<'
            try:
                import re
                # Eliminar BOM si existe
                if text and text[0] == '\ufeff':
                    text = text[1:]
                # Remover caracteres de control no permitidos por XML
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                # Recortar cualquier basura previa al primer tag XML
                first_lt = text.find('<')
                text_clean = text[first_lt:] if first_lt != -1 else text
            except Exception:
                text_clean = text

            logger.info(f"WSAA respondió HTTP {response.status_code}")
            logger.info(f"Respuesta AFIP recibida: {len(text_clean)} caracteres")
            logger.debug(f"Request SOAP a WSAA:\n{soap_body[:500]}")
            logger.debug(f"Response SOAP de WSAA (preview):\n{text_clean[:500]}")
            
            # Log más detallado para debugging
            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code} de AFIP")
                logger.error(f"Headers de respuesta: {dict(response.headers)}")
                logger.error(f"Contenido completo: {text_clean}")
                
                # Manejar caso especial: TA ya válido (WSAA Fault: coe.alreadyAuthenticated)
                if response.status_code == 500 and ("TA valido" in text_clean or "alreadyAuthenticated" in text_clean):
                    logger.warning("AFIP indica que hay un TA vigente para este CEE/servicio")
                    # Si tenemos TA persistido y no vencido, reutilizarlo
                    try:
                        from django.utils import timezone as dj_tz
                        if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
                            exp = getattr(self.config, 'afip_token_expiration', None)
                            if not exp or exp > dj_tz.now():
                                logger.info("Reutilizando TA persistido localmente (WSAA rechazó nueva emisión)")
                                token = self.config.afip_token
                                sign = self.config.afip_sign
                                gen = getattr(self.config, 'afip_token_generation', dj_tz.now())
                                exp_dt = exp or (dj_tz.now() + timedelta(hours=6))
                                simulated_xml = f'''<?xml version="1.0" encoding="UTF-8"?>\n<loginTicketResponse>\n    <token>{token}</token>\n    <sign>{sign}</sign>\n    <generationTime>{gen.isoformat()}</generationTime>\n    <expirationTime>{exp_dt.isoformat()}</expirationTime>\n</loginTicketResponse>'''
                                return simulated_xml
                        # Esperar brevemente a que otro proceso persista el TA y reintentar reutilización
                        logger.info("Esperando aparición de TA local tras alreadyAuthenticated...")
                        token_sign = self._wait_for_existing_ta(timeout_seconds=60, interval_seconds=5)
                        if token_sign is not None:
                            token, sign = token_sign
                            gen = getattr(self.config, 'afip_token_generation', dj_tz.now())
                            exp_dt = getattr(self.config, 'afip_token_expiration', dj_tz.now() + timedelta(hours=6))
                            simulated_xml = f'''<?xml version="1.0" encoding="UTF-8"?>\n<loginTicketResponse>\n    <token>{token}</token>\n    <sign>{sign}</sign>\n    <generationTime>{gen.isoformat()}</generationTime>\n    <expirationTime>{exp_dt.isoformat()}</expirationTime>\n</loginTicketResponse>'''
                            return simulated_xml
                    except Exception:
                        pass
                    # Sin TA local disponible: no podemos obtenerlo del Fault; esperar expiración o unificar storage
                    raise AfipAuthError("WSAA indicó TA válido, pero no hay TA local disponible para reutilizar")
                
                raise AfipAuthError(f"AFIP respondió con error HTTP {response.status_code}: {text_clean[:300]}")
            
            # Verificar que la respuesta contiene XML válido
            if not text_clean.strip():
                raise AfipAuthError("AFIP devolvió respuesta vacía")
            
            logger.info(f"Primeros 200 caracteres: {text_clean[:200]}")
            logger.info(f"Últimos 200 caracteres: {text_clean[-200:]}")
            return text_clean
            
        except requests.RequestException as e:
            logger.error(f"Error en request a AFIP: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en envío de login: {str(e)}")
            raise
    
    def _sign_xml(self, xml_content: str) -> str:
        """
        Firma el XML con el certificado digital
        
        Args:
            xml_content: Contenido XML a firmar
            
        Returns:
            str: XML firmado en base64
        """
        try:
            # Leer certificado y clave privada
            cert_path = self.config.certificate_path
            key_path = self.config.private_key_path
            
            if not os.path.exists(cert_path):
                raise FileNotFoundError(f"Certificado no encontrado: {cert_path}")
            if not os.path.exists(key_path):
                raise FileNotFoundError(f"Clave privada no encontrada: {key_path}")
            
            # Cargar certificado
            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
            
            # Cargar clave privada
            with open(key_path, 'rb') as key_file:
                key_data = key_file.read()
            
            # Parsear certificado y clave
            cert = x509.load_pem_x509_certificate(cert_data)
            private_key = serialization.load_pem_private_key(key_data, password=None)
            
            # Construir CMS (PKCS#7) detached del contenido del TRA
            builder = pkcs7.PKCS7SignatureBuilder().set_data(xml_content.encode('utf-8')).add_signer(
                cert,
                private_key,
                hashes.SHA256()
            )
            # No DetachedSignature -> el contenido queda embebido en el CMS, como espera WSAA
            cms_der = builder.sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
            
            # Base64 del CMS
            import base64
            signed_cms_b64 = base64.b64encode(cms_der).decode('utf-8')
            
            logger.info("TRA firmado en CMS exitosamente")
            return signed_cms_b64
            
        except Exception as e:
            logger.error(f"Error firmando XML: {str(e)}")
            raise
    
    def _parse_login_response(self, response_xml: str) -> Tuple[str, str, Optional[datetime], Optional[datetime]]:
        """
        Parsea la respuesta de login de AFIP
        
        Args:
            response_xml: Respuesta XML de AFIP
            
        Returns:
            Tuple[str, str]: (token, sign)
        """
        try:
            # Limpiar y preparar XML para parsing
            xml_clean = response_xml.strip()
            
            # Intentar parsear con diferentes estrategias
            root = None
            import re
            try:
                # Intentar parsear limpiando caracteres de control primero
                xml_clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_clean)
                xml_clean = xml_clean.lstrip('\ufeff')
                # Buscar primer < para recortar basura previa
                first_lt = xml_clean.find('<')
                if first_lt > 0:
                    xml_clean = xml_clean[first_lt:]
                root = ET.fromstring(xml_clean)
            except ET.ParseError as e:
                # Log del XML problemático para debugging
                logger.error(f"XML problemático (primeros 500 chars): {xml_clean[:500]}")
                logger.error(f"XML problemático (últimos 500 chars): {xml_clean[-500:]}")
                # Intentar una última vez sin limpieza (por si la limpieza rompió algo)
                try:
                    root = ET.fromstring(response_xml.strip())
                except:
                    raise ET.ParseError(f"Error parseando XML de AFIP: {str(e)}")
            
            # Buscar loginCmsReturn y extraer el contenido base64
            ns = {'wsaa': self.WSAA_SOAP_NS}
            login_return = root.find('.//wsaa:loginCmsReturn', ns)
            if login_return is None:
                # algunos despliegues retornan sin prefijo; intentar búsqueda por nombre
                login_return = root.find('.//loginCmsReturn')
            if login_return is None or not (login_return.text and login_return.text.strip()):
                # Intentar leer SOAP Fault para dar un mensaje claro
                fault = root.find('.//faultstring')
                if fault is not None and fault.text:
                    # Manejo especial: si hay TA válido, intentar reutilizar persistido
                    msg = fault.text
                    if 'TA valido' in msg or 'TA válido' in msg:
                        try:
                            from django.utils import timezone as dj_tz
                            if getattr(self.config, 'afip_token', None) and getattr(self.config, 'afip_sign', None):
                                exp = getattr(self.config, 'afip_token_expiration', None)
                                if exp and exp > dj_tz.now():
                                    logger.info("WSAA indica TA vigente; reutilizando TA persistido")
                                    return self.config.afip_token, self.config.afip_sign, getattr(self.config, 'afip_token_generation', None), exp
                        except Exception:
                            pass
                    raise AfipAuthError(f"WSAA Fault: {fault.text}")
                raise AfipAuthError("Respuesta de AFIP no contiene loginCmsReturn")
            raw_content = login_return.text.strip()
            if not raw_content:
                raise AfipAuthError("Respuesta de AFIP vacía")

            # Algunas implementaciones retornan XML escapado en lugar de base64
            # Heurística: si contiene '<' o entidades '&lt;', intentar desescapar y parsear como XML
            decoded_xml_bytes = None
            try:
                import base64
                trial = base64.b64decode(raw_content, validate=False)
                # Aceptar como base64 solo si se parece a XML
                if trial and (b'<' in trial or b'<loginTicketResponse' in trial):
                    decoded_xml_bytes = trial
            except Exception:
                decoded_xml_bytes = None

            if decoded_xml_bytes is not None:
                to_parse = decoded_xml_bytes
            else:
                # Intentar des-escapar HTML y parsear
                try:
                    import html
                    unescaped = html.unescape(raw_content)
                    to_parse = unescaped.encode('utf-8')
                except Exception:
                    raise AfipAuthError("No se pudo decodificar contenido de loginCmsReturn")

            # Parsear el contenido XML del ticket con estrategia robusta
            def _parse_ticket(xml_bytes_or_str):
                try:
                    root_local = ET.fromstring(xml_bytes_or_str)
                    tk = root_local.find('.//token')
                    sg = root_local.find('.//sign')
                    return (tk.text if tk is not None else None, sg.text if sg is not None else None, root_local)
                except Exception:
                    return (None, None, None)

            token, sign, ticket_root = _parse_ticket(to_parse)

            # Fallback: si viene escapado como string y el parse anterior falló, des-escapar manualmente y buscar por regex
            if not token or not sign:
                try:
                    import html, re
                    if isinstance(to_parse, (bytes, bytearray)):
                        unesc = to_parse.decode('utf-8', errors='ignore')
                    else:
                        unesc = str(to_parse)
                    unesc = html.unescape(unesc)
                    # Limpiar BOM/control y recortar hasta primer '<'
                    unesc = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', unesc).lstrip('\ufeff')
                    first_lt = unesc.find('<')
                    if first_lt > 0:
                        unesc = unesc[first_lt:]
                    # Segundo intento con parser
                    token2, sign2, ticket_root2 = _parse_ticket(unesc)
                    token = token or token2
                    sign = sign or sign2
                    if ticket_root is None:
                        ticket_root = ticket_root2
                    # Último recurso: regex directa en texto
                    if not token:
                        m = re.search(r'<token>([^<]+)</token>', unesc)
                        token = m.group(1) if m else None
                    if not sign:
                        m = re.search(r'<sign>([^<]+)</sign>', unesc)
                        sign = m.group(1) if m else None
                except Exception:
                    pass

            if not token or not sign:
                raise AfipAuthError("Token o sign no encontrados en respuesta de AFIP")

            # Extraer tiempos de generación y expiración si están presentes
            gen_dt = None
            exp_dt = None
            try:
                from django.utils.dateparse import parse_datetime
                if ticket_root is None:
                    ticket_root = ET.fromstring(to_parse if isinstance(to_parse, (bytes, bytearray)) else to_parse.encode('utf-8'))
                gen_el = ticket_root.find('.//generationTime')
                exp_el = ticket_root.find('.//expirationTime')
                if gen_el is None or exp_el is None:
                    # algunos esquemas los traen en header
                    gen_el = ticket_root.find('.//header/generationTime') if gen_el is None else gen_el
                    exp_el = ticket_root.find('.//header/expirationTime') if exp_el is None else exp_el
                if gen_el is not None and gen_el.text:
                    gen_dt = parse_datetime(gen_el.text)
                if exp_el is not None and exp_el.text:
                    exp_dt = parse_datetime(exp_el.text)
            except Exception:
                pass
            
            if not token or not sign:
                raise AfipAuthError("Token o sign vacíos en respuesta de AFIP")
            
            logger.info("Token y sign extraídos exitosamente de respuesta AFIP")
            return token, sign, gen_dt, exp_dt
            
        except ET.ParseError as e:
            preview = (response_xml or "")[:300]
            logger.error(f"Error parseando respuesta XML de AFIP: {str(e)} | Preview: {preview}")
            raise AfipAuthError(f"Error parseando respuesta de AFIP: {str(e)}")
        except Exception as e:
            logger.error(f"Error procesando respuesta de AFIP: {str(e)}")
            raise AfipAuthError(f"Error procesando respuesta de AFIP: {str(e)}")
    
    def clear_cache(self):
        """
        Limpia el cache de tokens
        """
        cache.delete(self.token_cache_key)
        cache.delete(self.sign_cache_key)
        logger.info(f"Cache de tokens AFIP limpiado para hotel {self.config.hotel.id}")
    
    def is_token_valid(self) -> bool:
        """
        Verifica si el token actual es válido
        
        Returns:
            bool: True si el token es válido
        """
        cached_token = cache.get(self.token_cache_key)
        return cached_token is not None


class AfipAuthError(Exception):
    """
    Excepción personalizada para errores de autenticación AFIP
    """
    pass
