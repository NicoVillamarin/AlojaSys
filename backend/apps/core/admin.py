from django.contrib import admin
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise", "city", "check_in_time", "check_out_time", "auto_check_in_enabled", "is_active")
    search_fields = ("name", "legal_name", "city__name", "enterprise__name")
    list_filter = ("is_active", "auto_check_in_enabled", "city", "enterprise")


 