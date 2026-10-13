"""One-time free Q-56 Buffer share-now; ONLY after Gumroad's two files are verified live."""
import io
from PIL import Image
from src import autopilot as a
CODE="KGS-011"
PIN="Q-56"
SLUG="bakeslot-free-one-order-quote-check"
URL="https://kindgridstudio.gumroad.com/l/"+SLUG

def one(s,tab,col,val):
    items=[r for r in s.get_rows(tab) if r.get(col)==val]
    a.require(len(items)==1,"Item identity mismatch: "+val)
    return items[0]

def main():
    a.require(a.enabled("LIVE_MODE") and a.enabled("BAKESLOT_FREE_OWNER_RELEASE"),"Owner release disabled")
    s=a.GoogleStore()
    prod=one(s,"Gumroad Upload Queue","Product ID",CODE)
    a.require(prod.get("Upload Status")=="PUBLISHED" and prod.get("Gumroad Live URL")==URL,"FREE product is not confirmed public")
    a.verify_public_product_url(URL,SLUG)
    row=one(s,"Publishing Queue","Queue ID",PIN)
    if row.get("Status") in ("PUBLISHED","SENT_PENDING_URL","SCHEDULED_BUFFER"):
        print("PIN_ALREADY_SENT "+row["Status"]);return
    a.require(row.get("Status")=="PRODUCT_RELEASE_PENDING","Do not retry an uncertain Pin")
    a.require(row.get("Product")==CODE and row.get("QA Verified (YES/NO)")=="YES","Wrong Pin identity")
    a.verify_qa_report(s,row,PIN)
    a.require(row.get("Destination URL","").startswith(URL+"?utm_source=pinterest"),"Pin must link to real free checkout")
    a.require(0<len(row["Pin Title"])<=100 and 100<=len(row["Pin Description"])<=500,"Bad Pinterest metadata")
    client=a.BufferClient(); boards=client.boards()
    board=row.get("Target Board"); a.require(board in boards,"Board unavailable")
    a.require(client.scheduled()<10,"Buffer queue is full")
    raw=s.get_bytes(a.google_file_id(row["Pin Image Drive Link"]),"image/png")
    a.validate_image(raw)
    s.patch("Publishing Queue",row,{"Status":"ONE_TIME_POSTING","Attempt Count":str(int(row.get("Attempt Count") or 0)+1),"Last Attempt UTC":a.make_timestamp()})
    try:
        imgurl=a.cloudinary_upload(raw,"q56")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
          ... on PostActionSuccess{post{id status externalLink}}
          ... on MutationError{message}}}'''
        body={"channelId":client.channel_id,"text":row["Pin Description"],"schedulingType":"automatic","mode":"shareNow","aiAssisted":True,
              "assets":[{"image":{"url":imgurl}}],
              "metadata":{"pinterest":{"boardServiceId":boards[board],"title":row["Pin Title"],"url":row["Destination URL"]}}}
        resp=client.graphql(query,{"input":body}).get("createPost") or {}
        post=resp.get("post") or {}
        ident=str(post.get("id") or "")
        a.require(bool(ident),"Buffer pin was not confirmed; do not retry: "+str(resp.get("message") or "no ID"))
        s.patch("Publishing Queue",row,{"Status":"SENT_PENDING_URL","Batch ID":ident,"Last Error":""})
        found=client.get_post(ident)
        link=str(found.get("externalLink") or (found.get("metadata") or {}).get("url") or "").strip()
        if link.startswith("https://") and ("pinterest.com/pin/" in link or "pin.it/" in link):
            s.patch("Publishing Queue",row,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            print("PINTEREST_PUBLISHED_VERIFIED "+link)
        else:print("PINTEREST_SUBMITTED "+ident+" public permalink pending")
    except Exception as e:
        current=one(s,"Publishing Queue","Queue ID",PIN)
        if current.get("Status")=="ONE_TIME_POSTING":s.patch("Publishing Queue",current,{"Status":"REVIEW","Last Error":(type(e).__name__+": "+str(e))[:420]})
        raise

if __name__=="__main__":
    main()
