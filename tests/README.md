# Testing Automatizado - AlojaSys

Este directorio contiene todos los tests automatizados para el sistema AlojaSys, incluyendo tests de API y tests de UI con Selenium para probar los flujos de check-in y check-out en los hoteles.

## 🚀 Configuración Rápida

### Opción 1: Configuración Automática (Recomendada)

```bash
# Navegar al directorio de tests
cd tests

# Ejecutar el script de configuración automática
python setup_selenium.py
```

### Opción 2: Configuración Manual

```bash
# Navegar al directorio de tests
cd tests

# Instalar dependencias de Python
pip install -r requirements.txt

# Verificar que Docker Compose esté ejecutándose
cd ..
docker-compose up -d
```

## 🧪 Ejecutar Tests

### Tests de Selenium (UI) - Funcionando ✅

```bash
# Test completo de check-in/check-out
python -m pytest test_checkin_checkout_automated.py -v -s

# Test específico
python -m pytest test_checkin_checkout_automated.py::test_complete_checkin_checkout_flow -v -s

# Con navegador visible (para debugging)
python -m pytest test_checkin_checkout_automated.py -v -s --headless=False
```

### Tests de API

```bash
python -m pytest test_api.py -v
```

## 🔧 Configuración del Navegador

Los tests están configurados para usar Chrome por defecto. El sistema detecta automáticamente la instalación de Chrome y descarga ChromeDriver automáticamente.

### Requisitos del navegador

- Google Chrome (última versión recomendada)
- ChromeDriver se descarga automáticamente

## 📊 Datos de Prueba

El sistema incluye datos de prueba automáticos:

- **Usuario**: admin
- **Contraseña**: admin123
- **Hotel**: Hotel Test (ID: 35, Bogotá)
- **Habitaciones**: 40 habitaciones distribuidas en 4 pisos
  - Piso 1: 10 habitaciones single (80,000 COP/noche)
  - Piso 2: 10 habitaciones double (120,000 COP/noche)  
  - Piso 3: 10 habitaciones triple (150,000 COP/noche)
  - Piso 4: 10 habitaciones suite (250,000 COP/noche)
- **Reservas**: ~17 reservas de prueba con fechas aleatorias

### Scripts de Configuración de Datos

```bash
# Configuración completa de datos de prueba
python setup_test_data.py

# Scripts individuales
python check_hotels.py              # Verificar hoteles existentes
python create_test_rooms.py         # Crear 40 habitaciones
python create_test_reservations.py  # Crear reservas de prueba
```

## 🐛 Troubleshooting

### Error de ChromeDriver

```bash
# Actualizar webdriver-manager
pip install --upgrade webdriver-manager
```

### Error de conexión al backend

```bash
# Verificar que Docker esté ejecutándose
docker-compose ps

# Reiniciar servicios
docker-compose down && docker-compose up -d
```

### Error de elementos no encontrados

- Verificar que el frontend esté ejecutándose en http://localhost:5173
- Usar `--headless=False` para debugging visual

## 📈 Estado Actual

✅ **Funcionando correctamente:**
- Login automatizado
- Navegación a página de reservas
- Búsqueda de reservas
- Proceso de check-in
- Detección de botones de acción

⚠️ **En desarrollo:**
- Proceso de check-out (depende del estado de la reserva)
- Tests de otros módulos del sistema

---

### 2. Configurar variables de entorno

Edita el archivo `.env` con tus credenciales:

```env
TEST_USERNAME=tu_usuario@test.com
TEST_PASSWORD=tu_contraseña
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

### 3. Asegurar que los servicios estén ejecutándose

```bash
# En la raíz del proyecto
docker-compose up -d

# O ejecutar manualmente:
# Backend: python manage.py runserver
# Frontend: npm run dev
```

## 🧪 Ejecutar Tests

### Ejecutar todos los tests

```bash
python run_tests.py
```

### Ejecutar tests específicos

```bash
# Solo tests de check-in
python run_tests.py checkin

# Solo tests de check-out  
python run_tests.py checkout

# Con navegador específico
python run_tests.py all firefox

# En modo headless (sin interfaz gráfica)
python run_tests.py all chrome true
```

### Ejecutar con pytest directamente

```bash
# Todos los tests
pytest test_*.py -v

# Test específico
pytest test_checkin.py::TestCheckIn::test_checkin_hotel_1 -v

# Con reporte HTML
pytest test_*.py --html=reports/report.html --self-contained-html
```

## 📁 Estructura de Archivos

```
tests/
├── requirements.txt          # Dependencias de Python
├── config.py                # Configuración de tests
├── conftest.py              # Fixtures globales de pytest
├── base_test.py             # Clase base para tests
├── test_checkin.py          # Tests de check-in
├── test_checkout.py         # Tests de check-out
├── run_tests.py             # Script principal de ejecución
├── setup_tests.py           # Script de configuración
├── README.md                # Este archivo
├── .env                     # Variables de entorno
├── logs/                    # Logs de ejecución
├── reports/                 # Reportes HTML
├── screenshots/             # Screenshots de errores
└── test_data/               # Datos de prueba
```

## 🔧 Configuración Avanzada

### Cambiar navegador

Edita `config.py`:

```python
BROWSER = "firefox"  # chrome, firefox, edge
HEADLESS = True      # True para ejecutar sin interfaz
```

### Ajustar timeouts

```python
IMPLICIT_WAIT = 10   # Espera implícita
EXPLICIT_WAIT = 20   # Espera explícita
```

### Agregar más datos de prueba

Edita `config.py` en la sección `TEST_RESERVATIONS`:

```python
TEST_RESERVATIONS = [
    {
        "hotel_id": 1,
        "room_id": 1,
        "guest_name": "Nuevo Huésped",
        "guest_email": "nuevo@test.com",
        "check_in": "2024-01-20",
        "check_out": "2024-01-22",
        "guests": 2
    }
]
```

## 🐛 Debugging

### Ver screenshots de errores

Los screenshots se guardan automáticamente en `screenshots/` cuando hay errores.

### Ver logs detallados

```bash
# Los logs se guardan en logs/test_run_TIMESTAMP.log
tail -f logs/test_run_*.log
```

### Ejecutar un test específico con debug

```bash
pytest test_checkin.py::TestCheckIn::test_checkin_hotel_1 -v -s --tb=long
```

## 📊 Reportes

Los reportes HTML se generan automáticamente en `reports/report.html` después de cada ejecución.

## 🔄 Flujo de Tests

### Test de Check-in
1. Navega a la página de reservas
2. Busca una reserva confirmada
3. Hace click en "Check-in"
4. Verifica que el estado cambie a "check-in"
5. Verifica que la habitación esté ocupada

### Test de Check-out
1. Navega a la página de reservas
2. Busca una reserva en check-in
3. Hace click en "Check-out"
4. Verifica que el estado cambie a "check-out"
5. Verifica que la habitación esté disponible

## ⚠️ Requisitos Previos

- Python 3.8+
- Navegador Chrome, Firefox o Edge
- AlojaSys ejecutándose (backend + frontend)
- Datos de prueba en la base de datos

## 🆘 Solución de Problemas

### Error: "Backend no disponible"
- Verifica que el backend esté ejecutándose en http://localhost:8000
- Revisa la configuración en `config.py`

### Error: "No se encontró reserva para huésped"
- Asegúrate de que existan reservas de prueba en la base de datos
- Verifica los nombres de huéspedes en `config.py`

### Error: "Elemento no encontrado"
- Los selectores pueden haber cambiado en el frontend
- Revisa y actualiza los selectores en `base_test.py`

### Error de drivers de Selenium
```bash
# Reinstalar drivers
python setup_tests.py
```

## 📝 Notas Importantes

- Los tests asumen que tienes al menos 2 hoteles con habitaciones
- Las reservas de prueba deben estar en estado "confirmed"
- Los tests pueden fallar si hay cambios en la interfaz de usuario
- Siempre revisa los logs para entender por qué falló un test
