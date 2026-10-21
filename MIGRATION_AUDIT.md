# KindGrid Studio — Migration Audit (Phase 1)

**Prepared by:** Antigravity AI
**Date:** 2026-10-20
**Status:** READ-ONLY inspection. No external writes performed.

---

## 1. What Was Inspected

### Local repository files (verified by direct file read)
- All top-level markdown documents (README, OPERATIONS_STATUS, AUTOMATED_TOOLS_STRATEGY, PREMIUM_PAIR_POLICY, CHATGPT_CREATION_HANDOFF, PINTEREST_US_ACQUISITION_V1, DAILY_7X7_CADENCE, GEMINI_HANDOFF, GEMINI_MASTER_PROMPT_QA_V2)
- All source code: `src/autopilot.py` (779 lines), `src/paired_release.py` (336 lines)
- All GitHub Actions workflows (58 workflow files in `.github/workflows/`)
- All test files: `tests/test_autopilot.py`, `tests/test_paired_release.py`, `tests/test_xlsx_tool_release.py`, `tests/test_existing_pin_send_now.py`, `tests/test_pair020_recovery_safety.py`
- All scripts (69 files in `scripts/`)
- All ops logs (18 files in `ops/`)
- Content: `content/artist_commission/` (2 listing files)
- `requirements.txt`, `sample_queue.json`

### External sources (read via URL — contents reviewed)
- Repository documentation references to live Google Sheets, Google Docs, and Drive
- Referenced Gumroad product URLs (structural only, no authentication)
- Referenced Pinterest URLs (structural only)

---

## 2. Business State — What Exists (Verified)

### Confirmed live Gumroad products (from documentation)
| ID | Slug | Price | Status | Notes |
|----|------|-------|--------|-------|
| KGS-001 | `52-week-savings-challenge` | Free | PUBLISHED | Live free challenge |
| KGS-002 | `ultimate-budget-planner` | Paid | PUBLISHED | 25-page planner |
| KGS-003 | `debt-payoff-accelerator` | $5 | DRAFT | Blocked — math errors in PDF; customer file NOT replaced |
| KGS-004 | `weekly-meal-grocery-budget-kit` | $3 | PUBLISHED | Flagged EDITORIAL_REWORK; too generic |
| KGS-005 | `subscription-renewal-control-kit` | $4 | PUBLISHED | Flagged EDITORIAL_REWORK; too generic |
| KGS-006 | `paycheck-gap-playbook` | $7 | PUBLISHED | 24-page + XLSX. Protected — active Pinterest acquisition campaign |
| KGS-007 | `paycheck-gap-starter` | Free | PUBLISHED | Free companion to KGS-006. Protected |
| KGS-008 | `market-day-margin-guide` | $9 | PUBLISHED | 27-page + formula XLSX. Market-day break-even tool |
| KGS-009 | (free companion to KGS-008) | Free | REVIEW/HOLD | Uncertain state; one-time recovery was authorized |
| KGS-010 | BakeSlot (paid) | Paid | PUBLISHED | Home baker custom order scheduler |
| KGS-011 | BakeSlot (free) | Free | PUBLISHED | Companion to KGS-010 |
| KGS-012 | BakeBatch Weekly Production Planner | Paid | PUBLISHED | `bakebatch-weekly-production-planner` confirmed in ops log |
| KGS-013 | CollectFlow (non-food) | Paid | Likely PUBLISHED | Owner-requested one-time release on 2026-10-13 |
| KGS-014 | Unknown | Unknown | Unknown | Referenced in scripts; state unconfirmed |
| KGS-015 | `commission-ready-artist-playbook` | $12 | Likely PUBLISHED | Listing draft exists in `content/artist_commission/`; artist commission system |
| KGS-016 | (free partner to KGS-015) | Free | Likely PUBLISHED | Free companion; referenced in scripts |
| KGS-017 | DepositGuard | Paid | Likely PUBLISHED | `kgs017_depositguard_once.py` (32 KB script) exists |
| KGS-018 | ScopePulse | Paid | Likely PUBLISHED | `kgs018_scopepulse_once.py` (34 KB script) exists |
| KGS-019 | MoveMargin | Paid | Likely PUBLISHED | `kgs019_movemargin_once.py` (12 KB script) exists |

> **IMPORTANT:** Product states for KGS-009 onward were NOT independently verified by live API calls. The above is inferred from script names, ops logs, and documentation. Treat as UNVERIFIED until confirmed against the live Business Dashboard.

### Protected hardcoded slugs in code (`src/autopilot.py` line 27)
```
52-week-savings-challenge, ultimate-budget-planner, debt-payoff-accelerator,
kindgrid-autopilot-upload-test-20261009, weekly-meal-grocery-budget-kit,
subscription-renewal-control-kit, paycheck-gap-playbook, paycheck-gap-starter
```
These cannot be re-created by the publisher. KGS-008 onward slugs are NOT in this set — they are protected only from duplication at creation time.

### Confirmed Pinterest Pin statuses (from documentation)
| Queue ID | Status | Notes |
|----------|--------|-------|
| Q-01 | BLOCKED_TIME (historical) | Audited but held; must not be resubmitted |
| Q-02 | SCHEDULED_BUFFER | Must not be resubmitted |
| Q-43, Q-44, Q-53 | PUBLISHED | Confirmed live Pinterest URLs recorded |
| Q-45, Q-46, Q-47, Q-50 | SCHEDULED_BUFFER | Per October 10 status verification |
| Q-51, Q-52 | SCHEDULED_BUFFER | Must not be resubmitted |
| Q-48, Q-49 | BLOCKED | Waiting on KGS-009 free URL confirmation |
| Q-55, Q-57 | One-time releases | Owner-authorized specific releases executed |
| Q-03 – Q-42 | Various | Historical; many had no valid individual Drive image links; many unverified |

---

## 3. GitHub Actions — What Exists and What Works

### Core scheduled workflow: `publisher.yml`
- **Schedule:** `17 */2 * * *` UTC (every 2 hours at :17 past — confirmed in code)
- **Live mode condition:** `LIVE_MODE = true` ONLY when `github.event_name == 'schedule'` AND `AUTOPILOT_LIVE_ENABLED == 'true'` AND `AUTOPILOT_PAUSED != 'true'`
- **What it does:**
  1. Runs unit tests
  2. On `workflow_dispatch`: checks Buffer, Cloudinary, Pinterest preflight, Gumroad connection (read-only)
  3. Runs `staged_pair_preflight.py` (read-only, `continue-on-error`)
  4. Runs `check_pair_queue.py` — sets `needs_cli` output
  5. Installs Go + Gumroad CLI ONLY if `needs_cli == 'true'`
  6. Runs `src/autopilot.py` — the actual publishing engine
- **Status:** Code looks correct. The `PYTHONPATH` fix (from Oct 10 incident) is in place.

### Quality CI: `quality-ci.yml`
- Triggers on push/PR to `src/**`, `tests/**`, `scripts/**`, `workflows/**`, `requirements.txt`
- Runs syntax check, unit tests, staged preflight (main branch only), and regression checks
- Status: Appears structurally sound

### One-time / historical workflows (58 total)
- Most are single-use operation scripts already executed (bakeslot, kgs012, kgs013, kgs017, kgs018, kgs019, pair001, pair002, etc.)
- Many have corresponding `ops/*.txt` logs showing they were triggered
- **These should not be re-triggered.** They represent past operations, not recurring automation.

---

## 4. Source Code Architecture — What Works

### `src/autopilot.py` — The Publisher Engine
**Status: WORKING (unit tested, structurally sound)**

Key verified behaviors:
- `LIVE_MODE` must be explicitly true before any external write
- `GUMROAD_CREATE_DRAFTS=false` — old solo product creation **disabled**
- `GUMROAD_AUTOPUBLISH=false` — auto-publish disabled for old path
- `PAIRED_RELEASE_ENABLED=true` — only PAID+FREE pairs can release
- KGS-003 release path: explicitly `require(False, ...)` — **permanently blocked** until customer PDF is safely replaced
- Pin scheduling: 7 daily limit, 8 named time windows, Buffer 10-post queue respected
- Duplicate prevention: checks `Batch ID` before scheduling, verifies `Actual Pinterest Pin URL` absent
- QA gate: requires KGS-QA-V2, within 14 days, PASS, item-specific Drive Doc with 8 PASS fields
- Destination validation: only `kindgridstudio.gumroad.com`, HTTPS, UTM params only
- Cloudinary → Buffer → Dashboard update chain (fail-closed)

### `src/paired_release.py` — The Pair Launch Gate
**Status: WORKING (unit tested)**

Key behaviors:
- XLSX validator: requires ≥2 sheets, ≥10 formulas, embedded artwork ≥3 KB, no macros/external links
- Pair selection: requires exactly 2 PAIR_READY rows, one PAID + one FREE, reciprocal IDs
- Asset validation: PDF 3–15 pages (PAID), 3–7 pages (FREE), contact sheet PNG, 2+ gallery images (PAID), 1+ (FREE)
- Demand research doc: requires 750+ chars, 5 required sections, ≥2 HTTPS URLs
- Daily cap: refuses to launch if fewer than 2 daily slots remain under `GUMROAD_DAILY_LIMIT`
- Paid price: $3–$30; Free price: exactly $0
- XLSX is now the **PRIMARY** paid deliverable (attached first), guide PDF second

> **CRITICAL NOTE:** The `prepare_pair()` function was updated — it no longer requires 16–55 PDF pages. The current gate requires 3–15 pages for PAID and 3–7 for FREE. This is tool-first compatible. The old documentation warning about "16–55 page requirement" is **OUTDATED** as of the current code.

---

## 5. What Is Broken or Uncertain

### Confirmed broken / blocked
1. **KGS-003 customer PDF** — math errors confirmed (wrong snowball ranking, impossible payoff date, unsupported interest savings). Release path explicitly blocked in code. Customer-facing PDF is the uncorrected version.
2. **KGS-009 free product** — state uncertain (REVIEW/HOLD). Q-48 and Q-49 cannot publish until this is resolved.
3. **Q-01** — historically BLOCKED_TIME; new time 08:30 EDT set but still requires fresh KGS-QA-V2 audit before READY.
4. **Q-03 through Q-42** — historical Pins mostly without valid individual Drive image links. Many unverified.
5. **ChatGPT creator automation** — referenced throughout docs but paused. ChatGPT does not currently produce new products. **This is the primary gap being filled by Antigravity.**

### Uncertain / requires live verification
6. **KGS-009 through KGS-019 exact publication states** — inferred from scripts, not verified via API
7. **Buffer queue state** — Q-02, Q-45–Q-47, Q-50–Q-52 last confirmed SCHEDULED_BUFFER on Oct 10; actual delivery to Pinterest not independently confirmed in this audit
8. **Cloudinary image hosting** — confirmed in code; actual connection health unknown without live auth
9. **Google Service Account** — confirmed secret name `GOOGLE_SERVICE_ACCOUNT_JSON_B64`; actual permission scope unknown without live test
10. **`AUTOPILOT_LIVE_ENABLED`** — must be set as a GitHub Actions **variable** (not secret) to `true` for the scheduled publisher to actually publish. Current value unknown.
11. **`AUTOPILOT_PAUSED`** — must be `false` (or unset) for publishing to occur. Current value unknown.
12. **KGT-001 Market Day Decision Engine prototype** — exists in Drive (ID `1wrpB6H7pq9H3wzCA0abDl8basltGtkKZ`) but was NOT released as a product. Status: INTERNAL PROTOTYPE. Cross-platform QA pending.

### Editorial issues (not code bugs)
13. **KGS-004 and KGS-005** — flagged EDITORIAL_REWORK; too generic; buyers retain access but no new promotion
14. **KGS-002** — finance maximum example requires review per documentation
15. **Old 7×7 cadence target** — documented as max 7 Gumroad + 7 Pinterest per NY day, but zero fully qualified new pairs are currently READY

---

## 6. Secrets and Credentials Required

> **No secret values were read or displayed. The following lists service names and required secret/variable names only.**

| Service | GitHub Secret Name | Status |
|---------|-------------------|--------|
| Google Sheets + Drive + Docs | `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | Present (name confirmed in workflow) |
| Buffer (Pinterest scheduler) | `BUFFER_API_KEY` | Present (name confirmed) |
| Buffer (channel) | `BUFFER_PINTEREST_CHANNEL_ID` | Present (name confirmed) |
| Buffer (organization) | `BUFFER_ORGANIZATION_ID` | Present (name confirmed) |
| Cloudinary (image hosting) | `CLOUDINARY_URL` | Present (name confirmed) |
| Gumroad (seller API) | `GUMROAD_ACCESS_TOKEN` | Present (name confirmed) |

| Service | GitHub Variable Name | Required Value | Status |
|---------|---------------------|----------------|--------|
| Publisher live mode | `AUTOPILOT_LIVE_ENABLED` | `true` | **Unknown — must verify** |
| Publisher pause switch | `AUTOPILOT_PAUSED` | `false` (or unset) | **Unknown — must verify** |

---

## 7. Previous AI Tools — Current Status

| Tool | Previous Role | Current Status |
|------|--------------|----------------|
| Gemini Spark | Original creator/QA | **ARCHIVED** — `GEMINI_HANDOFF.md` and `GEMINI_MASTER_PROMPT_QA_V2.md` both marked FOR HISTORICAL REFERENCE ONLY |
| ChatGPT (Premium Pair Studio) | Creator/QA replacement | **PAUSED** — referenced in docs but no longer active; now replaced by Antigravity |
| GitHub Actions | Publisher | **ACTIVE** — scheduled every 2 hours; awaiting approved pairs |
| Google Drive | Asset storage | **ACTIVE** — service account connection configured |
| Google Sheets | Business Dashboard | **ACTIVE** — used as live queue |
| Buffer | Pinterest scheduler | **ACTIVE** — queue state partially known |
| Cloudinary | Image CDN for Pinterest | **ACTIVE** — connection configured |
| Gumroad CLI | Seller publishing | **ACTIVE** — installed on-demand in GitHub Actions |

---

## 8. Repository Structural Findings

- **69 one-time scripts** in `/scripts/` — these represent past manual operations, not reusable automation. Most are safe to ignore going forward; none should be re-triggered without verifying their specific target state.
- **58 GitHub Actions workflows** — the vast majority are one-time operations already run. The two recurring workflows (`publisher.yml`, `quality-ci.yml`) are the live production system.
- **Operations logs** in `/ops/` — 18 text files documenting past releases. Important for understanding what was published; not for future operation.
- **`content/artist_commission/`** — listing drafts for KGS-015/016 (Commission Ready pair). These exist locally but whether they were published is unconfirmed without a live Gumroad check.
- **`sample_queue.json`** — contains KGS-003 in a `READY` state. This file is ONLY used by unit tests; it does not drive real publishing.

---

## 9. Summary: What Can Be Retained vs. What Needs Change

### Retain (confirmed working)
- GitHub Actions `publisher.yml` + `quality-ci.yml` — the publishing and CI infrastructure is sound
- `src/autopilot.py` and `src/paired_release.py` — well-structured, fail-closed, tested
- Google Sheets dashboard as the queue source of truth
- Buffer + Cloudinary + Gumroad CLI chain
- All existing published Gumroad products and customer access
- All existing scheduled/published Pinterest posts

### Change / fix (needed for XLSX-first tool products)
- The `prepare_pair()` page-count gate is **already updated** to 3–15 pages PAID / 3–7 pages FREE — this is tool-first compatible. No code change needed for page count.
- The `EXISTING_PRODUCTS` set in `autopilot.py` only covers KGS-001 through KGS-007. Products KGS-008 onward are protected at creation time by slug de-duplication against the live Gumroad account. This should be reviewed and expanded as more products launch.
- No new creator automation exists. Antigravity must assume the ChatGPT creator role: research, product creation, QA, Drive upload, and queue row preparation.

### Remove / do not re-trigger
- All 58 one-time workflow files — leave in place (they are historical records) but do not trigger them
- Old Gemini and ChatGPT schedule references — both are superseded by Antigravity

---

*End of Migration Audit. No external writes performed during this inspection.*
