"""Owner-authorized final KG-PAIR-002 FREE product upload and 3 unique Pinterest Pins.

The PAID product was already published and verified. The failed FREE create attempt
was conclusively reconciled: no seller product with free slug exists.
This is the first seller write after that read-only check.
"""
import io,json,os,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,'.')
from src import autopilot as a
from src import paired_release as pair
from scripts import resume_pair002_existing as candidate
from scripts import launch_pair002_now as prior

OUT=Path("kindgrid-free-pins-finish-proof")
PAID_URL="https://kindgridstudio.gumroad.com/l/market-day-margin-guide"
FREE_URL="https://kindgridstudio.gumroad.com/l/before-you-book-booth-free"
FREE_SLUG="before-you-book-booth-free"
PAID_SELLER_ID="dbXiy8eZ1uxF33itkI4p4Q=="
CORRECT_PAID_EMBEDS=["8rsz1Qlgu_bjkJTf5H-L0Q==","kbAWz_w8r7GJcyvHb7PFPw=="]

def receipt(step,**info):
 OUT.mkdir(exist_ok=True,parents=True);path=OUT/"proof.json"
 state=json.loads(path.read_text()) if path.exists() else {}
 state.update(info);state["phase"]=step;state["utc"]=a.make_timestamp()
 path.write_text(json.dumps(state,indent=2))
 print("PAIR002_FINAL "+step)

def verify_paid():
 o=a.gumroad_cli(["products","view",PAID_SELLER_ID]).get("product") or {}
 a.require(o.get("published") is True and o.get("custom_permalink")=="market-day-margin-guide",
           "The paid product must be publicly published with original seller ID")
 content=a.gumroad_cli(["products","content","get",PAID_SELLER_ID])
 ids=[str(b.get("attrs",{}).get("id")) for page in content for b in (page.get("description") or {}).get("content") or [] if b.get("type")=="fileEmbed"]
 a.require(ids==CORRECT_PAID_EMBEDS,
           "Paid content does not exclusively use two corrected customer files")
 a.verify_public_product_url(PAID_URL,"market-day-margin-guide")

def load_rows(store):
 rows=store.get_rows("Gumroad Upload Queue")
 pa=[r for r in rows if r.get("Product ID")=="KGS-008"]
 fr=[r for r in rows if r.get("Product ID")=="KGS-009"]
 a.require(len(pa)==1 and len(fr)==1,"Missing or duplicate paired row")
 paid,free=pa[0],fr[0]
 a.require(paid.get("Upload Status")=="PUBLISHED" and
          paid.get("Gumroad Live URL")==PAID_URL,
          "Paid queue must confirm verified public offer")
 a.require(free.get("Upload Status")=="REVIEW" and not free.get("Gumroad Live URL"),
          "Free queue changed since no-seller-draft reconciliation")
 a.require(paid.get("Pair ID")=="KG-PAIR-002" and free.get("Pair ID")=="KG-PAIR-002",
          "Unexpected campaign pairing")
 for row in (paid,free):
  a.require(row.get("QA Verified (YES/NO)")=="YES" and row.get("QA Outcome")=="PASS",
            "Source QA blocked")
  a.verify_qa_report(store,row,row["Product ID"])
 return paid,free

def inspect_no_free():
 products=a.gumroad_cli(["products","list","--all"]).get("products",[])
 matching=[p for p in products if str(p.get("custom_permalink") or "")==FREE_SLUG
           or str(p.get("short_url") or "").rstrip("/").endswith("/"+FREE_SLUG)]
 a.require(not matching,"Free seller product/draft exists; reconcile before another create")
 receipt("NO_EXISTING_FREE_SELLER_PRODUCT_VERIFIED")

def make_free(store,row,source):
 with tempfile.TemporaryDirectory(prefix="kgpair002-free-") as td:
  folder=Path(td)
  pdf=source["pdf"].read_bytes()
  cover=source["cover"].read_bytes()
  a.require(a.validate_pdf(pdf)==5,"Incorrect corrected FREE page count")
  a.validate_image(cover)
  a.require(PAID_URL in source["description"],"Free page lacks genuine PAID link")
  receipt("CREATE_FREE_METADATA_DRAFT_ATTEMPTED_DO_NOT_RETRY")
  store.patch("Gumroad Upload Queue",row,{"Upload Status":"UPLOADING","Last Attempt UTC":a.make_timestamp(),"Attempt Count":"3"})
  created=a.gumroad_cli(["products","create","--draft","--name",row["Product Name"],
      "--price","0.00","--currency","usd","--type","digital",
      "--custom-permalink",FREE_SLUG,"--pay-what-you-want",
      "--description",source["description"],
      "--custom-summary",source["summary"]])
  raw=created.get("product") or {}
  pid=str(raw.get("id") or "")
  a.require(pid,"Free metadata product may exist without returned ID; do not retry")
  receipt("FREE_METADATA_DRAFT_CREATED",gumroad_id=pid)
  o=a.gumroad_cli(["products","view",pid]).get("product") or {}
  a.require(o.get("published") is False and o.get("custom_permalink")==FREE_SLUG and
            o.get("name")==row["Product Name"],"Free metadata draft identity mismatch")
  store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
          "Gumroad Live URL":f"https://gumroad.com/products/{pid}/edit","Last Updated UTC":a.make_timestamp()})

  pdfpath=folder/"Before_You_Book_Booth_Corrected_5p.pdf";pdfpath.write_bytes(pdf)
  receipt("ATTACH_CORRECTED_FREE_PDF_ATTEMPTED_NO_RETRY")
  a.gumroad_cli(["products","update",pid,"--file",str(pdfpath)])
  o=a.gumroad_cli(["products","view",pid]).get("product") or {}
  files=o.get("files") or []
  matches=[x for x in files if int(x.get("size") or -1)==len(pdf)]
  a.require(len(matches)==1 and len(files)==1,"Cannot verify exact single corrected FREE PDF attachment")
  c=a.gumroad_cli(["products","content","get",pid])
  embedded=[str(b.get("attrs",{}).get("id")) for p in c for b in (p.get("description") or {}).get("content") or [] if b.get("type")=="fileEmbed"]
  a.require(embedded==[str(matches[0]["id"])],"Customer download does not match corrected FREE PDF")
  receipt("CORRECTED_FREE_PDF_ATTACHED",free_file_id=embedded[0])

  coverpath=folder/"KGS009_Gumroad_Cover.png";coverpath.write_bytes(cover)
  receipt("COVER_UPLOAD_ATTEMPTED_NO_RETRY")
  a.gumroad_cli(["products","covers","add",pid,"--image",str(coverpath)])
  o=a.gumroad_cli(["products","view",pid]).get("product") or {}
  a.require(bool(o.get("covers") or o.get("cover_images")),"Free listing cover missing")
  a.require(o.get("published") is False,"Free draft unexpectedly published")
  receipt("FREE_DRAFT_PDF_AND_COVER_VERIFIED",cover_count=len(o.get("covers") or []))
  receipt("FREE_PUBLICATION_ATTEMPTED_NO_RETRY")
  a.gumroad_cli(["products","publish",pid])
  o=a.gumroad_cli(["products","view",pid]).get("product") or {}
  a.require(o.get("published") is True,"Free publication not verified after one attempt")
  a.verify_public_product_url(FREE_URL,FREE_SLUG)
  store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
        "Gumroad Live URL":FREE_URL,"Last Error":"","Last Updated UTC":a.make_timestamp()})
  receipt("BOTH_PAID_AND_FREE_GUMROAD_LIVE",free_public=FREE_URL,paid_public=PAID_URL)
  print("KGS009_FREE_PUBLIC_URL_VERIFIED "+FREE_URL)

def main():
 a.require(os.getenv("KINDGRID_FINISH_KGPAIR002")=="true","Missing one-time owner authorization")
 store=a.GoogleStore()
 paid,free=load_rows(store)
 verify_paid()
 candidate.preflight_pins(store)
 inspect_no_free()
 with tempfile.TemporaryDirectory(prefix="kgs002-all-") as tmp:
  sources=pair.prepare_pair(store,paid,free,Path(tmp))
  receipt("SOURCE_QA_ALL_PAGES_AND_FILES_VERIFIED")
  try:
   make_free(store,free,sources["FREE"])
  except Exception as e:
   store.patch("Gumroad Upload Queue",free,{"Upload Status":"REVIEW",
         "Last Error":(type(e).__name__+": "+str(e))[:410]})
   receipt("FREE_REVIEW_NO_RETRY",error_type=type(e).__name__,error=str(e)[:200])
   raise
 # Both storefront links are now real; Pins may be uploaded exactly once.
 prior.publish_pins(store,{"KGS-008":PAID_URL,"KGS-009":FREE_URL})
 states={r["Queue ID"]:r.get("Status") for r in store.get_rows("Publishing Queue")
         if r.get("Queue ID") in ("Q-48","Q-49","Q-50")}
 receipt("BOTH_GUMROAD_PUBLISHED_THREE_PINS_BUFFER_SUBMITTED",pins=states)
 a.require(len(states)==3 and all(x=="SCHEDULED_BUFFER" for x in states.values()),
           "One or more Pinterest submissions need manual reconciliation; DO NOT retry automatically")
 print("SUCCESS_KGPAIR002_FULL_RELEASE "+json.dumps(states))
 return 0

if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  receipt("HALTED_REVIEW_NO_BLIND_RETRY",error_type=type(e).__name__,error=str(e)[:250])
  print("PAIR002_FREE_PIN_FINISH_HALTED "+type(e).__name__+": "+str(e)[:260])
  sys.exit(1)
