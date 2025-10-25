#!/usr/bin/env python3
"""
Script para generar certificados válidos para AFIP homologación
Este script genera certificados que pueden ser utilizados con AFIP real
"""

import os
import subprocess
import sys
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

def generate_afip_csr(cuit: str, alias: str = "AlojaSys Test System"):
    """Genera un CSR válido para AFIP para un CUIT específico"""
    print("🔧 Generando CSR para AFIP...")
    if not (cuit and cuit.isdigit() and len(cuit) == 11):
        raise ValueError("El CUIT debe tener 11 dígitos numéricos")

    # Datos para el CSR (deben ser reales para AFIP)
    subject_data = {
        'country': 'AR',
        'organization': 'AlojaSys Test',
        'common_name': alias,
        'serial_number': f'CUIT {cuit}'
    }
    
    # Generar clave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Crear el subject
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, subject_data['country']),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_data['organization']),
        x509.NameAttribute(NameOID.COMMON_NAME, subject_data['common_name']),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, subject_data['serial_number']),
    ])
    
    # Crear CSR
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        subject
    ).sign(private_key, hashes.SHA256())
    
    # Guardar clave privada
    key_path = f"certs/afip_private_key_{cuit}.key"
    with open(key_path, "wb") as key_file:
        key_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )
    
    # Guardar CSR
    csr_path = f"certs/afip_certificate_request_{cuit}.csr"
    with open(csr_path, "wb") as csr_file:
        csr_file.write(csr.public_bytes(serialization.Encoding.PEM))
    
    print(f"✅ Clave privada generada: {key_path}")
    print(f"✅ CSR generado: {csr_path}")
    
    return key_path, csr_path

def show_afip_instructions(cuit: str, alias: str):
    """Muestra las instrucciones para obtener certificados de AFIP"""
    print("\n" + "="*80)
    print("📋 INSTRUCCIONES PARA OBTENER CERTIFICADOS DE AFIP")
    print("="*80)
    
    print("\n1. 🌐 Acceder a AFIP:")
    print("   - Ve a https://www.afip.gob.ar")
    print("   - Inicia sesión con tu Clave Fiscal")
    
    print("\n2. 🔧 Adherir al servicio WSASS:")
    print("   - Ve a 'Administrador de Relaciones de Clave Fiscal'")
    print("   - Adhiere al servicio 'WSASS - Autogestión Certificados Homologación'")
    
    print("\n3. 📄 Crear certificado:")
    print("   - Ve a WSASS > 'Nuevo Certificado'")
    print(f"   - Nombre simbólico: '{alias}'")
    print(f"   - Copia el contenido del archivo 'afip_certificate_request_{cuit}.csr'")
    print("   - Pega el contenido en el campo 'Solicitud del certificado'")
    print("   - Haz clic en 'Crear DN y obtener certificado'")
    
    print("\n4. 💾 Descargar certificado:")
    print("   - Copia el certificado generado por AFIP")
    print(f"   - Guárdalo como 'afip_certificate_{cuit}.crt' en la carpeta certs/")
    
    print("\n5. 🔐 Autorizar certificado:")
    print("   - Ve a 'Administrador de Relaciones de Clave Fiscal'")
    print("   - Adhiere al servicio 'Facturación Electrónica'")
    print("   - Selecciona tu certificado como representante")
    
    print("\n6. 🧪 Probar conexión:")
    print("   - Una vez configurado, prueba la conexión desde el frontend")
    
    print("\n" + "="*80)

def main():
    """Función principal"""
    print("🚀 Generando certificados para AFIP homologación")
    print("=" * 60)
    
    # Crear directorio certs si no existe
    os.makedirs("certs", exist_ok=True)
    
    # Leer CUIT y alias desde argumentos
    cuit = None
    alias = None
    if len(sys.argv) >= 2:
        cuit = sys.argv[1]
    if len(sys.argv) >= 3:
        alias = sys.argv[2]
    if not cuit:
        print("Uso: python certs/generate_afip_certificates.py <CUIT_11_DIGITOS> [ALIAS]")
        sys.exit(1)
    if not alias:
        alias = "AlojaSys Test System"

    try:
        # Generar CSR
        key_path, csr_path = generate_afip_csr(cuit, alias)
        
        # Mostrar instrucciones
        show_afip_instructions(cuit, alias)
        
        print("\n📁 Archivos generados:")
        print(f"   🔑 Clave privada: {key_path}")
        print(f"   📋 CSR: {csr_path}")
        
        print("\n📝 Próximos pasos:")
        print("1. Sigue las instrucciones de arriba para obtener el certificado de AFIP")
        print(f"2. Guarda el certificado como 'afip_certificate_{cuit}.crt' en certs/")
        print("3. Copia los archivos al contenedor Docker")
        print("4. Actualiza la configuración en la base de datos")
        print("5. Prueba la conexión desde el frontend")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


