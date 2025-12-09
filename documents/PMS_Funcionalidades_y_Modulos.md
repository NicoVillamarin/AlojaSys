# AlojaSys - Funcionalidades y Módulos del Sistema

## Índice
1. [¿Qué es AlojaSys?](#qué-es-alojasys)
2. [¿Cómo Funciona el Sistema?](#cómo-funciona-el-sistema)
3. [Módulos y Funcionalidades](#módulos-y-funcionalidades)
   - [3.1 Gestión de Hoteles](#31-gestión-de-hoteles)
   - [3.2 Gestión de Habitaciones](#32-gestión-de-habitaciones)
   - [3.3 Gestión de Reservas](#33-gestión-de-reservas)
   - [3.4 Sistema de Pagos](#34-sistema-de-pagos)
   - [3.4.1 Sistema de Vouchers de Crédito](#341-sistema-de-vouchers-de-crédito)
   - [3.5 Políticas de Cancelación](#35-políticas-de-cancelación)
   - [3.6 Políticas de Devolución](#36-políticas-de-devolución)
   - [3.7 Gestión de Tarifas](#37-gestión-de-tarifas)
   - [3.8 Dashboard y Reportes](#38-dashboard-y-reportes)
   - [3.9 Calendario de Reservas](#39-calendario-de-reservas)
   - [3.10 Gestión de Usuarios](#310-gestión-de-usuarios)
   - [3.11 Gestión de Empresas](#311-gestión-de-empresas)
   - [3.12 Sistema de Notificaciones](#312-sistema-de-notificaciones)
   - [3.13 Facturación Electrónica Argentina](#313-facturación-electrónica-argentina)
   - [3.14 Facturación Electrónica Argentina](#314-facturación-electrónica-argentina)
   - [3.15 Comprobantes de Señas y Devoluciones](#315-comprobantes-de-señas-y-devoluciones)
   - [3.16 Integraciones con OTAs (Channel Manager)](#316-integraciones-con-otas-channel-manager)
   - [3.17 Gestión de Limpieza (Housekeeping)](#317-gestión-de-limpieza-housekeeping)
4. [Flujos de Trabajo del Día a Día](#flujos-de-trabajo-del-día-a-día)
5. [Casos de Uso Reales](#casos-de-uso-reales)
6. [Beneficios del Sistema](#beneficios-del-sistema)
1. [¿Qué es AlojaSys?](#qué-es-alojasys)
2. [¿Cómo Funciona el Sistema?](#cómo-funciona-el-sistema)
3. [Módulos y Funcionalidades](#módulos-y-funcionalidades)
   - [3.1 Gestión de Hoteles](#31-gestión-de-hoteles)
   - [3.2 Gestión de Habitaciones](#32-gestión-de-habitaciones)
   - [3.3 Gestión de Reservas](#33-gestión-de-reservas)
   - [3.4 Sistema de Pagos](#34-sistema-de-pagos)
   - [3.4.1 Transferencias Bancarias con OCR](#341-transferencias-bancarias-con-ocr-v22)
   - [3.4.2 Módulo de Cobros](#342-módulo-de-cobros-v22)
   - [3.4.3 Conciliación Bancaria Automática](#343-conciliación-bancaria-automática-v23)
   - [3.5 Políticas de Cancelación](#35-políticas-de-cancelación)
   - [3.6 Políticas de Devolución](#36-políticas-de-devolución)
   - [3.7 Gestión de Tarifas](#37-gestión-de-tarifas)
   - [3.8 Dashboard y Reportes](#38-dashboard-y-reportes)
   - [3.9 Calendario de Reservas](#39-calendario-de-reservas)
   - [3.10 Gestión de Usuarios](#310-gestión-de-usuarios)
   - [3.11 Gestión de Empresas](#311-gestión-de-empresas)
   - [3.12 Sistema de Notificaciones](#312-sistema-de-notificaciones)
   - [3.13 Procesamiento Automático de Reembolsos](#313-procesamiento-automático-de-reembolsos)
   - [3.14 Facturación Electrónica Argentina](#314-facturación-electrónica-argentina)
   - [3.15 Comprobantes de Señas y Pagos Parciales](#315-comprobantes-de-señas-y-pagos-parciales)
   - [3.16 Integraciones con OTAs (Channel Manager)](#316-integraciones-con-otas-channel-manager)
   - [3.17 Gestión de Limpieza (Housekeeping)](#317-gestión-de-limpieza-housekeeping)
4. [Flujos de Trabajo del Día a Día](#flujos-de-trabajo-del-día-a-día)
5. [Casos de Uso Reales](#casos-de-uso-reales)
6. [Beneficios del Sistema](#beneficios-del-sistema)

---

## ¿Qué es AlojaSys?

**AlojaSys** es un sistema de gestión hotelera completo que permite administrar todos los aspectos de un hotel de manera digital y eficiente. Es como tener un asistente digital que se encarga de:

- 🏨 **Gestionar las habitaciones** y su disponibilidad
- 📅 **Administrar las reservas** desde la consulta hasta el check-out
- 📆 **Visualizar reservas** en un calendario interactivo y elegante
- 💰 **Procesar pagos** de manera segura y flexible
- 💳 **Manejar señas** (pagos parciales) con facturación automática
- 🧾 **Generar comprobantes** de señas automáticamente
- 🤖 **Procesar reembolsos** automáticamente 24/7
- 🏦 **Conciliar bancos** automáticamente con extractos
- 📊 **Generar reportes** y métricas del negocio
- 👥 **Gestionar usuarios** y permisos del personal
- 🏢 **Administrar múltiples hoteles** desde una sola plataforma
- 🔔 **Recibir notificaciones** sobre eventos importantes del sistema

---

## ¿Cómo Funciona el Sistema?

### Arquitectura Simple
El sistema está dividido en **módulos especializados** que trabajan juntos:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Base de       │
│   (Interfaz)    │◄──►│   (Lógica)      │◄──►│   Datos         │
│                 │    │                 │    │                 │
│ • Reservas      │    │ • Validaciones  │    │ • Información   │
│ • Pagos         │    │ • Cálculos      │    │   de Hoteles    │
│ • Dashboard     │    │ • Procesos      │    │ • Reservas      │
│ • Configuración │    │ • APIs          │    │ • Pagos         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Flujo de Información
1. **Usuario** interactúa con la interfaz web
2. **Frontend** envía solicitudes al backend
3. **Backend** procesa la lógica de negocio
4. **Base de datos** almacena y recupera información
5. **Respuesta** se devuelve al usuario

---

## Módulos y Funcionalidades

## 3.1 Gestión de Hoteles

### ¿Qué hace?
Permite configurar y administrar la información básica de cada hotel en el sistema.

### ¿Cómo funciona?

#### Configuración Básica
- **Datos del Hotel**: Nombre, dirección, teléfono, email
- **Información Legal**: Razón social, CUIT/CUIL
- **Ubicación**: País, provincia, ciudad
- **Horarios**: Hora de check-in y check-out
- **Zona Horaria**: Para manejar reservas en diferentes zonas
- **Auto Check-in**: Configuración para marcar automáticamente reservas como check-in al llegar la fecha de entrada
- **Auto Check-out**: Configuración para hacer check-out automático cuando pasa la fecha de salida (habilitado por defecto)
- **Auto No-Show**: Configuración para marcar automáticamente reservas como no-show

#### Ejemplo Práctico
```
Hotel: "Hotel Plaza Central"
Dirección: "Av. Corrientes 1234, Buenos Aires"
Check-in: 15:00 hs
Check-out: 11:00 hs
Zona horaria: America/Argentina/Buenos_Aires
Auto check-in: Deshabilitado
Auto check-out: Habilitado (por defecto)
Auto no-show: Habilitado
```

### Beneficios
- ✅ **Información centralizada** de cada hotel
- ✅ **Configuración flexible** de horarios
- ✅ **Soporte multi-hotel** desde una sola plataforma
- ✅ **Datos legales** para facturación
- ✅ **Auto check-in configurable** por hotel
- ✅ **Auto check-out configurable** por hotel (habilitado por defecto para mayor eficiencia)
- ✅ **Auto no-show configurable** por hotel

### Check-out Automático

El sistema puede hacer check-out automático de las reservas cuando pasa la fecha de salida, liberando las habitaciones sin necesidad de intervención manual.

#### ¿Cómo funciona?

**Proceso Automático**:
1. **Detección**: El sistema verifica cada hora si hay reservas que deben hacer check-out
2. **Fecha Pasada**: Si la fecha de check-out ya pasó, se procesa inmediatamente
3. **Fecha de Hoy**: Si es el día de check-out, espera hasta la hora configurada del hotel (ej: 11:00 AM)
4. **Check-out**: Cambia el estado de la reserva a "Check-out" automáticamente
5. **Liberación**: Marca la habitación como "Disponible" para nuevas reservas

#### Configuración

- **Habilitado por Defecto**: Todos los hoteles tienen check-out automático habilitado automáticamente
- **Personalizable**: Puedes deshabilitarlo por hotel si prefieres hacer check-outs manualmente
- **Zona Horaria**: Respeta la zona horaria del hotel para cálculos precisos
- **Hora Configurada**: Usa la hora de check-out configurada del hotel (ej: 11:00 AM)

#### Beneficios del Check-out Automático

- ✅ **Menos Trabajo Manual**: No necesitas recordar hacer check-outs manualmente
- ✅ **Habitaciones Disponibles**: Las habitaciones se liberan automáticamente para nuevas reservas
- ✅ **Sin Olvidos**: Las reservas con fecha de salida pasada se procesan automáticamente
- ✅ **Eficiencia**: El sistema funciona 24/7 sin necesidad de supervisión
- ✅ **Configurable**: Puedes habilitarlo o deshabilitarlo según tus necesidades

---

## 3.2 Gestión de Habitaciones

### ¿Qué hace?
Administra todas las habitaciones del hotel: tipos, precios, capacidad y estado.

### ¿Cómo funciona?

#### Tipos de Habitaciones
- **Single**: Para 1 persona
- **Doble**: Para 2 personas
- **Triple**: Para 3 personas
- **Suite**: Habitación premium

#### Información de Cada Habitación
- **Identificación**: Número y piso
- **Capacidad**: Huéspedes incluidos y máximo
- **Precio Base**: Tarifa por noche
- **Extra por Huésped**: Costo adicional por persona extra
- **Estado**: Disponible, Ocupada, Mantenimiento, etc.

#### Ejemplo Práctico
```
Habitación: "101 - Suite Presidencial"
Piso: 1
Tipo: Suite
Capacidad incluida: 2 personas
Capacidad máxima: 4 personas
Precio base: $50,000 por noche
Extra por huésped: $15,000 por persona adicional
Estado: Disponible
```

### Estados de Habitación
- 🟢 **Disponible**: Lista para reservar
- 🔴 **Ocupada**: Con huéspedes
- 🟡 **Reservada**: Confirmada pero sin huéspedes
- 🔧 **Mantenimiento**: En reparación
- ❌ **Fuera de Servicio**: No disponible

### Beneficios
- ✅ **Control total** de la capacidad del hotel
- ✅ **Precios flexibles** por tipo de habitación
- ✅ **Gestión de extras** por huéspedes adicionales
- ✅ **Estados en tiempo real** de cada habitación

---

## 3.3 Gestión de Reservas

### ¿Qué hace?
Maneja todo el ciclo de vida de una reserva, desde la consulta hasta el check-out.

### ¿Cómo funciona?

#### Proceso de Reserva

##### 1. Consulta de Disponibilidad
```
Cliente busca:
- Fechas: 15/01/2024 - 18/01/2024
- Huéspedes: 2 personas
- Tipo: Suite

Sistema verifica:
- ¿Hay habitaciones disponibles?
- ¿La habitación soporta 2 huéspedes?
- ¿Hay restricciones de fechas?
- ¿Cuál es el precio total?
```

##### 2. Creación de Reserva
```
Datos del huésped:
- Nombre: Juan Pérez
- Email: juan@email.com
- Teléfono: +54 9 11 1234-5678
- Documento: 12345678

Datos de la reserva:
- Habitación: Suite 101
- Fechas: 15/01 - 18/01 (3 noches)
- Huéspedes: 2 personas
- Precio total: $150,000
```

##### 3. Estados de la Reserva
- 🟡 **Pendiente**: Creada pero sin confirmar
- 🟢 **Confirmada**: Pago procesado exitosamente
- 🔴 **Check-in**: Huéspedes en el hotel
- 🔵 **Check-out**: Huéspedes se fueron
- ❌ **Cancelada**: Reserva cancelada
- ⚠️ **No-show**: Huésped no se presentó

#### Validaciones Automáticas
- **Disponibilidad**: No permite reservas solapadas
- **Capacidad**: Verifica que no exceda el máximo de huéspedes
- **Fechas**: Check-in debe ser anterior al check-out
- **Restricciones**: Respeta CTA (cerrado a llegadas) y CTD (cerrado a salidas)
- **Estadía mínima/máxima**: Valida según las reglas del hotel
- **🛡️ Verificación con OTAs**: Antes de confirmar una reserva, el sistema verifica automáticamente si la habitación está ocupada en Booking.com o Airbnb para evitar overbooking (ver detalles más abajo)

### 🏨 Reservas Multi-Habitación (v2.6)

#### ¿Qué son las reservas multi-habitación?
Permiten reservar múltiples habitaciones para la misma estancia (mismas fechas de entrada y salida) en una sola operación. Ideal para familias, grupos o eventos que necesitan varias habitaciones.

#### ¿Cómo funciona?

##### 1. Creación de Reserva Multi-Habitación
```
Cliente necesita:
- 2 habitaciones
- Mismas fechas: 15/01/2024 - 18/01/2024
- Diferentes huéspedes en cada habitación

Sistema permite:
- Seleccionar múltiples habitaciones
- Asignar huéspedes específicos a cada habitación
- Aplicar códigos de descuento a nivel de grupo o por habitación
- Ver el precio total consolidado
```

##### 2. Proceso Simplificado
1. **Seleccionar hotel y fechas**: Mismas fechas para todas las habitaciones
2. **Agregar habitaciones**: Seleccionar cada habitación y número de huéspedes
3. **Datos de huéspedes**: Completar información de cada habitación
4. **Códigos de descuento**: Aplicar promociones o vouchers (opcional)
5. **Revisar y confirmar**: Ver resumen completo antes de crear
6. **Crear reserva**: Sistema crea todas las habitaciones vinculadas

##### 3. Visualización en el Sistema
- **En la tabla**: Las reservas multi-habitación aparecen agrupadas como una sola fila
- **Badge identificador**: Muestra "Multi-habitación · 2 hab." (o el número correspondiente)
- **Nombre clickeable**: Al hacer click en el nombre, se abre el detalle completo
- **Precio total**: Muestra la suma de todas las habitaciones del grupo

##### 4. Gestión de Pagos
- **Precio consolidado**: El sistema calcula el total sumando todas las habitaciones
- **Seña del grupo**: Si hay política de seña, se calcula sobre el total del grupo
- **Pagos flexibles**: Se pueden registrar pagos en cualquier reserva del grupo
- **Balance consolidado**: El sistema considera todos los pagos de todas las habitaciones

##### 5. Emails Automáticos
- **Email consolidado**: El huésped recibe un solo email con todas sus habitaciones
- **Detalles completos**: Incluye información de cada habitación, precios y total
- **Recibos adjuntos**: PDFs de recibos para cada habitación del grupo

#### Características Principales
- ✅ **Múltiples habitaciones**: Reserva 2, 3 o más habitaciones en una sola operación
- ✅ **Mismos check-in/check-out**: Todas las habitaciones comparten las mismas fechas
- ✅ **Huéspedes independientes**: Cada habitación puede tener diferentes huéspedes
- ✅ **Precios individuales**: Cada habitación calcula su precio según tarifas
- ✅ **Códigos de descuento**: Aplicar promociones a nivel de grupo o por habitación
- ✅ **Validación automática**: Verifica disponibilidad de cada habitación antes de confirmar
- ✅ **Prevención de duplicados**: No permite seleccionar la misma habitación dos veces
- ✅ **Visualización agrupada**: Se muestran como una sola reserva en las tablas
- ✅ **Emails consolidados**: Un solo email por huésped con todas sus habitaciones

#### Ejemplo Práctico
```
Familia Pérez necesita:
- Suite 101 para padres (2 personas)
- Habitación 205 para hijos (1 persona)
- Fechas: 15/01/2024 - 18/01/2024 (3 noches)

Proceso:
1. Seleccionar "Reserva multi-habitaciones"
2. Elegir hotel y fechas
3. Agregar Suite 101 → 2 huéspedes → Datos de padres
4. Agregar Habitación 205 → 1 huésped → Datos de hijo
5. Aplicar código promocional "FAMILIA2024" (descuento del 10%)
6. Revisar: Total Suite 101: $90,000 | Habitación 205: $60,000 | Total: $150,000
7. Confirmar reserva

Resultado:
- Se crean 2 reservas vinculadas con el mismo código de grupo
- Ambas comparten las mismas fechas
- Cada una tiene su precio y huéspedes
- El sistema envía un email consolidado a los padres
- En la tabla aparece como "Reserva N° 42 · Multi-habitación · 2 hab."
```

#### Beneficios para el Hotel
- ✅ **Proceso más rápido**: Crear múltiples reservas en una sola operación
- ✅ **Menos errores**: Validación automática de disponibilidad para todas las habitaciones
- ✅ **Mejor organización**: Reservas vinculadas se gestionan como un grupo
- ✅ **Pagos consolidados**: Facilita el cálculo de señas y saldos pendientes
- ✅ **Comunicación clara**: Emails consolidados mejoran la experiencia del huésped

#### Beneficios para el Huésped
- ✅ **Proceso simplificado**: Reserva todas sus habitaciones de una vez
- ✅ **Un solo email**: Recibe toda la información en un solo correo
- ✅ **Precio claro**: Ve el total consolidado desde el inicio
- ✅ **Flexibilidad**: Puede tener diferentes huéspedes en cada habitación
- ✅ **Descuentos**: Aplica códigos promocionales a todo el grupo

### Beneficios
- ✅ **Reservas sin errores** gracias a las validaciones
- ✅ **Control de disponibilidad** en tiempo real
- ✅ **Gestión completa** del ciclo de vida
- ✅ **Datos organizados** de huéspedes
- ✅ **Reservas multi-habitación** para grupos y familias

---

## 3.4 Sistema de Pagos

### ¿Qué hace?
Procesa pagos de manera segura y flexible, con políticas configurables y validaciones inteligentes.

### ¿Cómo funciona?

#### Configuración de Pasarelas de Pago
- **Mercado Pago**: Integración completa con tarjetas de crédito/débito
- **Configuración por Hotel**: Cada hotel puede tener su propia configuración
- **Modo Prueba/Producción**: Configuración separada para testing y producción
- **Validaciones Inteligentes**: El sistema previene errores comunes de configuración
- **Rotación Segura de Tokens**: Endpoint dedicado para actualizar claves de forma segura
- **Webhooks**: Confirmación automática de pagos
- **Múltiples Monedas**: Soporte para diferentes monedas por país
- **Idempotencia**: Prevención automática de pagos duplicados
- **Trazabilidad Completa**: Rastreo de todas las operaciones de pago
- **Simulación de Errores**: Testing seguro sin costos reales

#### Validaciones de Seguridad
- **Prevención de Errores**: No permite mezclar claves de prueba con producción
- **Detección Automática**: Identifica si las claves son de test o producción
- **Mensajes Claros**: Explica exactamente qué está mal y cómo corregirlo
- **Validación en Tiempo Real**: Verifica la configuración antes de guardar

#### Rotación de Tokens
- **Endpoint Seguro**: API dedicada para rotar claves de acceso
- **Validación Automática**: Aplica las mismas validaciones de seguridad
- **Rollback Automático**: Si algo falla, se revierten los cambios
- **Auditoría Completa**: Registra todas las rotaciones para seguimiento

#### Métodos de Pago Disponibles
- **Tarjetas de Crédito/Débito**: A través de Mercado Pago
- **Efectivo**: Registro manual por el personal
- **Transferencia Bancaria**: Registro manual
- **POS**: Terminal punto de venta
- **Vouchers de Crédito**: Sistema de vouchers reutilizables

#### Políticas de Pago Configurables
- **Sin Adelanto**: Pago completo al confirmar
- **Porcentaje**: Adelanto del X% del total
- **Monto Fijo**: Adelanto de $X fijo
- **Fechas de Vencimiento**: Al confirmar, días antes, al check-in
- **Saldo Pendiente**: Al check-in o al check-out

### 💰 Señas y Pagos Parciales (v2.4)

#### ¿Qué son las señas?
Las señas son pagos parciales que el huésped realiza antes del check-in para asegurar su reserva. El sistema calcula automáticamente el monto según la política configurada.

#### ¿Cómo funciona?

##### 1. Configuración de Políticas
- **Porcentaje**: "Seña del 50% del total"
- **Monto Fijo**: "Seña de $2000 fijo"
- **Sin Seña**: "Pago completo al confirmar"
- **Fechas de Vencimiento**: Al confirmar, días antes del check-in

##### 2. Cálculo Automático
- **El sistema calcula** el monto de seña según la política
- **Valida** que el monto no exceda el permitido
- **Muestra** información clara al usuario sobre la seña requerida

##### 3. Dos Modos de Facturación

###### Modo "Solo Recibos"
- **Seña**: Genera recibo PDF (no envía a AFIP)
- **Pago Final**: Genera recibo PDF (no envía a AFIP)
- **Factura Final**: Genera factura AFIP con CAE incluyendo todos los pagos

###### Modo "Facturación en Seña"
- **Seña**: Genera factura AFIP con CAE para el monto de la seña
- **Pago Final**: Genera recibo PDF
- **Nota de Crédito**: Genera nota de crédito o factura complementaria

##### 4. Proceso Completo
1. **Cliente hace reserva** → Sistema calcula seña requerida
2. **Cliente paga seña** → Se genera recibo/factura según configuración
3. **Cliente paga saldo** → Se genera recibo/factura según configuración
4. **Sistema genera factura final** → Incluye todos los pagos realizados

#### Características Principales
- **Cálculo Automático**: Usa la política de pago para calcular montos
- **Validaciones Inteligentes**: Previene errores de montos y estados
- **Múltiples Pagos por Factura**: Vincula señas + pago final en una factura
- **Integración AFIP**: Soporte completo para facturación electrónica argentina
- **PDFs Automáticos**: Genera recibos y facturas automáticamente
- **Emails Automáticos**: Envía comprobantes por email al huésped

#### Ejemplo Práctico
```
Reserva: $10,000 por 3 noches
Política: Seña del 50% al confirmar

1. Cliente confirma → Paga $5,000 (seña)
   - Sistema genera: Recibo PDF + Email
   - Si modo fiscal: Factura AFIP con CAE

2. Cliente llega al hotel → Paga $5,000 (saldo)
   - Sistema genera: Recibo PDF + Email

3. Sistema genera factura final
   - Incluye: Seña $5,000 + Saldo $5,000 = $10,000
   - Envía a AFIP y obtiene CAE
   - Genera PDF fiscal con código QR
```

#### Beneficios para el Hotel
- **Mayor Seguridad**: Reservas aseguradas con señas
- **Mejor Flujo de Caja**: Ingresos anticipados
- **Menos No-Shows**: Clientes comprometidos con el pago
- **Facturación Flexible**: Adaptable a necesidades contables
- **Automatización Completa**: Menos trabajo manual

#### Beneficios para el Huésped
- **Reserva Asegurada**: Su lugar está garantizado
- **Pago Flexible**: Puede pagar en cuotas
- **Comprobantes Claros**: Recibe todos los documentos
- **Transparencia Total**: Ve exactamente qué está pagando

### Mejoras de Seguridad Implementadas

#### Validaciones Inteligentes
- **Detección Automática**: El sistema identifica si las claves son de prueba o producción
- **Prevención de Errores**: No permite mezclar configuraciones de test con producción
- **Mensajes Claros**: Explica exactamente qué está mal y cómo corregirlo
- **Validación en Tiempo Real**: Verifica la configuración antes de guardar

#### Ejemplo de Validación
```
❌ Error detectado:
"No se puede marcar como producción si is_test=True"

✅ Solución:
- Desmarcar "is_test" si quieres usar en producción
- O usar claves de prueba si quieres mantener "is_test=True"
```

#### Rotación Segura de Tokens
- **Endpoint Dedicado**: API especializada para actualizar claves de acceso
- **Validación Automática**: Aplica las mismas validaciones de seguridad
- **Rollback Automático**: Si algo falla, se revierten los cambios automáticamente
- **Auditoría Completa**: Registra todas las rotaciones para seguimiento

#### Proceso de Rotación
1. **Acceso al endpoint** de rotación de tokens
2. **Ingreso de nuevas claves** (access_token y public_key)
3. **Validación automática** de las nuevas claves
4. **Actualización segura** si todo está correcto
5. **Registro de auditoría** de la operación

### Beneficios
- ✅ **Procesamiento seguro** de pagos
- ✅ **Configuración flexible** por hotel
- ✅ **Validaciones automáticas** que previenen errores
- ✅ **Rotación segura** de claves de acceso
- ✅ **Múltiples métodos** de pago
- ✅ **Integración completa** con Mercado Pago
- ✅ **Auditoría completa** de todas las operaciones
- ✅ **Prevención de errores** de configuración
- ✅ **Mensajes claros** para resolución de problemas
- ✅ **Prevención de duplicados** automática
- ✅ **Rastreo completo** de operaciones
- ✅ **Testing seguro** sin costos reales

### 💳 Transferencias Bancarias con OCR (v2.2)

#### ¿Qué son las transferencias bancarias?
Es un método de pago donde el cliente realiza una transferencia bancaria y sube el comprobante para confirmar el pago.

#### ¿Cómo funciona?

##### 1. Subida de Comprobante
- **Cliente selecciona transferencia** como método de pago
- **Sube comprobante** (PDF, JPG, PNG) con datos:
  - Monto de la transferencia
  - Fecha de la transferencia
  - CBU/IBAN del destinatario
  - Nombre del banco
- **Sistema procesa archivo** automáticamente

##### 2. Confirmación Automática
- **Confirmación inmediata**: La reserva se confirma automáticamente
- **Sin aprobación manual**: No requiere intervención del personal
- **Validación inteligente**: El sistema valida los datos ingresados
- **Registro completo**: Se guarda toda la información del pago

##### 3. Almacenamiento Híbrido
- **Desarrollo**: Archivos guardados localmente
- **Producción**: Archivos subidos a Cloudinary (nube)
- **Acceso universal**: Los archivos están disponibles desde cualquier lugar
- **Seguridad garantizada**: Almacenamiento seguro y confiable

##### 4. Procesamiento OCR (Opcional)
- **Extracción automática**: El sistema lee datos del comprobante
- **Validación cruzada**: Compara datos extraídos vs. datos ingresados
- **Revisión manual**: Solo si hay discrepancias importantes
- **Confirmación inteligente**: Aprovecha la tecnología para agilizar el proceso

#### Beneficios para el Cliente
- ✅ **Pago inmediato**: Confirmación instantánea de la reserva
- ✅ **Sin esperas**: No necesita aprobación manual
- ✅ **Fácil de usar**: Solo subir el comprobante
- ✅ **Seguro**: Almacenamiento protegido de comprobantes

#### Beneficios para el Hotel
- ✅ **Procesamiento automático**: Sin intervención manual necesaria
- ✅ **Trazabilidad completa**: Registro detallado de todas las transferencias
- ✅ **Archivos organizados**: Comprobantes guardados y accesibles
- ✅ **Validación inteligente**: OCR para verificar datos automáticamente

### 📊 Módulo de Cobros (v2.2)

#### ¿Qué es el módulo de Cobros?
Es un historial unificado que muestra todos los pagos y cobros del hotel en un solo lugar, con herramientas avanzadas de análisis y exportación.

#### ¿Qué incluye?

##### 1. Historial Completo
- **Pagos Manuales**: Efectivo, tarjeta, POS registrados por el personal
- **Pagos Online**: Mercado Pago y otras pasarelas de pago
- **Transferencias Bancarias**: Con comprobantes y validación
- **Reservas Pendientes**: Reservas que aún no han sido confirmadas

##### 2. Filtros Avanzados
- **Por Fecha**: Ver pagos de un período específico
- **Por Tipo**: Manual, Online, Transferencia, Pendiente
- **Por Método**: Efectivo, Tarjeta, Transferencia, Mercado Pago
- **Por Estado**: Aprobado, Pendiente, Rechazado, Cancelado
- **Por Monto**: Rango de montos específico
- **Por Huésped**: Buscar pagos de un huésped específico

##### 3. Estadísticas y Métricas
- **Resumen General**: Total de pagos, monto total, promedio
- **Distribución por Tipo**: Cuántos pagos de cada tipo
- **Distribución por Método**: Cuántos pagos de cada método
- **Evolución Temporal**: Cómo cambian los cobros en el tiempo
- **Tendencias**: Patrones de pago del hotel

##### 4. Exportación de Datos
- **Formato CSV**: Datos listos para Excel o sistemas contables
- **Filtros Aplicados**: Solo exporta los datos que necesitas
- **Descarga Directa**: Sin necesidad de procesamiento adicional
- **Datos Completos**: Todos los campos relevantes incluidos

##### 5. Archivos Adjuntos
- **Comprobantes**: Acceso directo a comprobantes de transferencias
- **Visualización**: Ver archivos sin descargarlos
- **Descarga**: Descargar archivos individuales
- **Organización**: Archivos organizados por pago

#### Beneficios para la Gestión

##### Para el Personal
- ✅ **Vista Unificada**: Todos los pagos en un solo lugar
- ✅ **Búsqueda Rápida**: Encuentra cualquier pago fácilmente
- ✅ **Filtros Intuitivos**: Reduce la información a lo que necesitas
- ✅ **Acceso a Archivos**: Ve comprobantes sin buscarlos

##### Para la Contabilidad
- ✅ **Exportación Fácil**: Datos listos para importar
- ✅ **Filtros Precisos**: Solo los datos que necesitas
- ✅ **Formato Estándar**: Compatible con cualquier sistema
- ✅ **Auditoría Completa**: Registro detallado de todo

##### Para el Análisis
- ✅ **Métricas Visuales**: Gráficos y estadísticas claras
- ✅ **Tendencias**: Ve cómo evoluciona el negocio
- ✅ **Comparaciones**: Compara diferentes períodos
- ✅ **Insights**: Descubre patrones en los pagos

### 🏦 Conciliación Bancaria Automática (v2.3)

#### ¿Qué es la Conciliación Bancaria?
Es una funcionalidad que automáticamente compara los movimientos de tu cuenta bancaria con los pagos registrados en el sistema, confirmando automáticamente las transferencias que coinciden.

#### ¿Cómo funciona?

##### 1. Subida de Extracto Bancario
- **Formato CSV**: Subes el extracto de tu banco en formato CSV
- **Detección Automática**: El sistema detecta automáticamente el formato y encoding
- **Validación**: Verifica que el archivo tenga la estructura correcta

##### 2. Matching Inteligente
- **Coincidencia Exacta**: Busca pagos con monto y fecha exactos
- **Coincidencia Aproximada**: Encuentra pagos con pequeñas diferencias de monto o fecha
- **Coincidencia Parcial**: Identifica pagos que podrían coincidir con tolerancias más amplias
- **Aprobación Manual**: Para casos dudosos, permite revisión manual

##### 3. Confirmación Automática
- **Alta Confianza (≥90%)**: Se confirman automáticamente
- **Confianza Media (70-89%)**: Requieren revisión manual
- **Baja Confianza (<70%)**: Se marcan para revisión

#### ¿Qué incluye?

##### 1. Algoritmos de Matching
- **Exact Match**: Monto exacto + fecha ±1 día
- **Fuzzy Match**: Monto ±0.5% + fecha ±2 días
- **Partial Match**: Monto ±1% + fecha ±3 días
- **Manual Match**: Aprobación manual de matches dudosos

##### 2. Configuración Flexible
- **Tolerancias Ajustables**: Configuración por hotel
- **Múltiples Monedas**: Conversión automática de tipos de cambio
- **Umbrales de Confianza**: Configuración de auto-confirmación
- **Notificaciones**: Alertas por email y sistema

##### 3. Procesamiento Automático
- **Job Nocturno**: Procesamiento automático todas las noches
- **Actualización de Tipos de Cambio**: Conversión automática de monedas
- **Notificaciones**: Alertas cuando hay problemas o resultados

##### 4. Logs de Auditoría
- **Registro Completo**: Todas las operaciones quedan registradas
- **Trazabilidad**: Seguimiento completo de cada match
- **Historial**: Acceso al historial de todas las conciliaciones

#### Formato CSV Esperado
```csv
fecha,descripcion,importe,moneda,referencia
2025-01-15,"Transferencia Juan Perez",25000.00,"ARS","CBU 28500109...1234"
2025-01-16,"Transferencia Maria Garcia",18000.00,"ARS","CBU 28500109...5678"
```

#### Beneficios para la Gestión

##### Para el Personal
- ✅ **Ahorro de Tiempo**: No más conciliación manual
- ✅ **Precisión Alta**: Algoritmos inteligentes de matching
- ✅ **Interfaz Intuitiva**: Subida de CSV con drag & drop
- ✅ **Revisión Manual**: Solo para casos que lo requieren

##### Para la Contabilidad
- ✅ **Automatización Total**: Conciliación sin intervención manual
- ✅ **Trazabilidad Completa**: Logs detallados de todas las operaciones
- ✅ **Exportación**: Datos listos para sistemas contables
- ✅ **Auditoría**: Registro completo de todas las operaciones

##### Para el Negocio
- ✅ **Eficiencia**: Procesamiento automático 24/7
- ✅ **Reducción de Errores**: Algoritmos precisos de matching
- ✅ **Escalabilidad**: Maneja grandes volúmenes de transacciones
- ✅ **Flexibilidad**: Configuración por hotel y moneda

#### 🎯 Mejoras Implementadas (v2.3)

##### Flujo de Transferencias Mejorado
- **Problema Resuelto**: Antes, cuando un huésped subía un comprobante de transferencia, la reserva se confirmaba inmediatamente, sin verificar que el dinero realmente llegara al banco
- **Nueva Solución**: 
  - ✅ **Mayor Seguridad**: Las transferencias ahora quedan en "Pendiente de Confirmación"
  - ✅ **Verificación Real**: Solo se confirman cuando el dinero aparece en el extracto bancario
  - ✅ **Proceso Automático**: La conciliación bancaria confirma automáticamente las reservas

##### Matching Inteligente Expandido
- **Nuevo**: Ahora el sistema puede encontrar reservas pendientes directamente
- **Criterios Mejorados**:
  - ✅ **Monto Exacto**: Busca reservas con el mismo monto
  - ✅ **Fechas Coincidentes**: Compara fechas de transacción con fechas de reserva
  - ✅ **Nombres de Huéspedes**: Identifica transferencias por nombre en la descripción
- **Tipos de Confianza**:
  - 🟢 **Exacto (100%)**: Monto y fecha coinciden perfectamente
  - 🟡 **Aproximado (70-99%)**: Pequeñas diferencias pero muy probable
  - 🟠 **Parcial (50-69%)**: Posible coincidencia, requiere revisión

##### Interfaz Mejorada
- **Estados Visuales**: Los colores de los badges ahora funcionan correctamente
  - 🟡 **Pendiente**: Amarillo para procesos en espera
  - 🔵 **Procesando**: Azul para operaciones en curso
  - 🟢 **Completada**: Verde para operaciones exitosas
  - 🔴 **Fallida**: Rojo para errores
- **Notificaciones Unificadas**: Mensajes de éxito y error consistentes en toda la aplicación

### 🚀 Mejoras del Sistema de Pagos (v2.1)

#### ¿Qué son las mejoras?
Son funcionalidades avanzadas que hacen que el sistema de pagos sea más robusto, confiable y fácil de mantener.

#### ¿Por qué son importantes?
- **Evitan errores costosos**: Prevención de pagos duplicados
- **Facilitan el debugging**: Rastreo completo de operaciones
- **Permiten testing seguro**: Simulación de errores sin costos reales

### 🔒 Sistema de Webhooks Mejorado (v2.0)

#### ¿Qué es un webhook?
Un webhook es como un "mensajero automático" que Mercado Pago envía a nuestro sistema cuando ocurre algo importante con un pago (aprobado, rechazado, etc.).

#### ¿Por qué es importante?
- **Confirmación automática**: Los pagos se confirman sin intervención manual
- **Seguridad garantizada**: Solo Mercado Pago puede enviar notificaciones válidas
- **Prevención de duplicados**: El sistema evita procesar la misma notificación dos veces
- **Procesamiento rápido**: Las notificaciones se procesan en segundos

#### ¿Cómo funciona?

##### 1. Seguridad Avanzada
- **Verificación de identidad**: Cada notificación viene con una "firma digital" que solo Mercado Pago puede generar
- **Validación automática**: El sistema verifica que la notificación sea realmente de Mercado Pago
- **Rechazo de falsificaciones**: Cualquier notificación sin firma válida es rechazada automáticamente

##### 2. Prevención de Duplicados
- **Control inteligente**: El sistema recuerda qué notificaciones ya procesó
- **Evita reprocesamiento**: Si llega la misma notificación dos veces, solo se procesa una vez
- **Ahorro de recursos**: No se desperdician recursos procesando lo mismo repetidamente

##### 3. Procesamiento Atómico
- **Todo o nada**: Si algo falla durante el procesamiento, se revierte todo automáticamente
- **Consistencia garantizada**: Los datos siempre quedan en un estado válido
- **Sin pérdida de información**: Si hay un error, no se pierden datos importantes

##### 4. Post-procesamiento Inteligente
- **Notificaciones automáticas**: El sistema notifica a usuarios y personal sobre cambios importantes
- **Auditoría completa**: Se registra todo lo que pasa para futuras consultas
- **Procesamiento en segundo plano**: Las tareas pesadas no bloquean la confirmación del pago

#### Beneficios para el Hotel

##### Seguridad
- **Protección contra fraudes**: Solo notificaciones auténticas de Mercado Pago son procesadas
- **Auditoría completa**: Registro detallado de todas las operaciones para cumplimiento
- **Prevención de errores**: El sistema evita procesar la misma notificación múltiples veces

##### Eficiencia
- **Confirmación automática**: Los pagos se confirman sin intervención manual
- **Procesamiento rápido**: Las notificaciones se procesan en segundos
- **Notificaciones automáticas**: El personal recibe alertas inmediatas sobre pagos importantes

##### Confiabilidad
- **Manejo de errores**: Si algo falla, el sistema se recupera automáticamente
- **Consistencia de datos**: Los datos siempre quedan en un estado válido
- **Monitoreo continuo**: El sistema registra todo para facilitar el debugging

#### Beneficios para el Personal

##### Visibilidad
- **Notificaciones inmediatas**: Reciben alertas en tiempo real sobre pagos procesados
- **Información detallada**: Cada notificación incluye todos los detalles relevantes
- **Historial completo**: Pueden consultar el historial de todas las operaciones

##### Simplicidad
- **Procesamiento automático**: No necesitan intervenir manualmente en la mayoría de casos
- **Interfaz clara**: Las notificaciones son fáciles de entender y actuar
- **Resolución rápida**: Si hay problemas, el sistema proporciona información clara para resolverlos

#### Beneficios para los Huéspedes

##### Experiencia Mejorada
- **Confirmación inmediata**: Sus pagos se confirman automáticamente
- **Notificaciones claras**: Reciben información clara sobre el estado de sus pagos
- **Procesamiento confiable**: Pueden confiar en que sus pagos se procesarán correctamente

##### Transparencia
- **Estado actualizado**: Siempre saben el estado actual de sus pagos
- **Información detallada**: Reciben todos los detalles relevantes sobre sus transacciones
- **Soporte eficiente**: Si hay problemas, el personal puede resolverlos rápidamente

#### Casos de Uso Reales

##### Caso 1: Pago Aprobado
```
1. Huésped completa pago con tarjeta
2. Mercado Pago procesa el pago exitosamente
3. Mercado Pago envía webhook a AlojaSys
4. AlojaSys verifica la firma del webhook
5. AlojaSys confirma que no es duplicado
6. AlojaSys actualiza el estado del pago
7. AlojaSys notifica al personal y huésped
8. La reserva se confirma automáticamente
```

##### Caso 2: Pago Rechazado
```
1. Huésped intenta pagar con tarjeta
2. Mercado Pago rechaza el pago
3. Mercado Pago envía webhook a AlojaSys
4. AlojaSys verifica la firma del webhook
5. AlojaSys actualiza el estado del pago
6. AlojaSys notifica al personal sobre el rechazo
7. El personal puede contactar al huésped para resolver
```

##### Caso 3: Notificación Duplicada
```
1. Mercado Pago envía webhook por pago aprobado
2. AlojaSys procesa la notificación exitosamente
3. Mercado Pago envía la misma notificación otra vez
4. AlojaSys detecta que ya fue procesada
5. AlojaSys responde "ya procesada" sin hacer nada más
6. Se evita procesamiento duplicado y errores
```

#### Configuración Técnica

##### Variables de Entorno
```bash
# Secreto para verificar webhooks de Mercado Pago
MERCADO_PAGO_WEBHOOK_SECRET=tu_secreto_aqui

# Token de acceso de Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=tu_token_aqui

# URL de Redis para control de duplicados
REDIS_URL=redis://localhost:6379/0
```

##### Configuración por Hotel
- **Webhook Secret**: Cada hotel puede tener su propio secreto
- **Modo Producción**: Configuración separada para producción
- **Validaciones**: El sistema valida la configuración automáticamente

#### Monitoreo y Alertas

##### Eventos Registrados
- **Webhook recibido**: Cada vez que llega una notificación
- **Firma verificada**: Cuando se valida la autenticidad
- **Duplicado detectado**: Cuando se evita procesamiento duplicado
- **Pago procesado**: Cuando se actualiza el estado del pago
- **Error detectado**: Cuando algo falla en el procesamiento

##### Métricas Importantes
- **Tiempo de procesamiento**: Qué tan rápido se procesan las notificaciones
- **Tasa de éxito**: Qué porcentaje de webhooks se procesan correctamente
- **Tasa de duplicados**: Qué porcentaje de notificaciones son duplicadas
- **Tasa de errores**: Qué porcentaje de webhooks fallan

#### Resolución de Problemas

##### Problema: Webhook no se procesa
**Posibles causas:**
- Firma HMAC inválida
- Configuración incorrecta del webhook secret
- Error en la configuración de Mercado Pago

**Solución:**
1. Verificar la configuración del webhook secret
2. Revisar los logs del sistema para ver el error específico
3. Contactar a Mercado Pago si el problema persiste

##### Problema: Pago duplicado
**Posibles causas:**
- Mercado Pago envió la notificación múltiples veces
- Error en la configuración de Redis

**Solución:**
1. El sistema ya previene esto automáticamente
2. Verificar que Redis esté funcionando correctamente
3. Revisar los logs para confirmar que se detectó el duplicado

##### Problema: Notificación no llega
**Posibles causas:**
- Problema de conectividad con Mercado Pago
- Configuración incorrecta de la URL del webhook
- Firewall bloqueando las notificaciones

**Solución:**
1. Verificar la conectividad con Mercado Pago
2. Revisar la configuración de la URL del webhook
3. Verificar que el firewall permita las notificaciones

#### ¿Cómo funcionan?

##### 🔑 Prevención de Duplicados (Idempotencia)
```
Problema: Si hay un error de red, el sistema podría enviar el mismo pago dos veces
Solución: Cada operación tiene una "huella digital" única
Resultado: Nunca se procesa el mismo pago dos veces
```

##### 📊 Rastreo Completo (Trace ID)
```
Problema: Es difícil saber qué pasó con una operación específica
Solución: Cada operación tiene un "número de seguimiento" único
Resultado: Puedes rastrear cualquier operación desde el inicio hasta el final
```

##### 🧪 Testing Seguro
```
Problema: Probar errores reales cuesta dinero y puede causar problemas
Solución: El sistema puede simular errores sin hacer operaciones reales
Resultado: Puedes probar todos los escenarios sin riesgo
```

#### Beneficios para tu Hotel

##### Para el Personal
- **Menos errores**: El sistema previene pagos duplicados automáticamente
- **Debugging fácil**: Si algo falla, puedes rastrear exactamente qué pasó
- **Testing seguro**: Puedes probar el sistema sin hacer operaciones reales

##### Para el Negocio
- **Ahorro de dinero**: No hay pagos duplicados accidentales
- **Mayor confianza**: El sistema es más confiable y predecible
- **Menos problemas**: Menos tiempo perdido resolviendo errores

##### Para el Desarrollo
- **Mantenimiento fácil**: Los logs son claros y organizados
- **Testing completo**: Se pueden probar todos los escenarios
- **Escalabilidad**: El sistema puede manejar más operaciones simultáneas

#### Ejemplos Prácticos

##### Caso 1: Error de Red
```
Situación: Se pierde la conexión justo después de enviar un pago
Sin mejoras: Podría procesarse dos veces el mismo pago
Con mejoras: El sistema detecta que ya se procesó y no lo repite
```

##### Caso 2: Debugging de Problemas
```
Situación: Un huésped dice que se le cobró dos veces
Sin mejoras: Es difícil encontrar qué pasó
Con mejoras: Puedes buscar por "trace_id" y ver toda la historia
```

##### Caso 3: Testing de Nuevas Funcionalidades
```
Situación: Quieres probar qué pasa si MercadoPago falla
Sin mejoras: Tendrías que hacer operaciones reales que fallan
Con mejoras: Simulas el error sin hacer operaciones reales
```

----

## 3.4.1 Sistema de Vouchers de Crédito

### ¿Qué hace?
Permite generar vouchers de crédito como alternativa a los reembolsos en dinero, facilitando la retención de clientes y mejorando el flujo de caja del hotel.

### ¿Cómo funciona?

#### Generación de Vouchers
Cuando un cliente cancela una reserva y tiene derecho a reembolso, puede elegir entre:

##### Opción 1: Reembolso en Dinero
```
Cliente cancela reserva → Sistema calcula reembolso → Dinero devuelto al método de pago original
```

##### Opción 2: Voucher de Crédito
```
Cliente cancela reserva → Sistema calcula reembolso → Se genera voucher con código único → Cliente recibe código
```

#### Características del Voucher
- **Código único**: Formato VCH-2025-00001
- **Monto**: Igual al reembolso calculado
- **Vencimiento**: 6 meses por defecto (configurable)
- **Estado**: Activo, Usado, Expirado, Cancelado
- **Reutilizable**: Se puede usar en futuras reservas

#### Ejemplo Práctico
```
Reserva cancelada: $150,000
Cliente elige: Voucher de crédito
Sistema genera: VCH-2025-00045
Monto: $150,000
Vencimiento: 15 de abril de 2025
Estado: Activo
```

### Aplicación de Vouchers en Nuevas Reservas

#### Proceso de Aplicación
1. **Cliente inicia nueva reserva**
2. **Ingresa código de voucher** en el campo correspondiente
3. **Sistema valida voucher** (activo, no expirado, monto suficiente)
4. **Sistema aplica descuento** al total de la reserva
5. **Cliente completa reserva** con el descuento aplicado

#### Ejemplo de Aplicación
```
Nueva reserva: $200,000
Voucher aplicado: VCH-2025-00045 ($150,000)
Descuento aplicado: $150,000
Total a pagar: $50,000
Voucher queda: Usado
```

### Gestión de Vouchers

#### Para el Personal del Hotel
- **Ver todos los vouchers** generados y su estado
- **Crear vouchers manuales** para compensaciones especiales
- **Cancelar vouchers** si es necesario
- **Ver historial de uso** de cada voucher
- **Filtrar por estado** (activos, usados, expirados)

#### Para el Cliente
- **Recibir código** por email o en la plataforma
- **Usar código** en futuras reservas
- **Ver estado** del voucher (activo, usado, expirado)
- **Conocer fecha de vencimiento**

### Beneficios del Sistema de Vouchers

#### Para el Hotel
- ✅ **Mejora el flujo de caja** - No devuelve dinero inmediatamente
- ✅ **Retiene clientes** - Los incentiva a volver
- ✅ **Reduce costos** - No hay comisiones de reembolso
- ✅ **Flexibilidad** - Puede crear vouchers manuales
- ✅ **Control total** - Gestiona cuándo y cómo se usan

#### Para el Cliente
- ✅ **Facilidad de uso** - Código simple de aplicar
- ✅ **Sin pérdida de dinero** - Crédito garantizado
- ✅ **Flexibilidad** - Puede usarlo cuando quiera
- ✅ **Transparencia** - Ve el estado y vencimiento
- ✅ **Sin comisiones** - No paga extra por usar el voucher

### Casos de Uso Reales

#### Caso 1: Cancelación por Emergencia
```
Situación: Cliente cancela por emergencia familiar
Reembolso calculado: $80,000
Cliente elige: Voucher de crédito
Resultado: Voucher VCH-2025-00012 por $80,000
Cliente usa: 2 meses después en nueva reserva de $120,000
Paga: Solo $40,000 (diferencia)
```

#### Caso 2: Compensación por Problema
```
Situación: Hotel tiene problema con la habitación
Compensación: Voucher manual por $50,000
Staff crea: Voucher VCH-2025-00025
Cliente usa: En su próxima reserva
Resultado: Cliente satisfecho, hotel retiene cliente
```

#### Caso 3: Promoción Especial
```
Situación: Hotel quiere incentivar reservas
Promoción: Voucher de $30,000 para nuevas reservas
Staff crea: Múltiples vouchers
Clientes usan: En sus reservas
Resultado: Incremento en reservas, clientes felices
```

### Integración con Otros Sistemas

#### Con Promociones
- **Coexistencia**: Vouchers y promociones pueden usarse juntos
- **Aplicación**: Primero promociones, luego vouchers
- **Flexibilidad**: Cliente puede usar ambos descuentos

#### Con Políticas de Cancelación
- **Automático**: Vouchers se generan según políticas
- **Configurable**: Cada hotel puede habilitar/deshabilitar
- **Consistente**: Misma lógica que reembolsos en dinero

#### Con Sistema de Pagos
- **Alternativa**: Voucher como método de reembolso
- **Integrado**: Se procesa igual que otros reembolsos
- **Trazable**: Historial completo de generación y uso

### Configuración por Hotel

#### Parámetros Configurables
- **Habilitar vouchers**: Sí/No
- **Días de vencimiento**: Por defecto 180 días
- **Monto mínimo**: Para generar voucher
- **Método por defecto**: Dinero o voucher
- **Mensajes personalizados**: Para el cliente

#### Ejemplo de Configuración
```
Hotel: "Hotel Plaza Central"
Vouchers habilitados: Sí
Días de vencimiento: 180
Monto mínimo: $10,000
Método por defecto: Voucher
Mensaje: "Su voucher de crédito estará listo en 24 horas"
```

---

### Sistema de Recibos Automáticos

#### ¿Qué hace?
Genera automáticamente recibos profesionales en PDF y los envía por email a los huéspedes cada vez que se procesa un pago o reembolso.

#### ¿Cómo funciona?

##### Generación Automática
- **Sin intervención manual**: Los recibos se generan automáticamente
- **Diseño profesional**: Incluye logo del hotel y información completa
- **Envío inmediato**: El huésped recibe el recibo por email al instante
- **Formato PDF**: Fácil de imprimir y guardar digitalmente

##### Cuándo se Generan Recibos
- ✅ **Pagos en efectivo**: Al confirmar una reserva
- ✅ **Pagos con tarjeta**: Al procesar el pago
- ✅ **Transferencias**: Al registrar el pago manual
- ✅ **Reembolsos**: Al procesar cualquier devolución
- ✅ **Vouchers**: Al generar vouchers de crédito

##### Información Incluida en el Recibo
- **Logo del hotel** (si está configurado)
- **Datos del hotel**: Nombre, dirección, teléfono, email, RUT
- **Fecha y hora de emisión** automática
- **Código de reserva** único
- **Monto del pago/reembolso**
- **Método de pago** utilizado
- **Datos del huésped** principal
- **Sello fiscal interno** de AlojaSys

#### Configuración para el Hotel

##### Logo del Hotel
- **Subir logo**: En la configuración del hotel
- **Formatos soportados**: JPG, PNG, GIF
- **Tamaño recomendado**: 200x200 píxeles
- **Ubicación**: Aparece en el encabezado del recibo

##### Información del Hotel
- **Datos obligatorios**: Nombre, email
- **Datos opcionales**: Dirección, teléfono, RUT/CUIT
- **Configuración**: Se completa en "Gestión de Hoteles"

##### Configuración de Email
- **Proveedor recomendado**: Resend (configuración automática)
- **Email de envío**: AlojaSys (global)
- **Reply-to**: Email específico del hotel
- **Configuración**: Se hace una sola vez por hotel

#### Ejemplo de Recibo Generado

```
┌─────────────────────────────────────────────────────────┐
│                    [LOGO HOTEL]                        │
│                 RECIBO DE PAGO                         │
│                                                         │
│ Hotel Plaza Central                                     │
│ Av. Corrientes 1234, Buenos Aires                      │
│ Tel: +54 11 1234-5678                                  │
│ Email: info@hotelplaza.com                             │
│ RUT: 30-12345678-9                                     │
│                                                         │
│ Fecha de emisión: 22/10/2025 a las 15:30:45           │
│ ─────────────────────────────────────────────────────── │
│                                                         │
│ INFORMACIÓN DEL PAGO                                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Código de Reserva:    RES-12345                    │ │
│ │ ID de Pago:           67                           │ │
│ │ Monto:                $45,000.00                   │ │
│ │ Método de Pago:       Efectivo                     │ │
│ │ Fecha:                22/10/2025 15:30:45         │ │
│ │ Huésped:              Juan Pérez                   │ │
│ │ Email:                juan.perez@email.com         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│                                                         │
│ Recibo generado automáticamente por AlojaSys           │
│ (sin validez fiscal)                                   │
│                                                         │
│ AlojaSys                    Generado el: 22/10/2025   │
│ Sistema de Gestión Hotelera   15:30:45                 │
└─────────────────────────────────────────────────────────┘
```

#### Beneficios para el Hotel

##### Automatización Completa
- **Sin trabajo manual**: Los recibos se generan solos
- **Consistencia**: Todos los recibos tienen el mismo formato profesional
- **Velocidad**: El huésped recibe el recibo al instante
- **Profesionalismo**: Imagen corporativa mejorada

##### Ahorro de Tiempo
- **No imprimir**: Los huéspedes reciben el recibo por email
- **No archivar**: Los PDFs se guardan automáticamente
- **No buscar**: Historial digital completo de todos los recibos

##### Mejor Experiencia del Huésped
- **Recibo inmediato**: No hay que esperar ni pedir
- **Formato digital**: Fácil de guardar y compartir
- **Información completa**: Todos los datos necesarios
- **Profesional**: Diseño limpio y claro

#### Configuración Técnica (Para Administradores)

##### Variables de Entorno
```bash
# Archivo: backend/.env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=TU_API_KEY_DE_RESEND
DEFAULT_FROM_EMAIL=AlojaSys <noreply@aloja.com>
```

##### Pasos de Configuración
1. **Crear cuenta en Resend**: Obtener API key
2. **Configurar variables**: Agregar al archivo .env
3. **Subir logo**: En configuración del hotel
4. **Completar datos**: Información del hotel
5. **Probar sistema**: Hacer un pago de prueba

##### Monitoreo del Sistema
- **Logs automáticos**: Se registran todos los envíos
- **Alertas de error**: Si algo falla, se notifica
- **Estadísticas**: Cantidad de recibos generados
- **Historial**: Todos los PDFs se guardan en /media/receipts/

#### Casos de Uso Reales

##### Caso 1: Check-in con Pago en Efectivo
```
1. Huésped llega al hotel
2. Personal registra pago en efectivo
3. Sistema genera PDF automáticamente
4. Huésped recibe recibo por email
5. Recibo se guarda en sistema
```

##### Caso 2: Cancelación con Reembolso
```
1. Huésped cancela reserva
2. Sistema procesa reembolso
3. PDF de reembolso se genera
4. Huésped recibe comprobante por email
5. Hotel tiene registro completo
```

##### Caso 3: Pago con Tarjeta
```
1. Huésped paga con tarjeta online
2. Mercado Pago confirma pago
3. Sistema genera recibo automáticamente
4. Email se envía al huésped
5. Recibo queda registrado
```

#### Solución de Problemas Comunes

##### El huésped no recibe el email
- **Verificar email**: Revisar que el email esté correcto en la reserva
- **Revisar spam**: El email puede estar en carpeta de spam
- **Verificar configuración**: Revisar variables de email
- **Reintentar**: El sistema reintenta automáticamente

##### El PDF no se genera
- **Verificar logs**: Revisar logs de Celery
- **Verificar permisos**: Revisar permisos de escritura en /media/
- **Verificar datos**: Revisar que todos los datos estén completos
- **Reiniciar servicios**: Reiniciar Celery si es necesario

##### El logo no aparece
- **Verificar archivo**: Revisar que el logo esté subido
- **Verificar formato**: Usar JPG, PNG o GIF
- **Verificar tamaño**: Máximo 2MB
- **Verificar permisos**: Revisar permisos de lectura

----

## 3.5 Políticas de Cancelación

### ¿Qué hace?
Permite configurar reglas flexibles de cancelación para cada hotel, definiendo cuándo se puede cancelar una reserva y qué penalidades aplican.

### ¿Cómo funciona?

**IMPORTANTE**: El sistema calcula las políticas de cancelación basándose en el tiempo restante hasta la **fecha de check-in**, NO desde la fecha de creación de la reserva. Esto significa que si reservas hoy para dentro de 7 días, puedes cancelar gratuitamente si tu política lo permite.

#### Configuración de Tiempos de Cancelación

Los tiempos deben configurarse en orden **descendente** (de mayor a menor tiempo antes del check-in):

```
Cancelación Gratuita > Cancelación Parcial > Sin Cancelación
```

**Ejemplo de configuración correcta**:
```
- Cancelación Gratuita: 72 horas (3 días) antes del check-in
- Cancelación Parcial: 24 horas (1 día) antes del check-in  
- Sin Cancelación: 24 horas (1 día) antes del check-in
```

Esto significa:
- **Si cancelas con 72 horas o más de anticipación**: Cancelación gratuita ✅
- **Si cancelas entre 24 y 72 horas antes**: Cancelación parcial (con penalidad) ⚠️
- **Si cancelas con menos de 24 horas**: Sin cancelación ❌

##### Cancelación Gratuita
```
Política: "Cancelación sin penalidad"
Tiempo: 72 horas (3 días) antes del check-in
Aplicación: Todas las habitaciones
Resultado: Cliente puede cancelar sin costo adicional y recibe reembolso completo
```

**Ejemplo práctico**:
```
- Reserva creada: 1 de noviembre
- Check-in: 15 de noviembre (14 días después)
- Cancelación: 12 de noviembre (3 días antes del check-in)
- Resultado: ✅ Cancelación gratuita, reembolso completo
```

##### Cancelación Parcial
```
Política: "Cancelación con penalidad"
Tiempo: 24 horas (1 día) antes del check-in
Penalidad: 50% del total de la reserva
Aplicación: Todas las habitaciones
Resultado: Cliente paga 50% como penalidad, recibe 50% de reembolso
```

**Ejemplo práctico**:
```
- Reserva creada: 1 de noviembre
- Check-in: 15 de noviembre
- Cancelación: 14 de noviembre (1 día antes del check-in)
- Total pagado: $100,000
- Penalidad: $50,000 (50%)
- Reembolso: $50,000 (50%)
- Resultado: ⚠️ Cancelación parcial, reembolso del 50%
```

##### Sin Cancelación
```
Política: "No se permite cancelación"
Tiempo: 24 horas (1 día) antes del check-in
Aplicación: Todas las habitaciones
Resultado: No se puede cancelar la reserva, no hay reembolso
```

**Ejemplo práctico**:
```
- Reserva creada: 1 de noviembre
- Check-in: 15 de noviembre
- Cancelación: 15 de noviembre (mismo día del check-in)
- Resultado: ❌ Sin cancelación, no hay reembolso
```

#### ¿Cómo se Calcula el Tiempo?

El sistema calcula el tiempo desde **hoy** hasta la **fecha de check-in**:

```
Tiempo hasta check-in = Fecha de check-in - Fecha actual
```

**Ejemplos**:
- Si hoy es 12 de noviembre y el check-in es 15 de noviembre: **3 días = 72 horas** ✅ Cancelación gratuita
- Si hoy es 14 de noviembre y el check-in es 15 de noviembre: **1 día = 24 horas** ⚠️ Cancelación parcial
- Si hoy es 15 de noviembre y el check-in es 15 de noviembre: **0 días = 0 horas** ❌ Sin cancelación

#### Tipos de Penalidades

##### Porcentaje del Total
```
Ejemplo:
- Total de reserva: $100,000
- Penalidad: 25%
- Monto a pagar: $25,000
- Devolución: $75,000
```

##### Monto Fijo
```
Ejemplo:
- Total de reserva: $100,000
- Penalidad fija: $20,000
- Monto a pagar: $20,000
- Devolución: $80,000
```

##### Por Número de Noches
```
Ejemplo:
- Total de reserva: $100,000 (4 noches)
- Penalidad: 1 noche
- Monto a pagar: $25,000
- Devolución: $75,000
```

#### Configuración Avanzada

##### Por Tipo de Habitación
```
Configuración:
- Singles: Cancelación gratuita hasta 24h
- Dobles: Cancelación parcial hasta 48h
- Suites: Sin cancelación después de 7 días
```

##### Por Canal de Reserva
```
Configuración:
- Directo: Cancelación gratuita hasta 24h
- Booking.com: Cancelación parcial hasta 48h
- Expedia: Sin cancelación después de 72h
```

##### Por Temporada
```
Configuración:
- Temporada baja: Cancelación gratuita hasta 24h
- Temporada media: Cancelación parcial hasta 48h
- Temporada alta: Sin cancelación después de 7 días
```

#### Mensajes Personalizados

##### Para Cancelación Gratuita
```
"Puedes cancelar tu reserva sin costo adicional hasta 24 horas antes de tu llegada. Después de ese tiempo, se aplicará una penalidad del 50%."
```

##### Para Cancelación Parcial
```
"Cancelación con penalidad: Se cobrará el 50% del total de la reserva como penalidad por cancelación tardía."
```

##### Para Sin Cancelación
```
"No se permite cancelación después de 7 días antes de la llegada. La reserva es no reembolsable."
```

### Snapshot de Políticas de Cancelación

#### ¿Qué es el Snapshot?
El **Snapshot de Políticas de Cancelación** es como tomar una "fotografía" de las reglas de cancelación exactas que estaban vigentes cuando se confirmó tu reserva. Es como tener un contrato que no puede cambiar, sin importar si el hotel modifica sus políticas después.

#### ¿Por qué es Importante?
Imagina que reservas una habitación con la política "Cancelación gratuita hasta 24 horas antes", pero después el hotel cambia a "Cancelación gratuita hasta 48 horas antes". Sin el snapshot, tu reserva se vería afectada por el cambio. **¡Con el snapshot, tus reglas originales están garantizadas!** 📸

#### ¿Cómo Funciona?

##### Captura Automática
```
Proceso automático:
1. Cliente confirma reserva
2. Sistema "fotografía" la política vigente
3. Guarda snapshot en la reserva
4. Política queda inmutable para esa reserva
```

##### Estructura del Snapshot
```
Información guardada:
- Nombre de la política
- Tiempos de cancelación (gratuita, parcial, sin cancelación)
- Porcentajes de penalidad
- Tipos de penalidad (porcentaje, monto fijo, por noches)
- Configuraciones especiales
- Fecha de captura
```

#### Ejemplos Prácticos

##### Ejemplo 1: Protección contra Cambios
```
Situación:
- Reserva confirmada: 15/01/2024
- Política vigente: "24h gratuita"
- Hotel cambia política: 20/01/2024 a "48h gratuita"
- Cliente cancela: 22/01/2024 (30 horas antes)

Resultado:
- Sistema usa snapshot (24h gratuita)
- Cliente: Cancelación gratuita ✅
- Sin snapshot: Penalidad del 50% ❌
```

##### Ejemplo 2: Auditoría Transparente
```
Situación:
- Cliente reclama penalidad incorrecta
- Sistema consulta snapshot de la reserva
- Muestra política exacta vigente al confirmar
- Resolución transparente del reclamo

Beneficio:
- Transparencia total
- Resolución rápida de disputas
- Confianza del cliente
```

##### Ejemplo 3: Consistencia Legal
```
Situación:
- Hotel debe cumplir regulaciones
- Cada reserva tiene su política histórica
- Auditoría completa de transacciones
- Cumplimiento regulatorio facilitado

Beneficio:
- Cumplimiento legal
- Auditoría profesional
- Protección legal del hotel
```

#### Beneficios para el Hotel

##### Protección Legal
- **Cumplimiento regulatorio**: Cada reserva mantiene su política original
- **Auditoría completa**: Registro histórico de todas las políticas aplicadas
- **Transparencia**: Clientes pueden ver exactamente qué reglas se aplicaron

##### Gestión Profesional
- **Consistencia**: Todas las reservas se procesan con sus reglas originales
- **Confianza**: Clientes saben que sus reglas no cambiarán
- **Menos disputas**: Políticas claras y documentadas

##### Flexibilidad Operativa
- **Cambios futuros**: Puedes modificar políticas sin afectar reservas existentes
- **Políticas diferenciadas**: Diferentes reglas para diferentes períodos
- **Evolución del negocio**: Adaptación sin impacto en reservas confirmadas

#### Beneficios para el Cliente

##### Transparencia Total
- **Reglas claras**: Sabes exactamente qué reglas se aplican a tu reserva
- **Sin sorpresas**: Las reglas no cambian después de confirmar
- **Confianza**: Puedes confiar en que las reglas se respetarán

##### Resolución de Disputas
- **Evidencia clara**: Snapshot como prueba de las reglas aplicadas
- **Resolución rápida**: Menos tiempo en disputas sobre penalidades
- **Satisfacción**: Proceso justo y transparente

#### Casos de Uso Reales

##### Caso 1: Hotel que Cambia Políticas por Temporada
```
Situación:
- Temporada baja: 24h gratuita
- Temporada alta: 48h gratuita
- Reserva en temporada baja, cancelación en temporada alta

Resultado:
- Snapshot mantiene reglas de temporada baja
- Cliente se beneficia de reglas más flexibles
- Hotel mantiene consistencia contractual
```

##### Caso 2: Hotel que Mejora Políticas
```
Situación:
- Política antigua: 24h gratuita
- Política nueva: 48h gratuita
- Reserva antigua con política nueva

Resultado:
- Snapshot mantiene política antigua
- Cliente no se ve afectado por mejora
- Hotel puede mejorar políticas gradualmente
```

##### Caso 3: Auditoría Regulatoria
```
Situación:
- Autoridades requieren auditoría
- Necesidad de mostrar políticas aplicadas
- Cumplimiento de regulaciones

Resultado:
- Snapshot proporciona evidencia clara
- Auditoría completa y transparente
- Cumplimiento regulatorio facilitado
```

### Flujo de Cancelación

#### 1. Usuario Solicita Cancelación
```
Proceso:
1. Usuario hace clic en "Cancelar" en su reserva
2. Sistema evalúa la política de cancelación
3. Sistema calcula tiempo hasta check-in
4. Sistema determina tipo de cancelación aplicable
```

#### 2. Sistema Muestra Opciones
```
Modal de cancelación muestra:
- Tipo de cancelación (gratuita/parcial/sin cancelación)
- Monto de penalidad (si aplica)
- Monto de devolución (si aplica)
- Mensaje personalizado de la política
- Resumen financiero final
```

#### 3. Usuario Confirma Cancelación
```
Proceso:
1. Usuario revisa las consecuencias
2. Usuario confirma la cancelación
3. Sistema procesa devolución automáticamente
4. Sistema actualiza estado de reserva
5. Sistema libera habitación automáticamente
6. Sistema envía confirmación con detalles de devolución
```

#### 4. Procesamiento Automático de Devoluciones
```
Proceso automático:
1. Sistema calcula total pagado de la reserva
2. Sistema aplica penalidad según política de cancelación histórica
3. Sistema calcula monto de devolución según política de devolución
4. Sistema procesa devolución por método de pago original
5. Sistema crea registro de pago negativo para devolución
6. Sistema registra log detallado con información financiera
```

#### 5. Registro Histórico de Políticas
```
Garantía de consistencia:
1. Al crear reserva se asigna automáticamente la política vigente
2. Campo "applied_cancellation_policy" mantiene referencia histórica
3. Cancelaciones siempre usan la política que estaba vigente al crear la reserva
4. Consistencia garantizada independientemente de cambios posteriores en políticas
```

### Beneficios

#### Para el Hotel
- ✅ **Control total** sobre políticas de cancelación
- ✅ **Protección de ingresos** con penalidades configurables
- ✅ **Flexibilidad** para diferentes tipos de habitaciones
- ✅ **Adaptación** a temporadas y canales
- ✅ **Transparencia** con mensajes claros
- ✅ **Devoluciones automáticas** sin intervención manual
- ✅ **Liberación automática** de habitaciones canceladas
- ✅ **Auditoría completa** de transacciones financieras
- ✅ **Registro histórico** de políticas aplicadas
- ✅ **Consistencia garantizada** en cancelaciones
- ✅ **Flujo financiero claro** con reembolsos explícitos
- ✅ **Trazabilidad completa** de devoluciones
- ✅ **Gestión automática** de vencimientos de reservas
- ✅ **Liberación automática** de habitaciones vencidas
- ✅ **Protección legal** con políticas históricas inmutables
- ✅ **Cumplimiento regulatorio** facilitado
- ✅ **Transparencia total** para clientes
- ✅ **Menos disputas** por políticas claras

#### Para el Huésped
- ✅ **Transparencia** sobre reglas de cancelación
- ✅ **Información clara** sobre penalidades
- ✅ **Proceso simple** de cancelación
- ✅ **Conocimiento previo** de consecuencias
- ✅ **Devoluciones automáticas** por método de pago original
- ✅ **Confirmación inmediata** de devolución procesada
- ✅ **Tiempos de procesamiento** claros y transparentes
- ✅ **Políticas consistentes** según lo acordado al reservar
- ✅ **Seguimiento detallado** del estado de reembolsos
- ✅ **Transparencia total** en el flujo financiero
- ✅ **Tiempos claros** para pago de adelantos
- ✅ **Notificaciones automáticas** de vencimientos
- ✅ **Protección contra cambios** en políticas
- ✅ **Reglas inmutables** una vez confirmada la reserva
- ✅ **Resolución transparente** de disputas
- ✅ **Confianza total** en el proceso

#### Para el Personal
- ✅ **Proceso automatizado** de evaluación
- ✅ **Cálculos precisos** de penalidades
- ✅ **Información centralizada** de políticas
- ✅ **Menos errores** en cancelaciones
- ✅ **Gestión eficiente** del proceso
- ✅ **Devoluciones automáticas** sin procesamiento manual
- ✅ **Liberación automática** de habitaciones
- ✅ **Logs detallados** para auditoría y seguimiento
- ✅ **Trazabilidad completa** de políticas aplicadas
- ✅ **Consistencia legal** en todas las cancelaciones
- ✅ **Gestión explícita** de reembolsos y devoluciones
- ✅ **Control total** del flujo financiero
- ✅ **Procesamiento automático** de vencimientos
- ✅ **Estadísticas detalladas** de reservas pendientes
- ✅ **Auditoría simplificada** con snapshots históricos
- ✅ **Menos disputas** con clientes
- ✅ **Procesos claros** y documentados

### Casos de Uso Prácticos

#### Caso 1: Hotel Boutique
```
Configuración:
- Cancelación gratuita: 24 horas
- Penalidad: 50% después de 24h
- Aplicación: Todas las habitaciones
- Canal: Solo directo

Resultado:
- Flexibilidad para huéspedes
- Protección de ingresos
- Proceso simple
```

#### Caso 2: Hotel de Temporada
```
Configuración:
- Temporada baja: Cancelación gratuita 24h
- Temporada media: Penalidad 25% hasta 48h
- Temporada alta: Sin cancelación después de 7 días

Resultado:
- Adaptación a demanda
- Maximización de ingresos
- Políticas diferenciadas
```

#### Caso 3: Hotel de Lujo
```
Configuración:
- Suites: Sin cancelación después de 14 días
- Habitaciones estándar: Penalidad 50% hasta 72h
- Promociones: Cancelación gratuita hasta 24h

Resultado:
- Políticas premium para suites
- Flexibilidad para habitaciones estándar
- Incentivos para promociones
```

---

## 3.6 Políticas de Devolución

### ¿Qué hace?
Permite configurar cómo se procesan las devoluciones de dinero cuando se cancela una reserva, definiendo tiempos, métodos y condiciones de reembolso.

### ¿Cómo funciona?

#### Configuración de Tiempos de Devolución

##### Devolución Completa
```
Política: "Devolución del 100%"
Tiempo: 24 horas antes del check-in
Aplicación: Todas las habitaciones
Resultado: Cliente recibe el 100% de su dinero
```

##### Devolución Parcial
```
Política: "Devolución del 50%"
Tiempo: 72 horas antes del check-in
Aplicación: Suites solamente
Resultado: Cliente recibe el 50% de su dinero
```

##### Sin Devolución
```
Política: "No hay devolución"
Tiempo: 168 horas (7 días) antes del check-in
Aplicación: Temporada alta
Resultado: No se devuelve dinero
```

#### Métodos de Devolución

##### Método de Pago Original
```
Ejemplo:
- Cliente pagó con tarjeta de crédito
- Devolución se procesa a la misma tarjeta
- Tiempo de procesamiento: 7 días hábiles
- Sin comisiones adicionales
```

##### Transferencia Bancaria
```
Ejemplo:
- Cliente pagó en efectivo
- Devolución por transferencia bancaria
- Tiempo de procesamiento: 3-5 días hábiles
- Requiere datos bancarios del cliente
```

##### Voucher
```
Ejemplo:
- Cliente cancela reserva
- Se genera voucher por el monto
- Voucher válido por 365 días
- Usable para futuras reservas
```

#### Configuración de Vouchers

##### Vencimiento
```
Configuración:
- Voucher válido por: 365 días
- Monto mínimo: $10,000
- Usable en cualquier habitación
- No transferible
```

##### Mensajes Personalizados
```
Para devolución completa:
"Tu devolución del 100% será procesada en 7 días hábiles por el método de pago original."

Para devolución parcial:
"Tu devolución del 50% será procesada en 7 días hábiles. El 50% restante se retiene como penalidad por cancelación tardía."

Para voucher:
"Se ha generado un voucher por $75,000 válido por 365 días. Puedes usarlo para futuras reservas."
```

### Flujo de Devolución Automática

#### 1. Cancelación de Reserva
```
Proceso:
1. Cliente cancela reserva con motivo
2. Sistema evalúa política de cancelación histórica
3. Sistema calcula penalidad según política
4. Sistema obtiene política de devolución actual
5. Sistema calcula monto de devolución
```

#### 2. Procesamiento de Devolución
```
Proceso automático:
1. Sistema crea registro de reembolso
2. Vincula reembolso al pago original
3. Establece método de devolución
4. Calcula días de procesamiento
5. Registra motivo de cancelación
6. Marca como "Procesando"
```

#### 3. Seguimiento de Estado
```
Estados del reembolso:
- Pendiente: Creado pero no procesado
- Procesando: En proceso de devolución
- Completado: Devuelto exitosamente
- Fallido: Error en la devolución
- Cancelado: Reembolso cancelado
```

#### 4. Gestión de Reembolsos
```
Para el personal:
- Ver lista completa de reembolsos
- Filtrar por estado, método, fecha
- Marcar como completado manualmente
- Ver detalles de cada reembolso
- Seguimiento de procesamiento
- Gestionar vouchers de crédito generados
```

#### 4.1 Gestión de Vouchers de Crédito
```
Para el personal:
- Ver todos los vouchers generados
- Crear vouchers manuales para compensaciones
- Cancelar vouchers si es necesario
- Ver historial de uso de vouchers
- Filtrar por estado (activos, usados, expirados)
- Ver códigos y montos de vouchers
```

#### 4.2 Aplicación de Vouchers en Reservas
```
Para el cliente:
- Ingresar código de voucher en nueva reserva
- Ver descuento aplicado en tiempo real
- Completar reserva con descuento
- Ver estado del voucher usado
```

### Beneficios

#### Para el Hotel
- ✅ **Control total** sobre políticas de devolución
- ✅ **Flexibilidad** en métodos de pago
- ✅ **Transparencia** con tiempos claros
- ✅ **Gestión centralizada** de reembolsos
- ✅ **Trazabilidad completa** de devoluciones
- ✅ **Configuración por hotel** independiente

#### Para el Huésped
- ✅ **Transparencia** sobre tiempos de devolución
- ✅ **Múltiples métodos** de devolución
- ✅ **Seguimiento** del estado del reembolso
- ✅ **Tiempos claros** de procesamiento
- ✅ **Confirmación** automática de devolución
- ✅ **Vouchers** para futuras reservas

#### Para el Personal
- ✅ **Gestión centralizada** de reembolsos
- ✅ **Filtros avanzados** para búsqueda
- ✅ **Actualización de estado** en tiempo real
- ✅ **Información completa** de cada reembolso
- ✅ **Seguimiento** de procesamiento
- ✅ **Notificaciones** automáticas
- ✅ **Trazabilidad completa** de quién procesó cada reembolso
- ✅ **Flexibilidad financiera** para reembolsos sin pago original
- ✅ **Auditoría histórica** de políticas aplicadas
- ✅ **Control granular** de reembolsos automáticos por política
- ✅ **Limitaciones configurables** por pasarela de pago

### Mejoras en la Gestión de Reembolsos (v2.0)

#### Nuevas Funcionalidades
- **Trazabilidad Completa**: Cada reembolso registra quién lo procesó y cuándo
- **Flexibilidad Financiera**: Posibilidad de crear reembolsos sin pago original asociado
- **Auditoría Histórica**: Snapshot de las políticas de cancelación aplicadas en cada reserva
- **Escalabilidad Mejorada**: Soporte para montos más grandes de reembolso
- **Consistencia Garantizada**: Las cancelaciones siempre usan la política vigente al momento de crear la reserva

#### Beneficios para el Negocio
- **Mayor Control**: Trazabilidad completa de todas las transacciones financieras
- **Flexibilidad Operativa**: Manejo de casos especiales y reembolsos manuales
- **Auditoría Profesional**: Registro histórico de políticas aplicadas
- **Escalabilidad**: Preparado para manejar montos más grandes
- **Consistencia Legal**: Políticas históricas garantizadas en cancelaciones

### Control Granular de Reembolsos Automáticos (v2.1)

#### Nuevas Funcionalidades de Control

##### Control por Política de Cancelación
```
Configuración avanzada:
- Política: "Cancelación con Reembolso Automático"
- Opción: "Procesar reembolso automáticamente al cancelar"
- Resultado: Sistema procesa devolución sin intervención manual
- Flexibilidad: Cada política puede tener configuración independiente
```

##### Limitaciones por Pasarela de Pago
```
Configuración de Mercado Pago:
- Días límite para reembolsos: 30 días
- Reembolsos parciales: Permitidos
- Resultado: Sistema respeta limitaciones del proveedor

Configuración de Transferencia Bancaria:
- Días límite para reembolsos: 90 días
- Reembolsos parciales: No permitidos
- Resultado: Restricciones específicas por método
```

#### Casos de Uso Prácticos

##### Caso 1: Hotel con Reembolsos Automáticos
```
Configuración:
- Política de cancelación: Reembolso automático habilitado
- Tiempo: 24 horas antes del check-in
- Resultado: Cliente cancela y recibe reembolso automáticamente
- Beneficio: Proceso sin intervención manual del personal
```

##### Caso 2: Hotel con Control Manual
```
Configuración:
- Política de cancelación: Reembolso manual
- Tiempo: 24 horas antes del check-in
- Resultado: Cliente cancela, personal procesa reembolso manualmente
- Beneficio: Control total del personal sobre cada devolución
```

##### Caso 3: Hotel con Limitaciones de Pasarela
```
Configuración:
- Mercado Pago: 30 días límite, reembolsos parciales permitidos
- Transferencia: 90 días límite, solo reembolsos completos
- Resultado: Sistema respeta automáticamente las limitaciones
- Beneficio: Prevención de errores y cumplimiento con proveedores
```

#### Beneficios para el Negocio

##### Para el Hotel
- ✅ **Control granular** sobre cuándo procesar reembolsos automáticamente
- ✅ **Flexibilidad operativa** para diferentes tipos de políticas
- ✅ **Cumplimiento automático** con limitaciones de pasarelas
- ✅ **Prevención de errores** en configuraciones de reembolsos
- ✅ **Configuración independiente** por hotel y política

##### Para el Personal
- ✅ **Menos trabajo manual** con reembolsos automáticos
- ✅ **Control total** cuando se prefiere procesamiento manual
- ✅ **Validaciones automáticas** de limitaciones de pasarelas
- ✅ **Configuración clara** de restricciones por proveedor
- ✅ **Prevención de errores** en configuraciones

##### Para el Huésped
- ✅ **Procesamiento más rápido** con reembolsos automáticos
- ✅ **Transparencia** sobre limitaciones de tiempo
- ✅ **Consistencia** en el procesamiento de devoluciones
- ✅ **Cumplimiento** con políticas del proveedor de pago

### Procesamiento Avanzado de Reembolsos (v2.2)

#### ¿Qué hace?
Proporciona un sistema robusto y escalable para procesar reembolsos a través de múltiples pasarelas de pago, con validaciones automáticas, reintentos inteligentes y logging completo.

#### ¿Cómo funciona?

##### Adaptadores de Pasarelas de Pago
```
Sistema modular:
- MercadoPago: Integración completa con API
- Transferencia Bancaria: Procesamiento directo
- Efectivo: Gestión manual
- Futuras pasarelas: Fácil integración

Beneficios:
- Mismo código para diferentes proveedores
- Configuración independiente por hotel
- Fácil agregar nuevas pasarelas
```

##### Validaciones Automáticas
```
Validación de ventana de tiempo:
- Sistema verifica días límite configurados
- MercadoPago: 30 días máximo
- Transferencia: 90 días máximo
- Efectivo: Sin límite de tiempo

Validación de reembolsos parciales:
- Sistema respeta configuración de pasarela
- MercadoPago: Permite reembolsos parciales
- Transferencia: Solo reembolsos completos
- Validación automática antes de procesar
```

##### Lógica de Reintentos Inteligente
```
Procesamiento robusto:
- Reintentos automáticos en caso de fallo
- Backoff exponencial (1s, 2s, 4s, 8s...)
- Máximo 3 intentos por defecto
- Logging detallado de cada intento

Ejemplo de procesamiento:
1. Intento 1: Fallo por timeout
2. Espera 1 segundo
3. Intento 2: Fallo por conectividad
4. Espera 2 segundos
5. Intento 3: Éxito
6. Reembolso completado
```

##### Modo de Prueba para Desarrollo
```
Simulación completa:
- Fallos simulados para testing
- Retrasos simulados para timeouts
- Respuestas realistas de APIs
- Desarrollo sin costos reales

Tipos de fallos simulados:
- Error de conectividad
- Pago no encontrado
- Fondos insuficientes
- Reembolso ya procesado
- Reembolso parcial no permitido
```

#### Flujo de Procesamiento Avanzado

##### 1. Validación Inicial
```
Proceso automático:
1. Sistema verifica ventana de tiempo
2. Valida configuración de pasarela
3. Verifica disponibilidad del adaptador
4. Confirma que reembolso no está procesado
```

##### 2. Procesamiento con Reintentos
```
Flujo robusto:
1. Marca reembolso como "Procesando"
2. Intenta procesar con pasarela
3. Si falla: Espera y reintenta
4. Si éxito: Marca como "Completado"
5. Si falla definitivamente: Marca como "Fallido"
```

##### 3. Logging y Auditoría
```
Registro completo:
- Cada intento de procesamiento
- Errores específicos encontrados
- Tiempo de procesamiento
- ID externo de la pasarela
- Usuario que procesó (si es manual)
```

#### Configuración por Hotel

##### Configuración de MercadoPago
```
Para Hotel Plaza Central:
- Días límite: 30 días
- Reembolsos parciales: Permitidos
- Modo: Producción
- Token: [configurado]

Para Hotel Plaza Norte:
- Días límite: 45 días
- Reembolsos parciales: No permitidos
- Modo: Prueba
- Token: [configurado para testing]
```

##### Configuración de Transferencia Bancaria
```
Para Hotel Plaza Sur:
- Días límite: 90 días
- Reembolsos parciales: No permitidos
- Modo: Producción
- Cuenta bancaria: [configurada]
```

#### Beneficios para el Negocio

##### Para el Hotel
- ✅ **Procesamiento automático** de reembolsos
- ✅ **Múltiples pasarelas** de pago
- ✅ **Validaciones automáticas** de limitaciones
- ✅ **Reintentos inteligentes** para mayor confiabilidad
- ✅ **Logging completo** para auditoría
- ✅ **Configuración independiente** por hotel
- ✅ **Modo de prueba** para desarrollo seguro

##### Para el Personal
- ✅ **Menos trabajo manual** con procesamiento automático
- ✅ **Validaciones automáticas** previenen errores
- ✅ **Logging detallado** para seguimiento
- ✅ **Configuración clara** por pasarela
- ✅ **Testing seguro** en modo de prueba
- ✅ **Múltiples opciones** de pasarelas

##### Para el Huésped
- ✅ **Procesamiento más rápido** y confiable
- ✅ **Múltiples métodos** de reembolso
- ✅ **Cumplimiento automático** con limitaciones
- ✅ **Transparencia** en tiempos de procesamiento
- ✅ **Consistencia** en el procesamiento

#### Casos de Uso Prácticos

##### Caso 1: Hotel con MercadoPago
```
Configuración:
- Pasarela: MercadoPago
- Días límite: 30 días
- Reembolsos parciales: Permitidos
- Modo: Producción

Resultado:
- Reembolsos automáticos en 1-3 días
- Soporte para reembolsos parciales
- Integración completa con API
- Logging detallado de transacciones
```

##### Caso 2: Hotel con Transferencia Bancaria
```
Configuración:
- Pasarela: Transferencia Bancaria
- Días límite: 90 días
- Reembolsos parciales: No permitidos
- Modo: Producción

Resultado:
- Reembolsos en 3-5 días hábiles
- Solo reembolsos completos
- Procesamiento directo
- Validación automática de limitaciones
```

##### Caso 3: Hotel en Desarrollo
```
Configuración:
- Pasarela: MercadoPago (Modo Prueba)
- Fallos simulados: Activados
- Retrasos simulados: 2 segundos
- Modo: Desarrollo

Resultado:
- Testing completo sin costos
- Simulación de escenarios de error
- Desarrollo seguro
- Validación de lógica de reintentos
```

#### Integración con Sistema Existente

##### RefundProcessor Original
```
Compatibilidad total:
- Sistema v1 sigue funcionando
- Sistema v2 se integra gradualmente
- Migración opcional por hotel
- Misma interfaz de usuario
```

##### APIs Unificadas
```
Endpoints existentes:
- /api/payments/refunds/ (sin cambios)
- /api/payments/refunds/{id}/ (sin cambios)
- Nuevos campos en respuestas
- Compatibilidad hacia atrás
```

#### Monitoreo y Alertas

##### Logging Automático
```
Eventos registrados:
- Inicio de procesamiento
- Cada intento de reembolso
- Errores específicos
- Éxito o fallo final
- Tiempo total de procesamiento
```

##### Alertas de Sistema
```
Notificaciones automáticas:
- Reembolsos fallidos después de 3 intentos
- Pasarelas no disponibles
- Configuraciones inválidas
- Ventanas de tiempo excedidas
```

#### Escalabilidad y Rendimiento

##### Procesamiento por Lotes
```
Optimización:
- Múltiples reembolsos simultáneos
- Procesamiento asíncrono
- Cola de tareas con Celery
- Recursos compartidos eficientemente
```

##### Configuración Dinámica
```
Flexibilidad:
- Adaptadores por hotel
- Configuración en tiempo real
- Hot-swapping de pasarelas
- A/B testing de proveedores
```

### Casos de Uso Prácticos

#### Caso 1: Hotel con Devoluciones Rápidas
```
Configuración:
- Devolución completa: 24 horas
- Método: Original payment
- Procesamiento: 3 días
- Aplicación: Todas las habitaciones

Resultado:
- Clientes satisfechos
- Proceso rápido
- Menos consultas
```

#### Caso 2: Hotel con Vouchers
```
Configuración:
- Devolución: Voucher
- Vencimiento: 365 días
- Monto mínimo: $20,000
- Usable: Cualquier habitación

Resultado:
- Retención de clientes
- Ingresos futuros garantizados
- Flexibilidad para huéspedes
```

#### Caso 3: Hotel de Lujo
```
Configuración:
- Suites: Devolución completa 48h
- Estándar: Devolución 50% hasta 72h
- Método: Transferencia bancaria
- Procesamiento: 5 días

Resultado:
- Políticas premium
- Flexibilidad diferenciada
- Procesamiento profesional
```

---

### ¿Cómo funciona?

#### Configuración de Tiempos de Cancelación

##### Cancelación Gratuita
```
Política: "Cancelación sin penalidad"
Tiempo: 24 horas antes del check-in
Aplicación: Todas las habitaciones
Resultado: Cliente puede cancelar sin costo adicional
```

##### Cancelación Parcial
```
Política: "Cancelación con penalidad"
Tiempo: 72 horas antes del check-in
Penalidad: 50% del total de la reserva
Aplicación: Suites solamente
Resultado: Cliente paga 50% como penalidad
```

##### Sin Cancelación
```
Política: "No se permite cancelación"
Tiempo: 168 horas (7 días) antes del check-in
Aplicación: Temporada alta
Resultado: No se puede cancelar la reserva
```

#### Tipos de Penalidades

##### Porcentaje del Total
```
Ejemplo:
- Total de reserva: $100,000
- Penalidad: 25%
- Monto a pagar: $25,000
- Devolución: $75,000
```

##### Monto Fijo
```
Ejemplo:
- Total de reserva: $100,000
- Penalidad fija: $20,000
- Monto a pagar: $20,000
- Devolución: $80,000
```

##### Por Número de Noches
```
Ejemplo:
- Total de reserva: $100,000 (4 noches)
- Penalidad: 1 noche
- Monto a pagar: $25,000
- Devolución: $75,000
```

#### Configuración Avanzada

##### Por Tipo de Habitación
```
Configuración:
- Singles: Cancelación gratuita hasta 24h
- Dobles: Cancelación parcial hasta 48h
- Suites: Sin cancelación después de 7 días
```

##### Por Canal de Reserva
```
Configuración:
- Directo: Cancelación gratuita hasta 24h
- Booking.com: Cancelación parcial hasta 48h
- Expedia: Sin cancelación después de 72h
```

##### Por Temporada
```
Configuración:
- Temporada baja: Cancelación gratuita hasta 24h
- Temporada media: Cancelación parcial hasta 48h
- Temporada alta: Sin cancelación después de 7 días
```

#### Mensajes Personalizados

##### Para Cancelación Gratuita
```
"Puedes cancelar tu reserva sin costo adicional hasta 24 horas antes de tu llegada. Después de ese tiempo, se aplicará una penalidad del 50%."
```

##### Para Cancelación Parcial
```
"Cancelación con penalidad: Se cobrará el 50% del total de la reserva como penalidad por cancelación tardía."
```

##### Para Sin Cancelación
```
"No se permite cancelación después de 7 días antes de la llegada. La reserva es no reembolsable."
```

### Modal de Cancelación Mejorado (v2.0)

#### ¿Qué es nuevo?
El modal de cancelación ha sido completamente mejorado para ofrecer una experiencia más clara y profesional:

### Pantalla de Éxito con Información Detallada de Reembolsos (v2.1)

#### ¿Qué es la Pantalla de Éxito?
La **Pantalla de Éxito** es una nueva funcionalidad que aparece después de que el cliente confirma la cancelación de su reserva. Es como recibir un recibo detallado de tu cancelación, con toda la información financiera y los próximos pasos claros.

#### ¿Por qué es Importante?
Imagina que cancelas una reserva y solo recibes un mensaje que dice "Cancelación exitosa". ¿Cómo sabes:
- ¿Cuánto dinero te van a devolver exactamente?
- ¿Cuándo lo vas a recibir?
- ¿Por qué método de pago?
- ¿Hay algún procesamiento manual requerido?
- ¿Cuál es el ID de tu reembolso para seguimiento?

**¡La pantalla de éxito te da toda esta información inmediatamente!** 📋

#### ¿Cómo Funciona?

##### 1. **Después de Confirmar la Cancelación**
```
Proceso automático:
1. Cliente confirma la cancelación
2. Sistema procesa el reembolso automáticamente
3. Sistema crea registro detallado del reembolso
4. Sistema muestra pantalla de éxito con toda la información
5. Cliente ve detalles completos antes de cerrar el modal
```

##### 2. **Información Detallada del Reembolso**
```
Información mostrada:
- ID del reembolso (para seguimiento)
- Monto exacto a devolver
- Estado actual (Completado, Procesando, Pendiente)
- Método de devolución (tarjeta, transferencia, voucher)
- Referencia externa (si aplica)
- Días de procesamiento estimados
- Fecha de procesamiento (si ya se completó)
- Si requiere procesamiento manual
```

##### 3. **Información de la Cancelación**
```
Detalles de la cancelación:
- Motivo de cancelación ingresado
- Política de cancelación aplicada históricamente
- Tipo de cancelación (gratuita, parcial, sin cancelación)
- Quién canceló la reserva (cliente o staff)
- Fecha y hora exacta de la cancelación
```

##### 4. **Resumen Financiero Final**
```
Desglose completo:
- Total pagado originalmente
- Penalidad aplicada (si hay)
- Monto de devolución
- Total neto a devolver
- Explicación clara de cada monto
```

##### 5. **Próximos Pasos Claros**
```
Información para el cliente:
- Cuándo recibirá la confirmación por email
- Cuándo aparecerá el reembolso en su método de pago
- Qué hacer si tiene preguntas
- Información de contacto del hotel
```

#### Ejemplo Práctico: Cancelación con Reembolso Automático

##### Escenario
```
Cliente: Juan Pérez
Reserva: Suite 101, 3 noches
Total pagado: $300,000
Política: Cancelación gratuita hasta 24h antes
Tiempo de cancelación: 2 horas antes del check-in
```

##### Pantalla de Éxito Mostrada
```
✅ ¡Cancelación Exitosa!

📋 Información del Reembolso:
• ID del Reembolso: #REF-12345
• Monto: $300,000
• Estado: Completado
• Método: Tarjeta de crédito original
• Referencia Externa: REF-12345-1705123456
• Procesado el: 15/01/2024 14:30

📝 Detalles de la Cancelación:
• Motivo: Cambio de planes
• Política aplicada: Cancelación gratuita 24h
• Tipo: Gratuita
• Cancelado por: Juan Pérez
• Fecha: 15/01/2024 14:30

💰 Resumen Financiero Final:
• Total pagado: $300,000
• Penalidad aplicada: $0
• Devolución: $300,000
• Total a devolver: $300,000

📧 Próximos pasos:
• Recibirás confirmación por email
• El reembolso aparecerá en tu tarjeta en 3-5 días
• Si tienes preguntas, contacta al hotel
```

#### Ejemplo Práctico: Cancelación con Penalidad

##### Escenario
```
Cliente: María González
Reserva: Habitación doble, 2 noches
Total pagado: $200,000
Política: Penalidad 50% después de 24h
Tiempo de cancelación: 12 horas antes del check-in
```

##### Pantalla de Éxito Mostrada
```
✅ ¡Cancelación Exitosa!

📋 Información del Reembolso:
• ID del Reembolso: #REF-12346
• Monto: $100,000
• Estado: Procesando
• Método: Tarjeta de crédito original
• Referencia Externa: REF-12346-1705123457
• Tiempo estimado: 3-5 días hábiles

📝 Detalles de la Cancelación:
• Motivo: Emergencia familiar
• Política aplicada: Penalidad 50% después de 24h
• Tipo: Parcial
• Cancelado por: María González
• Fecha: 15/01/2024 16:45

💰 Resumen Financiero Final:
• Total pagado: $200,000
• Penalidad aplicada: -$100,000
• Devolución: +$100,000
• Total a devolver: $100,000

📧 Próximos pasos:
• Recibirás confirmación por email
• El reembolso aparecerá en tu tarjeta en 3-5 días
• Si tienes preguntas, contacta al hotel
```

#### Ejemplo Práctico: Cancelación con Procesamiento Manual

##### Escenario
```
Cliente: Carlos López
Reserva: Suite presidencial, 5 noches
Total pagado: $500,000
Política: Cancelación gratuita hasta 24h
Método de pago: Transferencia bancaria
Tiempo de cancelación: 6 horas antes del check-in
```

##### Pantalla de Éxito Mostrada
```
✅ ¡Cancelación Exitosa!

📋 Información del Reembolso:
• ID del Reembolso: #REF-12347
• Monto: $500,000
• Estado: Pendiente
• Método: Transferencia bancaria
• Referencia Externa: Pendiente
• Procesamiento: Manual requerido

⚠️ Nota Importante:
• El equipo de administración procesará este reembolso manualmente
• Se requiere validación adicional para transferencias bancarias
• Tiempo estimado: 5-7 días hábiles

📝 Detalles de la Cancelación:
• Motivo: Problema de salud
• Política aplicada: Cancelación gratuita 24h
• Tipo: Gratuita
• Cancelado por: Carlos López
• Fecha: 15/01/2024 18:20

💰 Resumen Financiero Final:
• Total pagado: $500,000
• Penalidad aplicada: $0
• Devolución: $500,000
• Total a devolver: $500,000

📧 Próximos pasos:
• Recibirás confirmación por email
• El hotel te contactará para coordinar la transferencia
• Si tienes preguntas, contacta al hotel directamente
```

#### Beneficios para el Cliente

##### 🎯 **Transparencia Total**
- **Información completa**: Sabes exactamente qué va a pasar con tu dinero
- **Sin sorpresas**: Todos los montos y tiempos están claros
- **Trazabilidad**: Tienes un ID de reembolso para seguimiento

##### ⚡ **Feedback Inmediato**
- **Confirmación instantánea**: No tienes que esperar emails o llamadas
- **Estado en tiempo real**: Sabes si el reembolso ya se procesó
- **Próximos pasos claros**: Sabes exactamente qué esperar

##### 🔍 **Información Detallada**
- **Desglose financiero**: Entiendes cada monto y por qué
- **Detalles de la cancelación**: Tienes registro completo de lo que pasó
- **Información de contacto**: Sabes cómo contactar al hotel si necesitas ayuda

##### 📱 **Experiencia Profesional**
- **Interfaz moderna**: Pantalla elegante y fácil de entender
- **Información organizada**: Todo está bien estructurado y claro
- **Accesibilidad**: Funciona bien en todos los dispositivos

#### Beneficios para el Hotel

##### 💼 **Menos Consultas**
- **Información completa**: Los clientes tienen toda la información que necesitan
- **Menos llamadas**: Reduces consultas sobre reembolsos
- **Clientes satisfechos**: Mejor experiencia = menos quejas

##### 📊 **Mejor Seguimiento**
- **IDs de reembolso**: Fácil seguimiento de cada devolución
- **Estados claros**: Sabes exactamente qué está pasando con cada reembolso
- **Trazabilidad completa**: Registro detallado de todas las cancelaciones

##### 🎯 **Profesionalismo**
- **Experiencia premium**: Los clientes ven un sistema profesional
- **Confianza**: La transparencia genera confianza en el hotel
- **Diferenciación**: Te distingues de hoteles con sistemas básicos

#### Casos de Uso Reales

##### Caso 1: Cliente Ansioso por su Reembolso
```
Situación: Cliente cancela y quiere saber cuándo recibe su dinero
Solución: Pantalla de éxito muestra tiempo exacto de procesamiento
Resultado: Cliente tranquilo, no llama al hotel
```

##### Caso 2: Cancelación con Penalidad Confusa
```
Situación: Cliente no entiende por qué se aplicó una penalidad
Solución: Pantalla explica la política aplicada y el cálculo
Resultado: Cliente entiende y acepta la penalidad
```

##### Caso 3: Reembolso que Requiere Datos Bancarios
```
Situación: Cliente pagó por transferencia, necesita dar datos para reembolso
Solución: Pantalla indica que el hotel lo contactará
Resultado: Cliente sabe qué esperar y no se preocupa
```

#### Integración con Otros Módulos

##### Con Sistema de Pagos
- **Información de reembolsos**: Datos en tiempo real del procesamiento
- **Métodos de pago**: Información específica según el método usado
- **Referencias externas**: IDs de las pasarelas de pago

##### Con Sistema de Notificaciones
- **Confirmación por email**: Complementa la pantalla de éxito
- **Notificaciones de estado**: Actualizaciones si cambia el estado del reembolso
- **Recordatorios**: Si el reembolso tarda más de lo esperado

##### Con Dashboard del Hotel
- **Métricas de cancelaciones**: Información para análisis del negocio
- **Tiempos de procesamiento**: Datos para optimizar el servicio
- **Satisfacción del cliente**: Menos consultas = mejor experiencia

#### Configuración y Personalización

##### Mensajes Personalizables
- **Mensajes por hotel**: Cada hotel puede personalizar los textos
- **Idiomas**: Soporte para múltiples idiomas
- **Tono**: Formal, casual, o personalizado según el hotel

##### Información Condicional
- **Solo información relevante**: No muestra campos vacíos o irrelevantes
- **Adaptación al método**: Diferente información según el método de pago
- **Políticas específicas**: Información según las políticas del hotel

#### Mejoras Futuras

##### Próximas Funcionalidades
- **Seguimiento en tiempo real**: Actualización automática del estado
- **Notificaciones push**: Alertas cuando cambia el estado del reembolso
- **Historial de reembolsos**: Vista de todos los reembolsos del cliente

##### Integraciones Avanzadas
- **WhatsApp**: Envío de información por WhatsApp
- **SMS**: Confirmaciones por mensaje de texto
- **Email personalizado**: Templates específicos por hotel

#### 🎯 **Información Visual Mejorada**
- **Badge de reembolso automático**: Muestra "✓ Reembolso automático disponible" cuando la pasarela de pago soporta devoluciones automáticas
- **Nota informativa**: Explica claramente cuando la pasarela no soporta reembolsos automáticos
- **Política aplicada**: Muestra el nombre de la política de cancelación que se aplicó al crear la reserva
- **Método sugerido**: Indica el método de reembolso recomendado (tarjeta, transferencia, voucher, etc.)

#### 🔧 **Botones Reorganizados**
- **"Cerrar"**: Cierra el modal sin cancelar
- **"Cancelar y solicitar reembolso"**: Confirma la cancelación con devolución
- **"Cancelar sin reembolso (Solo staff)"**: Opción para personal autorizado (preparado para futuros roles)

#### ♿ **Accesibilidad Mejorada**
- **Atributos ARIA completos**: Para lectores de pantalla
- **Navegación por teclado**: Accesible sin mouse
- **Etiquetas descriptivas**: Para mejor comprensión
- **Roles semánticos**: Para mejor estructura

#### 📱 **Experiencia de Usuario**
- **Información clara**: El usuario sabe exactamente qué va a pasar
- **Transparencia total**: Montos, penalidades y devoluciones explicados
- **Confirmación segura**: Dos pasos para evitar cancelaciones accidentales
- **Feedback inmediato**: Estados de carga y confirmaciones claras

### Flujo de Cancelación

#### 1. Usuario Solicita Cancelación
```
Proceso:
1. Usuario hace clic en "Cancelar" en su reserva
2. Sistema evalúa la política de cancelación
3. Sistema calcula tiempo hasta check-in
4. Sistema determina tipo de cancelación aplicable
```

#### 2. Sistema Muestra Opciones
```
Modal de cancelación mejorado muestra:
- Tipo de cancelación (gratuita/parcial/sin cancelación)
- Monto de penalidad (si aplica)
- Monto de devolución (si aplica)
- Mensaje personalizado de la política
- Resumen financiero final
- Badge "✓ Reembolso automático disponible" (si está habilitado)
- Nota informativa sobre pasarelas sin soporte automático
- Información de la política aplicada históricamente
- Método sugerido de reembolso
- Botones organizados: "Cerrar", "Cancelar y solicitar reembolso", "Cancelar sin reembolso (Solo staff)"
```

#### 3. Usuario Confirma Cancelación
```
Proceso:
1. Usuario revisa las consecuencias
2. Usuario confirma la cancelación
3. Sistema procesa devolución automáticamente
4. Sistema actualiza estado de reserva
5. Sistema libera habitación automáticamente
6. Sistema envía confirmación con detalles de devolución
```

#### 4. Procesamiento Automático de Devoluciones
```
Proceso automático:
1. Sistema calcula total pagado de la reserva
2. Sistema aplica penalidad según política de cancelación histórica
3. Sistema calcula monto de devolución según política de devolución
4. Sistema procesa devolución por método de pago original
5. Sistema crea registro de pago negativo para devolución
6. Sistema registra log detallado con información financiera
```

#### 5. Registro Histórico de Políticas
```
Garantía de consistencia:
1. Al crear reserva se asigna automáticamente la política vigente
2. Campo "applied_cancellation_policy" mantiene referencia histórica
3. Cancelaciones siempre usan la política que estaba vigente al crear la reserva
4. Consistencia garantizada independientemente de cambios posteriores en políticas
```

#### 6. Manejo Explícito de Reembolsos
```
Flujo financiero claro:
1. Sistema crea registro explícito de reembolso (modelo Refund)
2. Cada reembolso está vinculado al pago original específico
3. Estados claros: Pendiente, Procesando, Completado, Fallido, Cancelado
4. Razones específicas: Cancelación, Sobrepago, Ajuste Administrativo, etc.
5. Trazabilidad completa del flujo financiero
6. Gestión de reembolsos parciales y completos
```

#### 7. Auto-cancelación de Reservas Vencidas
```
Gestión automática de vencimientos:
1. Sistema revisa diariamente reservas pendientes
2. Calcula fecha de vencimiento del adelanto según política de pago
3. Cancela automáticamente reservas vencidas sin pago
4. Libera habitaciones automáticamente
5. Registra logs detallados de cancelación automática
6. Proporciona estadísticas de reservas pendientes
```

#### 8. Auto-cancelación de Reservas PENDING Vencidas
```
Gestión automática de check-ins vencidos:
1. Sistema revisa diariamente reservas PENDING
2. Identifica reservas con fecha de check-in ya pasada
3. Cancela automáticamente reservas vencidas sin pago
4. Libera habitaciones automáticamente
5. Registra logs detallados de cancelación automática
6. Motivo: "Auto-cancelación: fecha de check-in vencida sin pago del depósito"
```

#### 9. Auto No-Show de Reservas CONFIRMED (v2.0 - Mejorado)
```
Gestión automática de no-shows con penalidades y reembolsos:
1. Sistema revisa diariamente reservas confirmadas
2. Identifica reservas con fecha de check-in ya pasada
3. Marca automáticamente como no-show
4. Aplica penalidades automáticas según política de cancelación
5. Calcula reembolsos específicos para NO_SHOW
6. Procesa reembolsos según método configurado
7. Crea notificaciones detalladas para hotel, huésped y administradores
8. Registra logs detallados de penalidades y reembolsos
9. Solo procesa hoteles con auto_no_show_enabled=True
10. Motivo: "Auto no-show: check-in date passed"
```

#### 9.1 Penalidades Automáticas por NO_SHOW
```
Procesamiento de penalidades:
1. Sistema obtiene política de cancelación aplicada a la reserva
2. Calcula reglas de cancelación para NO_SHOW (tiempo = 0)
3. Aplica penalidad según política (porcentaje, monto fijo, etc.)
4. Registra penalidad en log de cambios de la reserva
5. Crea notificación detallada con información financiera
6. Mantiene habitación ocupada (ya se cobró la penalidad)
```

#### 9.2 Reembolsos Específicos para NO_SHOW
```
Configuraciones especiales para NO_SHOW:
1. Porcentaje de reembolso específico para NO_SHOW (ej: 25%)
2. Método de reembolso diferenciado (voucher, transferencia, etc.)
3. Días de procesamiento específicos (ej: 45 días)
4. Vouchers con validez extendida (365 días)
5. Transferencias bancarias que requieren datos del huésped
6. Reembolsos al método de pago original
```

#### 9.3 Notificaciones Mejoradas para NO_SHOW
```
Notificaciones diferenciadas por tipo de usuario:

Para el Hotel:
- Información financiera completa (total pagado, penalidad, reembolso, pérdida neta)
- Detalles de la reserva (código, huéspedes, habitación, fechas)
- Acciones requeridas (procesar reembolso, actualizar estadísticas)
- Timestamp de procesamiento automático

Para el Huésped:
- Detalles de su reserva (código, hotel, habitación, fechas)
- Información financiera (total pagado, penalidad aplicada)
- Próximos pasos según tipo de reembolso
- Información de contacto del hotel
- Tiempos de procesamiento claros

Para Administradores:
- Reporte de impacto financiero
- Métricas de NO_SHOW por hotel
- Análisis de patrones de no-shows
```

#### 10. Cronograma de Tareas Automáticas
```
Horario de ejecución diario:
- 8:00 AM: Auto-cancelación por falta de pago del depósito
- 8:30 AM: Auto-cancelación de PENDING vencidas
- 9:00 AM: Auto no-show de CONFIRMED vencidas

Lógica de cancelación:
- PENDING vencidas → CANCELLED (liberar habitación)
- CONFIRMED vencidas → NO_SHOW (mantener habitación ocupada)
- Configuración por hotel: Campo auto_no_show_enabled
```

### Beneficios

#### Para el Hotel
- ✅ **Control total** sobre políticas de cancelación
- ✅ **Protección de ingresos** con penalidades configurables
- ✅ **Flexibilidad** para diferentes tipos de habitaciones
- ✅ **Adaptación** a temporadas y canales
- ✅ **Transparencia** con mensajes claros
- ✅ **Devoluciones automáticas** sin intervención manual
- ✅ **Liberación automática** de habitaciones canceladas
- ✅ **Auditoría completa** de transacciones financieras
- ✅ **Registro histórico** de políticas aplicadas
- ✅ **Consistencia garantizada** en cancelaciones
- ✅ **Flujo financiero claro** con reembolsos explícitos
- ✅ **Trazabilidad completa** de devoluciones
- ✅ **Gestión automática** de vencimientos de reservas
- ✅ **Liberación automática** de habitaciones vencidas

#### Para el Huésped
- ✅ **Transparencia** sobre reglas de cancelación
- ✅ **Información clara** sobre penalidades
- ✅ **Proceso simple** de cancelación
- ✅ **Conocimiento previo** de consecuencias
- ✅ **Devoluciones automáticas** por método de pago original
- ✅ **Confirmación inmediata** de devolución procesada
- ✅ **Tiempos de procesamiento** claros y transparentes
- ✅ **Políticas consistentes** según lo acordado al reservar
- ✅ **Seguimiento detallado** del estado de reembolsos
- ✅ **Transparencia total** en el flujo financiero
- ✅ **Tiempos claros** para pago de adelantos
- ✅ **Notificaciones automáticas** de vencimientos

#### Para el Personal
- ✅ **Proceso automatizado** de evaluación
- ✅ **Cálculos precisos** de penalidades
- ✅ **Información centralizada** de políticas
- ✅ **Menos errores** en cancelaciones
- ✅ **Gestión eficiente** del proceso
- ✅ **Devoluciones automáticas** sin procesamiento manual
- ✅ **Liberación automática** de habitaciones
- ✅ **Logs detallados** para auditoría y seguimiento
- ✅ **Trazabilidad completa** de políticas aplicadas
- ✅ **Consistencia legal** en todas las cancelaciones
- ✅ **Gestión explícita** de reembolsos y devoluciones
- ✅ **Control total** del flujo financiero
- ✅ **Procesamiento automático** de vencimientos
- ✅ **Estadísticas detalladas** de reservas pendientes

### Casos de Uso Prácticos

#### Caso 1: Hotel Boutique
```
Configuración:
- Cancelación gratuita: 24 horas
- Penalidad: 50% después de 24h
- Aplicación: Todas las habitaciones
- Canal: Solo directo

Resultado:
- Flexibilidad para huéspedes
- Protección de ingresos
- Proceso simple
```

#### Caso 2: Hotel de Temporada
```
Configuración:
- Temporada baja: Cancelación gratuita 24h
- Temporada media: Penalidad 25% hasta 48h
- Temporada alta: Sin cancelación después de 7 días

Resultado:
- Adaptación a demanda
- Maximización de ingresos
- Políticas diferenciadas
```

#### Caso 3: Hotel de Lujo
```
Configuración:
- Suites: Sin cancelación después de 14 días
- Habitaciones estándar: Penalidad 50% hasta 72h
- Promociones: Cancelación gratuita hasta 24h

Resultado:
- Políticas premium para suites
- Flexibilidad para habitaciones estándar
- Incentivos para promociones
```

---

### ¿Cómo funciona?

#### Políticas de Pago Configurables

##### Política 1: Pago Completo
```
Al confirmar la reserva:
- Cliente paga el 100% del total
- Reserva se confirma inmediatamente
- No hay saldos pendientes
```

##### Política 2: Pago con Adelanto
```
Al confirmar la reserva:
- Cliente paga el 50% (adelanto)
- Reserva se confirma
- Saldo pendiente: 50%

Al check-in:
- Sistema solicita el 50% restante
- Cliente paga el saldo
- Check-in se completa
```

##### Política 3: Pago al Check-in
```
Al confirmar la reserva:
- No se requiere pago
- Reserva se confirma sin pago

Al check-in:
- Cliente paga el 100% del total
- Check-in se completa
```

#### Métodos de Pago

##### Tarjetas de Crédito/Débito (Mercado Pago)
```
Proceso:
1. Cliente selecciona "Pagar con tarjeta"
2. Sistema genera formulario seguro
3. Cliente ingresa datos de tarjeta
4. Mercado Pago procesa el pago
5. Sistema confirma automáticamente
6. Reserva se actualiza
```

##### Pagos Manuales
```
Efectivo:
- Personal registra el pago
- Sistema actualiza el saldo
- Se genera comprobante

Transferencia:
- Cliente realiza transferencia
- Personal verifica y registra
- Sistema actualiza el saldo

POS:
- Pago con tarjeta en recepción
- Personal registra el pago
- Sistema actualiza el saldo
```

#### Cálculo Automático de Saldos
```
Ejemplo de reserva:
- Total de la reserva: $100,000
- Política: 50% adelanto
- Adelanto pagado: $50,000
- Saldo pendiente: $50,000

Al check-in:
- Sistema detecta saldo pendiente
- Solicita pago del saldo
- Cliente paga $50,000
- Check-in se completa
```

### Beneficios
- ✅ **Flexibilidad total** en políticas de pago
- ✅ **Pagos seguros** con Mercado Pago
- ✅ **Múltiples métodos** de pago
- ✅ **Cálculo automático** de saldos
- ✅ **Prevención de errores** en pagos

---

## 3.7 Gestión de Tarifas

### ¿Qué hace?
Permite configurar precios dinámicos, promociones e impuestos de manera flexible.

### ¿Cómo funciona?

#### Planes de Tarifas
```
Plan: "Tarifa Estándar"
- Precio base: $30,000 por noche
- Aplicable: Todo el año
- Habitaciones: Todas las habitaciones
- Canal: Directo
```

#### Reglas de Tarifas
```
Regla: "Fin de Semana"
- Fechas: Viernes y sábados
- Precio: $40,000 por noche (+$10,000)
- Habitaciones: Suites solamente
- Canal: Todos los canales
```

#### Promociones
```
Promoción: "Descuento de Temporada Baja"
- Código: "VERANO2024"
- Descuento: 20% por noche
- Fechas: 1/12/2024 - 28/2/2025
- Habitaciones: Todas
- Combinable: No
```

#### Impuestos
```
Impuesto: "IVA"
- Tipo: Porcentaje
- Valor: 21%
- Alcance: Por noche
- Aplicable: Todas las reservas
```

#### Cálculo Automático de Precios
```
Ejemplo de cotización:
Habitación: Suite 101
Fechas: 15/01/2024 - 18/01/2024 (3 noches)
Huéspedes: 2 personas

Cálculo por noche:
- Precio base: $30,000
- Regla fin de semana: +$10,000
- Subtotal: $40,000
- IVA (21%): +$8,400
- Total por noche: $48,400

Total de la reserva: $145,200
```

### Restricciones de Venta
- **CTA (Cerrado a Llegadas)**: No se pueden hacer check-ins en ciertas fechas
- **CTD (Cerrado a Salidas)**: No se pueden hacer check-outs en ciertas fechas
- **Días Cerrados**: Fechas completamente bloqueadas
- **Estadía Mínima**: Mínimo de noches requeridas
- **Estadía Máxima**: Máximo de noches permitidas

### Beneficios
- ✅ **Precios dinámicos** según la demanda
- ✅ **Promociones flexibles** con códigos
- ✅ **Impuestos automáticos** calculados
- ✅ **Restricciones inteligentes** de venta
- ✅ **Múltiples canales** de distribución

---

## 3.8 Dashboard y Reportes

### ¿Qué hace?
Proporciona métricas y análisis del negocio en tiempo real.

### ¿Cómo funciona?

#### Métricas de Habitaciones
```
Estado actual del hotel:
- Total de habitaciones: 50
- Disponibles: 15
- Ocupadas: 30
- En mantenimiento: 3
- Fuera de servicio: 2

Tasa de ocupación: 60%
```

#### Métricas de Reservas
```
Reservas del día:
- Total de reservas: 150
- Pendientes: 5
- Confirmadas: 120
- Canceladas: 10
- Check-ins hoy: 8
- Check-outs hoy: 12
- No-shows: 2
```

#### Métricas de Huéspedes
```
Huéspedes del día:
- Total de huéspedes: 300
- Check-in realizados: 180
- Esperados hoy: 25
- Partiendo hoy: 20
```

#### Métricas Financieras
```
Ingresos del día:
- Ingreso total: $2,500,000
- Tarifa promedio por habitación: $83,333
- Tasa de ocupación: 60%
```

#### Ocupación por Tipo de Habitación
```
Distribución actual:
- Singles ocupadas: 10
- Dobles ocupadas: 15
- Triples ocupadas: 3
- Suites ocupadas: 2
```

### Reportes Automáticos
- **Diarios**: Métricas del día actual
- **Semanal**: Resumen de la semana
- **Mensual**: Análisis del mes
- **Por hotel**: Métricas específicas de cada hotel

### Beneficios
- ✅ **Visión en tiempo real** del negocio
- ✅ **Métricas clave** del hotel
- ✅ **Análisis de ocupación** por tipo
- ✅ **Seguimiento financiero** automático
- ✅ **Reportes históricos** para análisis

---

## 3.9 Calendario de Reservas

### ¿Qué hace?
Proporciona una vista visual e interactiva de todas las reservas del hotel, permitiendo una gestión eficiente y una comprensión rápida del estado de ocupación.

### ¿Cómo funciona?

#### Vista de Calendario Inteligente
```
Vista mensual:
- Calendario completo del mes actual
- Reservas mostradas como bloques de colores
- Información de habitación y huésped visible
- Estados diferenciados por colores

Vista semanal:
- Detalle de una semana específica
- Mayor espacio para ver información
- Ideal para planificación detallada

Vista diaria:
- Enfoque en un día específico
- Lista detallada de todas las reservas
- Perfecta para operaciones diarias
```

#### Colores por Estado de Reserva
```
🟡 Pendiente: Amarillo - Reserva creada, pendiente de confirmación
🔵 Confirmada: Azul - Reserva confirmada, pago procesado
🟢 Check-in: Verde - Huéspedes en el hotel
⚫ Check-out: Gris - Huéspedes se fueron
🔴 Cancelada: Rojo - Reserva cancelada
🟣 No-show: Púrpura - Huésped no se presentó
```

#### Funcionalidades Interactivas

##### Visualización de Reservas
```
Información mostrada:
- Nombre de la habitación (ej: "HAB-101")
- Nombre del huésped (ej: "Juan Pérez")
- Fechas de check-in y check-out
- Estado actual de la reserva
- Duración de la estadía
```

##### Gestión desde el Calendario
```
Acciones disponibles:
- Crear nueva reserva haciendo clic en fecha vacía
- Editar reserva existente haciendo clic en el evento
- Ver detalles completos de la reserva
- Filtrar por hotel, habitación o estado
- Buscar reservas por nombre de huésped
```

##### Filtros Avanzados
```
Filtros disponibles:
- Por hotel: Ver reservas de un hotel específico
- Por habitación: Filtrar por habitación particular
- Por estado: Mostrar solo reservas en cierto estado
- Por búsqueda: Buscar por nombre de huésped
- Limpiar filtros: Volver a vista completa
```

#### Indicadores Visuales

##### Día Actual
```
Marcado especial:
- Fondo dorado sutil
- Borde superior dorado
- Número del día en dorado
- Efecto de gradiente elegante
```

##### Hover y Selección
```
Interacciones:
- Hover en fechas: Efecto dorado corporativo
- Selección de rango: Resaltado dorado
- Botones activos: Color dorado de la empresa
- Transiciones suaves y elegantes
```

#### Información Detallada de Reservas

##### Modal de Detalles
```
Al hacer clic en una reserva:
- Información completa del huésped
- Datos de la habitación asignada
- Fechas de check-in y check-out
- Estado actual de la reserva
- Opción para editar la reserva
- Botón para cerrar el modal
```

##### Datos Mostrados
```
Información del huésped:
- Nombre completo
- Email de contacto
- Teléfono
- Documento de identidad
- Dirección de contacto

Información de la reserva:
- Número de habitación
- Piso de la habitación
- Tipo de habitación
- Número de huéspedes
- Precio total de la estadía
```

#### Navegación Intuitiva

##### Controles de Navegación
```
Botones disponibles:
- Anterior: Ir al mes/semana/día anterior
- Siguiente: Ir al mes/semana/día siguiente
- Hoy: Volver a la fecha actual
- Cambiar vista: Mes/Semana/Día
```

##### Responsive Design
```
Adaptación automática:
- Vista optimizada para móviles
- Botones táctiles en tablets
- Navegación simplificada en pantallas pequeñas
- Información condensada pero completa
```

### Beneficios

#### Para el Personal de Recepción
- ✅ **Vista rápida** del estado de ocupación
- ✅ **Identificación inmediata** de habitaciones disponibles
- ✅ **Gestión eficiente** de check-ins y check-outs
- ✅ **Prevención de errores** con información visual clara

#### Para los Gerentes
- ✅ **Análisis visual** de la ocupación
- ✅ **Planificación estratégica** basada en patrones
- ✅ **Identificación de tendencias** de reservas
- ✅ **Toma de decisiones** informada

#### Para el Personal de Limpieza
- ✅ **Lista visual** de habitaciones a limpiar
- ✅ **Priorización** por horarios de check-in
- ✅ **Seguimiento** del estado de cada habitación
- ✅ **Coordinación** con recepción

#### Para el Personal de Mantenimiento
- ✅ **Identificación** de habitaciones fuera de servicio
- ✅ **Planificación** de tareas de mantenimiento
- ✅ **Seguimiento** del estado de habitaciones
- ✅ **Coordinación** con otros departamentos

### Casos de Uso Prácticos

#### Caso 1: Recepción Matutina
```
Situación: Recepcionista inicia el día
Proceso:
1. Abre el calendario en vista diaria
2. Ve todas las llegadas del día (check-ins)
3. Identifica habitaciones que necesitan limpieza
4. Planifica el trabajo del día
5. Coordina con limpieza y mantenimiento
```

#### Caso 2: Planificación Semanal
```
Situación: Gerente planifica la semana
Proceso:
1. Cambia a vista semanal
2. Analiza la ocupación por días
3. Identifica días de alta ocupación
4. Planifica recursos adicionales
5. Coordina con personal de limpieza
```

#### Caso 3: Gestión de Emergencias
```
Situación: Habitación necesita mantenimiento urgente
Proceso:
1. Identifica la habitación en el calendario
2. Ve si hay reservas futuras
3. Reasigna huéspedes si es necesario
4. Marca habitación como fuera de servicio
5. Actualiza el calendario en tiempo real
```

### Integración con Otros Módulos

#### Con Gestión de Reservas
- **Sincronización automática** de cambios
- **Actualización en tiempo real** del estado
- **Validación visual** de disponibilidad
- **Prevención de conflictos** de reservas

#### Con Dashboard
- **Métricas visuales** complementarias
- **Análisis de ocupación** gráfico
- **Tendencias** de reservas
- **Reportes** basados en datos del calendario

#### Con Sistema de Pagos
- **Indicadores visuales** de estado de pago
- **Alertas** de pagos pendientes
- **Seguimiento** de saldos
- **Confirmación** automática de pagos

---

## 3.10 Gestión de Usuarios

### ¿Qué hace?
Administra el acceso y permisos del personal del hotel.

### ¿Cómo funciona?

#### Perfiles de Usuario
```
Usuario: "María González"
Cargo: "Recepcionista"
Hoteles asignados: "Hotel Plaza Central"
Permisos:
- Ver reservas
- Hacer check-in/check-out
- Registrar pagos manuales
- Ver dashboard básico
```

#### Tipos de Usuarios
- **Administrador**: Acceso completo al sistema
- **Gerente**: Gestión de hotel y reportes
- **Recepcionista**: Operaciones diarias
- **Contador**: Gestión de pagos y reportes

#### Asignación de Hoteles
```
Un usuario puede trabajar en:
- Un solo hotel
- Múltiples hoteles
- Todos los hoteles de la empresa
```

### Beneficios
- ✅ **Control de acceso** granular
- ✅ **Perfiles específicos** por rol
- ✅ **Multi-hotel** para personal
- ✅ **Seguridad** en la información

---

## 3.11 Gestión de Empresas

### ¿Qué hace?
Administra empresas que pueden tener múltiples hoteles.

### ¿Cómo funciona?

#### Estructura Empresarial
```
Empresa: "Grupo Hotelero ABC"
Hoteles:
- Hotel Plaza Central (Buenos Aires)
- Hotel Plaza Norte (Córdoba)
- Hotel Plaza Sur (Rosario)

Configuración global:
- Políticas de pago estándar
- Métodos de pago habilitados
- Configuración de Mercado Pago
```

#### Configuraciones Globales
- **Políticas de pago**: Estándar para todos los hoteles
- **Métodos de pago**: Configuración centralizada
- **Usuarios**: Personal que puede trabajar en múltiples hoteles
- **Reportes**: Consolidados de todos los hoteles

### Beneficios
- ✅ **Gestión centralizada** de múltiples hoteles
- ✅ **Configuraciones globales** consistentes
- ✅ **Reportes consolidados** del grupo
- ✅ **Personal compartido** entre hoteles

---

## 3.13 Procesamiento Automático de Reembolsos

### ¿Qué es el Procesamiento Automático de Reembolsos?

El **Procesamiento Automático de Reembolsos** es como tener un asistente financiero que se encarga de procesar todas las devoluciones de dinero de manera automática, sin que tengas que hacer nada manualmente. Es como tener un cajero automático que funciona 24/7 para tus reembolsos.

### ¿Por qué es Importante?

Imagina que tienes que procesar 50 reembolsos al día. ¿Cómo manejas:
- Reembolsos que fallan por problemas temporales de la pasarela de pago?
- Reembolsos que expiran porque pasó mucho tiempo?
- Reintentos automáticos cuando hay fallos de conectividad?
- Notificaciones cuando algo requiere atención manual?

**¡El sistema lo hace todo automáticamente!** 🤖

### ¿Cómo Funciona?

#### 🔄 **Procesamiento Automático**
- **Cada hora**: El sistema busca reembolsos pendientes
- **Procesa automáticamente**: Intenta completar cada reembolso
- **Reintenta fallos**: Si falla, espera y vuelve a intentar
- **Notifica problemas**: Te avisa si algo requiere atención manual

#### ⏰ **Validación de Tiempo**
- **Ventana de tiempo**: Respeta los límites de tu pasarela de pago
- **Ejemplo**: Si Mercado Pago permite reembolsos hasta 30 días, el sistema respeta ese límite
- **Expiración automática**: Marca como fallido si se excede el tiempo

#### 🔁 **Reintentos Inteligentes**
- **Primer intento**: Inmediato
- **Segundo intento**: Después de 1 segundo
- **Tercer intento**: Después de 2 segundos
- **Cuarto intento**: Después de 4 segundos
- **Si falla todo**: Marca como fallido y te notifica

### ¿Qué Tipos de Reembolsos Procesa?

#### 💳 **Reembolsos por Cancelación**
- **Cuándo**: Cliente cancela una reserva
- **Proceso**: Calcula penalidad y devuelve el resto
- **Tiempo**: Inmediato si está dentro de la ventana

#### 🚫 **Reembolsos por No-Show**
- **Cuándo**: Huésped no se presenta
- **Proceso**: Aplica penalidad según política
- **Reembolso**: Puede dar voucher o devolución parcial

#### 💰 **Reembolsos por Sobrepago**
- **Cuándo**: Cliente pagó de más
- **Proceso**: Devuelve el exceso automáticamente
- **Tiempo**: Inmediato

#### 🔧 **Reembolsos por Ajustes**
- **Cuándo**: Error en el sistema o ajuste administrativo
- **Proceso**: Devuelve según la configuración
- **Tiempo**: Inmediato

### Configuración por Hotel

#### ⚙️ **Ventana de Tiempo**
- **Configuración**: Días límite para procesar reembolsos
- **Ejemplo**: 30 días para Mercado Pago, 7 días para transferencias
- **Flexibilidad**: Cada hotel puede configurar su límite

#### 💳 **Métodos de Reembolso**
- **Pago original**: Devuelve al método usado para pagar
- **Transferencia bancaria**: Requiere datos del huésped
- **Voucher**: Crédito para futuras reservas
- **Efectivo**: Para procesamiento manual

#### 🔄 **Reintentos Automáticos**
- **Configuración**: Número de intentos y tiempos de espera
- **Personalizable**: Cada hotel puede ajustar según su pasarela
- **Inteligente**: Aprende de los fallos para mejorar

### Notificaciones Automáticas

#### ✅ **Reembolsos Exitosos**
- **Cuándo**: Reembolso procesado correctamente
- **Ejemplo**: "Reembolso de $150.00 para RES-123 completado exitosamente"
- **Información**: Monto, método, referencia externa

#### ❌ **Reembolsos Fallidos**
- **Cuándo**: Reembolso no se pudo procesar después de todos los intentos
- **Ejemplo**: "Reembolso de $200.00 para RES-456 falló. Requiere atención manual"
- **Acción**: El personal debe revisar y procesar manualmente

#### ⏰ **Reembolsos Expirados**
- **Cuándo**: Reembolso excedió la ventana de tiempo
- **Ejemplo**: "Reembolso de $100.00 para RES-789 expiró. Ventana de 30 días excedida"
- **Acción**: El personal debe contactar al huésped

### Beneficios para tu Hotel

#### ⏱️ **Ahorro de Tiempo**
- **Automático**: No necesitas procesar reembolsos manualmente
- **24/7**: Funciona incluso cuando no estás en el hotel
- **Eficiente**: Procesa múltiples reembolsos simultáneamente

#### 💰 **Mejor Gestión Financiera**
- **Trazabilidad**: Sabes exactamente qué se procesó y cuándo
- **Estadísticas**: Reportes de reembolsos exitosos y fallidos
- **Control**: Configuración flexible por hotel

#### 😊 **Mejor Experiencia del Cliente**
- **Rápido**: Reembolsos procesados en minutos, no días
- **Confiable**: Reintentos automáticos para fallos temporales
- **Transparente**: El cliente recibe notificaciones del estado

#### 🔧 **Menos Trabajo Manual**
- **Solo excepciones**: Solo intervienes cuando algo falla
- **Notificaciones claras**: Sabes exactamente qué revisar
- **Proceso guiado**: El sistema te dice qué hacer

### Casos de Uso Reales

#### 📱 **Caso 1: Cancelación con Reembolso Automático**
1. **Cliente cancela** reserva 2 horas antes del check-in
2. **Modal muestra** badge "✓ Reembolso automático disponible"
3. **Sistema calcula** penalidad del 50% según política
4. **Modal muestra** información clara: "Se procesará automáticamente la devolución por el mismo método de pago"
5. **Sistema procesa** reembolso del 50% automáticamente
6. **Cliente recibe** confirmación en minutos
7. **Hotel recibe** notificación del reembolso procesado

#### 🏨 **Caso 2: Cancelación con Reembolso Manual**
1. **Cliente cancela** reserva 2 horas antes del check-in
2. **Modal muestra** nota "⚠️ Reembolso manual requerido: La pasarela de pago no soporta reembolsos automáticos"
3. **Sistema calcula** penalidad del 50% según política
4. **Modal explica** "Se generará un reembolso en estado 'Pendiente' que el staff debe procesar manualmente"
5. **Sistema crea** reembolso pendiente para procesamiento manual
6. **Staff recibe** notificación para procesar el reembolso
7. **Cliente recibe** confirmación de que el reembolso será procesado por el staff

#### 🚫 **Caso 2: No-Show con Voucher**
1. **Huésped no se presenta** en la fecha de check-in
2. **Sistema marca** como no-show automáticamente
3. **Sistema aplica** penalidad del 100%
4. **Sistema crea** voucher del 25% para futuras reservas
5. **Hotel recibe** notificación con detalles financieros

#### 💳 **Caso 3: Reembolso Fallido por Problema de Red**
1. **Sistema intenta** procesar reembolso
2. **Falla** por problema temporal de conectividad
3. **Sistema espera** 1 segundo y reintenta
4. **Falla nuevamente**, espera 2 segundos
5. **Tercer intento** es exitoso
6. **Cliente recibe** confirmación

#### ⏰ **Caso 4: Reembolso Expirado**
1. **Reembolso creado** hace 35 días
2. **Ventana de 30 días** ya expiró
3. **Sistema marca** como expirado
4. **Hotel recibe** notificación para procesar manualmente
5. **Personal contacta** al huésped para coordinar

### Configuración Recomendada

#### 🏨 **Para Hoteles Pequeños (1-20 habitaciones)**
- **Ventana de tiempo**: 30 días
- **Reintentos**: 3 intentos
- **Método principal**: Pago original
- **Notificaciones**: Email + sistema

#### 🏨 **Para Hoteles Medianos (21-100 habitaciones)**
- **Ventana de tiempo**: 45 días
- **Reintentos**: 5 intentos
- **Métodos**: Pago original + transferencia
- **Notificaciones**: Email + sistema + WhatsApp

#### 🏨 **Para Hoteles Grandes (100+ habitaciones)**
- **Ventana de tiempo**: 60 días
- **Reintentos**: 7 intentos
- **Métodos**: Todos disponibles
- **Notificaciones**: Email + sistema + WhatsApp + SMS

### Monitoreo y Reportes

#### 📊 **Dashboard de Reembolsos**
- **Reembolsos pendientes**: Cuántos están esperando procesamiento
- **Reembolsos exitosos**: Porcentaje de éxito
- **Reembolsos fallidos**: Qué necesita atención
- **Tiempo promedio**: Cuánto tarda en procesar

#### 📈 **Reportes Diarios**
- **Resumen del día**: Cuántos se procesaron exitosamente
- **Problemas**: Qué requirió intervención manual
- **Tendencias**: Patrones de fallos para mejorar

#### 🔔 **Alertas Inteligentes**
- **Muchos fallos**: Si hay problemas con la pasarela
- **Reembolsos expirados**: Para contactar huéspedes
- **Problemas de configuración**: Para ajustar parámetros

---

## Flujos de Trabajo del Día a Día

### 1. Recepción Matutina (8:00 AM)

#### Check-outs del Día
```
Opción 1: Check-out Automático (si está habilitado)
1. Sistema verifica cada hora si hay reservas que deben hacer check-out
2. Si la fecha de check-out pasó, procesa automáticamente
3. Si es el día de check-out, espera hasta la hora configurada del hotel
4. Cambia estado a "Check-out" y libera habitación automáticamente
5. Habitación aparece como "Disponible" en el calendario sin intervención manual

Opción 2: Check-out Manual
1. Recepcionista abre el sistema
2. Abre el calendario en vista diaria
3. Ve los check-outs programados visualmente
4. Prepara las facturas
5. Realiza check-outs cuando huéspedes se van
6. Sistema actualiza habitaciones a "Disponible" en el calendario
```

#### Check-ins del Día
```
1. Ve las llegadas esperadas en el calendario
2. Identifica habitaciones asignadas visualmente
3. Verifica pagos pendientes
4. Realiza check-ins cuando huéspedes llegan
5. Sistema actualiza habitaciones a "Ocupada" en el calendario
```

### 2. Gestión de Reservas (Todo el día)

#### Nuevas Reservas
```
1. Cliente consulta disponibilidad en el calendario
2. Sistema muestra habitaciones disponibles visualmente
3. Cliente selecciona habitación y fechas desde el calendario
4. Sistema calcula precio total
5. Cliente completa datos y pago
6. Sistema confirma reserva y actualiza el calendario
```

#### Modificaciones
```
1. Cliente solicita cambio de fecha
2. Sistema verifica nueva disponibilidad
3. Calcula diferencia de precio
4. Aplica cambio si es posible
5. Notifica al cliente
```

#### Cancelaciones
```
1. Cliente solicita cancelación de reserva
2. Sistema evalúa política de cancelación del hotel
3. Sistema calcula penalidades y devoluciones
4. Sistema muestra modal con consecuencias de la cancelación
5. Cliente confirma cancelación conociendo las reglas
6. Sistema actualiza estado de reserva y procesa devolución
7. Sistema envía confirmación de cancelación al cliente
```

### 3. Gestión de Pagos (Todo el día)

#### Pagos con Tarjeta
```
1. Cliente selecciona pago con tarjeta
2. Sistema genera formulario seguro
3. Cliente ingresa datos de tarjeta
4. Mercado Pago procesa pago
5. Sistema confirma automáticamente
```

#### Pagos Manuales
```
1. Cliente paga en efectivo/transferencia
2. Recepcionista registra pago
3. Sistema actualiza saldo
4. Se genera comprobante
```

### 4. Gestión de Reembolsos (Todo el día)

#### Procesamiento de Devoluciones
```
1. Personal revisa lista de reembolsos pendientes
2. Filtra por estado: Procesando, Pendiente
3. Marca como completado los reembolsos procesados
4. Actualiza estado de reembolsos fallidos
5. Verifica detalles de cada reembolso
```

#### Seguimiento de Cancelaciones
```
1. Sistema procesa cancelaciones automáticamente
2. Cliente selecciona método de reembolso (dinero o voucher)
3. Crea reembolsos según método seleccionado
4. Si es voucher: genera código único y notifica al cliente
5. Registra motivo de cancelación
6. Actualiza estado de reembolsos/vouchers
7. Notifica al personal sobre nuevos reembolsos
```

#### Gestión de Vouchers
```
1. Personal revisa vouchers generados
2. Verifica códigos y montos
3. Crea vouchers manuales si es necesario
4. Cancela vouchers expirados o problemáticos
5. Monitorea uso de vouchers en reservas
6. Actualiza estados según uso
```

### 5. Cierre del Día (11:00 PM)

#### Revisión de Métricas
```
1. Gerente revisa dashboard y calendario
2. Analiza ocupación del día visualmente
3. Revisa ingresos generados
4. Identifica oportunidades en el calendario
5. Planifica para el día siguiente usando vista semanal
```

#### Revisión de Reembolsos
```
1. Gerente revisa estadísticas de reembolsos
2. Analiza motivos de cancelación más comunes
3. Evalúa efectividad de políticas de devolución
4. Planifica ajustes en políticas si es necesario
5. Revisa reembolsos pendientes para el día siguiente
```

---

## Casos de Uso Reales

### Caso 1: Hotel Boutique (20 habitaciones)

#### Situación
Hotel pequeño que quiere digitalizar su gestión.

#### Solución AlojaSys
- **Configuración**: 20 habitaciones (10 dobles, 8 triples, 2 suites)
- **Política de pago**: 50% adelanto, 50% al check-in
- **Tarifas**: Precios fijos con promociones de fin de semana
- **Personal**: 1 recepcionista, 1 gerente

#### Resultado
- ✅ **Gestión simplificada** de reservas
- ✅ **Pagos automatizados** con Mercado Pago
- ✅ **Control de ocupación** en tiempo real
- ✅ **Reportes automáticos** para el gerente

### Caso 2: Cadena Hotelera (5 hoteles)

#### Situación
Grupo hotelero que necesita gestionar múltiples propiedades.

#### Solución AlojaSys
- **Configuración**: 5 hoteles en diferentes ciudades
- **Políticas**: Estándar para todos los hoteles
- **Personal**: Compartido entre hoteles
- **Reportes**: Consolidados del grupo

#### Resultado
- ✅ **Gestión centralizada** de todos los hoteles
- ✅ **Configuraciones consistentes**
- ✅ **Personal flexible** entre hoteles
- ✅ **Análisis comparativo** entre propiedades

### Caso 3: Hotel de Temporada

#### Situación
Hotel que maneja precios dinámicos según la temporada.

#### Solución AlojaSys
- **Tarifas**: Precios altos en temporada alta, bajos en baja
- **Promociones**: Códigos para temporada baja
- **Restricciones**: CTA en fechas de mantenimiento
- **Impuestos**: Automáticos según la región

#### Resultado
- ✅ **Precios dinámicos** según demanda
- ✅ **Promociones efectivas** para temporada baja
- ✅ **Control de restricciones** automático
- ✅ **Maximización de ingresos**

### Caso 4: Hotel con Políticas de Cancelación Flexibles

#### Situación
Hotel que necesita diferentes políticas de cancelación según el tipo de habitación y temporada.

#### Solución AlojaSys
- **Políticas diferenciadas**: Por tipo de habitación y temporada
- **Tiempos configurables**: 24h, 48h, 7 días según política
- **Penalidades flexibles**: Porcentaje, monto fijo, por noches
- **Mensajes personalizados**: Para cada tipo de cancelación
- **Targeting avanzado**: Por canal de reserva y temporada

#### Resultado
- ✅ **Flexibilidad total** en políticas de cancelación
- ✅ **Protección de ingresos** con penalidades configurables
- ✅ **Transparencia** con mensajes claros para huéspedes
- ✅ **Adaptación** a diferentes tipos de negocio

### Caso 5: Hotel con Gestión Completa de Reembolsos

#### Situación
Hotel que necesita gestionar devoluciones de manera profesional y transparente.

#### Solución AlojaSys
- **Políticas de devolución**: Configurables por hotel
- **Múltiples métodos**: Original payment, transferencia, voucher
- **Tiempos claros**: 3-7 días de procesamiento
- **Gestión centralizada**: Lista completa de reembolsos
- **Seguimiento de estado**: Pendiente, Procesando, Completado
- **Motivo obligatorio**: En todas las cancelaciones

#### Resultado
- ✅ **Gestión profesional** de devoluciones
- ✅ **Transparencia total** para huéspedes
- ✅ **Control centralizado** de reembolsos
- ✅ **Trazabilidad completa** de cancelaciones
- ✅ **Satisfacción del cliente** mejorada

#### Caso 6: Hotel con Auditoría Avanzada de Reembolsos

#### Situación
Hotel que necesita cumplir con regulaciones financieras y mantener auditoría completa de transacciones.

#### Solución AlojaSys (v2.0)
- **Trazabilidad completa**: Registro de quién procesó cada reembolso
- **Auditoría histórica**: Snapshot de políticas aplicadas en cada reserva
- **Flexibilidad financiera**: Reembolsos sin pago original asociado
- **Escalabilidad**: Soporte para montos más grandes
- **Consistencia legal**: Políticas históricas garantizadas

#### Resultado
- ✅ **Cumplimiento regulatorio** completo
- ✅ **Auditoría profesional** de transacciones
- ✅ **Trazabilidad total** de operaciones
- ✅ **Flexibilidad operativa** mejorada
- ✅ **Escalabilidad** para crecimiento

#### Caso 7: Hotel con Control Granular de Reembolsos

#### Situación
Hotel que necesita control granular sobre cuándo procesar reembolsos automáticamente y respetar limitaciones de pasarelas de pago.

#### Solución AlojaSys (v2.1)
- **Control por política**: Cada política puede habilitar/deshabilitar reembolsos automáticos
- **Limitaciones de pasarela**: Configuración de días límite y reembolsos parciales por proveedor
- **Validaciones automáticas**: Sistema respeta automáticamente las restricciones
- **Configuración independiente**: Por hotel, política y pasarela de pago
- **Prevención de errores**: Validaciones robustas de configuraciones

#### Resultado
- ✅ **Control granular** sobre procesamiento de reembolsos
- ✅ **Cumplimiento automático** con limitaciones de proveedores
- ✅ **Flexibilidad operativa** para diferentes tipos de negocio
- ✅ **Prevención de errores** en configuraciones
- ✅ **Configuración independiente** por hotel y política

#### Caso 8: Hotel con Procesamiento Avanzado de Reembolsos

#### Situación
Hotel que necesita un sistema robusto para procesar reembolsos a través de múltiples pasarelas de pago con validaciones automáticas y reintentos inteligentes.

#### Solución AlojaSys (v2.2)
- **Adaptadores de pasarelas**: Soporte para MercadoPago, transferencias bancarias y efectivo
- **Validaciones automáticas**: Ventana de tiempo y reembolsos parciales por pasarela
- **Reintentos inteligentes**: Backoff exponencial para fallos temporales
- **Modo de prueba**: Desarrollo seguro sin costos reales
- **Logging completo**: Auditoría detallada de todas las operaciones

#### Resultado
- ✅ **Procesamiento robusto** con múltiples pasarelas
- ✅ **Validaciones automáticas** previenen errores
- ✅ **Reintentos inteligentes** aumentan la confiabilidad
- ✅ **Desarrollo seguro** en modo de prueba
- ✅ **Auditoría completa** de todas las transacciones

#### Caso 9: Hotel con Pantalla de Éxito Detallada para Cancelaciones

#### Situación
Hotel que quiere proporcionar una experiencia de cancelación transparente y profesional, donde los clientes reciban información completa e inmediata sobre sus reembolsos.

#### Solución AlojaSys (v2.1)
- **Pantalla de éxito detallada**: Información completa del reembolso inmediatamente después de cancelar
- **Transparencia financiera**: Desglose claro de penalidades y devoluciones
- **Trazabilidad total**: IDs de reembolso para seguimiento
- **Próximos pasos claros**: Información específica según el tipo de reembolso
- **Información de contacto**: Datos del hotel para consultas
- **Estados en tiempo real**: Saber si el reembolso ya se procesó

#### Resultado
- ✅ **Experiencia premium** para los clientes
- ✅ **Menos consultas** al hotel sobre reembolsos
- ✅ **Transparencia total** en el proceso de cancelación
- ✅ **Confianza del cliente** con información detallada
- ✅ **Diferenciación competitiva** con sistema profesional

#### Ejemplo Práctico: Cliente con Cancelación Compleja
```
Situación:
- Cliente cancela reserva de $500,000
- Política: Penalidad 25% después de 48h
- Método de pago: Transferencia bancaria
- Tiempo: 36 horas antes del check-in

Pantalla de Éxito Mostrada:
✅ ¡Cancelación Exitosa!

📋 Información del Reembolso:
• ID: #REF-12348
• Monto: $375,000
• Estado: Pendiente
• Método: Transferencia bancaria
• Tiempo estimado: 5-7 días hábiles

💰 Resumen Financiero:
• Total pagado: $500,000
• Penalidad (25%): -$125,000
• Devolución: +$375,000

📧 Próximos pasos:
• El hotel te contactará para datos bancarios
• Recibirás confirmación por email
• Tiempo estimado: 5-7 días hábiles

Resultado:
- Cliente entiende exactamente qué va a pasar
- No llama al hotel con preguntas
- Confía en el proceso del hotel
- Tiene ID de reembolso para seguimiento
```

#### Caso 10: Hotel con Gestión Avanzada de NO_SHOW

#### Situación
Hotel que necesita gestionar automáticamente las reservas no-show con penalidades específicas, reembolsos diferenciados y notificaciones detalladas para diferentes tipos de usuarios.

#### Solución AlojaSys (v2.0 - NO_SHOW Mejorado)
- **Penalidades automáticas**: Aplicación automática según políticas de cancelación
- **Reembolsos específicos**: Configuraciones diferenciadas para NO_SHOW vs cancelaciones normales
- **Notificaciones mejoradas**: Mensajes detallados para hotel, huésped y administradores
- **Múltiples métodos de reembolso**: Voucher, transferencia bancaria, pago original, manual
- **Configuraciones granulares**: Por hotel, política y tipo de reembolso
- **Logs detallados**: Trazabilidad completa de penalidades y reembolsos

#### Resultado
- ✅ **Gestión automática** de penalidades por NO_SHOW
- ✅ **Reembolsos específicos** con configuraciones flexibles
- ✅ **Notificaciones diferenciadas** por tipo de usuario
- ✅ **Transparencia total** en penalidades y reembolsos
- ✅ **Configuración granular** de políticas NO_SHOW
- ✅ **Trazabilidad completa** del flujo financiero

#### Ejemplo Práctico: Hotel Boutique con Política NO_SHOW
```
Configuración del hotel:
- Política de cancelación: 100% de penalidad para NO_SHOW
- Política de reembolso NO_SHOW: 25% como voucher
- Método de reembolso: Voucher con validez de 365 días
- Días de procesamiento: 45 días
- Auto no-show: Habilitado

Escenario:
1. Reserva confirmada por $200,000
2. Huésped no se presenta (NO_SHOW)
3. Sistema aplica penalidad del 100% ($200,000)
4. Sistema calcula reembolso del 25% ($50,000)
5. Sistema crea voucher por $50,000 válido por 365 días
6. Sistema notifica al hotel con información financiera completa
7. Sistema notifica al huésped con próximos pasos claros
8. Sistema registra logs detallados de penalidad y reembolso

Resultado:
- Hotel: Recibe $200,000 (penalidad completa)
- Huésped: Recibe voucher de $50,000 para futuras reservas
- Sistema: Procesamiento automático sin intervención manual
```

---

## Beneficios del Sistema

### Para el Hotel
- 🏨 **Gestión eficiente** de habitaciones y reservas
- 📆 **Visualización clara** de ocupación en calendario
- 💰 **Maximización de ingresos** con precios dinámicos
- 📊 **Análisis del negocio** con métricas en tiempo real
- 🔒 **Pagos seguros** con integración bancaria
- ⚡ **Automatización** de procesos repetitivos
- 💸 **Gestión profesional** de reembolsos y devoluciones
- 🔄 **Procesamiento automático** de cancelaciones

### Beneficios del Modal de Cancelación Mejorado
- 🎯 **Transparencia total**: Los clientes saben exactamente qué esperar
- 📞 **Menos consultas**: Información clara reduce llamadas al hotel
- 🔧 **Procesos claros**: Staff sabe cuándo intervenir manualmente
- ♿ **Accesibilidad**: Cumple estándares de accesibilidad web
- ✨ **Experiencia profesional**: Interfaz moderna y confiable
- 🚀 **Preparado para el futuro**: Opciones para roles de staff
- 📋 **Pantalla de éxito detallada**: Información completa del reembolso inmediatamente
- 💰 **Transparencia financiera**: Desglose completo de penalidades y devoluciones
- 🔍 **Trazabilidad total**: IDs de reembolso para seguimiento
- ⚡ **Feedback inmediato**: Confirmación instantánea con todos los detalles
- 🔍 **Trazabilidad completa** de transacciones financieras
- 📋 **Auditoría histórica** de políticas aplicadas
- ⚖️ **Cumplimiento regulatorio** mejorado
- 🎛️ **Control granular** de reembolsos automáticos
- 🔧 **Limitaciones configurables** por pasarela de pago
- 🏗️ **Sistema modular** de adaptadores de pasarelas
- 🔄 **Reintentos inteligentes** para mayor confiabilidad
- 🧪 **Modo de prueba** para desarrollo seguro
- 📈 **Escalabilidad** para múltiples proveedores
- 🚨 **Gestión automática de NO_SHOW** con penalidades específicas
- 🤖 **Procesamiento automático de reembolsos** 24/7
- ⏰ **Validación de ventanas de tiempo** por pasarela
- 🔄 **Reintentos inteligentes** para fallos temporales
- 📊 **Monitoreo completo** de reembolsos y estadísticas
- 💳 **Reembolsos diferenciados** para NO_SHOW vs cancelaciones normales
- 🔔 **Notificaciones detalladas** con información financiera completa
- ⚙️ **Configuraciones granulares** de políticas NO_SHOW
- 📊 **Métricas específicas** de impacto financiero por NO_SHOW

### Para el Personal
- 👥 **Interfaz intuitiva** fácil de usar
- 📆 **Calendario visual** para gestión de reservas
- 🔍 **Información centralizada** en un solo lugar
- 📱 **Acceso desde cualquier dispositivo**
- 🚫 **Menos errores** con validaciones automáticas
- 📈 **Reportes automáticos** para análisis
- 💸 **Gestión centralizada** de reembolsos
- 🔄 **Procesamiento automático** de devoluciones
- 🔍 **Trazabilidad completa** de operaciones
- 📋 **Auditoría simplificada** de transacciones
- ⚖️ **Cumplimiento facilitado** de regulaciones
- 🎛️ **Control granular** sobre procesamiento de reembolsos
- 🔧 **Validaciones automáticas** de limitaciones de pasarelas
- 🏗️ **Múltiples opciones** de pasarelas de pago
- 🔄 **Reintentos automáticos** en caso de fallos
- 🧪 **Testing seguro** en modo de prueba
- 📊 **Logging detallado** para seguimiento
- 🚨 **Procesamiento automático** de penalidades NO_SHOW
- 🔔 **Notificaciones diferenciadas** por tipo de usuario
- 💰 **Información financiera** clara y detallada
- ⚙️ **Configuración granular** de políticas NO_SHOW
- 📋 **Acciones específicas** según tipo de reembolso

### Para los Huéspedes
- 🌐 **Reservas online** 24/7
- 💳 **Pagos seguros** con tarjeta
- 📧 **Confirmaciones automáticas** por email
- 🔄 **Modificaciones fáciles** de reservas
- 📱 **Experiencia digital** completa
- 💸 **Devoluciones transparentes** y rápidas
- 🔄 **Cancelaciones fáciles** con motivo obligatorio
- 📋 **Pantalla de éxito detallada** con información completa del reembolso
- 💰 **Transparencia financiera total** en cancelaciones
- 🔍 **Trazabilidad completa** con IDs de reembolso
- ⚡ **Feedback inmediato** sobre el estado del reembolso
- 📊 **Desglose financiero claro** de penalidades y devoluciones
- 🎯 **Próximos pasos claros** según el tipo de reembolso
- ⚡ **Procesamiento más rápido** de reembolsos automáticos
- 🔧 **Cumplimiento** con políticas del proveedor de pago
- 🏗️ **Múltiples métodos** de reembolso disponibles
- 🔄 **Procesamiento confiable** con reintentos automáticos
- ⚡ **Tiempos de procesamiento** más rápidos y consistentes
- 🚨 **Transparencia total** en penalidades por NO_SHOW
- 📋 **Información detallada** de la reserva y consecuencias
- ✅ **Próximos pasos claros** según tipo de reembolso
- 💳 **Múltiples opciones** de reembolso para NO_SHOW
- ⏰ **Tiempos de procesamiento** claros y realistas
- 📞 **Información de contacto** del hotel para consultas

### Para la Empresa
- 🏢 **Gestión multi-hotel** desde una plataforma
- 📊 **Reportes consolidados** del grupo
- ⚙️ **Configuraciones centralizadas**
- 👥 **Personal compartido** entre hoteles
- 📈 **Escalabilidad** para crecer

---

## 3.12 Sistema de Notificaciones

### ¿Qué es el Sistema de Notificaciones?

El **Sistema de Notificaciones** es como tener un asistente personal que te mantiene informado sobre todo lo que sucede en tu hotel de manera automática. Es como recibir mensajes importantes en tu teléfono, pero directamente en el sistema.

### ¿Por qué es Importante?

Imagina que tienes 50 habitaciones y 100 reservas activas. ¿Cómo sabes si:
- Una reserva se canceló automáticamente porque no se pagó el adelanto?
- Un huésped no se presentó (no-show)?
- Un reembolso se procesó correctamente?
- Hay algún problema que requiere tu atención?

**¡El sistema te notifica automáticamente!** 🔔

### ¿Qué Notificaciones Recibes?

#### 🔴 **Auto-Cancelaciones**
- **Cuándo**: Reservas que se cancelan automáticamente
- **Motivos**:
  - Depósito vencido sin pago
  - Días desde creación excedidos
  - Fecha de check-in vencida sin pago
- **Ejemplo**: "La reserva #RES-123 en Hotel Central fue cancelada automáticamente. Motivo: Depósito vencido sin pago (vencía: 15/01/2024)"

#### 🟠 **Cancelaciones Manuales**
- **Cuándo**: El personal cancela una reserva manualmente
- **Ejemplo**: "La reserva #RES-456 en Hotel Central fue cancelada manualmente. Motivo: Cliente solicitó cancelación"

#### 🟣 **No-Shows**
- **Cuándo**: Reservas confirmadas que no se presentaron
- **Ejemplo**: "La reserva #RES-789 en Hotel Central fue marcada como No-Show. Fecha de check-in: 16/01/2024"

#### 🟡 **Reembolsos Exitosos**
- **Cuándo**: Reembolsos procesados correctamente
- **Ejemplo**: "Reembolso de $150.00 para la reserva #RES-101 en Hotel Central. Estado: completado"

#### 🟠 **Reembolsos Fallidos**
- **Cuándo**: Reembolsos que no se pudieron procesar
- **Ejemplo**: "Reembolso de $200.00 para la reserva #RES-102 en Hotel Central. Estado: fallido"

### Funcionalidades Principales

#### 🔔 Notificaciones Automáticas
- **Auto-cancelaciones**: Te avisa cuando una reserva se cancela automáticamente
- **No-shows**: Te informa cuando un huésped no se presenta
- **Reembolsos**: Te notifica si un reembolso se procesó o falló
- **Eventos del sistema**: Cualquier acción automática importante

#### 📱 Interfaz Intuitiva
- **Campanita en el header**: Siempre visible, con contador de notificaciones
- **Dropdown rápido**: Ve las últimas 5 notificaciones sin salir de la página
- **Página completa**: Gestiona todas las notificaciones con filtros
- **Colores diferenciados**: Cada tipo de notificación tiene su color

#### 🎯 Tipos de Notificaciones

| Tipo | Color | ¿Qué Significa? |
|------|-------|-----------------|
| 🔴 **Auto Cancelación** | Rojo | Una reserva se canceló automáticamente |
| 🟣 **No Show** | Púrpura | Un huésped no se presentó |
| 🟡 **Reembolso Exitoso** | Amarillo | Un reembolso se procesó correctamente |
| 🟠 **Reembolso Fallido** | Naranja | Hubo un problema con un reembolso |

### ¿Cómo Funciona?

#### 1. **Creación Automática**
El sistema crea notificaciones automáticamente cuando:
- Una reserva PENDING se cancela por depósito vencido
- Una reserva CONFIRMED se marca como no-show
- Un reembolso automático se procesa (exitoso o fallido)

#### 2. **Visualización Inmediata**
- Aparece una campanita 🔔 en el header
- El número rojo muestra cuántas notificaciones sin leer tienes
- Haces clic y ves las últimas 5 notificaciones

#### 3. **Gestión Completa**
- Puedes ir a la página de notificaciones para ver todas
- Filtrar por tipo (cancelaciones, no-shows, reembolsos)
- Marcar como leídas individualmente o todas juntas

### Ejemplos Reales

#### Ejemplo 1: Auto-cancelación
```
🔴 Reserva cancelada automáticamente
La reserva #RES-123 en Hotel Central fue cancelada 
automáticamente. Motivo: Depósito vencido sin pago 
(vencía: 15/01/2024)
```

#### Ejemplo 2: No-show
```
🟣 Reserva marcada como No-Show
La reserva #RES-456 en Hotel Central fue marcada como 
No-Show. Fecha de check-in: 16/01/2024
```

#### Ejemplo 3: Reembolso Exitoso
```
🟡 Reembolso procesado automáticamente
Reembolso de $150.00 para la reserva #RES-789 en Hotel 
Central. Estado: success
```

### Beneficios para el Negocio

#### Para el Gerente
- **Visibilidad total**: Sabes todo lo que pasa en tu hotel
- **Control inmediato**: Puedes actuar rápido ante problemas
- **Historial completo**: Tienes registro de todos los eventos
- **Menos sorpresas**: No te enteras de problemas después

#### Para el Personal
- **Información centralizada**: Todo en un solo lugar
- **Fácil de usar**: Solo hacer clic en la campanita
- **Actualizaciones automáticas**: No necesitas buscar información
- **Priorización visual**: Los colores te ayudan a identificar urgencias

#### Para la Operación
- **Proactividad**: Puedes anticipar problemas
- **Eficiencia**: Menos tiempo buscando información
- **Trazabilidad**: Sabes exactamente qué pasó y cuándo
- **Mejora continua**: Puedes analizar patrones de problemas

### Casos de Uso Reales

#### Caso 1: Depósito Vencido
**Situación**: Un huésped no pagó el adelanto a tiempo
**Sistema**: Cancela automáticamente la reserva
**Notificación**: Te avisa inmediatamente con todos los detalles
**Acción**: Puedes contactar al huésped o liberar la habitación

#### Caso 2: No-Show
**Situación**: Un huésped confirmado no se presenta
**Sistema**: Marca la reserva como no-show
**Notificación**: Te informa para que puedas gestionar la habitación
**Acción**: Puedes liberar la habitación o aplicar políticas

#### Caso 3: Reembolso Fallido
**Situación**: Un reembolso automático no se pudo procesar
**Sistema**: Intenta varias veces, luego marca como fallido
**Notificación**: Te avisa del problema
**Acción**: Puedes procesar el reembolso manualmente

#### Caso 4: Voucher de Crédito Generado
**Situación**: Un cliente cancela y elige voucher en lugar de dinero
**Sistema**: Genera voucher con código único automáticamente
**Notificación**: Te avisa del voucher generado con código y monto
**Acción**: Puedes verificar el voucher en la gestión de vouchers

#### Caso 5: Voucher Aplicado en Nueva Reserva
**Situación**: Un cliente usa un voucher en una nueva reserva
**Sistema**: Valida el voucher y aplica el descuento
**Notificación**: Te avisa del voucher usado y la reserva creada
**Acción**: Puedes ver el historial de uso del voucher

### Configuración y Personalización

#### Filtros Disponibles
- **Por tipo**: Solo cancelaciones, solo no-shows, etc.
- **Por estado**: Solo no leídas, solo leídas
- **Por hotel**: Si manejas múltiples hoteles
- **Por fecha**: Notificaciones de un período específico

#### Acciones Rápidas
- **Marcar como leída**: Clic en el botón ✓
- **Ver todas**: Ir a la página completa
- **Marcar todas como leídas**: Botón para limpiar todas
- **Refrescar**: Actualizar la lista manualmente

### Integración con Otros Módulos

#### Con Gestión de Reservas
- Notificaciones cuando se cancelan reservas
- Alertas de no-shows para gestión de habitaciones
- Información contextual de la reserva

#### Con Sistema de Pagos
- Notificaciones de reembolsos exitosos o fallidos
- Alertas de problemas de procesamiento
- Información financiera detallada

#### Con Dashboard
- Resumen de notificaciones recientes
- Métricas de eventos del sistema
- Indicadores de salud operativa

### Ventajas Competitivas

#### vs. Sistemas Tradicionales
- **Automatización**: No necesitas revisar manualmente
- **Tiempo real**: Información inmediata
- **Contexto completo**: Todos los detalles en un lugar
- **Historial**: Registro permanente de eventos

#### vs. Emails
- **No spam**: Solo notificaciones importantes
- **Centralizado**: Todo en el sistema
- **Interactivo**: Puedes actuar directamente
- **Organizado**: Fácil de gestionar y filtrar

### Mejores Prácticas

#### Para el Gerente
1. **Revisa diariamente** las notificaciones
2. **Actúa rápidamente** ante alertas críticas
3. **Analiza patrones** para mejorar procesos
4. **Configura filtros** según tus necesidades

#### Para el Personal
1. **Marca como leídas** las notificaciones procesadas
2. **Usa los filtros** para encontrar información específica
3. **Revisa el contexto** antes de tomar acciones
4. **Comunica problemas** al equipo cuando sea necesario

### Mejoras NO_SHOW v2.0 - Sistema Avanzado de Penalidades y Reembolsos

#### ¿Qué es el Sistema NO_SHOW Mejorado?
El **Sistema NO_SHOW v2.0** es una evolución del sistema básico que no solo marca reservas como no-show, sino que también aplica penalidades automáticas, calcula reembolsos específicos y genera notificaciones detalladas para diferentes tipos de usuarios.

#### Características Principales

##### 🚨 Penalidades Automáticas
- **Aplicación automática** según políticas de cancelación del hotel
- **Cálculo inteligente** basado en el monto total pagado
- **Flexibilidad total** en tipos de penalidad (porcentaje, monto fijo, por noches)
- **Registro detallado** de todas las penalidades aplicadas

##### 💳 Reembolsos Específicos para NO_SHOW
- **Configuraciones diferenciadas** para NO_SHOW vs cancelaciones normales
- **Múltiples métodos** de reembolso (voucher, transferencia, pago original, manual)
- **Porcentajes específicos** para NO_SHOW (ej: 25% vs 50% para cancelaciones)
- **Días de procesamiento** diferenciados (ej: 45 días vs 30 días)
- **Vouchers con validez extendida** (365 días para NO_SHOW)

##### 🔔 Notificaciones Mejoradas
- **Mensajes diferenciados** por tipo de usuario (hotel, huésped, administrador)
- **Información financiera completa** (total pagado, penalidad, reembolso, pérdida neta)
- **Acciones específicas** según el tipo de reembolso
- **Próximos pasos claros** para cada tipo de usuario
- **Información de contacto** del hotel para consultas

#### Ejemplo Práctico: Hotel con Política NO_SHOW

##### Configuración del Hotel
```
Política de Cancelación:
- NO_SHOW: 100% de penalidad (no hay cancelación gratuita)
- Penalidad: Porcentaje del total pagado
- Aplicación: Todas las habitaciones

Política de Reembolso NO_SHOW:
- Porcentaje de reembolso: 25%
- Método: Voucher de crédito
- Validez del voucher: 365 días
- Días de procesamiento: 45 días
- Requiere datos del huésped: No (voucher automático)
```

##### Escenario de NO_SHOW
```
1. Reserva confirmada:
   - Código: RES-12345
   - Hotel: Hotel Plaza Central
   - Habitación: Suite 101
   - Fechas: 15/01/2024 - 18/01/2024 (3 noches)
   - Huéspedes: 2 personas
   - Total pagado: $300,000

2. Huésped no se presenta (NO_SHOW):
   - Fecha de check-in: 15/01/2024 (ya pasó)
   - Sistema detecta automáticamente

3. Procesamiento automático:
   - Cambia estado a NO_SHOW
   - Aplica penalidad del 100%: $300,000
   - Calcula reembolso del 25%: $75,000
   - Crea voucher por $75,000 válido por 365 días
   - Genera notificaciones detalladas

4. Notificación para el Hotel:
   "🚨 RESERVA NO_SHOW DETECTADA
   
   📋 Detalles de la reserva:
   • Código: RES-12345
   • Huéspedes: 2
   • Habitación: Suite 101
   • Check-in: 15/01/2024
   • Check-out: 18/01/2024
   
   💰 Impacto financiero:
   • Total pagado: $300,000
   • Penalidad aplicada: $300,000
   • Reembolso: $75,000
   • Pérdida neta: $225,000
   
   📝 Acciones requeridas:
   • Procesar reembolso de $75,000
   • Actualizar estadísticas de NO_SHOW
   • Revisar política de cancelación si es necesario"

5. Notificación para el Huésped:
   "❌ SU RESERVA FUE MARCADA COMO NO_SHOW
   
   📋 Detalles de su reserva:
   • Código: RES-12345
   • Hotel: Hotel Plaza Central
   • Habitación: Suite 101
   • Fecha de llegada: 15/01/2024
   • Fecha de salida: 18/01/2024
   
   💰 Información financiera:
   • Total pagado: $300,000
   • Penalidad aplicada: $300,000
   • Reembolso disponible: $75,000
   
   ✅ PRÓXIMOS PASOS:
   • Su reembolso será procesado según la política del hotel
   • Recibirá más información por email
   • El proceso puede tomar hasta 45 días hábiles"

6. Resultado final:
   - Hotel: Recibe $300,000 (penalidad completa)
   - Huésped: Recibe voucher de $75,000 para futuras reservas
   - Sistema: Procesamiento automático sin intervención manual
   - Trazabilidad: Logs detallados de penalidad y reembolso
```

#### Beneficios del Sistema NO_SHOW v2.0

##### Para el Hotel
- ✅ **Protección de ingresos** con penalidades automáticas
- ✅ **Flexibilidad** en configuraciones de reembolso
- ✅ **Transparencia** con notificaciones detalladas
- ✅ **Automatización** completa del proceso
- ✅ **Trazabilidad** de todas las operaciones
- ✅ **Configuración granular** por hotel y política

##### Para el Personal
- ✅ **Menos trabajo manual** con procesamiento automático
- ✅ **Información clara** sobre penalidades y reembolsos
- ✅ **Notificaciones diferenciadas** por tipo de usuario
- ✅ **Acciones específicas** según el tipo de reembolso
- ✅ **Configuración flexible** de políticas

##### Para el Huésped
- ✅ **Transparencia total** en penalidades y reembolsos
- ✅ **Información detallada** de la reserva y consecuencias
- ✅ **Próximos pasos claros** según el tipo de reembolso
- ✅ **Múltiples opciones** de reembolso disponibles
- ✅ **Tiempos de procesamiento** claros y realistas

#### Beneficios del Procesamiento Automático de Reembolsos

##### Para el Hotel
- ✅ **Ahorro de tiempo** con procesamiento automático 24/7
- ✅ **Reducción de errores** humanos en reembolsos
- ✅ **Mejor flujo de caja** con reembolsos más rápidos
- ✅ **Trazabilidad completa** de todos los reembolsos
- ✅ **Configuración flexible** por pasarela de pago
- ✅ **Notificaciones inteligentes** solo cuando es necesario
- ✅ **Estadísticas detalladas** de éxito y fallos

##### Para el Personal
- ✅ **Menos trabajo manual** con solo excepciones
- ✅ **Notificaciones claras** sobre qué revisar
- ✅ **Proceso guiado** para casos especiales
- ✅ **Tiempo para tareas importantes** en lugar de reembolsos
- ✅ **Confianza** en el sistema automático

##### Para el Cliente
- ✅ **Reembolsos más rápidos** (minutos vs días)
- ✅ **Mayor confiabilidad** con reintentos automáticos
- ✅ **Transparencia total** del estado del reembolso
- ✅ **Menos contacto** con el hotel para reembolsos
- ✅ **Mejor experiencia** general de cancelación

### Futuras Mejoras

#### Próximas Funcionalidades
- **Notificaciones por email**: Para eventos críticos
- **Sonidos personalizados**: Diferentes tonos por tipo
- **Notificaciones push**: Para dispositivos móviles
- **Integración con WhatsApp**: Para comunicación directa

#### Personalización Avanzada
- **Horarios de notificación**: Solo en horario laboral
- **Prioridades personalizadas**: Qué notificaciones son más importantes
- **Grupos de usuarios**: Diferentes notificaciones por rol
- **Escalación automática**: Notificar a supervisores si no se atiende

## 3.13 Facturación Electrónica Argentina

### ¿Qué hace?

El módulo de **Facturación Electrónica Argentina** permite generar y gestionar facturas electrónicas que cumplen con las normativas de AFIP (Administración Federal de Ingresos Públicos) de Argentina. Es como tener un contador digital que se encarga automáticamente de toda la documentación fiscal.

### ¿Cómo funciona?

#### Configuración Inicial
1. **Configuración AFIP**: Se configura el CUIT del hotel, punto de venta y certificados digitales
2. **Tipos de Factura**: El sistema soporta todos los tipos de comprobantes argentinos:
   - **Factura A**: Para responsables inscriptos
   - **Factura B**: Para consumidores finales
   - **Factura C**: Para exentos de IVA
   - **Factura E**: Para exportaciones
   - **Nota de Crédito**: Para devoluciones
   - **Nota de Débito**: Para ajustes

#### Proceso Automático
1. **Detección de Pago**: Cuando se procesa un pago, el sistema detecta automáticamente si necesita factura
2. **Generación Automática**: Se crea la factura con todos los datos del huésped y la reserva
3. **Envío a AFIP**: La factura se envía automáticamente a AFIP para obtener el CAE (Código de Autorización Electrónica)
4. **Generación de PDF**: Se crea un PDF profesional de la factura
5. **Notificación**: Se notifica al huésped con la factura adjunta

#### Ejemplo Práctico
**Escenario**: Un huésped se hospeda en el hotel y paga con tarjeta de crédito.

1. **Pago Procesado**: El sistema detecta que el pago fue exitoso
2. **Datos del Cliente**: El sistema obtiene automáticamente:
   - Nombre y apellido del huésped
   - CUIT/DNI del cliente
   - Dirección de facturación
   - Detalles de la reserva (noches, habitación, servicios)

3. **Creación de Factura**: Se genera automáticamente:
   - Número de factura secuencial (ej: 0001-00001234)
   - Fecha de emisión
   - Detalle de servicios (alojamiento, desayuno, etc.)
   - Cálculo de IVA
   - Total a pagar

4. **Envío a AFIP**: La factura se envía a AFIP y se obtiene el CAE
5. **PDF Fiscal Generado**: Se crea un PDF profesional que incluye:
   - Logo del hotel y datos fiscales
   - Información completa del cliente
   - Detalle de servicios con IVA
   - CAE y fecha de vencimiento
   - Código QR para verificación AFIP
6. **Email al Cliente**: Se envía automáticamente la factura por email

### Características Principales

#### 🧾 **Tipos de Comprobantes**
- **Factura A**: Para empresas responsables inscriptas
- **Factura B**: Para consumidores finales
- **Factura C**: Para exentos de IVA
- **Factura E**: Para exportaciones
- **Nota de Crédito**: Para devoluciones y cancelaciones
- **Nota de Débito**: Para ajustes y recargos

#### 🔧 **Funcionalidades Automáticas**
- ✅ **Generación automática** desde reservas
- ✅ **Envío automático a AFIP** con autenticación segura
- ✅ **Obtención de CAE** automática y validación
- ✅ **Generación de PDFs** profesionales con logo del hotel
- ✅ **Email automático** al cliente con factura adjunta
- ✅ **Código QR** para verificación AFIP en cada factura
- ✅ **Numeración secuencial** automática (formato: 0001-00001234)
- ✅ **Cálculo de IVA** automático según normativas
- ✅ **Reintentos automáticos** en caso de error
- ✅ **Validación de datos** antes del envío
- ✅ **Cache de autenticación** para mayor eficiencia
- ✅ **Notas de crédito automáticas** al procesar reembolsos
- ✅ **Vinculación de documentos** (facturas con sus notas de crédito)
- ✅ **Manejo de errores** inteligente y notificaciones

#### 📊 **Gestión y Control**
- **Dashboard de Facturas**: Vista general de todas las facturas
- **Estados de Factura**: Borrador, Enviada, Aprobada, Error
- **Búsqueda Avanzada**: Por fecha, cliente, número, estado
- **Reportes**: Facturas emitidas, ingresos, errores
- **Conciliación**: Con pagos y reservas

#### 🔄 **Automatización Inteligente**

##### **Generación Automática de Facturas**
El sistema genera facturas automáticamente cuando:
- ✅ Un pago es **aprobado** exitosamente
- ✅ Se completa una **reserva** con pago
- ✅ Se procesa un **check-in** con pago pendiente

**Proceso Automático**:
1. **Detección**: El sistema detecta el pago aprobado
2. **Validación**: Verifica que no exista factura previa
3. **Configuración**: Obtiene la configuración AFIP del hotel
4. **Generación**: Crea la factura con datos del pago y reserva
5. **Envío**: Envía automáticamente a AFIP (opcional)
6. **PDF**: Genera el PDF fiscal con CAE
7. **Email**: Envía la factura al cliente

##### **Generación Automática de Notas de Crédito**
El sistema genera notas de crédito automáticamente cuando:
- ✅ Se procesa un **reembolso** aprobado
- ✅ Se cancela una **reserva** con factura existente
- ✅ Se requiere un **ajuste** de factura

**Proceso Automático**:
1. **Detección**: El sistema detecta el reembolso aprobado
2. **Vinculación**: Busca la factura original del pago
3. **Validación**: Verifica que la factura esté aprobada
4. **Generación**: Crea la nota de crédito vinculada
5. **Envío**: Envía automáticamente a AFIP (opcional)
6. **PDF**: Genera el PDF fiscal con CAE
7. **Email**: Envía la nota de crédito al cliente

#### 🌐 **APIs y Endpoints Disponibles**

##### **Endpoints Principales**
- **`POST /api/invoices/generate-from-payment/{id}/`**
  - Genera factura automáticamente desde un pago
  - Incluye datos del cliente y items personalizados
  - Opción de envío automático a AFIP

- **`GET /api/invoices/by-reservation/{id}/`**
  - Lista todas las facturas de una reserva
  - Filtros por tipo y estado
  - Incluye notas de crédito relacionadas

- **`POST /api/invoices/{id}/create-credit-note/`**
  - Crea nota de crédito desde factura existente
  - Vinculación automática con factura original
  - Validación de totales y datos

##### **Endpoints de Gestión**
- **`GET /api/invoices/{id}/pdf/`** - Obtener PDF de factura
- **`GET /api/invoices/{id}/download-pdf/`** - Descargar PDF
- **`POST /api/invoices/{id}/send-to-afip/`** - Enviar a AFIP
- **`POST /api/invoices/{id}/retry/`** - Reintentar envío
- **`GET /api/invoices/{id}/summary/`** - Resumen de factura

##### **Endpoints de Estado**
- **`GET /api/afip/status/`** - Estado general de AFIP
- **`GET /api/afip-configs/{id}/test-connection/`** - Probar conexión

#### 🔗 **Integración con Otros Módulos**

##### **Módulo de Pagos**
- **Trigger**: Pago aprobado → Factura generada
- **Datos**: Monto, cliente, método de pago
- **Estado**: Sincronización automática

##### **Módulo de Reservas**
- **Trigger**: Check-in → Factura generada
- **Datos**: Habitación, fechas, servicios
- **Estado**: Vinculación automática

##### **Módulo de Reembolsos**
- **Trigger**: Reembolso aprobado → Nota de crédito
- **Datos**: Monto, motivo, factura original
- **Estado**: Vinculación automática

#### 📱 **Interfaz de Usuario**

##### **Panel de Facturas**
- **Vista General**: Lista de todas las facturas
- **Filtros**: Por hotel, fecha, tipo, estado
- **Acciones**: Generar, enviar, descargar, cancelar
- **Estados**: Visualización clara del estado de cada factura

##### **Panel de Notas de Crédito**
- **Vista General**: Lista de notas de crédito
- **Vinculación**: Factura original visible
- **Filtros**: Por factura original, fecha, estado
- **Acciones**: Generar, enviar, descargar

##### **Dashboard de AFIP**
- **Estado de Conexión**: Disponibilidad de AFIP
- **Configuración**: Gestión de certificados
- **Estadísticas**: Facturas enviadas, aprobadas, errores
- **Alertas**: CAE próximos a vencer, errores críticos

### Beneficios para el Hotel

#### 🏨 **Cumplimiento Fiscal**
- **Automático**: No hay que recordar generar facturas
- **Completo**: Cumple con todas las normativas AFIP
- **Auditable**: Historial completo de todas las facturas
- **Seguro**: Certificados digitales para máxima seguridad

#### 💰 **Eficiencia Operativa**
- **Tiempo Ahorrado**: No más facturación manual
- **Menos Errores**: Cálculos automáticos precisos
- **Mejor Organización**: Todo centralizado en el sistema
- **Cliente Satisfecho**: Recibe factura inmediatamente

#### 📈 **Control del Negocio**
- **Reportes Detallados**: Ingresos por período, tipo de cliente
- **Análisis de Ventas**: Qué servicios se facturan más
- **Control de Errores**: Facturas que fallaron y por qué
- **Conciliación**: Coincidencia entre pagos y facturas

### Casos de Uso Reales

#### Caso 1: Hotel Boutique (20 habitaciones)
**Problema**: Facturación manual consume mucho tiempo del personal
**Solución**: 
- Configuración AFIP en 30 minutos
- Facturación automática desde el primer día
- Ahorro de 2 horas diarias en facturación
- Clientes reciben factura por email automáticamente

#### Caso 2: Hotel de Negocios (100 habitaciones)
**Problema**: Muchas facturas A para empresas, gestión compleja
**Solución**:
- Detección automática de tipo de cliente
- Generación automática de Factura A o B según corresponda
- Integración con datos de empresas
- Reportes detallados por tipo de cliente

#### Caso 3: Hotel Resort (200 habitaciones)
**Problema**: Servicios adicionales (spa, restaurante) requieren facturación separada
**Solución**:
- Facturación por servicio o consolidada
- Múltiples puntos de venta
- Gestión de exenciones (turismo)
- Reportes por área del hotel

### Servicios AFIP Integrados

#### 🔐 **Autenticación Automática**
El sistema maneja automáticamente la autenticación con AFIP:
- **Certificados Digitales**: Se usan para firmar las solicitudes
- **Tokens de Acceso**: Se generan automáticamente y duran 12 horas
- **Cache Inteligente**: Evita autenticaciones innecesarias
- **Renovación Automática**: Los tokens se renuevan antes de vencer

#### 📤 **Envío de Facturas**
Proceso completamente automatizado:
- **Validación Previa**: Verifica todos los datos antes del envío
- **Construcción XML**: Genera el formato requerido por AFIP
- **Envío Seguro**: Usa HTTPS y certificados digitales
- **Procesamiento de Respuesta**: Extrae CAE y datos de AFIP
- **Actualización Automática**: Guarda los resultados en la base de datos

#### 📄 **Generación de PDFs Fiscales**
El sistema genera PDFs profesionales que cumplen con todas las normativas argentinas:

**Elementos del PDF:**
- **Logo del Hotel**: Imagen corporativa en la parte superior
- **Datos Fiscales Completos**: 
  - Razón social del hotel
  - CUIT y domicilio fiscal
  - Condición ante IVA
  - Punto de venta
- **Datos del Cliente**:
  - Nombre completo o razón social
  - Tipo y número de documento
  - Domicilio completo
- **Información de la Factura**:
  - Número de comprobante (formato: 0001-00001234)
  - Fecha de emisión
  - Tipo de comprobante (A, B, C, E, NC, ND)
  - Moneda y totales
- **Detalle de Servicios**:
  - Tabla profesional con servicios
  - Cantidades y precios unitarios
  - Cálculo de IVA desglosado
  - Totales por línea
- **Autorización AFIP**:
  - CAE (Código de Autorización Electrónica)
  - Fecha de vencimiento del CAE
  - Fecha y hora de autorización
- **Código QR**:
  - Link directo a AFIP para verificación
  - Contiene todos los datos fiscales
  - Escaneable desde cualquier dispositivo
- **Pie de Página**:
  - Información del sistema
  - Fecha de generación del PDF
  - Datos de contacto del hotel

**Características Técnicas:**
- **Formato Profesional**: Diseño limpio y fácil de leer
- **Cumplimiento Normativo**: Sigue todas las reglas de AFIP
- **Alta Calidad**: Generado con ReportLab para máxima calidad
- **Tamaño Optimizado**: PDFs ligeros para envío por email
- **Escalable**: Funciona con cualquier cantidad de items

#### 🧪 **Modo de Pruebas**
Para testing y homologación:
- **Ambiente Separado**: No afecta la producción
- **Datos de Prueba**: Incluye clientes y montos de ejemplo
- **Validación de Configuración**: Verifica que todo esté correcto
- **Parámetros Recomendados**: Sugiere valores para testing

#### Modo Mock de AFIP (Desarrollo)
Este modo permite validar el flujo completo de facturación (CAE simulado, PDF, notificaciones) sin conectarse a AFIP.

- Qué hace: simula WSAA y WSFEv1, devuelve CAE y fecha de vencimiento válidos (CAE de 14 dígitos, `CAEFchVto` en formato `YYYYMMDD`).
- Cuándo usarlo: desarrollo local o cuando homologación de AFIP no publica opcionales requeridos (p.ej., RG 5616) y bloquea pruebas.
- Cómo activarlo:
  1) En `.env` (raíz del proyecto o `backend/.env`, según despliegue):
  ```bash
  AFIP_USE_MOCK=true
  AFIP_TEST_MODE=true
  ```
  2) En la configuración del hotel (`AfipConfig`): `environment = test`.
  3) Reiniciar el backend.
- Señales en logs: “AfipService inicializado … modo test (mock)” y “Enviando factura … a AFIP (mock)”.
- Limitaciones: no valida contra AFIP real; usar homologación/producción para validaciones fiscales definitivas.

#### Diagnóstico RG 5616 – Condición IVA del receptor (Homologación AFIP)
A partir de RG 5616, AFIP exige informar la condición IVA del receptor mediante un opcional específico en WSFEv1.

- Síntoma: Rechazo 10246 “Campo Condición Frente al IVA del receptor es obligatorio…”.
- Causa habitual: en homologación, el CUIT/Punto de Venta no publica todavía el opcional requerido; por eso, aunque el XML incluya `<Opcionales>`, AFIP lo ignora y rechaza.
- Cómo verificar: llamar a `FEParamGetTiposOpcional` y listar Id:Desc habilitados. Si no aparece un Id con descripción alusiva a “Condición IVA del receptor”, no se puede enviar esa data (2101 es FCE CBU, no corresponde).
- Estado del sistema:
  - XML generado en orden WSDL (importes e Iva, luego `Opcionales`).
  - En test real, el sistema busca dinámicamente el Id correcto del opcional por descripción; si no existe, se registra en logs y se omite.
  - En desarrollo, activar “modo mock” para poder completar el flujo sin bloqueo.
- Qué pedir a AFIP: habilitar el opcional de “Condición frente al IVA del receptor” para el CUIT y Punto de Venta de homologación. Adjuntar el log de `FEParamGetTiposOpcional` y el rechazo 10246.

#### Variables de entorno relevantes (AFIP)
- `AFIP_USE_MOCK` (bool): usa servicios mock en modo test (no producción). Default: `false`.
- `AFIP_TEST_MODE` (bool): activa parámetros de test. Default: `true`.
Ubicación: `.env` raíz (si Docker/Compose lo monta) o `backend/.env` (leído por Django `decouple`). Reiniciar el backend tras cambios.

#### Cambios técnicos implementados (para desarrolladores)
- `AfipService`: enruta a `MockAfipAuthService` y `MockAfipInvoiceService` cuando `AFIP_USE_MOCK=true` y `environment!=production`.
- Mock:
  - CAE simulado de 14 dígitos; `CAEFchVto` como string `YYYYMMDD`.
  - Lectura robusta de campos desde `Invoice` con `getattr` y defaults.
- WSFEv1 real:
  - Orden de elementos en `FECAEDetRequest` alineado al WSDL (ImpTotConc → ImpNeto → ImpOpEx → ImpIVA → ImpTrib → ImpTotal, luego Iva/Tributos/Opcionales).
  - `Concepto`=2 por defecto (servicios) y fechas de servicio/pago incluidas.
  - Diagnóstico en logs: parámetros críticos, previews masked del XML y respuesta, lista de `TiposOpcional`.
  - Búsqueda dinámica del Id del opcional de Cond. IVA del receptor; si no está publicado, se loguea y se omite.

---

### Guía Rápida (Cliente) – Probar Facturación con Modo Mock

1) Configurar variables en `.env` y reiniciar:
```bash
AFIP_USE_MOCK=true
AFIP_TEST_MODE=true
```
2) Asegurarse que el hotel tenga `AfipConfig.environment = test`.
3) Generar factura desde una reserva y “Enviar a AFIP”.
4) Verás estado “Aprobada” con CAE simulado y PDF disponible.
5) Para volver a entorno real de homologación/producción: poner `AFIP_USE_MOCK=false` (y `environment=production` cuando corresponda).

Notas:
- El modo mock no contacta AFIP: sirve para validar fin a fin (números, PDF, emails, notificaciones).
- Si homologación rechaza con 10246, es por publicación pendiente del opcional RG 5616 en AFIP; continuar pruebas con mock y tramitar habilitación con AFIP.

### Configuración Paso a Paso

#### 1. **Configuración AFIP**
```
1. Ir a Configuración → Facturación
2. Completar datos del hotel:
   - CUIT del hotel (11 dígitos)
   - Punto de venta (1-9999)
   - Condición de IVA
   - Ambiente (Test o Producción)
3. Subir certificados digitales:
   - Certificado (.crt)
   - Clave privada (.key)
4. Probar conexión con AFIP
5. Verificar que la autenticación funcione
```

#### 2. **Configuración de Facturación**
```
1. Activar facturación automática
2. Configurar tipos de comprobante por defecto:
   - Factura A: Para empresas
   - Factura B: Para consumidores finales
3. Configurar plantillas de email
4. Configurar numeración inicial
5. Establecer reintentos automáticos
```

#### 3. **Primera Factura**
```
1. Procesar un pago de prueba
2. El sistema genera automáticamente la factura
3. Se autentica con AFIP automáticamente
4. Se envía la factura y se obtiene CAE
5. Se genera PDF y se envía por email
6. Verificar que todo funciona correctamente
```

#### 4. **Verificación del Sistema**
```
1. Revisar logs de facturación
2. Verificar que los CAEs se obtengan correctamente
3. Comprobar que los PDFs se generen
4. Confirmar que los emails se envíen
5. Validar la numeración secuencial
```

### Monitoreo y Mantenimiento

#### **Dashboard de Facturación**
- **Facturas del Día**: Cuántas se generaron hoy
- **Estado de AFIP**: Conexión funcionando correctamente
- **Errores Recientes**: Facturas que fallaron y por qué
- **Próximos Vencimientos**: CAEs que vencen pronto

#### **Alertas Automáticas**
- **Conexión AFIP**: Si se pierde la conexión
- **Errores de Facturación**: Si una factura falla
- **Vencimiento de CAE**: Si un CAE está por vencer
- **Certificados**: Si los certificados están por vencer

#### **Reportes Disponibles**
- **Facturas Emitidas**: Por período, tipo, cliente
- **Ingresos Facturados**: Total facturado por mes
- **Errores de Facturación**: Qué falló y cuándo
- **Conciliación**: Coincidencia entre pagos y facturas

### Integración con Otros Módulos

#### **Con Reservas**
- **Datos del Huésped**: Se obtienen automáticamente
- **Servicios Contratados**: Alojamiento, desayuno, spa, etc.
- **Fechas**: Check-in, check-out, noches
- **Habitación**: Tipo, número, tarifa

#### **Con Pagos**
- **Monto Pagado**: Se usa para calcular totales
- **Método de Pago**: Para identificar tipo de cliente
- **Fecha de Pago**: Para fecha de emisión
- **Estado del Pago**: Para validar si facturar

#### **Con Dashboard**
- **Métricas de Facturación**: Ingresos facturados
- **Tendencias**: Facturas por mes, tipo de cliente
- **Alertas**: Errores, vencimientos, conexiones

### Beneficios del Sistema

#### **Para el Hotel**
- ✅ **Cumplimiento Fiscal**: Automático y completo
- ✅ **Ahorro de Tiempo**: No más facturación manual
- ✅ **Menos Errores**: Cálculos automáticos
- ✅ **Mejor Organización**: Todo centralizado
- ✅ **Cliente Satisfecho**: Factura inmediata
- ✅ **Reportes Detallados**: Análisis del negocio

#### **Para el Personal**
- ✅ **Menos Trabajo Manual**: Automatización completa
- ✅ **Menos Errores**: Validaciones automáticas
- ✅ **Mejor Control**: Dashboard y alertas
- ✅ **Más Tiempo**: Para atención al cliente

#### **Para el Cliente**
- ✅ **Factura Inmediata**: Recibe por email automáticamente
- ✅ **Formato Profesional**: PDF con logo del hotel
- ✅ **Datos Correctos**: Información precisa de la reserva
- ✅ **Fácil Acceso**: Historial de facturas en su perfil

### Resolución de Problemas Comunes

#### **Problemas de Conexión AFIP**
- **Error de Autenticación**: Verificar certificados digitales
- **Token Expirado**: El sistema renueva automáticamente
- **Conexión Perdida**: Revisar conectividad a internet
- **Certificados Inválidos**: Verificar fechas de vencimiento

#### **Problemas de Facturación**
- **CAE No Obtenido**: Revisar datos del cliente y montos
- **XML Inválido**: Verificar formato de datos
- **Factura Rechazada**: Comprobar CUIT y punto de venta
- **Error de Numeración**: Verificar secuencia de números

#### **Problemas de PDF**
- **PDF No Generado**: Verificar plantilla y datos
- **Formato Incorrecto**: Revisar configuración de logo
- **Email No Enviado**: Comprobar configuración SMTP
- **Archivo Corrupto**: Regenerar PDF desde la factura

### 🧪 Testing y Homologación

#### **¿Qué es la Homologación?**

La **homologación** es el proceso de validación con AFIP antes de usar el sistema en producción. Es como un "examen" que AFIP hace para asegurarse de que tu sistema funciona correctamente antes de que emitas facturas reales.

#### **¿Por qué es Importante?**

- **Cumplimiento Legal**: AFIP requiere homologación para facturación electrónica
- **Validación Completa**: Asegura que todo funciona correctamente
- **Confianza Total**: Sabes que el sistema está listo para producción
- **Evita Problemas**: Detecta errores antes de que afecten a clientes reales

#### **Proceso de Homologación**

##### **1. Configuración de Pruebas**
```
1. Ir a Configuración → Facturación → Homologación
2. Usar datos de prueba de AFIP:
   - CUIT: 20123456789 (homologación)
   - Punto de Venta: 1
   - Ambiente: Test
3. Cargar certificados de prueba
4. Configurar tipos de factura a probar
```

##### **2. Pruebas Automáticas**
El sistema ejecuta **35+ tests automáticos** que verifican:

- **Conexión con AFIP**: ¿Se puede conectar correctamente?
- **Autenticación**: ¿Se obtienen tokens válidos?
- **Emisión de Facturas**: ¿Se pueden crear facturas A, B, C?
- **Notas de Crédito**: ¿Se pueden generar correctamente?
- **PDFs Fiscales**: ¿Se generan con formato correcto?
- **Validaciones**: ¿Se verifican todos los datos?

##### **3. Tipos de Factura Probados**
- **Factura A**: Para empresas (Responsables Inscriptos)
- **Factura B**: Para consumidores finales
- **Factura C**: Para exentos (turismo internacional)
- **Nota de Crédito**: Para devoluciones
- **Nota de Débito**: Para ajustes

##### **4. Tipos de Cliente Probados**
- **DNI**: Documento Nacional de Identidad
- **CUIT**: Código Único de Identificación Tributaria
- **CUIL**: Código Único de Identificación Laboral
- **Pasaporte**: Para turistas extranjeros

#### **Resultados de las Pruebas**

##### **✅ Pruebas Exitosas**
- **Conexión AFIP**: Funcionando correctamente
- **Autenticación**: Tokens válidos obtenidos
- **Emisión**: Facturas creadas exitosamente
- **PDFs**: Generados con formato fiscal correcto
- **Validaciones**: Todos los datos verificados

##### **❌ Pruebas Fallidas**
- **Conexión AFIP**: Revisar configuración de red
- **Certificados**: Verificar fechas de vencimiento
- **Datos**: Comprobar información del cliente
- **Montos**: Validar cálculos de IVA

#### **Configuración de Ambientes**

##### **Ambiente de Pruebas (Test)**
- **Propósito**: Desarrollo y pruebas locales
- **Datos**: Simulados con mocks
- **AFIP**: No se conecta realmente
- **Uso**: Para desarrolladores y testing

##### **Ambiente de Homologación**
- **Propósito**: Validación con AFIP real
- **Datos**: Datos de prueba oficiales de AFIP
- **AFIP**: Conexión real con servidores de prueba
- **Uso**: Validación antes de producción

##### **Ambiente de Producción**
- **Propósito**: Uso real con clientes
- **Datos**: Datos reales del hotel
- **AFIP**: Conexión real con servidores de producción
- **Uso**: Facturación real de clientes

#### **Monitoreo de Pruebas**

##### **Dashboard de Testing**
- **Estado de Pruebas**: Cuáles pasaron y cuáles fallaron
- **Tiempo de Ejecución**: Qué tan rápido se ejecutan
- **Cobertura**: Qué funcionalidades están probadas
- **Última Ejecución**: Cuándo se probó por última vez

##### **Alertas de Pruebas**
- **Pruebas Fallidas**: Si alguna prueba falla
- **Conexión AFIP**: Si se pierde la conexión
- **Certificados**: Si están por vencer
- **Datos Inválidos**: Si hay información incorrecta

#### **Beneficios del Testing**

##### **Para el Hotel** 🏨
- **Confianza Total**: Sabes que el sistema funciona
- **Cumplimiento Legal**: Cumples con normativas de AFIP
- **Menos Errores**: Problemas detectados antes de producción
- **Mejor Servicio**: Clientes reciben facturas correctas

##### **Para el Personal** 👥
- **Tranquilidad**: No hay sorpresas en producción
- **Eficiencia**: Sistema probado y confiable
- **Soporte**: Problemas resueltos rápidamente
- **Capacitación**: Sabes exactamente cómo funciona

##### **Para los Clientes** 👤
- **Facturas Correctas**: Siempre reciben documentos válidos
- **Sin Retrasos**: Procesamiento automático y rápido
- **Cumplimiento**: Documentos que cumplen con la ley
- **Confianza**: Saben que el hotel es profesional

#### **Comandos de Pruebas**

##### **Ejecutar Todas las Pruebas**
```bash
# Desde el panel de administración
Configuración → Facturación → Ejecutar Pruebas Completas
```

##### **Pruebas Específicas**
```bash
# Solo pruebas de conexión
Configuración → Facturación → Probar Conexión AFIP

# Solo pruebas de facturación
Configuración → Facturación → Probar Emisión de Facturas

# Solo pruebas de PDFs
Configuración → Facturación → Probar Generación de PDFs
```

##### **Ver Resultados**
```bash
# Ver reporte de pruebas
Configuración → Facturación → Ver Reporte de Pruebas
```

---

## 3.14 Facturación Electrónica Argentina

### ¿Qué hace?
Permite emitir facturas electrónicas oficiales de Argentina con integración completa a AFIP, cumpliendo con todas las normativas fiscales del país.

### ¿Cómo funciona?

#### **Configuración Inicial**
1. **Certificado Digital AFIP**: Se obtiene desde WSASS (homologación) o AFIP (producción)
2. **Configuración del Hotel**: CUIT, punto de venta, condición de IVA
3. **Autorización de Servicios**: Se autoriza el servicio `wsfe` (Facturación Electrónica)
4. **Pruebas de Conexión**: Se verifica que todo funcione correctamente

#### **Flujo de Facturación**
```
Reserva → Pago → Generación de Factura → Envío a AFIP → Obtención de CAE → PDF Fiscal
```

#### **Facturación con Señas (Pagos Parciales)**
El sistema soporta dos modos de facturación para manejar señas:

##### **Modo "Solo Recibos"**
```
Seña → Recibo PDF (sin AFIP)
Pago Final → Recibo PDF (sin AFIP)
Factura Final → Factura AFIP con CAE (incluye todos los pagos)
```

##### **Modo "Facturación en Seña"**
```
Seña → Factura AFIP con CAE (monto de la seña)
Pago Final → Recibo PDF (sin AFIP)
Nota de Crédito → Nota de crédito AFIP (ajuste final)
```

#### **Tipos de Comprobantes Soportados**
- **Factura A**: Para Responsables Inscriptos
- **Factura B**: Para Consumidores Finales  
- **Factura C**: Para Exentos
- **Factura E**: Para Exportación
- **Nota de Crédito**: Para devoluciones
- **Nota de Débito**: Para cargos adicionales

### **Configuraciones Requeridas**

#### **1. Certificado Digital AFIP**
- **Homologación**: Obtener desde WSASS (https://wsass-homo.afip.gob.ar)
- **Producción**: Obtener desde AFIP oficial
- **Formato**: Certificado .crt y clave privada .key
- **Autorización**: Debe estar autorizado para el servicio `wsfe`

#### **2. Datos del Hotel**
- **CUIT**: 11 dígitos del hotel
- **Punto de Venta**: Número asignado por AFIP (1-9999)
- **Condición de IVA**: Responsable Inscripto, Consumidor Final, etc.
- **Razón Social**: Nombre oficial del hotel
- **Domicilio**: Dirección fiscal completa

#### **3. Configuración Técnica**
- **Ambiente**: Testing (homologación) o Producción
- **Certificados**: Rutas a los archivos .crt y .key
- **Numeración**: Control automático de números de factura
- **Reintentos**: Configuración de reintentos en caso de error

### **Características Principales**

#### **Integración AFIP Completa**
- ✅ **Autenticación WSAA**: Token de acceso automático
- ✅ **Emisión WSFEv1**: Envío de facturas a AFIP
- ✅ **Obtención de CAE**: Código de Autorización Electrónica
- ✅ **Validaciones**: Cumplimiento de normativas argentinas
- ✅ **Reintentos**: Manejo automático de errores temporales

#### **Generación de PDFs Fiscales**
- ✅ **Diseño Oficial**: Formato según normativas AFIP
- ✅ **Datos Completos**: Emisor, comprador, items, totales
- ✅ **CAE Incluido**: Código de autorización visible
- ✅ **Código QR**: Para verificación en AFIP
- ✅ **Logo del Hotel**: Personalización profesional

#### **Gestión de Estados**
- ✅ **Borrador**: Factura creada, no enviada
- ✅ **Enviada**: Enviada a AFIP, esperando respuesta
- ✅ **Aprobada**: CAE obtenido, factura válida
- ✅ **Error**: Problema en el envío, requiere revisión

#### **Automatización**
- ✅ **Generación Automática**: Al procesar pagos
- ✅ **Reintentos Inteligentes**: En caso de errores temporales
- ✅ **Cache de Tokens**: Reutilización de tokens AFIP
- ✅ **Validaciones**: Antes de enviar a AFIP

### **Configuración Paso a Paso**

#### **Paso 1: Obtener Certificado Digital**
1. Ir a WSASS (https://wsass-homo.afip.gob.ar)
2. Crear nuevo certificado con CSR generado por el sistema
3. Descargar certificado .crt
4. Autorizar servicio `wsfe` (Facturación Electrónica)

#### **Paso 2: Configurar en AlojaSys**
1. Ir a **Configuración → Facturación AFIP**
2. Completar datos del hotel:
   - CUIT del hotel
   - Punto de venta AFIP
   - Condición de IVA
3. Subir certificados:
   - Archivo .crt (certificado)
   - Archivo .key (clave privada)
4. Seleccionar ambiente (Testing/Producción)

#### **Paso 3: Probar Conexión**
1. Hacer clic en **"Probar Conexión"**
2. Verificar que se obtenga token AFIP válido
3. Probar emisión de factura de prueba
4. Verificar que se genere PDF correctamente

### **Funcionalidades Implementadas**

#### **Gestión de Facturas**
- ✅ **Creación desde Reservas**: Generar factura directamente desde una reserva
- ✅ **Validación de Datos**: Verificación automática de datos del cliente
- ✅ **Numeración Automática**: Control secuencial de números de factura
- ✅ **Estados de Factura**: Borrador, Enviada, Aprobada, Rechazada, Cancelada
- ✅ **Historial Completo**: Seguimiento de todos los cambios de estado

#### **Integración con AFIP**
- ✅ **Autenticación Automática**: Token AFIP con cache inteligente
- ✅ **Manejo de Errores**: Gestión de errores "TA ya válido" de AFIP
- ✅ **Reintentos Automáticos**: En caso de errores temporales
- ✅ **Validaciones Pre-AFIP**: Verificación antes del envío
- ✅ **Obtención de CAE**: Código de Autorización Electrónica automático

#### **Generación de PDFs**
- ✅ **Template Oficial**: Diseño según normativas AFIP
- ✅ **Conversión HTML→PDF**: Usando WeasyPrint con fallback a ReportLab
- ✅ **Datos Dinámicos**: Información del hotel, cliente e items
- ✅ **Estilos Oficiales**: CSS compatible con normativas AFIP
- ✅ **Regeneración**: Forzar regeneración de PDFs actualizados

#### **Interfaz de Usuario**
- ✅ **Lista de Facturas**: Vista completa con filtros y búsqueda
- ✅ **Estado de Facturación**: Badge visual en reservas
- ✅ **Botón de Facturación**: En gestión de reservas
- ✅ **Visualización de PDF**: Modal con visor integrado
- ✅ **Acciones por Estado**: Enviar, Re-enviar, Cancelar según estado

#### **Automatización**
- ✅ **Generación Automática**: Al aprobar pagos completos
- ✅ **Envío a AFIP**: Proceso automático con manejo de errores
- ✅ **Notificaciones**: Alertas de estado de facturas
- ✅ **Cache de Tokens**: Reutilización eficiente de tokens AFIP

### **Flujos de Trabajo**

#### **Flujo Normal de Facturación**
1. **Reserva con Pago Completo** → Sistema detecta pago aprobado
2. **Generación Automática** → Se crea factura en estado "Borrador"
3. **Envío a AFIP** → Se envía automáticamente a AFIP
4. **Obtención de CAE** → AFIP devuelve código de autorización
5. **Generación de PDF** → Se crea PDF fiscal con CAE
6. **Notificación** → Se notifica al usuario del éxito

#### **Flujo Manual de Facturación**
1. **Seleccionar Reserva** → En gestión de reservas
2. **Hacer Clic en "Factura"** → Botón de facturación
3. **Completar Datos** → Información del cliente
4. **Generar Factura** → Se crea en estado "Borrador"
5. **Enviar a AFIP** → Proceso manual desde lista de facturas
6. **Verificar Estado** → Confirmar aprobación por AFIP

#### **Gestión de Errores**
1. **Error de Conexión** → Reintento automático
2. **Error de AFIP** → Manejo específico por tipo de error
3. **Token Expirado** → Renovación automática
4. **Factura Rechazada** → Notificación y opción de corrección

### **Estados de Factura**

#### **Draft (Borrador)**
- **Descripción**: Factura creada, no enviada a AFIP
- **Acciones**: Enviar a AFIP, Cancelar, Editar
- **Color**: Gris

#### **Sent (Enviada)**
- **Descripción**: Enviada a AFIP, esperando respuesta
- **Acciones**: Re-enviar si hay error
- **Color**: Azul

#### **Approved (Aprobada)**
- **Descripción**: CAE obtenido, factura válida
- **Acciones**: Ver PDF, Crear Nota de Crédito
- **Color**: Verde

#### **Rejected (Rechazada)**
- **Descripción**: Rechazada por AFIP
- **Acciones**: Revisar y corregir, Re-enviar
- **Color**: Rojo

#### **Cancelled (Cancelada)**
- **Descripción**: Cancelada manualmente
- **Acciones**: Ninguna
- **Color**: Gris

### **Configuraciones Avanzadas**

#### **Certificados AFIP**
- **Desarrollo**: Certificados de prueba desde WSASS
- **Producción**: Certificados reales desde AFIP
- **Renovación**: Proceso automático de renovación
- **Seguridad**: Almacenamiento seguro de claves privadas

#### **Templates PDF**
- **HTML Base**: Template oficial AFIP SDK
- **Personalización**: Logo y datos del hotel
- **Responsive**: Optimizado para impresión A4
- **Fallback**: ReportLab si WeasyPrint falla

#### **Manejo de Errores**
- **"TA ya válido"**: Reutilización de token existente
- **Timeout**: Reintentos automáticos
- **XML malformado**: Limpieza y reparación
- **Certificado expirado**: Renovación automática

### **Beneficios para el Hotel**

#### **Cumplimiento Fiscal**
- ✅ **Normativas Argentinas**: Cumplimiento total con AFIP
- ✅ **Auditoría**: Trazabilidad completa de facturas
- ✅ **Validación**: Verificación automática de datos
- ✅ **Backup**: Respaldo automático de todas las facturas

#### **Automatización**
- ✅ **Menos Errores**: Validaciones automáticas
- ✅ **Ahorro de Tiempo**: Proceso automático
- ✅ **Disponibilidad 24/7**: Funciona en cualquier momento
- ✅ **Escalabilidad**: Maneja cualquier volumen de facturas

#### **Experiencia del Usuario**
- ✅ **Interfaz Intuitiva**: Fácil de usar
- ✅ **Estados Claros**: Visualización del progreso
- ✅ **Notificaciones**: Alertas en tiempo real
- ✅ **PDFs Profesionales**: Documentos de calidad

### **Casos de Uso Reales**

#### **Hotel con 50 Habitaciones**
- **Volumen**: ~100 facturas/mes
- **Automatización**: 95% automático
- **Tiempo Ahorrado**: 8 horas/mes
- **Errores Reducidos**: 90% menos errores manuales

#### **Hotel con 200 Habitaciones**
- **Volumen**: ~500 facturas/mes
- **Automatización**: 98% automático
- **Tiempo Ahorrado**: 40 horas/mes
- **Cumplimiento**: 100% normativas AFIP

### **Próximas Funcionalidades**

#### **En Desarrollo**
- 🔄 **Notas de Crédito**: Para devoluciones
- 🔄 **Notas de Débito**: Para cargos adicionales
- 🔄 **Facturas por Lotes**: Procesamiento masivo
- 🔄 **Reportes Fiscales**: Libro IVA y otros

#### **Planificadas**
- 📋 **Integración Contable**: Con sistemas contables
- 📋 **Backup Automático**: Respaldo en la nube
- 📋 **Múltiples Puntos de Venta**: Para hoteles grandes
- 📋 **Facturas Internacionales**: Para turismo extranjero
2. Verificar que aparezca "Conexión exitosa"
3. Si hay errores, revisar certificados y configuración

#### **Paso 4: Configurar Facturación Automática**
1. Activar **"Generación automática de facturas"**
2. Seleccionar tipos de comprobante por defecto
3. Configurar datos del cliente por defecto

### **Tipos de Cliente Soportados**

#### **Responsable Inscripto**
- **Documento**: CUIT
- **Factura**: Tipo A
- **IVA**: Desglosado

#### **Consumidor Final**
- **Documento**: DNI, CUIL, etc.
- **Factura**: Tipo B
- **IVA**: Incluido

#### **Exento**
- **Documento**: Cualquier tipo
- **Factura**: Tipo C
- **IVA**: No aplica

### **Flujos de Trabajo**

#### **Facturación Automática**
1. **Cliente hace reserva** y paga
2. **Sistema detecta pago** procesado
3. **Genera factura automáticamente** con datos del cliente
4. **Envía a AFIP** y obtiene CAE
5. **Genera PDF fiscal** con CAE y QR
6. **Envía por email** al cliente

#### **Facturación Manual**
1. **Usuario selecciona reserva** para facturar
2. **Completa datos del cliente** si es necesario
3. **Selecciona tipo de comprobante**
4. **Confirma generación** de factura
5. **Sistema procesa** igual que automático

#### **Notas de Crédito**
1. **Seleccionar factura original** a anular
2. **Especificar motivo** de la anulación
3. **Generar nota de crédito** automáticamente
4. **Enviar a AFIP** para autorización

### **Monitoreo y Alertas**

#### **Estados de Facturas**
- **Dashboard**: Vista general de facturas por estado
- **Filtros**: Por fecha, tipo, estado, cliente
- **Búsqueda**: Por número, CAE, cliente

#### **Alertas Automáticas**
- **Facturas con error**: Requieren revisión
- **Certificados por vencer**: Renovar a tiempo
- **Conexión AFIP**: Problemas de conectividad
- **Límites de numeración**: Próximo a agotar

#### **Reportes**
- **Facturas emitidas**: Por período
- **Montos facturados**: Totales por tipo
- **Errores**: Análisis de problemas
- **Cumplimiento**: Estadísticas de AFIP

### **Beneficios para el Hotel**

#### **Cumplimiento Legal** ⚖️
- ✅ **Normativas AFIP**: Cumplimiento total
- ✅ **Auditorías**: Documentación completa
- ✅ **Inspecciones**: Sin problemas fiscales
- ✅ **Multas**: Evita sanciones por incumplimiento

#### **Eficiencia Operativa** ⚡
- ✅ **Automatización**: Sin intervención manual
- ✅ **Velocidad**: Facturas en segundos
- ✅ **Precisión**: Sin errores humanos
- ✅ **Trazabilidad**: Historial completo

#### **Experiencia del Cliente** 👤
- ✅ **Facturas Inmediatas**: Al momento del pago
- ✅ **Formato Profesional**: PDFs con logo del hotel
- ✅ **Verificación Fácil**: Código QR para validar
- ✅ **Email Automático**: Recibe factura por correo

#### **Gestión Financiera** 💰
- ✅ **Control Total**: Todas las facturas en un lugar
- ✅ **Reportes Detallados**: Análisis de ventas
- ✅ **Conciliación**: Fácil con contabilidad
- ✅ **Backup**: Respaldo automático de documentos

### **Requisitos Técnicos**

#### **Certificados Digitales**
- **Formato**: PEM (.crt y .key)
- **Algoritmo**: RSA 2048 bits mínimo
- **Firma**: SHA256
- **Vigencia**: Renovar antes del vencimiento

#### **Conectividad**
- **Internet**: Conexión estable requerida
- **Puertos**: 443 (HTTPS) abierto
- **DNS**: Resolución de dominios AFIP
- **Firewall**: Permitir tráfico a AFIP

#### **Datos Requeridos**
- **Hotel**: CUIT, razón social, domicilio
- **Cliente**: Nombre, documento, domicilio
- **Servicios**: Descripción, precios, IVA
- **Numeración**: Secuencial por punto de venta

### **Solución de Problemas**

#### **Errores Comunes**
- **"Certificado no encontrado"**: Verificar rutas de archivos
- **"Conexión fallida"**: Revisar conectividad a AFIP
- **"TA válido existente"**: Esperar vencimiento del token
- **"Datos inválidos"**: Verificar información del cliente

#### **Soporte Técnico**
- **Logs del sistema**: Para diagnóstico detallado
- **Pruebas de conexión**: Verificar configuración
- **Documentación AFIP**: Consultar manuales oficiales
- **Contacto AFIP**: soporte-ws-testing@arca.gob.ar

### **Costos y Consideraciones**

#### **Costos AFIP**
- **Homologación**: Gratuito para testing
- **Producción**: Según tarifas AFIP vigentes
- **Certificados**: Renovación anual
- **Servicios**: Sin costo adicional por factura

#### **Consideraciones de Seguridad**
- **Certificados**: Almacenamiento seguro
- **Claves**: No compartir con terceros
- **Accesos**: Solo personal autorizado
- **Backup**: Respaldo de configuraciones

### **Beneficios de las Señas para el Negocio**

#### **Para el Hotel**
- **💰 Mejor Flujo de Caja**: Ingresos anticipados antes del check-in
- **🔒 Reservas Aseguradas**: Menos cancelaciones de último momento
- **📊 Menos No-Shows**: Clientes comprometidos con el pago
- **⚡ Automatización**: Menos trabajo manual en facturación
- **📋 Flexibilidad Contable**: Adaptable a necesidades fiscales
- **🎯 Mayor Ocupación**: Reservas más estables y confiables

#### **Para el Huésped**
- **🏨 Reserva Garantizada**: Su lugar está asegurado
- **💳 Pago Flexible**: Puede pagar en cuotas cómodas
- **📄 Comprobantes Claros**: Recibe todos los documentos
- **🔍 Transparencia Total**: Ve exactamente qué está pagando
- **📧 Notificaciones**: Recibe emails con todos los comprobantes
- **💾 Historial Completo**: Acceso a todos sus pagos

#### **Para la Contabilidad**
- **📊 Trazabilidad Completa**: Seguimiento de todos los pagos
- **🏛️ Cumplimiento Fiscal**: Facturación según normativas argentinas
- **📈 Reportes Detallados**: Análisis de ingresos por señas
- **🔄 Conciliación Fácil**: Vinculación automática de pagos
- **📋 Auditoría**: Registro completo de todas las operaciones

---

## Flujos de Trabajo del Día a Día

# Ver logs detallados
Configuración → Facturación → Ver Logs de Pruebas
```

#### **Resolución de Problemas en Pruebas**

##### **Problemas de Conexión**
- **Verificar Internet**: Conexión estable
- **Revisar Firewall**: Puertos de AFIP abiertos
- **Comprobar DNS**: Resolución de nombres correcta
- **Contactar Soporte**: Si persiste el problema

##### **Problemas de Certificados**
- **Verificar Fechas**: No estén vencidos
- **Comprobar Formato**: Archivos válidos
- **Revisar Permisos**: Acceso a archivos
- **Regenerar**: Si es necesario

##### **Problemas de Datos**
- **Validar CUIT**: Formato correcto
- **Revisar Montos**: Cálculos de IVA
- **Comprobar Cliente**: Datos completos
- **Verificar Configuración**: Parámetros correctos

### Soporte Técnico

#### **Logs del Sistema**
- **Logs de AFIP**: Registro de todas las operaciones
- **Logs de Facturación**: Detalles de cada factura procesada
- **Logs de Errores**: Información para resolución de problemas
- **Logs de Autenticación**: Estado de conexión con AFIP

#### **Monitoreo en Tiempo Real**
- **Estado de AFIP**: Conexión activa o inactiva
- **Facturas Pendientes**: Cuántas están en proceso
- **Errores Recientes**: Últimos problemas detectados
- **Rendimiento**: Tiempo de procesamiento promedio

---

## Beneficios del Sistema

## Conclusión

**AlojaSys** es más que un sistema de gestión hotelera; es una solución integral que transforma la manera de operar un hotel. Desde la gestión básica de habitaciones hasta el análisis avanzado del negocio, el sistema proporciona todas las herramientas necesarias para:

- **Automatizar** procesos manuales
- **Optimizar** la ocupación y precios
- **Mejorar** la experiencia del huésped
- **Aumentar** la eficiencia del personal
- **Maximizar** los ingresos del hotel

Con su arquitectura modular y flexible, AlojaSys se adapta a cualquier tipo de hotel, desde pequeños establecimientos boutique hasta grandes cadenas hoteleras, proporcionando una base sólida para el crecimiento y la innovación en el sector hotelero.

---

## 3.15 Comprobantes de Señas y Devoluciones

### ¿Qué hace?

El módulo de **Comprobantes de Señas y Devoluciones** permite generar, gestionar y almacenar comprobantes de pago para señas, pagos parciales y devoluciones. Es como tener un sistema de recibos digitales que se integra perfectamente con el flujo de reservas y facturación.

### ¿Cómo funciona?

#### Generación Automática de Comprobantes
1. **Detección Inteligente**: El sistema identifica automáticamente cuando un pago es una seña (pago parcial)
2. **Identificadores Únicos**: Cada comprobante tiene un número formateado único (ej: S-0001-000012 para señas, D-0001-000004 para devoluciones)
3. **Generación Automática**: El PDF se genera automáticamente cuando:
   - Se crea una seña (seña = pago parcial)
   - Se confirma un reembolso (reembolso completado)
4. **Notificaciones**: Sistema de notificaciones integrado avisa cuando se genera un comprobante
5. **Almacenamiento Seguro**: El comprobante se guarda con una URL permanente
6. **Acceso Inmediato**: Se puede ver y descargar el comprobante desde cualquier lugar

#### Gestión de Señas
- **Identificación Automática**: Detecta señas incluso en pagos históricos
- **Políticas Configurables**: Se integra con las políticas de pago del hotel
- **Validaciones Inteligentes**: Verifica montos y tipos de pago automáticamente
- **Historial Completo**: Mantiene registro de todas las señas realizadas

#### Gestión de Devoluciones
- **Comprobantes de Reembolso**: Genera automáticamente PDFs para devoluciones
- **Estados de Seguimiento**: Pendiente, procesando, completado, fallido, cancelado
- **Métodos de Devolución**: Efectivo, transferencia, tarjeta, voucher, método original
- **Integración Completa**: Se conecta con el sistema de reembolsos existente

### Características Principales

#### 🧾 **Generación de Comprobantes**
- **PDFs Profesionales**: Diseño consistente con el branding del hotel
- **Datos Completos**: Información del pago, reserva y huésped
- **URLs Persistentes**: Acceso permanente a los comprobantes
- **Generación Rápida**: Proceso asíncrono que no bloquea la interfaz

#### 💳 **Gestión de Señas**
- **Detección Automática**: Identifica pagos parciales vs. pagos completos
- **Heurística Inteligente**: Detecta señas incluso sin configuración explícita
- **Integración con Políticas**: Se adapta a las reglas de pago del hotel
- **Validaciones Automáticas**: Verifica montos y tipos de pago

#### 📋 **Interfaz de Usuario**
- **Badges Visuales**: Indicadores claros del estado de pago en las reservas
- **Tooltips Informativos**: Detalles completos al pasar el mouse
- **Tabs Organizados**: Factura Electrónica, Comprobantes de Señas, Comprobantes de Devoluciones
- **Gestión Centralizada**: Todos los comprobantes en una sola interfaz
- **Búsqueda y Filtros**: Encuentra comprobantes por huésped, hotel, fecha, etc.

### Flujos de Trabajo

#### 1. **Flujo de Pago de Seña**
1. **Usuario crea reserva** → Sistema detecta política de seña
2. **Modal de pago** → Opciones: "Seña" o "Pagar Total"
3. **Selecciona "Seña"** → Monto calculado según política
4. **Procesa pago** → Se marca como pago parcial
5. **Genera automáticamente número de comprobante** → Formato S-0001-000012
6. **Genera PDF automáticamente** → Sin intervención del usuario
7. **Crea notificación** → Avisa al usuario que el comprobante está disponible
8. **Reserva confirmada** → Estado cambia a "confirmed"
9. **Botón "Comprobante"** → Abre directamente el PDF generado automáticamente

#### 2. **Flujo de Confirmación de Reembolso y Generación de Comprobante**
1. **Usuario gestiona reembolso** → Accede a "Gestión de Reembolsos"
2. **Marca reembolso como completado** → Cambia estado a "completed"
3. **Genera automáticamente número de comprobante** → Formato D-0001-000004
4. **Genera PDF automáticamente** → Sin intervención del usuario
5. **Crea notificación** → Avisa al usuario que el comprobante de devolución está disponible
6. **Actualiza URL** → Guarda enlace permanente en base de datos
7. **Botón "Generar Comprobante" desaparece** → Se convierte automáticamente en íconos de vista/descarga
8. **Lista actualizada** → Aparece en "Comprobantes de Devoluciones"

#### 3. **Flujo de Gestión de Comprobantes**
1. **Acceso a "Facturación"** → "Comprobantes" (con tabs)
2. **Tab "Comprobantes de Señas"**:
   - Filtrado automático → Solo pagos de señas
   - Lista de comprobantes → Con datos de reserva y huésped
   - Acciones disponibles → Ver y descargar PDFs
   - Búsqueda y filtros → Por huésped, hotel, método, fecha
3. **Tab "Comprobantes de Devoluciones"**:
   - Filtrado automático → Solo reembolsos con comprobantes generados
   - Lista de comprobantes → Con datos de reserva, monto y método de devolución
   - Acciones disponibles → Generar, ver y descargar PDFs
   - Búsqueda y filtros → Por reserva, hotel, método, estado, fecha

### Ejemplos Prácticos

#### **Ejemplo 1: Reserva con Seña**
**Escenario**: Un huésped reserva una habitación por 3 noches ($300) y paga una seña de $100.

1. **Reserva Creada**: Sistema detecta política de seña (30% del total)
2. **Modal de Pago**: Usuario selecciona "Pagar Seña" ($100)
3. **Pago Procesado**: Se marca como `is_deposit: true`
4. **Número de Comprobante Generado**: S-0001-000012 (automático)
5. **PDF Generado Automáticamente**: Sin intervención del usuario
6. **Notificación Creada**: Avisa que el comprobante está disponible
7. **Reserva Confirmada**: Estado cambia a "confirmed"
8. **Badge "Con Seña"**: Aparece en la lista de reservas
9. **Botón "Comprobante"**: Abre directamente el PDF generado (S-0001-000012)
10. **Lista Actualizada**: Aparece en "Comprobantes de Señas"

#### **Ejemplo 2: Gestión de Comprobantes**
**Escenario**: El personal del hotel necesita revisar todos los comprobantes de señas del mes.

1. **Acceso a Facturación**: Ir a "Facturación" → "Comprobantes de Señas"
2. **Lista Filtrada**: Solo comprobantes de señas (pagos parciales)
3. **Información Completa**: Huésped, hotel, monto, fecha, método
4. **Acciones Disponibles**: Ver PDF, descargar, buscar
5. **Filtros Avanzados**: Por fecha, huésped, hotel, método de pago
6. **Búsqueda Rápida**: Encuentra comprobantes específicos

### Beneficios para el Hotel

#### **Para el Personal**
- ✅ **Gestión Centralizada**: Todos los comprobantes en un solo lugar
- ✅ **Acceso Rápido**: Encuentra comprobantes en segundos
- ✅ **Automatización Completa**: Generación automática sin trabajo manual para señas y reembolsos
- ✅ **Identificadores Claros**: Números de comprobante formateados (S-, P-, D-) para fácil identificación
- ✅ **Notificaciones Inteligentes**: El sistema avisa cuando se generan comprobantes automáticamente
- ✅ **Organización**: Filtros y búsqueda para mantener orden

#### **Para la Contabilidad**
- ✅ **Documentación Completa**: Comprobantes profesionales y legales
- ✅ **Trazabilidad**: Historial completo de todas las señas
- ✅ **Integración**: Se conecta con el sistema de facturación
- ✅ **Cumplimiento**: Documentación adecuada para auditorías

#### **Para los Huéspedes**
- ✅ **Comprobantes Claros**: Recibos profesionales y legibles
- ✅ **Acceso Inmediato**: Pueden ver sus comprobantes al instante
- ✅ **Historial**: Mantienen registro de sus pagos
- ✅ **Confianza**: Documentación oficial de sus transacciones

### Casos de Uso Reales

#### **Caso 1: Hotel Boutique**
**Problema**: El hotel necesita generar comprobantes para señas de $50-200
**Solución**: Sistema genera automáticamente comprobantes profesionales
**Resultado**: Ahorro de 30 minutos diarios en gestión manual

#### **Caso 2: Hotel de Lujo**
**Problema**: Huéspedes requieren comprobantes para reembolsos corporativos
**Solución**: Comprobantes profesionales con todos los datos necesarios
**Resultado**: 100% de satisfacción en documentación de pagos

#### **Caso 3: Cadena Hotelera**
**Problema**: Necesidad de centralizar comprobantes de múltiples hoteles
**Solución**: Sistema unificado con filtros por hotel
**Resultado**: Gestión eficiente de 500+ comprobantes mensuales

### Configuración y Uso

#### **Configuración Automática**
- **Sin configuración adicional**: El sistema funciona automáticamente
- **Detección inteligente**: Identifica señas sin configuración explícita
- **Integración nativa**: Se conecta con políticas de pago existentes

#### **Uso Diario**
1. **Generar Comprobante**: Clic en "Comprobante" en gestión de reservas
2. **Ver Comprobantes**: Ir a "Facturación" → "Comprobantes de Señas"
3. **Buscar Comprobante**: Usar filtros por huésped, fecha, hotel
4. **Descargar PDF**: Clic en "Ver" para abrir o descargar

### Integración con Otros Módulos

#### **Sistema de Pagos**
- **Detección automática**: Identifica pagos parciales
- **Marcado inteligente**: Marca señas con `is_deposit: true`
- **Heurística de fallback**: Detecta señas en pagos históricos

#### **Sistema de Facturación**
- **Comprobantes vs. Facturas**: Diferencia entre recibos y facturas
- **Integración AFIP**: Se conecta con facturación electrónica
- **Flujo unificado**: Comprobantes para señas, facturas para pagos completos

#### **Sistema de Reservas**
- **Estados visuales**: Badges "Con Seña" en listas de reservas
- **Tooltips informativos**: Detalles de pagos al pasar el mouse
- **Acciones contextuales**: Botón "Comprobante" disponible cuando corresponde

### Métricas y Reportes

#### **Métricas Clave**
- **Comprobantes generados**: Cantidad por día/semana/mes
- **Tiempo de generación**: Velocidad promedio de creación
- **Uso de almacenamiento**: Espacio ocupado por PDFs
- **Errores de generación**: Fallos en la creación de comprobantes

#### **Reportes Disponibles**
- **Comprobantes por período**: Lista filtrada por fechas
- **Comprobantes por hotel**: Distribución por establecimiento
- **Comprobantes por método**: Análisis por tipo de pago
- **Comprobantes por huésped**: Historial individual

### Resolución de Problemas

#### **Problemas Comunes**

**Problema**: "No aparece el botón Comprobante"
- **Causa**: No hay pagos de seña en la reserva
- **Solución**: Verificar que el pago sea parcial (seña)

**Problema**: "Comprobante no se genera"
- **Causa**: Error en el proceso de generación
- **Solución**: Reintentar o contactar soporte técnico

**Problema**: "No aparece en la lista de comprobantes"
- **Causa**: El pago no está marcado como seña
- **Solución**: El sistema detectará automáticamente en la próxima actualización

#### **Soporte Técnico**
- **Logs detallados**: Registro de todas las operaciones
- **Monitoreo automático**: Detección de errores en tiempo real
- **Recuperación automática**: Reintentos automáticos en caso de fallos

### Ventajas Competitivas

#### **Automatización Completa**
- **Sin trabajo manual**: Generación automática de comprobantes
- **Detección inteligente**: Identifica señas sin configuración
- **Integración nativa**: Se conecta con todos los módulos

#### **Experiencia de Usuario**
- **Interfaz intuitiva**: Fácil de usar para todo el personal
- **Acceso rápido**: Encuentra comprobantes en segundos
- **Información completa**: Todos los datos necesarios en un lugar

#### **Escalabilidad**
- **Múltiples hoteles**: Funciona con cualquier cantidad de establecimientos
- **Alto volumen**: Maneja miles de comprobantes sin problemas
- **Performance optimizada**: Respuesta rápida incluso con grandes volúmenes

## 3.16 Integraciones con OTAs (Channel Manager)

### ¿Qué hace?
### Nueva vista: Canales de Reservas

Dispones de una pantalla específica para gestionar las conexiones con OTAs (se accede desde el menú como "Canales de Reservas").

- Qué permite:
  - Ver todos los canales configurados por hotel y proveedor (Booking.com, Airbnb, iCal, etc.).
  - Filtrar por hotel, proveedor y estado (activo/inactivo).
  - Editar una conexión (incluye URL iCal, modo sandbox/producción y credenciales cuando aplique).
  - Copiar la URL iCal del hotel con un clic.
  - Ver el estado de verificación de la URL del proveedor ("Verificado").
  - Ejecutar "Sincronizar ahora" y ver en tiempo real el resultado del último proceso (éxito/falla/en ejecución).

Seguridad de datos visibles:
- Los tokens iCal y secretos se muestran enmascarados (solo los primeros 4 caracteres).
- Nunca se exponen claves completas; solo se pueden actualizar.


**AlojaSys** se conecta automáticamente con plataformas de reservas online (Booking.com, Airbnb, etc.) para sincronizar disponibilidad, tarifas y reservas en ambos sentidos. Es como tener un "asistente digital" que mantiene tu hotel sincronizado con todos los canales de venta.

### ¿Cómo funciona?

El sistema trabaja en **dos direcciones automáticamente**:

#### 📤 Desde AlojaSys hacia las OTAs

1. **Cuando creas o modificas una reserva** en AlojaSys, el sistema automáticamente:
   - Actualiza la disponibilidad en Booking.com, Airbnb, etc.
   - Sincroniza los precios si cambiaron
   - Bloquea las fechas ocupadas para que no aparezcan disponibles

2. **Sincronización continua**: El sistema también hace una sincronización completa todas las noches para asegurar que todo esté actualizado.

#### 📥 Desde las OTAs hacia AlojaSys

1. **Reservas automáticas**: Cuando alguien reserva en Booking.com o Airbnb:
   - El sistema consulta cada 1-2 minutos si hay reservas nuevas (respaldo)
   - Las reservas aparecen automáticamente en AlojaSys
   - No necesitas hacer nada manual

2. **Importación de calendarios**: También puedes configurar que AlojaSys lea los calendarios de las OTAs para bloquear fechas ocupadas.

### Configuración Inicial

#### Paso 1: Configurar el Proveedor OTA

1. Ve a **Configuración → OTAs**
2. Clic en **"Crear OTAs"**
3. Selecciona:
   - **Hotel**: El hotel que quieres conectar
   - **Proveedor**: Booking.com, Airbnb, iCal, etc.
   - **Etiqueta**: Un nombre para identificarlo (ej: "Booking Principal")

**Para Booking.com o Airbnb** (cuando tengas credenciales):
- **Hotel ID**: El ID de tu propiedad en la plataforma
- **Client ID** y **Client Secret**: Credenciales que te entrega la OTA
- **Base URL**: URL del entorno (sandbox para pruebas, producción para uso real)
- **Modo**: Test (pruebas) o Producción

**Para iCal** (sin credenciales):
- Solo necesitas el **Token iCal** (el sistema puede generarlo automáticamente)

#### Paso 2: Mapear Tipos de Habitación

Las OTAs usan códigos diferentes para los tipos de habitación. Necesitas "mapear" (relacionar) tus tipos internos con los códigos de la OTA:

1. En la pestaña **"Tipos de Habitación (Mapeos)"**
2. Clic en **"Nuevo Mapeo Tipo"**
3. Completa:
   - **Hotel**: Tu hotel
   - **Proveedor**: Booking/Airbnb
   - **Código Tipo (PMS)**: Tu código interno (ej: "DOUBLE")
   - **Código OTA**: El código que usa la OTA (ej: "STD_DBL")
   - **Nombre**: Opcional, para referencia

**Ejemplo**: 
- En AlojaSys tienes una habitación tipo "DOBLE"
- En Booking.com el mismo tipo se llama "STD_DBL"
- El mapeo conecta ambos: "DOBLE" = "STD_DBL"

#### Paso 3: Mapear Planes de Tarifa

Similar a los tipos, necesitas mapear tus planes de tarifa:

1. En la pestaña **"Planes de Tarifa (Mapeos)"**
2. Clic en **"Nuevo Mapeo Plan"**
3. Completa:
   - **Hotel**: Tu hotel
   - **Proveedor**: Booking/Airbnb
   - **Código Plan (PMS)**: Tu plan interno (ej: "STANDARD")
   - **Código OTA**: El ID que usa la OTA (ej: "STD_REFUND")
   - **Moneda**: ARS, USD, etc.

**Ejemplo**:
- En AlojaSys tienes el plan "Estándar"
- En Booking.com el mismo plan tiene ID "STD_REFUND"
- El mapeo conecta ambos: "Estándar" = "STD_REFUND"

#### Paso 4: (Opcional) Mapeos por Habitación Individual

Si usas iCal (calendarios compartidos), puedes mapear habitación por habitación:

1. En la pestaña **"Mapeos por Habitación"**
2. Clic en **"Nuevo Mapeo"**
3. Selecciona:
   - **Habitación**: La habitación específica
   - **Proveedor**: iCal
   - **URL iCal de entrada**: La URL que te da la OTA para leer su calendario
   - **Dirección de sincronización**: 
     - **Ambos**: Importa y exporta (recomendado)
     - **Solo Importar**: Solo lee el calendario de la OTA
     - **Solo Exportar**: Solo comparte tu calendario con la OTA

**Nota**: Para Booking/Airbnb con API real, no necesitas esto; el sistema usa los mapeos de tipos y planes.

**¿Cuándo usar cada opción de sincronización?**
- **Ambos**: Cuando quieres sincronización completa bidireccional (la mayoría de casos)
- **Solo Importar**: Cuando la OTA solo te permite leer su calendario, pero no quieres compartir el tuyo
- **Solo Exportar**: Cuando quieres que la OTA vea tu disponibilidad, pero tú gestionas todo desde AlojaSys

### Uso Diario

#### Ver Reservas de OTAs en AlojaSys

Las reservas que vienen de Booking.com o Airbnb aparecen automáticamente en tu lista de reservas. Se identifican porque tienen el proveedor (ej: "Booking.com") y puedes ver todos los detalles del huésped.

#### Sincronización Automática

El sistema sincroniza automáticamente:

- **⚡ Sincronización instantánea (Webhooks)** → Cuando alguien reserva en Booking.com o Airbnb, **la reserva aparece en AlojaSys en segundos**:
  - Booking.com y Airbnb envían notificaciones automáticas al sistema
  - Las reservas se crean/actualizan instantáneamente sin esperar
  - **Beneficio principal**: Evita overbooking (reservas duplicadas) porque el sistema se actualiza al instante
  - Si los webhooks no están configurados, el sistema usa el método de respaldo cada 1-2 minutos
  
- **Al crear/modificar/cancelar una reserva** en AlojaSys → Se actualiza en las OTAs en menos de 1 minuto
  - **Antes de confirmar**: El sistema verifica automáticamente si la habitación está ocupada en las OTAs para evitar sobreventas (overbooking)
  
- **Cada 1-2 minutos (respaldo)** → El sistema consulta si hay reservas nuevas en las OTAs (solo si los webhooks no están disponibles)
  
- **Cada hora** → Importa calendarios iCal si los tienes configurados:
  - Descarga los calendarios desde las URLs configuradas
  - Procesa cada evento del calendario usando su código único (UID)
  - Crea o actualiza reservas automáticamente:
    - Si es un evento nuevo → Crea una nueva reserva con estado "Confirmada"
    - Si el evento ya existe (mismo código único) → Actualiza las fechas si cambiaron
  - Identifica el origen de cada evento (Booking.com, Airbnb, iCal genérico) para rastreo
  - Respeta la configuración de "Dirección de sincronización" (solo importa si está permitido)
  - Actualiza la fecha de última sincronización exitosa
  - Registra todos los detalles en el log de sincronización (qué eventos procesó, cuántas reservas creó/actualizó, si hubo errores)
- **Todas las noches** → Sincronización completa de seguridad

#### Push Manual de Disponibilidad

Si necesitas forzar una sincronización:

1. Ve a **Configuración → OTAs**
2. En la pestaña **"Mapeos por Habitación"**
3. Clic en **"Push ARI"**
4. Selecciona:
   - **Hotel**: El hotel
   - **Proveedor**: Booking/Airbnb
   - **Desde** y **Hasta**: Rango de fechas a sincronizar
5. Clic en **"Enviar"**

El sistema actualizará disponibilidad y precios para ese rango de fechas.

#### Importar Calendarios iCal

Si usas feeds iCal:

1. En **"Mapeos por Habitación"**
2. Encuentra el mapeo que quieres importar
3. Clic en el ícono de **"Importar ahora"** (flecha hacia abajo)
4. El sistema:
   - Descargará el calendario desde la URL configurada
   - Procesará cada evento en el calendario
   - **Identifica cada evento** usando su código único (UID) para evitar duplicados
   - **Crea reservas automáticamente** con:
     - Fechas de check-in y check-out del evento
     - Estado "Confirmada"
     - Canal según el proveedor (Booking.com aparece como "Booking", Airbnb/iCal como "Otro", etc.)
     - Notas indicando que fue importado desde la OTA
     - Un identificador único (external_id) que permite al sistema reconocer si ya existe
   - **Si el evento ya existe** (mismo código único), actualiza las fechas automáticamente si cambiaron
   - **Registra cada acción** en el log de sincronización con detalles completos y consistentes:
     - Qué evento procesó (usando su código único UID)
     - Si creó una nueva reserva o actualizó una existente (o la saltó por no tener cambios)
     - Si hubo algún error o conflicto
     - El origen del evento (source: "booking", "airbnb", "ical", "expedia")
     - El canal de la reserva (channel: "booking", "expedia", "other")
     - El estado de la operación (status: "success", "skipped", "error")
     - Toda esta información está disponible en los logs para auditoría completa
5. Verás el resultado con estadísticas: cuántos eventos procesó, cuántas reservas creó, actualizó o saltó por duplicados

**Nota importante**: 
- Las reservas importadas tienen un **identificador único** (UID del evento) que permite al sistema:
  - **Evitar duplicados**: Si importas el mismo calendario varias veces, no se crean reservas duplicadas
  - **Actualizar automáticamente**: Si la OTA cambia las fechas de una reserva, se actualiza en AlojaSys automáticamente
  - **Rastrear el origen**: Puedes ver de dónde vino cada reserva en los logs de sincronización
- El sistema registra **todo lo que hace** en logs detallados y consistentes que incluyen:
  - El origen (source): Booking.com, Airbnb, iCal genérico, Expedia
  - El canal (channel): cómo aparece la reserva en el sistema
  - El estado (status): si fue exitoso, si se saltó por no tener cambios, o si hubo un error
  - El identificador único (external_id): para rastrear cada evento
  - Todos estos campos están presentes en cada log de forma consistente para facilitar el seguimiento y la auditoría

También puedes copiar la URL iCal de exportación (el botón de copiar) para compartirla con otras plataformas.

### Monitoreo y Estado

#### Sistema de Auditoría y Logs

AlojaSys registra automáticamente **todas las acciones** de sincronización con las OTAs en un sistema de logs completo y detallado. Esto te permite:

**¿Qué se registra?**

1. **Inicio de cada sincronización**:
   - Cuando se inicia automáticamente (cada hora, cada 1-2 minutos)
   - Cuando se inicia manualmente desde el sistema
   - Cuando se inicia porque creaste o modificaste una reserva

2. **Resultado de cada operación**:
   - Si una reserva se creó correctamente desde la OTA
   - Si una reserva se actualizó porque cambió la fecha
   - Si una reserva se saltó porque no tenía cambios
   - Si hubo algún error o conflicto

3. **Información del origen**:
   - De dónde vino cada reserva (Booking.com, Airbnb, iCal genérico, etc.)
   - Qué acción la causó (creación manual, webhook, importación de calendario)
   - Detalles completos de cada operación

**¿Para qué sirve?**

- ✅ **Saber qué pasó**: Puedes ver exactamente qué reservas se sincronizaron y cuándo
- ✅ **Resolver problemas**: Si algo falla, los logs te muestran exactamente dónde y por qué
- ✅ **Auditoría**: Tienes un registro completo de todas las sincronizaciones para revisar después
- ✅ **Análisis**: Puedes ver patrones de uso y detectar problemas antes de que afecten

**¿Dónde ver los logs?**

En la interfaz de **Configuración → OTAs**, en la pestaña de **"Logs"**, puedes ver todos los registros de sincronización filtrados por:
- Hotel
- Proveedor (Booking, Airbnb, etc.)
- Tipo de mensaje (éxito, advertencia, error)
- Fecha

#### Ver Última Sincronización

En la tabla de **"Mapeos por Habitación"**, encontrarás:

- **Columna "Sincronización"**: Muestra la dirección configurada (Ambos, Solo Importar, Solo Exportar)
- **Columna "Última sincronización"**: Muestra la fecha y hora de la última sincronización exitosa (import o export)
- **Columna "Última importación"**: Muestra el estado del último job de importación:
  - **success** → Todo funcionó correctamente
  - **running** → Está sincronizando en este momento
  - **failed** → Hubo un error (revisa los logs)

También muestra cuántos eventos procesó (ej: "success • 5/3+0+2" = procesó 5, creó 3 nuevos, actualizó 0, saltó 2 duplicados).

#### Ver Jobs de Sincronización

Todos los trabajos de sincronización quedan registrados para auditoría. Puedes verlos consultando el API o solicitando reportes al soporte.

**Nota sobre Webhooks**: Si tienes webhooks configurados (Booking.com o Airbnb), verás jobs adicionales marcados como "webhook" en los logs. Estos indican que las reservas fueron sincronizadas instantáneamente desde las OTAs.

#### Configurar Webhooks (Opcional pero Recomendado)

**¿Qué son los webhooks?**
Los webhooks son notificaciones instantáneas que Booking.com y Airbnb envían a AlojaSys cuando ocurre algo importante (nueva reserva, cancelación, modificación). Es como recibir un mensaje inmediato en lugar de tener que preguntar cada 1-2 minutos si pasó algo.

**¿Por qué configurarlos?**
- ✅ **Sincronización instantánea**: Las reservas aparecen en segundos, no en minutos
- ✅ **Evita overbooking**: Si alguien reserva en Booking.com, el sistema se actualiza al instante y no permite otra reserva para las mismas fechas
- ✅ **Mejor experiencia**: No hay demoras ni retrasos

**¿Cómo configurarlos?**
1. **Booking.com**:
   - Ve a Partner Hub → Configuración → Webhooks
   - Ingresa la URL: `https://tu-dominio.com/api/otas/webhooks/booking/`
   - Configura eventos: Reservas nuevas, modificaciones, cancelaciones
   - Guarda un secreto seguro (se lo proporcionarás a tu equipo técnico)

2. **Airbnb**:
   - Ve a Partner Portal → Configuración → Webhooks
   - Ingresa la URL: `https://tu-dominio.com/api/otas/webhooks/airbnb/`
   - Configura eventos similares a Booking.com

### Gestión de Pagos de Reservas OTA

#### ¿Cómo Funcionan los Pagos cuando el Huésped Reserva por una OTA?

Cuando un huésped reserva a través de Booking.com, Airbnb u otra OTA, existen dos escenarios principales de pago:

**1. Reserva Pagada por la OTA (OTA Collect)**
- El huésped paga directamente a la OTA (Booking.com, Airbnb, etc.)
- La OTA luego liquida el dinero al hotel, descontando su comisión
- El sistema marca automáticamente la reserva como **"Pagada por [nombre del canal]"** (ej: "Pagada por Booking", "Pagada por Airbnb")
- El sistema registra información detallada del pago:
  - Monto bruto que pagó el huésped
  - Comisión retenida por la OTA
  - Monto neto que recibirá el hotel
  - Fecha de liquidación (payout date)
  - Método de pago (Payout directo, Tarjeta Virtual, etc.)

**2. Reserva con Pago Directo (Hotel Collect)**
- La OTA solo envía la reserva, pero el huésped paga en el hotel
- El sistema marca la reserva como **"Pago directo"**
- El hotel debe cobrar al huésped normalmente al check-in o check-out

#### ¿Cómo Identifico las Reservas Pagadas por OTA?

En la lista de reservas, verás badges (etiquetas) que indican:
- **Badge verde "Pagada por [Canal]"**: Reserva pagada por la OTA (Booking, Airbnb, etc.)
- **Badge azul "Pago directo"**: Reserva que debe cobrarse en el hotel

Estos badges aparecen en la columna **"Estado de Pagos"** de la tabla de reservas.

#### ¿Qué Pasa si Edito una Reserva Pagada por OTA?

Si necesitas editar una reserva que fue pagada por la OTA (cambiar fechas, habitación, etc.), el sistema te muestra claramente:

1. **Banner informativo**: Indica que la reserva está "Pagada por [Canal]" y que el pago del canal no se modifica al editar
2. **Diferencia de precio**: Si cambias fechas o habitación y el nuevo precio es diferente, el sistema calcula automáticamente la diferencia
3. **Opción de conciliar**: Si hay una diferencia (el nuevo precio es mayor), puedes:
   - **Cobrar la diferencia localmente**: El botón "Cobrar diferencia" te permite registrar un pago adicional para cubrir el nuevo precio
   - El sistema genera un nuevo registro de pago local que se suma al pago original de la OTA

**Ejemplo práctico:**
- Reserva original: 2 noches por $200 (pagada por Booking)
- Editas y cambias a 3 noches: nuevo precio $300
- Diferencia: $100
- Puedes usar "Cobrar diferencia" para registrar esos $100 adicionales que el huésped debe pagar al hotel

#### Información Detallada de Pagos OTA

El sistema registra automáticamente información completa sobre los pagos de OTAs:

**En el modelo de Pago:**
- **Origen del pago**: OTA_PAYOUT, OTA_VCC (Tarjeta Virtual), HOTEL_POS, ONLINE_GATEWAY
- **Proveedor**: Booking.com, Airbnb, Expedia, etc.
- **Referencia externa**: ID de transacción de la OTA
- **Desglose financiero**:
  - Monto bruto (lo que pagó el huésped)
  - Comisión de la OTA
  - Monto neto (lo que recibirá el hotel)
- **Fechas importantes**:
  - Fecha de activación del pago
  - Fecha de liquidación (cuando la OTA transferirá el dinero)

Esta información está disponible en el sistema y permite una conciliación precisa con las liquidaciones de las OTAs.

### Detección y Manejo de Overbooking

#### ¿Qué es el Overbooking?

El **overbooking** ocurre cuando la misma habitación está reservada para dos o más huéspedes en fechas que se solapan. Esto puede pasar cuando:
- Una OTA envía una reserva que se solapa con otra ya existente
- Hay retrasos en la sincronización entre canales
- Se crean reservas manuales que no consideran reservas de OTAs

#### ¿Cómo Detecta el Sistema el Overbooking?

El sistema detecta automáticamente overbooking cuando:
1. Se recibe una reserva desde una OTA (vía webhook o importación)
2. Esa reserva se solapa con otra reserva activa en la misma habitación
3. El sistema marca automáticamente la reserva con el badge **"Overbooking"** (amarillo) en la columna **"Estado"**

**Ejemplo:**
- Reserva A: Habitación 101, 5-10 de noviembre (reserva directa del hotel)
- Reserva B: Habitación 101, 7-12 de noviembre (reserva desde Booking.com)
- Ambas ocupan la habitación los días 7, 8, 9 y 10 → Overbooking detectado

#### ¿Cómo se Comporta el Sistema con Overbooking?

**Restricciones Automáticas:**
Cuando una reserva tiene el badge "Overbooking", el sistema **bloquea automáticamente** ciertas acciones para evitar problemas:
- ❌ **No se puede confirmar** la reserva
- ❌ **No se puede hacer check-in**
- ❌ **No se puede hacer check-out**
- ❌ **No se puede cancelar** (sin resolver primero)
- ❌ **No se puede facturar**
- ✅ **Sí se puede editar** (para resolver el conflicto)

**¿Por qué solo editar?**
- Permite cambiar la reserva a otra habitación disponible
- Permite ajustar las fechas para eliminar el solapamiento
- Una vez resuelto, el badge desaparece y se habilitan todas las acciones

#### ¿Cómo Resolver un Overbooking?

**Paso 1: Identificar el conflicto**
- Revisa ambas reservas en conflicto
- Verifica fechas y habitación

**Paso 2: Decidir la solución**
- **Opción A**: Mover una reserva a otra habitación disponible
- **Opción B**: Ajustar fechas de una reserva para eliminar el solapamiento
- **Opción C**: Cancelar una de las reservas (si es necesario)

**Paso 3: Editar la reserva**
- Haz clic en "Editar" en la reserva con overbooking
- Cambia la habitación o las fechas según tu decisión
- Guarda los cambios

**Paso 4: Verificación**
- El sistema verifica automáticamente si el conflicto se resolvió
- Si ya no hay solapamiento, el badge "Overbooking" desaparece
- Todas las acciones se habilitan automáticamente

#### Beneficios del Sistema de Overbooking

- ✅ **Detección automática**: No necesitas revisar manualmente cada reserva
- ✅ **Prevención de errores**: Evita operaciones que causarían problemas (check-in en habitación ocupada)
- ✅ **Visibilidad clara**: El badge amarillo te alerta inmediatamente
- ✅ **Flexibilidad**: Te permite resolver el conflicto de la mejor manera para tu hotel
- ✅ **Auditoría**: Todos los overbookings quedan registrados para análisis posterior

3. **Proporciona los secretos** a tu equipo técnico para que los configuren en el sistema.

**Si no configuras webhooks**: El sistema funcionará igual, pero usará el método de respaldo (consulta cada 1-2 minutos), lo cual puede causar pequeños retrasos.

#### Prevención de Overbooking (Validación Automática)
#### Webhooks con seguridad e idempotencia

- Seguridad: se verifica la firma de cada notificación (HMAC-SHA256) para garantizar que provenga de la OTA.
- Idempotencia: aunque la OTA envíe el mismo evento más de una vez, el sistema lo procesa una sola vez (usa un identificador único del evento).


**¿Qué hace el sistema para evitar sobreventas?**

Antes de confirmar una reserva que creas directamente en AlojaSys, el sistema verifica automáticamente si esa habitación ya está reservada en Booking.com o Airbnb. Esto evita que tengas dos reservas para las mismas fechas.

**¿Cómo funciona?**

1. **Cuando intentas confirmar una reserva** en AlojaSys:
   - El sistema revisa todas las OTAs configuradas para esa habitación (Booking.com, Airbnb, etc.)
   - Busca si hay reservas de esas OTAs en las mismas fechas
   - Si encuentra un conflicto → **No permite confirmar la reserva**
   - Te muestra un mensaje: "La habitación no está disponible en las OTAs"

2. **Ejemplo práctico**:
   ```
   Situación:
   - 14:00: Cliente reserva Habitación 101 del 15 al 17 en Booking.com
   - 14:01: (Webhook actualiza AlojaSys instantáneamente)
   - 14:02: Recepcionista intenta crear reserva para Habitación 101 del 15 al 17
   - Resultado: Sistema rechaza la reserva → "Habitación no disponible en las OTAs"
   ```

3. **Beneficios**:
   - ✅ **Evita overbooking**: No puedes vender una habitación dos veces
   - ✅ **Funciona automáticamente**: No necesitas verificar manualmente
   - ✅ **Funciona con webhooks y sin ellos**: Aunque los webhooks no estén configurados, verifica las reservas ya sincronizadas

4. **¿Cuándo NO verifica?**
   - Para reservas que vienen de las OTAs (estas ya están sincronizadas, no pueden causar conflicto)
   - Para reservas en estado "Pendiente" (solo verifica al confirmar)
   - Si no hay OTAs configuradas para esa habitación

5. **Modo estricto vs. advertencias**:
   - **Al confirmar**: Si hay conflicto, rechaza la reserva completamente
   - **Al crear como pendiente**: Puede permitir la reserva pero agregar una advertencia en las notas

**En resumen**: El sistema te protege automáticamente de vender la misma habitación dos veces, tanto desde AlojaSys como desde las OTAs.

### Casos de Uso Reales

#### Caso 1: Hotel Boutique con Booking.com

**Situación**: El hotel recibe 70% de reservas desde Booking.com.

**Configuración**:
1. Configura Booking.com con credenciales de producción
2. Mapea 3 tipos de habitación (Simple, Doble, Suite)
3. Mapea 2 planes de tarifa (Estándar, No Reembolsable)

**Resultado**:
- ✅ Todas las reservas de Booking aparecen automáticamente en AlojaSys
- ✅ Cuando se cancela una reserva en AlojaSys, se libera en Booking en menos de 1 minuto
- ✅ Los precios se sincronizan automáticamente
- ✅ Ahorra 2 horas diarias de trabajo manual

#### Caso 2: Host Airbnb Multi-Propiedad

**Situación**: Administra 5 propiedades en Airbnb desde AlojaSys.

**Configuración**:
1. Configura Airbnb para cada propiedad
2. Mapea tipos y planes por propiedad
3. Usa iCal para importar reservas existentes

**Resultado**:
- ✅ Todas las propiedades se sincronizan desde un solo lugar
- ✅ Evita sobreventas (el sistema bloquea automáticamente)
- ✅ Gestión centralizada de todas las reservas

#### Caso 3: Hotel con Múltiples Canales

**Situación**: Vende por Booking.com, Airbnb, Expedia y sitio web propio.

**Configuración**:
1. Configura cada proveedor en AlojaSys
2. Mapea tipos y planes para cada uno

**Resultado**:
- ✅ Disponibilidad sincronizada en todos los canales
- ✅ Precios consistentes
- ✅ Sin conflictos de doble reserva
- ✅ Reportes unificados de todos los canales

### Beneficios para el Hotel

#### Para el Personal de Recepción

- ✅ **Reservas automáticas**: Las reservas de OTAs aparecen solas, no hay que copiarlas manualmente
- ✅ **Sincronización en tiempo real**: Cambios en AlojaSys se reflejan en las OTAs al instante
- ✅ **Menos errores**: No hay riesgo de olvidar actualizar disponibilidad en algún canal
- ✅ **Ahorro de tiempo**: Automatiza tareas repetitivas

#### Para la Gerencia

- ✅ **Control centralizado**: Gestiona todos los canales desde un solo lugar
- ✅ **Sin sobreventas**: El sistema evita vender la misma habitación dos veces
- ✅ **Precios consistentes**: Mantiene los precios sincronizados automáticamente
- ✅ **Reportes completos**: Métricas de todos los canales en un solo dashboard

#### Para el Negocio

- ✅ **Mayor visibilidad**: Tu hotel aparece en más plataformas sin trabajo extra
- ✅ **Aumento de reservas**: Automatización permite atender más canales simultáneamente
- ✅ **Competitividad**: Respuesta rápida a cambios de disponibilidad y precios
- ✅ **Reducción de costos**: Menos personal necesario para gestionar múltiples canales

### Resolución de Problemas

#### Problema: "Las reservas de Booking no aparecen en AlojaSys"

**Causas posibles**:
- La configuración de Booking no está activa
- Faltan credenciales válidas
- El proveedor está en modo "Test" sin datos reales

**Solución**:
1. Verifica que la configuración esté marcada como "Activa"
2. Confirma que las credenciales sean correctas
3. Si estás en modo Test, cambia a Producción cuando tengas acceso

#### Problema: "La disponibilidad no se actualiza en Booking"

**Causas posibles**:
- No hay mapeos de tipos/planes activos
- Error en la última sincronización
- Rate limiting de Booking (muchos requests)

**Solución**:
1. Verifica que tengas mapeos activos en "Tipos de Habitación" y "Planes de Tarifa"
2. Haz un "Push ARI" manual para forzar sincronización
3. Si el problema persiste, revisa los logs o contacta soporte

#### Problema: "El import iCal no funciona"

**Causas posibles**:
- La URL iCal no es válida o está expirada
- La URL requiere autenticación
- El formato del calendario no es compatible

**Solución**:
1. Verifica que la URL sea accesible (pruébala en un navegador)
2. Confirma que no requiera login adicional
3. Contacta a la OTA para obtener una URL válida

### Seguridad

#### Protección de Información Sensible

- ✅ **Tokens enmascarados**: Los tokens iCal se muestran parcialmente (solo primeros 4 caracteres) para proteger la información
- ✅ **Secrets ocultos**: Las claves secretas (Client Secret) no se muestran nunca, solo se pueden actualizar
- ✅ **URLs completas seguras**: Las URLs de iCal se generan automáticamente sin exponer el token completo

**Ejemplo**: Si tu token es `abc123xyz789`, solo verás `abc1********` en la interfaz.

#### Validación de Configuraciones

El sistema valida automáticamente tus configuraciones para prevenir errores:

- ✅ **Validación de dominios**: Verifica que las URLs de Booking.com y Airbnb sean correctas
  - Solo acepta dominios oficiales: `booking.com`, `airbnb.com`, o dominios de prueba
  - Rechaza URLs inválidas o sospechosas antes de guardar
  
- ✅ **Indicador de verificación**: Un badge "Verificado" (verde) indica que tu configuración es válida
  - Aparece automáticamente cuando la URL pasa la validación
  - Si está "No Verificado" (gris), revisa que la URL sea correcta

**Ejemplo de Validación**:
```
✅ URL válida: https://connectivity-sandbox.booking.com/api/v1/...
   → Badge: "Verificado" (verde)

❌ URL inválida: https://otro-dominio.com/api/...
   → Error: "El dominio 'otro-dominio.com' no está permitido"
   → Badge: "No Verificado" (gris)
```

#### Protección de Credenciales

- ✅ **Credenciales encriptadas**: Los secrets de API se almacenan de forma segura en la base de datos
- ✅ **Logs sanitizados**: Los logs del sistema no exponen información sensible
- ✅ **Modo Test/Prod**: Separación clara entre entornos de prueba y producción
  - No puedes mezclar credenciales de prueba con producción
  - El sistema detecta automáticamente el tipo de credenciales

#### Mejores Prácticas

**Para Tokens iCal**:
1. **No compartas tus tokens**: Son únicos para tu hotel y proveedor
2. **Rotación periódica**: Cambia tus tokens cada cierto tiempo para mayor seguridad
3. **Usa URLs completas**: El sistema genera las URLs automáticamente, no necesitas el token completo

**Para Credenciales de API (Booking/Airbnb)**:
1. **Mantén secreto el Client Secret**: Nunca lo compartas ni lo incluyas en emails
2. **Usa modo Test para desarrollo**: Prueba primero con credenciales de sandbox
3. **Verifica antes de producción**: Asegúrate de que el badge muestre "Verificado" antes de activar en producción

**Indicadores Visuales**:
- 🟢 **Badge "Verificado"**: Tu configuración es válida y lista para usar
- ⚪ **Badge "No Verificado"**: Revisa tu configuración (URL puede ser inválida)
- 🔒 **Campo tipo "password"**: Los secrets siempre se ocultan al escribir
- 📋 **Botón "Copiar URL"**: Genera la URL completa sin exponer el token

### Configuración Avanzada

#### Modo Test vs Producción

- **Test**: Para pruebas sin afectar datos reales. Usa sandbox de las OTAs.
- **Producción**: Para uso real. Solo activar cuando estés certificado y listo.

**Importante**: Nunca uses credenciales de producción en modo Test.

#### Múltiples Configuraciones por Hotel

Puedes tener varias configuraciones del mismo proveedor para un hotel si necesitas:
- Diferentes cuentas (ej: Booking.com para diferentes propiedades)
- Configuraciones de prueba y producción simultáneas

#### Personalización por Proveedor

Cada proveedor (Booking, Airbnb, etc.) tiene campos específicos. El sistema muestra solo los campos relevantes según el proveedor seleccionado.

#### Control de Dirección de Sincronización

Cada mapeo de habitación permite configurar la dirección de sincronización:

- **Ambos** (recomendado): Sincronización completa en ambas direcciones
- **Solo Importar**: Útil cuando solo quieres recibir reservas de la OTA, sin compartir tu disponibilidad
- **Solo Exportar**: Útil cuando quieres compartir disponibilidad sin importar reservas externas

**Ejemplo práctico**: Si tienes una habitación que solo se vende por tu sitio web, pero quieres que Booking.com vea que está ocupada → usa "Solo Exportar". Así, Booking.com bloqueará esas fechas, pero no recibirás reservas desde Booking para esa habitación.

---

## 3.17 Gestión de Limpieza (Housekeeping)

El módulo de Gestión de Limpieza permite gestionar de manera integral todas las tareas de limpieza y mantenimiento de las habitaciones del hotel, con asignación automática de personal, seguimiento de tareas y control de calidad mediante checklists.

### ¿Qué es el Módulo de Housekeeping?

El módulo de Housekeeping es un sistema completo que automatiza y organiza todas las actividades de limpieza del hotel, desde la creación de tareas hasta el seguimiento de su completado, asegurando que todas las habitaciones estén en perfecto estado para los huéspedes.

### Características Principales

- ✅ **Gestión completa de tareas de limpieza**: Creación, asignación, seguimiento y completado
- ✅ **Asignación automática de personal**: El sistema asigna automáticamente el mejor personal disponible
- ✅ **Generación automática de tareas**: Tareas diarias y de checkout generadas automáticamente
- ✅ **Checklists personalizables**: Listas de verificación por tipo de habitación y tipo de tarea
- ✅ **Seguimiento en tiempo real**: Estado de cada tarea visible en tiempo real
- ✅ **Control de vencimientos**: Alertas y auto-completado de tareas vencidas
- ✅ **Gestión de zonas**: Organización del hotel en zonas para mejor distribución del trabajo
- ✅ **Horarios y turnos**: Configuración de horarios de trabajo y turnos del personal
- ✅ **Notificaciones automáticas**: Alertas al personal cuando se les asigna una tarea
- ✅ **Historial completo**: Registro de todas las tareas realizadas

### Tipos de Tareas

El sistema maneja tres tipos principales de tareas:

#### 1. Tareas de Salida (Checkout)
- Se crean automáticamente cuando un huésped hace checkout
- Prioridad alta (configurable)
- Incluyen limpieza profunda de la habitación
- Checklist específico para salidas

#### 2. Tareas Diarias
- Se generan automáticamente cada día para habitaciones ocupadas
- Prioridad media (configurable)
- Incluyen limpieza básica y reposición de amenities
- Respetan reglas como "no servicio en día de check-in/checkout"

#### 3. Tareas de Mantenimiento
- Se crean manualmente cuando se requiere mantenimiento especial
- Pueden incluir reparaciones o limpieza profunda
- Checklist específico según el tipo de mantenimiento

### Estados de las Tareas

Cada tarea puede estar en uno de los siguientes estados:

- **Pendiente**: Tarea creada pero aún no iniciada
- **En Proceso**: Personal ha iniciado la tarea
- **Completada**: Tarea finalizada exitosamente
- **Cancelada**: Tarea cancelada (no se completó)

### Gestión de Personal

#### Registro de Personal de Limpieza

Puedes registrar todo tu personal de limpieza con la siguiente información:

- **Datos básicos**: Nombre, apellido
- **Horarios de trabajo**: Hora de inicio y fin del turno
- **Turno**: Mañana, Tarde o Noche
- **Zonas asignadas**: Áreas del hotel donde trabaja
- **Usuario del sistema**: Opcional, para que puedan acceder y ver sus tareas

#### Asignación Automática

El sistema asigna automáticamente el mejor personal disponible basándose en:

1. **Disponibilidad horaria**: Solo asigna a personal que está en su horario de trabajo
2. **Turno actual**: Considera si es turno mañana, tarde o noche
3. **Zonas asignadas**: Prioriza personal asignado a la zona de la habitación
4. **Carga de trabajo**: Distribuye las tareas equitativamente

**Ejemplo**: Si una habitación del Piso 2 necesita limpieza a las 10:00 AM:
- El sistema busca personal activo
- Verifica que esté en su horario (ej: 09:00 - 17:00)
- Prioriza personal asignado al "Piso 2"
- Elige quien tenga menos tareas pendientes

#### Rebalanceo Automático de Carga

**Nueva funcionalidad**: El sistema rebalancea automáticamente la carga de trabajo cada 15 minutos:

- 🔄 **Distribución equitativa**: Si un miembro del personal tiene muchas más tareas que otro, el sistema mueve tareas automáticamente
- ⚖️ **Balance inteligente**: Solo mueve tareas pendientes (no las que ya están en progreso)
- 🎯 **Respeta asignaciones**: Mantiene las zonas y turnos del personal
- 📊 **Transparente**: Todo el rebalanceo se registra en los logs del sistema

**Ejemplo práctico**:
- Personal A tiene 8 tareas pendientes
- Personal B tiene 2 tareas pendientes
- El sistema mueve automáticamente hasta 5 tareas de A a B para equilibrar la carga

### Checklists Personalizables

#### ¿Qué son los Checklists?

Los checklists son listas de verificación que definen todos los pasos que debe seguir el personal al limpiar una habitación. Puedes crear diferentes checklists para:

- **Tipos de habitación**: Single, Double, Triple, Suite
- **Tipos de tarea**: Salida, Diaria, Mantenimiento
- **Checklist general**: Para usar cuando no hay uno específico

#### Creación de Checklists

1. **Nombre y descripción**: Identifica claramente el checklist
2. **Tipo de habitación**: Opcional, para aplicar solo a ciertos tipos
3. **Tipo de tarea**: Opcional, para aplicar solo a ciertos tipos de tarea
4. **Marcar como predeterminado**: Para usar cuando no hay checklist específico

#### Items del Checklist

Cada checklist puede tener múltiples items:

- **Nombre del item**: Descripción clara (ej: "Cambiar sábanas", "Limpiar baño")
- **Descripción**: Detalles adicionales (opcional)
- **Orden**: Secuencia en que debe completarse
- **Requerido**: Si es obligatorio o opcional

**Ejemplo de Checklist de Salida**:
1. ✅ Retirar ropa de cama usada (Requerido)
2. ✅ Colocar ropa de cama nueva (Requerido)
3. ✅ Limpiar baño completo (Requerido)
4. ✅ Reponer amenities (Requerido)
5. ✅ Aspirar alfombra (Requerido)
6. ✅ Verificar funcionamiento de TV (Opcional)
7. ✅ Verificar minibar (Opcional)

### Zonas de Limpieza

#### Organización por Zonas

Las zonas te permiten organizar tu hotel en áreas lógicas:

- **Por piso**: Piso 1, Piso 2, Piso 3
- **Por ala**: Ala A, Ala B
- **Por sector**: Sector Norte, Sector Sur

**Ventajas**:
- Mejor distribución del trabajo
- Personal especializado por zona
- Más eficiencia en la limpieza

### Configuración del Sistema

#### Generación Automática de Tareas

**Tareas Diarias**:
- ✅ Activar/desactivar generación automática
- ⏰ Hora de generación (ej: 07:00 AM) - El sistema respeta la zona horaria de tu hotel
- 📅 Se generan para habitaciones ocupadas (comportamiento por defecto)
- 🏨 **Nueva opción**: Generar limpieza diaria para todas las habitaciones (ocupadas y vacías)
  - Útil para mantenimiento preventivo diario de habitaciones disponibles
  - Asegura que todas las habitaciones reciban limpieza básica regularmente
  - Las habitaciones en mantenimiento o fuera de servicio se excluyen automáticamente

**Reglas de Servicio**:
- ⏭️ Omitir servicio en día de check-in
- ⏭️ Omitir servicio en día de checkout
- 🛏️ Cambiar sábanas cada N noches (ej: cada 3 noches)
- 🧺 Cambiar toallas cada N noches (ej: cada noche)

#### Ventanas de Tiempo

Define las ventanas de tiempo para cada turno:

- **Turno Mañana**: Inicio y fin (ej: 09:00 - 13:00)
- **Turno Tarde**: Inicio y fin (ej: 13:00 - 18:00)
- **Horas de silencio**: Período donde no se debe limpiar (opcional)

#### Prioridades

Configura la prioridad por defecto para cada tipo de tarea:

- **Tareas de Salida**: Prioridad alta (2)
- **Tareas Diarias**: Prioridad media (1)

#### Control de Vencimientos

**Duración Máxima de Tareas**:
- ⏱️ Tiempo máximo en minutos (ej: 120 minutos)
- ⚠️ Marca automáticamente como vencida si se excede

**Auto-completado**:
- ✅ Activar/desactivar auto-completado de tareas vencidas
- ⏰ Minutos de gracia adicionales antes de auto-completar

### Flujos de Trabajo

#### Flujo de Checkout

1. **Huésped hace checkout** → Sistema crea automáticamente tarea de limpieza
2. **Sistema asigna personal** → Busca el mejor personal disponible
3. **Notificación al personal** → Recibe notificación de nueva tarea
4. **Personal inicia tarea** → Marca como "En Proceso"
5. **Personal completa checklist** → Verifica cada item
6. **Personal completa tarea** → Marca como "Completada"
7. **Habitación disponible** → Estado cambia a "Disponible"

#### Flujo de Limpieza Diaria

1. **Sistema verifica hora** → Cada 10 minutos, verifica si es la hora configurada según la zona horaria de tu hotel
2. **Genera tareas** → Cuando coincide la hora, crea tareas diarias automáticamente
3. **Filtra habitaciones** → 
   - Si "Generar para todas las habitaciones" está activo: crea para todas las habitaciones activas (ocupadas y vacías)
   - Si está desactivado: solo crea para habitaciones ocupadas
4. **Aplica reglas** → Omite si es día de check-in/checkout (según configuración)
5. **Asigna personal** → Distribuye equitativamente usando el algoritmo inteligente
6. **Rebalanceo automático** → Cada 15 minutos, ajusta la carga si hay desequilibrios
7. **Personal completa** → Sigue el mismo proceso que checkout

#### Flujo de Tarea Vencida

1. **Tarea en progreso** → Personal inició pero no completó
2. **Sistema verifica** → Cada hora verifica tareas vencidas
3. **Marca como vencida** → Si excede tiempo máximo configurado
4. **Auto-completa** → Si está configurado y pasa tiempo de gracia
5. **Notificación** → Alerta a supervisores si es necesario

### Mejoras de Automatización

#### Scheduler Inteligente con Zona Horaria

El sistema ahora respeta completamente la zona horaria de tu hotel:

- 🌍 **Multi-zona horaria**: Si tienes hoteles en diferentes zonas horarias, cada uno genera sus tareas a la hora local correcta
- ⏰ **Precisión horaria**: El sistema verifica cada 10 minutos si es la hora configurada según tu zona horaria
- 🎯 **Sin duplicados**: Aunque el sistema verifique frecuentemente, nunca crea tareas duplicadas para el mismo día

**Ejemplo**:
- Hotel en Buenos Aires (UTC-3): Configurado para generar tareas a las 07:00 AM
- Hotel en Madrid (UTC+1): Configurado para generar tareas a las 08:00 AM
- El sistema genera las tareas de cada hotel exactamente a su hora local, no a una hora global

#### Limpieza Preventiva para Todas las Habitaciones

**Nueva opción disponible**: "Generar limpieza diaria para todas las habitaciones (ocupadas y vacías)"

**¿Cuándo usar esta opción?**
- ✅ Quieres asegurar que todas las habitaciones reciban limpieza básica diaria, incluso si están vacías
- ✅ Prefieres un mantenimiento preventivo constante
- ✅ Tienes personal suficiente para cubrir todas las habitaciones

**¿Cuándo NO usar esta opción?**
- ❌ Solo quieres limpiar habitaciones ocupadas (comportamiento estándar)
- ❌ Tienes personal limitado y prefieres enfocarte en habitaciones con huéspedes

**Comportamiento**:
- Si está **activada**: Crea tareas diarias para habitaciones disponibles, ocupadas y reservadas
- Si está **desactivada**: Solo crea tareas para habitaciones ocupadas (comportamiento tradicional)
- En ambos casos: Excluye automáticamente habitaciones en mantenimiento o fuera de servicio

### Permisos y Roles

#### Personal de Limpieza

**Permisos**:
- ✅ Ver sus tareas asignadas
- ✅ Iniciar tareas
- ✅ Completar tareas
- ✅ Ver detalles de checklists
- ❌ No puede crear, editar o eliminar tareas
- ❌ No puede acceder a configuraciones

**Interfaz**:
- Solo ve "Gestión de Limpieza" en el menú
- Redirección automática desde Dashboard
- Vista simplificada enfocada en sus tareas

#### Comandanta (Supervisora)

**Permisos**:
- ✅ Ver todas las tareas
- ✅ Crear nuevas tareas
- ✅ Editar tareas pendientes
- ✅ Eliminar tareas pendientes
- ✅ Cancelar tareas
- ✅ Gestionar personal
- ❌ No puede acceder a configuraciones avanzadas

**Interfaz**:
- Acceso completo a gestión de tareas
- Puede reasignar tareas
- Puede crear tareas manuales

#### Administrador

**Permisos**:
- ✅ Todo lo de Comandanta
- ✅ Configurar el sistema
- ✅ Gestionar zonas
- ✅ Gestionar plantillas
- ✅ Gestionar checklists
- ✅ Gestionar personal
- ✅ Configurar reglas y horarios

### Casos de Uso Reales

#### Caso 1: Checkout Matutino

**Situación**: Huésped hace checkout a las 10:00 AM

**Proceso Automático**:
1. Sistema crea tarea de limpieza de salida
2. Asigna a personal de turno mañana disponible
3. Personal recibe notificación
4. Personal inicia tarea a las 10:15 AM
5. Completa checklist de salida
6. Marca como completada a las 11:00 AM
7. Habitación queda disponible para nuevo huésped

#### Caso 2: Limpieza Diaria

**Situación**: Habitación ocupada por 3 días

**Proceso Automático**:
1. Día 1: Sistema genera tarea diaria (omite por ser check-in)
2. Día 2: Sistema genera tarea diaria, personal limpia
3. Día 3: Sistema genera tarea diaria, personal cambia sábanas (cada 3 noches)
4. Día 4: Sistema genera tarea diaria (omite por ser checkout)

#### Caso 3: Tarea Vencida

**Situación**: Personal inició tarea pero se olvidó de completarla

**Proceso Automático**:
1. Tarea iniciada a las 10:00 AM (duración estimada: 60 min)
2. A las 11:15 AM: Sistema marca como vencida (is_overdue=True)
3. A las 11:45 AM: Si auto-completado está activo, completa automáticamente
4. Sistema actualiza estado de habitación

#### Caso 4: Personal con Horarios Específicos

**Situación**: Personal trabaja de 09:00 a 17:00

**Proceso Automático**:
1. Tarea creada a las 08:00 AM → No se asigna (fuera de horario)
2. Tarea creada a las 10:00 AM → Se asigna (dentro de horario)
3. Tarea creada a las 18:00 AM → Se asigna a personal de turno tarde

### Beneficios del Sistema

#### Para el Hotel

- ✅ **Eficiencia mejorada**: Asignación automática optimiza el trabajo
- ✅ **Control de calidad**: Checklists aseguran estándares
- ✅ **Trazabilidad**: Historial completo de todas las tareas
- ✅ **Reducción de errores**: Sistema previene olvidos
- ✅ **Optimización de recursos**: Mejor distribución del personal

#### Para el Personal

- ✅ **Claridad**: Sabe exactamente qué hacer y cuándo
- ✅ **Organización**: Tareas organizadas por prioridad
- ✅ **Notificaciones**: Recibe alertas de nuevas tareas
- ✅ **Checklists**: Guía paso a paso para cada tarea

#### Para los Huéspedes

- ✅ **Habitaciones siempre limpias**: Sistema asegura limpieza regular
- ✅ **Checkout rápido**: Limpieza inmediata después de salida
- ✅ **Calidad consistente**: Checklists garantizan estándares

### Preguntas Frecuentes

**¿Puedo crear tareas manualmente?**
Sí, los usuarios con permisos de Comandanta o Administrador pueden crear tareas manuales desde el botón "Nueva tarea".

**¿Qué pasa si no hay personal disponible?**
La tarea se crea sin asignar. Un supervisor puede asignarla manualmente más tarde.

**¿Puedo personalizar los checklists?**
Sí, puedes crear checklists específicos por tipo de habitación y tipo de tarea.

**¿Cómo funciona la asignación automática?**
El sistema considera horarios, turnos, zonas y carga de trabajo para asignar al mejor personal disponible.

**¿Qué pasa con las tareas vencidas?**
El sistema las marca automáticamente y puede auto-completarlas si está configurado.

**¿Puedo ver el historial de tareas?**
Sí, hay una página de "Histórico de Limpieza" con todas las tareas pasadas y filtros avanzados.

---

*Documento de funcionalidades del sistema AlojaSys - Enfoque en el usuario final y casos de uso prácticos.*
