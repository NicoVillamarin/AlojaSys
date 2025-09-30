"""
Test manual para verificar que todo funciona
"""
import requests
import time

def test_services():
    """Test manual de servicios"""
    print("=== TEST MANUAL DE SERVICIOS ===")
    
    # Test backend
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print(f"OK - Backend: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Backend: {e}")
    
    # Test frontend
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        print(f"OK - Frontend: {response.status_code}")
    except Exception as e:
        print(f"ERROR - Frontend: {e}")
    
    print("\n=== INSTRUCCIONES PARA TESTING MANUAL ===")
    print("1. Abre tu navegador")
    print("2. Ve a http://localhost:5173")
    print("3. Haz login con tus credenciales")
    print("4. Ve a la sección de Reservas")
    print("5. Busca una reserva en estado 'confirmed'")
    print("6. Haz click en 'Check-in'")
    print("7. Verifica que el estado cambie a 'check-in'")
    print("8. Haz click en 'Check-out'")
    print("9. Verifica que el estado cambie a 'check-out'")
    print("\n¡Esto es exactamente lo que harán los tests automatizados!")

if __name__ == "__main__":
    test_services()
