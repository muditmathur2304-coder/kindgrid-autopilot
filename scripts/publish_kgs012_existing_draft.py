"""One-time existing-draft-only publication, never create another KGS-012."""
import os, requests
from src import autopilot as a

ID="n8he_NX5xJRvM_gfyd1jPg=="
CODE="KGS-012"
SLUG="bakebatch-weekly-production-planner"
NAME="BakeBatch — Weekly Bakery Production & Pantry Planner | Excel + Guide"
PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
EDIT="https://gumroad.com/products/"+ID+"/edit"

def read_product():
    token=os.environ.get("GUMROAD_ACCESS_TOKEN","").strip()
    a.require(bool(token),"Seller token missing")
    response=requests.get("https://api.gumroad.com/v2/products/"+ID,
        headers={"Authorization":"Bearer "+token},timeout=25)
    response.raise_for_status()
    data=response.json()
    a.require(data.get("success") is True,"Unsuccessful Gumroad product detail")
    return data.get("product") or {}

def release():
    a.require(a.enabled("LIVE_MODE"),"Existing-draft publication disabled")
    store=a.GoogleStore()
    rows=[x for x in store.get_rows("Gumroad Upload Queue") if x.get("Product ID")==CODE]
    a.require(len(rows)==1,"KGS-012 dashboard identity missing or duplicated")
    row=rows[0]
    a.require(row.get("Upload Status")=="REVIEW","Only the reconciled REVIEW draft may publish")
    a.require(row.get("Unique Slug")==SLUG and
              row.get("Product Name")==NAME and row.get("Price USD")=="14.00",
              "Dashboard listing identity drift")
    a.verify_qa_report(store,row,CODE)
    before=read_product()
    a.require(before.get("id")==ID and before.get("name")==NAME and
              before.get("published") is False and
              before.get("custom_permalink")==SLUG,
              "Wrong existing unpublished Gumroad draft")
    a.require(int(before.get("price") or -1)==1400,"Incorrect seller price in cents")
    files=before.get("files") or before.get("rich_content_files") or []
    covers=before.get("covers") or before.get("cover_images") or []
    a.require(len(files)==2 and len(covers)>=3,
              "Exact 2 customer files or 3 product images are incomplete")
    names=" ".join(str(f.get("name") or f.get("display_name") or
             f.get("filename") or f.get("file_name") or "") for f in files
             if isinstance(f,dict)).lower()
    if names.strip():
        a.require(".xlsx" in names and ".pdf" in names,
                  "Buyer attachment names do not match BakeBatch Excel + guide")
    print("READBACK_CONFIRMED seller ID, title, slug, price, 2 buyer files, 3 artwork images")
    store.patch("Gumroad Upload Queue",row,{
        "Upload Status":"EXISTING_DRAFT_PUBLISHING",
        "Gumroad Live URL":EDIT,
        "Last Attempt UTC":a.make_timestamp()
    })
    try:
        # This operation ONLY publishes the confirmed existing draft, never creates.
        a.gumroad_cli(["products","publish",ID])
        after=read_product()
        a.require(after.get("published") is True and
                  after.get("id")==ID and after.get("custom_permalink")==SLUG and
                  len(after.get("files") or [])==2,
                  "Seller publish/readback uncertain; no retry")
        store.patch("Gumroad Upload Queue",row,{
            "Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":PUBLIC,
            "Last Updated UTC":a.make_timestamp()
        })
        a.verify_public_product_url(PUBLIC,SLUG)
        store.patch("Gumroad Upload Queue",row,{
            "Upload Status":"PUBLISHED","Gumroad Live URL":PUBLIC,
            "Last Error":"","Last Updated UTC":a.make_timestamp()
        })
        print("GUMROAD_PUBLISHED_VERIFIED",PUBLIC)
    except Exception as exc:
        latest=[x for x in store.get_rows("Gumroad Upload Queue") if x.get("Product ID")==CODE][0]
        if latest.get("Upload Status")=="PUBLISHED_CHECK_URL":
            store.patch("Gumroad Upload Queue",latest,{
                "Last Error":"Seller is PUBLISHED, but public HTTP verification pending. Do NOT publish again."
            })
        else:
            store.patch("Gumroad Upload Queue",latest,{
                "Upload Status":"REVIEW",
                "Last Error":(type(exc).__name__+": "+str(exc))[:430]
            })
        raise

if __name__=="__main__":release()
