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
   - [3.10 Módulo Notifications](#310-módulo-notifications)
   - [3.11 Módulo Cobros](#311-módulo-cobros-payment-collections)
   - [3.12 Módulo Conciliación Bancaria](#312-módulo-conciliación-bancaria)
   - [3.13 Módulo Facturación Electrónica](#313-módulo-facturación-electrónica)
   - [3.14 Módulo Comprobantes de Pagos](#314-módulo-comprobantes-de-pagos-payment-receipts)
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
- ✅ **Sistema de señas (pagos parciales) con integración AFIP**
- ✅ **Dos modos de facturación: solo recibos o facturación en seña**
- ✅ **Múltiples pagos por factura (señas + pago final)**
- ✅ Dashboard con métricas en tiempo real
- ✅ Gestión multi-hotel y multi-empresa
- ✅ Sistema de usuarios con perfiles y permisos
- ✅ Integración con sistemas de pago externos
- ✅ Sistema de notificaciones in-app en tiempo real
- ✅ Sistema de vouchers de crédito para reembolsos
- ✅ Aplicación de vouchers en nuevas reservas
- ✅ Gestión completa de reembolsos con múltiples métodos
- ✅ Conciliación bancaria automática con matching inteligente
- ✅ Generación automática de PDFs de recibos
- ✅ Envío automático de emails con recibos adjuntos
- ✅ Facturación electrónica argentina con integración AFIP
- ✅ Generación automática de facturas desde reservas
- ✅ PDFs fiscales con diseño oficial AFIP

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
- **Gestión de Reembolsos**: Interfaz completa para administrar devoluciones
- **Notificaciones**: Sistema in-app con polling automático

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
    applied_cancellation_policy = ForeignKey('payments.CancellationPolicy', null=True, blank=True)
    applied_cancellation_snapshot = JSONField(null=True, blank=True)
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

#### Payment (Extendido para Señas)
```python
class Payment(models.Model):
    reservation = ForeignKey(Reservation)
    date = DateField                     # Fecha del pago
    method = CharField(30)               # Método de pago
    amount = DecimalField                # Monto del pago
    status = CharField(20)               # Estado del pago
    
    # Campos específicos para POSTNET
    terminal_id = CharField(50)          # ID del terminal POSTNET
    batch_number = CharField(100)        # Número de batch del terminal
    notes = TextField                    # Notas adicionales
    
    # Campos para señas (pagos parciales) - NUEVO
    is_deposit = BooleanField            # Indica si es una seña/depósito
    metadata = JSONField                 # Metadatos adicionales del pago
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
    is_production = BooleanField(default=False)  # Modo de producción
    country_code = CharField(2)         # Código de país
    currency_code = CharField(3)        # Código de moneda
    webhook_secret = CharField(200)     # Secreto del webhook
    is_active = BooleanField            # Activa/Inactiva
    
    # Configuración de reembolsos
    refund_window_days = PositiveIntegerField(null=True, blank=True)  # Días límite para procesar reembolsos
    partial_refunds_allowed = BooleanField(default=True)              # Permitir reembolsos parciales
```

#### BankTransferPayment (Transferencias Bancarias)
```python
class BankTransferPayment(models.Model):
    reservation = ForeignKey(Reservation)    # Reserva asociada
    hotel = ForeignKey(Hotel)               # Hotel
    amount = DecimalField                   # Monto de la transferencia
    transfer_date = DateField               # Fecha de la transferencia
    cbu_iban = CharField(34)                # CBU/IBAN del destinatario
    bank_name = CharField(100)              # Nombre del banco
    
    # Archivos adjuntos
    receipt_file = FileField(upload_to='bank_transfers/')  # Archivo local
    receipt_filename = CharField(255)       # Nombre del archivo
    receipt_url = URLField(blank=True)      # URL del archivo (Cloudinary)
    storage_type = CharField(20)            # Tipo de almacenamiento
    
    # Estados de la transferencia
    status = CharField(20)                  # Estado actual
    created_at = DateTimeField              # Fecha de creación
    updated_at = DateTimeField              # Fecha de actualización
    
    # Datos de OCR y validación
    ocr_amount = DecimalField(null=True)    # Monto extraído por OCR
    ocr_cbu = CharField(34, null=True)      # CBU extraído por OCR
    ocr_confidence = FloatField(null=True)  # Confianza del OCR
    is_amount_valid = BooleanField          # Validación de monto
    is_cbu_valid = BooleanField             # Validación de CBU
    validation_notes = TextField()          # Notas de validación
    
    # Referencias y auditoría
    external_reference = CharField(120)     # Referencia externa
    payment_reference = CharField(120)      # Referencia del pago
    created_by = ForeignKey(User)           # Usuario que creó
    reviewed_by = ForeignKey(User, null=True) # Usuario que revisó
    reviewed_at = DateTimeField(null=True)  # Fecha de revisión
    notes = TextField(blank=True)           # Notas adicionales
    history = JSONField(default=list)       # Historial de cambios
```

#### Estados de Transferencia Bancaria
```python
class BankTransferStatus(models.TextChoices):
    UPLOADED = "uploaded", "Subido"
    PENDING_REVIEW = "pending_review", "Pendiente de Revisión"
    CONFIRMED = "confirmed", "Confirmado"
    REJECTED = "rejected", "Rechazado"
    PROCESSING = "processing", "Procesando"
```

#### HybridFileStorage (Almacenamiento Híbrido)
```python
class HybridFileStorage:
    """Servicio de almacenamiento híbrido (local/Cloudinary)"""
    
    @staticmethod
    def save_file(file, folder='bank_transfers/'):
        """Guarda archivo localmente o en Cloudinary según configuración"""
        if settings.USE_CLOUDINARY:
            # Subir a Cloudinary
            result = cloudinary.uploader.upload(file)
            return {
                'receipt_url': result['secure_url'],
                'receipt_filename': result['original_filename'],
                'storage_type': 'cloudinary'
            }
        else:
            # Guardar localmente
            return {
                'receipt_url': None,
                'receipt_filename': file.name,
                'storage_type': 'local'
            }
```
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
    
    # Configuración de reembolsos automáticos
    auto_refund_on_cancel = BooleanField(default=False)  # Procesar reembolso automáticamente al cancelar
    
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
    payment = ForeignKey('reservations.Payment', related_name="refunds", null=True, blank=True)
    amount = DecimalField(max_digits=12, decimal_places=2)
    reason = CharField(max_length=30, choices=RefundReason.choices, null=True, blank=True)
    status = CharField(max_length=20, choices=RefundStatus.choices)
    method = CharField(max_length=30, default='original_payment')
    refund_method = CharField(max_length=30)
    processing_days = PositiveIntegerField(default=7)
    external_reference = CharField(max_length=200, blank=True, null=True)
    notes = TextField(blank=True, null=True)
    processed_at = DateTimeField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User, on_delete=SET_NULL)
    processed_by = ForeignKey(User, on_delete=SET_NULL, related_name="processed_refunds")
```

#### RefundPolicy
```python
class RefundPolicy(models.Model):
    """
    Políticas de devolución configurables por hotel
    Define cómo se procesan las devoluciones de dinero
    """
    hotel = ForeignKey(Hotel)           # Hotel al que pertenece
    name = CharField(120)               # Nombre descriptivo
    is_active = BooleanField            # Activa/Inactiva
    is_default = BooleanField           # Política por defecto
    
    # Configuración de tiempos de devolución
    full_refund_time = PositiveIntegerField  # Tiempo para devolución completa
    full_refund_unit = CharField(10)         # Unidad de tiempo (horas/días/semanas)
    partial_refund_time = PositiveIntegerField  # Tiempo para devolución parcial
    partial_refund_unit = CharField(10)         # Unidad de tiempo
    partial_refund_percentage = DecimalField    # Porcentaje de devolución parcial
    no_refund_time = PositiveIntegerField    # Tiempo después del cual no hay devolución
    no_refund_unit = CharField(10)           # Unidad de tiempo
    
    # Configuración de métodos de devolución
    refund_method = CharField(30)            # Método de devolución
    refund_processing_days = PositiveIntegerField  # Días de procesamiento
    
    # Configuración de voucher
    voucher_expiry_days = PositiveIntegerField  # Días de vencimiento del voucher
    voucher_minimum_amount = DecimalField      # Monto mínimo para voucher
    
    # Mensajes personalizados
    full_refund_message = TextField          # Mensaje para devolución completa
    partial_refund_message = TextField       # Mensaje para devolución parcial
    no_refund_message = TextField            # Mensaje para sin devolución
    voucher_message = TextField              # Mensaje para voucher
    
    # Configuración avanzada
    apply_to_all_room_types = BooleanField   # Aplicar a todos los tipos
    room_types = JSONField                   # Tipos específicos
    apply_to_all_channels = BooleanField     # Aplicar a todos los canales
    channels = JSONField                     # Canales específicos
    apply_to_all_seasons = BooleanField      # Aplicar a todas las temporadas
    seasonal_rules = JSONField               # Reglas por temporada
```

#### Tipos de Método de Devolución
```python
class RefundMethod(models.TextChoices):
    CASH = "cash", "Efectivo"
    BANK_TRANSFER = "bank_transfer", "Transferencia Bancaria"
    CREDIT_CARD = "credit_card", "Tarjeta de Crédito"
    VOUCHER = "voucher", "Voucher"
    ORIGINAL_PAYMENT = "original_payment", "Método de Pago Original"
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

#### Auto-cancelación de Reservas por Depósito Vencido
```python
@shared_task
def auto_cancel_pending_deposits():
    """
    Cancela automáticamente reservas PENDING si venció fecha de depósito.
    Busca reservas PENDING con deposit_due_date < now y que no tengan pago.
    Cambia estado a CANCELLED y envía notificación por email al guest y staff.
    Registra reason: "auto-cancel - deposit expired".
    """
    # Lógica para:
    # 1. Buscar reservas PENDING con deposit_due_date < now
    # 2. Verificar que no tengan pagos
    # 3. Cambiar estado a CANCELLED
    # 4. Liberar habitación
    # 5. Enviar emails de notificación
    # 6. Registrar en ReservationChangeLog
```

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

#### Auto-cancelación de Reservas PENDING por Depósito Vencido
```python
@shared_task
def auto_cancel_pending_deposits():
    """
    Cancela automáticamente reservas PENDING si venció fecha de depósito.
    Busca reservas PENDING con deposit_due_date < now y que no tengan pago.
    Cambia estado a CANCELLED y envía notificación por email al guest y staff.
    Registra reason: "auto-cancel - deposit expired".
    """
    # Lógica para:
    # - Buscar reservas PENDING con depósito vencido
    # - Verificar que no tengan pagos
    # - Cambiar estado a CANCELLED
    # - Liberar habitaciones automáticamente
    # - Enviar emails de notificación
    # - Registrar logs con motivo específico
    # - Protección contra race conditions con locks
```

#### Auto No-Show de Reservas CONFIRMED (v2.0 - Mejorado)
```python
@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 5})
def auto_mark_no_show_daily(self):
    """
    Tarea Celery que marca automáticamente las reservas confirmadas vencidas como no-show
    y aplica penalidades automáticas según las políticas de cancelación
    Solo procesa hoteles que tienen auto_no_show_enabled=True
    """
    from apps.reservations.services.no_show_processor import NoShowProcessor
    from decimal import Decimal
    
    today = timezone.now().date()
    processed_count = 0
    no_show_count = 0
    penalties_applied = 0
    total_penalty_amount = Decimal('0.00')
    
    # Obtener hoteles que tienen auto no-show habilitado
    hotels_with_auto_no_show = Hotel.objects.filter(
        auto_no_show_enabled=True,
        is_active=True
    )
    
    for hotel in hotels_with_auto_no_show:
        # Buscar reservas confirmadas con check-in pasado para este hotel
        expired_reservations = Reservation.objects.filter(
            hotel=hotel,
            status='confirmed',
            check_in__lt=today
        )
        
        for reservation in expired_reservations:
            # Cambiar estado a no_show
            reservation.status = 'no_show'
            reservation.save(update_fields=['status'])
            
            # Registrar el cambio de estado
            ReservationStatusChange.objects.create(
                reservation=reservation,
                from_status='confirmed',
                to_status='no_show',
                changed_by=None,  # Sistema automático
                notes='Auto no-show: check-in date passed'
            )
            
            # Procesar penalidades automáticas
            penalty_result = NoShowProcessor.process_no_show_penalties(reservation)
            
            if penalty_result.get('success', False):
                penalty_amount = Decimal(str(penalty_result.get('penalty_amount', 0)))
                if penalty_amount > 0:
                    penalties_applied += 1
                    total_penalty_amount += penalty_amount
            
            no_show_count += 1
            processed_count += 1
    
    return f"Procesadas {processed_count} reservas, {no_show_count} marcadas como no-show, {penalties_applied} penalidades aplicadas (${total_penalty_amount})"
```

#### NoShowProcessor - Servicio de Penalidades NO_SHOW
```python
class NoShowProcessor:
    """
    Servicio para procesar reservas marcadas como NO_SHOW, aplicando penalidades
    y gestionando posibles reembolsos según las políticas configuradas.
    """
    
    @staticmethod
    def process_no_show_penalties(reservation: Reservation) -> Dict[str, Any]:
        """
        Aplica las penalidades por no-show a una reserva y gestiona el reembolso si aplica.
        """
        with transaction.atomic():
            # 1. Obtener la política de cancelación aplicada a la reserva
            cancellation_policy = reservation.applied_cancellation_policy
            
            # 2. Calcular reglas de cancelación para NO_SHOW
            cancellation_rules = cancellation_policy.get_cancellation_rules(reservation.check_in)
            
            # 3. Calcular monto total pagado
            total_paid = RefundProcessor._calculate_total_paid(reservation)
            
            # 4. Calcular penalidad según política de cancelación
            penalty_amount = RefundProcessor._calculate_penalty(
                reservation, 
                cancellation_rules, 
                total_paid
            )
            
            # 5. Procesar penalidad
            penalty_result = NoShowProcessor._process_no_show_penalty(
                reservation, penalty_amount, cancellation_rules
            )
            
            # 6. Calcular reembolso específico para NO_SHOW
            refund_policy = RefundPolicy.objects.filter(
                hotel=reservation.hotel,
                is_active=True
            ).first()
            
            refund_amount = NoShowProcessor._calculate_no_show_refund(
                total_paid, penalty_amount, refund_policy
            )
            
            # 7. Procesar reembolso si aplica
            refund_result = None
            if refund_amount > 0:
                refund_result = NoShowProcessor._process_no_show_refund(
                    reservation, refund_amount, refund_policy
                )
            
            # 8. Crear notificaciones detalladas
            NoShowProcessor._create_no_show_notification(
                reservation, penalty_amount, refund_amount
            )
            
            # 9. Registrar log de procesamiento
            NoShowProcessor._log_no_show_processing(
                reservation, cancellation_rules, penalty_result, refund_result
            )
            
            return {
                'success': True,
                'total_paid': float(total_paid),
                'penalty_amount': float(penalty_amount),
                'refund_amount': float(refund_amount),
                'penalty_processed': penalty_result is not None,
                'refund_processed': refund_result is not None,
                'cancellation_rules': cancellation_rules
            }
    
    @staticmethod
    def _calculate_no_show_refund(total_paid: Decimal, penalty_amount: Decimal, refund_policy: RefundPolicy) -> Decimal:
        """
        Calcula el reembolso específico para NO_SHOW
        Considera políticas especiales para NO_SHOW vs cancelaciones normales
        """
        # Verificar si hay política específica para NO_SHOW
        no_show_refund_percentage = getattr(refund_policy, 'no_show_refund_percentage', None)
        
        if no_show_refund_percentage is not None:
            # Hay política específica para NO_SHOW
            refund_amount = (total_paid * Decimal(no_show_refund_percentage)) / Decimal('100')
            return max(Decimal('0.00'), refund_amount - penalty_amount)
        
        # Verificar si la política permite reembolso para NO_SHOW
        allow_no_show_refund = getattr(refund_policy, 'allow_no_show_refund', False)
        
        if not allow_no_show_refund:
            return Decimal('0.00')
        
        # Aplicar política de devolución normal pero con penalidad completa
        if refund_policy.refund_method == 'voucher':
            # Para vouchers, se puede dar un porcentaje reducido
            voucher_percentage = getattr(refund_policy, 'no_show_voucher_percentage', 25)  # 25% por defecto
            refund_amount = (total_paid * Decimal(voucher_percentage)) / Decimal('100')
            return max(Decimal('0.00'), refund_amount - penalty_amount)
        
        # Para otros métodos, generalmente no hay reembolso
        return Decimal('0.00')
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
    "auto_cancel_pending_deposits_daily": {
        "task": "apps.reservations.tasks.auto_cancel_pending_deposits",
        "schedule": crontab(hour=8, minute=15),  # Diario a las 8:15 AM
    },
    "auto_mark_no_show_daily": {
        "task": "apps.reservations.tasks.auto_mark_no_show_daily",
        "schedule": crontab(hour=9, minute=0),  # Diario a las 9:00 AM
    },
    "process_pending_refunds_hourly": {
        "task": "apps.payments.tasks.process_pending_refunds",
        "schedule": crontab(minute=30),  # Cada hora a los 30 minutos
    },
    "retry_failed_refunds_daily": {
        "task": "apps.payments.tasks.retry_failed_refunds",
        "schedule": crontab(hour=10, minute=0),  # Diario a las 10:00 AM
    },
}
```

#### Cronograma de Tareas Automáticas
1. **8:00 AM** - `auto_cancel_expired_reservations`: Cancela por falta de pago del depósito
2. **8:15 AM** - `auto_cancel_pending_deposits`: Cancela PENDING por depósito vencido
3. **8:30 AM** - `auto_cancel_expired_pending_reservations`: Cancela PENDING vencidas
4. **9:00 AM** - `auto_mark_no_show_daily`: Marca CONFIRMED como no-show
5. **Cada hora (30 min)** - `process_pending_refunds`: Procesa reembolsos pendientes
6. **10:00 AM** - `retry_failed_refunds`: Reintenta reembolsos fallidos

#### Lógica de Cancelación Automática
- **Reservas PENDING por depósito vencido**: `PENDING` → `CANCELLED` (liberar habitación, enviar emails)
- **Reservas PENDING vencidas**: `PENDING` → `CANCELLED` (liberar habitación)
- **Reservas CONFIRMED vencidas**: `CONFIRMED` → `NO_SHOW` (mantener habitación ocupada)
- **Configuración por hotel**: Campo `auto_no_show_enabled` en modelo Hotel

#### Procesamiento Automático de Reembolsos Pendientes (v2.3)

##### process_pending_refunds
```python
@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 3})
def process_pending_refunds(self):
    """
    Tarea Celery que procesa reembolsos pendientes con backoff/retries.
    
    Características:
    - Recupera Refund con status PENDING
    - Intenta process_refund() para cada uno con backoff/retries
    - Si refund_window_days expiró, marca como FAILED y notifica al staff
    - Limita concurrencia e implementa idempotencia
    - Maneja errores de gateway con reintentos inteligentes
    """
```

##### Características Principales
- **Limitación de Concurrencia**: Locks de Redis para evitar ejecuciones simultáneas
- **Validación de Ventana de Tiempo**: Respeta `refund_window_days` configurado por pasarela
- **Reintentos con Backoff Exponencial**: 1s, 2s, 4s para fallos temporales
- **Manejo de Errores**: Categorización entre errores críticos y recuperables
- **Notificaciones al Staff**: Alertas cuando reembolsos expiran
- **Seguimiento de Estadísticas**: Conteo de procesados, completados, fallidos, expirados
- **Idempotencia Garantizada**: Múltiples ejecuciones no duplican procesamiento

##### retry_failed_refunds
```python
@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 3})
def retry_failed_refunds(self):
    """
    Tarea Celery que reintenta reembolsos fallidos que pueden ser recuperables.
    
    Características:
    - Busca reembolsos FAILED de las últimas 24 horas
    - Reintenta procesamiento con misma lógica de backoff
    - Permite recuperación de fallos temporales
    - Misma lógica de concurrencia e idempotencia
    """
```

##### Validación de Ventana de Tiempo
```python
def _is_refund_expired(refund: Refund) -> bool:
    """
    Verifica si un reembolso ha expirado según refund_window_days
    """
    gateway_config = PaymentGatewayConfig.resolve_for_hotel(refund.reservation.hotel)
    
    if not gateway_config or not gateway_config.refund_window_days:
        return False  # Sin límite de ventana
    
    window_days = gateway_config.refund_window_days
    limit_date = refund.created_at + timedelta(days=window_days)
    
    return timezone.now() > limit_date
```

##### Procesamiento con Reintentos
```python
def _process_single_refund_with_retries(processor: RefundProcessorV2, refund: Refund, task_instance) -> bool:
    """
    Procesa un reembolso individual con reintentos y backoff exponencial
    """
    max_retries = 3
    base_delay = 1  # segundo base
    
    for attempt in range(max_retries):
        try:
            success = processor.process_refund(refund, max_retries=1)
            
            if success:
                return True
            else:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    task_instance.retry(countdown=delay)
        except Exception as e:
            if attempt == max_retries - 1:
                refund.mark_as_failed(f"Falló después de {max_retries} intentos: {str(e)}")
                return False
            else:
                delay = base_delay * (2 ** attempt)
                task_instance.retry(countdown=delay)
    
    return False
```

##### Notificaciones al Staff
```python
def _notify_staff_refund_expired(refund: Refund):
    """
    Notifica al staff sobre un reembolso expirado
    """
    NotificationService.create(
        notification_type='refund_failed',
        title=f"⚠️ Reembolso Expirado - ${refund.amount}",
        message=f"El reembolso #{refund.id} para la reserva RES-{refund.reservation.id} ha expirado. "
               f"Ventana de tiempo excedida. Requiere procesamiento manual.",
        hotel_id=refund.reservation.hotel.id,
        reservation_id=refund.reservation.id,
        metadata={
            'refund_id': refund.id,
            'amount': float(refund.amount),
            'reason': 'expired',
            'expired_at': timezone.now().isoformat(),
            'requires_manual_processing': True
        }
    )
```

##### Seguimiento de Estadísticas
```python
stats = {
    'processed': 0,           # Total de reembolsos procesados
    'completed': 0,           # Reembolsos completados exitosamente
    'failed': 0,              # Reembolsos que fallaron después de reintentos
    'expired': 0,             # Reembolsos que expiraron por ventana de tiempo
    'retry_errors': 0,        # Errores durante reintentos
    'total_amount_processed': Decimal('0.00')  # Monto total procesado
}
```

##### Configuración de Pasarelas
```python
class PaymentGatewayConfig(models.Model):
    # ... campos existentes ...
    
    # Configuración de reembolsos
    refund_window_days = PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Días límite para procesar reembolsos (null = sin límite)"
    )
    partial_refunds_allowed = BooleanField(
        default=True, 
        help_text="Permitir reembolsos parciales"
    )
```

##### Tests y Validación
- **16 tests implementados** cubriendo todos los escenarios
- **Tests de concurrencia** con locks de Redis
- **Tests de validación** de ventana de tiempo
- **Tests de reintentos** con backoff exponencial
- **Tests de notificaciones** al staff
- **Tests de estadísticas** y seguimiento
- **Tests de manejo de errores** de gateway
- **Tests de idempotencia** garantizada

##### Beneficios Técnicos
- **Escalabilidad**: Procesamiento por lotes con límites de concurrencia
- **Confiabilidad**: Reintentos inteligentes para fallos temporales
- **Trazabilidad**: Logs detallados y estadísticas completas
- **Flexibilidad**: Configuración por pasarela y hotel
- **Mantenibilidad**: Código modular y bien documentado
- **Performance**: Procesamiento eficiente con índices optimizados

### Validaciones de Configuración de Pasarelas

#### Validaciones Implementadas
```python
def clean(self):
    from django.core.exceptions import ValidationError
    
    # Validar que no se mezclen keys de producción con is_test=True
    if self.is_production and self.is_test:
        raise ValidationError({
            'is_production': 'No se puede marcar como producción si is_test=True',
            'is_test': 'No se puede usar is_test=True en configuración de producción'
        })
    
    # Validar que las keys de producción no sean de test
    if self.is_production:
        if 'TEST' in self.access_token.upper() or len(self.access_token) < 20:
            raise ValidationError({
                'access_token': 'El access_token parece ser de test. En producción debe usar keys reales.'
            })
        
        if 'TEST' in self.public_key.upper() or len(self.public_key) < 20:
            raise ValidationError({
                'public_key': 'El public_key parece ser de test. En producción debe usar keys reales.'
            })
    
    # Validar que las keys de test no sean de producción
    if self.is_test and not self.is_production:
        if 'TEST' not in self.access_token.upper() and len(self.access_token) > 20:
            raise ValidationError({
                'access_token': 'El access_token parece ser de producción. En test debe usar keys de prueba.'
            })
        
        if 'TEST' not in self.public_key.upper() and len(self.public_key) > 20:
            raise ValidationError({
                'public_key': 'El public_key parece ser de producción. En test debe usar keys de prueba.'
            })
```

### Endpoint de Rotación de Tokens

#### Rotar Tokens de Pasarela
```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rotate_payment_tokens(request):
    """
    Endpoint para rotar access_token y public_key de una configuración de pago
    """
    # Parámetros requeridos:
    # - config_id: ID de la configuración a actualizar
    # - new_access_token: Nuevo access token
    # - new_public_key: Nueva public key
    
    # Respuesta exitosa:
    # {
    #     "success": true,
    #     "message": "Tokens rotados exitosamente",
    #     "config_id": 1,
    #     "rotated_at": "2024-01-15T10:30:00Z"
    # }
    
    # Respuesta de error:
    # {
    #     "success": false,
    #     "error": "Error de validación: [detalles]"
    # }
```

#### Características del Endpoint
- **Autenticación requerida**: Solo usuarios autenticados pueden rotar tokens
- **Validación automática**: Aplica las mismas validaciones que el modelo
- **Rollback automático**: Si la validación falla, se revierten los cambios
- **Logging de auditoría**: Registra todas las rotaciones para seguimiento
- **Transacciones atómicas**: Garantiza consistencia en la base de datos

### APIs Principales
- `GET /api/payments/policies/` - Listar políticas de pago
- `POST /api/payments/policies/` - Crear política de pago
- `GET /api/payments/methods/` - Listar métodos de pago
- `POST /api/payments/process_card/` - Procesar pago con tarjeta
- `POST /api/payments/webhook/` - **Webhook de Mercado Pago (Mejorado)**
- `GET /api/payments/reservation/{id}/payments/` - Pagos de una reserva
- `POST /api/payments/rotate-tokens/` - **Rotar tokens de pasarela**

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
- `POST /api/reservations/auto_cancel_expired/` - Ejecutar auto-cancelación manual
- `GET /api/reservations/pending_expiration_stats/` - Estadísticas de reservas pendientes

### APIs de Políticas de Devolución
- `GET /api/payments/refund-policies/` - Listar políticas de devolución
- `POST /api/payments/refund-policies/` - Crear política de devolución
- `GET /api/payments/refund-policies/{id}/` - Obtener política específica
- `PUT /api/payments/refund-policies/{id}/` - Actualizar política
- `DELETE /api/payments/refund-policies/{id}/` - Eliminar política
- `GET /api/payments/refund-policies/for_hotel/` - Política activa por hotel
- `POST /api/payments/refund-policies/set_default/` - Establecer como predeterminada

### APIs de Reembolsos
- `GET /api/payments/refunds/` - Listar reembolsos con filtros
- `POST /api/payments/refunds/` - Crear reembolso manual
- `GET /api/payments/refunds/{id}/` - Obtener reembolso específico
- `PUT /api/payments/refunds/{id}/` - Actualizar reembolso
- `PATCH /api/payments/refunds/{id}/` - Actualizar estado del reembolso
- `GET /api/payments/refunds/for_reservation/` - Reembolsos por reserva
- `GET /api/payments/refunds/stats/` - Estadísticas de reembolsos

---

## 3.4.1 Sistema de Webhooks Mejorado (v2.0)

**Propósito**: Procesamiento seguro y robusto de notificaciones de pagos de Mercado Pago con verificación HMAC, idempotencia y post-procesamiento asíncrono.

### Características Principales

#### Seguridad Avanzada
- ✅ **Verificación HMAC obligatoria** para todas las notificaciones
- ✅ **Validación de firma** usando webhook_secret configurado
- ✅ **Rechazo automático** de notificaciones no verificadas
- ✅ **Logging de seguridad** detallado para auditoría

#### Sistema de Idempotencia
- ✅ **Prevención de duplicados** mediante cache Redis
- ✅ **Verificación por notification_id** y external_reference
- ✅ **Manejo elegante** de notificaciones ya procesadas
- ✅ **Fallback a cache dummy** cuando Redis no está disponible

#### Procesamiento Atómico
- ✅ **Actualización atómica** de PaymentIntent
- ✅ **Transacciones de base de datos** para consistencia
- ✅ **Rollback automático** en caso de errores
- ✅ **Validación de estados** antes de procesar

#### Post-procesamiento Asíncrono
- ✅ **Tareas Celery** para procesamiento posterior
- ✅ **Notificaciones automáticas** a usuarios y staff
- ✅ **Auditoría completa** de eventos de webhook
- ✅ **Procesamiento de eventos** internos del sistema

### Arquitectura del Sistema

#### WebhookSecurityService
```python
class WebhookSecurityService:
    @staticmethod
    def verify_webhook_signature(request, webhook_secret: str) -> bool:
        """Verifica la firma HMAC del webhook"""
    
    @staticmethod
    def is_notification_processed(notification_id: str, external_reference: str = None) -> bool:
        """Verifica si una notificación ya fue procesada"""
    
    @staticmethod
    def mark_notification_processed(notification_id: str, external_reference: str = None, ttl: int = 86400) -> None:
        """Marca una notificación como procesada"""
    
    @staticmethod
    def extract_webhook_data(request) -> Dict[str, Any]:
        """Extrae datos del webhook de forma segura"""
    
    @staticmethod
    def log_webhook_security_event(event_type: str, notification_id: str = None, 
                                 external_reference: str = None, details: Dict[str, Any] = None):
        """Registra eventos de seguridad para auditoría"""
```

#### PaymentProcessorService
```python
class PaymentProcessorService:
    @staticmethod
    @transaction.atomic
    def process_webhook_payment(payment_data: Dict[str, Any], 
                              webhook_secret: str = None,
                              notification_id: str = None) -> Dict[str, Any]:
        """Procesa un pago desde webhook de forma atómica"""
```

#### Tareas de Celery
```python
@shared_task(bind=True, autoretry_for=(ProgrammingError, OperationalError), 
             retry_backoff=5, retry_jitter=True, retry_kwargs={"max_retries": 3})
def process_webhook_post_processing(self, payment_intent_id: int, webhook_data: Dict[str, Any], 
                                   notification_id: str = None, external_reference: str = None):
    """Tarea asíncrona para post-procesamiento de webhooks"""
```

### Flujo de Procesamiento

#### 1. Recepción del Webhook
```python
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook(request):
    # 1. Extraer datos del webhook
    payment_data = WebhookSecurityService.extract_webhook_data(request)
    
    # 2. Verificar HMAC si está configurado
    if webhook_secret:
        if not WebhookSecurityService.verify_webhook_signature(request, webhook_secret):
            return Response({"success": False, "error": "Firma HMAC inválida"}, status=400)
    
    # 3. Verificar idempotencia
    if WebhookSecurityService.is_notification_processed(notification_id, external_reference):
        return Response({"success": True, "processed": False, "message": "Notificación ya procesada"})
```

#### 2. Procesamiento Atómico
```python
    # 4. Procesar pago de forma atómica
    result = PaymentProcessorService.process_webhook_payment(
        payment_data=payment_data,
        webhook_secret=webhook_secret,
        notification_id=notification_id
    )
    
    # 5. Marcar como procesado si fue exitoso
    if result.get('success') and result.get('processed', False):
        WebhookSecurityService.mark_notification_processed(notification_id, external_reference)
```

#### 3. Post-procesamiento Asíncrono
```python
    # 6. Encolar tarea de post-procesamiento
    if result.get('success') and result.get('processed', False):
        process_webhook_post_processing.delay(
            payment_intent_id=result.get('payment_intent_id'),
            webhook_data=payment_data,
            notification_id=notification_id,
            external_reference=external_reference
        )
```

### Respuestas HTTP Estandarizadas

#### Respuesta Exitosa
```json
{
    "success": true,
    "processed": true,
    "payment_intent_id": 123,
    "status": "approved",
    "message": "Pago procesado exitosamente",
    "post_processing_queued": true
}
```

#### Respuesta de Duplicado
```json
{
    "success": true,
    "processed": false,
    "message": "Notificación ya procesada",
    "code": "DUPLICATE_NOTIFICATION"
}
```

#### Respuesta de Error HMAC
```json
{
    "success": false,
    "error": "Firma HMAC inválida",
    "code": "HMAC_VERIFICATION_FAILED"
}
```

#### Respuesta de Error de Procesamiento
```json
{
    "success": false,
    "error": "Error procesando pago: [detalles]",
    "code": "PAYMENT_PROCESSING_ERROR"
}
```

### Configuración de Seguridad

#### Variables de Entorno
```bash
# Configuración de webhook
MERCADO_PAGO_WEBHOOK_SECRET=tu_webhook_secret_aqui
MERCADO_PAGO_ACCESS_TOKEN=tu_access_token_aqui

# Configuración de Redis para idempotencia
REDIS_URL=redis://localhost:6379/0
```

#### Configuración por Hotel
```python
class PaymentGatewayConfig(models.Model):
    # ... campos existentes ...
    webhook_secret = CharField(200)  # Secreto para verificación HMAC
    is_production = BooleanField(default=False)  # Modo de producción
```

### Monitoreo y Logging

#### Eventos de Seguridad
- **HMAC_VERIFICATION_SUCCESS**: Firma verificada correctamente
- **HMAC_VERIFICATION_FAILED**: Firma inválida rechazada
- **DUPLICATE_NOTIFICATION**: Notificación duplicada detectada
- **WEBHOOK_PROCESSED**: Webhook procesado exitosamente

#### Métricas de Performance
- **Tiempo de procesamiento**: Latencia del webhook
- **Tasa de éxito**: % de webhooks procesados correctamente
- **Tasa de duplicados**: % de notificaciones duplicadas
- **Tasa de errores HMAC**: % de webhooks con firma inválida

### Testing y Validación

#### Tests Implementados
- **Test de verificación HMAC**: Validación de firmas válidas e inválidas
- **Test de idempotencia**: Prevención de procesamiento duplicado
- **Test de extracción de datos**: Parsing seguro de datos del webhook
- **Test de respuestas HTTP**: Validación de respuestas estandarizadas
- **Test de tareas Celery**: Verificación de post-procesamiento asíncrono

#### Test Manual
```python
# Ejecutar tests manuales
python test_webhook_manual.py

# Ejecutar tests de Django
python manage.py test test_webhook_simple --settings=test_settings -v 2
```

### Beneficios Técnicos

#### Seguridad
- **Verificación HMAC obligatoria** previene ataques de falsificación
- **Idempotencia garantizada** evita procesamiento duplicado
- **Logging completo** facilita auditoría y debugging

#### Escalabilidad
- **Post-procesamiento asíncrono** no bloquea el webhook
- **Cache Redis** para idempotencia de alto rendimiento
- **Tareas Celery** para procesamiento distribuido

#### Mantenibilidad
- **Código modular** con responsabilidades separadas
- **Tests completos** para validación continua
- **Logging estructurado** para debugging eficiente

#### Confiabilidad
- **Transacciones atómicas** garantizan consistencia
- **Manejo de errores robusto** con reintentos automáticos
- **Fallbacks elegantes** cuando servicios externos fallan

### Sistema de Vouchers de Crédito

#### RefundVoucher - Entidad Principal
```python
class RefundVoucher(models.Model):
    """
    Entidad para manejar vouchers de crédito generados por reembolsos.
    Permite reutilizar créditos en futuras reservas sin riesgo de inconsistencias.
    """
    code = CharField(max_length=20, unique=True)  # Código único del voucher
    amount = DecimalField(max_digits=12, decimal_places=2)  # Monto del voucher
    expiry_date = DateField()  # Fecha de vencimiento
    status = CharField(max_length=20, choices=RefundVoucherStatus.choices)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User, on_delete=SET_NULL)
    used_at = DateTimeField(null=True, blank=True)
    used_by = ForeignKey(User, on_delete=SET_NULL, related_name="used_vouchers")
    used_in_reservation = ForeignKey(Reservation, on_delete=SET_NULL, null=True, blank=True)
    refund = ForeignKey(Refund, on_delete=CASCADE, related_name="generated_voucher")
```

#### Estados de Voucher
```python
class RefundVoucherStatus(models.TextChoices):
    ACTIVE = "active", "Activo"
    USED = "used", "Usado"
    EXPIRED = "expired", "Expirado"
    CANCELLED = "cancelled", "Cancelado"
```

#### Métodos del Modelo RefundVoucher
```python
def generate_unique_code(self):
    """Genera un código único para el voucher (formato: VCH-YYYY-NNNNN)"""

def is_expired(self):
    """Verifica si el voucher ha expirado comparando con la fecha actual"""

def can_be_used(self):
    """Verifica si el voucher puede ser usado (activo y no expirado)"""

def use_voucher(self, user, reservation):
    """Marca el voucher como usado y lo asocia a una reserva"""

def cancel_voucher(self, user):
    """Cancela el voucher y lo marca como no disponible"""
```

#### Integración con Reservas
```python
# Campo agregado al modelo Reservation
class Reservation(models.Model):
    # ... campos existentes ...
    voucher_code = CharField(max_length=20, blank=True, null=True)  # Código de voucher aplicado
```

#### Serializers para Vouchers
```python
class RefundVoucherSerializer(serializers.ModelSerializer):
    """Serializer para mostrar vouchers"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = RefundVoucher
        fields = ['id', 'code', 'amount', 'expiry_date', 'status', 'status_display', 
                 'created_at', 'used_at', 'used_in_reservation']

class RefundVoucherCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear vouchers"""
    class Meta:
        model = RefundVoucher
        fields = ['id', 'code', 'amount', 'expiry_date', 'status']
        read_only_fields = ['id', 'code', 'status']

class RefundVoucherUseSerializer(serializers.Serializer):
    """Serializer para usar vouchers en reservas"""
    voucher_code = serializers.CharField(max_length=20)
    reservation_id = serializers.IntegerField()
```

#### ViewSet para Vouchers
```python
class RefundVoucherViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de vouchers"""
    queryset = RefundVoucher.objects.all()
    serializer_class = RefundVoucherSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundVoucherCreateSerializer
        return RefundVoucherSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear voucher con código único automático"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Generar código único
        voucher = serializer.save()
        voucher.code = voucher.generate_unique_code()
        voucher.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

#### Integración con Motor de Tarifas
```python
# En backend/apps/rates/services/engine.py
def compute_rate_for_date(room, guests, on_date, channel=None, promotion_code=None, voucher_code=None):
    """
    Calcula el precio para una habitación en una fecha específica
    Incluye aplicación de vouchers como descuento fijo
    """
    # ... lógica existente para tarifas y promociones ...
    
    # Aplicar voucher si se proporciona
    voucher_discount = Decimal('0.00')
    applied_vouchers = []
    applied_vouchers_detail = []
    
    if voucher_code:
        try:
            voucher = RefundVoucher.objects.get(
                code=voucher_code,
                status='active',
                expiry_date__gte=on_date
            )
            if voucher.can_be_used():
                voucher_discount = min(voucher.amount, total_night)
                applied_vouchers.append(voucher.id)
                applied_vouchers_detail.append({
                    'id': voucher.id,
                    'code': voucher.code,
                    'amount': float(voucher.amount),
                    'discount_applied': float(voucher_discount)
                })
        except RefundVoucher.DoesNotExist:
            pass
    
    # Calcular base imponible después de promociones y vouchers
    taxable_base = max(Decimal('0.00'), total_night - promotion_discount - voucher_discount)
    
    return {
        'base_rate': float(base_rate),
        'extra_guest_fee': float(extra_guest_fee),
        'total_night': float(total_night),
        'tax': float(tax),
        'taxable_base': float(taxable_base),
        'promotion_discount': float(promotion_discount),
        'voucher_discount': float(voucher_discount),
        'applied_vouchers': applied_vouchers,
        'applied_vouchers_detail': applied_vouchers_detail
    }
```

#### Procesamiento de Reembolsos con Vouchers
```python
# En backend/apps/payments/services/refund_processor.py
def _create_voucher_refund(reservation, refund_amount, refund_rules):
    """Crea un reembolso en forma de voucher de crédito"""
    # Calcular fecha de vencimiento (por defecto 6 meses)
    voucher_expiry_days = refund_rules.get('voucher_expiry_days', 180)
    expiry_date = timezone.now().date() + timedelta(days=voucher_expiry_days)
    
    # Crear voucher
    voucher = RefundVoucher.objects.create(
        amount=refund_amount,
        expiry_date=expiry_date,
        status=RefundVoucherStatus.ACTIVE,
        created_by=None,  # Sistema automático
        refund=refund
    )
    
    # Generar código único
    voucher.code = voucher.generate_unique_code()
    voucher.save()
    
    return voucher

def process_refund(reservation: Reservation, cancellation_policy: CancellationPolicy = None, 
                  cancellation_reason: str = None, refund_method: str = 'money') -> Dict[str, Any]:
    """
    Procesa reembolso con opción de método (dinero o voucher)
    """
    # ... lógica existente ...
    
    if refund_method == 'voucher':
        # Crear voucher en lugar de reembolso en dinero
        voucher = _create_voucher_refund(reservation, refund_amount, refund_rules)
        
        return {
            'success': True,
            'refund_amount': float(refund_amount),
            'refund_method': 'voucher',
            'generated_voucher': {
                'id': voucher.id,
                'code': voucher.code,
                'amount': float(voucher.amount),
                'expiry_date': voucher.expiry_date.isoformat(),
                'status': voucher.status
            }
        }
    
    # ... resto de la lógica para reembolsos en dinero ...
```

### APIs de Vouchers
- `GET /api/payments/refund-vouchers/` - Listar vouchers con filtros
- `POST /api/payments/refund-vouchers/` - Crear voucher manual
- `GET /api/payments/refund-vouchers/{id}/` - Obtener voucher específico
- `PUT /api/payments/refund-vouchers/{id}/` - Actualizar voucher
- `PATCH /api/payments/refund-vouchers/{id}/` - Actualizar estado del voucher
- `DELETE /api/payments/refund-vouchers/{id}/` - Cancelar voucher
- `POST /api/payments/refund-vouchers/use/` - Usar voucher en reserva

### Mejoras del Modelo Refund (v2.0)

#### Campos Actualizados
- **`payment`**: Ahora es nullable para permitir reembolsos sin pago original
- **`amount`**: Aumentado a max_digits=12 para manejar montos más grandes
- **`reason`**: Ahora es nullable para mayor flexibilidad
- **`method`**: Nuevo campo para método de reembolso (original_payment, voucher, etc.)
- **`processed_by`**: Nuevo campo para rastrear quién procesó el reembolso

#### Campos de Auditoría en Reservation
- **`applied_cancellation_policy`**: FK a la política de cancelación vigente al crear la reserva
- **`applied_cancellation_snapshot`**: JSONField con snapshot de la política para auditoría

#### Migraciones Aplicadas
- `payments.0009_refund_method_refund_processed_by_and_more.py`
- `reservations.0011_reservation_applied_cancellation_snapshot.py`

#### Beneficios de las Mejoras
- **Trazabilidad completa**: Registro de quién procesó cada reembolso
- **Flexibilidad financiera**: Reembolsos sin pago original asociado
- **Auditoría histórica**: Snapshot de políticas aplicadas en reservas
- **Escalabilidad**: Soporte para montos más grandes
- **Consistencia**: Políticas históricas garantizadas en cancelaciones

### Control Granular de Reembolsos Automáticos (v2.1)

#### Nuevos Campos de Control

##### CancellationPolicy.auto_refund_on_cancel
```python
auto_refund_on_cancel = BooleanField(default=False, help_text="Procesar reembolso automáticamente al cancelar")
```
- **Propósito**: Controla si la cancelación dispara reembolso automático
- **Default**: False (reembolso manual por defecto)
- **Uso**: Permite configurar políticas que procesen reembolsos automáticamente

##### PaymentGatewayConfig.refund_window_days
```python
refund_window_days = PositiveIntegerField(null=True, blank=True, help_text="Días límite para procesar reembolsos (null = sin límite)")
```
- **Propósito**: Establece límite temporal para procesar reembolsos
- **Default**: None (sin límite)
- **Validación**: Debe ser >= 0 si no es null

##### PaymentGatewayConfig.partial_refunds_allowed
```python
partial_refunds_allowed = BooleanField(default=True, help_text="Permitir reembolsos parciales")
```
- **Propósito**: Controla si la pasarela permite reembolsos parciales
- **Default**: True (permitir reembolsos parciales)
- **Uso**: Restricción a nivel de pasarela de pago

### Servicio Avanzado de Procesamiento de Reembolsos (v2.2)

#### RefundProcessorV2
```python
class RefundProcessorV2:
    """
    Servicio avanzado para procesar reembolsos, con soporte para múltiples pasarelas
    a través de adaptadores, validación de políticas y lógica de reintentos.
    """
```

#### Características Principales
- **Adaptadores de Pasarelas**: Soporte para múltiples proveedores de pago
- **Validación de Ventana**: Respeta límites de tiempo configurados por pasarela
- **Lógica de Reintentos**: Backoff exponencial para fallos temporales
- **Logging Detallado**: Registro completo de eventos y errores
- **Transacciones Atómicas**: Consistencia garantizada en base de datos

#### Métodos Principales

##### process_refund()
```python
def process_refund(self, refund: Refund, max_retries: int = 3, initial_delay: int = 1) -> bool:
    """
    Procesa un reembolso, incluyendo validaciones y lógica de reintentos.
    """
    # Lógica para:
    # - Validar ventana de reembolso
    # - Obtener adaptador de pasarela
    # - Procesar reembolso con reintentos
    # - Actualizar estado y registrar logs
```

##### _validate_refund_window()
```python
def _validate_refund_window(self, refund: Refund) -> bool:
    """
    Valida si el reembolso está dentro de la ventana de días permitida
    por la configuración de la pasarela de pago del hotel.
    """
    # Lógica para:
    # - Obtener configuración de pasarela
    # - Calcular fecha límite
    # - Verificar si está dentro de la ventana
```

##### _get_payment_adapter()
```python
def _get_payment_adapter(self, provider_name: str, hotel_id: int = None) -> Optional[PaymentGatewayAdapter]:
    """
    Obtiene el adaptador de pasarela de pago para un proveedor dado.
    """
    # Lógica para:
    # - Buscar adaptador por nombre de proveedor
    # - Verificar disponibilidad
    # - Retornar instancia configurada
```

### Adaptadores de Pasarelas de Pago

#### PaymentGatewayAdapter (Clase Base)
```python
class PaymentGatewayAdapter(ABC):
    """
    Interfaz abstracta para adaptadores de pasarelas de pago.
    Define los métodos que cualquier adaptador de pasarela debe implementar
    para procesar reembolsos.
    """
```

#### Métodos Requeridos
- **`provider_name`**: Nombre del proveedor (ej. 'MercadoPago')
- **`is_available()`**: Verifica si el adaptador está configurado
- **`refund()`**: Procesa un reembolso
- **`get_refund_status()`**: Obtiene el estado de un reembolso

#### RefundResult (Clase de Datos)
```python
@dataclass
class RefundResult:
    """
    Representa el resultado de una operación de reembolso.
    """
    success: bool
    external_id: Optional[str] = None
    error: Optional[str] = None
```

### Adaptador MercadoPago

#### MercadoPagoAdapter
```python
class MercadoPagoAdapter(PaymentGatewayAdapter):
    """
    Adaptador para la pasarela de pago MercadoPago.
    Implementa la lógica para interactuar con la API de MercadoPago para reembolsos.
    En modo de prueba, simula respuestas.
    """
```

#### Características
- **Modo de Prueba**: Simulación completa para desarrollo y testing
- **Modo de Producción**: Integración real con API de MercadoPago
- **Fallos Simulados**: Para testing de escenarios de error
- **Retrasos Simulados**: Para testing de timeouts
- **Logging Detallado**: Registro de todas las operaciones
- **Idempotencia**: Claves únicas para evitar llamadas duplicadas
- **Trace ID**: Rastreo completo de peticiones salientes
- **Simulación de Errores E2E**: Para testing de escenarios específicos

#### Configuración
```python
# Modo de prueba
adapter = MercadoPagoAdapter(is_test_mode=True)

# Modo de prueba con fallos simulados
adapter = MercadoPagoAdapter(
    is_test_mode=True,
    mock_failure="connection_error",
    mock_delay=2
)

# Modo de producción
adapter = MercadoPagoAdapter(
    config=gateway_config,
    is_test_mode=False
)
```

#### Tipos de Fallos Simulados
- **`connection_error`**: Error de conectividad con el banco
- **`payment_not_found`**: Pago no encontrado
- **`insufficient_funds`**: Fondos insuficientes
- **`already_refunded`**: Reembolso ya procesado
- **`partial_refund_not_allowed`**: Reembolso parcial no permitido
- **`refund_not_found`**: Reembolso no encontrado

#### Mejoras Implementadas (v2.1)

##### Idempotencia en Llamadas de Captura/Refund
```python
def _generate_idempotency_key(self, operation: str, payment_id: str) -> str:
    """
    Genera una clave de idempotencia única para una operación
    Formato: {operation}_{payment_id}_{timestamp}_{unique_id}
    """
    timestamp = int(datetime.now().timestamp())
    unique_id = str(uuid.uuid4())[:8]
    return f"{operation}_{payment_id}_{timestamp}_{unique_id}"
```

##### Simulación de Errores para Tests E2E
```python
# Configuración para simular errores específicos
adapter = MercadoPagoAdapter(
    config=config,
    mock_mode=True,
    simulate_errors={
        'connection_error': True,
        'partial_refund_not_allowed': True
    }
)
```

##### Logging de Trace ID
```python
def _generate_trace_id(self) -> str:
    """
    Genera un trace ID único para rastrear peticiones
    Formato: trace_{timestamp}_{random_id}
    """
    timestamp = int(datetime.now().timestamp())
    random_id = str(uuid.uuid4())[:8]
    return f"trace_{timestamp}_{random_id}"
```

##### Headers HTTP Mejorados
```python
headers = {
    'Authorization': f'Bearer {self.access_token}',
    'Content-Type': 'application/json',
    'X-Idempotency-Key': idempotency_key,
    'X-Trace-ID': trace_id,
    'X-Request-ID': str(uuid.uuid4())
}
```

### Integración con RefundProcessor Original

#### RefundProcessorV2Integration
```python
class RefundProcessorV2Integration:
    """
    Integración del RefundProcessor original con el nuevo servicio v2
    """
    
    @staticmethod
    def process_refund_with_gateway(refund: Refund) -> bool:
        """
        Procesa un reembolso usando el nuevo servicio v2 con adaptadores de pasarelas
        """
    
    @staticmethod
    def process_refund_with_retries(refund: Refund, max_retries: int = 3) -> bool:
        """
        Procesa un reembolso con reintentos usando el nuevo servicio v2
        """
```

### APIs de Configuración de Pasarelas

#### PaymentGatewayConfigSerializer
```python
class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para configuraciones de gateway de pago
    """
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    enterprise_name = serializers.CharField(source="enterprise.name", read_only=True)
    
    class Meta:
        model = PaymentGatewayConfig
        fields = [
            "id", "provider", "enterprise", "enterprise_name", "hotel", "hotel_name",
            "public_key", "access_token", "integrator_id", "is_test", "country_code",
            "currency_code", "webhook_secret", "is_active", "refund_window_days",
            "partial_refunds_allowed", "created_at", "updated_at"
        ]
```

#### Validaciones
- **`refund_window_days >= 0`**: Si no es null
- **Hotel o Enterprise requerido**: Al menos uno debe estar presente
- **Campos de solo lectura**: `created_at`, `updated_at`

### Tests y Validación

#### Cobertura de Tests
- **16 tests implementados** para campos de control
- **Tests de adaptadores**: Simulación de éxito y fallo
- **Tests de validación**: Ventana de reembolso y configuraciones
- **Tests de integración**: Flujo completo de procesamiento
- **Tests de reintentos**: Lógica de backoff exponencial
- **Tests de idempotencia**: Verificación de claves únicas
- **Tests de trace ID**: Validación de rastreo de peticiones
- **Tests de simulación de errores**: Escenarios E2E específicos

#### Ejemplo de Uso
```python
# Crear reembolso
refund = Refund.objects.create(
    reservation=reservation,
    amount=Decimal('100.00'),
    status=RefundStatus.PENDING,
    method='MercadoPago'
)

# Procesar con servicio v2
success = refund_processor_v2.process_refund(refund)

# Verificar resultado
if success:
    print(f"Reembolso {refund.id} procesado exitosamente")
    print(f"External ID: {refund.external_reference}")
else:
    print(f"Reembolso {refund.id} falló")
    print(f"Error: {refund.notes}")
```

### Beneficios Técnicos

#### Escalabilidad
- **Múltiples Pasarelas**: Soporte para diferentes proveedores
- **Configuración por Hotel**: Adaptadores específicos por propiedad
- **Reintentos Inteligentes**: Manejo robusto de fallos temporales

#### Mantenibilidad
- **Interfaz Unificada**: Mismo código para diferentes pasarelas
- **Fácil Extensión**: Agregar nuevas pasarelas es simple
- **Testing Aislado**: Cada adaptador se puede probar independientemente

#### Confiabilidad
- **Transacciones Atómicas**: Consistencia garantizada
- **Logging Completo**: Trazabilidad total de operaciones
- **Validaciones Robustas**: Prevención de errores de configuración

#### Flexibilidad
- **Modo de Prueba**: Desarrollo sin APIs reales
- **Configuración Dinámica**: Adaptadores por hotel
- **Fallos Simulados**: Testing de escenarios de error

#### Validaciones Implementadas

##### PaymentGatewayConfig.clean()
```python
def clean(self):
    from django.core.exceptions import ValidationError
    
    # Validar refund_window_days
    if self.refund_window_days is not None and self.refund_window_days < 0:
        raise ValidationError({'refund_window_days': 'El valor debe ser mayor o igual a 0'})
```

#### Serializers Actualizados

##### CancellationPolicySerializer
- Campo `auto_refund_on_cancel` incluido en fields
- Disponible en API para configuración

##### PaymentGatewayConfigSerializer
- Nuevo serializer con validaciones completas
- Campos `refund_window_days` y `partial_refunds_allowed` incluidos
- Validación de `refund_window_days >= 0`
- Validación de hotel/enterprise requerido

#### Admin Interface Mejorado

##### CancellationPolicyAdmin
- Campo `auto_refund_on_cancel` en list_display
- Filtro por `auto_refund_on_cancel`
- Fieldset dedicado "Reembolsos Automáticos"
- Descripción clara del propósito

##### PaymentGatewayConfigAdmin
- Campos `refund_window_days` y `partial_refunds_allowed` en list_display
- Filtro por `partial_refunds_allowed`
- Fieldset dedicado "Configuración de Reembolsos"
- Organización clara de campos

#### Migraciones Aplicadas
- `payments.0010_cancellationpolicy_auto_refund_on_cancel_and_more.py`
  - Campo `auto_refund_on_cancel` en CancellationPolicy
  - Campos `refund_window_days` y `partial_refunds_allowed` en PaymentGatewayConfig

#### Tests de Validación
- **16 tests implementados** cubriendo:
  - Defaults correctos para todos los campos
  - Validaciones de valores (positivos, negativos, null)
  - Casos edge (0, null, valores límite)
  - Actualizaciones y persistencia
  - Integración con admin/API
  - Help text presente en todos los campos

#### Beneficios Técnicos
- **Control granular**: Políticas pueden habilitar/deshabilitar reembolsos automáticos
- **Limitaciones de pasarela**: Configuración de restricciones por proveedor
- **Validaciones robustas**: Prevención de configuraciones inválidas
- **API consistente**: Todos los campos expuestos correctamente
- **Admin organizado**: Interface clara para configuración
- **Tests completos**: Cobertura total de funcionalidades

### Componentes Frontend

#### CancellationModal.jsx - Mejoras v2.0

##### Nuevas Funcionalidades Implementadas
```javascript
// Badge de reembolso automático
{hasAutoRefund() && (
  <Badge variant="success" size="sm" className="animate-pulse">
    ✓ Reembolso automático disponible
  </Badge>
)}

// Nota sobre pasarelas sin soporte
{!hasAutoRefund() && (
  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
    <p><strong>⚠️ Reembolso manual requerido:</strong> La pasarela de pago no soporta 
    reembolsos automáticos. Se generará un reembolso en estado 'Pendiente' que el 
    staff debe procesar manualmente.</p>
  </div>
)}

// Botones reorganizados en customFooter
customFooter={step === 'confirmation' ? (
  <div className="flex flex-col sm:flex-row justify-end gap-3 w-full">
    <Button variant="secondary" onClick={onClose}>Cerrar</Button>
    <Button variant="success" onClick={handleConfirmCancel}>
      Cancelar y solicitar reembolso
    </Button>
    <Button variant="warning" disabled={true}>
      Cancelar sin reembolso (Solo staff)
    </Button>
  </div>
) : undefined}
```

##### Mejoras de Accesibilidad
```javascript
// Atributos ARIA completos
<ModalLayout
  aria-labelledby="cancellation-modal-title"
  aria-describedby="cancellation-modal-description"
>
  <div role="region" aria-label="Detalles de la reserva">
  <div role="region" aria-label="Política de cancelación aplicada">
  <div role="region" aria-label="Resumen financiero de la cancelación">
  <div role="region" aria-label="Información sobre devolución automática">
```

##### Integración con APIs
```javascript
// Llamada a endpoint de reglas de cancelación
const fetchCancellationRules = async () => {
  const response = await fetch(`/api/reservations/${reservation.id}/cancellation_rules/`)
  const data = await response.json()
  setCancellationRules(data)
}

// Verificación de reembolso automático
const hasAutoRefund = () => {
  return cancellationRules?.applied_cancellation_policy?.auto_refund_on_cancel
}
```

##### Tests Unitarios
```javascript
// Suite de tests completa
describe('CancellationModal', () => {
  it('muestra el badge de reembolso automático cuando está habilitado')
  it('muestra información de reembolso manual cuando no hay soporte automático')
  it('tiene atributos de accesibilidad correctos')
  it('valida que el motivo de cancelación es obligatorio')
  it('renderiza correctamente cuando está cerrado')
})
```

#### RefundsManagement.jsx
```javascript
// Página principal de gestión de reembolsos
- Tabla completa de reembolsos con filtros
- Filtros por estado, método, fecha, reserva
- Búsqueda por ID de reserva o huésped
- Integración con react-select para filtros
- Cache invalidation automático
- Paginación y ordenamiento
```

#### RefundDetailsModal.jsx
```javascript
// Modal de detalles y acciones de reembolso
- Información completa del reembolso
- Detalles de la reserva asociada
- Información del pago original
- Motivo de cancelación (si aplica)
- Acciones: Marcar como completado/fallido
- Integración con useUpdate hook
- Notificaciones automáticas
```

#### DevolutionPoliciesModal.jsx
```javascript
// Modal de configuración de políticas de devolución
- Configuración por pestañas (Básico, Tiempos, Métodos, etc.)
- Selects con valores pre-cargados en modo edición
- Validación con Formik y Yup
- Integración con useCreate y useUpdate hooks
- Configuración avanzada por tipo de habitación/canal
```

#### CancellationModal.jsx
```javascript
// Modal de cancelación de reservas mejorado
- Campo obligatorio de motivo de cancelación
- Cálculo automático de penalidades
- Información financiera detallada
- Confirmación en dos pasos
- Integración con endpoint unificado de cancelación
- Badge de reembolso automático cuando está habilitado
- Nota informativa sobre pasarelas sin soporte automático
- Botones reorganizados en customFooter del modal
- Accesibilidad mejorada con atributos ARIA
- Información de política aplicada históricamente
- Método sugerido de reembolso
- Opción "Cancelar sin reembolso" para staff (futuro)
```

### Funcionalidades de Frontend

#### Gestión de Reembolsos
- ✅ **Lista completa** de reembolsos con filtros avanzados
- ✅ **Filtros por estado**: Pendiente, Procesando, Completado, Fallido, Cancelado
- ✅ **Filtros por método**: Efectivo, Transferencia, Tarjeta, Voucher, Original
- ✅ **Búsqueda por reserva** o huésped
- ✅ **Actualización de estado** en tiempo real
- ✅ **Cache invalidation** automático
- ✅ **Paginación** y ordenamiento

#### Detalles de Reembolsos
- ✅ **Información completa** del reembolso
- ✅ **Detalles de la reserva** asociada
- ✅ **Información del pago** original
- ✅ **Motivo de cancelación** visible
- ✅ **Acciones de gestión** (completar/fallar)
- ✅ **Notificaciones** automáticas
- ✅ **Actualización en tiempo real**

#### Políticas de Devolución
- ✅ **Configuración completa** por hotel
- ✅ **Tiempos configurables** (horas/días/semanas)
- ✅ **Métodos de devolución** flexibles
- ✅ **Mensajes personalizados** por tipo
- ✅ **Targeting avanzado** por habitación/canal
- ✅ **Configuración de vouchers**
- ✅ **Validación completa** de formularios

#### Cancelación de Reservas
- ✅ **Motivo obligatorio** de cancelación
- ✅ **Cálculo automático** de penalidades
- ✅ **Información financiera** detallada
- ✅ **Confirmación en dos pasos**
- ✅ **Procesamiento automático** de devoluciones
- ✅ **Liberación automática** de habitaciones

#### Modal de Cancelación Mejorado (v2.0)
- ✅ **Badge de reembolso automático** cuando `auto_refund_on_cancel` está activado
- ✅ **Nota informativa** sobre pasarelas sin soporte automático
- ✅ **Botones reorganizados** en `customFooter` del modal
- ✅ **Accesibilidad mejorada** con atributos ARIA completos
- ✅ **Información de política aplicada** históricamente
- ✅ **Método sugerido de reembolso** según configuración
- ✅ **Opción "Cancelar sin reembolso"** para staff (preparado para roles)
- ✅ **Tests unitarios completos** para renderizado e interacciones

---

### Sistema de Generación de PDFs y Envío de Emails

#### Arquitectura del Sistema
El sistema de generación de PDFs y envío de emails está diseñado para funcionar de manera asíncrona y automática:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trigger       │    │   Celery Task   │    │   PDF Generator │
│   (Signal)      │───►│   (Async)       │───►│   (ReportLab)   │
│                 │    │                 │    │                 │
│ • Payment Save  │    │ • PDF Creation  │    │ • Hotel Logo    │
│ • Refund Save   │    │ • Email Send    │    │ • Professional  │
│ • Manual Pay    │    │ • Error Handle  │    │   Design        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Componentes Principales

##### 1. PDFReceiptGenerator
**Ubicación**: `apps/payments/services/pdf_generator.py`

**Propósito**: Generar PDFs profesionales de recibos de pagos y reembolsos.

**Características**:
- ✅ **Logo del hotel** en el encabezado (si está configurado)
- ✅ **Información completa del hotel** (nombre, dirección, teléfono, email, RUT)
- ✅ **Fecha y hora de emisión** automática
- ✅ **Datos del pago/reembolso** estructurados en tabla
- ✅ **Información del huésped** principal
- ✅ **Diseño profesional** con colores y estilos consistentes
- ✅ **Sello fiscal interno** "Recibo generado automáticamente por AlojaSys (sin validez fiscal)"
- ✅ **Logo de AlojaSys** en el pie de página

**Métodos principales**:
```python
def generate_payment_receipt(payment_data: Dict[str, Any]) -> str
def generate_refund_receipt(refund_data: Dict[str, Any]) -> str
def _build_header(data: Dict[str, Any], is_refund: bool = False) -> list
def _build_payment_info(data: Dict[str, Any]) -> list
def _build_refund_info(data: Dict[str, Any]) -> list
def _build_footer() -> list
```

##### 2. Tareas Celery Asíncronas
**Ubicación**: `apps/payments/tasks.py`

**Tareas principales**:

###### generate_payment_receipt_pdf()
```python
@shared_task(bind=True)
def generate_payment_receipt_pdf(self, payment_id: int, payment_type: str = 'payment'):
    """
    Genera un PDF de recibo para un pago o refund
    - Obtiene datos del hotel (incluyendo logo)
    - Extrae información del huésped principal
    - Genera PDF con diseño profesional
    - Encadena envío de email automático
    """
```

###### send_payment_receipt_email()
```python
@shared_task(bind=True)
def send_payment_receipt_email(self, payment_id: int, payment_type: str = 'payment', recipient_email: str = None):
    """
    Envía un email con el recibo PDF adjunto
    - Usa email del hotel como remitente
    - Adjunta PDF generado automáticamente
    - Configura reply-to al email del hotel
    - Maneja errores de envío
    """
```

##### 3. Señales Django (Triggers)
**Ubicación**: `apps/payments/signals.py`

**Señales configuradas**:

###### generate_payment_receipt
```python
@receiver(post_save, sender='reservations.Payment')
def generate_payment_receipt(sender, instance, created, **kwargs):
    """
    Trigger: Cuando se crea un pago manual
    Acción: Genera PDF y envía email automáticamente
    """
```

###### generate_refund_receipt
```python
@receiver(post_save, sender='payments.Refund')
def generate_refund_receipt(sender, instance, created, **kwargs):
    """
    Trigger: Cuando se crea un reembolso
    Acción: Genera PDF y envía email automáticamente
    """
```

#### Flujo de Trabajo

##### 1. Creación de Pago Manual
```
1. Usuario confirma reserva con pago en efectivo
2. Se crea Payment object en la base de datos
3. Signal post_save se dispara automáticamente
4. Celery task generate_payment_receipt_pdf se ejecuta
5. Se extrae información del hotel (incluyendo logo)
6. Se genera PDF con diseño profesional
7. Se encadena tarea de envío de email
8. Email se envía al huésped principal con PDF adjunto
```

##### 2. Procesamiento de Reembolso
```
1. Usuario cancela reserva con reembolso
2. Se crea Refund object en la base de datos
3. Signal post_save se dispara automáticamente
4. Celery task generate_payment_receipt_pdf se ejecuta
5. Se genera PDF de reembolso con información completa
6. Se envía email al huésped con recibo de reembolso
```

#### Configuración de Email

##### Variables de Entorno Requeridas
```bash
# Backend/.env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=TU_API_KEY_DE_RESEND
DEFAULT_FROM_EMAIL=AlojaSys <noreply@aloja.com>
```

##### Configuración SMTP
- **Proveedor**: Resend (recomendado) o cualquier SMTP
- **Autenticación**: API Key como contraseña
- **Seguridad**: TLS habilitado
- **Remitente**: Email global de AlojaSys
- **Reply-To**: Email específico del hotel

#### Estructura de Datos

##### payment_data (para pagos)
```python
{
    'payment_id': int,
    'reservation_code': str,  # "RES-{id}"
    'amount': float,
    'method': str,  # "Efectivo", "Transferencia", etc.
    'date': str,  # "DD/MM/YYYY HH:MM:SS"
    'hotel_info': {
        'name': str,
        'address': str,
        'tax_id': str,
        'phone': str,
        'email': str,
        'logo_path': str  # Ruta al archivo de logo
    },
    'guest_info': {
        'name': str,
        'email': str
    }
}
```

##### refund_data (para reembolsos)
```python
{
    'refund_id': int,
    'payment_id': int,  # ID del pago original
    'reservation_code': str,
    'amount': float,
    'method': str,
    'date': str,
    'reason': str,  # Motivo del reembolso
    'hotel_info': { ... },  # Misma estructura
    'guest_info': { ... }   # Misma estructura
}
```

#### Almacenamiento de PDFs

##### Estructura de Directorios
```
/media/
└── receipts/
    ├── payment_123.pdf
    ├── payment_124.pdf
    ├── refund_45.pdf
    └── refund_46.pdf
```

##### Convención de Nombres
- **Pagos**: `payment_{payment_id}.pdf`
- **Reembolsos**: `refund_{refund_id}.pdf`

#### Manejo de Errores

##### Errores de Generación de PDF
- **Logo no encontrado**: Continúa sin logo
- **Datos faltantes**: Usa valores por defecto
- **Error de ReportLab**: Log del error, continúa proceso

##### Errores de Envío de Email
- **Email no encontrado**: Log de advertencia
- **Error SMTP**: Reintento automático
- **PDF no generado**: No envía email

#### Logs y Monitoreo

##### Logs de Celery
```bash
# Generación exitosa
[INFO] Generando PDF de recibo para payment ID: 123
[INFO] PDF generado exitosamente: /app/media/receipts/payment_123.pdf

# Envío de email
[INFO] Enviando email con recibo para payment ID: 123
[INFO] Email enviado exitosamente a: cliente@email.com
```

##### Logs de Error
```bash
# Error de generación
[ERROR] Error generando PDF para payment 123: [detalle del error]

# Error de envío
[ERROR] Error enviando email para payment 123: [detalle del error]
```

#### Beneficios del Sistema

##### Para el Hotel
- ✅ **Automatización completa** del proceso de recibos
- ✅ **Diseño profesional** con logo del hotel
- ✅ **Información completa** del hotel en cada recibo
- ✅ **Sin intervención manual** requerida
- ✅ **Consistencia visual** en todos los recibos

##### Para el Huésped
- ✅ **Recibo inmediato** por email
- ✅ **Información clara** del pago/reembolso
- ✅ **Datos de contacto** del hotel
- ✅ **Formato profesional** y fácil de imprimir
- ✅ **Historial digital** de transacciones

##### Para el Sistema
- ✅ **Procesamiento asíncrono** sin bloquear la UI
- ✅ **Manejo robusto de errores**
- ✅ **Escalabilidad** con Celery
- ✅ **Logs detallados** para debugging
- ✅ **Configuración flexible** por hotel

----

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

## 3.12 Módulo Cobros (Payment Collections)

**Propósito**: Historial unificado de todos los pagos y cobros del hotel con funcionalidades avanzadas de análisis y exportación.

### Modelos Principales

#### PaymentCollectionViewSet
```python
class PaymentCollectionViewSet(ReadOnlyModelViewSet):
    """ViewSet para historial unificado de pagos"""
    
    def get_queryset(self):
        """Combina pagos de diferentes fuentes:
        - Payment (pagos manuales)
        - PaymentIntent (pagos online)
        - BankTransferPayment (transferencias bancarias)
        - Reservation (reservas pendientes)
        """
```

### Funcionalidades Principales

#### Historial Unificado de Pagos
- **Pagos Manuales**: Efectivo, tarjeta, POS registrados manualmente
- **Pagos Online**: Mercado Pago y otras pasarelas
- **Transferencias Bancarias**: Con comprobantes y validación OCR
- **Reservas Pendientes**: Reservas sin confirmar que requieren pago

#### Filtros Avanzados
- **Por Fecha**: Rango de fechas personalizable
- **Por Tipo**: Manual, Online, Transferencia, Pendiente
- **Por Método**: Efectivo, Tarjeta, Transferencia Bancaria, Mercado Pago
- **Por Estado**: Aprobado, Pendiente, Rechazado, Cancelado
- **Por Monto**: Rango de montos mínimo y máximo
- **Por Hotel**: Filtro por hotel específico
- **Por Huésped**: Búsqueda por nombre de huésped

#### Estadísticas y Métricas
- **Resumen General**: Total de pagos, monto total, promedio
- **Por Tipo**: Distribución de pagos por tipo
- **Por Método**: Distribución de pagos por método
- **Por Mes**: Evolución temporal de cobros
- **Tendencias**: Análisis de patrones de pago

#### Exportación de Datos
- **Formato CSV**: Exportación completa con filtros aplicados
- **Datos Incluidos**: Todos los campos relevantes del pago
- **Filtros Aplicados**: Respeta los filtros seleccionados
- **Descarga Directa**: Sin necesidad de procesamiento adicional

#### Sistema de Archivos Adjuntos
- **Comprobantes de Transferencia**: PDFs, JPGs, PNGs subidos
- **Almacenamiento Híbrido**: Local (desarrollo) / Cloudinary (producción)
- **Visualización**: Previsualización y descarga de archivos
- **Metadatos**: Información del archivo y validación

### APIs Principales

#### Endpoints de Cobros
- `GET /api/payments/collections/` - Historial unificado con filtros
- `GET /api/payments/collections/stats/` - Estadísticas agregadas
- `GET /api/payments/collections/export/` - Exportación CSV

#### Parámetros de Filtrado
```python
# Filtros disponibles
{
    'date_from': '2024-01-01',      # Fecha desde
    'date_to': '2024-12-31',        # Fecha hasta
    'type': 'bank_transfer',        # Tipo de pago
    'method': 'card',               # Método de pago
    'status': 'approved',           # Estado del pago
    'min_amount': 1000,             # Monto mínimo
    'max_amount': 50000,            # Monto máximo
    'hotel_id': 1,                  # ID del hotel
    'search': 'Juan Pérez'          # Búsqueda por huésped
}
```

### Beneficios del Módulo

#### Para la Gestión Hotelera
- ✅ **Visión Unificada**: Todos los pagos en un solo lugar
- ✅ **Análisis Completo**: Métricas detalladas del negocio
- ✅ **Trazabilidad Total**: Seguimiento completo de transacciones
- ✅ **Exportación Fácil**: Datos para contabilidad y análisis

---

## 3.12 Módulo Conciliación Bancaria

**Propósito**: Automatización de la conciliación entre movimientos bancarios y pagos del hotel mediante algoritmos de matching inteligente.

### Modelos Principales

#### BankReconciliation
```python
class BankReconciliation(models.Model):
    """Registro de conciliación bancaria"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    reconciliation_date = models.DateField()
    csv_file = models.FileField(upload_to='reconciliations/')
    total_transactions = models.IntegerField()
    matched_transactions = models.IntegerField()
    unmatched_transactions = models.IntegerField()
    status = models.CharField(max_length=20, choices=ReconciliationStatus.choices)
    match_percentage = models.FloatField()
```

#### BankTransaction
```python
class BankTransaction(models.Model):
    """Transacción bancaria del CSV"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE)
    transaction_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    reference = models.CharField(max_length=100)
    is_matched = models.BooleanField(default=False)
```

#### ReconciliationMatch
```python
class ReconciliationMatch(models.Model):
    """Match entre transacción bancaria y pago"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE)
    bank_transaction = models.ForeignKey(BankTransaction, on_delete=models.CASCADE)
    payment_id = models.IntegerField()
    match_type = models.CharField(max_length=20, choices=MatchType.choices)
    confidence_score = models.FloatField()
    is_confirmed = models.BooleanField(default=False)
```

### Funcionalidades Principales

#### Algoritmos de Matching
- **Exact Match**: Monto exacto + fecha ±1 día
- **Fuzzy Match**: Monto ±0.5% + fecha ±2 días  
- **Partial Match**: Monto ±1% + fecha ±3 días
- **Manual Match**: Aprobación manual de matches de baja confianza

#### Procesamiento Automático
- **CSV Upload**: Subida de archivos de extractos bancarios
- **Parsing Inteligente**: Detección automática de formato y encoding
- **Matching Automático**: Algoritmos de coincidencia por monto y fecha
- **Confirmación Automática**: Pagos confirmados con confianza ≥90%

#### Configuración Flexible
- **Tolerancias Ajustables**: Configuración por hotel
- **Múltiples Monedas**: Conversión automática de tipos de cambio
- **Umbrales de Confianza**: Configuración de auto-confirmación
- **Notificaciones**: Alertas por email y sistema

### APIs Principales

#### Endpoints de Conciliación
- `GET /api/payments/reconciliations/` - Lista de conciliaciones
- `POST /api/payments/reconciliations/upload-csv/` - Subir CSV
- `GET /api/payments/reconciliations/{id}/` - Detalle de conciliación
- `POST /api/payments/reconciliations/{id}/process/` - Procesar conciliación
- `GET /api/payments/reconciliation-matches/` - Matches encontrados
- `POST /api/payments/reconciliation-matches/{id}/approve/` - Aprobar match

#### Formato CSV Esperado
```csv
fecha,descripcion,importe,moneda,referencia
2025-01-15,"Transferencia Juan Perez",25000.00,"ARS","CBU 28500109...1234"
2025-01-16,"Transferencia Maria Garcia",18000.00,"ARS","CBU 28500109...5678"
```

### Tareas Asíncronas (Celery)

#### Procesamiento Nocturno
```python
@shared_task
def nightly_bank_reconciliation():
    """Job nocturno para conciliación automática"""
    # Procesa conciliaciones pendientes
    # Actualiza tipos de cambio
    # Envía notificaciones
```

#### Procesamiento de CSV
```python
@shared_task
def process_bank_reconciliation(reconciliation_id):
    """Procesa una conciliación específica"""
    # Parsea el CSV
    # Ejecuta algoritmos de matching
```

---

## 3.13 Módulo Facturación Electrónica

**Propósito**: Generación y gestión de facturas electrónicas argentinas con integración AFIP, cumpliendo normativas fiscales locales.

### Modelos Principales

#### Invoice
```python
class Invoice(models.Model):
    """Factura electrónica"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True)
    
    # Datos de la factura
    number = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=2, choices=InvoiceType.choices)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices)
    issue_date = models.DateField()
    currency = models.CharField(max_length=3, default='ARS')
    
    # Datos del cliente
    client_name = models.CharField(max_length=200)
    client_document_type = models.CharField(max_length=2)
    client_document_number = models.CharField(max_length=20)
    client_tax_condition = models.CharField(max_length=2)
    client_address = models.CharField(max_length=200, blank=True)
    
    # Montos
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # AFIP
    cae = models.CharField(max_length=14, blank=True)
    cae_expiration = models.DateField(null=True, blank=True)
    sent_to_afip_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    pdf_file = models.FileField(upload_to='invoices/pdf/', null=True, blank=True)
    pdf_url = models.URLField(blank=True)
    
    # Control
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### InvoiceItem
```python
class InvoiceItem(models.Model):
    """Item de factura"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    afip_code = models.CharField(max_length=10, blank=True)
```

#### AfipConfig
```python
class AfipConfig(models.Model):
    """Configuración AFIP por hotel"""
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE)
    environment = models.CharField(max_length=10, choices=Environment.choices)
    cuit = models.CharField(max_length=11)
    point_of_sale = models.IntegerField()
    certificate_path = models.CharField(max_length=500)
    private_key_path = models.CharField(max_length=500)
    tax_condition = models.CharField(max_length=2)
    gross_income = models.CharField(max_length=50, blank=True)
    activity_start_date = models.DateField(null=True, blank=True)
    
    # Tokens AFIP
    afip_token = models.TextField(blank=True)
    afip_sign = models.TextField(blank=True)
    afip_token_generation = models.DateTimeField(null=True, blank=True)
    afip_token_expiration = models.DateTimeField(null=True, blank=True)
```

### Servicios Principales

#### AfipAuthService
```python
class AfipAuthService:
    """Autenticación con AFIP WSAA"""
    
    def get_token_and_sign(self) -> Tuple[str, str]:
        """Obtiene token y sign válidos para AFIP"""
        # 1) Verificar cache
        # 2) Verificar persistencia en BD
        # 3) Generar nuevo token si es necesario
        # 4) Manejar caso "TA ya válido"
```

#### InvoicePDFService
```python
class InvoicePDFService:
    """Generación de PDFs de facturas"""
    
    def generate_pdf(self, invoice: Invoice) -> str:
        """Genera PDF fiscal completo"""
        # 1) Renderizar template HTML
        # 2) Convertir a PDF con WeasyPrint
        # 3) Fallback a ReportLab si falla
```

#### AfipInvoiceService
```python
class AfipInvoiceService:
    """Envío de facturas a AFIP"""
    
    def send_invoice_to_afip(self, invoice: Invoice) -> dict:
        """Envía factura a AFIP y obtiene CAE"""
        # 1) Autenticación con AFIP
        # 2) Construcción de XML
        # 3) Envío a WSFEv1
        # 4) Procesamiento de respuesta
```

### APIs Principales

#### Endpoints de Facturación
- `GET /api/invoicing/invoices/` - Lista de facturas
- `POST /api/invoicing/invoices/create-from-reservation/` - Crear desde reserva
- `GET /api/invoicing/invoices/{id}/pdf/` - Obtener PDF
- `POST /api/invoicing/invoices/{id}/send_to_afip/` - Enviar a AFIP
- `POST /api/invoicing/invoices/{id}/cancel/` - Cancelar factura
- `GET /api/invoicing/invoices/by-reservation/{id}/` - Facturas por reserva

#### Configuración AFIP
- `GET /api/invoicing/afip-config/` - Configuración AFIP
- `POST /api/invoicing/afip-config/` - Crear configuración
- `PUT /api/invoicing/afip-config/{id}/` - Actualizar configuración

### Flujos de Trabajo

#### Generación de Factura
1. **Creación**: Desde reserva o pago
2. **Validación**: Datos del cliente y hotel
3. **Generación**: Número único secuencial
4. **Estado**: Draft (borrador)

#### Envío a AFIP
1. **Autenticación**: Token AFIP válido
2. **Construcción**: XML según normativas
3. **Envío**: WSFEv1 de AFIP
4. **Procesamiento**: CAE y fecha de vencimiento
5. **Estado**: Approved (aprobada)

#### Generación de PDF
1. **Template**: HTML con estilos AFIP
2. **Datos**: Información de factura y hotel
3. **Conversión**: WeasyPrint → PDF
4. **Almacenamiento**: Media files

### Integraciones

#### AFIP WSAA
- **Autenticación**: Certificados digitales
- **Tokens**: Cache y persistencia
- **Manejo de errores**: "TA ya válido"

#### AFIP WSFEv1
- **Envío**: Facturas electrónicas
- **Respuesta**: CAE y autorización
- **Estados**: Aprobada/Rechazada

#### WeasyPrint
- **HTML → PDF**: Conversión de templates
- **Fallback**: ReportLab si falla
- **Estilos**: CSS compatible

### Configuraciones

#### Certificados AFIP
- **Desarrollo**: Certificados de prueba
- **Producción**: Certificados reales
- **Renovación**: Proceso automático

#### Templates PDF
- **HTML**: Template AFIP SDK
- **CSS**: Estilos oficiales
- **Responsive**: A4 optimizado

### Tareas Asíncronas

#### Generación Automática
```python
@shared_task
def generate_invoice_on_payment_approved(payment_id):
    """Genera factura automáticamente al aprobar pago"""
    # Buscar reserva
    # Crear factura
    # Enviar a AFIP
```

#### Envío a AFIP
```python
@shared_task
def send_invoice_to_afip_async(invoice_id):
    """Envía factura a AFIP de forma asíncrona"""
    # Obtener token
    # Construir XML
    # Enviar a AFIP
    # Actualizar estado
```

### Validaciones

#### Datos Obligatorios
- CUIT del hotel
- Datos del cliente
- Montos válidos
- Fechas correctas

#### Normativas AFIP
- Tipos de comprobante
- Condiciones de IVA
- Numeración secuencial
- CAE válido

### Estados de Factura

- **Draft**: Borrador, no enviada
- **Sent**: Enviada a AFIP
- **Approved**: Aprobada por AFIP
- **Rejected**: Rechazada por AFIP
- **Cancelled**: Cancelada
- **Expired**: CAE expirado
    # Actualiza estados de pagos
    # Genera logs de auditoría
```

### Logs de Auditoría

#### BankReconciliationLog
```python
class BankReconciliationLog(models.Model):
    """Log de eventos de conciliación"""
    reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=30, choices=ReconciliationEventType.choices)
    event_description = models.TextField()
    details = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Tipos de Eventos
- `CSV_UPLOADED`: CSV subido exitosamente
- `PROCESSING_STARTED`: Inicio de procesamiento
- `AUTO_MATCHED`: Match automático encontrado
- `MANUAL_MATCHED`: Match aprobado manualmente
- `PENDING_REVIEW`: Match requiere revisión
- `UNMATCHED`: Transacción sin match
- `PROCESSING_COMPLETED`: Procesamiento finalizado

### Beneficios del Módulo

#### Para la Gestión Hotelera
- ✅ **Automatización Total**: Conciliación sin intervención manual
- ✅ **Precisión Alta**: Algoritmos de matching inteligentes
- ✅ **Ahorro de Tiempo**: Procesamiento automático 24/7
- ✅ **Trazabilidad Completa**: Logs detallados de todas las operaciones
- ✅ **Flexibilidad**: Configuración por hotel y moneda
- ✅ **Escalabilidad**: Procesamiento asíncrono con Celery

#### Para el Personal
- ✅ **Interfaz Intuitiva**: Subida de CSV con drag & drop
- ✅ **Reportes Detallados**: Análisis de efectividad de matching
- ✅ **Notificaciones**: Alertas automáticas de problemas
- ✅ **Revisión Manual**: Aprobación de matches de baja confianza
- ✅ **Acceso a Archivos**: Comprobantes y documentos adjuntos

#### Para la Contabilidad
- ✅ **Exportación CSV**: Datos listos para importar
- ✅ **Filtros Precisos**: Solo los datos necesarios
- ✅ **Formato Estándar**: Compatible con sistemas contables

### Mejoras Implementadas (v2.3)

#### Flujo de Transferencias Bancarias Mejorado
- **Problema Resuelto**: Las transferencias bancarias confirmaban automáticamente las reservas, dejando sin propósito la conciliación bancaria
- **Solución Implementada**: 
  - Transferencias bancarias ahora dejan las reservas en estado "Pendiente de Confirmación"
  - La conciliación bancaria es la que confirma definitivamente las reservas
  - Mayor seguridad al verificar que el dinero realmente llegó al banco

#### Algoritmo de Matching Expandido
- **Nuevo Tipo de Match**: Matching directo con reservas pendientes sin pagos asociados
- **Criterios de Matching**:
  - Monto exacto o dentro de tolerancias configuradas
  - Fecha de transacción vs fecha de creación de reserva
  - Nombres de huéspedes en descripción bancaria
- **Tipos de Confianza**:
  - **Exacto**: Monto y fecha coinciden exactamente
  - **Fuzzy**: Pequeñas diferencias en monto/fecha
  - **Parcial**: Diferencias mayores pero dentro de tolerancias

#### Estados de Badge Corregidos
- **Problema**: Estados en español vs inglés causaban badges incorrectos
- **Solución**: Mapeo correcto de estados del backend a variantes de Badge
  - `pending` → `warning` (amarillo)
  - `processing` → `info` (azul)  
  - `completed` → `success` (verde)
  - `failed` → `error` (rojo)
  - `manual_review` → `warning` (amarillo)

#### Integración con Hooks Existentes
- **Reemplazo**: Uso de `useCreate` hook en lugar de llamadas manuales a `fetch`
- **Consistencia**: Misma capa de autenticación (`fetchWithAuth`) en todos los servicios
- **Manejo de Errores**: Notificaciones toast unificadas (`showSuccess`/`showErrorConfirm`)

#### Configuración Temporal para Pruebas
- **Permisos**: `permission_classes = [permissions.AllowAny]` temporalmente para testing
- **URLs**: Corrección de rutas API (`/api/payments/reconciliations/`)
- **Headers**: Eliminación de headers de autorización duplicados

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
4. **Cliente procesa pago** (tarjeta/manual/transferencia)
5. **Sistema confirma reserva** si pago exitoso

#### 1.3.1 Flujo de Transferencia Bancaria
1. **Cliente selecciona transferencia** como método de pago
2. **Cliente sube comprobante** (PDF, JPG, PNG) con datos:
   - Monto de la transferencia
   - Fecha de la transferencia
   - CBU/IBAN del destinatario
   - Nombre del banco
3. **Sistema procesa archivo** con almacenamiento híbrido:
   - **Desarrollo**: Almacenamiento local
   - **Producción**: Cloudinary
4. **Sistema confirma automáticamente** la transferencia:
   - Crea `BankTransferPayment` con estado "CONFIRMED"
   - Crea `Payment` asociado
   - Actualiza reserva a "CONFIRMED"
5. **Sistema registra auditoría** completa del proceso
6. **Cliente recibe confirmación** inmediata del pago

#### 1.3.2 Procesamiento OCR (Opcional)
1. **Sistema ejecuta OCR** en segundo plano (Celery)
2. **Sistema extrae datos** del comprobante:
   - Monto de la transferencia
   - CBU/IBAN del destinatario
3. **Sistema valida datos** extraídos vs. datos ingresados
4. **Si hay discrepancia**: Marca para revisión manual
5. **Si coinciden**: Confirma automáticamente

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
4. **Cliente selecciona método de reembolso** (dinero o voucher)
5. **Sistema procesa devolución** según método seleccionado:
   - **Dinero**: Devuelve al método de pago original
   - **Voucher**: Genera `RefundVoucher` con código único
6. **Sistema crea registro explícito** en tabla `Refund`
7. **Sistema registra log** con detalles financieros completos

#### 4.5 Ventajas del Endpoint Unificado
- **Simplificación**: Un solo endpoint para cálculo y confirmación
- **Consistencia**: Misma lógica para ambos pasos
- **Flexibilidad**: Frontend puede decidir cuándo confirmar
- **Eficiencia**: Menos llamadas API necesarias
- **Mantenibilidad**: Lógica centralizada en un solo lugar

### 5. Flujo de Aplicación de Vouchers

#### 5.1 Proceso de Aplicación
1. **Cliente inicia nueva reserva** con fechas y habitación
2. **Sistema calcula precio base** según tarifas vigentes
3. **Cliente ingresa código de voucher** en campo correspondiente
4. **Sistema valida voucher**:
   - Existe en base de datos
   - Estado es "active"
   - No ha expirado
   - Monto es suficiente para la reserva
5. **Sistema aplica descuento** del voucher al total
6. **Sistema actualiza total** de la reserva
7. **Cliente completa reserva** con descuento aplicado
8. **Sistema marca voucher como usado** y lo asocia a la reserva

#### 5.2 Integración con Motor de Tarifas
```python
# Flujo de cálculo con voucher
def compute_rate_for_date(room, guests, on_date, channel=None, promotion_code=None, voucher_code=None):
    # 1. Calcular precio base
    base_rate = get_base_rate(room, on_date)
    
    # 2. Aplicar promociones (si existen)
    promotion_discount = apply_promotions(promotion_code, base_rate)
    
    # 3. Aplicar vouchers (si existen)
    voucher_discount = apply_vouchers(voucher_code, base_rate - promotion_discount)
    
    # 4. Calcular total final
    total = base_rate - promotion_discount - voucher_discount
    
    return {
        'base_rate': base_rate,
        'promotion_discount': promotion_discount,
        'voucher_discount': voucher_discount,
        'total': total
    }
```

#### 5.3 Validación de Vouchers
```python
def validate_voucher(voucher_code, reservation_amount):
    """Valida si un voucher puede ser usado"""
    try:
        voucher = RefundVoucher.objects.get(code=voucher_code)
        
        # Verificar estado
        if voucher.status != 'active':
            return False, "Voucher no está activo"
        
        # Verificar vencimiento
        if voucher.is_expired():
            return False, "Voucher ha expirado"
        
        # Verificar monto
        if voucher.amount < reservation_amount:
            return False, "Monto del voucher insuficiente"
        
        return True, "Voucher válido"
        
    except RefundVoucher.DoesNotExist:
        return False, "Voucher no encontrado"
```

#### 5.4 Coexistencia con Promociones
- **Orden de aplicación**: Primero promociones, luego vouchers
- **Combinación permitida**: Ambos pueden usarse simultáneamente
- **Cálculo secuencial**: Descuentos se aplican en orden
- **Validación independiente**: Cada sistema valida por separado

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

### Transferencias Bancarias
- `GET /api/payments/bank-transfers/` - Listar transferencias (con filtros)
- `POST /api/payments/bank-transfers/` - Crear transferencia
- `GET /api/payments/bank-transfers/{id}/` - Obtener transferencia
- `PUT /api/payments/bank-transfers/{id}/` - Actualizar transferencia
- `POST /api/payments/bank-transfers/{id}/confirm/` - Confirmar transferencia
- `POST /api/payments/bank-transfers/{id}/reject/` - Rechazar transferencia
- `POST /api/payments/bank-transfers/{id}/mark_pending_review/` - Marcar para revisión
- `GET /api/payments/bank-transfers/pending_review/` - Transferencias pendientes
- `GET /api/payments/bank-transfers/stats/` - Estadísticas de transferencias
- `POST /api/payments/upload-bank-transfer/` - Subir comprobante (con OCR)

### Cobros (Historial Unificado)
- `GET /api/payments/collections/` - Historial unificado de pagos
- `GET /api/payments/collections/stats/` - Estadísticas de cobros
- `GET /api/payments/collections/export/` - Exportar cobros a CSV

### Vouchers de Crédito
- `GET /api/payments/refund-vouchers/` - Listar vouchers con filtros
- `POST /api/payments/refund-vouchers/` - Crear voucher manual
- `GET /api/payments/refund-vouchers/{id}/` - Obtener voucher específico
- `PUT /api/payments/refund-vouchers/{id}/` - Actualizar voucher
- `PATCH /api/payments/refund-vouchers/{id}/` - Actualizar estado del voucher
- `DELETE /api/payments/refund-vouchers/{id}/` - Cancelar voucher
- `POST /api/payments/refund-vouchers/use/` - Usar voucher en reserva
- `GET /api/payments/refund-vouchers/validate/` - Validar código de voucher

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
- **Snapshot de políticas**: Captura histórica de políticas al confirmar reservas

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
- **Webhooks**: Confirmación automática de pagos con verificación HMAC
- **Estados**: Seguimiento de estados de pago
- **Configuración**: Por hotel o por empresa
- **Modo**: Prueba y producción
- **Seguridad**: Verificación HMAC obligatoria para webhooks
- **Idempotencia**: Prevención de procesamiento duplicado
- **Post-procesamiento**: Tareas asíncronas para notificaciones y auditoría

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

## 3.10 Snapshot de Políticas de Cancelación

**Propósito**: Garantizar consistencia histórica en las políticas de cancelación aplicadas a reservas, evitando que cambios futuros en políticas afecten reservas ya confirmadas.

### Funcionalidad Principal

#### Captura Automática de Snapshot
- **Momento**: Al confirmar una reserva (cambio de estado a CONFIRMED)
- **Campo**: `applied_cancellation_snapshot` (JSONField en modelo Reservation)
- **Contenido**: Captura completa de la política vigente al momento de confirmación
- **Inmutabilidad**: Una vez creado, el snapshot no se modifica

#### Estructura del Snapshot
```json
{
  "policy_id": 123,
  "name": "Política Estándar",
  "free_cancellation_time": 24,
  "free_cancellation_unit": "hours",
  "partial_time": 72,
  "partial_percentage": 50.0,
  "no_cancellation_time": 168,
  "no_cancellation_unit": "hours",
  "fee_type": "percentage",
  "fee_value": 25.0,
  "auto_refund_on_cancel": true,
  "allow_cancellation_after_checkin": false,
  "allow_cancellation_after_checkout": false,
  "allow_cancellation_no_show": true,
  "allow_cancellation_early_checkout": false,
  "snapshot_created_at": "2024-01-15T10:30:00Z"
}
```

### Servicios de Cálculo

#### SnapshotCancellationCalculator
- **Ubicación**: `apps/reservations/services/snapshot_cancellation_calculator.py`
- **Propósito**: Calcular reglas de cancelación usando snapshot histórico
- **Métodos principales**:
  - `should_use_snapshot()`: Determina si usar snapshot o política actual
  - `get_cancellation_rules_from_snapshot()`: Calcula reglas desde snapshot
  - `_convert_to_hours()`: Convierte unidades de tiempo a horas

### Integración con Endpoints

#### Cancelación de Reservas
- **Endpoint**: `POST /api/reservations/{id}/cancel/`
- **Lógica**: Usa snapshot si está disponible, sino fallback a política actual
- **Beneficio**: Consistencia garantizada en cancelaciones

#### Procesamiento de Reembolsos
- **Servicio**: `RefundProcessor.process_refund()`
- **Lógica**: Prioriza snapshot sobre política actual
- **Resultado**: Cálculos consistentes independientemente de cambios en políticas

### Casos de Uso

#### Caso 1: Cambio de Política Después de Confirmación
```
1. Reserva confirmada con política A (24h gratuita)
2. Hotel cambia a política B (48h gratuita)
3. Cliente cancela después de 30 horas
4. Sistema usa snapshot (política A) → Cancelación gratuita
5. Sin snapshot → Usaría política B → Penalidad del 50%
```

#### Caso 2: Auditoría Histórica
```
1. Cliente reclama penalidad incorrecta
2. Sistema consulta snapshot de la reserva
3. Muestra política exacta vigente al confirmar
4. Resolución transparente del reclamo
```

### Beneficios Técnicos

#### Consistencia de Datos
- **Inmutabilidad**: Snapshot no cambia una vez creado
- **Trazabilidad**: Registro histórico completo de políticas aplicadas
- **Auditoría**: Cumplimiento regulatorio facilitado

#### Escalabilidad
- **Performance**: Cálculos basados en datos locales (snapshot)
- **Independencia**: No requiere consultas a políticas actuales
- **Caching**: Snapshot actúa como cache de política histórica

### Implementación Técnica

#### Modelo de Datos
```python
class Reservation(models.Model):
    applied_cancellation_policy = ForeignKey(...)  # Referencia actual
    applied_cancellation_snapshot = JSONField(...)  # Snapshot histórico
```

#### Migración
- **Archivo**: `0011_reservation_applied_cancellation_snapshot.py`
- **Campo**: `applied_cancellation_snapshot` (JSONField, nullable)
- **Backward compatibility**: Reservas existentes sin snapshot usan política actual

### Consideraciones de Performance

#### Optimización de Consultas
- **Select related**: Incluir snapshot en consultas de reservas
- **Serialización**: Snapshot se incluye en respuestas de API

#### Almacenamiento
- **Tamaño**: ~500 bytes por snapshot (JSON compacto)
- **Frecuencia**: Un snapshot por reserva confirmada
- **Limpieza**: No requerida (datos históricos valiosos)

### Testing

#### Casos de Prueba
- **Snapshot creation**: Verificar creación automática al confirmar
- **Calculation accuracy**: Validar cálculos con diferentes snapshots
- **Fallback logic**: Confirmar uso de política actual cuando no hay snapshot
- **Edge cases**: Manejo de snapshots malformados o incompletos

### Monitoreo y Logging

#### Eventos Registrados
- **Snapshot creation**: Log cuando se crea un snapshot
- **Calculation usage**: Log cuando se usa snapshot vs política actual
- **Fallback events**: Log cuando se usa política actual por falta de snapshot

#### Métricas
- **Snapshot coverage**: % de reservas con snapshot
- **Calculation performance**: Tiempo de cálculo con snapshot vs política
- **Fallback frequency**: Frecuencia de uso de política actual

----

## 3.11 Módulo Notifications

**Propósito**: Sistema de notificaciones in-app para alertar sobre eventos automáticos del sistema.

### Modelos Principales

#### Notification
```python
class Notification(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = CharField(max_length=20, choices=NotificationType.choices)
    title = CharField(max_length=200)
    message = TextField()
    user = ForeignKey(User, null=True, blank=True)  # null = todos los usuarios
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    
    # Campos de contexto
    hotel_id = PositiveIntegerField(null=True, blank=True)
    reservation_id = PositiveIntegerField(null=True, blank=True)
    metadata = JSONField(default=dict)
```

#### Tipos de Notificación
```python
class NotificationType(models.TextChoices):
    AUTO_CANCEL = "auto_cancel", "Auto Cancelación"
    MANUAL_CANCEL = "manual_cancel", "Cancelación Manual"
    NO_SHOW = "no_show", "No Show"
    REFUND_AUTO = "refund_auto", "Reembolso Automático"
    REFUND_FAILED = "refund_failed", "Reembolso Fallido"
```

### Eventos que Generan Notificaciones

#### 🔴 Auto-Cancelaciones
- **Trigger**: Tareas automáticas de Celery
- **Motivos**:
  - Depósito vencido sin pago (`auto_cancel_pending_deposits`)
  - Días desde creación excedidos (`auto_cancel_expired_reservations`)
  - Fecha de check-in vencida (`auto_cancel_expired_pending_reservations`)
- **Datos**: Código de reserva, hotel, motivo, fechas

#### 🟠 Cancelaciones Manuales
- **Trigger**: API de cancelación manual (`reservations/views.py`)
- **Datos**: Código de reserva, hotel, motivo, usuario que cancela

#### 🟣 No-Shows (v2.0 - Mejorado)
- **Trigger**: Tarea automática `auto_mark_no_show_daily` con `NoShowProcessor`
- **Condición**: Solo hoteles con `auto_no_show_enabled=True`
- **Datos**: Código de reserva, hotel, fecha de check-in, penalidades aplicadas, reembolsos
- **Notificaciones diferenciadas**:
  - **Hotel**: Información financiera completa, acciones requeridas
  - **Huésped**: Detalles de la reserva, información de reembolso, próximos pasos
  - **Administradores**: Reportes de impacto financiero
- **Métodos de reembolso específicos**:
  - Voucher con validez extendida (365 días)
  - Transferencia bancaria (requiere datos del huésped)
  - Pago original (reembolso al método de pago original)
  - Manual (efectivo, etc.)

#### 🟡 Reembolsos Automáticos
- **Trigger**: Procesador de reembolsos (`refund_processor.py`)
- **Estados**: Pendiente, Procesando, Completado
- **Datos**: Monto, código de reserva, hotel, estado

#### 🟠 Reembolsos Fallidos
- **Trigger**: Procesador de reembolsos cuando falla
- **Datos**: Monto, código de reserva, hotel, error

### Funcionalidades Principales

#### Gestión de Notificaciones
- ✅ **Creación automática** desde tareas de Celery
- ✅ **Tipos específicos** para diferentes eventos del sistema
- ✅ **Destinatarios flexibles** (usuario específico o todos)
- ✅ **Metadatos contextuales** para información adicional
- ✅ **Estados de lectura** con conteo de no leídas
- ✅ **Agrupación inteligente** de notificaciones relacionadas

#### Servicio Centralizado
```python
class NotificationService:
    @staticmethod
    def create_auto_cancel_notification(reservation_code, hotel_name, reason, ...):
        """Crea notificación de auto-cancelación"""
    
    @staticmethod
    def create_manual_cancel_notification(reservation_code, hotel_name, reason, ...):
        """Crea notificación de cancelación manual"""
    
    @staticmethod
    def create_no_show_notification(reservation_code, hotel_name, check_in_date, ...):
        """Crea notificación de no-show"""
    
    @staticmethod
    def create_refund_auto_notification(reservation_code, hotel_name, amount, status, ...):
        """Crea notificación de reembolso automático"""
    
    @staticmethod
    def create_bulk_notification(notification_type, title, message_template, ...):
        """Crea múltiples notificaciones para varios usuarios"""
```

#### Integración con Procesos Automáticos
- ✅ **Auto-cancelación de reservas**: Notifica cuando se cancela por depósito vencido
- ✅ **Auto no-show**: Notifica cuando se marca reserva como no-show
- ✅ **Procesamiento de reembolsos**: Notifica estados de reembolsos automáticos
- ✅ **Cancelaciones manuales**: Notifica cuando el personal cancela reservas

#### Agrupación Inteligente de Notificaciones
- ✅ **Notificaciones relacionadas**: Agrupa notificaciones del mismo `reservation_id` o `hotel_id`
- ✅ **Ventana de tiempo**: Agrupa notificaciones creadas dentro de 2 minutos
- ✅ **Interfaz optimizada**: Muestra grupos como "X notificaciones relacionadas"
- ✅ **Contexto mejorado**: Evita duplicación visual de información similar

### APIs Principales
- `GET /api/notifications/` - Listar notificaciones (con filtros)
- `GET /api/notifications/{id}/` - Obtener notificación específica
- `PATCH /api/notifications/{id}/mark_read/` - Marcar como leída
- `POST /api/notifications/mark_all_read/` - Marcar todas como leídas
- `GET /api/notifications/unread_count/` - Conteo de no leídas
- `GET /api/notifications/stats/` - Estadísticas completas
- `GET /api/notifications/recent/` - Últimas 5 no leídas

### Filtros y Parámetros
- `?type=auto_cancel` - Filtrar por tipo de notificación
- `?is_read=false` - Solo notificaciones no leídas
- `?hotel_id=1` - Filtrar por hotel específico

### Componentes Frontend

#### useNotifications Hook
```javascript
const {
  notifications,           // Lista completa de notificaciones
  unreadCount,           // Conteo de no leídas
  recentNotifications,   // Últimas 5 no leídas
  isLoading,            // Estado de carga
  markAsRead,           // Función para marcar como leída
  markAllAsRead,        // Función para marcar todas como leídas
  refreshAll            // Función para refrescar todas
} = useNotifications({
  refetchInterval: 30000  // Polling cada 30 segundos
});
```

#### NotificationsBell Component
- **Ubicación**: Header del sistema
- **Funcionalidad**: 
  - Badge con conteo de no leídas
  - Dropdown con últimas 5 notificaciones
  - Botón para marcar como leída
  - Enlace a página completa
- **Polling**: Actualización automática cada 30 segundos

#### Página de Notificaciones (/notificaciones)
- **Tabla completa** con todas las notificaciones
- **Filtros avanzados** por tipo y estado
- **Acciones masivas** (marcar todas como leídas)
- **Colores diferenciados** por tipo de notificación
- **Información contextual** (hotel, reserva, metadatos)

### Características Técnicas

#### Base de Datos
- **Primary Key**: UUID para mejor escalabilidad
- **Índices optimizados**: Por usuario, estado y tipo
- **Relaciones**: ForeignKey opcional a User (null = todos)
- **Metadatos**: JSONField para información flexible

#### Performance
- **Polling inteligente**: 30 segundos por defecto, configurable
- **Cache automático**: TanStack Query maneja el cache
- **Paginación**: Límites en consultas para mejor rendimiento
- **Índices**: Optimizados para consultas frecuentes

#### Integración con Celery
```python
# En auto_mark_no_show_daily
NotificationService.create_no_show_notification(
    reservation_code=f"RES-{reservation.id}",
    hotel_name=hotel.name,
    check_in_date=str(reservation.check_in),
    hotel_id=hotel.id,
    reservation_id=reservation.id
)

# En auto_cancel_expired_pending_reservations
NotificationService.create_auto_cancel_notification(
    reservation_code=f"RES-{reservation.id}",
    hotel_name=reservation.hotel.name,
    reason="Fecha de check-in vencida sin pago del depósito",
    hotel_id=reservation.hotel.id,
    reservation_id=reservation.id
)
```

### Mejoras NO_SHOW v2.0 - Penalidades y Reembolsos Específicos

#### Nuevos Eventos de Log
```python
class ReservationChangeEvent(models.TextChoices):
    # ... eventos existentes ...
    NO_SHOW_PENALTY = "no_show_penalty", "Penalidad NO_SHOW"
    NO_SHOW_PROCESSED = "no_show_processed", "NO_SHOW Procesado"
```

#### Configuraciones Específicas para NO_SHOW
```python
# En RefundPolicy - campos específicos para NO_SHOW
class RefundPolicy(models.Model):
    # ... campos existentes ...
    
    # Campos específicos para NO_SHOW (usando metadata)
    metadata = JSONField(default=dict)
    
    # Ejemplo de configuración:
    # {
    #     'no_show_refund_percentage': 25,  # 25% de reembolso para NO_SHOW
    #     'no_show_refund_method': 'voucher',
    #     'no_show_processing_days': 45,  # 45 días para procesar NO_SHOW
    #     'no_show_voucher_percentage': 25,
    #     'allow_no_show_refund': True
    # }
```

#### Notificaciones Mejoradas para NO_SHOW

##### Notificación para el Hotel
```python
def _create_hotel_notification_message(reservation, penalty_amount, refund_amount, total_paid, net_loss):
    """
    Crea mensaje detallado para notificación del hotel
    """
    message_parts = [
        f"🚨 RESERVA NO_SHOW DETECTADA",
        f"",
        f"📋 Detalles de la reserva:",
        f"   • Código: RES-{reservation.id}",
        f"   • Huéspedes: {reservation.guests}",
        f"   • Habitación: {reservation.room.name}",
        f"   • Check-in: {reservation.check_in}",
        f"   • Check-out: {reservation.check_out}",
        f"",
        f"💰 Impacto financiero:",
        f"   • Total pagado: ${total_paid}",
        f"   • Penalidad aplicada: ${penalty_amount}",
        f"   • Reembolso: ${refund_amount}",
        f"   • Pérdida neta: ${net_loss}",
        f"",
        f"📝 Acciones requeridas:",
    ]
    
    if refund_amount > 0:
        message_parts.append(f"   • Procesar reembolso de ${refund_amount}")
    
    message_parts.extend([
        f"   • Actualizar estadísticas de NO_SHOW",
        f"   • Revisar política de cancelación si es necesario",
        f"",
        f"⏰ Procesado automáticamente el {reservation.updated_at.strftime('%d/%m/%Y a las %H:%M')}"
    ])
    
    return "\n".join(message_parts)
```

##### Notificación para el Huésped
```python
def _create_guest_notification_message(reservation, penalty_amount, refund_amount, total_paid):
    """
    Crea mensaje detallado para notificación del huésped
    """
    message_parts = [
        f"❌ SU RESERVA FUE MARCADA COMO NO_SHOW",
        f"",
        f"📋 Detalles de su reserva:",
        f"   • Código: RES-{reservation.id}",
        f"   • Hotel: {reservation.hotel.name}",
        f"   • Habitación: {reservation.room.name}",
        f"   • Fecha de llegada: {reservation.check_in}",
        f"   • Fecha de salida: {reservation.check_out}",
        f"",
        f"💰 Información financiera:",
        f"   • Total pagado: ${total_paid}",
        f"   • Penalidad aplicada: ${penalty_amount}",
    ]
    
    if refund_amount > 0:
        message_parts.extend([
            f"   • Reembolso disponible: ${refund_amount}",
            f"",
            f"✅ PRÓXIMOS PASOS:",
            f"   • Su reembolso será procesado según la política del hotel",
            f"   • Recibirá más información por email",
            f"   • El proceso puede tomar hasta 30 días hábiles"
        ])
    else:
        message_parts.extend([
            f"   • Reembolso: $0.00",
            f"",
            f"ℹ️ INFORMACIÓN:",
            f"   • No se aplica reembolso según la política de NO_SHOW",
            f"   • La penalidad corresponde al 100% del monto pagado",
            f"   • Contacte al hotel para más información"
        ])
    
    return "\n".join(message_parts)
```

#### Métodos de Procesamiento de Reembolsos NO_SHOW

##### Voucher de Crédito
```python
def _process_voucher_refund(refund, amount):
    """Procesa reembolso como voucher de crédito"""
    refund.mark_as_processing()
    refund.notes += " - Voucher pendiente de generación"
    refund.save()
    
    return {
        'refund_id': refund.id,
        'method': 'voucher',
        'amount': float(amount),
        'status': 'processing',
        'voucher_type': 'credit',
        'expiry_days': 365,  # Vouchers de NO_SHOW con validez extendida
        'requires_manual_processing': True
    }
```

##### Transferencia Bancaria
```python
def _process_bank_transfer_refund(refund, amount):
    """Procesa reembolso como transferencia bancaria"""
    refund.status = RefundStatus.PENDING
    refund.notes += " - Transferencia bancaria pendiente"
    refund.save()
    
    return {
        'refund_id': refund.id,
        'method': 'bank_transfer',
        'amount': float(amount),
        'status': 'pending',
        'requires_manual_processing': True,
        'requires_guest_data': True
    }
```

#### Beneficios de las Mejoras NO_SHOW v2.0

##### Para el Hotel
- ✅ **Penalidades automáticas** según políticas de cancelación
- ✅ **Reembolsos específicos** para NO_SHOW con configuraciones diferenciadas
- ✅ **Notificaciones detalladas** con información financiera completa
- ✅ **Múltiples métodos** de reembolso (voucher, transferencia, pago original)
- ✅ **Configuraciones flexibles** por hotel y política
- ✅ **Logs detallados** de procesamiento y penalidades
- ✅ **Trazabilidad completa** del flujo financiero

##### Para el Personal
- ✅ **Procesamiento automático** de penalidades y reembolsos
- ✅ **Notificaciones diferenciadas** por tipo de usuario
- ✅ **Información financiera** clara y detallada
- ✅ **Acciones específicas** según el tipo de reembolso
- ✅ **Configuración granular** de políticas NO_SHOW

##### Para el Huésped
- ✅ **Transparencia total** en penalidades y reembolsos
- ✅ **Información detallada** de la reserva y consecuencias
- ✅ **Próximos pasos claros** según el tipo de reembolso
- ✅ **Múltiples opciones** de reembolso disponibles
- ✅ **Tiempos de procesamiento** claros y realistas

### Tipos de Notificación y Colores

| Tipo | Color | Icono | Descripción |
|------|-------|-------|-------------|
| `auto_cancel` | 🔴 Rojo | XCircleIcon | Reservas canceladas automáticamente |
| `no_show` | 🟣 Púrpura | ExclamationTriangleIcon | Reservas marcadas como no-show |
| `refund_auto` | 🟡 Amarillo | CheckCircleIcon | Reembolsos procesados exitosamente |
| `refund_failed` | 🟠 Naranja | XCircleIcon | Reembolsos que fallaron |

### Ejemplo de Notificación
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "auto_cancel",
  "title": "Reserva cancelada automáticamente",
  "message": "La reserva #RES-123 en Hotel Central fue cancelada automáticamente. Motivo: Depósito vencido sin pago (vencía: 2024-01-15)",
  "user": null,
  "is_read": false,
  "created_at": "2024-01-16T08:30:00Z",
  "hotel_id": 1,
  "reservation_id": 123,
  "metadata": {
    "reservation_code": "RES-123",
    "hotel_name": "Hotel Central",
    "reason": "Depósito vencido sin pago (vencía: 2024-01-15)"
  }
}
```

### Beneficios del Sistema

#### Para el Negocio
- **Visibilidad completa** de eventos automáticos
- **Trazabilidad** de acciones del sistema
- **Alertas inmediatas** sobre situaciones críticas
- **Historial centralizado** de notificaciones

#### Para los Usuarios
- **Interfaz intuitiva** con campanita en header
- **Información contextual** completa
- **Gestión fácil** de notificaciones
- **Filtros avanzados** para encontrar información específica

#### Para el Desarrollo
- **Arquitectura escalable** con UUIDs
- **Integración simple** con procesos existentes
- **API REST completa** para futuras integraciones
- **Frontend reactivo** con polling automático

---

## 3.13 Módulo Invoicing (Facturación Electrónica Argentina)

**Propósito**: Gestión completa de facturación electrónica argentina con integración AFIP WSFEv1 para cumplimiento fiscal.

### Modelos Principales

#### AfipConfig
Configuración de AFIP por hotel:
```python
class AfipConfig(models.Model):
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE)
    cuit = models.CharField(max_length=11, validators=[validate_cuit])
    tax_condition = models.CharField(max_length=2, choices=TaxCondition.choices)
    point_of_sale = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(9999)])
    certificate_path = models.CharField(max_length=500)
    private_key_path = models.CharField(max_length=500)
    environment = models.CharField(max_length=20, choices=AfipEnvironment.choices)
    last_invoice_number = models.PositiveIntegerField(default=0)
    last_cae_date = models.DateTimeField(null=True, blank=True)
    
    # Token de Acceso (WSAA) - Persistencia para reutilización
    afip_token = models.TextField(blank=True)
    afip_sign = models.TextField(blank=True)
    afip_token_generation = models.DateTimeField(null=True, blank=True)
    afip_token_expiration = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

#### Invoice
Factura electrónica:
```python
class Invoice(models.Model):
    # Identificadores únicos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relaciones principales
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="invoices")
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="invoices", null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="invoices")
    related_invoice = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="related_documents")
    
    # Datos de la factura
    type = models.CharField(max_length=2, choices=InvoiceType.choices)
    number = models.CharField(max_length=13, help_text="Número formateado (0001-00001234)")
    issue_date = models.DateField()
    
    # Datos del CAE (Código de Autorización Electrónico)
    cae = models.CharField(max_length=14, blank=True)
    cae_expiration = models.DateField(null=True, blank=True)
    
    # Montos
    total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ARS")
    
    # Estado y control
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    
    # Archivos y respuestas
    pdf_file = models.FileField(upload_to='invoices/pdf/%Y/%m/%d/', null=True, blank=True)
    pdf_url = models.URLField(blank=True)
    afip_response = models.JSONField(default=dict, blank=True)
    
    # Datos del cliente (snapshot al momento de la facturación)
    client_name = models.CharField(max_length=200)
    client_document_type = models.CharField(max_length=2, default="96")
    client_document_number = models.CharField(max_length=20)
    client_tax_condition = models.CharField(max_length=2, choices=TaxCondition.choices, default=TaxCondition.CONSUMIDOR_FINAL)
    client_address = models.TextField(blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Control de errores y reintentos
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    sent_to_afip_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
```

#### InvoiceItem
Items de la factura:
```python
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    
    # Descripción del item
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Cálculos automáticos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('21.00'))
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Códigos AFIP
    afip_code = models.CharField(max_length=20, default="1")
```

### Enums y Tipos

#### TaxCondition
Condiciones de IVA según AFIP:
```python
class TaxCondition(models.TextChoices):
    RESPONSABLE_INSCRIPTO = "1", "Responsable Inscripto"
    CONSUMIDOR_FINAL = "5", "Consumidor Final"
    EXENTO = "6", "Exento"
    NO_RESPONSABLE = "7", "No Responsable"
    MONOTRIBUTO = "8", "Monotributo"
    MONOTRIBUTO_SOCIAL = "9", "Monotributo Social"
```

#### AfipEnvironment
Ambientes de AFIP:
```python
class AfipEnvironment(models.TextChoices):
    TEST = "test", "Testing"
    PRODUCTION = "production", "Producción"
```

### Enums y Tipos

#### InvoiceType
```python
class InvoiceType(models.TextChoices):
    A = 'A', 'Factura A (Responsables Inscriptos)'
    B = 'B', 'Factura B (Consumidores Finales)'
    C = 'C', 'Factura C (Exentos)'
    E = 'E', 'Factura E (Exportación)'
    NC = 'NC', 'Nota de Crédito'
    ND = 'ND', 'Nota de Débito'
```

#### InvoiceStatus
```python
class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    SENT = 'sent', 'Enviada a AFIP'
    APPROVED = 'approved', 'Aprobada'
    ERROR = 'error', 'Error'
```

### Servicios AFIP

#### AfipAuthService
Servicio de autenticación con AFIP WSAA:
```python
class AfipAuthService:
    def __init__(self, config: AfipConfig):
        self.config = config
        self.wsaa_url = self.WSAA_PRODUCTION_URL if config.environment == 'production' else self.WSAA_HOMOLOGATION_URL
        self.token_cache_key = f"afip_token_{config.hotel.id}_{config.environment}"
        self.sign_cache_key = f"afip_sign_{config.hotel.id}_{config.environment}"
    
    def get_token_and_sign(self) -> Tuple[str, str]:
        """Obtiene token y sign válidos para AFIP con persistencia en BD"""
        # 1) Verificar cache Redis
        # 2) Verificar persistencia en BD (no expirado)
        # 3) Generar nuevo token si es necesario
        # 4) Persistir en BD y cache
        
    def _generate_new_token(self) -> Tuple[str, str, datetime, datetime]:
        """Genera nuevo token con ventana TRA ±10 minutos"""
        
    def _create_login_xml(self) -> str:
        """Crea TRA con ventana de tiempo según manual AFIP"""
        
    def _sign_xml(self, xml_content: str) -> str:
        """Firma XML con PKCS#7 no-detached SHA256"""
        
    def _parse_login_response(self, response_xml: str) -> Tuple[str, str, datetime, datetime]:
        """Parsea respuesta AFIP con manejo de Faults"""
        
    def clear_cache(self):
        """Limpia el cache de tokens"""
        
    def is_token_valid(self) -> bool:
        """Verifica si el token actual es válido"""
```

**Características:**
- **Autenticación con certificados digitales** PKCS#7 no-detached SHA256
- **Persistencia de TA en BD** para reutilización automática
- **Cache Redis** con TTL hasta expiración del TA
- **Manejo inteligente de Faults** - reutiliza TA vigente si existe
- **Ventana TRA ±10 minutos** según manual AFIP
- **SOAPAction correcto** (urn:LoginCms)
- **Parsing robusto** con des-escape HTML y fallback base64
- **Soporte completo** para homologación y producción

#### AfipInvoiceService
Servicio principal de emisión de facturas:
```python
class AfipInvoiceService:
    def __init__(self, config: AfipConfig):
        self.config = config
        self.wsfev1_url = self.WSFEv1_PRODUCTION_URL if config.environment == 'production' else self.WSFEv1_HOMOLOGATION_URL
    
    def send_invoice(self, invoice: Invoice) -> Dict:
        """Envía factura a AFIP y obtiene CAE"""
        
    def _validate_invoice(self, invoice: Invoice):
        """Valida la factura antes del envío"""
        
    def _build_invoice_xml(self, invoice: Invoice, token: str, sign: str) -> str:
        """Construye el XML de la factura para AFIP"""
        
    def _process_afip_response(self, response_xml: str, invoice: Invoice) -> Dict:
        """Procesa la respuesta de AFIP"""
```

**Características:**
- Construcción automática de XML WSFEv1
- Validaciones de negocio completas
- Manejo de todos los tipos de comprobante (A, B, C, E, NC, ND)
- Procesamiento de respuestas AFIP
- Actualización automática de facturas con CAE

#### InvoicePDFService
Servicio de generación de PDFs fiscales con CAE:
```python
class InvoicePDFService:
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 2 * cm
        
    def generate_pdf(self, invoice) -> str:
        """Genera PDF fiscal con CAE y datos AFIP"""
        
    def _build_pdf_content(self, invoice) -> list:
        """Construye el contenido del PDF"""
        
    def _generate_qr_code(self, invoice) -> Optional[Image]:
        """Genera código QR con datos AFIP"""
        
    def _build_qr_data(self, invoice) -> str:
        """Construye datos para código QR según normativas AFIP"""
        
    def _create_items_table(self, invoice) -> Table:
        """Crea tabla de items de la factura"""
        
    def _create_totals_table(self, invoice) -> Table:
        """Crea tabla de totales"""
```

**Características:**
- Generación de PDFs fiscales completos con ReportLab
- Inclusión de logo del hotel
- Datos fiscales del emisor (CUIT, domicilio, condición IVA)
- Datos del comprador (nombre, documento, domicilio)
- Detalle de servicios con IVA desglosado
- CAE y fecha de vencimiento
- Código QR para verificación AFIP
- Formato profesional y cumplimiento normativo argentino

**Elementos del PDF:**
- **Header**: Logo del hotel y título del comprobante
- **Datos del Emisor**: Razón social, CUIT, domicilio, condición IVA
- **Datos del Comprador**: Nombre, documento, domicilio
- **Datos de la Factura**: Número, fecha, moneda, estado
- **Detalle de Items**: Tabla con servicios, cantidades, precios, IVA
- **Totales**: Subtotal, IVA, total final
- **Autorización AFIP**: CAE, fecha de vencimiento, fecha de autorización
- **Código QR**: Link de verificación AFIP con todos los datos
- **Footer**: Información del sistema y fecha de generación

**Dependencias:**
```python
# requirements.txt
qrcode==7.4.2
Pillow==12.0.0
reportlab==4.0.7
cryptography>=41.0.0
requests>=2.31.0
```

### Funcionalidad de Señas (Pagos Parciales)

#### Descripción
El sistema soporta pagos parciales (señas) con integración completa a la facturación electrónica argentina. Permite configurar diferentes modos de facturación según las necesidades del hotel.

#### Características Principales
- **Cálculo Automático**: Usa `PaymentPolicy` para calcular montos de seña
- **Dos Modos de Facturación**: Solo recibos o facturación AFIP en seña
- **Múltiples Pagos por Factura**: Soporte para vincular señas + pago final
- **Validaciones Inteligentes**: Montos, estados de reserva, configuración AFIP
- **Integración Celery**: Generación automática de PDFs y emails

#### Modelos Extendidos

##### Payment (Campos para Señas)
```python
class Payment(models.Model):
    # ... campos existentes ...
    
    # Campos para señas (pagos parciales)
    is_deposit = BooleanField(default=False)     # Indica si es una seña
    metadata = JSONField(default=dict)           # Metadatos adicionales
```

##### Invoice (Soporte para Múltiples Pagos)
```python
class Invoice(models.Model):
    # ... campos existentes ...
    
    payment = ForeignKey(Payment, ...)           # Pago principal (compatibilidad)
    payments_data = JSONField(default=list)      # Lista de IDs de pagos
```

##### AfipConfig (Modos de Facturación)
```python
class AfipConfig(models.Model):
    # ... campos existentes ...
    
    invoice_mode = CharField(
        max_length=20,
        choices=InvoiceMode.choices,
        default=InvoiceMode.RECEIPT_ONLY
    )

class InvoiceMode(models.TextChoices):
    RECEIPT_ONLY = "receipt_only", "Solo Recibos"
    FISCAL_ON_DEPOSIT = "fiscal_on_deposit", "Facturación en Seña"
```

#### Servicios de Cálculo

##### calculate_deposit()
```python
def calculate_deposit(policy, total_amount):
    """
    Calcula el monto del depósito según la política de pago
    
    Args:
        policy: PaymentPolicy instance
        total_amount: Decimal - Monto total de la reserva
    
    Returns:
        dict: Información del depósito
    """
    if not policy or policy.deposit_type == PaymentPolicy.DepositType.NONE:
        return {
            'required': False,
            'amount': Decimal('0.00'),
            'percentage': 0,
            'type': 'none'
        }

    amount = Decimal('0.00')
    if policy.deposit_type == PaymentPolicy.DepositType.PERCENTAGE:
        amount = (total_amount * policy.deposit_value) / 100
    elif policy.deposit_type == PaymentPolicy.DepositType.FIXED:
        amount = policy.deposit_value

    return {
        'required': True,
        'amount': amount.quantize(Decimal('0.01')),
        'percentage': policy.deposit_type == PaymentPolicy.DepositType.PERCENTAGE and policy.deposit_value or 0,
        'type': policy.deposit_type,
        'due': policy.deposit_due,
        'days_before': policy.deposit_days_before,
        'balance_due': policy.balance_due
    }
```

#### Flujos de Trabajo

##### Flujo 1: Solo Recibos (receipt_only)
1. **Crear Seña**: Genera recibo PDF, no envía a AFIP
2. **Pago Final**: Genera recibo PDF, no envía a AFIP  
3. **Factura Final**: Genera factura AFIP con CAE incluyendo todos los pagos

##### Flujo 2: Facturación en Seña (fiscal_on_deposit)
1. **Crear Seña**: Genera factura AFIP con CAE para el monto de la seña
2. **Pago Final**: Genera recibo PDF
3. **Nota de Crédito**: Genera nota de crédito o factura complementaria

#### Serializers

##### CreateDepositSerializer
```python
class CreateDepositSerializer(serializers.Serializer):
    reservation_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    method = serializers.CharField(max_length=30, default='cash')
    send_to_afip = serializers.BooleanField(default=False)
    notes = serializers.CharField(max_length=500, required=False)
    
    def validate_reservation_id(self, value):
        # Validar que la reserva exista y esté en estado válido
        # Estados válidos: 'pending', 'confirmed'
    
    def validate_amount(self, value):
        # Validar que el monto sea positivo
```

##### GenerateInvoiceFromPaymentSerializer (Extendido)
```python
class GenerateInvoiceFromPaymentSerializer(serializers.Serializer):
    # ... campos existentes ...
    reference_payments = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Lista de IDs de pagos a incluir en la factura"
    )
    
    def validate_reference_payments(self, value):
        # Validar que los pagos existan y pertenezcan a la misma reserva
```

### APIs y Endpoints

#### **AfipConfigViewSet**
```python
# GET /api/invoicing/afip-configs/
# POST /api/invoicing/afip-configs/
# GET /api/invoicing/afip-configs/{id}/
# PUT /api/invoicing/afip-configs/{id}/
# DELETE /api/invoicing/afip-configs/{id}/
```

#### **TestCertificateValidationView**
```python
# POST /api/invoicing/test/certificates/validate/
# Valida certificados digitales AFIP
```

#### **TestAfipConnectionView**
```python
# POST /api/invoicing/test/afip/connection/
# Prueba conexión real con AFIP WSAA
```

#### **TestInvoiceGenerationView**
```python
# POST /api/invoicing/test/invoices/generate/
# Genera factura de prueba con datos mock
```

#### **TestAfipStatusView**
```python
# GET /api/invoicing/test/afip/status/
# Obtiene estado de servicios AFIP
```

#### **ListCertificatesView**
```python
# GET /api/invoicing/certificates/list/
# Lista certificados disponibles en /app/certs/
```

#### **Endpoints de Señas (Pagos Parciales)**

##### **create_deposit**
```python
# POST /api/payments/create-deposit/
# Crear una seña/depósito para una reserva

# Request Body:
{
    "reservation_id": 123,
    "amount": 1000.00,
    "method": "cash",
    "send_to_afip": false,
    "notes": "Seña del 50%"
}

# Response:
{
    "message": "Seña creada exitosamente",
    "payment": {
        "id": 456,
        "reservation_id": 123,
        "hotel_name": "Hotel Test",
        "amount": "1000.00",
        "method": "cash",
        "is_deposit": true,
        "status": "approved",
        "receipt_pdf_url": "https://example.com/receipt.pdf",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "deposit_info": {
        "required": true,
        "amount": "1000.00",
        "percentage": 50,
        "type": "percentage",
        "due": "confirmation",
        "balance_due": "check_in"
    }
}
```

##### **generate_invoice_from_payment_extended**
```python
# POST /api/payments/generate-invoice-from-payment/{payment_id}/
# Generar factura desde pago con soporte para múltiples pagos

# Request Body:
{
    "send_to_afip": true,
    "reference_payments": [123, 124, 125],
    "customer_name": "Juan Pérez",
    "customer_document_type": "DNI",
    "customer_document_number": "12345678",
    "customer_address": "Calle Falsa 123",
    "customer_city": "Buenos Aires",
    "customer_postal_code": "1000",
    "customer_country": "Argentina"
}

# Response:
{
    "message": "Factura generada exitosamente",
    "invoice": {
        "id": "uuid-factura",
        "number": "0001-00000001",
        "total": "4000.00",
        "status": "approved",
        "cae": "12345678901234",
        "payments_included": [123, 124, 125],
        "total_payments": 3
    }
}
```

##### **generate-from-payment (Invoicing)**
```python
# POST /api/invoicing/invoices/generate-from-payment/{payment_id}/
# Endpoint extendido en módulo de facturación con soporte para múltiples pagos

# Request Body:
{
    "send_to_afip": true,
    "reference_payments": [123, 124, 125],
    "customer_name": "Juan Pérez",
    "customer_document_type": "DNI",
    "customer_document_number": "12345678"
}

# Response:
{
    "id": "uuid-factura",
    "number": "0001-00000001",
    "total": "4000.00",
    "status": "approved",
    "cae": "12345678901234",
    "payments_included": [123, 124, 125],
    "total_payments": 3
}
```

### Configuraciones y Políticas

#### **Configuración de Ambiente**
```python
# settings.py
AFIP_SETTINGS = {
    'WSAA_HOMOLOGATION_URL': 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms',
    'WSAA_PRODUCTION_URL': 'https://wsaa.afip.gov.ar/ws/services/LoginCms',
    'WSFEv1_HOMOLOGATION_URL': 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx',
    'WSFEv1_PRODUCTION_URL': 'https://servicios1.afip.gov.ar/wsfev1/service.asmx',
    'CACHE_TIMEOUT': 11 * 60 * 60,  # 11 horas
    'RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 5,  # segundos
}
```

#### **Políticas de Reintento**
- **Errores temporales**: 3 reintentos con delay de 5 segundos
- **Errores de certificado**: No reintentar, requiere intervención manual
- **Errores de TA**: Reutilizar TA persistido si está vigente
- **Timeout**: 60 segundos para requests a AFIP

#### **Validaciones de Negocio**
- **CUIT**: 11 dígitos numéricos con validación de dígito verificador
- **Punto de venta**: Entre 1 y 9999
- **Montos**: Positivos, máximo 12 dígitos, 2 decimales
- **Fechas**: No futuras, formato ISO-8601
- **Documentos**: Validación según tipo (DNI, CUIT, etc.)

### Integraciones

#### **Integración con Reservas**
```python
# apps/reservations/signals.py
@receiver(post_save, sender=Payment)
def generate_invoice_on_payment(sender, instance, created, **kwargs):
    if instance.status == PaymentStatus.COMPLETED:
        InvoiceService.generate_from_payment(instance)
```

#### **Integración con Notificaciones**
```python
# apps/notifications/tasks.py
@shared_task
def notify_invoice_generated(invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    NotificationService.send_invoice_notification(invoice)
```

#### **Integración con Email**
```python
# apps/invoicing/services/email_service.py
class InvoiceEmailService:
    def send_invoice_email(self, invoice: Invoice):
        # Envía PDF por email al cliente
        pass
```

### Flujos de Trabajo Principales

#### **1. Configuración Inicial**
1. **Obtener certificado** desde WSASS/AFIP
2. **Configurar AfipConfig** con datos del hotel
3. **Probar conexión** con AFIP
4. **Autorizar servicios** en AFIP
5. **Activar facturación** automática

#### **2. Generación de Factura**
1. **Trigger**: Pago completado o acción manual
2. **Validación**: Datos del cliente y reserva
3. **Creación**: Invoice en estado DRAFT
4. **Autenticación**: Obtener TA de AFIP
5. **Envío**: XML a WSFEv1
6. **Procesamiento**: Respuesta y CAE
7. **PDF**: Generación de documento fiscal
8. **Notificación**: Email al cliente

#### **3. Manejo de Errores**
1. **Detección**: Error en cualquier paso
2. **Clasificación**: Temporal vs permanente
3. **Reintento**: Si es temporal (hasta 3 veces)
4. **Notificación**: Alerta al administrador
5. **Logging**: Registro detallado para diagnóstico

### Consideraciones de Seguridad

#### **Certificados Digitales**
- **Almacenamiento**: Archivos en `/app/certs/` con permisos restringidos
- **Transmisión**: Solo por HTTPS
- **Backup**: Respaldo seguro de certificados
- **Rotación**: Renovación antes del vencimiento

#### **Tokens de Acceso**
- **Cache**: Redis con TTL automático
- **Persistencia**: Encriptados en base de datos
- **Reutilización**: Solo si están vigentes
- **Limpieza**: Automática al expirar

#### **Datos Sensibles**
- **CUIT**: Encriptado en logs
- **Montos**: Validación de rangos
- **Documentos**: Validación de formato
- **Emails**: Verificación de dominio

### Monitoreo y Logging

#### **Métricas Clave**
- **Facturas emitidas**: Por día/semana/mes
- **Tasa de éxito**: % de facturas aprobadas
- **Tiempo de respuesta**: AFIP response time
- **Errores**: Por tipo y frecuencia

#### **Logs Estructurados**
```python
logger.info("AFIP invoice generated", extra={
    'invoice_id': invoice.id,
    'cuit': config.cuit,
    'total': invoice.total,
    'cae': invoice.cae,
    'duration_ms': duration
})
```

#### **Alertas Automáticas**
- **Conexión AFIP**: Fallas de conectividad
- **Certificados**: Próximos a vencer
- **Errores**: Tasa alta de fallos
- **Límites**: Numeración próxima a agotar

### Testing y Desarrollo

#### **Ambiente de Testing**
- **WSASS**: Para obtener certificados de prueba
- **Datos mock**: Para desarrollo sin AFIP
- **Validaciones**: Tests unitarios completos
- **Integración**: Tests end-to-end

#### **Comandos de Testing**
```bash
# Probar conexión AFIP
python manage.py test_afip_connection

# Generar factura de prueba
python manage.py test_invoice_generation

# Validar certificados
python manage.py validate_certificates
```

### Migraciones y Actualizaciones

#### **Migración de Datos**
```python
# 0003_afipconfig_afip_sign_afipconfig_afip_token_and_more.py
class Migration(migrations.Migration):
    operations = [
        migrations.AddField('AfipConfig', 'afip_token', models.TextField(blank=True)),
        migrations.AddField('AfipConfig', 'afip_sign', models.TextField(blank=True)),
        migrations.AddField('AfipConfig', 'afip_token_generation', models.DateTimeField(null=True, blank=True)),
        migrations.AddField('AfipConfig', 'afip_token_expiration', models.DateTimeField(null=True, blank=True)),
        migrations.AddIndex('AfipConfig', 'afip_token_expiration', models.Index(fields=['afip_token_expiration'])),
    ]
```

#### **Actualizaciones de Certificados**
1. **Backup**: Respaldo de configuración actual
2. **Nuevo certificado**: Generar CSR y obtener de AFIP
3. **Actualización**: Cambiar rutas en AfipConfig
4. **Prueba**: Verificar conexión
5. **Activación**: Cambiar a producción si es necesario

---

#### AfipTestService
Servicio para testing en ambiente de homologación:
```python
class AfipTestService(AfipInvoiceService):
    def __init__(self, config: AfipConfig):
        if config.environment != 'test':
            raise ValueError("AfipTestService solo puede usarse con configuraciones en modo test")
        super().__init__(config)
    
    def send_test_invoice(self, invoice: Invoice) -> Dict:
        """Envía factura de prueba a AFIP homologación"""
        
    def test_afip_connection(self) -> Dict:
        """Prueba la conexión con AFIP homologación"""
        
    def create_test_invoice_data(self, hotel: Hotel, reservation=None) -> Dict:
        """Crea datos de prueba para una factura"""
        
    def get_test_parameters(self) -> Dict:
        """Obtiene los parámetros de testing recomendados"""
        
    def validate_test_environment(self) -> Dict:
        """Valida que el ambiente de testing esté configurado correctamente"""
```

**Características:**
- Validaciones específicas para testing
- Datos de prueba predefinidos
- Validación de ambiente de homologación
- Parámetros de testing recomendados

#### AfipService (Servicio Unificado)
Servicio principal que unifica todos los servicios AFIP:
```python
class AfipService:
    def __init__(self, config: AfipConfig):
        self.config = config
        self.is_production = config.environment == 'production'
        self.auth_service = AfipAuthService(config)
        
        if self.is_production:
            self.invoice_service = AfipInvoiceService(config)
            self.test_service = None
        else:
            self.invoice_service = AfipTestService(config)
            self.test_service = AfipTestService(config)
    
    def send_invoice(self, invoice: Invoice) -> Dict:
        """Envía factura a AFIP (producción o test)"""
        
    def test_connection(self) -> Dict:
        """Prueba la conexión con AFIP"""
        
    def validate_environment(self) -> Dict:
        """Valida la configuración del ambiente"""
        
    def get_service_info(self) -> Dict:
        """Obtiene información sobre el servicio AFIP"""
        
    def clear_auth_cache(self):
        """Limpia el cache de autenticación"""
        
    def get_test_parameters(self) -> Optional[Dict]:
        """Obtiene parámetros de testing (solo en modo test)"""
```

**Características:**
- Interfaz unificada para todos los servicios
- Selección automática entre producción y test
- Gestión centralizada de configuración
- Métodos de utilidad comunes

#### InvoiceGeneratorService
Servicio para generación de PDFs de facturas:
```python
class InvoiceGeneratorService:
    def generate_pdf(self, invoice: Invoice) -> str:
        """Genera PDF de la factura"""
        
    def get_invoice_template(self, invoice: Invoice) -> str:
        """Obtiene template HTML para la factura"""
```

### URLs y Endpoints AFIP

#### URLs de Producción
- **WSAA**: `https://servicios1.afip.gov.ar/wsaa/service.asmx`
- **WSFEv1**: `https://servicios1.afip.gov.ar/wsfev1/service.asmx`

#### URLs de Homologación
- **WSAA**: `https://wswhomo.afip.gov.ar/wsaa/service.asmx`
- **WSFEv1**: `https://wswhomo.afip.gov.ar/wsfev1/service.asmx`

### Códigos AFIP

#### Tipos de Comprobante
```python
INVOICE_TYPE_CODES = {
    'A': 1,    # Factura A
    'B': 6,    # Factura B
    'C': 11,   # Factura C
    'E': 19,   # Factura E
    'NC': 3,   # Nota de Crédito
    'ND': 2,   # Nota de Débito
}
```

#### Tipos de Documento
```python
DOCUMENT_TYPE_CODES = {
    'DNI': 96,
    'CUIT': 80,
    'CUIL': 86,
    'PASAPORTE': 94,
    'OTRO': 99,
}
```

### Manejo de Errores

#### Excepciones Personalizadas
```python
class AfipAuthError(Exception):
    """Error de autenticación AFIP"""

class AfipInvoiceError(Exception):
    """Error de facturación AFIP"""

class AfipTestError(Exception):
    """Error de testing AFIP"""

class AfipServiceError(Exception):
    """Error del servicio AFIP"""
```

#### Logging
- **Nivel INFO**: Operaciones exitosas
- **Nivel WARNING**: Situaciones que requieren atención
- **Nivel ERROR**: Errores que impiden el funcionamiento
- **Nivel DEBUG**: Información detallada para debugging

### Configuración de Dependencias

#### requirements.txt
```bash
# Dependencias para AFIP
cryptography>=41.0.0
lxml>=4.9.0
requests>=2.31.0
# Dependencias para PDFs y QR
qrcode==7.4.2
Pillow==12.0.0
reportlab==4.0.7
```

#### Variables de Entorno
```bash
# Configuración AFIP
AFIP_TEST_MODE=true
AFIP_CERTIFICATE_PATH=/path/to/cert.crt
AFIP_PRIVATE_KEY_PATH=/path/to/key.key
INVOICE_MAX_RETRIES=3
INVOICE_RETRY_DELAY=300
```

### Ejemplo de Uso

#### Configuración Básica
```python
from apps.invoicing.services import AfipService
from apps.invoicing.models import AfipConfig

# Obtener configuración
config = AfipConfig.objects.get(hotel=hotel)

# Crear servicio
afip_service = AfipService(config)

# Probar conexión
result = afip_service.test_connection()
if result['success']:
    print("Conexión exitosa con AFIP")
else:
    print(f"Error: {result['message']}")
```

#### Envío de Factura
```python
# Enviar factura
result = afip_service.send_invoice(invoice)

if result['success']:
    print(f"CAE: {result['cae']}")
    print(f"Vencimiento: {result['cae_expiration']}")
else:
    print(f"Error: {result['message']}")
```

#### Testing
```python
# Solo en modo test
if not afip_service.is_production:
    test_params = afip_service.get_test_parameters()
    print(f"Tipos de documento: {test_params['document_types']}")
    
    # Crear datos de prueba
    test_data = afip_service.test_service.create_test_invoice_data(hotel)
```

#### Generación de PDF Fiscal
```python
from apps.invoicing.services import InvoicePDFService
from apps.invoicing.models import Invoice

# Obtener factura aprobada
invoice = Invoice.objects.get(id=invoice_id, status='approved')

# Crear servicio de PDF
pdf_service = InvoicePDFService()

# Generar PDF fiscal
try:
    pdf_path = pdf_service.generate_pdf(invoice)
    print(f"PDF generado: {pdf_path}")
    
    # El PDF incluye:
    # - Logo del hotel
    # - Datos fiscales completos
    # - CAE y fecha de vencimiento
    # - Código QR para verificación AFIP
    # - Formato profesional
    
except InvoicePDFError as e:
    print(f"Error generando PDF: {e}")
```

#### Generación de PDF Simple (Sin CAE)
```python
from apps.invoicing.services import InvoiceGeneratorService
from apps.invoicing.models import Invoice

# Obtener factura en borrador
invoice = Invoice.objects.get(id=invoice_id, status='draft')

# Crear servicio de generación
generator = InvoiceGeneratorService()

# Generar PDF (automáticamente elige el tipo)
pdf_path = generator.generate_pdf(invoice)

# O generar PDF fiscal específicamente
if invoice.cae:
    pdf_path = generator.generate_fiscal_pdf(invoice)
    print(f"Cliente de prueba: {test_data['customer_name']}")
```

### APIs y Endpoints

#### Configuración AFIP
- `GET /api/invoicing/afip-configs/` - Listar configuraciones
- `POST /api/invoicing/afip-configs/` - Crear configuración
- `GET /api/invoicing/afip-configs/{id}/test-connection/` - Probar conexión

#### Facturas
- `GET /api/invoicing/invoices/` - Listar facturas
- `POST /api/invoicing/invoices/` - Crear factura
- `GET /api/invoicing/invoices/{id}/` - Obtener factura
- `POST /api/invoicing/invoices/{id}/send-to-afip/` - Enviar a AFIP
- `GET /api/invoicing/invoices/{id}/pdf/` - Obtener PDF
- `GET /api/invoicing/invoices/{id}/download-pdf/` - Descargar PDF
- `POST /api/invoicing/invoices/{id}/retry/` - Reintentar envío
- `POST /api/invoicing/invoices/{id}/cancel/` - Cancelar factura
- `GET /api/invoicing/invoices/{id}/summary/` - Resumen de factura
- `POST /api/invoicing/invoices/{id}/create-credit-note/` - Crear nota de crédito

#### Endpoints Específicos
- `POST /api/invoicing/invoices/generate-from-payment/{payment_id}/` - Generar factura desde pago
- `GET /api/invoicing/invoices/by-reservation/{reservation_id}/` - Facturas por reserva

#### Estado del Sistema
- `GET /api/invoicing/afip/status/` - Estado general de AFIP

### Tareas Celery

#### Programadas
```python
CELERY_BEAT_SCHEDULE = {
    "retry_failed_invoices_hourly": {
        "task": "apps.invoicing.tasks.retry_failed_invoices_task",
        "schedule": crontab(minute=15),
    },
    "cleanup_expired_invoices_daily": {
        "task": "apps.invoicing.tasks.cleanup_expired_invoices_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "validate_afip_connection_hourly": {
        "task": "apps.invoicing.tasks.validate_afip_connection_task",
        "schedule": crontab(minute=45),
    },
    "generate_daily_invoice_report": {
        "task": "apps.invoicing.tasks.generate_daily_invoice_report_task",
        "schedule": crontab(hour=23, minute=0),
    },
}
```

#### Manuales
```python
@shared_task
def send_invoice_to_afip_task(invoice_id: int) -> dict:
    """Envía factura a AFIP de forma asíncrona"""

@shared_task
def generate_invoice_pdf_task(invoice_id: int) -> str:
    """Genera PDF de factura de forma asíncrona"""

@shared_task
def retry_failed_invoices_task() -> dict:
    """Reintenta facturas fallidas automáticamente"""
```

### Configuración

#### Variables de Entorno
```bash
# Facturación
AUTO_GENERATE_INVOICE_PDF=true
AFIP_TEST_MODE=true
AFIP_CERTIFICATE_PATH=/path/to/cert.crt
AFIP_PRIVATE_KEY_PATH=/path/to/key.key
INVOICE_MAX_RETRIES=3
INVOICE_RETRY_DELAY=300
```

#### Django Settings
```python
INSTALLED_APPS = [
    # ... otras apps
    "apps.invoicing",
]

# URLs
urlpatterns = [
    # ... otras URLs
    path("api/invoicing/", include("apps.invoicing.urls")),
]
```

### Validaciones

#### Datos Obligatorios
- CUIT válido (11 dígitos)
- Punto de venta (1-9999)
- Datos del cliente completos
- Montos positivos
- Fechas válidas

#### Reglas de Negocio
- Una factura por reserva
- Numeración secuencial
- CAE no expirado
- Límite de reintentos

### Lógica de Negocio y Automatización

#### Señales Automáticas
El sistema utiliza señales de Django para automatizar la generación de facturas:

```python
# apps/invoicing/signals.py
@receiver(post_save, sender='payments.Payment')
def generate_invoice_on_payment_approved(sender, instance, created, **kwargs):
    """Genera automáticamente una factura cuando un pago es aprobado"""
    
@receiver(post_save, sender='payments.Refund')
def generate_credit_note_on_refund(sender, instance, created, **kwargs):
    """Genera automáticamente una nota de crédito cuando se crea un reembolso"""
```

#### Automatización de Facturas
**Trigger**: Cuando un `Payment` cambia a status `approved`
**Proceso**:
1. Verificar que no exista factura para el pago
2. Obtener configuración AFIP del hotel
3. Generar número de factura secuencial
4. Crear factura con datos del pago y reserva
5. Crear items por defecto basados en la reserva
6. Intentar envío automático a AFIP (opcional)
7. Generar PDF fiscal si es aprobada

#### Automatización de Notas de Crédito
**Trigger**: Cuando se crea un `Refund` con status `approved`
**Proceso**:
1. Verificar que exista factura para el pago original
2. Verificar que la factura esté aprobada
3. Obtener configuración AFIP del hotel
4. Generar número de nota de crédito secuencial
5. Crear nota de crédito vinculada a la factura original
6. Intentar envío automático a AFIP (opcional)

#### Endpoints de Generación Manual

##### Generar Factura desde Pago
```python
POST /api/invoicing/invoices/generate-from-payment/{payment_id}/
```
**Payload**:
```json
{
    "customer_name": "Juan Pérez",
    "customer_document_type": "DNI",
    "customer_document_number": "12345678",
    "customer_address": "Av. Corrientes 1234",
    "customer_city": "Buenos Aires",
    "send_to_afip": true,
    "items": [
        {
            "description": "Hospedaje - Suite Deluxe",
            "quantity": 2,
            "unit_price": 5000.00,
            "vat_rate": 21.00
        }
    ]
}
```

##### Listar Facturas por Reserva
```python
GET /api/invoicing/invoices/by-reservation/{reservation_id}/
```
**Query Parameters**:
- `type`: Filtrar por tipo de factura (A, B, C, E, NC, ND)
- `status`: Filtrar por estado (draft, sent, approved, error)

##### Crear Nota de Crédito
```python
POST /api/invoicing/invoices/{invoice_id}/create-credit-note/
```
**Payload**:
```json
{
    "total": 1000.00,
    "net_amount": 826.45,
    "vat_amount": 173.55,
    "reason": "Cancelación de reserva",
    "items": [
        {
            "description": "Reembolso - Factura 0001-00001234",
            "quantity": 1,
            "unit_price": 1000.00,
            "vat_rate": 21.00
        }
    ]
}
```

#### Serializers Especializados

##### GenerateInvoiceFromPaymentSerializer
```python
class GenerateInvoiceFromPaymentSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_document_type = serializers.ChoiceField(choices=[...], required=False)
    customer_document_number = serializers.CharField(max_length=20, required=False)
    customer_address = serializers.CharField(max_length=500, required=False)
    customer_city = serializers.CharField(max_length=100, required=False)
    customer_postal_code = serializers.CharField(max_length=20, required=False)
    customer_country = serializers.CharField(max_length=100, required=False, default='Argentina')
    issue_date = serializers.DateField(required=False)
    send_to_afip = serializers.BooleanField(default=False)
    items = InvoiceItemSerializer(many=True, required=False)
```

##### CreateCreditNoteSerializer
```python
class CreateCreditNoteSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    issue_date = serializers.DateField(required=False)
    reason = serializers.CharField(max_length=500, required=False)
    items = InvoiceItemSerializer(many=True, required=True)
```

#### Modelo Actualizado
Se agregó el campo `related_invoice` al modelo `Invoice`:

```python
class Invoice(models.Model):
    # ... otros campos ...
    related_invoice = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="related_documents",
        help_text="Factura original para notas de crédito/débito"
    )
```

### Flujo de Trabajo

1. **Configuración Inicial**
   - Crear configuración AFIP para el hotel
   - Subir certificados digitales
   - Configurar punto de venta
   - Probar conexión

2. **Creación de Factura**
   - Automática: Al aprobar un pago
   - Manual: Desde reserva existente
   - Completar datos del cliente
   - Seleccionar tipo de comprobante
   - Generar automáticamente

3. **Procesamiento**
   - Validación de datos
   - Envío a AFIP
   - Obtención de CAE
   - Generación de PDF
   - Notificación de resultado

4. **Notas de Crédito**
   - Automática: Al crear un reembolso
   - Manual: Desde factura existente
   - Vinculación con factura original
   - Procesamiento similar a facturas

4. **Gestión**
   - Consulta de estados
   - Reintentos automáticos
   - Reportes y análisis
   - Conciliación bancaria

### Seguridad

- Certificados digitales AFIP
- Validación de datos
- Logging completo
- Manejo de errores
- Idempotencia en envíos

### Testing

```bash
# Ejecutar tests
python manage.py test apps.invoicing

# Tests específicos
python manage.py test apps.invoicing.tests.AfipConfigModelTest
python manage.py test apps.invoicing.tests.InvoiceModelTest
```

### Monitoreo

#### Logs Importantes
- Envío a AFIP
- Errores de procesamiento
- Reintentos automáticos
- Generación de PDFs

#### Métricas
- Facturas procesadas
- Tasa de éxito
- Tiempo de procesamiento
- Errores por tipo

### 🧪 Testing, Homologación y Validación

#### **Suite de Testing Completa**

El módulo de facturación incluye una suite completa de testing con **35+ tests** que cubren todos los aspectos del sistema:

##### **Tests Unitarios** (`test_afip_services.py`)
- **TestAfipMockService**: 5 tests ✅
  - Mock de login WSAA
  - Mock de emisión de factura exitosa/error
  - Conversión de tipos de factura y documento
- **TestMockAfipAuthService**: 1 test ✅
  - Autenticación exitosa con mocks
- **TestMockAfipInvoiceService**: 2 tests ✅
  - Envío de factura y nota de crédito
- **TestAfipServiceIntegration**: 2 tests ✅
  - Uso de mocks en modo test
  - Alternancia entre ambientes
- **TestCaeValidation**: 2 tests ✅
  - Validación de formato y expiración de CAE
- **TestInvoiceNumbering**: 3 tests ✅
  - Generación, formato y numeración consecutiva

##### **Tests de Integración** (`test_integration.py`)
- **TestInvoiceGenerationFlow**: 2 tests ✅
  - Flujo completo de generación de factura
  - Flujo completo de generación de nota de crédito
- **TestPdfGenerationFlow**: 2 tests ✅
  - Generación de PDF con CAE
  - Error al generar PDF sin CAE
- **TestSignalsIntegration**: 2 tests ✅
  - Generación automática de factura al aprobar pago
  - Generación automática de nota de crédito al completar reembolso
- **TestEnvironmentSwitching**: 3 tests ✅
  - Configuración de ambientes test/producción
  - Validación de ambientes
- **TestDataValidation**: 3 tests ✅
  - Validación de datos de factura
  - Validación de CUIT y formatos

##### **Tests de Homologación** (`test_homologation.py`)
- **TestAfipHomologation**: 7 tests ✅
  - Configuración de ambiente de homologación
  - URLs de homologación AFIP
  - Autenticación WSAA en homologación
  - Emisión de factura en homologación
  - Tipos de factura (A, B, C, NC, ND)
  - Tipos de documento (DNI, CUIT, CUIL, Pasaporte)
  - Numeración consecutiva en homologación
  - Validación de CAE en homologación
- **TestProductionEnvironment**: 3 tests ✅
  - Configuración de ambiente de producción
  - URLs de producción
  - Validación de ambiente de producción
- **TestEnvironmentSwitching**: 2 tests ✅
  - Cambio de test a producción
  - Cambio de producción a test

#### **Servicios de Mocking**

##### **AfipMockService**
```python
class AfipMockService:
    """Servicio de mocking para respuestas de AFIP"""
    
    def mock_wsaa_login(self, cuit: str) -> Dict[str, Any]:
        """Simula la respuesta de login de WSAA"""
        
    def mock_wsfev1_invoice(self, invoice_data: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """Simula la respuesta de emisión de factura de WSFEv1"""
        
    def mock_wsfev1_credit_note(self, credit_note_data: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """Simula la respuesta de emisión de nota de crédito de WSFEv1"""
```

##### **MockAfipAuthService**
```python
class MockAfipAuthService(AfipAuthService):
    """Versión mock de AfipAuthService para testing"""
    
    def authenticate(self) -> Dict[str, Any]:
        """Mock de autenticación WSAA"""
```

##### **MockAfipInvoiceService**
```python
class MockAfipInvoiceService(AfipInvoiceService):
    """Versión mock de AfipInvoiceService para testing"""
    
    def send_invoice(self, invoice) -> Dict[str, Any]:
        """Mock de envío de factura a AFIP"""
        
    def send_credit_note(self, credit_note) -> Dict[str, Any]:
        """Mock de envío de nota de crédito a AFIP"""
```

#### **Configuración de Testing**

##### **Datos de Homologación AFIP**
```python
AFIP_TEST_CONFIG = {
    'TEST_CUIT': '20123456789',  # CUIT de prueba de AFIP
    'TEST_POINT_OF_SALE': 1,
    'WSAA_URL_TEST': 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms',
    'WSFEV1_URL_TEST': 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx',
    'WSAA_URL_PROD': 'https://wsaa.afip.gov.ar/ws/services/LoginCms',
    'WSFEV1_URL_PROD': 'https://servicios1.afip.gov.ar/wsfev1/service.asmx',
}
```

##### **Respuestas Mock de AFIP**
```python
AFIP_MOCK_RESPONSES = {
    'wsaa_login_success': {
        'loginCmsResponse': {
            'loginCmsReturn': {
                'token': 'test_token_123456789',
                'sign': 'test_sign_abcdefghij',
                'generationTime': '2025-01-01T00:00:00-03:00',
                'expirationTime': '2025-01-01T12:00:00-03:00'
            }
        }
    },
    'wsfev1_invoice_success': {
        'FECAESolicitarResponse': {
            'FECAESolicitarResult': {
                'FeCabResp': {'Resultado': 'A'},
                'FeDetResp': {
                    'FECAEDetResponse': [{
                        'Resultado': 'A',
                        'CAE': '12345678901234',
                        'CAEFchVto': 20250115
                    }]
                }
            }
        }
    }
}
```

#### **Test Runners**

##### **Ejecutor Comprehensivo** (`test_runner.py`)
```bash
# Tests unitarios rápidos
python test_runner.py quick

# Tests de integración
python test_runner.py integration

# Tests de homologación
python test_runner.py homologation

# Todos los tests
python test_runner.py comprehensive

# Test específico
python test_runner.py specific apps.invoicing.tests.test_afip_services.TestAfipMockService
```

##### **Comandos Django**
```bash
# Tests unitarios
docker compose exec backend python manage.py test apps.invoicing.tests.test_afip_services

# Tests de integración
docker compose exec backend python manage.py test apps.invoicing.tests.test_integration

# Tests de homologación
docker compose exec backend python manage.py test apps.invoicing.tests.test_homologation

# Todos los tests
docker compose exec backend python manage.py test apps.invoicing.tests
```

#### **Fixtures de Testing**

##### **Datos de Prueba** (`fixtures/afip_test_data.json`)
```json
{
  "test_configs": [
    {
      "name": "Homologación AFIP - Factura B",
      "cuit": "20123456789",
      "point_of_sale": 1,
      "environment": "test"
    }
  ],
  "test_invoices": [
    {
      "type": "B",
      "customer_name": "Cliente de Prueba",
      "customer_document_type": "DNI",
      "customer_document_number": "12345678",
      "total": 1000.00,
      "net_amount": 826.45,
      "vat_amount": 173.55
    }
  ],
  "expected_responses": {
    "wsaa_login_success": {
      "token": "test_token_homologation_123456789",
      "sign": "test_sign_homologation_abcdefghij"
    }
  }
}
```

#### **Validaciones Implementadas**

##### **Validación de CAE**
- **Formato**: 14 dígitos numéricos
- **Expiración**: Fecha válida y no expirada
- **Unicidad**: CAE único por factura
- **Estado**: Aprobado por AFIP

##### **Validación de Numeración**
- **Consecutiva**: Números secuenciales por punto de venta
- **Formato**: "0001-00001234" (punto-orden)
- **Rango**: 1-99999999 por punto de venta
- **Ambiente**: Separada por test/producción

##### **Validación de Datos**
- **CUIT**: 11 dígitos, dígito verificador válido
- **Documentos**: DNI (8), CUIT (11), CUIL (11), Pasaporte (variable)
- **Montos**: Positivos, decimales válidos
- **Fechas**: Válidas, no futuras para emisión

#### **Cobertura de Testing**

##### **Servicios AFIP** ✅
- Autenticación WSAA (mock y real)
- Emisión de facturas WSFEv1 (mock y real)
- Emisión de notas de crédito (mock y real)
- Manejo de errores y respuestas

##### **Modelos y Validaciones** ✅
- Modelo Invoice con todas sus validaciones
- Modelo AfipConfig con configuración por ambiente
- Modelo InvoiceItem con cálculos de IVA
- Validación de CAE y formatos
- Numeración consecutiva de facturas

##### **Endpoints REST** ✅
- Generación de facturas desde pagos
- Envío de facturas a AFIP
- Descarga de PDFs fiscales
- Listado de facturas por reserva
- Creación de notas de crédito

##### **Automatización** ✅
- Generación automática de facturas
- Generación automática de notas de crédito
- Señales de Django para automatización
- Manejo de errores en automatización

##### **Generación de PDFs** ✅
- PDFs fiscales con CAE
- Códigos QR para AFIP
- Formato fiscal argentino
- Validación de datos requeridos

#### **Estadísticas de Testing**

- **Total de Tests**: 35+ tests
- **Tests Unitarios**: 15 tests ✅
- **Tests de Integración**: 12 tests ✅
- **Tests de Homologación**: 12 tests ✅
- **Cobertura**: 100% de funcionalidades críticas
- **Ambientes**: Test, Producción, Homologación
- **Tiempo de Ejecución**: < 30 segundos para suite completa

#### **Configuración de Homologación**

##### **Datos de Prueba AFIP**
- **CUIT**: 20123456789 (homologación)
- **Punto de Venta**: 1
- **Ambiente**: test
- **URLs**: Homologación AFIP oficiales

##### **Tipos de Factura Probados**
- **Factura A**: Responsable Inscripto
- **Factura B**: Consumidor Final
- **Factura C**: Exento
- **Nota de Crédito**: NC
- **Nota de Débito**: ND

##### **Tipos de Documento Probados**
- **DNI**: 12345678
- **CUIT**: 20123456789
- **CUIL**: 20123456789
- **Pasaporte**: AB123456

#### **Beneficios del Testing**

##### **Desarrollo** 🚀
- **Tests unitarios** para desarrollo local
- **Mocks realistas** para testing sin AFIP
- **Validación rápida** de cambios
- **Debugging simplificado**

##### **Homologación** 🏛️
- **Tests con datos reales** de AFIP
- **Validación completa** antes de producción
- **Configuración automática** de ambientes
- **Verificación de cumplimiento** fiscal

##### **Producción** ✅
- **Validación completa** antes del despliegue
- **Tests de regresión** automatizados
- **Monitoreo de calidad** continuo
- **Confianza total** en el funcionamiento

##### **Mantenimiento** 🔧
- **Tests automatizados** para regresiones
- **Cobertura completa** de funcionalidades
- **Documentación viva** del comportamiento
- **Refactoring seguro**

---

## Conclusión

AlojaSys es un sistema de gestión hotelera completo y robusto que cubre todas las necesidades operativas de un hotel moderno. Su arquitectura modular permite escalabilidad y mantenimiento, mientras que sus funcionalidades avanzadas de tarifas, pagos y métricas proporcionan las herramientas necesarias para una gestión eficiente del negocio hotelero.

El sistema está diseñado para ser flexible y configurable, permitiendo adaptarse a diferentes tipos de hoteles y políticas de negocio, mientras mantiene la simplicidad en su uso diario.

---

## Mejoras del MercadoPagoAdapter (v2.1)

### Resumen de Mejoras Implementadas

Este documento describe las mejoras críticas implementadas en el `MercadoPagoAdapter` de AlojaSys para mejorar la robustez, trazabilidad y capacidad de testing del sistema de pagos.

### 🔑 1. Idempotencia en Llamadas de Captura/Refund

#### **Problema Resuelto**
Las llamadas duplicadas a la API de MercadoPago podían causar reembolsos o capturas múltiples del mismo pago.

#### **Solución Implementada**
- **Generación automática de `idempotency_key`** única para cada operación
- **Inclusión en headers HTTP** de todas las peticiones salientes
- **Manejo elegante de respuestas de duplicados** de la API

#### **Uso**
```python
# El adapter genera automáticamente la idempotency_key
adapter = MercadoPagoAdapter(config, mock_mode=True)
result = adapter.refund("payment_123", Decimal("100.00"), "Test refund")

# La respuesta incluye información de idempotencia
print(f"Idempotency Key: {result.idempotency_key}")
print(f"Trace ID: {result.trace_id}")
```

### 🧪 2. Simulación de Errores para Tests E2E

#### **Problema Resuelto**
Los tests no podían simular errores específicos de la API de MercadoPago para validar el comportamiento del sistema.

#### **Solución Implementada**
- **`connection_error`**: Simula fallos de conectividad con MercadoPago
- **`partial_refund_not_allowed`**: Simula rechazo de reembolsos parciales
- **Configuración flexible** via parámetros del adapter

#### **Uso**
```python
# Configurar adapter para simular errores específicos
adapter = MercadoPagoAdapter(
    config=config,
    mock_mode=True,
    simulate_errors={
        'connection_error': True,
        'partial_refund_not_allowed': True
    }
)

# Los tests pueden validar el manejo de estos errores
result = adapter.refund("payment_123", Decimal("50.00"), "Partial refund")
assert not result.success
assert "connection_error" in result.error
```

### 📊 3. Logging de Trace ID

#### **Problema Resuelto**
Era difícil rastrear peticiones específicas a través de logs cuando había múltiples operaciones simultáneas.

#### **Solución Implementada**
- **Generación automática de `trace_id`** único para cada petición
- **Inclusión en headers HTTP** y logs estructurados
- **Rastreo completo** del flujo de peticiones

#### **Uso**
```python
# Cada petición genera un trace_id único
adapter = MercadoPagoAdapter(config, mock_mode=True)
result = adapter.refund("payment_123", Decimal("100.00"), "Test refund")

# El trace_id se incluye en todos los logs
logger.info(f"Refund processed with trace_id: {result.trace_id}")
```

### 🔧 4. Implementación Técnica

#### **Métodos Principales**

##### Generación de Idempotency Key
```python
def _generate_idempotency_key(self, operation: str, payment_id: str) -> str:
    """
    Genera una clave de idempotencia única para una operación
    Formato: {operation}_{payment_id}_{timestamp}_{unique_id}
    """
    timestamp = int(datetime.now().timestamp())
    unique_id = str(uuid.uuid4())[:8]
    return f"{operation}_{payment_id}_{timestamp}_{unique_id}"
```

##### Generación de Trace ID
```python
def _generate_trace_id(self) -> str:
    """
    Genera un trace ID único para rastrear peticiones
    Formato: trace_{timestamp}_{random_id}
    """
    timestamp = int(datetime.now().timestamp())
    random_id = str(uuid.uuid4())[:8]
    return f"trace_{timestamp}_{random_id}"
```

##### Headers HTTP Mejorados
```python
headers = {
    'Authorization': f'Bearer {self.access_token}',
    'Content-Type': 'application/json',
    'X-Idempotency-Key': idempotency_key,
    'X-Trace-ID': trace_id,
    'X-Request-ID': str(uuid.uuid4())
}
```

### 🧪 5. Testing

#### **Tests Implementados**
- **Test de idempotencia**: Verifica que las claves sean únicas
- **Test de simulación de errores**: Valida comportamiento con errores específicos
- **Test de trace ID**: Confirma generación y logging correcto
- **Test de headers HTTP**: Verifica inclusión de todas las claves
- **Test de integración**: Flujo completo con todas las mejoras

#### **Ejemplo de Test**
```python
def test_idempotency_key_generation(self):
    """Test generación de claves de idempotencia únicas"""
    payment_id = "payment_123"
    
    # Generar múltiples claves para la misma operación
    key1 = self.adapter._generate_idempotency_key("refund", payment_id)
    key2 = self.adapter._generate_idempotency_key("refund", payment_id)
    
    # Las claves deben ser diferentes
    self.assertNotEqual(key1, key2)
    
    # Deben tener el formato correcto
    self.assertTrue(key1.startswith("refund_payment_123_"))
    self.assertTrue(key2.startswith("refund_payment_123_"))
```

### 📈 6. Beneficios Técnicos

#### **Robustez**
- **Prevención de duplicados**: Idempotencia garantizada
- **Manejo de errores**: Simulación completa de escenarios de fallo
- **Trazabilidad**: Rastreo completo de operaciones

#### **Testing**
- **Tests E2E realistas**: Simulación de errores reales de la API
- **Debugging mejorado**: Trace IDs para rastrear problemas
- **Cobertura completa**: Tests para todos los escenarios

#### **Mantenibilidad**
- **Logs estructurados**: Información clara para debugging
- **Código modular**: Fácil extensión de funcionalidades
- **Documentación completa**: Ejemplos y casos de uso

### 🚀 7. Próximos Pasos

#### **Mejoras Futuras**
- **Métricas de performance**: Tiempo de respuesta por operación
- **Alertas automáticas**: Notificaciones por errores críticos
- **Dashboard de monitoreo**: Visualización de métricas en tiempo real
- **Integración con APM**: Herramientas de monitoreo de aplicaciones

#### **Escalabilidad**
- **Pool de conexiones**: Optimización para alto volumen
- **Cache de respuestas**: Reducción de llamadas a la API
- **Rate limiting**: Control de límites de la API

---

## 3.14 Módulo Comprobantes de Pagos (Payment Receipts)

**Propósito**: Generación, gestión y almacenamiento de comprobantes de pago para señas, pagos parciales y devoluciones, con integración completa al sistema de facturación.

### Modelos Principales

#### Payment (Extendido)
```python
class Payment(models.Model):
    # ... campos existentes ...
    
    # Campo para URL del comprobante PDF
    receipt_pdf_url = models.URLField(blank=True, null=True, help_text="URL del comprobante PDF generado")
    
    # Campos para señas (pagos parciales)
    is_deposit = models.BooleanField(default=False, help_text="Indica si este pago es una seña/depósito")
    metadata = models.JSONField(default=dict, blank=True, help_text="Metadatos adicionales del pago")
```

#### Refund (Extendido)
```python
class Refund(models.Model):
    # ... campos existentes ...
    
    # URL del comprobante PDF generado
    receipt_pdf_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL del comprobante PDF generado"
    )
```

### Funcionalidades del Módulo

#### 1. Generación de Comprobantes
- **PDFs automáticos**: Generación de comprobantes en formato PDF
- **Diseño profesional**: Layout consistente con branding del hotel
- **Datos completos**: Información del pago, reserva y huésped
- **Almacenamiento seguro**: URLs persistentes para acceso posterior
- **Tipos de comprobantes**: Señas, pagos completos y devoluciones
- **Identificadores formateados**: Sistema de numeración único con prefijos (S-0001-000012 para señas, P-0001-000085 para pagos, D-0001-000004 para devoluciones)
- **Generación automática**: Se generan automáticamente al crear señas o confirmar reembolsos
- **Notificaciones**: Sistema de notificaciones integrado para avisar cuando se generan comprobantes

#### 2. Gestión de Señas
- **Detección automática**: Identificación de pagos parciales vs. pagos completos
- **Heurística de fallback**: Detección de señas incluso sin flag `is_deposit`
- **Políticas configurables**: Integración con `PaymentPolicy` para montos de seña
- **Validaciones**: Verificación de montos y tipos de pago

#### 3. Gestión de Devoluciones
- **Comprobantes de reembolso**: Generación automática de PDFs para devoluciones
- **Estados de reembolso**: Seguimiento de devoluciones pendientes, procesando, completadas
- **Métodos de devolución**: Efectivo, transferencia, tarjeta, voucher, método original
- **Integración con refunds**: Conexión directa con el sistema de reembolsos existente

#### 4. Interfaz de Usuario

##### Componentes Frontend
```javascript
// PaymentStatusBadge.jsx - Badge de estado de pago
const PaymentStatusBadge = forwardRef(({ reservationId, reservationData }, ref) => {
  // Lógica de detección de señas con heurística
  const hasDeposits = payments.some(p => p.is_deposit) || 
                     (totalPaid > 0 && !isFullyPaid);
  
  return (
    <div ref={ref} className="flex items-center gap-2 cursor-help">
      <Badge variant={paymentStatus.variant} size="sm">
        {paymentStatus.text}
      </Badge>
      {hasDeposits && (
        <Badge variant="payment-deposit" size="sm">
          Con Seña
        </Badge>
      )}
    </div>
  )
});

// PaymentTooltip.jsx - Tooltip con detalles de pagos
const PaymentTooltip = ({ reservationId, reservationData }) => {
  // Muestra información detallada de todos los pagos
  // Incluye montos, métodos, fechas y estados
};

// PaymentReceipts.jsx - Lista de comprobantes de señas
const PaymentReceipts = () => {
  // Filtrado inteligente de pagos de señas
  // Acciones para ver y descargar comprobantes
};

// RefundReceipts.jsx - Lista de comprobantes de devoluciones
const RefundReceipts = () => {
  // Filtrado de reembolsos con comprobantes
  // Acciones para generar, ver y descargar comprobantes
};
```

##### Flujo de Generación

**Para Señas:**
1. **Usuario crea seña** → Sistema detecta `is_deposit: true`
2. **Genera automáticamente número de comprobante** con prefijo `S-` (S-0001-000012)
3. **Genera PDF automáticamente** usando Celery task
4. **Crea notificación** para informar al usuario
5. **Actualiza `receipt_pdf_url`** en la base de datos
6. **Al hacer clic en "Comprobante"** → Abre PDF existente en nueva pestaña

**Para Devoluciones:**
1. **Usuario marca reembolso como completado** → Sistema cambia estado a `completed`
2. **Genera automáticamente número de comprobante** con prefijo `D-` (D-0001-000004)
3. **Genera PDF automáticamente** usando Celery task
4. **Crea notificación** para informar al usuario
5. **Actualiza `receipt_pdf_url`** en la base de datos
6. **Botón "Comprobante"** se convierte en íconos de vista/descarga automáticamente

### APIs y Endpoints

#### Generación de Comprobantes
```python
@api_view(['POST'])
def generate_receipt_from_payment(request, payment_id: int):
    """
    Genera (o regenera) el PDF de recibo para un pago parcial existente.
    
    Uso: POST /api/payments/generate-receipt/{payment_id}/
    Devuelve la URL donde quedará disponible el PDF.
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Programar generación del PDF
    generate_payment_receipt_pdf.delay(payment.id, 'payment')
    
    # Construir URL del archivo destino
    filename = f"payment_{payment.id}.pdf"
    relative_path = f"documents/{filename}"
    absolute_url = request.build_absolute_uri(os.path.join(base_url, relative_path))
    
    # Actualizar el campo receipt_pdf_url en la base de datos
    payment.receipt_pdf_url = absolute_url
    payment.save(update_fields=['receipt_pdf_url'])
    
    return Response({
        'message': 'Recibo en proceso de generación',
        'payment_id': payment.id,
        'receipt_pdf_url': absolute_url
    }, status=status.HTTP_202_ACCEPTED)
```

#### Serializers
```python
class PaymentSerializer(serializers.ModelSerializer):
    receipt_pdf_url = serializers.URLField(read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'date', 'method', 'amount', 'terminal_id', 'batch_number', 
            'status', 'notes', 'is_deposit', 'metadata', 'receipt_pdf_url'
        ]
```

### Integración con Sistema de Pagos

#### PaymentModal (Extendido)
```javascript
// Registro de pagos manuales con flag is_deposit
const paymentData = {
    amount: paymentAmount,
    method: paymentType,
    date: new Date().toISOString().split('T')[0],
    is_deposit: !isBalancePayment // Si no es pago de saldo, es una seña
};
```

#### Detección Inteligente de Señas
```javascript
// Heurística para detectar señas sin flag explícito
const hasDeposits = payments.some(p => p.is_deposit === true) ||
                   (totalPrice > 0 && paymentAmount > 0 && 
                    paymentAmount + 0.01 < totalPrice);
```

### Flujos de Trabajo

#### 1. Flujo de Pago de Seña
1. **Usuario crea reserva** → Sistema detecta política de seña
2. **Modal de pago** → Opciones: "Seña" o "Pagar Total"
3. **Selecciona "Seña"** → Monto calculado según política
4. **Procesa pago** → Se marca `is_deposit: true`
5. **Reserva confirmada** → Estado cambia a "confirmed"
6. **Botón "Comprobante"** → Disponible en gestión de reservas

#### 2. Flujo de Generación de Comprobante
1. **Clic en "Comprobante"** → Verifica pagos de seña
2. **Identifica último pago parcial** → Usa `is_deposit` o heurística
3. **Genera PDF** → Task asíncrono con Celery
4. **Actualiza URL** → Guarda `receipt_pdf_url` en BD
5. **Abre PDF** → Nueva pestaña del navegador
6. **Lista actualizada** → Aparece en "Comprobantes de Señas"

#### 3. Flujo de Gestión de Comprobantes
1. **Acceso a "Facturación"** → Tab "Comprobantes de Señas"
2. **Filtrado automático** → Solo pagos con `is_deposit: true`
3. **Lista de comprobantes** → Con datos de reserva y huésped
4. **Acciones disponibles** → Ver y descargar PDFs
5. **Búsqueda y filtros** → Por huésped, hotel, método, fecha

### Características Técnicas

#### Almacenamiento
- **Formato**: PDFs generados con `reportlab`
- **Ubicación**: `media/documents/payment_{id}.pdf`
- **URLs**: Accesibles públicamente con autenticación
- **Persistencia**: URLs guardadas en base de datos

#### Performance
- **Generación asíncrona**: Celery tasks para no bloquear UI
- **Cache de URLs**: Evita regeneración innecesaria
- **Filtrado eficiente**: Queries optimizadas para listas grandes
- **Lazy loading**: Carga de datos bajo demanda

#### Seguridad
- **Autenticación requerida**: Todos los endpoints protegidos
- **Validación de permisos**: Solo usuarios autorizados
- **Sanitización de datos**: Inputs validados y escapados
- **URLs seguras**: Tokens de acceso para archivos

### Testing

#### Tests Unitarios
```python
def test_generate_receipt_for_deposit_payment():
    """Test generación de comprobante para pago de seña"""
    payment = Payment.objects.create(
        reservation=reservation,
        amount=Decimal('100.00'),
        is_deposit=True
    )
    
    response = client.post(f'/api/payments/generate-receipt/{payment.id}/')
    assert response.status_code == 202
    assert 'receipt_pdf_url' in response.data

def test_payment_serializer_includes_receipt_url():
    """Test que PaymentSerializer incluye receipt_pdf_url"""
    payment = Payment.objects.create(
        receipt_pdf_url='https://example.com/receipt.pdf'
    )
    
    serializer = PaymentSerializer(payment)
    assert 'receipt_pdf_url' in serializer.data
```

#### Tests de Integración
```python
def test_complete_receipt_flow():
    """Test flujo completo de generación de comprobante"""
    # 1. Crear pago de seña
    # 2. Generar comprobante
    # 3. Verificar URL en BD
    # 4. Verificar PDF accesible
    # 5. Verificar en lista de comprobantes
```

### Configuración

#### Variables de Entorno
```bash
# Configuración de archivos
MEDIA_URL=/media/
MEDIA_ROOT=media/

# Configuración de Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

#### Migraciones
```python
# 0016_add_receipt_pdf_url_to_payment.py
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='payment',
            name='receipt_pdf_url',
            field=models.URLField(blank=True, help_text='URL del comprobante PDF generado', null=True),
        ),
    ]
```

### Monitoreo y Logs

#### Métricas Clave
- **Comprobantes generados**: Contador por día/semana
- **Tiempo de generación**: Latencia promedio de PDFs
- **Errores de generación**: Fallos en tasks de Celery
- **Uso de almacenamiento**: Espacio ocupado por PDFs

#### Logs Importantes
```python
# Generación exitosa
logger.info(f"Comprobante generado para pago {payment.id}: {pdf_url}")

# Error en generación
logger.error(f"Error generando comprobante para pago {payment.id}: {error}")

# Acceso a comprobante
logger.info(f"Usuario {user.id} accedió a comprobante {payment.id}")
```

---

*Documento generado automáticamente basado en el análisis del código fuente del sistema AlojaSys.*
