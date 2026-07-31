from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Wallet


class WalletAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="ali",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_get_wallet_creates_wallet_for_user(self):
        response = self.client.get("/api/wallet/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Wallet.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("0.00"))

    def test_top_up_wallet(self):
        Wallet.objects.create(user=self.user, balance=Decimal("5.00"), currency="uzs")

        response = self.client.post("/api/wallet/top-up/", {"amount": "20.00"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("25.00"))
