#!/usr/bin/env python3
"""
Script para mostrar las rutas de certificados que deben usarse en el modal
"""

import os
from pathlib import Path

def show_certificate_paths():
    """Muestra las rutas de certificados para el modal"""
    
    # Rutas de los certificados generados
    base_dir = Path(__file__).parent.parent  # Directorio raíz del proyecto
    cert_path = base_dir / "certs" / "test_certificate.crt"
    key_path = base_dir / "certs" / "test_private_key.key"
    
    print("🔧 Rutas de Certificados AFIP para el Modal")
    print("=" * 60)
    
    # Verificar que los archivos existen
    cert_exists = cert_path.exists()
    key_exists = key_path.exists()
    
    print(f"📁 Certificado: {cert_path}")
    print(f"   ✅ Existe: {cert_exists}")
    
    print(f"🔑 Clave privada: {key_path}")
    print(f"   ✅ Existe: {key_exists}")
    
    if cert_exists and key_exists:
        print("\n✅ Ambos certificados están listos")
        print("\n📋 Configuración para el Modal 'Editar Configuración ARCA':")
        print("-" * 60)
        print(f"Hotel: Hotel principal")
        print(f"CUIT: 20123456789")
        print(f"Punto de Venta: 1")
        print(f"Condición Fiscal: Responsable Inscripto")
        print(f"Ambiente: Homologación (Test)")
        print(f"Configuración activa: ✅")
        print(f"")
        print(f"🔧 RUTAS PARA COPIAR EN EL MODAL:")
        print(f"Ruta del Certificado (.crt): {cert_path}")
        print(f"Ruta de la Clave Privada (.key): {key_path}")
        
        print("\n📝 Pasos para configurar:")
        print("1. Abre el modal 'Editar Configuración ARCA'")
        print("2. Copia las rutas de arriba en los campos correspondientes")
        print("3. Guarda la configuración")
        print("4. Prueba con los endpoints de validación")
        
        print("\n🧪 Endpoints de prueba disponibles:")
        print("GET  /api/invoicing/test/certificates/validate/")
        print("POST /api/invoicing/test/afip/connection/")
        print("POST /api/invoicing/test/invoices/generate/")
        print("GET  /api/invoicing/test/afip/status/")
        
    else:
        print("\n❌ Faltan certificados. Ejecuta primero:")
        print("   python certs/generate_certificates_python.py")

if __name__ == "__main__":
    show_certificate_paths()
