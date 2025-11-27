from rest_framework import serializers
from .models import (
    CleaningStaff, HousekeepingTask, HousekeepingConfig,
    CleaningZone, Shift, TaskTemplate, Checklist, ChecklistItem, TaskChecklistCompletion
)


class CleaningZoneSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = CleaningZone
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "name",
            "description",
            "floor",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CleaningStaffSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    shift_display = serializers.CharField(source="get_shift_display", read_only=True)
    cleaning_zones = CleaningZoneSerializer(many=True, read_only=True)
    cleaning_zone_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CleaningZone.objects.all(),
        source="cleaning_zones",
        write_only=True,
        required=False
    )

    class Meta:
        model = CleaningStaff
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "first_name",
            "last_name",
            "zone",
            "shift",
            "shift_display",
            "work_start_time",
            "work_end_time",
            "cleaning_zones",
            "cleaning_zone_ids",
            "is_active",
            "user",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HousekeepingTaskSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    assigned_to_user = serializers.IntegerField(write_only=True, required=False, help_text="ID de UserProfile para asignar staff automáticamente")
    checklist_name = serializers.CharField(source="checklist.name", read_only=True)
    checklist_id = serializers.IntegerField(source="checklist.id", read_only=True)

    class Meta:
        model = HousekeepingTask
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "room",
            "room_name",
            "task_type",
            "status",
            "assigned_to",
            "assigned_to_user",
            "assigned_to_name",
            "notes",
            "priority",
            "zone",
            "checklist",
            "checklist_name",
            "checklist_id",
            "created_by",
            "started_at",
            "completed_at",
            "estimated_minutes",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "checklist_name", "checklist_id"]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name or ''}".strip()
        return None

    def _assign_staff_from_user(self, validated_data):
        profile_id = validated_data.pop("assigned_to_user", None)
        if not profile_id:
            return validated_data
        hotel = validated_data.get("hotel")
        if not hotel:
            # si no se envió hotel en el body, usar el del instance (en update)
            hotel = getattr(self.instance, "hotel", None)
        if not hotel:
            return validated_data
        try:
            from apps.users.models import UserProfile
            from apps.housekeeping.models import CleaningStaff
            profile = UserProfile.objects.select_related("user").get(pk=profile_id)
            cs, _ = CleaningStaff.objects.get_or_create(
                hotel=hotel,
                user=profile.user,
                defaults={
                    "first_name": profile.user.first_name or profile.user.username,
                    "last_name": profile.user.last_name or "",
                    "is_active": True,
                },
            )
            validated_data["assigned_to"] = cs
        except Exception:
            pass
        return validated_data

    def create(self, validated_data):
        validated_data = self._assign_staff_from_user(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._assign_staff_from_user(validated_data)
        return super().update(instance, validated_data)


class HousekeepingConfigSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = HousekeepingConfig
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "enable_auto_assign",
            "create_daily_tasks",
            "daily_generation_time",
            "skip_service_on_checkin",
            "skip_service_on_checkout",
            "linens_every_n_nights",
            "towels_every_n_nights",
            "morning_window_start",
            "morning_window_end",
            "afternoon_window_start",
            "afternoon_window_end",
            "quiet_hours_start",
            "quiet_hours_end",
            "prefer_by_zone",
            "rebalance_every_minutes",
            "checkout_priority",
            "daily_priority",
            "durations",
            "alert_checkout_unstarted_minutes",
            "max_task_duration_minutes",
            "auto_complete_overdue",
            "overdue_grace_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaskTemplateSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)

    class Meta:
        model = TaskTemplate
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "room_type",
            "task_type",
            "task_type_display",
            "name",
            "description",
            "estimated_minutes",
            "is_required",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = [
            "id",
            "checklist",
            "name",
            "description",
            "order",
            "is_required",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChecklistSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    items = ChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Checklist
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "name",
            "description",
            "room_type",
            "task_type",
            "task_type_display",
            "is_default",
            "is_active",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaskChecklistCompletionSerializer(serializers.ModelSerializer):
    checklist_item_name = serializers.CharField(source="checklist_item.name", read_only=True)
    completed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskChecklistCompletion
        fields = [
            "id",
            "task",
            "checklist_item",
            "checklist_item_name",
            "completed",
            "completed_by",
            "completed_by_name",
            "completed_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "completed_at"]

    def get_completed_by_name(self, obj):
        if obj.completed_by:
            return f"{obj.completed_by.first_name} {obj.completed_by.last_name or ''}".strip()
        return None

