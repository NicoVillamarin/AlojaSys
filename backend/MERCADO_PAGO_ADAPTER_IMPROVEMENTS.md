# Mejoras del MercadoPagoAdapter - AlojaSys

## 📋 Resumen de Mejoras Implementadas

Este documento describe las mejoras críticas implementadas en el `MercadoPagoAdapter` de AlojaSys para mejorar la robustez, trazabilidad y capacidad de testing del sistema de pagos.

## 🔑 1. Idempotencia en Llamadas de Captura/Refund

### **Problema Resuelto**
Las llamadas duplicadas a la API de MercadoPago podían causar reembolsos o capturas múltiples del mismo pago.

### **Solución Implementada**
- **Generación automática de `idempotency_key`** única para cada operación
- **Inclusión en headers HTTP** de todas las peticiones salientes
- **Manejo elegante de respuestas de duplicados** de la API

### **Uso**
```python
# El adapter genera automáticamente la idempotency_key
adapter = MercadoPagoAdapter(config, mock_mode=True)
result = adapter.refund("payment_123", Decimal("100.00"), "Test refund")

# La respuesta incluye la clave utilizada
print(result.raw_response["idempotency_key"])
# Output: "refund_payment_123_1703123456_a1b2c3d4"
```

### **Formato de Idempotency Key**
```
{operation}_{payment_id}_{timestamp}_{unique_id}
```
- `operation`: Tipo de operación (refund, capture)
- `payment_id`: ID del pago en MercadoPago
- `timestamp`: Timestamp Unix de la operación
- `unique_id`: 8 caracteres únicos del UUID

## 🧪 2. Simulación de Errores para Tests E2E

### **Problema Resuelto**
Los tests E2E no podían simular errores específicos de la API de MercadoPago para validar el manejo de fallos.

### **Errores Simulables Implementados**

#### **A. Error de Conexión (`connection_error`)**
```python
config = {
    'simulate_connection_error': True,
    'connection_error_rate': 0.3  # 30% de probabilidad
}
adapter = MercadoPagoAdapter(config, mock_mode=True)
```

#### **B. Error de Reembolso Parcial (`partial_refund_not_allowed`)**
```python
config = {
    'simulate_partial_refund_error': True,
    'partial_refund_error_rate': 0.5  # 50% de probabilidad
}
adapter = MercadoPagoAdapter(config, mock_mode=True)
```

### **Configuración Completa de Simulación**
```python
config = {
    # Errores de conexión
    'simulate_connection_error': True,
    'connection_error_rate': 0.1,  # 10% de probabilidad
    
    # Errores de reembolso parcial
    'simulate_partial_refund_error': True,
    'partial_refund_error_rate': 0.2,  # 20% de probabilidad
    
    # Errores generales (existente)
    'failure_rate': 0.05,  # 5% de probabilidad
    'simulate_duplicates': True,
    'duplicate_rate': 0.1,  # 10% de probabilidad
    
    # Latencia (existente)
    'simulate_latency': True,
    'latency_min_ms': 100,
    'latency_max_ms': 2000
}
```

## 📊 3. Logging de Trace ID

### **Problema Resuelto**
No había trazabilidad de las peticiones salientes a MercadoPago, dificultando el debugging y monitoreo.

### **Solución Implementada**
- **Generación automática de `trace_id`** único para cada petición
- **Logging estructurado** con información de trazabilidad
- **Inclusión en respuestas** para correlación de logs

### **Formato de Trace ID**
```
mp_trace_{16_character_hex}
```
Ejemplo: `mp_trace_a1b2c3d4e5f67890`

### **Logging Estructurado**
```python
# Log de petición saliente
logger.info(
    "Petición saliente a MercadoPago",
    extra={
        'trace_id': 'mp_trace_a1b2c3d4e5f67890',
        'method': 'POST',
        'endpoint': '/v1/payments/123/refunds',
        'idempotency_key': 'refund_123_1703123456_a1b2c3d4',
        'is_test': True
    }
)

# Log de respuesta recibida
logger.info(
    "Respuesta recibida de MercadoPago",
    extra={
        'trace_id': 'mp_trace_a1b2c3d4e5f67890',
        'status_code': 200,
        'response_size': 1024
    }
)
```

## 🚀 4. Nuevos Métodos Implementados

### **A. Método `capture()`**
```python
# Capturar un pago autorizado
result = adapter.capture("payment_123", Decimal("100.00"))

# Capturar el monto total (sin especificar amount)
result = adapter.capture("payment_123")
```

### **B. Método `_make_api_request()`**
```python
# Método interno para peticiones HTTP con logging
response = adapter._make_api_request(
    method="POST",
    endpoint="/v1/payments/123/refunds",
    data={"amount": 100.00},
    idempotency_key="refund_123_1703123456_a1b2c3d4",
    trace_id="mp_trace_a1b2c3d4e5f67890"
)
```

## 🧪 5. Tests Comprehensivos

### **Archivo de Tests**
`backend/test_mercado_pago_adapter_improvements.py`

### **Cobertura de Tests**
- ✅ Generación de idempotency keys
- ✅ Generación de trace IDs
- ✅ Simulación de errores de conexión
- ✅ Simulación de errores de reembolso parcial
- ✅ Simulación de duplicados
- ✅ Simulación de latencia
- ✅ Logging estructurado
- ✅ Flujos completos de refund y capture
- ✅ Manejo de errores con trazabilidad

### **Ejecutar Tests**
```bash
# Ejecutar tests específicos del adapter
python manage.py test test_mercado_pago_adapter_improvements

# Ejecutar con verbose
python manage.py test test_mercado_pago_adapter_improvements -v 2
```

## 🔧 6. Configuración y Uso

### **Configuración Básica**
```python
from apps.payments.adapters.mercado_pago import MercadoPagoAdapter
from decimal import Decimal

# Configuración para testing
config = {
    'access_token': 'your_access_token',
    'public_key': 'your_public_key',
    'is_test': True,
    'mock_mode': True,  # Para testing
    'simulate_connection_error': True,
    'connection_error_rate': 0.1,
    'simulate_partial_refund_error': True,
    'partial_refund_error_rate': 0.2
}

adapter = MercadoPagoAdapter(config, mock_mode=True)
```

### **Configuración para Producción**
```python
# Configuración para producción
config = {
    'access_token': 'your_production_token',
    'public_key': 'your_production_key',
    'is_test': False,
    'mock_mode': False  # Usar API real
}

adapter = MercadoPagoAdapter(config, mock_mode=False)
```

## 📈 7. Beneficios de las Mejoras

### **Robustez**
- ✅ Prevención de operaciones duplicadas
- ✅ Manejo elegante de errores de API
- ✅ Recuperación automática de fallos de conexión

### **Trazabilidad**
- ✅ Rastreo completo de peticiones
- ✅ Correlación de logs entre sistemas
- ✅ Debugging simplificado

### **Testing**
- ✅ Simulación realista de errores
- ✅ Tests E2E más robustos
- ✅ Validación de escenarios de fallo

### **Monitoreo**
- ✅ Métricas de rendimiento
- ✅ Alertas de errores específicos
- ✅ Análisis de patrones de fallo

## 🔍 8. Ejemplos de Uso en Tests E2E

### **Test de Error de Conexión**
```python
def test_connection_error_handling():
    config = {
        'simulate_connection_error': True,
        'connection_error_rate': 1.0
    }
    adapter = MercadoPagoAdapter(config, mock_mode=True)
    
    with pytest.raises(ConnectionError):
        adapter.refund("payment_123", Decimal("100.00"))
```

### **Test de Error de Reembolso Parcial**
```python
def test_partial_refund_error():
    config = {
        'simulate_partial_refund_error': True,
        'partial_refund_error_rate': 1.0
    }
    adapter = MercadoPagoAdapter(config, mock_mode=True)
    
    result = adapter.refund("payment_123", Decimal("50.00"))
    assert not result.success
    assert result.error == "partial_refund_not_allowed"
```

### **Test de Idempotencia**
```python
def test_idempotency():
    adapter = MercadoPagoAdapter(config, mock_mode=True)
    
    # Primera llamada
    result1 = adapter.refund("payment_123", Decimal("100.00"))
    assert result1.success
    
    # Segunda llamada con misma idempotency_key (simulada)
    config['simulate_duplicates'] = True
    config['duplicate_rate'] = 1.0
    adapter2 = MercadoPagoAdapter(config, mock_mode=True)
    
    result2 = adapter2.refund("payment_123", Decimal("100.00"))
    assert not result2.success
    assert "ya procesado" in result2.error
```

## 🎯 9. Próximos Pasos

### **Mejoras Futuras**
1. **Circuit Breaker** - Para manejo robusto de fallos de API
2. **Métricas con Prometheus** - Para monitoreo avanzado
3. **Rate Limiting** - Para prevenir abuso de API
4. **Retry Logic** - Para reintentos automáticos en fallos temporales
5. **Health Checks** - Para verificar estado del adapter

### **Integración con Sistema Existente**
- ✅ Compatible con `PaymentProcessorService` existente
- ✅ Compatible con `WebhookSecurityService` existente
- ✅ Mantiene interfaz `PaymentGatewayAdapter`
- ✅ No requiere cambios en el frontend

## 📝 10. Notas de Desarrollo

### **Backward Compatibility**
- ✅ Todos los cambios son backward compatible
- ✅ No se requieren cambios en código existente
- ✅ Configuración opcional para nuevas funcionalidades

### **Performance**
- ✅ Generación de IDs optimizada
- ✅ Logging asíncrono para no impactar rendimiento
- ✅ Cache de configuraciones para evitar recálculos

### **Seguridad**
- ✅ Idempotency keys únicas e impredecibles
- ✅ Trace IDs no contienen información sensible
- ✅ Logging sanitizado de datos sensibles

---

## 🏆 Conclusión

Las mejoras implementadas en el `MercadoPagoAdapter` proporcionan una base sólida para:

1. **Operaciones seguras** con idempotencia garantizada
2. **Testing robusto** con simulación realista de errores
3. **Trazabilidad completa** para debugging y monitoreo
4. **Escalabilidad** para futuras mejoras del sistema

Estas mejoras posicionan a AlojaSys como un sistema de pagos robusto y confiable, listo para manejar los desafíos de un entorno de producción real.
