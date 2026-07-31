from django.db import models
from django.conf import settings
from django.db.models import Q

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12,decimal_places=2)
    currency = models.CharField(max_length=3,default='uzs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s balance: {self.balance}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_user'
            ),
            models.CheckConstraint(
                condition=Q(balance__gte=0),
                name='wallet_balance_non_negative'
            )
        ]
