from django.contrib import admin
from .models import PaymentGatewayConfig, PaymentIntent

@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ("provider","enterprise","hotel","is_test","currency_code","is_active","updated_at")
    list_filter = ("provider","is_test","is_active","currency_code")
    search_fields = ("enterprise__name","hotel__name","public_key")

@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("id","reservation","hotel","amount","currency","status","created_at")
    list_filter = ("status","currency")
    search_fields = ("reservation__id","mp_payment_id","mp_preference_id","external_reference")