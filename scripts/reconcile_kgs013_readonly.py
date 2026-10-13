"""Read-only seller reconciliation for uncertain KGS-013 draft creation."""
import os, sys, requests
from src.autopilot import GoogleStore, make_timestamp

def main():
    token=os.getenv("GUMROAD_ACCESS_TOKEN","").strip()
    if not token: raise RuntimeError("Seller token absent, no seller writes")
    response=requests.get("https://api.gumroad.com/v2/products",
        headers={"Authorization":"Bearer "+token,"Accept":"application/json"},timeout=30)
    if response.status_code!=200: raise RuntimeError("Seller inventory HTTP "+str(response.status_code))
    data=response.json()
    if data.get("success") is not True or not isinstance(data.get("products"),list):
        raise RuntimeError("Seller inventory response unavailable")
    matches=[]
    for p in data["products"]:
        slug=str(p.get("custom_permalink") or "")
        url=str(p.get("short_url") or "").split("?")[0].rstrip("/").split("/")[-1]
        name=str(p.get("name") or "")
        if (slug=="collectflow-invoice-followup-control" or url=="collectflow-invoice-followup-control" or
                name=="CollectFlow Studio — Invoice Follow-Up & Cash-Control System"):
            matches.append(p)
    store=GoogleStore()
    row=next(r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-013")
    if len(matches)>1:
        message="GUMROAD_RECONCILE: MULTIPLE_MATCHING_PRODUCTS; no automatic action"
    elif len(matches)==1:
        p=matches[0];ident=str(p.get("id") or "")
        files=p.get("files") or p.get("rich_content_files") or []
        covers=p.get("covers") or p.get("cover_images") or []
        control=next((x for x in data["products"] if
            str(x.get("custom_permalink") or "")=="bakeslot-order-capacity-studio" or
            str(x.get("short_url") or "").rstrip("/").endswith("/bakeslot-order-capacity-studio")), {})
        known_files=control.get("files") or control.get("rich_content_files") or []
        detail_response=requests.get("https://api.gumroad.com/v2/products/"+ident,
            headers={"Authorization":"Bearer "+token,"Accept":"application/json"},timeout=30)
        if detail_response.status_code==200:
            detail=detail_response.json().get("product") or {}
            detail_files=detail.get("files") or detail.get("rich_content_files") or []
            interesting=[k for k in detail if any(word in k.lower() for word in ("file","content","cover","preview"))]
            details=" DETAIL_FILES="+str(len(detail_files))+" DETAIL_FIELDS="+",".join(interesting[:8])
        else:
            details=" DETAIL_HTTP="+str(detail_response.status_code)
        message=("GUMROAD_DRAFT_DETAIL ID="+ident+" LIST_FILES="+str(len(files))+
                 " COVER="+str(bool(covers))+" KNOWN_LIVE_LIST_FILES="+str(len(known_files))+details)
    else:
        message="GUMROAD_RECONCILE_NOT_FOUND_IN_V2_LIST: check seller draft UI before retrying"
    if row.get("Upload Status")=="REVIEW":
        store.patch("Gumroad Upload Queue",row,{"Last Error":message[:425]})
    print(message)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("GUMROAD_READONLY_CHECK_FAILED "+type(e).__name__+" "+str(e))
        sys.exit(1)
