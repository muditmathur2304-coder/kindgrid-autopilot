"""Owner-requested one-time Q-55 immediate Pinterest post; only after confirmed KGS-010 listing."""
import io
from PIL import Image
from src import autopilot as a

def portrait(data):
    with Image.open(io.BytesIO(data)) as im:
        im=im.convert("RGB")
        im.thumbnail((1000,1470),Image.Resampling.LANCZOS)
        dest=Image.new("RGB",(1000,1500),(250,247,241))
        dest.paste(im,((1000-im.width)//2,(1500-im.height)//2))
        out=io.BytesIO()
        dest.save(out,"PNG",optimize=True)
    b=out.getvalue()
    a.validate_image(b)
    return b

def main():
    a.require(a.enabled("LIVE_MODE") and a.enabled("BAKESLOT_OWNER_RELEASE"),"Owner release disabled")
    s=a.GoogleStore()
    rr=[r for r in s.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-010"]
    a.require(len(rr)==1 and rr[0].get("Upload Status")=="PUBLISHED","Paid customer files must be published first")
    url=rr[0].get("Gumroad Live URL")
    a.require(url=="https://kindgridstudio.gumroad.com/l/bakeslot-order-capacity-studio","Wrong paid destination")
    a.verify_public_product_url(url,"bakeslot-order-capacity-studio")
    pins=[r for r in s.get_rows("Publishing Queue") if r.get("Queue ID")=="Q-55"]
    a.require(len(pins)==1,"Q-55 queue identity error")
    pin=pins[0]
    if pin.get("Status") in ("PUBLISHED","SCHEDULED_BUFFER","SENT_PENDING_URL"):
        print("PIN_ALREADY_SENT "+pin["Status"])
        return
    a.require(pin.get("Status")=="PRODUCT_RELEASE_PENDING","Pin already attempted or held: no retries")
    a.require(pin.get("Product")=="KGS-010" and pin.get("QA Verified (YES/NO)")=="YES","Pin product/QA mismatch")
    a.require(str(pin.get("Destination URL") or "").startswith(url+"?utm_source=pinterest"),"Pin URL not verified brand destination")
    a.require(0<len(pin["Pin Title"])<=100 and 100<=len(pin["Pin Description"])<=500,"Pinterest copy invalid")
    client=a.BufferClient()
    boards=client.boards()
    board=pin.get("Target Board")
    a.require(board in boards,"Pinterest board not connected")
    a.require(client.scheduled()<10,"Buffer free queue full")
    image=portrait(s.get_bytes(a.google_file_id(pin["Pin Image Drive Link"]),"image/png"))
    # This single owner-approved immediate action explicitly uses Buffer's shareNow mode;
    # no scheduled queue entry is accidentally presented as a public Pin.
    s.patch("Publishing Queue",pin,{"Status":"ONE_TIME_POSTING","Attempt Count":str(int(pin.get("Attempt Count") or 0)+1),"Last Attempt UTC":a.make_timestamp()})
    try:
        uri=a.cloudinary_upload(image,"q55")
        mutation='''mutation P($input:CreatePostInput!){createPost(input:$input){
           ... on PostActionSuccess{post{id status externalLink}}
           ... on MutationError{message}}}'''
        body={"channelId":client.channel_id,"text":pin["Pin Description"],"schedulingType":"automatic","mode":"shareNow",
              "aiAssisted":True,"assets":[{"image":{"url":uri}}],
              "metadata":{"pinterest":{"boardServiceId":boards[board],"title":pin["Pin Title"],"url":pin["Destination URL"]}}}
        reply=client.graphql(mutation,{"input":body}).get("createPost") or {}
        post=reply.get("post") or {}
        post_id=str(post.get("id") or "").strip()
        a.require(bool(post_id),"Buffer rejected/uncertain Q-55: "+str(reply.get("message") or "No ID"))
        s.patch("Publishing Queue",pin,{"Batch ID":post_id,"Status":"SENT_PENDING_URL","Last Error":""})
        snap=client.get_post(post_id)
        permalink=str(snap.get("externalLink") or (snap.get("metadata") or {}).get("url") or "").strip()
        if permalink.startswith("https://") and ("pinterest.com/pin/" in permalink or "pin.it/" in permalink):
            s.patch("Publishing Queue",pin,{"Actual Pinterest Pin URL":permalink,"Status":"PUBLISHED","Last Error":""})
            print("PINTEREST_PUBLISHED_VERIFIED "+permalink)
        else:
            state=str(snap.get("status") or post.get("status") or "").lower()
            actual="SCHEDULED_BUFFER" if state=="scheduled" else "SENT_PENDING_URL"
            s.patch("Publishing Queue",pin,{"Status":actual})
            print("PINTEREST_SUBMITTED "+post_id+" state="+actual+" (public permalink pending)")
    except Exception as e:
        latest=[r for r in s.get_rows("Publishing Queue") if r.get("Queue ID")=="Q-55"][0]
        if latest.get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",latest,{"Status":"REVIEW","Last Error":(type(e).__name__+": "+str(e))[:400]})
        raise

if __name__=="__main__":
    main()
