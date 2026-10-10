"""Exactly one next-day owner-authorized recovery after Gumroad 10-products/day cap.
Never bypass seller limits; never create a duplicate. Only 2026-10-11 UTC.
"""
import os,sys,tempfile,json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
sys.path.insert(0,'.')
from src import autopilot as a
from src import paired_release as pair
from scripts import complete_pair002_free_pins as existing
PAID="https://kindgridstudio.gumroad.com/l/market-day-margin-guide"
FREE="https://kindgridstudio.gumroad.com/l/before-you-book-booth-free"
BOARD="Budgeting Printables & Cash Stuffing"

def later_pins(store):
 rows=store.get_rows("Publishing Queue")
 need=("Q-48","Q-49")
 selected={}
 for rid in need:
  found=[r for r in rows if r.get("Queue ID")==rid]
  a.require(len(found)==1,f"{rid} missing or duplicated")
  row=found[0]
  a.require(row.get("Status")=="PREPARED_PENDING_LIVE_URL" and not row.get("Batch ID"),
            f"{rid} is already submitted or changed")
  a.verify_qa_report(store,row,rid)
  a.require(row.get("Destination URL")==FREE,"Freebie destination changed")
  selected[rid]=row
 a.verify_public_product_url(FREE,"before-you-book-booth-free")
 client=a.BufferClient()
 boards=client.boards()
 a.require(BOARD in boards,"Expected Buffer Pinterest board unavailable")
 a.require(client.scheduled()<=8,"Buffer Free queue lacks room for 2 Pins")
 ny=ZoneInfo("America/New_York")
 target_days={"Q-48":11,"Q-49":12}
 for rid in need:
  due=datetime(2026,10,target_days[rid],8,30,tzinfo=ny).astimezone(timezone.utc)
  a.require(due>datetime.now(timezone.utc),"Pin slot already passed")
  row=selected[rid]
  raw=store.get_bytes(a.google_file_id(row["Pin Image Drive Link"]),"image/png")
  a.validate_image(raw)
  destination=FREE+"?"+urlencode({"utm_source":"pinterest","utm_medium":"organic",
    "utm_campaign":"kg_pair_002","utm_content":rid.lower().replace("-","")})
  a.validate_destination(destination)
  image_url=a.cloudinary_upload(raw,rid.lower()+"-kgpair002-after-cap")
  store.patch("Publishing Queue",row,{"Status":"SCHEDULING",
    "Last Attempt UTC":a.make_timestamp(),
    "Last Error":"Single next-day recovery; do not resubmit without reconciliation"})
  print(rid+"_BUFFER_SUBMISSION_ATTEMPTED_NO_BLIND_RETRY")
  post=client.create({"id":rid,"title":row["Pin Title"],"description":row["Pin Description"],
     "board":BOARD,"destination":destination,"due":due},image_url,boards[BOARD])
  ident=str(post.get("id") or "")
  returned=str((post.get("metadata") or {}).get("url") or "")
  if not ident or returned!=destination:
   store.patch("Publishing Queue",row,{"Status":"LINK_REVIEW",
     "Batch ID":ident,"Last Error":"Buffer response unknown or destination mismatch; don't retry"})
   raise RuntimeError("Buffer created potentially uncertain "+rid)
  ist=due.astimezone(ZoneInfo("Asia/Kolkata"))
  store.patch("Publishing Queue",row,{"Status":"SCHEDULED_BUFFER","Batch ID":ident,
    "Scheduled Date":due.astimezone(ny).strftime("%Y-%m-%d"),
    "US Scheduled Time":due.astimezone(ny).strftime("%H:%M %Z")+" / "+ist.strftime("%H:%M IST"),
    "Destination URL":destination,"Last Error":"","Last Attempt UTC":a.make_timestamp()})
  print(rid+"_SCHEDULED "+json.dumps({"post_id":ident,"due":due.isoformat()}))

def main():
 a.require(os.getenv("KINDGRID_PAIR002_DELAYED_APPROVAL")=="true","Owner recovery approval missing")
 if datetime.now(timezone.utc).strftime("%Y-%m-%d")!="2026-10-11":
  print("SKIP: scheduled only for 2026-10-11 UTC; no seller or Buffer writes")
  return 0
 store=a.GoogleStore()
 paid,free=existing.load_rows(store)
 existing.verify_paid()
 # Q-50 already handled in separate successful owner-authorized Buffer job.
 q50=[r for r in store.get_rows("Publishing Queue") if r.get("Queue ID")=="Q-50"]
 a.require(len(q50)==1 and q50[0].get("Status") in ("SCHEDULED_BUFFER","PUBLISHED")
   and bool(q50[0].get("Batch ID")),"Paid Q50 must already be scheduled once")
 a.require(all(r.get("Status")=="PREPARED_PENDING_LIVE_URL" and not r.get("Batch ID")
    for r in store.get_rows("Publishing Queue") if r.get("Queue ID") in ("Q-48","Q-49")),
    "Freebie Pins may have been submitted already")
 existing.inspect_no_free()
 with tempfile.TemporaryDirectory(prefix="pair002-cap-reset-") as d:
  package=pair.prepare_pair(store,paid,free,Path(d))
  a.require(package["PAID"]["pages"]==27 and package["FREE"]["pages"]==5,
      "Source packages changed from corrected QA")
  try: existing.make_free(store,free,package["FREE"])
  except Exception as e:
   store.patch("Gumroad Upload Queue",free,{"Upload Status":"REVIEW",
      "Last Error":(type(e).__name__+": "+str(e))[:390]})
   print("FREEBIE_REVIEW_NO_AUTO_RETRY "+type(e).__name__+": "+str(e)[:170])
   raise
 later_pins(store)
 print("KGPAIR002_COMPLETE_GUMROAD_PAID_FREE_LIVE_AND_Q48_Q49_BUFFER_SCHEDULED")
 return 0

if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  print("NEXT_DAY_KGPAIR002_HALT_NO_REPEAT "+type(e).__name__+": "+str(e)[:240])
  sys.exit(1)
