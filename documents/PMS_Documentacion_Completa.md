# AlojaSys - Sistema de Gestión Hotelera (PMS)

## Índice
1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Módulos del Sistema](#módulos-del-sistema)
   - [3.1 Módulo Core](#31-módulo-core)
   - [3.2 Módulo Reservations](#32-módulo-reservations)
   - [3.3 Módulo Rooms](#33-módulo-rooms)
   - [3.4 Módulo Payments](#34-módulo-payments)
   - [3.5 Módulo Rates](#35-módulo-rates)
   - [3.6 Módulo Users](#36-módulo-users)
   - [3.7 Módulo Enterprises](#37-módulo-enterprises)
   - [3.8 Módulo Locations](#38-módulo-locations)
   - [3.9 Módulo Dashboard](#39-módulo-dashboard)
4. [Flujos de Trabajo Principales](#flujos-de-trabajo-principales)
5. [APIs y Endpoints](#apis-y-endpoints)
6. [Configuraciones y Políticas](#configuraciones-y-políticas)
7. [Integraciones](#integraciones)

---

## Introducción

**AlojaSys** es un sistema de gestión hotelera (PMS - Property Management System) desarrollado con Django REST Framework y React. El sistema está diseñado para gestionar hoteles de manera integral, desde la gestión de habitaciones y reservas hasta el procesamiento de pagos y análisis de métricas.

### Características Principales
- ✅ Gestión completa de reservas con estados dinámicos
- ✅ Sistema de tarifas flexible con reglas y promociones
- ✅ Procesamiento de pagos con Mercado Pago y métodos manuales
- ✅ Políticas de pago configurables (adelantos, saldos)
- ✅ Dashboard con métricas en tiempo real
- ✅ Gestión multi-hotel y multi-empresa
- ✅ Sistema de usuarios con perfiles y permisos
- ✅ Integración con sistemas de pago externos

---

## Arquitectura del Sistema

### Backend (Django REST Framework)
- **Framework**: Django 4.x con Django REST Framework
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación**: JWT (JSON Web Tokens)
- **Tareas Asíncronas**: Celery con Redis
- **API**: RESTful con documentación automática

### Frontend (React)
- **Framework**: React 18 con Vite
- **UI**: Tailwind CSS + componentes personalizados
- **Estado**: Zustand para gestión de estado
- **Internacionalización**: i18next
- **Pagos**: Integración con Mercado Pago

### Infraestructura
- **Contenedores**: Docker y Docker Compose
- **Despliegue**: Render.com
- **Monitoreo**: Logs estructurados

---

## Módulos del Sistema

## 3.1 Módulo Core

**Propósito**: Gestión central de hoteles y configuraciones básicas del sistema.

### Modelos Principales

#### Hotel
```python
class Hotel(models.Model):
    enterprise = ForeignKey(Enterprise)  # Empresa propietaria
    name = CharField(120, unique=True)   # Nombre del hotel
    legal_name = CharField(200)          # Razón social
    tax_id = CharField(50)               # CUIT/CUIL
    email = EmailField()                 # Email de contacto
    phone = CharField(50)                # Teléfono
    address = CharField(200)             # Dirección
    country = ForeignKey(Country)        # País
    state = ForeignKey(State)            # Provincia/Estado
    city = ForeignKey(City)              # Ciudad
    timezone = CharField(60)             # Zona horaria
    check_in_time = TimeField()          # Hora de check-in
    check_out_time = TimeField()         # Hora de check-out
    auto_check_in_enabled = BooleanField # Check-in automático
    auto_no_show_enabled = BooleanField  # Auto no-show automático
    is_active = BooleanField             # Estado activo
```

### Funcionalidades
- ✅ Gestión de información básica del hotel
- ✅ Configuración de horarios de check-in/check-out
- ✅ Gestión de zona horaria
- ✅ Configuración de auto no-show automático
- ✅ Validación de datos (horarios no pueden ser iguales)
- ✅ Relación con empresa y ubicación

### Validaciones
- Los horarios de check-in y check-out no pueden ser iguales
- Nombre del hotel debe ser único
- Campos obligatorios: nombre, email, teléfono

---

## 3.2 Módulo Reservations

**Propósito**: Gestión completa del ciclo de vida de las reservas.

### Modelos Principales

#### Reservation
```python
class Reservation(models.Model):
    hotel = ForeignKey(Hotel)
    room = ForeignKey(Room)
    guests = PositiveIntegerField        # Número de huéspedes
    guests_data = JSONField             # Datos de todos los huéspedes
    channel = CharField(20)             # Canal de reserva
    promotion_code = CharField(50)      # Código promocional
    check_in = DateField                # Fecha de llegada
    check_out = DateField               # Fecha de salida
    status = CharField(20)              # Estado de la reserva
    total_price = DecimalField          # Precio total
    notes = TextField                   # Notas adicionales
```

#### Estados de Reserva
```python
class ReservationStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CONFIRMED = "confirmed", "Confirmada"
    CANCELLED = "cancelled", "Cancelada"
    CHECK_IN = "check_in", "Check-in"
    CHECK_OUT = "check_out", "Check-out"
    NO_SHOW = "no_show", "No-show"
    EARLY_CHECK_IN = "early_check_in", "Check-in anticipado"
    LATE_CHECK_OUT = "late_check_out", "Check-out tardío"
```

#### Canales de Reserva
```python
class ReservationChannel(models.TextChoices):
    DIRECT = "direct", "Directo"
    BOOKING = "booking", "Booking"
    EXPEDIA = "expedia", "Expedia"
    OTHER = "other", "Otro"
```

### Modelos de Soporte

#### RoomBlock
```python
class RoomBlock(models.Model):
    hotel = ForeignKey(Hotel)
    room = ForeignKey(Room)
    start_date = DateField
    end_date = DateField
    block_type = CharField(20)          # Tipo de bloqueo
    reason = CharField(200)             # Razón del bloqueo
    is_active = BooleanField
```

#### ReservationNight
```python
class ReservationNight(models.Model):
    reservation = ForeignKey(Reservation)
    hotel = ForeignKey(Hotel)
    room = ForeignKey(Room)
    date = DateField
    base_rate = DecimalField            # Tarifa base
    extra_guest_fee = DecimalField      # Extra por huésped
    discount = DecimalField             # Descuento aplicado
    tax = DecimalField                  # Impuestos
    total_night = DecimalField          # Total por noche
```

#### Payment
```python
class Payment(models.Model):
    reservation = ForeignKey(Reservation)
    date = DateField
    method = CharField(30)              # Método de pago
    amount = DecimalField               # Monto pagado
```

### Funcionalidades Principales

#### Gestión de Reservas
- ✅ **Creación de reservas** con validaciones completas
- ✅ **Validación de disponibilidad** (no solapamiento)
- ✅ **Validación de capacidad** (huéspedes vs capacidad máxima)
- ✅ **Validación de fechas** (check-in < check-out)
- ✅ **Aplicación de reglas de tarifas** (CTA/CTD, min/max stay)
- ✅ **Cálculo automático de precios** con impuestos y descuentos

#### Estados y Transiciones
- ✅ **Check-in**: Cambio de estado a "check_in", habitación a "ocupada"
- ✅ **Check-out**: Cambio de estado a "check_out", habitación a "disponible"
- ✅ **Cancelación**: Cambio de estado a "cancelled"
- ✅ **No-show**: Marcado automático de no presentación

#### Validaciones Avanzadas
- ✅ **CTA (Closed to Arrival)**: Bloqueo de llegadas en fechas específicas
- ✅ **CTD (Closed to Departure)**: Bloqueo de salidas en fechas específicas
- ✅ **Min Stay**: Mínimo de noches requeridas
- ✅ **Max Stay**: Máximo de noches permitidas
- ✅ **Días cerrados**: Bloqueo completo de fechas
- ✅ **Bloqueos de habitación**: Mantenimiento, fuera de servicio

#### APIs Principales
- `GET /api/reservations/` - Listar reservas con filtros
- `POST /api/reservations/` - Crear nueva reserva
- `GET /api/reservations/{id}/` - Obtener reserva específica
- `PUT /api/reservations/{id}/` - Actualizar reserva
- `POST /api/reservations/{id}/check_in/` - Realizar check-in
- `POST /api/reservations/{id}/check_out/` - Realizar check-out
- `GET /api/reservations/{id}/balance_info/` - Información de saldo pendiente
- `POST /api/reservations/{id}/payments/` - Registrar pago manual

#### Cotización y Disponibilidad
- `GET /api/reservations/pricing_quote/` - Cotizar precio por rango
- `GET /api/reservations/can_book/` - Validar si se puede reservar
- `POST /api/reservations/quote/` - Cotización completa con validaciones

---

## 3.3 Módulo Rooms

**Propósito**: Gestión de habitaciones y su disponibilidad.

### Modelos Principales

#### Room
```python
class Room(models.Model):
    name = CharField(255, unique=True)  # Nombre de la habitación
    hotel = ForeignKey(Hotel)           # Hotel al que pertenece
    floor = IntegerField                # Piso
    room_type = CharField(255)          # Tipo de habitación
    number = IntegerField               # Número de habitación
    description = TextField             # Descripción
    base_price = DecimalField           # Precio base
    capacity = PositiveIntegerField     # Capacidad incluida
    max_capacity = PositiveIntegerField # Capacidad máxima
    extra_guest_fee = DecimalField      # Extra por huésped adicional
    status = CharField(255)             # Estado actual
    is_active = BooleanField            # Activa/Inactiva
```

#### Tipos de Habitación
```python
class RoomType(models.TextChoices):
    SINGLE = "single", "Single"
    DOUBLE = "double", "Doble"
    TRIPLE = "triple", "Triple"
    SUITE = "suite", "Suite"
```

#### Estados de Habitación
```python
class RoomStatus(models.TextChoices):
    AVAILABLE = "available", "Disponible"
    OCCUPIED = "occupied", "Ocupada"
    MAINTENANCE = "maintenance", "Mantenimiento"
    OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"
    RESERVED = "reserved", "Reservada"
```

### Funcionalidades
- ✅ **Gestión de habitaciones** con información detallada
- ✅ **Control de capacidad** (incluida vs máxima)
- ✅ **Cálculo de extras** por huéspedes adicionales
- ✅ **Estados dinámicos** que se actualizan automáticamente
- ✅ **Filtrado y búsqueda** por tipo, estado, piso
- ✅ **Validación de disponibilidad** para reservas

### APIs Principales
- `GET /api/rooms/` - Listar habitaciones
- `POST /api/rooms/` - Crear habitación
- `GET /api/rooms/{id}/` - Obtener habitación específica
- `PUT /api/rooms/{id}/` - Actualizar habitación
- `DELETE /api/rooms/{id}/` - Eliminar habitación

---

## 3.4 Módulo Payments

**Propósito**: Gestión de pagos, políticas de pago e integración con procesadores.

### Modelos Principales

#### PaymentPolicy
```python
class PaymentPolicy(models.Model):
    hotel = ForeignKey(Hotel)
    name = CharField(120)               # Nombre de la política
    is_active = BooleanField            # Activa/Inactiva
    is_default = BooleanField           # Política por defecto
    
    # Política de adelanto
    allow_deposit = BooleanField        # Permitir depósito/seña
    deposit_type = CharField(20)        # Tipo de adelanto
    deposit_value = DecimalField        # Valor del adelanto
    deposit_due = CharField(20)         # Cuándo vence el adelanto
    deposit_days_before = PositiveIntegerField # Días antes del check-in
    
    # Dónde se cobra el saldo
    balance_due = CharField(20)         # Cuándo se cobra el saldo
    
    # Métodos de pago habilitados
    methods = ManyToManyField(PaymentMethod)
```

#### Tipos de Adelanto
```python
class DepositType(models.TextChoices):
    NONE = "none", "Sin adelanto"
    PERCENTAGE = "percentage", "Porcentaje"
    FIXED = "fixed", "Monto fijo"
```

#### Cuándo Vence el Adelanto
```python
class DepositDue(models.TextChoices):
    CONFIRMATION = "confirmation", "Al confirmar"
    DAYS_BEFORE = "days_before", "Días antes del check-in"
    CHECK_IN = "check_in", "Al check-in"
```

#### Cuándo Se Cobra el Saldo
```python
class BalanceDue(models.TextChoices):
    CHECK_IN = "check_in", "Al check-in"
    CHECK_OUT = "check_out", "Al check-out"
```

#### PaymentIntent (Mercado Pago)
```python
class PaymentIntent(models.Model):
    reservation = ForeignKey(Reservation)
    hotel = ForeignKey(Hotel)
    enterprise = ForeignKey(Enterprise)
    amount = DecimalField               # Monto a pagar
    currency = CharField(3)             # Moneda (ARS)
    description = CharField(200)        # Descripción
    
    # Campos de Mercado Pago
    mp_preference_id = CharField(80)    # ID de preferencia
    mp_payment_id = CharField(80)       # ID de pago
    external_reference = CharField(120) # Referencia externa
    
    status = CharField(20)              # Estado del pago
```

#### Estados de PaymentIntent
```python
class PaymentIntentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CREATED = "created", "Creado"
    APPROVED = "approved", "Aprobado"
    REJECTED = "rejected", "Rechazado"
    CANCELLED = "cancelled", "Cancelado"
```

#### PaymentGatewayConfig
```python
class PaymentGatewayConfig(models.Model):
    provider = CharField(30)            # Proveedor (Mercado Pago)
    enterprise = ForeignKey(Enterprise) # Empresa
    hotel = ForeignKey(Hotel)           # Hotel específico
    
    public_key = CharField(200)         # Clave pública
    access_token = CharField(200)       # Token de acceso
    integrator_id = CharField(200)      # ID del integrador
    
    is_test = BooleanField              # Modo de prueba
    country_code = CharField(2)         # Código de país
    currency_code = CharField(3)        # Código de moneda
    webhook_secret = CharField(200)     # Secreto del webhook
    is_active = BooleanField            # Activa/Inactiva
```

#### CancellationPolicy
```python
class CancellationPolicy(models.Model):
    hotel = ForeignKey(Hotel)           # Hotel al que pertenece
    name = CharField(120)               # Nombre descriptivo
    is_active = BooleanField            # Activa/Inactiva
    is_default = BooleanField           # Política por defecto
    
    # Configuración de tiempos de cancelación
    free_cancellation_time = PositiveIntegerField  # Tiempo para cancelación gratuita
    free_cancellation_unit = CharField(10)         # Unidad de tiempo (horas/días/semanas)
    partial_cancellation_time = PositiveIntegerField  # Tiempo para cancelación parcial
    partial_cancellation_unit = CharField(10)         # Unidad de tiempo
    partial_cancellation_percentage = DecimalField    # Porcentaje de penalidad
    no_cancellation_time = PositiveIntegerField    # Tiempo después del cual no hay cancelación
    no_cancellation_unit = CharField(10)           # Unidad de tiempo
    
    # Configuración de penalidades
    cancellation_fee_type = CharField(20)          # Tipo de penalidad
    cancellation_fee_value = DecimalField          # Valor de la penalidad
    cancellation_fee_percentage = DecimalField     # Porcentaje de penalidad
    
    # Mensajes personalizados
    free_cancellation_message = TextField          # Mensaje para cancelación gratuita
    partial_cancellation_message = TextField       # Mensaje para cancelación parcial
    no_cancellation_message = TextField            # Mensaje para sin cancelación
    cancellation_fee_message = TextField           # Mensaje para penalidad
    
    # Configuración avanzada
    apply_to_all_room_types = BooleanField         # Aplicar a todos los tipos
    room_types = JSONField                         # Tipos específicos
    apply_to_all_channels = BooleanField           # Aplicar a todos los canales
    channels = JSONField                           # Canales específicos
    apply_to_all_seasons = BooleanField            # Aplicar a todas las temporadas
    seasonal_rules = JSONField                     # Reglas por temporada
```

#### Tipos de Penalidad
```python
class CancellationFeeType(models.TextChoices):
    NONE = "none", "Sin penalidad"
    PERCENTAGE = "percentage", "Porcentaje del total"
    FIXED = "fixed", "Monto fijo"
    NIGHTS = "nights", "Por número de noches"
```

#### Unidades de Tiempo
```python
class TimeUnit(models.TextChoices):
    HOURS = "hours", "Horas"
    DAYS = "days", "Días"
    WEEKS = "weeks", "Semanas"
```

### Funcionalidades Principales

#### Gestión de Políticas de Pago
- ✅ **Configuración flexible** de políticas por hotel
- ✅ **Tipos de adelanto**: Sin adelanto, porcentaje, monto fijo
- ✅ **Fechas de vencimiento** configurables
- ✅ **Métodos de pago** habilitados por política
- ✅ **Política por defecto** automática

#### Gestión de Políticas de Cancelación
- ✅ **Configuración flexible** de políticas por hotel
- ✅ **Tiempos configurables**: Cancelación gratuita, parcial, sin cancelación
- ✅ **Tipos de penalidad**: Sin penalidad, porcentaje, monto fijo, por noches
- ✅ **Unidades de tiempo**: Horas, días, semanas
- ✅ **Mensajes personalizados** para cada tipo de cancelación
- ✅ **Targeting avanzado**: Por tipo de habitación, canal, temporada
- ✅ **Política por defecto** automática
- ✅ **Validación de tiempos** progresivos (gratuita > parcial > sin cancelación)

#### Procesamiento de Pagos
- ✅ **Integración con Mercado Pago** (tarjetas de crédito/débito)
- ✅ **Pagos manuales** (efectivo, transferencia, POS)
- ✅ **Webhooks** para confirmación automática
- ✅ **Gestión de estados** de pagos
- ✅ **Prevención de duplicados**

#### Cálculo de Saldos
- ✅ **Cálculo automático** de depósitos requeridos
- ✅ **Cálculo de saldos pendientes** considerando políticas
- ✅ **Validación de pagos** en check-in/check-out
- ✅ **Tolerancia de 1 centavo** para comparaciones decimales

### Servicios de Cálculo

#### calculate_deposit()
```python
def calculate_deposit(policy, total_amount):
    """
    Calcula el monto del depósito según la política de pago
    """
    # Lógica para calcular depósito basado en:
    # - Tipo: porcentaje o monto fijo
    # - Valor: % o monto específico
    # - Fecha de vencimiento
```

#### calculate_balance_due()
```python
def calculate_balance_due(reservation, policy=None):
    """
    Calcula el saldo pendiente de pago de una reserva
    """
    # Lógica para:
    # - Calcular total pagado
    # - Calcular total de reserva
    # - Determinar si hay saldo pendiente
    # - Considerar política de pagos
```

#### get_cancellation_rules()
```python
def get_cancellation_rules(self, check_in_date, room_type=None, channel=None):
    """
    Obtiene las reglas de cancelación aplicables para una reserva específica
    """
    # Lógica para:
    # - Calcular tiempo hasta el check-in
    # - Determinar tipo de cancelación (gratuita/parcial/sin cancelación)
    # - Calcular penalidad según tipo y valor configurado
    # - Retornar reglas aplicables con mensajes personalizados
```

#### resolve_for_hotel()
```python
@staticmethod
def resolve_for_hotel(hotel: Hotel):
    """
    Obtiene la política de cancelación activa para un hotel
    """
    # Lógica para:
    # - Buscar política por defecto activa
    # - Fallback a cualquier política activa
    # - Retornar política aplicable o None
```

### Servicio de Procesamiento de Devoluciones

#### RefundProcessor
```python
class RefundProcessor:
    """
    Servicio para procesar devoluciones automáticas basadas en políticas de cancelación
    """
    
    @staticmethod
    def process_refund(reservation: Reservation, cancellation_policy: CancellationPolicy):
        """
        Procesa la devolución automática de una reserva cancelada
        """
        # Lógica para:
        # - Obtener política de devolución del hotel
        # - Calcular reglas de cancelación y devolución
        # - Calcular monto total pagado
        # - Calcular penalidad según política de cancelación
        # - Calcular monto de devolución según política de devolución
        # - Procesar devolución si aplica
        # - Registrar log de cancelación con detalles financieros
```

#### Métodos de Cálculo de Devoluciones
```python
def _calculate_total_paid(reservation: Reservation) -> Decimal:
    """
    Calcula el total pagado de una reserva (manuales + tarjetas)
    """

def _calculate_penalty(reservation, cancellation_rules, total_paid) -> Decimal:
    """
    Calcula la penalidad según las reglas de cancelación
    """

def _calculate_refund_amount(total_paid, penalty_amount, refund_rules) -> Decimal:
    """
    Calcula el monto de devolución según las reglas de devolución
    """
```

### Modelo de Reembolsos Explícitos

#### Refund
```python
class Refund(models.Model):
    """
    Modelo para manejar reembolsos explícitos
    Rastrea el flujo financiero de devoluciones de dinero
    """
    reservation = ForeignKey(Reservation, related_name="refunds")
    payment = ForeignKey('reservations.Payment', related_name="refunds")
    amount = DecimalField(max_digits=10, decimal_places=2)
    reason = CharField(max_length=30, choices=RefundReason.choices)
    status = CharField(max_length=20, choices=RefundStatus.choices)
    refund_method = CharField(max_length=30)
    processing_days = PositiveIntegerField(default=7)
    external_reference = CharField(max_length=200, blank=True, null=True)
    notes = TextField(blank=True, null=True)
    processed_at = DateTimeField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User, on_delete=SET_NULL)
```

#### Estados de Reembolso
```python
class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    PROCESSING = "processing", "Procesando"
    COMPLETED = "completed", "Completado"
    FAILED = "failed", "Fallido"
    CANCELLED = "cancelled", "Cancelado"
```

#### Razones de Reembolso
```python
class RefundReason(models.TextChoices):
    CANCELLATION = "cancellation", "Cancelación de Reserva"
    PARTIAL_CANCELLATION = "partial_cancellation", "Cancelación Parcial"
    OVERPAYMENT = "overpayment", "Sobrepago"
    DISCOUNT_APPLIED = "discount_applied", "Descuento Aplicado"
    ADMIN_ADJUSTMENT = "admin_adjustment", "Ajuste Administrativo"
    CUSTOMER_REQUEST = "customer_request", "Solicitud del Cliente"
    SYSTEM_ERROR = "system_error", "Error del Sistema"
```

#### Métodos del Modelo
```python
def mark_as_processing(self):
    """Marca el reembolso como en procesamiento"""

def mark_as_completed(self, external_reference=None):
    """Marca el reembolso como completado"""

def mark_as_failed(self, notes=None):
    """Marca el reembolso como fallido"""

def cancel(self, notes=None):
    """Cancela el reembolso"""
```

### Tareas de Celery

#### Auto-cancelación de Reservas Vencidas
```python
@shared_task
def auto_cancel_expired_reservations():
    """
    Cancela automáticamente reservas pendientes que no han pagado el adelanto
    dentro del tiempo configurado en la política de pago
    """
    # Lógica para:
    # - Obtener reservas pendientes
    # - Calcular fecha de vencimiento del adelanto
    # - Cancelar reservas vencidas
    # - Liberar habitaciones
    # - Registrar logs de cancelación automática
```

#### Auto-cancelación de Reservas PENDING Vencidas
```python
@shared_task
def auto_cancel_expired_pending_reservations():
    """
    Cancela automáticamente reservas PENDING que ya pasaron su fecha de check-in
    Estas reservas no pagaron el depósito y ya no pueden hacer check-in
    """
    # Lógica para:
    # - Buscar reservas PENDING con check_in < hoy
    # - Cambiar estado a CANCELLED
    # - Liberar habitaciones automáticamente
    # - Registrar logs de cancelación automática
    # - Motivo: "Auto-cancelación: fecha de check-in vencida sin pago del depósito"
```

#### Auto No-Show de Reservas CONFIRMED
```python
@shared_task
def auto_mark_no_show_daily():
    """
    Marca automáticamente las reservas confirmadas vencidas como no-show
    Solo procesa hoteles que tienen auto_no_show_enabled=True
    """
    # Lógica para:
    # - Obtener hoteles con auto_no_show_enabled=True
    # - Buscar reservas CONFIRMED con check_in < hoy
    # - Cambiar estado a NO_SHOW
    # - Registrar logs de cambio de estado
    # - Motivo: "Auto no-show: check-in date passed"
```

#### Configuración de Celery Beat
```python
CELERY_BEAT_SCHEDULE = {
    "auto_cancel_expired_reservations_daily": {
        "task": "apps.reservations.tasks.auto_cancel_expired_reservations",
        "schedule": crontab(hour=8, minute=0),  # Diario a las 8:00 AM
    },
    "auto_cancel_expired_pending_daily": {
        "task": "apps.reservations.tasks.auto_cancel_expired_pending_reservations",
        "schedule": crontab(hour=8, minute=30),  # Diario a las 8:30 AM
    },
    "auto_mark_no_show_daily": {
        "task": "apps.reservations.tasks.auto_mark_no_show_daily",
        "schedule": crontab(hour=9, minute=0),  # Diario a las 9:00 AM
    },
}
```

#### Cronograma de Tareas Automáticas
1. **8:00 AM** - `auto_cancel_expired_reservations`: Cancela por falta de pago del depósito
2. **8:30 AM** - `auto_cancel_expired_pending_reservations`: Cancela PENDING vencidas
3. **9:00 AM** - `auto_mark_no_show_daily`: Marca CONFIRMED como no-show

#### Lógica de Cancelación Automática
- **Reservas PENDING vencidas**: `PENDING` → `CANCELLED` (liberar habitación)
- **Reservas CONFIRMED vencidas**: `CONFIRMED` → `NO_SHOW` (mantener habitación ocupada)
- **Configuración por hotel**: Campo `auto_no_show_enabled` en modelo Hotel

### APIs Principales
- `GET /api/payments/policies/` - Listar políticas de pago
- `POST /api/payments/policies/` - Crear política de pago
- `GET /api/payments/methods/` - Listar métodos de pago
- `POST /api/payments/process_card/` - Procesar pago con tarjeta
- `POST /api/payments/webhook/` - Webhook de Mercado Pago
- `GET /api/payments/reservation/{id}/payments/` - Pagos de una reserva

### APIs de Políticas de Cancelación
- `GET /api/payments/cancellation-policies/` - Listar políticas de cancelación
- `POST /api/payments/cancellation-policies/` - Crear política de cancelación
- `GET /api/payments/cancellation-policies/{id}/` - Obtener política específica
- `PUT /api/payments/cancellation-policies/{id}/` - Actualizar política
- `DELETE /api/payments/cancellation-policies/{id}/` - Eliminar política
- `GET /api/payments/cancellation-policies/for_hotel/` - Política activa por hotel
- `POST /api/payments/cancellation-policies/set_default/` - Establecer como predeterminada
- `POST /api/payments/cancellation-policies/{id}/calculate_cancellation/` - Calcular reglas
- `GET /api/reservations/{id}/cancellation_rules/` - Reglas para reserva específica (usa política histórica)
- `GET /api/reservations/{id}/refund_history/` - Historial de devoluciones
- `GET /api/payments/refunds/` - Listar reembolsos
- `POST /api/payments/refunds/` - Crear reembolso
- `GET /api/payments/refunds/{id}/` - Obtener reembolso específico
- `PUT /api/payments/refunds/{id}/` - Actualizar reembolso
- `POST /api/payments/refunds/{id}/update_status/` - Actualizar estado del reembolso
- `GET /api/payments/refunds/for_reservation/` - Reembolsos por reserva
- `GET /api/payments/refunds/stats/` - Estadísticas de reembolsos
- `POST /api/reservations/auto_cancel_expired/` - Ejecutar auto-cancelación manual
- `GET /api/reservations/pending_expiration_stats/` - Estadísticas de reservas pendientes

---

## 3.5 Módulo Rates

**Propósito**: Gestión de tarifas, promociones e impuestos.

### Modelos Principales

#### RatePlan
```python
class RatePlan(models.Model):
    hotel = ForeignKey(Hotel)
    name = CharField(120)               # Nombre del plan
    code = CharField(40)                # Código interno
    is_active = BooleanField            # Activo/Inactivo
    priority = PositiveIntegerField     # Prioridad (mayor = más prioridad)
```

#### RateRule
```python
class RateRule(models.Model):
    plan = ForeignKey(RatePlan)
    name = CharField(120)               # Nombre de la regla
    
    # Ventana de fechas
    start_date = DateField
    end_date = DateField
    
    # Días de la semana
    apply_mon = BooleanField
    apply_tue = BooleanField
    apply_wed = BooleanField
    apply_thu = BooleanField
    apply_fri = BooleanField
    apply_sat = BooleanField
    apply_sun = BooleanField
    
    # Target (aplicación)
    target_room = ForeignKey(Room)      # Habitación específica
    target_room_type = CharField(30)    # Tipo de habitación
    channel = CharField(50)             # Canal de reserva
    
    # Prioridad y precios
    priority = PositiveIntegerField     # Prioridad de la regla
    price_mode = CharField(10)          # Modo de precio
    base_amount = DecimalField          # Monto base
    extra_guest_fee_amount = DecimalField # Extra por huésped
    
    # Restricciones
    min_stay = PositiveIntegerField     # Mínimo de noches
    max_stay = PositiveIntegerField     # Máximo de noches
    closed = BooleanField               # Día cerrado
    closed_to_arrival = BooleanField    # Cerrado a llegadas
    closed_to_departure = BooleanField  # Cerrado a salidas
```

#### Modos de Precio
```python
class PriceMode(models.TextChoices):
    ABSOLUTE = "absolute", "Absoluto"
    DELTA = "delta", "Delta sobre la tarifa base"
```

#### RateOccupancyPrice
```python
class RateOccupancyPrice(models.Model):
    rule = ForeignKey(RateRule)
    occupancy = PositiveIntegerField    # Número de huéspedes
    price = DecimalField                # Precio para esa ocupación
```

#### PromoRule
```python
class PromoRule(models.Model):
    hotel = ForeignKey(Hotel)
    plan = ForeignKey(RatePlan)         # Plan específico (opcional)
    name = CharField(120)               # Nombre de la promoción
    code = CharField(40)                # Código promocional
    
    # Ventana de fechas
    start_date = DateField
    end_date = DateField
    
    # Días de la semana
    apply_mon = BooleanField
    apply_tue = BooleanField
    apply_wed = BooleanField
    apply_thu = BooleanField
    apply_fri = BooleanField
    apply_sat = BooleanField
    apply_sun = BooleanField
    
    # Target
    target_room = ForeignKey(Room)
    target_room_type = CharField(30)
    channel = CharField(50)
    
    # Descuento
    priority = PositiveIntegerField
    discount_type = CharField(10)       # Tipo de descuento
    discount_value = DecimalField       # Valor del descuento
    scope = CharField(20)               # Alcance del descuento
    combinable = BooleanField           # Combinable con otras promos
    is_active = BooleanField
```

#### Tipos de Descuento
```python
class DiscountType(models.TextChoices):
    PERCENT = "percent", "Porcentaje"
    FIXED = "fixed", "Monto fijo"
```

#### Alcance de Promociones
```python
class PromoScope(models.TextChoices):
    PER_NIGHT = "per_night", "Por noche"
    PER_RESERVATION = "per_reservation", "Por reserva"
```

#### TaxRule
```python
class TaxRule(models.Model):
    hotel = ForeignKey(Hotel)
    name = CharField(120)               # Nombre del impuesto
    channel = CharField(50)             # Canal específico
    amount_type = CharField(10)         # Tipo de monto
    percent = DecimalField              # Porcentaje
    fixed_amount = DecimalField         # Monto fijo
    scope = CharField(30)               # Alcance del impuesto
    priority = PositiveIntegerField     # Prioridad
    is_active = BooleanField
```

#### Tipos de Monto de Impuesto
```python
class TaxAmountType(models.TextChoices):
    PERCENT = "percent", "Porcentaje"
    FIXED = "fixed", "Monto fijo"
```

#### Alcance de Impuestos
```python
class TaxScope(models.TextChoices):
    PER_NIGHT = "per_night", "Por noche"
    PER_RESERVATION = "per_reservation", "Por reserva"
    PER_GUEST_PER_NIGHT = "per_guest_per_night", "Por huésped por noche"
```

### Funcionalidades Principales

#### Motor de Tarifas
- ✅ **Cálculo dinámico** de precios por fecha
- ✅ **Aplicación de reglas** por prioridad
- ✅ **Soporte para múltiples planes** de tarifas
- ✅ **Precios por ocupación** específica
- ✅ **Modos de precio** (absoluto y delta)

#### Sistema de Promociones
- ✅ **Códigos promocionales** opcionales
- ✅ **Descuentos por porcentaje** o monto fijo
- ✅ **Alcance configurable** (por noche o por reserva)
- ✅ **Aplicación por días** de la semana
- ✅ **Targeting específico** (habitación, tipo, canal)
- ✅ **Promociones combinables** opcionales

#### Sistema de Impuestos
- ✅ **Impuestos por porcentaje** o monto fijo
- ✅ **Alcance flexible** (por noche, por reserva, por huésped)
- ✅ **Aplicación por canal** específico
- ✅ **Priorización** de reglas

#### Restricciones de Venta
- ✅ **CTA (Closed to Arrival)**: Bloqueo de llegadas
- ✅ **CTD (Closed to Departure)**: Bloqueo de salidas
- ✅ **Días cerrados**: Bloqueo completo
- ✅ **Min/Max Stay**: Restricciones de estadía
- ✅ **Aplicación por días** de la semana

### Motor de Cálculo

#### get_applicable_rule()
```python
def get_applicable_rule(room, on_date, channel=None, include_closed=True):
    """
    Obtiene la regla de tarifa aplicable para una habitación en una fecha
    """
    # Lógica para:
    # - Buscar planes activos por prioridad
    # - Filtrar reglas por fecha y días de la semana
    # - Aplicar targeting (habitación, tipo, canal)
    # - Retornar la regla con mayor prioridad
```

#### compute_rate_for_date()
```python
def compute_rate_for_date(room, guests, on_date, channel=None, promotion_code=None):
    """
    Calcula el precio para una habitación en una fecha específica
    """
    # Lógica para:
    # - Obtener regla aplicable
    # - Calcular precio base y extras por huésped
    # - Aplicar precios por ocupación si existen
    # - Aplicar promociones si se proporciona código
    # - Retornar desglose completo de precios
```

### APIs Principales
- `GET /api/rates/plans/` - Listar planes de tarifas
- `POST /api/rates/plans/` - Crear plan de tarifas
- `GET /api/rates/rules/` - Listar reglas de tarifas
- `POST /api/rates/rules/` - Crear regla de tarifas
- `GET /api/rates/promos/` - Listar promociones
- `POST /api/rates/promos/` - Crear promoción
- `GET /api/rates/taxes/` - Listar impuestos
- `POST /api/rates/taxes/` - Crear impuesto
- `GET /api/rates/preview_rate/` - Vista previa de tarifa
- `GET /api/rates/rate_choices/` - Opciones para formularios

---

## 3.6 Módulo Users

**Propósito**: Gestión de usuarios, autenticación y perfiles.

### Modelos Principales

#### UserProfile
```python
class UserProfile(models.Model):
    user = OneToOneField(User)          # Usuario de Django
    hotels = ManyToManyField(Hotel)     # Hoteles asignados
    phone = CharField(50)               # Teléfono
    position = CharField(100)           # Cargo
    is_active = BooleanField            # Activo/Inactivo
```

### Funcionalidades
- ✅ **Perfiles extendidos** de usuarios
- ✅ **Asignación múltiple** de hoteles por usuario
- ✅ **Información adicional** (teléfono, cargo)
- ✅ **Control de acceso** por hotel
- ✅ **Gestión de permisos** granular

### APIs Principales
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/refresh/` - Renovar token
- `GET /api/users/profile/` - Obtener perfil
- `PUT /api/users/profile/` - Actualizar perfil

---

## 3.7 Módulo Enterprises

**Propósito**: Gestión de empresas y organizaciones.

### Modelos Principales

#### Enterprise
```python
class Enterprise(models.Model):
    name = CharField(150, unique=True)  # Nombre de la empresa
    legal_name = CharField(200)         # Razón social
    tax_id = CharField(50)              # CUIT/CUIL
    email = EmailField                  # Email de contacto
    phone = CharField(50)               # Teléfono
    address = CharField(200)            # Dirección
    country = ForeignKey(Country)       # País
    state = ForeignKey(State)           # Provincia/Estado
    city = ForeignKey(City)             # Ciudad
    is_active = BooleanField            # Activa/Inactiva
```

### Funcionalidades
- ✅ **Gestión de empresas** con información completa
- ✅ **Relación con hoteles** (una empresa puede tener múltiples hoteles)
- ✅ **Configuraciones globales** por empresa
- ✅ **Validación de datos** empresariales

### APIs Principales
- `GET /api/enterprises/` - Listar empresas
- `POST /api/enterprises/` - Crear empresa
- `GET /api/enterprises/{id}/` - Obtener empresa específica
- `PUT /api/enterprises/{id}/` - Actualizar empresa

---

## 3.8 Módulo Locations

**Propósito**: Gestión de ubicaciones geográficas.

### Modelos Principales

#### Country
```python
class Country(models.Model):
    code2 = CharField(2, unique=True)   # Código ISO-3166-1 alpha-2
    code3 = CharField(3, unique=True)   # Código ISO-3166-1 alpha-3
    name = CharField(120, unique=True)  # Nombre del país
    phone_code = CharField(6)           # Código telefónico
    currency_code = CharField(3)        # Código de moneda
```

#### State
```python
class State(models.Model):
    country = ForeignKey(Country)
    code = CharField(10)                # Código ISO-3166-2
    name = CharField(120)               # Nombre de la provincia/estado
```

#### City
```python
class City(models.Model):
    state = ForeignKey(State)
    name = CharField(120)               # Nombre de la ciudad
    postal_code = CharField(20)         # Código postal
    lat = DecimalField(9, 6)            # Latitud
    lng = DecimalField(9, 6)            # Longitud
```

### Funcionalidades
- ✅ **Jerarquía geográfica** completa (País → Estado → Ciudad)
- ✅ **Códigos estándar** ISO para integración
- ✅ **Coordenadas geográficas** para mapas
- ✅ **Códigos postales** para validaciones
- ✅ **Relación con hoteles** y empresas

### APIs Principales
- `GET /api/locations/countries/` - Listar países
- `GET /api/locations/states/` - Listar estados/provincias
- `GET /api/locations/cities/` - Listar ciudades

---

## 3.9 Módulo Dashboard

**Propósito**: Métricas, reportes y análisis del negocio.

### Modelos Principales

#### DashboardMetrics
```python
class DashboardMetrics(models.Model):
    hotel = ForeignKey(Hotel)
    date = DateField                    # Fecha de las métricas
    
    # Métricas de habitaciones
    total_rooms = PositiveIntegerField
    available_rooms = PositiveIntegerField
    occupied_rooms = PositiveIntegerField
    maintenance_rooms = PositiveIntegerField
    out_of_service_rooms = PositiveIntegerField
    reserved_rooms = PositiveIntegerField
    
    # Métricas de reservas
    total_reservations = PositiveIntegerField
    pending_reservations = PositiveIntegerField
    confirmed_reservations = PositiveIntegerField
    cancelled_reservations = PositiveIntegerField
    check_in_today = PositiveIntegerField
    check_out_today = PositiveIntegerField
    no_show_today = PositiveIntegerField
    
    # Métricas de huéspedes
    total_guests = PositiveIntegerField
    guests_checked_in = PositiveIntegerField
    guests_expected_today = PositiveIntegerField
    guests_departing_today = PositiveIntegerField
    
    # Métricas financieras
    total_revenue = DecimalField
    average_room_rate = DecimalField
    occupancy_rate = DecimalField
    
    # Ocupación por tipo de habitación
    single_rooms_occupied = PositiveIntegerField
    double_rooms_occupied = PositiveIntegerField
    triple_rooms_occupied = PositiveIntegerField
    suite_rooms_occupied = PositiveIntegerField
```

### Funcionalidades Principales

#### Cálculo de Métricas
- ✅ **Métricas de habitaciones** (disponibles, ocupadas, mantenimiento)
- ✅ **Métricas de reservas** (totales, por estado, llegadas/salidas)
- ✅ **Métricas de huéspedes** (totales, check-in, esperados)
- ✅ **Métricas financieras** (ingresos, ADR, ocupación)
- ✅ **Ocupación por tipo** de habitación

#### Tareas Asíncronas
- ✅ **Cálculo diario** automático de métricas
- ✅ **Backfill** de métricas históricas
- ✅ **Procesamiento** por lotes de hoteles
- ✅ **Manejo de errores** y reintentos

#### Métodos de Cálculo
```python
@classmethod
def calculate_metrics(cls, hotel, target_date=None):
    """
    Calcula y actualiza las métricas para un hotel en una fecha específica
    """
    # Lógica para:
    # - Calcular métricas de habitaciones
    # - Calcular métricas de reservas
    # - Calcular métricas de huéspedes
    # - Calcular métricas financieras
    # - Calcular ocupación por tipo
    # - Guardar métricas en base de datos
```

### Tareas Celery
- `calculate_dashboard_metrics_for_date()` - Calcular métricas para fecha específica
- `calculate_dashboard_metrics_daily()` - Calcular métricas diarias
- `backfill_dashboard_metrics()` - Rellenar métricas históricas

### APIs Principales
- `GET /api/dashboard/metrics/` - Obtener métricas del dashboard
- `GET /api/dashboard/metrics/{hotel_id}/` - Métricas de hotel específico
- `GET /api/dashboard/metrics/range/` - Métricas por rango de fechas

---

## Flujos de Trabajo Principales

### 1. Flujo de Reserva Completo

#### 1.1 Cotización
1. **Cliente solicita cotización** con fechas, habitación, huéspedes
2. **Sistema valida disponibilidad** (no solapamiento, capacidad)
3. **Sistema aplica reglas de tarifas** (CTA/CTD, min/max stay)
4. **Sistema calcula precios** por noche con impuestos
5. **Sistema retorna cotización** detallada

#### 1.2 Creación de Reserva
1. **Cliente confirma reserva** con datos de huéspedes
2. **Sistema valida datos** (fechas, capacidad, reglas)
3. **Sistema crea reserva** en estado "PENDING"
4. **Sistema genera noches** de reserva con precios
5. **Sistema calcula total** de la reserva

#### 1.3 Procesamiento de Pago
1. **Sistema determina política** de pago del hotel
2. **Cliente selecciona tipo** de pago (adelanto/total)
3. **Sistema calcula monto** según política
4. **Cliente procesa pago** (tarjeta/manual)
5. **Sistema confirma reserva** si pago exitoso

#### 1.4 Check-in
1. **Personal inicia check-in** de reserva confirmada
2. **Sistema valida fecha** de check-in
3. **Sistema verifica saldo pendiente** según política
4. **Si hay saldo**: Sistema solicita pago del saldo
5. **Sistema actualiza estado** a "CHECK_IN"
6. **Sistema actualiza habitación** a "OCCUPIED"

#### 1.5 Check-out
1. **Personal inicia check-out** de reserva
2. **Sistema valida fecha** de check-out
3. **Sistema verifica saldo pendiente** si aplica
4. **Si hay saldo**: Sistema solicita pago del saldo
5. **Sistema actualiza estado** a "CHECK_OUT"
6. **Sistema actualiza habitación** a "AVAILABLE"

### 2. Flujo de Gestión de Tarifas

#### 2.1 Configuración de Plan de Tarifas
1. **Administrador crea plan** de tarifas
2. **Administrador define reglas** por fechas y días
3. **Administrador configura precios** base y extras
4. **Administrador establece restricciones** (CTA/CTD, min/max stay)
5. **Sistema activa plan** para uso

#### 2.2 Aplicación de Promociones
1. **Administrador crea promoción** con código
2. **Administrador define descuento** (porcentaje/monto)
3. **Administrador establece alcance** (por noche/reserva)
4. **Cliente ingresa código** promocional
5. **Sistema aplica descuento** en cotización

### 3. Flujo de Gestión de Pagos

#### 3.1 Configuración de Política
1. **Administrador crea política** de pago
2. **Administrador define adelanto** (tipo y valor)
3. **Administrador establece fechas** de vencimiento
4. **Administrador selecciona métodos** de pago
5. **Sistema activa política** para reservas

#### 3.2 Procesamiento de Pago con Tarjeta
1. **Cliente selecciona pago** con tarjeta
2. **Sistema crea PaymentIntent** con Mercado Pago
3. **Sistema genera preferencia** de pago
4. **Cliente completa pago** en formulario seguro
5. **Webhook confirma pago** y actualiza estado
6. **Sistema crea registro** de Payment

#### 3.3 Procesamiento de Pago Manual
1. **Cliente selecciona método** manual (efectivo/transferencia/POS)
2. **Personal registra pago** manualmente
3. **Sistema crea registro** de Payment
4. **Sistema actualiza saldo** de reserva

### 4. Flujo de Cancelación de Reservas

#### 4.1 Endpoint Unificado de Cancelación
El sistema ahora utiliza un endpoint unificado `/api/reservations/{id}/cancel/` que maneja tanto el cálculo como la confirmación de cancelación, simplificando el flujo del frontend.

#### 4.2 Flujo de Dos Pasos
1. **Paso 1 - Cálculo**: Frontend llama al endpoint con `confirm=false`
   - Sistema evalúa políticas históricas y actuales
   - Calcula penalidades y devoluciones
   - Devuelve información completa sin procesar cancelación
2. **Paso 2 - Confirmación**: Frontend llama al endpoint con `confirm=true`
   - Sistema procesa la cancelación real
   - Ejecuta devolución automática
   - Actualiza estados y registra logs

#### 4.3 Evaluación de Políticas
1. **Política Histórica**: Se usa `reservation.applied_cancellation_policy` (vigente al crear la reserva)
2. **Política de Devolución**: Se obtiene la política actual del hotel
3. **Cálculo de Reglas**: Se evalúan según la fecha de check-in
4. **Consistencia Garantizada**: Independientemente de cambios posteriores

#### 4.4 Procesamiento Automático de Devoluciones
1. **Sistema calcula total pagado** de la reserva
2. **Sistema aplica penalidad** según política de cancelación histórica
3. **Sistema calcula monto de devolución** según política de devolución
4. **Sistema procesa devolución** por método de pago original
5. **Sistema crea registro explícito** en tabla `Refund`
6. **Sistema registra log** con detalles financieros completos

#### 4.5 Ventajas del Endpoint Unificado
- **Simplificación**: Un solo endpoint para cálculo y confirmación
- **Consistencia**: Misma lógica para ambos pasos
- **Flexibilidad**: Frontend puede decidir cuándo confirmar
- **Eficiencia**: Menos llamadas API necesarias
- **Mantenibilidad**: Lógica centralizada en un solo lugar

---

## APIs y Endpoints

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/refresh/` - Renovar token JWT

### Reservas
- `GET /api/reservations/` - Listar reservas (con filtros)
- `POST /api/reservations/` - Crear reserva
- `GET /api/reservations/{id}/` - Obtener reserva
- `PUT /api/reservations/{id}/` - Actualizar reserva
- `DELETE /api/reservations/{id}/` - Eliminar reserva
- `POST /api/reservations/{id}/check_in/` - Check-in
- `POST /api/reservations/{id}/check_out/` - Check-out
- `GET /api/reservations/{id}/balance_info/` - Saldo pendiente
- `POST /api/reservations/{id}/payments/` - Registrar pago
- `POST /api/reservations/{id}/cancel/` - **Cancelar reserva (unificado)**
- `GET /api/reservations/{id}/cancellation_rules/` - Reglas de cancelación (deprecated)
- `GET /api/reservations/pricing_quote/` - Cotizar precio
- `GET /api/reservations/can_book/` - Validar disponibilidad
- `POST /api/reservations/quote/` - Cotización completa

### Habitaciones
- `GET /api/rooms/` - Listar habitaciones
- `POST /api/rooms/` - Crear habitación
- `GET /api/rooms/{id}/` - Obtener habitación
- `PUT /api/rooms/{id}/` - Actualizar habitación
- `DELETE /api/rooms/{id}/` - Eliminar habitación

### Pagos
- `GET /api/payments/policies/` - Políticas de pago
- `POST /api/payments/policies/` - Crear política
- `GET /api/payments/methods/` - Métodos de pago
- `POST /api/payments/process_card/` - Procesar tarjeta
- `POST /api/payments/webhook/` - Webhook Mercado Pago
- `GET /api/payments/reservation/{id}/payments/` - Pagos de reserva

### Políticas de Cancelación
- `GET /api/payments/cancellation-policies/` - Políticas de cancelación
- `POST /api/payments/cancellation-policies/` - Crear política
- `GET /api/payments/cancellation-policies/{id}/` - Obtener política
- `PUT /api/payments/cancellation-policies/{id}/` - Actualizar política
- `DELETE /api/payments/cancellation-policies/{id}/` - Eliminar política
- `GET /api/payments/cancellation-policies/for_hotel/` - Política por hotel
- `POST /api/payments/cancellation-policies/set_default/` - Establecer predeterminada
- `POST /api/payments/cancellation-policies/{id}/calculate_cancellation/` - Calcular reglas
- `GET /api/reservations/{id}/cancellation_rules/` - Reglas de cancelación

### Tarifas
- `GET /api/rates/plans/` - Planes de tarifas
- `POST /api/rates/plans/` - Crear plan
- `GET /api/rates/rules/` - Reglas de tarifas
- `POST /api/rates/rules/` - Crear regla
- `GET /api/rates/promos/` - Promociones
- `POST /api/rates/promos/` - Crear promoción
- `GET /api/rates/taxes/` - Impuestos
- `POST /api/rates/taxes/` - Crear impuesto
- `GET /api/rates/preview_rate/` - Vista previa
- `GET /api/rates/rate_choices/` - Opciones

### Dashboard
- `GET /api/dashboard/metrics/` - Métricas generales
- `GET /api/dashboard/metrics/{hotel_id}/` - Métricas por hotel
- `GET /api/dashboard/metrics/range/` - Métricas por rango

### Ubicaciones
- `GET /api/locations/countries/` - Países
- `GET /api/locations/states/` - Estados/Provincias
- `GET /api/locations/cities/` - Ciudades

### Usuarios
- `GET /api/users/profile/` - Perfil de usuario
- `PUT /api/users/profile/` - Actualizar perfil

### Empresas
- `GET /api/enterprises/` - Listar empresas
- `POST /api/enterprises/` - Crear empresa
- `GET /api/enterprises/{id}/` - Obtener empresa
- `PUT /api/enterprises/{id}/` - Actualizar empresa

---

## Configuraciones y Políticas

### Políticas de Pago
- **Sin adelanto**: Pago completo al confirmar
- **Porcentaje**: Adelanto del X% del total
- **Monto fijo**: Adelanto de $X fijo
- **Vencimiento**: Al confirmar, días antes, al check-in
- **Saldo**: Al check-in o al check-out

### Políticas de Cancelación
- **Cancelación gratuita**: Sin penalidad hasta X tiempo antes
- **Cancelación parcial**: Penalidad del X% hasta Y tiempo antes
- **Sin cancelación**: No se permite cancelación después de Z tiempo
- **Tipos de penalidad**: Sin penalidad, porcentaje, monto fijo, por noches
- **Unidades de tiempo**: Horas, días, semanas
- **Targeting**: Por tipo de habitación, canal, temporada
- **Mensajes personalizados**: Para cada tipo de cancelación

### Reglas de Tarifas
- **Modo absoluto**: Precio fijo por noche
- **Modo delta**: Incremento sobre tarifa base
- **Restricciones**: CTA, CTD, min/max stay
- **Targeting**: Por habitación, tipo, canal
- **Prioridad**: Mayor número = mayor prioridad

### Promociones
- **Códigos**: Opcionales para activación
- **Descuentos**: Porcentaje o monto fijo
- **Alcance**: Por noche o por reserva
- **Combinables**: Múltiples promociones simultáneas
- **Targeting**: Por habitación, tipo, canal

### Impuestos
- **Tipo**: Porcentaje o monto fijo
- **Alcance**: Por noche, por reserva, por huésped
- **Canal**: Aplicación por canal específico
- **Prioridad**: Orden de aplicación

---

## Integraciones

### Mercado Pago
- **Preferencias**: Creación de preferencias de pago
- **Webhooks**: Confirmación automática de pagos
- **Estados**: Seguimiento de estados de pago
- **Configuración**: Por hotel o por empresa
- **Modo**: Prueba y producción

### Celery (Tareas Asíncronas)
- **Métricas**: Cálculo diario de métricas
- **Backfill**: Relleno de datos históricos
- **Reintentos**: Manejo de errores automático
- **Escalabilidad**: Procesamiento por lotes

### Docker
- **Contenedores**: Aplicación y base de datos
- **Compose**: Orquestación de servicios
- **Variables**: Configuración por ambiente
- **Volúmenes**: Persistencia de datos

### Render.com
- **Despliegue**: Automático desde Git
- **Variables**: Configuración de ambiente
- **Logs**: Monitoreo de aplicación
- **Escalabilidad**: Recursos ajustables

---

## Consideraciones Técnicas

### Base de Datos
- **Índices**: Optimización de consultas frecuentes
- **Constraints**: Integridad referencial
- **Transacciones**: Consistencia de datos
- **Migraciones**: Versionado de esquema

### Seguridad
- **JWT**: Autenticación stateless
- **CORS**: Configuración de dominios
- **Validación**: Sanitización de inputs
- **Permisos**: Control de acceso granular

### Performance
- **Select Related**: Reducción de consultas N+1
- **Caching**: Métricas calculadas
- **Paginación**: Límites en listados
- **Async**: Tareas en segundo plano

### Monitoreo
- **Logs**: Estructurados y categorizados
- **Métricas**: KPIs del negocio
- **Errores**: Tracking y alertas
- **Health Checks**: Estado de servicios

---

## Conclusión

AlojaSys es un sistema de gestión hotelera completo y robusto que cubre todas las necesidades operativas de un hotel moderno. Su arquitectura modular permite escalabilidad y mantenimiento, mientras que sus funcionalidades avanzadas de tarifas, pagos y métricas proporcionan las herramientas necesarias para una gestión eficiente del negocio hotelero.

El sistema está diseñado para ser flexible y configurable, permitiendo adaptarse a diferentes tipos de hoteles y políticas de negocio, mientras mantiene la simplicidad en su uso diario.

---

*Documento generado automáticamente basado en el análisis del código fuente del sistema AlojaSys.*
