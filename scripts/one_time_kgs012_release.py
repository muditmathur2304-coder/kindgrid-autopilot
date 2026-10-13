"""One-time owner-authorized KGS-012 BakeBatch seller release.

Single use only. Fail closed. Never automatically retry this script following
a seller mutation, even when the CLI returns an error.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from src import autopilot as a

ITEM = "KGS-012"
SLUG = "bakebatch-weekly-production-planner"
PAID_PRICE = "14.00"


def release() -> None:
    a.require(a.enabled("LIVE_MODE"), "Publisher repository live flag is disabled")
    store = a.GoogleStore()
    rows = [r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID") == ITEM]
    a.require(len(rows) == 1, "KGS-012 row is missing or duplicated")
    row = rows[0]
    a.require(row.get("Upload Status") == "READY" and
              row.get("QA Verified (YES/NO)") == "YES" and
              row.get("QA Outcome") == "PASS", "KGS-012 is not genuinely QA-approved")
    a.require(row.get("Unique Slug") == SLUG and row.get("Price USD") == PAID_PRICE,
              "KGS-012 name/slug/price drift")
    a.verify_qa_report(store, row, ITEM)

    # Source files, mathematical model and exact deliverables are checked BEFORE a seller write.
    pdf = store.get_bytes(a.google_file_id(row["PDF Drive Link"]), "application/pdf")
    cover = store.get_bytes(a.google_file_id(row["Cover Drive Link"]), "image/png")
    xlsx = store.get_bytes(a.google_file_id(row["Bonus File Drive Link"]),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    gallery = [store.get_bytes(a.google_file_id(row[k]), "image/png")
               for k in ("Gallery Image 1 Drive Link", "Gallery Image 2 Drive Link")]
    a.require(a.validate_pdf(pdf) == 6, "Guide must contain exactly six pages")
    a.validate_image(cover)
    for picture in gallery:
        a.validate_image(picture)
    with ZipFile(BytesIO(xlsx)) as zipped:
        names = zipped.namelist()
        drawings = [x for x in names if x.startswith("xl/media/")]
        sheets = [x for x in names if x.startswith("xl/worksheets/sheet") and x.endswith(".xml")]
        a.require("xl/workbook.xml" in names and len(sheets) == 4 and
                  len(drawings) >= 2 and
                  all(len(zipped.read(name)) > 1000 for name in drawings),
                  "The actual workbook or its premium embedded visuals are incomplete")
    summary, description = a.get_listing_copy(store.get_doc_text(
        a.google_file_id(row["Listing Copy Drive Link"], "document")))
    a.require("three" in description.lower() and "eight" in description.lower(),
              "Listing must disclose the model's product/ingredient limits")
    a.require("six-page guide" in description.lower() or "six" in description.lower(),
              "Description must accurately identify the guide")

    # Seller-side check is distinct from the queue check.
    existing = a.gumroad_cli(["products", "list", "--all"]).get("products", [])
    for item in existing:
        short = str(item.get("short_url") or "").rstrip("/").split("/")[-1]
        custom = str(item.get("custom_permalink") or "")
        a.require(custom != SLUG and short != SLUG, "Seller already has this slug; reconcile")

    store.patch("Gumroad Upload Queue", row, {
        "Upload Status": "UPLOADING", "Last Attempt UTC": a.make_timestamp(),
        "Attempt Count": str(int(row.get("Attempt Count") or "0") + 1),
    })
    try:
        with TemporaryDirectory(prefix="kindgrid-kgs012-") as folder:
            folder = Path(folder)
            paths = {
                "pdf": folder / "BakeBatch_Illustrated_Field_Guide.pdf",
                "xlsx": folder / "BakeBatch_Weekly_Bakery_Planner.xlsx",
                "cover": folder / "BakeBatch_Gumroad_Cover.png",
                "gallery1": folder / "BakeBatch_Gallery_Cost.png",
                "gallery2": folder / "BakeBatch_Gallery_Flow.png",
            }
            for name, body in (("pdf", pdf), ("xlsx", xlsx), ("cover", cover),
                               ("gallery1", gallery[0]), ("gallery2", gallery[1])):
                paths[name].write_bytes(body)
            cmd = ["products", "create", "--draft",
                   "--name", row["Product Name"],
                   "--price", PAID_PRICE, "--currency", "usd", "--type", "digital",
                   "--custom-permalink", SLUG,
                   "--description", description, "--custom-summary", summary,
                   "--file", str(paths["xlsx"]), "--file", str(paths["pdf"]),
                   "--cover-image", str(paths["cover"]),
                   "--thumbnail", str(paths["cover"]),
                   "--preview-image", str(paths["gallery1"]),
                   "--preview-image", str(paths["gallery2"])]
            created = a.gumroad_cli(cmd).get("product") or {}
            ident = str(created.get("id") or "")
            a.require(ident, "Gumroad might have created a draft; missing product ID: DO NOT retry")
            draft = a.gumroad_cli(["products", "view", ident]).get("product") or {}
            files = draft.get("files") or draft.get("rich_content_files") or []
            covers = draft.get("covers") or draft.get("cover_images") or []
            a.require(draft.get("published") is False and
                      draft.get("name") == row["Product Name"] and
                      len(files) >= 2 and bool(covers),
                      "Gumroad draft files or cover not verified; manual reconciliation needed")
            store.patch("Gumroad Upload Queue", row, {
                "Upload Status": "DRAFT_VERIFIED",
                "Gumroad Live URL": f"https://gumroad.com/products/{ident}/edit",
                "Last Updated UTC": a.make_timestamp()
            })
            a.gumroad_cli(["products", "publish", ident])
            final = a.gumroad_cli(["products", "view", ident]).get("product") or {}
            a.require(final.get("published") is True and
                      len(final.get("files") or final.get("rich_content_files") or []) >= 2,
                      "Published state or both customer files unverified; DO NOT retry")
            public = f"https://kindgridstudio.gumroad.com/l/{SLUG}"
            a.verify_public_product_url(public, SLUG)
            store.patch("Gumroad Upload Queue", row, {
                "Upload Status": "PUBLISHED", "Gumroad Live URL": public,
                "Last Error": "", "Last Updated UTC": a.make_timestamp()
            })
            print(f"{ITEM}: VERIFIED PUBLISHED {public} | two files, cover and gallery source")
    except Exception as exc:
        # No second create attempt. A seller mutation may have succeeded even when
        # CLI response or public page verification failed.
        store.patch("Gumroad Upload Queue", row, {
            "Upload Status": "REVIEW",
            "Last Error": (type(exc).__name__ + ": " + str(exc))[:450],
            "Last Updated UTC": a.make_timestamp(),
        })
        raise


if __name__ == "__main__":
    release()
