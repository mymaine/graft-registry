# stripe

Stripe REST API helpers — list/get charges, list/get/create customers.

5 helpers cover the read-mostly cold-start path for payment + customer
inspection. Add more (subscriptions, invoices, refunds, ...) by editing
`helpers/stripe.py` in your project once `graft add stripe` has dropped
the file in.

## Auth

Get a [secret API key](https://dashboard.stripe.com/apikeys) — `sk_test_...`
for sandbox, `sk_live_...` for production. Store it one of two ways:

```toml
# .graft/auth.toml (gitignored)
[stripe]
token = "sk_test_..."
```

or via environment:

```bash
export GRAFT_STRIPE_TOKEN=sk_test_...
```

The graft daemon injects `Authorization: Bearer <token>` on every helper
call. Stripe traditionally documents HTTP Basic (`<key>:` base64-encoded),
but it equivalently accepts `Bearer <key>` — this helper relies on the
Bearer form so the daemon's default injection works without per-helper
header construction.

## Functions

| Helper | Purpose |
|---|---|
| `list_charges(limit=30)` | List recent charges, newest first |
| `get_charge(charge_id)` | Fetch one charge by `ch_...` ID |
| `list_customers(email=None, limit=30)` | List customers, optional exact email filter |
| `get_customer(customer_id)` | Fetch one customer by `cus_...` ID |
| `create_customer(email, name="")` | Create a new customer record |

All return parsed JSON (`dict` or `list[dict]`) — list endpoints unwrap
Stripe's `{"object": "list", "data": [...]}` envelope and return `data`
directly.

## Example

```python
from helpers.stripe import list_charges, list_customers, create_customer

charges = list_charges(limit=5)
for c in charges:
    print(f"{c['id']}: {c['amount']} {c['currency']}")

existing = list_customers(email="alice@example.com")
if not existing:
    cust = create_customer("alice@example.com", name="Alice")
    print(f"created {cust['id']}")
```

## Rate limits

- Live mode: 100 read req/sec, 100 write req/sec
- Test mode: 25 read req/sec, 25 write req/sec

The daemon does not handle rate-limit retry. On `429`, back off and retry
(Stripe returns `Retry-After` in seconds).

## Not in this helper (extend yourself)

- Subscriptions, invoices, payment intents, refunds, payouts
- Webhooks, events, idempotency keys
- Connect platform calls (need `Stripe-Account` header)
- Search API (`/v1/customers/search`) — only the basic `list` is here
- Pagination beyond `limit` — for >100 results, pass `starting_after=<id>`
