from django.contrib import admin
from .models import CleaningStaff, HousekeepingTask, HousekeepingConfig


@admin.register(CleaningStaff)
class CleaningStaffAdmin(admin.ModelAdmin):
    list_display = ["hotel", "first_name", "last_name", "zone", "is_active", "user"]
    list_filter = ["hotel", "is_active", "zone"]
    search_fields = ["first_name", "last_name", "zone"]


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

