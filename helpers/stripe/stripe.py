"""Stripe API helpers (secret key, Bearer auth).

Token comes from `[stripe] token = "sk_test_..."` in `.graft/auth.toml`, or
the `GRAFT_STRIPE_TOKEN` env var. The graft daemon injects it as
`Authorization: Bearer <token>` automatically — Stripe accepts Bearer as an
equivalent to its traditional HTTP Basic scheme, so helpers don't see the
key directly.

Stripe expects form-encoded bodies, not JSON. All write endpoints here pass
fields via `params=` (query string), which Stripe accepts in lieu of a form
body for the resources covered.
"""

from typing import Any

from graft.context import request

_BASE = "https://api.stripe.com/v1"


def list_charges(limit: int = 30) -> list[dict[str, Any]]:
    """List recent charges, newest first.

    Generalization:
        Works for any Stripe account the key authorizes. Cap with `limit` (1-100).
        Variant example: list_charges(limit=10)
        Not applicable: cursor pagination beyond `limit` (use `starting_after`
        manually if you need >100 results); Connect platform charges on other accounts.
    """
    url = f"{_BASE}/charges"
    body = request("stripe", "GET", url, params={"limit": str(limit)}).json()
    return list(body.get("data", []))


def get_charge(charge_id: str) -> dict[str, Any]:
    """Fetch one charge by ID.

    Generalization:
        Works for any charge ID the key can read (typically `ch_...` or `py_...`).
        Variant example: get_charge("ch_3PqR2k2eZvKYlo2C0abc1234")
        Not applicable: charges on connected accounts (needs `Stripe-Account` header).
    """
    url = f"{_BASE}/charges/{charge_id}"
    return dict(request("stripe", "GET", url).json())


def list_customers(
    email: str | None = None, limit: int = 30
) -> list[dict[str, Any]]:
    """List customers, optionally filtered by exact email match.

    Generalization:
        Works for any Stripe account. Pass `email` for exact match (case-insensitive
        per Stripe). Cap with `limit` (1-100).
        Variant example: list_customers(email="user@example.com")
        Not applicable: substring/fuzzy email search (use Stripe's Search API instead).
    """
    url = f"{_BASE}/customers"
    params: dict[str, str] = {"limit": str(limit)}
    if email is not None:
        params["email"] = email
    body = request("stripe", "GET", url, params=params).json()
    return list(body.get("data", []))


def get_customer(customer_id: str) -> dict[str, Any]:
    """Fetch one customer by ID.

    Generalization:
        Works for any customer ID the key can read (`cus_...`).
        Variant example: get_customer("cus_QpR2k2eZvKYlo2C")
        Not applicable: deleted customers return `{"deleted": true, ...}` rather than 404.
    """
    url = f"{_BASE}/customers/{customer_id}"
    return dict(request("stripe", "GET", url).json())


def create_customer(email: str, name: str = "") -> dict[str, Any]:
    """Create a new customer record.

    Generalization:
        Works for any account where the key has write scope. `name` optional.
        Stripe does not enforce email uniqueness — duplicates are allowed.
        Variant example: create_customer("alice@example.com", name="Alice")
        Not applicable: payment-method attachment, tax IDs, addresses, metadata
        (extend this helper or call `/v1/customers/{id}` PATCH endpoints separately).
    """
    url = f"{_BASE}/customers"
    params = {"email": email, "name": name}
    return dict(request("stripe", "POST", url, params=params).json())
