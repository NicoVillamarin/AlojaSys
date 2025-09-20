from django.contrib import admin
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "is_active")
    search_fields = ("name", "legal_name", "city", "country")
    list_filter = ("is_active",)