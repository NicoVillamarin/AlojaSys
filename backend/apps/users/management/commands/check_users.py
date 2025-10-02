from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = 'Verificar estado de usuarios creados desde el ABM'

    def handle(self, *args, **options):
        self.stdout.write("=== VERIFICANDO USUARIOS ===\n")
        
        users = User.objects.all().order_by('-id')[:5]  # Últimos 5 usuarios
        
        for u in users:
            self.stdout.write(f"\n👤 Usuario: {u.username}")
            self.stdout.write(f"   Email: {u.email}")
            self.stdout.write(f"   is_active: {u.is_active}")
            self.stdout.write(f"   is_staff: {u.is_staff}")
            self.stdout.write(f"   Password hash: {u.password[:30]}...")
            
            # Verificar si tiene perfil
            try:
                profile = u.profile
                self.stdout.write(f"   ✅ Tiene perfil:")
                self.stdout.write(f"      - is_active: {profile.is_active}")
                self.stdout.write(f"      - position: {profile.position or 'N/A'}")
                hotels = list(profile.hotels.all())
                self.stdout.write(f"      - hoteles: {[h.name for h in hotels]}")
            except UserProfile.DoesNotExist:
                self.stdout.write(f"   ❌ NO tiene perfil")
            
            # Probar contraseñas comunes de testing
            test_passwords = ['Test1234', 'test1234', f'{u.username}1234']
            self.stdout.write(f"   Probando contraseñas:")
            for pwd in test_passwords:
                result = u.check_password(pwd)
                icon = "✅" if result else "❌"
                self.stdout.write(f"      {icon} '{pwd}': {result}")
        
        self.stdout.write(self.style.SUCCESS('\n✅ Verificación completada'))

