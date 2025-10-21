from django.contrib import admin
from .models import (
    PaymentGatewayConfig, PaymentIntent, CancellationPolicy, Refund, RefundLog, RefundVoucher, 
    BankTransferPayment, BankTransferStatus, BankReconciliation, BankTransaction, ReconciliationMatch, 
    BankReconciliationLog, BankReconciliationConfig, ReconciliationStatus, MatchType, ReconciliationEventType
)

@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ("provider","enterprise","hotel","is_test","is_production","currency_code","refund_window_days","partial_refunds_allowed","is_active","updated_at")
    list_filter = ("provider","is_test","is_production","is_active","currency_code","partial_refunds_allowed")
    search_fields = ("enterprise__name","hotel__name","public_key")
    fieldsets = (
        ("Información Básica", {
            "fields": ("provider", "enterprise", "hotel", "is_active")
        }),
        ("Configuración de Acceso", {
            "fields": ("public_key", "access_token", "integrator_id", "webhook_secret")
        }),
        ("Configuración Regional", {
            "fields": ("is_test", "is_production", "country_code", "currency_code"),
            "description": "⚠️ No se puede marcar is_production=True si is_test=True"
        }),
        ("Configuración de Reembolsos", {
            "fields": ("refund_window_days", "partial_refunds_allowed"),
            "description": "Configuración de limitaciones para reembolsos"
        })
    )

@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("id","reservation","hotel","amount","currency","status","created_at")
    list_filter = ("status","currency")
    search_fields = ("reservation__id","mp_payment_id","mp_preference_id","external_reference")

@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(admin.ModelAdmin):
    list_display = ("name","hotel","is_active","is_default","auto_refund_on_cancel","free_cancellation_time","free_cancellation_unit","created_at")
    list_filter = ("is_active","is_default","auto_refund_on_cancel","free_cancellation_unit","cancellation_fee_type")
    search_fields = ("name","hotel__name")
    fieldsets = (
        ("Información Básica", {
            "fields": ("hotel", "name", "is_active", "is_default")
        }),
        ("Configuración de Tiempos", {
            "fields": ("free_cancellation_time", "free_cancellation_unit", "partial_refund_time", "partial_refund_unit", "no_refund_time", "no_refund_unit")
        }),
        ("Configuración de Penalidades", {
            "fields": ("cancellation_fee_type", "cancellation_fee_value")
        }),
        ("Restricciones", {
            "fields": ("allow_cancellation_after_checkin", "allow_cancellation_after_checkout", "allow_cancellation_no_show", "allow_cancellation_early_checkout")
        }),
        ("Reembolsos Automáticos", {
            "fields": ("auto_refund_on_cancel",),
            "description": "Controlar si la cancelación dispara reembolso automático"
        }),
        ("Mensajes", {
            "fields": ("free_cancellation_message", "partial_cancellation_message", "no_cancellation_message", "cancellation_fee_message")
        }),
        ("Configuración Avanzada", {
            "fields": ("apply_to_all_room_types", "room_types", "apply_to_all_channels", "channels", "apply_to_all_seasons", "seasonal_rules"),
            "classes": ("collapse",)
        })
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("id", "reservation", "amount", "status", "reason", "refund_method", "created_at", "processed_at")
    list_filter = ("status", "reason", "refund_method", "created_at")
    search_fields = ("reservation__id", "external_reference", "notes")
    readonly_fields = ("created_at", "updated_at", "history")
    fieldsets = (
        ("Información Básica", {
            "fields": ("reservation", "payment", "amount", "reason", "status")
        }),
        ("Configuración de Reembolso", {
            "fields": ("method", "refund_method", "processing_days", "external_reference")
        }),
        ("Auditoría", {
            "fields": ("created_by", "processed_by", "created_at", "updated_at", "processed_at"),
            "classes": ("collapse",)
        }),
        ("Notas e Historial", {
            "fields": ("notes", "history"),
            "classes": ("collapse",)
        })
    )


@admin.register(RefundLog)
class RefundLogAdmin(admin.ModelAdmin):
    list_display = ("id", "refund", "event_type", "status", "action", "user", "timestamp")
    list_filter = ("event_type", "status", "timestamp")
    search_fields = ("refund__id", "action", "message", "error_message")
    readonly_fields = ("timestamp",)
    fieldsets = (
        ("Información Básica", {
            "fields": ("refund", "event_type", "status", "action", "timestamp")
        }),
        ("Usuario y Contexto", {
            "fields": ("user", "external_reference")
        }),
        ("Detalles", {
            "fields": ("message", "details", "error_message"),
            "classes": ("collapse",)
        })
    )


@admin.register(RefundVoucher)
class RefundVoucherAdmin(admin.ModelAdmin):
    list_display = ("code", "hotel", "amount", "remaining_amount", "status", "expiry_date", "created_at", "used_at")
    list_filter = ("status", "hotel", "created_at", "expiry_date")
    search_fields = ("code", "hotel__name", "notes")
    readonly_fields = ("code", "created_at", "updated_at", "used_at")
    fieldsets = (
        ("Información Básica", {
            "fields": ("code", "hotel", "amount", "remaining_amount", "status")
        }),
        ("Fechas", {
            "fields": ("expiry_date", "created_at", "updated_at", "used_at")
        }),
        ("Relaciones", {
            "fields": ("original_refund", "used_in_reservation", "created_by", "used_by"),
            "classes": ("collapse",)
        }),
        ("Notas", {
            "fields": ("notes",),
            "classes": ("collapse",)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("hotel", "created_by", "used_by", "original_refund", "used_in_reservation")


@admin.register(BankTransferPayment)
class BankTransferPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "reservation", "hotel", "amount", "transfer_date", "cbu_iban", "status", "is_amount_valid", "is_cbu_valid", "created_at")
    list_filter = ("status", "is_amount_valid", "is_cbu_valid", "transfer_date", "created_at")
    search_fields = ("reservation__id", "cbu_iban", "bank_name", "external_reference", "payment_reference")
    readonly_fields = ("created_at", "updated_at", "reviewed_at", "history", "payment_reference")
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("reservation", "hotel", "amount", "transfer_date", "cbu_iban", "bank_name")
        }),
        ("Comprobante", {
            "fields": ("receipt_file", "receipt_filename")
        }),
        ("Estado y Validación", {
            "fields": ("status", "is_amount_valid", "is_cbu_valid", "validation_notes")
        }),
        ("Datos OCR", {
            "fields": ("ocr_amount", "ocr_cbu", "ocr_confidence"),
            "description": "Datos extraídos automáticamente del comprobante"
        }),
        ("Referencias", {
            "fields": ("external_reference", "payment_reference")
        }),
        ("Revisión", {
            "fields": ("reviewed_by", "reviewed_at", "notes")
        }),
        ("Metadatos", {
            "fields": ("created_by", "created_at", "updated_at", "history"),
            "classes": ("collapse",)
        })
    )
    
    actions = ["mark_as_confirmed", "mark_as_rejected", "mark_as_pending_review"]
    
    def mark_as_confirmed(self, request, queryset):
        """Marca las transferencias seleccionadas como confirmadas"""
        count = 0
        for transfer in queryset:
            if transfer.status != BankTransferStatus.CONFIRMED:
                transfer.mark_as_confirmed(user=request.user, notes="Confirmado desde admin")
                count += 1
        
        self.message_user(request, f"{count} transferencias marcadas como confirmadas.")
    mark_as_confirmed.short_description = "Marcar como confirmadas"
    
    def mark_as_rejected(self, request, queryset):
        """Marca las transferencias seleccionadas como rechazadas"""
        count = 0
        for transfer in queryset:
            if transfer.status != BankTransferStatus.REJECTED:
                transfer.mark_as_rejected(user=request.user, notes="Rechazado desde admin")
                count += 1
        
        self.message_user(request, f"{count} transferencias marcadas como rechazadas.")
    mark_as_rejected.short_description = "Marcar como rechazadas"
    
    def mark_as_pending_review(self, request, queryset):
        """Marca las transferencias seleccionadas como pendientes de revisión"""
        count = 0
        for transfer in queryset:
            if transfer.status not in [BankTransferStatus.PENDING_REVIEW, BankTransferStatus.CONFIRMED, BankTransferStatus.REJECTED]:
                transfer.mark_as_pending_review(user=request.user)
                count += 1
        
        self.message_user(request, f"{count} transferencias marcadas como pendientes de revisión.")
    mark_as_pending_review.short_description = "Marcar como pendientes de revisión"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("reservation", "hotel", "created_by", "reviewed_by")


# ===== ADMIN PARA CONCILIACIÓN BANCARIA =====

@admin.register(BankReconciliationConfig)
class BankReconciliationConfigAdmin(admin.ModelAdmin):
    list_display = ("hotel", "default_currency", "auto_confirm_threshold", "pending_review_threshold", "is_active", "updated_at")
    list_filter = ("is_active", "default_currency", "email_notifications")
    search_fields = ("hotel__name",)
    fieldsets = (
        ("Hotel", {
            "fields": ("hotel", "is_active")
        }),
        ("Tolerancias de Matching", {
            "fields": (
                "exact_match_date_tolerance", "fuzzy_match_amount_tolerance_percent", 
                "fuzzy_match_date_tolerance", "partial_match_amount_tolerance_percent", 
                "partial_match_date_tolerance"
            )
        }),
        ("Umbrales de Confianza", {
            "fields": ("auto_confirm_threshold", "pending_review_threshold")
        }),
        ("Configuración de Moneda", {
            "fields": ("default_currency", "currency_rate", "currency_rate_date")
        }),
        ("Notificaciones", {
            "fields": ("email_notifications", "notification_threshold_percent", "notification_emails")
        }),
        ("Configuración de CSV", {
            "fields": ("csv_encoding", "csv_separator", "csv_columns")
        })
    )


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ("hotel", "reconciliation_date", "status", "total_transactions", "matched_transactions", "match_percentage", "created_at")
    list_filter = ("status", "reconciliation_date", "hotel")
    search_fields = ("hotel__name", "csv_filename")
    readonly_fields = ("csv_file_size", "total_transactions", "matched_transactions", "unmatched_transactions", 
                      "pending_review_transactions", "error_transactions", "processing_started_at", 
                      "processing_completed_at", "created_at", "updated_at", "match_percentage", "needs_manual_review")
    
    fieldsets = (
        ("Información Básica", {
            "fields": ("hotel", "reconciliation_date", "status")
        }),
        ("Archivo CSV", {
            "fields": ("csv_file", "csv_filename", "csv_file_size")
        }),
        ("Estadísticas", {
            "fields": ("total_transactions", "matched_transactions", "unmatched_transactions", 
                      "pending_review_transactions", "error_transactions", "match_percentage", "needs_manual_review")
        }),
        ("Procesamiento", {
            "fields": ("processing_started_at", "processing_completed_at", "processing_notes", "error_details")
        }),
        ("Auditoría", {
            "fields": ("created_by", "created_at", "updated_at")
        })
    )
    
    actions = ["process_reconciliation", "send_notifications"]
    
    def process_reconciliation(self, request, queryset):
        """Procesa las conciliaciones seleccionadas"""
        from .tasks import process_bank_reconciliation
        count = 0
        for reconciliation in queryset:
            if reconciliation.status == ReconciliationStatus.PENDING:
                process_bank_reconciliation.delay(reconciliation.id)
                count += 1
        
        self.message_user(request, f"{count} conciliaciones programadas para procesamiento.")
    process_reconciliation.short_description = "Procesar conciliaciones"
    
    def send_notifications(self, request, queryset):
        """Envía notificaciones para las conciliaciones seleccionadas"""
        from .tasks import send_reconciliation_notifications
        count = 0
        for reconciliation in queryset:
            if reconciliation.status == ReconciliationStatus.COMPLETED:
                send_reconciliation_notifications.delay(reconciliation.id)
                count += 1
        
        self.message_user(request, f"{count} notificaciones programadas para envío.")
    send_notifications.short_description = "Enviar notificaciones"


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ("reconciliation", "transaction_date", "amount", "currency", "is_matched", "is_reversal", "match_confidence", "created_at")
    list_filter = ("is_matched", "is_reversal", "currency", "transaction_date", "reconciliation__hotel")
    search_fields = ("description", "reference", "reconciliation__hotel__name")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Información de la Transacción", {
            "fields": ("reconciliation", "transaction_date", "description", "amount", "currency", "reference")
        }),
        ("Estado del Matching", {
            "fields": ("is_matched", "is_reversal", "match_confidence", "match_type")
        }),
        ("Referencias al Pago", {
            "fields": ("matched_payment_id", "matched_payment_type", "matched_reservation_id")
        }),
        ("Diferencias", {
            "fields": ("amount_difference", "date_difference_days")
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at")
        })
    )


@admin.register(ReconciliationMatch)
class ReconciliationMatchAdmin(admin.ModelAdmin):
    list_display = ("reconciliation", "bank_transaction", "payment_type", "payment_id", "match_type", "confidence_score", "is_confirmed", "is_manual", "created_at")
    list_filter = ("is_confirmed", "is_manual", "match_type", "payment_type", "reconciliation__hotel")
    search_fields = ("reconciliation__hotel__name", "payment_id", "reservation_id")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Información del Match", {
            "fields": ("reconciliation", "bank_transaction", "payment_id", "payment_type", "reservation_id")
        }),
        ("Detalles del Match", {
            "fields": ("match_type", "confidence_score", "amount_difference", "date_difference_days")
        }),
        ("Estado del Match", {
            "fields": ("is_confirmed", "is_manual", "manual_approved_by", "manual_approved_at", "manual_notes")
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at")
        })
    )
    
    actions = ["approve_matches", "reject_matches"]
    
    def approve_matches(self, request, queryset):
        """Aprueba los matches seleccionados"""
        count = 0
        for match in queryset:
            if not match.is_confirmed:
                match.is_confirmed = True
                match.is_manual = True
                match.manual_approved_by = request.user
                match.manual_approved_at = timezone.now()
                match.manual_notes = "Aprobado desde admin"
                match.save()
                count += 1
        
        self.message_user(request, f"{count} matches aprobados.")
    approve_matches.short_description = "Aprobar matches"
    
    def reject_matches(self, request, queryset):
        """Rechaza los matches seleccionados"""
        count = 0
        for match in queryset:
            if not match.is_confirmed:
                match.delete()
                count += 1
        
        self.message_user(request, f"{count} matches rechazados.")
    reject_matches.short_description = "Rechazar matches"


@admin.register(BankReconciliationLog)
class BankReconciliationLogAdmin(admin.ModelAdmin):
    list_display = ("reconciliation", "event_type", "event_description", "created_by", "created_at")
    list_filter = ("event_type", "created_at", "reconciliation__hotel")
    search_fields = ("event_description", "reconciliation__hotel__name", "csv_filename")
    readonly_fields = ("created_at",)
    
    fieldsets = (
        ("Evento", {
            "fields": ("reconciliation", "event_type", "event_description", "csv_filename")
        }),
        ("Referencias", {
            "fields": ("bank_transaction_id", "payment_id", "payment_type", "reservation_id")
        }),
        ("Detalles", {
            "fields": ("details", "confidence_score")
        }),
        ("Auditoría", {
            "fields": ("created_by", "created_at")
        })
    )