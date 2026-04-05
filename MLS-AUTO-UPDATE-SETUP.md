# MLS Auto-Update Setup Guide
## Gadura Real Estate — Automated Listings from OneKey® MLS

This site is wired to automatically pull live listings from OneKey® MLS every day at 7 AM — the same data source as KW.com.

---

## How It Works

```
OneKey® MLS  →  MLS GRID RESO API  →  GitHub Actions (daily cron)  →  listings.json  →  Website
               (same source KW uses)    runs every morning
```

1. MLS GRID is OneKey® MLS's official RESO API provider (confirmed 2023)
2. GitHub Actions fetches all active listings in Queens, Brooklyn & Long Island every morning
3. The updated `listings.json` is committed back to the repo
4. GitHub Pages automatically redeploys with fresh listings

---

## Setup (one-time, ~30 minutes)

### Step 1 — Apply for MLS GRID Access

1. Go to **https://mlsgrid.com** → click "Get Access"
2. You'll need:
   - Your OneKey® MLS Member ID
   - Your broker's information
   - Gadura Real Estate LLC license number
3. Select **OneKey® MLS** as your data provider
4. Choose the **IDX** data access level (for public display)
5. Submit — approval typically takes 1–3 business days

**Cost:** MLS GRID pricing is set by your MLS — contact OneKey® at
memberservices@onekeymls.com or (631) 661-4800 to confirm current IDX data fees.

### Step 2 — Get Your API Token

Once approved:
1. Log into your MLS GRID account at https://mlsgrid.com
2. Go to **API Tokens** → **Create Token**
3. Copy the Bearer token (keep this private — treat like a password)

### Step 3 — Add the Token to GitHub

1. Go to your repo: **https://github.com/ngaduraaa-creator/gadura-realestate**
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `MLSGRID_TOKEN`
5. Value: (paste your MLS GRID Bearer token)
6. Click **Add secret**

### Step 4 — Test It

1. Go to **Actions** tab in your GitHub repo
2. Click **"Auto-Update MLS Listings"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs — should show hundreds of listings being fetched
5. Check `data/listings.json` in the repo to confirm it updated

---

## After Setup: What Updates Automatically

Every morning at 7 AM, the site will refresh:

| Category | Area | What's Included |
|---|---|---|
| `woodhavenListings` | Ozone Park, Woodhaven, Richmond Hill, South Ozone Park | ~50–80 active listings |
| `queensListings` | All other Queens neighborhoods | ~200–400 active listings |
| `brooklynListings` | East NY, Flatbush, Canarsie, Crown Heights, Cypress Hills & more | ~200–300 listings |
| `longIslandListings` | Elmont, Valley Stream, Hempstead, Freeport, Baldwin & more | ~100–200 listings |

**What's preserved** (never overwritten by the bot):
- `activeListings` — Your own active listings (manually managed)
- `soldListings` — Your sold history
- `areaListings` — Manually curated showcase properties

---

## MLS GRID API Details (for reference)

| Detail | Value |
|---|---|
| Base URL | `https://api.mlsgrid.com/v2/Property` |
| Auth | Bearer token in `Authorization` header |
| MLS ID | `onekey2` (OneKey® MLS identifier in MLS GRID) |
| Protocol | OData / RESO Web API |
| Data | Active listings, price, beds, baths, sqft, address, description, coordinates |
| Update frequency | Real-time (we fetch daily) |

Script location: `scripts/fetch-mls-grid.js`

---

## Frequently Asked Questions

**Q: What if I don't have MLS GRID yet?**
A: The site still works — it uses the listings already in `listings.json`. The workflow falls back to the agent profile sync. You can still manually add listings.

**Q: Will this show other agents' listings on my site?**
A: Yes — that's how IDX works. All participating brokerages' listings show on your site with proper attribution ("Courtesy of [Brokerage Name]"). This is required by MLS rules and is what KW.com does too.

**Q: What about photos?**
A: MLS GRID can provide photos via the `$expand=Media` parameter. Once your token is set up and working, we can enable full photo sync.

**Q: Can I filter out certain properties?**
A: Yes — edit `scripts/fetch-mls-grid.js` to adjust `MIN_PRICE`, `MAX_PRICE`, city lists, or add additional OData filters.

---

## Support

- OneKey® MLS: memberservices@onekeymls.com | (631) 661-4800
- MLS GRID support: https://mlsgrid.com/contact
- Script issues: check GitHub Actions logs under the Actions tab
