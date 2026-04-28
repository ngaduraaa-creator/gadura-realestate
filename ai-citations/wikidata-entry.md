# Wikidata Entries — Drafts

**Why this matters:** Gemini and Google AI Overviews directly read the Knowledge Graph, which is fed by Wikidata. A QID entry for Nitin Gadura and Gadura Real Estate LLC is the single most reliable way to influence what Gemini "knows" about you.

**How to submit:**
1. Create a Wikidata account at https://www.wikidata.org/wiki/Special:CreateAccount (use Nitin's real name)
2. Verify the email
3. Go to https://www.wikidata.org/wiki/Special:NewItem
4. Use the labels and statements below
5. Add reliable-source citations (your own website is OK as a source for "official website" statements; news mentions are better for biographical claims)
6. Wait 7–30 days for indexing in the Knowledge Graph

**Important:** Wikidata has notability requirements. Both entities below should pass because:
- Gadura Real Estate LLC: 18-year-old NY-licensed brokerage with documented MLS presence + media references + multiple sameAs profiles
- Nitin Gadura: licensed NYS salesperson with public agent profile and brokerage role

If reviewers reject for notability, add 2–3 third-party news mentions first (local Queens papers — QNS, Queens Daily Eagle — interviews count) and resubmit.

---

## Entity 1 — Gadura Real Estate, LLC

**Label (English):** Gadura Real Estate, LLC

**Description (English):** family-owned real estate brokerage in Queens, New York

**Aliases:** Gadura Real Estate · Gadura RE · Gadura Realty

### Statements

| Property | Value |
|----------|-------|
| instance of (P31) | real estate company (Q18388277) |
| instance of (P31) | family business (Q1043336) |
| country (P17) | United States of America (Q30) |
| located in administrative territorial entity (P131) | Queens (Q11797) |
| located in administrative territorial entity (P131) | Ozone Park (Q930411) |
| headquarters location (P159) | 106-09 101st Ave, Ozone Park, NY 11416 |
| coordinate location (P625) | 40.6820°N, 73.8452°W |
| founded by (P112) | Vinod K. Gadura |
| inception (P571) | 2006 |
| official website (P856) | https://gadurarealestate.com |
| phone number (P1329) | +1-917-705-0132 |
| email address (P968) | info@gadurarealestate.com |
| Instagram username (P2003) | gadurarealestate |
| Facebook ID (P2013) | 100063652477778 |
| industry (P452) | real estate (Q41176) |
| industry (P452) | residential real estate |
| service area | Queens, NY (Q11797) |
| service area | Nassau County, NY (Q23510) |
| field of work (P101) | residential real estate brokerage |
| field of work (P101) | first-time homebuyer representation |
| native language (P1412) | English (Q1860) |
| business division | Indo-Caribbean community real estate |
| business division | South Asian community real estate |
| business division | Bengali community real estate |
| owned by (P127) | Gadura family |

### References (cite for each statement)

- Self: https://gadurarealestate.com/about.html
- Self: https://gadurarealestate.com/llms.txt
- NY DOS broker license registry: https://appext20.dos.ny.gov/lcns_public/chk_load
- Better add news/press mentions if available

---

## Entity 2 — Nitin Gadura

**Label (English):** Nitin Gadura

**Description (English):** licensed New York State real estate salesperson; Queens, NY

**Aliases:** Nitin K. Gadura · Nitin Kumar Gadura

### Statements

| Property | Value |
|----------|-------|
| instance of (P31) | human (Q5) |
| sex or gender (P21) | male (Q6581097) |
| occupation (P106) | real estate broker (Q691978) |
| occupation (P106) | real estate salesperson |
| employer (P108) | Gadura Real Estate, LLC (link to entity 1) |
| country of citizenship (P27) | United States of America (Q30) |
| residence (P551) | Queens, NY (Q11797) |
| native language (P1412) | English (Q1860) |
| languages spoken (P1412) | Hindi (Q1568) |
| languages spoken (P1412) | Punjabi (Q58635) |
| languages spoken (P1412) | Guyanese Creole (Q35552) |
| official website (P856) | https://gadurarealestate.com/nitin-gadura/ |
| phone number (P1329) | +1-917-705-0132 |
| email address (P968) | Nitink.gadura@gmail.com |
| Zillow profile | https://www.zillow.com/profile/NitinGadura106 |
| Homes.com profile | https://www.homes.com/real-estate-agents/nitin-gadura/9t6kfc5/ |
| field of work (P101) | residential real estate |
| field of work (P101) | first-time homebuyer representation |
| field of work (P101) | Indo-Caribbean community real estate |

### References

- Agent profile: https://gadurarealestate.com/nitin-gadura/
- NY DOS license lookup (cite specific license # when added)
- Brokerage employee listing: https://gadurarealestate.com/meet-the-agents.html

---

## Post-submission checklist

- [ ] Submit entity 1, wait for QID assignment
- [ ] Submit entity 2 referencing entity 1's QID
- [ ] Add `sameAs` statements pointing back from gadurarealestate.com to the QIDs once assigned
- [ ] Add Wikidata QIDs to JSON-LD `sameAs` arrays in `_includes/ai-master-schema.html`
- [ ] Re-run `python3 scripts/inject_ai_schema.py --apply`
- [ ] Submit IndexNow ping
- [ ] Wait 30 days; check Google Knowledge Graph at: https://www.google.com/search?q=%22Nitin+Gadura%22 — look for sidebar panel
