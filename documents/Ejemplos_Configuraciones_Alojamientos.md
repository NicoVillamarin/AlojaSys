# Ejemplos de Configuraciones para Diferentes Tipos de Alojamientos

Este documento proporciona ejemplos prácticos de cómo configurar AlojaSys para diferentes tipos de establecimientos de alojamiento. Cada ejemplo incluye configuraciones específicas de Hotel, Habitaciones, Housekeeping y otras características relevantes.

---

## Índice

1. [Hotel Pequeño (10-30 habitaciones)](#1-hotel-pequeño-10-30-habitaciones)
2. [Hotel Mediano (30-100 habitaciones)](#2-hotel-mediano-30-100-habitaciones)
3. [Hotel Grande (100+ habitaciones)](#3-hotel-grande-100-habitaciones)
4. [Cabañas / Emprendimiento de Cabañas](#4-cabañas--emprendimiento-de-cabañas)
5. [Hostel / Albergue](#5-hostel--albergue)
6. [Apart Hotel / Residencial](#6-apart-hotel--residencial)
7. [Posada / Bed & Breakfast](#7-posada--bed--breakfast)
8. [Resort / Complejo Turístico](#8-resort--complejo-turístico)

---

## 1. Hotel Pequeño (10-30 habitaciones)

### Características Típicas
- Operación familiar o con personal reducido
- Check-in/check-out más flexibles
- Limpieza manual, sin turnos múltiples
- Atención personalizada

### Configuración del Hotel

```json
{
  "name": "Hotel Boutique San Martín",
  "legal_name": "Hotel Boutique San Martín S.A.",
  "tax_id": "30-12345678-9",
  "email": "reservas@hotelsanmartin.com",
  "phone": "+54 11 1234-5678",
  "address": "Av. San Martín 1234",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "14:00",
  "check_out_time": "11:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": false,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5491112345678"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": false,
  "daily_generation_time": "08:00",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 3,
  "towels_every_n_nights": 1,
  "morning_window_start": "09:00",
  "morning_window_end": "13:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "17:00",
  "prefer_by_zone": false,
  "rebalance_every_minutes": 10,
  "checkout_priority": 2,
  "daily_priority": 1,
  "max_task_duration_minutes": 90,
  "alert_checkout_unstarted_minutes": 30
}
```

### Ejemplo de Habitaciones

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------|
| 101 | 1 | DOUBLE | 2 | 3 | $15,000 | Habitación estándar con vista al jardín |
| 102 | 1 | DOUBLE | 2 | 3 | $15,000 | Habitación estándar con vista al jardín |
| 201 | 2 | DOUBLE | 2 | 3 | $18,000 | Habitación superior con balcón |
| 202 | 2 | TRIPLE | 3 | 4 | $22,000 | Habitación familiar |
| 301 | 3 | SUITE | 2 | 4 | $28,000 | Suite con jacuzzi |

### Notas Importantes
- **Check-in manual**: `auto_check_in_enabled: false` para atención personalizada
- **Limpieza simple**: Sin zonas complejas, asignación directa
- **Horarios flexibles**: Ventanas de limpieza más amplias
- **WhatsApp activo**: Importante para hoteles pequeños que dependen de comunicación directa

---

## 2. Hotel Mediano (30-100 habitaciones)

### Características Típicas
- Personal de limpieza organizado en turnos
- Procesos más estandarizados
- Integración con OTAs común
- Check-in/check-out más estructurados

### Configuración del Hotel

```json
{
  "name": "Hotel Plaza Central",
  "legal_name": "Hotel Plaza Central S.R.L.",
  "tax_id": "30-98765432-1",
  "email": "reservas@plazacentral.com",
  "phone": "+54 11 4321-9876",
  "address": "Av. Corrientes 2500",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": true,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5491143219876"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": false,
  "daily_generation_time": "07:00",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 3,
  "towels_every_n_nights": 1,
  "morning_window_start": "09:00",
  "morning_window_end": "13:00",
  "afternoon_window_start": "13:00",
  "afternoon_window_end": "18:00",
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "prefer_by_zone": true,
  "rebalance_every_minutes": 5,
  "checkout_priority": 2,
  "daily_priority": 1,
  "max_task_duration_minutes": 120,
  "alert_checkout_unstarted_minutes": 30,
  "auto_complete_overdue": false
}
```

### Zonas de Limpieza Recomendadas

```
- Piso 1 (Floor 1): Zona Recepción
- Piso 2 (Floor 2): Zona Centro
- Piso 3 (Floor 3): Zona Superior
- Piso 4 (Floor 4): Zona Premium
```

### Ejemplo de Habitaciones

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Extra por Huésped |
|--------|-------|------|-----------|---------------|-------------|-------------------|
| 101-110 | 1 | SINGLE | 1 | 2 | $12,000 | $3,000 |
| 201-220 | 2 | DOUBLE | 2 | 3 | $18,000 | $4,000 |
| 301-315 | 3 | DOUBLE | 2 | 3 | $20,000 | $4,000 |
| 401-410 | 4 | SUITE | 2 | 4 | $35,000 | $5,000 |

### Notas Importantes
- **Zonas activadas**: `prefer_by_zone: true` para optimizar rutas de limpieza
- **Horas de silencio**: Configuradas para respetar descanso de huéspedes
- **Auto no-show**: Habilitado para gestionar reservas no presentadas
- **Rebalanceo frecuente**: Cada 5 minutos para optimizar carga de trabajo

---

## 3. Hotel Grande (100+ habitaciones)

### Características Típicas
- Múltiples turnos de limpieza
- Procesos altamente estandarizados
- Integración completa con OTAs
- Gestión por zonas/alas
- Check-in/check-out automatizados

### Configuración del Hotel

```json
{
  "name": "Grand Hotel Internacional",
  "legal_name": "Grand Hotel Internacional S.A.",
  "tax_id": "30-11223344-5",
  "email": "reservas@grandhotel.com",
  "phone": "+54 11 5555-0000",
  "address": "Av. 9 de Julio 1500",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "auto_check_in_enabled": true,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": true,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5491155550000"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": false,
  "daily_generation_time": "06:30",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 2,
  "towels_every_n_nights": 1,
  "morning_window_start": "08:00",
  "morning_window_end": "14:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "20:00",
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "07:00",
  "prefer_by_zone": true,
  "rebalance_every_minutes": 3,
  "checkout_priority": 3,
  "daily_priority": 1,
  "max_task_duration_minutes": 90,
  "alert_checkout_unstarted_minutes": 20,
  "auto_complete_overdue": true,
  "overdue_grace_minutes": 15
}
```

### Zonas de Limpieza Recomendadas

```
- Ala Norte - Pisos 1-5 (Floor 1-5)
- Ala Sur - Pisos 1-5 (Floor 1-5)
- Ala Este - Pisos 6-10 (Floor 6-10)
- Ala Oeste - Pisos 6-10 (Floor 6-10)
- Suites Premium - Piso 11 (Floor 11)
```

### Ejemplo de Habitaciones

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Extra por Huésped |
|--------|-------|------|-----------|---------------|-------------|-------------------|
| 101-150 | 1-5 | DOUBLE | 2 | 3 | $25,000 | $5,000 |
| 201-250 | 1-5 | DOUBLE | 2 | 3 | $28,000 | $5,000 |
| 301-350 | 6-10 | DOUBLE | 2 | 3 | $32,000 | $6,000 |
| 401-450 | 6-10 | TRIPLE | 3 | 4 | $38,000 | $7,000 |
| 501-520 | 11 | SUITE | 2 | 4 | $65,000 | $10,000 |

### Notas Importantes
- **Check-in automático**: Habilitado para agilizar procesos
- **Limpieza más frecuente**: Ropa blanca cada 2 noches
- **Rebalanceo agresivo**: Cada 3 minutos para optimizar
- **Auto-completar tareas vencidas**: Para mantener flujo constante
- **Múltiples ventanas**: Mañana y tarde para cubrir todo el día

---

## 4. Cabañas / Emprendimiento de Cabañas

### Características Típicas
- Unidades independientes (no habitaciones)
- Check-in/check-out más flexibles
- Limpieza menos frecuente
- Capacidades variables (2-10+ personas)
- Estacionalidad importante

### Configuración del Hotel

```json
{
  "name": "Cabañas Los Pinos",
  "legal_name": "Cabañas Los Pinos S.R.L.",
  "tax_id": "30-55667788-9",
  "email": "reservas@cabanaslospinos.com",
  "phone": "+54 2944 12-3456",
  "address": "Ruta 40 km 123, San Carlos de Bariloche",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "10:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": false,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5492944123456"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": false,
  "daily_for_all_rooms": false,
  "daily_generation_time": "09:00",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 5,
  "towels_every_n_nights": 3,
  "morning_window_start": "10:00",
  "morning_window_end": "14:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "18:00",
  "prefer_by_zone": true,
  "rebalance_every_minutes": 15,
  "checkout_priority": 2,
  "daily_priority": 1,
  "max_task_duration_minutes": 180,
  "alert_checkout_unstarted_minutes": 60
}
```

### Zonas de Limpieza Recomendadas

```
- Zona Norte (Floor 1): Cabañas 1-5
- Zona Sur (Floor 2): Cabañas 6-10
- Zona Lago (Floor 3): Cabañas 11-15 (Premium)
- Zona Bosque (Floor 4): Cabañas 16-20
```

### Ejemplo de Cabañas (Habitaciones)

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Extra por Huésped | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------------|-------------|
| Cabaña 1 | 1 | DOUBLE | 2 | 4 | $25,000 | $5,000 | Cabaña pequeña, vista al jardín |
| Cabaña 2 | 1 | DOUBLE | 2 | 4 | $25,000 | $5,000 | Cabaña pequeña, vista al jardín |
| Cabaña 6 | 2 | TRIPLE | 4 | 6 | $35,000 | $6,000 | Cabaña mediana, chimenea |
| Cabaña 11 | 3 | SUITE | 6 | 8 | $55,000 | $7,000 | Cabaña premium, vista al lago, jacuzzi |
| Cabaña 12 | 3 | SUITE | 6 | 8 | $55,000 | $7,000 | Cabaña premium, vista al lago, jacuzzi |
| Cabaña 16 | 4 | TRIPLE | 4 | 6 | $40,000 | $6,000 | Cabaña en el bosque, más privada |

### Notas Importantes
- **Sin limpieza diaria automática**: `create_daily_tasks: false` - las cabañas se limpian solo al checkout
- **Ropa blanca menos frecuente**: Cada 5 noches (estadías más largas)
- **Check-in manual**: Para entregar llaves y explicar servicios
- **Campo Floor como zona**: Usar para agrupar por ubicación física
- **Descripciones detalladas**: Importante para destacar características únicas
- **Capacidades flexibles**: Muchas cabañas permiten huéspedes adicionales

---

## 5. Hostel / Albergue

### Características Típicas
- Habitaciones compartidas (dormitorios)
- Habitaciones privadas también disponibles
- Check-in/check-out muy flexibles
- Limpieza diaria esencial
- Precios por cama o por habitación

### Configuración del Hotel

```json
{
  "name": "Hostel Backpackers",
  "legal_name": "Hostel Backpackers S.R.L.",
  "tax_id": "30-99887766-5",
  "email": "info@hostelbackpackers.com",
  "phone": "+54 11 4444-5555",
  "address": "Av. Córdoba 2000",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "14:00",
  "check_out_time": "10:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": true,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5491144445555"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": true,
  "daily_generation_time": "08:00",
  "skip_service_on_checkin": false,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 1,
  "towels_every_n_nights": 1,
  "morning_window_start": "10:00",
  "morning_window_end": "14:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "18:00",
  "prefer_by_zone": false,
  "rebalance_every_minutes": 10,
  "checkout_priority": 3,
  "daily_priority": 2,
  "max_task_duration_minutes": 60,
  "alert_checkout_unstarted_minutes": 20
}
```

### Ejemplo de Habitaciones

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------|
| Dormitorio 1 (4 camas) | 1 | TRIPLE | 4 | 4 | $8,000 | Dormitorio mixto, 4 camas literas |
| Dormitorio 2 (6 camas) | 1 | TRIPLE | 6 | 6 | $12,000 | Dormitorio mixto, 6 camas literas |
| Dormitorio 3 (8 camas) | 1 | TRIPLE | 8 | 8 | $16,000 | Dormitorio solo mujeres |
| Habitación Privada 1 | 2 | DOUBLE | 2 | 2 | $25,000 | Habitación privada con baño |
| Habitación Privada 2 | 2 | DOUBLE | 2 | 2 | $25,000 | Habitación privada con baño |

### Notas Importantes
- **Limpieza diaria para todas**: `daily_for_all_rooms: true` - esencial en hostels
- **Limpieza al check-in**: `skip_service_on_checkin: false` - asegurar limpieza
- **Ropa blanca diaria**: Cambio diario por alta rotación
- **Precios por cama**: En dormitorios, el precio base es por cama
- **Capacidad fija**: En dormitorios, capacidad = max_capacity (no hay extras)

---

## 6. Apart Hotel / Residencial

### Características Típicas
- Unidades con cocina y living
- Estadías más largas
- Limpieza menos frecuente
- Check-in/check-out flexibles
- Servicios opcionales

### Configuración del Hotel

```json
{
  "name": "Apart Hotel Suites",
  "legal_name": "Apart Hotel Suites S.A.",
  "tax_id": "30-11223344-7",
  "email": "reservas@aparthotelsuites.com",
  "phone": "+54 11 7777-8888",
  "address": "Av. Santa Fe 3000",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": false,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5491177778888"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": false,
  "daily_for_all_rooms": false,
  "daily_generation_time": "09:00",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 7,
  "towels_every_n_nights": 3,
  "morning_window_start": "10:00",
  "morning_window_end": "14:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "18:00",
  "prefer_by_zone": true,
  "rebalance_every_minutes": 15,
  "checkout_priority": 2,
  "daily_priority": 1,
  "max_task_duration_minutes": 120,
  "alert_checkout_unstarted_minutes": 45
}
```

### Ejemplo de Apartamentos (Habitaciones)

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Extra por Huésped | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------------|-------------|
| Suite 101 | 1 | SUITE | 2 | 4 | $35,000 | $8,000 | 1 dormitorio, cocina, living |
| Suite 102 | 1 | SUITE | 2 | 4 | $35,000 | $8,000 | 1 dormitorio, cocina, living |
| Suite 201 | 2 | SUITE | 4 | 6 | $50,000 | $10,000 | 2 dormitorios, cocina, living |
| Suite 202 | 2 | SUITE | 4 | 6 | $50,000 | $10,000 | 2 dormitorios, cocina, living |
| Suite 301 | 3 | SUITE | 6 | 8 | $75,000 | $12,000 | 3 dormitorios, cocina, living, balcón |

### Notas Importantes
- **Sin limpieza diaria**: `create_daily_tasks: false` - solo al checkout
- **Ropa blanca semanal**: Cada 7 noches (estadías largas)
- **Limpieza opcional**: Se puede ofrecer como servicio extra
- **Capacidades flexibles**: Muchos apartamentos permiten huéspedes adicionales
- **Servicios extra**: Cocina equipada, WiFi, estacionamiento

---

## 7. Posada / Bed & Breakfast

### Características Típicas
- Ambiente familiar y acogedor
- Pocas habitaciones (5-15)
- Desayuno incluido
- Atención personalizada
- Check-in/check-out muy flexibles

### Configuración del Hotel

```json
{
  "name": "Posada del Sol",
  "legal_name": "Posada del Sol",
  "tax_id": "30-22334455-6",
  "email": "info@posadadelsol.com",
  "phone": "+54 2944 98-7654",
  "address": "Calle Principal 456, Villa La Angostura",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "10:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": false,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5492944987654"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": false,
  "daily_generation_time": "08:30",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 3,
  "towels_every_n_nights": 2,
  "morning_window_start": "10:00",
  "morning_window_end": "13:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "17:00",
  "prefer_by_zone": false,
  "rebalance_every_minutes": 20,
  "checkout_priority": 2,
  "daily_priority": 1,
  "max_task_duration_minutes": 90,
  "alert_checkout_unstarted_minutes": 45
}
```

### Ejemplo de Habitaciones

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------|
| Habitación Rosa | 1 | DOUBLE | 2 | 2 | $18,000 | Habitación romántica, vista al jardín |
| Habitación Azul | 1 | DOUBLE | 2 | 3 | $18,000 | Habitación familiar, cama adicional |
| Habitación Verde | 2 | DOUBLE | 2 | 2 | $20,000 | Habitación superior, balcón |
| Habitación Suite | 2 | SUITE | 2 | 4 | $28,000 | Suite familiar, living privado |

### Notas Importantes
- **Check-in muy personalizado**: Siempre manual, con tour del lugar
- **Desayuno incluido**: Registrar como servicio extra con precio $0 o incluido
- **Limpieza cuidadosa**: Más tiempo por habitación, atención al detalle
- **Nombres descriptivos**: Usar nombres en lugar de números
- **Capacidades limitadas**: Generalmente no permiten muchos extras

---

## 8. Resort / Complejo Turístico

### Características Típicas
- Múltiples tipos de alojamiento
- Muchas habitaciones/cabañas
- Servicios adicionales (SPA, restaurantes, actividades)
- Temporadas altas y bajas marcadas
- Gestión compleja por zonas

### Configuración del Hotel

```json
{
  "name": "Resort & Spa Las Montañas",
  "legal_name": "Resort & Spa Las Montañas S.A.",
  "tax_id": "30-33445566-8",
  "email": "reservas@resortlasmontanas.com",
  "phone": "+54 2944 11-2233",
  "address": "Ruta 82 km 45, San Martín de los Andes",
  "timezone": "America/Argentina/Buenos_Aires",
  "check_in_time": "15:00",
  "check_out_time": "11:00",
  "auto_check_in_enabled": false,
  "auto_check_out_enabled": true,
  "auto_no_show_enabled": true,
  "whatsapp_enabled": true,
  "whatsapp_phone": "+5492944112233"
}
```

### Configuración de Housekeeping

```json
{
  "enable_auto_assign": true,
  "create_daily_tasks": true,
  "daily_for_all_rooms": false,
  "daily_generation_time": "07:00",
  "skip_service_on_checkin": true,
  "skip_service_on_checkout": true,
  "linens_every_n_nights": 2,
  "towels_every_n_nights": 1,
  "morning_window_start": "09:00",
  "morning_window_end": "14:00",
  "afternoon_window_start": "14:00",
  "afternoon_window_end": "19:00",
  "quiet_hours_start": "23:00",
  "quiet_hours_end": "08:00",
  "prefer_by_zone": true,
  "rebalance_every_minutes": 5,
  "checkout_priority": 3,
  "daily_priority": 2,
  "max_task_duration_minutes": 120,
  "alert_checkout_unstarted_minutes": 30,
  "auto_complete_overdue": true,
  "overdue_grace_minutes": 20
}
```

### Zonas de Limpieza Recomendadas

```
- Hotel Principal - Pisos 1-4 (Floor 1-4)
- Cabañas Zona Norte (Floor 10)
- Cabañas Zona Sur (Floor 11)
- Cabañas Premium Lago (Floor 12)
- Bungalows (Floor 13)
```

### Ejemplo de Unidades (Habitaciones)

| Nombre | Floor | Tipo | Capacidad | Max Capacidad | Precio Base | Extra por Huésped | Descripción |
|--------|-------|------|-----------|---------------|-------------|-------------------|-------------|
| 101-150 | 1-4 | DOUBLE | 2 | 3 | $40,000 | $8,000 | Habitaciones hotel estándar |
| 201-250 | 1-4 | TRIPLE | 3 | 4 | $50,000 | $10,000 | Habitaciones familiares |
| 301-320 | 1-4 | SUITE | 2 | 4 | $80,000 | $12,000 | Suites premium |
| Cabaña 1-10 | 10 | TRIPLE | 4 | 6 | $60,000 | $10,000 | Cabañas estándar |
| Cabaña 11-15 | 11 | TRIPLE | 4 | 6 | $65,000 | $10,000 | Cabañas con vista |
| Cabaña Premium 1-5 | 12 | SUITE | 6 | 8 | $120,000 | $15,000 | Cabañas premium, jacuzzi |
| Bungalow 1-8 | 13 | SUITE | 4 | 6 | $70,000 | $12,000 | Bungalows independientes |

### Servicios Extra Recomendados

- SPA y masajes
- Actividades (cabalgatas, pesca, etc.)
- Restaurante (desayuno, almuerzo, cena)
- Bar
- Traslados
- Alquiler de equipos (bicicletas, kayaks, etc.)

### Notas Importantes
- **Múltiples tipos de unidades**: Hotel + Cabañas + Bungalows
- **Floor como categoría**: Usar para diferenciar tipos de alojamiento
- **Servicios extensos**: Aprovechar módulo de servicios para todo
- **Temporadas**: Configurar tarifas diferenciadas por temporada
- **Gestión compleja**: Requiere personal organizado y procesos claros

---

## Consideraciones Generales

### Campo "Floor" - Uso Flexible

El campo `floor` puede usarse de manera flexible según el tipo de alojamiento:

- **Hoteles tradicionales**: Piso real del edificio
- **Cabañas**: Zona o sector (Norte, Sur, Lago, etc.)
- **Resorts**: Tipo de alojamiento (Hotel=1-9, Cabañas=10-19, Bungalows=20-29)
- **Hostels**: Piso del edificio o área (Recepción, Patio, etc.)

### Tipos de Habitación - Adaptación

Los tipos existentes (`SINGLE`, `DOUBLE`, `TRIPLE`, `SUITE`) pueden adaptarse:

- **SINGLE**: Habitación individual, cabaña pequeña (2 personas)
- **DOUBLE**: Habitación doble, cabaña mediana (2-4 personas)
- **TRIPLE**: Habitación triple, cabaña grande (4-6 personas)
- **SUITE**: Suite, cabaña premium, apartamento (6+ personas)

### Configuración de Capacidades

- **capacity**: Capacidad incluida en el precio base
- **max_capacity**: Capacidad máxima permitida
- **extra_guest_fee**: Cargo por huésped adicional sobre la capacidad base

### Housekeeping - Frecuencias Recomendadas

| Tipo de Alojamiento | Limpieza Diaria | Ropa Blanca | Toallas |
|---------------------|----------------|-------------|---------|
| Hotel Pequeño | Solo ocupadas | Cada 3 noches | Cada noche |
| Hotel Mediano | Solo ocupadas | Cada 3 noches | Cada noche |
| Hotel Grande | Solo ocupadas | Cada 2 noches | Cada noche |
| Cabañas | Solo checkout | Cada 5 noches | Cada 3 noches |
| Hostel | Todas las habitaciones | Cada noche | Cada noche |
| Apart Hotel | Solo checkout | Cada 7 noches | Cada 3 noches |
| Posada | Solo ocupadas | Cada 3 noches | Cada 2 noches |
| Resort | Solo ocupadas | Cada 2 noches | Cada noche |

---

## Checklist de Configuración

Para cualquier tipo de alojamiento, asegúrate de configurar:

- [ ] **Hotel**: Datos básicos, horarios, timezone
- [ ] **Habitaciones**: Crear todas las unidades con nombres, tipos, capacidades y precios
- [ ] **Housekeeping**: Configurar limpieza según necesidades
- [ ] **Zonas de Limpieza**: Si aplica, crear zonas para optimizar rutas
- [ ] **Servicios Extra**: Definir servicios adicionales ofrecidos
- [ ] **Tarifas**: Configurar tarifas base y reglas especiales
- [ ] **WhatsApp**: Si aplica, configurar integración
- [ ] **OTAs**: Si aplica, configurar integraciones con Booking, Expedia, etc.
- [ ] **Usuarios y Roles**: Crear usuarios con permisos apropiados
- [ ] **Políticas de Pago**: Configurar adelantos, señas, métodos de pago

---

## Notas Finales

Este documento proporciona ejemplos de referencia. Cada establecimiento tiene sus particularidades, por lo que estas configuraciones deben adaptarse según:

- Tamaño real del establecimiento
- Personal disponible
- Estacionalidad del negocio
- Tipo de clientela
- Servicios ofrecidos
- Presupuesto y recursos

Para configuraciones más específicas o casos especiales, consultar la documentación completa del sistema o contactar al equipo de soporte.

---

**Última actualización**: 2025-01-XX  
**Versión del documento**: 1.0











