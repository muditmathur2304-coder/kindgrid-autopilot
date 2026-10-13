"""Owner-authorised ONE KGS-010 release; fail closed and do not change normal pair policy."""
import io, os, re, tempfile, zipfile
from pathlib import Path
from PIL import Image
from src import autopilot as a

CODE="KGS-010"
SLUG="bakeslot-order-capacity-studio"
NAME="BakeSlot Studio — Custom Order, Quote & Capacity System for Bakers"

def one(store,sheet,col,val):
    r=[r for r in store.get_rows(sheet) if r.get(col)==val]
    a.require(len(r)==1,"Expected exactly one "+val)
    return r[0]

def portrait(blob):
    with Image.open(io.BytesIO(blob)) as im:
        im=im.convert("RGB")
        im.thumbnail((1000,1470),Image.Resampling.LANCZOS)
        back=Image.new("RGB",(1000,1500),(250,247,241))
        back.paste(im,((1000-im.width)//2,(1500-im.height)//2))
        out=io.BytesIO()
        back.save(out,"PNG",optimize=True)
    b=out.getvalue()
    a.validate_image(b)
    return b

def run():
    a.require(a.enabled("LIVE_MODE") and a.enabled("BAKESLOT_OWNER_RELEASE"),"Owner release disabled")
    s=a.GoogleStore()
    r=one(s,"Gumroad Upload Queue","Product ID",CODE)
    if r.get("Upload Status")=="PUBLISHED":
        a.require(r.get("Gumroad Live URL")=="https://kindgridstudio.gumroad.com/l/"+SLUG,"Wrong existing seller URL")
        a.verify_public_product_url(r["Gumroad Live URL"],SLUG)
        print("ALREADY_PUBLISHED_VERIFIED "+r["Gumroad Live URL"])
        return
    a.require(r.get("Upload Status")=="OWNER_ONE_TIME_READY","Unsafe release status")
    a.require(r.get("Product Name")==NAME and r.get("Price USD")=="19.00" and r.get("Unique Slug")==SLUG,"Wrong product or price")
    a.verify_qa_report(s,r,CODE)
    pd=s.get_bytes(a.google_file_id(r["PDF Drive Link"]),"application/pdf")
    xl=s.get_bytes(a.google_file_id(r["Bonus File Drive Link"]),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    a.require(a.validate_pdf(pd)==6,"Invalid user guide")
    with zipfile.ZipFile(io.BytesIO(xl)) as z:
        a.require(z.testzip() is None,"Broken Excel workbook")
        sheets=[n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n)]
        f=sum(z.read(n).count(b"<x:f") for n in sheets)
        media=[n for n in z.infolist() if n.filename.startswith("xl/media/")]
        a.require(len(sheets)==10 and f>=790 and len(media)>=8 and all(n.file_size>20000 for n in media),"Missing formulas or visuals")
    txt=s.get_doc_text(a.google_file_id(r["Listing Copy Drive Link"],"document"))
    summary=txt.split("SUMMARY_START",1)[1].split("SUMMARY_END",1)[0].strip()
    description=txt.split("DESCRIPTION_START",1)[1].split("DESCRIPTION_END",1)[0].strip()
    a.require(60<=len(summary)<=400 and 650<=len(description)<=10000,"Listing text invalid")
    cover=portrait(s.get_bytes(a.google_file_id(r["Cover Drive Link"]),"image/png"))
    prev=[portrait(s.get_bytes(a.google_file_id(r[key]),"image/png")) for key in ("Gallery Image 1 Drive Link","Gallery Image 2 Drive Link")]
    # Check existing Gumroad products BEFORE making a draft, never clone an existing slug.
    current=a.gumroad_cli(["products","list","--all"]).get("products",[])
    for x in current:
        a.require(SLUG not in (str(x.get("custom_permalink") or ""),str(x.get("short_url") or "").rstrip("/").split("/")[-1]),"Seller product slug already exists: reconcile, do not duplicate")
    with tempfile.TemporaryDirectory(prefix="kgs010-") as d:
        base=Path(d)
        files=[]
        for fname,buf in (("BakeSlot_Studio_Premium_Integrated.xlsx",xl),("BakeSlot_Professional_Guide.pdf",pd),("cover.png",cover),("preview_profit.png",prev[0]),("preview_decision.png",prev[1])):
            p=base/fname;p.write_bytes(buf);files.append(str(p))
        s.patch("Gumroad Upload Queue",r,{"Upload Status":"ONE_TIME_UPLOADING","Attempt Count":str(int(r.get("Attempt Count") or 0)+1),"Last Attempt UTC":a.make_timestamp()})
        try:
            args=["products","create","--draft","--name",NAME,"--price","19.00","--currency","usd","--type","digital","--custom-permalink",SLUG,"--description",description,"--custom-summary",summary,
                  "--file",files[0],"--file",files[1],"--cover-image",files[2],"--thumbnail",files[2],"--preview-image",files[3],"--preview-image",files[4]]
            response=a.gumroad_cli(args)
            pid=str((response.get("product") or {}).get("id") or "")
            a.require(pid,"Gumroad returned no product ID: no retry")
            s.patch("Gumroad Upload Queue",r,{"Gumroad Live URL":"https://gumroad.com/products/"+pid+"/edit"})
            st=a.gumroad_cli(["products","view",pid]).get("product") or {}
            attached=st.get("files") or st.get("rich_content_files") or []
            covers=st.get("covers") or st.get("cover_images") or []
            a.require(st.get("published") is False and st.get("name")==NAME and len(attached)>=2 and len(covers)>=1,"Draft attachments not confirmed; refuse publish")
            a.gumroad_cli(["products","publish",pid])
            st=a.gumroad_cli(["products","view",pid]).get("product") or {}
            a.require(st.get("published") is True,"Gumroad publish unconfirmed")
            url="https://kindgridstudio.gumroad.com/l/"+SLUG
            a.verify_public_product_url(url,SLUG)
            s.patch("Gumroad Upload Queue",r,{"Upload Status":"PUBLISHED","Gumroad Live URL":url,"Last Error":"","Last Updated UTC":a.make_timestamp()})
            print("GUMROAD_PUBLISHED_VERIFIED "+url)
        except Exception as e:
            s.patch("Gumroad Upload Queue",r,{"Upload Status":"REVIEW","Last Error":(type(e).__name__+": "+str(e))[:420]})
            raise

if __name__=="__main__":
    run()
