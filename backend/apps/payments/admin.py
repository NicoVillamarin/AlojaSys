from django.contrib import admin
from .models import PaymentGatewayConfig, PaymentIntent, CancellationPolicy, Refund, RefundLog, RefundVoucher

@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ("provider","enterprise","hotel","is_test","currency_code","refund_window_days","partial_refunds_allowed","is_active","updated_at")
    list_filter = ("provider","is_test","is_active","currency_code","partial_refunds_allowed")
    search_fields = ("enterprise__name","hotel__name","public_key")
    fieldsets = (
        ("Información Básica", {
            "fields": ("provider", "enterprise", "hotel", "is_active")
        }),
        ("Configuración de Acceso", {
            "fields": ("public_key", "access_token", "integrator_id", "webhook_secret")
        }),
        ("Configuración Regional", {
            "fields": ("is_test", "country_code", "currency_code")
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