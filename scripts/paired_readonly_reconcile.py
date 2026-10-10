"""Safe read-only seller inspection after paused KG-PAIR-001 launch.
Never create/update/publish a Gumroad product or Pin.
"""
import json
import sys
sys.path.insert(0,".")
from src import autopilot as a

NEEDLES={"paycheck-gap-playbook","paycheck-gap-starter"}
print("PAIR001_READ_ONLY_RECONCILIATION_START")
try:
    data=a.gumroad_cli(["products","list","--all"])
    items=data.get("products", [])
    matched=[]
    for p in items:
        slug=str(p.get("custom_permalink") or "").strip("/")
        link=str(p.get("short_url") or "").rstrip("/")
        if slug in NEEDLES or link.split("/")[-1] in NEEDLES or "Paycheck Gap" in str(p.get("name") or ""):
            ident=str(p.get("id") or "")
            details=a.gumroad_cli(["products","view",ident]).get("product") or {}
            matched.append({"id":ident,"slug":slug,"name":str(p.get("name") or "")[:120],
               "published":details.get("published"),"download_count":len(details.get("files") or details.get("rich_content_files") or []),
               "cover_present":bool(details.get("covers") or details.get("cover_images"))})
    print("SAFE_MATCHING_PRODUCTS_JSON="+json.dumps(matched))
    print("TOTAL_LISTED_PRODUCTS="+str(len(items)))
except Exception as ex:
    print("SAFE_READ_ERROR="+type(ex).__name__+": "+str(ex)[:240])
    sys.exit(1)
print("PAIR001_RECONCILIATION_FINISHED_NO_WRITES")
