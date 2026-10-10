"""One-time removal of two obsolete embeds from a KNOWN unpublished KGS008 draft.

Does NOT upload any files or publish anything. Stops rather than retrying.
"""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,'.')
from src import autopilot as a

PID="dbXiy8eZ1uxF33itkI4p4Q=="
OLD=["H2segmakuganqGb2ngzIAg==","zUQbX-eIOUJfvSO3cI5ALw=="]
NEW=["8rsz1Qlgu_bjkJTf5H-L0Q==","kbAWz_w8r7GJcyvHb7PFPw=="]
EXPECTED_SIZES={OLD[0]:132558,OLD[1]:8854,NEW[0]:133503,NEW[1]:9506}
OUT=Path("kindgrid-kgs008-swap-proof")
def record(stage,**info):
 OUT.mkdir(exist_ok=True,parents=True)
 p=OUT/"receipt.json"
 data=json.loads(p.read_text()) if p.exists() else {}
 data.update(info);data["stage"]=stage;data["utc"]=a.make_timestamp()
 p.write_text(json.dumps(data,indent=2))
 print("KGS008_SWAP "+stage)
def embed_ids(pages):
 a.require(isinstance(pages,list) and len(pages)==1,"Unknown rich content page count")
 d=pages[0].get("description") or {}
 a.require(d.get("type")=="doc","Unknown Gumroad rich content schema")
 return [str(n.get("attrs",{}).get("id") or "") for n in d.get("content") or []
         if n.get("type")=="fileEmbed"]
def run():
 store=a.GoogleStore()
 rows=[r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-008"]
 a.require(len(rows)==1 and rows[0].get("Upload Status")=="REVIEW",
           "Only the historical held product may be modified")
 a.verify_qa_report(store,rows[0],"KGS-008")
 obj=a.gumroad_cli(["products","view",PID]).get("product") or {}
 a.require(obj.get("published") is False and
           obj.get("custom_permalink")=="market-day-margin-guide","Seller product identity/state changed")
 seller_files=obj.get("files") or []
 actual={str(f.get("id")):int(f.get("size") or -1) for f in seller_files}
 a.require(actual==EXPECTED_SIZES,"Seller file ids or bytes do not match known preflight")
 content=a.gumroad_cli(["products","content","get",PID])
 a.require(embed_ids(content)==OLD+NEW,
           "Known old and new embeds are not in expected order; do not edit")
 rec=content[0]
 blocks=rec["description"]["content"]
 rec["description"]["content"]=[node for node in blocks
     if node.get("type")!="fileEmbed" or
        str(node.get("attrs",{}).get("id")) not in OLD]
 a.require(embed_ids(content)==NEW,"Exact corrected file embed payload mismatch")
 with tempfile.TemporaryDirectory(prefix="k008-no-uploads-") as tmp:
  p=Path(tmp)/"approved_content.json";p.write_text(json.dumps(content))
  dry=a.gumroad_cli(["products","content","set",PID,str(p),"--dry-run"])
  record("VALIDATED_CONTENT_SWAP_DRY_RUN",draft_id=PID,
         obsolete_ids=OLD,corrected_ids=NEW,
         dry_run_json_keys=list(dry.keys()) if isinstance(dry,dict) else None)
  record("LIVE_STRUCTURE_EDIT_ATTEMPTED_NO_RETRY")
  a.gumroad_cli(["products","content","set",PID,str(p),"--yes"])
  c=a.gumroad_cli(["products","content","get",PID])
  a.require(embed_ids(c)==NEW,"Actual customer download embeds still show an old file")
  after=a.gumroad_cli(["products","view",PID]).get("product") or {}
  a.require(after.get("published") is False,"Product unexpectedly published")
  # The actual Content is the customer-delivery surface; product.files may
  # list historic unattached file assets. Record them for the final check.
  file_ids=[str(x.get("id")) for x in after.get("files") or []]
  record("CORRECTED_CUSTOMER_CONTENT_VERIFIED_UNPUBLISHED",
         current_embed_ids=NEW,all_product_file_ids=file_ids)
  print("SUCCESS_KGS008_CONTENT_ONLY_CORRECTED_FILES_NO_PUBLICATION")
  return 0

if __name__=="__main__":
 try:sys.exit(run())
 except Exception as e:
  record("HALTED_REVIEW_NO_RETRY",error_type=type(e).__name__,
         error=str(e)[:260])
  print("KGS008_STRUCTURAL_EDIT_HALTED "+type(e).__name__+" "+str(e)[:300])
  sys.exit(1)
