# ARCHIVED — FOR HISTORICAL REFERENCE ONLY

This was the old Gemini Spark creative workflow. KindGrid Studio has now appointed **ChatGPT** as content creator / quality reviewer. **Do not execute the old Gemini schedules or use this document as current publishing instructions.** See [CHATGPT_CREATION_HANDOFF.md](CHATGPT_CREATION_HANDOFF.md) and [OPERATIONS_STATUS.md](OPERATIONS_STATUS.md). The GitHub publisher and existing historical product records remain intact.

---

# Gemini Spark — KindGrid Studio handoff (current QA-V2 policy)

The owner should paste/execute this **single comprehensive master prompt** in Gemini Spark:
- GitHub: https://github.com/muditmathur2304-coder/kindgrid-autopilot/blob/main/GEMINI_MASTER_PROMPT_QA_V2.md
- Google Doc: https://docs.google.com/document/d/1BZy_Pkc8QUe0PEnpCNr1B1aYuXa7jdTogHfprWf9lSk/edit

Do NOT follow old instructions from the previously weekly-only or six-hour, draft-only system if they conflict with this new specification.

## Frequency and ownership

- GitHub publisher: every 2 hours at **UTC even hours :17**, i.e. **05:47,07:47,...03:47 IST**. It may publish **new audited Gumroad products without user approval** and schedule approved Pinterest Pins. Green executions with empty READY queues are not a successful product-generation cycle.
- Gemini Spark: try scheduling independent creative + retrospective QA **every 4 hours, IST 00:45/04:45/08:45/12:45/16:45/20:45**. Schedule MUST actually be created inside Gemini; ChatGPT/GitHub changes do not modify Gemini schedules. Keep Sunday deep quality review.
- Pinterest times: 08:30 / 14:30 / 20:30 America/New_York, 3 per US calendar day. Q-02 is already scheduled at 14:28 EDT on Oct 12 and must not be resubmitted.

## Queue fields that Gemini MUST populate after real checks

Both `Publishing Queue` (S:V) and `Gumroad Upload Queue` (O:R) now have:
- `QA Version` = `KGS-QA-V2`
- `QA Report Drive Link` = REAL item-specific shared Google Doc URL
- `QA Audited UTC` = actual current ISO-8601 UTC time
- `QA Outcome` = `PASS` only with full truthful inspection

The linked report must contain ITEM ID, QA VERSION, RESULT, EVIDENCE, and eight separate PASS audit fields: ASSET_OPEN, VISUAL, CONTENT, COPY, LINKS, LICENSE, FACTS, PRODUCT_MATCH. Every PASS must be backed by true evidence. Broken links, blank PDF pages, incorrect page counts, untested sums, clipping, copyright/licensing defects, generic/spam Pins, unverified savings promises or misrepresented digital capabilities mean FAIL / NEEDS_FIX, not READY.

GitHub additionally checks QA freshness (14 days), PDF US Letter page sizes and nonblank content streams, 2:3 image aspect, listing copy, real public Gumroad URLs and Buffer slot/queue uniqueness. If Gemini's report is fake, those machine checks alone may not catch every content defect; Gemini must actually examine every page and link.

## Retrospective priorities

1. Published KGS-001 and KGS-002: inspect actual downloads, live pages and matching copy; protect their identities and don't overwrite without issue review.
2. KGS-003: correct exaggerated 'automated rollover/calculator' and overbroad refunds text in source listing. Audit original 8-page printable and existing unpublished draft. Do not recreate it or reset to READY. CURRENT OVERRIDE: Keep KGS-003 at DRAFT_VERIFIED, QA Verified RECHECK_REQUIRED and QA Outcome FAIL. The customer-delivered PDF itself has wrong snowball ranking, impossible example payoff date, unsupported interest savings and inaccurate debt-free labeling. Regenerate and verify the source plus replace the existing Gumroad downloadable file (not append it); the historical automatic release path is disabled until a safe replacement routine has been tested. Do NOT mark RELEASE_READY yet.
3. Q-01 historically BLOCKED_TIME, but its source now uses 08:30 EDT. Recheck QA and only then mark READY and clear resolved timing error.
4. Q-02 already SCHEDULED_BUFFER and verified link: do not reschedule/duplicate.
5. Q-03..Q-06 have loose images but lack V2 certification; audit each image, source link and copy before READY.
6. Q-07..Q-42 have no single loose image links in the source queue. Extract, independently upload/share each genuine image and audit individually. Never use ZIP-only link/imaginary endpoints.
7. All previous products, covers, bulk schedule URLs, PDF claims, date conversions and Drive links must be independently rechecked; old Gemini DONE messages are not evidence.

## Future workflow

New products start at KGS-004, with absolutely unique source PDF/PNG/Google Doc/slug and complete QA report. Target one genuinely original fully verified product per day, more only when work meets standards; two-hour GitHub runs check the queue, they do not force Gemini to ship every two hours. Prepare three distinct Pins/day with correct published Gumroad destinations and NY/DST times.

Gumroad READY + QA Verified YES + QA V2 PASS -> GitHub creates draft, verifies, publishes and confirms actual public URL automatically. The publisher does not ask for human approval on these routine qualified releases.

Pinterest READY + QA Verified YES + QA V2 PASS + a real loose image + live Gumroad product destination -> GitHub hosts the image on Cloudinary, schedules via Buffer, checks link/board and records SCHEDULED_BUFFER. Do not claim Pinterest PUBLISHED until Buffer delivers a live Pinterest URL.

Creative errors -> Gemini repairs and re-audits; uncertain API/platform errors -> leave REVIEW or LINK_REVIEW for human reconciliation, never retry blindly.

For detailed timing and owner stop switch, see:
https://github.com/muditmathur2304-coder/kindgrid-autopilot/blob/main/OPERATIONS_STATUS.md
