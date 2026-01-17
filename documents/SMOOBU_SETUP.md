# Integración Smoobu (Channel Manager) — Setup

Esta integración agrega **Smoobu** como provider de OTAs en AlojaSys, sin quitar nada de lo existente.

## Qué hace hoy (MVP)

- **Entrada a AlojaSys**:
  - Webhook Smoobu → crea/actualiza/cancela reservas en AlojaSys.
  - Pull periódico (respaldo) → consulta reservas modificadas y hace upsert en AlojaSys.
- **Mapeo**:
  - Smoobu `apartmentId` → AlojaSys `Room` usando `OtaRoomMapping` con `provider=smoobu` y `external_id=<apartmentId>`.

## Qué NO hace aún (fase 2)

- Enviar disponibilidad/precios/bloqueos desde AlojaSys hacia Smoobu.

## Variables de entorno (backend)

- `SMOOBU_WEBHOOK_TOKEN`: token propio para validar requests entrantes del webhook (Smoobu no documenta firma HMAC).
- (Opcional) `SMOOBU_BASE_URL`: default `https://login.smoobu.com`.

## Endpoints (backend)

- **Webhook**: `POST /api/otas/webhooks/smoobu/?token=SMOOBU_WEBHOOK_TOKEN`

## Configuración en Frontend (Configuración → OTAs)

1. Crear `Config`:
   - **Provider**: `Smoobu`
   - **Smoobu API Key**: pegá la Api-Key (header `Api-Key`)
   - (Opcional) **Smoobu Base URL**: `https://login.smoobu.com`
2. Crear `Mapeo por habitación`:
   - **Provider**: `Smoobu`
   - **External ID**: `Apartment ID` de Smoobu (ej: `398`)

## Smoke test (backend)

Ejecutar:

```bash
python manage.py smoobu_smoke_test --hotel-id 1 --room-id 10 --apartment-id 398 --api-key "TU_API_KEY"
```

Este comando:
- Crea/actualiza `OtaConfig` Smoobu con api key.
- Crea/actualiza el `OtaRoomMapping` Smoobu.
- Ejecuta un pull de reservas y registra el resultado en `OtaSyncJob`/`OtaSyncLog`.

