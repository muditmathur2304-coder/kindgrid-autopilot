"""KindGrid Studio — Asset Pipeline: Drive Uploader + Dashboard Writer.

GitHub Actions runs this after Antigravity pushes a completed campaign folder.

Usage:
    python -m scripts.asset_pipeline assets/kgs-024

The campaign folder must contain:
    manifest.json   — describes the campaign and queue rows to create
    *.xlsx, *.pdf, *.png  — product files to upload to Google Drive

On success:
    - All files uploaded to Google Drive (under DRIVE_ASSETS_FOLDER_ID/<campaign_id>/)
    - manifest enriched with Drive link for each file → drive_links.json written
    - Business Dashboard: Gumroad Upload Queue rows created (PAIR_READY)
    - Business Dashboard: Publishing Queue rows created (READY)
    - Business Dashboard: Stale pin IDs listed in manifest['stale_q_ids'] marked STALE

Environment variables (all from GitHub Actions secrets / variables):
    GOOGLE_SERVICE_ACCOUNT_JSON_B64   — base64-encoded service account JSON
    DRIVE_ASSETS_FOLDER_ID            — Google Drive folder ID for campaign assets
                                        (defaults to Business HQ: 1XkUEtz2KqflOK3HB3ksbPtxZOBPP0lhN)
    GOOGLE_SHEET_ID                   — Business Dashboard sheet ID
                                        (defaults to 1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs)
"""
import base64
import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Lazy imports — only available in GitHub Actions environment
# ---------------------------------------------------------------------------

def _require_google_libs():
    try:
        import google.oauth2.service_account as sa
        import googleapiclient.discovery as disc
        import googleapiclient.http as ghttp
        import gspread
        return sa, disc, ghttp, gspread
    except ImportError as exc:
        print(f"PIPELINE_DEPS_MISSING: {exc} — install google-auth google-api-python-client gspread")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs")
DRIVE_ROOT = os.environ.get("DRIVE_ASSETS_FOLDER_ID", "1XkUEtz2KqflOK3HB3ksbPtxZOBPP0lhN")


def _build_credentials():
    sa, disc, ghttp, gspread = _require_google_libs()
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "").strip()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON_B64 secret is missing")
    info = json.loads(base64.b64decode(raw).decode("utf-8"))
    creds = sa.Credentials.from_service_account_info(info, scopes=SCOPES)
    return creds, disc, ghttp, gspread


# ---------------------------------------------------------------------------
# Drive helpers
# ---------------------------------------------------------------------------

def _get_or_create_folder(drive_svc, name: str, parent_id: str) -> str:
    """Return folder ID, creating it if it does not exist."""
    q = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = drive_svc.files().list(q=q, fields="files(id,name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = drive_svc.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _upload_file(drive_svc, ghttp, local_path: Path, folder_id: str) -> str:
    """Upload file, return its public 'anyone-can-view' Drive URL."""
    mime_map = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".json": "application/json",
        ".zip": "application/zip",
    }
    mime = mime_map.get(local_path.suffix.lower(), "application/octet-stream")
    meta = {"name": local_path.name, "parents": [folder_id]}
    media = ghttp.MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    uploaded = (
        drive_svc.files()
        .create(body=meta, media_body=media, fields="id,name")
        .execute()
    )
    file_id = uploaded["id"]
    # Make it readable by anyone with the link
    drive_svc.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    return f"https://drive.google.com/file/d/{file_id}/view"


# ---------------------------------------------------------------------------
# Sheets helpers
# ---------------------------------------------------------------------------

_GUMROAD_QUEUE_TAB = "Gumroad Upload Queue"
_PIN_QUEUE_TAB = "Publishing Queue"

# Column order must match the live Dashboard exactly.
_GUMROAD_COLUMNS = [
    "Product ID", "Product Name", "Price USD", "Unique Slug",
    "PDF Drive Link", "Cover Drive Link", "Listing Copy Drive Link",
    "QA Verified (YES/NO)", "Upload Status",
    "Gumroad Live URL", "Last Error", "Last Attempt UTC", "Attempt Count",
    "Last Updated UTC", "QA Version", "QA Report Drive Link", "QA Audited UTC",
    "QA Outcome", "Pair ID", "Pair Role", "Paired Product ID",
    "Bonus File Drive Link", "Gallery Image 1 Drive Link", "Gallery Image 2 Drive Link",
    "Demand Evidence Doc Link", "Visual Audit Contact Sheet Link",
]

_PIN_COLUMNS = [
    "Queue ID", "Product", "Content Type", "Scheduled Date", "Time Window",
    "US Scheduled Time", "Target Board", "Pin Title", "Pin Description",
    "Destination URL", "Status", "Pin Image Drive Link", "QA Verified (YES/NO)",
]


def _get_sheet(gspread_client, tab_name: str):
    sh = gspread_client.open_by_key(SHEET_ID)
    return sh.worksheet(tab_name)


def _append_row(ws, columns: list, row_dict: dict):
    row = [row_dict.get(col, "") for col in columns]
    ws.append_row(row, value_input_option="USER_ENTERED")


def _mark_stale(ws, stale_ids: list[str]):
    """Set Status = STALE for every row whose Queue ID is in stale_ids."""
    if not stale_ids:
        return
    data = ws.get_all_values()
    if not data:
        return
    header = data[0]
    try:
        id_col = header.index("Queue ID") + 1   # 1-indexed
        status_col = header.index("Status") + 1
    except ValueError:
        print("PIPELINE_WARN: Could not find Queue ID or Status column in Publishing Queue tab")
        return
    stale_set = set(stale_ids)
    for row_idx, row in enumerate(data[1:], start=2):
        q_id = row[id_col - 1].strip() if len(row) >= id_col else ""
        if q_id in stale_set:
            ws.update_cell(row_idx, status_col, "STALE")
            time.sleep(0.3)   # respect Sheets API rate limit
    print(f"PIPELINE_STALE: Marked {len(stale_ids)} pins as STALE")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(campaign_dir: Path):
    # KGS_RELEASE_GATE_HOLD: no Drive permissions, queue writes, or false QA
    # approvals until item-specific KGS-QA-V2 and live duplicate checks are
    # independently enforced. This is intentionally fail-closed.
    raise RuntimeError(
        "PIPELINE_BLOCKED: independent KGS-QA-V2 verification, "
        "seller attachment readback, public URL, and live queue collision "
        "checks are not implemented; no uploads or queue writes attempted"
    )
    manifest_path = campaign_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"PIPELINE_ERROR: {manifest_path} not found")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    campaign_id = manifest.get("campaign", campaign_dir.name)
    print(f"PIPELINE_START: {campaign_id}")

    creds, disc, ghttp, gspread_mod = _build_credentials()

    # Build API clients
    drive_svc = disc.build("drive", "v3", credentials=creds, cache_discovery=False)
    gc = gspread_mod.authorize(creds)

    # 1. Create campaign subfolder in Drive
    folder_id = _get_or_create_folder(drive_svc, campaign_id, DRIVE_ROOT)
    print(f"PIPELINE_FOLDER: {campaign_id} → {folder_id}")

    # 2. Upload every non-manifest file, build drive_links map
    drive_links: dict[str, str] = {}
    upload_files = sorted(
        f for f in campaign_dir.iterdir()
        if f.is_file() and f.name not in ("manifest.json", "drive_links.json")
    )
    for fpath in upload_files:
        url = _upload_file(drive_svc, ghttp, fpath, folder_id)
        drive_links[fpath.name] = url
        print(f"PIPELINE_UPLOADED: {fpath.name} → {url}")

    # 3. Write drive_links.json back into the campaign folder
    links_path = campaign_dir / "drive_links.json"
    links_path.write_text(json.dumps(drive_links, indent=2), encoding="utf-8")
    print(f"PIPELINE_LINKS: Written to {links_path}")

    # 4. Append Gumroad Upload Queue rows
    def _resolve(key: str) -> str:
        """Look up a filename key in drive_links, return URL or empty string."""
        val = manifest.get(key, "")
        if val and not val.startswith("http") and val in drive_links:
            return drive_links[val]
        return val

    gumroad_ws = _get_sheet(gc, _GUMROAD_QUEUE_TAB)
    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for role in ("paid", "free"):
        prod = manifest.get("products", {}).get(role)
        if not prod:
            continue
        row = {
            "Product ID": prod["product_id"],
            "Product Name": prod["product_name"],
            "Price USD": prod["price_usd"],
            "Unique Slug": prod["unique_slug"],
            "PDF Drive Link": _resolve(prod.get("pdf_file", "")),
            "Cover Drive Link": _resolve(prod.get("cover_file", "")),
            "Listing Copy Drive Link": prod.get("listing_copy_doc_url", ""),
            "QA Verified (YES/NO)": "YES",
            "Upload Status": "PAIR_READY",
            "QA Version": "KGS-QA-V2",
            "QA Report Drive Link": prod.get("qa_report_url", ""),
            "QA Audited UTC": prod.get("qa_audited_utc", now_utc),
            "QA Outcome": "PASS",
            "Pair ID": manifest.get("pair_id", ""),
            "Pair Role": role.upper(),
            "Paired Product ID": prod.get("paired_product_id", ""),
            "Bonus File Drive Link": _resolve(prod.get("bonus_file", "")) if role == "paid" else "",
            "Gallery Image 1 Drive Link": _resolve(prod.get("gallery_1_file", "")),
            "Gallery Image 2 Drive Link": _resolve(prod.get("gallery_2_file", "")) if role == "paid" else "",
            "Demand Evidence Doc Link": manifest.get("demand_evidence_url", ""),
            "Visual Audit Contact Sheet Link": _resolve(prod.get("contact_sheet_file", "")),
            "Last Updated UTC": now_utc,
            "Attempt Count": "0",
        }
        _append_row(gumroad_ws, _GUMROAD_COLUMNS, row)
        print(f"PIPELINE_QUEUE_ROW: {prod['product_id']} ({role.upper()}) → PAIR_READY")

    # 5. Append Pinterest Publishing Queue rows
    pin_ws = _get_sheet(gc, _PIN_QUEUE_TAB)
    for pin in manifest.get("pinterest_pins", []):
        row = {
            "Queue ID": pin["queue_id"],
            "Product": pin["product_id"],
            "Content Type": pin.get("content_type", "Standard Pin"),
            "Scheduled Date": pin["scheduled_date"],
            "Time Window": pin.get("time_window", "Morning"),
            "US Scheduled Time": pin.get("us_scheduled_time", "08:30 EDT"),
            "Target Board": pin["target_board"],
            "Pin Title": pin["pin_title"],
            "Pin Description": pin["pin_description"],
            "Destination URL": pin["destination_url"],
            "Status": "READY",
            "Pin Image Drive Link": _resolve(pin.get("image_file", "")),
            "QA Verified (YES/NO)": "YES",
        }
        _append_row(pin_ws, _PIN_COLUMNS, row)
        print(f"PIPELINE_PIN_ROW: {pin['queue_id']} → READY")

    # 6. Mark stale pins
    stale_ids = manifest.get("stale_q_ids", [])
    _mark_stale(pin_ws, stale_ids)

    print(f"PIPELINE_COMPLETE: {campaign_id} — all rows written, {len(drive_links)} files uploaded")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.asset_pipeline <campaign_dir>")
        sys.exit(1)
    run(Path(sys.argv[1]))
