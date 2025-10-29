"""
Servicio de emisión de facturas con AFIP WSFEv1
Maneja la emisión de comprobantes electrónicos
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
import requests
from .afip_auth_service import AfipAuthService, AfipAuthError

logger = logging.getLogger(__name__)


class AfipInvoiceService:
    """
    Servicio para emisión de facturas con AFIP WSFEv1
    """
    
    # URLs de AFIP
    WSFEv1_HOMOLOGATION_URL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx"
    WSFEv1_PRODUCTION_URL = "https://servicios1.afip.gov.ar/wsfev1/service.asmx"
    
    # Códigos de tipos de comprobante AFIP
    INVOICE_TYPE_CODES = {
        'A': 1,    # Factura A
        'B': 6,    # Factura B
        'C': 11,   # Factura C
        'E': 19,   # Factura E
        'NC': 3,   # Nota de Crédito
        'ND': 2,   # Nota de Débito
    }
    
    # Códigos de tipos de documento AFIP
    DOCUMENT_TYPE_CODES = {
        'DNI': 96,
        'CUIT': 80,
        'CUIL': 86,
        'PASAPORTE': 94,
        'OTRO': 99,
    }
    
    def __init__(self, config):
        """
        Inicializa el servicio de facturación
        
        Args:
            config: Instancia de AfipConfig
        """
        self.config = config
        self.is_production = config.environment == 'production'
        self.wsfev1_url = self.WSFEv1_PRODUCTION_URL if self.is_production else self.WSFEv1_HOMOLOGATION_URL
        self.auth_service = AfipAuthService(config)
        
    def send_invoice(self, invoice) -> Dict:
        """
        Envía una factura a AFIP para obtener CAE
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            Dict: Respuesta de AFIP con CAE y datos
            
        Raises:
            AfipInvoiceError: Si hay error en el envío
        """
        try:
            logger.info(f"Iniciando envío de factura {invoice.number} a AFIP")
            
            # Validar factura antes del envío
            self._validate_invoice(invoice)
            
            # Obtener token y sign
            token, sign = self.auth_service.get_token_and_sign()
            
            # Construir XML de la factura
            invoice_xml = self._build_invoice_xml(invoice, token, sign)
            
            # Enviar a AFIP
            response = self._send_to_afip(invoice_xml)
            
            # Procesar respuesta
            result = self._process_afip_response(response, invoice)
            
            logger.info(f"Factura {invoice.number} enviada exitosamente a AFIP")
            return result
            
        except AfipAuthError as e:
            logger.error(f"Error de autenticación AFIP para factura {invoice.number}: {str(e)}")
            raise AfipInvoiceError(f"Error de autenticación: {str(e)}")
        except Exception as e:
            logger.error(f"Error enviando factura {invoice.number} a AFIP: {str(e)}")
            raise AfipInvoiceError(f"Error enviando factura: {str(e)}")
    
    def _validate_invoice(self, invoice):
        """
        Valida la factura antes del envío
        
        Args:
            invoice: Instancia de Invoice
            
        Raises:
            AfipInvoiceError: Si la factura no es válida
        """
        # Validar que la factura esté en estado draft
        if invoice.status != 'draft':
            raise AfipInvoiceError(f"La factura debe estar en estado draft, actual: {invoice.status}")
        
        # Validar que tenga items
        if not invoice.items.exists():
            raise AfipInvoiceError("La factura debe tener al menos un item")
        
        # Validar montos
        if invoice.total <= 0:
            raise AfipInvoiceError("El total de la factura debe ser mayor a 0")
        
        # Validar datos del cliente
        if not getattr(invoice, 'client_document_number', None):
            raise AfipInvoiceError("La factura debe tener número de documento del cliente")
        
        # Validar tipo de comprobante
        if invoice.type not in self.INVOICE_TYPE_CODES:
            raise AfipInvoiceError(f"Tipo de comprobante inválido: {invoice.type}")
        
        logger.info(f"Factura {invoice.number} validada correctamente")
    
    def _build_invoice_xml(self, invoice, token: str, sign: str) -> str:
        """
        Construye el XML de la factura para AFIP
        
        Args:
            invoice: Instancia de Invoice
            token: Token de autenticación
            sign: Sign de autenticación
            
        Returns:
            str: XML de la factura
        """
        try:
            # Obtener el próximo número de comprobante según WSFE (FECompUltimoAutorizado)
            cbte_tipo = self.INVOICE_TYPE_CODES[invoice.type]
            try:
                last_auth = self._get_last_authorized_number(token, sign, cbte_tipo, self.config.point_of_sale)
            except Exception:
                last_auth = None
            if isinstance(last_auth, int) and last_auth >= 0:
                next_number = last_auth + 1
            else:
                next_number = self.config.get_next_invoice_number()
            
            # Construir XML base
            # Determinar DocTipo/DocNro según condición IVA del cliente
            tax_cond = str(getattr(invoice, 'client_tax_condition', '5')).strip()  # default CF
            raw_doc_type = self._get_document_type_code(getattr(invoice, 'client_document_type', ''))
            raw_doc_nro = str(getattr(invoice, 'client_document_number', '') or '').strip()

            if tax_cond == '5':  # Consumidor Final
                doc_type_code = 99
                doc_nro = '0'
            elif tax_cond in ('1', '8'):  # RI o Monotributo → CUIT obligatorio
                doc_type_code = 80
                doc_nro = raw_doc_nro if raw_doc_nro and raw_doc_nro.isdigit() else ''
                if len(doc_nro) != 11:
                    # Si CUIT inválido, degradar a CF para evitar rechazo en homologación
                    doc_type_code = 99
                    doc_nro = '0'
            elif tax_cond == '6':  # Exento
                # Usar lo provisto, si no hay, degradar a CF
                doc_type_code = raw_doc_type if raw_doc_type else 96
                doc_nro = raw_doc_nro if raw_doc_nro and raw_doc_nro.isdigit() else ''
                if not doc_nro:
                    doc_type_code = 99
                    doc_nro = '0'
            else:
                # Fallback seguro
                doc_type_code = 99
                doc_nro = '0'

            # Código de condición IVA del receptor (para Opcionales RG 5616)
            cond_code_map = {
                '5': 'CF',   # Consumidor Final
                '1': 'RI',   # Responsable Inscripto
                '8': 'MO',   # Monotributista
                '6': 'EX',   # Exento
            }
            cond_code = cond_code_map.get(tax_cond, 'CF')

            # Intentar obtener la condición real del receptor desde AFIP
            try:
                resolved_cond = self._get_receptor_tax_condition(token, sign, int(doc_type_code), str(doc_nro))
                if resolved_cond:
                    cond_code = str(resolved_cond).strip().upper()
            except Exception:
                pass

            # Para Opcional 2101, usar literal según WSDL/SDKs (RI/CF/MO/EX)
            cond_value = cond_code

            # No forzar el CUIT del emisor como receptor en homologación.
            # Para Consumidor Final (99) mantener DocNro=0, evitando que coincida con el emisor (error 10069).

            # Determinar Concepto (1=Productos, 2=Servicios, 3=Ambos). Hotelería: Servicios.
            try:
                concept_code = int(getattr(invoice, 'concept', 2))
                if concept_code not in (1, 2, 3):
                    concept_code = 2
            except Exception:
                concept_code = 2

            # Log de parámetros críticos para diagnóstico (sin credenciales)
            try:
                # Logear también si 2101 está habilitado (solo una vez por instancia)
                if not getattr(self, '_optionals_logged', False):
                    self._log_available_optionals(token, sign)
                    self._optionals_logged = True
                logger.info(
                    "WSFE parámetros – CbteTipo=%s, PtoVta=%s, Concepto=%s, DocTipo=%s, DocNro=%s, CondIVA=%s, ImpTotal=%s, ImpNeto=%s, ImpIVA=%s",
                    cbte_tipo,
                    self.config.point_of_sale,
                    concept_code,
                    doc_type_code,
                    doc_nro,
                    cond_value,
                    self._format_amount(invoice.total),
                    self._format_amount(invoice.net_amount),
                    self._format_amount(invoice.vat_amount),
                )
            except Exception:
                pass

            xml_parts = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"',
                '               xmlns:wsfe="http://ar.gov.afip.dif.FEV1/">',
                '    <soap:Header/>',
                '    <soap:Body>',
                '        <wsfe:FECAESolicitar>',
                '            <wsfe:Auth>',
                f'                <wsfe:Token>{token}</wsfe:Token>',
                f'                <wsfe:Sign>{sign}</wsfe:Sign>',
                f'                <wsfe:Cuit>{self.config.cuit}</wsfe:Cuit>',
                '            </wsfe:Auth>',
                '            <wsfe:FeCAEReq>',
                '                <wsfe:FeCabReq>',
                f'                    <wsfe:CantReg>1</wsfe:CantReg>',
                f'                    <wsfe:PtoVta>{self.config.point_of_sale}</wsfe:PtoVta>',
                f'                    <wsfe:CbteTipo>{cbte_tipo}</wsfe:CbteTipo>',
                '                </wsfe:FeCabReq>',
                '                <wsfe:FeDetReq>',
                '                    <wsfe:FECAEDetRequest>',
                f'                        <wsfe:Concepto>{concept_code}</wsfe:Concepto>',
                f'                        <wsfe:DocTipo>{doc_type_code}</wsfe:DocTipo>',
                f'                        <wsfe:DocNro>{doc_nro}</wsfe:DocNro>',
                f'                        <wsfe:CbteDesde>{next_number}</wsfe:CbteDesde>',
                f'                        <wsfe:CbteHasta>{next_number}</wsfe:CbteHasta>',
                f'                        <wsfe:CbteFch>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:CbteFch>',
                f'                        <wsfe:ImpTotConc>{self._format_amount(Decimal("0.00"))}</wsfe:ImpTotConc>',
                f'                        <wsfe:ImpNeto>{self._format_amount(invoice.net_amount)}</wsfe:ImpNeto>',
                f'                        <wsfe:ImpOpEx>{self._format_amount(0)}</wsfe:ImpOpEx>',
                f'                        <wsfe:ImpIVA>{self._format_amount(invoice.vat_amount)}</wsfe:ImpIVA>',
                f'                        <wsfe:ImpTrib>{self._format_amount(0)}</wsfe:ImpTrib>',
                f'                        <wsfe:ImpTotal>{self._format_amount(invoice.total)}</wsfe:ImpTotal>',
                f'                        <wsfe:FchServDesde>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchServDesde>',
                f'                        <wsfe:FchServHasta>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchServHasta>',
                f'                        <wsfe:FchVtoPago>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchVtoPago>',
                f'                        <wsfe:MonId>PES</wsfe:MonId>',
                f'                        <wsfe:MonCotiz>1</wsfe:MonCotiz>',
            ]
            
            # Agregar IVA (AlicIva) correctamente
            if invoice.vat_amount > 0 and invoice.net_amount > 0:
                iva_id = self._infer_afip_vat_id(invoice.net_amount, invoice.vat_amount)
                xml_parts.extend([
                    '                        <wsfe:Iva>',
                    '                            <wsfe:AlicIva>',
                    f'                                <wsfe:Id>{iva_id}</wsfe:Id>',
                    f'                                <wsfe:BaseImp>{self._format_amount(invoice.net_amount)}</wsfe:BaseImp>',
                    f'                                <wsfe:Importe>{self._format_amount(invoice.vat_amount)}</wsfe:Importe>',
                    '                            </wsfe:AlicIva>',
                    '                        </wsfe:Iva>'
                ])
            
            # Agregar Opcionales (RG 5616 - Condición IVA del receptor)
            # Determinar dinámicamente el Id del opcional para "Condición IVA del receptor" (RG 5616)
            try:
                cond_optional_id = self._get_condicion_iva_optional_id(token, sign)
            except Exception:
                cond_optional_id = None
            if cond_optional_id:
                xml_parts.extend([
                    '                        <wsfe:Opcionales>',
                    '                            <wsfe:Opcional>',
                    f'                                <wsfe:Id>{cond_optional_id}</wsfe:Id>',
                    f'                                <wsfe:Valor>{cond_value}</wsfe:Valor>',
                    '                            </wsfe:Opcional>',
                    '                        </wsfe:Opcionales>',
                ])
            else:
                logger.warning("No se halló Id de opcional para 'Condición IVA del receptor' en FEParamGetTiposOpcional; no se enviará 2101 por no corresponder")
            
            # Cerrar XML
            xml_parts.extend([
                '                    </wsfe:FECAEDetRequest>',
                '                </wsfe:FeDetReq>',
                '            </wsfe:FeCAEReq>',
                '        </wsfe:FECAESolicitar>',
                '    </soap:Body>',
                '</soap:Envelope>'
            ])
            
            xml_content = '\n'.join(xml_parts)
            logger.info(f"XML de factura {invoice.number} construido correctamente")
            # Log seguro del XML con credenciales enmascaradas (para diagnóstico)
            try:
                masked_xml = self._mask_sensitive_xml(xml_content)
                logger.info("WSFE XML (masked preview 800 chars): %s", masked_xml[:800])
                logger.info("WSFE XML (masked tail 800 chars): %s", masked_xml[-800:])
            except Exception:
                pass
            return xml_content
            
        except Exception as e:
            logger.error(f"Error construyendo XML de factura {invoice.number}: {str(e)}")
            raise
    
    def _get_document_type_code(self, document_type: str) -> int:
        """
        Obtiene el código AFIP para el tipo de documento
        
        Args:
            document_type: Tipo de documento
            
        Returns:
            int: Código AFIP
        """
        # Si viene un código numérico como string ("96", "80"), devolverlo como int
        try:
            if isinstance(document_type, (int,)):
                return int(document_type)
            dt = str(document_type).strip().upper()
            if dt.isdigit():
                return int(dt)
            return self.DOCUMENT_TYPE_CODES.get(dt, 99)  # 99 = Otro
        except Exception:
            return 99

    def _mask_sensitive_xml(self, xml_text: str) -> str:
        """
        Enmascara credenciales sensibles (Token y Sign) en un XML para logging seguro.
        """
        try:
            masked = xml_text
            # Enmascarar Token
            masked = self._mask_between(masked, '<wsfe:Token>', '</wsfe:Token>')
            masked = self._mask_between(masked, '<Token>', '</Token>')
            # Enmascarar Sign
            masked = self._mask_between(masked, '<wsfe:Sign>', '</wsfe:Sign>')
            masked = self._mask_between(masked, '<Sign>', '</Sign>')
            return masked
        except Exception:
            return xml_text

    def _mask_between(self, text: str, start_tag: str, end_tag: str) -> str:
        try:
            start = text.find(start_tag)
            end = text.find(end_tag, start + len(start_tag))
            if start == -1 or end == -1:
                return text
            sensitive = text[start + len(start_tag):end]
            if not sensitive:
                return text
            # Mostrar solo los primeros/últimos 4 chars
            prefix = sensitive[:4]
            suffix = sensitive[-4:] if len(sensitive) > 8 else ''
            masked_val = f"{prefix}...{suffix}" if suffix else f"{prefix}..."
            return text[:start + len(start_tag)] + masked_val + text[end:]
        except Exception:
            return text

    def _get_receptor_tax_condition(self, token: str, sign: str, doc_tipo: int, doc_nro: str) -> str:
        """
        Llama a FEParamGetCondicionIvaReceptor para obtener la condición frente al IVA del receptor.
        Devuelve códigos como: RI (Responsable Inscripto), CF (Consumidor Final), MO (Monotributo), EX (Exento), etc.
        """
        try:
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://ar.gov.afip.dif.FEV1/FEParamGetCondicionIvaReceptor'
            }
            body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsfe="http://ar.gov.afip.dif.FEV1/">
  <soap:Header/>
  <soap:Body>
    <wsfe:FEParamGetCondicionIvaReceptor>
      <wsfe:Auth>
        <wsfe:Token>{token}</wsfe:Token>
        <wsfe:Sign>{sign}</wsfe:Sign>
        <wsfe:Cuit>{self.config.cuit}</wsfe:Cuit>
      </wsfe:Auth>
      <wsfe:DocTipo>{doc_tipo}</wsfe:DocTipo>
      <wsfe:DocNro>{doc_nro}</wsfe:DocNro>
    </wsfe:FEParamGetCondicionIvaReceptor>
  </soap:Body>
</soap:Envelope>'''
            session = requests.Session()
            resp = session.post(self.wsfev1_url, data=body, headers=headers, timeout=(10, 20))
            text = resp.text
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                import re
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text).lstrip('\ufeff')
                root = ET.fromstring(text)
            val_el = root.find('.//{http://ar.gov.afip.dif.FEV1/}CondicionIvaReceptor')
            if val_el is not None and val_el.text:
                return val_el.text.strip()
        except Exception as e:
            logger.error(f"Error consultando FEParamGetCondicionIvaReceptor: {e}")
        # Fallback: Consumidor Final
        return 'CF'

    def _log_available_optionals(self, token: str, sign: str) -> None:
        """
        Consulta FEParamGetTiposOpcional y loguea si el Id 2101 está habilitado.
        """
        try:
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://ar.gov.afip.dif.FEV1/FEParamGetTiposOpcional'
            }
            body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsfe="http://ar.gov.afip.dif.FEV1/">
  <soap:Header/>
  <soap:Body>
    <wsfe:FEParamGetTiposOpcional>
      <wsfe:Auth>
        <wsfe:Token>{token}</wsfe:Token>
        <wsfe:Sign>{sign}</wsfe:Sign>
        <wsfe:Cuit>{self.config.cuit}</wsfe:Cuit>
      </wsfe:Auth>
    </wsfe:FEParamGetTiposOpcional>
  </soap:Body>
</soap:Envelope>'''
            session = requests.Session()
            resp = session.post(self.wsfev1_url, data=body, headers=headers, timeout=(10, 20))
            text = resp.text
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                import re
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text).lstrip('\ufeff')
                root = ET.fromstring(text)
            found = []
            for opc in root.findall('.//{http://ar.gov.afip.dif.FEV1/}OpcionalTipo'):
                id_el = opc.find('.//{http://ar.gov.afip.dif.FEV1/}Id')
                desc_el = opc.find('.//{http://ar.gov.afip.dif.FEV1/}Desc')
                if id_el is not None and id_el.text:
                    found.append((id_el.text.strip(), (desc_el.text.strip() if desc_el is not None and desc_el.text else '')))
            self._available_optionals = found
            enabled_str = ', '.join([f"{fid}:{desc}" for fid, desc in found])
            logger.info(f"WSFE TiposOpcional habilitados (Id:Desc): {enabled_str}")
            has_2101 = any(fid == '2101' for fid, _ in found)
            if has_2101:
                desc = next((d for fid, d in found if fid == '2101'), '')
                logger.info(f"Opcional 2101 habilitado. Desc: {desc}")
            else:
                logger.warning("Opcional 2101 NO aparece habilitado en FEParamGetTiposOpcional")
        except Exception as e:
            logger.error(f"Error consultando FEParamGetTiposOpcional: {e}")

    def _get_condicion_iva_optional_id(self, token: str, sign: str) -> str:
        """Obtiene el Id del opcional correspondiente a 'Condición IVA del receptor' buscando por descripción."""
        # Reutilizar cache si existe
        found = getattr(self, '_available_optionals', None)
        if not found:
            self._log_available_optionals(token, sign)
            found = getattr(self, '_available_optionals', None) or []
        # Buscar por keywords en la descripción
        keywords = ['CONDICION', 'IVA', 'RECEPTOR']
        for fid, desc in found:
            desc_up = (desc or '').upper()
            if all(kw in desc_up for kw in keywords):
                logger.info(f"Usando opcional {fid} para 'Condición IVA del receptor' ({desc})")
                return fid
        # No encontrado
        logger.warning("No se encontró opcional por descripción para 'Condición IVA del receptor'")
        return None

    def _get_last_authorized_number(self, token: str, sign: str, cbte_tipo: int, pto_vta: int) -> Optional[int]:
        """
        Consulta FECompUltimoAutorizado para obtener el último comprobante autorizado.
        """
        try:
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://ar.gov.afip.dif.FEV1/FECompUltimoAutorizado'
            }
            body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsfe="http://ar.gov.afip.dif.FEV1/">
  <soap:Header/>
  <soap:Body>
    <wsfe:FECompUltimoAutorizado>
      <wsfe:Auth>
        <wsfe:Token>{token}</wsfe:Token>
        <wsfe:Sign>{sign}</wsfe:Sign>
        <wsfe:Cuit>{self.config.cuit}</wsfe:Cuit>
      </wsfe:Auth>
      <wsfe:PtoVta>{pto_vta}</wsfe:PtoVta>
      <wsfe:CbteTipo>{cbte_tipo}</wsfe:CbteTipo>
    </wsfe:FECompUltimoAutorizado>
  </soap:Body>
 </soap:Envelope>'''
            session = requests.Session()
            resp = session.post(self.wsfev1_url, data=body, headers=headers, timeout=(10, 20))
            text = resp.text
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                import re
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text).lstrip('\ufeff')
                root = ET.fromstring(text)
            nro_el = root.find('.//{http://ar.gov.afip.dif.FEV1/}CbteNro')
            if nro_el is not None and nro_el.text and nro_el.text.isdigit():
                return int(nro_el.text)
        except Exception as e:
            logger.error(f"Error consultando FECompUltimoAutorizado: {e}")
        return None
    
    def _format_amount(self, amount: Decimal) -> str:
        """
        Formatea un monto para AFIP
        
        Args:
            amount: Monto a formatear
            
        Returns:
            str: Monto formateado
        """
        return f"{amount:.2f}"
    
    def _get_vat_rate(self, invoice) -> str:
        """
        Obtiene la alícuota de IVA para la factura
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            str: Alícuota de IVA
        """
        if invoice.vat_amount > 0 and invoice.net_amount > 0:
            vat_rate = (invoice.vat_amount / invoice.net_amount) * 100
            return f"{vat_rate:.2f}"
        return "0.00"

    def _infer_afip_vat_id(self, net_amount: Decimal, vat_amount: Decimal) -> int:
        """
        Deduce el código AFIP de IVA (Id) a partir de los montos.
        Soporta 10.5% (Id=4), 21% (Id=5), 27% (Id=6), 5% (Id=8), 2.5% (Id=9).
        Por defecto retorna 5 (21%) si no coincide dentro de tolerancia.
        """
        try:
            if net_amount and net_amount > 0:
                perc = float(vat_amount / net_amount * 100)
            else:
                return 5
            candidates = [
                (4, 10.5),
                (5, 21.0),
                (6, 27.0),
                (8, 5.0),
                (9, 2.5),
            ]
            tol = 0.15
            for code, target in candidates:
                if abs(perc - target) <= tol:
                    return code
            # Elegir el más cercano
            closest = min(candidates, key=lambda c: abs(perc - c[1]))
            return closest[0]
        except Exception:
            return 5
    
    def _send_to_afip(self, xml_content: str) -> str:
        """
        Envía el XML a AFIP
        
        Args:
            xml_content: XML de la factura
            
        Returns:
            str: Respuesta XML de AFIP
        """
        try:
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://ar.gov.afip.dif.FEV1/FECAESolicitar'
            }
            
            # Reintentos y timeouts controlados
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=2)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            # Log de request saliente (XML enmascarado)
            try:
                masked_xml = self._mask_sensitive_xml(xml_content)
                logger.info("Enviando a WSFEv1 %s – payload (masked preview 800 chars): %s", self.wsfev1_url, masked_xml[:800])
            except Exception:
                pass

            response = session.post(
                self.wsfev1_url,
                data=xml_content,
                headers=headers,
                timeout=(10, 25)  # (connect, read)
            )
            
            # No forzar raise_for_status: AFIP puede devolver SOAP Fault con 500 pero XML válido
            text_clean = None
            try:
                content_bytes = response.content or b""
                try:
                    text_clean = content_bytes.decode('utf-8', errors='replace')
                except Exception:
                    text_clean = content_bytes.decode('latin-1', errors='replace')
                text_clean = text_clean.lstrip("\ufeff\n\r\t ")
            except Exception:
                text_clean = response.text

            logger.info(f"WSFEv1 respondió HTTP {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code} de WSFEv1")
                logger.error(f"Headers de respuesta: {dict(response.headers)}")
                logger.error(f"Contenido (preview 500 chars): {text_clean[:500]}")
            else:
                # Log de respuesta exitosa (preview)
                try:
                    logger.info("WSFEv1 respuesta (preview 800 chars): %s", text_clean[:800])
                    logger.info("WSFEv1 respuesta (tail 800 chars): %s", text_clean[-800:])
                except Exception:
                    pass
            
            if not text_clean.strip():
                raise AfipInvoiceError("AFIP devolvió respuesta vacía en WSFEv1")
            
            return text_clean
            
        except requests.RequestException as e:
            logger.error(f"Error en request a AFIP: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado enviando a AFIP: {str(e)}")
            raise
    
    def _process_afip_response(self, response_xml: str, invoice) -> Dict:
        """
        Procesa la respuesta de AFIP
        
        Args:
            response_xml: Respuesta XML de AFIP
            invoice: Instancia de Invoice
            
        Returns:
            Dict: Datos procesados de la respuesta
        """
        try:
            # Parsear XML
            try:
                root = ET.fromstring(response_xml)
            except ET.ParseError:
                import re
                xml_clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', response_xml).lstrip('\ufeff')
                root = ET.fromstring(xml_clean)
            
            # Buscar el elemento FECAESolicitarResponse
            response_element = root.find('.//{http://ar.gov.afip.dif.FEV1/}FECAESolicitarResponse')
            
            if response_element is None:
                # Intentar leer Fault para mejor diagnóstico
                fault = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
                if fault is not None:
                    fault_string = fault.findtext('.//faultstring') or 'Fault desconocido'
                    raise AfipInvoiceError(f"SOAP Fault de AFIP: {fault_string}")
                raise AfipInvoiceError("Respuesta de AFIP no contiene FECAESolicitarResponse")
            
            # Buscar el resultado
            result_element = response_element.find('.//{http://ar.gov.afip.dif.FEV1/}FECAESolicitarResult')
            
            if result_element is None:
                raise AfipInvoiceError("Respuesta de AFIP no contiene resultado")
            
            # Extraer datos del resultado
            result_data = self._extract_result_data(result_element)
            
            # Validar resultado (maneja ausencia de 'Resultado')
            if (result_data.get('result') or '').upper() != 'A':
                error_msg = result_data.get('errors', [])
                if not error_msg:
                    error_msg = ['Error desconocido']
                raise AfipInvoiceError(f"AFIP rechazó la factura: {', '.join(error_msg)}")
            
            # Extraer CAE y otros datos
            cae_data = result_data.get('cae_data', {})
            
            if not cae_data.get('cae'):
                raise AfipInvoiceError("AFIP no devolvió CAE")
            
            # Actualizar factura con datos de AFIP
            self._update_invoice_with_afip_data(invoice, cae_data)
            
            logger.info(f"Factura {invoice.number} procesada exitosamente con CAE {cae_data.get('cae')}")
            
            return {
                'success': True,
                'cae': cae_data.get('cae'),
                'cae_expiration': cae_data.get('cae_expiration'),
                'invoice_number': cae_data.get('invoice_number'),
                'afip_response': result_data
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parseando respuesta XML de AFIP: {str(e)}")
            # Guardar preview crudo para diagnóstico
            try:
                invoice.afip_response = {
                    **(invoice.afip_response or {}),
                    'raw_preview': (response_xml or '')[:500],
                    'raw_tail': (response_xml or '')[-500:]
                }
                invoice.save(update_fields=['afip_response', 'updated_at'])
            except Exception:
                pass
            raise AfipInvoiceError(f"Error parseando respuesta de AFIP: {str(e)}")
        except Exception as e:
            logger.error(f"Error procesando respuesta de AFIP: {str(e)}")
            # Guardar preview crudo para diagnóstico
            try:
                invoice.afip_response = {
                    **(invoice.afip_response or {}),
                    'raw_preview': (response_xml or '')[:500],
                    'raw_tail': (response_xml or '')[-500:]
                }
                invoice.save(update_fields=['afip_response', 'updated_at'])
            except Exception:
                pass
            raise AfipInvoiceError(f"Error procesando respuesta de AFIP: {str(e)}")
    
    def _extract_result_data(self, result_element) -> Dict:
        """
        Extrae los datos del resultado de AFIP
        
        Args:
            result_element: Elemento XML del resultado
            
        Returns:
            Dict: Datos extraídos
        """
        data = {}
        
        # Resultado general
        result = result_element.find('.//{http://ar.gov.afip.dif.FEV1/}Resultado')
        if result is not None:
            data['result'] = result.text
        
        # Errores
        errors = []
        for error in result_element.findall('.//{http://ar.gov.afip.dif.FEV1/}Err'):
            code = error.find('.//{http://ar.gov.afip.dif.FEV1/}Code')
            msg = error.find('.//{http://ar.gov.afip.dif.FEV1/}Msg')
            if code is not None or msg is not None:
                code_text = code.text if code is not None else ''
                msg_text = msg.text if msg is not None else ''
                errors.append(f"{code_text}: {msg_text}".strip(': '))
        # Observaciones (también pueden indicar rechazo)
        for obs in result_element.findall('.//{http://ar.gov.afip.dif.FEV1/}Obs'):
            code = obs.find('.//{http://ar.gov.afip.dif.FEV1/}Code')
            msg = obs.find('.//{http://ar.gov.afip.dif.FEV1/}Msg')
            if code is not None or msg is not None:
                code_text = code.text if code is not None else ''
                msg_text = msg.text if msg is not None else ''
                errors.append(f"Obs {code_text}: {msg_text}".strip(': '))
        data['errors'] = errors
        
        # Datos del CAE
        cae_data = {}
        cae = result_element.find('.//{http://ar.gov.afip.dif.FEV1/}CAE')
        if cae is not None:
            cae_data['cae'] = cae.text
        
        cae_expiration = result_element.find('.//{http://ar.gov.afip.dif.FEV1/}CAEFchVto')
        if cae_expiration is not None:
            cae_data['cae_expiration'] = cae_expiration.text
        
        invoice_number = result_element.find('.//{http://ar.gov.afip.dif.FEV1/}CbteDesde')
        if invoice_number is not None:
            cae_data['invoice_number'] = invoice_number.text
        
        data['cae_data'] = cae_data
        
        return data
    
    def _update_invoice_with_afip_data(self, invoice, cae_data: Dict):
        """
        Actualiza la factura con los datos de AFIP
        
        Args:
            invoice: Instancia de Invoice
            cae_data: Datos del CAE de AFIP
        """
        try:
            # Actualizar CAE
            if cae_data.get('cae'):
                invoice.cae = cae_data['cae']
            
            # Actualizar fecha de vencimiento del CAE
            if cae_data.get('cae_expiration'):
                cae_expiration_str = cae_data['cae_expiration']
                cae_expiration = datetime.strptime(cae_expiration_str, '%Y%m%d').date()
                invoice.cae_expiration = timezone.make_aware(
                    datetime.combine(cae_expiration, datetime.min.time())
                )
            
            # Actualizar número de factura
            if cae_data.get('invoice_number'):
                invoice.number = cae_data['invoice_number']
            
            # Actualizar estado
            invoice.status = 'approved'
            
            # Guardar cambios
            invoice.save()
            
            # Actualizar último número de factura en configuración
            if cae_data.get('invoice_number'):
                try:
                    invoice_number = int(cae_data['invoice_number'])
                    if invoice_number > self.config.last_invoice_number:
                        self.config.last_invoice_number = invoice_number
                        self.config.save()
                except (ValueError, TypeError):
                    pass
            
            logger.info(f"Factura {invoice.number} actualizada con datos de AFIP")
            
        except Exception as e:
            logger.error(f"Error actualizando factura {invoice.number} con datos de AFIP: {str(e)}")
            raise


class AfipInvoiceError(Exception):
    """
    Excepción personalizada para errores de facturación AFIP
    """
    pass
