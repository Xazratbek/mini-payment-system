from dataclasses import dataclass
from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from wallets.models import Wallet

from .models import LedgerDirectionChoice, LedgerEntry, Payment, PaymentStatusChoice


@dataclass(frozen=True)
class PaymentResult:
    payment: Payment
    created: bool


def create_payment(*, user, amount: Decimal, currency: str, idempotency_key: str) -> PaymentResult:
    if not idempotency_key:
        raise ValidationError({"Idempotency-Key": "This header is required."})

    try:
        with transaction.atomic():
            existing_payment = (
                Payment.objects.select_for_update()
                .select_related("wallet")
                .filter(user=user, idempotency_key=idempotency_key)
                .first()
            )
            if existing_payment:
                return PaymentResult(payment=existing_payment, created=False)

            wallet, _ = Wallet.objects.select_for_update().get_or_create(
                user=user,
                defaults={"balance": 0, "currency": currency},
            )

            payment = Payment.objects.create(
                user=user,
                wallet=wallet,
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
                status=PaymentStatusChoice.PENDING,
            )

            if wallet.currency != currency:
                payment.status = PaymentStatusChoice.FAILED
                payment.failure_reason = "Currency mismatch."
                payment.save(update_fields=["status", "failure_reason", "updated_at"])
                return PaymentResult(payment=payment, created=True)

            if wallet.balance < amount:
                payment.status = PaymentStatusChoice.FAILED
                payment.failure_reason = "Insufficient balance."
                payment.save(update_fields=["status", "failure_reason", "updated_at"])
                return PaymentResult(payment=payment, created=True)

            balance_before = wallet.balance
            balance_after = balance_before - amount
            wallet.balance = balance_after
            wallet.save(update_fields=["balance", "updated_at"])

            payment.status = PaymentStatusChoice.SUCCEEDED
            payment.save(update_fields=["status", "updated_at"])

            LedgerEntry.objects.create(
                wallet=wallet,
                payment=payment,
                direction=LedgerDirectionChoice.MONEY_OUT,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
            )

            return PaymentResult(payment=payment, created=True)
    except IntegrityError:
        payment = Payment.objects.select_related("wallet").get(
            user=user,
            idempotency_key=idempotency_key,
        )
        return PaymentResult(payment=payment, created=False)
