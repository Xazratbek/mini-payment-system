from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Wallet
from .serializers import WalletSerializer, WalletTopUpSerializer


class WalletDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: WalletSerializer}, tags=["wallet"])
    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(
            user=request.user,
            defaults={"balance": 0, "currency": "uzs"},
        )
        return Response(WalletSerializer(wallet).data)


class WalletTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=WalletTopUpSerializer,
        responses={200: WalletSerializer},
        tags=["wallet"],
        summary="Top up authenticated user's wallet",
    )
    def post(self, request):
        serializer = WalletTopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(
                user=request.user,
                defaults={"balance": 0, "currency": "uzs"},
            )
            wallet.balance += serializer.validated_data["amount"]
            wallet.save(update_fields=["balance", "updated_at"])

        return Response(WalletSerializer(wallet).data, status=status.HTTP_200_OK)
