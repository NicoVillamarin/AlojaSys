from django.contrib import admin
from .models import Room

# Register your models here.
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "floor", "room_type", "number", "status", "is_active"]
    list_filter = ["room_type", "status", "is_active"]
    search_fields = ["name", "number"]
    ordering = ("floor", "name")
    list_per_page = 25
    list_editable = ["status", "is_active"]