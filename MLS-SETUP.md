# MLS Live Listings Setup — Gadura Real Estate

## Overview

The website is wired to automatically display real, live MLS listings from
**OneKey® MLS**. Once you complete the steps below, listings will update
**every 4 hours automatically** — any time you or your agents list or close
a property, it will appear on gadurarealestate.com within 4 hours.

**Why not Zillow or homes.com?**
- Zillow does not allow third parties to display their data (their ToS prohibits it)
- CoStar (homes.com) actively sues real estate sites that hotlink their images
- The only legal, compliant way to display MLS data is through the **official IDX program**
- OneKey® MLS is YOUR MLS — you're entitled to this data as a member

---

## Step 1: Request RESO API Credentials from OneKey® MLS

### Option A — Matrix IDX (Easiest — takes 1-2 days to approve)

1. Log into **https://www.mlsmatrix.com**
2. Go to **My Matrix → My Account**
3. Look for **"IDX / RESO API"** or **"Data Share"**
4. Request IDX data access
5. They will email you an API URL, client ID, and client secret

**OR call/email OneKey® MLS directly:**
- Phone: **(631) 661-4800**
- Email: **memberservices@onekeymls.com**
- Say: *"I need RESO Web API credentials for my IDX website"*

### Option B — MLS Grid (If OneKey uses this vendor)

Many MLSs use **MLS Grid** as their API vendor.
1. Go to **https://mlsgrid.com**
2. Click "Sign In with MLS"
3. Select "OneKey® MLS"
4. Log in with your Matrix credentials
5. You'll get a bearer token immediately

### Option C — Bridge Interactive (Free, Zillow Group's IDX platform)
1. Go to **https://bridgeinteractive.com**
2. Create a free account
3. Connect your OneKey® MLS credentials
4. Get API access token

---

## Step 2: Add Credentials to GitHub Secrets

1. Go to: **https://github.com/ngaduraaa-creator/gadura-realestate/settings/secrets/actions**
2. Click **"New repository secret"** for each of the following:

| Secret Name | Value | Where to find it |
|-------------|-------|------------------|
| `RESO_BASE_URL` | Your API base URL | From MLS/IDX provider |
| `RESO_ACCESS_TOKEN` | Your bearer token | From MLS/IDX provider |
| `RESO_CLIENT_ID` | OAuth client ID | From MLS/IDX provider (if OAuth) |
| `RESO_CLIENT_SECRET` | OAuth secret | From MLS/IDX provider (if OAuth) |
| `RESO_TOKEN_URL` | OAuth token URL | From MLS/IDX provider (if OAuth) |
| `AGENT_ID_NITIN` | Nitin's MLS member ID | Your Matrix profile → My Account |
| `AGENT_ID_VINOD` | Vinod's MLS member ID | Vinod's Matrix profile |
| `AGENT_ID_GAURAV` | Gaurav's MLS member ID | Gaurav's Matrix profile |

> **Finding your MLS member ID:** Log into Matrix → My Matrix → My Account →
> look for "Member ID" or "Agent ID" — it's usually a number like "12345"

---

## Step 3: Test the Connection

1. Go to: **https://github.com/ngaduraaa-creator/gadura-realestate/actions**
2. Click **"Sync Listings — OneKey® MLS RESO API"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs — should say "✅ Wrote X active + Y sold listings"
5. Check **data/listings.json** — it will have real property addresses!

---

## What Happens After Setup

```
Every 4 hours:
  GitHub Actions → calls OneKey® MLS API → updates data/listings.json
  → commits to repo → GitHub Pages deploys in ~30 seconds
  → gadurarealestate.com shows real listings automatically
```

**Your listings appear on the website within 4 hours of going live on MLS.**

---

## Immediate Option (While Waiting for API Credentials)

You can manually export listings from Matrix right now:

1. Log into **https://www.mlsmatrix.com**
2. Search for active listings in your zip codes (11416, 11417, 11418, 11419, etc.)
3. Select All → **Export → Spreadsheet (CSV)**
4. Save as: `data/mls-export.csv`
5. Run: `node scripts/import-mls-csv.js`
6. Commit and push: `git add data/listings.json && git commit -m "listings: import from MLS" && git push`

Your listings will be live on the website within minutes.

---

## OneKey® MLS Attribution Requirements

The website already includes all required attribution on every listing:

- "© OneKey® MLS"
- "All information deemed reliable but not guaranteed"
- "IDX information is provided exclusively for consumers' personal, non-commercial use"
- Equal Housing Opportunity logo in footer

These are required by your IDX agreement. Do not remove them.

---

## Contacts

| Service | Contact |
|---------|---------|
| OneKey® MLS Member Services | (631) 661-4800 |
| OneKey® MLS Email | memberservices@onekeymls.com |
| MLS Grid (API vendor) | support@mlsgrid.com |
| Bridge Interactive | support@bridgeinteractive.com |
