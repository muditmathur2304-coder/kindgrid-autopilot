# KindGrid Autopilot — Current Operations and Safety
Updated October 10, 2026. CREATOR = ChatGPT. PUBLISHER = GitHub Actions. Existing Google Drive/Sheets and Gumroad/Buffer integrations are retained.

## New verified launch — October 10, 2026

- KGS-005 **Subscription & Renewal Control - 7-Page Printable Kit** was created in ChatGPT from the previously owner-approved original premium workbook sample and independently QC-checked. Published at $4.00 USD after direct PDF/cover attachment verification and live public URL fetch: https://kindgridstudio.gumroad.com/l/subscription-renewal-control-kit
- Source PDF: https://drive.google.com/file/d/1gx3d--n8IMn4jo6BVaNvizo6DzALd_Us/view ; cover https://drive.google.com/file/d/18BWsjXPWoRpDeJ4RLBvbPR3TvCmKVE83/view ; QA report https://docs.google.com/document/d/13vUsX4loTvatf5pzhROvxO0a2QO76e9eSY9aX3_4Q2k/edit
- Pinterest Q-44 submitted through connected Buffer and confirmed SCHEDULED_BUFFER (ID 6ac98f24b07d37ac975846a0, due 2026-10-10 01:11 UTC / 06:41 IST), matched to actual public Gumroad URL. Its Pin image is https://drive.google.com/file/d/1gfPY17Op2xNXxQ_ljlLBEMDlk5XRiwbu/view ; QA report https://docs.google.com/document/d/1oCUoECqf8Skn3s0FEd_JVloyub-Zzdy6OmWrXxsCkRY/edit . Do not call it PUBLISHED until Buffer delivery is independently verified.
- Owner-authorized one-time launch workflow succeeded at https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions/runs/38011641880 . That workflow has been archived/disabled to prevent duplicates.
- Existing published IDs KGS-001,KGS-002,KGS-004,KGS-005 are now protected; historical KGS-003 stays DRAFT_VERIFIED / QA FAIL. Q-43 remains PUBLISHED. Next truly new product ID **KGS-006**, next Pin **Q-45**. Never republish existing slugs.
- The ChatGPT recurring creator task remains scheduled but has NOT yet proven unattended PDF/PNG creation and Drive upload; do not treat this manual interactive launch as proof of the scheduled creative pipeline.

## Active timetable

- ChatGPT task KindGrid ChatGPT Production: registered and ENABLED. Every four hours at 00:45,04:45,08:45,12:45,16:45,20:45 IST, first scheduled run 08:45 on October 10. Use canonical creator manual: https://docs.google.com/document/d/1SCJjJOujkgcnTZp1VMdOe2M2X4geXUfElqiksXsuEoA/edit
- GitHub publisher cron: 17 */2 * * * UTC, equivalent to 05:47,07:47,09:47,11:47,13:47,15:47,17:47,19:47,21:47,23:47,01:47,03:47 IST. GitHub cron execution is best-effort.
- Pinterest public audience slots: 08:30, 14:30 and 20:30 America/New_York; use real EDT/EST offset for the specific date. Max three distinctive Pins per US day and max Buffer Free queue limit.
- No new billing/service/API key for ChatGPT creation is set up in GitHub.

## CRITICAL status caveat

The ChatGPT recurring task is REAL and ENABLED, and connected ChatGPT in this interactive session HAS demonstrated writing the user's two 7-page sample product sets into Google Drive. However, a scheduled ChatGPT execution may not be able to run the same Python file-production and Google Drive upload tools. No background run has yet proven it can autonomously generate/save a product. Its first real run must be audited, not assumed.

The user must disable old Gemini creative/QA Scheduled Actions in Gemini. We cannot edit Gemini provider-specific schedules from ChatGPT. Preserve all source history and working dashboard rows; no duplicate producer jobs.

## Distinct responsibilities

ChatGPT: original product ideas, unusually premium and human-crafted PDF content and layouts, professional strong cover and Pinterest thumbnails, true visual/technical audits, actual asset files, Drive/Docs storage, release-queue entry with QA-V2 certification ONLY after verified completion. Owner-approved design references: https://drive.google.com/drive/folders/15BnEZ8F5dZ13xDkaDM2cXp4vn5xBG-Ei

GitHub: only reads READY rows from the Dashboard, validates source files and QA evidence, creates/verifies/publishes new Gumroad products, schedules/Pinterest through Buffer, reconciles statuses; cannot create new products and cannot invoke the ChatGPT consumer app itself.

Creator spec + handoff: [CHATGPT_CREATION_HANDOFF.md](CHATGPT_CREATION_HANDOFF.md).

## Known protected products and posts

- KGS-001 and KGS-002: already published, may need retrospective quality/content improvements; do not overwrite without confirming seller customer deliveries.
- KGS-003: pre-existing seller draft (wzlgpm), QA FAIL, status DRAFT_VERIFIED. Contains wrong debt snowball ordering, impossible payoff example, unsupported interest claims. Existing Gumroad CLI update --file appends rather than replacing old customer files, so historical auto-release path is BLOCKED until a tested replacement procedure exists. Never re-create/publish it from a misleading READY.
- KGS-004: published original one-off Grocery Budget Kit, do not duplicate.
- Q-02: existing Buffer scheduled Pin, retain original time/ID.
- Q-43: already PUBLISHED to Pinterest, do not reschedule.
- Q-01/Q-03 and parts of historic Q04-Q42: blocked for QA defects or missing loose image links.
- New product starts KGS-005, next new Pin ID Q-44; always read live queue first.

## QA release gate

Two Sheets tabs use existing QA fields (version, report link, timestamp, outcome). Each row needs genuine current KGS-QA-V2 item-specific Google Docs with exact item ID, PASS + eight individual ASSET_OPEN, VISUAL, CONTENT, COPY, LINKS, LICENSE, FACTS, PRODUCT_MATCH PASS labels, and EVIDENCE from real visual/page/math/link checks. Do not certify just because a model said DONE. Customer-facing PDFs must have true US Letter pages and no blank/cropped content; covers/Pin images should be vertical ~2:3. Every source file must be actually uploaded to Drive with valid individual links accessible to publisher service account. New product Pin destinations must be live Gumroad product URLs, never draft/guessed links.

## Observed technical results

A prior one-off owner-authorized GitHub workflow did create and publish KGS-004 with actual six-page PDF and cover; Buffer Q-43 was subsequently confirmed published on Pinterest at https://www.pinterest.com/pin/1114148395352597855. The regular two-hour unattended publisher also ran LIVE with a green result but zero READY items; this proved the queue can be empty, NOT that ongoing creation works.

## Emergency pause and operational integrity

- Enabled publish only if repository Actions variable AUTOPILOT_LIVE_ENABLED=true and AUTOPILOT_PAUSED is not true.
- Stop new GitHub publishing by setting AUTOPILOT_PAUSED=true or disable the workflow. Existing scheduled Buffer posts / published Gumroad products remain independent.
- Status SCHEDULED_BUFFER is not actual PUBLISHED; DRAFT_VERIFIED is not sold.
- REVIEW/LINK_REVIEW and uncertain API outcomes must be reconciled, never blindly retried.
- Secrets (Gumroad, Buffer, Cloudinary, service account) stay in Actions Secrets, not prompts or Docs.
- Explicit human customer-service, payouts, taxes, broken-platform-auth and high-stakes QA decisions can still require intervention.

## Dashboard

https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit

## Final verification milestone

After first ChatGPT scheduled run at/after 08:45 IST October 10, verify actual new artifact file IDs and Drive location, QA Docs, queue row, and the first standard GitHub publication if an item becomes READY. Do not claim complete autonomous replacement before this evidence exists.
