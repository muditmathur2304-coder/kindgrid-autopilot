"""KindGrid publisher: free scheduled queue processor; fail closed, never writes creative copy.

External calls are disabled by default. Requires authorized service accounts/API keys.
Compatible with KindGrid Studio's existing Google Sheets column headers.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

SHEET_ID = "1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs"
EXISTING_PRODUCTS = {"KGS-001", "KGS-002", "KGS-003"}
QA_VERSION = "KGS-QA-V2"
QA_FIELDS = ("ASSET_OPEN", "VISUAL", "CONTENT", "COPY", "LINKS", "LICENSE", "FACTS", "PRODUCT_MATCH")

EXISTING_GUMROAD_SLUGS = {"52-week-savings-challenge", "ultimate-budget-planner", "debt-payoff-accelerator", "kindgrid-autopilot-upload-test-20261009"}
TRUTHY = {"true", "1", "yes", "on"}


def enabled(name: str) -> bool:
    return os.getenv(name, "false").lower().strip() in TRUTHY


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def google_file_id(url: str, kind: str = "file") -> str:
    path = urlparse(str(url)).path
    if kind == "file":
        m = re.fullmatch(r"/file/d/([A-Za-z0-9_-]+)/view/?", path)
    elif kind == "document":
        m = re.fullmatch(r"/document/d/([A-Za-z0-9_-]+)/(?:edit|view)/?", path)
    else:
        m = None
    if urlparse(str(url)).netloc not in {"drive.google.com", "docs.google.com"} or not m:
        raise ValueError(f"Expected a real Google Drive {kind} link; got unsupported URL")
    return m.group(1)


def validate_destination(url: str) -> str:
    parsed = urlparse(str(url))
    require(parsed.scheme == "https", "Destination link must use HTTPS")
    require(parsed.netloc.lower() == "kindgridstudio.gumroad.com", "Unexpected destination host")
    require(re.fullmatch(r"/l/[a-z0-9-]+/?", parsed.path) is not None,
            "Destination must be an individual KindGrid Gumroad product")
    require(not parsed.query and not parsed.fragment, "Unexpected parameters on destination")
    return url


def validate_qa_metadata(row: dict) -> None:
    """Require a current, item-linked QA audit before any new publishing action."""
    require(str(row.get("QA Version", "")).strip() == QA_VERSION,
            "Requires retrospective KGS-QA-V2 audit before publishing")
    require(str(row.get("QA Outcome", "")).strip().upper() == "PASS",
            "QA Outcome must be PASS")
    google_file_id(row.get("QA Report Drive Link", ""), "document")
    stamp = str(row.get("QA Audited UTC", "")).strip()
    try:
        audited = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError("QA Audited UTC must contain a valid ISO-8601 timestamp") from None
    require(audited.tzinfo is not None, "QA audit timestamp requires UTC timezone")
    age = datetime.now(timezone.utc) - audited.astimezone(timezone.utc)
    require(timedelta(minutes=-5) <= age <= timedelta(days=14),
            "QA report is outdated or dated in the future; re-audit item")


def verify_qa_report(store, row: dict, item_id: str) -> None:
    """Independent existence/structure check for Gemini's signed QA record.

    This cannot prove visual/semantic perfection; it ensures auditable evidence
    exists and is specific to the item being released, never a stale placeholder.
    """
    validate_qa_metadata(row)
    report_id = google_file_id(row["QA Report Drive Link"], "document")
    report = store.get_doc_text(report_id)
    normalized = "\n".join(x.strip().upper() for x in report.splitlines())
    require(len(report.strip()) >= 350, "QA report must contain substantive inspection evidence")
    require(f"ITEM ID: {item_id.upper()}" in normalized, "QA report item ID mismatch")
    require(f"QA VERSION: {QA_VERSION}" in normalized, "QA version missing from linked report")
    require("RESULT: PASS" in normalized, "QA report has not confirmed PASS")
    for check in QA_FIELDS:
        require(f"{check}: PASS" in normalized, f"QA report missing {check}: PASS")
    require("EVIDENCE:" in normalized, "QA report lacks documented inspection evidence")


def validate_gumroad(row: dict, *, existing_release: bool = False) -> dict:
    require(str(row.get("QA Verified (YES/NO)", "")).upper() == "YES", "Gemini QA not approved")
    validate_qa_metadata(row)
    required_status = "RELEASE_READY" if existing_release else "READY"
    require(row.get("Upload Status") == required_status, "Not ready for Gumroad")
    product_id = str(row.get("Product ID", "")).strip()
    require(re.fullmatch(r"KGS-\d{3,}", product_id) is not None, "Invalid product ID")
    if existing_release:
        require(product_id == "KGS-003", "Only the known KGS-003 draft can use historical release")
    else:
        require(product_id not in EXISTING_PRODUCTS,
                "Existing product or draft must not be recreated")
    title = str(row.get("Product Name", "")).strip()
    require(len(title) >= 12, "Product title absent/too short")
    slug = str(row.get("Unique Slug", "")).strip()
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is not None, "Invalid slug")
    if existing_release:
        require(slug == "debt-payoff-accelerator", "Known KGS-003 draft slug mismatch")
    else:
        require(slug not in EXISTING_GUMROAD_SLUGS, "Existing Gumroad slug")
    try:
        price = Decimal(str(row.get("Price USD", "")))
        require(Decimal("0.50") <= price <= Decimal("100.00"), "Price out of configured guardrails")
    except InvalidOperation as exc:
        raise ValueError("Invalid product price") from exc
    return {"product_id": product_id, "title": title, "price": str(price), "slug": slug,
            "pdf": google_file_id(row.get("PDF Drive Link", "")),
            "cover": google_file_id(row.get("Cover Drive Link", "")),
            "listing_doc": google_file_id(row.get("Listing Copy Drive Link", ""), "document")}


def pin_due_at(row: dict) -> datetime:
    """Treat New York tz as authoritative; reject wrong EDT/EST labels."""
    day = datetime.strptime(str(row.get("Scheduled Date", "")), "%Y-%m-%d")
    clock = str(row.get("US Scheduled Time", ""))
    m = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)\s+(EDT|EST)\b", clock)
    require(m is not None, "Invalid US scheduled time label")
    local = day.replace(hour=int(m.group(1)), minute=int(m.group(2)), tzinfo=ZoneInfo("America/New_York"))
    require(local.strftime("%Z") == m.group(3), "Wrong EDT/EST label for date")
    return local.astimezone(timezone.utc)


def validate_pin(row: dict, now: datetime, lookahead_hours: int) -> dict:
    require(row.get("Status") == "READY", "Pin is not marked READY")
    require(str(row.get("QA Verified (YES/NO)", "")).upper() == "YES", "Pin is not QA approved")
    validate_qa_metadata(row)
    key = str(row.get("Queue ID", ""))
    require(re.fullmatch(r"Q-\d{2,}", key) is not None, "Invalid Pin ID")
    title = str(row.get("Pin Title", "")).strip()
    description = str(row.get("Pin Description", "")).strip()
    board = str(row.get("Target Board", "")).strip()
    require(title and description and board, "Missing title, description or board")
    require(len(title) <= 100 and len(description) <= 500, "Pinterest character limit exceeded")
    link = validate_destination(row.get("Destination URL", ""))
    file_id = google_file_id(row.get("Pin Image Drive Link", ""))
    due = pin_due_at(row)
    require(due > now, "Pin scheduled time has already passed")
    require(due <= now + timedelta(hours=lookahead_hours), "Pin date outside rolling queue window")
    require(not row.get("Actual Pinterest Pin URL"), "A Pin URL is already recorded")
    require(not row.get("Batch ID"), "A Buffer post ID is already recorded: reconcile, do not duplicate")
    return {"id": key, "title": title, "description": description, "board": board,
            "destination": link, "image_id": file_id, "due": due}


def get_listing_copy(text: str) -> tuple[str, str]:
    """Legacy listing kit supported, but never send entire kit as product description."""
    if "BEGIN_GUMROAD_DESCRIPTION" in text and "END_GUMROAD_DESCRIPTION" in text:
        description = text.split("BEGIN_GUMROAD_DESCRIPTION", 1)[1].split("END_GUMROAD_DESCRIPTION", 1)[0].strip()
        summary = ""
        if "BEGIN_GUMROAD_SUMMARY" in text and "END_GUMROAD_SUMMARY" in text:
            summary = text.split("BEGIN_GUMROAD_SUMMARY", 1)[1].split("END_GUMROAD_SUMMARY", 1)[0].strip()
    else:
        # Existing KGS-003 format from Gemini, which uses numbered section headings.
        m = re.search(r"2\.\s*Complete Gumroad Product Description\s*(.*?)\s*3\.\s*Recommended Gumroad Tags", text, re.S | re.I)
        require(m is not None, "Gemini listing needs BEGIN/END description markers")
        description = m.group(1).strip()
        s = re.search(r"1\.\s*Public Short Summary.*?\n\s*(.*?)\s*2\.\s*Complete Gumroad Product Description", text, re.S | re.I)
        summary = s.group(1).strip() if s else ""
    require(len(description) >= 250, "Listing description appears incomplete")
    require(len(description) <= 10000, "Listing description unusually long")
    require(not re.search(r"\ball sales.{0,40}final\b", description, re.I),
            "Gemini must review absolute 'all sales final' language before publication")
    return summary[:400], description


class GoogleStore:
    def __init__(self):
        import google.auth
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        secret = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "")
        if not secret:
            raise RuntimeError("Missing service account secret; setup required")
        info = json.loads(base64.b64decode(secret).decode("utf-8"))
        creds = service_account.Credentials.from_service_account_info(info, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/documents.readonly"])
        self.sheet = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.docs = build("docs", "v1", credentials=creds, cache_discovery=False)

    def get_rows(self, sheet_name: str) -> list[dict]:
        import urllib.parse
        escaped = sheet_name.replace("'", "''")
        result = self.sheet.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"'{escaped}'!A1:U1000").execute()
        values = result.get("values", [])
        if not values:
            return []
        header = [str(x) for x in values[0]]
        return [dict(zip(header, [str(v) if v is not None else "" for v in row])) | {"_sheet_row": i}
                for i, row in enumerate(values[1:], start=2)]

    def patch(self, sheet_name: str, row: dict, updates: dict) -> None:
        """Write only operational fields; never overwrite Gemini's creative columns."""
        header = self.sheet.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range=f"'{sheet_name}'!1:1").execute().get("values", [[]])[0]
        missing = set(updates) - set(header)
        if missing:
            raise RuntimeError(f"Dashboard is missing required operational columns: {missing}")
        data = []
        for k, v in updates.items():
            col = header.index(k)
            letters = ""
            while col >= 0:
                letters = chr(65 + col % 26) + letters
                col = col // 26 - 1
            data.append({"range": f"'{sheet_name}'!{letters}{row['_sheet_row']}", "values": [[str(v)]]})
        self.sheet.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID,
            body={"valueInputOption": "RAW", "data": data}).execute()

    def get_bytes(self, file_id: str, expected_type: str) -> bytes:
        from googleapiclient.http import MediaIoBaseDownload
        metadata = self.drive.files().get(fileId=file_id, fields="id,name,mimeType,size").execute()
        require(metadata.get("mimeType") == expected_type,
                f"Drive asset {file_id} has wrong media type")
        expected_size = int(metadata.get("size", 0))
        require(1000 <= expected_size <= 30 * 1024 * 1024, "Drive file size outside safety limits")
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, self.drive.files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        data = buf.getvalue()
        require(len(data) == expected_size, "Incomplete Drive download")
        return data

    def get_doc_text(self, doc_id: str) -> str:
        doc = self.docs.documents().get(documentId=doc_id, includeTabsContent=True).execute()
        blocks = []
        def flatten(items):
            for item in items:
                if "paragraph" in item:
                    blocks.append("".join(el.get("textRun", {}).get("content", "") for el in item["paragraph"].get("elements", [])))
                if "table" in item:
                    for row in item["table"].get("tableRows", []):
                        for cell in row.get("tableCells", []):
                            flatten(cell.get("content", []))
        if doc.get("tabs"):
            def recurse(tabs):
                for tab in tabs:
                    flatten(tab.get("documentTab", {}).get("body", {}).get("content", []))
                    recurse(tab.get("childTabs", []))
            recurse(doc["tabs"])
        else:
            flatten(doc.get("body", {}).get("content", []))
        return "".join(blocks)


def validate_pdf(data: bytes) -> int:
    from pypdf import PdfReader
    require(data.startswith(b"%PDF-"), "File is not a real PDF")
    pdf = PdfReader(io.BytesIO(data), strict=False)
    require(1 <= len(pdf.pages) <= 300, "Unexpected PDF page count")
    return len(pdf.pages)


def validate_image(data: bytes) -> tuple[int, int]:
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        width, height = im.size
        require(im.format in {"PNG", "JPEG"}, "Only PNG and JPG assets accepted")
        require(width >= 600 and height >= 600, "Image resolution too low")
        return width, height


class BufferClient:
    API = "https://api.buffer.com"
    def __init__(self):
        self.key = os.environ["BUFFER_API_KEY"]
        self.channel_id = os.environ["BUFFER_PINTEREST_CHANNEL_ID"]
        self.org_id = os.environ["BUFFER_ORGANIZATION_ID"]

    def graphql(self, query, variables=None):
        import requests
        res = requests.post(self.API, headers={"Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"}, json={"query": query, "variables": variables or {}}, timeout=25)
        res.raise_for_status()
        payload = res.json()
        if payload.get("errors"):
            raise RuntimeError(f"Buffer GraphQL error: {payload['errors'][0].get('message', 'unknown')}")
        return payload.get("data", {})

    def boards(self):
        q = '''query B($id: ChannelId!) { channel(input: {id:$id}) {
        metadata { ... on PinterestMetadata {boards {name serviceId}} }}}'''
        channel = self.graphql(q, {"id": self.channel_id}).get("channel") or {}
        boards = ((channel.get("metadata") or {}).get("boards") or [])
        require(bool(boards), "Buffer Pinterest boards unavailable; connect Pinterest first")
        return {board["name"].strip(): board["serviceId"] for board in boards}

    def scheduled(self):
        """Refuse to schedule if count is uncertain, to respect Buffer Free limit."""
        q = '''query Q($org:OrganizationId!, $channel:ChannelId!) { posts(
          first:50, input:{organizationId:$org, filter:{status:[scheduled],channelIds:[$channel]}})
          {edges{node{id dueAt}} pageInfo{hasNextPage}} }'''
        result = self.graphql(q, {"org": self.org_id, "channel": self.channel_id}).get("posts")
        require(result is not None, "Unable to check Buffer queue")
        require(not result.get("pageInfo", {}).get("hasNextPage"), "Queue count is unknown")
        return len(result.get("edges", []))

    def get_post(self, post_id: str) -> dict:
        q = '''query Post($id:PostId!) {post(input:{id:$id}) {id status externalLink metadata{... on PinterestPostMetadata{url}}}}'''
        return self.graphql(q, {"id": post_id}).get("post") or {}

    def create(self, pin: dict, image_url: str, board_id: str):
        mutation = '''mutation P($input:CreatePostInput!) {createPost(input:$input) {
        ... on PostActionSuccess {post{id status dueAt metadata{
          ... on PinterestPostMetadata {title url board{serviceId}}
        }}}
        ... on MutationError {message}
        }}'''
        body = {"channelId": self.channel_id, "text": pin["description"],
                "schedulingType": "automatic", "mode": "customScheduled",
                "dueAt": pin["due"].isoformat().replace("+00:00", "Z"),
                "aiAssisted": True,
                "assets": [{"image": {"url": image_url}}],
                "metadata": {"pinterest": {"boardServiceId": board_id,
                                           "title": pin["title"], "url": pin["destination"]}}}
        response = self.graphql(mutation, {"input": body}).get("createPost") or {}
        if not response.get("post"):
            raise RuntimeError("Buffer rejected Pin: " + response.get("message", "unknown response"))
        return response["post"]


def verify_public_product_url(url: str, expected_slug: str | None = None) -> None:
    """Do not market or mark an unpublished/404 Gumroad product as usable."""
    import requests
    parsed = urlparse(str(url))
    require(parsed.scheme == "https" and parsed.netloc.lower() in {
        "kindgridstudio.gumroad.com", "gumroad.com", "www.gumroad.com"
    }, "Gumroad destination is not on an authorised storefront")
    if expected_slug:
        require(parsed.path.rstrip("/").endswith("/" + expected_slug),
                "Public Gumroad URL does not match the approved product slug")
    try:
        response = requests.get(url, timeout=20, allow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0 KindGridQualityCheck/2.0"})
    except requests.RequestException:
        raise ValueError("Gumroad product page could not be reached") from None
    require(response.status_code == 200,
            f"Gumroad product page returned HTTP {response.status_code}; verify before marketing")
    final = urlparse(response.url)
    require(final.netloc.lower() in {"kindgridstudio.gumroad.com",
                                    "gumroad.com", "www.gumroad.com"},
            "Gumroad product page redirected outside permitted domains")
    require(len(response.content) > 1000, "Gumroad product page appears empty or inaccessible")


def cloudinary_upload(data: bytes, pin_id: str) -> str:
    import cloudinary
    import cloudinary.uploader
    require(bool(os.getenv("CLOUDINARY_URL")), "Cloudinary credentials missing")
    # The Cloudinary SDK reads CLOUDINARY_URL directly from the environment.
    cloudinary.config(secure=True)
    media = cloudinary.uploader.upload(io.BytesIO(data), resource_type="image",
        folder="kindgrid-pinterest", public_id=pin_id.lower(), overwrite=False, unique_filename=False)
    url = media.get("secure_url", "")
    require(url.startswith("https://res.cloudinary.com/"), "Cloudinary upload returned invalid URL")
    return url


def gumroad_cli(args: list[str]) -> dict:
    env = dict(os.environ)
    require(bool(env.get("GUMROAD_ACCESS_TOKEN")), "Gumroad seller token missing")
    cmd = ["gumroad"] + args + ["--json", "--no-input"]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=150, env=env)
    if result.returncode != 0:
        # CLI stderr may contain seller tokens or private account information.
        # Do not print raw output or blindly retry a possibly completed upload.
        raise RuntimeError(f"Gumroad CLI exited {result.returncode}; verify product state in Gumroad before retrying")
    return json.loads(result.stdout)


def gumroad_create_draft(store: GoogleStore, config: dict) -> tuple[str, str]:
    pdf_bytes = store.get_bytes(config["pdf"], "application/pdf")
    cover_bytes = store.get_bytes(config["cover"], "image/png")
    validate_pdf(pdf_bytes)
    validate_image(cover_bytes)
    summary, description = get_listing_copy(store.get_doc_text(config["listing_doc"]))
    existing = gumroad_cli(["products", "list", "--all"]).get("products", [])
    for p in existing:
        if (p.get("custom_permalink") == config["slug"] or
            config["slug"] in str(p.get("short_url", "")).split("/")[-1:]):
            raise ValueError("Slug already exists in Gumroad: reconciliation required, NOT a new product")
    with tempfile.TemporaryDirectory(prefix="kindgrid-") as folder:
        pdf_path = Path(folder) / "product.pdf"
        cover_path = Path(folder) / "cover.png"
        pdf_path.write_bytes(pdf_bytes)
        cover_path.write_bytes(cover_bytes)
        args = ["products", "create", "--draft", "--name", config["title"],
            "--price", config["price"], "--currency", "usd",
            "--type", "digital", "--custom-permalink", config["slug"],
            "--description", description, "--file", str(pdf_path),
            "--cover-image", str(cover_path)]
        if summary:
            args.extend(["--custom-summary", summary])
        output = gumroad_cli(args)
        product = output.get("product", {})
        product_id = product.get("id")
        require(bool(product_id), "Gumroad draft may have been created but ID not returned; reconcile manually")
        # Don't publish from an unverified draft. View fresh product after saving.
        reread = gumroad_cli(["products", "view", str(product_id)]).get("product", {})
        require(bool(reread) and not reread.get("published"), "Created product cannot be verified as a draft")
        require(str(reread.get("name", "")).strip() == config["title"], "Product name mismatch after reload")
        # Response shapes can evolve. If file/cover presence cannot be established, REVIEW.
        files = reread.get("files") or reread.get("rich_content_files") or []
        covers = reread.get("covers") or reread.get("cover_images") or []
        if not files or not covers:
            raise RuntimeError(f"Draft created with ID {product_id}, but PDF/cover response fields require manual inspection; do not retry")
        return str(product_id), f"https://gumroad.com/products/{product_id}/edit"


def finalize_existing_draft(store: GoogleStore, row: dict) -> str:
    """Publish ONLY the existing KGS-003 draft after Gemini's fresh V2 audit.

    Its ID and edit URL must match the already verified seller-owned draft.
    Never create a replacement. This path is not a retry after an API error.
    """
    require(row.get("Upload Status") == "RELEASE_READY",
            "Existing draft must pass retrospective audit and be RELEASE_READY")
    parsed = validate_gumroad(row, existing_release=True)
    verify_qa_report(store, row, "KGS-003")
    require(enabled("GUMROAD_AUTOPUBLISH"), "Gumroad publication disabled")
    draft_url = str(row.get("Gumroad Live URL", ""))
    m = re.fullmatch(r"https://gumroad\.com/products/([A-Za-z0-9_=-]+)/edit(?:/content)?/?", draft_url)
    require(bool(m), "KGS-003 draft must retain its genuine Gumroad edit URL")
    product_id = m.group(1)
    require(product_id == "wzlgpm", "KGS-003 existing draft ID mismatch; stop")
    # Validate source assets and updated listing copy before touching the draft.
    validate_pdf(store.get_bytes(parsed["pdf"], "application/pdf"))
    validate_image(store.get_bytes(parsed["cover"], "image/png"))
    summary, description = get_listing_copy(store.get_doc_text(parsed["listing_doc"]))
    before = gumroad_cli(["products", "view", product_id]).get("product", {})
    require(bool(before), "KGS-003 draft no longer exists")
    require(str(before.get("name", "")).strip() == parsed["title"],
            "KGS-003 title mismatch; do not change another product")
    require(before.get("published") is False,
            "KGS-003 already published or publication state uncertain")
    if before.get("custom_permalink"):
        require(str(before["custom_permalink"]) == parsed["slug"], "Draft slug mismatch")
    require(bool(before.get("files") or before.get("rich_content_files")),
            "Existing KGS-003 PDF attachment cannot be independently confirmed")
    require(bool(before.get("covers") or before.get("cover_images")),
            "Existing KGS-003 cover attachment cannot be independently confirmed")
    store.patch("Gumroad Upload Queue", row, {"Upload Status": "UPLOADING",
                "Last Attempt UTC": make_timestamp(),
                "Attempt Count": str(int(row.get("Attempt Count") or 0) + 1)})
    args = ["products", "update", product_id, "--description", description]
    if summary:
        args.extend(["--custom-summary", summary])
    gumroad_cli(args)
    gumroad_cli(["products", "publish", product_id])
    after = gumroad_cli(["products", "view", product_id]).get("product", {})
    require(after.get("published") is True, "KGS-003 publication needs manual reconciliation")
    url = "https://kindgridstudio.gumroad.com/l/debt-payoff-accelerator"
    verify_public_product_url(url, "debt-payoff-accelerator")
    store.patch("Gumroad Upload Queue", row, {"Upload Status": "PUBLISHED",
                "Gumroad Live URL": url, "Last Error": "",
                "Last Updated UTC": make_timestamp()})
    return "KGS-003: existing corrected draft automatically published and verified"


def make_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def process_gumroad(store: GoogleStore, row: dict) -> str:
    marker = make_timestamp()
    try:
        parsed = validate_gumroad(row)
        if enabled("LIVE_MODE"):
            verify_qa_report(store, row, parsed["product_id"])
        if not enabled("LIVE_MODE") or not enabled("GUMROAD_CREATE_DRAFTS"):
            return f"{parsed['product_id']}: validated metadata; dry run; no product created"
        store.patch("Gumroad Upload Queue", row, {"Upload Status": "UPLOADING",
                    "Last Attempt UTC": marker,
                    "Attempt Count": str(int(row.get("Attempt Count") or 0) + 1)})
        product_id, url = gumroad_create_draft(store, parsed)
        store.patch("Gumroad Upload Queue", row, {"Upload Status": "DRAFT_VERIFIED",
                    "Gumroad Live URL": url, "Last Error": "",
                    "Last Updated UTC": make_timestamp()})
        if enabled("GUMROAD_AUTOPUBLISH"):
            # Auto-publish ONLY the brand-new draft created and inspected in
            # this invocation. Never auto-process KGS-003 or historical drafts.
            gumroad_cli(["products", "publish", product_id])
            reread = gumroad_cli(["products", "view", product_id]).get("product", {})
            require(reread.get("published") is True,
                    "Publish action uncertain; do NOT retry or recreate product")
            canonical = f"https://kindgridstudio.gumroad.com/l/{parsed['slug']}"
            short_url = str(reread.get("short_url") or "")
            if short_url and short_url != canonical:
                require(urlparse(short_url).netloc.lower() in {
                    "gumroad.com", "www.gumroad.com", "kindgridstudio.gumroad.com"
                }, "Gumroad returned an unexpected public link")
            verify_public_product_url(canonical, parsed["slug"])
            store.patch("Gumroad Upload Queue", row, {"Upload Status": "PUBLISHED",
                        "Gumroad Live URL": canonical, "Last Error": "",
                        "Last Updated UTC": make_timestamp()})
            return f"{parsed['product_id']}: auto-published and verified ({product_id})"
        return f"{parsed['product_id']}: draft verified ({product_id}), NOT published"
    except ValueError as error:
        if enabled("LIVE_MODE"):
            store.patch("Gumroad Upload Queue", row, {"Upload Status": "NEEDS_FIX", "Last Error": str(error)[:450]})
        return f"{row.get('Product ID')}: NEEDS_FIX: {error}"
    except Exception as error:
        if enabled("LIVE_MODE"):
            store.patch("Gumroad Upload Queue", row, {"Upload Status": "REVIEW", "Last Error": str(error)[:450]})
        return f"{row.get('Product ID')}: REVIEW: {error}"


def process_pins(store: GoogleStore, rows: list[dict], now: datetime) -> list[str]:
    result = []
    active = enabled("LIVE_MODE") and enabled("PIN_AUTOSCHEDULE")
    lookahead = int(os.getenv("PIN_LOOKAHEAD_HOURS", "72"))
    client = None
    boards = {}
    slots = 0
    # Schedule no more than three Pins per NY calendar day, with at most one
    # per morning/afternoon/evening slot, even if Gemini adds duplicate rows.
    booked = set()
    counts = {}
    if active:
        historical = store.get_rows("Publishing Queue")
        for existing in historical:
            if existing.get("Status") in {"SCHEDULED_BUFFER", "PUBLISHED"}:
                day = existing.get("Scheduled Date")
                window = existing.get("Time Window")
                if day and window:
                    booked.add((day, window))
                    counts[day] = counts.get(day, 0) + 1
    for row in rows:
        try:
            pin = validate_pin(row, now, lookahead)
            if active:
                verify_qa_report(store, row, pin["id"])
            if not active:
                result.append(f"{pin['id']}: ready metadata, dry run; no API post created")
                continue
            calendar_day = row.get("Scheduled Date", "")
            slot = row.get("Time Window", "")
            require(slot in {"Morning", "Afternoon", "Evening"},
                    "Pin requires a recognised 3-per-day time window")
            require((calendar_day, slot) not in booked,
                    "This US daily Pinterest time window already has a scheduled or published Pin")
            require(counts.get(calendar_day, 0) < 3,
                    "Three Pinterest Pins already booked for this US calendar day")
            if client is None:
                client = BufferClient()
                boards = client.boards()
                slots = max(0, 10 - client.scheduled())
            if slots == 0:
                result.append("Buffer Free queue at 10 posts; wait for scheduled posts to publish")
                break
            require(pin["board"] in boards, f"Pinterest board '{pin['board']}' not in Buffer")
            verify_public_product_url(pin["destination"])
            image = store.get_bytes(pin["image_id"], "image/png")
            validate_image(image)
            store.patch("Publishing Queue", row, {"Status": "SCHEDULING",
                "Last Attempt UTC": make_timestamp(),
                "Attempt Count": str(int(row.get("Attempt Count") or 0) + 1)})
            image_url = cloudinary_upload(image, pin["id"])
            post = client.create(pin, image_url, boards[pin["board"]])
            # CRITICAL: Buffer's roadmap has a reported bug dropping destination URLs.
            # Immediately halt this item if returned Pin link is absent/wrong.
            returned_url = (post.get("metadata") or {}).get("url")
            # A successful API mutation can create a post even when response
            # metadata is incomplete. Never return it to READY automatically.
            if not post.get("id"):
                store.patch("Publishing Queue", row, {"Status": "LINK_REVIEW",
                    "Last Error": "Buffer may have created Pin but returned no post ID; inspect Buffer before retrying"})
                result.append(f"{pin['id']}: LINK_REVIEW; missing Buffer post ID")
                break
            if returned_url != pin["destination"]:
                store.patch("Publishing Queue", row, {"Status": "LINK_REVIEW",
                    "Last Error": "Buffer Pin destination URL absent/different; inspect created post ID " + str(post.get("id")),
                    "Batch ID": str(post.get("id", ""))})
                result.append(f"{pin['id']}: LINK_REVIEW; do not send further Pins until issue fixed")
                break
            store.patch("Publishing Queue", row, {"Status": "SCHEDULED_BUFFER",
                "Batch ID": str(post.get("id", "")), "Last Error": ""})
            result.append(f"{pin['id']}: scheduled in Buffer; NOT verified live on Pinterest")
            booked.add((calendar_day, slot))
            counts[calendar_day] = counts.get(calendar_day, 0) + 1
            slots -= 1
        except ValueError as error:
            if active and "outside rolling queue window" not in str(error):
                store.patch("Publishing Queue", row, {"Status": "NEEDS_FIX", "Last Error": str(error)[:450]})
            result.append(f"{row.get('Queue ID')}: {error}")
        except Exception as error:
            if active:
                store.patch("Publishing Queue", row, {"Status": "REVIEW", "Last Error": str(error)[:450]})
            result.append(f"{row.get('Queue ID')}: REVIEW: {error}")
            break
    return result


def monitor_existing_pins(store: GoogleStore, rows: list[dict]) -> list[str]:
    """Verify that Buffer actually sent a previously scheduled Pin."""
    if not (enabled("LIVE_MODE") and enabled("PIN_AUTOSCHEDULE")):
        return []
    scheduled = [r for r in rows if r.get("Status") == "SCHEDULED_BUFFER" and r.get("Batch ID")]
    if not scheduled:
        return []
    client = BufferClient()
    messages = []
    for row in scheduled[:10]:
        try:
            post = client.get_post(row["Batch ID"])
            status = post.get("status")
            if status == "sent":
                actual_url = post.get("externalLink", "")
                if not actual_url or "pinterest." not in urlparse(actual_url).netloc:
                    store.patch("Publishing Queue", row, {"Status": "LINK_REVIEW",
                        "Last Error": "Buffer reports sent but Pinterest URL unavailable"})
                    messages.append(f"{row.get('Queue ID')}: sent; missing live Pinterest URL")
                else:
                    store.patch("Publishing Queue", row, {"Status": "PUBLISHED",
                        "Actual Pinterest Pin URL": actual_url, "Last Error": ""})
                    messages.append(f"{row.get('Queue ID')}: verified published")
            elif status == "error":
                store.patch("Publishing Queue", row, {"Status": "NEEDS_FIX",
                    "Last Error": "Buffer reports Pinterest publishing error"})
                messages.append(f"{row.get('Queue ID')}: publishing error")
        except Exception as error:
            messages.append(f"{row.get('Queue ID')}: monitoring deferred: {error}")
    return messages


def main() -> int:
    active = enabled("LIVE_MODE") and not enabled("DISPATCH_DRY_RUN")
    if not active:
        # Even if LIVE_MODE accidentally true, an explicit dry-run must override it.
        os.environ["LIVE_MODE"] = "false"
    print(f"KindGrid Autopilot | live={active} | UTC={make_timestamp()}")
    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64"):
        print("SETUP_REQUIRED: Google service-account secret missing. No external writes.")
        return 0
    try:
        store = GoogleStore()
        gumrows = store.get_rows("Gumroad Upload Queue")
        pinrows = store.get_rows("Publishing Queue")
        ready_gum = [r for r in gumrows if r.get("Upload Status") == "READY" and r.get("QA Verified (YES/NO)") == "YES"]
        verified_drafts = [r for r in gumrows if r.get("Upload Status") == "DRAFT_VERIFIED" and r.get("QA Verified (YES/NO)") == "YES"]
        ready_pin = [r for r in pinrows if r.get("Status") == "READY" and r.get("QA Verified (YES/NO)") == "YES"]
        print(f"Queue: {len(ready_gum)} new products, {len(ready_pin)} Pins")
        # Historical drafts cannot be recreated. Only the specifically known
        # KGS-003 draft may be released automatically *after* Gemini sets
        # RELEASE_READY with a fresh item-specific QA V2 audit.
        if verified_drafts:
            print(f"Protected historical Gumroad drafts: {len(verified_drafts)}")
        release_rows = [r for r in gumrows if r.get("Product ID") == "KGS-003"
                        and r.get("Upload Status") == "RELEASE_READY"]
        if active and enabled("GUMROAD_AUTOPUBLISH") and release_rows:
            row = release_rows[0]
            try:
                print(finalize_existing_draft(store, row))
            except ValueError as error:
                store.patch("Gumroad Upload Queue", row, {
                    "Upload Status": "NEEDS_FIX", "Last Error": str(error)[:450]})
                print(f"KGS-003: NEEDS_FIX: {error}")
            except Exception as error:
                store.patch("Gumroad Upload Queue", row, {
                    "Upload Status": "REVIEW", "Last Error": type(error).__name__})
                print("KGS-003: REVIEW required; do not retry an uncertain release")
        else:
            for row in ready_gum[:int(os.getenv("MAX_GUMROAD_PER_RUN", "1"))]:
                print(process_gumroad(store, row))
        now = datetime.now(timezone.utc)
        for line in monitor_existing_pins(store, pinrows):
            print(line)
        # Once a previous Pin is in an uncertain state, halt *future* batches
        # until the owner reconciles that post; not merely the current run.
        uncertain_pins = [r.get("Queue ID") for r in pinrows
                          if r.get("Status") in {"LINK_REVIEW", "REVIEW", "SCHEDULING"}]
        if uncertain_pins and enabled("LIVE_MODE") and enabled("PIN_AUTOSCHEDULE"):
            print("PINTEREST_PAUSED: Unresolved Pin state(s): " + ", ".join(uncertain_pins[:10]))
            print("No further Pins scheduled until Buffer/dashboard statuses are reconciled.")
        else:
            for line in process_pins(store, ready_pin[:int(os.getenv("MAX_PINS_PER_RUN", "3"))], now):
                print(line)
        return 0
    except Exception as error:
        print(f"BLOCKED: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
