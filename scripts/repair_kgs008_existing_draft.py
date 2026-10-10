"""Exactly once: replace KGS-008 historical draft downloadable files safely.

Only use exact existing slug and seller ID verified in a prior read-only run.
Never publish or create a product in this stage. Never blindly rerun on uncertain state.
"""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,".")
from src import autopilot as a

ID="dbXiy8eZ1uxF33itkI4p4Q=="
SLUG="market-day-margin-guide"
OLD_PDF="H2segmakuganqGb2ngzIAg=="
OLD_EXCEL="zUQbX-eIOUJfvSO3cI5ALw=="
NEW_PDF="1bfhntLiv7QD21ZYC3nxYfp0tP43hHmDm"
NEW_XLS="1_K0PZZPtzVrTHTpD4VvyJ3Hskc8C1DpJ"
OUT=Path("kindgrid-repair008-proof")

def mark(step,**more):
    OUT.mkdir(exist_ok=True,parents=True)
    p=OUT/"receipt.json"
    d=json.loads(p.read_text()) if p.exists() else {}
    d.update(more)
    d["stage"]=step
    d["time_utc"]=a.make_timestamp()
    p.write_text(json.dumps(d,indent=2))
    print("CORRECT_008 "+step)

def ids_from_pages(raw):
    a.require(isinstance(raw,list) and len(raw)==1,"Unexpected number of shared rich-content pages")
    page=raw[0]
    a.require(page.get("title")=="Page 1","Unexpected shared page title")
    d=page.get("description")
    a.require(isinstance(d,dict) and d.get("type")=="doc","Not a familiar rich-content document")
    blocks=d.get("content") or []
    ids=[str(b.get("attrs",{}).get("id")) for b in blocks if b.get("type")=="fileEmbed"]
    return ids

def main():
    store=a.GoogleStore()
    matches=[r for r in store.get_rows("Gumroad Upload Queue") if r.get("Product ID")=="KGS-008"]
    a.require(len(matches)==1,"Product queue row missing or duplicated")
    row=matches[0]
    a.require(row.get("Upload Status")=="REVIEW","Only original held REVIEW product may be repaired")
    a.require(row.get("Unique Slug")==SLUG,"Original slug mismatch")
    a.require(row.get("QA Verified (YES/NO)")=="YES" and row.get("QA Outcome")=="PASS",
              "Corrected source QA not approved")
    a.verify_qa_report(store,row,"KGS-008")
    pdf=store.get_bytes(NEW_PDF,"application/pdf")
    excel=store.get_bytes(NEW_XLS,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    a.require(a.validate_pdf(pdf)==27,"Corrected paid source page count mismatch")
    import io
    from zipfile import ZipFile
    from pypdf import PdfReader
    import re
    dtext="\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages)
    a.require("$19.22" in dtext and "-$22.05" in dtext and "$19.62" not in dtext,
              "Corrected arithmetic missing or stale in updated source")
    with ZipFile(io.BytesIO(excel)) as z:
        a.require("xl/workbook.xml" in z.namelist(),"Corrected spreadsheet broken")

    matches=[p for p in a.gumroad_cli(["products","list","--all"]).get("products",[]) if
             str(p.get("custom_permalink") or "")==SLUG or
             str(p.get("short_url") or "").rstrip("/").endswith("/"+SLUG)]
    a.require(len(matches)==1 and str(matches[0].get("id") or "")==ID,
              "Original seller draft no longer uniquely matches known ID")
    view=a.gumroad_cli(["products","view",ID]).get("product") or {}
    a.require(view.get("published") is False and
              str(view.get("name") or "")==row["Product Name"],
              "Original Gumroad seller draft is already published or identity changed")
    pages=a.gumroad_cli(["products","content","get",ID])
    before=ids_from_pages(pages)
    a.require(before==[OLD_PDF,OLD_EXCEL],"Draft rich content changed since independent inspection; no retries")
    old=view.get("files") or []
    a.require(len(old)==2 and {str(x.get("id")) for x in old}=={OLD_PDF,OLD_EXCEL},
              "Seller old files not exactly the known obsolete PDF/Excel")
    mark("ORIGINAL_DRAFT_VERIFIED",old_file_ids=before)
    with tempfile.TemporaryDirectory(prefix="k008-corrected-") as tmp:
        target=Path(tmp)
        p=target/"Market_Day_Margin_Corrected_27p.pdf"
        x=target/"Market_Day_Margin_Companion_Corrected.xlsx"
        p.write_bytes(pdf)
        x.write_bytes(excel)
        mark("CORRECTED_ATTACH_ATTEMPTED_DO_NOT_RETRY")
        # File attachments append, so we MUST structurally remove both old embeds before publish.
        a.gumroad_cli(["products","update",ID,"--file",str(p),"--file",str(x)])
        after=a.gumroad_cli(["products","view",ID]).get("product") or {}
        a.require(after.get("published") is False,"File update accidentally published product")
        files=after.get("files") or []
        newpdf=[f for f in files if int(f.get("size") or -1)==len(pdf) and str(f.get("id")) not in before]
        newxls=[f for f in files if int(f.get("size") or -1)==len(excel) and str(f.get("id")) not in before]
        a.require(len(newpdf)==1 and len(newxls)==1,
                  "Cannot uniquely identify corrected PDFs/XLSX among seller files")
        corrected_ids=[str(newpdf[0]["id"]),str(newxls[0]["id"])]
        print("REVISED_FILES_ATTACHED_IDS "+json.dumps(corrected_ids))
        mark("CORRECTED_FILES_APPENDED_BEFORE_STRUCTURAL_SWAP",new_file_ids=corrected_ids)
        updated_pages=a.gumroad_cli(["products","content","get",ID])
        ids=ids_from_pages(updated_pages)
        a.require(len(ids)==4 and ids[:2]==before and ids[2:]==corrected_ids,
                  "Unexpected rich-content embeds after append; refuse destructive content write")
        for b in updated_pages[0]["description"]["content"]:
            if b.get("type")=="fileEmbed" and str(b.get("attrs",{}).get("id")) in (OLD_PDF,OLD_EXCEL):
                b["_remove_legacy"]=True
        nodes=updated_pages[0]["description"]["content"]
        updated_pages[0]["description"]["content"]=[b for b in nodes if not b.get("_remove_legacy")]
        a.require(ids_from_pages(updated_pages)==corrected_ids,"Replacement content payload wrong")
        payload=target/"corrected_content.json"
        payload.write_text(json.dumps(updated_pages))
        # Verify the CLI understands the exact payload before any structural edit.
        a.gumroad_cli(["products","content","set",ID,str(payload),"--dry-run"])
        mark("STRUCTURAL_CONTENT_REPLACE_ATTEMPTED_NO_RETRY")
        a.gumroad_cli(["products","content","set",ID,str(payload),"--yes"])
        saved=a.gumroad_cli(["products","content","get",ID])
        a.require(ids_from_pages(saved)==corrected_ids,
                  "Saved customer-content contains obsolete file embeds; do not publish")
        final=a.gumroad_cli(["products","view",ID]).get("product") or {}
        a.require(final.get("published") is False and
                  str(final.get("custom_permalink") or "")==SLUG,
                  "Product identity changed while updating content")
        # Product.files may still include orphaned attachments but the entire
        # single customer-content page must have only the two new confirmed IDs.
        mark("REVISED_GUMROAD_CONTENT_VERIFIED",
             new_file_ids=corrected_ids,
             seller_files=[{"id":str(f.get("id")),"size":f.get("size")} for f in final.get("files") or []],
             customer_content_file_ids=ids_from_pages(saved))
        print("SUCCESS_EXISTING_DRAFT_CORRECT_CONTENT_UNPUBLISHED")
        return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as e:
        mark("REVIEW_REQUIRED_DO_NOT_RETRY",error_type=type(e).__name__,error=str(e)[:300])
        print("DRAFT_REPAIR_HALTED: "+type(e).__name__+" "+str(e)[:300])
        print("NEVER_REPEAT_THIS_WORKFLOW_WITHOUT_RECONCILIATION")
        sys.exit(1)
