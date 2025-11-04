from django.contrib import admin
from .models import OtaConfig, OtaRoomMapping, OtaSyncJob, OtaSyncLog, OtaImportedEvent, OtaRoomTypeMapping, OtaRatePlanMapping

@admin.register(OtaConfig)
class OtaConfigAdmin(admin.ModelAdmin):
    list_display = ("hotel", "provider", "is_active", "label")
    list_filter = ("provider", "is_active")
    search_fields = ("hotel__name", "label")


@admin.register(OtaRoomMapping)
class OtaRoomMappingAdmin(admin.ModelAdmin):
    list_display = ("hotel", "room", "provider", "external_id", "sync_direction", "last_synced", "is_active")
    list_filter = ("provider", "is_active", "hotel", "sync_direction")
    search_fields = ("room__name", "external_id")


@admin.register(OtaSyncJob)
class OtaSyncJobAdmin(admin.ModelAdmin):
    list_display = ("provider", "job_type", "status", "started_at", "finished_at")
    list_filter = ("provider", "job_type", "status")
    date_hierarchy = "started_at"


@admin.register(OtaSyncLog)
class OtaSyncLogAdmin(admin.ModelAdmin):
    list_display = ("job", "level", "created_at")
    list_filter = ("level", "created_at")
    date_hierarchy = "created_at"


@admin.register(OtaImportedEvent)
class OtaImportedEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "room", "uid", "dtstart", "dtend", "last_seen")
    list_filter = ("provider", "dtstart", "dtend")
    search_fields = ("uid", "room__name")


@admin.register(OtaRoomTypeMapping)
class OtaRoomTypeMappingAdmin(admin.ModelAdmin):
    list_display = ("hotel", "provider", "room_type_code", "provider_code", "is_active")
    list_filter = ("provider", "is_active")
    search_fields = ("room_type_code", "provider_code")


@admin.register(OtaRatePlanMapping)
class OtaRatePlanMappingAdmin(admin.ModelAdmin):
    list_display = ("hotel", "provider", "rate_plan_code", "provider_code", "currency", "is_active")
    list_filter = ("provider", "currency", "is_active")
    search_fields = ("rate_plan_code", "provider_code")