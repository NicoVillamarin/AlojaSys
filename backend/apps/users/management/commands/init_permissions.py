"""
Management command para inicializar grupos y permisos del sistema.

Este comando:
1. Crea grupos de usuarios (admin, recepción, etc.)
2. Asigna permisos a cada grupo
3. Muestra un resumen de los permisos creados

Uso:
    python manage.py init_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Inicializa grupos de usuarios y permisos del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Inicializando permisos y grupos...\n'))
        
        # Definir grupos y sus permisos
        groups_config = {
            'Administrador': {
                'description': 'Acceso completo al sistema',
                'apps': ['core', 'rooms', 'reservations', 'payments', 'rates', 'users', 'enterprises', 'invoicing', 'notifications'],
                'all_permissions': True,  # Todos los permisos
            },
            'Recepcionista': {
                'description': 'Gestión de reservas, check-in/out y habitaciones',
                'apps': ['core', 'rooms', 'reservations', 'payments', 'users'],
                'permissions': {
                    'core': ['view_hotel'],
                    'rooms': ['view_room', 'change_room'],  # Ver y cambiar estado de habitaciones
                    'reservations': ['view_reservation', 'add_reservation', 'change_reservation'],  # No puede eliminar
                    'payments': ['view_payment', 'add_payment', 'change_payment'],
                    'users': ['view_user'],  # Solo ver usuarios
                }
            },
            'Contador': {
                'description': 'Gestión de facturación y pagos',
                'apps': ['core', 'reservations', 'payments', 'invoicing'],
                'permissions': {
                    'core': ['view_hotel'],
                    'reservations': ['view_reservation'],  # Solo lectura
                    'payments': ['view_payment', 'add_payment', 'change_payment'],
                    'invoicing': ['view_invoice', 'add_invoice', 'change_invoice', 'delete_invoice'],
                }
            },
            'Solo Lectura': {
                'description': 'Solo puede ver información, no modificar',
                'apps': ['core', 'rooms', 'reservations', 'payments', 'rates'],
                'permissions': {
                    'core': ['view_hotel'],
                    'rooms': ['view_room'],
                    'reservations': ['view_reservation'],
                    'payments': ['view_payment'],
                    'rates': ['view_rateplan', 'view_raterule'],
                }
            },
        }
        
        created_groups = []
        
        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Grupo creado: {group_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Grupo ya existe: {group_name}'))
            
            # Limpiar permisos existentes del grupo (opcional, comentar si quieres mantener)
            # group.permissions.clear()
            
            permissions_added = 0
            
            # Si tiene todos los permisos
            if config.get('all_permissions'):
                apps = config.get('apps', [])
                for app_label in apps:
                    content_types = ContentType.objects.filter(app_label=app_label)
                    for ct in content_types:
                        perms = Permission.objects.filter(content_type=ct)
                        for perm in perms:
                            if perm not in group.permissions.all():
                                group.permissions.add(perm)
                                permissions_added += 1
            
            # Asignar permisos específicos
            else:
                permissions_config = config.get('permissions', {})
                for app_label, perm_codenames in permissions_config.items():
                    content_types = ContentType.objects.filter(app_label=app_label)
                    
                    for ct in content_types:
                        for codename in perm_codenames:
                            try:
                                # Buscar permiso por codename completo o parcial
                                perm = Permission.objects.filter(
                                    content_type=ct,
                                    codename__contains=codename
                                ).first()
                                
                                if perm and perm not in group.permissions.all():
                                    group.permissions.add(perm)
                                    permissions_added += 1
                            except Permission.DoesNotExist:
                                self.stdout.write(
                                    self.style.ERROR(f'  ⚠ Permiso no encontrado: {app_label}.{codename}')
                                )
            
            if permissions_added > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  → {permissions_added} permisos asignados')
                )
            
            created_groups.append({
                'name': group_name,
                'description': config.get('description', ''),
                'count': permissions_added
            })
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE GRUPOS CREADOS'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        for group_info in created_groups:
            group = Group.objects.get(name=group_info['name'])
            perm_count = group.permissions.count()
            self.stdout.write(
                f"{group_info['name']:20} | "
                f"Permisos: {perm_count:3} | "
                f"{group_info['description']}"
            )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Inicialización completada'))
        self.stdout.write(self.style.SUCCESS('\nPara asignar usuarios a grupos:'))
        self.stdout.write(self.style.SUCCESS('  python manage.py shell'))
        self.stdout.write(self.style.SUCCESS('  >>> from django.contrib.auth.models import User, Group'))
        self.stdout.write(self.style.SUCCESS('  >>> user = User.objects.get(username="usuario")'))
        self.stdout.write(self.style.SUCCESS('  >>> group = Group.objects.get(name="Recepcionista")'))
        self.stdout.write(self.style.SUCCESS('  >>> user.groups.add(group)'))

