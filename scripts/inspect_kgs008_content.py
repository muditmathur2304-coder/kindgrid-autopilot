"""Read-only inspection of exact held KGS-008 Gumroad draft content and file embeds.
NO uploads, edits or publishing. No personal details printed.
"""
import json,sys
sys.path.insert(0,'.')
from src import autopilot as a
SLUG="market-day-margin-guide"
items=a.gumroad_cli(["products","list","--all"]).get("products",[])
matches=[p for p in items if str(p.get("custom_permalink") or "")==SLUG or str(p.get("short_url") or "").rstrip("/").endswith("/"+SLUG)]
a.require(len(matches)==1,"Expected one known existing market-day draft")
pid=str(matches[0]["id"])
p=a.gumroad_cli(["products","view",pid]).get("product") or {}
a.require(p.get("published") is False,"Existing product unexpectedly published")
print("PRODUCT_STATE "+json.dumps({"id":pid,"slug":p.get("custom_permalink"),"title":p.get("name"),"published":p.get("published"),"files":[{"id":f.get("id"),"name":f.get("display_name") or f.get("name") or f.get("filename"),"size":f.get("size")} for f in p.get("files") or []]}))
raw=a.gumroad_cli(["products","content","get",pid])
pages=raw if isinstance(raw,list) else raw.get("rich_content") or raw.get("result") or raw
def brief(obj,depth=0):
 if depth>8:return "[depth]"
 if isinstance(obj,list):return [brief(v,depth+1) for v in obj[:15]]
 if isinstance(obj,dict):
  out={}
  for k,v in obj.items():
   if k.lower() in {"text","description","html","content","caption"} and isinstance(v,str):
    out[k] = v[:70] if len(v)>70 else v
   elif k in ("id","type","file_id","file_url","url","name","display_name","filename","children","content","attrs","data","pages","rich_content","files","file","source","src","blocks"):
    out[k]=brief(v,depth+1)
  return out
 return obj if not isinstance(obj,str) or len(obj)<130 else obj[:120]
print("RICH_CONTENT_SHAPE "+json.dumps(brief(pages),ensure_ascii=False)[:13000])
print("READ_ONLY_NO_MUTATION")
