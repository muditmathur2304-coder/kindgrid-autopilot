"""One-time Gumroad seller CLI draft pilot.

Preview (default): read existing Gumroad products and inspect the already
verified KGS-003 PDF/cover. No external writes.

Explicit live approval: create exactly one *new unpublished test draft* using
copies of the existing KGS-003 files. Never updates or publishes any existing
product. This script must not be retried if an upload has an uncertain result.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

PILOT_NAME = "KindGrid Autopilot Technical Upload Test - Unpublished"
PILOT_SLUG = "kindgrid-autopilot-upload-test-20261009"
PILOT_PDF_ID = "1rHxf3w8vAhHvE9pkJnucnBBxeiU9qEKc"
PILOT_COVER_ID = "1yMwMMKDP4iD5M5DbjPGULvr_gRSkWn8o"
EXPECTED_PRODUCT_NAMES = {
    "52-Week Financial Wellness Savings Challenge Printable",
    "Ultimate 52-Week Savings & Budgeting Planner Bundle",
}
PILOT_DESCRIPTION = (
    "AUTOMATION TEST ONLY — NOT FOR SALE. This unpublished technical test "
    "confirms that the KindGrid Studio publishing agent can securely upload "
    "a PDF and product cover to a brand-new Gumroad draft. The sample files "
    "are copies of an existing KindGrid Studio asset. This listing must stay "
    "unpublished and must never be offered to customers or used for marketing."
)


def seller_command(arguments: list[str]) -> dict:
    # Avoid propagating full CLI stderr or responses into public Actions logs.
    try:
        return a.gumroad_cli(arguments)
    except Exception as exc:
        raise RuntimeError(
            "Gumroad CLI operation failed or returned unexpected data; "
            "inspect Gumroad drafts before any retry. "
            f"Failure category: {type(exc).__name__}"
        ) from None


def assert_unique(existing: list[dict]) -> None:
    known_names = set()
    for product in existing:
        if not isinstance(product, dict):
            continue
        name = str(product.get("name") or "").strip()
        known_names.add(name)
        slug = str(product.get("custom_permalink") or "").strip()
        short_url = str(product.get("short_url") or "")
        if (name == PILOT_NAME or slug == PILOT_SLUG
                or short_url.rstrip("/").endswith("/" + PILOT_SLUG)):
            raise RuntimeError(
                "PILOT_ALREADY_EXISTS: This test draft may have been created "
                "previously. Do not rerun live; inspect Gumroad manually."
            )
    if not EXPECTED_PRODUCT_NAMES.issubset(known_names):
        raise RuntimeError(
            "The authenticated Gumroad account does not contain both known "
            "KindGrid products; upload cancelled."
        )


def check_queued_draft(store: a.GoogleStore) -> None:
    rows = [r for r in store.get_rows("Gumroad Upload Queue")
            if r.get("Product ID") == "KGS-003"]
    if len(rows) != 1 or rows[0].get("Upload Status") != "DRAFT_VERIFIED":
        raise RuntimeError(
            "KGS-003 queue entry was changed or is missing. "
            "Do not upload until existing draft is reconciled."
        )


def main() -> int:
    live = os.getenv("GUMROAD_PILOT_CONFIRM_LIVE", "false").strip().lower() == "true"
    print(f"GUMROAD_DRAFT_PILOT: live={live}; existing products untouched.")
    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64"):
        print("PILOT_BLOCKED: Missing Google service-account secret.")
        return 1
    if not os.getenv("GUMROAD_ACCESS_TOKEN"):
        print("PILOT_BLOCKED: Missing Gumroad seller secret.")
        return 1
    try:
        store = a.GoogleStore()
        check_queued_draft(store)
        response = seller_command(["products", "list", "--all"])
        products = response.get("products")
        if not isinstance(products, list):
            raise RuntimeError("Gumroad product list unavailable; refuse to create draft.")
        assert_unique(products)

        # Check both existing files BEFORE making a Gumroad write.
        pdf = store.get_bytes(PILOT_PDF_ID, "application/pdf")
        cover = store.get_bytes(PILOT_COVER_ID, "image/png")
        pages = a.validate_pdf(pdf)
        width, height = a.validate_image(cover)
        print(f"PILOT_ASSETS_VALID: {pages} PDF pages; cover {width}x{height}.")
        print(f"PILOT_TARGET: {PILOT_NAME} | unique slug={PILOT_SLUG}.")
        if not live:
            print("GUMROAD_PILOT_DRY_RUN_OK: Seller, uniqueness, PDF and cover verified.")
            print("GUMROAD_SAFE: No draft created, no changes made.")
            return 0

        with tempfile.TemporaryDirectory(prefix="kindgrid-gumroad-pilot-") as folder:
            path = Path(folder)
            pdf_path = path / "technical-test.pdf"
            cover_path = path / "technical-test.png"
            pdf_path.write_bytes(pdf)
            cover_path.write_bytes(cover)
            print("GUMROAD_PILOT_CREATING: One unpublished draft; no automatic retry.")
            # --draft is mandatory. There is intentionally NO publish command
            # anywhere in this pilot script.
            created = seller_command([
                "products", "create", "--draft",
                "--name", PILOT_NAME,
                "--price", "5.00", "--currency", "usd", "--type", "digital",
                "--custom-permalink", PILOT_SLUG,
                "--description", PILOT_DESCRIPTION,
                "--file", str(pdf_path), "--cover-image", str(cover_path),
            ])
        product = created.get("product") or {}
        product_id = str(product.get("id") or "").strip()
        if not product_id:
            print("GUMROAD_PILOT_REVIEW: Create result lacked ID; it may have succeeded.")
            print("STOP: Inspect Gumroad draft list. Do not rerun.")
            return 1
        # Display draft edit URL *before* attempting re-read so that any later
        # verification failure can be reconciled without creating duplicates.
        print("GUMROAD_PILOT_DRAFT_EDIT_URL: "
              f"https://gumroad.com/products/{product_id}/edit")
        verified = seller_command(["products", "view", product_id]).get("product") or {}
        if not verified:
            print("GUMROAD_PILOT_REVIEW: Draft readback unavailable. Do not rerun.")
            return 1
        if verified.get("published") is not False:
            print("GUMROAD_PILOT_ALERT: Gumroad did not confirm unpublished status.")
            print("STOP: Inspect draft immediately; do not rerun.")
            return 1
        if str(verified.get("name") or "").strip() != PILOT_NAME:
            print("GUMROAD_PILOT_REVIEW: Draft name mismatch; manual review needed.")
            return 1
        has_file = bool(verified.get("files") or verified.get("rich_content_files"))
        has_cover = bool(verified.get("covers") or verified.get("cover_images"))
        if not (has_file and has_cover):
            print("GUMROAD_PILOT_REVIEW: The draft exists and is unpublished, "
                  "but file/cover fields require manual UI verification. Do not rerun.")
            return 1
        print("GUMROAD_DRAFT_PILOT_PASSED: Unpublished draft, PDF and cover confirmed.")
        print("GUMROAD_SAFE: Existing live products and KGS-003 were never edited.")
        return 0
    except Exception as exc:
        # Avoid showing SDK/server exception bodies that may contain secrets.
        print(f"GUMROAD_PILOT_BLOCKED_OR_REVIEW: {str(exc)}")
        print("Do not rerun live until Gumroad drafts have been inspected.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
