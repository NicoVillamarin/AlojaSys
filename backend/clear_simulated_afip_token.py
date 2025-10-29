"""
Script para limpiar tokens AFIP simulados
Ejecuta: python clear_simulated_afip_token.py
"""
import os
import sys
import django

# Forzar SQLite
os.environ.setdefault('USE_SQLITE', 'True')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')

# Cambiar a directorio backend
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

django.setup()

from apps.invoicing.models import AfipConfig
from django.core.cache import cache

def main():
    """Busca y limpia tokens AFIP simulados"""
    
    # Buscar configuraciones con tokens simulados
    configs = AfipConfig.objects.filter(
        afip_token__startswith='SIMULATED_TOKEN_'
    )
    
    if not configs.exists():
        print("✓ No se encontraron tokens simulados")
        return
    
    print(f"Encontradas {configs.count()} configuración(es) con tokens simulados\n")
    
    # Limpiar cada configuración
    for config in configs:
        try:
            token_before = config.afip_token
            
            # Limpiar en BD
            config.afip_token = ""
            config.afip_sign = ""
            config.afip_token_generation = None
            config.afip_token_expiration = None
            config.save(update_fields=['afip_token', 'afip_sign', 'afip_token_generation', 'afip_token_expiration'])
            
            # Limpiar cache
            cache_key_token = f"afip_token_{config.hotel.id}_{config.environment}"
            cache_key_sign = f"afip_sign_{config.hotel.id}_{config.environment}"
            cache.delete(cache_key_token)
            cache.delete(cache_key_sign)
            
            print(f"✓ Limpiado AfipConfig #{config.id}")
            print(f"  Hotel: {config.hotel.name}")
            print(f"  Ambiente: {config.environment}")
            print(f"  Token anterior: {token_before[:50]}...")
            print()
            
        except Exception as e:
            print(f"✗ Error limpiando AfipConfig #{config.id}: {str(e)}")
            print()
    
    print("✓✓✓ Limpieza completada")
    print("   Ahora intenta generar una factura y se pedirá un TA nuevo")

if __name__ == '__main__':
    main()

