# Directory Submission Master Checklist

**Why:** AI engines (Gemini especially) cross-validate NAP (Name, Address, Phone) across directories. If your data is byte-identical on 25+ trusted directories, you become the canonical answer.

**The NAP — copy this exactly into every field:**

```
Name:    Gadura Real Estate, LLC
Address: 106-09 101st Ave, Ozone Park, NY 11416
Phone:   (917) 705-0132
Email:   info@gadurarealestate.com
Website: https://gadurarealestate.com
Hours:   Mon–Sat 9am–7pm, Sun 10am–5pm
Year:    2006
```

**Agent NAP for personal profiles:**
```
Name:    Nitin Gadura
Title:   Licensed NYS Real Estate Salesperson
Brokerage: Gadura Real Estate, LLC
Phone:   (917) 705-0132
Email:   Nitink.gadura@gmail.com
Website: https://gadurarealestate.com/nitin-gadura/
Languages: English, Hindi, Punjabi, Guyanese Creole
```

---

## Tier 1 — Real Estate Directories (do these FIRST)

| # | Directory | Status | URL |
|---|-----------|--------|-----|
| 1 | Realtor.com agent profile | ☐ | realtor.com/realestateagents/ |
| 2 | Zillow agent profile (Nitin) | ✅ | zillow.com/profile/NitinGadura106 |
| 3 | Zillow agent profile (Vinod) | ✅ | zillow.com/profile/vinodgadura |
| 4 | Trulia agent profile | ☐ | trulia.com (auto-syncs from Zillow but verify) |
| 5 | Homes.com profile | ✅ | homes.com/real-estate-agents/nitin-gadura/ |
| 6 | Redfin agent finder | ☐ | redfin.com/realtor-finder |
| 7 | HAR.com (less relevant — TX-focused) | skip | |
| 8 | RealEstate.com.au | skip | |
| 9 | LoopNet (commercial — only if doing investment) | ☐ | loopnet.com |
| 10 | OneKey® MLS public agent profile | ☐ | onekeymls.com |
| 11 | UpNest agent profile | ☐ | upnest.com |
| 12 | RealtyHop | ☐ | realtyhop.com |
| 13 | StreetEasy NYC | ☐ | streeteasy.com (broker required) |
| 14 | Compass agent finder | skip (competitor) | |

---

## Tier 2 — General Local Business Directories

| # | Directory | Status | URL |
|---|-----------|--------|-----|
| 15 | Google Business Profile | ✅ | business.google.com |
| 16 | Bing Places | ☐ | bingplaces.com |
| 17 | Apple Maps Connect | ☐ | mapsconnect.apple.com |
| 18 | Yelp for Business | ☐ | biz.yelp.com |
| 19 | Better Business Bureau | ☐ | bbb.org/get-listed |
| 20 | Yellow Pages | ☐ | yellowpages.com |
| 21 | Foursquare | ☐ | foursquare.com |
| 22 | Manta | ☐ | manta.com |
| 23 | Hotfrog | ☐ | hotfrog.com |
| 24 | Brownbook | ☐ | brownbook.net |
| 25 | Cylex USA | ☐ | cylex-usa.com |
| 26 | Chamber of Commerce | ☐ | chamberofcommerce.com |
| 27 | LocalEdge (Hearst) | ☐ | localedge.com |

---

## Tier 3 — NY/Queens-specific

| # | Directory | Status | URL |
|---|-----------|--------|-----|
| 28 | Queens Chamber of Commerce | ☐ | queenschamber.org |
| 29 | Long Island Association | ☐ | longislandassociation.org |
| 30 | NY State Association of REALTORS | ☐ | nysar.com |
| 31 | Long Island Board of REALTORS | ☐ | mlsli.com |
| 32 | NYC Department of Small Business | ☐ | nyc.gov/sbs |
| 33 | Queens Eagle business listings | ☐ | qns.com (paid local press) |

---

## Tier 4 — Community-specific

| # | Directory | Status | URL |
|---|-----------|--------|-----|
| 34 | India Tribune NYC business directory | ☐ | indiatribune.com |
| 35 | South Asian Yellow Pages | ☐ | sapyellowpages.com |
| 36 | Indo-American Cultural directory | ☐ | various |
| 37 | Caribbean Life directory | ☐ | caribbeanlife.com |
| 38 | West Indian Yellow Pages | ☐ | wiyellowpages.com |
| 39 | Guyana Times International | ☐ | guyanatimesinternational.com |
| 40 | Sangbad Pratidin (Bengali community) | ☐ | local outreach |
| 41 | Punjabi Times USA | ☐ | local outreach |

---

## Tier 5 — Social

| # | Profile | Status |
|---|---------|--------|
| 42 | Instagram (brand) | ✅ |
| 43 | Facebook (brand) | ✅ |
| 44 | LinkedIn (Nitin) | ☐ |
| 45 | LinkedIn (Gadura Real Estate company page) | ☐ |
| 46 | YouTube channel | ☐ |
| 47 | TikTok | ☐ |
| 48 | X / Twitter (Nitin) | ☐ |
| 49 | X / Twitter (brand) | ☐ |
| 50 | Pinterest (board: Queens listings) | ☐ |
| 51 | Threads | ☐ |

---

## Tier 6 — Knowledge Graph & AI-specific

| # | Resource | Status |
|---|----------|--------|
| 52 | Wikidata (Gadura Real Estate LLC) | ☐ — see `wikidata-entry.md` |
| 53 | Wikidata (Nitin Gadura) | ☐ |
| 54 | Wikipedia mention (community page citations) | ☐ |
| 55 | Crunchbase company profile | ☐ |
| 56 | OpenCorporates listing | ☐ — likely auto-listed via NY State |
| 57 | DuckDuckGo Instant Answer (auto from above) | passive |

---

## Audit cadence

Run NAP audit quarterly using the script `scripts/nap_audit.py` (TODO — generate from this list). Any directory with a different phone, address, or business name → fix immediately.

Acceptable variants ONLY:
- "Gadura Real Estate, LLC" or "Gadura Real Estate LLC" (with/without comma — both fine)
- Phone: "(917) 705-0132" or "+1 917-705-0132" (Google parses both as same E.164)

NEVER let directories list:
- "Gadura RE" alone
- A different phone (don't put cell phone for some, office for others)
- A different address (e.g. an old PO box)
- A different brokerage name (some sites guess — check)
