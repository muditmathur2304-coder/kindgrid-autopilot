# KindGrid Studio — Operations Runbook

**For:** The business owner (non-technical)
**Purpose:** How to run, monitor, troubleshoot, pause, and resume KindGrid Studio without writing any code.

---

## What Happens Automatically (Without You Doing Anything)

Once set up correctly, your business runs on two automatic systems:

1. **The Publisher** (GitHub Actions) — checks your Business Dashboard queue every 2 hours, 24/7. If there are approved products ready, it publishes them to Gumroad and schedules them on Pinterest. If the queue is empty or nothing passes quality checks, it does nothing and waits for the next check.

2. **The Creator** (Antigravity) — when you start a conversation with Antigravity, it can research new product ideas, build the tools, design the content, perform quality checks, and prepare the queue for the Publisher. (Note: Antigravity only works when you open a conversation — it does not run in the background on its own between conversations.)

> **What happens when your computer is off?** The Publisher (GitHub Actions) runs on GitHub's servers — it will keep running regardless of whether your computer is on or off. Antigravity requires an open conversation to do creative work. Your products stay live on Gumroad 24/7 regardless of any of this.

---

## The Business Dashboard — Your Control Center

Open this every time you want to check what is happening:
**https://docs.google.com/spreadsheets/d/1Ohlav6l4e62r2vH5u3cRSIFMrgBwfAbvi8zJxsByivs/edit**

Key tabs to know:
| Tab Name | What It Shows |
|----------|---------------|
| **Gumroad Upload Queue** | All products and their current status (PAIR_READY, PUBLISHED, REVIEW, etc.) |
| **Publishing Queue** | All Pinterest Pins and their status (READY, SCHEDULED_BUFFER, PUBLISHED) |
| **Growth & Quality Review** | Evidence, research findings, and quality notes |
| **Automated Tools Pipeline** | R&D products not yet ready for public launch |
| **Market Research Evidence** | Demand research findings |
| **Automation Cadence & QA** | Current effective rules for the publisher |
| **Pinterest US Buyer Intent Research** | Keyword and audience research |

### Product status meanings (Gumroad Upload Queue)
| Status | Meaning | Your action needed? |
|--------|---------|---------------------|
| PAIR_READY | Fully approved — will publish on next scheduled run | None — wait |
| PUBLISHING/PAIR_RELEASING | Publisher is actively creating this product right now | Do not touch |
| DRAFT_VERIFIED | Created but not yet published | Review — may need to publish |
| PUBLISHED | Live on your Gumroad store ✅ | None |
| NEEDS_FIX | Quality issue found — publisher stopped it | Tell Antigravity what it says |
| REVIEW | Something went wrong — requires investigation | Do not retry — contact Antigravity |
| PAIR_HELD | Paid succeeded but free is waiting due to an error | Contact Antigravity |
| EDITORIAL_REWORK | Old product; too generic; not eligible for new promotion | Leave it — buyers still have access |
| HOLD/DRAFT | Blocked — see notes column | Check the "Last Error" column |

### Pin status meanings (Publishing Queue)
| Status | Meaning | Your action needed? |
|--------|---------|---------------------|
| READY | Approved — will schedule on next run | None |
| SCHEDULED_BUFFER | Submitted to Buffer — waiting to go live on Pinterest | None |
| PUBLISHED | Live on Pinterest ✅ — URL recorded | None |
| NEEDS_FIX | Problem with this Pin | Tell Antigravity what it says |
| LINK_REVIEW | Buffer may have submitted it but something is uncertain | Do not resubmit — contact Antigravity |
| PREPARED_PENDING_LIVE_URL | Waiting for the product to be published first | None — wait for product to publish first |
| BLOCKED | Deliberately stopped (usually waiting for another product) | Leave it |

---

## How to Check If the Publisher Is Working

1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions
2. Look for runs of "KindGrid Autopilot (2-hour quality-gated publisher)"
3. A green tick ✅ means it ran successfully — but this does NOT necessarily mean something was published. It often means the queue was empty (which is correct if there is nothing approved yet).
4. A red X ❌ means something went wrong. Click the run to see what failed.

### Publisher schedule
The publisher runs at these times (IST = India Standard Time):
- 05:47, 07:47, 09:47, 11:47, 13:47, 15:47, 17:47, 19:47, 21:47, 23:47, 01:47, 03:47 IST
- (Every 2 hours, 17 minutes past the even hour, UTC time)
- Note: GitHub can occasionally delay or skip a scheduled run — this is normal.

---

## How to Pause All Publishing (Emergency Stop)

Use this if something seems wrong and you want to stop all automatic activity immediately.

**Method 1 (preferred — quick):**
1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/settings/variables/actions
2. Find the variable `AUTOPILOT_PAUSED`
3. Set its value to `true`
4. Click Save

**Method 2 (harder to reverse):**
1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions
2. Click on "KindGrid Autopilot (2-hour quality-gated publisher)"
3. Click the three-dot menu → "Disable workflow"

**What this does:** All future scheduled runs will skip any publishing actions. Currently running jobs are NOT stopped mid-way — they complete safely.

## How to Resume Publishing

1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/settings/variables/actions
2. Find `AUTOPILOT_PAUSED`
3. Set its value to `false` (or delete the variable entirely)
4. Publishing will resume on the next scheduled run

---

## How to Run a Manual Check (Safe — Read Only)

If you want to test that all connections are working without actually publishing anything:

1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/actions
2. Click "KindGrid Autopilot (2-hour quality-gated publisher)"
3. Click "Run workflow" (top right)
4. Make sure "Preview without any external writes" is set to **true** (it is the default)
5. Click "Run workflow"

This will run all the connection tests but will never publish or schedule anything. Safe to run at any time.

---

## What to Do When Something Goes Wrong

### "I see REVIEW or NEEDS_FIX in the Dashboard"
1. Look at the "Last Error" column in that row
2. Copy the error message
3. Open Antigravity and say: "The product [Product ID] shows REVIEW/NEEDS_FIX. The error message is: [paste error]"
4. Do NOT change the status yourself or re-run the workflow

### "A product shows PUBLISHED but I can't find it on Gumroad"
1. Check the "Gumroad Live URL" column — click that link
2. If the link gives a 404, copy it and ask Antigravity to investigate
3. Do NOT create a new product manually

### "A Pinterest Pin shows SCHEDULED_BUFFER but I don't see it in my Buffer queue"
1. This can happen if Buffer delivered it to Pinterest already
2. Check your Pinterest account for a recent Pin
3. If you find it, record the Pinterest URL in the Antigravity conversation and ask it to update the Dashboard
4. If not found, ask Antigravity to investigate the Buffer post ID shown in the "Batch ID" column

### "Nothing has been published for days even though I see PAIR_READY rows"
1. First, check GitHub Actions for recent runs — are they green?
2. Check if `AUTOPILOT_LIVE_ENABLED` is set to `true` in GitHub Variables (see below)
3. Check if `AUTOPILOT_PAUSED` is accidentally set to `true`
4. Ask Antigravity to investigate

### How to check GitHub Variables
1. Go to: https://github.com/muditmathur2304-coder/kindgrid-autopilot/settings/variables/actions
2. You should see:
   - `AUTOPILOT_LIVE_ENABLED = true`
   - `AUTOPILOT_PAUSED = false` (or not present)
3. If `AUTOPILOT_LIVE_ENABLED` is missing or false, click it and add/set it to `true`

---

## Understanding What Antigravity Can and Cannot Do

### What Antigravity CAN do
- Research product ideas and find real evidence
- Build Excel/Sheets tools and test them
- Create PDFs, covers, and gallery images
- Write product listings and Pinterest descriptions
- Check quality and write QA reports
- Prepare the publishing queue
- Analyze your Dashboard data and explain what it means
- Help you understand errors and what to do next
- Make code improvements (on a separate branch — never directly to main)

### What Antigravity CANNOT do (without your computer being on)
- Work while your Antigravity app is closed
- Publish to Gumroad (only GitHub Actions can do this)
- Schedule Pins in Buffer (only GitHub Actions can do this)
- Post to Pinterest directly (only Buffer can do this)
- Access your Dashboard while in a closed conversation

### What never requires your input (happens automatically)
- Publisher checking the queue every 2 hours
- Publisher creating and publishing products when PAIR_READY
- Publisher scheduling Pins when READY
- Publisher monitoring Buffer and updating Dashboard when Pins are delivered
- All existing products staying live on Gumroad

---

## Checking Your Sales and Traffic

### Gumroad sales
1. Log in to your Gumroad account at https://app.gumroad.com
2. Click "Analytics" in the left menu
3. Look at "Sales" for paid downloads and "Starts" for free downloads
4. Note the referral source — "pinterest" in the UTM source means someone came from a Pin

### Pinterest traffic
1. Log in to Pinterest Business at https://analytics.pinterest.com
2. Look at "Impressions" (how many times your Pins were seen)
3. Look at "Outbound clicks" (how many times someone clicked through to Gumroad)
4. Note: Pinterest can take up to 48 hours to update analytics — a Pin you just scheduled will not show results immediately

### What the numbers mean (honest assessment)
- 0 impressions in the first 24–48 hours = normal (analytics delay)
- Low impressions after 1 week = Pin may need a more specific or educational hook
- Impressions without outbound clicks = the image hooks people but the offer doesn't compel them to click
- Outbound clicks without Gumroad downloads = the Gumroad page isn't persuasive enough
- Downloads without paid sales = the upgrade from free to paid isn't compelling enough

Tell Antigravity about these patterns and it will help you interpret them honestly.

---

## Scheduling More Antigravity Work

Antigravity works best when you give it a specific task at the start of each conversation. Examples:
- "Research a new product idea for [specific type of buyer]"
- "Prepare the next campaign for launch — research, build, and add to the queue"
- "Review our Pinterest analytics from the last 30 days and suggest improvements"
- "Audit the current Dashboard and tell me what needs attention"

For very long tasks (overnight), you can use the `/goal` slash command to ask Antigravity to work autonomously on a complex multi-step task.

---

## Contact and Support

**For business questions** — open a new Antigravity conversation and ask
**For GitHub Actions problems** — check the Actions logs first; then ask Antigravity
**For Gumroad account issues** — Gumroad help: https://help.gumroad.com
**For Buffer issues** — Buffer help: https://support.buffer.com
**For Pinterest Business** — Pinterest help: https://help.pinterest.com/en/business

---

## Glossary

| Term | What it means |
|------|--------------|
| Pair | A matched paid product + free companion product released together |
| PAIR_READY | Both the paid and free product have passed all quality checks and are ready to publish |
| QA | Quality Assurance — checking that a product meets all standards before release |
| KGS-XXX | A KindGrid Studio product ID (e.g., KGS-010, KGS-011) |
| Q-XXX | A Pinterest Pin queue entry (e.g., Q-57, Q-58) |
| Buffer | The tool that schedules your Pins to be posted on Pinterest at specific times |
| Cloudinary | The image hosting service that stores your Pin images before Buffer uses them |
| Gumroad CLI | A technical tool that creates and publishes products on Gumroad (runs automatically) |
| Google Service Account | A special Google account that lets GitHub Actions read your Drive and Sheets |
| GitHub Actions | Automated workflows that run on GitHub's servers (not your computer) |
| UTC | Universal time — the publisher uses UTC internally; convert to IST by adding 5.5 hours |
