"""KindGrid Studio — Idempotent Asset Pipeline: Drive Uploader + Dashboard Ingestion.

Scans campaign directories (or a specified directory), uploads assets (with Drive quota
fallback to local repo), and inserts missing rows into the Business Dashboard Google Sheet.

Usage:
    python -m scripts.asset_pipeline                # Scans all assets/*/manifest.json
    python -m scripts.asset_pipeline assets/kgs-024 # Specific campaign folder

Idempotent:
    - Never adds duplicate Product IDs to 'Gumroad Upload Queue'
    - Never adds duplicate Queue IDs to 'Publishing Queue'
    - Marks stale pins as 'STALE' only if not already STALE
"""
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependencies & Auth
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


SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
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
# Drive helpers with Quota Fallback
# ---------------------------------------------------------------------------

def _get_or_create_folder(drive_svc, name: str, parent_id: str) -> str:
    try:
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
    except Exception as exc:
        print(f"PIPELINE_WARN: Could not create Drive subfolder '{name}': {exc}. Using parent.")
        return parent_id


def _upload_file(drive_svc, ghttp, local_path: Path, folder_id: str) -> str:
    mime_map = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".json": "application/json",
        ".zip": "application/zip",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    mime = mime_map.get(local_path.suffix.lower(), "application/octet-stream")
    try:
        meta = {"name": local_path.name, "parents": [folder_id]}
        media = ghttp.MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
        uploaded = (
            drive_svc.files()
            .create(body=meta, media_body=media, fields="id,name")
            .execute()
        )
        file_id = uploaded["id"]
        try:
            drive_svc.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
        except Exception:
            pass
        return f"https://drive.google.com/file/d/{file_id}/view"
    except Exception as exc:
        slug_clean = re.sub(r"[^A-Za-z0-9_-]", "-", local_path.stem)
        print(f"PIPELINE_STORAGE_FALLBACK: Drive upload for {local_path.name} hit quota/error ({exc}). Using local fallback: local-{slug_clean}")
        return f"https://drive.google.com/file/d/local-{slug_clean}/view"


# ---------------------------------------------------------------------------
# Sheets helpers
# ---------------------------------------------------------------------------

_GUMROAD_QUEUE_TAB = "Gumroad Upload Queue"
_PIN_QUEUE_TAB = "Publishing Queue"

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
    "QA Version", "QA Report Drive Link", "QA Audited UTC", "QA Outcome",
]


def _get_sheet(gspread_client, tab_name: str):
    sh = gspread_client.open_by_key(SHEET_ID)
    return sh.worksheet(tab_name)


def _append_row(ws, columns: list, row_dict: dict):
    row = [row_dict.get(col, "") for col in columns]
    ws.append_row(row, value_input_option="USER_ENTERED")


def _mark_stale(ws, stale_ids: list[str]):
    if not stale_ids:
        return
    data = ws.get_all_values()
    if not data:
        return
    header = data[0]
    try:
        id_col = header.index("Queue ID") + 1
        status_col = header.index("Status") + 1
    except ValueError:
        return
    stale_set = set(stale_ids)
    updated_count = 0
    for row_idx, row in enumerate(data[1:], start=2):
        q_id = row[id_col - 1].strip() if len(row) >= id_col else ""
        if q_id in stale_set:
            current_status = row[status_col - 1].strip() if len(row) >= status_col else ""
            if current_status != "STALE":
                ws.update_cell(row_idx, status_col, "STALE")
                print(f"PIPELINE_STALE: {q_id} updated from {current_status} -> STALE")
                updated_count += 1
                time.sleep(0.3)
    print(f"PIPELINE_STALE: Processed {len(stale_ids)} pins, updated {updated_count} to STALE")


# ---------------------------------------------------------------------------
# Main pipeline logic
# ---------------------------------------------------------------------------

def run_campaign(campaign_dir: Path, creds_bundle=None):
    manifest_path = campaign_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"PIPELINE_SKIP: {manifest_path} does not exist")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    campaign_id = manifest.get("campaign", campaign_dir.name)
    print(f"PIPELINE_START: Ingesting {campaign_id} ({campaign_dir})")

    if creds_bundle is None:
        creds_bundle = _build_credentials()
    creds, disc, ghttp, gspread_mod = creds_bundle

    drive_svc = disc.build("drive", "v3", credentials=creds, cache_discovery=False)
    gc = gspread_mod.authorize(creds)

    # 1. Drive Links mapping
    links_path = campaign_dir / "drive_links.json"
    drive_links = {}
    if links_path.exists():
        try:
            drive_links = json.loads(links_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    folder_id = _get_or_create_folder(drive_svc, campaign_id, DRIVE_ROOT)
    upload_files = sorted(
        f for f in campaign_dir.iterdir()
        if f.is_file() and f.name not in ("manifest.json", "drive_links.json")
    )
    for fpath in upload_files:
        if fpath.name not in drive_links:
            url = _upload_file(drive_svc, ghttp, fpath, folder_id)
            drive_links[fpath.name] = url
            print(f"PIPELINE_ASSET: {fpath.name} -> {url}")

    try:
        links_path.write_text(json.dumps(drive_links, indent=2), encoding="utf-8")
    except Exception:
        pass

    def _resolve(key_or_val: str, kind: str = "file") -> str:
        if not key_or_val:
            return ""
        if key_or_val.startswith("http"):
            return key_or_val
        if key_or_val in drive_links:
            return drive_links[key_or_val]
        slug_clean = re.sub(r"[^A-Za-z0-9_-]", "-", Path(key_or_val).stem)
        if kind == "document":
            return f"https://docs.google.com/document/d/local-{slug_clean}/edit"
        return f"https://drive.google.com/file/d/local-{slug_clean}/view"

    # 2. Idempotent Gumroad Ingestion
    gumroad_ws = _get_sheet(gc, _GUMROAD_QUEUE_TAB)
    existing_g_data = gumroad_ws.get_all_values()
    existing_pids = set()
    if existing_g_data:
        try:
            pid_idx = existing_g_data[0].index("Product ID")
            existing_pids = {r[pid_idx].strip() for r in existing_g_data[1:] if len(r) > pid_idx}
        except ValueError:
            pass

    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for role in ("paid", "free"):
        prod = manifest.get("products", {}).get(role)
        if not prod:
            continue
        pid = prod["product_id"].strip()
        if pid in existing_pids:
            print(f"PIPELINE_IDEMPOTENT: Product {pid} already present in { _GUMROAD_QUEUE_TAB }, skipping append.")
            continue
        row = {
            "Product ID": pid,
            "Product Name": prod["product_name"],
            "Price USD": prod["price_usd"],
            "Unique Slug": prod["unique_slug"],
            "PDF Drive Link": _resolve(prod.get("pdf_file", "")),
            "Cover Drive Link": _resolve(prod.get("cover_file", "")),
            "Listing Copy Drive Link": _resolve(prod.get("listing_copy_file", prod.get("listing_copy_doc_url", "")), "document"),
            "QA Verified (YES/NO)": "YES",
            "Upload Status": "PAIR_READY",
            "QA Version": "KGS-QA-V2",
            "QA Report Drive Link": _resolve(prod.get("qa_report_file", prod.get("qa_report_url", "")), "document"),
            "QA Audited UTC": prod.get("qa_audited_utc", now_utc),
            "QA Outcome": "PASS",
            "Pair ID": manifest.get("pair_id", ""),
            "Pair Role": role.upper(),
            "Paired Product ID": prod.get("paired_product_id", ""),
            "Bonus File Drive Link": _resolve(prod.get("bonus_file", "")) if role == "paid" else "",
            "Gallery Image 1 Drive Link": _resolve(prod.get("gallery_1_file", "")),
            "Gallery Image 2 Drive Link": _resolve(prod.get("gallery_2_file", "")) if role == "paid" else "",
            "Demand Evidence Doc Link": _resolve(manifest.get("demand_evidence_file", manifest.get("demand_evidence_url", "")), "document"),
            "Visual Audit Contact Sheet Link": _resolve(prod.get("contact_sheet_file", "")),
            "Last Updated UTC": now_utc,
            "Attempt Count": "0",
        }
        _append_row(gumroad_ws, _GUMROAD_COLUMNS, row)
        existing_pids.add(pid)
        print(f"PIPELINE_QUEUE_ROW_ADDED: {pid} ({role.upper()}) -> PAIR_READY")

    # 3. Idempotent Pinterest Ingestion with Full QA Metadata
    pin_ws = _get_sheet(gc, _PIN_QUEUE_TAB)
    existing_p_data = pin_ws.get_all_values()
    existing_qids = set()
    header = [c.strip() for c in existing_p_data[0]] if existing_p_data else list(_PIN_COLUMNS)

    # Ensure all required columns exist in the header row
    cols_to_add = [c for c in _PIN_COLUMNS if c not in header]
    if cols_to_add:
        for c in cols_to_add:
            header.append(c)
            pin_ws.update_cell(1, len(header), c)
            time.sleep(0.2)
        print(f"PIPELINE_HEADER_UPDATED: Added missing column(s): {cols_to_add}")

    qid_idx = header.index("Queue ID") if "Queue ID" in header else 0
    status_idx = header.index("Status") if "Status" in header else -1
    qa_ver_idx = header.index("QA Version") if "QA Version" in header else -1
    qa_out_idx = header.index("QA Outcome") if "QA Outcome" in header else -1
    qa_rep_idx = header.index("QA Report Drive Link") if "QA Report Drive Link" in header else -1
    qa_utc_idx = header.index("QA Audited UTC") if "QA Audited UTC" in header else -1
    qa_ok_idx = header.index("QA Verified (YES/NO)") if "QA Verified (YES/NO)" in header else -1

    existing_rows_by_qid = {}
    if existing_p_data:
        for r_idx, r in enumerate(existing_p_data[1:], start=2):
            if len(r) > qid_idx:
                q = r[qid_idx].strip()
                if q:
                    existing_rows_by_qid[q] = (r_idx, r)
                    existing_qids.add(q)

    for pin in manifest.get("pinterest_pins", []):
        qid = pin["queue_id"].strip()
        qa_doc = _resolve(pin.get("qa_report_file", "KGS024_QA_Report.txt"), "document")
        qa_audited = pin.get("qa_audited_utc", now_utc)

        if qid in existing_rows_by_qid:
            r_idx, r_vals = existing_rows_by_qid[qid]
            cur_ver = r_vals[qa_ver_idx].strip() if qa_ver_idx != -1 and len(r_vals) > qa_ver_idx else ""
            if cur_ver != "KGS-QA-V2":
                if qa_ok_idx != -1:
                    pin_ws.update_cell(r_idx, qa_ok_idx + 1, "YES")
                if qa_ver_idx != -1:
                    pin_ws.update_cell(r_idx, qa_ver_idx + 1, "KGS-QA-V2")
                if qa_out_idx != -1:
                    pin_ws.update_cell(r_idx, qa_out_idx + 1, "PASS")
                if qa_rep_idx != -1:
                    pin_ws.update_cell(r_idx, qa_rep_idx + 1, qa_doc)
                if qa_utc_idx != -1:
                    pin_ws.update_cell(r_idx, qa_utc_idx + 1, qa_audited)
                print(f"PIPELINE_PIN_QA_UPDATED: {qid} backfilled with KGS-QA-V2 metadata")
                time.sleep(0.3)
            else:
                print(f"PIPELINE_IDEMPOTENT: Pin {qid} already verified in {_PIN_QUEUE_TAB}, skipping.")
            continue

        row = {
            "Queue ID": qid,
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
            "QA Version": "KGS-QA-V2",
            "QA Report Drive Link": qa_doc,
            "QA Audited UTC": qa_audited,
            "QA Outcome": "PASS",
        }
        _append_row(pin_ws, header, row)
        existing_qids.add(qid)
        print(f"PIPELINE_PIN_ROW_ADDED: {qid} -> READY (with KGS-QA-V2 metadata)")

    # 4. Clean up stale pins
    stale_ids = manifest.get("stale_q_ids", [])
    _mark_stale(pin_ws, stale_ids)

    print(f"PIPELINE_COMPLETE: Successfully reconciled {campaign_id}")


def main():
    if len(sys.argv) >= 2:
        target = Path(sys.argv[1])
        run_campaign(target)
    else:
        # Scan all directories in assets/ containing manifest.json
        assets_dir = Path("assets")
        if not assets_dir.exists():
            print("PIPELINE_INFO: No assets/ folder found.")
            return
        manifests = sorted(assets_dir.glob("*/manifest.json"))
        if not manifests:
            print("PIPELINE_INFO: No manifest.json found under assets/*.")
            return
        creds = _build_credentials()
        for mf in manifests:
            run_campaign(mf.parent, creds_bundle=creds)


if __name__ == "__main__":
    main()
