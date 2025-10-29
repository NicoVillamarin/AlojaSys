"""
Script para generar un TA real de WSAA y darte el token/sign para inyectar manualmente
EJECUTA: python generate_real_ta_for_injection.py
"""
import os
import sys
# NO forzar USE_SQLITE = True porque queremos PostgreSQL del Docker
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
# Dentro del contenedor el CWD ya es /app, no hace falta chdir
import django
django.setup()

from apps.invoicing.models import AfipConfig
from apps.invoicing.services.afip_auth_service import AfipAuthService
from django.utils import timezone

def main():
    try:
        # Buscar tu config
        config = AfipConfig.objects.first()
        if not config:
            print("❌ No hay AfipConfig. Creá una primero desde el admin/frontend.")
            return
        
        print("=" * 80)
        print("GENERANDO TA REAL DE WSAA")
        print("=" * 80)
        print(f"CUIT: {config.cuit}")
        print(f"Punto de Venta: {config.point_of_sale}")
        print(f"Ambiente: {config.environment}")
        print(f"Certificado: {config.certificate_path}")
        print(f"Clave: {config.private_key_path}")
        print("=" * 80)
        
        # Crear servicio de auth
        auth_service = AfipAuthService(config)
        
        # Generar TA
        print("\n⏳ Generando TA desde WSAA...")
        token, sign, gen_dt, exp_dt = auth_service._generate_new_token()
        
        print("\n" + "=" * 80)
        print("✅ TA GENERADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\nToken: {token[:80]}...")
        print(f"Sign: {sign[:80]}...")
        print(f"Generation: {gen_dt}")
        print(f"Expiration: {exp_dt}")
        
        print("\n" + "=" * 80)
        print("📋 DÁLE ESTO A POSTMAN/FRONTEND PARA INYECTAR:")
        print("=" * 80)
        print(f"""
POST http://localhost:8000/api/invoicing/afip-configs/{config.id}/inject_ta/
Content-Type: application/json

{{
  "token": "{token}",
  "sign": "{sign}",
  "generation_time": "{gen_dt.isoformat()}",
  "expiration_time": "{exp_dt.isoformat()}"
}}
""")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

