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
print("NO_MUTATIONS_PERFORMED")
