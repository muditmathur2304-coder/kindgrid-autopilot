"""Read-only verification whether failed KGS009 create actually made a draft."""
import json
from src import autopilot as a
SLUG="before-you-book-booth-free"
x=a.gumroad_cli(["products","list","--all"]).get("products",[])
matched=[]
for p in x:
 if str(p.get("custom_permalink") or "")==SLUG or str(p.get("short_url") or "").rstrip("/").endswith("/"+SLUG):
  id=str(p.get("id") or "")
  v=a.gumroad_cli(["products","view",id]).get("product") or {}
  matched.append({"id":id,"name":v.get("name"),"slug":v.get("custom_permalink"),
   "published":v.get("published"),"files":[{"id":z.get("id"),"size":z.get("size")} for z in v.get("files") or []],
   "cover_count":len(v.get("covers") or v.get("cover_images") or []),
   "summary_present":bool(v.get("custom_summary"))})
print("KGS009_READ_ONLY_MATCHES="+json.dumps(matched))
print("NO_MUTATIONS_PERFORMED")
