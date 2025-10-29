"""
Comando Django para limpiar tokens AFIP sim fake
Útil cuando hay un TA simulado guardado que está causando errores
"""
import os
import sys
import django

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.invoicing.models import AfipConfig


class Command(BaseCommand):
    help = 'Limpia tokens AFIP sim fake (SIMULATED_TOKEN_*) y regenera TA real'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-id',
            type=int,
            help='ID específico de AfipConfig a limpiar (opcional)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpiar TODOS los AfipConfig con tokens simulados'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Limpiar TODOS los tokens sin importar si son simulados'
        )

    def handle(self, *args, **options):
        # Identificar qué configuraciones limpiar
        if options['config_id']:
            configs = AfipConfig.objects.filter(id=options['config_id'])
            if not configs.exists():
                self.stdout.write(self.style.ERROR(f'No se encontró AfipConfig con id {options["config_id"]}'))
                return
        elif options['all'] or options['force']:
            configs = AfipConfig.objects.all()
        else:
            # Buscar solo configuraciones con tokens simulados
            configs = AfipConfig.objects.filter(
                afip_token__startswith='SIMULATED_TOKEN_'
            )
            
            if not configs.exists():
                self.stdout.write(self.style.WARNING('No se encontraron tokens simulados'))
                self.stdout.write('Usa --all para limpiar todos o --config-id XXX para limpiar uno específico')
                return
        
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
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Limpiado AfipConfig #{config.id} (hotel: {config.hotel.name}, '
                        f'ambiente: {config.environment})\n'
                        f'  Token anterior: {token_before[:50] if token_before else "vacío"}...'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error limpiando AfipConfig #{config.id}: {str(e)}')
                )
        
        total = configs.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n✓✓✓ Total limpiado: {total} configuración(es)')
        )
        self.stdout.write(self.style.SUCCESS('Ahora intenta generar una factura y se pedirá un TA nuevo'))

