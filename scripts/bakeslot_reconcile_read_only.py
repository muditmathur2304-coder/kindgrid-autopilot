"""Read-only KGS-010 Gumroad recovery and specific draft inspection. Do not create anything."""
from src import autopilot as a
import subprocess,os,re,json
CODE="KGS-010"
SLUG="bakeslot-order-capacity-studio"
NAME="BakeSlot Studio — Custom Order, Quote & Capacity System for Bakers"
def main():
    s=a.GoogleStore()
    r=[x for x in s.get_rows("Gumroad Upload Queue") if x.get("Product ID")==CODE][0]
    cmd=["gumroad","products","list","--all","--json","--no-input"]
    res=subprocess.run(cmd,text=True,capture_output=True,timeout=150,env=os.environ.copy())
    if res.returncode:
        err=(res.stderr or res.stdout or "unknown Gumroad CLI failure")
        err=re.sub(r"(?i)(access[_-]?token|authorization|bearer)\s*[:= ]+\S+",r"\1 [REDACTED]",err)
        err=re.sub(r"(?i)https?://[^\s]+","[URL]",err)
        s.patch("Gumroad Upload Queue",r,{"Last Error":("READ_ONLY_CLI_ERROR: "+err)[:420]})
        print("SELLER_LIST_READ_FAILED",res.returncode)
        return
    try:
        obj=json.loads(res.stdout)
        products=obj.get("products") or []
    except Exception:
        s.patch("Gumroad Upload Queue",r,{"Last Error":"READ_ONLY_CLI_PARSE_ERROR"})
        return
    matches=[]
    for p in products:
        permalink=str(p.get("custom_permalink") or "")
        tail=str(p.get("short_url") or "").rstrip("/").split("/")[-1]
        if SLUG in (permalink,tail) or p.get("name")==NAME:
            matches.append(p)
    if not matches:
        s.patch("Gumroad Upload Queue",r,{"Last Error":"RECONCILE: no matching Gumroad listing in seller products list; first attempt failed before a confirmed product ID. No blind auto-retry."})
        print("NO_MATCHING_PRODUCT")
        return
    if len(matches)!=1:
        s.patch("Gumroad Upload Queue",r,{"Last Error":"RECONCILE: multiple similar seller products; manual intervention required."})
        print("MULTIPLE_MATCHES")
        return
    ident=str(matches[0].get("id") or "")
    if not ident:
        s.patch("Gumroad Upload Queue",r,{"Last Error":"RECONCILE: found matching listing without ID."})
        return
    try:
        state=a.gumroad_cli(["products","view",ident]).get("product") or {}
    except Exception as e:
        s.patch("Gumroad Upload Queue",r,{"Gumroad Live URL":"https://gumroad.com/products/"+ident+"/edit",
                 "Last Error":"RECONCILE: matched seller listing, view call failed; inspect attachments before action."})
        print("MATCH_FOUND_VIEW_FAILED")
        return
    files=state.get("files") or state.get("rich_content_files") or []
    covers=state.get("covers") or state.get("cover_images") or []
    published=state.get("published")
    s.patch("Gumroad Upload Queue",r,{"Gumroad Live URL":"https://gumroad.com/products/"+ident+"/edit",
             "Last Error":"RECONCILE: matching listing ID confirmed; published="+str(published)+
             "; downloadable file objects="+str(len(files))+"; cover objects="+str(len(covers))+
             ". No automatic retry or publication until full attachment verification."})
    print("MATCHING_PRODUCT",ident,"published",published,"files",len(files),"covers",len(covers))
if __name__=="__main__":
    main()
