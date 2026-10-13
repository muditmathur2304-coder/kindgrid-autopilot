# KindGrid Studio — 7×7 Premium Daily Cadence
Effective 2026-10-13, by owner's instruction. Zero added investment.

## Exact meaning
- **Pinterest:** target UP TO 7 individually QA-pass, DIFFERENT, educational/solution-focused Pins per **America/New_York** calendar day. A Pin only counts as *published* after the real provider confirms its public Pinterest URL; Buffer's SCHEDULED_BUFFER is not published. Never spam a new image/text clone to reach the goal.
- **Gumroad:** target UP TO 7 **new distinct** genuinely customer-ready public product listings per NY day (paid AND free count as one listing each). Uploading an updated cover or editing a draft is not a new public listing. An existing public listing is not a new upload. Buyer-demand evidence, authentic seller UI/file verification, license check and strict math/visual QA remain mandatory. The current pair publisher only auto-releases a complete PAID+FREE pair after full validation: one pair per run. Other authorised one-time release mechanisms must not silently bypass that gate.
- **This is a production ambition, not an automatic promise of 7 successful uploads each day.** If there is no approved high-quality product/Pin, 0 is the correct number. No counterfeited inventory or fabricated provider links to fill the scoreboard.

## Timing and quota rules
- Existing ChatGPT creator/QA automation was changed from every 4 hours to every **2 hours**. Its ability to actually generate/import valid assets in recurring execution varies; monitor actual run output, not only task enabled flag.
- Existing publisher GitHub Actions workflow remains every 2 hours at even UTC hours :17, strictly live mode only for scheduled events and independently QA-approved queue rows.
- Publisher environmental limits now `PIN_DAILY_LIMIT=7`, `MAX_PINS_PER_RUN=7`, `GUMROAD_DAILY_LIMIT=7`, `MAX_GUMROAD_PER_RUN=2`, `PIN_LOOKAHEAD_HOURS=36`.
- **Seven compatible New York slots:** Early Morning 08:00, Morning 08:30, Late Morning 10:30, Midday 12:30, Afternoon 14:30, Late Afternoon 16:30, Evening 20:30. The publisher accepts backup Late Evening 21:30 but prevents 8+ confirmed/scheduled Pins on any NY day. Use correct EDT/EST label, preserve existing reservations, do not schedule two visuals in one window.
- Buffer **Free** permits **10 posts pending in the queue at once**, not a 10/day cap, and will not allow unlimited advance scheduling. Verify current queue count before any write and refill as published posts clear. No subscription upgrades authorised.
- The paired uploader counts confirmed PUBLISHED rows with recorded UTC Last Updated timestamps converted to New York day. To protect the paid+free release as a unit, it refuses to start another pair when fewer than 2 daily slots remain. One-off Gumroad uploads should apply the same daily ceiling.
- No guarantee of Pinterest reach or sales; fewer differentiated Pins may outperform repetitive volume.

## Mandatory premium quality, independent of daily target
- Truly functional niche-specific Excel/Sheets tools, practical documented user workflows and realistic solved examples; a free tool must solve a smaller buyer problem on its own.
- Relevant original editorial/3D-style infographics integrated within actual downloadable XLSX/PDF and real screenshot gallery/marketing images. Human-checked typography, spacing, no clipped visuals.
- XLSX embedded images nonempty, formulas preserved, input/profit/capacity scenarios tested, real app compatibility verified where possible; no static image masquerading as interactive output.
- 1000x1500 original accurate cover/Pin, proof of real licensed source assets, original content and no invented search/sales/savings claims.
- KGS-QA-V2 item-specific audited Drive report is required before any READY flag; seller must actually verify uploaded files, publicly published slug and customer download files; never retry uncertain provider creation.
- Historical KGS-003 math-defective draft and KGS-009 uncertain free attachment remain held. KGS-010 paid BakeSlot and KGS-011 free companion are already published; protect customer entitlements.

## Daily evidence log
Maintain per-New-York-day totals: approved new Gumroad products, actual new public Gumroad listings, original QA-approved Pin creatives, scheduled Buffer posts, real PUBLISHED Pinterest URLs, impressions, outbound clicks, free downloads, paid orders, refunds/net revenue. Only factual observed metrics; 7 planned != 7 published. Examine completion/quality and acquisition impact at 7 and 30 days.

## Sources and implementation
Google Sheet: https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit , tab `Automation Cadence & QA` for current effective rules.
Official Buffer Free limit: https://support.buffer.com/articles/how-many-posts-can-i-schedule-in-advance-Kmy2IEecqm
Pinterest original-content recommendations: https://help.pinterest.com/en/business/article/pin-performance-and-distribution
Code: `src/autopilot.py` seven-slot safe scheduler, `src/paired_release.py` complete pair daily quota gate, `.github/workflows/publisher.yml` configuration, regression tests in `tests/`.

No upfront expenditure, forced publishing, artificial reviews or duplicate provider writes authorised.
