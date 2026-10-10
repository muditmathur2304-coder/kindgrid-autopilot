import json,subprocess
h=subprocess.run(["gumroad","products","create","--help"],capture_output=True,text=True)
print("HELP_STATUS",h.returncode)
for line in h.stdout.splitlines():
    if any(x in line.lower() for x in ["preview","thumbnail","summary","file","draft"]):
        print("FLAG",line[:130])
r=subprocess.run(["gumroad","products","list","--all","--json","--no-input"],capture_output=True,text=True)
print("LIST_STATUS",r.returncode)
if r.returncode==0:
    for p in json.loads(r.stdout).get("products",[]):
        if "market-day-margin" in str(p.get("custom_permalink") or "") or "Market Day Margin" in str(p.get("name") or ""):
            print("MATCH",p.get("id"),p.get("name"),p.get("published"),p.get("custom_permalink"))
            if p.get("id"):
                v=subprocess.run(["gumroad","products","view",str(p["id"]),"--json","--no-input"],capture_output=True,text=True)
                print("VIEW_STATUS",v.returncode)
                if v.returncode==0:
                    q=json.loads(v.stdout).get("product") or {}
                    print("DRAFT_INSPECTION",json.dumps({"published":q.get("published"),"file_count":len(q.get("files") or q.get("rich_content_files") or []),"cover_count":len(q.get("covers") or q.get("cover_images") or []),"keys":sorted(q.keys()),"summary_present":bool(q.get("custom_summary"))}))

print("NO_MUTATIONS_PERFORMED")
