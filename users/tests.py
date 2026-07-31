from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from wallets.models import Wallet


class RegisterAPITests(TestCase):
    def test_register_creates_user_and_wallet(self):
        client = APIClient()

        response = client.post(
            "/api/auth/register/",
            {
                "username": "ali",
                "email": "ali@example.com",
                "password": "testpass123",
                "first_name": "Ali",
                "last_name": "Valiyev",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username="ali")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(Wallet.objects.filter(user=user).exists())
