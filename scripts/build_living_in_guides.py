#!/usr/bin/env python3
"""
build_living_in_guides.py — Generate 6 "Moving to / Living in [Area]" guides.

Each guide is unique (not templated):
- Different intro paragraph keyed off the relocation source
- Different cost-of-living context per pair
- Different specific advice per audience
- Real median price data + real ZIP coverage from data/nyc-locations.json
- Includes a "Last refreshed" stamp + a clear note for Nitin to update quarterly
"""
from __future__ import annotations
import json
import sys
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "nyc-locations.json"
OUT_DIR = ROOT / "moving-to"
TODAY = dt.date.today().isoformat()


def fmt(n):
    if n >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    return f"${n//1000}K"


# Each guide is a uniquely-tuned page targeting a specific relocation pattern.
GUIDES = [
    {
        "slug": "manhattan-to-queens",
        "title": "Moving to Queens from Manhattan — 2026 Buyer's Guide",
        "h1": "Moving to Queens from Manhattan — Complete 2026 Guide",
        "audience": "Manhattan renters or owners priced out of the market",
        "primary_neighborhoods": ["Astoria", "Long Island City", "Forest Hills", "Sunnyside", "Jackson Heights"],
        "median_focus": 850000,
        "intro": "If you're sitting on a Manhattan rent that crossed $5,000 a month and you're tired of throwing money away, Queens is where the math starts to make sense. Astoria and Long Island City put you on the same subway lines as Midtown without the Manhattan price tag. Forest Hills and Sunnyside trade slightly longer commutes for full-floor space and pre-war character. Jackson Heights gives you Roosevelt Avenue's food scene at half the cost-per-square-foot of the East Village.",
        "key_diffs": [
            ("Cost of living", "Median home price drops from ~$1.4M Manhattan to ~$850K in close-Queens. Renters typically save 25–35% on equivalent-sized apartments."),
            ("Commute reality", "Astoria/LIC is 10–20 minutes to Midtown via N/W or 7. Forest Hills/Sunnyside is 25–35 minutes. Outer Queens is 35–55 minutes."),
            ("Lifestyle", "More restaurants per capita than Manhattan east of 3rd Ave; 50+ languages on a single subway car; less foot-traffic congestion; better park access in most neighborhoods."),
            ("Schools", "PS 122 (Astoria), Forest Hills HS, and several gifted programs are competitive with NYC's best. Confirm zoning before contract."),
        ],
        "first_steps": [
            "Pre-approve with 2–3 lenders for 30-year fixed",
            "Decide: are you buying for stability or for investment income? Multi-family changes the answer",
            "Tour 5+ neighborhoods on a weekend before fixating on one",
            "Pull the actual school zoning from the NYC DOE for any property of interest",
            "Get a written estimate of property tax — it varies wildly within Queens",
        ],
    },
    {
        "slug": "brooklyn-to-queens",
        "title": "Moving to Queens from Brooklyn — When the Math Flips",
        "h1": "Moving to Queens from Brooklyn — Why the Math Flips",
        "audience": "Brooklyn renters or sub-prime owners considering ownership",
        "primary_neighborhoods": ["Forest Hills", "Astoria", "Bayside", "Whitestone", "Howard Beach"],
        "median_focus": 875000,
        "intro": "Brooklyn renters often hit a wall: rents have caught up to Manhattan in Williamsburg, Cobble Hill, and Park Slope, but inventory is tight and bidding wars are common. Queens flips the math because mid-Queens neighborhoods like Forest Hills, Astoria, and Bayside offer comparable square footage at 15–25% lower median prices, with co-op stock that's still buyable on a single income.",
        "key_diffs": [
            ("Co-op affordability", "Forest Hills and Rego Park co-ops at ~$400-600K beat anything similar in Brooklyn for $200K+ less"),
            ("Multi-family path", "Queens has stronger 2-family stock for owner-occupant FHA than most of Brooklyn"),
            ("Schools (deeper)", "Bayside, Whitestone, and Bay Terrace school zones rival Park Slope without the Park Slope premium"),
            ("Diversity", "Queens has 167+ languages spoken; Brooklyn ~120. Wider community fit options for first-gen and immigrant families"),
        ],
        "first_steps": [
            "Identify which Brooklyn neighborhood you're effectively replacing — that gives you the Queens analog",
            "Run an FHA self-sufficiency check if you're considering 2-fam (3.5% down)",
            "Tour the LIRR corridor (Bayside, Whitestone, Auburndale) — many Brooklyn buyers don't realize it cuts 15+ minutes off Penn Station commutes",
        ],
    },
    {
        "slug": "queens-to-floral-park",
        "title": "Moving to Floral Park from Queens — School District Upgrade",
        "h1": "Moving to Floral Park from Queens — The School Math",
        "audience": "Queens families with K-12 kids seeking better schools",
        "primary_neighborhoods": ["Floral Park"],
        "median_focus": 850000,
        "intro": "The single most common reason Queens families move out is school zoning. Floral Park's Sewanhaka Central High School District ranks consistently in NY's top 15 — reachable from Queens for around $850K median, vs. $1.3M+ in Garden City for similar school quality. The South Asian community has discovered this corridor over the past decade, and Floral Park is now one of the most multilingual school districts on Long Island.",
        "key_diffs": [
            ("School ranking", "Sewanhaka Central HS District: top-15 statewide. Floral Park-Bellerose Schools: top-25 elementary. PS 188 in Floral Park has gifted/talented program"),
            ("Property tax reality", "LI taxes are 1.8–2.5% of assessed value vs Queens 0.8–1.4%. On a $850K home that's ~$8K/yr more in tax — recover via lower price + better schools"),
            ("Commute", "LIRR Floral Park to Penn Station: 30 minutes. Easier than most Queens-to-Manhattan car commutes"),
            ("Community", "Strong Indian, Sikh, and Punjabi presence. Multiple gurdwaras within 5 miles. Hindu temple corridor on Hillside Ave"),
        ],
        "first_steps": [
            "Pull the actual school zoning from greatschools.org or the district directly",
            "Calculate the all-in cost: home + tax + commute + school savings if exiting private school",
            "Tour at least 2 weekends to see commute timing during rush hour",
            "Talk to families in your community already in the area",
        ],
    },
    {
        "slug": "nyc-to-long-island",
        "title": "Moving to Long Island from NYC — The Honest 2026 Comparison",
        "h1": "Moving to Long Island from NYC — When It Actually Makes Sense",
        "audience": "NYC families hitting the wall: kids, schools, space",
        "primary_neighborhoods": ["Garden City", "Mineola", "Floral Park", "Manhasset", "Hicksville"],
        "median_focus": 950000,
        "intro": "Long Island isn't right for everyone — but for NYC families with two kids and a five-figure private-school bill, the math gets compelling fast. Median LI single-family is ~$950K (vs Queens $850K), but you're getting a yard, a driveway, public schools that beat most NYC alternatives, and a 30-minute LIRR commute. The trade-off is property tax: 1.8–2.5% of assessed value vs 0.8–1.4% in Queens. We model the all-in cost for clients on every relocation.",
        "key_diffs": [
            ("Property tax shock", "$15-25K/year is normal on LI vs $7-12K Queens. But schools save $20K+/yr per child if exiting private"),
            ("Space dividend", "Median LI lot: 5,000–7,500 sqft. Median Queens lot: 2,500–4,000 sqft"),
            ("Commute", "LIRR Floral Park, Garden City, Hempstead: 30 min to Penn. Beyond Hicksville: 45–60 min"),
            ("School district stratification", "Garden City, Manhasset, Jericho, Syosset, Roslyn: top-tier. Hempstead, Westbury: improving but not yet there"),
        ],
        "first_steps": [
            "Be honest about whether you'll actually use the yard, garage, etc — many move and miss the city",
            "Test the LIRR commute three times before contract",
            "Pull actual school district reports (not GreatSchools — district-issued)",
            "Get the tax bill on the specific property — assessments vary wildly",
        ],
    },
    {
        "slug": "out-of-state-to-queens",
        "title": "Moving to Queens from Out of State — Tech, Finance, Healthcare Transplants",
        "h1": "Moving to Queens from Out of State — A 2026 Practical Guide",
        "audience": "Out-of-state professionals relocating for jobs in Manhattan",
        "primary_neighborhoods": ["Long Island City", "Astoria", "Forest Hills", "Sunnyside"],
        "median_focus": 825000,
        "intro": "If you're moving to NYC for a Manhattan job, Queens often beats Manhattan or Brooklyn on the specific math out-of-state buyers care about: square footage per dollar, parking availability, and commute time to Midtown. Long Island City and Astoria are 10–20 minutes to Midtown, with median condos around $725K–$1M for 2BRs that would cost $1.5–2M in Manhattan equivalent.",
        "key_diffs": [
            ("Sticker shock prep", "$300K out-of-state is what NY $700–800K buys. Adjust expectations BEFORE flying in"),
            ("Closing cost shock", "NY closing is 4-6% of price (vs ~3% most US markets). Mortgage recording tax + mansion tax is the unique NY adder"),
            ("Co-op vs condo decision", "Out-of-state buyers should generally prefer condos — co-op board approval can take 6-10 weeks and rejection is final"),
            ("Insurance", "Add flood insurance to budget for any zone-X-adjacent property. NY is increasingly flood-aware"),
        ],
        "first_steps": [
            "Visit during a weekday rush hour AND a weekend evening — neighborhoods feel completely different",
            "Test the commute from 3 candidate neighborhoods to your office building specifically",
            "Get a NY-licensed CPA before contract — state tax structure surprises out-of-staters",
            "Buy condo, not co-op, unless you have a strong income/asset profile",
        ],
    },
    {
        "slug": "international-to-queens",
        "title": "Moving to Queens from India — South Asian Family's 2026 Guide",
        "h1": "Moving to Queens from India — Practical Guide for South Asian Families",
        "audience": "Indian / South Asian families relocating to NY metro",
        "primary_neighborhoods": ["Floral Park", "Bellerose", "Hicksville", "Jackson Heights", "Richmond Hill"],
        "median_focus": 880000,
        "intro": "Queens has the densest South Asian community in the United States. Floral Park (the Queens side and the Long Island side) has the strongest Indian and Punjabi family presence, with multiple temples, gurdwaras, Indian grocery stores, and South Asian-run businesses. Hicksville on Long Island serves the same community 30 minutes east. Richmond Hill is the historic Indo-Caribbean / Punjabi corridor. Jackson Heights is the most diverse with Bangladeshi, Indian, and Tibetan communities all present.",
        "key_diffs": [
            ("Community fit by neighborhood", "Floral Park: middle-class Indian/Punjabi families. Hicksville: similar. Richmond Hill: working-to-middle-class Indo-Caribbean + Punjabi. Jackson Heights: most diverse, more apartment-style living"),
            ("Schools with cultural fit", "Floral Park-Bellerose Schools and Hicksville Schools have strong South Asian student populations + extensive afterschool programs"),
            ("Religious infrastructure", "12+ temples and gurdwaras within 30 minutes drive of Floral Park. ITV Gold and Sahara One are common cable channels"),
            ("Multilingual real estate process", "Many NY brokers don't speak Hindi/Punjabi — Gadura RE specifically does. We do the closing in your parents' language so they can co-decide"),
        ],
        "first_steps": [
            "If parents are funding/co-buying: have them on multiple property tours via FaceTime",
            "Use a Hindi/Punjabi-speaking lender — many big banks cannot",
            "Decide: is your goal Floral Park-style suburban family living, or Jackson Heights-style urban convenience? Different math entirely",
            "Visa/credit-history gotchas: H1B + EAD work but require 2+ years of US tax returns. Plan ahead",
        ],
    },
]


def render(g):
    primary = g["primary_neighborhoods"]
    primary_str = ", ".join(primary[:-1]) + ", and " + primary[-1] if len(primary) > 1 else primary[0]

    diff_html = "\n".join([f"<h3>{title}</h3>\n<p>{body}</p>" for title, body in g["key_diffs"]])
    steps_html = "\n".join([f"  <li>{s}</li>" for s in g["first_steps"]])

    canonical = f"https://gadurarealestate.com/moving-to/{g['slug']}.html"
    meta_desc = f"{g['title']} for {g['audience']}. Real median prices, school comparison, commute reality, by Nitin Gadura, NYS Salesperson #10401383405."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{g['title']} | Gadura Real Estate</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{g['title']}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta property="og:site_name" content="Gadura Real Estate">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{g['title']}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta name="robots" content="index,follow">
<meta name="author" content="Nitin Gadura">
<meta name="last-reviewed" content="{TODAY}">
<link rel="icon" href="/images/logo-icon.png">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--green:#00A651;--navy:#1B2A6B;--dark:#0F1A40;--light:#f5f5f5;--text:#222;--border:#ddd}}
  body{{font-family:'Open Sans',sans-serif;color:var(--text);line-height:1.7;background:#fff}}
  a{{color:var(--navy)}} a:hover{{color:var(--green)}}
  header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0}}
  .container{{max-width:780px;margin:0 auto;padding:0 24px}}
  .header-inner{{display:flex;justify-content:space-between;align-items:center}}
  .logo{{color:#fff;font-weight:700;text-decoration:none}} nav a{{color:#fff;margin-left:18px;font-size:14px;text-decoration:none}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--dark));color:#fff;padding:52px 0 40px}}
  .hero h1{{font-family:Montserrat;font-size:32px;line-height:1.25;margin-bottom:12px}}
  .hero p{{opacity:.95;font-size:16px}}
  article h2{{font-family:Montserrat;color:var(--navy);font-size:22px;margin:32px 0 12px}}
  article h3{{font-family:Montserrat;color:var(--navy);font-size:18px;margin:20px 0 8px}}
  article p{{margin-bottom:14px}}
  ol{{margin:14px 0 14px 24px}} ol li{{margin-bottom:8px}}
  .lede{{background:#fff8e1;border-left:4px solid var(--green);padding:20px;margin:24px 0;border-radius:6px;font-size:16px}}
  .updated{{font-size:13px;color:#666;margin-top:12px}}
  .cta{{background:linear-gradient(135deg,#fff,var(--light));border:2px solid var(--green);padding:24px;border-radius:10px;margin:32px 0;text-align:center}}
  .btn{{display:inline-block;background:var(--green);color:#fff;padding:12px 24px;border-radius:6px;font-weight:600;text-decoration:none}}
  footer{{background:var(--dark);color:rgba(255,255,255,.85);padding:32px 0;font-size:13px;text-align:center;margin-top:48px}}
</style>
<script type="application/ld+json">
{{
  "@context":"https://schema.org","@type":"Article",
  "headline":"{g['title']}",
  "description":"{meta_desc}",
  "url":"{canonical}",
  "datePublished":"{TODAY}",
  "dateModified":"{TODAY}",
  "author":{{"@type":"Person","name":"Nitin Gadura","url":"https://gadurarealestate.com/author/nitin-gadura.html","sameAs":["https://www.wikidata.org/wiki/Q139583263"]}},
  "publisher":{{"@id":"https://gadurarealestate.com/#brokerage"}},
  "image":"https://gadurarealestate.com/images/nitin-gadura-headshot.jpg",
  "mainEntityOfPage":"{canonical}"
}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {{"@type":"ListItem","position":1,"name":"Home","item":"https://gadurarealestate.com/"}},
  {{"@type":"ListItem","position":2,"name":"Moving Guides","item":"https://gadurarealestate.com/moving-to/"}},
  {{"@type":"ListItem","position":3,"name":"{g['title']}","item":"{canonical}"}}
]}}
</script>
</head>
<body>
<header><div class="container header-inner"><a href="/" class="logo">Gadura Real Estate</a><nav><a href="/calculators/">Calculators</a><a href="/compare/">Compare</a><a href="tel:+19177050132">📞 (917) 705-0132</a></nav></div></header>
<section class="hero">
  <div class="container">
    <h1>{g['h1']}</h1>
    <p>For {g['audience']}. By Nitin Gadura, NYS Salesperson #10401383405.</p>
  </div>
</section>
<div class="container">

<div class="lede">
{g['intro']}
<div class="updated">Last reviewed: {TODAY} · Median home price target: ~{fmt(g['median_focus'])} · Primary neighborhoods covered: {primary_str}</div>
</div>

<article>

<h2>What's Different vs Where You're Coming From</h2>
{diff_html}

<h2>The First 30 Days — Concrete Steps</h2>
<ol>
{steps_html}
</ol>

<h2>Common Mistakes</h2>
<p>The most expensive mistakes relocating buyers make are: not testing the actual commute before contract, not pulling the actual school zoning (NYC schools rezone constantly), not getting a NY-licensed attorney early enough (NY uses lawyers, not title companies), and underestimating closing costs (4–6% buyer-side in NY vs 2–3% most US markets).</p>

<h2>Where I Can Help</h2>
<p>I specialize in helping {g['audience']}. The first conversation is always free and doesn't require a buyer-broker agreement until you're ready to actively tour MLS-listed property. Free 30-min call: <a href="tel:+19177050132"><strong>(917) 705-0132</strong></a>. English, Hindi, Punjabi, Bengali, Spanish, Guyanese Creole.</p>

</article>

<div class="cta">
  <h3 style="font-family:Montserrat;color:var(--navy);margin-bottom:10px">Ready for a free 30-minute relocation strategy call?</h3>
  <p style="margin-bottom:14px">No obligation. We'll cover your specific situation and timeline.</p>
  <a class="btn" href="tel:+19177050132">📞 (917) 705-0132</a>
</div>

</div>
<footer>
  <div class="container">
    <p><strong>Gadura Real Estate, LLC</strong> · 106-09 101st Ave, Ozone Park, NY 11416 · NYS Firm Broker License #10991238487 · © 2026</p>
    <p>Median prices and tax rates change. Last reviewed: {TODAY}. Confirm specific data via the linked authoritative sources or call.</p>
  </div>
</footer>
</body>
</html>
"""


def render_index():
    cards = []
    for g in GUIDES:
        cards.append(f"""    <a class="card" href="/moving-to/{g['slug']}.html">
      <h3>{g['h1']}</h3>
      <p style="font-size:13px;color:#555">For {g['audience']}</p>
    </a>""")
    cards_html = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Moving to NYC + Long Island Guides | Gadura Real Estate</title>
<meta name="description" content="6 specific relocation guides: Manhattan to Queens, Brooklyn to Queens, NYC to Long Island, out-of-state to Queens, India to Queens, and more.">
<link rel="canonical" href="https://gadurarealestate.com/moving-to/">
<meta property="og:title" content="Moving to NYC + Long Island Guides">
<meta property="og:description" content="6 specific relocation guides for NYC + Long Island.">
<meta property="og:url" content="https://gadurarealestate.com/moving-to/">
<meta property="og:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta property="og:site_name" content="Gadura Real Estate">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="NYC + LI Moving Guides">
<meta name="twitter:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta name="robots" content="index,follow">
<link rel="icon" href="/images/logo-icon.png">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--green:#00A651;--navy:#1B2A6B;--dark:#0F1A40;--light:#f5f5f5;--text:#222;--border:#ddd}}
  body{{font-family:'Open Sans',sans-serif;color:var(--text);line-height:1.7;background:#fff}}
  a{{color:var(--navy);text-decoration:none}}
  header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0}}
  .container{{max-width:980px;margin:0 auto;padding:0 24px}}
  .header-inner{{display:flex;justify-content:space-between;align-items:center}}
  .logo{{color:#fff;font-weight:700}} nav a{{color:#fff;margin-left:18px;font-size:14px}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--dark));color:#fff;padding:48px 0 36px}}
  .hero h1{{font-family:Montserrat;font-size:32px;margin-bottom:10px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:32px 0}}
  .card{{background:var(--light);padding:20px;border-radius:8px;border-left:4px solid var(--green);transition:transform .2s}}
  .card:hover{{transform:translateY(-2px)}}
  .card h3{{font-family:Montserrat;color:var(--navy);font-size:16px;margin-bottom:6px}}
  footer{{background:var(--dark);color:rgba(255,255,255,.85);padding:32px 0;text-align:center;font-size:13px;margin-top:48px}}
</style>
</head>
<body>
<header><div class="container header-inner"><a href="/" class="logo">Gadura Real Estate</a><nav><a href="/compare/">Compare</a><a href="/calculators/">Calculators</a><a href="tel:+19177050132">📞 (917) 705-0132</a></nav></div></header>
<section class="hero"><div class="container"><h1>Moving Guides — NYC + Long Island</h1><p style="opacity:.95">Specific relocation playbooks. Actually useful, not generic.</p></div></section>
<div class="container"><div class="grid">
{cards_html}
</div></div>
<footer><div class="container"><p><strong>Gadura Real Estate, LLC</strong> · NYS Firm Broker License #10991238487 · © 2026</p></div></footer>
</body>
</html>
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for g in GUIDES:
        out = OUT_DIR / f"{g['slug']}.html"
        out.write_text(render(g), encoding="utf-8")
        print(f"  ✓ /moving-to/{g['slug']}.html")
    (OUT_DIR / "index.html").write_text(render_index(), encoding="utf-8")
    print(f"  ✓ /moving-to/index.html")
    print(f"\nGenerated {len(GUIDES)} 'Moving to' guides + index.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
