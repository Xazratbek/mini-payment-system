from rest_framework import serializers

from .models import LedgerEntry, Payment


class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    currency = serializers.ChoiceField(choices=["uzs"], default="uzs")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "wallet",
            "amount",
            "currency",
            "status",
            "idempotency_key",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "wallet",
            "payment",
            "direction",
            "amount",
            "balance_before",
            "balance_after",
            "created_at",
        ]
        read_only_fields = fields

