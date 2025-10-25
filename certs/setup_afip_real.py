#!/usr/bin/env python3
"""
Script para configurar certificados reales de AFIP
"""

import os
import sys
from pathlib import Path

def setup_afip_real():
    """Configura certificados reales de AFIP"""
    
    print("🔧 Configurando certificados reales de AFIP")
    print("=" * 60)
    
    # Verificar archivos
    cert_path = Path("certs/afip_certificate.crt")
    key_path = Path("certs/afip_private_key.key")
    
    if not cert_path.exists():
        print("❌ Error: No se encontró afip_certificate.crt")
        print("   Debes obtener el certificado de AFIP primero:")
        print("   1. Ve a https://www.afip.gob.ar")
        print("   2. Accede a WSASS")
        print("   3. Crea un certificado con el CSR generado")
        print("   4. Guarda el certificado como 'afip_certificate.crt' en certs/")
        return False
    
    if not key_path.exists():
        print("❌ Error: No se encontró afip_private_key.key")
        print("   Ejecuta primero: python certs/generate_afip_certificates.py")
        return False
    
    print("✅ Certificados encontrados:")
    print(f"   📄 Certificado: {cert_path}")
    print(f"   🔑 Clave privada: {key_path}")
    
    # Copiar al contenedor Docker
    print("\n🐳 Copiando certificados al contenedor Docker...")
    
    try:
        # Crear directorio en el contenedor
        os.system("docker exec hotel_backend mkdir -p /app/certs")
        
        # Copiar certificado
        os.system(f"docker cp {cert_path} hotel_backend:/app/certs/")
        print("✅ Certificado copiado al contenedor")
        
        # Copiar clave privada
        os.system(f"docker cp {key_path} hotel_backend:/app/certs/")
        print("✅ Clave privada copiada al contenedor")
        
        # Actualizar configuración en la base de datos
        print("\n💾 Actualizando configuración en la base de datos...")
        
        update_script = '''
from apps.invoicing.models import AfipConfig
from apps.core.models import Hotel

# Obtener el primer hotel
hotel = Hotel.objects.first()
if hotel:
    # Actualizar configuración AFIP
    afip_config = AfipConfig.objects.filter(hotel=hotel).first()
    if afip_config:
        afip_config.certificate_path = "/app/certs/afip_certificate.crt"
        afip_config.private_key_path = "/app/certs/afip_private_key.key"
        afip_config.save()
        print(f"✅ Configuración actualizada para hotel: {hotel.name}")
        print(f"   Certificado: {afip_config.certificate_path}")
        print(f"   Clave privada: {afip_config.private_key_path}")
    else:
        print("❌ No hay configuración AFIP para este hotel")
else:
    print("❌ No hay hoteles en la base de datos")
'''
        
        os.system(f'docker exec hotel_backend python manage.py shell -c "{update_script}"')
        
        print("\n🎉 ¡Configuración completada!")
        print("\n📋 Para usar en el modal del frontend:")
        print(f"   Ruta del Certificado (.crt): /app/certs/afip_certificate.crt")
        print(f"   Ruta de la Clave Privada (.key): /app/certs/afip_private_key.key")
        
        print("\n🧪 Prueba la conexión desde el frontend ahora")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_afip_real()
    if not success:
        sys.exit(1)


