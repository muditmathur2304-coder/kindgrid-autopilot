# KindGrid Studio — Migration Checklist

**Created:** 2026-10-20 by Antigravity Phase 1 audit
**Purpose:** Exact migration tasks in dependency order. Each task must be completed before the next begins.

> [!IMPORTANT]
> Do not skip steps or reorder them. Each step protects against breaking a live system.

---

## PHASE 1 — COMPLETED ✅ Read-only audit and documentation

- [x] Read and understand all repository files
- [x] Map all existing products (KGS-001 through KGS-019)
- [x] Map all GitHub Actions workflows (58 total)
- [x] Understand publisher code architecture
- [x] Identify broken/uncertain states
- [x] Create MIGRATION_AUDIT.md
- [x] Create ANTIGRAVITY_MASTER_BRIEF.md
- [x] Create AGENTS.md
- [x] Create MIGRATION_CHECKLIST.md (this file)
- [x] Create OPERATIONS_RUNBOOK.md
- [x] Create CREDENTIALS_CHECKLIST.md

---

## PHASE 2 — Live System Verification (NEXT — owner participation required)

These steps require the owner to open the Business Dashboard and confirm live states.

### 2A. Verify publisher is enabled and not paused
- [ ] Open GitHub repository → Settings → Variables
- [ ] Confirm `AUTOPILOT_LIVE_ENABLED` is set to `true`
- [ ] Confirm `AUTOPILOT_PAUSED` is NOT set to `true` (or does not exist)
- [ ] If wrong, set correctly (see OPERATIONS_RUNBOOK.md for how)

### 2B. Confirm all 6 secrets are present in GitHub
- [ ] Open GitHub repository → Settings → Secrets and Variables → Actions → Secrets
- [ ] Confirm all 6 secrets exist: `GOOGLE_SERVICE_ACCOUNT_JSON_B64`, `BUFFER_API_KEY`, `BUFFER_PINTEREST_CHANNEL_ID`, `BUFFER_ORGANIZATION_ID`, `CLOUDINARY_URL`, `GUMROAD_ACCESS_TOKEN`
- [ ] Do NOT reveal values — just confirm presence with a green checkmark

### 2C. Run a dry-run workflow dispatch
- [ ] Open GitHub repository → Actions → "KindGrid Autopilot (2-hour quality-gated publisher)"
- [ ] Click "Run workflow" → set `dry_run = true` → click "Run workflow"
- [ ] Wait for run to complete (typically 2–3 minutes)
- [ ] Check the logs: confirm all connection checks pass (Buffer, Cloudinary, Pinterest, Gumroad)
- [ ] Note any errors and record them

### 2D. Verify Business Dashboard structure
- [ ] Open the Business Dashboard
- [ ] Confirm "Gumroad Upload Queue" tab exists with correct column headers
- [ ] Confirm "Publishing Queue" tab exists with correct column headers
- [ ] Check for any rows in PAIR_READY state — if found, review carefully before Phase 3

### 2E. Verify existing live products
- [ ] Open https://kindgridstudio.gumroad.com and confirm the storefront loads
- [ ] Verify KGS-006 (paycheck-gap-playbook) is publicly accessible
- [ ] Verify KGS-007 (paycheck-gap-starter) is publicly accessible
- [ ] Verify KGS-008 (market-day-margin-guide) is publicly accessible
- [ ] Check KGS-009 — open Gumroad seller dashboard and confirm its actual state (PUBLISHED or still draft)
- [ ] Record actual states in the Business Dashboard

---

## PHASE 3 — Queue and Pinterest Reconciliation

**Dependency:** Phase 2 must be complete first.

### 3A. Reconcile Buffer Pin queue
- [ ] Log into Buffer
- [ ] Check how many posts are currently in the Pinterest queue (should be ≤10)
- [ ] Identify which Q-IDs are actually in Buffer (compare to Dashboard "SCHEDULED_BUFFER" rows)
- [ ] Check if any SCHEDULED_BUFFER rows have now been delivered to Pinterest (their status in Buffer will be "sent")
- [ ] For any "sent" posts: record the actual Pinterest Pin URL in the Dashboard and update status to PUBLISHED
- [ ] For any posts in Buffer with no matching Dashboard row: identify the Q-ID and reconcile

### 3B. Resolve KGS-009 free product state
- [ ] Check the Gumroad seller dashboard for KGS-009
- [ ] If PUBLISHED: record the public URL, update Dashboard row to PUBLISHED, enable Q-48 and Q-49 for future scheduling
- [ ] If still draft or deleted: mark clearly in Dashboard; do not create a duplicate

### 3C. Audit Q-01 for re-enabling
- [ ] Open the Q-01 Pin image from its Drive link
- [ ] Confirm it is 1000×1500 px, readable, original, and accurate
- [ ] If passes KGS-QA-V2 inspection: write a QA report and mark READY (the scheduler will pick it up)
- [ ] If fails: update Status to NEEDS_FIX and document the issue

### 3D. Verify KGS-015 through KGS-019 states
- [ ] For each: open Gumroad seller dashboard and check if published
- [ ] Record actual states in the Business Dashboard
- [ ] If any are in REVIEW or uncertain: note in the Dashboard; do not retry without investigating

---

## PHASE 4 — XLSX Publisher Validation

**Dependency:** Phase 3 must be complete. At least one pair of products must be confirmed working through the full pipeline.

### 4A. Verify KGT-001 prototype status
- [ ] Open the Drive file at ID `1wrpB6H7pq9H3wzCA0abDl8basltGtkKZ`
- [ ] Open in Google Sheets and test: zero units, all sold, 20 SKUs, card rate change
- [ ] Check cross-platform: download and open in Excel (or test on a Windows machine)
- [ ] Record which edge cases pass and which fail
- [ ] Note: this is NOT the same as KGS-008 (Market Day Margin Guide); document differentiation clearly

### 4B. Expand the EXISTING_PRODUCTS set in code
- [ ] Open `src/autopilot.py` line 23
- [ ] Current: `{"KGS-001", "KGS-002", "KGS-003", "KGS-004", "KGS-005", "KGS-006", "KGS-007"}`
- [ ] Update to include all confirmed-published product IDs from Phase 2 and 3 verification
- [ ] Also update `EXISTING_GUMROAD_SLUGS` on line 27 to include all confirmed live slugs
- [ ] Create a branch, make the change, run `quality-ci.yml`, verify tests pass
- [ ] Submit a pull request; do NOT push directly to main

### 4C. Validate the XLSX publishing path end-to-end
- [ ] When a genuinely new, differentiated product is ready for launch:
  - Build and validate the XLSX locally using `src/paired_release.py:validate_tool_xlsx`
  - Run all 12 edge case tests
  - Upload to Drive; verify service account can read
  - Prepare both queue rows as PAIR_READY
  - Let the scheduled publisher pick it up on the next 2-hour run
  - Do NOT trigger a one-time release script

---

## PHASE 5 — First New Antigravity-Created Campaign

**Dependency:** Phases 2–4 complete. Must include full research, creation, QA, and a verified pair.

### 5A. Market research
- [ ] Choose a specific underserved US microbusiness problem
- [ ] Find Pinterest Trends evidence (log it with a date; mark UNVERIFIED if Trends is inaccessible)
- [ ] Find ≥2 real competing products with actual prices and features noted
- [ ] Identify clear differentiation (not just "it's better")
- [ ] Write demand evidence Google Doc with 5 required headings and ≥2 source URLs
- [ ] Save to Business HQ and share with Google service account

### 5B. Product creation
- [ ] Build the XLSX tool
- [ ] Test 12 edge cases; document results
- [ ] Write the guide PDF (3–15 pages for paid)
- [ ] Create the free companion (3–7 pages; independently useful)
- [ ] Write listing copy Google Docs (both paid and free)
- [ ] Create 1000×1500 covers (paid and free)
- [ ] Capture gallery preview images (≥2 paid, ≥1 free)
- [ ] Produce page-by-page contact sheet PNGs for both

### 5C. Upload and verify assets
- [ ] Upload all files to Business HQ product subfolder
- [ ] Verify each Drive file ID is readable by the service account
- [ ] Confirm MIME types are correct (PDF = application/pdf, cover = image/png, XLSX = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

### 5D. QA
- [ ] Write a separate KGS-QA-V2 Google Doc for the PAID product
- [ ] Write a separate KGS-QA-V2 Google Doc for the FREE product
- [ ] Both must have all 8 PASS fields with substantive evidence

### 5E. Queue preparation
- [ ] Assign next available KGS IDs (verify in Dashboard first)
- [ ] Assign a unique Pair ID
- [ ] Add both rows to Gumroad Upload Queue with PAIR_READY status
- [ ] Design 2–3 Pinterest Pins; add to Publishing Queue as READY with QA-V2 reports

### 5F. Wait for publisher
- [ ] Do NOT trigger a manual release
- [ ] Check GitHub Actions at the next scheduled run (at :17 past an even UTC hour)
- [ ] Verify PUBLISHED status and actual public URLs in the Dashboard
- [ ] Record campaign launch metrics

---

## PHASE 6 — Analytics and Iteration (ongoing)

- [ ] At 48 hours: record Pinterest impressions, outbound clicks, Gumroad visits, free downloads, paid orders
- [ ] At 7 days: record same metrics
- [ ] At 14 days: decide whether to create complementary Pins or adjust strategy
- [ ] At 30 days: full campaign review; document what worked and what did not
- [ ] Use findings to inform the next product campaign

---

## Blocking Issues (must resolve before Phase 3)

| Issue | Severity | Blocker For |
|-------|----------|-------------|
| KGS-003 customer PDF has math errors | HIGH | Cannot release KGS-003 until safely replaced |
| KGS-009 state unknown | MEDIUM | Q-48, Q-49 cannot publish |
| `AUTOPILOT_LIVE_ENABLED` value unknown | HIGH | Publisher may not be live |
| Many historical Q-01 to Q-42 Pins unverified | LOW | Only affects those specific Pins |
| ChatGPT creator no longer active | HIGH | No new products will be created without Antigravity taking over |
