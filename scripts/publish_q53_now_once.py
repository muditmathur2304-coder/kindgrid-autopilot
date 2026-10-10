"""Immediate one-time Pinterest Pin Q-53. Owner requested ONE post NOW, not scheduling.
No duplicate submission, no changes to existing Pins. Buffer shareNow delivers automatically.
"""
from __future__ import annotations
import os,sys,time,json
from urllib.parse import urlparse
from src import autopilot as a

PIN="Q-53"
PRODUCT="KGS-007"
LINK="https://kindgridstudio.gumroad.com/l/paycheck-gap-starter"
BOARD="Budgeting Printables & Cash Stuffing"
IMAGE_ID="1069EqbMEPYfB3fc2zUEMZKYvRHwrmXGY"
EXPECTED_IMG="https://drive.google.com/file/d/"+IMAGE_ID+"/view"

def verified_pin(link):
    p=urlparse(str(link))
    return (p.scheme=="https" and p.netloc.lower() in
            ("www.pinterest.com","pinterest.com","pin.it") and
            (p.path.startswith("/pin/") or p.netloc.lower()=="pin.it"))

def status_update(store,row,**changes):
    store.patch("Publishing Queue",row,changes)

def main():
    a.require(os.getenv("KINDGRID_Q53_IMMEDIATE_OWNER_APPROVAL")=="true",
              "Explicit owner authorization absent")
    store=a.GoogleStore()
    found=[r for r in store.get_rows("Publishing Queue") if r.get("Queue ID")==PIN]
    a.require(len(found)==1,"Q53 missing or duplicated")
    row=found[0]
    a.require(row.get("Status")=="READY","Q53 has already been attempted; never resend")
    a.require(not row.get("Batch ID") and not row.get("Actual Pinterest Pin URL"),
              "Existing Buffer/Pinterest ID; never duplicate")
    a.require(row.get("Product")==PRODUCT and row.get("Destination URL")==LINK,
              "Unexpected product destination")
    a.require(row.get("Pin Image Drive Link")==EXPECTED_IMG,
              "Artwork changed since final QA")
    a.require(row.get("Target Board")==BOARD,
              "Unexpected Pinterest board")
    a.require(row.get("QA Verified (YES/NO)")=="YES" and
              row.get("QA Outcome")=="PASS","Q53 does not have QA PASS")
    a.verify_qa_report(store,row,PIN)
    a.validate_destination(LINK)
    a.require(len(row.get("Pin Title",""))<=100 and
              len(row.get("Pin Description",""))<=500,
              "Pinterest title/description character limit")

    prods=[p for p in store.get_rows("Gumroad Upload Queue")
           if p.get("Product ID")==PRODUCT]
    a.require(len(prods)==1 and
              prods[0].get("Upload Status")=="PUBLISHED" and
              prods[0].get("Gumroad Live URL")==LINK,
              "Free landing page is not confirmed published")
    a.verify_public_product_url(LINK,"paycheck-gap-starter")
    img=store.get_bytes(IMAGE_ID,"image/png")
    a.require(a.validate_image(img)==(1000,1500),"Invalid approved creative dimensions")

    client=a.BufferClient()
    boards=client.boards()
    a.require(BOARD in boards,"Target board not found")
    count=client.scheduled()
    print("PREFLIGHT_OK Q53 original image / live free product / Pinterest board. Previously queued:",count)

    # Media hosting must be complete before an irreversible Buffer post submission.
    hosted=a.cloudinary_upload(img,"q53-kindgrid-income-floor-20261010-once")
    a.require(hosted.startswith("https://res.cloudinary.com/"),
              "Could not verify uploaded hosted creative")
    status_update(store,row,Status="SUBMITTING",
                  **{"Last Error":"ONE immediate Buffer submission in progress: never auto-retry",
                     "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
    print("Q53_BUFFER_SHARE_NOW_ATTEMPTED_DO_NOT_RETRY",flush=True)
    mutation='''mutation PublishNow($input:CreatePostInput!) {
       createPost(input:$input) {
         ... on PostActionSuccess {
           post{id status externalLink metadata{
             ... on PinterestPostMetadata {title url board{serviceId}}}}
         }
         ... on MutationError {message}
       }
    }'''
    body={
        "channelId":client.channel_id,
        "text":row["Pin Description"],
        "schedulingType":"automatic",
        "mode":"shareNow",
        "aiAssisted":True,
        "assets":[{"image":{"url":hosted}}],
        "metadata":{"pinterest":{
          "boardServiceId":boards[BOARD],
          "title":row["Pin Title"],
          "url":LINK
        }}
    }
    try:
        answer=(client.graphql(mutation,{"input":body}).get("createPost") or {})
    except Exception as exc:
        status_update(store,row,Status="LINK_REVIEW",
                      **{"Last Error":"Buffer create outcome uncertain ("+type(exc).__name__+
                         "); MUST reconcile seller before retry"})
        raise
    post=answer.get("post") or {}
    pid=str(post.get("id") or "")
    if not pid:
        status_update(store,row,Status="LINK_REVIEW",
                      **{"Last Error":"Buffer submission response uncertain: "+
                         str(answer.get("message") or "no post id")[:180]+
                         "; no retry"})
        raise RuntimeError("Buffer did not confirm a unique new post; no retry")
    url=str((post.get("metadata") or {}).get("url") or "")
    if url!=LINK:
        status_update(store,row,Status="LINK_REVIEW",
                      **{"Batch ID":pid,
                         "Last Error":"Returned product destination mismatch, reconcile without retry"})
        raise RuntimeError("Buffer post created but unexpected destination")
    status_update(store,row,Status="SUBMITTED_PENDING",
                  **{"Batch ID":pid,"Last Error":"Immediate post accepted by Buffer; awaiting Pinterest sent/URL verification"})
    print("Q53_BUFFER_ACCEPTED "+json.dumps({"id":pid,"mode":"shareNow",
                                           "initial_status":post.get("status")}),flush=True)

    # 'shareNow' may be asynchronous. Never claim publication on mere accepted status.
    for attempt in range(10):
        try:
            snap=client.get_post(pid)
            a.require(str(snap.get("id") or "")==pid,"Readback ID mismatch")
            outcome=str(snap.get("status") or "").lower()
            target=str((snap.get("metadata") or {}).get("url") or "")
            public=str(snap.get("externalLink") or "")
            a.require(target==LINK,"Published post destination changed")
            print("Q53_POLL "+json.dumps({"attempt":attempt+1,"status":outcome,
                                          "has_public_url":bool(public)}),flush=True)
            if outcome=="sent" and verified_pin(public):
                status_update(store,row,Status="PUBLISHED",
                              **{"Actual Pinterest Pin URL":public,
                                 "Last Error":"","Last Attempt UTC":a.make_timestamp()})
                print("Q53_PINTEREST_PUBLISHED_VERIFIED "+public,flush=True)
                return 0
            if outcome in ("error","failed"):
                status_update(store,row,Status="LINK_REVIEW",
                              **{"Last Error":"Buffer post returned "+outcome+
                                 "; exact ID recorded, do not retry"})
                raise RuntimeError("Buffer reporting failed, not a published Pin")
        except RuntimeError:
            raise
        except Exception as exc:
            print("Q53_TRANSIENT_READBACK_ERROR "+type(exc).__name__,flush=True)
        time.sleep(8)
    status_update(store,row,Status="SUBMITTED_PENDING",
                  **{"Last Error":"Buffer shareNow accepted; Pinterest external URL not confirmed yet. Reconcile Buffer post ID; do not repost."})
    print("Q53_SUBMITTED_NOW_AWAITING_DELIVERY "+pid,flush=True)
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("Q53_ONE_OFF_HALTED_NO_RETRY "+type(exc).__name__+": "+str(exc)[:230],flush=True)
        sys.exit(1)
