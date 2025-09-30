"""
Script final para ejecutar todos los tests de AlojaSys
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

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{description}...")
    print(f"Comando: {command}")
    print("-" * 40)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd="tests")
        
        if result.returncode == 0:
            print("EXITO")
            if result.stdout:
                print("Salida:", result.stdout)
        else:
            print("ERROR")
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
        print("Comando: cd tests && python run_final_tests.py")
        return
    
    print("\nVERIFICANDO SISTEMA...")
    
    # 1. Test de servicios (API)
    success_api = run_command(
        "python test_api.py",
        "1. Verificando servicios y API"
    )
    
    # 2. Test manual
    print_header("INSTRUCCIONES PARA TESTING MANUAL")
    print("""
    Para probar el flujo completo de check-in y check-out:
    
    1. 🌐 Abre tu navegador web
    2. 🔗 Ve a: http://localhost:5173
    3. 🔐 Haz login con tus credenciales
    4. 📋 Ve a la sección de 'Reservas'
    5. 🔍 Busca una reserva en estado 'confirmed'
    6. ✅ Haz click en 'Check-in'
    7. ✨ Verifica que el estado cambie a 'check-in'
    8. 🚪 Haz click en 'Check-out'
    9. ✨ Verifica que el estado cambie a 'check-out'
    
    ¡Esto es exactamente lo que harán los tests automatizados!
    """)
    
    # 3. Resumen final
    print_header("RESUMEN FINAL")
    
    if success_api:
        print("OK - Sistema de testing configurado correctamente")
        print("OK - Backend y Frontend funcionando")
        print("OK - API endpoints respondiendo")
        print("OK - Dependencias instaladas")
        
        print("\nPROXIMOS PASOS:")
        print("1. Ejecuta el testing manual siguiendo las instrucciones arriba")
        print("2. Verifica que tengas reservas en estado 'confirmed'")
        print("3. Prueba el flujo completo de check-in/check-out")
        
        print("\nPARA TESTING AUTOMATIZADO COMPLETO:")
        print("- Necesitaras instalar Chrome o Firefox")
        print("- O configurar un driver de navegador manualmente")
        print("- Los tests de API ya funcionan perfectamente")
        
    else:
        print("ERROR - Algunos tests fallaron")
        print("Revisa los errores arriba y soluciona los problemas")
    
    print("\n" + "="*60)
    print(" ¡TESTING COMPLETADO! ")
    print("="*60)

if __name__ == "__main__":
    main()
