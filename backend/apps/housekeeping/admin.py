from django.contrib import admin
from .models import (
    CleaningStaff, HousekeepingTask, HousekeepingConfig,
    CleaningZone, TaskTemplate, Checklist, ChecklistItem, TaskChecklistCompletion
)


@admin.register(CleaningZone)
class CleaningZoneAdmin(admin.ModelAdmin):
    list_display = ["hotel", "name", "floor", "is_active"]
    list_filter = ["hotel", "is_active"]
    search_fields = ["name", "description"]


@admin.register(CleaningStaff)
class CleaningStaffAdmin(admin.ModelAdmin):
    list_display = ["hotel", "first_name", "last_name", "shift", "zone", "is_active", "user"]
    list_filter = ["hotel", "is_active", "shift", "zone"]
    search_fields = ["first_name", "last_name", "zone"]
    filter_horizontal = ["cleaning_zones"]


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ["hotel", "room", "task_type", "status", "assigned_to", "priority", "created_at"]
    list_filter = ["hotel", "task_type", "status", "assigned_to"]
    search_fields = ["room__name", "notes"]


@admin.register(HousekeepingConfig)
class HousekeepingConfigAdmin(admin.ModelAdmin):
    list_display = ["hotel", "enable_auto_assign", "create_daily_tasks", "daily_generation_time", "checkout_priority", "daily_priority"]
    list_filter = ["enable_auto_assign", "create_daily_tasks"]
    search_fields = ["hotel__name"]


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ["hotel", "room_type", "task_type", "name", "estimated_minutes", "is_required", "order", "is_active"]
    list_filter = ["hotel", "room_type", "task_type", "is_required", "is_active"]
    search_fields = ["name", "description"]


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ["name", "description", "order", "is_required", "is_active"]


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ["hotel", "name", "room_type", "task_type", "is_default", "is_active"]
    list_filter = ["hotel", "room_type", "task_type", "is_default", "is_active"]
    search_fields = ["name", "description"]
    inlines = [ChecklistItemInline]


@admin.register(TaskChecklistCompletion)
class TaskChecklistCompletionAdmin(admin.ModelAdmin):
    list_display = ["task", "checklist_item", "completed", "completed_by", "completed_at"]
    list_filter = ["completed", "completed_at"]
    search_fields = ["task__room__name", "checklist_item__name"]

