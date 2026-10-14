"""Owner-authorized one-time original ScopePulse offline tool and QA-gated Gumroad/Buffer release.

Strict one-create rule. A nonzero Gumroad CLI exit after create causes seller readback,
not a second create. Never upload the same Pin twice.
"""
from __future__ import annotations
import csv, hashlib, io, json, os, sys, time, textwrap, zipfile
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from src import autopilot as a
from scripts import kgs017_depositguard_once as g

PID="KGS-018";QID="Q-63";SLUG="scopepulse-revision-pricing-studio"
NAME="ScopePulse Studio | Revision Pricing & Scope-Change Decision System"
PRICE="12.00";PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
PIN_TITLE="Client Asked for 3 More Revisions? Quote the Real Cost"
PIN_DESC=("A 'quick extra revision' can consume your entire profit. "
 "This example shows how a designer can price 3 added revision rounds with time, "
 "direct costs, contingency and a target margin. Includes an original offline "
 "revision-pricing dashboard and eight-page field guide. Example only.")
DEST=PUBLIC+"?utm_source=pinterest&utm_medium=organic&utm_campaign=scopepulse_launch&utm_content=q63"
EVIDENCE=Path("kindgrid-kgs018-evidence")
SUMMARY="An offline revision-quote and delivery-capacity calculator for freelancers with an illustrated eight-page guide."
DESC="""ScopePulse Studio turns vague 'one more quick change' requests into measurable scope decisions.

WHAT YOU GET
• A custom-built offline interactive HTML dashboard with zero logins, subscriptions, macros or data collection.
• Track included versus used revision rounds, estimate the requested extra hours and distinguish included work from out-of-scope rounds.
• Calculate a suggested change-order fee from labor effort, external expenses, a contingency allowance and a TARGET MARGIN, not an ambiguous markup.
• Compare the extra work against your remaining available hours, including a clear capacity overrun indicator.
• Model a higher-hour revision scenario and see how your effective economics change.
• Export your project assumptions and results to a simple CSV for your records.
• An eight-page illustrated US Letter field guide, step-by-step fictional worked case, scope clarification script and decision checklist.

This system is for freelancers, designers, writers, photographers, consultants and other solo service providers. It is specifically about change requests and time-bound capacity; it is NOT an invoicing app, a client portal or an automatic email service.

HOW TO USE
Unzip the download and open ScopePulse_Offline_Tool.html in a modern browser; it runs on your computer without sending any information to us. Follow the eight-page PDF guide for the worked example.

IMPORTANT
Examples and pricing outputs are illustrative and depend on your own inputs. The model assumes explicitly approved, out-of-scope changes can be separately priced; your contract and client agreement determine what may actually be charged. The quoted result is a scenario estimate, not a legal right, profit guarantee or tax-adjusted earnings amount.

Created by KindGrid Studio for thoughtful independent businesses."""

def note(state,**info):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    p=EVIDENCE/"receipt.json"
    try: obj=json.loads(p.read_text()) if p.exists() else {}
    except Exception:obj={}
    obj.update(info);obj.update({"state":state,"utc":a.make_timestamp()})
    p.write_text(json.dumps(obj,indent=2),encoding="utf-8")
    print("KGS018_STAGE "+state,flush=True)

def asset_images():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    ink="#193D43";cream="#F7F5EF";lilac="#D6D8E8";white="#FFFFFF";coral="#B66A51";silver="#DEE5E5"
    p=Image.new("RGB",(1000,1500),cream);d=ImageDraw.Draw(p)
    d.rectangle((0,0,1000,20),fill=ink)
    d.text((82,77),"KINDGRID STUDIO / FIELD NOTES",font=g.font(27,True),fill=ink)
    d.text((82,173),"CLIENT SCOPE CONTROL",font=g.font(23,True),fill=coral)
    y=g.multiline(d,(82,250),"3 extra revisions are not 'just a quick change.'",840,63,ink,1.25,True)
    d.text((82,y+25),"ILLUSTRATIVE DESIGN PROJECT",font=g.font(23,True),fill=ink)
    d.rounded_rectangle((64,y+86,936,y+525),radius=30,fill=white)
    vals=[("Revision rounds included","2"),("Revision rounds already used","2"),
        ("Additional rounds requested","3"),("Time per round","2.5 h")]
    yy=y+122
    for name,val in vals:
        d.text((112,yy),name,font=g.font(25),fill=ink)
        d.text((796,yy),val,font=g.font(32,True),fill=ink)
        yy+=92;d.line((110,yy-20,890,yy-20),fill=silver,width=2)
    d.rounded_rectangle((92,y+557,908,y+751),radius=30,fill=ink)
    d.text((127,y+588),"ESTIMATED CHANGE-ORDER QUOTE",font=g.font(24,True),fill="#D6E9E8")
    d.text((124,y+633),"$583",font=g.font(79,True),fill=white)
    d.text((82,1317),"Time. Extra costs. Profit margin.",font=g.font(31,True),fill=ink)
    d.text((82,1370),"SCOPEPULSE / OFFLINE PRICING TOOL",font=g.font(25),fill=ink)
    p.save(EVIDENCE/"Q63_ScopePulse_Original_Pin.png",optimize=True)
    cv=Image.new("RGB",(1600,900),cream);x=ImageDraw.Draw(cv)
    x.rectangle((0,0,24,900),fill=ink)
    x.text((100,100),"KINDGRID STUDIO  /  INDEPENDENT WORK SYSTEMS",font=g.font(30,True),fill=ink)
    x.text((102,270),"SCOPEPULSE",font=g.font(105,True),fill=ink)
    x.text((107,429),"REVISION PRICING & CAPACITY STUDIO",font=g.font(39),fill=ink)
    g.multiline(x,(108,541),"Know when a small client change needs a new quote.",900,34,ink,1.5)
    x.rounded_rectangle((106,741,1071,814),radius=20,fill=lilac)
    x.text((144,755),"OFFLINE DASHBOARD + 8-PAGE ILLUSTRATED GUIDE",font=g.font(26,True),fill=ink)
    for j,h in enumerate([150,230,330,415]):
        xx=1160+j*92
        x.rounded_rectangle((xx,770-h,xx+62,770),radius=13,fill=[lilac,ink,coral,lilac][j])
    cv.save(EVIDENCE/"KGS018_ScopePulse_Gumroad_Cover.png",optimize=True)
    return p,cv

def html_tool():
    return r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScopePulse Studio / KindGrid</title>
<style>
:root{--ink:#193d43;--paper:#f7f5ef;--lilac:#e5e7f0;--line:#d1d9d9;--orange:#b66a51}
*{box-sizing:border-box}body{font:16px/1.5 system-ui,-apple-system,Segoe UI,Arial,sans-serif;margin:0;background:var(--paper);color:var(--ink)}
header{background:var(--ink);color:white;padding:37px max(24px,calc((100vw - 1180px)/2));}
header small{letter-spacing:2.5px;color:#d1e3e3}
h1{font-size:clamp(42px,6vw,68px);line-height:1.02;letter-spacing:-2px;margin:20px 0 10px}
header p{max-width:750px;color:#d9e9e9;font-size:17px}
main{max-width:1180px;margin:auto;padding:25px 24px 68px}
.strap{max-width:790px;font-size:18px}
.layout{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}
.card{background:#fff;border:1px solid var(--line);box-shadow:0 8px 32px #12373210;border-radius:18px;padding:28px}
h2{font-size:23px;margin:0 0 8px}
h3{font-size:18px;margin-top:20px}
label{font-size:13px;font-weight:700;display:block;margin:13px 0 6px}
input{width:100%;padding:12px;border:1px solid #9ab0ad;border-radius:9px;font:inherit;color:var(--ink);background:white}
input:focus,button:focus{outline:3px solid #a9c5ce;outline-offset:2px}
small,.fine{font-size:13px;color:#5c7174}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.stat{background:#eef1f3;border-radius:13px;padding:18px;margin:10px 0}
.stat span{display:block;font-size:13px}.stat b{font-size:29px;font-variant-numeric:tabular-nums}
.stat.key{background:var(--lilac)}.stat.alert{background:#f8e5dd;color:#8b4939}
.divider{border-top:1px solid var(--line);margin:21px 0}
button{font:inherit;background:var(--ink);border:0;border-radius:9px;color:white;font-weight:700;padding:13px 24px;cursor:pointer}
.note{border-left:4px solid var(--orange);padding:2px 0 2px 16px;margin-top:25px;color:#536b6c}
footer{text-align:center;color:#6c7a7a;border-top:1px solid var(--line);padding:22px;font-size:12px}
@media(max-width:800px){.layout,.grid{grid-template-columns:1fr}}
@media print{header{background:white;color:var(--ink)}button{display:none}}
</style></head><body>
<header><small>KINDGRID STUDIO / SMALL BUSINESS TOOLKIT</small>
<h1>ScopePulse.</h1>
<p>Every extra revision spends time. Check whether it is included, what a fair change-order scenario might cost, and whether you have capacity to deliver.</p></header>
<main>
<p class="strap">For independent service providers. This offline tool doesn't contact a server or save your project details online. Use fictional example numbers until you are ready to enter a real project.</p>
<div class="layout"><section class="card"><h2>01 / Existing agreement</h2>
<p class="fine">Document the signed scope separately. Input only revision rounds, not every tiny adjustment.</p>
<div class="grid">
<div><label for="included">Included revision rounds</label><input id="included" type="number" min="0" step="1" value="2"></div>
<div><label for="used">Rounds already completed</label><input id="used" type="number" min="0" step="1" value="2"></div>
<div><label for="request">New revision rounds requested</label><input id="request" type="number" min="0" step="1" value="3"></div>
<div><label for="hours">Estimated work hours per round</label><input id="hours" type="number" min="0" step="0.25" value="2.5"></div>
<div><label for="rate">Your internal labor value ($/hour)</label><input id="rate" type="number" min="0" step="0.01" value="45"></div>
<div><label for="external">Extra outside costs ($)</label><input id="external" type="number" min="0" step="0.01" value="60"></div>
<div><label for="contingency">Cost contingency (%)</label><input id="contingency" type="number" min="0" max="80" step="0.5" value="10"></div>
<div><label for="margin">Target contribution margin (%)</label><input id="margin" type="number" min="0" max="80" step="1" value="25"></div>
<div><label for="capacity">Hours available this delivery window</label><input id="capacity" type="number" min="0" step="0.25" value="5"></div>
<div><label for="stress">Extra hours per change in stress case</label><input id="stress" type="number" min="0" step="0.25" value="1"></div>
</div>
<p class="note">An included round is still real work, but it is not automatically billable as an extra. Separately agreed changes outside the signed scope may require a new quote.</p>
</section><section class="card"><h2>02 / Change-order decision</h2>
<div class="stat key"><span>Illustrative out-of-scope change-order quote</span><b id="quote">$0</b><small>Direct labor + costs + contingency, divided by 1 − target margin</small></div>
<div class="grid">
<div class="stat"><span>Revision rounds still included</span><b id="remaining">0</b></div>
<div class="stat"><span>Potentially chargeable rounds</span><b id="billable">0</b></div>
<div class="stat"><span>Total new work time</span><b id="newtime">0 h</b></div>
<div class="stat"><span>Additional time beyond capacity</span><b id="over">0 h</b></div>
<div class="stat"><span>Expected direct cost + contingency</span><b id="cost">$0</b></div>
<div class="stat"><span>Stress-case change-order quote</span><b id="stressquote">$0</b></div>
</div><p id="signal" class="note" role="status">Enter your project figures.</p>
<div class="divider"></div><button id="save">Export this scenario as CSV</button>
<p class="fine">A suggested quote is not a right to bill. It only applies when a scope change is contractually and commercially approved. Consider tax and overhead separately.</p>
</section></div>
<section class="card" style="margin-top:24px"><h2>03 / How the numbers work</h2>
<p><strong>Included left:</strong> the greater of zero and agreed included rounds minus used rounds. <strong>Billable:</strong> the greater of zero and requested rounds minus included rounds left.</p>
<p><strong>Requested work time:</strong> all new requested rounds × hours per round. <strong>Quote:</strong> for out-of-scope rounds only, estimate labor hours × your target labor value, add outside costs, apply contingency, then divide by (1 − target contribution margin).</p>
<p><strong>Capacity:</strong> all new work hours count toward the delivery window, whether billable or included. If the window is too small, discuss a revised deadline or smaller scope before agreeing.</p>
<p class="fine">The CSV export records only the values in this browser session. No personal details are collected or transmitted.</p></section>
</main><footer>© KindGrid Studio · Offline-only scenario calculator · Educational pricing and capacity planning, not legal or tax advice.</footer>
<script>
(function(){"use strict";
const keys=["included","used","request","hours","rate","external","contingency","margin","capacity","stress"];
const el=id=>document.getElementById(id);
const fmt=x=>"$"+Math.max(0,x).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
let saved={};
function calculate(){
let v={};for(let k of keys){let n=Number(el(k).value);v[k]=Number.isFinite(n)?Math.max(0,n):0}
v.included=Math.floor(v.included);v.used=Math.floor(v.used);v.request=Math.floor(v.request);
v.contingency=Math.min(80,v.contingency);v.margin=Math.min(80,v.margin);
const remaining=Math.max(0,v.included-v.used);
const billable=Math.max(0,v.request-remaining);
const work=v.request*v.hours;
const paidHours=billable*v.hours;
const cost=paidHours*v.rate+(billable>0?v.external:0);
const allowed=cost*(1+v.contingency/100);
const quote=allowed/(1-v.margin/100);
const stressCost=billable*(v.hours+v.stress)*v.rate+(billable>0?v.external:0);
const stressQuote=stressCost*(1+v.contingency/100)/(1-v.margin/100);
const overflow=Math.max(0,work-v.capacity);
el("remaining").textContent=remaining;
el("billable").textContent=billable;
el("newtime").textContent=work.toFixed(1)+" h";
el("over").textContent=overflow.toFixed(1)+" h";
el("cost").textContent=fmt(allowed);
el("quote").textContent=fmt(quote);
el("stressquote").textContent=fmt(stressQuote);
let msg=(billable===0?"All requested rounds are currently inside the agreed included-round count. ":
"Some rounds exceed the included-round count; clarify scope and obtain written approval before quoting. ");
msg+=overflow>0?"The current delivery window is short by "+overflow.toFixed(1)+" working hours.":
"The requested work fits within the hours you entered.";
el("signal").textContent=msg;
el("over").parentElement.className="stat"+(overflow>0?" alert":"");
saved={...v,remaining_included_rounds:remaining,billable_rounds:billable,
new_work_hours:work,delivery_hours_gap:overflow,estimated_direct_cost:cost,
cost_including_contingency:allowed,illustrative_quote:quote,stress_case_quote:stressQuote};
}
keys.forEach(k=>el(k).addEventListener("input",calculate));
el("save").addEventListener("click",()=>{
const rows=["metric,value"].concat(Object.entries(saved).map(([k,v])=>k+","+v));
const blob=new Blob([rows.join("\r\n")],{type:"text/csv;charset=utf-8"});
const u=URL.createObjectURL(blob),a=document.createElement("a");
a.href=u;a.download="ScopePulse_Change_Order_Scenario.csv";a.click();URL.revokeObjectURL(u);
});
calculate();
})();
</script></body></html>'''

def pdf_guide():
    pdf=EVIDENCE/"ScopePulse_8_Page_Field_Guide.pdf"
    can=canvas.Canvas(str(pdf),pagesize=letter)
    ink=HexColor("#193D43");cream=HexColor("#F7F5EF");coral=HexColor("#B66A51");lilac=HexColor("#E5E7F0")
    pages=[
      ("GET ORIENTED","The hidden cost of one more revision",[
        "A project can still be popular with clients and underpay you when requests expand beyond the priced scope.",
        "ScopePulse isolates the hours inside your original agreement from hours newly requested outside that agreement.",
        "Use it before replying to a new round of changes—not after you have already committed to free extra work."],[
        "Try the dashboard with the fictional design brief before using a real contract.",
        "Never send the tool's calculated amount to a client without checking the scope and agreement."]),
      ("THE FIVE STEPS","Run a change request through one page",[
        "1. Confirm how many formal revision rounds the original agreement includes.",
        "2. Count completed rounds and record the client's new requested rounds.",
        "3. Estimate hours per new round and any outside vendor costs.",
        "4. Enter a cautious contingency and your target contribution margin.",
        "5. Check available working hours before accepting a deadline."],[
        "Keep a dated written change record with the exact deliverables affected.",
        "Request approval for any revised fee or deadline before starting extra work."]),
      ("WORKED EXAMPLE","Why three changes can mean $583",[
        "Fictional brand designer: two included rounds; two already completed; three more requested.",
        "Each new round takes 2.5 hours at an internal $45 hourly value.",
        "Added outside costs are $60. Contingency is 10%. Target contribution margin is 25%.",
        "Chargeable work cost: 3 × 2.5 × $45 + $60 = $397.50.",
        "Cost including contingency: $397.50 × 1.10 = $437.25.",
        "Illustrative quote: $437.25 ÷ (1 − 0.25) = $583.00."],[
        "The result is a pricing scenario, not a contractually owed amount.",
        "Avoid saying 'guaranteed profit': overhead, taxes and change complexity remain unknown."]),
      ("REVISIONS","What's included versus newly billable?",[
        "Included rounds remaining = max(0, included rounds − already used rounds).",
        "Potentially chargeable rounds = max(0, new rounds − included rounds remaining).",
        "Even included rounds still consume working hours and can create a deadline problem.",
        "Track the client's change request by round, not by the number of individual comments."],[
        "A large scope change can be outside the agreed scope even if revision rounds remain.",
        "A trivial typo fix may be nonbillable despite exhausted rounds. Use contract judgment."]),
      ("PRICE LOGIC","Margin is not the same as markup",[
        "First estimate incremental out-of-scope work cost: paid hours × your target hourly value, plus vendor costs.",
        "Add a contingency allowance for minor uncertainty.",
        "Target-margin quote = cost including contingency ÷ (1 − target margin rate).",
        "Illustration: $437.25 at a 25% target margin requires $583.00, not $546.56.",
        "The model does not automatically include taxes, payment collection fees or general overhead."],[
        "Keep your margin assumption realistic and disclose external costs when appropriate.",
        "If costs could change materially, use a fixed cap or phased approval."]),
      ("TIME TEST","A profitable add-on can miss the deadline",[
        "New hours required = all requested rounds × hours per round, including rounds that remain included.",
        "Time overflow = max(0, new hours required − available delivery-window hours).",
        "Worked case: 3 rounds × 2.5 hours = 7.5 hours.",
        "Only 5 hours are available this week; the shortfall is 2.5 hours.",
        "A positive price outcome does not make an impossible timeline achievable."],[
        "Offer a later deadline, reduce deliverables or secure additional capacity.",
        "Check your own availability, not theoretical full workday hours."]),
      ("WORDS TO USE","Three short client responses",[
        "Clarify: 'I can confirm the next changes. Are these edits to the approved version or a new direction?'",
        "Quote: 'The requested additions add [hours] and [deliverables]. I can provide an updated scope and fee for approval.'",
        "Schedule: 'I can include this work if we adjust the delivery date to [date]. Would that work for your launch?'",
        "Document new rounds and paid milestones before accepting the request."],[
        "These are professional communication examples, not legal contract templates.",
        "Maintain a respectful tone: visibility of work can strengthen the relationship."]),
      ("MAKE IT A SYSTEM","Your weekly change-control checklist",[
        "Keep one row or folder for each active project and its agreed revision allowance.",
        "Run ScopePulse as soon as changes are requested; save the CSV with the date.",
        "Review overrun hours and pricing before promising an updated deliverable.",
        "After completion, compare hours estimated with hours spent to improve future quotes.",
        "Store the signed scope, client approvals and any invoices outside the app."],[
        "The HTML calculator works entirely offline; it does not keep a client database.",
        "KindGrid Studio / Original planning tool. Example figures are fictional."])
    ]
    W,H=letter
    for idx,(slug,title,paragraphs,notes) in enumerate(pages,1):
        can.setFillColor(cream);can.rect(0,0,W,H,fill=1,stroke=0)
        can.setFillColor(ink);can.rect(0,H-13,W,13,fill=1,stroke=0)
        can.setFillColor(ink);can.setFont("Helvetica-Bold",10)
        can.drawString(44,H-52,"KINDGRID STUDIO  /  SCOPEPULSE")
        can.setFillColor(coral);can.setFont("Helvetica-Bold",11)
        can.drawString(44,H-114,str(idx).zfill(2)+"  /  "+slug)
        can.setFillColor(ink);can.setFont("Helvetica-Bold",22)
        can.drawString(44,H-147,title)
        y=H-206
        for line in paragraphs:
            can.setFillColor(lilac);can.roundRect(45,y-2,8,8,3,stroke=0,fill=1)
            can.setFillColor(ink);can.setFont("Helvetica",10.5)
            for fragment in textwrap.wrap(line,width=86,break_long_words=False):
                can.drawString(64,y,fragment);y-=16
            y-=19
        y=min(y-5,300)
        can.setFillColor(lilac);can.roundRect(41,72,W-82,max(104,y-73),17,stroke=0,fill=1)
        ny=min(y-7,280)
        for paragraph in notes:
            can.setFillColor(ink);can.setFont("Helvetica",10)
            for line in textwrap.wrap(paragraph,width=84):
                can.drawString(57,ny,line);ny-=15
            ny-=10
        can.setFont("Helvetica",8);can.drawString(44,39,"Illustrative examples, not legal or tax advice.")
        can.drawRightString(W-43,39,f"{idx:02d} / 08")
        can.showPage()
    can.save()
    return pdf

def build_assets():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    asset_images()
    html=html_tool()
    assert "URL.createObjectURL" in html and "stressQuote" in html and "Math.max" in html
    (EVIDENCE/"ScopePulse_Offline_Tool.html").write_text(html,encoding="utf-8")
    pdf=pdf_guide()
    assert len(PdfReader(str(pdf)).pages)==8
    assert Image.open(EVIDENCE/"Q63_ScopePulse_Original_Pin.png").size==(1000,1500)
    assert Image.open(EVIDENCE/"KGS018_ScopePulse_Gumroad_Cover.png").size==(1600,900)
    cost=3*2.5*45+60
    quote=cost*1.1/(1-0.25)
    assert cost==397.5 and round(quote,2)==583 and round(3*2.5-5,2)==2.5
    archive=EVIDENCE/"ScopePulse_Original_Customer_Download.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(EVIDENCE/"ScopePulse_Offline_Tool.html","ScopePulse_Offline_Tool.html")
        z.write(pdf,"ScopePulse_8_Page_Field_Guide.pdf")
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==2 and z.testzip() is None
        assert len(z.read("ScopePulse_Offline_Tool.html"))>8500
    note("ORIGINAL_ASSETS_PASS",archive_bytes=archive.stat().st_size,
         pin_sha256=hashlib.sha256((EVIDENCE/"Q63_ScopePulse_Original_Pin.png").read_bytes()).hexdigest(),
         zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    return archive

def single(s,tab,key,val):
    out=[x for x in s.get_rows(tab) if x.get(key)==val]
    a.require(len(out)==1,"Missing/duplicate "+val+" in "+tab)
    return out[0]

def append(s,tab,values):
    header=s.sheet.spreadsheets().values().get(spreadsheetId=a.SHEET_ID,range=f"'{tab}'!1:1").execute()["values"][0]
    a.require(set(values)<=set(header),"Queue headers changed: "+str(set(values)-set(header)))
    s.sheet.spreadsheets().values().append(spreadsheetId=a.SHEET_ID,
      range=f"'{tab}'!A1",valueInputOption="RAW",insertDataOption="INSERT_ROWS",
      body={"values":[[str(values.get(k,"")) for k in header]]}).execute()
    return single(s,tab,"Product ID" if tab.startswith("Gumroad") else "Queue ID",
                  values.get("Product ID",values.get("Queue ID")))

def seller_match(seller):
    return [p for p in seller if str(p.get("custom_permalink") or "")==SLUG or
        str(p.get("short_url") or "").rstrip("/").endswith("/"+SLUG)]

def main():
    a.require(a.enabled("KINDGRID_SCOPEPULSE_ONETIME"),"Owner release not enabled")
    archive=build_assets()
    s=a.GoogleStore()
    product_rows=s.get_rows("Gumroad Upload Queue")
    pin_rows=s.get_rows("Publishing Queue")
    a.require(not any(r.get("Product ID")==PID or r.get("Unique Slug")==SLUG for r in product_rows),
              "Existing product row: refuse any duplicate create")
    a.require(not any(r.get("Queue ID")==QID or r.get("Destination URL","").startswith(PUBLIC)
                      for r in pin_rows),"Pin/destination already exists")
    a.require(g.cap_used(product_rows,"Upload Status","Last Updated UTC")<7,"Gumroad NY cap seven reached")
    a.require(g.cap_used(pin_rows,"Status","Last Attempt UTC")<7,"Pinterest NY cap seven reached")
    seller=a.gumroad_cli(["products","list","--all"]).get("products",[])
    a.require(not seller_match(seller),"Duplicate seller slug exists")
    b=a.BufferClient();boards=b.boards()
    preferred=sorted([n for n in boards if any(w in n.lower() for w in
         ("business","freelanc","finance","budget","pricing"))],
         key=lambda n:0 if ("freelanc" in n.lower() or "business" in n.lower()) else 1)
    a.require(bool(preferred),"No verified relevant Pinterest board")
    board=preferred[0]
    a.require(b.scheduled()<10,"Free Buffer queue full")
    note("SELLER_NO_DUPLICATE_AND_BUFFER_PREFLIGHT_PASS",board=board)
    row=append(s,"Gumroad Upload Queue",{
        "Product ID":PID,"Product Name":NAME,"Price USD":PRICE,"Unique Slug":SLUG,
        "QA Verified (YES/NO)":"INTERNAL_TESTS_PASS",
        "Upload Status":"ONE_TIME_CREATING","Last Attempt UTC":a.make_timestamp(),
        "Attempt Count":"1","Last Updated UTC":a.make_timestamp(),
        "QA Version":"KGS018-INTERNAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    note("ONE_TIME_CREATE_ATTEMPTED_NO_DUPLICATE")
    try:
        try:
            response=a.gumroad_cli(["products","create","--draft","--name",NAME,
               "--price",PRICE,"--currency","usd","--type","digital",
               "--custom-permalink",SLUG,"--description",DESC,"--custom-summary",SUMMARY,
               "--file",str(archive),
               "--cover-image",str(EVIDENCE/"KGS018_ScopePulse_Gumroad_Cover.png"),
               "--thumbnail",str(EVIDENCE/"KGS018_ScopePulse_Gumroad_Cover.png")])
            created_id=str((response.get("product") or {}).get("id") or "")
        except Exception as exc:
            # The Gumroad CLI sometimes reports a post-create error after the exact draft
            # and customer attachment are already created. Read seller, NEVER recreate.
            note("CREATE_RESPONSE_UNCERTAIN_READ_SELLER_ONLY",error_type=type(exc).__name__)
            created_id=""
        matching=seller_match(a.gumroad_cli(["products","list","--all"]).get("products",[]))
        a.require(len(matching)==1,"Seller did not return exactly one reconciled original draft")
        seller_id=str(matching[0].get("id") or "")
        a.require(bool(seller_id) and (not created_id or seller_id==created_id),
                  "Seller identity mismatch after first create")
        view=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
        attached=view.get("files") or view.get("rich_content_files") or []
        covers=view.get("covers") or view.get("cover_images") or []
        a.require(view.get("published") is False and view.get("name")==NAME
               and view.get("custom_permalink")==SLUG,"Wrong seller draft identity")
        a.require(len(attached)==1 and int(attached[0].get("size") or -1)==archive.stat().st_size,
                  "Exact customer ZIP not uploaded (hold; never blind retry)")
        a.require(bool(covers),"Seller cover not uploaded")
        try:
            rich=a.gumroad_cli(["products","content","get",seller_id])
            pages=rich if isinstance(rich,list) else rich.get("rich_content",[]) if isinstance(rich,dict) else []
            embeds=[str(n.get("attrs",{}).get("id") or "") for part in pages
                for n in (part.get("description") or {}).get("content") or [] if n.get("type")=="fileEmbed"]
            a.require(embeds==[str(attached[0].get("id") or "")],"Customer download is not embedded in product delivery")
        except ValueError:raise
        note("SELLER_EXACT_DRAFT_ZIP_COVER_DELIVERY_PASS",seller_id=seller_id)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"DRAFT_VERIFIED",
                "Gumroad Live URL":"https://gumroad.com/products/"+seller_id+"/edit"})
    except Exception as error:
        latest=single(s,"Gumroad Upload Queue","Product ID",PID)
        s.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW",
            "Last Error":(type(error).__name__+": "+str(error))[:390],
            "Last Updated UTC":a.make_timestamp()})
        note("SELLER_DRAFT_UNCERTAIN_STOP",error_type=type(error).__name__)
        raise
    note("GUMROAD_PUBLISH_EXACT_DRAFT_ONCE",seller_id=seller_id)
    try:
        a.gumroad_cli(["products","publish",seller_id])
        live=a.gumroad_cli(["products","view",seller_id]).get("product") or {}
        files=live.get("files") or live.get("rich_content_files") or []
        a.require(live.get("published") is True and len(files)==1
                  and int(files[0].get("size") or -1)==archive.stat().st_size,
                  "Live customer asset not verified")
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED_CHECK_URL",
                "Gumroad Live URL":PUBLIC})
        a.verify_public_product_url(PUBLIC,SLUG)
        s.patch("Gumroad Upload Queue",row,{"Upload Status":"PUBLISHED",
            "Gumroad Live URL":PUBLIC,"Last Error":"","Last Updated UTC":a.make_timestamp()})
        note("GUMROAD_PUBLIC_AND_SINGLE_ZIP_VERIFIED",product_url=PUBLIC)
        print("KGS018_GUMROAD_PUBLISHED "+PUBLIC,flush=True)
    except Exception as error:
        latest=single(s,"Gumroad Upload Queue","Product ID",PID)
        if latest.get("Upload Status")=="DRAFT_VERIFIED":
            s.patch("Gumroad Upload Queue",latest,{"Upload Status":"REVIEW",
                "Last Error":str(error)[:380]})
        note("GUMROAD_PUBLICATION_UNCERTAIN_DO_NOT_RETRY",error_type=type(error).__name__)
        raise
    q=append(s,"Publishing Queue",{
        "Queue ID":QID,"Product":PID,"Content Type":"Original illustrative revision-pricing infographic",
        "Scheduled Date":datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "Time Window":"Owner one-time immediate release","US Scheduled Time":"NOW",
        "Target Board":board,"Pin Title":PIN_TITLE,"Pin Description":PIN_DESC,
        "Destination URL":DEST,"Status":"ONE_TIME_POSTING",
        "QA Verified (YES/NO)":"INTERNAL_TESTS_PASS",
        "Last Attempt UTC":a.make_timestamp(),"Attempt Count":"1",
        "QA Version":"KGS018-INTERNAL-1","QA Outcome":"PENDING_INDEPENDENT_VISUAL_REVIEW"})
    try:
        img=a.cloudinary_upload((EVIDENCE/"Q63_ScopePulse_Original_Pin.png").read_bytes(),
                   "kgs018-q63-scopepulse-original-20261014")
        a.require(img.startswith("https://"),"Pin media hosting failed")
        query='''mutation P($input:CreatePostInput!){createPost(input:$input){
          ... on PostActionSuccess{post{id status externalLink}}
          ... on MutationError{message}}}'''
        payload={"channelId":b.channel_id,"text":PIN_DESC,"schedulingType":"automatic",
          "mode":"shareNow","aiAssisted":False,
          "assets":[{"image":{"url":img}}],
          "metadata":{"pinterest":{"boardServiceId":boards[board],
              "title":PIN_TITLE,"url":DEST}}}
        note("BUFFER_ONE_TIME_CREATE_ATTEMPTED")
        result=b.graphql(query,{"input":payload}).get("createPost") or {}
        obj=result.get("post") or {};ident=str(obj.get("id") or "")
        a.require(bool(ident),"Buffer may have accepted submission; provider ID unknown")
        s.patch("Publishing Queue",q,{"Status":"SENT_PENDING_URL","Batch ID":ident})
        note("BUFFER_PIN_ID_CONFIRMED",buffer_id=ident)
        link=str(obj.get("externalLink") or "")
        for j in range(6):
            if "pinterest.com/pin/" in link:break
            if j:time.sleep(4)
            link=str(b.get_post(ident).get("externalLink") or "")
        if "pinterest.com/pin/" in link:
            s.patch("Publishing Queue",q,{"Status":"PUBLISHED","Actual Pinterest Pin URL":link})
            note("PINTEREST_PUBLIC_VERIFIED",pin_url=link)
            print("Q63_PINTEREST_PUBLISHED "+link,flush=True)
        else:
            note("PINTEREST_BUFFER_SENT_LINK_PENDING",buffer_id=ident)
            print("Q63_BUFFER_PENDING "+ident,flush=True)
    except Exception as e:
        latest=single(s,"Publishing Queue","Queue ID",QID)
        if latest.get("Status")=="ONE_TIME_POSTING":
            s.patch("Publishing Queue",latest,{"Status":"REVIEW","Last Error":str(e)[:400]})
        note("PINTEREST_UNCERTAIN_DO_NOT_RESUBMIT",error_type=type(e).__name__)
        raise

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("KGS018_SAFE_RELEASE_STOP "+type(e).__name__+" "+str(e)[:280],flush=True)
        sys.exit(1)
