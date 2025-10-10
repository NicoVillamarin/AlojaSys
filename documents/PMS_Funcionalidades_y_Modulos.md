# AlojaSys - Funcionalidades y Módulos del Sistema

## Índice
1. [¿Qué es AlojaSys?](#qué-es-alojasys)
2. [¿Cómo Funciona el Sistema?](#cómo-funciona-el-sistema)
3. [Módulos y Funcionalidades](#módulos-y-funcionalidades)
   - [3.1 Gestión de Hoteles](#31-gestión-de-hoteles)
   - [3.2 Gestión de Habitaciones](#32-gestión-de-habitaciones)
   - [3.3 Gestión de Reservas](#33-gestión-de-reservas)
   - [3.4 Sistema de Pagos](#34-sistema-de-pagos)
   - [3.5 Gestión de Tarifas](#35-gestión-de-tarifas)
   - [3.6 Dashboard y Reportes](#36-dashboard-y-reportes)
   - [3.7 Gestión de Usuarios](#37-gestión-de-usuarios)
   - [3.8 Gestión de Empresas](#38-gestión-de-empresas)
4. [Flujos de Trabajo del Día a Día](#flujos-de-trabajo-del-día-a-día)
5. [Casos de Uso Reales](#casos-de-uso-reales)
6. [Beneficios del Sistema](#beneficios-del-sistema)

---

## ¿Qué es AlojaSys?

**AlojaSys** es un sistema de gestión hotelera completo que permite administrar todos los aspectos de un hotel de manera digital y eficiente. Es como tener un asistente digital que se encarga de:

- 🏨 **Gestionar las habitaciones** y su disponibilidad
- 📅 **Administrar las reservas** desde la consulta hasta el check-out
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

#### Ejemplo Práctico
```
Hotel: "Hotel Plaza Central"
Dirección: "Av. Corrientes 1234, Buenos Aires"
Check-in: 15:00 hs
Check-out: 11:00 hs
Zona horaria: America/Argentina/Buenos_Aires
```

### Beneficios
- ✅ **Información centralizada** de cada hotel
- ✅ **Configuración flexible** de horarios
- ✅ **Soporte multi-hotel** desde una sola plataforma
- ✅ **Datos legales** para facturación

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

## 3.5 Gestión de Tarifas

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

## 3.6 Dashboard y Reportes

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

## 3.7 Gestión de Usuarios

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

## 3.8 Gestión de Empresas

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
2. Ve la lista de check-outs programados
3. Prepara las facturas
4. Realiza check-outs cuando huéspedes se van
5. Sistema actualiza habitaciones a "Disponible"
```

#### Check-ins del Día
```
1. Ve la lista de llegadas esperadas
2. Prepara habitaciones asignadas
3. Verifica pagos pendientes
4. Realiza check-ins cuando huéspedes llegan
5. Sistema actualiza habitaciones a "Ocupada"
```

### 2. Gestión de Reservas (Todo el día)

#### Nuevas Reservas
```
1. Cliente consulta disponibilidad
2. Sistema muestra habitaciones disponibles
3. Cliente selecciona habitación y fechas
4. Sistema calcula precio total
5. Cliente completa datos y pago
6. Sistema confirma reserva
```

#### Modificaciones
```
1. Cliente solicita cambio de fecha
2. Sistema verifica nueva disponibilidad
3. Calcula diferencia de precio
4. Aplica cambio si es posible
5. Notifica al cliente
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
1. Gerente revisa dashboard
2. Analiza ocupación del día
3. Revisa ingresos generados
4. Identifica oportunidades
5. Planifica para el día siguiente
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

---

## Beneficios del Sistema

### Para el Hotel
- 🏨 **Gestión eficiente** de habitaciones y reservas
- 💰 **Maximización de ingresos** con precios dinámicos
- 📊 **Análisis del negocio** con métricas en tiempo real
- 🔒 **Pagos seguros** con integración bancaria
- ⚡ **Automatización** de procesos repetitivos

### Para el Personal
- 👥 **Interfaz intuitiva** fácil de usar
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
