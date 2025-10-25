# Integración de Señas (Pagos Parciales) con AFIP

Este documento describe la implementación de soporte completo para señas (pagos parciales) en el módulo Payments e integración con el módulo Invoicing/AFIP.

## Configuración

### 1. PaymentPolicy

La política de pago define las reglas para señas:

```python
# Campos relevantes para señas
allow_deposit = True  # Permitir señas
deposit_type = "percentage"  # "percentage", "fixed", "none"
deposit_value = 50.00  # 50% o monto fijo
deposit_due = "confirmation"  # Cuándo vence la seña
deposit_days_before = 0  # Días antes del check-in
balance_due = "check_in"  # Cuándo vence el saldo
```

### 2. AfipConfig

Configuración de facturación por hotel:

```python
# Modos de facturación para señas
invoice_mode = "receipt_only"  # Solo recibos para señas
# o
invoice_mode = "fiscal_on_deposit"  # Facturación AFIP en señas
```

## Endpoints

### 1. Crear Seña

**POST** `/api/payments/create-deposit/`

```json
{
    "reservation_id": 123,
    "amount": 1000.00,
    "method": "cash",
    "send_to_afip": false,
    "notes": "Seña del 50%"
}
```

**Respuesta:**
```json
{
    "message": "Seña creada exitosamente",
    "payment": {
        "id": 456,
        "reservation_id": 123,
        "hotel_name": "Hotel Test",
        "amount": "1000.00",
        "method": "cash",
        "is_deposit": true,
        "status": "approved",
        "receipt_pdf_url": "https://example.com/receipt.pdf",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "deposit_info": {
        "required": true,
        "amount": "1000.00",
        "percentage": 50,
        "type": "percentage",
        "due": "confirmation",
        "balance_due": "check_in"
    }
}
```

### 2. Generar Factura con Múltiples Pagos

**POST** `/api/invoicing/invoices/generate-from-payment/{payment_id}/`

```json
{
    "send_to_afip": true,
    "reference_payments": [123, 124, 125],
    "customer_name": "Juan Pérez",
    "customer_document_type": "DNI",
    "customer_document_number": "12345678",
    "customer_address": "Calle Falsa 123",
    "customer_city": "Buenos Aires",
    "customer_postal_code": "1000",
    "customer_country": "Argentina"
}
```

**Respuesta:**
```json
{
    "id": "uuid-factura",
    "number": "0001-00000001",
    "total": "4000.00",
    "status": "approved",
    "cae": "12345678901234",
    "payments_included": [123, 124, 125],
    "total_payments": 3
}
```

## Flujos de Trabajo

### Flujo 1: Solo Recibos (receipt_only)

1. **Crear seña:**
   ```bash
   curl -X POST /api/payments/create-deposit/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "reservation_id": 123,
       "amount": 2000.00,
       "method": "cash",
       "send_to_afip": false
     }'
   ```

2. **Pago final:**
   ```bash
   curl -X POST /api/payments/create-deposit/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "reservation_id": 123,
       "amount": 2000.00,
       "method": "cash",
       "send_to_afip": false
     }'
   ```

3. **Generar factura final:**
   ```bash
   curl -X POST /api/invoicing/invoices/generate-from-payment/456/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "send_to_afip": true,
       "reference_payments": [123, 456],
       "customer_name": "Juan Pérez"
     }'
   ```

### Flujo 2: Facturación en Seña (fiscal_on_deposit)

1. **Crear seña con facturación:**
   ```bash
   curl -X POST /api/payments/create-deposit/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "reservation_id": 123,
       "amount": 2000.00,
       "method": "cash",
       "send_to_afip": true
     }'
   ```

2. **Pago final:**
   ```bash
   curl -X POST /api/payments/create-deposit/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "reservation_id": 123,
       "amount": 2000.00,
       "method": "cash",
       "send_to_afip": false
     }'
   ```

3. **Generar nota de crédito o factura complementaria:**
   ```bash
   curl -X POST /api/invoicing/invoices/generate-from-payment/456/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "send_to_afip": true,
       "reference_payments": [123, 456],
       "customer_name": "Juan Pérez"
     }'
   ```

## Modelos de Datos

### Payment (extendido)

```python
class Payment(models.Model):
    # ... campos existentes ...
    is_deposit = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
```

### Invoice (extendido)

```python
class Invoice(models.Model):
    # ... campos existentes ...
    payment = models.ForeignKey(Payment, ...)  # Pago principal (compatibilidad)
    payments_data = models.JSONField(default=list)  # Lista de IDs de pagos
```

### AfipConfig (extendido)

```python
class AfipConfig(models.Model):
    # ... campos existentes ...
    invoice_mode = models.CharField(
        max_length=20,
        choices=InvoiceMode.choices,
        default=InvoiceMode.RECEIPT_ONLY
    )
```

## Validaciones

- **Monto de seña:** No puede exceder el depósito requerido según la política
- **Estado de reserva:** Solo se pueden crear señas en estados `pending` o `confirmed`
- **Pagos de referencia:** Todos deben pertenecer a la misma reserva
- **Configuración AFIP:** Requerida para facturación

## Tareas Automáticas

- **Generación de PDF:** Se genera automáticamente un recibo PDF para cada seña
- **Envío de email:** Se envía el recibo por email al huésped principal
- **Facturación AFIP:** Se envía automáticamente a AFIP si está configurado

## Testing

Ejecutar tests de integración:

```bash
cd backend
python manage.py test test_deposit_integration
```

## Notas de Implementación

- Los campos `is_deposit` y `metadata` en Payment permiten identificar y almacenar información adicional de las señas
- El campo `payments_data` en Invoice permite vincular múltiples pagos a una factura
- El modo `invoice_mode` en AfipConfig controla el comportamiento de facturación para señas
- Se mantiene compatibilidad con el sistema existente mediante el campo `payment` en Invoice
