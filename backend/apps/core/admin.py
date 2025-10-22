from django.contrib import admin
from django.utils.html import format_html
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise", "city", "check_in_time", "check_out_time", "auto_check_in_enabled", "logo_preview", "is_active")
    search_fields = ("name", "legal_name", "city__name", "enterprise__name")
    list_filter = ("is_active", "auto_check_in_enabled", "city", "enterprise")
    fields = (
        "enterprise", "name", "legal_name", "tax_id", "email", "phone", "address",
        "country", "state", "city", "timezone", "check_in_time", "check_out_time",
        "auto_check_in_enabled", "auto_no_show_enabled", "logo", "is_active"
    )
    
    def logo_preview(self, obj):
        """Muestra una vista previa del logo en la lista"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: contain;" />',
                obj.logo.url
            )
        return "Sin logo"
    logo_preview.short_description = "Logo"


 