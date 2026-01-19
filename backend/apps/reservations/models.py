from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.core.models import Hotel
from apps.rooms.models import Room
from decimal import Decimal
from datetime import timedelta
from apps.rates.services.engine import get_applicable_rule

class ReservationStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    CONFIRMED = "confirmed", "Confirmada"
    CANCELLED = "cancelled", "Cancelada"
    CHECK_IN = "check_in", "Check-in"
    CHECK_OUT = "check_out", "Check-out"
    NO_SHOW = "no_show", "No-show"
    EARLY_CHECK_IN = "early_check_in", "Check-in anticipado"
    LATE_CHECK_OUT = "late_check_out", "Check-out tardío"

class RoomBlockType(models.TextChoices):
    MAINTENANCE = "maintenance", "Mantenimiento"
    OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"
    HOLD = "hold", "Bloqueo"

class ReservationChannel(models.TextChoices):
    DIRECT = "direct", "Directo"
    WHATSAPP = "whatsapp", "WhatsApp"
    BOOKING = "booking", "Booking"
    EXPEDIA = "expedia", "Expedia"
    AIRBNB = "airbnb", "Airbnb"
    OTHER = "other", "Otro"

class Reservation(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="reservations")
    guests = models.PositiveIntegerField(default=1, help_text="Número de huéspedes")
    guests_data = models.JSONField(default=list, help_text="Información de todos los huéspedes")
    group_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        help_text="Identificador de grupo para reservas multi-habitación (misma estancia con varias habitaciones)"
    )
    channel = models.CharField(max_length=20, choices=ReservationChannel.choices, default=ReservationChannel.DIRECT)
    external_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID externo de la reserva (ej: UID de iCal, ID de OTA)")
    promotion_code = models.CharField(max_length=50, blank=True, null=True, help_text="Código de promoción aplicado")
    voucher_code = models.CharField(max_length=50, blank=True, null=True, help_text="Código de voucher aplicado")
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    # Pago por quién: OTA u HOTEL (para evitar dobles cobros y conciliar)
    class PaidBy(models.TextChoices):
        OTA = "ota", "Pagada por OTA"
        HOTEL = "hotel", "Pago directo en hotel"
    paid_by = models.CharField(max_length=10, choices=PaidBy.choices, blank=True, null=True)

    # Bandera operativa para marcar choque/overbooking importado
    overbooking_flag = models.BooleanField(default=False)
    applied_cancellation_policy = models.ForeignKey(
        'payments.CancellationPolicy', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Política de cancelación vigente al momento de crear la reserva"
    )
    applied_cancellation_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot de la política de cancelación al momento de crear la reserva"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Normalización de canal/origen
        # - Si no hay external_id, forzar canal DIRECT (reservas internas)
        # - Si hay external_id, no permitir canal DIRECT (debe ser una reserva de OTA)
        if not self.external_id and self.channel != ReservationChannel.DIRECT:
            self.channel = ReservationChannel.DIRECT
        if self.external_id and self.channel == ReservationChannel.DIRECT:
            raise ValidationError({"channel": "Reservas con external_id deben tener canal distinto de DIRECT."})

        if self.check_in >= self.check_out:
            raise ValidationError("check_in debe ser anterior a check_out.")

        if self.hotel_id is None and self.room_id:
            self.hotel = self.room.hotel

        # Validar número de huéspedes
        if self.room_id and self.guests:
            if self.guests > self.room.max_capacity:
                raise ValidationError(f"La habitación {self.room.name} tiene una capacidad máxima de {self.room.max_capacity} huéspedes.")
            if self.guests < 1:
                raise ValidationError("Debe haber al menos 1 huésped.")

        # Si la reserva tiene external_id, es una reserva importada desde OTA
        # Permitimos solapamientos porque la OTA puede tener reservas que se solapan
        # con reservas gestionadas directamente en el PMS
        if not self.external_id:
            active_status = [
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.CHECK_IN,
            ]
            qs = Reservation.objects.filter(
                hotel=self.hotel,
                room=self.room,
                status__in=active_status,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("La habitación ya está reservada en ese rango.")

        # Reglas de tarifas: CTA/CTD, min/max stay
        if self.room_id and self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            # closed: si alguna noche está cerrada, no se permite
            current = self.check_in
            while current < self.check_out:
                rule = get_applicable_rule(self.room, current, self.channel, include_closed=True)
                if rule and rule.closed:
                    raise ValidationError({"__all__": f"Día {current} cerrado para venta."})
                current += timedelta(days=1)

            # CTA y CTD
            start_rule = get_applicable_rule(self.room, self.check_in, self.channel, include_closed=True)
            if start_rule and start_rule.closed_to_arrival:
                raise ValidationError({"check_in": "Cerrado para llegada (CTA)."})
            end_rule = get_applicable_rule(self.room, self.check_out, self.channel, include_closed=True)
            if end_rule and end_rule.closed_to_departure:
                raise ValidationError({"check_out": "Cerrado para salida (CTD)."})

            # min/max stay (se toma la regla del día de llegada como referencia)
            if start_rule and start_rule.min_stay and nights < start_rule.min_stay:
                raise ValidationError({"__all__": f"Mínimo de estadía: {start_rule.min_stay} noches."})
            if start_rule and start_rule.max_stay and nights > start_rule.max_stay:
                raise ValidationError({"__all__": f"Máximo de estadía: {start_rule.max_stay} noches."})
            
    def save(self, *args, **kwargs):
        skip_clean = kwargs.pop('skip_clean', False)
        # Importante:
        # - Para reservas DIRECTAS (sin external_id) calculamos el total aproximado con base_price.
        # - Para reservas OTA (con external_id), si ya vino un total desde el channel manager/OTA,
        #   NO debemos pisarlo. Solo hacemos fallback si el total está vacío/0.
        should_autocalculate_total = (not self.external_id) or (self.total_price is None) or (self.total_price == 0)

        if self.room_id and self.check_in and self.check_out and should_autocalculate_total:
            nights = (self.check_out - self.check_in).days
            # Precio base por noche desde la habitación
            base_nightly = self.room.base_price or Decimal('0.00')
            # Extra por huéspedes por encima de la capacidad incluida
            included = self.room.capacity or 1
            extra_guests = max((self.guests or 1) - included, 0)
            extra_fee = (self.room.extra_guest_fee or Decimal('0.00')) * Decimal(extra_guests)
            # Total aproximado: (tarifa base + extra x noche) * noches
            self.total_price = (Decimal(max(nights, 0)) * (Decimal(base_nightly) + Decimal(extra_fee))).quantize(Decimal('0.01'))
            if self.hotel_id is None:
                self.hotel = self.room.hotel
        if skip_clean:
            # Saltar clean() para reservas importadas desde OTAs que pueden tener solapamientos
            super().save(*args, **kwargs)
        else:
            self.full_clean()
            super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "room"]),
            models.Index(fields=["hotel", "check_in"]),
            models.Index(fields=["status"]),
            models.Index(fields=["external_id"]),  # Para búsquedas por ID externo (OTAs)
        ]
        # Django crea automáticamente estos permisos:
        # - reservations.add_reservation
        # - reservations.change_reservation
        # - reservations.delete_reservation
        # - reservations.view_reservation
        permissions = [
            # Puedes agregar permisos personalizados aquí si necesitas
            # ("cancel_reservation", "Puede cancelar reservas"),
            # ("check_in_reservation", "Puede realizar check-in"),
            # ("check_out_reservation", "Puede realizar check-out"),
        ]

    @property
    def guest_name(self):
        """Obtiene el nombre del huésped principal"""
        primary_guest = self.get_primary_guest()
        return primary_guest.get('name', '') if primary_guest else ''
    
    @property
    def guest_email(self):
        """Obtiene el email del huésped principal"""
        primary_guest = self.get_primary_guest()
        return primary_guest.get('email', '') if primary_guest else ''
    
    def get_primary_guest(self):
        """Obtiene el huésped principal (is_primary=True)"""
        if not self.guests_data:
            return None
        return next((guest for guest in self.guests_data if guest.get('is_primary', False)), None)
    
    def get_all_guests(self):
        """Obtiene todos los huéspedes ordenados (principal primero)"""
        if not self.guests_data:
            return []
        return sorted(self.guests_data, key=lambda x: (not x.get('is_primary', False), x.get('name', '')))

    @property
    def display_name(self):
        """Nombre descriptivo generado dinámicamente para la reserva"""
        return f"Reserva N° {self.id}"

    def __str__(self):
        return f"{self.display_name} ({self.check_in} -> {self.check_out})"

class RoomBlock(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_blocks")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room_blocks")
    start_date = models.DateField()
    end_date = models.DateField()
    block_type = models.CharField(max_length=20, choices=RoomBlockType.choices)
    reason = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")

    class Meta:
        verbose_name = "Bloqueo de habitación"
        verbose_name_plural = "Bloqueos de habitaciones"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["hotel", "room"]),
            models.Index(fields=["hotel", "start_date"]),
            models.Index(fields=["is_active"]),
        ]


# --- Pricing primitives ---
class ReservationNight(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='nights')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reservation_nights')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='reservation_nights')
    date = models.DateField()
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_guest_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_night = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reservation', 'date')
        indexes = [
            models.Index(fields=['hotel', 'date']),
            models.Index(fields=['room', 'date']),
        ]


class ReservationCharge(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='charges')
    date = models.DateField()
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    taxable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ChannelCommission(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='commissions')
    channel = models.CharField(max_length=50, default='direct')
    rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    method = models.CharField(max_length=30, default='cash')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ARS')
    
    # Campos específicos para POSTNET
    terminal_id = models.CharField(max_length=50, blank=True, help_text="ID del terminal POSTNET")
    batch_number = models.CharField(max_length=100, blank=True, help_text="Número de batch del terminal")
    status = models.CharField(max_length=20, default='approved', help_text="Estado del pago: approved, pending_settlement, failed")
    notes = models.TextField(blank=True, help_text="Notas adicionales del pago")
    
    # Campos para señas (pagos parciales)
    is_deposit = models.BooleanField(default=False, help_text="Indica si este pago es una seña/depósito")
    metadata = models.JSONField(default=dict, blank=True, help_text="Metadatos adicionales del pago")
    
    # Origen del pago (para conciliación OTA)
    class PaymentSource(models.TextChoices):
        OTA_PAYOUT = "ota_payout", "Payout OTA"
        OTA_VCC = "ota_vcc", "Tarjeta virtual OTA"
        HOTEL_POS = "hotel_pos", "POS del hotel"
        ONLINE_GATEWAY = "online_gateway", "Pasarela online"
    payment_source = models.CharField(max_length=20, choices=PaymentSource.choices, blank=True, null=True)
    provider = models.CharField(max_length=20, blank=True, null=True, help_text="Proveedor/canal (booking, airbnb, expedia)")
    external_reference = models.CharField(max_length=100, blank=True, null=True, help_text="ID externo de pago/transacción OTA")
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    activation_date = models.DateField(blank=True, null=True, help_text="Fecha de activación de VCC (si aplica)")
    payout_date = models.DateField(blank=True, null=True, help_text="Fecha estimada/real de payout OTA")
    
    # Campo para URL del comprobante PDF
    receipt_pdf_url = models.URLField(blank=True, null=True, help_text="URL del comprobante PDF generado")
    
    # Número de comprobante serio (ej: S-0001-000012 o P-0001-000085)
    receipt_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Número de comprobante serio (ej: S-0001-000012 para seña, P-0001-000085 para pago)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generar número de comprobante si no existe
        if not self.receipt_number:
            try:
                from apps.payments.models import ReceiptNumberSequence
                
                # Determinar el tipo de comprobante según si es seña o pago total
                if self.is_deposit:
                    receipt_type = ReceiptNumberSequence.ReceiptType.DEPOSIT  # "S"
                else:
                    receipt_type = ReceiptNumberSequence.ReceiptType.PAYMENT  # "P"
                
                self.receipt_number = ReceiptNumberSequence.generate_receipt_number(
                    hotel=self.reservation.hotel,
                    receipt_type=receipt_type
                )
            except Exception as e:
                # Si hay error, no fallar la creación del pago
                pass
        
        # Marcar si es un nuevo pago
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Si es una seña nueva, enviar notificación sobre el comprobante
        # NOTA: La generación del PDF y envío de email se hace automáticamente vía signal (apps/payments/signals.py)
        # para evitar duplicación de emails
        if is_new and self.is_deposit:
            try:
                from apps.notifications.services import NotificationService
                from django.contrib.auth import get_user_model
                
                # Obtener el usuario que creó el pago si existe
                user_id = getattr(self, 'created_by_id', None)
                if not user_id:
                    # Intentar obtener el usuario de la reserva
                    try:
                        user_id = getattr(self.reservation, 'created_by_id', None)
                    except Exception:
                        pass
                
                NotificationService.create_receipt_generated_notification(
                    receipt_type='deposit',
                    receipt_number=self.receipt_number or f'S-{self.id}',
                    reservation_code=f"RES-{self.reservation.id}",
                    hotel_name=self.reservation.hotel.name,
                    amount=str(self.amount),
                    hotel_id=self.reservation.hotel.id,
                    reservation_id=self.reservation.id,
                    user_id=user_id
                )
            except Exception as notif_error:
                # No fallar si hay error en notificación
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creando notificación para comprobante {self.id}: {notif_error}")

class ReservationStatusChange(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='status_changes')
    from_status = models.CharField(max_length=20, choices=ReservationStatus.choices, null=True, blank=True)
    to_status = models.CharField(max_length=20, choices=ReservationStatus.choices)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=['reservation', 'changed_at']),
            models.Index(fields=['to_status']),
        ]
    
class ReservationChangeEvent(models.TextChoices):
    CREATED = "created", "Creada"
    UPDATED = "updated", "Actualizada"
    STATUS_CHANGED = "status_changed", "Cambio de estado"
    CHECK_IN = "check_in", "Check-in"
    CHECK_OUT = "check_out", "Check-out"
    CANCEL = "cancel", "Cancelación"
    CHARGE_ADDED = "charge_added", "Cargo agregado"
    CHARGE_REMOVED = "charge_removed", "Cargo eliminado"
    PAYMENT_ADDED = "payment_added", "Pago agregado"
    COMMISSION_UPDATED = "commission_updated", "Comisión actualizada"
    NO_SHOW_PENALTY = "no_show_penalty", "Penalidad NO_SHOW"
    NO_SHOW_PROCESSED = "no_show_processed", "NO_SHOW Procesado"
    NIGHTS_REGENERATED = "nights_regenerated", "Noches regeneradas"

class ReservationChangeLog(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='change_logs')
    event_type = models.CharField(max_length=30, choices=ReservationChangeEvent.choices)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    fields_changed = models.JSONField(default=list, help_text="Campos modificados", null=True, blank=True)
    snapshot = models.JSONField(default=dict, help_text="Snapshot del estado anterior", null=True, blank=True)
    message = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=['reservation', 'changed_at']),
            models.Index(fields=['event_type']),
        ]