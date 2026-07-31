## Qisqa Arxitektura

Loyiha kichik DRF modular monolith:

- `users`: register va JWT token.
- `wallets`: user balansi.
- `payments`: payment yaratish, idempotency, ledger audit.

Payment biznes logic view ichida emas, `payments/services.py` ichida turadi. View HTTP request/response bilan ishlaydi. Service esa balance, idempotency, transaction va ledger bilan ishlaydi.

Client
  |
  | POST /api/payments/
  | Authorization: Bearer <token>
  | Idempotency-Key: unique-request-key
  v
DRF PaymentListCreateView
  |
  v
PaymentCreateSerializer
  |
  v
create_payment() service
  |
  v
transaction.atomic()
  |
  +--> existing Payment check: user + idempotency_key
  |
  +--> Wallet row lock: select_for_update()
  |
  +--> balance validation
  |
  +--> Payment status update
  |
  +--> LedgerEntry audit
  v
Response: 201 new payment yoki 200 duplicate result

## Takroriy So'rovlarni Qanday Ushlaymiz?

Payment yaratishda client `Idempotency-Key` header yuboradi:

Idempotency-Key: pay-20260731-001

Backend shu keyni payment bilan saqlaydi. Database darajasida bu constraint bor:

Payment.user + Payment.idempotency_key = unique

Ya'ni bitta user bir xil idempotency key bilan faqat bitta payment yarata oladi.

Jarayon:

1. Client payment request yuboradi.
2. Backend user + idempotency_key bo'yicha oldingi paymentni qidiradi.
3. Agar payment topilsa:
   - yangi payment yaratilmaydi
   - walletdan pul qayta yechilmaydi
   - oldingi payment qaytariladi
   - response status 200 bo'ladi
4. Agar payment topilmasa:
   - yangi payment yaratiladi
   - wallet balance tekshiriladi
   - balance yetarli bo'lsa pul yechiladi
   - response status 201 bo'ladi

Nega bu kerak:

Client payment yubordi.
Internet uzildi yoki timeout bo'ldi.
Client "payment o'tmadimikan" deb yana yubordi.
Idempotency bo'lmasa pul 2 marta yechiladi.
Idempotency bilan 2-request eski paymentni qaytaradi.

Koddagi asosiy joy:

existing_payment = (
    Payment.objects.select_for_update()
    .select_related("wallet")
    .filter(user=user, idempotency_key=idempotency_key)
    .first()
)
if existing_payment:
    return PaymentResult(payment=existing_payment, created=False)

Parallel request holatida `UniqueConstraint` oxirgi himoya sifatida ishlaydi. Ikki request bir vaqtda bir xil key bilan kirsa, database faqat bittasini o'tkazadi.

## Bazani Qanday Himoya Qilamiz?

Payment tizimda eng xavfli joy balance update. Shu sabab himoya bir nechta qatlamda qilingan.

### 1. Atomic Transaction

Payment yaratish, wallet balance update, audit log yozish bitta transaction ichida bajariladi:

with transaction.atomic():

Foydasi:

- payment yaratilib, balance update bo'lmay qolmaydi;
- balance update bo'lib, audit log yozilmay qolmaydi;
- xatolik bo'lsa hammasi rollback bo'ladi.

### 2. Wallet Row Lock

Wallet balance o'zgartirilishidan oldin row lock qilinadi:

Wallet.objects.select_for_update().get_or_create(...)

Foydasi:

User balance: 100
Request A: 80 yechmoqchi
Request B: 80 yechmoqchi

Lock bo'lmasa:
  A ham 100 ko'radi
  B ham 100 ko'radi
  ikkalasi ham o'tib ketishi mumkin

Lock bilan:
  A wallet rowni lock qiladi
  B kutadi
  A balance 20 qilib commit qiladi
  B keyin 20 ko'radi va failed bo'ladi

### 3. DecimalField

Pul fieldlari `DecimalField`:

amount = models.DecimalField(max_digits=12, decimal_places=2)
balance = models.DecimalField(max_digits=12, decimal_places=2)

Foydasi:

- pul hisobida float precision xatosi bo'lmaydi;
- `100.10 - 25.05` kabi hisoblar aniqroq.

### 4. Database Constraints

Wallet balance manfiy bo'lmasligi kerak:

models.CheckConstraint(
    condition=Q(balance__gte=0),
    name='wallet_balance_non_negative'
)

Payment amount 0 dan katta bo'lishi kerak:

models.CheckConstraint(
    condition=Q(amount__gt=0),
    name='payment_amount_positive'
)

Idempotency uchun unique constraint:

models.UniqueConstraint(
    fields=['user', 'idempotency_key'],
    name='user_idm_key'
)

Bu constraintlar serializerdan tashqari database darajasida ham himoya beradi.

### 5. User Scope

Payment list/detail faqat current user bo'yicha filter qiladi:

Payment.objects.filter(user=request.user)
Payment.objects.get(pk=pk, user=request.user)

Foydasi:

- user boshqa user paymentini ko'ra olmaydi;
- boshqa user payment IDsi ma'lum bo'lsa ham `404` qaytadi.

### 6. Audit Log

Har muvaffaqiyatli payment uchun `LedgerEntry` yoziladi:

wallet
payment
direction = money_out
amount
balance_before
balance_after
created_at

Foydasi:

- balance nima sabab o'zgargani ko'rinadi;
- payment tarixini tekshirish mumkin;
- debugging va audit osonlashadi.

## Payment Status Flow

```text
          +---------+
          | pending |
          +----+----+
               |
       +-------+-------+
       |               |
       v               v
+-----------+     +--------+
| succeeded |     | failed |
+-----------+     +--------+
```

`succeeded` bo'lishi uchun shu shartlar qanoatlantirilishi kerak:

- wallet currency request currencyga teng;
- wallet balance yetarli;
- wallet balance kamaygan;
- ledger entry yozilgan.

`failed` bo'lishi mumkin:

- balance yetmasa;
- currency mos kelmasa.

## Xulosa

Takroriy so'rovlar `Idempotency-Key` va `user + idempotency_key` unique constraint orqali ushlanadi.

Baza `transaction.atomic()`, `select_for_update()`, `DecimalField`, `CheckConstraint`, `UniqueConstraint`, user-scoped queries va `LedgerEntry` audit orqali himoyalanadi.

SQLite local demo uchun yetarli. Real concurrency tekshiruv uchun PostgreSQL kerak, chunki `select_for_update()` row-level lockni PostgreSQLda to'liq ko'rsatadi.
