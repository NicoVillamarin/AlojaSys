"""
Clase base para todos los tests de AlojaSys
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

class BaseTest:
    """Clase base con métodos comunes para todos los tests"""
    
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def navigate_to_reservations(self):
        """Navegar a la página de gestión de reservas"""
        try:
            # Buscar y hacer click en el enlace de reservas
            reservations_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Reservas') or contains(text(), 'Reservations')]"))
            )
            reservations_link.click()
            
            # Esperar a que cargue la página
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "reservations-page"))
            )
            return True
            
        except TimeoutException:
            self.logger.error("No se pudo navegar a la página de reservas")
            return False
    
    def find_reservation_by_guest(self, guest_name):
        """Buscar una reserva por nombre de huésped"""
        try:
            # Buscar en la tabla de reservas
            rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
            
            for row in rows:
                guest_cell = row.find_element(By.XPATH, ".//td[1]")  # Primera columna es huésped
                if guest_name in guest_cell.text:
                    return row
                    
            return None
            
        except NoSuchElementException:
            self.logger.error(f"No se encontró reserva para huésped: {guest_name}")
            return None
    
    def click_action_button(self, row, action):
        """Hacer click en un botón de acción específico"""
        try:
            # Buscar el botón de acción en la fila
            action_buttons = row.find_elements(By.XPATH, ".//button")
            
            for button in action_buttons:
                if action.lower() in button.text.lower():
                    button.click()
                    return True
                    
            self.logger.error(f"No se encontró botón de acción: {action}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error al hacer click en botón {action}: {e}")
            return False
    
    def wait_for_status_change(self, expected_status, timeout=10):
        """Esperar a que cambie el estado de una reserva"""
        try:
            # Esperar a que aparezca un mensaje de confirmación o cambio de estado
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{expected_status}')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'realizado') or contains(text(), 'exitoso')]"))
                )
            )
            return True
            
        except TimeoutException:
            self.logger.error(f"No se detectó cambio de estado a: {expected_status}")
            return False
    
    def verify_room_status(self, room_name, expected_status):
        """Verificar el estado de una habitación"""
        try:
            # Navegar a la página de habitaciones
            rooms_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Habitaciones') or contains(text(), 'Rooms')]")
            rooms_link.click()
            
            # Buscar la habitación específica
            room_row = self.driver.find_element(By.XPATH, f"//tr[contains(., '{room_name}')]")
            status_cell = room_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
            
            return expected_status.lower() in status_cell.text.lower()
            
        except Exception as e:
            self.logger.error(f"Error al verificar estado de habitación {room_name}: {e}")
            return False
    
    def take_screenshot(self, name):
        """Tomar screenshot para debugging"""
        try:
            timestamp = int(time.time())
            filename = f"screenshots/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot guardado: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error al tomar screenshot: {e}")
            return None
    
    def wait_and_click(self, locator, timeout=10):
        """Esperar elemento y hacer click"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
            return True
        except TimeoutException:
            self.logger.error(f"Elemento no clickeable: {locator}")
            return False
    
    def wait_for_text(self, locator, text, timeout=10):
        """Esperar a que aparezca un texto específico"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator, text)
            )
            return True
        except TimeoutException:
            self.logger.error(f"Texto '{text}' no encontrado en: {locator}")
            return False
