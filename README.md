# KindGrid Autopilot — ChatGPT Creator + GitHub Publisher

**Current system (October 10, 2026):** ChatGPT is now the designated premium creative + QA producer. The existing GitHub Actions workflow handles the 2-hour Gumroad and Pinterest publishing checks. Connected Google Drive/Docs/Sheets hold actual finished assets, listings, QA evidence and the publishing queues. Gemini Spark is no longer an intended part of the active workflow.

## Authoritative current instructions

- ChatGPT creation and handoff: [CHATGPT_CREATION_HANDOFF.md](CHATGPT_CREATION_HANDOFF.md)
- Current safety rules and known product defects: [OPERATIONS_STATUS.md](OPERATIONS_STATUS.md)
- Canonical ChatGPT operational manual in Google Drive: https://docs.google.com/document/d/1SCJjJOujkgcnTZp1VMdOe2M2X4geXUfElqiksXsuEoA/edit
- Owner-approved premium design references saved by ChatGPT to Google Drive: https://drive.google.com/drive/folders/15BnEZ8F5dZ13xDkaDM2cXp4vn5xBG-Ei
- Business Dashboard: https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit
- Publisher workflow: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions/workflows/publisher.yml
- Prior GEMINI_HANDOFF.md and GEMINI_MASTER_PROMPT_QA_V2.md are archived historical materials; do NOT follow their creative schedules or use them as current instructions.

## Scheduled tasks

**ChatGPT production and QA:** an actual ChatGPT recurring task named KindGrid ChatGPT Production has been CREATED and ENABLED; its first run is scheduled for October 10 2026 at 08:45 AM Asia/Kolkata and repeats every 4 hours (00:45 / 04:45 / 08:45 / 12:45 / 16:45 / 20:45 IST). Each run attempts one premium source package and fully truthful QA, saving to Drive/Sheets only where the scheduled-run tools support PDF/PNG creation and connector writes. The scheduled task has NOT yet proven it can execute PDF/PNG creation and Drive uploads unattended. Do not equate a registered reminder with successful unattended production.

**GitHub automated publishing:** cron 17 */2 * * * UTC: every even UTC hour at minute 17 (IST 05:47 / 07:47 / ... / 03:47). GitHub checks the READY queue and publishes no more than one new thoroughly approved Gumroad product/run. Buffer schedules audited Pinterest Pins at most three per New York calendar day (08:30, 14:30, 20:30 America/New_York). Delays/missed GitHub scheduled runs remain possible.

**No new API/billing:** a consumer ChatGPT subscription is not an OpenAI API key. This repository does NOT invoke the ChatGPT app in GitHub Actions, does not contain a paid OpenAI API agent, and does not autonomously generate PDFs from GitHub. A separate API-based creator would require explicit authorization and potentially additional cost.

## Safe release conditions

- READY is earned only after a real PDF, cover, listing Docs and item-specific QA V2 document exist in Google Drive with verified IDs, permissions, actual renders and arithmetic/claim checks.
- Gumroad listing copy uses exact BEGIN_GUMROAD_SUMMARY/DESCRIPTION and END_GUMROAD_SUMMARY/DESCRIPTION markers.
- QA Doc must contain ITEM ID, QA VERSION KGS-QA-V2, RESULT PASS, eight separate evidence-backed QA checks and substantive item-specific EVIDENCE.
- Existing published KGS-001, KGS-002, KGS-004 and Q-43 must never be recreated.
- KGS-003 remains an unpublished defective historical draft on QA FAIL until actual PDF replacement has been proven; its historical auto-release code is disabled.
- Q-02 remains an existing scheduled Pin; do not duplicate. Historic Q-01/Q-03 etc have specific issue holds.
- Do not bypass platform-review states or re-trigger an uncertain seller/Buffer write.
- GitHub live switch: repository variable AUTOPILOT_LIVE_ENABLED=true; stop switch: AUTOPILOT_PAUSED=true, or disable workflow in GitHub Actions. Manual workflow dispatch remains dry/read-only.

## Owner's remaining actions

1. In Gemini Scheduled Actions, **disable the old KindGrid creative/QA schedule** and other duplicate content-creation schedules. ChatGPT cannot do that in Gemini.
2. Let the first ChatGPT 08:45 IST scheduled run occur; review its actual result. It must produce and SAVE a file in Drive with correct links before declaring creator replacement fully functional.
3. If scheduled ChatGPT does not have PDF/PNG file-making/Drive-writer tools, choose either manual ChatGPT batch creation followed by free GitHub auto-publishing OR a separately approved API-powered creator with possible additional billing. Do not silently pretend the automation works.
4. Check both actual publishing outcomes and customer support/revenue periodically; no guaranteed product count or earnings.

For owner-approved visual quality, treat the two Drive reference product packages as the starting floor, not cookie-cutter templates.
