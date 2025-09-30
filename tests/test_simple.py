"""
Test simple para verificar que Selenium funciona
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_selenium_basic():
    """Test básico para verificar que Selenium funciona"""
    print("Iniciando test básico de Selenium...")
    
    # Configurar Chrome
    options = Options()
    options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Navegar a Google
        driver.get("https://www.google.com")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        
        # Verificar que el elemento existe
        assert search_box is not None, "No se encontró el cuadro de búsqueda de Google"
        
        print("✓ Test básico de Selenium completado exitosamente")
        
    except Exception as e:
        print(f"Error en test básico: {e}")
        raise
    finally:
        driver.quit()

def test_frontend_connection():
    """Test para verificar conexión al frontend de AlojaSys"""
    print("Iniciando test de conexión al frontend...")
    
    # Configurar Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Navegar al frontend de AlojaSys
        driver.get("http://localhost:5173")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 10)
        
        # Buscar algún elemento de la página
        try:
            # Buscar el título de la página o algún elemento característico
            title = driver.title
            print(f"Título de la página: {title}")
            
            # Verificar que la página cargó
            assert "AlojaSys" in title or len(title) > 0, "La página no cargó correctamente"
            
            print("✓ Conexión al frontend exitosa")
            
        except Exception as e:
            print(f"Error al verificar elementos de la página: {e}")
            # Tomar screenshot para debugging
            driver.save_screenshot("screenshots/frontend_error.png")
            raise
            
    except Exception as e:
        print(f"Error en test de frontend: {e}")
        raise
    finally:
        driver.quit()
