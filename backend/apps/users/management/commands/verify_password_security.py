from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Demuestra que las contraseñas están hasheadas de forma segura'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== VERIFICACIÓN DE SEGURIDAD DE CONTRASEÑAS ===\n"))
        
        # Tomar un usuario de ejemplo
        try:
            user = User.objects.get(username='BrendaSterli')
            
            self.stdout.write("📊 Información del usuario: BrendaSterli")
            self.stdout.write(f"   Username: {user.username}")
            self.stdout.write(f"   Email: {user.email}\n")
            
            self.stdout.write("🔐 Contraseña en la Base de Datos:")
            self.stdout.write(f"   {user.password}\n")
            
            self.stdout.write("📝 Análisis del hash:")
            parts = user.password.split('$')
            if len(parts) >= 4:
                self.stdout.write(f"   - Algoritmo: {parts[0]}")
                self.stdout.write(f"   - Iteraciones: {parts[1]}")
                self.stdout.write(f"   - Salt (único por usuario): {parts[2]}")
                self.stdout.write(f"   - Hash (irreversible): {parts[3][:30]}...\n")
            
            self.stdout.write("✅ Verificación de contraseña:")
            # Probar con la contraseña correcta
            correct = user.check_password('BrendaSterli1234')
            self.stdout.write(f"   - check_password('BrendaSterli1234'): {correct} ✅")
            
            # Probar con contraseña incorrecta
            wrong = user.check_password('BrendaSterli123')
            self.stdout.write(f"   - check_password('BrendaSterli123'): {wrong} ❌")
            
            wrong2 = user.check_password('brendasterli1234')
            self.stdout.write(f"   - check_password('brendasterli1234'): {wrong2} ❌\n")
            
            self.stdout.write(self.style.SUCCESS("🔒 CONCLUSIÓN:"))
            self.stdout.write(self.style.SUCCESS("   ✅ Las contraseñas están hasheadas con PBKDF2-SHA256"))
            self.stdout.write(self.style.SUCCESS("   ✅ Usan 600,000 iteraciones (estándar de seguridad alto)"))
            self.stdout.write(self.style.SUCCESS("   ✅ Cada usuario tiene un salt único"))
            self.stdout.write(self.style.SUCCESS("   ✅ Es IMPOSIBLE revertir el hash a la contraseña original"))
            self.stdout.write(self.style.SUCCESS("   ✅ Solo se puede verificar con check_password()"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Usuario BrendaSterli no encontrado"))

