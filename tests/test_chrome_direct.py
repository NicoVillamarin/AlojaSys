"""
Test con Chrome usando la ruta directa del ejecutable
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def test_chrome_direct():
    """Test con Chrome usando ruta directa"""
    print("Iniciando test con Chrome directo...")
    
    # Configurar Chrome
    options = Options()
    options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Intentar usar Chrome desde ubicaciones comunes
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if chrome_path:
        options.binary_location = chrome_path
        print(f"Chrome encontrado en: {chrome_path}")
    else:
        print("Chrome no encontrado en ubicaciones estándar")
        print("Intentando sin especificar ruta...")
    
    # Usar ChromeDriverManager para el driver
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error con ChromeDriverManager: {e}")
        print("Intentando sin service...")
        driver = webdriver.Chrome(options=options)
    
    try:
        # Navegar a Google
        print("Navegando a Google...")
        driver.get("https://www.google.com")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        
        # Verificar que el elemento existe
        assert search_box is not None, "No se encontró el cuadro de búsqueda de Google"
        
        print("OK - Test básico con Chrome completado exitosamente")
        
    except Exception as e:
        print(f"Error en test básico: {e}")
        # Tomar screenshot para debugging
        try:
            driver.save_screenshot("screenshots/chrome_error.png")
            print("Screenshot guardado en screenshots/chrome_error.png")
        except:
            pass
        raise
    finally:
        driver.quit()

def test_chrome_aloja():
    """Test de conexión a AlojaSys con Chrome"""
    print("Iniciando test de AlojaSys con Chrome...")
    
    # Configurar Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Intentar usar Chrome desde ubicaciones comunes
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if chrome_path:
        options.binary_location = chrome_path
        print(f"Chrome encontrado en: {chrome_path}")
    
    # Usar ChromeDriverManager para el driver
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error con ChromeDriverManager: {e}")
        print("Intentando sin service...")
        driver = webdriver.Chrome(options=options)
    
    try:
        # Navegar al frontend de AlojaSys
        print("Navegando a AlojaSys...")
        driver.get("http://localhost:5173")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 10)
        
        # Buscar algún elemento de la página
        try:
            # Buscar el título de la página
            title = driver.title
            print(f"Título de la página: {title}")
            
            # Verificar que la página cargó
            assert len(title) > 0, "La página no cargó correctamente"
            
            print("OK - Conexión a AlojaSys exitosa con Chrome")
            
        except Exception as e:
            print(f"Error al verificar elementos de la página: {e}")
            # Tomar screenshot para debugging
            driver.save_screenshot("screenshots/chrome_aloja_error.png")
            print("Screenshot guardado en screenshots/chrome_aloja_error.png")
            raise
            
    except Exception as e:
        print(f"Error en test de AlojaSys: {e}")
        raise
    finally:
        driver.quit()
