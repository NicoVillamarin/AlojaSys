# Tests de Integración - Cancelación y Reembolsos

Este directorio contiene los tests de integración para el sistema de cancelación y reembolsos de AlojaSys.

## Estructura

```
tests/
├── README.md                           # Este archivo
├── conftest.py                        # Configuración de pytest
├── factories.py                       # Factories para crear datos de test
├── test_cancel_refund_integration.py  # Tests de integración principales
└── fixtures/                          # Datos de prueba (si es necesario)
```

## Tests Incluidos

### 1. Tests de Cancelación

- **test_pending_reservation_cancelled_no_refund**: Reserva PENDING cancelada → no refund
- **test_confirmed_reservation_cancelled_within_cutoff_full_refund**: Reserva CONFIRMED cancelada antes de cutoff → refund total
- **test_confirmed_reservation_cancelled_outside_cutoff_partial_refund**: Reserva CONFIRMED cancelada fuera de ventana → refund parcial
- **test_confirmed_reservation_cancelled_outside_cutoff_no_refund**: Reserva CONFIRMED cancelada fuera de ventana → refund marked pending/manual

### 2. Tests de Auto-cancelación

- **test_auto_cancel_task_pending_deposit_expired**: Auto-cancel task: PENDING con deposit expired → CANCELLED
- **test_auto_cancel_task_pending_checkin_expired**: Auto-cancel task: PENDING con check-in vencido → CANCELLED

### 3. Tests de Procesamiento de Reembolsos

- **test_process_pending_refunds_task_retry_logic**: process_pending_refunds task retry logic
- **test_refund_processing_with_different_methods**: Procesamiento con diferentes métodos
- **test_refund_processing_with_voucher**: Procesamiento con voucher
- **test_refund_expiration_handling**: Manejo de expiración de refunds

### 4. Tests de Casos Edge

- **test_cancellation_without_payment_policy**: Cancelación sin política de pago
- **test_cancellation_without_refund_policy**: Cancelación sin política de devolución
- **test_cancellation_with_zero_amount**: Cancelación con monto cero
- **test_cancellation_with_negative_amount**: Cancelación con monto negativo
- **test_cancellation_with_invalid_dates**: Cancelación con fechas inválidas

## Factories Incluidas

### Factories de Entidades Principales

- **HotelFactory**: Crea hoteles de prueba
- **RoomFactory**: Crea habitaciones de prueba
- **ReservationFactory**: Crea reservas de prueba
- **PaymentFactory**: Crea pagos de prueba
- **RefundFactory**: Crea reembolsos de prueba

### Factories Especializadas

- **PendingReservationFactory**: Reservas PENDING sin pagos
- **ConfirmedReservationFactory**: Reservas CONFIRMED con pago
- **ExpiredPendingReservationFactory**: Reservas PENDING con check-in vencido
- **FreeCancellationPolicyFactory**: Política de cancelación gratuita
- **StrictCancellationPolicyFactory**: Política de cancelación estricta
- **FullRefundPolicyFactory**: Política de devolución completa
- **NoRefundPolicyFactory**: Política sin devoluciones

### Factories de Métodos de Reembolso

- **CreditCardRefundFactory**: Reembolso por tarjeta de crédito
- **BankTransferRefundFactory**: Reembolso por transferencia bancaria
- **CashRefundFactory**: Reembolso en efectivo
- **VoucherRefundFactory**: Reembolso por voucher

## Ejecución de Tests

### Instalación de Dependencias

```bash
pip install -r requirements-test.txt
```

### Ejecutar Todos los Tests

```bash
# Desde el directorio backend/
python run_tests.py
```

### Ejecutar Tests Específicos

```bash
# Tests de integración
pytest tests/test_cancel_refund_integration.py -v

# Tests con coverage
pytest tests/test_cancel_refund_integration.py --cov=apps.payments --cov=apps.reservations

# Tests específicos
pytest tests/test_cancel_refund_integration.py::TestCancelRefundIntegration::test_pending_reservation_cancelled_no_refund -v
```

### Ejecutar con Pytest

```bash
# Todos los tests
pytest

# Tests de integración
pytest -m integration

# Tests unitarios
pytest -m unit

# Tests rápidos
pytest -m fast

# Tests lentos
pytest -m slow
```

## Configuración

### Variables de Entorno

```bash
# Base de datos de test
DATABASE_URL=sqlite:///test_db.sqlite3

# Configuración de Celery para tests
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=True

# Configuración de email para tests
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
```

### Configuración de Pytest

El archivo `pytest.ini` contiene la configuración básica:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = hotel.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = --tb=short --strict-markers --disable-warnings
```

## Mocks y Fixtures

### Fixtures Principales

- **mock_timezone**: Mock para timezone.now()
- **mock_celery_tasks**: Mock para tareas de Celery
- **mock_notifications**: Mock para servicio de notificaciones
- **mock_payment_gateway**: Mock para pasarela de pagos
- **sample_hotel_data**: Datos de hotel de ejemplo
- **sample_reservation**: Reserva de ejemplo
- **sample_refund**: Reembolso de ejemplo

### Uso de Mocks

```python
def test_with_mock(self, mock_payment_gateway):
    # El mock está configurado automáticamente
    result = RefundProcessor.process_refund(reservation)
    # Verificar que se llamó el mock
    mock_payment_gateway.assert_called_once()
```

## Cobertura de Tests

### Generar Reporte de Cobertura

```bash
pytest --cov=apps.payments --cov=apps.reservations --cov-report=html
```

### Ver Cobertura en Terminal

```bash
pytest --cov=apps.payments --cov=apps.reservations --cov-report=term-missing
```

## Debugging

### Ejecutar Tests con Debug

```bash
pytest -s -v --tb=long tests/test_cancel_refund_integration.py
```

### Ejecutar Test Específico con Debug

```bash
pytest -s -v --tb=long tests/test_cancel_refund_integration.py::TestCancelRefundIntegration::test_pending_reservation_cancelled_no_refund
```

### Usar PDB para Debug

```python
import pdb; pdb.set_trace()
```

## Mejores Prácticas

### 1. Nombres Descriptivos

```python
def test_confirmed_reservation_cancelled_within_cutoff_full_refund(self):
    """Test: Reserva CONFIRMED cancelada antes de cutoff → refund total"""
```

### 2. Arrange-Act-Assert

```python
def test_example(self):
    # Arrange
    reservation = ConfirmedReservationFactory()
    
    # Act
    result = RefundProcessor.process_refund(reservation)
    
    # Assert
    self.assertTrue(result['success'])
```

### 3. Un Test por Escenario

```python
def test_pending_reservation_cancelled_no_refund(self):
    """Test: Reserva PENDING cancelada → no refund"""
    # Test específico para este escenario

def test_confirmed_reservation_cancelled_within_cutoff_full_refund(self):
    """Test: Reserva CONFIRMED cancelada antes de cutoff → refund total"""
    # Test específico para este escenario
```

### 4. Usar Factories

```python
# ✅ Bueno
reservation = ConfirmedReservationFactory(hotel=self.hotel)

# ❌ Malo
reservation = Reservation.objects.create(
    hotel=self.hotel,
    room=self.room,
    # ... muchos campos
)
```

### 5. Limpiar Después de Tests

```python
def tearDown(self):
    """Limpieza después de cada test"""
    super().tearDown()
    # Limpiar datos si es necesario
```

## Troubleshooting

### Problemas Comunes

1. **Error de base de datos**: Verificar que las migraciones estén aplicadas
2. **Error de imports**: Verificar que el PYTHONPATH esté configurado
3. **Error de Celery**: Verificar que CELERY_TASK_ALWAYS_EAGER esté configurado
4. **Error de timezone**: Usar el fixture mock_timezone

### Logs de Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verificar Estado de la Base de Datos

```python
def test_debug(self):
    print(f"Reservas: {Reservation.objects.count()}")
    print(f"Reembolsos: {Refund.objects.count()}")
    print(f"Pagos: {Payment.objects.count()}")
```

## Contribución

### Agregar Nuevos Tests

1. Crear test en `test_cancel_refund_integration.py`
2. Usar factories existentes cuando sea posible
3. Seguir el patrón Arrange-Act-Assert
4. Agregar docstring descriptivo
5. Ejecutar tests para verificar que pasen

### Agregar Nuevas Factories

1. Crear factory en `factories.py`
2. Seguir convenciones de naming
3. Usar SubFactory para relaciones
4. Agregar docstring descriptivo
5. Ejecutar tests para verificar que funcionen

### Modificar Tests Existentes

1. Verificar que no rompa tests existentes
2. Actualizar docstrings si es necesario
3. Ejecutar todos los tests
4. Actualizar documentación si es necesario

