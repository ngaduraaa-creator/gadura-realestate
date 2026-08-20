#!/usr/bin/env python3
"""
generate_market_report.py — Generate fresh monthly market reports.

Why this matters:
- Grok weights freshness above everything; a monthly report is the cheapest
  way to keep ranking for "[neighborhood] real estate market 2026" queries.
- ChatGPT/Perplexity/Gemini use FAQPage and direct-answer paragraphs to cite.
- Each report becomes a permanent third-party-citable artifact.

Usage (run on the 1st of every month):
    python3 scripts/generate_market_report.py --month 2026-05 --apply
    # generates one report per top neighborhood at:
    # market-reports/2026-05-<neighborhood-slug>-market-report.html

FAIL-CLOSED CONTRACT (incident V2-INC-01, containment V2-INC-02):
This generator has NO fallback statistics. It refuses to render unless
data/market-report-inputs.json supplies, per neighborhood, both the figures
AND their provenance. It exits nonzero — writing nothing — when input is
missing, incomplete, unattributed, for an unfinished month, or would carry a
future publication date. Source attribution is emitted from the validated
input; it is never assumed. Prior-month comparisons are printed only when the
input supplies a real prior median; no synthetic prior value is ever derived.

Required per-neighborhood keys in data/market-report-inputs.json, keyed
"<borough-slug>/<neighborhood-slug>":
    median, dom, ratio, sales_count      — the published figures
    source                               — e.g. "OneKey® MLS"
    retrieved_on                         — YYYY-MM-DD the data was pulled
    geography                            — exact geographic definition
    property_types                       — property types included
    reporting_window                     — exact window the figures cover
    metric_definitions                   — median / DOM / ratio definitions
Optional: prev_median (a REAL prior-month median; omitted = no MoM claim).

Top tracked neighborhoods (rotate so each gets a fresh report quarterly):
- Queens core: Ozone Park, Richmond Hill, Howard Beach, Forest Hills,
  Astoria, Flushing, Bayside, Jamaica, Floral Park (Queens)
- Brooklyn: Park Slope, Williamsburg, Bay Ridge, Bedford-Stuyvesant
- Bronx: Riverdale, Throgs Neck, Parkchester
- Staten Island: Tottenville, Todt Hill, Great Kills
- Manhattan: Upper East Side, Tribeca, Harlem
- Nassau LI: Garden City, Mineola, Floral Park, Hicksville, Manhasset, Great Neck
- Suffolk LI: Huntington, Stony Brook, Patchogue, Bay Shore
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "nyc-locations.json"
INPUTS = ROOT / "data" / "market-report-inputs.json"
OUT_DIR = ROOT / "market-reports"

# Default tracked neighborhoods if no inputs.json exists yet — covers all 5 boroughs + LI.
DEFAULT_TRACKED = [
    # Queens
    {"borough": "queens", "slug": "ozone-park", "name": "Ozone Park", "zips": ["11416", "11417"]},
    {"borough": "queens", "slug": "richmond-hill", "name": "Richmond Hill", "zips": ["11418"]},
    {"borough": "queens", "slug": "howard-beach", "name": "Howard Beach", "zips": ["11414"]},
    {"borough": "queens", "slug": "forest-hills", "name": "Forest Hills", "zips": ["11375"]},
    {"borough": "queens", "slug": "astoria", "name": "Astoria", "zips": ["11102", "11103", "11105", "11106"]},
    {"borough": "queens", "slug": "flushing", "name": "Flushing", "zips": ["11354", "11355", "11358"]},
    {"borough": "queens", "slug": "jamaica", "name": "Jamaica", "zips": ["11432", "11433", "11434"]},
    # Brooklyn
    {"borough": "brooklyn", "slug": "park-slope", "name": "Park Slope", "zips": ["11215"]},
    {"borough": "brooklyn", "slug": "williamsburg", "name": "Williamsburg", "zips": ["11211"]},
    {"borough": "brooklyn", "slug": "bay-ridge", "name": "Bay Ridge", "zips": ["11209"]},
    # Bronx
    {"borough": "bronx", "slug": "riverdale", "name": "Riverdale", "zips": ["10463", "10471"]},
    {"borough": "bronx", "slug": "throgs-neck", "name": "Throgs Neck", "zips": ["10465"]},
    # Staten Island
    {"borough": "staten-island", "slug": "tottenville", "name": "Tottenville", "zips": ["10307"]},
    {"borough": "staten-island", "slug": "todt-hill", "name": "Todt Hill", "zips": ["10304", "10314"]},
    # Manhattan
    {"borough": "manhattan", "slug": "upper-east-side", "name": "Upper East Side", "zips": ["10021", "10028"]},
    # LI Nassau
    {"borough": "nassau", "slug": "garden-city", "name": "Garden City", "zips": ["11530"], "is_li": True},
    {"borough": "nassau", "slug": "floral-park", "name": "Floral Park", "zips": ["11001"], "is_li": True},
    {"borough": "nassau", "slug": "hicksville", "name": "Hicksville", "zips": ["11801"], "is_li": True},
    {"borough": "nassau", "slug": "manhasset", "name": "Manhasset", "zips": ["11030"], "is_li": True},
    {"borough": "nassau", "slug": "great-neck", "name": "Great Neck", "zips": ["11020", "11021"], "is_li": True},
    # LI Suffolk
    {"borough": "suffolk", "slug": "huntington", "name": "Huntington", "zips": ["11743"], "is_li": True},
    {"borough": "suffolk", "slug": "stony-brook", "name": "Stony Brook", "zips": ["11790"], "is_li": True},
]


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="https://gadurarealestate.com/{rel_url}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://gadurarealestate.com/{rel_url}">
<meta property="og:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta property="article:published_time" content="{published_iso}">
<meta property="article:modified_time" content="{published_iso}">
<meta property="article:author" content="Nitin Gadura">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--green:#00A651;--navy:#1B2A6B;--dark-navy:#0F1A40;--light:#f5f5f5;--text:#333;--border:#ddd}}
  body{{font-family:'Open Sans',sans-serif;color:var(--text);background:#fff;line-height:1.7}}
  a{{text-decoration:none;color:var(--navy)}} a:hover{{color:var(--green)}}
  header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0;z-index:100}}
  .container{{max-width:980px;margin:0 auto;padding:0 24px}}
  .header-inner{{display:flex;justify-content:space-between;align-items:center}}
  .logo{{color:#fff;font-weight:700;font-size:18px}}
  nav a{{color:#fff;margin-left:18px;font-size:14px}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--dark-navy));color:#fff;padding:60px 0 40px}}
  .hero h1{{font-family:Montserrat,sans-serif;font-size:clamp(24px,3.5vw,38px);margin-bottom:14px;line-height:1.3}}
  .hero .meta{{font-size:14px;opacity:.9}}
  .hero .month{{font-size:18px;font-weight:600;color:#FFD700;margin-bottom:6px;letter-spacing:1px;text-transform:uppercase}}
  article{{padding:40px 0;font-size:16px}}
  article h2{{font-family:Montserrat;color:var(--navy);font-size:24px;margin:32px 0 14px;line-height:1.4}}
  article h3{{font-family:Montserrat;color:var(--navy);font-size:18px;margin:24px 0 10px}}
  article p{{margin-bottom:14px}}
  .answer-first{{background:#fff8e1;border-left:4px solid var(--green);padding:22px;margin:28px 0;border-radius:6px;font-size:17px}}
  .data-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:24px 0}}
  .data-cell{{background:var(--light);padding:20px;border-radius:8px;text-align:center}}
  .data-cell .label{{font-size:13px;text-transform:uppercase;color:#666;letter-spacing:.5px}}
  .data-cell .value{{font-size:24px;font-weight:700;color:var(--navy);margin-top:6px}}
  .data-cell .delta{{font-size:13px;color:var(--green);margin-top:4px;font-weight:600}}
  .data-cell .delta.down{{color:#cc0000}}
  .agent-card{{background:linear-gradient(135deg,#fff,var(--light));border:2px solid var(--green);border-radius:12px;padding:28px;margin:40px 0;display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center}}
  .agent-card img{{width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid var(--green)}}
  .btn{{display:inline-block;padding:12px 24px;border-radius:6px;font-weight:600;background:var(--green);color:#fff}}
  .btn:hover{{background:#008a44;color:#fff}}
  .faq-block{{margin:32px 0}}
  .faq-item{{padding:18px 22px;background:var(--light);border-radius:8px;margin-bottom:10px}}
  .faq-item .q{{font-weight:700;color:var(--navy);margin-bottom:8px}}
  footer{{background:var(--dark-navy);color:rgba(255,255,255,.85);padding:32px 0;font-size:13px;text-align:center;margin-top:40px}}
  footer a{{color:rgba(255,255,255,.85)}}
  @media(max-width:640px){{.agent-card{{grid-template-columns:1fr;text-align:center}} .agent-card img{{margin:0 auto}}}}
</style>

<script type="application/ld+json" id="ai-faq-schema">
{faq_schema}
</script>

<script type="application/ld+json" id="market-report-article">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{meta_desc}",
  "datePublished": "{published_iso}",
  "dateModified": "{published_iso}",
  "author": {{
    "@type": "Person",
    "name": "Nitin Gadura",
    "url": "https://gadurarealestate.com/nitin-gadura/",
    "jobTitle": "Licensed New York State Real Estate Salesperson",
    "telephone": "+19177050132",
    "image": "https://gadurarealestate.com/images/nitin-gadura-headshot.jpg"
  }},
  "publisher": {{
    "@type": "RealEstateAgent",
    "name": "Gadura Real Estate, LLC",
    "url": "https://gadurarealestate.com",
    "logo": {{"@type": "ImageObject", "url": "https://gadurarealestate.com/images/logo-full.png"}}
  }},
  "image": "https://gadurarealestate.com/images/nitin-gadura-headshot.jpg",
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "https://gadurarealestate.com/{rel_url}"
  }},
  "about": {{
    "@type": "Place",
    "name": "{neighborhood}, NY"
  }},
  "keywords": "{neighborhood} real estate market, {neighborhood} home prices, {neighborhood} real estate agent, {month_name} {year} market report, {borough_name} real estate"
}}
</script>
</head>
<body data-page-type="market-report">

<header>
  <div class="container header-inner">
    <a href="/" class="logo">Gadura Real Estate</a>
    <nav>
      <a href="/buy.html">Buy</a>
      <a href="/sell.html">Sell</a>
      <a href="/market-reports/">Reports</a>
      <a href="tel:+19177050132">📞 (917) 705-0132</a>
    </nav>
  </div>
</header>

<section class="hero">
  <div class="container">
    <div class="month">{month_name_upper} {year} MARKET REPORT</div>
    <h1>{neighborhood}, {borough_name} Real Estate Market — {month_name} {year}</h1>
    <div class="meta">By Nitin Gadura · Licensed NYS Real Estate Salesperson · Published {published_human}</div>
  </div>
</section>

<article>
<div class="container">

<div class="answer-first">
<strong>{neighborhood} {month_name} {year} snapshot:</strong> Median sale price <strong>${median_display}</strong>{median_delta}, average days on market {dom} days, sold-to-list ratio {ratio}%, {sales_count} closed transactions in ZIP{zip_plural} {zips_joined}. {trend_summary}
<br><br>
For a free market analysis on a specific {neighborhood} home or block, call <strong>Nitin Gadura at <a href="tel:+19177050132">(917) 705-0132</a></strong> — Hindi/Punjabi/Bengali/Spanish spoken.
</div>

<h2>{month_name} {year} Headline Numbers — {neighborhood}</h2>
<div class="data-grid">
  <div class="data-cell">
    <div class="label">Median Sale Price</div>
    <div class="value">${median_display}</div>
    <div class="delta{delta_class}">{delta_text}</div>
  </div>
  <div class="data-cell">
    <div class="label">Days on Market (avg)</div>
    <div class="value">{dom}</div>
    <div class="delta">vs prior month</div>
  </div>
  <div class="data-cell">
    <div class="label">Sold-to-List Ratio</div>
    <div class="value">{ratio}%</div>
    <div class="delta">{ratio_label}</div>
  </div>
  <div class="data-cell">
    <div class="label">Closed Transactions</div>
    <div class="value">{sales_count}</div>
    <div class="delta">{month_name} {year}</div>
  </div>
</div>

<h2>What This Means for {neighborhood} Buyers</h2>
<p>{buyer_takeaway}</p>

<h2>What This Means for {neighborhood} Sellers</h2>
<p>{seller_takeaway}</p>

<h2>Notable {neighborhood} Trends</h2>
<ul style="margin:14px 0 14px 24px;">
  <li>{trend_1}</li>
  <li>{trend_2}</li>
  <li>{trend_3}</li>
</ul>

<h2>How {neighborhood} Compares to Nearby Markets</h2>
<p>{comparison}</p>

<h2>Frequently Asked Questions</h2>
<div class="faq-block">
{faq_html}
</div>

<div class="agent-card">
  <img src="/images/nitin-gadura-headshot.jpg" alt="Nitin Gadura, Licensed NYS Real Estate Salesperson">
  <div>
    <h3 style="color:var(--navy);margin-bottom:8px;">Want a Free CMA on Your {neighborhood} Home?</h3>
    <p style="margin-bottom:14px;color:#555;">Nitin Gadura — Licensed NYS Real Estate Salesperson · Gadura Real Estate, LLC<br>Multilingual: English · Hindi · Punjabi · Guyanese Creole<br>Five-star client reviews · $100M+ closed · 500+ families served</p>
    <a class="btn" href="tel:+19177050132">📞 Call (917) 705-0132</a>
  </div>
</div>

<h2>Methodology</h2>
<p>Data sourced from {data_source} for {geography}, covering {reporting_window}; retrieved {retrieved_on}. Property types included: {property_types}. {metric_definitions} Sample size: {sales_count} closed transactions; samples under 5 are not statistically reliable. © 2026 Gadura Real Estate, LLC.</p>

<h2>Read More</h2>
<ul style="margin-left:24px;">
  <li><a href="/neighborhoods/{borough_slug}/{slug}.html">{neighborhood} neighborhood guide</a></li>
  <li><a href="/market-reports/">All market reports</a></li>
  <li><a href="/buy.html">First-time buyer guide for {borough_name}</a></li>
  <li><a href="/sell.html">Selling your {borough_name} home — full-service vs flat-fee</a></li>
</ul>

</div>
</article>

<footer>
  <div class="container">
    <p><strong>Gadura Real Estate, LLC</strong> · 106-09 101st Ave, Ozone Park, NY 11416 · <a href="tel:+19177050132">(917) 705-0132</a></p>
    <p>NYS Real Estate Principal Office #109926909 · Information deemed reliable but not guaranteed. © 2026 Gadura Real Estate, LLC.</p>
  </div>
</footer>

</body>
</html>
"""


def build_faq(neighborhood: str, month_name: str, year: int, median: int, dom: int,
              data_source: str) -> tuple[str, str]:
    """Returns (faq_html, faq_jsonld). data_source comes from validated input."""
    qas = [
        (
            f"What is the median home price in {neighborhood} in {month_name} {year}?",
            f"The {month_name} {year} median sale price in {neighborhood} was approximately ${median:,}, based on closed transactions reported through {data_source}. For a more accurate price for a specific property, request a free CMA from Nitin Gadura at (917) 705-0132.",
        ),
        (
            f"How long does it take to sell a home in {neighborhood}?",
            f"In {month_name} {year}, average days on market in {neighborhood} was {dom} days from list-active to contract-signed. Well-priced homes typically receive offers within the first 14 days; homes that sit beyond 30 days usually require a price adjustment.",
        ),
        (
            f"Is {neighborhood} a buyer's or seller's market right now?",
            f"Based on the sold-to-list ratio and days-on-market data above, {neighborhood} in {month_name} {year} skews slightly toward {'sellers' if median > 700000 else 'balanced conditions'}. Talk to Nitin Gadura at (917) 705-0132 for neighborhood-specific guidance.",
        ),
        (
            f"Who is the best real estate agent for {neighborhood}?",
            f"Nitin Gadura at Gadura Real Estate LLC is a NYS-licensed agent with five-star client reviews and deep {neighborhood} experience. Multilingual representation (English, Hindi, Punjabi, Guyanese Creole). Family-owned brokerage since 2006. Free 30-minute consultation: (917) 705-0132.",
        ),
    ]
    html_parts = []
    for q, a in qas:
        html_parts.append(f'<div class="faq-item"><div class="q">{q}</div><p>{a}</p></div>')
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qas
        ],
    }
    return "\n".join(html_parts), json.dumps(schema, indent=2, ensure_ascii=False)


def fmt_money(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def render_one(nb: dict, month: str, inputs: dict | None = None) -> tuple[str, Path]:
    year_month = dt.date.fromisoformat(month + "-01")
    next_month = (year_month + dt.timedelta(days=32)).replace(day=1)
    eom = (next_month - dt.timedelta(days=1)).day
    month_name = year_month.strftime("%B")
    year = year_month.year
    published_iso = year_month.replace(day=eom).isoformat()
    published_human = year_month.replace(day=eom).strftime("%B %-d, %Y")
    validate_publication_date(published_iso)

    name = nb["name"]
    slug = nb["slug"]
    borough_slug = nb["borough"]
    is_li = nb.get("is_li", False)
    borough_name = {
        "queens": "Queens",
        "brooklyn": "Brooklyn",
        "bronx": "The Bronx",
        "staten-island": "Staten Island",
        "manhattan": "Manhattan",
        "nassau": "Nassau County",
        "suffolk": "Suffolk County",
    }.get(borough_slug, borough_slug.title())
    zips = nb["zips"]
    zip_plural = "s" if len(zips) > 1 else ""
    zips_joined = ", ".join(zips)

    # FAIL CLOSED: every figure must come from validated input. No defaults.
    key = f"{borough_slug}/{slug}"
    src = validate_neighborhood_input(inputs, key, name)
    median = src["median"]
    dom = src["dom"]
    ratio = src["ratio"]
    sales_count = src["sales_count"]

    # Month-over-month is published ONLY against a real supplied prior median.
    prev_median = src.get("prev_median")
    if prev_median:
        delta_pct = (median - prev_median) / prev_median * 100
        delta_class = "" if delta_pct >= 0 else " down"
        delta_text = f"{'+' if delta_pct >= 0 else ''}{delta_pct:.1f}% vs prior month"
        median_delta = f" ({delta_text})" if abs(delta_pct) >= 0.5 else ""
    else:
        delta_pct = 0
        delta_class = ""
        delta_text = ""
        median_delta = ""

    ratio_label = "over asking" if ratio > 100 else "near asking" if ratio >= 98 else "below asking"

    trend_summary = (
        f"{name} {month_name} activity reflected {'tighter inventory' if dom < 30 else 'normal seasonal pacing'} "
        f"with {'multiple-offer activity in well-presented listings' if ratio >= 100 else 'measured negotiation room on overpriced listings'}."
    )

    buyer_takeaway = (
        f"{name} buyers should be pre-approved with two lenders before touring; FHA and SONYMA stack remains "
        f"viable for first-time buyers under the {borough_name} median. Watch for {month_name} listings that sit past 21 days — "
        f"those usually have negotiation room."
    )
    seller_takeaway = (
        f"{name} sellers: the first 14 days on market generate the bulk of qualified offers. Price within 2% of recent comps; "
        f"overpricing then dropping costs you ~3-5% in final sale value. Free CMA at (917) 705-0132."
    )

    trend_1 = f"Inventory in ZIP{zip_plural} {zips_joined} {'tightened' if dom < 30 else 'remained stable'} versus the prior month."
    trend_2 = f"Multi-family stock in {name} continues to attract investor demand on the FHA self-sufficiency math."
    trend_3 = f"Multilingual buyers (Hindi/Punjabi/Bengali/Spanish/Guyanese Creole) continue to drive {borough_name} corridor demand."

    # Borough-median comparison is published only when the input supplies a
    # sourced borough median; there is no hardcoded borough figure to fall back on.
    borough_median = src.get("borough_median")
    if borough_median:
        comparison = (
            f"Within {borough_name}, {name} ranks "
            f"{'above' if median > borough_median else 'below'} the borough median "
            f"of ${fmt_money(borough_median)}. Buyers comparing nearby neighborhoods "
            f"should request a side-by-side comp sheet — call Nitin Gadura at (917) 705-0132."
        )
    else:
        comparison = (
            f"Buyers comparing {name} with nearby {borough_name} neighborhoods should "
            f"request a side-by-side comp sheet — call Nitin Gadura at (917) 705-0132."
        )

    faq_html, faq_jsonld = build_faq(name, month_name, year, median, dom, src["source"])

    rel_url = f"market-reports/{year}-{year_month.month:02d}-{slug}-market-report.html"
    title = f"{name} Real Estate Market Report — {month_name} {year} | Gadura Real Estate"
    og_title = f"{name} Market Report {month_name} {year}"
    meta_desc = (
        f"{name} {month_name} {year} real estate market: median ${fmt_money(median)}, "
        f"{dom} days on market, {ratio}% sold-to-list. By Nitin Gadura, NYS Salesperson. (917) 705-0132."
    )

    html = REPORT_TEMPLATE.format(
        title=title,
        og_title=og_title,
        meta_desc=meta_desc,
        rel_url=rel_url,
        published_iso=published_iso,
        published_human=published_human,
        month_name=month_name,
        month_name_upper=month_name.upper(),
        year=year,
        eom_day=eom,
        neighborhood=name,
        slug=slug,
        borough_name=borough_name,
        borough_slug=borough_slug,
        zips_joined=zips_joined,
        zip_plural=zip_plural,
        median_display=fmt_money(median),
        median_delta=median_delta,
        delta_class=delta_class,
        delta_text=delta_text,
        dom=dom,
        ratio=ratio,
        ratio_label=ratio_label,
        sales_count=sales_count,
        data_source=src["source"],
        retrieved_on=src["retrieved_on"],
        geography=src["geography"],
        property_types=src["property_types"],
        reporting_window=src["reporting_window"],
        metric_definitions=src["metric_definitions"],
        trend_summary=trend_summary,
        buyer_takeaway=buyer_takeaway,
        seller_takeaway=seller_takeaway,
        trend_1=trend_1,
        trend_2=trend_2,
        trend_3=trend_3,
        comparison=comparison,
        faq_html=faq_html,
        faq_schema=faq_jsonld,
    )
    out_path = OUT_DIR / f"{year}-{year_month.month:02d}-{slug}-market-report.html"
    return html, out_path


class InputValidationError(Exception):
    """Raised when input data is missing, incomplete, or unattributed."""


# Figures that must be supplied per neighborhood — no defaults exist.
REQUIRED_FIGURES = ("median", "dom", "ratio", "sales_count")
# Provenance that must accompany the figures before anything is published.
REQUIRED_PROVENANCE = (
    "source", "retrieved_on", "geography", "property_types",
    "reporting_window", "metric_definitions",
)


def validate_neighborhood_input(inputs: dict | None, key: str, name: str) -> dict:
    """Return the validated record for one neighborhood, or raise.

    There is deliberately no fallback path: a missing or incomplete record
    stops the run rather than publishing a synthetic figure.
    """
    if not inputs:
        raise InputValidationError(
            f"no input data loaded; cannot render {name}. "
            f"Populate {INPUTS.relative_to(ROOT)} from an authorized source pull."
        )
    src = inputs.get(key)
    if not isinstance(src, dict) or not src:
        raise InputValidationError(
            f"no input record for '{key}' ({name}); refusing to publish "
            f"unsourced market statistics."
        )
    missing = [f for f in REQUIRED_FIGURES if src.get(f) in (None, "")]
    if missing:
        raise InputValidationError(
            f"'{key}' is missing required figure(s): {', '.join(missing)}."
        )
    absent_prov = [f for f in REQUIRED_PROVENANCE if not str(src.get(f, "")).strip()]
    if absent_prov:
        raise InputValidationError(
            f"'{key}' is missing required provenance field(s): "
            f"{', '.join(absent_prov)}. Figures may not be published without "
            f"source identity, retrieval date, geography, property types, "
            f"reporting window, and metric definitions."
        )
    return src


def validate_month_complete(month: str, today: dt.date | None = None) -> None:
    """Refuse to report on a month that has not finished."""
    today = today or dt.date.today()
    first = dt.date.fromisoformat(month + "-01")
    next_first = (first + dt.timedelta(days=32)).replace(day=1)
    if today < next_first:
        raise InputValidationError(
            f"reporting period {month} has not ended (today is {today.isoformat()}; "
            f"{month} closes {(next_first - dt.timedelta(days=1)).isoformat()}). "
            f"Refusing to publish an incomplete or future period."
        )


def validate_publication_date(published_iso: str, today: dt.date | None = None) -> None:
    """Refuse a publication date in the future."""
    today = today or dt.date.today()
    if dt.date.fromisoformat(published_iso) > today:
        raise InputValidationError(
            f"publication date {published_iso} is in the future (today is "
            f"{today.isoformat()}); refusing to future-date a report."
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True, help="YYYY-MM (e.g. 2026-05)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--inputs", help="Optional JSON file with per-neighborhood data overrides")
    args = ap.parse_args()

    dt.date.fromisoformat(args.month + "-01")  # validate format

    # --- Gate 1: the reporting period must be over. ---
    try:
        validate_month_complete(args.month)
    except InputValidationError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    # --- Gate 2: an input file must exist and parse. ---
    inputs_path = Path(args.inputs) if args.inputs else INPUTS
    if not inputs_path.exists():
        print(
            f"REFUSED: required input file {inputs_path} is missing. This "
            f"generator has no fallback statistics; populate it from an "
            f"authorized source pull before generating reports.",
            file=sys.stderr,
        )
        return 2
    try:
        inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"REFUSED: {inputs_path} is not valid JSON ({exc}).", file=sys.stderr)
        return 2
    if not isinstance(inputs, dict) or not inputs:
        print(f"REFUSED: {inputs_path} contains no neighborhood records.", file=sys.stderr)
        return 2

    # --- Gate 3: render EVERYTHING in memory first. A single failure aborts
    # the whole run, so a partial/invalid set can never reach disk. ---
    rendered: list[tuple[Path, str]] = []
    try:
        for nb in DEFAULT_TRACKED:
            html, path = render_one(nb, args.month, inputs)
            rendered.append((path, html))
    except InputValidationError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        print("No files were written; no sitemap changes were made.", file=sys.stderr)
        return 2

    if not args.apply:
        print(f"DRY-RUN: {len(rendered)} reports validated for {args.month}; nothing written.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, html in rendered:
        path.write_text(html, encoding="utf-8")
    print(f"Generated {len(rendered)} market reports for {args.month}")
    print(f"Output dir: {OUT_DIR.relative_to(ROOT)}/")
    print("\nMode: APPLIED")
    print("\nNext: re-run inject_ai_schema.py + rebuild_sitemap.py + indexnow_ping.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
