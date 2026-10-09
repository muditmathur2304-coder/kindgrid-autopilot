"""OWNER-AUTHORISED ONE-TIME LIVE PROOF: one original Gumroad item and one Buffer Pin.

The one-time event is triggered only by creation of oneoff_grocery_live_proof.py
in main. Do not re-run the job after any attempt, successful or uncertain.
All normal KindGrid queues and earlier seller products remain untouched.
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

OUT = Path("kindgrid-proof-output")
PRODUCT_TITLE = "KindGrid Weekly Meal & Grocery Budget Kit — 6-Page Printable"
PRODUCT_SLUG = "weekly-meal-grocery-budget-kit"
PRODUCT_PRICE = "3.00"
PINTEREST_TITLE = "Plan a Week of Meals Without Overspending"
BOARD = "Budgeting Printables & Cash Stuffing"
LINK = "https://kindgridstudio.gumroad.com/l/" + PRODUCT_SLUG
COLORS = {"pine": "#2E5144", "mint": "#E7F1EB", "paper": "#FCFBF7",
          "text": "#22362F", "muted": "#60786F", "line": "#CADAD0"}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def color(value: str):
    return colors.HexColor(value)


def draw_pdf():
    pdfmetrics.registerFont(TTFont("KGSRegular", FONT))
    pdfmetrics.registerFont(TTFont("KGSBold", BOLD))
    target = OUT / "kindgrid_weekly_meal_grocery_budget_kit.pdf"
    c = canvas.Canvas(str(target), pagesize=letter, pageCompression=1)
    c.setTitle("KindGrid Weekly Meal & Grocery Budget Kit")
    c.setAuthor("KindGrid Studio")
    W, H = letter
    x0, right = 46, 566

    def line(x1, y, x2):
        c.setStrokeColor(color(COLORS["line"]))
        c.setLineWidth(0.65)
        c.line(x1, y, x2, y)

    def txt(x, y, s, size=9, bold=False, shade="text"):
        c.setFillColor(color(COLORS[shade]))
        c.setFont("KGSBold" if bold else "KGSRegular", size)
        c.drawString(x, y, s)

    def page(n, label, subtitle):
        c.setFillColor(color(COLORS["paper"]))
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(color(COLORS["pine"]))
        c.rect(0, H-16, W, 16, stroke=0, fill=1)
        txt(46, 748, "K I N D G R I D   S T U D I O", 9, True, "pine")
        txt(46, 710, label, 21, True)
        txt(46, 687, subtitle, 8.4, False, "muted")
        line(46, 669, 566)
        line(46, 49, 566)
        txt(46, 31, "Mindful planning | For personal use | US Letter 8.5 × 11 in", 7.5, False, "muted")
        txt(529, 31, "%d / 6" % n, 8, True, "pine")

    def section(y, label):
        c.setFillColor(color(COLORS["mint"]))
        c.roundRect(46, y-3, 520, 26, 5, stroke=0, fill=1)
        txt(58, y+5, label.upper(), 10, True, "pine")

    def field(label, y, width=240, x=46):
        txt(x, y+15, label, 8.2, True, "muted")
        line(x, y, x+width)

    def grid(headers, widths, nrows, top, rh=30):
        xx = [46]
        for w in widths: xx.append(xx[-1]+w)
        c.setFillColor(color(COLORS["mint"]))
        c.roundRect(46, top-27, sum(widths), 27, 4, stroke=0, fill=1)
        for j,h in enumerate(headers):
            txt(xx[j]+7, top-18, h, 8, True, "pine")
        for i in range(nrows):
            y = top-27-(i+1)*rh
            line(46, y, 46+sum(widths))
            for j in range(1,len(xx)-1):
                c.setStrokeColor(color(COLORS["line"]))
                c.line(xx[j],y,xx[j],y+rh)
        return top-27-nrows*rh

    page(1, "Your calmer grocery week", "A reusable six-page planner to make food decisions more intentional.")
    txt(46, 627, "START WITH WHAT YOU OWN. PLAN WHAT YOU NEED.", 12, True, "pine")
    txt(46, 600, "Use this printable workbook to organize meals and expected food spending.", 9)
    txt(46, 582, "No apps, complicated calculations, or special supplies required.", 9)
    section(531, "Your six-page planning toolkit")
    items=[
      ("01","Set a realistic grocery limit","Decide what you can spend this week."),
      ("02","Check the fridge, freezer, and pantry","Use ingredients you already have."),
      ("03","Map seven days of meals","Keep your plan flexible and practical."),
      ("04","Build a category-based shopping list","Shop what is missing, not what looks tempting."),
      ("05","Estimate before checkout","Compare expected and actual costs."),
      ("06","Review and improve next week","Notice unused food and adjust.")
    ]
    y=488
    for no,title,descr in items:
        c.setFillColor(color(COLORS["mint"]))
        c.circle(63,y+7,15,stroke=0,fill=1)
        txt(55,y+4,no,8,True,"pine")
        txt(88,y+10,title,10,True)
        txt(88,y-8,descr,8.2,False,"muted")
        y-=62
    field("Week beginning",97,235,46)
    field("Budget amount (USD or your currency)",97,230,336)
    c.showPage()

    page(2,"1. Inventory before shopping","Check quantities and use-by dates before adding anything to your list.")
    section(632,"Fridge, freezer and pantry inventory")
    grid(["Food / ingredient","Approx. quantity","Use first?","Planned meal"],[177,116,80,147],14,602,29)
    txt(46,132,"Tip: Prioritize anything close to its use-by date, and freeze safe leftovers.",8,False,"muted")
    field("Top three ingredients to use this week",94,515)
    c.showPage()

    page(3,"2. Your seven-day meal map","Use repeat meals and leftovers to reduce planning effort.")
    section(632,"Draft a plan you can actually follow")
    y=606
    days=["MON","TUE","WED","THU","FRI","SAT","SUN"]
    for day in days:
        c.setFillColor(color(COLORS["mint"]))
        c.roundRect(46,y-55,68,62,4,stroke=0,fill=1)
        txt(62,y-19,day,9,True,"pine")
        txt(58,y-40,"Day plan",7,False,"muted")
        for label,xx in [("BREAKFAST",125),("LUNCH",271),("DINNER",417)]:
            txt(xx,y, label,7.3,True,"muted")
            line(xx,y-25,xx+132)
            line(xx,y-44,xx+132)
        y-=72
    txt(46,88,"Prep once, reuse twice: ____________________________________________",8.5)
    txt(46,68,"Planned leftovers / easy backup meal: _______________________________",8.5)
    c.showPage()

    page(4,"3. Your intentional shopping list","Choose essentials first; keep alternatives visible if prices change.")
    section(632,"Only add what the meal map requires")
    cats=[("PRODUCE",46),("PROTEIN / DAIRY",225),("PANTRY / OTHER",404)]
    for label,x in cats:
        c.setFillColor(color(COLORS["mint"]))
        c.roundRect(x,593,163,31,4,stroke=0,fill=1)
        txt(x+12,604,label,8.4,True,"pine")
        for i in range(13):
            y=578-i*32
            c.setStrokeColor(color(COLORS["muted"]))
            c.rect(x+4,y-4,9,9,stroke=1,fill=0)
            line(x+20,y-4,x+153)
    section(136,"Double-check before checkout")
    txt(54,104,"[ ] Did I check pantry duplicates?  [ ] Is each item linked to a meal?",8.2)
    txt(54,82,"[ ] Could I substitute a less costly ingredient?",8.2)
    c.showPage()

    page(5,"4. Grocery cost estimate","Estimate individual costs. Use actual shelf prices when possible.")
    field("Budget limit",628,150)
    field("Estimated basket total",628,150,226)
    field("Expected remaining = budget minus estimate",628,174,392)
    section(580,"Item-by-item cost plan")
    grid(["Item","Quantity","Est. unit price","Est. line cost"],[208,86,113,113],13,548,30)
    txt(46,112,"To estimate a line: quantity × expected unit price = estimated line cost.",8.2)
    txt(46,92,"To estimate your total: add all estimated line costs. No automatic math is included.",8.2,False,"muted")
    txt(46,72,"A negative remaining amount means adjust your list before checkout.",8.2,False,"muted")
    c.showPage()

    page(6,"5. Review & next-week reset","Your results are information, not a judgment about your choices.")
    section(633,"Close the loop")
    field("Planned grocery budget",581,220)
    field("Actual amount spent",581,220,346)
    field("Difference = budget minus actual spending",516,520)
    field("Meals that worked especially well",449,520)
    field("Food I used before it spoiled",382,520)
    field("Food I did not use (and why)",315,520)
    field("One small improvement for next week",248,520)
    section(178,"Quick reflection")
    txt(54,150,"What was the easiest way to keep my shopping list focused?",8.3)
    line(54,128,557)
    txt(54,110,"What's one meal I can repeat or batch-prep next week?",8.3)
    line(54,89,557)
    c.showPage()
    c.save()
    return target


def art(output: Path, is_pin: bool):
    im=Image.new("RGB",(1000,1500),COLORS["paper"])
    d=ImageDraw.Draw(im)
    fr=lambda size: ImageFont.truetype(FONT,size)
    fb=lambda size: ImageFont.truetype(BOLD,size)
    d.rectangle((0,0,1000,18),fill=COLORS["pine"])
    d.text((75,65),"KINDGRID STUDIO  /  FOOD & HOME",font=fb(25),fill=COLORS["muted"])
    d.text((75,151),"Your Weekly",font=fb(70),fill=COLORS["text"])
    d.text((75,239),"Meal & Grocery",font=fb(70),fill=COLORS["text"])
    d.text((75,327),"Budget Kit",font=fb(70),fill=COLORS["text"])
    d.text((75,438),"6-page printable planning workbook",font=fr(35),fill=COLORS["muted"])
    d.rounded_rectangle((75,526,925,1180),radius=20,fill="#EAF1EA",outline=COLORS["line"],width=3)
    x,y=107,557
    d.text((x,y),"THE WEEKLY RESET",font=fb(28),fill=COLORS["pine"])
    d.line((x,y+50,895,y+50),fill=COLORS["line"],width=3)
    headers=["MON","TUE","WED","THU","FRI","SAT","SUN"]
    for i,h in enumerate(headers):
        xx=107+(i%4)*196
        yy=650+(i//4)*137
        d.rounded_rectangle((xx,yy,xx+178,yy+111),radius=11,fill="white",outline=COLORS["line"],width=2)
        d.text((xx+16,yy+14),h,font=fb(22),fill=COLORS["pine"])
        for off in [56,78]:
            d.line((xx+16,yy+off,xx+156,yy+off),fill=COLORS["line"],width=3)
    d.text((107,1033),"PLAN MEALS   •   SHOP INTENTIONALLY",font=fb(23),fill=COLORS["pine"])
    d.text((107,1080),"TRACK COSTS   •   REVIEW THE WEEK",font=fb(23),fill=COLORS["pine"])
    d.text((75,1251),"Pantry inventory  /  7-day meal map",font=fr(30),fill=COLORS["text"])
    d.text((75,1302),"Grocery list  /  Price estimate  /  Reflection",font=fr(30),fill=COLORS["text"])
    d.line((75,1390,925,1390),fill=COLORS["line"],width=3)
    d.text((75,1412),"kindgridstudio.gumroad.com",font=fb(25),fill=COLORS["pine"])
    im.save(output,optimize=True)
    return output


def prepare_assets():
    OUT.mkdir(parents=True,exist_ok=True)
    pdf=draw_pdf()
    cover=art(OUT/"grocery_cover.png",False)
    pin=art(OUT/"grocery_pin.png",True)
    reader=PdfReader(str(pdf))
    a.require(len(reader.pages)==6,"Incorrect product page count")
    for number,p in enumerate(reader.pages,1):
        a.require(abs(float(p.mediabox.width)-612)<1 and abs(float(p.mediabox.height)-792)<1,
                  f"Page {number} is not US Letter")
        a.require(len(p.extract_text() or "")>=180,f"Page {number} appears incomplete")
    for img in (cover,pin):
        with Image.open(img) as check:
            a.require(check.size==(1000,1500),"Wrong cover or Pin dimensions")
            check.verify()
    print("ASSET_QA_OK: Original six-page US Letter PDF and both 1000x1500 images validated.")
    return pdf,cover,pin


def persist(data: dict):
    (OUT/"publishing_proof.json").write_text(json.dumps(data,indent=2),encoding="utf-8")


def submit():
    a.require(os.getenv("KINDGRID_OWNER_AUTHORIZED_ONETIME")=="true",
              "This is a manual owner-authorized proof; no generic live automation.")
    pdf,cover,pin=prepare_assets()
    proof={"title":PRODUCT_TITLE,"slug":PRODUCT_SLUG,"price_usd":PRODUCT_PRICE,
           "mode":"single owner-authorized one-off", "gumroad":"not attempted",
           "pinterest":"not attempted", "generated_at":a.make_timestamp()}
    persist(proof)
    a.require(bool(os.getenv("GUMROAD_ACCESS_TOKEN")) and bool(os.getenv("BUFFER_API_KEY")),
              "Seller and Buffer connection secrets required")
    products=a.gumroad_cli(["products","list","--all"]).get("products",[])
    for product in products:
        slug=str(product.get("custom_permalink") or "")
        if slug==PRODUCT_SLUG or str(product.get("short_url") or "").rstrip("/").endswith("/"+PRODUCT_SLUG):
            print("STOP: Proof product slug already exists. Do not create/retry.")
            proof["gumroad"]="DUPLICATE_PROTECTED"
            persist(proof)
            return 1
    # This unit is an original, printable-only product with no investment claims.
    description="""A simple six-page printable workbook for planning meals and grocery spending with less guesswork.

WHAT'S INCLUDED
• Getting-started guide and weekly budget intention
• Pantry, fridge and freezer inventory worksheet
• Seven-day breakfast, lunch and dinner meal map
• Shopping list with produce, protein/dairy and pantry categories
• Item-by-item grocery cost estimate and budget comparison
• Weekly reflection to reduce unwanted repeat purchases

The six-page US Letter PDF is designed to print at home. Each page can be printed again for personal use. This is a static paper-and-pencil planner: no formulas run automatically, and it is not a grocery price prediction tool.

HOW IT WORKS
Download the PDF after purchase, print the pages you want to use, check your kitchen before shopping, draft meals, write expected prices, and compare your actual grocery spending after the trip.

Digital file only; no physical item is shipped. Personal-use licence only: do not redistribute or resell the PDF. We aim to provide accurate, useful printables; results depend on local prices and individual circumstances. For any file-delivery problems, contact the seller through Gumroad support/messaging."""
    if len(description)<400: raise RuntimeError("Description QA failed")
    proof["gumroad"]="CREATING_UNPUBLISHED_DRAFT"
    persist(proof)
    response=a.gumroad_cli(["products","create","--draft","--name",PRODUCT_TITLE,
          "--price",PRODUCT_PRICE,"--currency","usd","--type","digital",
          "--custom-permalink",PRODUCT_SLUG,"--description",description,
          "--file",str(pdf),"--cover-image",str(cover)])
    prod=response.get("product") or {}
    seller_id=str(prod.get("id") or "")
    if not seller_id:
        proof["gumroad"]="UNCERTAIN_CREATE_DO_NOT_RETRY"
        persist(proof)
        raise RuntimeError("Gumroad may have created draft without ID; never repeat.")
    proof["gumroad_draft_id"]=seller_id
    proof["gumroad_edit_url"]=f"https://gumroad.com/products/{seller_id}/edit"
    proof["gumroad"]="DRAFT_CREATED"
    persist(proof)
    p=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
    a.require(p.get("published") is False and str(p.get("name") or "")==PRODUCT_TITLE,
              "Draft identity/publication state unverified; stop.")
    a.require(bool(p.get("files") or p.get("rich_content_files")) and
              bool(p.get("covers") or p.get("cover_images")),
              "PDF/cover not confirmed in actual Gumroad draft; stop.")
    proof["gumroad"]="DRAFT_PDF_AND_COVER_VERIFIED"
    persist(proof)
    a.gumroad_cli(["products","publish",seller_id])
    p=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
    a.require(p.get("published") is True,"Publish not confirmed; DO NOT retry.")
    proof["gumroad"]="PUBLISHED_BY_GUMROAD_API"
    persist(proof)
    a.verify_public_product_url(LINK,PRODUCT_SLUG)
    proof["gumroad"]="PUBLIC_URL_VERIFIED"
    proof["gumroad_public_url"]=LINK
    persist(proof)
    print("GUMROAD_ONEOFF_PUBLISHED_VERIFIED: "+LINK)

    board_client=a.BufferClient()
    boards=board_client.boards()
    a.require(BOARD in boards,"Target Pinterest board not available in Buffer.")
    a.require(board_client.scheduled()<10,"Buffer Free queue is full.")
    # Near-term scheduled send. Prioritise reliable established Buffer API over
    # inventing an untested send-now mutation.
    due=datetime.now(timezone.utc)+timedelta(minutes=25)
    data={"id":"KGS-004-PIN-ONEOFF","title":PINTEREST_TITLE,
          "description":"Plan seven days of meals, check your pantry and organize grocery costs with this original six-page US Letter printable from KindGrid Studio. A calmer grocery week starts with a simple list.",
          "board":BOARD,"destination":LINK,"due":due}
    image_url=a.cloudinary_upload(pin.read_bytes(),"kgs004-grocery-proof-20261009")
    proof["pinterest"]="IMAGE_HOSTED"
    proof["pin_image_url"]=image_url
    persist(proof)
    post=board_client.create(data,image_url,boards[BOARD])
    proof["pinterest_buffer_post_id"]=str(post.get("id") or "")
    proof["pinterest_due_utc"]=due.isoformat()
    returned=(post.get("metadata") or {}).get("url")
    if not proof["pinterest_buffer_post_id"] or returned!=LINK:
        proof["pinterest"]="LINK_REVIEW_NO_AUTOMATIC_RETRY"
        persist(proof)
        raise RuntimeError("Buffer may have created post with uncertain destination; inspect before any retry.")
    proof["pinterest"]="SCHEDULED_BUFFER"
    persist(proof)
    print("PINTEREST_ONEOFF_SCHEDULED: Buffer post "+proof["pinterest_buffer_post_id"])
    print("PINTEREST_EXPECTED_SEND_UTC: "+proof["pinterest_due_utc"])
    print("SAFE: All existing KindGrid queue rows and listings left unchanged.")
    return 0


if __name__=="__main__":
    if "--prepare-only" in sys.argv:
        try:
            prepare_assets()
            print("READ_ONLY_PREVIEW_SUCCESS: no Gumroad or Pinterest API calls made")
            sys.exit(0)
        except Exception as exc:
            print("READ_ONLY_PREVIEW_FAILED: " + type(exc).__name__ + ": " + str(exc))
            sys.exit(1)
    try:
        sys.exit(submit())
    except Exception as e:
        print("ONEOFF_PROOF_REVIEW_REQUIRED: "+type(e).__name__+": "+str(e)[:350])
        print("STOP: Do NOT rerun this workflow; inspect Gumroad and Buffer for partial success.")
        sys.exit(1)
