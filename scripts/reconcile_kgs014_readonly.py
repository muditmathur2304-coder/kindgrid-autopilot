"""No mutation: determine whether KGS014 create returned error after making a draft."""
import json,subprocess
from src import autopilot as a
slug="unpaid-invoice-reset-free"
products=a.gumroad_cli(["products","list","--all"]).get("products",[])
matches=[]
for p in products:
 if p.get("custom_permalink")==slug or str(p.get("short_url") or "").rstrip("/").endswith("/"+slug):
  pid=str(p.get("id") or "")
  view=a.gumroad_cli(["products","view",pid]).get("product") or {}
  matches.append({"seller_id":pid,"title":view.get("name"),"slug":view.get("custom_permalink"),
    "published":view.get("published"),
    "files":[{"size":v.get("size"),"id":v.get("id")} for v in view.get("files") or []],
    "covers":len(view.get("covers") or view.get("cover_images") or [])})
print("KGS014_READ_ONLY_MATCHES="+json.dumps(matches))
p=subprocess.run(["gumroad","products","create","--help"],capture_output=True,text=True,timeout=20)
flags=["--draft","--pay-what-you-want","--thumbnail","--cover-image","--custom-summary","--file"]
print("CREATE_HELP_FLAGS="+json.dumps({f:(f in p.stdout) for f in flags}))
print("READ_ONLY_NO_SELLER_WRITES")
