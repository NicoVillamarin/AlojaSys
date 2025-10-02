from django.apps import AppConfig
import os
from django.db import connection
from django.contrib.auth import get_user_model

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Usuarios'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import apps.users.signals
        # Crear superusuario automáticamente si hay variables de entorno definidas
        # Útil en Render sin shell ni jobs pagos
        try:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            enabled = os.environ.get('AUTO_CREATE_SUPERUSER', 'true').lower() in {'1','true','yes'}

            if enabled and username and password:
                # Verificar que la tabla exista (evita fallar durante migraciones iniciales)
                tables = connection.introspection.table_names()
                if 'auth_user' in tables:
                    User = get_user_model()
                    if not User.objects.filter(username=username).exists():
                        User.objects.create_superuser(username=username, email=email or '', password=password)
        except Exception:
            # No interrumpir el arranque si falla; solo omitimos la creación
            pass