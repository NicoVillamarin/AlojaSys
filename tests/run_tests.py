"""
Script principal para ejecutar todos los tests de AlojaSys
"""
import os
import sys
import subprocess
import logging
from datetime import datetime

def setup_logging():
    """Configurar logging para los tests"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/test_run_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    logger = logging.getLogger(__name__)
    
    try:
        import selenium
        import pytest
        logger.info("OK - Dependencias de testing encontradas")
        return True
    except ImportError as e:
        logger.error(f"ERROR - Dependencias faltantes: {e}")
        logger.info("Ejecuta: pip install -r tests/requirements.txt")
        return False

def check_services():
    """Verificar que los servicios estén ejecutándose"""
    logger = logging.getLogger(__name__)
    
    import requests
    from config import TestConfig
    
    # Verificar backend
    try:
        response = requests.get(f"{TestConfig.BACKEND_URL}/api/", timeout=5)
        if response.status_code == 200:
            logger.info("OK - Backend disponible")
        else:
            logger.warning(f"WARNING - Backend responde con código: {response.status_code}")
    except Exception as e:
        logger.error(f"ERROR - Backend no disponible: {e}")
        return False
    
    # Verificar frontend
    try:
        response = requests.get(TestConfig.FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            logger.info("OK - Frontend disponible")
        else:
            logger.warning(f"WARNING - Frontend responde con código: {response.status_code}")
    except Exception as e:
        logger.error(f"ERROR - Frontend no disponible: {e}")
        return False
    
    return True

def run_tests(test_type="all", browser="chrome", headless=False, verbose=False):
    """Ejecutar los tests"""
    logger = logging.getLogger(__name__)
    
    # Configurar variables de entorno para pytest
    os.environ["BROWSER"] = browser
    os.environ["HEADLESS"] = str(headless).lower()
    
    # Construir comando de pytest
    cmd = ["python", "-m", "pytest"]
    
    if test_type == "checkin":
        cmd.append("test_checkin.py")
    elif test_type == "checkout":
        cmd.append("test_checkout.py")
    elif test_type == "all":
        cmd.append("test_*.py")
    else:
        logger.error(f"Tipo de test inválido: {test_type}")
        return False
    
    if verbose:
        cmd.append("-v")
    
    # Agregar opciones adicionales
    cmd.extend([
        "--tb=short",  # Formato corto de traceback
        "--html=reports/report.html",  # Reporte HTML
        "--self-contained-html",  # HTML autocontenido
        "-x",  # Parar en el primer fallo
    ])
    
    # Crear directorio de reportes
    os.makedirs("reports", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    
    logger.info(f"Ejecutando comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd="tests", capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✓ Todos los tests pasaron exitosamente")
        else:
            logger.error("✗ Algunos tests fallaron")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error ejecutando tests: {e}")
        return False

def main():
    """Función principal"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("INICIANDO TESTS AUTOMATIZADOS DE ALOJASYS")
    logger.info("=" * 60)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar servicios
    if not check_services():
        logger.warning("Servicios no disponibles, pero continuando...")
    
    # Obtener parámetros de línea de comandos
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    browser = sys.argv[2] if len(sys.argv) > 2 else "chrome"
    headless = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    logger.info(f"Configuración:")
    logger.info(f"  - Tipo de test: {test_type}")
    logger.info(f"  - Navegador: {browser}")
    logger.info(f"  - Modo headless: {headless}")
    logger.info("")
    
    # Ejecutar tests
    success = run_tests(test_type, browser, headless, verbose=True)
    
    if success:
        logger.info("SUCCESS - TESTS COMPLETADOS EXITOSAMENTE")
    else:
        logger.error("ERROR - TESTS FALLARON")
        sys.exit(1)

if __name__ == "__main__":
    main()
