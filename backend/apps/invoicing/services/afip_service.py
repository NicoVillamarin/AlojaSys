"""
Servicio unificado de AFIP
Facilita el uso de todos los servicios de AFIP desde un solo punto
"""

import logging
from typing import Dict, Optional
from django.conf import settings
from .afip_auth_service import AfipAuthService, AfipAuthError
from .afip_invoice_service import AfipInvoiceService, AfipInvoiceError
from .afip_test_service import AfipTestService, AfipTestError

logger = logging.getLogger(__name__)


class AfipService:
    """
    Servicio unificado para integración con AFIP
    Facilita el uso de todos los servicios de AFIP
    """
    
    def __init__(self, config):
        """
        Inicializa el servicio unificado de AFIP
        
        Args:
            config: Instancia de AfipConfig
        """
        self.config = config
        self.is_production = config.environment == 'production'
        
        # Inicializar servicios específicos
        self.auth_service = AfipAuthService(config)
        
        if self.is_production:
            self.invoice_service = AfipInvoiceService(config)
            self.test_service = None
        else:
            self.invoice_service = AfipTestService(config)
            self.test_service = AfipTestService(config)
        
        logger.info(f"AfipService inicializado para hotel {config.hotel.id} en modo {config.environment}")
    
    def send_invoice(self, invoice) -> Dict:
        """
        Envía una factura a AFIP
        
        Args:
            invoice: Instancia de Invoice
            
        Returns:
            Dict: Respuesta de AFIP
        """
        try:
            if self.is_production:
                logger.info(f"Enviando factura {invoice.number} a AFIP producción")
                return self.invoice_service.send_invoice(invoice)
            else:
                logger.info(f"Enviando factura {invoice.number} a AFIP homologación")
                return self.invoice_service.send_test_invoice(invoice)
                
        except Exception as e:
            logger.error(f"Error enviando factura {invoice.number}: {str(e)}")
            raise
    
    def test_connection(self) -> Dict:
        """
        Prueba la conexión con AFIP
        
        Returns:
            Dict: Resultado de la prueba
        """
        try:
            if self.is_production:
                # En producción, solo probar autenticación
                token, sign = self.auth_service.get_token_and_sign()
                return {
                    'success': True,
                    'message': 'Conexión exitosa con AFIP producción',
                    'environment': 'production',
                    'has_token': bool(token),
                    'has_sign': bool(sign)
                }
            else:
                # En test, usar el servicio de testing
                return self.test_service.test_afip_connection()
                
        except Exception as e:
            logger.error(f"Error probando conexión AFIP: {str(e)}")
            return {
                'success': False,
                'message': f'Error de conexión: {str(e)}',
                'environment': self.config.environment
            }
    
    def validate_environment(self) -> Dict:
        """
        Valida la configuración del ambiente
        
        Returns:
            Dict: Resultado de la validación
        """
        try:
            if self.is_production:
                return self._validate_production_environment()
            else:
                return self.test_service.validate_test_environment()
                
        except Exception as e:
            logger.error(f"Error validando ambiente: {str(e)}")
            return {
                'success': False,
                'message': f'Error validando ambiente: {str(e)}',
                'environment': self.config.environment
            }
    
    def _validate_production_environment(self) -> Dict:
        """
        Valida el ambiente de producción
        
        Returns:
            Dict: Resultado de la validación
        """
        validation_results = {
            'environment': 'production',
            'checks': {},
            'overall_success': True,
            'timestamp': self._get_timestamp()
        }
        
        try:
            # Verificar configuración
            validation_results['checks']['config_environment'] = {
                'success': self.config.environment == 'production',
                'message': f"Environment configurado como: {self.config.environment}"
            }
            
            # Verificar URLs de producción
            validation_results['checks']['production_url'] = {
                'success': 'servicios1.afip.gov.ar' in self.invoice_service.wsfev1_url,
                'message': f"URL de producción: {self.invoice_service.wsfev1_url}"
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
            
            logger.info(f"Validación de ambiente de producción completada: {validation_results['overall_success']}")
            
        except Exception as e:
            logger.error(f"Error en validación de ambiente de producción: {str(e)}")
            validation_results['overall_success'] = False
            validation_results['error'] = str(e)
        
        return validation_results
    
    def get_service_info(self) -> Dict:
        """
        Obtiene información sobre el servicio AFIP
        
        Returns:
            Dict: Información del servicio
        """
        return {
            'environment': self.config.environment,
            'is_production': self.is_production,
            'hotel_id': self.config.hotel.id,
            'cuit': self.config.cuit,
            'point_of_sale': self.config.point_of_sale,
            'wsfev1_url': self.invoice_service.wsfev1_url,
            'wsaa_url': self.auth_service.wsaa_url,
            'services_available': {
                'auth': True,
                'invoice': True,
                'test': not self.is_production
            }
        }
    
    def clear_auth_cache(self):
        """
        Limpia el cache de autenticación
        """
        self.auth_service.clear_cache()
        logger.info("Cache de autenticación AFIP limpiado")
    
    def get_test_parameters(self) -> Optional[Dict]:
        """
        Obtiene parámetros de testing (solo en modo test)
        
        Returns:
            Dict: Parámetros de testing o None si está en producción
        """
        if self.is_production:
            return None
        
        return self.test_service.get_test_parameters()
    
    def _get_timestamp(self) -> str:
        """
        Obtiene timestamp actual
        
        Returns:
            str: Timestamp en formato ISO
        """
        from django.utils import timezone
        return timezone.now().isoformat()


class AfipServiceError(Exception):
    """
    Excepción personalizada para errores del servicio AFIP
    """
    pass