"""
Test con Edge para verificar que Selenium funciona
"""
import pytest
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_edge_basic():
    """Test básico con Edge"""
    print("Iniciando test básico con Edge...")
    
    # Configurar Edge
    options = Options()
    options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    
    try:
        # Navegar a Google
        driver.get("https://www.google.com")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        
        # Verificar que el elemento existe
        assert search_box is not None, "No se encontró el cuadro de búsqueda de Google"
        
        print("OK - Test básico con Edge completado exitosamente")
        
    except Exception as e:
        print(f"Error en test básico: {e}")
        raise
    finally:
        driver.quit()

def test_edge_aloja():
    """Test de conexión a AlojaSys con Edge"""
    print("Iniciando test de AlojaSys con Edge...")
    
    # Configurar Edge
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    
    try:
        # Navegar al frontend de AlojaSys
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
            
            print("OK - Conexión a AlojaSys exitosa con Edge")
            
        except Exception as e:
            print(f"Error al verificar elementos de la página: {e}")
            # Tomar screenshot para debugging
            driver.save_screenshot("screenshots/edge_error.png")
            raise
            
    except Exception as e:
        print(f"Error en test de AlojaSys: {e}")
        raise
    finally:
        driver.quit()
