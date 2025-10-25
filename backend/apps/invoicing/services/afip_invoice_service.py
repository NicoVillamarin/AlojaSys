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
            # Obtener el próximo número de comprobante
            next_number = self.config.get_next_invoice_number()
            
            # Construir XML base
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
                f'                    <wsfe:CbteTipo>{self.INVOICE_TYPE_CODES[invoice.type]}</wsfe:CbteTipo>',
                '                </wsfe:FeCabReq>',
                '                <wsfe:FeDetReq>',
                '                    <wsfe:FECAEDetRequest>',
                f'                        <wsfe:Concepto>1</wsfe:Concepto>',
                f'                        <wsfe:DocTipo>{self._get_document_type_code(invoice.client_document_type)}</wsfe:DocTipo>',
                f'                        <wsfe:DocNro>{invoice.client_document_number}</wsfe:DocNro>',
                f'                        <wsfe:CbteDesde>{next_number}</wsfe:CbteDesde>',
                f'                        <wsfe:CbteHasta>{next_number}</wsfe:CbteHasta>',
                f'                        <wsfe:CbteFch>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:CbteFch>',
                f'                        <wsfe:ImpTotal>{self._format_amount(invoice.total)}</wsfe:ImpTotal>',
                f'                        <wsfe:ImpTotConc>{self._format_amount(invoice.net_amount)}</wsfe:ImpTotConc>',
                f'                        <wsfe:ImpNeto>{self._format_amount(invoice.net_amount)}</wsfe:ImpNeto>',
                f'                        <wsfe:ImpOpEx>{self._format_amount(0)}</wsfe:ImpOpEx>',
                f'                        <wsfe:ImpTrib>{self._format_amount(0)}</wsfe:ImpTrib>',
                f'                        <wsfe:ImpIVA>{self._format_amount(invoice.vat_amount)}</wsfe:ImpIVA>',
                f'                        <wsfe:FchServDesde>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchServDesde>',
                f'                        <wsfe:FchServHasta>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchServHasta>',
                f'                        <wsfe:FchVtoPago>{invoice.issue_date.strftime("%Y%m%d")}</wsfe:FchVtoPago>',
                f'                        <wsfe:MonId>PES</wsfe:MonId>',
                f'                        <wsfe:MonCotiz>1</wsfe:MonCotiz>',
            ]
            
            # Agregar items de la factura
            xml_parts.append('                        <wsfe:CbtesAsoc>')
            for item in invoice.items.all():
                xml_parts.extend([
                    '                            <wsfe:CbteAsoc>',
                    f'                                <wsfe:Tipo>{self.INVOICE_TYPE_CODES[invoice.type]}</wsfe:Tipo>',
                    f'                                <wsfe:PtoVta>{self.config.point_of_sale}</wsfe:PtoVta>',
                    f'                                <wsfe:Nro>{next_number}</wsfe:Nro>',
                    '                            </wsfe:CbteAsoc>'
                ])
            xml_parts.append('                        </wsfe:CbtesAsoc>')
            
            # Agregar tributos (IVA)
            if invoice.vat_amount > 0:
                xml_parts.extend([
                    '                        <wsfe:Tributos>',
                    '                            <wsfe:Tributo>',
                    '                                <wsfe:Id>5</wsfe:Id>',
                    '                                <wsfe:Desc>IVA</wsfe:Desc>',
                    f'                                <wsfe:BaseImp>{self._format_amount(invoice.net_amount)}</wsfe:BaseImp>',
                    f'                                <wsfe:Alic>{self._get_vat_rate(invoice)}</wsfe:Alic>',
                    f'                                <wsfe:Importe>{self._format_amount(invoice.vat_amount)}</wsfe:Importe>',
                    '                            </wsfe:Tributo>',
                    '                        </wsfe:Tributos>'
                ])
            
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
                'Content-Type': 'application/xml',
                'SOAPAction': 'http://ar.gov.afip.dif.FEV1/FECAESolicitar'
            }
            
            response = requests.post(
                self.wsfev1_url,
                data=xml_content,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info("Request enviado exitosamente a AFIP WSFEv1")
            return response.text
            
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
            root = ET.fromstring(response_xml)
            
            # Buscar el elemento FECAESolicitarResponse
            response_element = root.find('.//{http://ar.gov.afip.dif.FEV1/}FECAESolicitarResponse')
            
            if response_element is None:
                raise AfipInvoiceError("Respuesta de AFIP no contiene FECAESolicitarResponse")
            
            # Buscar el resultado
            result_element = response_element.find('.//{http://ar.gov.afip.dif.FEV1/}FECAESolicitarResult')
            
            if result_element is None:
                raise AfipInvoiceError("Respuesta de AFIP no contiene resultado")
            
            # Extraer datos del resultado
            result_data = self._extract_result_data(result_element)
            
            # Validar resultado
            if result_data['result'] != 'A':
                error_msg = result_data.get('errors', ['Error desconocido'])
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
            raise AfipInvoiceError(f"Error parseando respuesta de AFIP: {str(e)}")
        except Exception as e:
            logger.error(f"Error procesando respuesta de AFIP: {str(e)}")
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
            if code is not None and msg is not None:
                errors.append(f"{code.text}: {msg.text}")
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
