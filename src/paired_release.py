"""Two-product free+paid launch gate. No standalone paid product publication.

This module is intentionally fail-closed and never retries uncertain Gumroad
writes: the owner should reconcile any partial pair in the seller dashboard.
Its only mutation entrypoint is release_one_pair, called in LIVE cron mode.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from src import autopilot as a

EXACT_ROLES = {"PAID", "FREE"}
MIN_NEW_ID = 8


def validate_tool_xlsx(blob: bytes, pair_id: str) -> None:
    """Fail closed on tool-first XLSX packages before any Gumroad mutation.

    This checks workbook structure and original embedded instructional artwork.
    Arithmetic, mobile visuals, buyer demand, and native Sheets checks still
    require independent item-specific KGS-QA-V2 PASS documentation.
    """
    a.require(15000 <= len(blob) <= 20_000_000,
              f"{pair_id}: primary XLSX size is implausible")
    try:
        with ZipFile(io.BytesIO(blob)) as zipped:
            names = zipped.namelist()
            sheets = [n for n in names if n.startswith("xl/worksheets/sheet")
                      and n.endswith(".xml")]
            a.require("xl/workbook.xml" in names and len(sheets) >= 2,
                      f"{pair_id}: expected a real multi-sheet Excel workbook")
            a.require(not any("vbaProject.bin" in n or
                              n.startswith("xl/externalLinks/") for n in names),
                      f"{pair_id}: macros and external links are not allowed")
            formula_count = sum(len(re.findall(rb"<(?:[A-Za-z0-9_]+:)?f(?=\\s|>)",
                                               zipped.read(n))) for n in sheets)
            a.require(formula_count >= 10,
                      f"{pair_id}: interactive XLSX requires at least 10 formulas")
            artwork = [n for n in names if n.startswith("xl/media/") and
                       n.lower().endswith((".png", ".jpg", ".jpeg"))]
            a.require(bool(artwork),
                      f"{pair_id}: no actual instructional image embedded in XLSX")
            from PIL import Image, UnidentifiedImageError
            suitable = 0
            for n in artwork:
                picture = zipped.read(n)
                try:
                    with Image.open(io.BytesIO(picture)) as img:
                        width, height = img.size
                        img.verify()
                except (OSError, UnidentifiedImageError):
                    raise ValueError(f"{pair_id}: unreadable embedded XLSX illustration")
                if len(picture) >= 3000 and width >= 500 and height >= 250:
                    suitable += 1
            a.require(suitable >= 1,
                      f"{pair_id}: no substantial, readable embedded illustration")
    except BadZipFile:
        raise ValueError(f"{pair_id}: invalid Excel workbook archive") from None


def select_ready_pairs(rows: list[dict]) -> list[tuple[dict, dict]]:
    """Only fully staged, reciprocal pairs. Never synthesize a partner."""
    groups = defaultdict(list)
    for row in rows:
        if row.get("Upload Status") == "PAIR_READY":
            pair_id = str(row.get("Pair ID") or "").strip()
            a.require(bool(pair_id), "PAIR_READY without a Pair ID is unsafe")
            groups[pair_id].append(row)
    approved = []
    for pair_id, members in groups.items():
        a.require(len(members) == 2,
                  f"{pair_id}: exactly two PAIR_READY rows required")
        by_role = {str(r.get("Pair Role") or "").upper().strip(): r for r in members}
        a.require(set(by_role) == EXACT_ROLES, f"{pair_id}: must have PAID and FREE")
        paid, free = by_role["PAID"], by_role["FREE"]
        paid_id, free_id = paid.get("Product ID", ""), free.get("Product ID", "")
        a.require(paid.get("Paired Product ID") == free_id and
                  free.get("Paired Product ID") == paid_id,
                  f"{pair_id}: reciprocal partner ID pointers missing")
        a.require(paid_id != free_id, f"{pair_id}: duplicate product ID")
        for member in (paid, free):
            a.require(member.get("QA Verified (YES/NO)") == "YES",
                      f"{pair_id}: creator QA approval missing")
            a.validate_qa_metadata(member)
            a.require(member.get("QA Outcome") == "PASS",
                      f"{pair_id}: QA outcome must PASS")
            a.require(member.get("Unique Slug") not in a.EXISTING_GUMROAD_SLUGS,
                      f"{pair_id}: slug belongs to an existing product")
            product_code = member.get("Product ID", "")
            a.require(product_code.startswith("KGS-") and
                      product_code[4:].isdigit() and int(product_code[4:]) >= MIN_NEW_ID,
                      f"{pair_id}: historic product is not eligible for new launch")
        a.require(paid.get("Unique Slug") != free.get("Unique Slug"),
                  f"{pair_id}: duplicate slug")
        try:
            paid_price = Decimal(str(paid.get("Price USD", "")))
            free_price = Decimal(str(free.get("Price USD", "")))
        except InvalidOperation:
            raise ValueError(f"{pair_id}: invalid price") from None
        a.require(Decimal("3.00") <= paid_price <= Decimal("30.00"),
                  f"{pair_id}: paid price outside safe range")
        a.require(free_price == Decimal("0.00"),
                  f"{pair_id}: companion must be genuinely free ($0)")
        approved.append((paid, free))
    return sorted(approved, key=lambda p: p[0].get("Pair ID", ""))


def prepare_pair(store, paid, free, target: Path) -> dict:
    """Inspect real Google Drive assets before any external mutation."""
    pair_id = paid["Pair ID"]
    files = {}
    # A commercial-demand hypothesis must be documented before any paid
    # product launches. The report records observed competitors and caveats,
    # never imaginary Pinterest search volume or guaranteed sales.
    research_ids = {
        a.google_file_id(str(row.get("Demand Evidence Doc Link") or ""), "document")
        for row in (paid, free)
    }
    a.require(len(research_ids) == 1,
              f"{pair_id}: paid and free must share one actual demand research report")
    research = store.get_doc_text(next(iter(research_ids)))
    required = ("BUYER PROBLEM", "COMPETITOR", "DIFFERENTIATION", "EVIDENCE", "LIMITATION")
    a.require(len(research.strip()) >= 750 and
              all(term in research.upper() for term in required) and
              research.lower().count("https://") >= 2,
              f"{pair_id}: demand/competition report missing specific evidence or caveats")
    paid_url = ("https://kindgridstudio.gumroad.com/l/" +
                paid["Unique Slug"].strip())
    for role, row in (("PAID", paid), ("FREE", free)):
        a.verify_qa_report(store, row, row["Product ID"])
        pdf = store.get_bytes(a.google_file_id(row["PDF Drive Link"]), "application/pdf")
        cover = store.get_bytes(a.google_file_id(row["Cover Drive Link"]), "image/png")
        count = a.validate_pdf(pdf)
        a.validate_image(cover)
        sheet_url = str(row.get("Visual Audit Contact Sheet Link") or "").strip()
        contact = store.get_bytes(a.google_file_id(sheet_url), "image/png")
        # Contact sheets are mosaics, not 2:3 portrait covers.
        from PIL import Image
        with Image.open(io.BytesIO(contact)) as image:
            image.verify()
            a.require(image.width >= 850 and image.height >= 500,
                      f"{pair_id}: {role} page-by-page contact sheet unreadable")
        if role == "PAID":
            a.require(bool(str(row.get("Bonus File Drive Link") or "").strip()),
                      f"{pair_id}: paid product must include a real primary XLSX")
        a.require((3 <= count <= 15) if role == "PAID" else (3 <= count <= 7),
                  f"{pair_id}: {role} instructional guide page count outside quality gate")
        listing = store.get_doc_text(
            a.google_file_id(row["Listing Copy Drive Link"], "document"))
        summary, description = a.get_listing_copy(listing)
        a.require(bool(summary) and len(summary) >= 60,
                  f"{pair_id}: {role} listing summary inadequate")
        a.require(len(description) >= (650 if role == "PAID" else 400),
                  f"{pair_id}: {role} listing insufficiently descriptive")
        if role == "FREE":
            a.require(paid_url in description,
                      f"{pair_id}: free listing must contain actual paid destination")
        path_pdf = target / (role.lower() + ".pdf")
        path_png = target / (role.lower() + "_cover.png")
        path_pdf.write_bytes(pdf)
        path_png.write_bytes(cover)
        item = {"row": row, "pdf": path_pdf, "cover": path_png,
                "summary": summary, "description": description, "pages": count,
                "bonus": None, "previews": []}
        extra_link = str(row.get("Bonus File Drive Link") or "").strip()
        if extra_link:
            blob = store.get_bytes(
                a.google_file_id(extra_link),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            validate_tool_xlsx(blob, pair_id)
            bonus = target / (role.lower() + "_interactive.xlsx")
            bonus.write_bytes(blob)
            item["bonus"] = bonus
        for key in ("Gallery Image 1 Drive Link", "Gallery Image 2 Drive Link"):
            link = str(row.get(key) or "").strip()
            if not link:
                continue
            raw = store.get_bytes(a.google_file_id(link), "image/png")
            a.validate_image(raw)
            preview = target / (role.lower() + "_gallery_" + str(len(item["previews"]) + 1) + ".png")
            preview.write_bytes(raw)
            item["previews"].append(preview)
        a.require(len(item["previews"]) >= (2 if role == "PAID" else 1),
                  f"{pair_id}: {role} must have real customer-visible gallery previews")
        files[role] = item
    return files


def create_and_verify_draft(item: dict, role: str) -> str:
    row = item["row"]
    arguments = ["products", "create", "--draft", "--name", row["Product Name"],
                 "--price", str(row["Price USD"]), "--currency", "usd",
                 "--type", "digital", "--custom-permalink", row["Unique Slug"],
                 "--description", item["description"], "--custom-summary", item["summary"]]
    if role == "FREE":
        arguments.append("--pay-what-you-want")
    # XLSX is the primary PAID deliverable, with the short visual PDF guide
    # attached second; FREE may remain a complete standalone PDF.
    if role == "PAID" and item["bonus"]:
        arguments += ["--file", str(item["bonus"]), "--file", str(item["pdf"])]
    else:
        arguments += ["--file", str(item["pdf"])]
        if item["bonus"]:
            arguments += ["--file", str(item["bonus"])]
    # Gumroad may create a complete draft then fail when applying the optional
    # thumbnail, leaving an uncertain seller write. Cover + original galleries
    # are mandatory and independently checked, so avoid this nonessential call.
    arguments += ["--cover-image", str(item["cover"])]
    for img in item["previews"]:
        arguments += ["--preview-image", str(img)]
    response = a.gumroad_cli(arguments)
    product = response.get("product") or {}
    ident = str(product.get("id") or "")
    a.require(ident, "Seller returned no new draft ID; do not retry")
    status = a.gumroad_cli(["products", "view", ident]).get("product") or {}
    attached = status.get("files") or status.get("rich_content_files") or []
    covers = status.get("covers") or status.get("cover_images") or []
    a.require(status.get("published") is False and
              str(status.get("name") or "").strip() == row["Product Name"],
              "Draft identity/readback does not match the approved source")
    a.require(len(attached) >= (2 if item["bonus"] else 1) and bool(covers),
              "Actual downloadable files or cover were not verified")
    return ident


def publish_and_verify(ident: str, row: dict) -> str:
    a.gumroad_cli(["products", "publish", ident])
    status = a.gumroad_cli(["products", "view", ident]).get("product") or {}
    a.require(status.get("published") is True, "Seller publish result uncertain; stop")
    public = "https://kindgridstudio.gumroad.com/l/" + row["Unique Slug"]
    a.verify_public_product_url(public, row["Unique Slug"])
    return public


def launch_pair_once(store, paid: dict, free: dict) -> list[str]:
    """Paid first; then free with public paid link. At most one attempt."""
    a.require(a.enabled("LIVE_MODE") and a.enabled("PAIRED_RELEASE_ENABLED"),
              "Paired Gumroad publishing is not live")
    outputs = []
    with tempfile.TemporaryDirectory(prefix="kindgrid-premium-pair-") as temp:
        files = prepare_pair(store, paid, free, Path(temp))
        current = a.gumroad_cli(["products", "list", "--all"]).get("products", [])
        slugs = {r["Unique Slug"] for r in (paid, free)}
        for prod in current:
            slug = str(prod.get("custom_permalink") or "")
            tail = str(prod.get("short_url") or "").rstrip("/").split("/")[-1]
            a.require(slug not in slugs and tail not in slugs,
                      "Seller already has at least one matching slug; reconcile, no duplicate")
        # Claim both rows before ANY seller write: crash/retry must not
        # create a second listing. Free can remain held if paid succeeds.
        for row in (paid, free):
            store.patch("Gumroad Upload Queue", row, {
                "Upload Status": "PAIR_RELEASING",
                "Last Attempt UTC": a.make_timestamp(),
                "Attempt Count": str(int(row.get("Attempt Count") or "0") + 1)})
        for role, row in (("PAID", paid), ("FREE", free)):
            try:
                ident = create_and_verify_draft(files[role], role)
                store.patch("Gumroad Upload Queue", row, {
                    "Upload Status": "DRAFT_VERIFIED",
                    "Gumroad Live URL": "https://gumroad.com/products/" + ident + "/edit",
                    "Last Updated UTC": a.make_timestamp()})
                public = publish_and_verify(ident, row)
                store.patch("Gumroad Upload Queue", row, {
                    "Upload Status": "PUBLISHED", "Gumroad Live URL": public,
                    "Last Error": "", "Last Updated UTC": a.make_timestamp()})
                outputs.append(f"{row['Product ID']} {role}: published and verified {public}")
                if role == "PAID":
                    a.require(public in files["FREE"]["description"],
                              "Free description unexpectedly omits real paid URL")
            except Exception as error:
                store.patch("Gumroad Upload Queue", row, {
                    "Upload Status": "REVIEW",
                    "Last Error": (type(error).__name__ + ": " + str(error))[:420]})
                if role == "PAID":
                    store.patch("Gumroad Upload Queue", free, {
                        "Upload Status": "PAIR_HELD",
                        "Last Error": "Paid launch uncertain; do not launch free or retry blindly"})
                outputs.append(f"{row['Product ID']} {role}: REVIEW, no retry")
                break
    return outputs


def published_today_count(gumrows: list[dict], *, now: datetime | None = None) -> int:
    """Count confirmed PUBLIC listings in the America/New_York seller calendar day.

    If the recorded completion timestamp is absent, it is not counted; a live
    seller-side duplicate slug and draft verification still protects publication.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Publishing clock must be timezone-aware")
    ny = ZoneInfo("America/New_York")
    today = current.astimezone(ny).date()
    count = 0
    for row in gumrows:
        if row.get("Upload Status") != "PUBLISHED":
            continue
        stamp = str(row.get("Last Updated UTC") or "").strip()
        if not stamp:
            continue
        try:
            value = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if value.tzinfo and value.astimezone(ny).date() == today:
                count += 1
        except ValueError:
            continue
    return count


def run_ready_pair_cycle(store, gumrows: list[dict]) -> list[str]:
    try:
        approved = select_ready_pairs(gumrows)
    except ValueError as error:
        # Bad PAIR_READY metadata is not an exception to the no-publish gate.
        # Preserve the rows and prevent *all* seller mutations for this cycle.
        return [f"PAIR_RELEASE_BLOCKED: {error}; no Gumroad mutation"]
    if not approved:
        return ["PAIR_RELEASE_IDLE: No fully QA-approved PAID+FREE pair ready"]
    # The owner asked for a target of 7 Gumroad LISTINGS / NY calendar day.
    # Never create extras merely to hit it. A verified pair needs two free slots.
    cap = max(2, min(7, int(os.getenv("GUMROAD_DAILY_LIMIT", "7"))))
    today_count = published_today_count(gumrows)
    if today_count + 2 > cap:
        return [f"PAIR_RELEASE_DAILY_CAP: {today_count}/{cap} confirmed listings today; " +
                "hold the complete paid+free pair instead of partially releasing it"]
    # One independently audited pair maximum PER RUN; hourly checks can handle
    # more pairs across the day, never bypassing asset or QA validation.
    paid, free = approved[0]
    return launch_pair_once(store, paid, free)
