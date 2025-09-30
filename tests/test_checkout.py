"""
Tests para el flujo de Check-out
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from base_test import BaseTest
import logging
import time

class TestCheckOut(BaseTest):
    """Tests específicos para el proceso de check-out"""
    
    def test_checkout_hotel_1(self, driver, wait, login, test_data):
        """Test de check-out para Hotel 1"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-out Hotel 1")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar reserva de prueba que esté en check-in
        reservation_data = test_data[0]  # Primera reserva
        guest_name = reservation_data["guest_name"]
        
        self.logger.info(f"Buscando reserva para huésped: {guest_name}")
        reservation_row = self.find_reservation_by_guest(guest_name)
        
        assert reservation_row is not None, f"No se encontró reserva para {guest_name}"
        
        # Verificar que la reserva esté en estado "check-in"
        status_cell = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        if "check-in" not in status_cell.text.lower():
            # Si no está en check-in, intentar hacer check-in primero
            self.logger.info("Reserva no está en check-in, intentando check-in primero...")
            assert self.click_action_button(reservation_row, "Check-in"), "No se pudo hacer check-in"
            assert self.wait_for_status_change("check-in"), "No se confirmó el check-in"
            time.sleep(2)  # Esperar actualización de UI
        
        # Hacer check-out
        self.logger.info("Realizando check-out...")
        assert self.click_action_button(reservation_row, "Check-out"), "No se pudo hacer click en Check-out"
        
        # Esperar confirmación
        assert self.wait_for_status_change("check-out"), "No se confirmó el check-out"
        
        # Verificar que el estado cambió
        time.sleep(2)  # Esperar a que se actualice la UI
        updated_status = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-out" in updated_status.text.lower(), f"Estado no cambió a check-out: {updated_status.text}"
        
        # Verificar estado de la habitación (debe estar disponible)
        room_name = reservation_row.find_element(By.XPATH, ".//td[3]").text  # Columna de habitación
        assert self.verify_room_status(room_name, "available"), f"Habitación {room_name} no está disponible"
        
        self.logger.info("Test de check-out Hotel 1 completado exitosamente")
    
    def test_checkout_hotel_2(self, driver, wait, login, test_data):
        """Test de check-out para Hotel 2"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-out Hotel 2")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar reserva de prueba que esté en check-in
        reservation_data = test_data[1]  # Segunda reserva
        guest_name = reservation_data["guest_name"]
        
        self.logger.info(f"Buscando reserva para huésped: {guest_name}")
        reservation_row = self.find_reservation_by_guest(guest_name)
        
        assert reservation_row is not None, f"No se encontró reserva para {guest_name}"
        
        # Verificar que la reserva esté en estado "check-in"
        status_cell = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        if "check-in" not in status_cell.text.lower():
            # Si no está en check-in, intentar hacer check-in primero
            self.logger.info("Reserva no está en check-in, intentando check-in primero...")
            assert self.click_action_button(reservation_row, "Check-in"), "No se pudo hacer check-in"
            assert self.wait_for_status_change("check-in"), "No se confirmó el check-in"
            time.sleep(2)  # Esperar actualización de UI
        
        # Hacer check-out
        self.logger.info("Realizando check-out...")
        assert self.click_action_button(reservation_row, "Check-out"), "No se pudo hacer click en Check-out"
        
        # Esperar confirmación
        assert self.wait_for_status_change("check-out"), "No se confirmó el check-out"
        
        # Verificar que el estado cambió
        time.sleep(2)  # Esperar a que se actualice la UI
        updated_status = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-out" in updated_status.text.lower(), f"Estado no cambió a check-out: {updated_status.text}"
        
        # Verificar estado de la habitación (debe estar disponible)
        room_name = reservation_row.find_element(By.XPATH, ".//td[3]").text  # Columna de habitación
        assert self.verify_room_status(room_name, "available"), f"Habitación {room_name} no está disponible"
        
        self.logger.info("Test de check-out Hotel 2 completado exitosamente")
    
    def test_checkout_invalid_status(self, driver, wait, login):
        """Test de check-out con estado inválido (debe fallar)"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-out con estado inválido")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar una reserva que no esté en check-in
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        
        for row in rows:
            status_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
            if "confirmed" in status_cell.text.lower() or "pending" in status_cell.text.lower():
                # El botón de check-out debe estar deshabilitado
                checkout_button = row.find_element(By.XPATH, ".//button[contains(text(), 'Check-out')]")
                assert not checkout_button.is_enabled(), "Botón de check-out debería estar deshabilitado para reserva no en check-in"
                break
        else:
            pytest.skip("No se encontró reserva con estado inválido para probar")
    
    def test_checkout_already_checked_out(self, driver, wait, login):
        """Test de check-out en reserva ya con check-out (debe fallar)"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test de check-out en reserva ya con check-out")
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar una reserva que ya esté en check-out
        rows = self.driver.find_elements(By.XPATH, "//tbody/tr")
        
        for row in rows:
            status_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
            if "check-out" in status_cell.text.lower():
                # El botón de check-out debe estar deshabilitado
                checkout_button = row.find_element(By.XPATH, ".//button[contains(text(), 'Check-out')]")
                assert not checkout_button.is_enabled(), "Botón de check-out debería estar deshabilitado para reserva ya con check-out"
                break
        else:
            pytest.skip("No se encontró reserva con check-out para probar")
    
    def test_complete_checkin_checkout_flow(self, driver, wait, login, test_data):
        """Test completo: check-in seguido de check-out"""
        if not login:
            pytest.skip("Login fallido")
        
        self.logger.info("Iniciando test completo de check-in y check-out")
        
        # Usar la primera reserva de prueba
        reservation_data = test_data[0]
        guest_name = reservation_data["guest_name"]
        
        # Navegar a reservas
        assert self.navigate_to_reservations(), "No se pudo navegar a reservas"
        
        # Buscar reserva
        reservation_row = self.find_reservation_by_guest(guest_name)
        assert reservation_row is not None, f"No se encontró reserva para {guest_name}"
        
        # 1. Hacer check-in
        self.logger.info("Paso 1: Realizando check-in...")
        assert self.click_action_button(reservation_row, "Check-in"), "No se pudo hacer check-in"
        assert self.wait_for_status_change("check-in"), "No se confirmó el check-in"
        time.sleep(2)
        
        # Verificar estado check-in
        status_cell = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-in" in status_cell.text.lower(), "Estado no cambió a check-in"
        
        # 2. Hacer check-out
        self.logger.info("Paso 2: Realizando check-out...")
        assert self.click_action_button(reservation_row, "Check-out"), "No se pudo hacer check-out"
        assert self.wait_for_status_change("check-out"), "No se confirmó el check-out"
        time.sleep(2)
        
        # Verificar estado check-out
        updated_status = reservation_row.find_element(By.XPATH, ".//td[contains(@class, 'status')]")
        assert "check-out" in updated_status.text.lower(), "Estado no cambió a check-out"
        
        # 3. Verificar que la habitación esté disponible
        room_name = reservation_row.find_element(By.XPATH, ".//td[3]").text
        assert self.verify_room_status(room_name, "available"), f"Habitación {room_name} no está disponible"
        
        self.logger.info("Test completo de check-in y check-out finalizado exitosamente")
