from django.contrib import admin
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    search_fields = ("name", "legal_name", "city__name")
    list_filter = ("is_active", "city")