from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer
from .services import create_payment


class PaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: PaymentSerializer(many=True)}, tags=["payments"])
    def get(self, request):
        payments = (
            Payment.objects.select_related("wallet")
            .filter(user=request.user)
            .order_by("-created_at")
        )
        return Response(PaymentSerializer(payments, many=True).data)

    @extend_schema(
        request=PaymentCreateSerializer,
        responses={201: PaymentSerializer, 200: PaymentSerializer},
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Unique request key. Reusing same key returns same payment without double charging.",
            )
        ],
        tags=["payments"],
        summary="Create payment safely",
    )
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = create_payment(
            user=request.user,
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data["currency"],
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        response_status = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
        return Response(PaymentSerializer(result.payment).data, status=response_status)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: PaymentSerializer}, tags=["payments"])
    def get(self, request, pk):
        try:
            payment = Payment.objects.select_related("wallet").get(pk=pk, user=request.user)
        except Payment.DoesNotExist:
            raise NotFound("Payment not found.")

        return Response(PaymentSerializer(payment).data)
