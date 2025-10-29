"""
Servicio de testing con AFIP para homologación
Permite emitir comprobantes de prueba en el ambiente de homologación
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from django.utils import timezone
from .afip_invoice_service import AfipInvoiceService, AfipInvoiceError

logger = logging.getLogger(__name__)


class AfipTestService(AfipInvoiceService):
    """
    Servicio para testing con AFIP en ambiente de homologación
    Extiende AfipInvoiceService pero con configuraciones específicas para testing
    """
    
    def __init__(self, config):
        """
        Inicializa el servicio de testing
        
        Args:
            config: Instancia de AfipConfig (debe estar en modo test)
        """
        if config.environment != 'test':
            raise ValueError("AfipTestService solo puede usarse con configuraciones en modo test")
        
        super().__init__(config)
        logger.info(f"AfipTestService inicializado para hotel {config.hotel.id}")
    
    def send_test_invoice(self, invoice) -> Dict:
        """
        Envía una factura de prueba a AFIP homologación
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            Dict: Respuesta de AFIP con CAE de prueba
        """
        try:
            logger.info(f"Enviando factura de prueba {invoice.number} a AFIP homologación")
            
            # Validaciones específicas para testing
            self._validate_test_invoice(invoice)
            
            # Enviar usando el servicio base
            result = self.send_invoice(invoice)
            
            # Marcar como factura de prueba
            result['is_test'] = True
            result['test_environment'] = 'homologation'
            
            logger.info(f"Factura de prueba {invoice.number} enviada exitosamente")
            return result
            
        except Exception as e:
            logger.error(f"Error enviando factura de prueba {invoice.number}: {str(e)}")
            raise AfipInvoiceError(f"Error enviando factura de prueba: {str(e)}")
    
    def _validate_test_invoice(self, invoice):
        """
        Valida la factura específicamente para testing
        
        Args:
            invoice: Instancia de Invoice
        """
        # Validaciones base
        self._validate_invoice(invoice)
        
        # Validaciones específicas para testing
        if not self._is_valid_test_document_number(getattr(invoice, 'client_document_number', '')):
            logger.warning(f"Documento {invoice.client_document_number} puede no ser válido para testing")
        
        # Validar que los montos sean razonables para testing
        if invoice.total > Decimal('1000000'):  # 1 millón
            logger.warning(f"Total muy alto para testing: {invoice.total}")
        
        logger.info(f"Factura de prueba {invoice.number} validada para testing")
    
    def _is_valid_test_document_number(self, document_number: str) -> bool:
        """
        Valida si un número de documento es válido para testing
        
        Args:
            document_number: Número de documento
            
        Returns:
            bool: True si es válido para testing
        """
        # Para testing, aceptamos varios formatos
        if not document_number:
            return False
        
        # Remover espacios y guiones
        clean_doc = document_number.replace(' ', '').replace('-', '')
        
        # Debe ser numérico
        if not clean_doc.isdigit():
            return False
        
        # Longitud válida para DNI/CUIT
        if len(clean_doc) not in [7, 8, 11]:
            return False
        
        return True
    
    def create_test_invoice_data(self, hotel, reservation=None) -> Dict:
        """
        Crea datos de prueba para una factura
        
        Args:
            hotel: Instancia de Hotel
            reservation: Instancia de Reservation (opcional)
            
        Returns:
            Dict: Datos de prueba para la factura
        """
        test_data = {
            'hotel': hotel,
            'type': 'B',  # Factura B para consumidores finales
            'customer_name': 'Cliente de Prueba',
            'customer_document_type': 'DNI',
            'customer_document_number': '12345678',
            'customer_address': 'Dirección de Prueba 123',
            'customer_city': 'Buenos Aires',
            'customer_postal_code': '1000',
            'customer_country': 'AR',
            'issue_date': timezone.now(),
            'total': Decimal('1000.00'),
            'net_amount': Decimal('909.09'),
            'vat_amount': Decimal('90.91'),
            'currency': 'ARS',
            'status': 'draft',
            'items': [
                {
                    'description': 'Servicio de Alojamiento - Prueba',
                    'quantity': Decimal('1.00'),
                    'unit_price': Decimal('1000.00'),
                    'total_price': Decimal('1000.00'),
                    'vat_rate': Decimal('10.00'),
                    'vat_amount': Decimal('90.91'),
                    'afip_code': '1'
                }
            ]
        }
        
        # Si hay una reserva, usar sus datos
        if reservation:
            test_data.update({
                'reservation': reservation,
                'customer_name': f"{reservation.guest_first_name} {reservation.guest_last_name}",
                'customer_document_number': reservation.guest_document_number or '12345678',
                'total': reservation.total_amount or Decimal('1000.00'),
                'net_amount': (reservation.total_amount or Decimal('1000.00')) / Decimal('1.1'),
                'vat_amount': (reservation.total_amount or Decimal('1000.00')) - ((reservation.total_amount or Decimal('1000.00')) / Decimal('1.1')),
            })
        
        logger.info(f"Datos de prueba creados para hotel {hotel.id}")
        return test_data
    
    def test_afip_connection(self) -> Dict:
        """
        Prueba la conexión con AFIP homologación
        
        Returns:
            Dict: Resultado de la prueba de conexión
        """
        try:
            logger.info("Iniciando prueba de conexión con AFIP homologación")
            
            # Obtener token y sign reales de AFIP
            token, sign = self.auth_service.get_token_and_sign()
            
            if token and sign:
                result = {
                    'success': True,
                    'message': 'Conexión exitosa con AFIP homologación',
                    'environment': 'homologation',
                    'timestamp': timezone.now().isoformat(),
                    'token': token[:20] + '...' if len(token) > 20 else token,
                    'sign': sign[:20] + '...' if len(sign) > 20 else sign,
                    'token_length': len(token),
                    'sign_length': len(sign)
                }
                logger.info("Prueba de conexión exitosa con AFIP real")
            else:
                result = {
                    'success': False,
                    'message': 'No se pudo obtener token de AFIP',
                    'environment': 'homologation',
                    'timestamp': timezone.now().isoformat()
                }
                logger.error("No se pudo obtener token de AFIP")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en prueba de conexión AFIP: {str(e)}")
            return {
                'success': False,
                'message': f'Error de conexión: {str(e)}',
                'environment': 'homologation',
                'timestamp': timezone.now().isoformat()
            }
    
    def get_test_parameters(self) -> Dict:
        """
        Obtiene los parámetros de testing recomendados
        
        Returns:
            Dict: Parámetros de testing
        """
        return {
            'document_types': {
                'DNI': '12345678',
                'CUIT': '20123456789',
                'CUIL': '20123456789',
                'PASAPORTE': '123456789'
            },
            'invoice_types': ['A', 'B', 'C'],
            'amount_ranges': {
                'min': 1.00,
                'max': 100000.00,
                'recommended': 1000.00
            },
            'test_scenarios': [
                'factura_b_consumidor_final',
                'factura_a_responsable_inscripto',
                'nota_credito_devolucion',
                'nota_debito_ajuste'
            ],
            'afip_test_data': {
                'cuit_homologacion': '20123456789',
                'punto_venta_homologacion': '1',
                'url_homologacion': self.wsfev1_url
            }
        }
    
    def validate_test_environment(self) -> Dict:
        """
        Valida que el ambiente de testing esté configurado correctamente
        
        Returns:
            Dict: Resultado de la validación
        """
        validation_results = {
            'environment': 'test',
            'checks': {},
            'overall_success': True,
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            # Verificar configuración
            validation_results['checks']['config_environment'] = {
                'success': self.config.environment == 'test',
                'message': f"Environment configurado como: {self.config.environment}"
            }
            
            # Verificar URLs de homologación
            validation_results['checks']['homologation_url'] = {
                'success': 'wswhomo.afip.gov.ar' in self.wsfev1_url,
                'message': f"URL de homologación: {self.wsfev1_url}"
            }
            
            # Verificar certificados
            import os
            cert_exists = os.path.exists(self.config.certificate_path) if self.config.certificate_path else False
            key_exists = os.path.exists(self.config.private_key_path) if self.config.private_key_path else False
            
            validation_results['checks']['certificates'] = {
                'success': cert_exists and key_exists,
                'message': f"Certificados: cert={cert_exists}, key={key_exists}"
            }
            
            # Verificar CUIT
            validation_results['checks']['cuit'] = {
                'success': len(self.config.cuit) == 11 and self.config.cuit.isdigit(),
                'message': f"CUIT: {self.config.cuit}"
            }
            
            # Verificar punto de venta
            validation_results['checks']['point_of_sale'] = {
                'success': 1 <= self.config.point_of_sale <= 9999,
                'message': f"Punto de venta: {self.config.point_of_sale}"
            }
            
            # Determinar éxito general
            validation_results['overall_success'] = all(
                check['success'] for check in validation_results['checks'].values()
            )
            
            logger.info(f"Validación de ambiente de testing completada: {validation_results['overall_success']}")
            
        except Exception as e:
            logger.error(f"Error en validación de ambiente de testing: {str(e)}")
            validation_results['overall_success'] = False
            validation_results['error'] = str(e)
        
        return validation_results


class AfipTestError(Exception):
    """
    Excepción personalizada para errores de testing AFIP
    """
    pass
