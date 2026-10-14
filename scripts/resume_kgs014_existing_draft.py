"""Resume exactly one reconciled KGS014 draft; then share Q59 only if FREE is public."""
import io,os,sys,hashlib,json,time
from pathlib import Path
from src import autopilot as a
from scripts import one_time_kgs014_free_and_pin as config
PID="Tw0_kGRzHBG1a5ILgepIYQ=="
OUT=Path("kindgrid-kgs014-resume-proof")
def proof(step,**items):
 OUT.mkdir(exist_ok=True,parents=True);p=OUT/"receipt.json"
 try: saved=json.loads(p.read_text()) if p.exists() else {}
 except Exception:saved={}
 saved.update(items);saved.update({"step":step,"utc":a.make_timestamp()})
 p.write_text(json.dumps(saved,indent=2))
 print("KGS014_RESUME "+step)
def one(s,tab,key,val):
 rows=[r for r in s.get_rows(tab) if r.get(key)==val]
 a.require(len(rows)==1,"Duplicate/missing "+val)
 return rows[0]
def main():
 a.require(a.enabled("LIVE_MODE") and a.enabled("KINDGRID_OWNER_RESUME_KGS014"),
           "No owner permission to resume the old draft")
 s=a.GoogleStore()
 row=one(s,"Gumroad Upload Queue","Product ID","KGS-014")
 q=one(s,"Publishing Queue","Queue ID","Q-59")
 a.require(row.get("Upload Status")=="REVIEW","Do not repeat a previously completed or attempted publication")
 a.require(row.get("Unique Slug")==config.SLUG and row.get("Product Name")==config.NAME,
           "Product metadata changed since read-only seller reconciliation")
 a.require(q.get("Status")=="PRODUCT_RELEASE_PENDING" and not q.get("Batch ID") and
           not q.get("Actual Pinterest Pin URL"),"Pin was already submitted")
 a.require(q.get("Destination URL","").startswith(config.URL+"?utm_source=pinterest"),
           "Wrong Pinterest destination")
 paid=one(s,"Gumroad Upload Queue","Product ID","KGS-013")
 a.require(paid.get("Upload Status")=="PUBLISHED" and paid.get("Gumroad Live URL")==config.PAID,
           "Companion paid item not verified public")
 a.verify_public_product_url(config.PAID,"collectflow-invoice-followup-control")
 data={}
 for k,(id,mime,sha) in config.FILES.items():
  raw=s.get_bytes(id,mime)
  a.require(hashlib.sha256(raw).hexdigest()==sha,"QA-approved asset changed: "+k)
  data[k]=raw
 a.require(a.validate_pdf(data["pdf"])==6,"Not original six-page PDF")
 a.validate_image(data["cover"]);a.validate_image(data["pin"])
 desc_doc=s.get_doc_text("1qlLrrO-NOokyYpcC65PvfqDES60-zhNjlc1dk9xtPWU")
 summary,description=a.get_listing_copy(desc_doc)
 a.require(config.PAID in description,"Mandatory existing paid upgrade missing")
 b=a.BufferClient();boards=b.boards()
 a.require(config.BOARD in boards and b.scheduled()<10,"Buffer channel / free capacity unavailable")
 seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
 found=[]
 for p in seller:
  if str(p.get("custom_permalink") or "")==config.SLUG or str(p.get("short_url") or "").rstrip("/").endswith("/"+config.SLUG):
   found.append(str(p.get("id") or ""))
 a.require(found==[PID],"Seller draft identity changed; no creation/retry")
 view=a.gumroad_cli(["products","view",PID]).get("product") or {}
 a.require(view.get("published") is False and view.get("name")==config.NAME and
           view.get("custom_permalink")==config.SLUG,"Expected exact unpublished KGS014 draft")
 files=view.get("files") or []
 a.require(len(files)==1 and int(files[0].get("size") or -1)==len(data["pdf"]),
           "Gumroad customer PDF does not match original byte count")
 a.require(bool(view.get("covers") or view.get("cover_images")),"Gumroad cover missing")
 rich=a.gumroad_cli(["products","content","get",PID])
 if isinstance(rich,list):
  embedded=[str(n.get("attrs",{}).get("id") or "") for part in rich
   for n in (part.get("description") or {}).get("content") or [] if n.get("type")=="fileEmbed"]
  a.require(embedded==[str(files[0]["id"])],"Customer-delivery attachment not confirmed")
 # New seller draft metadata was produced by the failed CLI create; finish and
 # verify listing copy in-place if original create completed before response error.
 seller_copy=str(view.get("description") or "")
 if config.PAID not in seller_copy:
  proof("EXISTING_DRAFT_DESCRIPTION_REPAIR_ATTEMPTED_NO_RETRY")
  a.gumroad_cli(["products","update",PID,"--description",description,
                "--custom-summary",summary])
  view=a.gumroad_cli(["products","view",PID]).get("product") or {}
  a.require(config.PAID in str(view.get("description") or ""),
            "Paid upgrade not confirmed in seller description; stop")
 proof("EXISTING_CORRECT_DRAFT_AND_DELIVERY_VERIFIED",seller_id=PID)
 s.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
    "Gumroad Live URL":"https://gumroad.com/products/"+PID+"/edit",
    "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2"})
 proof("GUMROAD_PUBLISH_ATTEMPTED_ONCE")
 try:
  a.gumroad_cli(["products","publish",PID])
  latest=a.gumroad_cli(["products","view",PID]).get("product") or {}
  a.require(latest.get("published") is True,"Seller publication response uncertain")
  s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL",
    "Gumroad Live URL":config.URL})
  a.verify_public_product_url(config.URL,config.SLUG)
  s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
      "Gumroad Live URL":config.URL,"Last Error":"","Last Updated UTC":a.make_timestamp()})
  proof("GUMROAD_PUBLIC_VERIFIED",free_url=config.URL)
  print("KGS014_GUMROAD_PUBLISHED "+config.URL)
 except Exception as e:
  latest=one(s,"Gumroad Upload Queue","Product ID","KGS-014")
  if latest.get("Upload Status")=="DRAFT_VERIFIED":
   s.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW","Last Error":str(e)[:350]})
  proof("GUMROAD_PUBLICATION_NEEDS_RECONCILIATION",error_type=type(e).__name__)
  raise
 # Post only after verified PUBLIC Gumroad page. Link is UTM-tagged.
 try:
  s.patch("Publishing Queue",q,{"Status":"ONE_TIME_POSTING",
     "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
  image_url=a.cloudinary_upload(data["pin"],"kgs014-q59-final-20261014")
  proof("PINTEREST_IMAGE_HOSTED",image=image_url)
  query='''mutation P($input:CreatePostInput!){createPost(input:$input){
   ... on PostActionSuccess{post{id status externalLink}}
   ... on MutationError{message}}}'''
  body={"channelId":b.channel_id,"text":q["Pin Description"],
   "schedulingType":"automatic","mode":"shareNow","aiAssisted":True,
   "assets":[{"image":{"url":image_url}}],
   "metadata":{"pinterest":{"boardServiceId":boards[config.BOARD],
        "title":q["Pin Title"],"url":q["Destination URL"]}}}
  proof("BUFFER_CREATE_ATTEMPTED_NO_RETRY")
  result=b.graphql(query,{"input":body}).get("createPost") or {}
  post=result.get("post") or {};pid=str(post.get("id") or "")
  a.require(bool(pid),"Buffer mutation no ID: inspect before another attempt")
  s.patch("Publishing Queue",q,{"Status":"SENT_PENDING_URL","Batch ID":pid,"Last Error":""})
  proof("BUFFER_PIN_SUBMITTED_CONFIRMED",buffer_id=pid)
  link=str(post.get("externalLink") or "")
  for i in range(5):
   if "pinterest.com/pin/" in link or "pin.it/" in link:break
   if i:time.sleep(5)
   link=str(b.get_post(pid).get("externalLink") or "")
  if "pinterest.com/pin/" in link or "pin.it/" in link:
   s.patch("Publishing Queue",q,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
   proof("PINTEREST_LIVE",pin_url=link)
   print("Q59_PINTEREST_PUBLISHED "+link)
  else:
   print("Q59_BUFFER_SENT_PENDING_PUBLISHER_PERMALINK "+pid)
  return 0
 except Exception as e:
  current=one(s,"Publishing Queue","Queue ID","Q-59")
  if current.get("Status")=="ONE_TIME_POSTING":
   s.patch("Publishing Queue",current,{"Status":"REVIEW","Last Error":str(e)[:350]})
  proof("PIN_UPLOAD_NEEDS_RECONCILIATION",error_type=type(e).__name__)
  raise
if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  print("KGS014_SAFE_RESUME_STOP "+type(e).__name__+": "+str(e)[:310])
  print("DO_NOT_REPEAT_UNTIL_SELLER_AND_BUFFER_ARE_RECONCILED")
  sys.exit(1)
