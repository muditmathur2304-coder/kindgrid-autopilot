"""Read-only KGS009 inspection: no uploads and no seller writes."""
import json,sys
sys.path.insert(0,'.')
from src import autopilot as a
matches=[]
for p in a.gumroad_cli(["products","list","--all"]).get("products",[]):
 slug=str(p.get("custom_permalink") or "")
 tail=str(p.get("short_url") or "").rstrip("/").split("/")[-1]
 if slug=="before-you-book-booth-free" or tail=="before-you-book-booth-free":
  pid=str(p.get("id") or "")
  obj=a.gumroad_cli(["products","view",pid]).get("product") or {}
  raw=a.gumroad_cli(["products","content","get",pid])
  page_ids=[]
  if isinstance(raw,list):
   for page in raw:
    page_ids.extend(str(n.get("attrs",{}).get("id") or "")
                    for n in (page.get("description") or {}).get("content") or []
                    if n.get("type")=="fileEmbed")
  matches.append({"id":pid,"title":obj.get("name"),"slug":slug,
      "published":obj.get("published"),"size_files":[{"id":x.get("id"),"size":x.get("size")} for x in obj.get("files") or []],
      "covers":len(obj.get("covers") or []),"summary":bool(obj.get("custom_summary")),
      "customer_embed_ids":page_ids})
print("KGS009_FREE_READONLY_RECONCILIATION "+json.dumps(matches))
print("NO_WRITES_NO_DUPLICATES")
