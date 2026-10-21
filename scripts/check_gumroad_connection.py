"""KindGrid Gumroad seller access smoke test (read-only).

Never prints access tokens, account email, full API responses or headers.
Performs GET /v2/user and GET /v2/products only.

Checks slugs rather than product names — slugs are stable; names can be
edited by the owner without updating this file.  At least one slug from
EXPECTED_SLUGS must appear in the live product list for the preflight to pass.
This design tolerates 21+ products and future additions without code changes.
"""
import os
import sys
import requests

BASE = "https://api.gumroad.com/v2"

# Sample of verified live slugs spanning KGS-001 to KGS-022.
# At least one must be present for the preflight to pass.
EXPECTED_SLUGS = {
    "52-week-savings-challenge",
    "market-day-margin-guide",
    "bakeslot-order-capacity-studio",
    "retainer-margin-studio",
    "market-payout-reconciler-studio",
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
        live_slugs = {
            str(p.get("custom_permalink") or p.get("permalink") or p.get("short_url") or "").strip()
            for p in products if isinstance(p, dict)
        }
        found = EXPECTED_SLUGS & live_slugs
        product_count = len(products)
        if not found:
            print(f"GUMROAD_ACCESS_OK: Seller authenticated. {product_count} products found.")
            print("GUMROAD_REVIEW: None of the expected KindGrid slugs matched. Confirm seller account or slug list.")
            return 1
    except RuntimeError as exc:
        print(f"GUMROAD_VERIFY_FAILED: {exc}")
        print("GUMROAD_SAFE: No product was created, edited or published.")
        return 1
    print(f"GUMROAD_CONNECTED: Seller authenticated. {product_count} products found. {len(found)} slug(s) verified.")
    print("GUMROAD_SAFE: No products created, modified, or published.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
