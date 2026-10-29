# KindGrid Studio — AGENTS.md
# Durable instructions for all future Antigravity agents

**Read this file at the start of every session.**
**Do not skip any section. Do not assume prior context.**

---

## What This Project Is

KindGrid Studio is a real digital-products business selling niche spreadsheet tools and guides on Gumroad, with Pinterest as the primary traffic channel. It is a live, revenue-generating business with real buyers. Actions taken here can affect real customers.

The repository at `c:\Users\mudit\OneDrive - abc\Documents\Github Automation\kindgrid-autopilot` (GitHub: `muditmathur2304-coder/kindgrid-autopilot`) is the automation engine. It does not contain the actual product files — those live in Google Drive.

---

## Orientation — Read These Files First

Before doing any work, always read:
1. `ANTIGRAVITY_MASTER_BRIEF.md` — business model, quality standards, prohibited actions
2. `MIGRATION_AUDIT.md` — verified current state of all products and workflows
3. `OPERATIONS_STATUS.md` — most recent operational notes and live incident records
4. `src/autopilot.py` — the actual publishing gate; this defines what the publisher enforces

---

## Role Division

| Actor | Responsibility | Can Write To |
|-------|---------------|-------------|
| **Antigravity** | Research, creation, QA, Drive upload, queue preparation | Google Drive (assets), Google Sheets (queue rows), this repository (code, docs) |
| **GitHub Actions** | Validation, Gumroad publishing, Pinterest scheduling | Gumroad (create/publish), Buffer (schedule), Google Sheets (status updates) |

**Never** have Antigravity directly call Gumroad, Buffer, or Pinterest APIs.
**Never** have GitHub Actions create product content.

---

## Known Product IDs — Never Reuse

KGS-001 through KGS-019 are assigned. The next unused ID depends on which products were actually published — **verify in the live Business Dashboard before assigning a new KGS number**.

The current code in `src/autopilot.py` protects only KGS-001–007 by hardcode. For KGS-008 onward, slug uniqueness is verified live against the Gumroad seller account at publish time.

---

## The Publishing Queue — How It Works

The Business Dashboard Google Sheet has two key tabs:
- **Gumroad Upload Queue** — one row per product. Publisher reads this.
- **Publishing Queue** — one row per Pinterest Pin. Publisher reads this.

### To queue a new paid+free product pair
Add exactly **two rows** to `Gumroad Upload Queue`:
- One row with `Pair Role = PAID`
- One row with `Pair Role = FREE`
- Both rows must have:
  - Same `Pair ID` (e.g., `PAIR-010`)
  - `Upload Status = PAIR_READY`
  - Reciprocal `Paired Product ID` values
  - `QA Verified (YES/NO) = YES`
  - `QA Version = KGS-QA-V2`
  - `QA Outcome = PASS`
  - Valid `QA Report Drive Link` (Google Doc)
  - `QA Audited UTC` within last 14 days (ISO-8601 UTC)
  - Valid `PDF Drive Link` (Google Drive file URL)
  - Valid `Cover Drive Link` (Google Drive PNG URL)
  - Valid `Bonus File Drive Link` for PAID product (Google Drive XLSX URL)
  - Valid `Listing Copy Drive Link` (Google Doc URL)
  - Valid `Visual Audit Contact Sheet Link` (Google Drive PNG URL)
  - Valid `Gallery Image 1 Drive Link` and `Gallery Image 2 Drive Link` (PAID)
  - Valid `Gallery Image 1 Drive Link` (FREE)
  - Valid `Demand Evidence Doc Link` (same Google Doc for both rows)
  - Unique `Unique Slug` (not previously used)
  - New `Product ID` (not previously used)

### To queue a Pinterest Pin
Add one row to `Publishing Queue`:
- `Status = READY`
- `QA Verified (YES/NO) = YES`
- All QA-V2 fields complete (see above pattern)
- `Queue ID` in format `Q-XXX` (never reuse a Q-ID)
- `Scheduled Date` in `YYYY-MM-DD` format
- `US Scheduled Time` in format `HH:MM EDT` or `HH:MM EST` (correct for the date)
- `Time Window` = one of: Early Morning, Morning, Late Morning, Midday, Afternoon, Late Afternoon, Evening, Late Evening
- `Target Board` = a real Pinterest board name that exists in Buffer
- `Pin Title` ≤100 characters
- `Pin Description` ≤500 characters
- `Destination URL` = `https://kindgridstudio.gumroad.com/l/[slug]` (optionally with UTM params)
- `Pin Image Drive Link` = real Google Drive PNG file URL

---

## Before Creating Any New Product

1. **Read the live Business Dashboard** — check the Gumroad Upload Queue and Publishing Queue for any existing PAIR_READY or READY rows. Never duplicate work already in progress.
2. **Verify the next available KGS ID** — check the dashboard for the highest existing ID. The next is one higher.
3. **Write a demand evidence report** — BUYER PROBLEM, COMPETITOR, DIFFERENTIATION, EVIDENCE, LIMITATION. Save as a Google Doc in Business HQ. Get at minimum 2 real source URLs.
4. **Check for product overlap** — does an existing KindGrid product already solve this problem? If substantially overlapping, stop and document why this new product is differentiated.
5. **Do not announce a product** or mark anything READY until all assets are independently verified.

---

## Before Marking PAIR_READY

All of the following must be independently verified (not assumed):
- [ ] XLSX: opens in Excel, ≥2 sheets, ≥10 formulas, embedded instructional image, no macros
- [ ] XLSX: 12 edge cases tested (zero sold, all sold, zero card, all card, unsold stock, 1 SKU, 20 SKUs, empty rows, negative margin, invalid input flag)
- [ ] PDF (PAID): 3–15 pages, US Letter, no blank pages, real worked examples, checked arithmetic
- [ ] PDF (FREE): 3–7 pages, US Letter, no blank pages, independently useful (not just an ad)
- [ ] Free PDF listing copy contains the exact paid product URL
- [ ] Both covers: PNG, 2:3 ratio (approximately 1000×1500), readable, professional
- [ ] Contact sheet: PNG ≥850×500 px, all pages visible
- [ ] Gallery images: ≥2 for PAID, ≥1 for FREE, 2:3 ratio
- [ ] Listing copy Google Doc: has BEGIN/END markers, no placeholders, no forbidden phrases
- [ ] Demand evidence Doc: ≥750 chars, 5 required headings, ≥2 source URLs
- [ ] QA report Google Doc: KGS-QA-V2, 8 PASS fields, EVIDENCE section, item-specific, ≥350 chars
- [ ] All Google Drive files: service account can read them (viewer permission or link-shared)
- [ ] All slugs: not previously used in Gumroad (check via script or Dashboard)
- [ ] Paid product destination URL is a real live public Gumroad page (HTTP 200)

---

## Error Handling Rules

| Situation | Action |
|-----------|--------|
| Cannot verify a Drive file exists | Stop. Mark HOLD. Report precisely what is missing. |
| Gumroad returned uncertain state | Mark REVIEW. Do not retry. Owner must reconcile in Gumroad dashboard. |
| Buffer returned uncertain state | Mark LINK_REVIEW. All further Pin scheduling halted until resolved. |
| QA report does not meet all 8 criteria | Mark NEEDS_FIX. Do not release. Regenerate and re-audit. |
| Demand evidence is thin or invented | Do not mark PAIR_READY. Gather real evidence first. |
| Paid product not yet live | Pin must stay in PREPARED_PENDING_LIVE_URL, not READY. |
| Any Pin already has a Batch ID | Do not reschedule. It is already in Buffer. |

---

## Do Not Trigger These Workflows

The following workflow files are historical one-time operations already executed. Do not trigger them:
- Any file in `.github/workflows/` except `publisher.yml` (scheduled) and `quality-ci.yml` (on push/PR)
- Any `scripts/one_time_*.py`, `scripts/kgs0*_*.py`, `scripts/oneoff_*.py`, `scripts/bakeslot_*.py`

---

## Emergency Stop

If anything goes wrong with publishing:
1. Set GitHub Actions variable `AUTOPILOT_PAUSED = true` — this stops all live writes immediately
2. Alternatively, disable the `publisher.yml` workflow in GitHub Actions settings
3. Do NOT delete any products, posts, or assets

To resume: set `AUTOPILOT_PAUSED = false` (or delete the variable) and re-enable the workflow.

---

## Metric Honesty Rules

- Do not claim X Pinterest views means the product is suppressed or successful
- Do not claim zero sales means poor conversion without sufficient traffic data
- Pinterest analytics can lag up to 48 hours
- Gumroad Discover requires genuine sales history to surface products — it does not automatically promote new sellers
- Unknown values stay BLANK in the Dashboard — never fill with zero to look complete
- Record: delivered Pin URL, impressions, saves, outbound clicks, Gumroad UTM referrers, free downloads, paid orders, refunds, NET sales — at 48h, 7d, 14d, 30d cohorts

---

## Permanent Autonomous Operations Loop

KindGrid Studio operates under full end-to-end autonomous execution with zero manual owner involvement:

1. **Autonomous Git Operations**: Headless Git operations authenticate silently via the configured credential helper. Never ask the non-coder owner to push via GitHub Desktop or run terminal commands.
2. **Automated Asset Ingestion**: Asset generation deposits files in `assets/kgs-XXX/` with a corresponding `manifest.json`. GitHub Actions (`publisher.yml` and `asset-pipeline.yml`) automatically reconciles the manifest, handles Drive quota with resilient fallbacks, populates `Gumroad Upload Queue` and `Publishing Queue`, and marks stale pins.
3. **Automated Keepalive**: Scheduled workflow `.github/workflows/keepalive.yml` automatically ensures cron triggers in `.github/workflows/publisher.yml` remain active indefinitely beyond GitHub's 60-day inactivity limit.
4. **Daily Autonomous Schedule**: Antigravity runs on a recurring schedule to inspect the live dashboard, maintain queue volume, design next-generation spreadsheet tools and illustrated guides, verify quality gates (KGS-QA-V2), and commit/push updates silently.

---

## Version History of This File

| Date | Change |
|------|--------|
| 2026-10-20 | Initial creation by Antigravity Phase 1 audit |
| 2026-10-29 | Integrated fully autonomous pipeline, headless git credentials, Actions keepalive, and recurring Antigravity operator loop |
