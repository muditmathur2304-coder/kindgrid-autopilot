# KindGrid Autopilot — Operational Status, October 10 2026

## CURRENT release guard
- GitHub `.github/workflows/publisher.yml` executes best-effort at UTC 17 past every even hour (IST 05:47,07:47,...). Old Gumroad solo uploader disabled (`GUMROAD_CREATE_DRAFTS=false`, `GUMROAD_AUTOPUBLISH=false`). New PAID+FREE gate enabled (`PAIRED_RELEASE_ENABLED=true`) in `src/paired_release.py`. Only when both new KGS-008+ queue rows share one Pair ID, PAIR_READY, reciprocal FREE and PAID roles, QA V2 reports, verified research doc, page contact-sheet PNGs, gallery images and actual Drive PDF/PNG files will it attempt ONE pair. This generic release path passed unit tests but has NOT yet been proven by a fresh end-to-end live KGS-008+ pair. No approved future pair currently exists.
- Pinterest queue auto scheduler remains disabled (`PIN_AUTOSCHEDULE=false`) during design/SEO overhaul; pre-scheduled Q-45..Q-47 remain in Buffer and are not canceled. It must only resume after source-based Pin quality audit and public destination checks. Buffer quota 10 max.
- ChatGPT scheduled creative task `KindGrid ChatGPT Production` every four hours was temporarily PAUSED pending updated QA quality standard. Its ability to produce PDF/PNG and upload to Drive unattended is still unverified. GitHub does not have a consumer ChatGPT API or paid creator account configured.

## Existing releases and editorial triage
- FREE KGS-007 https://kindgridstudio.gumroad.com/l/paycheck-gap-starter paired to PAID KGS-006 https://kindgridstudio.gumroad.com/l/paycheck-gap-playbook (24-page workbook plus real XLSX companion); successful original matched launch. Protect both, test user acquisition. Existing scheduled Q-45, Q-46, Q-47 are unaffected.
- KGS-004 $3 grocery and KGS-005 $4 subscription seven/six-page products live but too light/generic for new aggressive promotion; EDITORIAL_REWORK before advancing. Their old buyers must retain access. KGS-001 free and KGS-002 paid live; KGS-002 finance maximum example requires review. KGS-003 historical debt draft QA FAIL must never auto-publish until actual customer PDF replaced and math corrected.
- Pin Q-43 and Q-44 published. Earlier rejected/blocked Q-01/Q-03 and legacy ZIP Pins require actual unique image/QA, no duplicate submissions.

## Business signal and strategy
- Original video video https://youtu.be/RJl_ofd_s6w (creator reported 17 free and 7 paid sales in seven days, but unverified traffic/profit attribution) demonstrates useful freebie -> valuable paid conversion via Pinterest SEO. That result is NOT a guarantee.
- Owner's ~2 Gumroad views and 0 Pinterest analytics views were not independently confirmed via authenticated analytics. Pinterest metrics can lag ~48 hours, Gumroad Discover has eligibility thresholds and does not necessarily give new sellers internal traffic. Do not make inference about conversion or shadowban from tiny numbers.
- Market comparison established broad craft-show planners crowded (~1000+ Etsy results). Irregular-income listings demonstrate competition and prices, not guaranteed demand. Specific micro-bakery farmers-market break-even organizer is a research hypothesis pending honest Pinterest US signals. Do not release based merely on a keyword or low search-result count.
- Operational research: https://docs.google.com/document/d/1IbyUI_KTdkuQdyutjIGHFp1xk1km7StMpEfbUiNeo44/edit and [PREMIUM_PAIR_POLICY.md](PREMIUM_PAIR_POLICY.md). New dashboard `Growth & Quality Review` records evidence, action statuses and reporting cadence.
- Initial Pin marketing test two genuinely distinct creative Pins to FREE, one to PAID, naturally researched keywords; real UTM whitelist in branded Gumroad links; measure impressions, outbound clicks, Gumroad referral landing visits, free downloads and paid checkouts after 48 hours, 7, 14 and 30 days.

## Safeguards
- No automatic stale refunds, no paid advertising, fake purchases, invented metrics or unauthorized new API billing.
- Uncertain upload state => REVIEW/PAIR_HELD, no blind automatic retries. Paid public page verified BEFORE free publish with matching link. Existing customer PDFs not silently replaced through CLI appends.
- GitHub owner's emergency brake: AUTOPILOT_PAUSED=true, or disable workflow. Manual workflow_dispatch is read-only. Github CI must be green before any new live pair.
- Premium content means human-edited writing, ORIGINAL explanatory infographics and worked examples rather than pages of placeholder tables; true customer value and actual image/print QA, not nominal page count.
