"""Read-only reconciliation for uncertain KGS-012 draft after Gumroad CLI error."""
import os
import requests
TARGET="bakebatch-weekly-production-planner"
TARGET_NAME="BakeBatch"
def main():
    token=os.environ.get("GUMROAD_ACCESS_TOKEN","").strip()
    if not token:raise RuntimeError("Missing Gumroad seller token")
    r=requests.get("https://api.gumroad.com/v2/products",headers={"Authorization":f"Bearer {token}","Accept":"application/json"},timeout=25)
    r.raise_for_status()
    p=r.json().get("products") or []
    if not isinstance(p,list):raise RuntimeError("Unexpected seller list")
    print("SELLER_LIST_READ_OK",len(p))
    found=0
    for x in p:
        if not isinstance(x,dict):continue
        name=str(x.get("name") or "")
        slug=str(x.get("custom_permalink") or "")
        short=str(x.get("short_url") or "")
        if TARGET in (slug,short.rstrip("/").split("/")[-1]) or TARGET_NAME.lower() in name.lower():
            found+=1
            print("BAKEBATCH_CANDIDATE",{"id":x.get("id"),"name":name,"slug":slug,"short_url":short,
                 "published":x.get("published"),"deleted":x.get("deleted"),
                 "file_count":len(x.get("files") or x.get("rich_content_files") or []),
                 "cover_count":len(x.get("covers") or x.get("cover_images") or [])})
    print("BAKEBATCH_CANDIDATE_COUNT",found)
    print("READ_ONLY_NO_WRITES")
if __name__=="__main__":main()
