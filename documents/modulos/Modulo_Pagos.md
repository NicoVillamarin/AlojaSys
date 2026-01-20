# Módulo: Sistema de Pagos — Guía para Clientes

Este módulo permite **cobrar, registrar y controlar pagos** de reservas (señas, pagos parciales y pagos finales).

## Qué soporta

- **Mercado Pago** (integración con webhooks para confirmar pagos).
- **Métodos manuales**: efectivo, transferencia, POS.
- **Múltiples monedas** (según configuración).

## Políticas de pago (configurables)

- **Sin adelanto** (pago completo al confirmar).
- **Adelanto por porcentaje** (ej: 50%).
- **Adelanto por monto fijo**.
- **Vencimientos**: al confirmar / días antes / al check-in.
- **Saldo pendiente**: al check-in o check-out.

## Señas y pagos parciales

- El sistema puede calcular automáticamente la **seña requerida** según la política.
- Podés cobrar **seña** y luego **saldo**.

## Beneficios

- Orden y trazabilidad: sabés qué se cobró, cuándo y cómo.
- Menos trabajo manual con confirmaciones automáticas (cuando aplica).
- Se integra con comprobantes, devoluciones y facturación (si está habilitada).

