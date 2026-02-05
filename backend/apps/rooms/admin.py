from django.contrib import admin
from .models import Room, RoomType

# Register your models here.
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "sort_order", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]
    ordering = ("sort_order", "name")
    list_per_page = 25

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "floor", "room_type", "number", "status", "cleaning_status", "is_active"]
    list_filter = ["room_type", "status", "cleaning_status", "is_active"]
    search_fields = ["name", "number"]
    ordering = ("floor", "name")
    list_per_page = 25
    list_editable = ["status", "cleaning_status", "is_active"]