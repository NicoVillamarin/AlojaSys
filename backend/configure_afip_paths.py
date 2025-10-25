#!/usr/bin/env python3
"""
Script para configurar las rutas de certificados AFIP en la base de datos
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.invoicing.models import AfipConfig
from apps.core.models import Hotel

def configure_afip_paths():
    """Configura las rutas de certificados AFIP"""
    
    # Rutas de los certificados generados
    base_dir = Path(__file__).parent.parent  # Directorio raíz del proyecto
    cert_path = base_dir / "certs" / "test_certificate.crt"
    key_path = base_dir / "certs" / "test_private_key.key"
    
    print(f"🔧 Configurando rutas de certificados AFIP...")
    print(f"   Certificado: {cert_path}")
    print(f"   Clave privada: {key_path}")
    
    # Verificar que los archivos existen
    if not cert_path.exists():
        print(f"❌ Error: Certificado no encontrado en {cert_path}")
        print("   Ejecuta primero: python certs/generate_certificates_python.py")
        return False
    
    if not key_path.exists():
        print(f"❌ Error: Clave privada no encontrada en {key_path}")
        print("   Ejecuta primero: python certs/generate_certificates_python.py")
        return False
    
    # Obtener el primer hotel
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ Error: No hay hoteles en la base de datos")
            return False
        
        print(f"🏨 Configurando para hotel: {hotel.name}")
        
        # Crear o actualizar configuración AFIP
        afip_config, created = AfipConfig.objects.get_or_create(
            hotel=hotel,
            defaults={
                'cuit': '20123456789',
                'point_of_sale': 1,
                'environment': 'test',
                'is_active': True,
                'certificate_path': str(cert_path),
                'private_key_path': str(key_path),
            }
        )
        
        if not created:
            # Actualizar rutas existentes
            afip_config.certificate_path = str(cert_path)
            afip_config.private_key_path = str(key_path)
            afip_config.save()
            print("🔄 Configuración AFIP actualizada")
        else:
            print("✨ Nueva configuración AFIP creada")
        
        print("\n✅ Configuración completada:")
        print(f"   Hotel: {hotel.name}")
        print(f"   CUIT: {afip_config.cuit}")
        print(f"   Punto de venta: {afip_config.point_of_sale}")
        print(f"   Ambiente: {afip_config.environment}")
        print(f"   Certificado: {afip_config.certificate_path}")
        print(f"   Clave privada: {afip_config.private_key_path}")
        
        print("\n🎯 Para usar en el modal del frontend:")
        print(f"   Ruta del Certificado (.crt): {cert_path}")
        print(f"   Ruta de la Clave Privada (.key): {key_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = configure_afip_paths()
    if success:
        print("\n🎉 ¡Configuración exitosa! Las rutas ahora aparecerán en el modal.")
    else:
        print("\n💥 Error en la configuración.")
        sys.exit(1)
