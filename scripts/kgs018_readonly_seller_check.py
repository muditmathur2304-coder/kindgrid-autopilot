"""Read-only seller verification for exact ScopePulse slug; no listing or asset writes."""
import os,json,requests
token=os.getenv("GUMROAD_ACCESS_TOKEN","")
if not token:raise SystemExit("Seller token unavailable")
base="https://api.gumroad.com/v2"
headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
r=requests.get(base+"/products",headers=headers,timeout=25)
print("KGS018_SELLER_GET_HTTP",r.status_code)
r.raise_for_status()
items=r.json().get("products") or []
target=[x for x in items if x.get("custom_permalink")=="scopepulse-revision-pricing-studio" or
    str(x.get("short_url") or "").rstrip("/").endswith("/scopepulse-revision-pricing-studio")]
print("KGS018_SELLER_MATCH_COUNT",len(target))
for x in target:
    pid=x.get("id")
    d=requests.get(base+"/products/"+str(pid),headers=headers,timeout=25)
    obj=(d.json().get("product") or {}) if d.ok else x
    fs=obj.get("files") or []
    print("KGS018_SELLER_DETAIL",json.dumps({
      "id":pid,"name":obj.get("name"),"price":obj.get("price"),
      "published":obj.get("published"),"slug":obj.get("custom_permalink"),
      "files":[{"id":f.get("id"),"size":f.get("size"),"name":f.get("name"),"filename":f.get("filename")} for f in fs],
      "cover_count":len(obj.get("covers") or obj.get("cover_images") or []),
      "description_len":len(str(obj.get("description") or "")),
      "short_url":obj.get("short_url")} ))
print("READ_ONLY_NO_MUTATION")
