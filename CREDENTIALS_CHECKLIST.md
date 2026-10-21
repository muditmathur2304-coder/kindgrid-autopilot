# KindGrid Studio — Credentials Checklist

**Purpose:** Service names, required permissions, connection status, and secure setup steps.
**Security:** This document NEVER contains actual secret values. Only names, types, and locations.

---

## ⚠️ Critical Security Rules

- Do NOT paste any API key, token, or JSON content into a chat conversation
- Do NOT share secret values in this file or any document in this repository
- All credentials are stored in GitHub Actions Secrets — the only place they should live
- If a secret is accidentally exposed, rotate it immediately in the relevant service

---

## Required GitHub Secrets

Go to: **https://github.com/muditmathur2304-coder/kindgrid-autopilot/settings/secrets/actions**

| Secret Name | Service | Type | Required Permissions | Notes |
|------------|---------|------|---------------------|-------|
| `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | Google (Sheets, Drive, Docs) | Service account JSON, base64-encoded | Viewer on Drive files; Editor on the Business Dashboard spreadsheet; Viewer on QA/listing/research Google Docs | Entire JSON file, base64-encoded. Must share specific files with the service account email. |
| `BUFFER_API_KEY` | Buffer | API token | Read + Write on Pinterest channel | From Buffer → Account → API Keys |
| `BUFFER_PINTEREST_CHANNEL_ID` | Buffer | Channel ID string | — | The ID of your connected Pinterest channel in Buffer |
| `BUFFER_ORGANIZATION_ID` | Buffer | Organization ID string | — | Your Buffer organization ID |
| `CLOUDINARY_URL` | Cloudinary | Connection URL | Upload permission on `kindgrid-pinterest` folder | Format: `cloudinary://api_key:api_secret@cloud_name` |
| `GUMROAD_ACCESS_TOKEN` | Gumroad | API access token | Read + Write on seller account; create/publish products | From Gumroad → Settings → Applications |

---

## Required GitHub Variables

Go to: **https://github.com/muditmathur2304-coder/kindgrid-autopilot/settings/variables/actions**

| Variable Name | Type | Required Value | Current Status | Notes |
|--------------|------|----------------|----------------|-------|
| `AUTOPILOT_LIVE_ENABLED` | Variable (not secret) | `true` | **Verify this exists and is set to `true`** | If missing or `false`, publisher will never make live writes |
| `AUTOPILOT_PAUSED` | Variable (not secret) | `false` or not set | **Verify this is NOT `true`** | Emergency stop switch; must be `false` for normal operation |

---

## Google Service Account Setup

The Google service account allows GitHub Actions to read your Drive files and update the Business Dashboard without you needing to be logged in.

### What the service account needs access to

**Must be able to read:**
- All product PDF files in Drive (viewer permission on each file, or on the Business HQ folder)
- All product cover PNG files in Drive
- All gallery image PNG files in Drive
- All contact sheet PNG files in Drive
- All XLSX files in Drive
- All QA report Google Docs
- All listing copy Google Docs
- All demand evidence Google Docs

**Must be able to read AND write:**
- The Business Dashboard (Google Sheets) — Editor permission

### How to find the service account email
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Find the KindGrid service account
3. Copy its email address (looks like `something@something.iam.gserviceaccount.com`)

### How to share files with the service account
For any new Drive file or folder:
1. Right-click the file or folder in Google Drive
2. Click "Share"
3. Paste the service account email address
4. Set to "Viewer" (for Drive files) or "Editor" (for the Business Dashboard spreadsheet)
5. Click "Send" (it will say the email "can't be notified" — that is fine, click "Share anyway")

### How to generate a new service account key (if needed)
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Click on the KindGrid service account
3. Click "Keys" → "Add Key" → "Create new key" → JSON
4. Download the JSON file
5. Encode it to base64: open a terminal and run `base64 -w 0 keyfile.json` (Linux/Mac) or use an online base64 encoder
6. Paste the base64 result as the value of `GOOGLE_SERVICE_ACCOUNT_JSON_B64` in GitHub Secrets
7. Delete the downloaded JSON file from your computer

---

## Buffer Setup

Buffer connects your Pinterest business account and allows the publisher to schedule Pins.

### Required connection
- A Buffer account linked to your Pinterest business account
- Buffer Free plan allows: up to 10 scheduled posts per channel at any one time

### Finding your Buffer credentials
- **API Key:** Buffer → Account Settings → API Keys → "Copy" your personal access token
- **Channel ID:** Buffer → Channels → click Pinterest → the ID appears in the URL: `https://buffer.com/manage/[CHANNEL_ID]/...`
- **Organization ID:** Buffer → Manage → in the URL: `https://buffer.com/manage/[ORG_ID]/...`

### Connection health check
Run a dry-run workflow dispatch (see OPERATIONS_RUNBOOK.md) and look for the "Verify Buffer connection" step in the logs.

---

## Cloudinary Setup

Cloudinary hosts your Pin images publicly so that Buffer can attach them to Pinterest posts.

### Required configuration
- A Cloudinary account (free tier is sufficient)
- A folder named `kindgrid-pinterest` in your Cloudinary media library

### Finding your Cloudinary URL
1. Log into Cloudinary Dashboard
2. Click "Dashboard" in the top menu
3. Your Cloud URL format is: `cloudinary://[API_KEY]:[API_SECRET]@[CLOUD_NAME]`
4. Example format (not real): `cloudinary://123456789012345:AbCdEfGhIjKlMnOpQrStUvWxYz@kindgrid`

### Note on duplicate prevention
The publisher uploads images with `overwrite=False` — if an image with the same Pin ID already exists in Cloudinary, it will NOT be re-uploaded. This prevents duplicates.

---

## Gumroad Setup

Gumroad hosts your products and processes payments.

### Required account type
- A Gumroad seller account (the standard seller account)
- Your storefront: https://kindgridstudio.gumroad.com

### Finding your access token
1. Log into Gumroad
2. Go to Settings → Advanced → Applications
3. Copy your "Access Token"
4. If you need to regenerate it, do so and update the GitHub secret immediately

### What the token can do
The Gumroad access token allows the publisher to:
- List all your existing products (read)
- Create new draft products (write)
- Publish draft products (write)
- Read product details (read)

> **Note:** The token does NOT give access to payment or payout settings. Never share the token publicly. If you suspect it has been compromised, rotate it immediately in Gumroad settings and update the GitHub secret.

---

## Connection Status Verification

Use the dry-run workflow to verify all connections are working. Expected results:

| Step | Expected Result | If Failed |
|------|----------------|-----------|
| Verify Buffer connection | Lists Pinterest boards found | Check BUFFER_API_KEY; reconnect Pinterest in Buffer |
| Verify Cloudinary connection | Reports Cloudinary cloud name | Check CLOUDINARY_URL format |
| Verify Pinterest board | Lists board names | Check BUFFER_PINTEREST_CHANNEL_ID |
| Verify Gumroad | Lists your products | Check GUMROAD_ACCESS_TOKEN; may have expired |
| Inspect staged pair preflight | Reports queue status | Check GOOGLE_SERVICE_ACCOUNT_JSON_B64 |

---

## What to Do If a Secret Expires or Rotates

| Service | How to rotate | After rotating |
|---------|--------------|----------------|
| Google Service Account | Generate a new key (see above); delete old key in Google Cloud Console | Update `GOOGLE_SERVICE_ACCOUNT_JSON_B64` in GitHub Secrets |
| Buffer | Go to Buffer → Account Settings → API Keys → regenerate | Update `BUFFER_API_KEY` in GitHub Secrets |
| Cloudinary | Go to Cloudinary Dashboard → Account → Security → rotate API secret | Update `CLOUDINARY_URL` in GitHub Secrets with new secret |
| Gumroad | Go to Gumroad → Settings → Advanced → Applications → regenerate | Update `GUMROAD_ACCESS_TOKEN` in GitHub Secrets |

After updating any secret: run a dry-run workflow to confirm the new credential works before relying on the scheduled publisher.

---

## What Is NOT Required

The following would require costs or have been explicitly rejected:

| Service | Status |
|---------|--------|
| Pinterest Ads | NOT used — organic traffic only |
| Buffer paid plan | NOT required — Buffer Free is sufficient |
| Paid Gumroad plan | NOT required — standard seller account |
| Cloudinary paid plan | NOT required — free tier is sufficient |
| OpenAI / ChatGPT API | NOT used — Antigravity replaced this |
| Additional AI APIs | NOT authorized |
| Google Workspace paid | NOT required |
| Domain/hosting | NOT required — Gumroad provides the storefront |
