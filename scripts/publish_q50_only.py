"""One-time owner-authorized Q-50 Pin for VERIFIED LIVE KGS008; no freebie link."""
import os,sys,json
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
sys.path.insert(0,'.')
from src import autopilot as a
PIN="Q-50"
TARGET="https://kindgridstudio.gumroad.com/l/market-day-margin-guide"
BOARD="Budgeting Printables & Cash Stuffing"
def main():
 a.require(os.getenv("Q50_ONE_TIME_OWNER_APPROVAL")=="true","Owner authorization required")
 store=a.GoogleStore()
 matching=[r for r in store.get_rows("Publishing Queue") if r.get("Queue ID")==PIN]
 a.require(len(matching)==1,"Missing or duplicate Q50")
 row=matching[0]
 a.require(row.get("Status")=="PREPARED_PENDING_LIVE_URL" and not row.get("Batch ID"),
   "Q50 was already submitted or status changed; do not repeat")
 a.verify_qa_report(store,row,PIN)
 a.require(row.get("Destination URL")==TARGET,"Wrong destination")
 a.verify_public_product_url(TARGET,"market-day-margin-guide")
 product=[r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-008"]
 a.require(len(product)==1 and product[0].get("Upload Status")=="PUBLISHED" and product[0].get("Gumroad Live URL")==TARGET,"Paid listing not confirmed")
 raw=store.get_bytes(a.google_file_id(row["Pin Image Drive Link"]),"image/png")
 a.validate_image(raw)
 client=a.BufferClient()
 boards=client.boards()
 a.require(BOARD in boards,"Pinterest board not connected")
 a.require(client.scheduled()<10,"Buffer free queue capacity exceeded")
 due=datetime.now(timezone.utc)+timedelta(minutes=20)
 image=a.cloudinary_upload(raw,"q50-kgs008-owner-paid-pin-once")
 store.patch("Publishing Queue",row,{"Status":"SCHEDULING","Last Error":"Owner one-time Q50, cannot safely retry", "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
 print("Q50_BUFFER_CREATE_ATTEMPTED_DO_NOT_RETRY")
 post=client.create({"id":PIN,"title":row["Pin Title"],"description":row["Pin Description"],"board":BOARD,"destination":TARGET,"due":due},image,boards[BOARD])
 ident=str(post.get("id") or "")
 url=str((post.get("metadata") or {}).get("url") or "")
 if not ident or url!=TARGET:
  store.patch("Publishing Queue",row,{"Status":"LINK_REVIEW","Batch ID":ident,"Last Error":"Buffer response uncertain; inspect platform before attempting again"})
  raise ValueError("Post may have been submitted but link cannot be independently verified")
 nt=due.astimezone(ZoneInfo("America/New_York"));ist=due.astimezone(ZoneInfo("Asia/Kolkata"))
 store.patch("Publishing Queue",row,{"Status":"SCHEDULED_BUFFER","Batch ID":ident,
 "Scheduled Date":nt.strftime("%Y-%m-%d"),
 "US Scheduled Time":nt.strftime("%H:%M %Z")+" / "+ist.strftime("%H:%M IST"),
 "Last Error":"","Last Attempt UTC":a.make_timestamp()})
 print("Q50_BUFFER_SCHEDULED_VERIFIED "+json.dumps({"post_id":ident,"due_utc":due.isoformat(),"destination":TARGET}))
 return 0
if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  print("Q50_OWNER_PIN_STOP_NO_RETRY "+type(e).__name__+": "+str(e)[:250]);sys.exit(1)
