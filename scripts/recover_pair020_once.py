"""One-time owner-authorized recovery of an ALREADY-created Gumroad paid draft.

Seller details verified from authenticated read-only API on 2026-10-16:
- Existing paid product id 2Oo_ipk1UmplVimSJLqNnA==, correct slug,
  unpublished; 2 downloadable files; 3 gallery/cover images; $9.
- Free partner slug does not exist.

Fail closed on any changed provider/QA status and never re-create the paid product.
This module is not imported by the recurring publisher and cannot run on cron.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from src import autopilot as a
from src.paired_release import prepare_pair, create_and_verify_draft, publish_and_verify

APPROVAL = "KINDGRID_OWNER_RECOVER_2026_10_16"
PAID_ID = "2Oo_ipk1UmplVimSJLqNnA=="
PAID = "KGS-020"
FREE = "KGS-021"
PAIR = "KG-PAIR-020-021"


def main() -> int:
    a.require(os.environ.get("KINDGRID_RECOVERY_AUTHORIZED") == APPROVAL,
              "No owner-scoped recovery authorization; no Gumroad writes")
    store = a.GoogleStore()
    rows = store.get_rows("Gumroad Upload Queue")
    paid = next((r for r in rows if r.get("Product ID") == PAID), None)
    free = next((r for r in rows if r.get("Product ID") == FREE), None)
    a.require(paid is not None and free is not None, "Exact pair missing")
    a.require(paid.get("Pair ID") == PAIR and free.get("Pair ID") == PAIR and
              paid.get("Pair Role") == "PAID" and free.get("Pair Role") == "FREE" and
              paid.get("Paired Product ID") == FREE and
              free.get("Paired Product ID") == PAID, "Not the authorized reciprocal pair")
    a.require(paid.get("Upload Status") == "REVIEW" and
              free.get("Upload Status") == "PAIR_HELD",
              "State changed since read-only reconciliation; refuse any release")
    a.require(paid.get("Unique Slug") == "retainer-margin-studio" and
              free.get("Unique Slug") == "retainer-one-contract-reality-check-free",
              "Expected seller slugs changed; refuse")
    for row in (paid, free):
        a.require(row.get("QA Verified (YES/NO)") == "YES" and
                  row.get("QA Outcome") == "PASS", "QA approval is no longer valid")
        a.verify_qa_report(store, row, row["Product ID"])

    with tempfile.TemporaryDirectory(prefix="kindgrid-recover-known-draft-") as folder:
        assets = prepare_pair(store, paid, free, Path(folder))
        # First read-only seller reconciliation, no draft POST.
        existing = a.gumroad_cli(["products", "view", PAID_ID]).get("product") or {}
        a.require(str(existing.get("id")) == PAID_ID and
                  existing.get("published") is False and
                  str(existing.get("name") or "").strip() == paid["Product Name"] and
                  existing.get("custom_permalink") == paid["Unique Slug"] and
                  str(existing.get("price")) == "900",
                  "Existing paid Gumroad draft identity, price or state differs")
        attachments = existing.get("files") or existing.get("rich_content_files") or []
        covers = existing.get("covers") or existing.get("cover_images") or []
        a.require(len(attachments) >= 2 and len(covers) >= 3,
                  "Existing paid draft lacks the approved XLSX/PDF and real previews")
        seller = a.gumroad_cli(["products", "list", "--all"]).get("products", [])
        wanted = (paid["Unique Slug"], free["Unique Slug"])
        count = {s: 0 for s in wanted}
        for p in seller:
            if not isinstance(p, dict):
                continue
            s = str(p.get("custom_permalink") or "").strip()
            tail = str(p.get("short_url") or "").rstrip("/").split("/")[-1]
            for slug in wanted:
                if slug in (s, tail):
                    count[slug] += 1
        a.require(count[paid["Unique Slug"]] == 1 and
                  count[free["Unique Slug"]] == 0,
                  "Seller duplicate/free slug state uncertain; no new writes")

        # Publish EXACT existing paid draft; never perform products create for paid.
        try:
            store.patch("Gumroad Upload Queue", paid, {
                "Upload Status": "DRAFT_VERIFIED",
                "Gumroad Live URL": "https://gumroad.com/products/" + PAID_ID + "/edit",
                "Last Error": "", "Last Updated UTC": a.make_timestamp()})
            print("RECOVERY_PAID_DRAFT_VERIFIED: existing original seller draft")
            paid_url = publish_and_verify(PAID_ID, paid)
            store.patch("Gumroad Upload Queue", paid, {
                "Upload Status": "PUBLISHED", "Gumroad Live URL": paid_url,
                "Last Error": "", "Last Updated UTC": a.make_timestamp()})
            print("RECOVERY_PAID_PUBLIC_VERIFIED: " + paid_url)
        except Exception as exc:
            store.patch("Gumroad Upload Queue", paid, {
                "Upload Status": "REVIEW",
                "Last Error": ("Paid draft publication uncertain: " + type(exc).__name__)[:320]})
            print("RECOVERY_PAID_BLOCKED: " + type(exc).__name__ +
                  "; seller state uncertain, do not retry")
            return 1

        # Free companion may launch only after the exact paid URL is live.
        a.require(paid_url in assets["FREE"]["description"], "Free cross-link mismatch")
        try:
            store.patch("Gumroad Upload Queue", free, {
                "Upload Status": "PAIR_RELEASING",
                "Last Attempt UTC": a.make_timestamp(),
                "Attempt Count": str(int(free.get("Attempt Count") or "0") + 1)})
            ident = create_and_verify_draft(assets["FREE"], "FREE")
            store.patch("Gumroad Upload Queue", free, {
                "Upload Status": "DRAFT_VERIFIED",
                "Gumroad Live URL": "https://gumroad.com/products/" + ident + "/edit",
                "Last Updated UTC": a.make_timestamp()})
            free_url = publish_and_verify(ident, free)
            store.patch("Gumroad Upload Queue", free, {
                "Upload Status": "PUBLISHED", "Gumroad Live URL": free_url,
                "Last Error": "", "Last Updated UTC": a.make_timestamp()})
            print("RECOVERY_FREE_PUBLIC_VERIFIED: " + free_url)
        except Exception as exc:
            store.patch("Gumroad Upload Queue", free, {
                "Upload Status": "REVIEW",
                "Last Error": ("Free launch uncertain, inspect seller: " + type(exc).__name__)[:320]})
            print("RECOVERY_FREE_BLOCKED: " + type(exc).__name__ +
                  "; do not create another free product or retry blindly")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
