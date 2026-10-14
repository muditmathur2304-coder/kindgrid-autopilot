"""KGS014 one-time FREE invoice kit and Q59 immediate Pinterest posting; never blindly rerun."""
import io,os,sys,hashlib,json,time,tempfile
from pathlib import Path
from src import autopilot as a
ID="KGS-014";QID="Q-59";SLUG="unpaid-invoice-reset-free"
NAME="The Unpaid Invoice Reset | FREE 6-Page Follow-Up Kit"
URL="https://kindgridstudio.gumroad.com/l/"+SLUG
PAID="https://kindgridstudio.gumroad.com/l/collectflow-invoice-followup-control"
BOARD="Budgeting Printables & Cash Stuffing"
FILES={"pdf":("19anHEo5ZqeVyOu-Z6rjgRAdKgR3LKLVu","application/pdf","7042acdee3d6f6015a54f822bd028011edc8caa26e82fed2b0c5601be2b99572"),
       "cover":("1l5puOyLXnStH8RHhCMC8bejG_O44-Tjy","image/png","503bb5a873ad25c009c3d20ef2701abce841ec1aea381f54b57cfebe87f68872"),
       "pin":("1savtk8pg4ImNKI9dnorMUsCc-qWSpKwo","image/png","613ee34c5c0f63407905d2d45e8c4efc5c9005eb794dd3cca26125b4acf3249d")}
OUT=Path("kindgrid-kgs014-release-proof")
def note(stage,**kwargs):
 OUT.mkdir(exist_ok=True,parents=True);f=OUT/"receipt.json"
 try: old=json.loads(f.read_text()) if f.exists() else {}
 except Exception:old={}
 old.update(kwargs);old.update({"stage":stage,"timestamp":a.make_timestamp()})
 f.write_text(json.dumps(old,indent=2))
 print("KGS014_STATUS "+stage)
def one(s,t,k,v):
 matched=[r for r in s.get_rows(t) if r.get(k)==v]
 a.require(len(matched)==1,"Not exactly one "+v+" in "+t)
 return matched[0]
def run():
 a.require(a.enabled("KINDGRID_OWNER_RELEASE_KGS014") and a.enabled("LIVE_MODE"),"One-time release disabled")
 s=a.GoogleStore()
 paid=one(s,"Gumroad Upload Queue","Product ID","KGS-013")
 a.require(paid.get("Upload Status")=="PUBLISHED" and paid.get("Gumroad Live URL")==PAID,"Existing paid upgrade not published")
 a.verify_public_product_url(PAID,"collectflow-invoice-followup-control")
 row=one(s,"Gumroad Upload Queue","Product ID",ID)
 pinrow=one(s,"Publishing Queue","Queue ID",QID)
 a.require(row.get("Upload Status")=="OWNER_FREE_ONE_TIME_READY" and row.get("Unique Slug")==SLUG
           and row.get("Product Name")==NAME and row.get("Price USD")=="0.00","Already attempted or wrong Gumroad product")
 a.require(pinrow.get("Status")=="PRODUCT_RELEASE_PENDING" and not pinrow.get("Batch ID")
           and not pinrow.get("Actual Pinterest Pin URL"),"Already attempted Pin")
 a.require(pinrow.get("Destination URL","").startswith(URL+"?utm_source=pinterest"),"Pin link mismatch")
 blobs={}
 for kind,(fid,mime,expected_sha) in FILES.items():
  data=s.get_bytes(fid,mime)
  a.require(hashlib.sha256(data).hexdigest()==expected_sha,kind+" changed after independent visual QA")
  blobs[kind]=data
 a.require(a.validate_pdf(blobs["pdf"])==6,"Expected actual six-page PDF")
 a.validate_image(blobs["cover"]);a.validate_image(blobs["pin"])
 content=s.get_doc_text("1qlLrrO-NOokyYpcC65PvfqDES60-zhNjlc1dk9xtPWU")
 summary,description=a.get_listing_copy(content)
 a.require(PAID in description and len(description)>700,"Customer freebie copy missing paid upgrade")
 seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
 for item in seller:
  a.require(item.get("custom_permalink")!=SLUG and
            str(item.get("short_url") or "").rstrip("/").split("/")[-1]!=SLUG,
            "Seller already has KGS014; refuse duplicate")
 b=a.BufferClient();boards=b.boards()
 a.require(BOARD in boards and b.scheduled()<10,"Buffer board unavailable or free queue full")
 a.require(len(pinrow.get("Pin Title",""))<=100 and len(pinrow.get("Pin Description",""))<500,
           "Invalid Pinterest title/description length")
 note("PREFLIGHT_DONE_SELLER_AND_BUFFER_READ_ONLY")
 with tempfile.TemporaryDirectory(prefix="kgs014-") as td:
  pdf=Path(td)/"KGS014_Unpaid_Invoice_Reset_6page.pdf"
  cover=Path(td)/"KGS014_Gumroad_Cover.png"
  pdf.write_bytes(blobs["pdf"]);cover.write_bytes(blobs["cover"])
  s.patch("Gumroad Upload Queue",row,{"Upload Status":"ONE_TIME_UPLOADING",
    "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
  note("GUMROAD_CREATE_ATTEMPTED_DO_NOT_RERUN")
  try:
   result=a.gumroad_cli(["products","create","--draft","--name",NAME,
    "--price","0","--currency","usd","--type","digital","--custom-permalink",SLUG,
    "--pay-what-you-want","--description",description,"--custom-summary",summary,
    "--file",str(pdf),"--cover-image",str(cover),"--thumbnail",str(cover)])
   obj=result.get("product") or {};pid=str(obj.get("id") or "")
   a.require(bool(pid),"Seller creation may have succeeded with no ID: do not retry")
   note("GUMROAD_DRAFT_ID_CONFIRMED",gumroad_id=pid)
   s.patch("Gumroad Upload Queue",row,{"Gumroad Live URL":"https://gumroad.com/products/"+pid+"/edit"})
   view=a.gumroad_cli(["products","view",pid]).get("product") or {}
   attached=view.get("files") or view.get("rich_content_files") or []
   covers=view.get("covers") or view.get("cover_images") or []
   a.require(view.get("published") is False and view.get("name")==NAME and
             view.get("custom_permalink")==SLUG and bool(covers),"Gumroad draft/cover mismatch")
   a.require(any(int(z.get("size") or -1)==len(blobs["pdf"]) for z in attached),
             "The delivered customer PDF does not match verified source size")
   s.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED"})
   note("GUMROAD_DRAFT_CUSTOMER_PDF_AND_COVER_VERIFIED")
   a.gumroad_cli(["products","publish",pid])
   live=a.gumroad_cli(["products","view",pid]).get("product") or {}
   a.require(live.get("published") is True,"Gumroad publication uncertain")
   s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":URL})
   a.verify_public_product_url(URL,SLUG)
   s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED","Gumroad Live URL":URL,
       "Last Error":"","Last Updated UTC":a.make_timestamp()})
   note("GUMROAD_PUBLIC_VERIFIED",product_url=URL)
   print("KGS014_GUMROAD_LIVE "+URL)
  except Exception as err:
   cur=one(s,"Gumroad Upload Queue","Product ID",ID)
   if cur.get("Upload Status") in ("ONE_TIME_UPLOADING","DRAFT_VERIFIED"):
    s.patch("Gumroad Upload Queue",cur,{"Upload Status":"REVIEW","Last Error":str(err)[:370]})
   note("GUMROAD_UNCERTAIN_DO_NOT_RETRY",error_type=type(err).__name__)
   raise
 try:
  s.patch("Publishing Queue",pinrow,{"Status":"ONE_TIME_POSTING",
       "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
  image_url=a.cloudinary_upload(blobs["pin"],"kgs014-q59-new-20261014")
  note("CLOUDINARY_IMAGE_VERIFIED",image_url=image_url)
  query='''mutation P($input:CreatePostInput!){createPost(input:$input){
    ... on PostActionSuccess{post{id status externalLink}}
    ... on MutationError{message}}}'''
  body={"channelId":b.channel_id,"text":pinrow["Pin Description"],
    "schedulingType":"automatic","mode":"shareNow","aiAssisted":True,
    "assets":[{"image":{"url":image_url}}],
    "metadata":{"pinterest":{"boardServiceId":boards[BOARD],
      "title":pinrow["Pin Title"],"url":pinrow["Destination URL"]}}}
  note("BUFFER_CREATE_ATTEMPTED_DO_NOT_RERUN")
  response=b.graphql(query,{"input":body}).get("createPost") or {}
  obj=response.get("post") or {};bid=str(obj.get("id") or "")
  a.require(bool(bid),"Buffer create returned no post ID; review provider before retry")
  s.patch("Publishing Queue",pinrow,{"Status":"SENT_PENDING_URL","Batch ID":bid,"Last Error":""})
  note("BUFFER_POST_ID_CONFIRMED",buffer_post_id=bid)
  link=str(obj.get("externalLink") or "")
  for n in range(5):
   if "pinterest.com/pin/" in link or "pin.it/" in link:break
   if n:time.sleep(5)
   state=b.get_post(bid);link=str(state.get("externalLink") or "")
  if "pinterest.com/pin/" in link or "pin.it/" in link:
   s.patch("Publishing Queue",pinrow,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
   note("PINTEREST_PUBLIC_URL_CONFIRMED",pin_url=link)
   print("KGS014_PINTEREST_LIVE "+link)
  else: print("KGS014_PIN_SUBMITTED_BUFFER_ID "+bid+" (Pinterest permalink pending)")
 except Exception as err:
  cur=one(s,"Publishing Queue","Queue ID",QID)
  if cur.get("Status")=="ONE_TIME_POSTING":
   s.patch("Publishing Queue",cur,{"Status":"REVIEW","Last Error":str(err)[:370]})
  note("PINTEREST_UNCERTAIN_DO_NOT_RETRY",error_type=type(err).__name__)
  raise
 return 0
if __name__=="__main__":
 try:sys.exit(run())
 except Exception as error:
  print("ONE_TIME_RELEASE_HALTED "+type(error).__name__+": "+str(error)[:260])
  print("STOP_NO_BLIND_RETRY")
  sys.exit(1)
