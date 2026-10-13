"""Owner-authorized one-time FREE KGS-011 release. Never duplicates a Gumroad draft."""
import io, re, tempfile, zipfile
from pathlib import Path
from PIL import Image
from src import autopilot as a

CODE="KGS-011"
SLUG="bakeslot-free-one-order-quote-check"
NAME="BakeSlot FREE — One-Order Quote Check"
PAID="https://kindgridstudio.gumroad.com/l/bakeslot-order-capacity-studio"

def exactly(store,sheet,col,value):
    arr=[x for x in store.get_rows(sheet) if x.get(col)==value]
    a.require(len(arr)==1,f"Expected unique {value}")
    return arr[0]

def main():
    a.require(a.enabled("LIVE_MODE") and a.enabled("BAKESLOT_FREE_OWNER_RELEASE"),"Freebie release not authorized or paused")
    store=a.GoogleStore()
    paid=exactly(store,"Gumroad Upload Queue","Product ID","KGS-010")
    a.require(paid.get("Upload Status")=="PUBLISHED" and paid.get("Gumroad Live URL")==PAID,"Paid product must already be public")
    a.verify_public_product_url(PAID,"bakeslot-order-capacity-studio")
    row=exactly(store,"Gumroad Upload Queue","Product ID",CODE)
    url="https://kindgridstudio.gumroad.com/l/"+SLUG
    if row.get("Upload Status")=="PUBLISHED":
        a.require(row.get("Gumroad Live URL")==url,"Public free URL mismatch")
        a.verify_public_product_url(url,SLUG)
        print("FREEBIE_ALREADY_PUBLISHED "+url);return
    a.require(row.get("Upload Status")=="OWNER_FREE_ONE_TIME_READY","Freebie not uniquely cleared for new release")
    a.require(row.get("Product Name")==NAME and row.get("Price USD")=="0.00" and row.get("Unique Slug")==SLUG,"Freebie identity/price mismatch")
    a.verify_qa_report(store,row,CODE)
    pdf=store.get_bytes(a.google_file_id(row["PDF Drive Link"]),"application/pdf")
    xlsx=store.get_bytes(a.google_file_id(row["Bonus File Drive Link"]),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    cover=store.get_bytes(a.google_file_id(row["Cover Drive Link"]),"image/png")
    a.require(a.validate_pdf(pdf)==4,"Expected 4-page full quality guide")
    a.validate_image(cover)
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        a.require(z.testzip() is None,"Bad XLSX checksum")
        tabs=[n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n)]
        formulas=sum(z.read(n).count(b"<x:f") for n in tabs)
        media=[x for x in z.infolist() if x.filename.startswith("xl/media/")]
        a.require(len(tabs)==3 and formulas>=15 and len(media)>=3 and all(x.file_size>20000 for x in media),"Broken interactive workbook or zero-byte infographics")
    text=store.get_doc_text(a.google_file_id(row["Listing Copy Drive Link"],"document"))
    a.require("SUMMARY_START" in text and "SUMMARY_END" in text and "DESCRIPTION_START" in text and "DESCRIPTION_END" in text,"Listing markers missing")
    summary=text.split("SUMMARY_START",1)[1].split("SUMMARY_END",1)[0].strip()
    description=text.split("DESCRIPTION_START",1)[1].split("DESCRIPTION_END",1)[0].strip()
    a.require(75<=len(summary)<=400 and 650<=len(description)<=10000,"Listing copy incomplete")
    a.require(PAID in description,"Missing factual optional full product link")
    listing=a.gumroad_cli(["products","list","--all"]).get("products",[])
    for p in listing:
        existing=str(p.get("custom_permalink") or "")
        tail=str(p.get("short_url") or "").rstrip("/").split("/")[-1]
        a.require(SLUG not in (existing,tail),"Slug already in seller account; reconcile before creating")
    with tempfile.TemporaryDirectory(prefix="kgs011-free-") as tmp:
        d=Path(tmp)
        paths=[]
        for filename,data in [("BakeSlot_FREE_Quote_Check.xlsx",xlsx),("BakeSlot_FREE_Illustrated_Guide.pdf",pdf),("cover.png",cover)]:
            fp=d/filename; fp.write_bytes(data); paths.append(str(fp))
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"ONE_TIME_UPLOADING","Attempt Count":str(int(row.get("Attempt Count") or 0)+1),"Last Attempt UTC":a.make_timestamp()})
        try:
            cmd=["products","create","--draft","--name",NAME,"--price","0","--currency","usd","--type","digital","--custom-permalink",SLUG,"--description",description,"--custom-summary",summary,"--pay-what-you-want","--file",paths[0],"--file",paths[1],"--cover-image",paths[2],"--thumbnail",paths[2]]
            response=a.gumroad_cli(cmd)
            product=response.get("product") or {}
            ident=str(product.get("id") or "")
            a.require(bool(ident),"Seller created unknown draft? Do NOT retry")
            store.patch("Gumroad Upload Queue",row,{"Gumroad Live URL":"https://gumroad.com/products/"+ident+"/edit"})
            read=a.gumroad_cli(["products","view",ident]).get("product") or {}
            files=read.get("files") or read.get("rich_content_files") or []
            covers=read.get("covers") or read.get("cover_images") or []
            a.require(read.get("published") is False and read.get("name")==NAME and len(files)==2 and bool(covers),"Actual FREE XLSX/PDF + cover not independently confirmed")
            names=" ".join(str(x.get("name") or x.get("display_name") or x.get("filename") or x.get("file_name") or "") for x in files if isinstance(x,dict)).lower()
            if names.strip():a.require(".xlsx" in names and ".pdf" in names,"Actual buyer files mismatched")
            store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED","Last Updated UTC":a.make_timestamp()})
            a.gumroad_cli(["products","publish",ident])
            reread=a.gumroad_cli(["products","view",ident]).get("product") or {}
            a.require(reread.get("published") is True,"Seller publish uncertain")
            store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":url,"Last Updated UTC":a.make_timestamp()})
            a.verify_public_product_url(url,SLUG)
            store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED","Gumroad Live URL":url,"Last Error":"","Last Updated UTC":a.make_timestamp()})
            print("FREE_GUMROAD_PUBLISHED_VERIFIED "+url)
        except Exception as e:
            latest=exactly(store,"Gumroad Upload Queue","Product ID",CODE)
            if latest.get("Upload Status") in ("ONE_TIME_UPLOADING","DRAFT_VERIFIED"):
                store.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW","Last Error":(type(e).__name__+": "+str(e))[:420]})
            elif latest.get("Upload Status")=="PUBLISHED_CHECK_URL":
                store.patch("Gumroad Upload Queue",latest,{"Last Error":"Gumroad published, public HTTP check pending. Never republish."})
            raise

if __name__=="__main__":
    main()
