"""One-time owner-requested KindGrid artist quote PAID+FREE release and one Pinterest Pin.

Permission-only rerun: prior run stopped before seller mutation (paid listing Doc HTTP 403); both listing Docs have now been shared as reader to the publisher service account.

Never rerun after any seller write; the receipts and seller state must be reconciled.
"""
from __future__ import annotations
import json, os, sys, tempfile, io
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zipfile import ZipFile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

OUT=Path("kindgrid-art-pair-proof")
PRODUCTS=[
 dict(id="KGS-015",slug="commission-ready-artist-playbook",title="Commission Ready — Art Quote & Scope System | 24-Page Guide + Excel",price="12.00",
 pdf="1V6i_v-ndYpN8Rl5cKSFYhHvYLMEy3g3W",cover="1KtoAmBglb93u8c2dUeXJxVSbERPTbx_2",
 listing="1XRebz-gV11Rhkjnqu8yULeHYSYyHw3Dw3w0WCmr5xk4",bonus="1jySGib_ejEA40DKUnWVtAckym8k6gq4Z"),
 dict(id="KGS-016",slug="before-you-quote-art-free",title="Before You Quote — FREE Artist Commission Brief & Price Check",price="0.00",
 pdf="1iLjB1B0xAduZmd69U2mb8iqLPQ426OJ7",cover="1T3hq9lfQnzE0w73QpHTmzqmmBScMJyF9",
 listing="1TdaD3lQVtSgy0BLhTHdwGN_i6bn8b7l_oqL8T9NyO_4",bonus=None)
]
PIN_IMAGE="1rXBzhTSnwFu902UxSLe7ivN4-Ka0aO6e"
PAID_URL="https://kindgridstudio.gumroad.com/l/commission-ready-artist-playbook"
FREE_URL="https://kindgridstudio.gumroad.com/l/before-you-quote-art-free"
BOARD="Budgeting Printables & Cash Stuffing"

def receipt(**entries):
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/"release.json"
    try: obj=json.loads(p.read_text()) if p.exists() else {}
    except (ValueError,OSError): obj={}
    obj.update(entries)
    obj["last_checked_utc"]=a.make_timestamp()
    p.write_text(json.dumps(obj,indent=2),encoding="utf-8")

def source_listing(raw):
    summary,description=a.get_listing_copy(raw)
    a.require(len(summary)>=55 and len(description)>400,"Incomplete customer listing")
    return summary,description

def run():
    a.require(os.getenv("KINDGRID_ONEOFF_ART_AUTHORIZED")=="true","One-off owner authorization absent")
    store=a.GoogleStore()
    rows=store.get_rows("Gumroad Upload Queue")
    by_id={}
    for spec in PRODUCTS:
        found=[r for r in rows if r.get("Product ID")==spec["id"]]
        a.require(len(found)==1,"Missing or duplicated staged product "+spec["id"])
        row=found[0]
        a.require(row.get("Upload Status")=="OWNER_ONE_TIME_STAGED","Staged product changed; do not duplicate")
        a.require(row.get("Unique Slug")==spec["slug"] and row.get("Product Name")==spec["title"],"Source product ID mismatch")
        a.require(row.get("QA Verified (YES/NO)")=="YES","Creator QC missing")
        by_id[spec["id"]]=row

    # Read all actual sources into a disposable isolated workspace and validate BEFORE a seller write.
    with tempfile.TemporaryDirectory(prefix="kindgrid-artist-onetime-") as base:
        t=Path(base)
        for spec in PRODUCTS:
            spec["pdf_file"]=t/(spec["id"]+".pdf")
            spec["cover_file"]=t/(spec["id"]+".png")
            binary=store.get_bytes(spec["pdf"],"application/pdf")
            count=a.validate_pdf(binary)
            a.require(count==(24 if spec["id"]=="KGS-015" else 5),"Wrong PDF page count")
            spec["pdf_file"].write_bytes(binary)
            cover=store.get_bytes(spec["cover"],"image/png")
            a.validate_image(cover)
            spec["cover_file"].write_bytes(cover)
            spec["summary"],spec["description"]=source_listing(store.get_doc_text(spec["listing"]))
            if spec["id"]=="KGS-016":
                a.require(PAID_URL in spec["description"],"Free product missing paid upgrade link")
            if spec.get("bonus"):
                file_data=store.get_bytes(spec["bonus"],"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with ZipFile(io.BytesIO(file_data)) as zipx:
                    a.require("xl/workbook.xml" in zipx.namelist(),"Paid Excel bonus malformed")
                spec["bonus_file"]=t/"KGS015_Quote_Calculator.xlsx"
                spec["bonus_file"].write_bytes(file_data)
            receipt(**{spec["id"]+"_source_verified":True})
        pin_blob=store.get_bytes(PIN_IMAGE,"image/png")
        a.validate_image(pin_blob)
        receipt(preflight="VALIDATED_SOURCE_FILES")

        # Check seller before changing anything. A previous timed-out create could already exist.
        existing=a.gumroad_cli(["products","list","--all"]).get("products",[])
        for spec in PRODUCTS:
            a.require(not any(str(p.get("custom_permalink") or "")==spec["slug"] or
                  str(p.get("short_url") or "").rstrip("/").endswith("/"+spec["slug"])
                  for p in existing),spec["id"]+" seller slug already exists; stop and reconcile")

        for spec in PRODUCTS: 
            row=by_id[spec["id"]]
            store.patch("Gumroad Upload Queue",row,{"Upload Status":"UPLOADING",
                "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1"})
            receipt(**{spec["id"]+"_seller":"CREATE_ATTEMPTED_DO_NOT_RETRY"})
            args=["products","create","--draft","--name",spec["title"],"--price",spec["price"],
                "--currency","usd","--type","digital","--custom-permalink",spec["slug"],
                "--description",spec["description"],"--custom-summary",spec["summary"]]
            if spec["price"]=="0.00":args+=["--pay-what-you-want"]
            args+=["--file",str(spec["pdf_file"])]
            if spec.get("bonus_file"):args+=["--file",str(spec["bonus_file"])]
            args+=["--cover-image",str(spec["cover_file"])]
            try:
                response=a.gumroad_cli(args)
                item=response.get("product") or {}
                sellerid=str(item.get("id") or "")
                a.require(sellerid,"Gumroad create response missing product ID")
                receipt(**{spec["id"]+"_sellerid":sellerid})
                view=a.gumroad_cli(["products","view",sellerid]).get("product") or {}
                files=view.get("files") or view.get("rich_content_files") or []
                covers=view.get("covers") or view.get("cover_images") or []
                a.require(view.get("published") is False and
                    str(view.get("name") or "")==spec["title"] and
                    len(files)>=(2 if spec.get("bonus_file") else 1) and bool(covers),
                    "Actual Gumroad draft files, cover or identity not confirmed")
                store.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
                  "Gumroad Live URL":"https://gumroad.com/products/"+sellerid+"/edit"})
                receipt(**{spec["id"]+"_seller":"DRAFT_VERIFIED"})
                a.gumroad_cli(["products","publish",sellerid])
                reread=a.gumroad_cli(["products","view",sellerid]).get("product") or {}
                a.require(reread.get("published") is True,"Gumroad publication not confirmed")
                public="https://kindgridstudio.gumroad.com/l/"+spec["slug"]
                a.verify_public_product_url(public,spec["slug"])
                store.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
                   "Gumroad Live URL":public,"Last Error":"","Last Updated UTC":a.make_timestamp()})
                receipt(**{spec["id"]+"_seller":"PUBLIC_VERIFIED",spec["id"]+"_url":public})
                print(spec["id"]+"_PUBLIC_VERIFIED: "+public)
            except Exception as exc:
                store.patch("Gumroad Upload Queue",row,{"Upload Status":"REVIEW",
                    "Last Error":(type(exc).__name__+": "+str(exc))[:400]})
                receipt(**{spec["id"]+"_seller":"REVIEW_NO_RETRY",
                           "error":type(exc).__name__+": "+str(exc)[:200]})
                raise

        # Exactly ONE promotional Pin for the free product, whose listing links paid.
        a.verify_public_product_url(FREE_URL,"before-you-quote-art-free")
        client=a.BufferClient()
        board_ids=client.boards()
        a.require(BOARD in board_ids,"Connected Buffer board unavailable")
        a.require(client.scheduled()<10,"Buffer Free queue full")
        due=datetime.now(timezone.utc)+timedelta(minutes=30)
        img_url=a.cloudinary_upload(pin_blob,"kgs016-art-commission-free-pin-oneoff-20261014")
        caption=("Free 5-page printable artist commission brief: clarify project scope, "
                 "revision limits and a preliminary price estimate before sending a quote. "
                 "Includes an optional link to the complete Commission Ready guide.")
        receipt(pin_status="BUFFER_CREATE_ATTEMPTED_DO_NOT_RETRY",pin_due_utc=due.isoformat())
        pin_data={"id":"Q-61","title":"Free Artist Commission Brief & Price Check Printable",
                  "description":caption,"board":BOARD,"destination":FREE_URL,"due":due}
        result=client.create(pin_data,img_url,board_ids[BOARD])
        ident=str(result.get("id") or "")
        delivered=str((result.get("metadata") or {}).get("url") or "")
        a.require(ident and delivered==FREE_URL,"Buffer ID or link uncertain; DO NOT resubmit")
        receipt(pin_status="SCHEDULED_BUFFER",buffer_post_id=ident,
                pin_destination=FREE_URL)
        print("Q61_BUFFER_SCHEDULED_VERIFIED: "+ident+" | due="+due.isoformat())
    return 0

if __name__=="__main__":
    try:sys.exit(run())
    except Exception as exc:
        print("KINDGRID_ARTIST_PAIR_ONEOFF_STOP: "+type(exc).__name__+": "+str(exc)[:350])
        print("DO_NOT_RERUN; RECONCILE SELLER AND BUFFER FIRST")
        sys.exit(1)
