# Secure Payment System

Mini DRF payment API with idempotency, wallet balance protection, and ledger audit.

## Tech Stack

- Python
- Django
- Django REST Framework
- SimpleJWT
- drf-spectacular
- SQLite for local demo

## Architecture

System design is documented in [docs/architecture.md](docs/architecture.md).

Core decision: small modular monolith with service-layer payment logic. Payment creation uses idempotency key, database transaction, wallet row lock, and ledger entry.

## Endpoints

```text
POST /api/auth/register/
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/wallet/
POST /api/wallet/top-up/
GET  /api/payments/
POST /api/payments/
GET  /api/payments/{id}/
GET  /api/schema/swagger-ui/
```

## Payment Request

```text
POST /api/payments/
Authorization: Bearer <access-token>
Idempotency-Key: client-generated-key
```

```json
{
  "amount": "25.00",
  "currency": "uzs"
}
```

Same `Idempotency-Key` for same user returns same payment and prevents double charge.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

## Tests

```bash
python3 manage.py test
```

## Limitations

- No real bank/provider integration.
- Demo top-up endpoint exists so payment flow can be tested locally.
- SQLite is used by default. PostgreSQL is recommended for real row locking verification.
