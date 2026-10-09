# KindGrid Autopilot — GitHub publisher + Gemini Spark creator

**Current design (Oct 2026):** Gemini Spark produces ORIGINAL digital products and Pinterest assets, performs item-specific QA V2, and writes complete approved handoffs to Google Sheets. GitHub Actions independently checks queues **every 2 hours** and may automatically publish new approved Gumroad products and schedule approved Pinterest Pins. Routine publishing uses no ChatGPT Work credits.

**This is a live publisher, not a promise of content output.** It does not create products. A scheduled check with no qualified items does nothing. Actual recurring execution, Gumroad auto-publish and full creative quality must be monitored; the first live new-product publication through this *new* workflow has not yet been observed.

## Authoritative documentation

- [Operations, schedules and safety switches](OPERATIONS_STATUS.md)
- [Single Gemini Spark creative + audit master prompt](GEMINI_MASTER_PROMPT_QA_V2.md) (also [Google Doc](https://docs.google.com/document/d/1BZy_Pkc8QUe0PEnpCNr1B1aYuXa7jdTogHfprWf9lSk/edit))
- [Gemini handoff schema](GEMINI_HANDOFF.md)
- [Business Dashboard](https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit) including the **Automation Cadence & QA** tab.
- [Pinterest publishing planning spreadsheet](https://docs.google.com/spreadsheets/d/1Z-1AxByDq1wFTiKZGcSOjxuw208EWG7Mk2uGqW9HQjA/edit) (not directly bulk-upload ready when Media URL points to Google Drive).

## Exact timing

- Publisher cron: `0 */2 * * *` UTC (00,02,...22). In IST: 05:30,07:30,...03:30. GitHub may run late.
- Gemini should maintain a separate four-hourly QA/creative schedule: **00:45,04:45,08:45,12:45,16:45,20:45 IST**. IMPORTANT: This schedule must be created and verified inside Gemini, not by the GitHub code.
- Pinterest: three distinctive Pins per **US calendar day**, at 08:30,14:30,20:30 **America/New_York**. Correctly convert DST (EDT before Nov 1 2026, EST thereafter).
- Exception: Q-02 previously scheduled for Oct 12 2026 14:28 EDT must remain unchanged.

## Automated product publication without manual approvals

GitHub reads `Gumroad Upload Queue`. A new KGS-004+ item is eligible ONLY if:
- Its `Upload Status=READY` and `QA Verified (YES/NO)=YES` and the four **QA V2** fields are complete/current.
- Its separate real PDF, PNG cover, description Google Doc and QA audit Doc can be opened with the Google publisher service account and pass machine validations.
- The price is within safety limits, the unique slug is not present already, the listing has no obvious placeholder or deceptive text, and the QA evidence is item-specific.

When eligible, the publisher downloads the PDF/cover, creates an **unpublished draft first**, rereads it to verify attachments, THEN publishes that *newly created* draft and verifies the public product URL. At most **one new product per 2-hour check**. No approval click is required after legitimate QA V2 PASS, but unverified content does not get published.

Historical KGS-001 / KGS-002 remain protected. KGS-003's pre-existing draft stays `DRAFT_VERIFIED` until Gemini finishes a **retrospective** QA V2 and sets `RELEASE_READY`; only this known original draft can then be updated/published via the separate protected path. The technical upload test must never be published or recreated.

## Pinterest publication

- Source of truth: `Publishing Queue` READY rows with QA=YES, new QA V2 evidence, and real separately linked PNG (not a ZIP).
- Verifies correct real public Gumroad destination, board, original title/description, exact NY time and image format.
- Uploads Pin graphics to Cloudinary and schedules through Buffer; checks Buffer response URL/ID.
- Max **3 per US calendar day**, one per morning/afternoon/evening slot, and max 10 total queued in Buffer Free.
- A Pin marked `SCHEDULED_BUFFER` has not necessarily been published yet. Only record `PUBLISHED` after external delivery verification.

## Activation and emergency stop

The scheduled workflow is LIVE only when repository Actions variable `AUTOPILOT_LIVE_ENABLED=true` and `AUTOPILOT_PAUSED` is not `true`. Manual `workflow_dispatch` remains read-only irrespective of the `dry_run` checkbox.

To pause: GitHub Settings -> Secrets and variables -> Actions -> Variables -> set `AUTOPILOT_PAUSED=true`; or disable the workflow. No GitHub Secret value belongs in any document or chat.

Current protected states: Q-02 scheduled once in Buffer; Q-01 still BLOCKED_TIME until reaudited; Q-03..Q-06 need QA V2; Q-07..Q-42 mostly lack individual ready images. New QA fields intentionally make older YES statuses insufficient. Strict quality and zero duplicates matter more than hitting a publishing quota.

## Tooling

- `src/autopilot.py`: publisher engine, source validators, QA/report gate, Gumroad CLI, Cloudinary, Buffer.
- `scripts/check_gumroad_queue.py`: skip expensive Go/CLI install when there are no qualified product uploads/releases.
- `.github/workflows/publisher.yml`: recurring publisher, manual safe previews and preflight checks.
- `.github/workflows/quality-ci.yml`: syntax and regression tests on code changes.
- `tests/test_autopilot.py`: local regression suite.
- `scripts/gumroad_one_draft_pilot.py`, `scripts/pinterest_one_pin_pilot.py`: historical one-shot tests; do NOT rerun any LIVE pilot after its first successful creation.

## Fundamental limitation

No model can guarantee every creative is error-free. Gemini should render/open actual assets, fact-check and fix until confidence is justified. GitHub's own checks can verify technical properties and recorded audit evidence but cannot perfectly judge usefulness/design/content. Never mark a product published merely because a schedule was created, a link looks plausible, or a model said DONE. GitHub, Gumroad, Pinterest, Google and Buffer all have limits and outages; run failures must be reconciled, not blindly retried.
