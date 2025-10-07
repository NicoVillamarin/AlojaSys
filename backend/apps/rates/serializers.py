from rest_framework import serializers
from .models import RatePlan, RateRule, RateOccupancyPrice, PromoRule, TaxRule

class RateOccupancyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateOccupancyPrice
        fields = ["id", "occupancy", "price"]

class RateRuleSerializer(serializers.ModelSerializer):
    occupancy_prices = RateOccupancyPriceSerializer(many=True, required=False)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    class Meta:
        model = RateRule
        fields = [
            "id", "plan", "plan_name", "name",
            "start_date", "end_date",
            "apply_mon","apply_tue","apply_wed","apply_thu","apply_fri","apply_sat","apply_sun",
            "target_room","target_room_type","channel","priority",
            "price_mode","base_amount","extra_guest_fee_amount",
            "min_stay","max_stay","closed","closed_to_arrival","closed_to_departure",
            "occupancy_prices",
        ]

    def create(self, validated_data):
        occ = validated_data.pop("occupancy_prices", [])
        rule = super().create(validated_data)
        for o in occ:
            RateOccupancyPrice.objects.create(rule=rule, **o)
        return rule

    def update(self, instance, validated_data):
        occ = validated_data.pop("occupancy_prices", None)
        rule = super().update(instance, validated_data)
        if occ is not None:
            instance.occupancy_prices.all().delete()
            for o in occ:
                RateOccupancyPrice.objects.create(rule=instance, **o)
        return rule

class RatePlanSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)

    class Meta:
        model = RatePlan
        fields = ["id", "hotel", "hotel_name", "name", "code", "is_active", "priority"]


class PromoRuleSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    class Meta:
        model = PromoRule
        fields = [
            "id", "hotel", "hotel_name", "plan", "name", "code",
            "start_date", "end_date",
            "apply_mon","apply_tue","apply_wed","apply_thu","apply_fri","apply_sat","apply_sun",
            "target_room", "target_room_type", "channel",
            "priority", "discount_type", "discount_value", "scope", "combinable", "is_active",
        ]


class TaxRuleSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    class Meta:
        model = TaxRule
        fields = [
            "id", "hotel", "hotel_name", "name", "channel",
            "amount_type", "percent", "fixed_amount", "scope",
            "priority", "is_active"
        ]