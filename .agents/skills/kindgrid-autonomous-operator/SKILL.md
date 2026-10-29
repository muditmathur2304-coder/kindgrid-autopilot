---
name: kindgrid-autonomous-operator
description: Fully autonomous daily operations loop for KindGrid Studio. Inspects dashboard queues, conducts niche research, designs Excel decision tools and illustrated PDFs, creates 2:3 Pinterest creatives, audits against KGS-QA-V2, and pushes to GitHub silently.
---

# KindGrid Autonomous Operator Skill

This skill governs the end-to-end autonomous operation of KindGrid Studio by Antigravity. It is executed autonomously on a recurring schedule without requiring any manual human coding, terminal commands, or manual Google Drive uploads.

## Operating Principles

1. **Zero Human Burden**:
   - Never prompt the operator to run git commands, push from GitHub Desktop, write code, or manually upload files to Google Drive.
   - All Git pushes are executed silently via the authenticated remote helper (`https://x-access-token:...@github.com/...`).
   - All file uploads to Google Drive and row insertions into the Google Sheet are executed idempotently via GitHub Actions (`scripts.asset_pipeline`).

2. **Strict Quality Gating (KGS-QA-V2)**:
   - Every product release requires a reciprocal **PAID + FREE pair** (`Pair Role = PAID` / `FREE`).
   - Every paid product requires an editable `.xlsx` decision tool meeting the 8 Tool-First criteria (≥2 sheets, ≥10 formulas, embedded visual, 12 tested edge cases, no external links/macros).
   - Every paid product includes a 3–15 page illustrated field guide PDF; every free product includes a 3–7 page actionable starter PDF.
   - Every pin must be 2:3 vertical (1000×1500 or 1200×1800 PNG) and mapped to a real Pinterest board with verified destination URLs.

3. **Daily Autonomous Cadence**:
   On each scheduled wake-up:
   1. **Inspect Live Dashboard & Gumroad**:
      - Read the Google Sheet (`Gumroad Upload Queue` and `Publishing Queue`).
      - Check existing product IDs, active statuses, and scheduled pins.
   2. **Queue Health & Pin Scheduling**:
      - Ensure at least 4–7 audited Pinterest pins are queued in the lookahead window.
      - If pins are running low, generate new high-CTR pin creatives for existing live products.
   3. **Campaign Generation (When Queue Needs Next Pair)**:
      - If no `PAIR_READY` pair is currently waiting to publish, initiate the next campaign (e.g., KGS-026 + KGS-027).
      - Step 1: Research high-intent search volume on Etsy/Pinterest/Google for underserved business niches (e.g., mobile detailing, cottage food, mobile dog grooming, vintage resale).
      - Step 2: Compile a 5-section Demand Evidence document (≥750 chars, ≥2 real source URLs).
      - Step 3: Build the `.xlsx` financial model with professional formatting, formula protections, and embedded instructional diagrams.
      - Step 4: Write and compile the paid and free PDF guides using ReportLab.
      - Step 5: Render high-converting 2:3 visual mockups (covers, contact sheets, gallery cards, and Pinterest pins).
      - Step 6: Draft listing copy and strict KGS-QA-V2 audit reports for both products.
      - Step 7: Save all assets to `assets/kgs-XXX/` with a complete `manifest.json`.
      - Step 8: Run unit test suite (`python -m unittest discover -s tests -v`) to verify all assertions pass.
      - Step 9: Stage, commit, and push directly to `origin main`.
   4. **Verification & Logging**:
      - Confirm GitHub Actions (`publisher.yml` and `asset-pipeline.yml`) successfully trigger and ingest the new assets.
      - Record operational notes in `OPERATIONS_STATUS.md`.

## Prohibited Actions
- Never make direct live write calls to Gumroad or Buffer APIs from local scripts. All external mutations are handled strictly by GitHub Actions (`publisher.yml`).
- Never reuse a Product ID (KGS-xxx), Queue ID (Q-xxx), or Gumroad slug.
- Never publish unpaired single products.
