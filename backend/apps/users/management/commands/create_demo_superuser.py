from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea o actualiza un superuser para demo (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
            help='Username del superuser'
        )
        parser.add_argument(
            '--email',
            type=str,
            default=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@alojasys.com'),
            help='Email del superuser'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.getenv('DJANGO_SUPERUSER_PASSWORD', None),
            help='Password del superuser (si no se proporciona, se pedirá interactivamente)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Si no hay password y no estamos en modo interactivo, usar un default seguro
        if not password:
            password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Admin123!@#')

        try:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if not created:
                # Usuario ya existe, actualizar permisos y password
                user.is_staff = True
                user.is_superuser = True
                user.email = email
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser "{username}" actualizado correctamente')
                )
            else:
                # Usuario nuevo, establecer password
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser "{username}" creado correctamente')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear/actualizar superuser: {str(e)}')
            )

