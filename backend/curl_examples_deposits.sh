#!/bin/bash

# Ejemplos de curl para probar la funcionalidad de señas
# Asegúrate de reemplazar <token> con un token JWT válido y <base_url> con la URL de tu API

BASE_URL="http://localhost:8000"
TOKEN="<tu_token_jwt_aqui>"

echo "=== EJEMPLOS DE CURL PARA SEÑAS ==="
echo ""

# 1. Crear seña (modo solo recibos)
echo "1. Crear seña (modo solo recibos):"
curl -X POST "$BASE_URL/api/payments/create-deposit/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 1,
    "amount": 2000.00,
    "method": "cash",
    "send_to_afip": false,
    "notes": "Seña del 50%"
  }' | jq '.'

echo ""
echo "---"
echo ""

# 2. Crear seña (modo fiscal)
echo "2. Crear seña (modo fiscal):"
curl -X POST "$BASE_URL/api/payments/create-deposit/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 1,
    "amount": 2000.00,
    "method": "cash",
    "send_to_afip": true,
    "notes": "Seña con facturación AFIP"
  }' | jq '.'

echo ""
echo "---"
echo ""

# 3. Generar factura con múltiples pagos
echo "3. Generar factura con múltiples pagos:"
curl -X POST "$BASE_URL/api/invoicing/invoices/generate-from-payment/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "send_to_afip": true,
    "reference_payments": [1, 2, 3],
    "customer_name": "Juan Pérez",
    "customer_document_type": "DNI",
    "customer_document_number": "12345678",
    "customer_address": "Calle Falsa 123",
    "customer_city": "Buenos Aires",
    "customer_postal_code": "1000",
    "customer_country": "Argentina"
  }' | jq '.'

echo ""
echo "---"
echo ""

# 4. Obtener pagos de una reserva
echo "4. Obtener pagos de una reserva:"
curl -X GET "$BASE_URL/api/payments/reservation/1/payments/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "---"
echo ""

# 5. Obtener facturas de una reserva
echo "5. Obtener facturas de una reserva:"
curl -X GET "$BASE_URL/api/invoicing/invoices/by-reservation/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "---"
echo ""

# 6. Verificar configuración AFIP
echo "6. Verificar configuración AFIP:"
curl -X GET "$BASE_URL/api/invoicing/afip/status/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "=== FIN DE EJEMPLOS ==="
