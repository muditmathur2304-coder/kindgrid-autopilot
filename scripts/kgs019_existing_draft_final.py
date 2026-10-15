"""Finish ONLY uniquely reconciled KGS-019 draft, then send ONLY Q64 original Pin.
No seller create/duplicate file upload or repeated Buffer requests. Expected exact source
customer ZIP 16095 bytes recorded by original attempt run 38693332551.
"""
import sys,time,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image
from src import autopilot as a
from scripts import kgs019_movemargin_assets as m
from scripts import kgs019_movemargin_once as p
from scripts.kgs017_depositguard_once import cap_used

SID="V7A9JLJTZsBgHtNIsDkUwQ=="
FILE_ID="QnsoybwjJWC6LCZ8QEJJWw=="
FILE_SIZE=16095
PIN_SHA=p.PIN_SHA
COVER_SHA=p.COVER_SHA
EDITOR="https://gumroad.com/products/"+SID+"/edit"
PROOF="https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions/runs/38693332551"

def check_seller():
    seller=a.gumroad_cli(["products","list","--all"]).get("products") or []
    matches=p.find_seller()
    a.require([str(v.get("id") or "") for v in matches]==[SID],
              "Seller product identity/slug duplicate or missing")
    product=p.assert_supplier_files(SID,FILE_SIZE)
    files=product.get("files") or product.get("rich_content_files") or []
    a.require(str(files[0].get("id") or "")==FILE_ID,
              "Existing customer-download file ID changed")
    return product

def main():
    a.require(a.enabled("KGS019_OWNER_EXISTING_FINAL"),"Owner final launch not enabled")
    m.run()
    img=m.OUT/"Q64_MoveMargin_Original_2x3.png"
    cover=m.OUT/"KGS019_Gumroad_Cover.png"
    a.require(hashlib.sha256(img.read_bytes()).hexdigest()==PIN_SHA,
              "Pinned QA-reviewed Pin image hash changed")
    a.require(hashlib.sha256(cover.read_bytes()).hexdigest()==COVER_SHA,
              "Pinned QA-reviewed cover hash changed")
    a.require(Image.open(img).size==(1000,1500),"Pin dimensions changed")
    s=a.GoogleStore()
    row=p.single(s,"Gumroad Upload Queue","Product ID",m.PID)
    a.require(row.get("Upload Status")=="REVIEW" and row.get("Unique Slug")==m.SLUG
        and row.get("Product Name")==m.NAME and row.get("Price USD")==m.PRICE
        and int(row.get("Attempt Count") or "0")==1
        and not row.get("Gumroad Live URL"),"KGS019 not the uniquely reconciled held draft")
    a.verify_qa_report(s,row,m.PID)
    pins=s.get_rows("Publishing Queue")
    a.require(not any(q.get("Queue ID")==m.QID or str(q.get("Destination URL","")).startswith(m.PUBLIC)
                      for q in pins),"Q64 or this destination already exists in queue")
    a.require(cap_used(s.get_rows("Gumroad Upload Queue"),"Upload Status","Last Updated UTC")<7,
              "Owner's US day Gumroad cap reached")
    a.require(cap_used(pins,"Status","Last Attempt UTC")<7,"US day Pinterest cap reached")
    existing=check_seller()
    a.require(existing.get("published") is False,"Seller already published, no blind duplicate")
    # The original exact source builder generated 16095 bytes. Later rebuild differed by 2 bytes
    # because PDF metadata / ZIP compression timestamps vary; never replace original seller file.
    p.receipt("EXISTING_DRAFT_FILE_ID_SIZE_EMBED_COVER_VERIFIED",
        original_release_run=PROOF,seller_id=SID,buyer_file_id=FILE_ID,buyer_file_bytes=FILE_SIZE)
    buffer=a.BufferClient();boards=buffer.boards()
    a.require(p.BOARD in boards,"Appropriate budgeting board unavailable")
    a.require(buffer.scheduled()<10,"Free Buffer channel has no remaining capacity")
    s.patch("Gumroad Upload Queue",row,{"Upload Status":"EXISTING_DRAFT_PUBLISHING",
       "Gumroad Live URL":EDITOR,"Last Attempt UTC":a.make_timestamp(),"Attempt Count":"2",
       "Last Error":""})
    p.receipt("SINGLE_EXISTING_PRODUCT_PUBLICATION_ATTEMPT",seller_id=SID)
    try:
        try:
            a.gumroad_cli(["products","publish",SID])
        except Exception as error:
            p.receipt("GUMROAD_PUBLISH_RESPONSE_UNCERTAIN_READBACK_ONLY",error_type=type(error).__name__)
        live=check_seller()
        a.require(live.get("published") is True,"Original Gumroad product not confirmed published")
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL",
           "Gumroad Live URL":m.PUBLIC})
        a.verify_public_product_url(m.PUBLIC,m.SLUG)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
            "Gumroad Live URL":m.PUBLIC,"Last Updated UTC":a.make_timestamp(),"Last Error":""})
        p.receipt("GUMROAD_PUBLIC_SINGLE_CUSTOMER_ZIP_VERIFIED",product_url=m.PUBLIC)
        print("KGS019_GUMROAD_LIVE "+m.PUBLIC,flush=True)
    except Exception as error:
        current=p.single(s,"Gumroad Upload Queue","Product ID",m.PID)
        if current.get("Upload Status")=="EXISTING_DRAFT_PUBLISHING":
            s.patch("Gumroad Upload Queue",current,{"Upload Status":"REVIEW","Last Error":str(error)[:410]})
        p.receipt("SELLER_PUBLICATION_NEEDS_RECONCILIATION_NO_RETRY",error_type=type(error).__name__)
        raise
    now=a.make_timestamp()
    pinrow=p.append(s,"Publishing Queue",{
        "Queue ID":m.QID,"Product":m.PID,
        "Content Type":"Original illustrated two-scenario household moving-budget infographic",
        "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "Time Window":"Owner-approved immediate Pinterest post","US Scheduled Time":"NOW",
        "Target Board":p.BOARD,"Pin Title":m.TITLE,"Pin Description":m.DESC_PIN,
        "Destination URL":m.DEST,"Status":"ONE_TIME_POSTING",
        "QA Verified (YES/NO)":"YES","Last Attempt UTC":now,"Attempt Count":"1",
        "QA Version":"KGS-QA-V2","QA Report Drive Link":p.QQA,"QA Audited UTC":now,
        "QA Outcome":"PASS"},"Queue ID")
    a.verify_qa_report(s,pinrow,m.QID)
    try:
        hosted=a.cloudinary_upload(img.read_bytes(),"kgs019-q64-original-20261015")
        a.require(str(hosted).startswith("https://"),"Pin hosting URL invalid")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
          ... on PostActionSuccess{post{id status externalLink}}
          ... on MutationError{message}}}'''
        body={"channelId":buffer.channel_id,"text":m.DESC_PIN,
            "schedulingType":"automatic","mode":"shareNow","aiAssisted":False,
            "assets":[{"image":{"url":hosted}}],
            "metadata":{"pinterest":{"boardServiceId":boards[p.BOARD],
                "title":m.TITLE,"url":m.DEST}}}
        p.receipt("ONE_TIME_Q64_BUFFER_SUBMISSION_ATTEMPTED")
        response=buffer.graphql(query,{"input":body}).get("createPost") or {}
        post=response.get("post") or {};bid=str(post.get("id") or "")
        a.require(bool(bid),"Buffer request may have succeeded but provider ID absent: hold")
        s.patch("Publishing Queue",pinrow,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        p.receipt("Q64_BUFFER_ID_VERIFIED",buffer_id=bid)
        link=str(post.get("externalLink") or "")
        for j in range(7):
            if "pinterest.com/pin/" in link:break
            if j:time.sleep(5)
            link=str(buffer.get_post(bid).get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            s.patch("Publishing Queue",pinrow,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            p.receipt("PINTEREST_PUBLIC_PIN_VERIFIED",public_pin=link)
            print("Q64_PINTEREST_LIVE "+link,flush=True)
        else:
            p.receipt("PINTEREST_PROVIDER_ACCEPTED_URL_PENDING",buffer_id=bid)
            print("Q64_PROVIDER_ACCEPTED_PENDING_PUBLIC_LINK "+bid,flush=True)
    except Exception as error:
        current=p.single(s,"Publishing Queue","Queue ID",m.QID)
        if current.get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",current,{"Status":"REVIEW",
                "Last Error":(type(error).__name__+": "+str(error))[:410]})
        p.receipt("Q64_PIN_UNCERTAIN_NO_DUPLICATE_RETRY",error_type=type(error).__name__)
        raise
if __name__=="__main__":
    try:main()
    except Exception as error:
        print("KGS019_SAFE_FINAL_STOP "+type(error).__name__+" "+str(error)[:240],flush=True)
        sys.exit(1)
