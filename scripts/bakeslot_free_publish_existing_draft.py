"""Safely publish reconciled KGS-011 EXISTING draft; never create a new listing."""
from src import autopilot as a
PRODUCT="KGS-011"
SLUG="bakeslot-free-one-order-quote-check"
ID="jHdVFZOAxlAYfPpw3YRYgA=="
NAME="BakeSlot FREE — One-Order Quote Check"

def run():
    a.require(a.enabled("LIVE_MODE") and a.enabled("BAKESLOT_FREE_OWNER_RELEASE"),"Owner live control disabled")
    store=a.GoogleStore()
    rows=[x for x in store.get_rows("Gumroad Upload Queue") if x.get("Product ID")==PRODUCT]
    a.require(len(rows)==1,"Unknown owner-approved item")
    row=rows[0]
    public="https://kindgridstudio.gumroad.com/l/"+SLUG
    if row.get("Upload Status")=="PUBLISHED":
        a.require(row.get("Gumroad Live URL")==public,"PUBLISHED link mismatch")
        a.verify_public_product_url(public,SLUG)
        print("GUMROAD_ALREADY_LIVE "+public)
        return
    a.require(row.get("Upload Status")=="REVIEW" and row.get("Gumroad Live URL")==("https://gumroad.com/products/"+ID+"/edit"),"Different draft/status, refuse action")
    a.require(row.get("Unique Slug")==SLUG and row.get("Product Name")==NAME and row.get("Price USD")=="0.00","Queue identity/price changed")
    a.verify_qa_report(store,row,PRODUCT)
    # Read the exact existing product rather than attempting to create a second one.
    product=a.gumroad_cli(["products","view",ID]).get("product") or {}
    a.require(product.get("published") is False,"Existing seller state not draft")
    a.require(product.get("name")==NAME,"Seller product identity mismatch")
    permalink=str(product.get("custom_permalink") or "")
    tail=str(product.get("short_url") or "").rstrip("/").split("/")[-1]
    a.require(SLUG in (permalink,tail),"Actual Gumroad slug mismatch")
    files=product.get("files") or product.get("rich_content_files") or []
    cover=product.get("covers") or product.get("cover_images") or []
    a.require(len(files)==2 and len(cover)>=1,"Exact two free downloadable files / cover not complete: HOLD")
    seller_price=product.get("price")
    if seller_price is not None:
        a.require(str(seller_price) in {"0","0.0","0.00"},"Seller price is not zero; HOLD")
    # Check uploaded filenames when the CLI includes names; never assume the two files are correct if any declared filename differs.
    names=[str(x.get("name") or x.get("display_name") or x.get("filename") or x.get("file_name") or "") for x in files if isinstance(x,dict)]
    text=" ".join(names).lower()
    if text.strip():
        a.require(".xlsx" in text and ".pdf" in text,"Buyer attachments are not BakeSlot XLSX + PDF")
    store.patch("Gumroad Upload Queue",row,{"Upload Status":"EXISTING_DRAFT_PUBLISHING","Last Attempt UTC":a.make_timestamp()})
    try:
        a.gumroad_cli(["products","publish",ID])
        refreshed=a.gumroad_cli(["products","view",ID]).get("product") or {}
        a.require(refreshed.get("published") is True,"Gumroad publishing unconfirmed")
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":public,"Last Updated UTC":a.make_timestamp()})
        a.verify_public_product_url(public,SLUG)
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED","Gumroad Live URL":public,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        print("GUMROAD_PUBLISHED_VERIFIED "+public)
    except Exception as e:
        latest=[x for x in store.get_rows("Gumroad Upload Queue") if x.get("Product ID")==PRODUCT][0]
        status=latest.get("Upload Status")
        if status=="EXISTING_DRAFT_PUBLISHING":
            store.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW","Last Error":(type(e).__name__+": "+str(e))[:420]})
        elif status=="PUBLISHED_CHECK_URL":
            store.patch("Gumroad Upload Queue",latest,{"Last Error":"Seller published, but public listing HTTP verification pending. Do not republish."})
        raise
if __name__=="__main__":
    run()
