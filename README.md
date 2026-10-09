# KindGrid Autopilot — secure publishing handoff (starter)

**Purpose:** Gemini Spark prepares PDFs, product covers and Pinterest images, and records `READY` rows in the existing KindGrid Studio Google Sheets dashboard. A scheduled GitHub Actions workflow checks those rows **every 6 hours** and (only after credentials/permissions and a pilot are validated) performs the repetitive publishing work. It never generates or rewrites creative assets.

> **CURRENT STATE (2026-10-09):** Deployed to a private GitHub repository. Google/Buffer/Cloudinary/Gumroad credentials were verified. A single Pinterest Pin was scheduled through GitHub and its Gumroad destination confirmed; a separate unpublished Gumroad draft was created with both attachments and visually verified by the owner. The 6-hour schedule is now **configured for actual operation**, but the first unattended scheduled run has NOT yet been observed. Scheduled runs can schedule approved Pinterest Pins and create *new unpublished* Gumroad drafts only. **Gumroad live publication is hard-locked off.** See [OPERATIONS_STATUS.md](OPERATIONS_STATUS.md) for the current runbook and pause switch.

Dashboard: https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit

## What it does

1. Reads `Gumroad Upload Queue` and `Publishing Queue` from your existing Sheets dashboard.
2. Processes **only** rows with an exact `READY` status and `QA Verified (YES/NO) = YES`.
3. Checks Google Drive links, Gumroad slugs, price ranges, pin board/title/description, destination URL and US time zone labels.
4. Fetches Google Drive PDF/cover files only on a permitted Gumroad upload run. Verifies real PDF and PNG content before creating anything.
5. Calls the pinned [Gumroad CLI](https://github.com/antiwork/gumroad-cli) with the **explicit `--draft` flag** to create an unpublished draft (the CLI publishes by default without this flag). It reads back the draft and refuses to mark it verified when file/cover verification is uncertain. Publishing is separately gated behind `GUMROAD_AUTOPUBLISH`.
6. On the Pinterest side, downloads the single Drive image, hosts **promotional images only** in Cloudinary, and uses Buffer's API to schedule by exact Eastern-time moment. Free-queue count (10) and maximum of 3 Pins per pass are enforced.
7. If the returned Buffer Pin destination URL is absent/wrong, records `LINK_REVIEW` and stops the batch (Buffer's roadmap reports this as a possible API defect). An image-only Pin with no destination is not a successful marketing result.
8. Tracks failures in a Sheet status/error field rather than retrying creative work or starting endless loops. Gemini fixes `NEEDS_FIX` rows in its own scheduled job and changes them back to `READY`.
9. Checks Buffer's delivery status on later passes: a Pin is `PUBLISHED` only if Buffer says `sent` and returns a Pinterest URL.

The controller **cannot directly start a Gemini Spark chat**. Feedback occurs through existing Sheet statuses; Gemini must separately run on its configured schedule and read those fields. Login, platform restrictions, insufficient API permissions and service outages remain possible human-intervention cases.

## Very important prerequisites

The first one-time setup requires you (not this starter project) to create/connect **GitHub, Buffer, Cloudinary, and a Google Cloud service account**, and to authorize a Gumroad seller token. There is no reason to give credentials to an AI chat.

### A. Create a private GitHub repository

- Create a **private** repository named `kindgrid-autopilot`.
- Extract this ZIP and upload its **contents** (including the hidden `.github` folder) to the repository. Don't upload PDFs, login cookies, seller API tokens, or your service-account JSON to the repository.
- Click **Actions**, and confirm the `KindGrid Autopilot (safe handoff)` workflow appears. It may run automatically every 6 hours, but at this stage it is a non-publishing dry run. GitHub's cron scheduler may be delayed.

### B. Connect Google Sheets and Google Drive

- In Google Cloud Console, create or select a project, enable **Google Sheets API, Google Drive API and Google Docs API**, and create a service account with a JSON key.
- Share the exact KindGrid Business Dashboard **and the Drive Business HQ and its child assets** with that service account's email, giving Sheets *Editor* and file read access. Private paid PDFs should stay private to the owner and this service account.
- Base64-encode the complete JSON key **locally** and store it in GitHub repository **Settings → Secrets and variables → Actions → Secrets** as `GOOGLE_SERVICE_ACCOUNT_JSON_B64`. Never post it in chat or commit it to GitHub. For local setup, see the commands below.

PowerShell (Windows):

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes('C:\secure\service-account.json')) | Set-Clipboard
```

Linux/macOS:

```bash
base64 -w0 /secure/path/service-account.json  # Linux
base64 -i /secure/path/service-account.json | tr -d '\n'  # macOS
```

### C. Connect Buffer and Pinterest

- Open https://buffer.com/, make a Free account, verify email and connect **your existing Pinterest account** as a channel.
- Make sure the Pinterest boards from the Google Sheet exist in Buffer.
- Create a **personal Buffer API key** at **Settings → API** (https://developers.buffer.com/guides/authentication.html). Add it to GitHub Secrets as `BUFFER_API_KEY`.
- Identify your Buffer Pinterest `channelId` and `organizationId` in Buffer's API explorer or CLI; add them as GitHub Secrets `BUFFER_PINTEREST_CHANNEL_ID` and `BUFFER_ORGANIZATION_ID`.
- If Buffer doesn't permit your channel to schedule full Pinterest posts or drops Pin destination links, leave `PIN_AUTOSCHEDULE=false` and stop here. Do not accept image-only Pins as success.

### D. Connect Cloudinary (public Pinterest images only)

- Sign up for a Cloudinary Free account. Put its `CLOUDINARY_URL` in GitHub Secrets.
- **Never upload paid PDFs, transaction records, private email or credentials to Cloudinary.** Only marketing graphics that are meant to be public.

### E. Gumroad seller authorization

- The [Gumroad CLI](https://github.com/antiwork/gumroad-cli) uses a **seller** access token for its `products` commands. Test on a computer you control using `gumroad auth login` and `gumroad user`. See the project's official seller-token instructions.
- Place a seller token in GitHub Secrets as `GUMROAD_ACCESS_TOKEN`. Do not copy any admin token into that field. The token grants sensitive seller capabilities: guard it and revoke it if exposed.
- **SAFETY:** Do not remove `--draft` from the create command: Gumroad CLI v0.20261002.0 makes new products public by default. The GitHub workflow installs a pinned Gumroad CLI release (`v0.20261002.0`) only when draft upload is explicitly enabled. The underlying CLI may change; test it against an unpublished draft before live publication.

### F. Activation gates — CURRENT SETTINGS

In `.github/workflows/publisher.yml`, only **scheduled** (cron) runs can be live when not paused. Manually dispatched runs remain read-only.

| Setting | Recurring workflow | Effect |
|---|---|---|
| `LIVE_MODE` | true on schedule | Enables the queue processor |
| `PIN_AUTOSCHEDULE` | true on schedule | Up to 3 approved Pins/run within Buffer queue limits |
| `GUMROAD_CREATE_DRAFTS` | true on schedule | Up to 1 **new unpublished** product draft/run |
| `GUMROAD_AUTOPUBLISH` | **false, hard-locked** | Cannot publish Gumroad products on schedule |
| `AUTOPILOT_PAUSED` repository variable | absent/false | Set to `true` to pause ALL scheduled external writes |

The `workflow_dispatch` screen is for safe previews. Refer to [OPERATIONS_STATUS.md](OPERATIONS_STATUS.md), not the outdated pilot instructions below, for actual operation.

## Previously completed pilot test sequence (historical)

The numbered guidance below records how the integrations were tested during initial setup. **It is not a request to repeat completed tests or change the active safety gates.** For current run status, see [OPERATIONS_STATUS.md](OPERATIONS_STATUS.md).


1. Run Actions → KindGrid Autopilot → **Run workflow** with `dry_run=true`: expect only queue summaries. As of the latest dashboard check on October 9, **KGS-003 is already `DRAFT_VERIFIED`**, **Q-01 is `BLOCKED_TIME`**, and **Q-02 through Q-06 are `READY`**. The included `sample_queue.json` demonstrates the original pre-test `READY` format; it is **not a current status export**.
2. Ensure Gemini has corrected KGS-003's listing description if it contains an unconditional “All sales of digital download files are final” claim. The starter deliberately marks this as `NEEDS_FIX` rather than silently altering Gemini's creative copy.
3. First ask Gemini to prepare **a new, not previously uploaded pilot product**, or inspect KGS-003's already verified draft in Gumroad. Do **not** reset KGS-003 from `DRAFT_VERIFIED` back to `READY`: that risks duplication. To test the API draft creation on a new item, enable `LIVE_MODE=true` and `GUMROAD_CREATE_DRAFTS=true`, with `GUMROAD_AUTOPUBLISH=false` and `PIN_AUTOSCHEDULE=false`, and run `dry_run=false`.
4. For the Pinterest pilot, connect Buffer and host a single promotional image. Enable `PIN_AUTOSCHEDULE=true` only for **one test Pin**, preserving Q-01's `BLOCKED_TIME` until its native-scheduler time issue is resolved. Verify that the created Pin keeps the **exact Gumroad destination link**. If it doesn't, stop and use Pinterest's native browser workflow or an approved Pinterest API integration instead.
5. **Existing KGS-003 draft:** `DRAFT_VERIFIED` plus `GUMROAD_AUTOPUBLISH=true` authorizes the controller to publish that verified draft after checking the updated listing description and attachments. It will never create a replacement draft for KGS-003. If Gemini must correct that draft's existing text, retain its edit URL and return it to `DRAFT_VERIFIED` after the fix rather than marking it as a new `READY` product.
6. Only after both pilot results are independently confirmed should you consider enabling normal scheduled publishing. To avoid accidentally sending several live Pins, first restrict the active queue to one test row. The CLI's publish operation is not enabled automatically by uploading this repository.

## Errors and retrying

- `NEEDS_FIX`: Gemini must fix missing/wrong creative inputs and explicitly mark the item `READY` again.
- `REVIEW`: An uncertain platform action, including possible partial success. **Do not retry automatically**. Reconcile against the destination first.
- `UPLOADING` or `SCHEDULING`: A previous attempt may still have succeeded despite lost network connectivity; do not create duplicates.
- `DRAFT_VERIFIED`: Gumroad draft only; not a public product.
- `SCHEDULED_BUFFER`: Scheduled inside Buffer; not proof that Pinterest has published it.
- `LINK_REVIEW`: Buffer's saved Pin destination URL is missing or wrong; stop future Pins until solved.
- `PUBLISHED`: Verified in the target platform or its confirmed delivery response.

## Security notes

- GitHub secret values are NOT included in this download. Never send them to ChatGPT, Gemini or any public repository.
- Only a **private** GitHub repository should be used for this seller automation.
- GitHub Actions time and API calls are subject to free limits and platform changes; zero subscription charges does **not** mean unlimited free capacity.
- Gumroad fees, payment verification and seller legal requirements still apply.
- Live user authorization for Google, Buffer, Gumroad and Cloudinary is unavoidable once. After validation, normal runs don't require a browser login.
- Never disable a platform's security protections or bypass authentication checks.

## Files

- `src/autopilot.py`: queue validator, Google Sheets/Drive/Docs adapter, Gumroad CLI adapter, Buffer scheduling adapter, error reporting
- `.github/workflows/publisher.yml`: 6-hour scheduled job with dry-run toggle, concurrency guard and pinned CLI install
- `tests/test_autopilot.py`: offline safety tests
- `sample_queue.json`: anonymized-format sample of the real KGS-003 and Q-01 rows (public business links, no private file bytes)
- `.env.example`: required environment variable names without credentials
- `GEMINI_HANDOFF.md`: instructions for Spark's queue writer and error-correction loop

**Known limitation:** The one-time live publishing pilots succeeded, but unattended cron delivery remains unproven until a scheduled run completes. Gemini Spark must maintain the upstream queue independently; errors that are ambiguous or security-related still require human review. Platform limits, uptime, and final Pinterest publication are not guaranteed.
