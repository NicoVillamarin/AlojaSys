# Módulo: Reembolsos Automáticos — Guía para Clientes

Este módulo automatiza el **procesamiento de reembolsos**, reduciendo trabajo manual y mejorando tiempos de respuesta.

## Qué hace

- Busca reembolsos pendientes de forma periódica (ej: cada hora).
- Intenta procesarlos automáticamente.
- Hace **reintentos inteligentes** si hay fallos temporales.
- Respeta la **ventana de tiempo** permitida por la pasarela (ej: límites de Mercado Pago).

## Qué tipos de reembolso contempla

- Por **cancelación**
- Por **no-show**
- Por **sobrepago**
- Por **ajustes administrativos**

## Cómo te enterás

El sistema genera **notificaciones** cuando:

- un reembolso fue exitoso
- un reembolso falló y requiere atención manual
- un reembolso expiró (se pasó el límite de tiempo)

## Beneficios

- Ahorra tiempo (solo intervenís en excepciones).
- Mejora la experiencia del huésped (más rápido y transparente).

