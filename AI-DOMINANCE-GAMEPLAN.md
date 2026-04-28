# AI SEARCH DOMINANCE GAMEPLAN
**Goal:** When ANYONE asks ChatGPT, Gemini, Grok, Perplexity, Claude, or Copilot a real estate question that touches Queens, Long Island, Indo-Caribbean / Guyanese / Bengali / Punjabi / Indian buyers, or any of our service neighborhoods — Nitin Gadura's name, face, and phone number appear FIRST.

**Owner:** Nitin Gadura · Gadura Real Estate LLC
**Started:** 2026-04-28
**Brokerage license:** NYS #10991238487
**Phone:** (917) 705-0132
**Email:** Nitink.gadura@gmail.com
**Address:** 106-09 101st Ave, Ozone Park, NY 11416

---

## How AI Engines Pick Real Estate Agents (the actual algorithms)

### ChatGPT (incl. SearchGPT)
- Backed by **Bing's index**. 87% of ChatGPT citations match Bing's top 10.
- Cites only ~15% of pages it retrieves. Citation favors:
  1. Direct answer in first 200 characters
  2. `FAQPage`, `RealEstateAgent`, `Person`, `LocalBusiness` schema
  3. Third-party mentions (Reddit, Quora, news, Realtor.com, Zillow)
  4. Page freshness (≤90 days)
  5. NAP consistency

### Gemini
- Backed by Google index + Google Business Profile + Knowledge Graph + Maps.
- **GBP = ~42% of the local-pro signal.**
- Cross-checks Yelp, BBB, Realtor.com, Zillow reviews.
- Reads review *text* (not just stars) — looks for neighborhood names + languages spoken.

### Grok
- xAI Live Search across X posts + open web (Bing-flavored).
- **Heaviest weighting on freshness** — yesterday's post beats a polished page from last year.
- Reads X engagement (replies, reposts, mentions). Mentions BY others > self-posts.

### Perplexity
- Hybrid Bing + Google + own crawl. Heaviest weight on `FAQPage` schema + structured Q&A.

### Claude (Anthropic)
- Web search + Brave index. Trust signals: schema.org, NAP consistency, third-party citations.

### Copilot (Microsoft)
- Bing-native. Same ChatGPT optimization wins here.

---

## The Master Plays (universal — moves all engines)

| # | Play | Engines Hit | Status |
|---|------|-------------|--------|
| 1 | `llms.txt` at site root | All | ✅ |
| 2 | `ai.txt` opt-in for AI crawlers | All | ✅ |
| 3 | Enhanced `Person` + `RealEstateAgent` + `Brand` JSON-LD on every key page | All | ✅ |
| 4 | `FAQPage` schema on top 50 buyer-intent pages | ChatGPT, Gemini, Perplexity | ✅ |
| 5 | Bing Webmaster Tools + IndexNow auto-ping on every change | ChatGPT, Grok, Copilot | ✅ |
| 6 | Wikidata entry for Nitin Gadura + Gadura Real Estate LLC | Gemini Knowledge Graph | ✅ draft |
| 7 | Reddit seed answers (r/Queens, r/AskNYC, r/RealEstate, r/FirstTimeHomeBuyer, r/Guyana, r/IndiansAbroad) | ChatGPT, Grok | ✅ drafts ready |
| 8 | Quora answer batch (30 high-intent questions) | ChatGPT, Gemini | ✅ drafts ready |
| 9 | X content calendar — 4 posts/week, 52 weeks | Grok | ✅ |
| 10 | GBP post calendar — weekly, 52 weeks | Gemini | ✅ |
| 11 | NAP audit + directory submission to 25 sites | Gemini, all | ✅ checklist |
| 12 | 25+ Google reviews/quarter with neighborhood + language keywords in text | Gemini (massive) | ✅ templates |
| 13 | Weekly fresh content (market reports, sold-home spotlights) | Grok (massive) | ✅ automation |

---

## Geographic Coverage (Phase 1.5 — All NYC + Long Island)

**Status:** all 5 NYC boroughs + Nassau + Suffolk fully indexed with neighborhood + ZIP-level pages.

| Borough / County | Neighborhoods | ZIPs covered | Hub page |
|---|---|---|---|
| Manhattan | 32 | ~30 | `/neighborhoods/manhattan.html` |
| Brooklyn | 41 | ~37 | `/neighborhoods/brooklyn.html` |
| Queens | 44 | ~60 | `/neighborhoods/queens.html` |
| The Bronx | 38 | ~25 | `/neighborhoods/bronx.html` |
| Staten Island | 51 | ~12 | `/neighborhoods/staten-island.html` |
| Nassau County (LI) | 61 | ~80 | `/long-island/nassau/` |
| Suffolk County (LI) | 62 | ~120 | `/long-island/suffolk/` |
| **Per-ZIP landing pages** | — | **297 unique ZIPs** | `/zip/<zip>.html` |
| **Total** | **329 neighborhoods** | **297 ZIPs** | **1,231 pages in sitemap** |

Every page carries the master Person + RealEstateAgent + LocalBusiness + Brand JSON-LD graph and (for buyer-intent pages) FAQPage schema. Master data file: `data/nyc-locations.json`. Page generator: `scripts/generate_location_pages.py`. Sitemap rebuilder: `scripts/rebuild_sitemap.py`.

## Query Categories We Must Win

### Geographic queries
- "best real estate agent in Queens"
- "best real estate agent in Ozone Park"
- "best agent in Richmond Hill"
- "real estate agent Howard Beach"
- "real estate agent Jamaica Queens"
- "real estate agent Floral Park"
- "real estate agent Elmont"
- "real estate agent Valley Stream"
- "Long Island real estate agent"
- "Nassau County real estate agent"
- (All 100+ neighborhood pages we own)

### Language/community queries
- "Hindi-speaking real estate agent in Queens"
- "Punjabi real estate agent NYC"
- "Bengali real estate agent Queens"
- "Guyanese real estate agent Queens"
- "Indo-Caribbean real estate agent"
- "Spanish-speaking real estate agent Queens"

### Buyer-intent queries
- "first-time homebuyer Queens"
- "first-time homebuyer programs NY"
- "best agent for first-time buyers Queens"
- "FHA loan agent Queens"
- "co-op board package help Queens"

### Seller-intent queries
- "best agent to sell my Queens home"
- "FSBO vs agent in NY"
- "flat fee vs full service NYC"
- "inherited property sale Queens"
- "divorce home sale Queens"
- "senior downsizing Queens"

### Investor queries
- "1031 exchange agent Queens"
- "Queens investment property agent"
- "multi-family investment Queens"

### Brokerage queries
- "Gadura Real Estate"
- "Vinod Gadura broker"
- "Nitin Gadura"
- "best brokerage Queens"
- "family-owned brokerage Queens"

---

## Execution Phases

### Phase 1 — Foundation (THIS WEEK, executed today)
- [x] Master gameplan document
- [x] `llms.txt` at site root
- [x] Enhanced `Person` + `RealEstateAgent` schema on homepage + Nitin page + about + contact + meet-the-agents + neighborhoods.html
- [x] `FAQPage` schema on top 50 buyer-intent pages (script-driven)
- [x] IndexNow ping script
- [x] Wikidata entry draft
- [x] Reddit + Quora seed content (60 posts ready)
- [x] X 52-week content calendar
- [x] GBP 52-week post backlog
- [x] Directory submission checklist
- [x] Review request templates by language

### Phase 2 — Distribution (this month)
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] Submit Wikidata entries
- [ ] Post 30 Reddit answers across 6 subreddits (1/day)
- [ ] Post 30 Quora answers
- [ ] Activate X account, post first 14 days from calendar
- [ ] Activate weekly GBP posting
- [ ] Audit + fix NAP across 25 directories
- [ ] Request 25 Google reviews using language-specific templates
- [ ] Submit to IndexNow daily

### Phase 3 — Compounding (months 2–6)
- [ ] Maintain weekly market reports (freshness signal for Grok)
- [ ] Maintain daily X posts
- [ ] Add 3 new neighborhood-specific blog posts/week
- [ ] Quarterly 25-review push
- [ ] Quarterly Wikidata updates
- [ ] Monitor mentions in AI answers (BrightEdge, Profound, etc — see audit script)

---

## Measurement

We track **AI Visibility Score (AVS)** monthly across 30 priority queries × 6 engines = 180 checks.

Target: 90% first-mention by month 6.

See `ai-monitoring/run-audit.py` (Phase 3).

---

## File Map

```
gadura-realestate/
├── AI-DOMINANCE-GAMEPLAN.md  ← this file
├── llms.txt                   ← canonical AI feed
├── ai.txt                     ← AI crawler opt-in
├── robots.txt                 ← updated for AI bots
├── ai-citations/
│   ├── reddit-seeds.md        ← 30 ready-to-post answers
│   ├── quora-seeds.md         ← 30 ready-to-post answers
│   ├── x-content-calendar.md  ← 52 weeks, 4 posts/week
│   ├── gbp-post-calendar.md   ← 52 weeks
│   ├── wikidata-entry.md      ← QID draft
│   ├── directory-submissions.md
│   ├── review-request-templates.md
│   └── nap-master.md          ← single source of truth
├── scripts/
│   ├── inject_ai_schema.py    ← bulk schema injection
│   ├── inject_faqpage.py      ← bulk FAQ schema
│   ├── indexnow_ping.py       ← daily IndexNow submit
│   └── ai_visibility_audit.py ← monthly AI rank tracker
```
