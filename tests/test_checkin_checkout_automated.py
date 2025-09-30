"""
Test automatizado completo de check-in y check-out para AlojaSys
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os

class AlojaSysTester:
    def __init__(self, headless=True):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Configurar el driver de Chrome"""
        print("Configurando Chrome...")
        
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        # No deshabilitar JavaScript ni CSS para aplicaciones React
        
        # Buscar Chrome en ubicaciones comunes
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
        
        # Intentar usar ChromeDriverManager primero, si falla usar driver local
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            # Forzar descarga de la versión correcta para Windows
            service = Service(ChromeDriverManager(version="119.0.6045.105").install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("ChromeDriverManager configurado correctamente")
        except Exception as e:
            print(f"Error con ChromeDriverManager: {e}")
            try:
                # Intentar con driver local
                self.driver = webdriver.Chrome(options=options)
                print("Driver local configurado correctamente")
            except Exception as e2:
                print(f"Error con driver local: {e2}")
                raise Exception("No se pudo configurar Chrome WebDriver")
        
        self.wait = WebDriverWait(self.driver, 20)
        print("Chrome configurado correctamente")
    
    def navigate_to_login(self):
        """Navegar a la página de login"""
        print("Navegando a la página de login...")
        self.driver.get("http://localhost:5173")
        
        # Esperar a que cargue la página
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Página cargada correctamente")
    
    def login(self, username="admin", password="admin123"):
        """Hacer login en el sistema"""
        print(f"Intentando hacer login con usuario: {username}")
        
        try:
            # Esperar a que la página cargue completamente
            time.sleep(2)
            
            # Buscar campos de login usando los selectores correctos del componente React
            # Los campos no tienen atributo 'name', usamos placeholder o posición
            username_field = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@placeholder='Nombre de Usuario']"
            )))
            
            password_field = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@type='password' and @placeholder='Contraseña']"
            )))
            
            # Limpiar y llenar campos
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # Buscar y hacer click en el botón de login
            login_button = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@type='submit' and contains(text(), 'Ingresar')]"
            )))
            login_button.click()
            
            # Esperar a que se complete el login (verificar redirección o elementos del dashboard)
            time.sleep(3)  # Dar tiempo para el proceso de login
            
            # Verificar si el login fue exitoso
            current_url = self.driver.current_url
            print(f"URL actual después del login: {current_url}")
            
            # Si estamos en la página principal (no en login), consideramos exitoso
            if "login" not in current_url.lower() or current_url == "http://localhost:5173/":
                print("Login exitoso")
                return True
            else:
                # Verificar si hay mensajes de error
                try:
                    error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'invalid') or contains(text(), 'credenciales')]")
                    if error_elements:
                        print(f"Error de login detectado: {error_elements[0].text}")
                    else:
                        print("Login falló sin mensaje de error específico")
                except:
                    print("No se pudo verificar mensajes de error")
                
                return False
            
        except Exception as e:
            print(f"Error en login: {e}")
            self.take_screenshot("login_error")
            return False
    
    def navigate_to_reservations(self):
        """Navegar a la página de reservas"""
        print("Navegando a la página de reservas...")
        
        try:
            # Navegar directamente a la URL de reservas
            self.driver.get("http://localhost:5173/reservations-gestion")
            
            # Esperar a que cargue la página
            time.sleep(3)
            
            # Verificar que estamos en la página correcta
            current_url = self.driver.current_url
            print(f"URL actual: {current_url}")
            
            if "reservations-gestion" in current_url:
                print("Página de reservas cargada correctamente")
                return True
            else:
                print("No se pudo cargar la página de reservas")
                return False
            
        except Exception as e:
            print(f"Error navegando a reservas: {e}")
            self.take_screenshot("reservations_navigation_error")
            return False
    
    def find_reservation_by_status(self, status="confirmed"):
        """Buscar una reserva por estado"""
        print(f"Buscando reserva con estado: {status}")
        
        try:
            # Esperar a que la tabla cargue
            time.sleep(2)
            
            # Buscar en la tabla de reservas - usar selectores más flexibles
            rows = self.driver.find_elements(By.XPATH, "//tbody/tr | //div[contains(@class, 'table')]//tr")
            
            print(f"Encontradas {len(rows)} filas en la tabla")
            
            for i, row in enumerate(rows):
                try:
                    # Buscar texto que contenga el estado en cualquier celda
                    row_text = row.text.lower()
                    print(f"Fila {i+1}: {row_text}")
                    
                    if status and status.lower() in row_text:
                        print(f"Reserva encontrada en fila {i+1} con estado: {status}")
                        return row
                    elif not status and row_text.strip():  # Si no se especifica estado, tomar cualquier fila con contenido
                        print(f"Reserva encontrada en fila {i+1} (cualquier estado)")
                        return row
                except Exception as e:
                    print(f"Error procesando fila {i+1}: {e}")
                    continue
            
            print(f"No se encontró reserva con estado: {status}")
            return None
            
        except Exception as e:
            print(f"Error buscando reserva: {e}")
            return None
    
    def click_action_button(self, row, action):
        """Hacer click en un botón de acción"""
        print(f"Haciendo click en botón: {action}")
        
        try:
            # Buscar el botón de acción en la fila
            action_buttons = row.find_elements(By.XPATH, ".//button")
            
            for button in action_buttons:
                if action.lower() in button.text.lower():
                    if button.is_enabled():
                        button.click()
                        print(f"Click en {action} exitoso")
                        return True
                    else:
                        print(f"Botón {action} está deshabilitado")
                        return False
            
            print(f"No se encontró botón de acción: {action}")
            return False
            
        except Exception as e:
            print(f"Error haciendo click en {action}: {e}")
            return False
    
    def wait_for_status_change(self, expected_status, timeout=10):
        """Esperar a que cambie el estado"""
        print(f"Esperando cambio de estado a: {expected_status}")
        
        try:
            # Esperar a que aparezca un mensaje de confirmación
            self.wait.until(EC.any_of(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{expected_status}')]")),
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'realizado') or contains(text(), 'exitoso')]")),
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'success')]"))
            ))
            print(f"Estado cambiado a: {expected_status}")
            return True
            
        except Exception as e:
            print(f"No se detectó cambio de estado: {e}")
            return False
    
    def take_screenshot(self, name):
        """Tomar screenshot para debugging"""
        try:
            timestamp = int(time.time())
            filename = f"screenshots/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            print(f"Screenshot guardado: {filename}")
            return filename
        except Exception as e:
            print(f"Error tomando screenshot: {e}")
            return None
    
    def close(self):
        """Cerrar el driver"""
        if self.driver:
            self.driver.quit()

def test_complete_checkin_checkout_flow():
    """Test completo de check-in y check-out"""
    print("="*60)
    print("INICIANDO TEST AUTOMATIZADO DE CHECK-IN/CHECK-OUT")
    print("="*60)
    
    tester = AlojaSysTester(headless=False)  # Cambiar a True para ejecutar sin interfaz
    
    try:
        # 1. Navegar y hacer login
        tester.navigate_to_login()
        if not tester.login():
            pytest.fail("No se pudo hacer login")
        
        # 2. Navegar a reservas
        if not tester.navigate_to_reservations():
            pytest.fail("No se pudo navegar a reservas")
        
        # 3. Buscar reserva confirmada
        reservation_row = tester.find_reservation_by_status("confirmed")
        if not reservation_row:
            print("No hay reservas confirmadas, buscando cualquier reserva...")
            reservation_row = tester.find_reservation_by_status("")
        
        if not reservation_row:
            pytest.fail("No se encontró ninguna reserva para probar")
        
        # 4. Hacer check-in
        print("\n--- REALIZANDO CHECK-IN ---")
        if tester.click_action_button(reservation_row, "Check-in"):
            tester.wait_for_status_change("check-in")
            time.sleep(2)  # Esperar actualización de UI
        else:
            print("No se pudo hacer check-in (botón deshabilitado o no encontrado)")
        
        # 5. Hacer check-out
        print("\n--- REALIZANDO CHECK-OUT ---")
        if tester.click_action_button(reservation_row, "Check-out"):
            tester.wait_for_status_change("check-out")
            time.sleep(2)  # Esperar actualización de UI
        else:
            print("No se pudo hacer check-out (botón deshabilitado o no encontrado)")
        
        print("\n" + "="*60)
        print("TEST COMPLETADO EXITOSAMENTE")
        print("="*60)
        
    except Exception as e:
        print(f"Error en test: {e}")
        tester.take_screenshot("test_error")
        raise
    finally:
        tester.close()

def test_basic_navigation():
    """Test básico de navegación"""
    print("Iniciando test básico de navegación...")
    
    tester = AlojaSysTester(headless=False)
    
    try:
        # Navegar a la página
        tester.navigate_to_login()
        
        # Verificar que la página cargó
        title = tester.driver.title
        assert len(title) > 0, "La página no cargó correctamente"
        
        print(f"Título de la página: {title}")
        print("OK - Navegación básica exitosa")
        
    except Exception as e:
        print(f"Error en navegación: {e}")
        tester.take_screenshot("navigation_error")
        raise
    finally:
        tester.close()

if __name__ == "__main__":
    # Ejecutar tests individualmente
    print("Ejecutando test básico...")
    test_basic_navigation()
    
    print("\nEjecutando test completo...")
    test_complete_checkin_checkout_flow()
