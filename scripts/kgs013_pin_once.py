"""Owner-approved one-time Pinterest handoff for the VERIFIED KGS-013 seller page."""
import sys
from datetime import datetime,timezone
from src import autopilot as a
def run():
 s=a.GoogleStore()
 p=[x for x in s.get_rows("Gumroad Upload Queue") if x.get("Product ID")=="KGS-013"]
 q=[x for x in s.get_rows("Publishing Queue") if x.get("Queue ID")=="Q-58"]
 a.require(len(p)==1 and len(q)==1,"Queue identity missing/duplicated")
 a.require(p[0].get("Upload Status")=="PUBLISHED","Seller still unpublished; no Pinterest")
 a.require(p[0].get("Gumroad Live URL")=="https://kindgridstudio.gumroad.com/l/collectflow-invoice-followup-control","Unexpected public URL")
 a.verify_public_product_url(p[0]["Gumroad Live URL"])
 r=q[0]
 a.require(r.get("Status")=="AWAITING_GUMROAD","Pin state already changed, reconcile")
 a.require(not r.get("Batch ID") and not r.get("Actual Pinterest Pin URL"),"Pin provider already attempted")
 a.verify_qa_report(s,r,"Q-58")
 s.patch("Publishing Queue",r,{"Status":"READY","Last Error":""})
 r["Status"]="READY"
 for msg in a.process_pins(s,[r],datetime.now(timezone.utc)):
  print(msg)
 return 0
if __name__=="__main__":sys.exit(run())
