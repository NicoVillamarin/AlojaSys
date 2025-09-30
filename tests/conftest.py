"""
Configuración global de pytest y fixtures comunes
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import requests
from config import TestConfig

@pytest.fixture(scope="session")
def driver():
    """Fixture para crear y configurar el driver de Selenium"""
    config = TestConfig()
    
    if config.BROWSER.lower() == "chrome":
        options = Options()
        if config.HEADLESS:
            options.add_argument("--headless")
        options.add_argument(f"--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
    elif config.BROWSER.lower() == "firefox":
        options = FirefoxOptions()
        if config.HEADLESS:
            options.add_argument("--headless")
        options.add_argument(f"--width={config.WINDOW_SIZE[0]}")
        options.add_argument(f"--height={config.WINDOW_SIZE[1]}")
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        
    else:
        raise ValueError(f"Browser {config.BROWSER} no soportado")
    
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    driver.maximize_window()
    
    yield driver
    
    driver.quit()

@pytest.fixture(scope="session")
def wait(driver):
    """Fixture para WebDriverWait"""
    return WebDriverWait(driver, TestConfig.EXPLICIT_WAIT)

@pytest.fixture(scope="session")
def backend_available():
    """Verificar que el backend esté disponible"""
    try:
        response = requests.get(f"{TestConfig.BACKEND_URL}/api/", timeout=5)
        return response.status_code == 200
    except:
        return False

@pytest.fixture(scope="session")
def frontend_available():
    """Verificar que el frontend esté disponible"""
    try:
        response = requests.get(TestConfig.FRONTEND_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

@pytest.fixture(scope="function")
def login(driver, wait, backend_available, frontend_available):
    """Fixture para hacer login en la aplicación"""
    if not backend_available or not frontend_available:
        pytest.skip("Backend o Frontend no disponible")
    
    config = TestConfig()
    driver.get(config.FRONTEND_URL)
    
    # Esperar a que cargue la página de login
    try:
        # Buscar campos de login (ajustar según tu implementación)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.clear()
        username_field.send_keys(config.TEST_USERNAME)
        
        password_field.clear()
        password_field.send_keys(config.TEST_PASSWORD)
        
        # Hacer click en el botón de login
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Esperar a que se complete el login
        wait.until(EC.url_contains("dashboard") or EC.presence_of_element_located((By.CLASS_NAME, "dashboard")))
        
        return True
        
    except Exception as e:
        print(f"Error en login: {e}")
        return False

@pytest.fixture(scope="function")
def test_data():
    """Fixture con datos de prueba"""
    return TestConfig.TEST_RESERVATIONS
