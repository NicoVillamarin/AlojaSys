"""
Script para ejecutar todos los tests automatizados de AlojaSys
"""
import subprocess
import sys
import os
from datetime import datetime

def print_header(title):
    """Imprimir encabezado"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def run_test(test_name, description, headless=True):
    """Ejecutar un test específico"""
    print(f"\n{description}...")
    print("-" * 50)
    
    # Configurar comando
    cmd = ["python", "-m", "pytest", test_name, "-v", "-s"]
    
    if headless:
        cmd.append("--headless")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="tests")
        
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
    print_header("SISTEMA DE TESTING AUTOMATIZADO COMPLETO - ALOJASYS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("test_api.py"):
        print("ERROR - Ejecuta este script desde el directorio 'tests'")
        print("Comando: cd tests && python run_automated_tests.py")
        return
    
    print("\nVERIFICANDO SISTEMA...")
    
    # 1. Test de API
    success_api = run_test(
        "test_api.py",
        "1. Verificando servicios y API",
        headless=True
    )
    
    # 2. Test básico de Chrome
    success_chrome = run_test(
        "test_chrome_direct.py::test_chrome_direct",
        "2. Verificando Chrome básico",
        headless=True
    )
    
    # 3. Test de navegación a AlojaSys
    success_navigation = run_test(
        "test_chrome_direct.py::test_chrome_aloja",
        "3. Verificando navegación a AlojaSys",
        headless=True
    )
    
    # 4. Test básico de navegación automatizada
    success_auto_nav = run_test(
        "test_checkin_checkout_automated.py::test_basic_navigation",
        "4. Test de navegación automatizada",
        headless=False  # Mostrar navegador para debugging
    )
    
    # 5. Test completo de check-in/check-out (solo si todo lo anterior funciona)
    if success_api and success_chrome and success_navigation and success_auto_nav:
        print("\n" + "="*70)
        print(" INICIANDO TEST COMPLETO DE CHECK-IN/CHECK-OUT")
        print("="*70)
        print("IMPORTANTE: Este test abrirá el navegador para que puedas ver el proceso")
        print("El test intentará hacer login y probar el flujo completo")
        print("Si no tienes credenciales válidas, el test fallará en el login")
        print("="*70)
        
        input("Presiona Enter para continuar con el test completo...")
        
        success_full = run_test(
            "test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow",
            "5. Test completo de check-in/check-out",
            headless=False
        )
    else:
        print("\nSaltando test completo debido a errores previos")
        success_full = False
    
    # Resumen final
    print_header("RESUMEN FINAL")
    
    tests = [
        ("API y Servicios", success_api),
        ("Chrome Básico", success_chrome),
        ("Navegación a AlojaSys", success_navigation),
        ("Navegación Automatizada", success_auto_nav),
        ("Test Completo", success_full if 'success_full' in locals() else False)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "OK" if passed else "ERROR"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nFELICITACIONES! Todos los tests pasaron exitosamente")
        print("Tu sistema de testing automatizado está funcionando perfectamente")
        
        print("\nPROXIMOS PASOS:")
        print("1. Asegúrate de tener reservas en estado 'confirmed' en tu sistema")
        print("2. Verifica que las credenciales de login sean correctas")
        print("3. Ejecuta regularmente: python run_automated_tests.py")
        
    else:
        print("\nAlgunos tests fallaron. Revisa los errores arriba.")
        print("Los tests de API deberían funcionar siempre.")
        print("Los tests de navegador pueden fallar si:")
        print("- No tienes Chrome instalado correctamente")
        print("- El frontend no está ejecutándose")
        print("- Las credenciales de login son incorrectas")
    
    print("\n" + "="*70)
    print(" TESTING AUTOMATIZADO COMPLETADO! ")
    print("="*70)

if __name__ == "__main__":
    main()
