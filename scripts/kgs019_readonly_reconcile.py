"""Seller GET-only audit for KGS019. No file uploads, listing writes, or retries."""
import os,requests,json
from scripts import kgs019_movemargin_assets as m
m.run()
p=m.OUT/"MoveMargin_Customer_Download.zip"
expected=p.stat().st_size
token=os.getenv("GUMROAD_ACCESS_TOKEN","").strip()
if not token:raise SystemExit("MISSING_SELLER_TOKEN")
h={"Authorization":"Bearer "+token,"Accept":"application/json"}
r=requests.get("https://api.gumroad.com/v2/products",headers=h,timeout=30)
print("SELLER_LIST_HTTP",r.status_code);r.raise_for_status()
items=r.json().get("products") or []
matching=[x for x in items if x.get("custom_permalink")==m.SLUG
     or str(x.get("short_url") or "").rstrip("/").endswith("/"+m.SLUG)]
print("KGS019_EXACT_SLUG_MATCHES",len(matching))
for obj in matching:
    sid=obj.get("id")
    d=requests.get("https://api.gumroad.com/v2/products/"+str(sid),headers=h,timeout=30)
    result=(d.json().get("product") or {}) if d.ok else obj
    files=result.get("files") or result.get("rich_content_files") or []
    info={"seller_id":sid,"name":result.get("name"),"slug":result.get("custom_permalink"),
          "published":result.get("published"),"cover_count":len(result.get("covers") or result.get("cover_images") or []),
          "files":[{"id":f.get("id"),"size":f.get("size")} for f in files],
          "local_customer_zip_bytes":expected,"exact_zip_size_match":len(files)==1 and int(files[0].get("size") or -1)==expected,
          "public_slug":result.get("short_url")}
    print("KGS019_SELLER_READBACK "+json.dumps(info))
print("NO_SELLER_WRITES_OR_PIN_RETRIES")
