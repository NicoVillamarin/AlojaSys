#!/usr/bin/env python3
"""
Script de configuración para Selenium en AlojaSys
Este script instala las dependencias necesarias y configura el entorno para testing automatizado
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Instalar las dependencias de Python necesarias"""
    print("🔧 Instalando dependencias de Python...")
    
    requirements = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1", 
        "pytest==7.4.3",
        "pytest-html==4.1.1",
        "pytest-xdist==3.3.1",
        "requests==2.31.0",
        "python-dotenv==1.0.0"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {package}: {e}")
            return False
    
    return True

def check_chrome():
    """Verificar que Chrome esté instalado"""
    print("🌐 Verificando instalación de Chrome...")
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome encontrado en: {path}")
            return True
    
    print("❌ Chrome no encontrado. Por favor instala Google Chrome desde https://www.google.com/chrome/")
    return False

def create_test_data():
    """Crear datos de prueba básicos"""
    print("📊 Creando datos de prueba...")
    
    # Este comando asume que Docker Compose está ejecutándose
    try:
        # Crear superusuario si no existe
        subprocess.run([
            "docker-compose", "exec", "-T", "backend", 
            "python", "manage.py", "shell", "-c",
            "from django.contrib.auth.models import User; "
            "u, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@test.com', 'is_superuser': True}); "
            "u.set_password('admin123'); u.save(); "
            "print('Superusuario configurado' if created else 'Superusuario ya existe')"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Datos de prueba creados")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando datos de prueba: {e}")
        print("💡 Asegúrate de que Docker Compose esté ejecutándose (docker-compose up -d)")
        return False

def run_test():
    """Ejecutar un test básico para verificar la configuración"""
    print("🧪 Ejecutando test de verificación...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow",
            "-v", "-s", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Test ejecutado exitosamente")
            return True
        else:
            print(f"❌ Test falló: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False

def main():
    """Función principal de configuración"""
    print("🚀 Configurando Selenium para AlojaSys")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("test_checkin_checkout_automated.py").exists():
        print("❌ Este script debe ejecutarse desde el directorio tests/")
        sys.exit(1)
    
    success = True
    
    # 1. Instalar dependencias
    if not install_requirements():
        success = False
    
    # 2. Verificar Chrome
    if not check_chrome():
        success = False
    
    # 3. Crear datos de prueba
    if not create_test_data():
        success = False
    
    if success:
        print("\n🎉 Configuración completada exitosamente!")
        print("\n📋 Para ejecutar los tests:")
        print("   python -m pytest test_checkin_checkout_automated.py -v -s")
        print("\n📋 Para ejecutar un test específico:")
        print("   python -m pytest test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow -v -s")
    else:
        print("\n❌ La configuración no se completó correctamente")
        print("💡 Revisa los errores anteriores y vuelve a intentar")
        sys.exit(1)

if __name__ == "__main__":
    main()
