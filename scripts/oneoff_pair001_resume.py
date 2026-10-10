"""KG-PAIR-001 premium paired launch. One paid book + one useful free starter.

This standalone launch is intentionally one-off and idempotent by refusing
pre-existing slugs and refusing queue statuses other than PAIR_READY.
It MUST NOT be rerun after an uncertain seller API response.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

PAIR_ID="KG-PAIR-001"
PAID_ID="KGS-006"
FREE_ID="KGS-007"
PAID_SLUG="paycheck-gap-playbook"
FREE_SLUG="paycheck-gap-starter"
PAID_URL="https://kindgridstudio.gumroad.com/l/"+PAID_SLUG
FREE_URL="https://kindgridstudio.gumroad.com/l/"+FREE_SLUG
OUT=Path("kindgrid-pair001-proof")

def save(proof):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"pair001_receipt.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")

def get_pair(store):
    rows=store.get_rows("Gumroad Upload Queue")
    items=[r for r in rows if r.get("Pair ID")==PAIR_ID]
    a.require(len(items)==2,"Pair must contain exactly one FREE and one PAID product.")
    paid=next((r for r in items if r.get("Pair Role")=="PAID"),None)
    free=next((r for r in items if r.get("Pair Role")=="FREE"),None)
    a.require(bool(paid) and bool(free),"Both approved pair roles are mandatory.")
    a.require(paid["Product ID"]==PAID_ID and free["Product ID"]==FREE_ID,
              "Pair must retain original assigned IDs.")
    a.require(paid["Paired Product ID"]==FREE_ID and free["Paired Product ID"]==PAID_ID,
              "Companion pointers are mismatched.")
    a.require(paid.get("Upload Status")=="REVIEW" and free.get("Upload Status")=="PAIR_READY",
              "Only the reconciled REVIEW paid draft and untouched free product may continue.")
    a.require(all(r.get("QA Verified (YES/NO)")=="YES" for r in items),
              "Pair contains an unapproved item.")
    a.require(float(paid["Price USD"])==7.00 and float(free["Price USD"])==0.00,
              "Price or freebie identity mismatch.")
    a.require(paid["Unique Slug"]==PAID_SLUG and free["Unique Slug"]==FREE_SLUG,
              "Pair slug mismatch.")
    a.verify_qa_report(store,paid,PAID_ID)
    a.verify_qa_report(store,free,FREE_ID)
    return paid,free

def source_bundle(store,paid,free,folder):
    vals={}
    for key,row,expected_pages in [("paid",paid,24),("free",free,4)]:
        pdf=store.get_bytes(a.google_file_id(row["PDF Drive Link"]),"application/pdf")
        cover=store.get_bytes(a.google_file_id(row["Cover Drive Link"]),"image/png")
        a.require(a.validate_pdf(pdf)==expected_pages,
                  f"{key} PDF has wrong page count")
        a.validate_image(cover)
        outpdf=folder/(f"{key}_paycheck_gap.pdf")
        outcover=folder/(f"{key}_cover.png")
        outpdf.write_bytes(pdf)
        outcover.write_bytes(cover)
        summary,desc=a.get_listing_copy(
            store.get_doc_text(a.google_file_id(row["Listing Copy Drive Link"],"document")))
        vals[key]={"pdf":outpdf,"cover":outcover,"summary":summary,
                   "description":desc,"row":row}
    assert PAID_URL in vals["free"]["description"],"The free description must link to exact paid page"
    excel=store.get_bytes(a.google_file_id(paid["Bonus File Drive Link"]),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with ZipFile(BytesIO(excel)) as z:
        a.require("xl/workbook.xml" in z.namelist(),"Bonus workbook invalid")
        a.require(any(x.startswith("xl/worksheets/sheet") for x in z.namelist()),
                  "Bonus workbook has no sheets")
    xlsx=folder/"Paycheck_Gap_Interactive_Cashflow_Companion.xlsx"
    xlsx.write_bytes(excel)
    vals["paid"]["bonus"]=xlsx
    for tag,column in [("paid","Gallery Image 1 Drive Link"),
                      ("paid2","Gallery Image 2 Drive Link"),
                      ("free","Gallery Image 1 Drive Link")]:
        row=paid if tag.startswith("paid") else free
        raw=store.get_bytes(a.google_file_id(row[column]),"image/png")
        a.validate_image(raw)
        target=folder/(tag+"_preview.png")
        target.write_bytes(raw)
        vals[tag+"_preview"]=target
    return vals

def preflight(store):
    a.require(os.getenv("KINDGRID_OWNER_AUTHORIZED_PAIR001")=="true",
              "Pair live authorization not active.")
    a.require(bool(os.getenv("GUMROAD_ACCESS_TOKEN")),
              "Seller API integration missing.")
    a.require(bool(os.getenv("BUFFER_API_KEY")) and bool(os.getenv("CLOUDINARY_URL")),
              "Pinterest/Buffer/Cloudinary integration missing.")
    paid,free=get_pair(store)
    for key in ["Q-45","Q-46","Q-47"]:
        rows=[p for p in store.get_rows("Publishing Queue")
              if p.get("Queue ID")==key]
        a.require(len(rows)==1,f"Pin {key} not unique in queue")
        row=rows[0]
        a.require(row.get("Status")=="PREPARED_PENDING_LIVE_URL"
                  and not row.get("Batch ID"),f"{key} may already have been submitted")
        a.verify_qa_report(store,row,key)
    # An actual earlier CLI command created a valid unpublished paid draft but
    # returned an error during media attachment. NEVER create it again.
    current=a.gumroad_cli(["products","list","--all"]).get("products",[])
    matching=[]
    for product in current:
        slug=str(product.get("custom_permalink") or "")
        last=str(product.get("short_url") or "").rstrip("/").split("/")[-1]
        if slug==FREE_SLUG or last==FREE_SLUG:
            raise ValueError("Free product may already exist; do not duplicate it")
        if slug==PAID_SLUG or last==PAID_SLUG:
            matching.append(product)
    a.require(len(matching)==1,
              "Exactly one existing paid slug is required for reconciliation")
    pid=str(matching[0].get("id") or "")
    a.require(pid=="n2HmiRQFXZ3M6iym7pRJ8A==",
              "Existing draft ID changed since independent seller readback")
    existing=a.gumroad_cli(["products","view",pid]).get("product") or {}
    a.require(existing.get("published") is False,
              "Paid product already published or cannot verify draft state")
    a.require(str(existing.get("name") or "")==paid["Product Name"],
              "Existing paid draft title differs from approved title")
    a.require(len(existing.get("files") or existing.get("rich_content_files") or [])>=2,
              "Existing paid draft must contain both actual PDF and Excel companion")
    a.require(bool(existing.get("covers") or existing.get("cover_images")),
              "Existing paid draft cover absent; stop for manual review")
    client=a.BufferClient()
    boards=client.boards()
    a.require("Budgeting Printables & Cash Stuffing" in boards,
              "Budgeting Pinterest board missing")
    a.require(client.scheduled()<=6,
              "Buffer queue has insufficient slots for a three-Pin campaign")
    return paid,free,pid

def create_draft(files,slug,title,price,summary,description,free=False,bonus=None,previews=None):
    args=["products","create","--draft","--name",title,"--price",price,
          "--currency","usd","--type","digital","--custom-permalink",slug,
          "--description",description,"--custom-summary",summary]
    if free:
        args+=["--pay-what-you-want"]
    args+=["--file",str(files["pdf"])]
    if bonus:
        args+=["--file",str(bonus)]
    # Minimal proven media path for the genuinely FREE starter; no repeated
    # optional preview uploads that caused the prior paid draft partial failure.
    args+=["--cover-image",str(files["cover"])]
    response=a.gumroad_cli(args)
    item=response.get("product") or {}
    ident=str(item.get("id") or "")
    a.require(bool(ident),
              "Gumroad could have created a draft but omitted its ID: do not retry.")
    read=a.gumroad_cli(["products","view",ident]).get("product") or {}
    a.require(read.get("published") is False and str(read.get("name") or "").strip()==title,
              "Draft identity or published status not verified")
    attached=read.get("files") or read.get("rich_content_files") or []
    cover=read.get("covers") or read.get("cover_images") or []
    needed=2 if bonus else 1
    a.require(len(attached)>=needed,
              f"Draft {ident}: expected {needed} attached downloadable files, got {len(attached)}")
    a.require(bool(cover),f"Draft {ident}: cover is not confirmed")
    return ident

def publish(ident,slug):
    a.gumroad_cli(["products","publish",ident])
    read=a.gumroad_cli(["products","view",ident]).get("product") or {}
    a.require(read.get("published") is True,
              "Seller API did not confirm public publication; do not retry.")
    url="https://kindgridstudio.gumroad.com/l/"+slug
    a.verify_public_product_url(url,slug)
    return url

def live_launch():
    store=a.GoogleStore()
    paid,free,pid=preflight(store)
    proof={"pair_id":PAIR_ID,"paid":PAID_ID,"free":FREE_ID,"phase":"VALIDATED",
           "started_at":a.make_timestamp(),"pinterest":{}}
    save(proof)
    with tempfile.TemporaryDirectory(prefix="kgs-pair-001-") as temp:
        directory=Path(temp)
        vals=source_bundle(store,paid,free,directory)
        proof["phase"]="SOURCE_ASSETS_VERIFIED"
        save(proof)
        # Reconcile and PUBLISH precisely the original seller draft identified
        # by the previous independently confirmed read-only Gumroad inspection.
        # It already has the paid PDF, workbook and cover. Never create another.
        proof["paid_gumroad_id"]=pid
        proof["phase"]="RECONCILED_PAID_DRAFT_FILES_VERIFIED"
        save(proof)
        store.patch("Gumroad Upload Queue",paid,{"Upload Status":"UPLOADING",
            "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2"})
        proof["phase"]="EXISTING_PAID_PUBLISH_ATTEMPTED_NO_RETRY"
        save(proof)
        try:
            live=publish(pid,PAID_SLUG)
            proof["paid_public_url"]=live
            proof["phase"]="PAID_PUBLIC_URL_VERIFIED"
            save(proof)
            store.patch("Gumroad Upload Queue",paid,{
                "Upload Status":"PUBLISHED","Gumroad Live URL":live,
                "Last Error":"","Last Updated UTC":a.make_timestamp()})
            print("KG_PAIR001_PAID_EXISTING_DRAFT_VERIFIED "+live)
        except Exception as ex:
            store.patch("Gumroad Upload Queue",paid,{
                "Upload Status":"REVIEW",
                "Last Error":(type(ex).__name__+": "+str(ex))[:380]})
            proof["phase"]="PAID_REVIEW_NO_RETRY"
            save(proof)
            raise

        # Publish the FREE starter only after paid product is demonstrably live.
        a.verify_public_product_url(PAID_URL,PAID_SLUG)
        store.patch("Gumroad Upload Queue",free,{"Upload Status":"UPLOADING",
            "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
        proof["phase"]="FREE_CREATE_ATTEMPTED_NO_BLIND_RETRY"
        save(proof)
        try:
            fid=create_draft(vals["free"],FREE_SLUG,free["Product Name"],
                       free["Price USD"],vals["free"]["summary"],
                       vals["free"]["description"],free=True,
                       previews=[vals["free_preview"]])
            proof["free_gumroad_id"]=fid
            proof["phase"]="FREE_DRAFT_FILES_VERIFIED"
            save(proof)
            free_url=publish(fid,FREE_SLUG)
            proof["free_public_url"]=free_url
            proof["phase"]="BOTH_PUBLIC_URLS_VERIFIED"
            save(proof)
            store.patch("Gumroad Upload Queue",free,{
                "Upload Status":"PUBLISHED","Gumroad Live URL":free_url,
                "Last Error":"","Last Updated UTC":a.make_timestamp()})
            print("KG_PAIR001_FREE_VERIFIED "+free_url)
        except Exception as ex:
            store.patch("Gumroad Upload Queue",free,{
                "Upload Status":"REVIEW",
                "Last Error":(type(ex).__name__+": "+str(ex))[:380]})
            proof["phase"]="FREE_REVIEW_NO_RETRY_PAID_ALREADY_LIVE"
            save(proof)
            raise

    # Marketing releases require BOTH sellers' public pages, the matching links,
    # and individual signed QA docs. The freebie is the default landing page.
    rows=store.get_rows("Publishing Queue")
    selected=[r for r in rows if r.get("Queue ID") in {"Q-45","Q-46","Q-47"}]
    for r in selected:
        a.verify_public_product_url(r["Destination URL"])
        store.patch("Publishing Queue",r,{
            "Status":"READY","QA Verified (YES/NO)":"YES",
            "Last Error":"","Last Attempt UTC":a.make_timestamp()})
    rows=store.get_rows("Publishing Queue")
    selected=[r for r in rows if r.get("Queue ID") in {"Q-45","Q-46","Q-47"}]
    os.environ["LIVE_MODE"]="true"
    os.environ["PIN_AUTOSCHEDULE"]="true"
    os.environ["PIN_LOOKAHEAD_HOURS"]="72"
    os.environ["MAX_PINS_PER_RUN"]="3"
    result=a.process_pins(store,selected,datetime.now(timezone.utc))
    proof["pinterest"]=result
    proof["phase"]="BOTH_GUMROAD_LIVE_PIN_BATCH_SUBMITTED"
    save(proof)
    for msg in result:
        print("KG_PAIR001_PIN_RESULT: "+msg)
    final={r["Queue ID"]:r.get("Status") for r in store.get_rows("Publishing Queue")
           if r.get("Queue ID") in {"Q-45","Q-46","Q-47"}}
    proof["final_pin_statuses"]=final
    save(proof)
    print("KG_PAIR001_SUMMARY: "+json.dumps(final,sort_keys=True))
    a.require(all(status=="SCHEDULED_BUFFER" for status in final.values())
              and len(final)==3,
              "Some Pinterest Pins were not scheduled; inspect queue and Buffer, do NOT rerun")
    return 0

if __name__=="__main__":
    try:
        sys.exit(live_launch())
    except Exception as e:
        print("KG_PAIR001_HALT_AND_RECONCILE "+type(e).__name__+": "+str(e)[:340])
        print("KG_PAIR001_NO_AUTOMATIC_RETRY")
        sys.exit(1)
