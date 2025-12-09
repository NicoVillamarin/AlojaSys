# AlojaSys – Definición de Planes y Módulos (BORRADOR)

## 1. Objetivo del documento

Dejar por escrito, de forma clara y estable, **qué incluye cada plan comercial** de AlojaSys a nivel de módulos/funcionalidades, separado de los precios.  
Los precios se pueden ajustar en otro documento o sección sin tocar esta definición.

Los números de secciones entre paréntesis hacen referencia a los módulos descritos en:
- `PMS_Documentacion_Completa.md` (doc técnica para devs)
- `PMS_Funcionalidades_y_Modulos.md` (doc funcional para clientes)

---

## 2. Plan Starter – Operación diaria simple

**Target:** hostels y hoteles pequeños que necesitan gestionar reservas, habitaciones y cobros manuales, sin OTAs ni integraciones complejas.

### 2.1 Módulos incluidos

- **Core / Configuración base**
  - Gestión de Hoteles (3.1)
  - Gestión de Habitaciones (3.2)
  - Gestión de Reservas (3.3)
  - Gestión de Usuarios básica (3.10)  
    - Roles mínimos: administrador, recepción

- **Operación diaria**
  - Calendario de reservas (3.9 / 3.3)
  - Dashboard / reportes básicos (3.8)  
    - Ocupación, reservas por día, ingresos simples
  - Sistema de notificaciones básico (3.12)  
    - Avisos de nuevas reservas, cambios de estado, etc.
  - Gestión de Limpieza / Housekeeping básico (3.17 / 3.16)  
    - Vista de tareas e historial  
    - **Generación automática de tarea de limpieza en check-out**

- **Pagos y políticas (versión simple)**
  - Sistema de Pagos manuales (3.4)  
    - Registro de pagos: efectivo, transferencia, POS externo.  
    - Cálculo de saldo pendiente por reserva.
  - Políticas de cancelación y devoluciones simples (3.5 / 3.6)  
    - Configuración de 1–2 políticas generales por hotel.  
    - Manejo manual de cancelaciones y no-show (sin automatizar devoluciones).

- **Automatizaciones básicas**
  - Emails automáticos simples (confirmación, cancelación, check-out)
  - Auto check-in según fecha/hora configurada por hotel  
  - Auto check-out según fecha/hora de salida  
  - Auto no-show cuando el huésped no se presenta

### 2.2 Lo que NO incluye el Plan Starter

- Integraciones con OTAs / Channel Manager (3.16).
- Facturación electrónica AFIP (3.13 / 3.14).
- Mercado Pago / integraciones de cobro online (3.4.x avanzado).
- Módulo avanzado de devoluciones automáticas / vouchers masivos.
- Chatbot de WhatsApp (módulo chatbot).

### 2.3 Modelo de precios sugerido

> Referencia principal en **USD** para mantener estabilidad. Los montos en ARS se ajustan según tipo de cambio al momento de la propuesta.

- **Precio por habitación/mes (USD)**: **USD 3** / habitación / mes.  
- **Mínimo mensual por hotel (USD)**: **USD 25** / mes.  
- **Ejemplos (USD)**:
  - Hotel de 8 habitaciones → se aplica mínimo → **USD 25 / mes**.  
  - Hotel de 15 habitaciones → 15 × 3 = **USD 45 / mes**.  
  - Hotel de 25 habitaciones → 25 × 3 = **USD 75 / mes**.

> Referencia no contractual para Argentina (ejemplo):  
> si 1 USD ≈ 1.000 ARS →  
> - **Precio por habitación/mes (ARS)**: ≈ **ARS 3.000** / habitación / mes.  
> - **Mínimo mensual por hotel (ARS)**: ≈ **ARS 25.000** / mes.  
> - **Ejemplos (ARS)**:  
>   - Hotel de 8 habitaciones → mínimo → ≈ **ARS 25.000 / mes**.  
>   - Hotel de 15 habitaciones → 15 × 3.000 = ≈ **ARS 45.000 / mes**.  
>   - Hotel de 25 habitaciones → 25 × 3.000 = ≈ **ARS 75.000 / mes**.

---

## 3. Plan Pro – PMS + Pagos online + AFIP + WhatsApp (BYON)

**Target:** hoteles que ya necesitan facturación, pagos online y automatizar parte del flujo de reservas directas, incluyendo WhatsApp bot con número propio (Bring Your Own Number).

### 3.1 Módulos incluidos

Incluye **todo lo del Plan Starter**, más:

- **Pagos avanzados**
  - Sistema de Pagos completo (3.4)  
    - Integración con **Mercado Pago** (links/QR de pago).  
    - Registro combinado de pagos online + manuales.  
    - Información de saldo y movimientos de pago por reserva.
  - Módulo de señas y pagos parciales (3.4.1 / 3.4.2)  
    - Configuración de porcentaje de seña.  
    - Registro de pagos parciales ligados a reservas.

- **Políticas y devoluciones avanzadas**
  - Políticas de cancelación / devolución más detalladas (3.5 / 3.6)  
    - Reglas ligadas a la seña (cuánto se devuelve según fecha de cancelación).  
    - Soporte para creación de **vouchers de crédito** como medio de devolución.

- **Facturación**
  - Facturación electrónica Argentina (3.13 / 3.14)  
    - Emisión de comprobantes AFIP desde reservas y pagos.  
    - Asociación de comprobantes a huéspedes y reservas.

- **Automatizaciones de cobro**
  - Envío automático del link de pago de seña por email o WhatsApp  
  - Cambio automático del estado de la reserva a **Confirmada** cuando entra el pago  
  - Recordatorios automáticos de vencimiento de seña

- **Chatbot & WhatsApp (modo BYON)**
  - Configuración de WhatsApp por hotel:  
    - `whatsapp_enabled`, `whatsapp_phone`, `whatsapp_provider`, IDs y token.  
  - Chatbot de reservas:  
    - Flujo guiado por WhatsApp que crea **reservas en estado PENDING**.  
    - Uso del mismo motor de disponibilidad y precios que el PMS.  
    - Canal de reserva marcado como **`ReservationChannel.WHATSAPP`**.  
  - Notificaciones internas de nueva reserva vía WhatsApp  
    - `NotificationType.WHATSAPP_RESERVATION_RECEIVED`.

### 3.2 Lo que NO incluye el Plan Pro

- Integraciones con OTAs / Channel Manager (3.16).
- Número de WhatsApp administrado por AlojaSys (modelo “AlojaSys-managed number”) salvo acuerdo específico.
- Housekeeping avanzado (reglas de generación automática complejas, checklists detalladas).
- Conciliación bancaria automática a nivel cuenta bancaria completa.

### 3.3 Modelo de precios sugerido

- **Precio por habitación/mes (USD)**: **USD 5** / habitación / mes.  
- **Mínimo mensual por hotel (USD)**: **USD 45** / mes.  
- **Ejemplos (USD)**:
  - Hotel de 10 habitaciones → 10 × 5 = **USD 50 / mes**.  
  - Hotel de 20 habitaciones → 20 × 5 = **USD 100 / mes**.  
  - Hotel de 30 habitaciones → 30 × 5 = **USD 150 / mes**.

> Referencia no contractual para Argentina (ejemplo):  
> si 1 USD ≈ 1.000 ARS →  
> - **Precio por habitación/mes (ARS)**: ≈ **ARS 5.000** / habitación / mes.  
> - **Mínimo mensual por hotel (ARS)**: ≈ **ARS 45.000** / mes.  
> - **Ejemplos (ARS)**:  
>   - Hotel de 10 habitaciones → 10 × 5.000 = ≈ **ARS 50.000 / mes**.  
>   - Hotel de 20 habitaciones → 20 × 5.000 = ≈ **ARS 100.000 / mes**.  
>   - Hotel de 30 habitaciones → 30 × 5.000 = ≈ **ARS 150.000 / mes**.

> Este plan incluye AFIP + Mercado Pago + bot de WhatsApp (BYON), por lo que el diferencial de precio frente al Plan Starter se justifica por la automatización de cobros y reducción de trabajo manual.

---

## 4. Plan Premium – Todo incluido + OTAs + automatizaciones avanzadas

**Target:** hoteles que quieren centralizar todo el flujo operativo: OTAs, pagos, AFIP, housekeeping avanzado y automatizaciones.

### 4.1 Módulos incluidos

Incluye **todo lo del Plan Pro**, más:

- **Integraciones con OTAs / Channel Manager (3.16)**
  - Sincronización de disponibilidad y tarifas con OTAs (Booking, Expedia, etc.).  
  - Importación automática de reservas OTA al PMS.  
  - Mapeo de canales a `ReservationChannel` correspondiente.

- **Notificaciones avanzadas (3.12)**
  - Alertas por overbooking, conflictos de disponibilidad con OTAs.  
  - Notificaciones de pagos, vencimientos, eventos críticos.

- **Housekeeping avanzado (3.17 / 3.16)**
  - Generación automática de tareas de limpieza: checkout, daily, mantenimiento.  
  - Asignación automática de personal según zonas, turnos y carga de trabajo.  
  - Checklists configurables por tipo de habitación y tipo de tarea.  
  - Métricas de desempeño y vencimiento de tareas.

- **Automatizaciones avanzadas**
  - Reglas de tarifas avanzadas (CTA/CTD, min stay, max stay, días cerrados).  
  - Automatización de limpieza diaria y de mantenimiento.  
  - Alertas inteligentes de overbooking y conflictos con OTAs.  
  - Reglas automáticas específicas por canal OTA.

- **Opcional en este plan**  
  - Modo “WhatsApp número administrado por AlojaSys”:  
    - El hotel usa una cuenta/proveedor de WhatsApp gestionado por AlojaSys.  
    - AlojaSys asume el costo directo del proveedor y lo refactura como servicio adicional.

### 4.2 Lo que NO incluye el Plan Premium

- Desarrollo a medida de funcionalidades fuera del roadmap estándar (eso se cotiza como proyecto).

### 4.3 Modelo de precios sugerido

- **Precio por habitación/mes (USD)**: **USD 7** / habitación / mes.  
- **Mínimo mensual por hotel (USD)**: **USD 70** / mes.  
- **Ejemplos (USD)**:
  - Hotel de 15 habitaciones → 15 × 7 = **USD 105 / mes**.  
  - Hotel de 25 habitaciones → 25 × 7 = **USD 175 / mes**.  
  - Hotel de 40 habitaciones → 40 × 7 = **USD 280 / mes**.

> Referencia no contractual para Argentina (ejemplo):  
> si 1 USD ≈ 1.000 ARS →  
> - **Precio por habitación/mes (ARS)**: ≈ **ARS 7.000** / habitación / mes.  
> - **Mínimo mensual por hotel (ARS)**: ≈ **ARS 70.000** / mes.  
> - **Ejemplos (ARS)**:  
>   - Hotel de 15 habitaciones → 15 × 7.000 = ≈ **ARS 105.000 / mes**.  
>   - Hotel de 25 habitaciones → 25 × 7.000 = ≈ **ARS 175.000 / mes**.  
>   - Hotel de 40 habitaciones → 40 × 7.000 = ≈ **ARS 280.000 / mes**.

> Este plan agrega OTAs, automatizaciones y housekeeping avanzado: en general se puede posicionar para hoteles que ya tienen ingresos significativos y necesitan ahorro fuerte de horas de trabajo del equipo.

---

## 5. Plan Custom – A la carta por módulos

**Target:** hoteles muy pequeños o proyectos especiales donde se arma el paquete módulo por módulo.

### 5.1 Estructura general

- **Base obligatoria (siempre incluida)**:
  - Gestión de Hoteles (3.1)  
  - Gestión de Habitaciones (3.2)  
  - Gestión de Reservas (3.3)

- **Módulos opcionales que se pueden sumar**:
  - **Pagos manuales simples** (3.4 básico).  
  - **Pagos avanzados / Mercado Pago** (3.4 completo).  
  - **Políticas de cancelación / devoluciones avanzadas** (3.5 / 3.6).  
  - **Facturación electrónica AFIP** (3.13 / 3.14).  
  - **OTAs / Channel Manager** (3.16).  
  - **Chatbot WhatsApp**:
    - Modo BYON (hotel aporta proveedor).  
    - Modo número administrado por AlojaSys.  
  - **Housekeeping avanzado** (3.17).  
  - **Conciliación bancaria / cobros avanzados** (módulos 3.4.3 y relacionados).  
  - **Reportes / dashboards adicionales** (3.8 extendido).

### 5.2 Uso del plan Custom

- Pensado para:
  - Hoteles chicos que solo quieren un subconjunto de funcionalidades.  
  - Proyectos especiales (por ejemplo, solo Channel Manager + WhatsApp, sin AFIP).  
  - Clientes que crecen: se empieza en Custom y luego se migra a un plan estándar.

En este plan, la política comercial es:
- Definir un **fee base por hotel** + **precio por habitación**.  
- Sumar un **recargo por cada módulo opcional** activado.

### 5.3 Modelo de precios sugerido

- **Fee base por hotel (USD)**: **USD 20 / mes**.  
- **Precio por habitación/mes (USD)**: **USD 2 / habitación / mes**.  
- **Recargos por módulo opcional (referencia, USD)**:
  - AFIP / facturación electrónica: **+ USD 10 / mes**.  
  - Mercado Pago / pagos avanzados: **+ USD 10 / mes**.  
  - OTAs / Channel Manager: **+ USD 20 / mes**.  
  - Chatbot WhatsApp (BYON): **+ USD 5 / mes**.  
  - Chatbot WhatsApp (número administrado por AlojaSys): **+ USD 10–15 / mes** (según costos del proveedor).  
  - Housekeeping avanzado: **+ USD 10 / mes**.  
  - Conciliación bancaria / cobros avanzados: **+ USD 10 / mes**.

> Referencia no contractual para Argentina (ejemplo):  
> si 1 USD ≈ 1.000 ARS →  
> - **Fee base por hotel (ARS)**: ≈ **ARS 20.000 / mes**.  
> - **Precio por habitación/mes (ARS)**: ≈ **ARS 2.000 / habitación / mes**.  
> - **Recargos por módulo opcional (ARS, referencia)**:  
>   - AFIP / facturación electrónica: ≈ **+ ARS 10.000 / mes**.  
>   - Mercado Pago / pagos avanzados: ≈ **+ ARS 10.000 / mes**.  
>   - OTAs / Channel Manager: ≈ **+ ARS 20.000 / mes**.  
>   - Chatbot WhatsApp (BYON): ≈ **+ ARS 5.000 / mes**.  
>   - Chatbot WhatsApp (número administrado por AlojaSys): ≈ **+ ARS 10.000–15.000 / mes**.  
>   - Housekeeping avanzado: ≈ **+ ARS 10.000 / mes**.  
>   - Conciliación bancaria / cobros avanzados: ≈ **+ ARS 10.000 / mes**.

**Ejemplo de armado Custom:**  
- Hotel de 10 habitaciones que quiere: PMS básico + AFIP + WhatsApp BYON.  
  - Base: USD 20  
  - Habitaciones: 10 × 2 = USD 20  
  - AFIP: + USD 10  
  - WhatsApp BYON: + USD 5  
  - **Total sugerido**: **USD 55 / mes**.

---

## 6. Estructura de precios por plan (resumen comercial)

Esta sección resume **cómo se cobran los planes** en función de la cantidad de habitaciones.  
Los montos siguen expresados en **USD de referencia**; para clientes en Argentina se convierten a ARS al tipo de cambio vigente.

### 6.1 Rangos recomendados por plan

- **Plan Starter**
  - Rango recomendado: **1 a 20 habitaciones** (hostels y hoteles chicos).
  - Precio: **USD 3 / habitación / mes**, con **mínimo USD 25 / hotel / mes**.

- **Plan Pro**
  - Rango recomendado: **20 a 60 habitaciones** (hoteles medianos).
  - Precio: **USD 5 / habitación / mes**, con **mínimo USD 45 / hotel / mes**.

- **Plan Premium**
  - Rango recomendado: **más de 60 habitaciones** (hoteles grandes o cadenas).
  - Precio: **USD 7 / habitación / mes**, con **mínimo USD 70 / hotel / mes**.

- **Plan Custom**
  - Sin límite de habitaciones.
  - Se arma a medida con:
    - **Fee base por hotel**.
    - **Precio por habitación**.
    - **Recargo por cada módulo opcional** activado (AFIP, OTAs, WhatsApp, etc.).

### 6.2 Fórmula general de cobro por plan (Starter / Pro / Premium)

Para los planes Starter, Pro y Premium, el precio mensual se calcula como:

\[
\text{Precio mensual} = \max(\text{habitaciones} \times \text{precio\_por\_habitación}, \text{mínimo\_del\_plan})
\]

Donde:
- **precio\_por\_habitación** es:
  - Starter: **USD 3 / habitación / mes**.
  - Pro: **USD 5 / habitación / mes**.
  - Premium: **USD 7 / habitación / mes**.
- **mínimo\_del\_plan** es:
  - Starter: **USD 25 / hotel / mes**.
  - Pro: **USD 45 / hotel / mes**.
  - Premium: **USD 70 / hotel / mes**.

Esto permite:
- Comunicar comercialmente los planes por **rangos de habitaciones** (ej: “Starter hasta 20 hab”)  
  mientras internamente se cobra **por habitación + mínimo**.
- Ajustar fácilmente los precios cuando cambien las tarifas o el tipo de cambio.

---

## 7. Notas finales

- Este documento define **alcance funcional** y una **propuesta de precios de referencia** (en USD) pensada para ser competitiva en mercado Latam/Argentina.  
- Los planes pueden mapearse internamente a flags de configuración por hotel, por ejemplo:
  - `plan_type = starter | pro | premium | custom`
  - `enabled_features = { "afip": true, "otas": false, "whatsapp_bot": true, ... }`
- Cualquier cambio fuerte de alcance (por ejemplo, mover AFIP del Plan Pro al Starter) debería reflejarse aquí, y luego ajustar solo los montos si hace falta.
- Los montos en ARS que se comuniquen a clientes deben calcularse a partir de estos valores en USD usando el tipo de cambio vigente y, si es necesario, aplicar impuestos locales correspondientes.


