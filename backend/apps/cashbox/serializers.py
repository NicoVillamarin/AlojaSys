from decimal import Decimal

from rest_framework import serializers

from .models import CashSession, CashMovement


class CashMovementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = CashMovement
        fields = [
            "id",
            "session",
            "hotel",
            "movement_type",
            "currency",
            "amount",
            "description",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class CashSessionSerializer(serializers.ModelSerializer):
    opened_by_name = serializers.CharField(source="opened_by.username", read_only=True)
    closed_by_name = serializers.CharField(source="closed_by.username", read_only=True)

    # Estos 3 se completan desde la vista (cálculo dinámico)
    cash_payments_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=Decimal("0.00")
    )
    movements_in_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=Decimal("0.00")
    )
    movements_out_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=Decimal("0.00")
    )
    expected_amount_current = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=Decimal("0.00")
    )

    class Meta:
        model = CashSession
        fields = [
            "id",
            "hotel",
            "status",
            "currency",
            "opened_at",
            "opened_by",
            "opened_by_name",
            "opening_amount",
            "closed_at",
            "closed_by",
            "closed_by_name",
            "closing_amount",
            "expected_amount",
            "difference_amount",
            "notes",
            "created_at",
            "updated_at",
            "cash_payments_total",
            "movements_in_total",
            "movements_out_total",
            "expected_amount_current",
        ]
        read_only_fields = [
            "id",
            "status",
            "opened_at",
            "opened_by",
            "closed_at",
            "closed_by",
            "expected_amount",
            "difference_amount",
            "created_at",
            "updated_at",
        ]


class CashSessionOpenSerializer(serializers.Serializer):
    hotel_id = serializers.IntegerField()
    opening_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = serializers.CharField(max_length=3, default="ARS", required=False, allow_blank=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CashSessionCloseSerializer(serializers.Serializer):
    closing_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

