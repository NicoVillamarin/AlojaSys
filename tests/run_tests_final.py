"""
Script final para ejecutar tests automatizados de AlojaSys
"""
import subprocess
import sys
import os
from datetime import datetime

def print_header(title):
    """Imprimir encabezado"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def run_pytest_command(test_command, description):
    """Ejecutar comando de pytest"""
    print(f"\n{description}...")
    print("-" * 40)
    
    try:
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("EXITO - Test completado")
            if result.stdout:
                print("Salida:", result.stdout)
        else:
            print("ERROR - Test falló")
            if result.stderr:
                print("Error:", result.stderr)
            if result.stdout:
                print("Salida:", result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"EXCEPCION: {e}")
        return False

def main():
    """Función principal"""
    print_header("SISTEMA DE TESTING AUTOMATIZADO - ALOJASYS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("test_api.py"):
        print("ERROR - Ejecuta este script desde el directorio 'tests'")
        print("Comando: cd tests && python run_tests_final.py")
        return
    
    print("\nVERIFICANDO SISTEMA...")
    
    # 1. Test de API
    success_api = run_pytest_command(
        "python test_api.py",
        "1. Verificando servicios y API"
    )
    
    # 2. Test básico de Chrome
    success_chrome = run_pytest_command(
        "python -m pytest test_chrome_direct.py::test_chrome_direct -v",
        "2. Verificando Chrome básico"
    )
    
    # 3. Test de navegación a AlojaSys
    success_aloja = run_pytest_command(
        "python -m pytest test_chrome_direct.py::test_chrome_aloja -v",
        "3. Verificando navegación a AlojaSys"
    )
    
    # 4. Test de navegación automatizada
    success_nav = run_pytest_command(
        "python -m pytest test_checkin_checkout_automated.py::test_basic_navigation -v -s",
        "4. Test de navegación automatizada"
    )
    
    # Resumen
    print_header("RESUMEN DE TESTS")
    
    tests = [
        ("API y Servicios", success_api),
        ("Chrome Básico", success_chrome),
        ("Navegación a AlojaSys", success_aloja),
        ("Navegación Automatizada", success_nav)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "OK" if passed else "ERROR"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nFELICITACIONES! Todos los tests básicos pasaron")
        print("Tu sistema de testing automatizado está funcionando")
        
        print("\nPARA PROBAR CHECK-IN/CHECK-OUT AUTOMATIZADO:")
        print("Ejecuta: python -m pytest test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow -v -s")
        print("\nIMPORTANTE:")
        print("- Este test abrirá el navegador")
        print("- Necesitas tener credenciales válidas")
        print("- Necesitas tener reservas en estado 'confirmed'")
        
    else:
        print("\nAlgunos tests fallaron. Revisa los errores arriba.")
    
    print("\n" + "="*60)
    print(" TESTING COMPLETADO! ")
    print("="*60)

if __name__ == "__main__":
    main()
