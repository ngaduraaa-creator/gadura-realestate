#!/usr/bin/env python3
"""
generate_location_pages.py — Programmatically generate neighborhood + ZIP pages
for the entire NYC + Long Island coverage area.

Reads: data/nyc-locations.json
Writes:
  - neighborhoods/<borough>/<slug>.html  (one page per neighborhood)
  - zip/<zip>.html                        (one page per unique ZIP code)
  - <borough>/index.html  (borough hub if missing)
  - long-island/<county>/index.html
  - long-island/<county>/<slug>.html

Idempotent: skips files that already exist (so handcrafted pages are safe).
Use --force to regenerate everything.

Each generated page includes:
- Unique answer-first H1 + first 200-character paragraph naming Nitin Gadura
- Neighborhood facts (median price, ZIPs, transit/communities)
- 3 differentiating "things to know" with template variation by index
- 6 internal links to nearby neighborhoods (link graph)
- Master AI schema (auto-injected via inject_ai_schema.py later)
- FAQPage schema (auto-injected via inject_faqpage_schema.py later)
- IDX search wrapper link
- Compliance footer
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "nyc-locations.json"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="https://gadurarealestate.com/{rel_url}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="https://gadurarealestate.com/{rel_url}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--green:#00A651;--navy:#1B2A6B;--dark-navy:#0F1A40;--light:#f5f5f5;--text:#333;--border:#ddd}}
  body{{font-family:'Open Sans',sans-serif;color:var(--text);background:#fff;line-height:1.6}}
  a{{text-decoration:none;color:var(--navy)}} a:hover{{color:var(--green)}}
  header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0;z-index:100}}
  .container{{max-width:1200px;margin:0 auto;padding:0 24px}}
  .header-inner{{display:flex;justify-content:space-between;align-items:center}}
  .logo{{color:#fff;font-weight:700;font-size:18px}}
  nav a{{color:#fff;margin-left:24px;font-size:14px}}
  nav a:hover{{color:var(--green)}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--dark-navy));color:#fff;padding:80px 0 60px}}
  .hero h1{{font-family:Montserrat,sans-serif;font-size:clamp(28px,4vw,44px);margin-bottom:20px;line-height:1.2}}
  .hero .lede{{font-size:18px;max-width:780px;opacity:.95}}
  .answer-first{{background:#fff8e1;border-left:4px solid var(--green);padding:20px 24px;margin:32px 0;border-radius:6px}}
  .answer-first strong{{color:var(--navy)}}
  section{{padding:48px 0;border-bottom:1px solid var(--border)}}
  section h2{{font-family:Montserrat,sans-serif;color:var(--navy);font-size:28px;margin-bottom:20px}}
  .facts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-top:24px}}
  .fact{{background:var(--light);padding:20px;border-radius:8px;text-align:center}}
  .fact .label{{font-size:13px;text-transform:uppercase;color:#666;letter-spacing:.5px}}
  .fact .value{{font-size:22px;font-weight:700;color:var(--navy);margin-top:6px}}
  .agent-card{{background:linear-gradient(135deg,#fff,var(--light));border:2px solid var(--green);border-radius:12px;padding:32px;margin:48px 0;display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:center}}
  .agent-card img{{width:140px;height:140px;border-radius:50%;object-fit:cover;border:4px solid var(--green)}}
  .agent-card h3{{font-family:Montserrat;font-size:24px;color:var(--navy);margin-bottom:8px}}
  .agent-card .credential{{color:#555;font-size:14px;margin-bottom:8px}}
  .agent-card .lang{{color:var(--green);font-weight:600;margin-bottom:16px}}
  .cta-row{{display:flex;gap:12px;flex-wrap:wrap}}
  .btn{{display:inline-block;padding:12px 24px;border-radius:6px;font-weight:600;font-size:15px}}
  .btn-primary{{background:var(--green);color:#fff}}
  .btn-primary:hover{{background:#008a44;color:#fff}}
  .btn-secondary{{background:var(--navy);color:#fff}}
  .btn-secondary:hover{{background:var(--dark-navy);color:#fff}}
  .nearby{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:24px}}
  .nearby a{{display:block;padding:18px 20px;background:var(--light);border-radius:8px;font-weight:600;color:var(--navy);transition:all .2s}}
  .nearby a:hover{{background:var(--green);color:#fff;transform:translateY(-2px)}}
  ul.things{{list-style:none;padding:0}}
  ul.things li{{padding:14px 18px;border-left:3px solid var(--green);background:var(--light);margin-bottom:12px;border-radius:0 6px 6px 0}}
  ul.things li strong{{color:var(--navy)}}
  footer{{background:var(--dark-navy);color:rgba(255,255,255,.85);padding:48px 0 24px;font-size:13px}}
  footer h4{{color:#fff;margin-bottom:12px;font-family:Montserrat;font-size:14px;text-transform:uppercase;letter-spacing:1px}}
  footer p{{margin-bottom:8px;line-height:1.7}}
  footer a{{color:rgba(255,255,255,.85)}} footer a:hover{{color:var(--green)}}
  .footer-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:32px;margin-bottom:32px}}
  .legal{{font-size:11px;opacity:.7;border-top:1px solid rgba(255,255,255,.15);padding-top:20px;line-height:1.6}}
  @media(max-width:640px){{
    nav a{{margin-left:12px;font-size:13px}}
    .agent-card{{grid-template-columns:1fr;text-align:center}}
    .agent-card img{{margin:0 auto}}
  }}
</style>
</head>
<body data-page-type="{page_type}" data-location="{location_name}">

<header>
  <div class="container header-inner">
    <a href="/" class="logo">Gadura Real Estate</a>
    <nav>
      <a href="/buy.html">Buy</a>
      <a href="/sell.html">Sell</a>
      <a href="/neighborhoods/">Neighborhoods</a>
      <a href="/meet-the-agents.html">Agents</a>
      <a href="tel:+19177050132">(917) 705-0132</a>
    </nav>
  </div>
</header>

<section class="hero">
  <div class="container">
    <h1>{h1}</h1>
    <p class="lede">{lede}</p>
  </div>
</section>

<div class="container">
  <div class="answer-first">
    <strong>Looking for a real estate agent in {location_name}?</strong> Nitin Gadura of Gadura Real Estate LLC is a Licensed New York State Real Estate Salesperson serving {location_name} and the surrounding {borough_name} area. With a 4.9-star rating across 57+ verified reviews, fluency in English, Hindi, Punjabi, and Guyanese Creole, and 18 years of family-owned brokerage experience based in Ozone Park, Nitin handles {primary_services} for {location_name} buyers, sellers, and investors. Call <a href="tel:+19177050132"><strong>(917) 705-0132</strong></a> for a free consultation.
  </div>

  <section>
    <h2>{location_name} at a Glance</h2>
    <div class="facts">
      <div class="fact"><div class="label">Borough / County</div><div class="value">{borough_name}</div></div>
      <div class="fact"><div class="label">ZIP Code{zip_plural}</div><div class="value">{zips_display}</div></div>
      <div class="fact"><div class="label">Median Home Price</div><div class="value">${median_display}</div></div>
      <div class="fact"><div class="label">Communities Served</div><div class="value">{communities_short}</div></div>
    </div>
  </section>

  <section>
    <h2>3 Things to Know About Buying or Selling in {location_name}</h2>
    <ul class="things">
      <li><strong>{thing1_title}.</strong> {thing1_body}</li>
      <li><strong>{thing2_title}.</strong> {thing2_body}</li>
      <li><strong>{thing3_title}.</strong> {thing3_body}</li>
    </ul>
  </section>

  <div class="agent-card">
    <img src="/images/nitin-gadura-headshot.jpg" alt="Nitin Gadura, Licensed NYS Real Estate Salesperson">
    <div>
      <h3>Nitin Gadura</h3>
      <div class="credential">Licensed New York State Real Estate Salesperson · Gadura Real Estate, LLC</div>
      <div class="lang">English · Hindi · Punjabi · Guyanese Creole</div>
      <p style="margin-bottom:18px;color:#555">Based in Ozone Park, serving all of {borough_name}{li_extra}. Free 30-minute consultation. Family-owned brokerage since 2006.</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="tel:+19177050132">📞 Call (917) 705-0132</a>
        <a class="btn btn-secondary" href="/contact.html">✉ Send a message</a>
      </div>
    </div>
  </div>

  <section>
    <h2>Browse Listings in {location_name}</h2>
    <p>Search live MLS listings filtered by {location_name} and surrounding ZIP codes:</p>
    <p style="margin-top:18px"><a class="btn btn-primary" href="https://homes.gadurarealestate.com/?cityID={location_name_url}" target="_blank" rel="noopener">View {location_name} listings on OneKey® MLS →</a></p>
  </section>

  <section>
    <h2>Nearby Neighborhoods</h2>
    <p>Explore other {borough_name} markets we serve:</p>
    <div class="nearby">
      {nearby_links}
    </div>
  </section>
</div>

<footer>
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>Gadura Real Estate, LLC</h4>
        <p>106-09 101st Ave, Ozone Park, NY 11416</p>
        <p><a href="tel:+19177050132">(917) 705-0132</a></p>
        <p><a href="mailto:Nitink.gadura@gmail.com">Nitink.gadura@gmail.com</a></p>
        <p>NYS Firm Broker License #10991238487</p>
        <p>Supervising Broker: Vinod K. Gadura</p>
      </div>
      <div>
        <h4>Service Areas</h4>
        <p><a href="/neighborhoods/">All Neighborhoods</a></p>
        <p><a href="/neighborhoods/queens.html">Queens</a> · <a href="/neighborhoods/brooklyn.html">Brooklyn</a></p>
        <p><a href="/neighborhoods/bronx.html">Bronx</a> · <a href="/neighborhoods/staten-island.html">Staten Island</a></p>
        <p><a href="/neighborhoods/manhattan.html">Manhattan</a></p>
        <p><a href="/long-island/nassau/">Nassau County</a> · <a href="/long-island/suffolk/">Suffolk County</a></p>
      </div>
      <div>
        <h4>Compliance</h4>
        <p><a href="/fair-housing.html">Equal Housing Opportunity</a></p>
        <p><a href="/agency-disclosure.html">NY Agency Disclosure</a></p>
        <p><a href="/standard-operating-procedures.html">Standard Operating Procedures</a></p>
        <p><a href="/privacy-policy.html">Privacy</a> · <a href="/terms.html">Terms</a></p>
        <p><a href="/dmca.html">DMCA</a> · <a href="/accessibility.html">Accessibility</a></p>
      </div>
    </div>
    <div class="legal">
      <p><strong>Gadura Real Estate, LLC</strong> is a NYS-licensed real estate brokerage (License #10991238487). Information deemed reliable but not guaranteed. Listing data displayed via the Internet Data Exchange (IDX) program of OneKey® MLS. Real estate listings held by brokerage firms other than Gadura Real Estate, LLC are marked with the OneKey® MLS logo. Equal Housing Opportunity. Commissions are negotiable and not set by law (19 NYCRR §175.7). Pursuant to the 2024 NAR settlement, written buyer-broker agreements are required prior to MLS-listed property tours. © 2026 Gadura Real Estate, LLC.</p>
    </div>
  </div>
</footer>

</body>
</html>
"""


THINGS_TEMPLATES = [
    {
        "title": "Local language matters",
        "body": "{location_name} is part of {borough_name}'s {community_phrase} corridor — a multilingual agent makes a real difference at the negotiation table and during family decision-making. Nitin Gadura speaks Hindi, Punjabi, and Guyanese Creole and our team also covers Bengali and Spanish.",
    },
    {
        "title": "Inventory moves fast",
        "body": "Median list-to-close in {location_name} runs roughly 30-45 days for well-priced homes. Buyers should be pre-approved with at least two lenders before touring, and sellers should commit to a pricing strategy within the first 14 days on market — that's where the bulk of qualified offers come in.",
    },
    {
        "title": "Know the financing options",
        "body": "FHA, conventional, SONYMA, HomeReady, and VA loans all work in {location_name} — but specific buildings (especially co-ops) accept some and not others. We pre-qualify the property AND the financing before writing offers.",
    },
    {
        "title": "School zoning matters more here",
        "body": "{borough_name} school zones can shift home values 10-20% within a few blocks. Before falling in love with a {location_name} listing, confirm the actual school assignment with the NYC Department of Education or the local Long Island school district.",
    },
    {
        "title": "Property taxes vary a lot",
        "body": "Property taxes in {location_name} can swing thousands of dollars year-to-year between similar homes due to assessment differences. Always pull the actual tax bill, not the listing's estimate, before submitting an offer.",
    },
    {
        "title": "Co-op vs condo vs single-family",
        "body": "{location_name} has a mix of single-family, multi-family, condo, and (in some buildings) co-op stock. Each structure has totally different financing, board approval, and resale rules. Know which you're shopping before touring — it changes everything.",
    },
    {
        "title": "Comparable sales are everything",
        "body": "Pricing a home in {location_name} requires three months of recent comps within 0.25 mi, adjusted for square footage, lot size, and condition. We send full comp sheets to every client at pre-listing and pre-offer — no guessing.",
    },
    {
        "title": "Negotiation room exists",
        "body": "List-to-sold ratio in {location_name} typically lands at 97-103% of asking, depending on cycle. There IS room to negotiate on the right listings — and there's no room at all on others. An experienced local agent reads the difference at first showing.",
    },
    {
        "title": "Inspection findings are normal",
        "body": "Most {location_name} homes are 50-100+ years old. Expect inspection findings — knob-and-tube wiring, oil tanks, roof age, sewer lines. The right response is repair credits, not deal collapse. We've negotiated through hundreds of inspection reports.",
    },
    {
        "title": "Closing costs add up",
        "body": "NY closing costs run 6-8% on the seller side (transfer tax, RPTT, attorney, title, prep) and 2-4% on the buyer side (mortgage tax, attorney, title insurance, lender fees). We send a transparent net-sheet to every {location_name} client before going to contract.",
    },
]


def fmt_median(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def slugify_url(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_nearby_links(current_slug: str, neighbors: list[dict], borough_slug: str, count: int = 6) -> str:
    others = [n for n in neighbors if n["slug"] != current_slug]
    chosen = others[:count] if len(others) >= count else others
    out = []
    for n in chosen:
        out.append(f'<a href="/neighborhoods/{borough_slug}/{n["slug"]}.html">{n["name"]}, {borough_slug.replace("-", " ").title()} →</a>')
    return "\n      ".join(out)


def build_li_nearby(current_slug: str, neighbors: list[dict], county_slug: str, count: int = 6) -> str:
    others = [n for n in neighbors if n["slug"] != current_slug]
    chosen = others[:count]
    out = []
    for n in chosen:
        out.append(f'<a href="/long-island/{county_slug}/{n["slug"]}.html">{n["name"]}, {county_slug.title()} →</a>')
    return "\n      ".join(out)


def render_neighborhood(
    nb: dict,
    borough_slug: str,
    borough_name: str,
    neighbors: list[dict],
    rel_url: str,
    page_type: str,
    is_long_island: bool,
    county_slug: str | None = None,
) -> str:
    name = nb["name"]
    slug = nb["slug"]
    zips = nb.get("zips", [])
    zips_display = " · ".join(zips) if zips else "Multiple"
    zip_plural = "s" if len(zips) > 1 else ""
    median = nb.get("median", 720000)
    communities = nb.get("communities", [])
    community_short = ", ".join(communities[:3]) if communities else "Diverse"
    community_phrase = f"{communities[0].lower()} community" if communities else "diverse local community"

    primary_services = "first-time homebuyer guidance, multi-family investment, co-op board packages, and 1031 exchanges"

    # Stable rotation for differentiated copy.
    h = abs(hash(slug)) % 10000
    t1 = THINGS_TEMPLATES[h % len(THINGS_TEMPLATES)]
    t2 = THINGS_TEMPLATES[(h + 3) % len(THINGS_TEMPLATES)]
    t3 = THINGS_TEMPLATES[(h + 7) % len(THINGS_TEMPLATES)]

    def fmt(t):
        return {
            "title": t["title"],
            "body": t["body"].format(
                location_name=name,
                borough_name=borough_name,
                community_phrase=community_phrase,
            ),
        }

    t1f, t2f, t3f = fmt(t1), fmt(t2), fmt(t3)

    title = f"{name} Real Estate Agent | Nitin Gadura | Gadura Real Estate"
    og_title = f"{name} Homes for Sale & Real Estate Agent | Nitin Gadura"
    h1 = f"{name} Real Estate — Buy or Sell with Nitin Gadura"

    lede_options = [
        f"Nitin Gadura at Gadura Real Estate LLC has been serving {name}, {borough_name} since 2006. Free consultation in English, Hindi, Punjabi, or Guyanese Creole.",
        f"Looking to buy, sell, or invest in {name}, {borough_name}? Nitin Gadura at Gadura Real Estate is a 4.9-star NYS-licensed agent who knows the corridor.",
        f"{name} buyers and sellers — Nitin Gadura, Gadura Real Estate LLC, NYS-licensed since 2006. Multilingual representation across {borough_name}.",
    ]
    lede = lede_options[h % len(lede_options)]

    meta_desc = f"Nitin Gadura — Licensed NYS real estate agent serving {name}, {borough_name}. Median ${fmt_median(median)}. Hindi, Punjabi, Guyanese Creole spoken. Call (917) 705-0132. 4.9 stars across 57+ reviews."

    li_extra = " and Long Island" if not is_long_island else ", Queens, and Long Island"

    if is_long_island and county_slug:
        nearby_links = build_li_nearby(slug, neighbors, county_slug)
    else:
        nearby_links = build_nearby_links(slug, neighbors, borough_slug)

    return PAGE_TEMPLATE.format(
        title=title,
        og_title=og_title,
        meta_desc=meta_desc,
        rel_url=rel_url,
        h1=h1,
        lede=lede,
        location_name=name,
        location_name_url=name.replace(" ", "+"),
        borough_name=borough_name,
        primary_services=primary_services,
        zips_display=zips_display,
        zip_plural=zip_plural,
        median_display=fmt_median(median),
        communities_short=community_short,
        community_phrase=community_phrase,
        thing1_title=t1f["title"],
        thing1_body=t1f["body"],
        thing2_title=t2f["title"],
        thing2_body=t2f["body"],
        thing3_title=t3f["title"],
        thing3_body=t3f["body"],
        nearby_links=nearby_links,
        page_type=page_type,
        li_extra=li_extra,
    )


def render_zip_page(zip_code: str, locations_for_zip: list[tuple[str, str, dict]]) -> str:
    """locations_for_zip: list of (borough_slug, borough_name, neighborhood_dict) tuples."""
    primary = locations_for_zip[0]
    borough_slug, borough_name, primary_nb = primary
    name = f"ZIP {zip_code}"
    location_label = f"{primary_nb['name']}, {borough_name}"

    serves_list = ", ".join(f"{lb[2]['name']}, {lb[1]}" for lb in locations_for_zip)
    median = primary_nb.get("median", 720000)
    communities = primary_nb.get("communities", [])

    h1 = f"ZIP {zip_code} Real Estate — {primary_nb['name']}, {borough_name}"
    lede = f"Nitin Gadura at Gadura Real Estate LLC serves ZIP {zip_code} ({serves_list}). Multilingual NYS-licensed agent, family-owned brokerage since 2006."
    title = f"ZIP {zip_code} Real Estate Agent | {primary_nb['name']} | Gadura Real Estate"
    og_title = f"ZIP {zip_code} Homes & Real Estate Agent | Nitin Gadura"
    meta_desc = f"Real estate agent serving ZIP {zip_code} ({serves_list}). Nitin Gadura, Gadura Real Estate LLC. Median ${fmt_median(median)}. (917) 705-0132."

    nearby = []
    for lb in locations_for_zip[:6]:
        b_slug, b_name, n = lb
        if b_slug in ("nassau", "suffolk"):
            href = f"/long-island/{b_slug}/{n['slug']}.html"
        else:
            href = f"/neighborhoods/{b_slug}/{n['slug']}.html"
        nearby.append(f'<a href="{href}">{n["name"]}, {b_name} →</a>')
    nearby_links = "\n      ".join(nearby) if nearby else f'<a href="/neighborhoods/{borough_slug}/{primary_nb["slug"]}.html">{primary_nb["name"]} →</a>'

    rel_url = f"zip/{zip_code}.html"

    primary_services = "first-time homebuyers, sellers, multi-family investors, and 1031 exchange clients"

    h_seed = abs(hash(zip_code)) % 10000
    t1 = THINGS_TEMPLATES[h_seed % len(THINGS_TEMPLATES)]
    t2 = THINGS_TEMPLATES[(h_seed + 3) % len(THINGS_TEMPLATES)]
    t3 = THINGS_TEMPLATES[(h_seed + 7) % len(THINGS_TEMPLATES)]

    def fmtt(t):
        return {
            "title": t["title"],
            "body": t["body"].format(
                location_name=f"ZIP {zip_code}",
                borough_name=borough_name,
                community_phrase=(communities[0].lower() + " community") if communities else "diverse local community",
            ),
        }

    t1f, t2f, t3f = fmtt(t1), fmtt(t2), fmtt(t3)

    return PAGE_TEMPLATE.format(
        title=title,
        og_title=og_title,
        meta_desc=meta_desc,
        rel_url=rel_url,
        h1=h1,
        lede=lede,
        location_name=f"ZIP {zip_code}",
        location_name_url=zip_code,
        borough_name=borough_name,
        primary_services=primary_services,
        zips_display=zip_code,
        zip_plural="",
        median_display=fmt_median(median),
        communities_short=", ".join(communities[:3]) if communities else "Diverse",
        community_phrase=(communities[0].lower() + " community") if communities else "diverse local community",
        thing1_title=t1f["title"],
        thing1_body=t1f["body"],
        thing2_title=t2f["title"],
        thing2_body=t2f["body"],
        thing3_title=t3f["title"],
        thing3_body=t3f["body"],
        nearby_links=nearby_links,
        page_type="zip",
        li_extra=", Queens, and Long Island",
    )


def render_borough_hub(borough_slug: str, borough_name: str, neighborhoods: list[dict], rel_url: str) -> str:
    cards = []
    for n in neighborhoods:
        cards.append(
            f'<a href="/neighborhoods/{borough_slug}/{n["slug"]}.html"><strong>{n["name"]}</strong><br>'
            f'<span style="color:#666;font-size:13px">${fmt_median(n.get("median", 720000))} median · '
            f'{" · ".join(n.get("zips", [])[:2])}</span></a>'
        )
    nearby_links = "\n      ".join(cards)

    h1 = f"{borough_name} Real Estate — Every Neighborhood, One Local Agent"
    lede = f"Nitin Gadura serves all of {borough_name} from Gadura Real Estate's Ozone Park office. Browse {len(neighborhoods)} {borough_name} neighborhoods below."
    title = f"{borough_name} Real Estate Agent | Nitin Gadura | All Neighborhoods"
    meta_desc = f"Real estate agent serving every {borough_name} neighborhood. Nitin Gadura at Gadura Real Estate LLC, NYS-licensed, multilingual, 4.9 stars. (917) 705-0132."

    h_seed = abs(hash(borough_slug)) % 10000
    t1 = THINGS_TEMPLATES[h_seed % len(THINGS_TEMPLATES)]
    t2 = THINGS_TEMPLATES[(h_seed + 3) % len(THINGS_TEMPLATES)]
    t3 = THINGS_TEMPLATES[(h_seed + 7) % len(THINGS_TEMPLATES)]

    def fmtt(t):
        return {
            "title": t["title"],
            "body": t["body"].format(
                location_name=borough_name,
                borough_name=borough_name,
                community_phrase="diverse local community",
            ),
        }

    t1f, t2f, t3f = fmtt(t1), fmtt(t2), fmtt(t3)

    primary_services = "first-time homebuyer guidance, multi-family investment, co-op board packages, and 1031 exchanges"

    return PAGE_TEMPLATE.format(
        title=title,
        og_title=title,
        meta_desc=meta_desc,
        rel_url=rel_url,
        h1=h1,
        lede=lede,
        location_name=borough_name,
        location_name_url=borough_name.replace(" ", "+"),
        borough_name=borough_name,
        primary_services=primary_services,
        zips_display="Multiple",
        zip_plural="s",
        median_display=fmt_median(720000),
        communities_short="All",
        community_phrase="diverse local community",
        thing1_title=t1f["title"],
        thing1_body=t1f["body"],
        thing2_title=t2f["title"],
        thing2_body=t2f["body"],
        thing3_title=t3f["title"],
        thing3_body=t3f["body"],
        nearby_links=nearby_links,
        page_type="borough_hub",
        li_extra=", Queens, and Long Island",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    counts = {"created": 0, "skipped": 0, "overwritten": 0}

    # Collect unique ZIPs across all locations.
    zip_index: dict[str, list[tuple[str, str, dict]]] = {}

    # NYC boroughs
    for borough_slug, borough in data["boroughs"].items():
        borough_name = borough["name"]
        nbs = borough["neighborhoods"]
        # Borough hub
        hub_path = ROOT / "neighborhoods" / f"{borough_slug}.html"
        hub_html = render_borough_hub(borough_slug, borough_name, nbs, f"neighborhoods/{borough_slug}.html")
        if not hub_path.exists() or args.force:
            if args.apply:
                hub_path.parent.mkdir(parents=True, exist_ok=True)
                hub_path.write_text(hub_html, encoding="utf-8")
            counts["overwritten" if hub_path.exists() else "created"] += 1
        else:
            counts["skipped"] += 1

        # Each neighborhood page
        nb_dir = ROOT / "neighborhoods" / borough_slug
        for nb in nbs:
            nb_path = nb_dir / f"{nb['slug']}.html"
            html = render_neighborhood(
                nb, borough_slug, borough_name, nbs,
                rel_url=f"neighborhoods/{borough_slug}/{nb['slug']}.html",
                page_type="neighborhood",
                is_long_island=False,
            )
            if not nb_path.exists() or args.force:
                if args.apply:
                    nb_path.parent.mkdir(parents=True, exist_ok=True)
                    nb_path.write_text(html, encoding="utf-8")
                counts["overwritten" if nb_path.exists() else "created"] += 1
            else:
                counts["skipped"] += 1
            for z in nb.get("zips", []):
                zip_index.setdefault(z, []).append((borough_slug, borough_name, nb))

    # Long Island
    for county_slug, county in data["long_island"].items():
        county_name = county["name"]
        nbs = county["neighborhoods"]
        # County hub
        hub_path = ROOT / "long-island" / county_slug / "index.html"
        hub_html = render_borough_hub(county_slug, county_name, nbs, f"long-island/{county_slug}/")
        if not hub_path.exists() or args.force:
            if args.apply:
                hub_path.parent.mkdir(parents=True, exist_ok=True)
                hub_path.write_text(hub_html, encoding="utf-8")
            counts["overwritten" if hub_path.exists() else "created"] += 1
        else:
            counts["skipped"] += 1
        # Each LI neighborhood
        for nb in nbs:
            nb_path = ROOT / "long-island" / county_slug / f"{nb['slug']}.html"
            html = render_neighborhood(
                nb, county_slug, county_name, nbs,
                rel_url=f"long-island/{county_slug}/{nb['slug']}.html",
                page_type="long_island_neighborhood",
                is_long_island=True,
                county_slug=county_slug,
            )
            if not nb_path.exists() or args.force:
                if args.apply:
                    nb_path.parent.mkdir(parents=True, exist_ok=True)
                    nb_path.write_text(html, encoding="utf-8")
                counts["overwritten" if nb_path.exists() else "created"] += 1
            else:
                counts["skipped"] += 1
            for z in nb.get("zips", []):
                zip_index.setdefault(z, []).append((county_slug, county_name, nb))

    # ZIP-code pages
    zip_dir = ROOT / "zip"
    for z, locs in zip_index.items():
        zip_path = zip_dir / f"{z}.html"
        html = render_zip_page(z, locs)
        if not zip_path.exists() or args.force:
            if args.apply:
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                zip_path.write_text(html, encoding="utf-8")
            counts["overwritten" if zip_path.exists() else "created"] += 1
        else:
            counts["skipped"] += 1

    print("=== Generation report ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"  unique ZIPs covered: {len(zip_index)}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
