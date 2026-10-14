"""Publish exact reconciled KGS018 existing draft, then deliver one original Q63 Pin.
No product creation, no replacement attachments, no blind Pinterest repost.
"""
from __future__ import annotations
import sys,time,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from src import autopilot as a
from scripts import kgs018_scopepulse_once as p
from scripts import kgs017_depositguard_once as g

SELLER_ID="tq8HcMXzt2hOQy2Zqrf-ig=="
FILE_ID="-b1z3h-H4o5s7t1BTVSuGg=="
FILE_BYTES=13844
EDITOR="https://gumroad.com/products/"+SELLER_ID+"/edit"

def check_seller():
    view=a.gumroad_cli(["products","view",SELLER_ID]).get("product") or {}
    a.require(view.get("name")==p.NAME and view.get("custom_permalink")==p.SLUG,"Seller identity changed")
    a.require(view.get("published") is False,"KGS018 already published; stop duplicate attempt")
    fs=view.get("files") or view.get("rich_content_files") or []
    a.require(len(fs)==1 and str(fs[0].get("id") or "")==FILE_ID
              and int(fs[0].get("size") or -1)==FILE_BYTES,"Buyer file identity/size differs")
    a.require(len(view.get("covers") or view.get("cover_images") or [])>=1,
              "Customer-facing cover missing")
    rich=a.gumroad_cli(["products","content","get",SELLER_ID])
    pages=rich if isinstance(rich,list) else (rich.get("rich_content") or []) if isinstance(rich,dict) else []
    ids=[str(node.get("attrs",{}).get("id") or "") for page in pages
         for node in (page.get("description") or {}).get("content") or []
         if node.get("type")=="fileEmbed"]
    a.require(ids==[FILE_ID],"Gumroad product rich-content buyer download embed mismatch")
    return view

def main():
    a.require(a.enabled("KINDGRID_SCOPEPULSE_EXISTING_ONCE"),"Not owner approved")
    s=a.GoogleStore()
    row=p.single(s,"Gumroad Upload Queue","Product ID",p.PID)
    a.require(row.get("Upload Status")=="REVIEW" and row.get("Unique Slug")==p.SLUG
              and row.get("Product Name")==p.NAME and row.get("Price USD")==p.PRICE
              and int(row.get("Attempt Count") or "0")==1,"Not exact held first-use KGS018 draft")
    a.require(not row.get("Gumroad Live URL"),"Seller page already recorded, reconcile")
    pins=s.get_rows("Publishing Queue")
    a.require(not any(r.get("Queue ID")==p.QID or r.get("Destination URL","").startswith(p.PUBLIC)
                      for r in pins),"Q63 already attempted: no duplicate")
    a.require(g.cap_used(s.get_rows("Gumroad Upload Queue"),"Upload Status","Last Updated UTC")<7,
              "Gumroad US-day daily cap reached")
    a.require(g.cap_used(pins,"Status","Last Attempt UTC")<7,"Pinterest US-day daily cap reached")
    seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
    a.require([str(r.get("id")) for r in p.seller_match(seller)]==[SELLER_ID],
              "No single exact seller draft")
    source=p.build_assets()
    a.require(source.stat().st_size==FILE_BYTES,
              "Locally regenerated ZIP does not have the original approved customer byte count")
    check_seller()
    b=a.BufferClient();boards=b.boards()
    choices=sorted([n for n in boards if any(k in n.lower() for k in
               ("freelanc","business","finance","budget","pricing"))],
               key=lambda n:0 if ("freelanc" in n.lower() or "business" in n.lower()) else 1)
    a.require(bool(choices) and b.scheduled()<10,"Appropriate Buffer board/capacity unavailable")
    board=choices[0]
    p.note("EXACT_EXISTING_SELLER_ZIP_DELIVERY_COVER_VERIFIED",
           seller_id=SELLER_ID,buyer_attachment_id=FILE_ID,bytes=FILE_BYTES,
           sha256=hashlib.sha256(source.read_bytes()).hexdigest(),board=board)
    s.patch("Gumroad Upload Queue",row,{"Upload Status":"EXISTING_DRAFT_PUBLISHING",
        "Gumroad Live URL":EDITOR,"Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2"})
    p.note("PUBLISH_EXACT_SELLER_DRAFT_ATTEMPT_ONCE")
    try:
        a.gumroad_cli(["products","publish",SELLER_ID])
        live=a.gumroad_cli(["products","view",SELLER_ID]).get("product") or {}
        fs=live.get("files") or live.get("rich_content_files") or []
        a.require(live.get("published") is True and len(fs)==1
           and str(fs[0].get("id") or "")==FILE_ID
           and int(fs[0].get("size") or -1)==FILE_BYTES,"Live product and buyer attachment not verified")
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL",
            "Gumroad Live URL":p.PUBLIC})
        a.verify_public_product_url(p.PUBLIC,p.SLUG)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
            "Gumroad Live URL":p.PUBLIC,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        p.note("GUMROAD_PUBLIC_VERIFIED",product_url=p.PUBLIC)
        print("KGS018_PUBLIC_GUMROAD "+p.PUBLIC,flush=True)
    except Exception as e:
        current=p.single(s,"Gumroad Upload Queue","Product ID",p.PID)
        if current.get("Upload Status")=="EXISTING_DRAFT_PUBLISHING":
            s.patch("Gumroad Upload Queue",current,{"Upload Status":"REVIEW","Last Error":str(e)[:400]})
        p.note("GUMROAD_PUBLISH_UNCERTAIN_DO_NOT_RETRY",error_type=type(e).__name__)
        raise
    pin=p.append(s,"Publishing Queue",{
        "Queue ID":p.QID,"Product":p.PID,
        "Content Type":"Original revision-cost infographic",
        "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "Time Window":"Owner-authorized immediate original Pin",
        "US Scheduled Time":"NOW","Target Board":board,
        "Pin Title":p.PIN_TITLE,"Pin Description":p.PIN_DESC,"Destination URL":p.DEST,
        "Status":"ONE_TIME_POSTING","QA Verified (YES/NO)":"INTERNAL_TESTS_PASS",
        "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1",
        "QA Version":"KGS018-INTERNAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    try:
        photo=p.EVIDENCE/"Q63_ScopePulse_Original_Pin.png"
        url=a.cloudinary_upload(photo.read_bytes(),"kgs018-q63-original-one-time")
        a.require(str(url).startswith("https://"),"Image host unavailable")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
           ... on PostActionSuccess{post{id status externalLink}}
           ... on MutationError{message}}}'''
        body={"channelId":b.channel_id,"text":p.PIN_DESC,
            "schedulingType":"automatic","mode":"shareNow","aiAssisted":False,
            "assets":[{"image":{"url":url}}],
            "metadata":{"pinterest":{"boardServiceId":boards[board],
                "title":p.PIN_TITLE,"url":p.DEST}}}
        p.note("ONE_TIME_BUFFER_SUBMISSION_ATTEMPT")
        response=b.graphql(query,{"input":body}).get("createPost") or {}
        post=response.get("post") or {}
        bid=str(post.get("id") or "")
        a.require(bid,"No Buffer post ID, no duplicate attempt")
        s.patch("Publishing Queue",pin,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        p.note("BUFFER_ID_VERIFIED",buffer_id=bid)
        link=str(post.get("externalLink") or "")
        for i in range(6):
            if "pinterest.com/pin/" in link:break
            if i:time.sleep(4)
            link=str(b.get_post(bid).get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            s.patch("Publishing Queue",pin,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            p.note("PINTEREST_PUBLIC_LINK_VERIFIED",pin_url=link)
            print("Q63_PUBLIC_PIN "+link,flush=True)
        else:
            p.note("PINTEREST_PROVIDER_PENDING",buffer_id=bid)
            print("Q63_BUFFER_SUBMITTED_PIN_URL_PENDING "+bid,flush=True)
    except Exception as e:
        current=p.single(s,"Publishing Queue","Queue ID",p.QID)
        if current.get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",current,{"Status":"REVIEW","Last Error":str(e)[:400]})
        p.note("PINTEREST_UNCERTAIN_DO_NOT_RETRY",error_type=type(e).__name__)
        raise

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("KGS018_EXISTING_DRAFT_SAFE_STOP",type(exc).__name__,str(exc)[:250],flush=True)
        sys.exit(1)
