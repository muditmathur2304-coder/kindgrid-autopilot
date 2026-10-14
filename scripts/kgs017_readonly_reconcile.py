"""Read-only KGS017 seller reconciliation: never create, edit, retry or publish."""
import json, os, subprocess, requests
from src import autopilot as a
slug="depositguard-project-cash-coverage"
result={"slug":slug}
token=os.getenv("GUMROAD_ACCESS_TOKEN","")
if not token:raise SystemExit("NO_TOKEN")
resp=requests.get("https://api.gumroad.com/v2/products",headers={"Authorization":"Bearer "+token,"Accept":"application/json"},timeout=25)
result["v2_http_status"]=resp.status_code
data=resp.json() if resp.status_code==200 else {}
matches=[]
for p in data.get("products") or []:
    if str(p.get("custom_permalink") or "")==slug or str(p.get("short_url") or "").rstrip("/").endswith("/"+slug):
        matches.append({"id":p.get("id"),"name":p.get("name"),"published":p.get("published"),
                        "custom_permalink":p.get("custom_permalink"),"short_url":p.get("short_url"),
                        "files_count":len(p.get("files") or []),"file_sizes":[f.get("size") for f in p.get("files") or []]})
result["api_matches"]=matches
result["api_product_total"]=len(data.get("products") or [])
try:
    seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
    result["cli_matches"]=[{"id":p.get("id"),"name":p.get("name"),"published":p.get("published"),
                            "custom_permalink":p.get("custom_permalink"),"short_url":p.get("short_url")}
                           for p in seller if p.get("custom_permalink")==slug or str(p.get("short_url") or "").rstrip("/").endswith("/"+slug)]
except Exception as exc:
    result["cli_list_error_type"]=type(exc).__name__
p=subprocess.run(["gumroad","products","create","--help"],capture_output=True,text=True,timeout=20)
result["create_help_flags"]={k:(k in p.stdout) for k in ["--file","--cover-image","--thumbnail","--custom-summary","--draft","--custom-permalink"]}
print("KGS017_READ_ONLY_RECON="+json.dumps(result))
print("NO_SELLER_MUTATION_NO_UPLOAD_NO_RETRY")
