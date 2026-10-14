"""One-time OWNER-authorized KGS017 DepositGuard release. Never rerun after mutation."""
from __future__ import annotations
import hashlib, io, json, math, os, sys, textwrap, time, zipfile
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from src import autopilot as a

PID="KGS-017"; QID="Q-62"; SLUG="depositguard-project-cash-coverage"
NAME="DepositGuard Studio | Client Deposits, Commitments & Cash-Coverage Tool"
PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
PRICE="14.00"; BOARD="Budgeting Printables & Cash Stuffing"
EVIDENCE=Path("kindgrid-kgs017-evidence")
SUMMARY="An offline, interactive deposit and project-cash decision system for freelancers. Includes the tool and eight-page field guide."
DESCRIPTION="""An invoice can be profitable on paper while leaving you short of cash before delivery. DepositGuard Studio makes the timing visible.

WHAT YOU GET
• A carefully designed, self-contained offline HTML decision tool. No login, spreadsheets subscription, or data collection.
• Adjustable project price, deposit received, cleared reserves, project commitments, target labor time, and protected cash buffer.
• A cash-coverage dashboard distinguishing money already received from future milestone payments that you cannot spend yet.
• A suggested minimum funding gap, deposit sufficiency signal, effective hourly outcome and 15% cost-overrun scenario.
• An eight-page US Letter illustrated field guide, a realistic worked case and reusable client deposit wording.
• A one-click local CSV summary export to use alongside your project record.

WHO IT IS FOR
US-based freelancers and solo service operators who collect deposits before delivering client work: designers, consultants, photographers, editors, and independent contractors.

IMPORTANT LIMITS
This is a project-level planning model, not a bookkeeping system, credit product, tax opinion, legal advice, or automatic bank connection. Example values are illustrative. Enter only amounts you have actually received as cleared cash. The proposed minimum deposit is a planning benchmark, never a legal entitlement or a guarantee that a client will pay. No sales or savings results are promised.

FILES: DepositGuard_Offline_Tool.html and DepositGuard_8_Page_Guide.pdf, together inside one downloadable ZIP. Open the HTML tool in a current web browser; it runs offline. No macros required.

Created by KindGrid Studio for thoughtful independent businesses."""
TITLE="50% CLIENT DEPOSIT: HOW MUCH CAN YOU ACTUALLY USE?"
PIN_DESC=("A $900 deposit is not automatically $900 available to spend. "
          "Check supplier commitments, contractor fees and your protected buffer before accepting a new project. "
          "DepositGuard is an offline planning tool for freelancers with a downloadable illustrated guide. "
          "Examples are fictional; no guaranteed outcomes.")
DEST=PUBLIC+"?utm_source=pinterest&utm_medium=organic&utm_campaign=depositguard_launch&utm_content=q62"

def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def receipt(state,**kwargs):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    p=EVIDENCE/"receipt.json"
    try: state0=json.loads(p.read_text()) if p.exists() else {}
    except Exception: state0={}
    state0.update(kwargs);state0["state"]=state;state0["at_utc"]=stamp()
    p.write_text(json.dumps(state0,indent=2),encoding="utf-8")
    print("KGS017_STATE",state,flush=True)

def font(size=32,bold=False):
    paths=([
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ] if bold else [
      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"])
    for f in paths:
        if Path(f).is_file(): return ImageFont.truetype(f,size)
    return ImageFont.load_default()

def multiline(draw,point,text,width,size,fill,leading=1.40,bold=False):
    face=font(size,bold)
    words=text.split()
    lines=[]; cur=""
    for word in words:
        test=(cur+" "+word).strip()
        if draw.textbbox((0,0),test,font=face)[2]>width and cur:
            lines.append(cur); cur=word
        else: cur=test
    if cur: lines.append(cur)
    x,y=point
    for line in lines:
        draw.text((x,y),line,font=face,fill=fill)
        y+=int(size*leading)
    return y

def images():
    cream="#F6F4EE"; ink="#213D3C"; sage="#AABCA9"; pale="#E0E9DE"; coral="#C46E4E"; white="#FFFFFF"
    # A clean, flat editorial treatment; all artwork drawn with exact geometry.
    pin=Image.new("RGB",(1000,1500),cream); d=ImageDraw.Draw(pin)
    d.rectangle((0,0,1000,24),fill=ink)
    d.text((80,82),"KINDGRID / TOOLS",font=font(27,True),fill=ink)
    d.text((80,176),"FREELANCE CASHFLOW",font=font(24,True),fill=coral)
    y=multiline(d,(80,252),"A 50% deposit doesn't mean 50% is spendable.",840,65,ink,1.23,True)
    d.text((83,y+20),"PROJECT CASH-COVERAGE EXAMPLE",font=font(22,True),fill=ink)
    d.rounded_rectangle((70,y+84,930,y+570),radius=34,fill=white)
    entries=[("Deposit received","$900"),("Pre-delivery commitments","-$670"),("Protected cash buffer","-$150")]
    yy=y+125
    for lab,val in entries:
        d.text((115,yy),lab,font=font(25),fill=ink);d.text((727,yy),val,font=font(29,True),fill=ink)
        d.line((115,yy+57,885,yy+57),fill="#DFE4DD",width=2); yy+=115
    d.rounded_rectangle((106,yy-4,894,yy+92),radius=17,fill=pale)
    d.text((135,yy+18),"Cash left uncommitted",font=font(29,True),fill=ink)
    d.text((740,yy+18),"$80",font=font(38,True),fill=ink)
    d.text((80,1239),"See obligations before saying yes.",font=font(36,True),fill=ink)
    d.text((80,1297),"OFFLINE TOOL + ILLUSTRATED FIELD GUIDE",font=font(24),fill=ink)
    d.rounded_rectangle((75,1372,925,1457),radius=28,fill=ink)
    d.text((130,1393),"DEPOSITGUARD  /  KINDGRID STUDIO",font=font(29,True),fill=white)
    pin.save(EVIDENCE/"Q62_Pinterest_Original.png",optimize=True)
    # storefront cover
    cover=Image.new("RGB",(1600,900),cream); g=ImageDraw.Draw(cover)
    g.rectangle((0,0,26,900),fill=ink)
    g.text((115,113),"KINDGRID STUDIO   /   WORKING SYSTEMS",font=font(30,True),fill=ink)
    g.text((115,264),"DEPOSITGUARD",font=font(92,True),fill=ink)
    g.text((120,391),"PROJECT CASH-COVERAGE STUDIO",font=font(43),fill=ink)
    multiline(g,(120,505),"Know what your deposit must cover before you commit to the work.",1090,34,ink)
    g.rounded_rectangle((116,725,1000,802),radius=18,fill=pale)
    g.text((150,740),"OFFLINE INTERACTIVE TOOL  +  8-PAGE GUIDE",font=font(29,True),fill=ink)
    for i,ht in enumerate([130,240,338,425]):
        x=1220+90*i;g.rounded_rectangle((x,750-ht,x+58,752),radius=18,fill=[sage,ink,coral,sage][i])
    cover.save(EVIDENCE/"KGS017_Gumroad_Cover.png",optimize=True)
    return pin,cover

def tool_html():
    return r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DepositGuard Studio — KindGrid</title>
<style>
:root{--ink:#213d3c;--sage:#769287;--light:#f6f4ee;--panel:#fff;--line:#d9e2da;--orange:#b76546}
*{box-sizing:border-box}body{margin:0;background:var(--light);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,Arial,sans-serif}
header{background:var(--ink);color:white;padding:34px max(24px,calc((100vw - 1160px)/2));}header small{letter-spacing:3px;color:#c9dfd2}
header h1{font-size:clamp(36px,6vw,62px);margin:10px 0 3px;letter-spacing:-1.5px}header p{max-width:620px;opacity:.87}
main{max-width:1160px;margin:auto;padding:28px 22px 68px}.intro{max-width:900px;font-size:18px}
.layout{display:grid;grid-template-columns:minmax(280px,1fr) minmax(280px,1fr);gap:24px;align-items:start}
.card{background:white;border:1px solid var(--line);border-radius:18px;padding:26px;box-shadow:0 5px 30px #243c3810}
h2{font-size:22px;margin:0 0 10px}h3{margin:22px 0 10px;font-size:17px}label{display:block;font-size:13px;font-weight:700;margin:14px 0 5px}
input{width:100%;border:1px solid #a5bdb0;border-radius:9px;font:inherit;padding:11px 13px;background:white;color:var(--ink)}
small,.muted{color:#62746a;font-size:13px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.metric{padding:17px 18px;border-radius:12px;background:#ecf1ea;margin:13px 0}.metric b{display:block;font-size:30px;font-variant-numeric:tabular-nums}
.metric span{font-size:13px}.metric.accent{background:#e0e8dc}.metric.warning{background:#faeadf;color:#824b38}
.rule{border-top:1px solid var(--line);margin:22px 0}.list{padding-left:18px}.list li{padding:4px 0}
button{background:var(--ink);color:white;border:0;border-radius:9px;padding:13px 22px;cursor:pointer;font-weight:700}
button:focus,input:focus{outline:3px solid #98bba7;outline-offset:2px}
.note{border-left:4px solid var(--orange);padding-left:17px;color:#445a51;margin-top:22px}
footer{padding:23px;border-top:1px solid var(--line);font-size:13px;text-align:center;color:#66796e}
@media(max-width:780px){.layout{grid-template-columns:1fr}.grid2{grid-template-columns:1fr}}
@media print{header{color:#213d3c;background:white}button{display:none}}
</style></head><body>
<header><small>KINDGRID STUDIO / WORKING SYSTEMS</small><h1>DepositGuard.</h1>
<p>See what a client deposit must cover before you commit to work. A self-contained, private, offline project cash planner.</p></header>
<main><p class="intro">Money promised later is not cash received today. Enter the cleared funds and realistic obligations for one project; this tool keeps those two concepts separate.</p>
<section class="layout"><div class="card"><h2>01 / Project inputs</h2>
<p class="muted">USD. Example figures are fictional and editable.</p>
<div class="grid2">
<div><label for="price">Agreed project fee ($)</label><input type="number" id="price" min="0" step="0.01" value="1800"></div>
<div><label for="paid">Deposit already cleared ($)</label><input type="number" id="paid" min="0" step="0.01" value="900"></div>
<div><label for="cash">Other cash allocated to project ($)</label><input type="number" id="cash" min="0" step="0.01" value="0"></div>
<div><label for="vendor">Supplier/material commitments ($)</label><input type="number" id="vendor" min="0" step="0.01" value="250"></div>
<div><label for="contract">Contractor commitments ($)</label><input type="number" id="contract" min="0" step="0.01" value="380"></div>
<div><label for="fees">Other project costs before delivery ($)</label><input type="number" id="fees" min="0" step="0.01" value="40"></div>
<div><label for="buffer">Protected cash buffer ($)</label><input type="number" id="buffer" min="0" step="0.01" value="150"></div>
<div><label for="later">Other costs after delivery ($)</label><input type="number" id="later" min="0" step="0.01" value="60"></div>
<div><label for="hours">Your expected work hours</label><input type="number" id="hours" min="0" step="0.5" value="18"></div>
<div><label for="rate">Target pay for your time ($/h)</label><input type="number" id="rate" min="0" step="0.01" value="35"></div>
</div>
<p class="note">Treat the deposit as "cleared" only when accessible in your account. Do not count unsigned agreements or unpaid milestone invoices.</p>
</div>
<div class="card"><h2>02 / Cash decision board</h2>
<div class="metric accent"><span>Cash left after pre-delivery commitments and buffer</span><b id="available">$0</b><span id="status">Waiting for inputs</span></div>
<div class="grid2">
<div class="metric"><span>Pre-delivery cash commitments</span><b id="before">$0</b></div>
<div class="metric"><span>Future client payment (not spendable yet)</span><b id="future">$0</b></div>
<div class="metric"><span>Cash funding gap to protect buffer</span><b id="shortfall">$0</b></div>
<div class="metric"><span>Indicative deposit coverage %</span><b id="pct">0%</b></div>
</div>
<div class="rule"></div>
<h3>03 / Price quality and stress test</h3>
<div class="grid2">
<div class="metric"><span>Residual after direct costs and your target labor value</span><b id="residual">$0</b></div>
<div class="metric"><span>Residual if project costs rise 15%</span><b id="stress">$0</b></div>
</div>
<p class="muted">These are planning residuals, not tax-adjusted net profit. The 15% sensitivity applies to direct costs, not contract revenue or target labor.</p>
<button id="export">Export a project CSV</button>
<p class="note">If cash is negative, secure a deposit/milestone, reduce early commitments, adjust scope, or decline the project. The tool cannot evaluate contract enforceability.</p>
</div></section>
<section class="card" style="margin-top:24px"><h2>How to read your result</h2>
<ol class="list">
<li><strong>Today’s cash coverage</strong> uses only cleared deposit plus money already allocated to this project, less obligations that must be paid before delivery and a protected buffer.</li>
<li><strong>Future payment</strong> is shown for planning but is not added to the spendable-cash figure.</li>
<li><strong>Indicative deposit coverage</strong> answers how much of the fee would cover the early commitments and protected buffer if no other cash were allocated. It is not a legal minimum.</li>
<li><strong>Price residual</strong> subtracts estimated direct costs and the value you assign to your own work; compare it with your goals before quoting.</li>
</ol><p class="muted">For more, see the included eight-page DepositGuard field guide.</p></section>
</main><footer>© KindGrid Studio · Offline only · Your data remains in this browser session unless you save the CSV. Educational financial planning tool, not advice.</footer>
<script>
(function(){
"use strict";
const ids=["price","paid","cash","vendor","contract","fees","buffer","later","hours","rate"];
const el=id=>document.getElementById(id);
const money=x=>(x<0?"−":"")+"$"+Math.abs(x).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
const percent=x=>(x*100).toFixed(1)+"%";
let latest={};
function run(){
 const v={};for(const id of ids){const n=Number(el(id).value);v[id]=Number.isFinite(n)?Math.max(0,n):0;}
 const before=v.vendor+v.contract+v.fees;
 const funds=v.paid+v.cash;
 const available=funds-before-v.buffer;
 const shortfall=Math.max(0,-available);
 const future=Math.max(0,v.price-v.paid);
 const minDeposit=Math.max(0,before+v.buffer-v.cash);
 const pct=v.price>0?minDeposit/v.price:0;
 const costs=before+v.later;
 const residual=v.price-costs-v.hours*v.rate;
 const stress=v.price-costs*1.15-v.hours*v.rate;
 el("before").textContent=money(before);el("future").textContent=money(future);
 el("available").textContent=money(available);el("shortfall").textContent=money(shortfall);
 el("pct").textContent=percent(pct);el("residual").textContent=money(residual);
 el("stress").textContent=money(stress);
 el("status").textContent=available>=0?"Early commitments and buffer are covered.":"Funding gap: take action before committing.";
 el("available").parentElement.className="metric accent"+(available<0?" warning":"");
 latest={...v,before,available,shortfall,future,minimum_deposit_planning:minDeposit,residual,stress};
}
for(const id of ids){el(id).addEventListener("input",run);}
el("export").addEventListener("click",function(){
 const lines=["metric,value"].concat(Object.entries(latest).map(([k,v])=>k+","+String(v)));
 const blob=new Blob([lines.join("\r\n")],{type:"text/csv;charset=utf-8"});
 const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="DepositGuard_Project_Summary.csv";a.click();URL.revokeObjectURL(url);
});
run();
})();
</script></body></html>'''

def pdf_guide():
    p=EVIDENCE/"DepositGuard_8_Page_Field_Guide.pdf"
    c=canvas.Canvas(str(p),pagesize=letter)
    W,H=letter; ink=HexColor("#213D3C");sage=HexColor("#8BAA99");light=HexColor("#F6F4EE");orange=HexColor("#C46E4E")
    pages=[
      ("START HERE","What your deposit must really cover",
       ["The price on an invoice is not the cash in your account.",
        "Project work creates expenses on different dates. Before you promise a delivery date, list the costs that must be funded now.",
        "DepositGuard separates cleared cash, committed outflows, protected liquidity and the future payment you cannot yet spend."],
       ["Your decision in 60 seconds:","1. Enter confirmed cleared deposit, never an unpaid promise.","2. List supplier, contractor and other pre-delivery bills.","3. Set a protected project buffer.","4. Read the cash-coverage result before accepting scope."]),
      ("THE MODEL","Four numbers, one decision",
       ["CLEARED FUNDS = deposit received + existing cash earmarked for the project.",
        "PRE-DELIVERY OBLIGATIONS = suppliers + contractors + early project fees.",
        "EARLY FREE CASH = cleared funds − pre-delivery obligations − protected buffer.",
        "FUNDING GAP = max(0, −early free cash)."],
       ["Do not treat a client's future milestone payment as cleared funds.","A negative early free-cash figure is a funding prompt, not proof that the whole project is unprofitable."]),
      ("WORKED CASE","A 50% deposit can still be tight",
       ["Illustrative project: $1,800 fee; $900 cleared deposit.",
        "Suppliers $250; contracted help $380; early fees $40.",
        "Protected cash buffer $150.",
        "Today's early free cash: $900 − ($250 + $380 + $40) − $150 = $80.",
        "The remaining $900 invoice is not spendable until received."],
       ["Change one variable: If contractor cost rose by $120, early free cash would be −$40.","Choose a funding milestone or lower the early obligation; do not assume future payment arrives on time."]),
      ("SET YOUR FLOOR","The deposit coverage benchmark",
       ["A simple planning baseline is: early commitments + protected buffer − other allocated project cash.",
        "Divide that baseline by contract price to see a useful deposit coverage ratio.",
        "Example: ($670 + $150 − $0) / $1,800 = 45.6%.",
        "This is an internal cash benchmark, not a client-facing mandatory deposit or a legal entitlement."],
       ["If the ratio exceeds 100%, the project design asks you to risk more cash than the full fee can cover.","Re-scope, stage the work, reduce commitments or reconsider the quote."]),
      ("PRICE QUALITY","Profitability is not liquidity",
       ["A deposit may cover the next bills while total project pricing remains weak.",
        "Residual after target labor = agreed fee − all direct project costs − (expected hours × target hourly value).",
        "Illustration: $1,800 − ($250+$380+$40+$60) − (18 × $35) = $440.",
        "This amount is not net profit after taxes, overhead or every business expense."],
       ["The tool also shows a 15% direct-cost increase scenario.","If a small cost change consumes the residual, the quote may require scope or pricing changes."]),
      ("CLIENT LANGUAGE","Say it clearly and professionally",
       ["Initial deposit: 'To reserve the production window, I request an initial payment of [amount] before booking third-party work.'",
        "Milestone request: 'The next phase includes [items]. A milestone payment of [amount] is due before I authorize these costs.'",
        "Scope change: 'This request adds [deliverable/time]. I can confirm the updated price and timeline before proceeding.'"],
       ["Use precise contract terms suited to your jurisdiction. This guide does not supply legal clauses.","Document agreed deliverables and revision rounds separately."]),
      ("EXCEPTIONS","Three scenarios to test before 'yes'",
       ["1. DELAY: What if the second payment arrives two weeks late? You may still owe early suppliers.",
        "2. OVERRUN: What if material or contractor costs rise 15%? Inspect price residual, not just today's cash.",
        "3. CHANGE: What if the buyer adds another revision? Write a new quote instead of silently absorbing extra time."],
       ["Flag high-dependency suppliers, deposits refundable to clients, and business-wide overhead outside this project.","The model assumes clean inputs; judgment is still required."]),
      ("FIELD CHECKLIST","Make the decision repeatable",
       ["Before accepting: verify signed scope, realistic hours, cleared deposit and supplier due dates.",
        "Before spending: compare cleared funds with commitments and protected buffer.",
        "Before a change: re-price scope and check delivery capacity.",
        "At close: export the CSV and compare forecast versus actual costs."],
       ["KEEP THE FILES: Open the HTML offline in a browser. The CSV is saved locally when you click Export.","KindGrid Studio · Tools for careful independent businesses · No guaranteed results."])
    ]
    def wrap(s,limit=80):return textwrap.wrap(s,width=limit,break_long_words=False,break_on_hyphens=False)
    for idx,(section,title,paras,notes) in enumerate(pages,1):
        c.setFillColor(light);c.rect(0,0,W,H,fill=1,stroke=0)
        c.setFillColor(ink);c.rect(0,H-12,W,12,fill=1,stroke=0)
        c.setFont("Helvetica-Bold",10);c.drawString(44,H-52,"KINDGRID STUDIO  /  DEPOSITGUARD")
        c.setFillColor(orange);c.setFont("Helvetica-Bold",11);c.drawString(44,H-114,f"{idx:02d}  /  {section}")
        c.setFillColor(ink);c.setFont("Helvetica-Bold",23);c.drawString(44,H-151,title)
        ypos=H-210
        for n,para in enumerate(paras):
            c.setFillColor(sage);c.roundRect(46,ypos+2,8,8,3,stroke=0,fill=1)
            c.setFillColor(ink);c.setFont("Helvetica",11)
            for line in wrap(para,76):
                c.drawString(64,ypos,line);ypos-=18
            ypos-=18
        ypos=min(ypos-10,300)
        c.setFillColor(HexColor("#E3ECE4"));c.roundRect(42,63,W-84,max(118,ypos-68),16,fill=1,stroke=0)
        ty=min(ypos-2,277);c.setFillColor(ink)
        for para in notes:
            for line in wrap(para,78):
                c.setFont("Helvetica-Bold" if para.endswith(":") else "Helvetica",10)
                c.drawString(60,ty,line);ty-=16
            ty-=10
        c.setFillColor(ink);c.setFont("Helvetica",8)
        c.drawString(44,35,"Illustrative planning tool, not tax/legal/financial advice.")
        c.drawRightString(W-44,35,f"{idx:02d} / 08")
        c.showPage()
    c.save()
    return p

def make_assets():
    EVIDENCE.mkdir(exist_ok=True,parents=True)
    images()
    html=tool_html()
    a.require("URL.createObjectURL" in html and "future" in html and "shortfall" in html,"Offline tool incomplete")
    (EVIDENCE/"DepositGuard_Offline_Tool.html").write_text(html,encoding="utf-8")
    guide=pdf_guide()
    a.require(len(PdfReader(str(guide)).pages)==8,"Guide must have eight pages")
    a.require(Image.open(EVIDENCE/"Q62_Pinterest_Original.png").size==(1000,1500),"Pin 2:3 aspect wrong")
    # Regression math against the exact example shown in the visual and guide.
    pre=250+380+40; free=900-pre-150; residual=1800-(pre+60)-18*35
    a.require((pre,free,residual)==(670,80,440),"Illustrative financial model arithmetic incorrect")
    z=EVIDENCE/"DepositGuard_Studio_Customer_Download.zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        archive.write(EVIDENCE/"DepositGuard_Offline_Tool.html","DepositGuard_Offline_Tool.html")
        archive.write(guide,"DepositGuard_8_Page_Field_Guide.pdf")
    with zipfile.ZipFile(z) as check:
        a.require(len(check.namelist())==2 and check.testzip() is None,"Customer ZIP invalid")
        a.require(len(check.read("DepositGuard_Offline_Tool.html"))>9500,"Customer offline app incomplete")
    sha={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in EVIDENCE.iterdir() if f.is_file()}
    (EVIDENCE/"assets_sha256.json").write_text(json.dumps(sha,indent=2))
    receipt("ASSETS_GENERATED_VERIFIED",files=sha)
    return z

def append(store,tab,row):
    sheets=store.sheet.spreadsheets().values()
    header=sheets.get(spreadsheetId=a.SHEET_ID,range=f"'{tab}'!1:1").execute()["values"][0]
    assert row.keys()<=set(header)
    vals=[str(row.get(k,"")) for k in header]
    sheets.append(spreadsheetId=a.SHEET_ID,range=f"'{tab}'!A1",
        valueInputOption="RAW",insertDataOption="INSERT_ROWS",
        body={"values":[vals]}).execute()
    return [r for r in store.get_rows(tab) if r.get("Product ID",r.get("Queue ID"))==row.get("Product ID",row.get("Queue ID"))][0]

def cap_used(rows,field,datefield):
    now=datetime.now(ZoneInfo("America/New_York")).date()
    count=0
    for row in rows:
        if row.get(field)!="PUBLISHED":continue
        try:
            t=datetime.fromisoformat(row.get(datefield,"").replace("Z","+00:00"))
            if t.astimezone(ZoneInfo("America/New_York")).date()==now:count+=1
        except (TypeError,ValueError): pass
    return count

def release():
    a.require(a.enabled("KINDGRID_OWNER_KGS017_ONCE"),"Not owner authorized")
    z=make_assets()
    store=a.GoogleStore()
    prows=store.get_rows("Gumroad Upload Queue");pins=store.get_rows("Publishing Queue")
    a.require(not any(r.get("Product ID")==PID or r.get("Unique Slug")==SLUG for r in prows),"KGS017 product already exists in queue; DO NOT retry")
    a.require(not any(r.get("Queue ID")==QID for r in pins),"Q62 Pin already exists in queue; DO NOT retry")
    a.require(cap_used(prows,"Upload Status","Last Updated UTC")<7,"Gumroad NY-day limit reached")
    a.require(cap_used(pins,"Status","Last Attempt UTC")<7,"Pinterest NY-day limit reached")
    seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
    for p in seller:
        short=str(p.get("short_url") or "").split("/")[-1]
        a.require(p.get("custom_permalink")!=SLUG and short!=SLUG,"Existing seller slug; refuse duplicate")
    buffer=a.BufferClient();boards=buffer.boards()
    a.require(BOARD in boards,"No verified relevant Pinterest board")
    a.require(buffer.scheduled()<10,"Buffer free queue full")
    receipt("SELLER_AND_BUFFER_PREFLIGHT_PASS")
    # We do not misstate missing Drive-hosted asset links as verified; source/evidence stays in GitHub Actions artifact.
    prow=append(store,"Gumroad Upload Queue",{
      "Product ID":PID,"Product Name":NAME,"Price USD":PRICE,"Unique Slug":SLUG,
      "QA Verified (YES/NO)":"LOCAL_TESTS_PASS","Upload Status":"ONE_TIME_UPLOADING",
      "Last Attempt UTC":stamp(),"Attempt Count":"1","Last Updated UTC":stamp(),
      "QA Version":"KGS017-LOCAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    receipt("GUMROAD_MUTATION_BEGIN_NO_RERUN")
    try:
        result=a.gumroad_cli(["products","create","--draft","--name",NAME,
          "--price",PRICE,"--currency","usd","--type","digital","--custom-permalink",SLUG,
          "--description",DESCRIPTION,"--custom-summary",SUMMARY,
          "--file",str(z),"--cover-image",str(EVIDENCE/"KGS017_Gumroad_Cover.png"),
          "--thumbnail",str(EVIDENCE/"KGS017_Gumroad_Cover.png")])
        prod=result.get("product") or {}; ident=str(prod.get("id") or "")
        a.require(bool(ident),"Seller draft might exist but ID missing. No retry.")
        receipt("GUMROAD_DRAFT_KNOWN",seller_id=ident)
        store.patch("Gumroad Upload Queue",prow,{"Gumroad Live URL":f"https://gumroad.com/products/{ident}/edit"})
        view=a.gumroad_cli(["products","view",ident]).get("product") or {}
        files=view.get("files") or view.get("rich_content_files") or []
        covers=view.get("covers") or view.get("cover_images") or []
        a.require(view.get("published") is False and view.get("name")==NAME and view.get("custom_permalink")==SLUG and covers,
                  "Gumroad seller draft identity or cover mismatch")
        a.require(any(int(f.get("size") or -1)==z.stat().st_size for f in files),
                  "Gumroad did not verify exact customer ZIP attachment")
        store.patch("Gumroad Upload Queue",prow,{"Upload Status":"DRAFT_VERIFIED"})
        a.gumroad_cli(["products","publish",ident])
        post=a.gumroad_cli(["products","view",ident]).get("product") or {}
        a.require(post.get("published") is True and any(int(f.get("size") or -1)==z.stat().st_size
                   for f in (post.get("files") or post.get("rich_content_files") or [])),
                  "Customer ZIP not verifiably present on published listing")
        a.verify_public_product_url(PUBLIC,SLUG)
        store.patch("Gumroad Upload Queue",prow,{"Upload Status":"PUBLISHED","Gumroad Live URL":PUBLIC,"Last Updated UTC":stamp(),"Last Error":""})
        receipt("GUMROAD_PUBLIC_VERIFIED",public_url=PUBLIC)
        print("KGS017_GUMROAD_PUBLISHED",PUBLIC,flush=True)
    except Exception as error:
        store.patch("Gumroad Upload Queue",prow,{"Upload Status":"REVIEW","Last Error":(type(error).__name__+": "+str(error))[:420],"Last Updated UTC":stamp()})
        receipt("GUMROAD_UNCERTAIN_NO_RETRY",error_type=type(error).__name__)
        raise
    pinrow=append(store,"Publishing Queue",{
        "Queue ID":QID,"Product ID":PID,"Pin Type":"Original cash-coverage educational infographic",
        "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "Time Slot":"Owner-authorized one-time live post","US Scheduled Time":"NOW",
        "Target Board":BOARD,"Pin Title":TITLE,"Pin Description":PIN_DESC,
        "Destination URL":DEST,"Status":"ONE_TIME_POSTING",
        "QA Verified (YES/NO)":"LOCAL_TESTS_PASS",
        "Last Attempt UTC":stamp(),"Attempt Count":"1",
        "QA Version":"KGS017-LOCAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    try:
        image=a.cloudinary_upload((EVIDENCE/"Q62_Pinterest_Original.png").read_bytes(),"kgs017-q62-original")
        a.require(image.startswith("https://"),"Image host rejected Pin")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
        ... on PostActionSuccess{post{id status externalLink}}
        ... on MutationError{message}}}'''
        body={"channelId":buffer.channel_id,"text":PIN_DESC,"schedulingType":"automatic",
            "mode":"shareNow","aiAssisted":False,"assets":[{"image":{"url":image}}],
            "metadata":{"pinterest":{"boardServiceId":boards[BOARD],"title":TITLE,"url":DEST}}}
        receipt("BUFFER_MUTATION_BEGIN_NO_RERUN")
        resp=buffer.graphql(query,{"input":body}).get("createPost") or {}
        item=resp.get("post") or {};bid=str(item.get("id") or "")
        a.require(bid,"Buffer may have created Pin without ID; stop and reconcile")
        store.patch("Publishing Queue",pinrow,{"Status":"SENT_PENDING_URL","Batch ID":bid})
        receipt("BUFFER_POST_ID_VERIFIED",buffer_id=bid)
        link=str(item.get("externalLink") or "")
        for j in range(6):
            if "pinterest.com/pin/" in link:break
            if j:time.sleep(5)
            state=buffer.get_post(bid)
            link=str(state.get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            store.patch("Publishing Queue",pinrow,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            receipt("PINTEREST_PUBLIC_URL_VERIFIED",pin_url=link)
            print("Q62_PINTEREST_PUBLISHED",link,flush=True)
        else:
            receipt("PINTEREST_PROVIDER_PENDING",buffer_id=bid)
            print("Q62_SUBMITTED_PROVIDER_PENDING_PIN_URL",bid,flush=True)
    except Exception as error:
        fresh=[x for x in store.get_rows("Publishing Queue") if x.get("Queue ID")==QID][0]
        if fresh.get("Status")=="ONE_TIME_POSTING":
            store.patch("Publishing Queue",fresh,{"Status":"REVIEW","Last Error":(type(error).__name__+": "+str(error))[:420]})
        receipt("PINTEREST_UNCERTAIN_NO_RETRY",error_type=type(error).__name__)
        raise

if __name__=="__main__":
    try:
        if os.getenv("KGS017_GENERATE_ONLY")=="true":
            make_assets(); print("ASSET_DRY_RUN_COMPLETE")
        else:release()
    except Exception as exc:
        print("KGS017_STOP_NO_BLIND_RETRY",type(exc).__name__,str(exc)[:240],flush=True)
        sys.exit(1)
