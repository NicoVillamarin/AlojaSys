#!/usr/bin/env python3
"""
Script maestro para configurar todos los datos de prueba
Ejecuta la creación de habitaciones y reservas para testing automatizado
"""

import subprocess
import sys
import os
from pathlib import Path

def run_script(script_name, description):
    """Ejecutar un script y mostrar el resultado"""
    print(f"\n{'='*60}")
    print(f"[SETUP] {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"[SUCCESS] {description} completado exitosamente")
            return True
        else:
            print(f"[ERROR] {description} falló con código {result.returncode}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error ejecutando {script_name}: {e}")
        return False

def check_backend():
    """Verificar que el backend esté funcionando"""
    print("[CHECK] Verificando conexión al backend...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/api/hotels/")
        if response.status_code == 401:  # 401 es esperado sin token
            print("[OK] Backend funcionando correctamente")
            return True
        else:
            print("[WARNING] Backend responde pero con código inesperado")
            return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] No se puede conectar al backend")
        print("[TIP] Asegúrate de ejecutar: docker-compose up -d")
        return False
    except ImportError:
        print("[ERROR] requests no está instalado")
        print("[TIP] Ejecuta: pip install requests")
        return False

def main():
    """Función principal de configuración"""
    print("[MASTER] Script maestro de configuración de datos de prueba")
    print("=" * 60)
    print("Este script configurará todos los datos necesarios para testing automatizado")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("create_test_rooms.py").exists():
        print("[ERROR] Este script debe ejecutarse desde el directorio tests/")
        sys.exit(1)
    
    # Verificar backend
    if not check_backend():
        print("\n[ERROR] El backend no está funcionando")
        print("[TIP] Ejecuta: docker-compose up -d")
        sys.exit(1)
    
    success_count = 0
    total_scripts = 3
    
    # 1. Verificar hoteles existentes
    if run_script("check_hotels.py", "Verificando hoteles existentes"):
        success_count += 1
    
    # 2. Crear habitaciones de prueba
    if run_script("create_test_rooms.py", "Creando 40 habitaciones de prueba"):
        success_count += 1
    
    # 3. Crear reservas de prueba
    if run_script("create_test_reservations.py", "Creando reservas de prueba"):
        success_count += 1
    
    # Resumen final
    print(f"\n{'='*60}")
    print("[RESUMEN FINAL] CONFIGURACIÓN DE DATOS DE PRUEBA")
    print(f"{'='*60}")
    print(f"[STATS] Scripts ejecutados exitosamente: {success_count}/{total_scripts}")
    
    if success_count == total_scripts:
        print("\n[SUCCESS] ¡Configuración completada exitosamente!")
        print("[TEST] Los datos están listos para testing automatizado")
        print("\n[INFO] Datos creados:")
        print("  - 40 habitaciones en Hotel Test (ID: 35)")
        print("  - ~17 reservas de prueba")
        print("  - Archivos de datos en test_data/")
        
        print("\n[COMMANDS] Para ejecutar tests:")
        print("  python -m pytest test_checkin_checkout_automated.py -v -s")
        print("  python -m pytest test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow -v -s")
        
    else:
        print(f"\n[WARNING] Solo {success_count}/{total_scripts} scripts se completaron exitosamente")
        print("[TIP] Revisa los errores anteriores y vuelve a intentar")
    
    return success_count == total_scripts

if __name__ == "__main__":
    main()
