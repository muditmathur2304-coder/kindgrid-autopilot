"""KindGrid KGS019 MoveMargin: original 2-scenario offline moving budget tool and assets.
Build-only; no provider access. All prices are fictional examples, not market data.
"""
import hashlib, io, json, zipfile, textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader

OUT=Path("kindgrid-kgs019-build")
NAME="MoveMargin Studio | Moving Quote Comparison & Cash-Ready Planner"
SLUG="movemargin-moving-cash-planner"
PRICE="16.00"
PID="KGS-019"
QID="Q-64"
PUBLIC="https://kindgridstudio.gumroad.com/l/"+SLUG
TITLE="Moving Cost Reality: $1,110 DIY vs $1,875 Movers"
DESC_PIN=("Your moving quote isn't your total move-in budget. In this fictional example, "
 "$1,110 DIY costs versus $1,875 full-service logistics become $5,040 versus $5,805 "
 "when you include new security deposit, overlapping rent, setup fees and a protected cash buffer. "
 "Explore an original editable offline moving-cost comparison and 10-page illustrated guide. "
 "Example only; not a real carrier quote.")
DEST=PUBLIC+"?utm_source=pinterest&utm_medium=organic&utm_campaign=movemargin&utm_content=q64"
SUMMARY="A private offline moving-budget comparison system, editable two-option cashflow dashboard, 15% stress test, and original ten-page illustrated guide."
DESCRIPTION="""The moving quote is not the amount of money you need for your move.

MoveMargin Studio is a purpose-built offline decision tool for US households and renters who want to compare DIY/truck rental with a professional moving service without forgetting housing transition expenses.

Inside your purchase:
• An original interactive offline HTML dashboard with editable cost breakdowns for BOTH moving options.
• Clear full move-in cash calculations including security deposit, overlapping rent, utility setup, cleaning, and a protected buffer.
• Cash-on-hand sufficiency and shortfall indicators, a customizable logistics overrun stress test, and an old-deposit-refund field kept OUT of today's spendable cash.
• Private browser-local saving, one-click CSV export, a print view and resettable worked example. No login, subscription, macros or server tracking.
• An original ten-page illustrated US Letter field guide with quote checklists, mathematical walkthrough, scenario comparisons and timeline.

Worked example figures are fictional: $1,110 truck-plus-DIY logistics versus $1,875 full service, increasing to $5,040 versus $5,805 after transition costs and a protected reserve.

HOW TO USE: Unzip and open MoveMargin_Offline_Planner.html in a modern browser, enter real provider quotes and household commitments, and use the companion PDF as a guide.

IMPORTANT: It does not provide live or verified moving prices, booking, insurance, legal or financial advice. Estimates vary by provider, dates, market and contract. Confirm coverage, mileage, stairs, fees and due dates with the actual provider. Anticipated old security-deposit refunds are excluded from spendable funds until received.

KindGrid Studio — original systems for real-life decisions."""
INK="#243F3D";PAPER="#F7F5F0";MOSS="#618473";MIST="#E3EBE4";RUST="#B07053";WHITE="#FFFFFF";LINE="#DBE2D9"
DEMO_A=[450,160,75,240,90,95];DEMO_B=[1250,175,125,85,160,80]
def fonts(sz,bold=False):
    fs=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for f in fs:
        if Path(f).exists():return ImageFont.truetype(f,sz)
    return ImageFont.load_default()
def wrapped(d,x,y,txt,maxw,sz=27,bold=False,color=INK):
    f=fonts(sz,bold);w=""
    for word in txt.split():
        t=(w+" "+word).strip()
        if d.textbbox((0,0),t,font=f)[2]>maxw and w:
            d.text((x,y),w,font=f,fill=color);y+=int(sz*1.43);w=word
        else:w=t
    if w:d.text((x,y),w,font=f,fill=color);y+=int(sz*1.43)
    return y
def art():
    OUT.mkdir(exist_ok=True,parents=True)
    pin=Image.new("RGB",(1000,1500),PAPER);d=ImageDraw.Draw(pin)
    d.rectangle((0,0,1000,20),fill=INK)
    d.text((72,74),"KINDGRID STUDIO  /  MONEY IN MOTION",font=fonts(25,True),fill=INK)
    d.text((75,170),"MOVING COST REALITY",font=fonts(25,True),fill=RUST)
    y=wrapped(d,75,250,"The moving quote is not your move-in budget.",850,57,True)+50
    d.text((75,y),"ILLUSTRATIVE LOGISTICS QUOTES",font=fonts(24,True),fill=INK)
    y+=64
    for x,lab,amt in [(73,"DIY + TRUCK","$1,110"),(516,"FULL SERVICE","$1,875")]:
        d.rounded_rectangle((x,y,x+414,y+208),radius=28,fill=WHITE)
        d.text((x+22,y+28),lab,font=fonts(25,True),fill=INK)
        d.text((x+22,y+97),amt,font=fonts(55,True),fill=INK)
    y+=235;d.text((75,y),"PLUS THESE SHARED COMMITMENTS",font=fonts(24,True),fill=INK);y+=60
    for label,value in [("New security deposit","$1,600"),("Overlapping rent","$1,200"),
      ("Setup and cleaning","$430"),("Protected cash buffer","$700")]:
        d.text((88,y),label,font=fonts(25),fill=INK)
        d.text((765,y),value,font=fonts(26,True),fill=INK)
        d.line((85,y+56,913,y+56),fill=LINE,width=2);y+=73
    y+=14;d.rounded_rectangle((70,y,930,y+205),radius=26,fill=INK)
    d.text((110,y+25),"TOTAL CASH TO BE READY",font=fonts(25,True),fill="#E0ECE4")
    d.text((110,y+78),"$5,040",font=fonts(65,True),fill=WHITE)
    d.text((544,y+78),"$5,805",font=fonts(65,True),fill="#F3D5C4")
    d.text((115,y+167),"DIY",font=fonts(23,True),fill=WHITE)
    d.text((546,y+167),"MOVERS",font=fonts(23,True),fill=WHITE)
    d.text((76,1363),"Compare quotes. Protect your cash.",font=fonts(28,True),fill=INK)
    d.text((76,1417),"MOVEMARGIN  /  OFFLINE TOOL + GUIDE",font=fonts(23),fill=INK)
    pin.save(OUT/"Q64_MoveMargin_Original_2x3.png",optimize=True)
    cover=Image.new("RGB",(1600,900),PAPER);c=ImageDraw.Draw(cover)
    c.rectangle((0,0,25,900),fill=INK)
    c.text((114,113),"KINDGRID STUDIO   /   DECISION TOOLS",font=fonts(30,True),fill=INK)
    c.text((114,270),"MoveMargin.",font=fonts(112,True),fill=INK)
    c.text((117,446),"MOVING QUOTE & CASH-READY STUDIO",font=fonts(41,True),fill=RUST)
    wrapped(c,118,560,"The actual cost of moving, before you sign.",900,35)
    c.rounded_rectangle((114,741,1080,816),radius=20,fill=MIST)
    c.text((146,756),"OFFLINE DASHBOARD  +  10-PAGE GUIDE",font=fonts(28,True),fill=INK)
    for i,h in enumerate([145,250,325,426]):
        x=1191+i*86;c.rounded_rectangle((x,760-h,x+53,760),radius=14,fill=[MOSS,INK,RUST,MOSS][i])
    cover.save(OUT/"KGS019_Gumroad_Cover.png",optimize=True)
    # Editorial proof/gallery: showing the product's actual calculations.
    preview=Image.new("RGB",(1600,900),PAPER);v=ImageDraw.Draw(preview)
    v.text((90,79),"TWO QUOTES. ONE CASH DECISION.",font=fonts(44,True),fill=INK)
    v.text((96,155),"FICTIONAL WORKED EXAMPLE / USD",font=fonts(26,True),fill=RUST)
    for i,(lab,amount,color) in enumerate([("DIY + TRUCK",5040,INK),("PROFESSIONAL MOVERS",5805,RUST)]):
        y=293+i*225
        v.text((111,y-50),lab,font=fonts(29,True),fill=INK)
        v.rounded_rectangle((110,y,1420,y+78),radius=19,fill=MIST)
        v.rounded_rectangle((110,y,110+int(1310*amount/6500),y+78),radius=19,fill=color)
        v.text((1150,y+105),"$"+format(amount,",.0f"),font=fonts(31,True),fill=INK)
    v.text((113,817),"Includes security, rent overlap, utility setup, cleaning and reserve.",font=fonts(24),fill=INK)
    preview.save(OUT/"KGS019_Gallery_Real_Cash_Need.png",optimize=True)
    flow=Image.new("RGB",(1600,900),PAPER);f=ImageDraw.Draw(flow)
    f.text((101,72),"BUILT FOR REAL DECISIONS",font=fonts(46,True),fill=INK)
    f.text((103,145),"A four-stage moving cash-control system",font=fonts(29),fill=RUST)
    for j,(name,detail) in enumerate([
       ("01 / QUOTE BREAKDOWN","Itemize both real moving offers"),
       ("02 / HOUSING TRANSITION","Add lease and setup obligations"),
       ("03 / CASH SUFFICIENCY","Keep the protected buffer"),
       ("04 / UNCERTAINTY TEST","Apply a logistics overrun")]):
        x=96+(j%2)*712;y=261+(j//2)*282
        f.rounded_rectangle((x,y,x+667,y+239),radius=22,fill=WHITE)
        f.text((x+30,y+45),name,font=fonts(26,True),fill=INK)
        wrapped(f,x+30,y+118,detail,615,27)
    flow.save(OUT/"KGS019_Gallery_Workflow.png",optimize=True)

def html_source():
    return r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MoveMargin | KindGrid Studio</title><style>
:root{--ink:#243f3d;--paper:#f7f5f0;--mist:#e3ebe4;--rust:#b07053;--line:#dbe2d9}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,Arial,sans-serif}
header{background:var(--ink);color:white;padding:40px max(20px,calc((100vw - 1200px)/2))}
header small{letter-spacing:2.3px;color:#d6e6de}h1{font-size:clamp(43px,6vw,70px);margin:13px 0 5px;letter-spacing:-2px}
header p{max-width:690px;font-size:18px;color:#e2ece7}main{max-width:1200px;margin:auto;padding:26px 22px 68px}
.layout{display:grid;grid-template-columns:1.12fr .88fr;gap:24px;align-items:start}
.card{background:white;border:1px solid var(--line);border-radius:18px;padding:27px;box-shadow:0 6px 26px #172f290b}
h2{font-size:23px;margin:0 0 11px}h3{font-size:18px;margin:19px 0 10px}
.fields,.pair{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
label{font-size:12px;font-weight:700;display:block;margin:12px 0 5px}
input{padding:12px;font:inherit;width:100%;border:1px solid #9eb3a7;border-radius:8px;color:var(--ink);background:white}
input:focus,button:focus{outline:3px solid #a1beb0;outline-offset:2px}
.metric{border-radius:12px;background:var(--mist);padding:16px;margin:10px 0}
.metric span{font-size:13px;display:block}.metric b{font-size:29px;font-variant-numeric:tabular-nums}
.metric.dark{background:var(--ink);color:white}.metric.warn{background:#f6e4da;color:#863f2d}
small,.muted{font-size:13px;color:#667b6e}
button{background:var(--ink);border:0;border-radius:9px;padding:13px 18px;color:white;font:inherit;font-weight:700;cursor:pointer;margin:4px 4px 4px 0}
button.alt{background:var(--mist);color:var(--ink)}
.note{margin-top:17px;border-left:4px solid var(--rust);padding:5px 0 5px 15px;color:#52695c}
hr{border:0;border-top:1px solid var(--line);margin:23px 0}
.bar{height:17px;border-radius:12px;background:var(--mist);overflow:hidden;margin:10px 0 21px}.bar div{height:100%;background:#618473}
footer{text-align:center;color:#718175;font-size:13px;border-top:1px solid var(--line);padding:20px}
@media(max-width:790px){.layout,.pair,.fields{grid-template-columns:1fr}}
@media print{button{display:none}header{background:white;color:var(--ink)}header p,header small{color:var(--ink)}}
</style></head><body><header><small>KINDGRID STUDIO  /  CASH DECISION TOOLS</small><h1>MoveMargin.</h1><p>Compare a DIY move with professional movers. See the payments a quote can leave out—and what remains of your cash buffer.</p></header>
<main><p>All initial dollar values are fictional. Replace with quotes from real providers and the actual expenses of changing homes. Your edits stay in this browser.</p>
<div class="layout"><div class="card"><h2>01 / Logistics choices</h2><div class="pair"><div><h3>DIY + truck</h3>
<label for="a0">Truck rental ($)</label><input type="number" min="0" step=".01" id="a0" value="450">
<label for="a1">Fuel/mileage ($)</label><input type="number" min="0" step=".01" id="a1" value="160">
<label for="a2">Boxes/supplies ($)</label><input type="number" min="0" step=".01" id="a2" value="75">
<label for="a3">Helpers/labor ($)</label><input type="number" min="0" step=".01" id="a3" value="240">
<label for="a4">Coverage ($)</label><input type="number" min="0" step=".01" id="a4" value="90">
<label for="a5">Other fees ($)</label><input type="number" min="0" step=".01" id="a5" value="95"></div>
<div><h3>Full-service movers</h3>
<label for="b0">Company base ($)</label><input type="number" min="0" step=".01" id="b0" value="1250">
<label for="b1">Travel/mileage ($)</label><input type="number" min="0" step=".01" id="b1" value="175">
<label for="b2">Stairs/extra fees ($)</label><input type="number" min="0" step=".01" id="b2" value="125">
<label for="b3">Packing materials ($)</label><input type="number" min="0" step=".01" id="b3" value="85">
<label for="b4">Tips allowance ($)</label><input type="number" min="0" step=".01" id="b4" value="160">
<label for="b5">Coverage/other ($)</label><input type="number" min="0" step=".01" id="b5" value="80"></div></div>
<hr><h2>02 / Home-transition cash</h2><div class="fields">
<div><label for="deposit">New security deposit</label><input id="deposit" type="number" min="0" step=".01" value="1600"></div>
<div><label for="overlap">Overlapping rent</label><input id="overlap" type="number" min="0" step=".01" value="1200"></div>
<div><label for="setup">Utilities/setup</label><input id="setup" type="number" min="0" step=".01" value="250"></div>
<div><label for="cleaning">Cleaning / repairs</label><input id="cleaning" type="number" min="0" step=".01" value="180"></div>
<div><label for="buffer">Protected cash reserve</label><input id="buffer" type="number" min="0" step=".01" value="700"></div>
<div><label for="cash">Cash already available</label><input id="cash" type="number" min="0" step=".01" value="5300"></div>
<div><label for="refund">Old deposit expected later</label><input id="refund" type="number" min="0" step=".01" value="1200"></div>
<div><label for="stress">Logistics overrun stress (%)</label><input id="stress" type="number" min="0" max="100" step=".5" value="15"></div>
</div><p class="note">An expected old-deposit refund is NOT added to today's available cash. Refund eligibility and payment timing vary; do not depend on funds you haven't received.</p>
<button id="save">Save locally</button><button class="alt" id="export">Export CSV</button><button class="alt" id="print">Print</button><button class="alt" id="reset">Reset</button>
<p class="muted" id="saveMsg">No account, network connection or analytics tracking. Saved data stays in this browser.</p>
</div><div class="card"><h2>03 / Cash decision dashboard</h2>
<div class="pair"><div class="metric"><span>DIY logistics</span><b id="totalA">$0</b></div><div class="metric"><span>Full-service logistics</span><b id="totalB">$0</b></div></div>
<div class="metric"><span>Shared home-transition costs</span><b id="shared">$0</b></div>
<div class="pair"><div class="metric dark"><span>DIY total cash needed</span><b id="needA">$0</b></div><div class="metric dark"><span>Movers cash needed</span><b id="needB">$0</b></div></div>
<div class="pair"><div class="metric" id="boxA"><span>DIY cash left or gap</span><b id="leftA">$0</b></div><div class="metric" id="boxB"><span>Movers cash left or gap</span><b id="leftB">$0</b></div></div>
<h3>Relative required cash</h3><label>DIY + truck</label><div class="bar"><div id="barA"></div></div>
<label>Professional movers</label><div class="bar"><div id="barB"></div></div>
<h3>04 / What if costs climb?</h3><div class="pair">
<div class="metric"><span>DIY stressed total</span><b id="stressA">$0</b></div>
<div class="metric"><span>Movers stressed total</span><b id="stressB">$0</b></div></div>
<div class="metric"><span>Old deposit expected (not cleared)</span><b id="future">$0</b></div>
<p class="note" id="decision"></p>
<p class="muted">The stress percentage is applied ONLY to logistics costs. Security, overlap rent, setup and reserve are not inflated. Verify actual payment due dates separately.</p></div></div>
<div class="card" style="margin-top:24px"><h2>Quote checklist</h2><p>Before signing: review binding vs nonbinding estimates, minimum hours, travel, fuel, stairs, parking, long carries, packing materials, excluded work, coverage/deductibles and cancellation terms. This is a budgeting model, not a provider recommendation or a legally binding quote.</p></div>
</main><footer>© KindGrid Studio · Original offline planning system · Fictional example, not financial, moving or legal advice.</footer>
<script>(function(){"use strict";
const names=["a0","a1","a2","a3","a4","a5","b0","b1","b2","b3","b4","b5","deposit","overlap","setup","cleaning","buffer","cash","refund","stress"];
const initial={a0:450,a1:160,a2:75,a3:240,a4:90,a5:95,b0:1250,b1:175,b2:125,b3:85,b4:160,b5:80,deposit:1600,overlap:1200,setup:250,cleaning:180,buffer:700,cash:5300,refund:1200,stress:15};
const el=id=>document.getElementById(id);
const usd=x=>(x<0?"−":"")+"$"+Math.abs(x).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
let final={};
function update(){
let v={};names.forEach(k=>{const n=Number(el(k).value);v[k]=Number.isFinite(n)?Math.max(0,n):0;});
v.stress=Math.min(100,v.stress);
const a=[0,1,2,3,4,5].reduce((t,i)=>t+v["a"+i],0),b=[0,1,2,3,4,5].reduce((t,i)=>t+v["b"+i],0);
const common=v.deposit+v.overlap+v.setup+v.cleaning;
const needA=a+common+v.buffer,needB=b+common+v.buffer;
const leftA=v.cash-needA,leftB=v.cash-needB;
const stressA=a*(1+v.stress/100)+common+v.buffer;
const stressB=b*(1+v.stress/100)+common+v.buffer;
[["totalA",a],["totalB",b],["shared",common],["needA",needA],["needB",needB],
["leftA",leftA],["leftB",leftB],["stressA",stressA],["stressB",stressB],["future",v.refund]]
.forEach(pair=>el(pair[0]).textContent=usd(pair[1]));
el("boxA").className="metric"+(leftA<0?" warn":"");el("boxB").className="metric"+(leftB<0?" warn":"");
const denom=Math.max(needA,needB,v.cash,1);
el("barA").style.width=(needA/denom*100)+"%";el("barB").style.width=(needB/denom*100)+"%";
let msg="With your cleared cash, ";
if(leftA>=0&&leftB>=0)msg+="both options cover their modeled costs and protected buffer.";
else if(leftA>=0)msg+="DIY appears funded, while movers have a "+usd(-leftB)+" gap.";
else if(leftB>=0)msg+="movers appear funded, while DIY has a "+usd(-leftA)+" gap.";
else msg+="both options exceed the modeled available cash.";
el("decision").textContent=msg+" Check real payment timing and quote exclusions.";
final={...v,diy_logistics:a,movers_logistics:b,shared_transition:common,diy_cash_required:needA,
movers_cash_required:needB,diy_cash_left:leftA,movers_cash_left:leftB,
diy_stress_requirement:stressA,movers_stress_requirement:stressB};
}
names.forEach(k=>el(k).addEventListener("input",update));
el("save").addEventListener("click",()=>{try{
localStorage.setItem("kindgrid_movemargin_v1",JSON.stringify(names.reduce((o,k)=>(o[k]=el(k).value,o),{})));
el("saveMsg").textContent="Saved on this browser only. Clear site data to remove it.";
}catch(err){el("saveMsg").textContent="Local save unavailable; use Export CSV."; }});
el("reset").addEventListener("click",()=>{names.forEach(k=>el(k).value=initial[k]);update();});
el("print").addEventListener("click",()=>window.print());
el("export").addEventListener("click",()=>{
const rows=["metric,value"].concat(Object.entries(final).map(pair=>pair[0]+","+pair[1]));
const blob=new Blob([rows.join("\r\n")],{type:"text/csv;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");
a.href=url;a.download="MoveMargin_Moving_Cash_Plan.csv";a.click();URL.revokeObjectURL(url);
});
try{const saved=JSON.parse(localStorage.getItem("kindgrid_movemargin_v1")||"null");
if(saved&&typeof saved==="object")names.forEach(k=>{if(Object.prototype.hasOwnProperty.call(saved,k))el(k).value=saved[k];});}catch(err){}
update();})();
</script></body></html>'''
def pdf():
    path=OUT/"MoveMargin_Illustrated_10_Page_Guide.pdf"
    pdf=canvas.Canvas(str(path),pagesize=letter);w,h=letter
    pages=[
("WELCOME","Your quote is not your cash need",[
"The carrier price is only one cost layer. A move may also need rent overlap, a new deposit, utility setup, cleaning and reserve cash.",
"MoveMargin separates the logistics decision from shared home-transition costs and expected future refunds.",
"Start with fictional inputs to understand the math; replace everything with verified provider quotes and your actual household figures."],
["THE QUOTE","IS NOT","THE BUDGET"]),
("COSTS","Compare two genuinely different quotes",[
"DIY case includes $450 truck, $160 fuel, $75 boxes, $240 helpers, $90 coverage and $95 other fees; total $1,110.",
"Full-service case includes $1,250 base, $175 travel, $125 stairs, $85 materials, $160 gratuities and $80 other coverage; total $1,875.",
"Service inclusions differ; compare itemized contracts, not just the headline prices."],
["DIY  $1,110","FULL SERVICE  $1,875","DIFFERENCE  $765"]),
("TRANSITION","Add the costs you can't ignore",[
"New lease deposit $1,600 and rent overlap $1,200 are included in the fictional worked case.",
"Utility setup $250 plus cleaning $180 raises shared transition costs to $3,230.",
"Keep a separate $700 protected buffer: this is cash you choose not to spend even after move-in."],
["SECURITY  $1,600","OVERLAP RENT  $1,200","SETUP + CLEANING  $430"]),
("RESULT","The two complete cash requirements",[
"DIY: $1,110 logistics + $3,230 transition + $700 protected cash = $5,040 required.",
"Movers: $1,875 logistics + $3,230 transition + $700 protected cash = $5,805 required.",
"With $5,300 actually available, DIY retains $260 and full-service has a $505 cash deficit."],
["DIY TOTAL  $5,040","MOVERS TOTAL  $5,805","AVAILABLE  $5,300"]),
("QUOTE AUDIT","Questions before signing",[
"Is the provider price binding, nonbinding, hourly, or subject to a minimum?",
"Ask about stairs, long carries, parking, special items, fuel, mileage, packing materials, minimum crew time and fees.",
"Clarify coverage, deductibles, damages process, cancellation terms and payment due dates in writing."],
["SERVICE SCOPE","ADDITIONAL FEES","WRITTEN TERMS"]),
("TIMING","Don't count an old deposit twice",[
"Your previous home deposit may be refunded after moving out; amount and timing are not guaranteed.",
"The calculator displays expected refund independently but excludes it from cash available for move-in.",
"Even a positive total cash balance does not prove you have enough on each intermediate payment date."],
["CLEARED CASH NOW","FUTURE REFUND LATER"]),
("STRESS TEST","What happens if quotes increase?",[
"Apply the customizable stress percentage only to logistics, not security deposits, rent overlap or the reserve.",
"At 15%, fictional DIY becomes $1,276.50 of logistics and a total $5,206.50.",
"The full-service logistics becomes $2,156.25 and total cash requirement $6,086.25."],
["DIY STRESSED  $5,206.50","MOVERS STRESSED  $6,086.25"]),
("30 DAY PLAN","Plan four checkpoints",[
"30 or more days: check lease dates and request equivalent written moving quotes.",
"14 days: verify elevator access, parking, coverage conditions, packing obligations and deposits.",
"7 days: reconfirm utilities, crew schedule, building move-in rules and payment dates.",
"48 hours: review actual cleared funds, essential documents and emergency cash."],
["30+ DAYS","14 DAYS","7 DAYS","48 HOURS"]),
("WORKFLOW","Use your offline product well",[
"Open the HTML file in a modern browser; all calculations run on your computer without a connection.",
"Edit both sets of logistics components and the shared housing items, then watch cash-gap values recalculate.",
"Save values locally, export CSV to share your assumptions, or print a one-page decision snapshot.",
"Read your actual contract. This model is not a moving booking, licensing or provider ratings service."],
["EDIT QUOTES","COMPARE CASH","SAVE + RECHECK"]),
("LIMITS","Use it as a decision aid",[
"All costs in the guide are fictional and are not a claim about actual moving company prices.",
"This is an educational budget planning aid rather than financial, legal, insurance or moving advice.",
"It cannot model every property rule, timing mismatch, dispute, non-financial consideration or tax consequence.",
"Before committing money, verify each price and due date independently with the real providers."],
["NO LIVE QUOTES","NO GUARANTEED SAVINGS","REAL CONTRACTS MATTER"])
]
    for idx,(label,title,paras,snaps) in enumerate(pages,1):
        pdf.setFillColor(HexColor(PAPER));pdf.rect(0,0,w,h,stroke=0,fill=1)
        pdf.setFillColor(HexColor(INK));pdf.rect(0,h-12,w,12,stroke=0,fill=1)
        pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica-Bold",10);pdf.drawString(46,h-50,"KINDGRID STUDIO / MOVEMARGIN")
        pdf.setFillColor(HexColor(RUST));pdf.setFont("Helvetica-Bold",11);pdf.drawString(46,h-110,str(idx).zfill(2)+"  /  "+label)
        pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica-Bold",22);pdf.drawString(46,h-147,title)
        py=h-214
        for p in paras:
            pdf.setFillColor(HexColor(MOSS));pdf.circle(53,py+4,3.4,fill=1,stroke=0)
            pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica",10.5)
            for line in textwrap.wrap(p,width=83,break_long_words=False):
                pdf.drawString(68,py,line);py-=18
            py-=19
        top=min(py-15,305)
        pdf.setFillColor(HexColor(MIST));pdf.roundRect(44,71,w-88,max(110,top-75),16,fill=1,stroke=0)
        pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica-Bold",11)
        pdf.drawString(66,top-20,"DECISION SNAPSHOT")
        for j,v in enumerate(snaps):
            if top-54-j*32<93:break
            pdf.setFillColor(HexColor(RUST));pdf.rect(66,top-57-j*32,6,11,stroke=0,fill=1)
            pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica-Bold",12)
            pdf.drawString(88,top-55-j*32,v)
        # Each relevant lesson includes a human-typeset numerical chart in the decision box.
        if idx in (2,4,7):
            pairs={2:[("DIY logistics",1110),("Movers logistics",1875)],
                   4:[("DIY full need",5040),("Movers full need",5805)],
                   7:[("DIY overrun",5206.5),("Movers overrun",6086.25)]}[idx]
            mx=max(value for _,value in pairs)
            by=top-155
            for ci,(name,value) in enumerate(pairs):
                ry=by-ci*44
                pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica",9)
                pdf.drawString(68,ry+21,name)
                pdf.setFillColor(HexColor(LINE));pdf.roundRect(68,ry,329,11,5.5,fill=1,stroke=0)
                pdf.setFillColor(HexColor(MOSS if ci==0 else RUST))
                pdf.roundRect(68,ry,329*value/mx,11,5.5,fill=1,stroke=0)
                pdf.setFont("Helvetica-Bold",9);pdf.setFillColor(HexColor(INK))
                pdf.drawRightString(519,ry+3,"$"+format(value,",.2f"))
        pdf.setFillColor(HexColor(INK));pdf.setFont("Helvetica",8)
        pdf.drawString(46,35,"Fictional worked case. Verify contracts, rates and real due dates.")
        pdf.drawRightString(w-46,35,f"{idx:02d} / 10")
        pdf.showPage()
    pdf.save();return path
def run():
    art()
    page=html_source()
    assert "localStorage" in page and "old deposit" in page.lower() and "stressA" in page
    (OUT/"MoveMargin_Offline_Planner.html").write_text(page,encoding="utf-8")
    guide=pdf()
    assert len(PdfReader(str(guide)).pages)==10
    checks=dict(diy=sum(DEMO_A),movers=sum(DEMO_B),transition=1600+1200+250+180,
        diy_required=1110+3230+700,movers_required=1875+3230+700,
        diy_remaining=5300-5040,movers_remaining=5300-5805,
        diy_stress=round(1110*1.15+3230+700,2),
        movers_stress=round(1875*1.15+3230+700,2))
    assert checks==dict(diy=1110,movers=1875,transition=3230,diy_required=5040,
        movers_required=5805,diy_remaining=260,movers_remaining=-505,
        diy_stress=5206.5,movers_stress=6086.25)
    for n,expected in [("Q64_MoveMargin_Original_2x3.png",(1000,1500)),
        ("KGS019_Gumroad_Cover.png",(1600,900)),
        ("KGS019_Gallery_Real_Cash_Need.png",(1600,900)),
        ("KGS019_Gallery_Workflow.png",(1600,900))]:
        assert Image.open(OUT/n).size==expected
    archive=OUT/"MoveMargin_Customer_Download.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.write(OUT/"MoveMargin_Offline_Planner.html","MoveMargin_Offline_Planner.html")
        z.write(guide,"MoveMargin_Illustrated_10_Page_Guide.pdf")
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==2
        assert len(z.read("MoveMargin_Offline_Planner.html"))>8500
    manifest={f.name:{"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()}
           for f in OUT.iterdir() if f.is_file()}
    (OUT/"KGS019_Creative_QA_Manifest.json").write_text(json.dumps({
        "product":PID,"pin":QID,"tested":checks,"assets":manifest,
        "qa_stage":"BUILD PASS -- NEEDS INDEPENDENT VISUAL INSPECTION"},indent=2))
    print("KGS019_BUILD_QA_PASS "+json.dumps({"product":PID,"pin":QID,"math":checks,
        "zip_bytes":archive.stat().st_size,"guide_pages":10,"image_count":4}),flush=True)
if __name__=="__main__":run()
