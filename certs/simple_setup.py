#!/usr/bin/env python3
"""
Setup SIMPLE para AFIP - Solo lo esencial
"""

import os
from pathlib import Path

def simple_setup():
    print("🚀 Setup SIMPLE para AFIP")
    print("=" * 40)
    
    # Crear directorio
    os.makedirs("certs", exist_ok=True)
    
    print("📋 PASOS SIMPLES:")
    print()
    print("1. 🌐 Ve a https://www.afip.gob.ar")
    print("   - Entra con tu Clave Fiscal")
    print("   - Ve a WSASS (Autogestión Certificados)")
    print("   - Crea un certificado nuevo")
    print("   - Descarga el certificado")
    print()
    print("2. 💾 Guarda el certificado como:")
    print("   certs/afip_certificate.crt")
    print()
    print("3. 🔑 Genera la clave privada:")
    print("   openssl genrsa -out certs/afip_private_key.key 2048")
    print()
    print("4. 🐳 Copia al contenedor:")
    print("   docker cp certs/afip_certificate.crt hotel_backend:/app/certs/")
    print("   docker cp certs/afip_private_key.key hotel_backend:/app/certs/")
    print()
    print("5. ⚙️ En el modal usa estas rutas:")
    print("   Certificado: /app/certs/afip_certificate.crt")
    print("   Clave privada: /app/certs/afip_private_key.key")
    print()
    print("¡Y LISTO! 🎉")

if __name__ == "__main__":
    simple_setup()


