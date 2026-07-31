from .serializers import SignUpResponseSerializer, SignUpSerializer
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from wallets.models import Wallet

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignUpSerializer,
        responses={201: SignUpResponseSerializer},
        tags=['auth'],
        summary="Register new user",
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "username": "ali",
                    "email": "ali@example.com",
                    "password": "testpass123",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "address": "Tashkent",
                    "age": 22
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        Wallet.objects.get_or_create(user=user,defaults={"balance": 0, "currency": "uzs"})
        return Response({
            "message": "Ro'yxatdan o'tdingiz",
            "user": SignUpSerializer(user).data
        }, status=status.HTTP_201_CREATED)
