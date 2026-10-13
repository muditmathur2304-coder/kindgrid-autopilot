"""Recover and publish EXISTING verified KGS-013 Gumroad draft, never create new SKU."""
from __future__ import annotations
import io, os, sys, time
import requests
from zipfile import ZipFile
from src import autopilot as a
from scripts.release_kgs013_once import schedule_pin

ID="y4IKDWhW7lNztF7E8LR5pw=="
SKU="KGS-013"
SLUG="collectflow-invoice-followup-control"
PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
BASE="https://api.gumroad.com/v2"

def get_seller(path):
    token=os.environ.get("GUMROAD_ACCESS_TOKEN","").strip()
    a.require(token,"Gumroad token missing")
    r=requests.get(BASE+"/"+path,headers={"Authorization":"Bearer "+token,
                   "Accept":"application/json"},timeout=25)
    a.require(r.status_code==200,f"Read-only seller HTTP {r.status_code}")
    j=r.json()
    a.require(j.get("success") is True,"Seller lookup did not succeed")
    return j

def verified_detail():
    listing=get_seller("products").get("products") or []
    matches=[x for x in listing if
             str(x.get("custom_permalink") or "")==SLUG or
             str(x.get("short_url") or "").rstrip("/").endswith("/"+SLUG)]
    a.require(len(matches)==1 and str(matches[0].get("id") or "")==ID,
              "Existing seller draft slug does not uniquely match approved product ID")
    detail=get_seller("products/"+ID).get("product") or {}
    a.require(str(detail.get("id") or "")==ID,"Product detail returned unexpected ID")
    a.require(str(detail.get("name") or "")==
              "CollectFlow Studio — Invoice Follow-Up & Cash-Control System",
              "Product title mismatch on draft")
    a.require(str(detail.get("price"))=="1500","Gumroad price is not the approved $15")
    files=detail.get("files") or detail.get("rich_content_files") or []
    covers=detail.get("covers") or detail.get("cover_images") or []
    a.require(len(files)==2 and len(covers)>=3,
              "Expected both workbook/guide downloads and all three approved galleries")
    return detail

def main():
    a.require(a.enabled("LIVE_MODE"),"Live account publishing not enabled")
    store=a.GoogleStore()
    rows=[r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")==SKU]
    a.require(len(rows)==1,"KGS013 queue identity conflict")
    row=rows[0]
    a.require(row.get("Upload Status")=="REVIEW" and row.get("QA Outcome")=="PASS",
              "Seller recovery not in explicitly approved REVIEW state")
    a.require(row.get("Unique Slug")==SLUG,"KGS013 slug mismatch")
    a.verify_qa_report(store,row,SKU)
    pdf=store.get_bytes(a.google_file_id(row["PDF Drive Link"]),"application/pdf")
    xlsx=store.get_bytes(a.google_file_id(row["Bonus File Drive Link"]),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    a.require(a.validate_pdf(pdf)==5,"Illustrated guide no longer matches original")
    with ZipFile(io.BytesIO(xlsx)) as z:
        a.require(len([k for k in z.namelist() if k.startswith("xl/worksheets/sheet") and k.endswith(".xml")])==8,
                  "The original Excel download changed")
        a.require(len([k for k in z.namelist() if k.startswith("xl/media/")])>=2,
                  "Embedded infographic missing")
    before=verified_detail()
    print("EXISTING_DRAFT_VERIFIED TWO_FILES THREE_COVERS $15 NO_DUPLICATE")
    if before.get("published") is not True:
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
                    "Gumroad Live URL":"https://gumroad.com/products/"+ID+"/edit",
                    "Last Attempt UTC":a.make_timestamp(),
                    "Attempt Count":str(int(row.get("Attempt Count") or "0")+1)})
        try:
            a.gumroad_cli(["products","publish",ID])
        except Exception as e:
            # Read seller again to distinguish ambiguous CLI errors from actual failed publish.
            after=verified_detail()
            if after.get("published") is not True:
                store.patch("Gumroad Upload Queue",row,{"Upload Status":"REVIEW",
                            "Last Error":("EXISTING_DRAFT_PUBLISH_UNCERTAIN "+type(e).__name__)[:420]})
                raise
            print("CLI_RETURNED_ERROR_BUT_SELLER_CONFIRMS_PUBLISHED")
    final=verified_detail()
    a.require(final.get("published") is True,"Product still unpublished after existing draft recovery")
    last_error=None
    for attempt in range(3):
        try:
            a.verify_public_product_url(PUBLIC,SLUG)
            last_error=None
            break
        except ValueError as e:
            last_error=str(e)
            if attempt!=2: time.sleep(4)
    if last_error:
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"REVIEW",
                    "Last Error":"SELLER_PUBLISHED_PUBLIC_PAGE_UNVERIFIED "+last_error[:340]})
        raise RuntimeError("Public seller page not verified; leave Pinterest held")
    store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
                "Gumroad Live URL":PUBLIC,"Last Error":"","Last Updated UTC":a.make_timestamp()})
    print("GUMROAD_PUBLIC_VERIFIED "+PUBLIC)
    try:
        schedule_pin(store)
    except Exception as e:
        print("PIN_HELD_AFTER_LIVE_GUMROAD "+type(e).__name__+": "+str(e))

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("KGS013_EXISTING_DRAFT_RECOVERY_BLOCKED "+type(e).__name__+": "+str(e))
        sys.exit(1)
