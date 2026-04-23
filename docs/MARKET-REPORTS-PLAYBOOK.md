# Monthly Market Reports — Full Playbook

This is the operational manual for the per-ZIP monthly market report system. Three sections: automation status, Mailchimp setup walkthrough, and the 5-minute monthly update workflow.

---

## Part 1 — Automation Status (what's live right now)

### ✅ GitHub Action wired up

File: `.github/workflows/monthly-market-reports.yml`

**What it does:**
- Runs automatically on the 1st of every month at 05:00 UTC
- Regenerates all 18 market report HTML files from `scripts/generate-market-reports.py`
- Re-injects the master legal compliance footer into each regenerated file
- Bumps `<lastmod>` timestamps in `sitemap.xml` for every `/market-reports/*` URL
- Auto-commits and pushes the changes as `gadura-market-reports-bot`

**Manual trigger option:**
- Go to GitHub → Actions → "Monthly Market Reports Regeneration"
- Click "Run workflow"
- Useful for off-cycle refreshes

**How to verify it's running:**
- GitHub repo → Actions tab → you'll see a run entry on the 1st of each month
- Green checkmark = success; red X = failure (email notification will fire)

**Next scheduled run:** First day of next month, 05:00 UTC.

---

## Part 2 — Mailchimp Setup (email distribution)

The subscribe form at `/market-reports/subscribe.html` currently falls back to a `mailto:` link if Formspree isn't configured. To send emails at scale, wire it up with Mailchimp's free plan (500 subscribers / 1,000 emails per month free).

### Step-by-step Mailchimp setup

**Step 1 — Create a free Mailchimp account**
- Go to mailchimp.com → Sign up
- Use `Nitink.gadura@gmail.com` or a dedicated `marketing@gadurarealestate.com` if you have it
- Verify the email

**Step 2 — Create an audience**
- In Mailchimp dashboard → **Audience → Audiences → Create Audience**
- Name: `Gadura Market Report Subscribers`
- Default from name: `Nitin Gadura`
- Default from email: your verified email
- Company: `Gadura Real Estate, LLC`
- Address: `106-09 101st Ave, Ozone Park, NY 11416` *(CAN-SPAM requires a real address in every email)*
- Click **Save**

**Step 3 — Add custom audience fields for ZIPs**
- Audience → Settings → Audience fields and *|MERGE|* tags → **Add a field**
- Add a multi-select or tag-style field called `ZIPS` so you can target emails by ZIP
- Add other fields as useful: `ROLE` (buyer/seller/owner/investor), `PHONE`

**Step 4 — Generate the embedded signup form**
- Audience → Signup Forms → **Embedded forms**
- Pick the "Classic" style
- Copy the generated `<form action="https://...list-manage.com/subscribe/post?u=XXXX&id=YYYY">` code

**Step 5 — Tell me when you have the Mailchimp embed code**
- Paste the Mailchimp `<form action="...">` URL to me
- I'll swap the `action="https://formspree.io/f/YOUR_FORM_ID"` in `subscribe.html` with your real Mailchimp URL
- I'll also map the existing form field names (`name`, `email`, `phone`, `zips`, `role`) to Mailchimp's expected merge-tag field names (usually `FNAME`, `EMAIL`, `PHONE`, `ZIPS`, `ROLE`)

**Step 6 — Send the first monthly email**
- On the 1st of each month, after the GitHub Action regenerates the reports
- In Mailchimp → Campaigns → **Create Campaign → Regular email**
- Subject: `Your [ZIP] market report for [Month]`
- From: Nitin Gadura · `Nitink.gadura@gmail.com`
- Audience: Market Report Subscribers, segmented by ZIP tag
- Template: I can generate a Mailchimp-compatible HTML email template that pulls the relevant report into the body. Ask me when you're ready.
- Preview, test-send to yourself, click Send

### Alternative email services if you don't want Mailchimp

| Service | Free tier | Best for |
|---|---|---|
| **Mailchimp** | 500 subs, 1,000 sends/mo | General small-business use — easiest UI |
| **ConvertKit** | 1,000 subs, unlimited sends | Creator-focused — great segmentation |
| **SendGrid** | 100 emails/day | Developer-focused — use with API |
| **Constant Contact** | 60-day trial, then paid | Non-technical users, best templates |
| **Substack** | Free for email newsletters | Content-first approach, public archive |

My recommendation: **Mailchimp** for the 500-subscriber free ceiling and simplest form integration.

### Compliance reminders for any service you pick

- Every email must include a **one-click unsubscribe link** (CAN-SPAM mandatory)
- Every email must include your **physical mailing address** — `106-09 101st Ave, Ozone Park, NY 11416`
- You may only email people who **opted in** (the subscribe form's consent checkbox)
- Never buy lists — violates CAN-SPAM and NY GBL §399-p
- Honor unsubscribe requests within 10 business days

---

## Part 3 — The 5-Minute Monthly Update Workflow

This is how you refresh the real numbers each month.

### Step 1 — Open the data file

In your editor, open: `scripts/generate-market-reports.py`

Find the `REPORT_DATA = [` list near the top. Each entry looks like:

```python
{
    "zip": "11414", "slug": "howard-beach",
    "name": "Howard Beach", "county": "Queens",
    "median": "$875,000", "dom": "42 days", "supply": "1.9 months", "ratio": "97.4%",
    ...
}
```

### Step 2 — Pull last month's numbers from OneKey® MLS

For each ZIP:
1. Log into OneKey® MLS (or IDX Broker if you've enabled Market Stats)
2. Filter: status = Sold, date range = prior calendar month, ZIP = XXXXX
3. Note the four numbers:
   - **median** — median sale price
   - **dom** — average days on market
   - **supply** — months of supply (active count ÷ monthly pace)
   - **ratio** — sale-to-list ratio (sale price ÷ last list price × 100)
4. Update the four values in the Python dict for that ZIP

**Time budget:** ~15 seconds per ZIP × 18 ZIPs = roughly 5 minutes total.

### Step 3 — Don't touch "reasons to buy"

The `reasons` and `caveats` arrays stay the same month-over-month unless something genuinely changes about the neighborhood (new transit line opens, major development, etc.). Leave them alone for routine updates.

### Step 4 — Commit the data change

```bash
cd ~/Jagex/gadura-realestate
git add scripts/generate-market-reports.py
git commit -m "data: refresh market report numbers for [MONTH] [YEAR]"
git push
```

### Step 5 — Regeneration happens automatically

The GitHub Action will fire on the 1st and regenerate all 18 HTML files from the new data. You don't need to run the Python script locally. If you want to verify before the cron fires, run:

```bash
python3 scripts/generate-market-reports.py
git add market-reports/
git commit -m "chore: regenerate reports with [MONTH] data"
git push
```

### Step 6 — Send the Mailchimp campaign

After the reports refresh on the 1st:
1. Log into Mailchimp
2. Duplicate last month's campaign
3. Update the subject line (e.g., "Your Howard Beach market report for May 2026")
4. Update the email body with the new numbers (or use merge tags)
5. Send to the audience, segmented by ZIP

---

## Monthly workflow at a glance

| When | What | Time |
|---|---|---|
| Last day of month | Pull sold data from MLS, update Python dict, commit | 5 min |
| 1st of month, 05:00 UTC | GitHub Action auto-regenerates pages | 0 min (automated) |
| 1st of month, morning | Log into Mailchimp, send monthly campaign | 5–10 min |

**Total monthly overhead: 10–15 minutes.**

---

## Troubleshooting

**GitHub Action failed**
- Go to Actions tab → click the failed run → read the error
- Most common: Python syntax error in your data edit. Run the script locally first: `python3 scripts/generate-market-reports.py`
- If stuck, ping me with the error message

**Mailchimp form not collecting leads**
- Test in incognito window
- Check Mailchimp audience → recent signups
- Verify the form action URL matches your Mailchimp audience's embed URL

**Reports show wrong month**
- The `MONTH` variable in the Python script uses `datetime.date.today()` — so the month reflects when the script was run
- GitHub Action runs on the 1st so the month header shows the correct current month
- Manual runs mid-month will label reports with the current month, which is fine

**Stats feel stale**
- That's because you haven't updated the Python dict yet this month
- Follow the Part 3 workflow above — 5 minutes

---

## When to upgrade to IDX Broker Engage plan

If the manual monthly data pull becomes a burden (e.g., you're serving 50+ ZIPs), upgrade to IDX Broker's **Engage** tier. Their Market Report widget auto-pulls MLS data, auto-updates monthly, and requires zero manual work. Current tier lacks it.

Roughly $200–$300/month premium over your current tier, depending on promotion. Worth it at scale; overkill at 18 ZIPs with 5 min/month manual work.

---

## Next things I can wire up when you're ready

- Mailchimp embed form integration (send me the action URL, I'll swap it in)
- Mailchimp email template HTML (Nitin-branded, matches site footer)
- Additional ZIPs beyond the current 18
- Quarterly summary email that aggregates all ZIPs into one long-form email
- Seasonal "reasons to buy" variations (spring / summer / fall / winter emphasis)

---

*Last updated: 2026-04-23. Gadura Real Estate, LLC.*
