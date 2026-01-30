#!/usr/bin/env python3
"""
Script para generar variables de entorno para una nueva instancia de cliente en Railway.

Uso:
    python scripts/generate_railway_env.py --cliente "hotel-plaza" --dominio "hotelplaza.alojasys.com"
"""

import argparse
import secrets
import sys
from pathlib import Path

# Agregar el directorio backend al path para importar Django
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from django.core.management.utils import get_random_secret_key
except ImportError:
    print("Error: Django no está instalado. Instala las dependencias primero.")
    sys.exit(1)


def generate_secret_key():
    """Genera una SECRET_KEY segura para Django."""
    return get_random_secret_key()


def generate_env_template(cliente_nombre, dominio_frontend, dominio_backend=None):
    """
    Genera un template de variables de entorno para Railway.
    
    Args:
        cliente_nombre: Nombre del cliente (ej: "hotel-plaza")
        dominio_frontend: Dominio del frontend (ej: "hotelplaza.alojasys.com")
        dominio_backend: Dominio del backend (ej: "api.hotelplaza.alojasys.com")
                         Si no se proporciona, se genera automáticamente.
    """
    if not dominio_backend:
        # Generar dominio backend basado en el frontend
        if dominio_frontend.startswith("http"):
            dominio_backend = dominio_frontend.replace("https://", "https://api.").replace("http://", "http://api.")
        else:
            dominio_backend = f"api.{dominio_frontend}"
    
    secret_key = generate_secret_key()
    
    template = f"""# =============================================================================
# Variables de Entorno para Cliente: {cliente_nombre}
# =============================================================================
# 
# INSTRUCCIONES:
# 1. Copia estas variables a Railway en el servicio del BACKEND
# 2. Railway automáticamente creará DATABASE_URL y REDIS_URL cuando conectes los servicios
# 3. Ajusta los valores según las necesidades del cliente
# 4. NO compartas este archivo públicamente (contiene SECRET_KEY)
#
# =============================================================================

# Django Core
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS={dominio_frontend},{dominio_backend}

# URLs
FRONTEND_URL=https://{dominio_frontend}
EXTERNAL_BASE_URL=https://{dominio_backend}

# Base de Datos
# NOTA: Railway creará automáticamente DATABASE_URL cuando conectes PostgreSQL
# No necesitas configurarlo manualmente, pero si lo haces, usa:
# DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require

# Redis
# NOTA: Railway creará automáticamente REDIS_URL cuando conectes Redis
# No necesitas configurarlo manualmente

# Cloudinary (si usas almacenamiento en la nube)
# USE_CLOUDINARY=True
# CLOUDINARY_CLOUD_NAME=tu-cloud-name
# CLOUDINARY_API_KEY=tu-api-key
# CLOUDINARY_API_SECRET=tu-api-secret

# Email (Resend)
# RESEND_API_KEY=tu-resend-api-key
# USE_RESEND_API=True
# DEFAULT_FROM_EMAIL=noreply@{dominio_frontend}

# AFIP (Facturación Electrónica Argentina)
# AFIP_TEST_MODE=False
# AFIP_USE_MOCK=False
# AFIP_CERTIFICATE_PATH=/path/to/certificate.crt
# AFIP_PRIVATE_KEY_PATH=/path/to/private.key

# Otros
# USE_SQLITE=False
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
"""
    
    return template


def generate_frontend_env(cliente_nombre, dominio_backend):
    """
    Genera variables de entorno para el frontend.
    
    Args:
        cliente_nombre: Nombre del cliente
        dominio_backend: URL completa del backend (ej: "https://api.hotelplaza.alojasys.com")
    """
    template = f"""# =============================================================================
# Variables de Entorno para Frontend - Cliente: {cliente_nombre}
# =============================================================================
# 
# INSTRUCCIONES:
# 1. Copia estas variables a Railway en el servicio del FRONTEND
# 2. Asegúrate de que el dominio del backend sea correcto
#
# =============================================================================

VITE_API_URL={dominio_backend}
"""
    
    return template


def main():
    parser = argparse.ArgumentParser(
        description="Genera variables de entorno para nueva instancia de cliente en Railway"
    )
    parser.add_argument(
        "--cliente",
        required=True,
        help="Nombre del cliente (ej: 'hotel-plaza')"
    )
    parser.add_argument(
        "--dominio-frontend",
        required=True,
        help="Dominio del frontend (ej: 'hotelplaza.alojasys.com')"
    )
    parser.add_argument(
        "--dominio-backend",
        help="Dominio del backend (ej: 'api.hotelplaza.alojasys.com'). Si no se proporciona, se genera automáticamente."
    )
    parser.add_argument(
        "--output-dir",
        default="railway_envs",
        help="Directorio donde guardar los archivos (default: railway_envs)"
    )
    
    args = parser.parse_args()
    
    # Generar templates
    backend_env = generate_env_template(
        args.cliente,
        args.dominio_frontend,
        args.dominio_backend
    )
    
    # Determinar dominio backend
    if args.dominio_backend:
        backend_url = f"https://{args.dominio_backend}"
    else:
        backend_url = f"https://api.{args.dominio_frontend}"
    
    frontend_env = generate_frontend_env(args.cliente, backend_url)
    
    # Crear directorio de salida
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Guardar archivos
    backend_file = output_dir / f"{args.cliente}_backend.env"
    frontend_file = output_dir / f"{args.cliente}_frontend.env"
    
    backend_file.write_text(backend_env, encoding="utf-8")
    frontend_file.write_text(frontend_env, encoding="utf-8")
    
    print(f"✅ Variables de entorno generadas para cliente: {args.cliente}")
    print(f"\n📁 Archivos creados:")
    print(f"   - Backend:  {backend_file}")
    print(f"   - Frontend: {frontend_file}")
    print(f"\n📋 Próximos pasos:")
    print(f"   1. Revisa y ajusta las variables según las necesidades del cliente")
    print(f"   2. Copia las variables del backend a Railway (servicio backend)")
    print(f"   3. Copia las variables del frontend a Railway (servicio frontend)")
    print(f"   4. Railway creará automáticamente DATABASE_URL y REDIS_URL")
    print(f"\n⚠️  IMPORTANTE: No compartas estos archivos públicamente (contienen SECRET_KEY)")


if __name__ == "__main__":
    main()
