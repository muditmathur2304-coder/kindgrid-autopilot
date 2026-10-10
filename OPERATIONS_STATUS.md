# KindGrid Studio — Automation Operations Status (QA V2)
Last policy update: October 9, 2026. Source of truth: Google Sheets Business Dashboard and the live platform APIs.

## Live workflow

- GitHub Actions workflow: `.github/workflows/publisher.yml`
- Frequency: **every 2 hours** at even UTC hours 00:17,02:17,...22:17 (India: 05:47,07:47,...03:47, 12 checks per day). Offset by 17 minutes to reduce top-of-hour GitHub delays. GitHub cron remains best-effort; runs can still be delayed or skipped.
- Owner enable gate: `AUTOPILOT_LIVE_ENABLED=true` repository variable; pause gate `AUTOPILOT_PAUSED=true`. Without an enabled gate or while paused, scheduled runs are dry read-only checks.
- Manual workflow dispatch ALWAYS remains read-only, even if its dry_run checkbox is false. Never use an old one-off live pilot again.
- Each 2-hour run MAY publish **one genuinely new, quality-approved Gumroad product** and MAY schedule up to 3 Pins if eligible, while respecting one Pin per US morning/afternoon/evening window and Buffer Free 10-queued-item limit.
- Publishing is conditional, not an obligation. Zero audited READY products -> zero Gumroad uploads. No manufactured or repetitive products to meet the cadence.
- `GUMROAD_AUTOPUBLISH` runs only when enabled and not paused; **no per-product human approval required** after the automated QA V2 gate. Draft creation with explicit `--draft`, verify PDF and cover, publish that newly created draft, read back published status, and independently check its public product URL.
- Historical `KGS-003`: remains protected at `DRAFT_VERIFIED`; never recreate it. Current QA override: the actual original PDF has wrong snowball ranking, an impossible two-month payoff example, unsupported interest-savings claims and misleading debt-free milestones. KGS-003 is therefore DRAFT_VERIFIED / QA FAIL / RECHECK_REQUIRED. The existing uploader only updates listing copy; CLI --file APPENDS a file without replacing the old downloadable PDF. Its historical auto-release path is DISABLED pending a fully tested customer-content replacement workflow. Gemini must repair/audit the original PDF and verify the actual Gumroad deliverable; it must NOT mark RELEASE_READY merely because a corrected Drive PDF exists.
- Existing KGS-001/KGS-002 and technical one-off upload test are never recreated, altered, or automatically republished. Q-02 already scheduled in Buffer and must never be submitted again.

## October 10 content starvation diagnosis

At the first verified overnight unattended run (2026-10-09 20:34 UTC / 2026-10-10 02:04 IST), LIVE_MODE was true and GitHub printed `Queue: 0 new products, 0 Pins`; Q-43 was confirmed published by Buffer. There was no new approved KGS-005+ product in the Google Sheet. Therefore, **Gumroad published nothing because Gemini had not provided another fully QA-approved package**. Do not claim that cron creates PDFs or that green runs always publish. The old Gemini instruction to finish ALL retrospective work before producing anything caused queue starvation. Its master prompt and Google Doc now require a parallel production lane, starting with distinct KGS-005+, and a reserve of 2–3 truthful QA-PASS new products when feasible. Actual Gemini Scheduled Action description must reflect the revised master; GitHub cannot edit Gemini task schedules directly.

## Gemini Spark orchestration — must be configured in Gemini

- Creative + retrospective QA cadence: **every 4 hours**, IST 00:45,04:45,08:45,12:45,16:45,20:45, approximately 45 minutes before alternating GitHub checks.
- One separate Sunday 10:00 IST deep content-audit/strategy pass (only if existing Sunday schedule supports it).
- IMPORTANT: Changing this GitHub repository **does not change Gemini Spark's own schedules**. Owner must paste/execute `GEMINI_MASTER_PROMPT_QA_V2.md` in Gemini, verify Gemini actually registered the requested schedule, and accept any honest scheduling limitations.
- Comprehensive master prompt stored in GitHub and Google Doc: https://docs.google.com/document/d/1BZy_Pkc8QUe0PEnpCNr1B1aYuXa7jdTogHfprWf9lSk/edit
- Target ~1 polished original product/day to start; higher volume only if QA survives. Gemini should instead prioritize prior failures, link/asset repairs and 7-day Pinterest backlog.

## Pinterest times (America/New_York authoritative)

- Morning 08:30 NY: 18:00 IST during EDT, 19:00 IST during EST.
- Afternoon 14:30 NY: 00:00 IST next day EDT, 01:00 IST next day EST.
- Evening 20:30 NY: 06:00 IST next day EDT, 07:00 IST next day EST.
- Convert using actual DST for the date (US DST ends Nov 1 2026).
- Primary Publishing Queue and secondary Pinterest planning sheet already updated for Q-01 and unscheduled Q-03 through Q-42; Q-02's existing accepted 14:28 EDT time was preserved. Do not alter any scheduled Buffer post to match a spreadsheet retroactively.
- Q-01 still BLOCKED_TIME until audited and consciously changed to READY. Q-03..Q-06 have source images but need NEW QA-V2 evidence. Q-07..Q-42 need actual separate loose Drive images and audits; a ZIP is not publishable input.

## Hard QA release gate (both Sheets queues)

Exactly FOUR new columns are enforced by GitHub:
1. `QA Version`: must equal `KGS-QA-V2`.
2. `QA Report Drive Link`: actual Google Doc URL owned/shared with KindGrid publisher service account.
3. `QA Audited UTC`: real ISO-8601 UTC timestamp, no more than 14 days old.
4. `QA Outcome`: must equal `PASS`.

In addition, original `QA Verified (YES/NO)=YES` and correct `READY` status are required for new items, together with valid Google Drive PDF/cover or loose image, appropriate listing copy, acceptable price/slug, accurate Pinterest board/three daily slots, and a destination page independently reachable from GitHub. The QA report must specifically identify the current item, contain substantive EVIDENCE, and certify all eight mandatory checks: ASSET_OPEN, VISUAL, CONTENT, COPY, LINKS, LICENSE, FACTS, PRODUCT_MATCH. The controller verifies structural presence, while Gemini must actually inspect evidence; an AI self-report alone cannot guarantee flawless content.

Important restrictions:
- Gemini may set `READY` ONLY after creating and checking the actual linked QA record and source media.
- Historical items that lack these extra fields are intentionally blocked until retrospectively reaudited. Do not backfill PASS from old 'YES' flags.
- Broken public destination URL, wrong/missing image, outdated report, wrong listing, incomplete PDFs, suspect page formats, overly strong refund/performance claims or possible duplicate -> no publication.
- A failed / uncertain Gumroad attempt goes to REVIEW or NEEDS_FIX; never blindly retry or reset to READY.
- An uncertain Pinterest state LINK_REVIEW/REVIEW/SCHEDULING halts future scheduled Pin batches until reconciled.

## Independent outcome verification

- Gumroad `PUBLISHED`: API reported published AND public verified Gumroad URL recorded. `DRAFT_VERIFIED` is NOT for sale.
- Pinterest `SCHEDULED_BUFFER`: accepted by Buffer, NOT yet published on Pinterest. `PUBLISHED`: Buffer reports sent with Pinterest external URL.
- The first scheduled 2-hour run of the NEW workflow is not yet independently confirmed here. Check actual GitHub Actions logs for `live=True` and all unit tests passed.
- Automatic new-product public publishing path remains unproven in a live release: the Gumroad pilot previously verified draft upload only. QA V2 and auto-publish release code must pass new regression tests before relying on unattended distribution.

## Owner controls / pause

- Stop writes: GitHub Settings -> Secrets and variables -> Actions -> Variables -> `AUTOPILOT_PAUSED` = `true`, or disable the workflow in GitHub Actions.
- Resume: `AUTOPILOT_PAUSED=false` and `AUTOPILOT_LIVE_ENABLED=true` (after checking quality failures).
- All secrets remain in GitHub Actions Secrets; NEVER put Gumroad/Buffer/Cloudinary/Google credentials in source code, creative assets, Gemini prompts or ChatGPT chat.
- The autonomous feedback loop is ASYNCHRONOUS. GitHub writes issue statuses to Sheets; Spark must independently reread and fix them on its genuine schedule. No browser bridge or direct Gemini-chat trigger is implied.

## Actual evidence and relevant links

- First Pinterest Q-02 submission and destination were confirmed by owner, with Buffer post ID recorded in the Google Sheet.
- First technical Gumroad upload created an unpublished 8-page PDF + cover draft and was independently verified by owner; this proves draft upload, not live new-product auto-publication.
- GitHub publisher: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions/workflows/publisher.yml
- Google Dashboard: https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit
- Buffer: https://publish.buffer.com/
- Gumroad: https://gumroad.com/products
- Gemini master QA prompt: https://github.com/muditmathur2304-coder/kindgrid-autopilot/blob/main/GEMINI_MASTER_PROMPT_QA_V2.md
