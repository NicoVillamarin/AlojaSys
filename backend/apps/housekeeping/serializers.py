from rest_framework import serializers
from .models import CleaningStaff, HousekeepingTask, HousekeepingConfig


class CleaningStaffSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = CleaningStaff
        fields = [
            "id",
            "hotel",
            "hotel_name",
            "first_name",
            "last_name",
            "zone",
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
            "created_by",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

