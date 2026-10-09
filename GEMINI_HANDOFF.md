# Message to Gemini Spark — publisher agent integration

Continue creating and QA-checking KindGrid Studio products using the existing Drive and dashboard. **The GitHub Actions publisher is now configured to run every 6 hours**: it may automatically schedule ready Pinterest Pins and create **unpublished new Gumroad drafts**, but it NEVER publishes Gumroad products automatically. Manual Github runs are still dry runs. Only platform-confirmed scheduled or published statuses may be reported; the first unattended cron execution has not yet been observed.

## Handoff requirements

- Keep using `Gumroad Upload Queue` and `Publishing Queue`, preserve existing rows and never edit operational status fields while they are `UPLOADING`, `SCHEDULING`, `DRAFT_VERIFIED`, `SCHEDULED_BUFFER`, `PUBLISHED`, `REVIEW`, `LINK_REVIEW` or `BLOCKED_TIME` without explicit reconciliation. KGS-003 is ALREADY `DRAFT_VERIFIED` (do not upload it again). Q-01 is `BLOCKED_TIME` from the native Pinterest scheduler (do not claim it was scheduled).
- **Permanent protection:** KGS-001, KGS-002, KGS-003, and the one-off technical Gumroad upload-test draft must not be placed into a new `READY` row. New product IDs start at **KGS-004**, with fresh unique slugs and source assets. Never add a Gumroad product to the Pinterest marketing queue until it has a verified *public* product URL; draft edit URLs are NOT marketing destinations.
- For a Gumroad product, complete columns A–I, including a **unique** product ID and custom slug, price USD, separate genuine Drive PDF/PNG links, and a separate Google Doc that holds ready-to-use product copy. Set H=`YES`, I=`READY` only after full PDF and cover QA.
- Format the listing Doc so the publisher can extract copy unambiguously:

```
BEGIN_GUMROAD_SUMMARY
A compelling short summary written by Gemini.
END_GUMROAD_SUMMARY
BEGIN_GUMROAD_DESCRIPTION
The complete final product description, with licensing and financial disclaimers.
END_GUMROAD_DESCRIPTION
```

- Do not claim unconditional no-refunds or guaranteed savings. Use accurate product contents, page numbers and licensing.
- For each Pinterest row, use a real INDIVIDUAL `drive.google.com/file/d/<id>/view` PNG link in column L, put `YES` in column M, and only then set status K to `READY`.
- Correct US time labels using `America/New_York` for each date. October 12–13 2026 is EDT (UTC-4); daylight saving ends November 1, 2026, after which EST (UTC-5) applies.
- Never use fake image-hosting URLs from `kindgridstudio.gumroad.com/assets/...`; the publisher hosts only approved promotional graphics when needed.
- Check `NEEDS_FIX`, `REVIEW` and `LINK_REVIEW` entries on each Gemini review run. Fix only creative/source-file issues. For NEW products, change to `READY` only once the issue is fixed. For a *verified existing Gumroad draft* (like KGS-003), restore `DRAFT_VERIFIED` after fixing its listing copy and preserve its actual Gumroad edit URL; NEVER change it to `READY` because that would request duplicate draft creation. If the error is an API/auth issue, preserve `REVIEW` for human intervention rather than repeatedly recreating assets.
- Never create duplicate products or Pins, and do not mark `SCHEDULED_BUFFER` as `PUBLISHED`.
- The editor must not alter the user's Google Sheets operational columns N–R of the Pinterest queue or J–N of the Gumroad queue except to resolve an explicitly documented error after inspecting it.

## First concrete task

KGS-003's current listing kit includes the statement "All sales of digital download files are final." Review that absolute claim and replace it with accurate, legally appropriate wording in Gemini's own copy. Use the BEGIN/END delimiters above and retain all checked product specifications. Keep KGS-003 as `DRAFT_VERIFIED` (its existing Gumroad draft must not be recreated) after the updated copy is fully checked; preserve the verified draft edit URL.
