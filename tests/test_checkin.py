"""
Tests para el flujo de Check-in
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from base_test import BaseTest
import logging

def test_checkin_hotel_1(driver, wait, login, test_data):
        """Test de check-in para Hotel 1"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-in Hotel 1")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar reserva de prueba
        reservation_data = test_data[0]  # Primera reserva
        guest_name = reservation_data["guest_name"]
        
        self.logger.info(f"Buscando reserva para huésped: {guest_name}")
        reservation_row = self.find_reservation_by_guest(guest_name)
        
        assert reservation_row is not None, f"No se encontró reserva para {guest_name}"
        
        # Verificar que la reserva esté en estado "confirmed"
        status_cell = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "confirmed" in status_cell.text.lower(), f"Reserva no está confirmada: {status_cell.text}"
        
        # Hacer check-in
        self.logger.info("Realizando check-in...")
        assert self.click_action_button(reservation_row, "Check-in"), "No se pudo hacer click en Check-in"
        
        # Esperar confirmación
        assert self.wait_for_status_change("check-in"), "No se confirmó el check-in"
        
        # Verificar que el estado cambió
        time.sleep(2)  # Esperar a que se actualice la UI
        updated_status = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-in" in updated_status.text.lower(), f"Estado no cambió a check-in: {updated_status.text}"
        
        # Verificar estado de la habitación
        room_name = reservation_row.find_element(By.XPATH, ".//td[3]").text  # Columna de habitación
        assert self.verify_room_status(room_name, "occupied"), f"Habitación {room_name} no está ocupada"
        
        self.logger.info("Test de check-in Hotel 1 completado exitosamente")
    
    def test_checkin_hotel_2(self, driver, wait, login, test_data):
        """Test de check-in para Hotel 2"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-in Hotel 2")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar reserva de prueba
        reservation_data = test_data[1]  # Segunda reserva
        guest_name = reservation_data["guest_name"]
        
        self.logger.info(f"Buscando reserva para huésped: {guest_name}")
        reservation_row = self.find_reservation_by_guest(guest_name)
        
        assert reservation_row is not None, f"No se encontró reserva para {guest_name}"
        
        # Verificar que la reserva esté en estado "confirmed"
        status_cell = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "confirmed" in status_cell.text.lower(), f"Reserva no está confirmada: {status_cell.text}"
        
        # Hacer check-in
        self.logger.info("Realizando check-in...")
        assert self.click_action_button(reservation_row, "Check-in"), "No se pudo hacer click en Check-in"
        
        # Esperar confirmación
        assert self.wait_for_status_change("check-in"), "No se confirmó el check-in"
        
        # Verificar que el estado cambió
        time.sleep(2)  # Esperar a que se actualice la UI
        updated_status = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-in" in updated_status.text.lower(), f"Estado no cambió a check-in: {updated_status.text}"
        
        # Verificar estado de la habitación
        room_name = reservation_row.find_element(By.XPATH, ".//td[3]").text  # Columna de habitación
        assert self.verify_room_status(room_name, "occupied"), f"Habitación {room_name} no está ocupada"
        
        self.logger.info("Test de check-in Hotel 2 completado exitosamente")
    
    def test_checkin_invalid_status(self, driver, wait, login):
        """Test de check-in con estado inválido (debe fallar)"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-in con estado inválido")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar una reserva que no esté confirmada
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        
        for row in rows:
            status_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
            if "pending" in status_cell.text.lower():
                # Intentar hacer check-in en reserva pendiente
                checkin_button = row.find_element(By.XPATH, ".//button[contains(text(), 'Check-in')]")
                
                # El botón debe estar deshabilitado
                assert not checkin_button.is_enabled(), "Botón de check-in debería estar deshabilitado para reserva pendiente"
                break
        else:
            pytest.skip("No se encontró reserva pendiente para probar")
    
    def test_checkin_already_checked_in(self, driver, wait, login):
        """Test de check-in en reserva ya con check-in (debe fallar)"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-in en reserva ya con check-in")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar una reserva que ya esté en check-in
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        
        for row in rows:
            status_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
            if "check-in" in status_cell.text.lower():
                # El botón de check-in debe estar deshabilitado
                checkin_button = row.find_element(By.XPATH, ".//button[contains(text(), 'Check-in')]")
                assert not checkin_button.is_enabled(), "Botón de check-in debería estar deshabilitado para reserva ya con check-in"
                break
        else:
            pytest.skip("No se encontró reserva con check-in para probar")
