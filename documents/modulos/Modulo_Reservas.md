# Módulo: Gestión de Reservas — Guía para Clientes

Este módulo maneja el **ciclo completo de una reserva**: desde la creación hasta el check-out.

## Flujo típico

- **Consultar disponibilidad**: fechas, huéspedes, tipo de habitación.
- **Crear reserva**: datos del huésped + datos de estadía.
- **Gestionar estados**:
  - **Pendiente**: creada, aún sin confirmar.
  - **Confirmada**: confirmada (por ejemplo, pago OK).
  - **Check-in**: huésped alojado.
  - **Check-out**: estadía finalizada.
  - **Cancelada** / **No-show**.

## Validaciones automáticas (para evitar errores)

- Evita **solapamientos** (no permite overbooking interno).
- Valida **capacidad** y **fechas** (check-in < check-out).
- Respeta restricciones de venta:
  - **CTA** (cerrado a llegadas) / **CTD** (cerrado a salidas)
  - **estadía mínima/máxima** según reglas del hotel.

## Reservas multi-habitación (para grupos)

Permite reservar **varias habitaciones en una sola operación**, con:

- Mismas fechas para el grupo.
- Huéspedes por habitación.
- Precio total consolidado.

## Beneficios

- Menos errores por validaciones.
- Operación clara: estados, historial y trazabilidad.
- Ideal para recepción y administración.

