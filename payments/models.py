from django.db import models
from django.conf import settings
from django.db.models import Q
from wallets.models import Wallet
# `Payment`

# - `user`: payment egasi;
# - `wallet`: qaysi walletdan yechiladi;
# - `amount`: DecimalField;
# - `currency`;
# - `status`: `pending/succeeded/failed`;
# - `idempotency_key`: client yuboradigan unique kalit;
# - `failure_reason`;
# - `created_at`, `updated_at`.

# Muhim constraint:

# - `user + idempotency_key` unique bo'lishi kerak.

class PaymentStatusChoice(models.TextChoices):
    PENDING = "pending", "Jarayonda"
    SUCCEEDED = "succeeded", "Muvaffaqiyatli"
    FAILED = "failed", "Muvaffaqiyatsiz"


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet,on_delete=models.SET_NULL,null=True,blank=True)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    currency = models.CharField(max_length=3,default='uzs')
    status = models.CharField(max_length=20,choices=PaymentStatusChoice.choices,default=PaymentStatusChoice.PENDING)
    idempotency_key = models.CharField(max_length=300)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of: {self.user.get_full_name()} amount: {self.amount} | payed at: {self.created_at}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user','idempotency_key'],
                name='user_idm_key'
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='payment_amount_positive'
            )
        ]


class LedgerDirectionChoice(models.TextChoices):
    MONEY_OUT = "money_out", "Money out"
    MONEY_IN = "money_in", "Money in"


class LedgerEntry(models.Model):
    wallet = models.ForeignKey(Wallet,on_delete=models.PROTECT,related_name='ledger_entries')
    payment = models.ForeignKey(Payment,on_delete=models.PROTECT,related_name='ledger_entries')
    direction = models.CharField(max_length=10,choices=LedgerDirectionChoice.choices)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    balance_before = models.DecimalField(max_digits=12,decimal_places=2)
    balance_after = models.DecimalField(max_digits=12,decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.direction} {self.amount} for payment {self.payment_id}"
