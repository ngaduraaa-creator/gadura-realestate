#!/usr/bin/env python3
"""
Generate monthly ZIP-level market reports for Gadura Real Estate service area.

Run monthly (manual or cron) to regenerate static HTML pages. Each page embeds
LIVE IDX Broker iframes for active listings, so the listing portion auto-updates
in real time. The static text (reasons to buy, neighborhood profile) is stable
and only changes when you intentionally edit the REPORT_DATA dict below.

Usage:
    python3 scripts/generate-market-reports.py

Output:
    market-reports/<zip>-<neighborhood>-market-report.html
    market-reports/index.html (auto-generated hub)
"""
import os, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT_DIR = os.path.join(ROOT, 'market-reports')
os.makedirs(OUT_DIR, exist_ok=True)

# Month string for report cover
now = datetime.date.today()
MONTH = now.strftime('%B %Y')
DATE_ISO = now.strftime('%Y-%m-%d')

# ===================================================================
# SERVICE-AREA DATA — edit this dict each month to refresh numbers.
# Keep "reasons" stable; update "median", "dom", etc. as MLS data shifts.
# ===================================================================
REPORT_DATA = [
    {
        "zip": "11414", "slug": "howard-beach",
        "name": "Howard Beach", "county": "Queens",
        "median": "$875,000", "dom": "42 days", "supply": "1.9 months", "ratio": "97.4%",
        "stock": "Detached 1–2 family, attached row, limited condo/co-op",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Waterfront Queens — canal, bay, and Jamaica Bay access define the lifestyle",
            "Tight, slow-turnover inventory — once homes are bought, families stay 15–25 years",
            "Four distinct sub-neighborhoods: Old Howard Beach, Lindenwood, New Howard Beach/Rockwood Park, Hamilton Beach",
            "Excellent commute via A train at Howard Beach–JFK with free AirTrain connection",
            "Quiet, residential character with strong community identity",
            "Restaurants and shopping clustered along Crossbay Boulevard",
            "PS 207 (Rockwood Park) and PS 232 (Lindenwood) serve local families"
        ],
        "caveats": [
            "Much of 11414 sits in FEMA Special Flood Hazard Areas (AE and VE zones)",
            "Flood insurance is a material monthly cost on many blocks",
            "Post-Sandy elevation and bulkhead condition affect resale"
        ],
    },
    {
        "zip": "11417", "slug": "ozone-park",
        "name": "Ozone Park", "county": "Queens",
        "median": "$850,000", "dom": "35 days", "supply": "2.1 months", "ratio": "98.1%",
        "stock": "Attached and detached 1–2 family, rowhouses, mixed-use on Crossbay",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Central South Queens location with A and J train access",
            "Strong 2-family owner-occupied market with rental offset economics",
            "Diverse, long-established community — Guyanese, Indo-Caribbean, Italian, Punjabi",
            "Crossbay Boulevard retail corridor — restaurants, grocery, services walkable",
            "FHA owner-occupant 2-family financing makes entry accessible at 3.5% down",
            "Tukhum Park and adjacent open spaces for families",
            "Strong resale velocity — 35-day average means sellers aren't sitting"
        ],
        "caveats": [
            "Older housing stock requires inspection of electrical, boiler, and basement",
            "Some streets flood during heavy rain (verify with FEMA maps)"
        ],
    },
    {
        "zip": "11418", "slug": "richmond-hill",
        "name": "Richmond Hill", "county": "Queens",
        "median": "$850,000", "dom": "38 days", "supply": "2.3 months", "ratio": "97.8%",
        "stock": "Victorian and colonial-revival 1-family, some 2-family",
        "school_district": "NYC DOE District 28",
        "reasons": [
            "Some of the oldest housing stock in Queens — Victorian character unlike anywhere else",
            "Forest Park adjacency — hundreds of acres of green space",
            "Quieter, tree-lined residential streets",
            "J and Z trains at 111th St and 121st St stations",
            "Growing restaurant and coffee scene along Lefferts Boulevard",
            "Strong multigenerational and family-oriented buyer pool",
            "More accessible price than Forest Hills for similar Victorian character"
        ],
        "caveats": [
            "Older homes require careful inspection — wiring, plumbing, roof age critical",
            "Basement/attic conversions often unfiled — verify Certificate of Occupancy"
        ],
    },
    {
        "zip": "11419", "slug": "south-richmond-hill",
        "name": "South Richmond Hill", "county": "Queens",
        "median": "$790,000", "dom": "31 days", "supply": "1.6 months", "ratio": "98.7%",
        "stock": "Dense 2-family rowhouses, attached 1-family",
        "school_district": "NYC DOE District 28",
        "reasons": [
            "One of the largest Punjabi, Sikh, and Indo-Caribbean communities in the United States",
            "Densest 2-family investor submarket in South Queens",
            "Liberty Avenue — cultural and commercial spine with every essential walkable",
            "Strong rental-income offset economics (owner-occupied upstairs, rental down)",
            "Multilingual buyer pool widens a seller's reach substantially",
            "31-day average DOM — fastest-moving submarket in our coverage",
            "FHA 3.5% down on 2-families accessible to first-time buyers"
        ],
        "caveats": [
            "Verify basement unit legality — unfiled conversions are common",
            "Dense construction means careful party-wall inspection recommended"
        ],
    },
    {
        "zip": "11420", "slug": "south-ozone-park",
        "name": "South Ozone Park", "county": "Queens",
        "median": "$720,000", "dom": "33 days", "supply": "1.8 months", "ratio": "98.3%",
        "stock": "2-family investor submarket, some 1-family",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Most active 2-family investor market in South Queens — deep inventory",
            "Strong rental demand from JFK workforce and Queens-Brooklyn commuters",
            "A train access via Aqueduct Racetrack–North Conduit Ave or Rockaway Blvd",
            "FHA 2–4 unit friendly for owner-occupant first-time buyers",
            "Consistent price growth over the last decade",
            "Diverse community including South Asian, Indo-Caribbean, and Hispanic families",
            "Relatively affordable entry into Queens ownership"
        ],
        "caveats": [
            "Older electrical and plumbing common in the housing stock",
            "Some blocks near JFK experience aircraft noise"
        ],
    },
    {
        "zip": "11421", "slug": "woodhaven",
        "name": "Woodhaven", "county": "Queens",
        "median": "$820,000", "dom": "34 days", "supply": "2.0 months", "ratio": "98.0%",
        "stock": "Brick 2-family rowhouses, detached 1-family",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Classic brick 2-family housing stock — durable, well-built homes",
            "J train access at Woodhaven Blvd with Manhattan and Brooklyn connections",
            "Forest Park adjacency — recreational asset on the northern edge",
            "Jamaica Avenue commercial corridor with established small businesses",
            "Strong first-time buyer and multigenerational family activity",
            "Prices typically below Richmond Hill for similar square footage",
            "Active community civic associations"
        ],
        "caveats": [
            "1920s-era brick construction requires repointing inspection",
            "Some sidewalks and streets need infrastructure upgrades"
        ],
    },
    {
        "zip": "11432", "slug": "jamaica",
        "name": "Jamaica", "county": "Queens",
        "median": "$725,000", "dom": "40 days", "supply": "2.5 months", "ratio": "96.9%",
        "stock": "Wide range — Jamaica Estates luxury to 11433 entry-level",
        "school_district": "NYC DOE District 28 / 29",
        "reasons": [
            "Widest price range in Queens — everything from $500K first-time buyer to $1.2M+ Jamaica Estates luxury",
            "Major transit hub — LIRR Jamaica Station (express to Penn), E, F, J, Z trains, AirTrain to JFK",
            "Jamaica Estates — tree-lined Tudor detached homes, premium schools",
            "St. John's University and cultural anchors",
            "Strong rental market for investor-owned properties",
            "Active redevelopment along Hillside and Jamaica Avenues",
            "Diverse, historic African-American and Caribbean community"
        ],
        "caveats": [
            "11432 vs 11433 vs 11434 price differences are substantial — know your sub-ZIP",
            "Some blocks have higher vacancy or distressed inventory"
        ],
    },
    {
        "zip": "11428", "slug": "queens-village",
        "name": "Queens Village", "county": "Queens",
        "median": "$670,000", "dom": "38 days", "supply": "2.2 months", "ratio": "97.5%",
        "stock": "Detached 1-family, some semi-attached, FHA-heavy buyer pool",
        "school_district": "NYC DOE District 29",
        "reasons": [
            "Detached single-family homes at more accessible prices than northern Queens",
            "LIRR Queens Village station — express service to Penn",
            "Quieter residential streets with yard space",
            "Strong first-time buyer submarket, FHA-friendly",
            "Diverse, well-established community with multigenerational families",
            "Adjacent to Nassau border — Belmont and Cambria Heights walkable",
            "Good resale velocity despite being further out"
        ],
        "caveats": [
            "Longer commute to Midtown via subway (LIRR is faster)",
            "Some blocks have aging infrastructure"
        ],
    },
    {
        "zip": "11693", "slug": "broad-channel",
        "name": "Broad Channel", "county": "Queens",
        "median": "$780,000", "dom": "48 days", "supply": "2.8 months", "ratio": "96.2%",
        "stock": "Waterfront stilt homes, detached 1-family, unique bungalows",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Unique island community inside Jamaica Bay — nothing else like it in NYC",
            "Direct water access on nearly every block — boating lifestyle built in",
            "Small, tight-knit community with strong identity",
            "Jamaica Bay Wildlife Refuge on doorstep",
            "A train connection to Manhattan available",
            "Peaceful, almost rural feel inside the five boroughs",
            "Appreciating slowly but steadily over the last decade"
        ],
        "caveats": [
            "FEMA flood zones (AE and VE) dominate — flood insurance essential",
            "Bulkhead and stilt-foundation condition critical to inspect",
            "Limited school and retail options — most residents drive off-island"
        ],
    },
    {
        "zip": "11694", "slug": "rockaway-park",
        "name": "Rockaway Park", "county": "Queens",
        "median": "$880,000", "dom": "52 days", "supply": "3.1 months", "ratio": "96.5%",
        "stock": "Oceanfront condos, co-ops, 1- and 2-family detached",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Oceanfront Queens — year-round beach lifestyle within NYC",
            "A train access (with seasonal shuttle)",
            "Revitalized boardwalk and beach infrastructure post-Sandy",
            "Growing dining and surf scene along Beach 92nd–Beach 116th",
            "Mix of seasonal and year-round residents",
            "Condos with direct beach access at relatively accessible Queens prices",
            "Active civic and community organizations"
        ],
        "caveats": [
            "Waterfront flood exposure — FEMA mapping essential",
            "Travel time to Manhattan is longer than inland Queens",
            "Post-storm infrastructure concerns to verify per block"
        ],
    },
    {
        "zip": "11691", "slug": "far-rockaway",
        "name": "Far Rockaway", "county": "Queens",
        "median": "$580,000", "dom": "55 days", "supply": "3.5 months", "ratio": "95.8%",
        "stock": "Mix of condos, co-ops, 1–4 family; diverse housing types",
        "school_district": "NYC DOE District 27",
        "reasons": [
            "Most affordable entry to oceanfront Queens living",
            "A train access at the end of the Rockaway line",
            "LIRR Far Rockaway station to Brooklyn/Penn",
            "Wide price range — starter condos through larger family homes",
            "Diverse, historic communities including Jewish Orthodox enclaves in the Five Towns border",
            "Beach access and waterfront recreation",
            "Active neighborhood revitalization efforts"
        ],
        "caveats": [
            "Sub-neighborhood variation is large — verify specific block",
            "Flood exposure in many areas",
            "Longer commute profile"
        ],
    },
    {
        "zip": "11004", "slug": "glen-oaks",
        "name": "Glen Oaks", "county": "Queens",
        "median": "$480,000", "dom": "62 days", "supply": "3.2 months", "ratio": "96.5%",
        "stock": "Primarily co-op — Glen Oaks Village is one of largest in Queens; some detached",
        "school_district": "NYC DOE District 26",
        "reasons": [
            "Glen Oaks Village — one of the largest garden-apartment co-op complexes in the borough",
            "NYC DOE District 26 — historically highest-rated elementary schools in Queens",
            "Quiet, park-like setting with mature trees",
            "Affordable entry to NYC homeownership via co-op structure",
            "Access to both LIRR and express bus to Manhattan",
            "Strong retirement and multigenerational community",
            "Nassau border lifestyle at NYC tax rates"
        ],
        "caveats": [
            "Co-op board approval required — prepare for financial disclosure process",
            "Maintenance fees apply on top of any mortgage",
            "Longer commute than central Queens"
        ],
    },
    {
        "zip": "11426", "slug": "bellerose",
        "name": "Bellerose", "county": "Queens",
        "median": "$825,000", "dom": "45 days", "supply": "2.6 months", "ratio": "97.2%",
        "stock": "Detached 1-family, suburban-feel, Nassau-adjacent",
        "school_district": "NYC DOE District 26",
        "reasons": [
            "Suburban feel within NYC city limits — detached homes, yards, quiet streets",
            "District 26 schools — one of the top-rated districts in Queens",
            "LIRR Bellerose station — fast commute to Manhattan",
            "Nassau border — easy access to Long Island amenities",
            "Strong family-oriented community with long-hold owners",
            "Parks and recreation infrastructure",
            "Premium Queens commuter market without Nassau tax rates"
        ],
        "caveats": [
            "Prices tracking toward Nassau levels",
            "Longer commute than central Queens on subway alone"
        ],
    },
    {
        "zip": "11001", "slug": "floral-park",
        "name": "Floral Park", "county": "Queens / Nassau border",
        "median": "$830,000", "dom": "40 days", "supply": "2.4 months", "ratio": "97.5%",
        "stock": "Detached 1-family, some 2-family, suburban character",
        "school_district": "NYC DOE District 26 / Nassau districts",
        "reasons": [
            "Straddles Queens and Nassau — choose your tax/school district based on address",
            "LIRR Floral Park station — 28-minute ride to Penn Station",
            "Detached single-family housing stock with yards",
            "Strong walking village feel along Tulip Avenue",
            "Excellent schools on both the Queens and Nassau sides",
            "Close to Long Island parkways for day-trip access to beaches and parks",
            "Community events and civic associations"
        ],
        "caveats": [
            "Know which side of the street you're on — taxes and school districts differ",
            "Some village-level Nassau taxes can be higher than the equivalent Queens block"
        ],
    },
    {
        "zip": "11580", "slug": "valley-stream",
        "name": "Valley Stream", "county": "Nassau",
        "median": "$620,000", "dom": "36 days", "supply": "2.3 months", "ratio": "97.8%",
        "stock": "Detached 1-family, 2-family, village character",
        "school_district": "Valley Stream Central High / Elementary districts",
        "reasons": [
            "First Long Island town off the Queens border — most accessible Nassau entry",
            "Strong LIRR service — 30-minute ride to Penn",
            "Green Acres Mall and commercial corridor",
            "Diverse, family-oriented community",
            "Relatively accessible Nassau pricing for detached homes",
            "Access to Long Island beaches and parks",
            "Solid school options across multiple districts"
        ],
        "caveats": [
            "Nassau property taxes apply — typically $12K–$18K annually on these homes",
            "Village-level taxes vary by specific village boundaries within Valley Stream"
        ],
    },
    {
        "zip": "11003", "slug": "elmont",
        "name": "Elmont", "county": "Nassau",
        "median": "$610,000", "dom": "38 days", "supply": "2.5 months", "ratio": "97.4%",
        "stock": "Detached 1-family, 2-family, Queens-border character",
        "school_district": "Sewanhaka / Elmont districts",
        "reasons": [
            "Queens-adjacent Nassau entry — commute and lifestyle feel like Queens",
            "Strong South Asian and Caribbean community anchor",
            "Belmont Park — horse racing and the new UBS Arena revitalization",
            "More yard space than neighboring Queens ZIPs at comparable prices",
            "Access to LIRR via Elmont–UBS Arena station (new), plus bus connections",
            "Diverse commercial corridors along Hempstead Turnpike",
            "Good family community with long-hold ownership patterns"
        ],
        "caveats": [
            "Nassau taxes and school district rules apply",
            "Verify specific school district — Elmont-Sewanhaka boundaries matter"
        ],
    },
    {
        "zip": "11550", "slug": "hempstead",
        "name": "Hempstead", "county": "Nassau",
        "median": "$550,000", "dom": "42 days", "supply": "2.8 months", "ratio": "96.8%",
        "stock": "Wide range — detached, 1–2 family, condos, some multi-unit",
        "school_district": "Hempstead UFSD",
        "reasons": [
            "Nassau County seat — historic, central location",
            "Most accessible detached-home pricing in Nassau's inner ring",
            "LIRR Hempstead station with Main Line service",
            "Hofstra University and NuHealth medical anchor major employers",
            "Diverse, long-established community",
            "Active redevelopment and revitalization efforts",
            "Central Nassau location — everything else is a short drive"
        ],
        "caveats": [
            "Sub-neighborhood variation is large — verify the specific village",
            "School district performance varies by zone"
        ],
    },
    {
        "zip": "11570", "slug": "rockville-centre",
        "name": "Rockville Centre", "county": "Nassau",
        "median": "$820,000", "dom": "32 days", "supply": "1.8 months", "ratio": "98.5%",
        "stock": "Detached 1-family, colonial and Tudor, premium suburban",
        "school_district": "Rockville Centre UFSD",
        "reasons": [
            "LIRR express station — 38-minute ride to Penn Station",
            "Walkable downtown with restaurants, coffee, shopping",
            "Rockville Centre school district — strong performance",
            "Family-oriented, tight-knit community",
            "Mix of charming older homes and mid-century colonials",
            "Active civic and recreational life",
            "South Shore of Long Island — beaches reachable quickly"
        ],
        "caveats": [
            "Nassau taxes typical — budget $15K–$25K+ annually",
            "Prices tracking toward the top of the mid-market tier"
        ],
    },
]

# ===================================================================
# HTML TEMPLATE
# ===================================================================

def render_report(entry):
    zip_ = entry["zip"]
    slug = entry["slug"]
    name = entry["name"]
    reasons_html = "\n".join(f"      <li>{r}</li>" for r in entry["reasons"])
    caveats_html = "\n".join(f"      <li>{c}</li>" for c in entry.get("caveats", []))
    caveats_section = f"""
<h2>Things to Verify Before Buying</h2>
<ul>
{caveats_html}
</ul>""" if caveats_html else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} ({zip_}) Market Report {MONTH} — Prices, Trends & Reasons to Buy | Gadura Real Estate</title>
<meta name="description" content="{name} ({zip_}) {entry['county']} monthly market report: median {entry['median']}, {entry['dom']} days on market, reasons to buy in {name}, live MLS listings, and neighborhood profile. Updated {MONTH}.">
<meta name="keywords" content="{name} market report, {zip_} home prices, {name} real estate {now.year}, reasons to buy {name}, {name} median price, {name} homes for sale, Nitin Gadura {name}">
<link rel="canonical" href="https://gadurarealestate.com/market-reports/{zip_}-{slug}-market-report.html">
<meta property="og:type" content="article">
<meta property="og:title" content="{name} ({zip_}) Market Report {MONTH}">
<meta property="og:description" content="Prices, trends, reasons to buy, and live MLS listings for {name}. Updated {MONTH}.">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{name} ({zip_}) Market Report {MONTH}","author":{{"@type":"Person","name":"Nitin Gadura"}},"publisher":{{"@type":"RealEstateAgent","name":"Gadura Real Estate, LLC","telephone":"+1-917-705-0132"}},"datePublished":"{DATE_ISO}","dateModified":"{DATE_ISO}"}}
</script>
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/senior-friendly.css">
<script src="/js/senior-tools.js" defer></script>
<style>
.report{{max-width:1000px;margin:0 auto;padding:2rem 1.25rem;line-height:1.7}}
.report h1{{font-size:clamp(2rem,1.2rem+2.4vw,3rem);margin:.5rem 0 1rem}}
.report h2{{margin-top:2.25rem;border-bottom:2px solid #e8c547;padding-bottom:.35rem}}
.eyebrow{{color:#00A651;font-weight:700;letter-spacing:1px;text-transform:uppercase;font-size:.85rem}}
.updated{{color:#555;font-style:italic;font-size:.9rem}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin:1.5rem 0}}
.stat{{background:#0b2545;color:#fff;padding:1.25rem;border-radius:8px;text-align:center}}
.stat b{{display:block;font-size:1.6rem;color:#e8c547}}
.stat span{{font-size:.85rem;color:#d4d9e0}}
.reasons-grid{{background:#fff8e1;border-left:4px solid #e8c547;padding:1.25rem 1.5rem;border-radius:8px;margin:1.5rem 0}}
.reasons-grid ol{{margin:.5rem 0 0 1rem;padding:0}}
.reasons-grid li{{margin:.5rem 0;font-weight:500}}
.idx-frame{{position:relative;width:100%;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.06);background:#fafafa;margin:1rem 0}}
.idx-frame iframe{{width:100%;height:620px;border:0;display:block}}
.nitin-card{{background:linear-gradient(135deg,#0b2545,#13315c);color:#fff;padding:1.5rem;border-radius:10px;margin:2rem 0}}
.nitin-card h3{{color:#e8c547;margin-top:0}}
.nitin-card a{{color:#e8c547;font-weight:700}}
.subscribe-card{{background:#f0f9ff;border:2px solid #00A651;padding:1.25rem 1.5rem;border-radius:10px;margin:2rem 0}}
.subscribe-card h3{{margin-top:0;color:#00813f}}
.legal{{font-size:.85rem;color:#555;font-style:italic;margin-top:1.5rem;padding-top:1rem;border-top:1px solid #ddd}}
</style>
</head>
<body>
<nav><a href="/">Home</a> · <a href="/market-reports/">Market Reports</a> · <a href="/listings/">MLS Search</a> · <a href="/why-choose-a-broker/">Why a Broker</a> · <a href="/contact.html">Contact</a></nav>

<main class="report">
<p class="eyebrow">📊 Monthly Market Report · {entry['county']}</p>
<h1>{name} ({zip_}) Market Report</h1>
<p class="updated">{MONTH} · data sourced from OneKey® MLS activity · next update scheduled {(now.replace(day=1) + datetime.timedelta(days=32)).replace(day=1).strftime('%B %Y')}</p>

<section aria-label="Headline statistics">
<div class="stats">
  <div class="stat"><b>{entry['median']}</b><span>Median sale price</span></div>
  <div class="stat"><b>{entry['dom']}</b><span>Avg. days on market</span></div>
  <div class="stat"><b>{entry['supply']}</b><span>Months of supply</span></div>
  <div class="stat"><b>{entry['ratio']}</b><span>Sale-to-list ratio</span></div>
</div>
</section>

<div class="subscribe-card">
<h3>📬 Get This Report Monthly</h3>
<p>Want the {name} market report delivered to your inbox on the 1st of every month? <a href="/market-reports/subscribe.html?zip={zip_}">Subscribe free →</a>. No spam, cancel anytime, only the data that matters for {zip_}.</p>
</div>

<h2>Why Buy in {name}</h2>
<div class="reasons-grid">
<ol>
{reasons_html}
</ol>
</div>

<h2>Neighborhood Profile</h2>
<p><strong>Housing stock:</strong> {entry['stock']}</p>
<p><strong>School district:</strong> {entry['school_district']}</p>
<p><strong>County:</strong> {entry['county']}</p>

{caveats_section}

<h2>Live {name} Listings (OneKey® MLS)</h2>
<p>Every active listing in {zip_}, pulled live from the MLS. Click any pin to see photos, full details, and request a showing.</p>
<div class="idx-frame">
<iframe src="https://gadurarealestate.idxbroker.com/idx/map/mapsearch?pt=1&ccz=zipcode&zipcode%5B%5D={zip_}" loading="lazy" title="Live {name} MLS listings" allow="geolocation"></iframe>
</div>

<div class="nitin-card">
<h3>Thinking About Buying or Selling in {name}?</h3>
<p><strong>Nitin Gadura · (917) 705-0132</strong></p>
<p>I pull block-level comps for any {zip_} address at no charge. Free 15-minute consult, no pressure.</p>
<p><a href="tel:+19177050132">Call (917) 705-0132</a> · <a href="/contact.html">Request consult →</a></p>
</div>

<h2>Related Resources</h2>
<ul>
<li><a href="/why-choose-a-broker/{slug}.html">Why a {name} real estate broker</a></li>
<li><a href="/listings/">Full NY MLS search</a></li>
<li><a href="/open-houses/">Upcoming open houses</a></li>
<li><a href="/blog/nyc-property-tax-guide-by-zip.html">NYC property tax by ZIP</a></li>
<li><a href="/closing-costs-nyc-guide.html">NYC closing costs</a></li>
<li><a href="/market-reports/">All market reports</a></li>
</ul>

<p class="legal">Figures are directional based on OneKey® MLS activity for ZIP {zip_} and similar submarkets. Not a substitute for a transaction-specific CMA. Informational only; not legal, tax, or investment advice. Commissions are negotiable and not set by law (19 NYCRR §175.7). Equal Housing Opportunity. Nitin Gadura, Gadura Real Estate, LLC.</p>
</main>
</body>
</html>
"""

def render_index():
    rows = []
    for entry in REPORT_DATA:
        rows.append(f'  <a class="report-card" href="{entry["zip"]}-{entry["slug"]}-market-report.html"><strong>{entry["name"]} ({entry["zip"]})</strong><span>{entry["county"]}</span><em>Median {entry["median"]} · {entry["dom"]}</em></a>')
    grid = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NY Real Estate Market Reports by ZIP — {MONTH} | Gadura Real Estate</title>
<meta name="description" content="Monthly market reports for every Queens, Brooklyn, Nassau, and Suffolk ZIP Gadura Real Estate serves. Median prices, trends, reasons to buy, and live MLS listings. Updated {MONTH}.">
<link rel="canonical" href="https://gadurarealestate.com/market-reports/">
<link rel="stylesheet" href="/css/style.css">
<link rel="stylesheet" href="/css/senior-friendly.css">
<script src="/js/senior-tools.js" defer></script>
<style>
.hub{{max-width:1200px;margin:0 auto;padding:2rem 1.25rem;line-height:1.7}}
.hub h1{{font-size:clamp(2rem,1.2rem+2.4vw,3rem)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;margin:1.5rem 0}}
.report-card{{display:flex;flex-direction:column;padding:1.25rem;background:#fff8e1;border-left:4px solid #e8c547;border-radius:8px;text-decoration:none;color:#0b2545;transition:transform .15s}}
.report-card:hover{{transform:translateY(-2px);background:#fff3c4}}
.report-card strong{{font-size:1.1rem}}
.report-card span{{color:#555;font-size:.85rem;margin-top:.15rem}}
.report-card em{{color:#00813f;font-weight:600;font-style:normal;margin-top:.5rem;font-size:.88rem}}
.subscribe-card{{background:#f0f9ff;border:2px solid #00A651;padding:1.5rem;border-radius:10px;margin:2rem 0}}
.subscribe-card h3{{margin-top:0;color:#00813f}}
.legal{{font-size:.85rem;color:#555;font-style:italic;margin-top:2rem;padding-top:1rem;border-top:1px solid #ddd}}
</style>
</head>
<body>
<nav><a href="/">Home</a> · <a href="/market-reports/">Market Reports</a> · <a href="/listings/">MLS Search</a> · <a href="/why-choose-a-broker/">Why a Broker</a></nav>
<main class="hub">
<h1>NY Market Reports by ZIP — {MONTH}</h1>
<p>Monthly market reports for every ZIP code in the Gadura Real Estate service area. Each report includes median price, days on market, months of supply, reasons to buy in that neighborhood, and live OneKey® MLS listings. Updated at the start of every month.</p>

<div class="subscribe-card">
<h3>📬 Subscribe Free</h3>
<p>Pick any ZIP and get its report emailed on the 1st of every month. No spam, just the numbers. <a href="/market-reports/subscribe.html">Subscribe →</a></p>
</div>

<h2>Select a Neighborhood</h2>
<div class="grid">
{grid}
</div>

<p class="legal">Market figures are directional from recent OneKey® MLS activity. Not a substitute for transaction-specific CMA. Equal Housing Opportunity. Nitin Gadura, Gadura Real Estate, LLC.</p>
</main>
</body>
</html>
"""

def main():
    generated = 0
    for entry in REPORT_DATA:
        fname = f"{entry['zip']}-{entry['slug']}-market-report.html"
        path = os.path.join(OUT_DIR, fname)
        with open(path, 'w') as f:
            f.write(render_report(entry))
        generated += 1
        print(f"✓ {fname}")

    idx_path = os.path.join(OUT_DIR, 'index.html')
    with open(idx_path, 'w') as f:
        f.write(render_index())
    print(f"\n✓ index.html ({generated} reports linked)")
    print(f"\nGenerated {generated} market reports for {MONTH}")

if __name__ == '__main__':
    main()
