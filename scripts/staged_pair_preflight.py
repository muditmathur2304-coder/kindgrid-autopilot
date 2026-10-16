"""READ ONLY: independently inspect proposed KGS020/021 staged assets and providers.

Scheduled by the EXISTING two-hour publisher, not a new automation.
Never creates products/posts, marks QA, or edits any Google Sheet.
Failures are reported as holds, not retried against sellers.
"""
from __future__ import annotations

import io
import os
from zipfile import ZipFile

from src import autopilot as a
from src.paired_release import validate_tool_xlsx

STAGED_ASSETS = {
    "KGS020_PAID_XLSX": ("1j3R_-E1KURkDCySPQTkwaiSS65_mWTJa",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "KGS020_GUIDE": ("1loOWZHvU1aiUeqsyRJ3G17NturvRU79r", "application/pdf"),
    "KGS021_FREE_PDF": ("1fPOiQLQPYZ7s_PZ6MkS0ay4SqQxaUFGy", "application/pdf"),
    "KGS020_COVER": ("1bOEOgM_VNoLFmSw9m-1sIIJ9NFgaZlR7", "image/png"),
    "KGS021_COVER": ("10DGxnD5XYRwSI_9Pd0NOegz1eeVTjDNn", "image/png"),
    "KGS020_GALLERY_ONE": ("1Qf-BmgfN9fp30u6mVosbYBCtvCgrORoq", "image/png"),
    "KGS020_GALLERY_TWO": ("1Y3i9TO3EbU0aIaOIdeqDTyP8h-c7qLwL", "image/png"),
    "KGS021_GALLERY": ("11VsxZt_JdykX8AsKNW4oE67uPptsYjaV", "image/png"),
    "KGS020_CONTACT": ("18qsA1iMnkX08wvxc3cmg-x6HKE9PWec-", "image/png"),
    "KGS021_CONTACT": ("1izyNiye62fUn5FwSE0XwUi1XdP54yC8_", "image/png"),
}
REQUIRED_DOCS = {
    "KGS020_LISTING": "1G9Bof_QN-dvY3a0XXc3q3msJo3MOIquC76LPUpZeEac",
    "KGS021_LISTING": "1wymxtss3IhzNNgN_9Ml9Tj-ukO0shSpCDM_MQJ0cCn0",
    "RESEARCH": "1wnCRwQvEbtdf772JGk1OfGH9kwkrSzBoJKwdTrGqEYY",
    "KGS020_QA_HOLD": "1Nv72BSaFOGRMB4LnIr7b_gzKf9gIiV33ZOJU90py-2U",
    "KGS021_QA_HOLD": "1amdRpWs690KlfDKvCoxpqmRJnXe5KB8m11HPrdRVxN4",
}

def check_assets() -> None:
    try:
        store = a.GoogleStore()
    except Exception as exc:
        print("STAGED_DRIVE_AUTH_BLOCKED:", type(exc).__name__)
        return
    for label, (file_id, mime) in STAGED_ASSETS.items():
        try:
            content = store.get_bytes(file_id, mime)
            if label.endswith("XLSX"):
                validate_tool_xlsx(content, label)
            elif label.endswith("GUIDE") or label.endswith("PDF"):
                pages = a.validate_pdf(content)
                a.require(pages == (3 if label == "KGS020_GUIDE" else 4),
                          "Wrong instructional guide page count")
            elif label.endswith("CONTACT"):
                from PIL import Image
                with Image.open(io.BytesIO(content)) as image:
                    image.verify()
                    a.require(image.width >= 850 and image.height >= 500,
                              "Contact sheet too small")
            else:
                a.validate_image(content)
            print(f"STAGED_DRIVE_PASS: {label}")
        except Exception as exc:
            print(f"STAGED_DRIVE_BLOCKED: {label}: {type(exc).__name__}")

    for label, doc_id in REQUIRED_DOCS.items():
        try:
            content = store.get_doc_text(doc_id)
            a.require(len(content.strip()) >= 350, "Doc missing substantive content")
            print(f"STAGED_DOC_READ_PASS: {label}")
        except Exception as exc:
            print(f"STAGED_DOC_READ_BLOCKED: {label}: {type(exc).__name__}")

def check_buffer() -> None:
    try:
        client = a.BufferClient()
        boards = client.boards()
        queued = client.scheduled()
        print(f"STAGED_BUFFER_QUEUE_READ_PASS: {queued}/10")
        print("STAGED_BOARDS_AVAILABLE: " + " | ".join(sorted(boards.keys())))
        for name in ("Freelancer Pricing & Cash Flow",
                     "Freelancer Budgeting & Irregular Income",
                     "Farmers Market Bakery Business Tips"):
            if name in boards:
                print("STAGED_BOARD_VERIFIED: " + name)
            else:
                print("STAGED_BOARD_MISSING: " + name)
    except Exception as exc:
        print("STAGED_BUFFER_PREFLIGHT_BLOCKED:", type(exc).__name__)

def check_seller_slugs() -> None:
    token = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        print("STAGED_GUMROAD_READ_BLOCKED: Token not configured")
        return
    try:
        import requests
        response = requests.get("https://api.gumroad.com/v2/products",
                                headers={"Authorization": "Bearer " + token,
                                         "Accept": "application/json"},
                                timeout=20)
        a.require(response.status_code == 200, "Non-200 Gumroad GET")
        payload = response.json()
        a.require(payload.get("success") is True and isinstance(payload.get("products"), list),
                  "Unverified seller product list")
        products = payload["products"]
        print("STAGED_GUMROAD_PRODUCT_COUNT: " + str(len(products)))
        slugs = set()
        for product in products:
            if not isinstance(product, dict):
                continue
            slugs.add(str(product.get("custom_permalink") or ""))
            slugs.add(str(product.get("short_url") or "").split("/")[-1])
        for key in ("retainer-margin-studio", "retainer-one-contract-reality-check-free"):
            print(("STAGED_GUMROAD_SLUG_COLLISION: " if key in slugs
                   else "STAGED_GUMROAD_SLUG_AVAILABLE_IN_LIST: ") + key)
        # Existing live funnels are safe only when seller confirms current public status.
        for expected_slug in ("paycheck-gap-starter", "paycheck-gap-playbook"):
            matching = [p for p in products if isinstance(p, dict)
                        and (str(p.get("custom_permalink") or "") == expected_slug
                             or str(p.get("short_url") or "").rstrip("/").split("/")[-1] == expected_slug)]
            if len(matching) == 1 and matching[0].get("published") is True:
                print("STAGED_EXISTING_LIVE_CONFIRMED: " + expected_slug)
            elif len(matching) == 1:
                print("STAGED_EXISTING_PRODUCT_NOT_PUBLISHED: " + expected_slug)
            else:
                print("STAGED_EXISTING_PRODUCT_NOT_UNIQUE: " + expected_slug)
        # Log only public matching titles and publish flags (never seller IDs/tokens).
        for expected_name in ("The Paycheck Gap Playbook", "FREE Paycheck Gap Starter"):
            found = [p for p in products if isinstance(p, dict)
                     and expected_name.lower() in str(p.get("name") or "").lower()]
            print("STAGED_EXISTING_TITLE_MATCH: " + expected_name +
                  f" count={len(found)} published={','.join(str(p.get('published')) for p in found)}")
        for slug in ("paycheck-gap-starter", "paycheck-gap-playbook"):
            try:
                a.verify_public_product_url("https://kindgridstudio.gumroad.com/l/" + slug, slug)
                print("STAGED_PUBLIC_GUMROAD_PAGE_PASS: " + slug)
            except Exception as exc:
                print("STAGED_PUBLIC_GUMROAD_PAGE_BLOCKED: " + slug + " " + type(exc).__name__)
        print("STAGED_GUMROAD_READ_OK: Seller product list available")
    except Exception as exc:
        print("STAGED_GUMROAD_READ_BLOCKED:", type(exc).__name__)


def check_live_release_candidates() -> None:
    """Full read-only dry preflight of existing dashboard READY rows.

    This does not authorize or create any seller/Buffer mutation.
    """
    from datetime import datetime, timezone
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from src.paired_release import select_ready_pairs, prepare_pair
    try:
        store = a.GoogleStore()
        gumrows = store.get_rows("Gumroad Upload Queue")
        pairs = select_ready_pairs(gumrows)
        print("STAGED_PAIRS_READY_COUNT: " + str(len(pairs)))
        for paid, free in pairs:
            if (paid.get("Product ID"), free.get("Product ID")) != ("KGS-020", "KGS-021"):
                continue
            try:
                with TemporaryDirectory(prefix="kindgrid-readonly-pair-") as folder:
                    prepared = prepare_pair(store, paid, free, Path(folder))
                    for role, item in prepared.items():
                        print("STAGED_FULL_PAIR_ASSETS_PASS: " + role +
                              " pages=" + str(item.get("pages")) +
                              " preview_count=" + str(len(item.get("previews"))) +
                              " xlsx=" + str(bool(item.get("bonus"))))
            except Exception as exc:
                print("STAGED_FULL_PAIR_ASSETS_BLOCKED: " + type(exc).__name__ +
                      ": " + str(exc)[:180])
        pins = store.get_rows("Publishing Queue")
        boards = a.BufferClient().boards()
        queued = a.BufferClient().scheduled()
        for row in pins:
            if row.get("Queue ID") not in ("Q-65", "Q-66"):
                continue
            try:
                pin = a.validate_pin(row, datetime.now(timezone.utc), 36)
                a.verify_qa_report(store, row, row["Queue ID"])
                a.require(pin["board"] in boards, "Pinterest board not found")
                a.require(queued < 10, "Buffer queue full")
                a.verify_public_product_url(pin["destination"])
                a.validate_image(store.get_bytes(pin["image_id"], "image/png"))
                print("STAGED_PIN_FULL_PREFLIGHT_PASS: " + row["Queue ID"])
            except Exception as exc:
                print("STAGED_PIN_FULL_PREFLIGHT_BLOCKED: " + row.get("Queue ID", "?") +
                      " " + type(exc).__name__ + ": " + str(exc)[:180])
    except Exception as exc:
        print("STAGED_RELEASE_READONLY_PREFLIGHT_ERROR: " + type(exc).__name__ +
              ": " + str(exc)[:200])

def main() -> int:
    print("KINDGRID_STAGED_PREFLIGHT_READ_ONLY: no seller/Buffer/Sheets mutation")
    check_assets()
    check_buffer()
    check_seller_slugs()
    check_live_release_candidates()
    print("STAGED_PREFLIGHT_ONLY: This is NOT KGS-QA-V2 PASS or release authorization")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
