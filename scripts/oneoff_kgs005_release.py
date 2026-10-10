"""One-time owner-authorized KGS-005 Gumroad product + Q-44 Pinterest Pin."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

OUT=Path("kindgrid-kgs005-release-proof")
SLUG="subscription-renewal-control-kit"
TITLE="Subscription & Renewal Control - 7-Page Printable Kit"
PRICE="4.00"
URL="https://kindgridstudio.gumroad.com/l/"+SLUG
BOARD="Budgeting Printables & Cash Stuffing"

def save(result):
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"release_receipt.json").write_text(json.dumps(result,indent=2),encoding="utf-8")

def main():
    a.require(os.getenv("KINDGRID_KGS005_OWNER_AUTHORIZED_ONETIME")=="true","Owner authorization absent")
    a.require(all(os.getenv(n) for n in ["GOOGLE_SERVICE_ACCOUNT_JSON_B64","GUMROAD_ACCESS_TOKEN","BUFFER_API_KEY","CLOUDINARY_URL"]),"Required integration unavailable")
    store=a.GoogleStore()
    rows=[r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-005"]
    a.require(len(rows)==1,"KGS-005 must exist once in the product queue")
    row=rows[0]
    a.require(row.get("Upload Status")=="PREPARED","Do not recreate an existing Gumroad product")
    a.require(row.get("Unique Slug")==SLUG and row.get("Product Name")==TITLE,"Wrong product identity")
    ready=dict(row,**{"Upload Status":"READY"})
    parsed=a.validate_gumroad(ready)
    a.verify_qa_report(store,ready,"KGS-005")
    a.require(parsed["price"]==PRICE,"Price differs from owner's product")
    pdf=store.get_bytes(parsed["pdf"],"application/pdf")
    cover=store.get_bytes(parsed["cover"],"image/png")
    pin=store.get_bytes("1gfPY17Op2xNXxQ_ljlLBEMDlk5XRiwbu","image/png")
    a.require(a.validate_pdf(pdf)==7,"Wrong PDF page count")
    a.validate_image(cover);a.validate_image(pin)
    summary,description=a.get_listing_copy(store.get_doc_text(parsed["listing_doc"]))
    a.require("subscription" in description.lower() and "renewal" in description.lower(),"Wrong listing description")
    pins=[r for r in store.get_rows("Publishing Queue") if r.get("Queue ID")=="Q-44"]
    a.require(len(pins)==1,"Q-44 queue row absent or duplicated")
    q=pins[0]
    a.require(q.get("Status")=="PREPARED_PENDING_LIVE_URL" and not q.get("Batch ID"),"Q-44 may already exist")
    a.require(q.get("Destination URL")==URL,"Pin URL mismatch")
    OUT.mkdir(exist_ok=True,parents=True)
    pdffile=OUT/"KGS005_Subscription_Renewal_Control.pdf"
    coverfile=OUT/"KGS005_Gumroad_Cover.png"
    pinfile=OUT/"Q44_Pinterest_Pin.png"
    pdffile.write_bytes(pdf);coverfile.write_bytes(cover);pinfile.write_bytes(pin)
    proof={"product_id":"KGS-005","pin_id":"Q-44","price_usd":PRICE,"public_url":URL,
           "gumroad":"NOT_ATTEMPTED","pinterest":"NOT_ATTEMPTED","created_utc":a.make_timestamp()}
    save(proof)

    existing=a.gumroad_cli(["products","list","--all"]).get("products",[])
    for item in existing:
        if str(item.get("custom_permalink") or "")==SLUG or str(item.get("short_url") or "").rstrip("/").endswith("/"+SLUG):
            proof["gumroad"]="DUPLICATE_PROTECTED";save(proof)
            raise ValueError("Slug already exists in Gumroad; no repeated publication")
    store.patch("Gumroad Upload Queue",row,{"Upload Status":"UPLOADING",
                 "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
    proof["gumroad"]="CREATION_ATTEMPTED_DO_NOT_RETRY"
    save(proof)
    try:
        resp=a.gumroad_cli(["products","create","--draft","--name",TITLE,"--price",PRICE,
               "--currency","usd","--type","digital","--custom-permalink",SLUG,
               "--description",description,"--file",str(pdffile),"--cover-image",str(coverfile)])
        p=resp.get("product") or {}
        seller_id=str(p.get("id") or "")
        a.require(bool(seller_id),"Gumroad may have created draft but did not return ID")
        proof["seller_id"]=seller_id
        proof["draft_edit_url"]=f"https://gumroad.com/products/{seller_id}/edit"
        proof["gumroad"]="DRAFT_CREATED";save(proof)
        readback=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
        a.require(readback.get("published") is False and str(readback.get("name") or "")==TITLE,
                  "New Gumroad draft identity mismatch")
        a.require(bool(readback.get("files") or readback.get("rich_content_files")) and
                  bool(readback.get("covers") or readback.get("cover_images")),"PDF or cover not confirmed")
        proof["gumroad"]="DRAFT_PDF_AND_COVER_VERIFIED";save(proof)
        a.gumroad_cli(["products","publish",seller_id])
        readback=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
        a.require(readback.get("published") is True,"Gumroad publish state uncertain")
        proof["gumroad"]="PUBLISHED_API";save(proof)
        a.verify_public_product_url(URL,SLUG)
        proof["gumroad"]="PUBLISHED_PUBLIC_VERIFIED";save(proof)
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
                   "Gumroad Live URL":URL,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        print("KGS005_GUMROAD_LIVE_VERIFIED: "+URL)
    except Exception as err:
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"REVIEW",
                    "Last Error":(type(err).__name__+": "+str(err))[:400]})
        proof["gumroad"]="REVIEW_NO_AUTOMATIC_RETRY";save(proof)
        raise

    # This separate one-off Pinterest submission starts ONLY after the public
    # seller URL has been independently checked. No historical queue rows change.
    try:
        buffer=a.BufferClient()
        boards=buffer.boards()
        a.require(BOARD in boards,"Expected Pinterest board not connected")
        a.require(buffer.scheduled()<10,"Buffer free queue is full")
        title=q["Pin Title"].strip();desc=q["Pin Description"].strip()
        a.require(title and desc and len(title)<=100 and len(desc)<=500,"Pin text invalid")
        due=datetime.now(timezone.utc)+timedelta(minutes=7)
        image_url=a.cloudinary_upload(pin,"kgs005-subscription-q44-20261010")
        proof["pin_image_url"]=image_url
        proof["pinterest"]="PIN_IMAGE_HOSTED";save(proof)
        store.patch("Publishing Queue",q,{"Status":"SCHEDULING",
                    "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
        proof["pinterest"]="BUFFER_CREATE_ATTEMPTED_NO_RETRY";save(proof)
        payload={"id":"Q-44","title":title,"description":desc,
                 "board":BOARD,"destination":URL,"due":due}
        post=buffer.create(payload,image_url,boards[BOARD])
        buffer_id=str(post.get("id") or "")
        proof["buffer_post_id"]=buffer_id
        proof["scheduled_utc"]=due.isoformat()
        if not buffer_id or str((post.get("metadata") or {}).get("url") or "")!=URL:
            store.patch("Publishing Queue",q,{"Status":"LINK_REVIEW",
                         "Last Error":"Buffer ID or destination uncertain. Do not duplicate."})
            proof["pinterest"]="LINK_REVIEW";save(proof)
            raise ValueError("Buffer response cannot be safely confirmed")
        nyt=due.astimezone(ZoneInfo("America/New_York"))
        ist=due.astimezone(ZoneInfo("Asia/Kolkata"))
        label=nyt.strftime("%H:%M %Z")+" / "+ist.strftime("%H:%M IST")
        store.patch("Publishing Queue",q,{"Status":"SCHEDULED_BUFFER",
                   "Batch ID":buffer_id,"US Scheduled Time":label,
                   "Last Error":"One-time Pin; awaiting actual Pinterest delivery"})
        proof["pinterest"]="SCHEDULED_BUFFER";save(proof)
        print("KGS005_PIN_SCHEDULED_BUFFER: "+buffer_id)
        print("KGS005_PIN_DUE_UTC: "+due.isoformat())
    except Exception as err:
        if proof.get("pinterest")!="LINK_REVIEW":
            uncertain=proof.get("pinterest")=="BUFFER_CREATE_ATTEMPTED_NO_RETRY"
            store.patch("Publishing Queue",q,{"Status":"REVIEW" if uncertain else "NEEDS_FIX",
                       "Last Error":(type(err).__name__+": "+str(err))[:400]})
        save(proof)
        raise
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as err:
        print("KGS005_RECONCILE_BEFORE_RETRY: "+type(err).__name__+": "+str(err)[:320])
        print("DO_NOT_RERUN_THIS_ONE_TIME_WORKFLOW")
        sys.exit(1)
