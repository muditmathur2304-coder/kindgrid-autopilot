"""One-shot KGS-013 Excel-first public release. Never retry uncertain seller actions."""
from __future__ import annotations
import io, os, re, sys, tempfile
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from src import autopilot as a
from src.paired_release import published_today_count

SKU="KGS-013"
PIN="Q-58"
SLUG="collectflow-invoice-followup-control"
PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
XLSX="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def single(store, sheet, key, value):
    result=[r for r in store.get_rows(sheet) if r.get(key)==value]
    a.require(len(result)==1,"Expected exactly one "+value+" record")
    return result[0]

def prepare(store, r):
    a.require(r.get("Unique Slug")==SLUG and r.get("Price USD")=="15.00","Wrong approved slug or price")
    a.require(r.get("QA Verified (YES/NO)")=="YES","QA not approved")
    a.verify_qa_report(store,r,SKU)
    pdf=store.get_bytes(a.google_file_id(r["PDF Drive Link"]),"application/pdf")
    a.require(a.validate_pdf(pdf)==5,"Expected five illustrated guide pages")
    xlsx=store.get_bytes(a.google_file_id(r["Bonus File Drive Link"]),XLSX)
    with ZipFile(io.BytesIO(xlsx)) as z:
        media=[n for n in z.namelist() if n.startswith("xl/media/")]
        sheets=[n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
        a.require(len(sheets)==8 and len(media)>=2 and all(z.getinfo(n).file_size>10000 for n in media),"Workbook formula tabs or embedded illustrations missing")
    pictures=[store.get_bytes(a.google_file_id(r[col]),"image/png") for col in
              ("Cover Drive Link","Gallery Image 1 Drive Link","Gallery Image 2 Drive Link")]
    for img in pictures: a.validate_image(img)
    doc=store.get_doc_text(a.google_file_id(r["Listing Copy Drive Link"],"document"))
    summary=re.search(r"(?m)^SUMMARY:\s*(.+)$",doc)
    a.require(summary is not None and "DESCRIPTION:" in doc and "ITEM ID:" in doc,"Seller copy or QA text absent")
    desc=doc.split("DESCRIPTION:",1)[1].split("ITEM ID:",1)[0].strip()
    a.require(len(desc)>=650 and "INCLUDED:" in desc,"Customer description incomplete")
    return pdf,xlsx,pictures,summary.group(1),desc

def check_duplicate():
    resp=a.gumroad_cli(["products","list","--all"])
    items=resp.get("products") or []
    a.require(isinstance(items,list),"Seller inventory inaccessible")
    for product in items:
        s=str(product.get("custom_permalink") or "")
        short=str(product.get("short_url") or "").split("?")[0].rstrip("/").split("/")[-1]
        a.require(s!=SLUG and short!=SLUG,"A CollectFlow listing already exists; hold to reconcile")

def publish(store,r,assets):
    pdf,xlsx,pictures,summary,description=assets
    with tempfile.TemporaryDirectory(prefix="kindgrid-kgs013-") as tmp:
        directory=Path(tmp)
        mapping={"guide.pdf":pdf,"CollectFlow.xlsx":xlsx,"cover.png":pictures[0],
                 "gallery1.png":pictures[1],"gallery2.png":pictures[2]}
        for name,data in mapping.items(): (directory/name).write_bytes(data)
        args=["products","create","--draft","--name",r["Product Name"],"--price","15.00",
              "--currency","usd","--type","digital","--custom-permalink",SLUG,
              "--description",description,"--custom-summary",summary,
              "--file",str(directory/"guide.pdf"),"--file",str(directory/"CollectFlow.xlsx"),
              "--cover-image",str(directory/"cover.png"),"--thumbnail",str(directory/"cover.png"),
              "--preview-image",str(directory/"gallery1.png"),
              "--preview-image",str(directory/"gallery2.png")]
        store.patch("Gumroad Upload Queue",r,{"Upload Status":"RELEASE_ATTEMPTED",
                    "Last Attempt UTC":a.make_timestamp(),
                    "Attempt Count":str(int(r.get("Attempt Count") or "0")+1)})
        response=a.gumroad_cli(args)
        pid=str((response.get("product") or {}).get("id") or "")
        a.require(pid,"Seller create response omitted product ID; do not retry")
        draft=a.gumroad_cli(["products","view",pid]).get("product") or {}
        files=draft.get("files") or draft.get("rich_content_files") or []
        cover=draft.get("covers") or draft.get("cover_images") or []
        a.require(draft.get("published") is False and draft.get("name")==r["Product Name"]
                  and len(files)>=2 and bool(cover),"Draft/readback or attached files uncertain")
        store.patch("Gumroad Upload Queue",r,{"Upload Status":"DRAFT_VERIFIED",
             "Gumroad Live URL":"https://gumroad.com/products/"+pid+"/edit",
             "Last Updated UTC":a.make_timestamp()})
        a.gumroad_cli(["products","publish",pid])
        live=a.gumroad_cli(["products","view",pid]).get("product") or {}
        files=live.get("files") or live.get("rich_content_files") or []
        cover=live.get("covers") or live.get("cover_images") or []
        a.require(live.get("published") is True and len(files)>=2 and bool(cover),
                  "Publication/readback uncertain; do not promote")
        a.verify_public_product_url(PUBLIC,SLUG)
        store.patch("Gumroad Upload Queue",r,{"Upload Status":"PUBLISHED",
             "Gumroad Live URL":PUBLIC,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        print("GUMROAD_PUBLISHED_VERIFIED "+PUBLIC)

def schedule_pin(store):
    p=single(store,"Publishing Queue","Queue ID",PIN)
    a.require(p.get("Status")=="AWAITING_GUMROAD" and p.get("Product")==SKU,
              "Q-58 may already be processing, stop to avoid duplicate")
    a.require(not p.get("Batch ID") and not p.get("Actual Pinterest Pin URL"),
              "Pinterest provider identity already exists")
    a.verify_qa_report(store,p,PIN)
    uncertain=[r.get("Queue ID") for r in store.get_rows("Publishing Queue")
               if r.get("Status") in {"REVIEW","LINK_REVIEW","SCHEDULING"}]
    a.require(not uncertain,"Prior uncertain Pinterest posts; do not create another")
    a.verify_public_product_url(PUBLIC,SLUG)
    now=datetime.now(timezone.utc)
    if a.pin_due_at(p)<=now+timedelta(minutes=8):
        local=now.astimezone(ZoneInfo("America/New_York"))
        times=[(10,30,"Late Morning"),(12,30,"Midday"),(14,30,"Afternoon"),
               (16,30,"Late Afternoon"),(20,30,"Evening"),(21,30,"Late Evening")]
        option=next(((h,m,win) for h,m,win in times if
                     local.replace(hour=h,minute=m,second=0,microsecond=0)>local+timedelta(minutes=12)),None)
        if not option:
            print("PINTEREST_HELD no safe remaining NY slot today")
            return
        h,m,window=option
        p["Time Window"]=window
        p["US Scheduled Time"]=f"{h:02d}:{m:02d} {local.strftime('%Z')}"
        store.patch("Publishing Queue",p,{"Time Window":window,"US Scheduled Time":p["US Scheduled Time"]})
    p["Status"]="READY"
    store.patch("Publishing Queue",p,{"Status":"READY"})
    for line in a.process_pins(store,[p],datetime.now(timezone.utc)):
        print("PINTEREST_RESULT "+line)

def main():
    a.require(a.enabled("LIVE_MODE"),"Live seller mode has not been authorized in repo settings")
    store=a.GoogleStore()
    r=single(store,"Gumroad Upload Queue","Product ID",SKU)
    a.require(r.get("Upload Status")=="RELEASE_APPROVED_ONCE",
              "No unused one-time approval; do not retry or recreate")
    used=published_today_count(store.get_rows("Gumroad Upload Queue"))
    a.require(used<7,"Seven Gumroad listings already confirmed today in NY")
    assets=prepare(store,r)
    print("KGS013_SOURCE_QA_PASS")
    check_duplicate()
    print("KGS013_DUPLICATE_CHECK_PASS")
    try:
        publish(store,r,assets)
    except Exception as error:
        latest=single(store,"Gumroad Upload Queue","Product ID",SKU)
        if latest.get("Upload Status") in {"RELEASE_ATTEMPTED","DRAFT_VERIFIED"}:
            store.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW",
                        "Last Error":(type(error).__name__+": "+str(error))[:420]})
        raise
    try:
        schedule_pin(store)
    except Exception as error:
        print("PINTEREST_HELD_AFTER_VERIFIED_GUMROAD "+type(error).__name__+": "+str(error))

if __name__=="__main__":
    try: main()
    except Exception as error:
        print("KGS013_RELEASE_BLOCKED "+type(error).__name__+": "+str(error))
        sys.exit(1)
