from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from wallets.models import Wallet

from .models import LedgerEntry, Payment, PaymentStatusChoice


class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="ali",
            email="ali@example.com",
            password="testpass123",
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal("100.00"),
            currency="uzs",
        )
        self.client.force_authenticate(self.user)

    def test_create_payment_debits_wallet_and_writes_ledger(self):
        response = self.client.post(
            "/api/payments/",
            {"amount": "25.00", "currency": "uzs"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="pay-1",
        )

        self.assertEqual(response.status_code, 201)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("75.00"))

        payment = Payment.objects.get(id=response.data["id"])
        self.assertEqual(payment.status, PaymentStatusChoice.SUCCEEDED)
        self.assertEqual(LedgerEntry.objects.filter(payment=payment).count(), 1)

    def test_same_idempotency_key_does_not_double_charge(self):
        payload = {"amount": "25.00", "currency": "uzs"}

        first_response = self.client.post(
            "/api/payments/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-key",
        )
        second_response = self.client.post(
            "/api/payments/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-key",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.data["id"], second_response.data["id"])
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("75.00"))
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_insufficient_balance_fails_without_debit(self):
        response = self.client.post(
            "/api/payments/",
            {"amount": "150.00", "currency": "uzs"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="too-large",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], PaymentStatusChoice.FAILED)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("100.00"))
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_user_cannot_read_other_user_payment(self):
        other_user = get_user_model().objects.create_user(
            username="vali",
            password="testpass123",
        )
        other_wallet = Wallet.objects.create(
            user=other_user,
            balance=Decimal("10.00"),
            currency="uzs",
        )
        payment = Payment.objects.create(
            user=other_user,
            wallet=other_wallet,
            amount=Decimal("5.00"),
            currency="uzs",
            idempotency_key="other-key",
            status=PaymentStatusChoice.SUCCEEDED,
        )

        response = self.client.get(f"/api/payments/{payment.id}/")

        self.assertEqual(response.status_code, 404)

    def test_idempotency_key_is_required(self):
        response = self.client.post(
            "/api/payments/",
            {"amount": "10.00", "currency": "uzs"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Idempotency-Key", response.data)
