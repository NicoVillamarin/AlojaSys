"""
Script para configurar el entorno de testing
"""
import os
import sys
import subprocess
import logging

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def install_dependencies():
    """Instalar dependencias de Python"""
    logger = logging.getLogger(__name__)
    
    logger.info("Instalando dependencias de Python...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, cwd="tests")
        logger.info("✓ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Error instalando dependencias: {e}")
        return False

def create_directories():
    """Crear directorios necesarios"""
    logger = logging.getLogger(__name__)
    
    directories = [
        "logs",
        "reports", 
        "screenshots",
        "test_data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"✓ Directorio creado: {directory}")

def create_env_file():
    """Crear archivo .env si no existe"""
    logger = logging.getLogger(__name__)
    
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write("""# Configuración de testing
TEST_USERNAME=admin@test.com
TEST_PASSWORD=admin123
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
""")
        logger.info("✓ Archivo .env creado")
    else:
        logger.info("✓ Archivo .env ya existe")

def check_selenium_drivers():
    """Verificar drivers de Selenium"""
    logger = logging.getLogger(__name__)
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.firefox import GeckoDriverManager
        
        # Descargar drivers
        logger.info("Descargando drivers de Selenium...")
        ChromeDriverManager().install()
        GeckoDriverManager().install()
        
        logger.info("✓ Drivers de Selenium configurados")
        return True
    except Exception as e:
        logger.error(f"✗ Error configurando drivers: {e}")
        return False

def create_test_data():
    """Crear datos de prueba"""
    logger = logging.getLogger(__name__)
    
    # Este script se ejecutaría para crear datos de prueba en la base de datos
    # Por ahora solo creamos un archivo de ejemplo
    test_data_file = "test_data/sample_reservations.json"
    
    import json
    
    sample_data = {
        "reservations": [
            {
                "hotel_id": 1,
                "room_id": 1,
                "guest_name": "Juan Pérez",
                "guest_email": "juan@test.com",
                "check_in": "2024-01-15",
                "check_out": "2024-01-17",
                "guests": 2,
                "status": "confirmed"
            },
            {
                "hotel_id": 2,
                "room_id": 2,
                "guest_name": "María García", 
                "guest_email": "maria@test.com",
                "check_in": "2024-01-16",
                "check_out": "2024-01-18",
                "guests": 1,
                "status": "confirmed"
            }
        ]
    }
    
    with open(test_data_file, "w") as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info("✓ Datos de prueba creados")

def main():
    """Función principal de configuración"""
    logger = setup_logging()
    
    logger.info("=" * 50)
    logger.info("CONFIGURANDO ENTORNO DE TESTING")
    logger.info("=" * 50)
    
    # Crear directorios
    create_directories()
    
    # Crear archivo .env
    create_env_file()
    
    # Instalar dependencias
    if not install_dependencies():
        logger.error("Error en la instalación de dependencias")
        sys.exit(1)
    
    # Configurar drivers de Selenium
    if not check_selenium_drivers():
        logger.error("Error configurando drivers de Selenium")
        sys.exit(1)
    
    # Crear datos de prueba
    create_test_data()
    
    logger.info("=" * 50)
    logger.info("CONFIGURACIÓN COMPLETADA")
    logger.info("=" * 50)
    logger.info("Para ejecutar los tests:")
    logger.info("  python run_tests.py")
    logger.info("  python run_tests.py checkin")
    logger.info("  python run_tests.py checkout")
    logger.info("  python run_tests.py all chrome true  # headless")

if __name__ == "__main__":
    main()
