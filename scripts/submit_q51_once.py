"""Owner-approved one-off Q-51 Pin upload; no historical Pins or Gumroad products touched.

Safety:
- Existing LIVE KGS-007 destination only.
- Q-51 must be fresh, individually QA-PASS and not previously submitted.
- Verify destination, source image, Buffer board and quota BEFORE submission.
- One Buffer POST, no retries when outcome is ambiguous.
"""
from __future__ import annotations
import os
import sys
import json
from datetime import datetime, timezone
sys.path.insert(0, ".")
from src import autopilot as a

PIN = "Q-51"
PRODUCT = "KGS-007"
LINK = "https://kindgridstudio.gumroad.com/l/paycheck-gap-starter"
BOARD = "Budgeting Printables & Cash Stuffing"
ARTWORK = "1TCTmdRET6GyUvJqm9XQPvgW525nU8r4X"

def main() -> int:
    a.require(os.getenv("KINDGRID_Q51_OWNER_APPROVED") == "true", "Missing specific owner approval")
    store = a.GoogleStore()
    pins = [x for x in store.get_rows("Publishing Queue") if x.get("Queue ID") == PIN]
    a.require(len(pins) == 1, "Q51 missing or duplicated; no submission")
    row = pins[0]
    a.require(row.get("Status") == "READY", "Q51 not READY or already attempted; never resubmit")
    a.require(not row.get("Batch ID") and not row.get("Actual Pinterest Pin URL"),
              "Existing Buffer / Pinterest post reference; do not duplicate")
    a.require(row.get("Product") == PRODUCT and row.get("Destination URL") == LINK,
              "Product/destination mismatch")
    a.require(row.get("Pin Image Drive Link") ==
              "https://drive.google.com/file/d/" + ARTWORK + "/view", "Source artwork changed")
    a.require(row.get("QA Verified (YES/NO)") == "YES", "Visual audit not approved")
    a.verify_qa_report(store, row, PIN)
    candidate = a.validate_pin(row, datetime.now(timezone.utc), 96)
    a.require(candidate["image_id"] == ARTWORK and candidate["board"] == BOARD,
              "Wrong image or board")
    # The exact scheduled slot is protected from time drift.
    from zoneinfo import ZoneInfo
    local = candidate["due"].astimezone(ZoneInfo("America/New_York"))
    a.require(local.strftime("%Y-%m-%d %H:%M %Z") == "2026-10-11 20:30 EDT",
              "Expected US slot no longer matches")

    prows = [p for p in store.get_rows("Gumroad Upload Queue") if p.get("Product ID") == PRODUCT]
    a.require(len(prows) == 1 and prows[0].get("Upload Status") == "PUBLISHED"
              and prows[0].get("Gumroad Live URL") == LINK,
              "Existing free product not confirmed live")
    a.verify_public_product_url(LINK, "paycheck-gap-starter")
    raw = store.get_bytes(ARTWORK, "image/png")
    w, h = a.validate_image(raw)
    a.require((w, h) == (1000, 1500), "Incorrect final creative dimensions")

    client = a.BufferClient()
    boards = client.boards()
    a.require(BOARD in boards, "Pinterest board not connected")
    count = client.scheduled()
    a.require(count < 10, "Buffer free queue at capacity")
    # First external media write is Cloudinary. Q51 public_id is unique.
    image_url = a.cloudinary_upload(raw, "q51-kgs007-late-invoice-check-once")
    a.require(image_url.startswith("https://res.cloudinary.com/"),
              "Cloudinary image upload not verified")

    store.patch("Publishing Queue", row, {
        "Status": "SCHEDULING",
        "Last Error": "Q51 one-time Buffer attempt in progress; NEVER blindly retry",
        "Last Attempt UTC": a.make_timestamp(),
        "Attempt Count": "1",
    })
    print("Q51_BUFFER_ATTEMPT_STARTED_DO_NOT_RETRY")
    try:
        post = client.create(candidate, image_url, boards[BOARD])
    except Exception as exc:
        store.patch("Publishing Queue", row, {
            "Status": "LINK_REVIEW",
            "Last Error": "Buffer create outcome uncertain: " + type(exc).__name__ +
                          "; reconcile with Buffer before any retry"
        })
        raise

    ident = str(post.get("id") or "")
    metadata = post.get("metadata") or {}
    url = str(metadata.get("url") or "")
    if not ident or url != LINK:
        store.patch("Publishing Queue", row, {
            "Status": "LINK_REVIEW",
            "Batch ID": ident,
            "Last Error": "Buffer post response ID/destination uncertain; DO NOT retry"
        })
        raise RuntimeError("Buffer response uncertain; check existing post, do not duplicate")

    # Read back the created post rather than trusting the initial creation response.
    try:
        observed = client.get_post(ident)
        a.require(str(observed.get("id") or "") == ident, "Missing Buffer readback")
        a.require(str((observed.get("metadata") or {}).get("url") or "") == LINK,
                  "Buffered post destination readback mismatch")
        a.require(str(observed.get("status") or "").lower() in ("scheduled", "pending"),
                  "Buffered post status not scheduled")
    except Exception as exc:
        store.patch("Publishing Queue", row, {
            "Status": "LINK_REVIEW",
            "Batch ID": ident,
            "Last Error": "Buffer created but readback unverified (" +
                          type(exc).__name__ + "); do NOT resubmit"
        })
        raise

    store.patch("Publishing Queue", row, {
        "Status": "SCHEDULED_BUFFER",
        "Batch ID": ident,
        "Last Error": "",
        "Last Attempt UTC": a.make_timestamp(),
        "Attempt Count": "1"
    })
    print("Q51_VERIFIED_SCHEDULED " + json.dumps({
        "pin": PIN, "buffer_id": ident, "due_utc": candidate["due"].isoformat(),
        "product": LINK, "queue_before": count,
    }))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("Q51_ONEOFF_HALTED: " + type(exc).__name__ + ": " + str(exc)[:220])
        sys.exit(1)
