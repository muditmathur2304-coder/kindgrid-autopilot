# KindGrid Autopilot — live operations and safety (2026-10-09)

## Activation state

The GitHub Actions workflow `.github/workflows/publisher.yml` is configured to execute at **00:00, 06:00, 12:00, and 18:00 UTC** (05:30, 11:30, 17:30, 23:30 IST), subject to GitHub scheduled-run delays. **Safe holding mode is currently active:** no six-hour run may write to Gumroad or Buffer until a user sets the repository variable `AUTOPILOT_LIVE_ENABLED=true` after a successful read-only regression test. The next *unattended* live run must be checked before considering periodic operation proven.

**Scheduled runs (only after explicitly enabled, and not paused):**
- `LIVE_MODE=true`
- `PIN_AUTOSCHEDULE=true`: schedule only `READY` Pinterest rows with `QA Verified (YES/NO)=YES`, up to 3 Pins per run, future date within 72 hours, within Buffer Free's 10-item queue. Images come from the linked individual Google Drive PNGs; Cloudinary holds only the public Pin creatives.
- `GUMROAD_CREATE_DRAFTS=true`: create **unpublished** Gumroad drafts only for brand-new, valid `READY` product rows, at most one per run. Install Gumroad CLI only if a new eligible draft exists.
- `GUMROAD_AUTOPUBLISH=false`: **hard-locked in workflow**. No scheduled run can publish Gumroad drafts. Publication requires a separate future authorization and tested change.
- Already-uploaded Gumroad products `KGS-001`, `KGS-002`, `KGS-003`, and the technical pilot slug are protected from creation by ID/slug guardrails.
- Existing KGS-003 remains `DRAFT_VERIFIED`. Do not modify it or put it back to `READY`.
- Already scheduled Pinterest Q-02 remains `SCHEDULED_BUFFER` with an existing Buffer ID; cannot be submitted again by the READY-only filter.
- Q-01 is `BLOCKED_TIME`; do not bypass its review status or misreport it as scheduled.
- If any Pin has `LINK_REVIEW`, `REVIEW`, or `SCHEDULING`, new Pinterest submissions pause across subsequent runs until manually reconciled. Existing scheduled Pins can still be checked for sent status.
- No empty-queue Gumroad CLI installation, duplicate retries after uncertain Gumroad or Buffer operations, or browser-based ChatGPT Work publishing.

**Manually triggered runs of this same workflow** always have `LIVE_MODE=false`, regardless of how the `dry_run` checkbox is set. Use them for safe connection checks and queue previews only.

## Pause immediately

**To activate after the manual preview succeeds:** GitHub repository -> Settings -> Secrets and variables -> Actions -> Variables -> New repository variable `AUTOPILOT_LIVE_ENABLED` = `true`. If this variable is missing or has any other value, scheduled runs are read-only.

**Option A — pause without disabling the workflow:** GitHub repository -> Settings -> Secrets and variables -> Actions -> Variables -> New repository variable named `AUTOPILOT_PAUSED` with the value `true`. Future six-hour runs become read-only. Delete the variable or set it to `false` to resume.

**Option B — stop scheduled runs entirely:** GitHub -> Actions -> KindGrid Autopilot (6-hour scheduled publisher) -> three-dot workflow menu -> Disable workflow. This prevents any further scheduled runs until re-enabled.

For a suspected duplicate or incorrect destination, pause the workflow before changing any statuses. Review actual Gumroad or Buffer listing before retrying.

## Queue ownership

**Gemini Spark:** Creates, reviews, and fixes original assets; populates real individual Google Drive links; marks only genuinely completed items READY/QA=YES. It never edits IDs or submitted listings to force retries.

**GitHub controller:** Pulls READY items; validates metadata/assets; submits only allowed platform operations; records status and platform ID in the existing Google Sheet.

**Human exception review:** Security challenges, ambiguous API results, refunds/licensing questions, draft publication approvals, incorrect Pinterest destination, or any status `REVIEW` / `LINK_REVIEW`.

Gemini's own scheduled job must independently inspect Google Sheets errors; GitHub cannot summon a Gemini Spark chat directly. This is an *asynchronous* feedback loop, not an instantly self-correcting autonomous agent.

## Status and verification

- `SCHEDULED_BUFFER` = accepted by Buffer, **not yet live on Pinterest**.
- `PUBLISHED` (Pinterest) = Buffer reported sent and provided a Pinterest URL.
- `DRAFT_VERIFIED` (Gumroad) = draft with verified PDF + cover, **not publicly for sale**.
- `NEEDS_FIX` = creative/file issue Gemini should fix before re-approval.
- `REVIEW` / `LINK_REVIEW` = uncertain platform state, manual reconciliation required.
- Never use an empty `Batch ID` or API timeout as authorization for another posting attempt.

Check the *first scheduled GitHub run* and ensure it reports `live=True`. Verify that any queued Pin preserves its exact Gumroad destination link before treating the pipeline as reliable.

## Recurring publication limits

Github Actions scheduled runs may be delayed; the configured cron is not a guaranteed exact-time SLA. Buffer Free queue has up to 10 scheduled posts at once; 3/day is a **target**, dependent on enough verified Gemini assets being ready on time. Usage and API limits may change. No guarantee of sales or uninterrupted account access.

## Relevant links

- GitHub Actions: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions/workflows/publisher.yml
- Business Dashboard: https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit
- Buffer: https://publish.buffer.com/
- Gumroad: https://gumroad.com/products

## Evidence from prior pilot tests

- Pinterest Q-02: created through Github/Buffer and verified by the owner, retained the correct paid-product destination URL.
- Gumroad technical draft: created through GitHub CLI and verified by owner as unpublished with cover and 8-page PDF.
- Both tests were one-time/manual triggers, NOT evidence that the six-hour scheduled job has completed successfully yet.
