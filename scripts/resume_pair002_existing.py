"""OWNER-AUTHORIZED SINGLE ATTEMPT: reconcile KGS-008 existing paid draft; then KGS-009 free; Q48-Q50 Pins.

An earlier live attempt may have created the PAID draft. NEVER create it again.
Any uncertain seller or Buffer response stops execution with REVIEW, no automatic retry.
"""
import json,os,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import autopilot as a
from src import paired_release as pair
from scripts import launch_pair002_now as previous

PAIR_ID="KG-PAIR-002"
PAID_ID="KGS-008"
FREE_ID="KGS-009"
PAID_SLUG="market-day-margin-guide"
FREE_SLUG="before-you-book-booth-free"
PAID_URL="https://kindgridstudio.gumroad.com/l/"+PAID_SLUG
FREE_URL="https://kindgridstudio.gumroad.com/l/"+FREE_SLUG
OUT=Path("kindgrid-pair002-resume-proof")

def receipt(note,**kwargs):
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"status.json"
    try: state=json.loads(path.read_text()) if path.exists() else {}
    except (ValueError,OSError):state={}
    state.update(kwargs)
    state["step"]=note
    state["timestamp_utc"]=a.make_timestamp()
    path.write_text(json.dumps(state,indent=2),encoding="utf-8")
    print("PAIR002_STAGE "+note)

def get_rows(store):
    rows=store.get_rows("Gumroad Upload Queue")
    paid=[r for r in rows if r.get("Product ID")==PAID_ID]
    free=[r for r in rows if r.get("Product ID")==FREE_ID]
    a.require(len(paid)==1 and len(free)==1,"Expected EXACTLY one existing paid and free queue row")
    paid,free=paid[0],free[0]
    a.require(paid.get("Upload Status")=="REVIEW" and free.get("Upload Status")=="PAIR_HELD",
              "Pair was modified since the last reconciliation; refuse uncertain retry")
    a.require(paid["Pair ID"]==PAIR_ID and free["Pair ID"]==PAIR_ID,"Pair identity changed")
    a.require(paid.get("Pair Role")=="PAID" and free.get("Pair Role")=="FREE","Roles changed")
    a.require(paid.get("Paired Product ID")==FREE_ID and free.get("Paired Product ID")==PAID_ID,
              "Reciprocal pairing mismatch")
    a.require(paid.get("Unique Slug")==PAID_SLUG and free.get("Unique Slug")==FREE_SLUG,
              "Gumroad slugs changed")
    a.require(float(paid["Price USD"])==9.0 and float(free["Price USD"])==0.0,"Unexpected pricing")
    a.require(paid.get("QA Verified (YES/NO)")=="YES" and free.get("QA Verified (YES/NO)")=="YES",
              "The required product QA approval has been revoked")
    a.validate_qa_metadata(paid); a.validate_qa_metadata(free)
    a.verify_qa_report(store,paid,PAID_ID)
    a.verify_qa_report(store,free,FREE_ID)
    return paid,free

def check_existing_draft(paid):
    products=a.gumroad_cli(["products","list","--all"]).get("products",[])
    found=[];free_found=[]
    for p in products:
        slug=str(p.get("custom_permalink") or "")
        tail=str(p.get("short_url") or "").rstrip("/").split("/")[-1]
        if slug==PAID_SLUG or tail==PAID_SLUG:found.append(p)
        if slug==FREE_SLUG or tail==FREE_SLUG:free_found.append(p)
    a.require(not free_found,
              "Free seller product may already exist; refuse new creation and reconcile manually")
    a.require(len(found)==1,
              "Exactly one existing paid seller product required; never create another")
    product_id=str(found[0].get("id") or "")
    a.require(product_id and str(found[0].get("name") or "").strip()==paid["Product Name"],
              "Found paid product identity does not exactly match source")
    data=a.gumroad_cli(["products","view",product_id]).get("product") or {}
    a.require(str(data.get("custom_permalink") or "")==PAID_SLUG,"Existing paid slug mismatch")
    a.require(str(data.get("name") or "").strip()==paid["Product Name"],"Draft title mismatch")
    a.require(data.get("published") is False,"Paid already public or publication status uncertain")
    attached=data.get("files") or data.get("rich_content_files") or []
    covers=data.get("covers") or data.get("cover_images") or []
    a.require(len(attached)>=2 and bool(covers),
              "Paid draft missing 27-page PDF/Excel or cover")
    a.require(bool(data.get("custom_summary")),
              "Paid draft listing summary was not saved")
    receipt("EXISTING_PAID_DRAFT_CONFIRMED",paid_id=product_id,paid_attached_count=len(attached),
            paid_cover_count=len(covers))
    return product_id

def preflight_pins(store):
    wanted=("Q-48","Q-49","Q-50")
    rows=store.get_rows("Publishing Queue")
    matched={}
    for ident in wanted:
        found=[row for row in rows if row.get("Queue ID")==ident]
        a.require(len(found)==1,"Missing/duplicate Pinterest queue ID "+ident)
        row=found[0]
        a.require(row.get("Status")=="PREPARED_PENDING_LIVE_URL" and not row.get("Batch ID"),
                  "Previously scheduled Pin cannot be recreated: "+ident)
        a.verify_qa_report(store,row,ident)
        expected=FREE_URL if ident in ("Q-48","Q-49") else PAID_URL
        a.require(row.get("Destination URL")==expected,"Pin destination mismatch")
        ident_img=a.google_file_id(row.get("Pin Image Drive Link"))
        a.validate_image(store.get_bytes(ident_img,"image/png"))
        matched[ident]=row
    # Inspect Buffer queue before seller writes so a capacity blocker cannot
    # strand both new Gumroad products without a chance for promoted Pins.
    buffer=a.BufferClient()
    a.require(buffer.scheduled()<=7,"Buffer Free capacity insufficient for three Pins")
    a.require("Budgeting Printables & Cash Stuffing" in buffer.boards(),
              "Expected Pinterest board not in connected Buffer channel")
    daily={}
    for row in rows:
        if row.get("Status") in ("SCHEDULED_BUFFER","PUBLISHED"):
            day=row.get("Scheduled Date") or ""
            daily[day]=daily.get(day,0)+1
    for ident in wanted:
        due=previous.choose_due(ident)
        a.require(due>datetime.now(timezone.utc)+timedelta(minutes=6),
                  "Pin due time is no longer in the future")
        day=due.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        a.require(daily.get(day,0)<3,"Daily Pinterest cap reached for "+day)
        daily[day]=daily.get(day,0)+1
    receipt("PINTEREST_PRECHECK_OK",pin_ids=list(wanted),buffer_slots_required=3)

def create_only_free(store,row,item):
    # A narrower known-good CLI call than the prior experimental batch:
    # exactly one FREE PDF + one cover; no unsupported preview flags.
    a.require(PAID_URL in item["description"],"Free listing must link to real paid product")
    args=["products","create","--draft","--name",row["Product Name"],
          "--price",row["Price USD"],"--currency","usd","--type","digital",
          "--custom-permalink",row["Unique Slug"],"--description",item["description"],
          "--custom-summary",item["summary"],"--pay-what-you-want",
          "--file",str(item["pdf"]),"--cover-image",str(item["cover"])]
    receipt("FREE_CREATE_ATTEMPTED_DO_NOT_RETRY")
    data=a.gumroad_cli(args)
    obj=data.get("product") or {}
    ident=str(obj.get("id") or "")
    a.require(ident,"Free Gumroad creation returned no ID; inspect seller before another attempt")
    receipt("FREE_DRAFT_ID_CONFIRMED",free_id=ident)
    view=a.gumroad_cli(["products","view",ident]).get("product") or {}
    files=view.get("files") or view.get("rich_content_files") or []
    covers=view.get("covers") or view.get("cover_images") or []
    a.require(view.get("published") is False and view.get("name")==row["Product Name"],
              "New free draft identity uncertain")
    a.require(files and covers,"Free PDF or cover not attached")
    store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
                 "Gumroad Live URL":f"https://gumroad.com/products/{ident}/edit",
                 "Last Updated UTC":a.make_timestamp()})
    return ident

def run():
    a.require(os.getenv("KINDGRID_PAIR002_OWNER_RESUME")=="true",
              "This is a single owner-authorized reconciliation job")
    a.require(os.getenv("LIVE_MODE")=="true" and os.getenv("PAIRED_RELEASE_ENABLED")=="true",
              "Paired publishing control not enabled")
    store=a.GoogleStore()
    paid,free=get_rows(store)
    preflight_pins(store)
    with tempfile.TemporaryDirectory(prefix="pair002-resume-") as d:
        assets=pair.prepare_pair(store,paid,free,Path(d))
        a.require(assets["PAID"]["pages"]==27 and assets["FREE"]["pages"]==5,
                  "Product page count differs from approved materials")
        ident=check_existing_draft(paid)
        receipt("EXISTING_DRAFT_PUBLISH_ATTEMPTED_NO_RETRY")
        store.patch("Gumroad Upload Queue",paid,{"Upload Status":"UPLOADING",
                   "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2"})
        try:
            a.gumroad_cli(["products","publish",ident])
            after=a.gumroad_cli(["products","view",ident]).get("product") or {}
            a.require(after.get("published") is True,
                      "Paid publication was not verified after one attempt")
            a.verify_public_product_url(PAID_URL,PAID_SLUG)
            store.patch("Gumroad Upload Queue",paid,{"Upload Status":"PUBLISHED",
                    "Gumroad Live URL":PAID_URL,"Last Error":"",
                    "Last Updated UTC":a.make_timestamp()})
            receipt("PAID_PUBLIC_URL_VERIFIED",paid_public=PAID_URL)
            print("KGS008_PAID_PUBLISHED_VERIFIED: "+PAID_URL)
        except Exception as e:
            store.patch("Gumroad Upload Queue",paid,{"Upload Status":"REVIEW",
                  "Last Error":(type(e).__name__+": "+str(e))[:400]})
            receipt("PAID_REVIEW_NO_RETRY",error_type=type(e).__name__)
            raise

        store.patch("Gumroad Upload Queue",free,{"Upload Status":"UPLOADING",
                 "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2"})
        try:
            fid=create_only_free(store,free,assets["FREE"])
            receipt("FREE_EXISTING_DRAFT_PUBLISH_ATTEMPTED_NO_RETRY")
            a.gumroad_cli(["products","publish",fid])
            data=a.gumroad_cli(["products","view",fid]).get("product") or {}
            a.require(data.get("published") is True,"Free publication not confirmed")
            a.verify_public_product_url(FREE_URL,FREE_SLUG)
            store.patch("Gumroad Upload Queue",free,{"Upload Status":"PUBLISHED",
                  "Gumroad Live URL":FREE_URL,"Last Error":"",
                  "Last Updated UTC":a.make_timestamp()})
            receipt("PAID_AND_FREE_PUBLIC_VERIFIED",paid_public=PAID_URL,free_public=FREE_URL)
            print("KGS009_FREE_PUBLISHED_VERIFIED: "+FREE_URL)
        except Exception as e:
            store.patch("Gumroad Upload Queue",free,{"Upload Status":"REVIEW",
                  "Last Error":(type(e).__name__+": "+str(e))[:400]})
            receipt("FREE_REVIEW_NO_RETRY",error_type=type(e).__name__)
            raise

    # All three Pins are submitted ONLY if both storefront products are public.
    previous.publish_pins(store,{PAID:PAID_URL,FREE:FREE_URL})
    final={r["Queue ID"]:r.get("Status") for r in store.get_rows("Publishing Queue")
           if r.get("Queue ID") in ("Q-48","Q-49","Q-50")}
    receipt("PAIR_GUMROAD_LIVE_BUFFER_PINS_SUBMITTED",pinterest=final)
    a.require(len(final)==3 and all(v=="SCHEDULED_BUFFER" for v in final.values()),
              "Partial Pinterest batch; do not rerun, inspect Buffer and dashboard")
    print("PAIR002_ALL_THREE_PINS_BUFFER_CONFIRMED")
    return 0

if __name__=="__main__":
    try:sys.exit(run())
    except Exception as e:
        print("PAIR002_SAFE_RESUME_FAILED: "+type(e).__name__+": "+str(e)[:350])
        print("DO_NOT_REPEAT_THIS_ONE_TIME_WORKFLOW")
        sys.exit(1)
