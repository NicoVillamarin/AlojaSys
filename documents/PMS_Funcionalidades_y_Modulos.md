# AlojaSys - Funcionalidades y Módulos del Sistema

## Índice
1. [¿Qué es AlojaSys?](#qué-es-alojasys)
2. [¿Cómo Funciona el Sistema?](#cómo-funciona-el-sistema)
3. [Módulos y Funcionalidades](#módulos-y-funcionalidades)
   - [3.1 Gestión de Hoteles](#31-gestión-de-hoteles)
   - [3.2 Gestión de Habitaciones](#32-gestión-de-habitaciones)
   - [3.3 Gestión de Reservas](#33-gestión-de-reservas)
   - [3.4 Sistema de Pagos](#34-sistema-de-pagos)
   - [3.5 Políticas de Cancelación](#35-políticas-de-cancelación)
   - [3.6 Gestión de Tarifas](#36-gestión-de-tarifas)
   - [3.7 Dashboard y Reportes](#37-dashboard-y-reportes)
   - [3.8 Calendario de Reservas](#38-calendario-de-reservas)
   - [3.9 Gestión de Usuarios](#39-gestión-de-usuarios)
   - [3.10 Gestión de Empresas](#310-gestión-de-empresas)
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
- 📊 **Generar reportes** y métricas del negocio
- 👥 **Gestionar usuarios** y permisos del personal
- 🏢 **Administrar múltiples hoteles** desde una sola plataforma

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
- **Auto No-Show**: Configuración para marcar automáticamente reservas como no-show

#### Ejemplo Práctico
```
Hotel: "Hotel Plaza Central"
Dirección: "Av. Corrientes 1234, Buenos Aires"
Check-in: 15:00 hs
Check-out: 11:00 hs
Zona horaria: America/Argentina/Buenos_Aires
Auto no-show: Habilitado
```

### Beneficios
- ✅ **Información centralizada** de cada hotel
- ✅ **Configuración flexible** de horarios
- ✅ **Soporte multi-hotel** desde una sola plataforma
- ✅ **Datos legales** para facturación
- ✅ **Auto no-show configurable** por hotel

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

### Beneficios
- ✅ **Reservas sin errores** gracias a las validaciones
- ✅ **Control de disponibilidad** en tiempo real
- ✅ **Gestión completa** del ciclo de vida
- ✅ **Datos organizados** de huéspedes

---

## 3.4 Sistema de Pagos

### ¿Qué hace?
Procesa pagos de manera segura y flexible, con políticas configurables.

---

## 3.5 Políticas de Cancelación

### ¿Qué hace?
Permite configurar reglas flexibles de cancelación para cada hotel, definiendo cuándo se puede cancelar una reserva y qué penalidades aplican.

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

#### 9. Auto No-Show de Reservas CONFIRMED
```
Gestión automática de no-shows:
1. Sistema revisa diariamente reservas confirmadas
2. Identifica reservas con fecha de check-in ya pasada
3. Marca automáticamente como no-show
4. Mantiene habitación ocupada (ya se cobró)
5. Registra logs detallados de cambio de estado
6. Motivo: "Auto no-show: check-in date passed"
7. Solo procesa hoteles con auto_no_show_enabled=True
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

## 3.6 Gestión de Tarifas

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

## 3.7 Dashboard y Reportes

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

## 3.8 Calendario de Reservas

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

## 3.9 Gestión de Usuarios

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

## 3.10 Gestión de Empresas

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

## Flujos de Trabajo del Día a Día

### 1. Recepción Matutina (8:00 AM)

#### Check-outs del Día
```
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

### 4. Cierre del Día (11:00 PM)

#### Revisión de Métricas
```
1. Gerente revisa dashboard y calendario
2. Analiza ocupación del día visualmente
3. Revisa ingresos generados
4. Identifica oportunidades en el calendario
5. Planifica para el día siguiente usando vista semanal
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

---

## Beneficios del Sistema

### Para el Hotel
- 🏨 **Gestión eficiente** de habitaciones y reservas
- 📆 **Visualización clara** de ocupación en calendario
- 💰 **Maximización de ingresos** con precios dinámicos
- 📊 **Análisis del negocio** con métricas en tiempo real
- 🔒 **Pagos seguros** con integración bancaria
- ⚡ **Automatización** de procesos repetitivos

### Para el Personal
- 👥 **Interfaz intuitiva** fácil de usar
- 📆 **Calendario visual** para gestión de reservas
- 🔍 **Información centralizada** en un solo lugar
- 📱 **Acceso desde cualquier dispositivo**
- 🚫 **Menos errores** con validaciones automáticas
- 📈 **Reportes automáticos** para análisis

### Para los Huéspedes
- 🌐 **Reservas online** 24/7
- 💳 **Pagos seguros** con tarjeta
- 📧 **Confirmaciones automáticas** por email
- 🔄 **Modificaciones fáciles** de reservas
- 📱 **Experiencia digital** completa

### Para la Empresa
- 🏢 **Gestión multi-hotel** desde una plataforma
- 📊 **Reportes consolidados** del grupo
- ⚙️ **Configuraciones centralizadas**
- 👥 **Personal compartido** entre hoteles
- 📈 **Escalabilidad** para crecer

---

## Conclusión

**AlojaSys** es más que un sistema de gestión hotelera; es una solución integral que transforma la manera de operar un hotel. Desde la gestión básica de habitaciones hasta el análisis avanzado del negocio, el sistema proporciona todas las herramientas necesarias para:

- **Automatizar** procesos manuales
- **Optimizar** la ocupación y precios
- **Mejorar** la experiencia del huésped
- **Aumentar** la eficiencia del personal
- **Maximizar** los ingresos del hotel

Con su arquitectura modular y flexible, AlojaSys se adapta a cualquier tipo de hotel, desde pequeños establecimientos boutique hasta grandes cadenas hoteleras, proporcionando una base sólida para el crecimiento y la innovación en el sector hotelero.

---

*Documento de funcionalidades del sistema AlojaSys - Enfoque en el usuario final y casos de uso prácticos.*
