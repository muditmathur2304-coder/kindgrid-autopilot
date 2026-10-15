"""Owner-authorized one-time KGS019/Q64 original product plus Pin.
Never retry uncertain seller or Buffer action; require seller customer file and Pin public URL.
"""
from __future__ import annotations
import os,sys,time,hashlib,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image
from src import autopilot as a
from scripts import kgs019_movemargin_assets as m
from scripts.kgs017_depositguard_once import cap_used

PQA="https://docs.google.com/document/d/1puAyumGa-cwfGm1-uLpSBtyi2XrsUsXlY9Mu94ZL124/edit"
QQA="https://docs.google.com/document/d/1aFjUDKO6HpADRC9ECYg3WhZhFYdxq6RAnKugx9dp7A8/edit"
PIN_SHA="51171ad8f4ccb6d2901603ca45ca228a3be3cbacc18c02c7f47a3797a05fde81"
COVER_SHA="73747471484d070c8a026138f496d17ae1ebdbc6a458f64be42d105416a66fd6"
BOARD="Budgeting Printables & Cash Stuffing"

def receipt(step,**kw):
    m.OUT.mkdir(exist_ok=True,parents=True)
    p=m.OUT/"KGS019_RELEASE_RECEIPT.json"
    try: state=json.loads(p.read_text()) if p.exists() else {}
    except Exception:state={}
    state.update(kw);state["step"]=step;state["utc"]=a.make_timestamp()
    p.write_text(json.dumps(state,indent=2),encoding="utf-8")
    print("KGS019_RELEASE "+step,flush=True)

def single(s,tab,key,value):
    rows=[x for x in s.get_rows(tab) if x.get(key)==value]
    a.require(len(rows)==1,"Expected single "+value+" row on "+tab)
    return rows[0]

def append(s,tab,record,ref_key):
    api=s.sheet.spreadsheets().values()
    header=api.get(spreadsheetId=a.SHEET_ID,range="'"+tab+"'!1:1").execute()["values"][0]
    a.require(set(record)<=set(header),"Unexpected queue column "+str(set(record)-set(header)))
    api.append(spreadsheetId=a.SHEET_ID,range="'"+tab+"'!A1",
        valueInputOption="RAW",insertDataOption="INSERT_ROWS",
        body={"values":[[str(record.get(k,"")) for k in header]]}).execute()
    return single(s,tab,ref_key,record[ref_key])

def find_seller():
    items=a.gumroad_cli(["products","list","--all"]).get("products") or []
    out=[]
    for p in items:
        slug=str(p.get("custom_permalink") or "")
        tail=str(p.get("short_url") or "").split("?")[0].rstrip("/").split("/")[-1]
        if m.SLUG in (slug,tail):out.append(p)
    return out

def assert_supplier_files(seller_id,zip_bytes):
    p=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
    a.require(p.get("name")==m.NAME and p.get("custom_permalink")==m.SLUG,
              "Seller identity does not match requested unique product")
    files=p.get("files") or p.get("rich_content_files") or []
    covers=p.get("covers") or p.get("cover_images") or []
    a.require(len(files)==1 and int(files[0].get("size") or -1)==zip_bytes,
              "Exactly one downloadable buyer ZIP of verified source size is required")
    a.require(len(covers)>=1,"Original seller cover missing")
    rich=a.gumroad_cli(["products","content","get",seller_id])
    pages=rich if isinstance(rich,list) else rich.get("rich_content",[]) if isinstance(rich,dict) else []
    embeds=[str(n.get("attrs",{}).get("id") or "") for part in pages
            for n in (part.get("description") or {}).get("content") or []
            if n.get("type")=="fileEmbed"]
    a.require(embeds==[str(files[0].get("id") or "")],"Customer delivery ZIP embed not confirmed")
    return p

def main():
    a.require(a.enabled("KGS019_OWNER_ONE_TIME_RELEASE"),"Owner release switch off")
    m.run()
    pin=m.OUT/"Q64_MoveMargin_Original_2x3.png"
    cover=m.OUT/"KGS019_Gumroad_Cover.png"
    archive=m.OUT/"MoveMargin_Customer_Download.zip"
    a.require(hashlib.sha256(pin.read_bytes()).hexdigest()==PIN_SHA,
              "Inspected Pin image has changed since visual QA")
    a.require(hashlib.sha256(cover.read_bytes()).hexdigest()==COVER_SHA,
              "Inspected storefront cover has changed since visual QA")
    a.require(Image.open(pin).size==(1000,1500) and Image.open(cover).size==(1600,900),
              "Image dimensions do not match QA")
    a.require(archive.stat().st_size>=15000,"Customer ZIP suspiciously small")
    s=a.GoogleStore()
    products=s.get_rows("Gumroad Upload Queue")
    pins=s.get_rows("Publishing Queue")
    a.require(not any(x.get("Product ID")==m.PID or x.get("Unique Slug")==m.SLUG for x in products),
              "Existing KGS019 row or slug: no duplicate")
    a.require(not any(x.get("Queue ID")==m.QID or str(x.get("Destination URL","")).startswith(m.PUBLIC) for x in pins),
              "Q64 or matching destination already in queue; no duplicate")
    a.require(cap_used(products,"Upload Status","Last Updated UTC")<7,
              "US-day Gumroad listing limit reached")
    a.require(cap_used(pins,"Status","Last Attempt UTC")<7,
              "US-day Pinterest publishing limit reached")
    a.require(len(find_seller())==0,"Gumroad seller already contains this slug")
    b=a.BufferClient();boards=b.boards()
    a.require(BOARD in boards,"Relevant existing Pinterest board not accessible")
    a.require(b.scheduled()<10,"Buffer Free ten queued limit reached")
    receipt("EXTERNAL_PREFLIGHT_PASS",buffer_board=BOARD,existing_seller_slug_count=0)
    ts=a.make_timestamp()
    row=append(s,"Gumroad Upload Queue",{
      "Product ID":m.PID,"Product Name":m.NAME,"Price USD":m.PRICE,"Unique Slug":m.SLUG,
      "QA Verified (YES/NO)":"YES","Upload Status":"OWNER_ONETIME_CREATING",
      "Last Attempt UTC":ts,"Attempt Count":"1","Last Updated UTC":ts,
      "QA Version":"KGS-QA-V2","QA Report Drive Link":PQA,"QA Audited UTC":ts,
      "QA Outcome":"PASS","Pair Role":"PAID"},"Product ID")
    a.verify_qa_report(s,row,m.PID)
    receipt("PRODUCT_QA_V2_REPORT_VERIFIED")
    # Gumroad CLI may report error after it has ALREADY created exact seller draft.
    # Even in error case, read seller state and NEVER submit another create.
    seller_id=""
    receipt("GUMROAD_CREATE_ATTEMPTED_ONCE_NO_RETRY")
    try:
        try:
            resp=a.gumroad_cli(["products","create","--draft",
                "--name",m.NAME,"--price",m.PRICE,"--currency","usd",
                "--type","digital","--custom-permalink",m.SLUG,
                "--description",m.DESCRIPTION,"--custom-summary",m.SUMMARY,
                "--file",str(archive),"--cover-image",str(cover),"--thumbnail",str(cover),
                "--preview-image",str(m.OUT/"KGS019_Gallery_Real_Cash_Need.png"),
                "--preview-image",str(m.OUT/"KGS019_Gallery_Workflow.png")])
            seller_id=str((resp.get("product") or {}).get("id") or "")
        except Exception as err:
            receipt("CREATE_RESPONSE_UNCERTAIN_READBACK_ONLY",error_type=type(err).__name__)
        found=find_seller()
        a.require(len(found)==1,"Cannot prove a unique Gumroad draft after create; no retry")
        ident=str(found[0].get("id") or "")
        a.require(bool(ident) and (not seller_id or ident==seller_id),
                  "Gumroad create returned conflicting product identity")
        seller_id=ident
        draft=assert_supplier_files(seller_id,archive.stat().st_size)
        a.require(draft.get("published") is False,"Gumroad seller product already published unexpectedly")
        receipt("GUMROAD_EXACT_DRAFT_CUSTOMER_FILE_COVER_VERIFIED",
                seller_id=seller_id,zip_bytes=archive.stat().st_size)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
            "Gumroad Live URL":"https://gumroad.com/products/"+seller_id+"/edit"})
    except Exception as err:
        r=single(s,"Gumroad Upload Queue","Product ID",m.PID)
        s.patch("Gumroad Upload Queue",r,{"Upload Status":"REVIEW",
            "Last Error":(type(err).__name__+": "+str(err))[:420],
            "Last Updated UTC":a.make_timestamp()})
        receipt("DRAFT_UNCERTAIN_HOLD_NO_RETRY",seller_id=seller_id,error_type=type(err).__name__)
        raise
    receipt("EXACT_DRAFT_PUBLISH_ATTEMPTED_ONCE",seller_id=seller_id)
    try:
        a.gumroad_cli(["products","publish",seller_id])
        live=assert_supplier_files(seller_id,archive.stat().st_size)
        a.require(live.get("published") is True,"Seller published state not confirmed")
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL","Gumroad Live URL":m.PUBLIC})
        a.verify_public_product_url(m.PUBLIC,m.SLUG)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
           "Gumroad Live URL":m.PUBLIC,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        receipt("GUMROAD_PUBLIC_VERIFIED",public_product=m.PUBLIC)
        print("KGS019_GUMROAD_PUBLIC "+m.PUBLIC,flush=True)
    except Exception as err:
        r=single(s,"Gumroad Upload Queue","Product ID",m.PID)
        if r.get("Upload Status")=="DRAFT_VERIFIED":
            s.patch("Gumroad Upload Queue",r,{"Upload Status":"REVIEW",
                "Last Error":str(err)[:400]})
        receipt("PUBLISH_UNCERTAIN_NO_RETRY",error_type=type(err).__name__)
        raise
    ts=a.make_timestamp()
    pinrow=append(s,"Publishing Queue",{
       "Queue ID":m.QID,"Product":m.PID,
       "Content Type":"Original moving-cost quote infographic, US consumer budgeting",
       "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
       "Time Window":"Owner-approved immediate one-time post",
       "US Scheduled Time":"NOW","Target Board":BOARD,
       "Pin Title":m.TITLE,"Pin Description":m.DESC_PIN,"Destination URL":m.DEST,
       "Status":"ONE_TIME_POSTING","QA Verified (YES/NO)":"YES",
       "Last Attempt UTC":ts,"Attempt Count":"1",
       "QA Version":"KGS-QA-V2","QA Report Drive Link":QQA,
       "QA Audited UTC":ts,"QA Outcome":"PASS"},"Queue ID")
    a.verify_qa_report(s,pinrow,m.QID)
    receipt("PIN_QA_V2_REPORT_VERIFIED")
    try:
        url=a.cloudinary_upload(pin.read_bytes(),"kgs019-q64-movemargin-original-20261015")
        a.require(str(url).startswith("https://"),"Hosted Pin image invalid")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
           ... on PostActionSuccess{post{id status externalLink}}
           ... on MutationError{message}}}'''
        fields={"channelId":b.channel_id,"text":m.DESC_PIN,
            "schedulingType":"automatic","mode":"shareNow","aiAssisted":False,
            "assets":[{"image":{"url":url}}],
            "metadata":{"pinterest":{"boardServiceId":boards[BOARD],
               "title":m.TITLE,"url":m.DEST}}}
        receipt("BUFFER_Q64_CREATE_ATTEMPTED_ONCE")
        resp=b.graphql(query,{"input":fields}).get("createPost") or {}
        obj=resp.get("post") or {};bid=str(obj.get("id") or "")
        a.require(bool(bid),"Buffer result lacks provider ID; no duplicate submission")
        s.patch("Publishing Queue",pinrow,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        receipt("BUFFER_Q64_PROVIDER_ID_VERIFIED",buffer_id=bid)
        link=str(obj.get("externalLink") or "")
        for i in range(6):
            if "pinterest.com/pin/" in link:break
            if i:time.sleep(4)
            link=str(b.get_post(bid).get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            s.patch("Publishing Queue",pinrow,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            receipt("PINTEREST_PUBLIC_PIN_VERIFIED",public_pin=link)
            print("Q64_PINTEREST_PUBLIC "+link,flush=True)
        else:
            receipt("PINTEREST_PROVIDER_ACCEPTED_PUBLIC_LINK_PENDING",buffer_id=bid)
            print("Q64_BUFFER_PENDING_PUBLIC_PIN "+bid,flush=True)
    except Exception as err:
        r=single(s,"Publishing Queue","Queue ID",m.QID)
        if r.get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",r,{"Status":"REVIEW",
                "Last Error":str(err)[:400]})
        receipt("PIN_UNCERTAIN_NO_RESUBMIT",error_type=type(err).__name__)
        raise
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("KGS019_ONE_TIME_SAFE_STOP",type(exc).__name__,str(exc)[:280],flush=True)
        sys.exit(1)
