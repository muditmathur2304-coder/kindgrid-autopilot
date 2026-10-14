"""One-time Q62 Pinterest post only; known KGS017 paid product must already be public."""
from __future__ import annotations
import sys, time, hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image
from src import autopilot as a
from scripts import kgs017_depositguard_once as g

def main():
    s=a.GoogleStore()
    product=[r for r in s.get_rows("Gumroad Upload Queue") if r.get("Product ID")==g.PID]
    a.require(len(product)==1 and product[0].get("Upload Status")=="PUBLISHED"
       and product[0].get("Gumroad Live URL")==g.PUBLIC,"Gumroad product not approved/public")
    a.verify_public_product_url(g.PUBLIC,g.SLUG)
    existing=[r for r in s.get_rows("Publishing Queue") if r.get("Queue ID")==g.QID
              or r.get("Destination URL","").startswith(g.PUBLIC)]
    a.require(not existing,"Q62 or this destination already in Pinterest queue; no duplicate")
    a.require(g.cap_used(s.get_rows("Publishing Queue"),"Status","Last Attempt UTC")<7,"Pinterest daily cap")
    b=a.BufferClient(); boards=b.boards()
    choices=[n for n in boards if any(t in n.lower() for t in
            ("freelanc","business","small business","pricing","finance","budget"))]
    a.require(bool(choices),"No audience-relevant verified Pinterest board")
    choices.sort(key=lambda n:(0 if ("freelanc" in n.lower() or "business" in n.lower()) else 1))
    board=choices[0]
    a.require(b.scheduled()<10,"Buffer Free queue full")
    g.make_assets()
    pin=g.EVIDENCE/"Q62_Pinterest_Original.png"
    a.require(Image.open(pin).size==(1000,1500),"Pin must be original 2:3")
    image_hash=hashlib.sha256(pin.read_bytes()).hexdigest()
    g.receipt("Q62_ORIGINAL_PIN_AND_TARGET_VERIFIED",board=board,sha256=image_hash)
    # Pin row must be established before provider mutation; failing after this does not permit a blind retry.
    header=s.sheet.spreadsheets().values().get(spreadsheetId=a.SHEET_ID,range="'Publishing Queue'!1:1").execute()["values"][0]
    data={"Queue ID":g.QID,"Product":g.PID,"Content Type":"Original educational cashflow infographic",
      "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
      "Time Window":"One-time owner-approved immediate post","US Scheduled Time":"NOW",
      "Target Board":board,"Pin Title":g.TITLE,"Pin Description":g.PIN_DESC,
      "Destination URL":g.DEST,"Status":"ONE_TIME_POSTING",
      "QA Verified (YES/NO)":"INTERNAL_CHECKS_ONLY","Last Attempt UTC":a.make_timestamp(),
      "Attempt Count":"1","QA Version":"KGS017-LOCAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"}
    s.sheet.spreadsheets().values().append(spreadsheetId=a.SHEET_ID,
      range="'Publishing Queue'!A1",valueInputOption="RAW",insertDataOption="INSERT_ROWS",
      body={"values":[[str(data.get(k,"")) for k in header]]}).execute()
    found=[r for r in s.get_rows("Publishing Queue") if r.get("Queue ID")==g.QID]
    a.require(len(found)==1,"Unknown Pin queue persistence after append; stop")
    row=found[0]
    image=a.cloudinary_upload(pin.read_bytes(),"kgs017-q62-original-verified-20261014")
    a.require(image.startswith("https://"),"Pin image host URL invalid")
    query='''mutation P($input:CreatePostInput!){createPost(input:$input){
      ... on PostActionSuccess{post{id status externalLink}}
      ... on MutationError{message}}}'''
    body={"channelId":b.channel_id,"text":g.PIN_DESC,"schedulingType":"automatic",
      "mode":"shareNow","aiAssisted":False,"assets":[{"image":{"url":image}}],
      "metadata":{"pinterest":{"boardServiceId":boards[board],
          "title":g.TITLE,"url":g.DEST}}}
    g.receipt("Q62_BUFFER_CREATE_ATTEMPTED_ONCE")
    try:
        result=b.graphql(query,{"input":body}).get("createPost") or {}
        obj=result.get("post") or {};bid=str(obj.get("id") or "")
        a.require(bid,"No Buffer ID: hold until actual provider check")
        s.patch("Publishing Queue",row,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        g.receipt("Q62_BUFFER_POST_ID_VERIFIED",buffer_id=bid)
        link=str(obj.get("externalLink") or "")
        for i in range(6):
            if "pinterest.com/pin/" in link:break
            if i:time.sleep(4)
            link=str(b.get_post(bid).get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            s.patch("Publishing Queue",row,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            g.receipt("Q62_LIVE_PIN",pin_url=link)
            print("KGS017_Q62_PUBLIC_PIN "+link)
        else:
            g.receipt("Q62_BUFFER_POST_SENT_PIN_LINK_PENDING",buffer_id=bid)
            print("KGS017_Q62_PENDING_PROVIDER "+bid)
    except Exception as e:
        latest=[x for x in s.get_rows("Publishing Queue") if x.get("Queue ID")==g.QID]
        if len(latest)==1 and latest[0].get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",latest[0],{"Status":"REVIEW",
                "Last Error":(type(e).__name__+": "+str(e))[:420]})
        raise

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("Q62_ONE_TIME_SAFE_STOP",type(e).__name__,str(e)[:240],flush=True);sys.exit(1)
