from django.contrib import admin

from .models import CashSession, CashMovement


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "status", "currency", "opened_at", "opened_by", "closed_at", "closed_by")
    list_filter = ("status", "currency", "hotel")
    search_fields = ("hotel__name", "opened_by__username", "closed_by__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "session", "movement_type", "amount", "currency", "created_at", "created_by")
    list_filter = ("movement_type", "currency", "hotel")
    search_fields = ("description", "hotel__name", "created_by__username")
    readonly_fields = ("created_at",)

