from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Establece contraseñas temporales para usuarios con contraseñas inutilizables'

    def handle(self, *args, **options):
        self.stdout.write("=== ARREGLANDO USUARIOS CON CONTRASEÑAS INUTILIZABLES ===\n")
        
        users_fixed = []
        
        # Buscar usuarios con contraseñas inutilizables (empiezan con !)
        for user in User.objects.all():
            if user.password.startswith('!'):
                # Establecer contraseña temporal: <username>1234
                temp_password = f"{user.username}1234"
                user.set_password(temp_password)
                user.save()
                
                users_fixed.append({
                    'username': user.username,
                    'temp_password': temp_password
                })
                
                self.stdout.write(f"✅ Usuario: {user.username}")
                self.stdout.write(f"   Contraseña temporal: {temp_password}\n")
        
        if users_fixed:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Se arreglaron {len(users_fixed)} usuarios'))
            self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANTE: Anota las contraseñas temporales:'))
            for user_info in users_fixed:
                self.stdout.write(f"   - {user_info['username']}: {user_info['temp_password']}")
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ No hay usuarios para arreglar'))

