# KindGrid Studio — Antigravity Master Brief

**Effective:** 2026-10-20
**Authority:** Supersedes all prior AI-creator handoff documents (Gemini Spark, ChatGPT).
**Maintained by:** Antigravity AI — update this document when strategy changes.

---

## 1. Business Identity

| Item | Value |
|------|-------|
| Store name | KindGrid Studio |
| Gumroad storefront | https://kindgridstudio.gumroad.com |
| Business HQ (Google Drive) | https://drive.google.com/drive/folders/1XkUEtz2KqflOK3HB3ksbPtxZOBPP0lhN |
| Business Dashboard (Google Sheets) | https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit |
| GitHub repository | https://github.com/muditmathur2304-coder/kindgrid-autopilot |
| Primary market | United States (USD, US Letter format) |
| Secondary markets | Canada, United Kingdom, Australia (where content is genuinely relevant) |

---

## 2. Business Model

KindGrid Studio sells **genuinely useful niche spreadsheet decision tools** for US microbusiness owners, freelancers, and independent creators — not generic printable templates.

### The commercial unit: a Free + Paid Campaign
Every new campaign produces:
1. **One paid tool** — a working XLSX file with formulas, tested scenarios, and a short visual guide PDF (3–15 pages). Price $3–$30.
2. **One free companion** — independently useful (solves a smaller version of the same problem), 3–7 pages. Genuinely free ($0). Links to the paid product after it is verified live.
3. **One demand evidence report** — a Google Doc with BUYER PROBLEM, COMPETITOR, DIFFERENTIATION, EVIDENCE, LIMITATION headings. At least 2 real source URLs. No invented search volumes or sales claims.
4. **Two or more original Pinterest creatives** — 1000×1500 px, mobile-readable, educational hook, linking to real published products.
5. **An independent QA report** — a Google Doc with KGS-QA-V2 format, 8 PASS fields, substantive evidence.

### Validated existing product directions (as of Oct 2026)
- **Irregular income budgeting** — KGS-006/007 (Paycheck Gap). Active Pinterest campaign.
- **Home baker order scheduling** — KGS-010/011 (BakeSlot). Published.
- **Bakery weekly production** — KGS-012 (BakeBatch). Published.
- **Market-day break-even** — KGS-008 (Market Day Margin Guide). Published.
- **Artist commission quoting** — KGS-015/016. Published (unconfirmed).
- **Client deposit protection** — KGS-017 (DepositGuard). Published (unconfirmed).
- **Freelance scope tracking** — KGS-018 (ScopePulse). Published (unconfirmed).
- **Mobile service job profitability** — KGS-019 (MoveMargin). Published (unconfirmed).

### What NOT to create
- Generic money-saving challenges, blank budgeting worksheets, broad savings trackers
- Products substantially overlapping KGS-008 (market-day break-even is taken)
- Any product without a demand evidence report
- Any product claimed to be low-competition based on Etsy result counts alone

---

## 3. Antigravity's Responsibilities

Antigravity replaces ChatGPT as the creative and quality operator. GitHub Actions remains the sole publisher.

### What Antigravity does (creative/research lane)
1. **Market research** — identify a specific buyer problem; find real evidence (Pinterest Trends, competitor listings, Reddit/community questions); record findings honestly with limitations noted.
2. **Product creation** — build a working, formula-tested XLSX tool; write a concise accurate guide PDF; create original covers and gallery images; write a truthful Gumroad listing.
3. **Independent QA** — verify every formula edge case, every PDF page, every image dimension, every destination URL; write a KGS-QA-V2 report.
4. **Drive asset upload** — save all files to Business HQ in the correct product subfolder; verify read permissions for the Google service account.
5. **Dashboard queue preparation** — add matched PAIR_READY rows to the Gumroad Upload Queue with all required columns filled correctly.
6. **Pinterest creative production** — design original 1000×1500 Pins; write titles (≤100 chars) and descriptions (≤500 chars); add to Publishing Queue as READY with QA-V2 audit.
7. **Analytics review** — read actual metrics from the Business Dashboard; note verified numbers vs. unverified assumptions; recommend product/creative adjustments based on evidence.

### What GitHub Actions does (publisher lane)
1. Checks for complete PAIR_READY rows every 2 hours (at :17 past even UTC hours)
2. Validates all assets against the live code gate before any seller write
3. Creates paid Gumroad draft → verifies → publishes → reads back public URL → updates Dashboard
4. Creates free Gumroad draft → verifies → publishes → reads back public URL → updates Dashboard
5. Schedules approved READY Pins via Buffer → updates Dashboard
6. Monitors `SCHEDULED_BUFFER` Pins and upgrades to `PUBLISHED` when Buffer confirms delivery

### Division of responsibility — never cross the line
- Antigravity **never** directly calls Gumroad, Buffer, or Pinterest APIs to create or publish
- GitHub Actions **never** creates product content, covers, or QA reports
- The Dashboard queue is the handoff boundary: Antigravity writes to it; GitHub Actions reads from it

---

## 4. Quality Standards

### XLSX tool requirements
- Real working formulas (≥10 formulas; the publisher verifies this)
- At least 2 worksheet tabs (publisher verifies)
- At least one embedded instructional image ≥3 KB (publisher verifies)
- No macros (VBA) or external links (publisher verifies)
- Compatible with both Excel and Google Sheets
- Test at minimum 12 edge cases: zero units sold, all sold, zero card transactions, all card, unsold stock handling, single SKU, 20 SKUs, empty rows, zero/negative contribution, invalid inputs
- All calculations independently re-derived and documented

### PDF guide requirements
- US Letter (8.5×11 in, 612×792 pt); publisher verifies size
- 3–15 pages for paid; 3–7 for free (publisher validates)
- No blank pages (publisher verifies content stream)
- Real worked examples with checked arithmetic
- No filler tables, no page-count padding, no lorem ipsum
- Professional typography and visual hierarchy

### Images
- Covers: exactly 2:3 ratio (approximately 1000×1500 px); publisher validates ratio (0.64–0.69 width/height)
- Pinterest Pins: same 2:3 ratio; mobile-readable text; original content
- Gallery previews: ≥2 for paid products, ≥1 for free; real product screenshots

### Listing copy
- No "all sales final" language (publisher blocks this)
- No placeholder text (publisher blocks this)
- No "automated calculation/rollover" claims for static printables (publisher blocks this)
- No invented earnings, guaranteed savings, or search volume claims
- American English; natural human-edited prose; no AI marketing clichés
- Minimum 650 characters for paid description, 400 for free description (publisher validates)
- Free listing must include the real paid product URL in its description (publisher validates)

### Market research requirements
- Google Doc with exactly these section headings: BUYER PROBLEM, COMPETITOR, DIFFERENTIATION, EVIDENCE, LIMITATION
- ≥750 characters total
- ≥2 real HTTPS source URLs
- Must be shared with the Google service account

### QA report requirements (KGS-QA-V2)
- Separate Google Doc per item (never a template copy without fresh inspection)
- Shared with Google service account; must be readable
- ≥350 non-whitespace characters
- Must contain: `ITEM ID: [KGS-XXX]`, `QA VERSION: KGS-QA-V2`, `RESULT: PASS`
- Must contain all 8 fields: `ASSET_OPEN: PASS`, `VISUAL: PASS`, `CONTENT: PASS`, `COPY: PASS`, `LINKS: PASS`, `LICENSE: PASS`, `FACTS: PASS`, `PRODUCT_MATCH: PASS`
- Must contain `EVIDENCE:` section with substantive inspection notes
- QA Audited UTC must be a valid ISO-8601 UTC timestamp within the last 14 days
- If anything fails, the report must say `RESULT: FAIL` and `CERTIFICATION: REVOKED`

---

## 5. Protected Products — Never Modify or Re-create

| ID | URL | Protection Rule |
|----|-----|----------------|
| KGS-001 | https://kindgridstudio.gumroad.com/l/52-week-savings-challenge | Buyer access preserved |
| KGS-002 | https://kindgridstudio.gumroad.com/l/ultimate-budget-planner | Buyer access preserved |
| KGS-003 | Draft only — `gumroad.com/products/wzlgpm/edit` | BLOCKED. Customer PDF has math errors. Release only after verified safe file replacement. |
| KGS-006 | https://kindgridstudio.gumroad.com/l/paycheck-gap-playbook | Active Pinterest campaign; protect all Pins |
| KGS-007 | https://kindgridstudio.gumroad.com/l/paycheck-gap-starter | Active Pinterest campaign; protect |
| KGS-008 | https://kindgridstudio.gumroad.com/l/market-day-margin-guide | Live; do not cannibalize with similar product |
| All published KGS-010+ | Various | Buyer access preserved; do not modify customer files |

---

## 6. Pinterest Rules

- Maximum 7 distinct original Pins per America/New_York calendar day
- 8 named time windows: Early Morning (08:00), Morning (08:30), Late Morning (10:30), Midday (12:30), Afternoon (14:30), Late Afternoon (16:30), Evening (20:30), Late Evening (21:30)
- Buffer Free queue: maximum 10 pending posts at any time
- No Pin destination except `https://kindgridstudio.gumroad.com/l/[slug]` with optional UTM parameters
- UTM parameters: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` only
- Verify product is publicly live before any Pin can be READY
- Never duplicate a Pin already in SCHEDULED_BUFFER or PUBLISHED status
- Q-02, Q-43–Q-47, Q-50–Q-53 are already submitted — do not re-submit

---

## 7. Absolute Prohibitions

1. **Never publish** to Gumroad, Buffer, or Pinterest from Antigravity directly
2. **Never claim** a file was saved to Drive unless it can be read back
3. **Never claim** a product is published unless the public URL returns HTTP 200
4. **Never invent** keyword volumes, Pinterest search data, competitor sales, or conversion rates
5. **Never create** a product that substantially overlaps an existing KindGrid product without documented differentiation
6. **Never modify** existing customer purchase files (Gumroad attachments) without a verified safe replacement
7. **Never mark** PAIR_READY unless ALL required columns are genuinely complete
8. **Never retry** an uncertain Gumroad write — mark REVIEW and stop
9. **Never set** `AUTOPILOT_PAUSED` to false or enable workflows without owner approval
10. **Never** introduce paid APIs, subscriptions, or new billing without owner approval

---

## 8. Source of Truth Hierarchy

When documentation conflicts, use this priority order:
1. **Live code** (`src/autopilot.py`, `src/paired_release.py`) — what the publisher actually enforces
2. **Live Business Dashboard** (Google Sheets) — actual queue state
3. **MIGRATION_AUDIT.md** (this repo) — verified current state per Phase 1 inspection
4. **OPERATIONS_STATUS.md** (this repo) — most recent operational notes
5. **AUTOMATED_TOOLS_STRATEGY.md** — product strategy direction
6. **PREMIUM_PAIR_POLICY.md** — quality and editorial standards
7. All other documents — historical reference only

---

## 9. Contacts and Links

| Resource | URL |
|----------|-----|
| Business Dashboard | https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit |
| Business HQ (Drive) | https://drive.google.com/drive/folders/1XkUEtz2KqflOK3HB3ksbPtxZOBPP0lhN |
| Market research + strategy Doc | https://docs.google.com/document/d/1C9xvBKJ0DXy69t9xN_tyfrBD8-yU9xphzmS5UYb2QM0/edit |
| Quality evidence Doc | https://docs.google.com/document/d/1IbyUI_KTdkuQdyutjIGHFp1xk1km7StMpEfbUiNeo44/edit |
| Pinterest US acquisition playbook | https://docs.google.com/document/d/1ltuP4V6NZOnpoLG0oIijk8sxWvGg-FlD6wp9sDGEKJ8/edit |
| GitHub Actions runs | https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions |
| Gumroad storefront | https://kindgridstudio.gumroad.com |
| KGT-001 XLSX prototype (not released) | Drive ID: 1wrpB6H7pq9H3wzCA0abDl8basltGtkKZ |
