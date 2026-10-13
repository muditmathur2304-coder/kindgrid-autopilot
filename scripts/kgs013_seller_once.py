"""Single-use CollectFlow KGS-013 seller upload. Never retries ambiguous writes."""
import io,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
from src import autopilot as a
from src.paired_release import published_today_count
ID="KGS-013";SLUG="collectflow-invoice-followup-control"
def run():
 s=a.GoogleStore()
 rows=s.get_rows("Gumroad Upload Queue")
 matches=[r for r in rows if r.get("Product ID")==ID]
 a.require(len(matches)==1,"Duplicate or absent queue entry")
 r=matches[0]
 a.require(r.get("Upload Status")=="RELEASE_APPROVED_ONCE","Not release-approved")
 a.require(r.get("Unique Slug")==SLUG and r.get("Price USD")=="15.00","Identity/price mismatch")
 a.verify_qa_report(s,r,ID)
 a.require(published_today_count(rows)<7,"7-listing daily cap reached")
 x=s.get_bytes("1K4M6EOZg4nRMxSb92M1cpyhMq9_5bnFG","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
 p=s.get_bytes("1KT-bPipbs7aMsSs_VArU0SsxeZmg0UJx","application/pdf")
 c=s.get_bytes("1Q6JmUAojyUJR0GUIVpRREJ0tQdf7V7Dx","image/png")
 a.require(a.validate_pdf(p)==5,"Wrong PDF")
 a.validate_image(c)
 with ZipFile(io.BytesIO(x)) as z:
  media=[n for n in z.namelist() if n.startswith("xl/media/")]
  a.require("xl/workbook.xml" in z.namelist() and len(media)>=2 and all(z.getinfo(n).file_size>100000 for n in media),"Broken workbook images")
 for prod in a.gumroad_cli(["products","list","--all"]).get("products",[]):
  a.require(prod.get("custom_permalink")!=SLUG and str(prod.get("short_url") or "").rstrip("/").split("/")[-1]!=SLUG,"Existing seller slug; no duplicate")
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);(d/"CollectFlow.xlsx").write_bytes(x);(d/"Guide.pdf").write_bytes(p);(d/"Cover.png").write_bytes(c)
  desc=("An editable eight-tab Excel invoice follow-up system for freelancers and service businesses. Track thirty invoices and partial payments, prioritize unpaid clients, see next contact dates, and view eight weeks of contractual amounts due. Includes cash scenarios, four professional follow-up scripts and a five-page illustrated guide. The real XLSX contains two original non-empty embedded 3D-style infographics. This file never sends messages, connects bank accounts, collects payments or guarantees a payment. Sample invoices are fictional and must be replaced. No macros or subscription are required.")
  s.patch("Gumroad Upload Queue",r,{"Upload Status":"RELEASING_ONCE","Last Attempt UTC":a.make_timestamp(),"Attempt Count":str(int(r.get("Attempt Count") or 0)+1)})
  try:
   ans=a.gumroad_cli(["products","create","--draft","--name",r["Product Name"],"--price","15.00","--currency","usd","--type","digital","--custom-permalink",SLUG,"--description",desc,"--custom-summary","A clear daily invoice follow-up queue plus an eight-week cash-due map.","--file",str(d/"CollectFlow.xlsx"),"--file",str(d/"Guide.pdf"),"--cover-image",str(d/"Cover.png"),"--thumbnail",str(d/"Cover.png")])
   pid=str((ans.get("product") or {}).get("id") or "")
   a.require(bool(pid),"Draft may exist; no ID returned")
   item=a.gumroad_cli(["products","view",pid]).get("product") or {}
   a.require(item.get("published") is False and item.get("name")==r["Product Name"],"Wrong draft readback")
   a.require(len(item.get("files") or item.get("rich_content_files") or [])>=2 and bool(item.get("covers") or item.get("cover_images")),"Files/cover not verified")
   s.patch("Gumroad Upload Queue",r,{"Upload Status":"DRAFT_VERIFIED","Gumroad Live URL":"https://gumroad.com/products/"+pid+"/edit"})
   a.gumroad_cli(["products","publish",pid])
   item=a.gumroad_cli(["products","view",pid]).get("product") or {}
   a.require(item.get("published") is True,"Publication unverified")
   url="https://kindgridstudio.gumroad.com/l/"+SLUG
   a.verify_public_product_url(url,SLUG)
   s.patch("Gumroad Upload Queue",r,{"Upload Status":"PUBLISHED","Gumroad Live URL":url,"Last Error":"","Last Updated UTC":a.make_timestamp()})
   print("VERIFIED_PUBLIC",url)
  except Exception as exc:
   s.patch("Gumroad Upload Queue",r,{"Upload Status":"REVIEW","Last Error":(type(exc).__name__+": "+str(exc))[:380]})
   print("SELLER_REVIEW no retry: "+type(exc).__name__,file=sys.stderr)
   return 1
 return 0
if __name__=="__main__":sys.exit(run())
