from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = 'Crea perfiles (UserProfile) para usuarios que no lo tengan'

    def handle(self, *args, **options):
        self.stdout.write("=== CREANDO PERFILES FALTANTES ===\n")
        
        users_without_profile = []
        
        # Buscar todos los usuarios sin perfil
        for user in User.objects.all():
            try:
                # Intentar acceder al perfil
                _ = user.profile
            except UserProfile.DoesNotExist:
                # El usuario no tiene perfil, crearlo
                profile = UserProfile.objects.create(
                    user=user,
                    phone='',
                    position='Administrador' if user.is_superuser else '',
                    is_active=user.is_active
                )
                
                users_without_profile.append({
                    'username': user.username,
                    'email': user.email,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff
                })
                
                self.stdout.write(f"✅ Perfil creado para: {user.username}")
                if user.is_superuser:
                    self.stdout.write(f"   → Es superuser")
                if user.is_staff:
                    self.stdout.write(f"   → Es staff")
        
        if users_without_profile:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Se crearon {len(users_without_profile)} perfiles'))
            self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANTE:'))
            self.stdout.write(self.style.WARNING('   Los superusers/staff ahora aparecerán en el ABM de usuarios.'))
            self.stdout.write(self.style.WARNING('   Asigna hoteles a los usuarios que lo necesiten.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Todos los usuarios ya tienen perfil'))



