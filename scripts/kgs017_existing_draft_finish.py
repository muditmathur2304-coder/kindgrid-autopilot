"""KGS017: ONE controlled existing-draft attachment+publication; no new seller product."""
from __future__ import annotations
import sys, time, hashlib, json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from src import autopilot as a
from scripts import kgs017_depositguard_once as g

EXACT_ID="WNBcrAtSKAlJggxEeZotxg=="
EDITOR="https://gumroad.com/products/"+EXACT_ID+"/edit"

def single(store,tab,key,val):
    matches=[row for row in store.get_rows(tab) if row.get(key)==val]
    a.require(len(matches)==1,"Wrong number of matching "+val+" dashboard records")
    return matches[0]

def seller_state():
    p=a.gumroad_cli(["products","view",EXACT_ID]).get("product") or {}
    return p

def run():
    a.require(a.enabled("KINDGRID_OWNER_KGS017_RECOVER_ONCE"),"Owner recovery disabled")
    store=a.GoogleStore()
    row=single(store,"Gumroad Upload Queue","Product ID",g.PID)
    a.require(row.get("Upload Status")=="REVIEW" and row.get("Unique Slug")==g.SLUG and
              row.get("Product Name")==g.NAME and row.get("Price USD")==g.PRICE,
              "KGS017 draft is not the exact reconciled REVIEW record")
    a.require(not row.get("Gumroad Live URL"),"Draft seller ID is already recorded; no duplicate attempt")
    a.require(int(row.get("Attempt Count") or "0")==1,"Not the first uniquely-reconciled recovery")
    a.require(not [q for q in store.get_rows("Publishing Queue") if q.get("Queue ID")==g.QID],
              "Q62 already exists; no more Pinterest submission")
    a.require(g.cap_used(store.get_rows("Gumroad Upload Queue"),"Upload Status","Last Updated UTC")<7,
              "Gumroad New York daily cap reached")
    a.require(g.cap_used(store.get_rows("Publishing Queue"),"Status","Last Attempt UTC")<7,
              "Pinterest New York daily cap reached")
    seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
    matched=[str(i.get("id") or "") for i in seller if i.get("custom_permalink")==g.SLUG or
             str(i.get("short_url") or "").rstrip("/").endswith("/"+g.SLUG)]
    a.require(matched==[EXACT_ID],"Seller ID duplicated or changed")
    draft=seller_state()
    a.require(draft.get("published") is False and draft.get("name")==g.NAME and
              draft.get("custom_permalink")==g.SLUG,"Expected exact original unpublished product")
    # Read-only seller audit confirmed exactly ONE existing buyer attachment and cover.
    # Never issue a second file upload; verify the existing one before publication.
    existing_files=draft.get("files") or draft.get("rich_content_files") or []
    a.require(len(existing_files)==1,"Draft must contain exactly one existing customer download")
    b=a.BufferClient();boards=b.boards()
    a.require(g.BOARD in boards and b.scheduled()<10,"No correct Pinterest board or Buffer queue full")
    archive=g.make_assets()
    cover=g.EVIDENCE/"KGS017_Gumroad_Cover.png"
    pin=g.EVIDENCE/"Q62_Pinterest_Original.png"
    a.require(archive.exists() and archive.stat().st_size>10000,"Original offline package incomplete")
    from PIL import Image
    a.require(Image.open(cover).size==(1600,900),"Storefront cover dimensions mismatch")
    a.require(Image.open(pin).size==(1000,1500),"Pinterest 2:3 dimensions mismatch")
    a.require(int(existing_files[0].get("size") or -1)==archive.stat().st_size,
              "Gumroad customer file size differs from independently recreated original ZIP")
    covers=draft.get("covers") or draft.get("cover_images") or []
    a.require(len(covers)>=1,"Gumroad draft cover missing")
    rich=a.gumroad_cli(["products","content","get",EXACT_ID])
    pages=rich if isinstance(rich,list) else (rich.get("rich_content") or []) if isinstance(rich,dict) else []
    embeds=[str(node.get("attrs",{}).get("id") or "") for part in pages
         for node in (part.get("description") or {}).get("content") or []
         if node.get("type")=="fileEmbed"]
    a.require(embeds==[str(existing_files[0].get("id") or "")],"Buyer ZIP not linked as a delivery file")
    g.receipt("EXACT_EXISTING_CUSTOMER_ZIP_AND_COVER_VERIFIED",
              seller_id=EXACT_ID,zip_bytes=archive.stat().st_size,
              zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
              file_id=embeds[0])
    store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
       "Gumroad Live URL":EDITOR,"Last Attempt UTC":a.make_timestamp(),
       "Attempt Count":"2","Last Error":""})
    g.receipt("GUMROAD_PUBLISH_ATTEMPTED_ONCE")
    try:
        a.gumroad_cli(["products","publish",EXACT_ID])
        live=seller_state()
        attached=live.get("files") or live.get("rich_content_files") or []
        a.require(live.get("published") is True and len(attached)==1 and
                  int(attached[0].get("size") or -1)==archive.stat().st_size,
                  "Published listing/customer ZIP unverified")
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":g.PUBLIC})
        a.verify_public_product_url(g.PUBLIC,g.SLUG)
        store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED","Gumroad Live URL":g.PUBLIC,
                  "Last Error":"","Last Updated UTC":a.make_timestamp()})
        g.receipt("GUMROAD_PUBLIC_AND_CUSTOMER_FILE_VERIFIED",product_url=g.PUBLIC)
        print("KGS017_GUMROAD_PUBLISHED "+g.PUBLIC)
    except Exception as exc:
        current=single(store,"Gumroad Upload Queue","Product ID",g.PID)
        if current.get("Upload Status")=="DRAFT_VERIFIED":
            store.patch("Gumroad Upload Queue",current,{"Upload Status":"REVIEW","Last Error":str(exc)[:390]})
        g.receipt("PUBLICATION_UNCERTAIN_NO_RETRY",error_type=type(exc).__name__)
        raise
    q=g.append(store,"Publishing Queue",{
        "Queue ID":g.QID,"Product ID":g.PID,"Pin Type":"Original project deposit cashflow infographic",
        "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "Time Slot":"Owner one-time immediate Pin","US Scheduled Time":"NOW",
        "Target Board":g.BOARD,"Pin Title":g.TITLE,"Pin Description":g.PIN_DESC,
        "Destination URL":g.DEST,"Status":"ONE_TIME_POSTING",
        "QA Verified (YES/NO)":"LOCAL_TESTS_PASS",
        "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1",
        "QA Version":"KGS017-LOCAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    try:
        image=a.cloudinary_upload(pin.read_bytes(),"kgs017-q62-original-recovery")
        a.require(image.startswith("https://"),"Missing publicly accessible Pin image")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
        ... on PostActionSuccess{post{id status externalLink}}
        ... on MutationError{message}}}'''
        body={"channelId":b.channel_id,"text":g.PIN_DESC,
          "schedulingType":"automatic","mode":"shareNow","aiAssisted":True,
          "assets":[{"image":{"url":image}}],
          "metadata":{"pinterest":{"boardServiceId":boards[g.BOARD],
               "title":g.TITLE,"url":g.DEST}}}
        g.receipt("BUFFER_PIN_CREATE_ATTEMPTED_ONCE")
        result=b.graphql(query,{"input":body}).get("createPost") or {}
        post=result.get("post") or {}; bid=str(post.get("id") or "")
        a.require(bid,"Provider mutation response missing ID; no retry")
        store.patch("Publishing Queue",q,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        g.receipt("BUFFER_PIN_ID_VERIFIED",buffer_id=bid)
        link=str(post.get("externalLink") or "")
        for n in range(6):
            if "pinterest.com/pin/" in link or "pin.it/" in link:break
            if n:time.sleep(5)
            link=str(b.get_post(bid).get("externalLink") or "")
        if "pinterest.com/pin/" in link or "pin.it/" in link:
            store.patch("Publishing Queue",q,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            g.receipt("PINTEREST_PUBLIC_URL_VERIFIED",pin_url=link)
            print("Q62_PINTEREST_PUBLISHED "+link)
        else:
            g.receipt("PINTEREST_PIN_PROVIDER_PENDING",buffer_id=bid)
            print("Q62_BUFFER_ID_CONFIRMED_PIN_URL_PENDING "+bid)
    except Exception as exc:
        current=single(store,"Publishing Queue","Queue ID",g.QID)
        if current.get("Status")=="ONE_TIME_POSTING":
            store.patch("Publishing Queue",current,{"Status":"REVIEW","Last Error":str(exc)[:400]})
        g.receipt("PINTEREST_UNCERTAIN_DO_NOT_RETRY",error_type=type(exc).__name__)
        raise

if __name__=="__main__":
    try:run()
    except Exception as exc:
        print("KGS017_SAFE_EXISTING_DRAFT_RECOVERY_STOP",type(exc).__name__,str(exc)[:220],flush=True)
        sys.exit(1)
