# KindGrid Studio — ChatGPT Creator + GitHub Publisher
Effective October 10, 2026. This file is the authoritative creative handoff, superseding the historical Gemini instructions. It does NOT alter the existing publisher's technical QA rules.

## Real components and statuses

**ChatGPT Scheduled Task:** KindGrid ChatGPT Production, enabled, starting October 10 at 08:45 AM India time, repeats at 00:45 / 04:45 / 08:45 / 12:45 / 16:45 / 20:45 IST. Its mandate is real product creation, content quality review, and Google Drive handoff. **Limit:** the task has not yet completed an unattended run producing PDFs/PNGs and saving them to Drive. Some scheduled-task environments may lack file-generation or connected-Drive write access. If unavailable, accurately report the blocker, NEVER claim an upload, and keep the queue unchanged.

**GitHub publisher:** workflows/publisher.yml, cron 17 */2 * * * UTC, i.e. every two hours around 05:47 / 07:47 / ... / 03:47 IST. It publishes only actual READY products and Pins passing all existing QA V2 checks and live-mode gates. It cannot create source products or start a consumer ChatGPT chat via GitHub. No new OpenAI API usage/billing has been installed or authorized.

**Google Drive HQ:** https://drive.google.com/drive/folders/1XkUEtz2KqflOK3HB3ksbPtxZOBPP0lhN

**Business Dashboard:** https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit

**Premium sample reference folder, created and uploaded by ChatGPT:** https://drive.google.com/drive/folders/15BnEZ8F5dZ13xDkaDM2cXp4vn5xBG-Ei

**Historical KGS-003 hold:** KGS-003 currently DRAFT_VERIFIED with FAIL QA; no historical Gumroad draft auto-release. Preserve KGS-001/002/004 and existing Q-02 scheduled/Q-43 published. Never duplicate these.

**Gemini:** no longer intended to be an active creative agent. Its existing scheduled tasks must be disabled in Gemini's account by the user (ChatGPT cannot disable another provider's tasks). Preserve historical files and audit records.

## Creative quality: owner-approved STANDARD, not a generic template

Match or exceed the two professionally designed ChatGPT seven-page samples in the linked reference folder:
- Variable Income Money Map
- Subscription & Renewal Control

Use editorially natural, HUMAN-SOUNDING prose, genuinely useful worksheets, real practical examples and meaningful differentiation between product concepts. Make each product look authored with substantial care, not mass AI filler. The user has specifically requested MORE visual appeal, carefully chosen typography, sophisticated covers, attractive Pinterest thumbnail compositions, legible mobile-first text, and consistent layouts.

Create printable US Letter PDF (typically 6–12 pages if merited), original 1000x1500 PNG cover and distinct Pin images, truthful listing copy and accurate QA report. Render and inspect EVERY PDF page and each full-resolution image. Verify sums, claims, cross-references, empty pages, design clipping, page count, file format and end-user value. Do not claim specific savings, performance, guaranteed income, interactive spreadsheet features or automated calculations unless truly supported.

The samples are only design references, NOT two READY products: never upload, sell or release them without a new full licensing/commercial review and explicit user request. Do not reuse their layouts unchanged.

## Drive handoff (required outputs and folder mapping)

Original finished product PDF and cover: 03 Paid Products (or 02 Free Products for a true free lead magnet). Pinterest PNGs: 04 Pinterest Creatives. Listing copy Google Doc: 05 Gumroad Listings. Exact item-specific QA V2 Google Doc: 07 Business Operations.

Do not invent a Drive ID, link, access permission or publication result. Open/read back every created file; confirm the publisher service account can access it before calling READY.

Gumroad listing Doc must have the exact BEGIN_GUMROAD_SUMMARY, END_GUMROAD_SUMMARY, BEGIN_GUMROAD_DESCRIPTION, END_GUMROAD_DESCRIPTION delimiters. The description must accurately describe the PDF's actual pages and features.

## Gumroad Upload Queue — immutable schema

18 fields in order:
Product ID | Product Name | Price USD | Unique Slug | PDF Drive Link | Cover Drive Link | Listing Copy Drive Link | QA Verified (YES/NO) | Upload Status | Gumroad Live URL | Last Error | Last Attempt UTC | Attempt Count | Last Updated UTC | QA Version | QA Report Drive Link | QA Audited UTC | QA Outcome.

New product IDs begin with **KGS-005**; check the sheet before assigning subsequent IDs. Never reuse an existing slug. New product READY is only permitted after full real QA and actual files.

Required QA cells: QA Version = KGS-QA-V2, QA Outcome = PASS, QA Verified (YES/NO) = YES, QA Audited UTC = current real UTC ISO-8601 time, QA Report Drive Link = actual accessible item-specific Google Doc. Publisher service account checks this Doc's contents.

QA Doc MUST contain these exact standalone lines (replace ID as appropriate): 
ITEM ID: KGS-005
QA VERSION: KGS-QA-V2
RESULT: PASS
ASSET_OPEN: PASS
VISUAL: PASS
CONTENT: PASS
COPY: PASS
LINKS: PASS
LICENSE: PASS
FACTS: PASS
PRODUCT_MATCH: PASS
EVIDENCE: [detailed true evidence derived from actual source page render inspections, recalculations, source URLs, product matches and accessibility checks].

Do not certify unchecked work. Don't add PASS markers to a previously revoked/failed QA Doc. Create fresh QA evidence after actual corrections.

## Pinterest Publishing Queue

22 fields in order:
Queue ID | Product | Content Type | Scheduled Date | Time Window | US Scheduled Time | Target Board | Pin Title | Pin Description | Destination URL | Status | Pin Image Drive Link | QA Verified (YES/NO) | Actual Pinterest Pin URL | Last Error | Last Attempt UTC | Attempt Count | Batch ID | QA Version | QA Report Drive Link | QA Audited UTC | QA Outcome.

New item IDs start Q-44 (Q-43 was previously published successfully); inspect the queue for newer rows on each run. Target US audience windows 08:30 / 14:30 / 20:30 America/New_York, DST-aware. Maximum three genuinely distinct Pins per NY calendar day, one per window. Verify destination is the genuine PUBLIC Gumroad page; do not mark Pin READY while its new product remains a draft or unknown. Existing Q-02 has a confirmed scheduled Buffer ID; Q-43 published; never duplicate either.

## Scheduled production algorithm — every 4 hours

1. Read the latest dashboard, GitHub status and current reviewer notes before creating anything. Determine whether there are already 2 genuinely approved new READY products and adequate audited upcoming Pins.
2. In PARALLEL, triage urgent defects in existing LIVE products; preserve KGS-003 failed draft; do not let the unprocessed Q-07 through Q-42 archives prevent new premium products forever.
3. If fewer than two genuinely READY new product packs exist, CREATE/FINISH one new ORIGINAL useful product, with actual PDF and PNG, listing copy, QC report. Do not claim completion if the creation or Drive tools were unavailable. Limit to one new pack per run to conserve usage; if current cycle time is insufficient, record exact progress and resume next.
4. Prepare original individual Pinterest images for live products so the 3/day demand can be met without duplicate/spam.
5. Save finished assets in Drive, verify URLs and document text, and only then write eligible READY/QA PASS rows. Do not mutate publisher-managed status of already submitted posts. No forced publishing.
6. Report briefly with specific IDs, Drive links, verified steps, blockers and next action; not a generic idea list. No guarantees of zero design errors or commercial outcomes.

## First-run proof and owner controls

The four-hour ChatGPT task was created successfully, but the first unattended run's ability to generate and SAVE to Google Drive has NOT been demonstrated yet. The first run is scheduled for 08:45 IST October 10 2026. Check that it produced real PDF/PNG + Docs, accurate QA report and row; if not, the owner needs to choose an alternative automation runtime (a paid API-based GitHub creator is a different product from ChatGPT subscription).

GitHub remains automatically live only when repository variable AUTOPILOT_LIVE_ENABLED=true and AUTOPILOT_PAUSED is not true. Manual workflow dispatch stays dry. Pausing publication does NOT cancel existing Buffer scheduled posts or live Gumroad products.

This transition has NO added paid OpenAI API subscription or hidden payment requirement. Automated task execution and cloud access are subject to the user's subscription, account limits and future tool availability.
