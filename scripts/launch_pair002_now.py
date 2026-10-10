"""ONE-TIME owner-authorized KG-PAIR-002 PAID+FREE launch and three Pinterest Pins.

Do not re-run after any seller or Buffer mutation; inspect queues to reconcile.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from src import autopilot as a
from src import paired_release as pair

PAIR="KG-PAIR-002"
PAID="KGS-008"
FREE="KGS-009"
IDS=("Q-48","Q-49","Q-50")
BOARD="Budgeting Printables & Cash Stuffing"
NY=ZoneInfo("America/New_York")
IST=ZoneInfo("Asia/Kolkata")

def rows_named(store, name):
    return store.get_rows(name)

def validate_pair_identity(approved):
    matching=[(x,y) for x,y in approved if x.get("Pair ID")==PAIR]
    a.require(len(matching)==1,"Expected exactly one owner-approved paid+free pair")
    paid,free=matching[0]
    a.require(paid.get("Product ID")==PAID and free.get("Product ID")==FREE,
              "Pair IDs do not match approved products")
    return paid,free

def verify_gumroad_pair(store):
    rows=rows_named(store,"Gumroad Upload Queue")
    paid=[r for r in rows if r.get("Product ID")==PAID]
    free=[r for r in rows if r.get("Product ID")==FREE]
    a.require(len(paid)==1 and len(free)==1,"Missing or duplicate product records")
    expected={
       PAID:"https://kindgridstudio.gumroad.com/l/market-day-margin-guide",
       FREE:"https://kindgridstudio.gumroad.com/l/before-you-book-booth-free"}
    for row in (paid[0],free[0]):
        ident=row["Product ID"]
        a.require(row.get("Upload Status")=="PUBLISHED",
                  f"{ident} Gumroad publication not fully verified")
        a.require(row.get("Gumroad Live URL")==expected[ident],
                  f"{ident} public URL mismatch")
        a.verify_public_product_url(expected[ident],row["Unique Slug"])
    return expected

def choose_due(qid):
    now=datetime.now(timezone.utc)
    if qid=="Q-48":
        return now+timedelta(minutes=15)
    if qid=="Q-49":
        return datetime(2026,10,11,8,30,tzinfo=NY).astimezone(timezone.utc)
    if qid=="Q-50":
        return datetime(2026,10,12,8,30,tzinfo=NY).astimezone(timezone.utc)
    raise ValueError("Unexpected Pin ID")

def record_written(store,row,due,buffer_id,destination):
    ny=due.astimezone(NY)
    ist=due.astimezone(IST)
    store.patch("Publishing Queue",row,{
      "Status":"SCHEDULED_BUFFER",
      "Scheduled Date":ny.strftime("%Y-%m-%d"),
      "US Scheduled Time":ny.strftime("%H:%M %Z")+" / "+ist.strftime("%H:%M IST"),
      "Destination URL":destination,
      "Batch ID":buffer_id,
      "Last Error":"",
      "Last Attempt UTC":a.make_timestamp()})

def publish_pins(store,public_urls):
    all_rows=rows_named(store,"Publishing Queue")
    qrows={}
    for rid in IDS:
        chosen=[r for r in all_rows if r.get("Queue ID")==rid]
        a.require(len(chosen)==1,f"{rid} must exist exactly once")
        qrows[rid]=chosen[0]
        a.require(chosen[0].get("Status")=="PREPARED_PENDING_LIVE_URL" and
                  not chosen[0].get("Batch ID"),
                  f"{rid} may already have been submitted; do not duplicate")
    existing={}
    for row in all_rows:
        if row.get("Status") in ("SCHEDULED_BUFFER","PUBLISHED"):
            existing[row.get("Scheduled Date","")]=existing.get(row.get("Scheduled Date",""),0)+1
    due={}
    for rid in IDS:
        d=choose_due(rid)
        a.require(d>datetime.now(timezone.utc)+timedelta(minutes=6),
                  f"{rid} intended schedule no longer in the future")
        day=d.astimezone(NY).strftime("%Y-%m-%d")
        a.require(existing.get(day,0)<3,
                  f"{rid}: the date has already reached the 3-Pin daily limit")
        existing[day]=existing.get(day,0)+1
        due[rid]=d
    client=a.BufferClient()
    boards=client.boards()
    a.require(BOARD in boards,"Connected Pinterest account lacks approved budgeting board")
    capacity=client.scheduled()
    a.require(capacity+3<=10,"Buffer Free queue has insufficient slots for three Pins")
    for rid in IDS:
        row=qrows[rid]
        a.verify_qa_report(store,row,rid)
        image=a.google_file_id(row["Pin Image Drive Link"])
        blob=store.get_bytes(image,"image/png")
        a.validate_image(blob)
        target=public_urls[FREE if rid in ("Q-48","Q-49") else PAID]
        a.require(row.get("Destination URL")==target,
                  "Creator destination must match the actual newly published product")
        campaign=urlencode({"utm_source":"pinterest","utm_medium":"organic",
                             "utm_campaign":"kg_pair_002","utm_content":rid.lower().replace("-","")})
        dest=target+"?"+campaign
        a.validate_destination(dest)
        a.verify_public_product_url(dest)
        title=row.get("Pin Title","").strip()
        description=row.get("Pin Description","").strip()
        a.require(12<=len(title)<=100 and 80<=len(description)<=500,
                  f"{rid} title or description is too short/long")
        # Source image is publicly hosted only AFTER validating its own actual
        # content and the authenticated destination.
        image_url=a.cloudinary_upload(blob,rid.lower()+"-pair002")
        store.patch("Publishing Queue",row,{
            "Status":"SCHEDULING","Last Error":"Owner one-time pair launch; do not resubmit",
            "Last Attempt UTC":a.make_timestamp(),
            "Attempt Count":str(int(row.get("Attempt Count") or 0)+1)})
        print(f"{rid}: BUFFER_CREATE_ATTEMPTED; NEVER BLINDLY REPEAT")
        payload={"id":rid,"title":title,"description":description,"board":BOARD,
                 "destination":dest,"due":due[rid]}
        post=client.create(payload,image_url,boards[BOARD])
        ident=str(post.get("id") or "")
        returned=str((post.get("metadata") or {}).get("url") or "")
        if not ident or returned!=dest:
            store.patch("Publishing Queue",row,{
               "Status":"LINK_REVIEW","Batch ID":ident,
               "Last Error":"Buffer post uncertain or destination mismatched; reconcile before retry"})
            raise RuntimeError(f"{rid} Buffer may have created a post without a verified matching destination")
        record_written(store,row,due[rid],ident,dest)
        print(f"{rid}: BUFFER_SCHEDULED_VERIFIED | id={ident} | due={due[rid].isoformat()}")

def main():
    a.require(os.getenv("KINDGRID_OWNER_APPROVED_PAIR002")=="true",
              "This one-time launch requires explicit owner approval")
    a.require(a.enabled("LIVE_MODE") and a.enabled("PAIRED_RELEASE_ENABLED"),
              "The paired publishing safety controls are not enabled")
    store=a.GoogleStore()
    before=rows_named(store,"Gumroad Upload Queue")
    paid,free=validate_pair_identity(pair.select_ready_pairs(before))
    print("PAIR_PREFLIGHT_OK: one complete owner-authorized PAID+FREE pair")
    # This call reserves both rows before any seller mutation, checks every
    # actual file and report, and creates/verifies PAID then FREE, never retrying
    # uncertain seller operations.
    statuses=pair.launch_pair_once(store,paid,free)
    for line in statuses:print("PAIR_RESULT: "+line)
    public=verify_gumroad_pair(store)
    print("PAID_AND_FREE_GUMROAD_PUBLIC_VERIFIED")
    publish_pins(store,public)
    print("PAIR002_RELEASE_COMPLETE: Both Gumroad products public, three Pins scheduled in Buffer")
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("PAIR002_STOP_NO_RETRY: "+type(exc).__name__+": "+str(exc)[:260],file=sys.stderr)
        print("CHECK_GUMROAD_AND_BUFFER_BEFORE_ANY_SECOND_ATTEMPT",file=sys.stderr)
        sys.exit(1)
