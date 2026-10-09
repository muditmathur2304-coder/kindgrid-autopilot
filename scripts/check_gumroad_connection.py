"""KindGrid Gumroad seller access smoke test (read-only).

Never prints access tokens, account email, full API responses or headers.
Performs GET /v2/user and GET /v2/products only.
"""
import os
import sys
import requests

BASE = "https://api.gumroad.com/v2"
EXPECTED = {
    "52-Week Financial Wellness Savings Challenge Printable",
    "Ultimate 52-Week Savings & Budgeting Planner Bundle",
}


def safe_read(endpoint: str, token: str) -> dict:
    try:
        response = requests.get(
            f"{BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20,
        )
        if response.status_code in (401, 403):
            raise RuntimeError("Gumroad rejected the seller token or its permissions")
        response.raise_for_status()
        data = response.json()
        if data.get("success") is not True:
            raise RuntimeError("Gumroad returned an unsuccessful response")
        return data
    except requests.RequestException:
        raise RuntimeError("Gumroad request failed or timed out") from None
    except (ValueError, AttributeError):
        raise RuntimeError("Gumroad returned unexpected response data") from None


def main() -> int:
    token = os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        print("GUMROAD_SETUP_REQUIRED: Add GUMROAD_ACCESS_TOKEN as a GitHub Actions secret.")
        return 1
    try:
        user_response = safe_read("user", token)
        if not isinstance(user_response.get("user"), dict):
            raise RuntimeError("Gumroad user endpoint returned no account object")
        product_response = safe_read("products", token)
        products = product_response.get("products") or []
        if not isinstance(products, list):
            raise RuntimeError("Gumroad returned an unexpected product-list format")
        existing_names = {
            str(p.get("name", "")).strip() for p in products if isinstance(p, dict)
        }
        missing = EXPECTED - existing_names
        if missing:
            print("GUMROAD_ACCESS_OK: Seller authenticated and product list accessible.")
            print("GUMROAD_REVIEW: One or more expected KindGrid product names not found; confirm seller account.")
            return 1
    except RuntimeError as exc:
        print(f"GUMROAD_VERIFY_FAILED: {exc}")
        print("GUMROAD_SAFE: No product was created, edited or published.")
        return 1
    print("GUMROAD_CONNECTED: Seller account and two existing KindGrid products verified.")
    print("GUMROAD_SAFE: No products created, modified, or published.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
