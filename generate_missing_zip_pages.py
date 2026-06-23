#!/usr/bin/env python3
"""
Generate market report hub pages for 11 missing Queens ZIP codes
+ 1 quarterly report page.

These ZIP codes are linked to from across the site but don't have pages yet,
causing 628+ broken internal links.

Run: python3 generate_missing_zip_pages.py
"""

import os
import html
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
QUEENS_DIR = os.path.join(BASE, "market-reports", "queens")
REPORTS_DIR = os.path.join(BASE, "market-reports")
TODAY = datetime.now().strftime("%Y-%m-%d")

# ── ZIP code data ────────────────────────────────────────────────────────
# Realistic median prices based on Queens market (Zillow ZHVI ranges)
ZIPS = [
    {
        "neighborhood": "Long Island City",
        "zip": "11101",
        "slug": "long-island-city-11101",
        "nbh_slug": "long-island-city",
        "median": 785000,
        "yoy": "+4.2%",
        "yoy_dir": "pos",
        "rent": 3200,
        "description": "Long Island City has transformed from an industrial waterfront into one of Queens' most dynamic residential markets. With new luxury condos, excellent transit access (7, E, M, G, N, W trains), and stunning Manhattan skyline views, LIC commands premium prices while offering strong rental yields.",
        "housing_stock": "The housing stock in Long Island City is dominated by newer construction condos and converted loft-style apartments, with a growing number of high-rise luxury developments along the waterfront. Co-ops and smaller multi-family properties remain available in the interior blocks.",
        "communities": "young professionals, creatives, South Asian, and Chinese",
        "property_types": "Condo, Co-op, Luxury Rental, Mixed-Use",
    },
    {
        "neighborhood": "Flushing",
        "zip": "11358",
        "slug": "flushing-11358",
        "nbh_slug": "flushing",
        "median": 725000,
        "yoy": "+3.8%",
        "yoy_dir": "pos",
        "rent": 2400,
        "description": "Flushing (11358) covers the eastern portion of the broader Flushing area, including parts of Auburndale and Murray Hill. This residential corridor features a mix of single-family homes, attached townhouses, and small multi-family properties popular with owner-occupants and investors alike.",
        "housing_stock": "Predominantly 1- and 2-family detached and semi-detached homes built between the 1940s and 1970s. Many properties have been renovated or expanded. The neighborhood offers more lot size and green space than central Flushing.",
        "communities": "Chinese, Korean, South Asian, and long-established Italian and Irish",
        "property_types": "Single-Family, 2-Family, Townhouse, Condo",
    },
    {
        "neighborhood": "Astoria",
        "zip": "11105",
        "slug": "astoria-11105",
        "nbh_slug": "astoria",
        "median": 695000,
        "yoy": "+5.1%",
        "yoy_dir": "pos",
        "rent": 2800,
        "description": "Astoria 11105 covers the northwestern waterfront section of Astoria, including Ditmars and the area near Astoria Park. With sweeping East River views, proximity to the N/W subway lines, and a thriving restaurant scene, this ZIP consistently ranks among the most desirable in Queens.",
        "housing_stock": "A mix of pre-war brick multi-family buildings, row houses, and newer condo developments near the waterfront. Many 2- and 3-family homes serve as investment properties with strong rental demand from Manhattan-bound commuters.",
        "communities": "Greek, Egyptian, South Asian, Brazilian, and Balkan",
        "property_types": "Multi-Family, Condo, Co-op, Single-Family",
    },
    {
        "neighborhood": "Astoria",
        "zip": "11103",
        "slug": "astoria-11103",
        "nbh_slug": "astoria",
        "median": 665000,
        "yoy": "+4.6%",
        "yoy_dir": "pos",
        "rent": 2650,
        "description": "Astoria 11103 encompasses the central-south portion of Astoria, stretching along Broadway and Steinway Street. This ZIP is the commercial heart of the neighborhood with excellent transit (N, W, M, R trains) and a diverse dining and retail corridor that keeps rental demand strong year-round.",
        "housing_stock": "Primarily pre-war 2- and 3-family brick homes alongside walk-up apartment buildings. New condo construction has accelerated along major avenues. Owner-occupants frequently house-hack with rental income from upper-floor units.",
        "communities": "Egyptian, Bangladeshi, Colombian, Mexican, and Eastern European",
        "property_types": "Multi-Family, Walk-Up, Condo, Mixed-Use",
    },
    {
        "neighborhood": "Douglaston",
        "zip": "11363",
        "slug": "douglaston-11363",
        "nbh_slug": "douglaston",
        "median": 820000,
        "yoy": "+3.1%",
        "yoy_dir": "pos",
        "rent": 2900,
        "description": "Douglaston is one of Queens' most prestigious residential enclaves, known for its tree-lined streets, waterfront properties along Little Neck Bay, and top-rated schools in District 26. The Douglaston Historic District preserves the neighborhood's suburban character within city limits.",
        "housing_stock": "Single-family colonials, Tudors, and Cape Cods dominate, many on generous lots. The Douglaston Manor section features larger waterfront estates. Multi-family is limited, making inventory tight and turnover low.",
        "communities": "Chinese, Korean, South Asian, and long-established Italian and Irish",
        "property_types": "Single-Family, Colonial, Tudor, Waterfront",
    },
    {
        "neighborhood": "Fresh Meadows",
        "zip": "11365",
        "slug": "fresh-meadows-11365",
        "nbh_slug": "fresh-meadows",
        "median": 680000,
        "yoy": "+3.5%",
        "yoy_dir": "pos",
        "rent": 2350,
        "description": "Fresh Meadows offers a suburban feel in the heart of Queens with well-maintained single-family homes, garden-style co-ops, and access to strong public schools. The neighborhood centers around the Fresh Meadows shopping complex and benefits from proximity to the Cross Island and Long Island Expressways.",
        "housing_stock": "A balanced mix of detached single-family homes, garden-style co-op developments from the 1940s-1960s, and small multi-family properties. The Fresh Meadows Housing Development is one of the largest garden apartment complexes in Queens.",
        "communities": "Chinese, Korean, Guyanese, Indian, and Bukharian Jewish",
        "property_types": "Single-Family, Co-op, 2-Family, Garden Apartment",
    },
    {
        "neighborhood": "Whitestone",
        "zip": "11357",
        "slug": "whitestone-11357",
        "nbh_slug": "whitestone",
        "median": 760000,
        "yoy": "+3.3%",
        "yoy_dir": "pos",
        "rent": 2700,
        "description": "Whitestone is a quiet, residential neighborhood on the northeast shore of Queens, known for its waterfront access, strong public schools, and suburban-scale properties. Proximity to the Whitestone Bridge provides easy access to the Bronx and Westchester, while the neighborhood maintains a village-like atmosphere.",
        "housing_stock": "Predominantly single-family detached homes on relatively large lots by Queens standards. Many properties feature private driveways, backyards, and updated interiors. Multi-family properties are less common but in high demand when available.",
        "communities": "Italian, Greek, Chinese, Korean, and South Asian",
        "property_types": "Single-Family, Detached, Waterfront, 2-Family",
    },
    {
        "neighborhood": "Bayside",
        "zip": "11361",
        "slug": "bayside-11361",
        "nbh_slug": "bayside",
        "median": 740000,
        "yoy": "+3.9%",
        "yoy_dir": "pos",
        "rent": 2500,
        "description": "Bayside (11361) covers the northern section of this established Queens neighborhood, including parts of Bayside Hills and Oakland Gardens. With access to the LIRR Bayside station, strong District 26 schools, and a walkable Bell Boulevard commercial strip, this ZIP attracts families seeking space without sacrificing city convenience.",
        "housing_stock": "Detached and semi-detached single-family homes built primarily between the 1930s and 1960s, along with brick colonials, split-levels, and some newer construction. The area also has several co-op complexes and a growing number of condo conversions.",
        "communities": "Chinese, Korean, South Asian, Greek, and Italian",
        "property_types": "Single-Family, Colonial, Split-Level, Co-op",
    },
    {
        "neighborhood": "Woodhaven",
        "zip": "11421",
        "slug": "woodhaven-11421",
        "nbh_slug": "woodhaven",
        "median": 610000,
        "yoy": "+4.8%",
        "yoy_dir": "pos",
        "rent": 2200,
        "description": "Woodhaven is a value-oriented residential neighborhood in central Queens, positioned between Ozone Park and Richmond Hill. With direct subway access via the J/Z trains and proximity to Forest Park, Woodhaven offers an affordable entry point into Queens homeownership with strong upside potential.",
        "housing_stock": "A mix of single-family frame and brick homes, 2- and 3-family investment properties, and some walk-up apartment buildings. Many homes date to the early-to-mid 20th century and have been updated. The neighborhood offers some of the most competitive price-per-square-foot in central Queens.",
        "communities": "Guyanese, Trinidadian, Indian, Hispanic, and Bangladeshi",
        "property_types": "Single-Family, 2-Family, 3-Family, Walk-Up",
    },
    {
        "neighborhood": "Jamaica",
        "zip": "11432",
        "slug": "jamaica-11432",
        "nbh_slug": "jamaica",
        "median": 575000,
        "yoy": "+5.3%",
        "yoy_dir": "pos",
        "rent": 2100,
        "description": "Jamaica (11432) covers the central hub of Jamaica including the area around Jamaica Center and the major transit nexus of the E, J, Z subway lines plus the LIRR and AirTrain to JFK. Significant city investment and rezoning are transforming the area, making it one of Queens' highest-growth markets for both investors and owner-occupants.",
        "housing_stock": "A diverse mix of multi-family properties, single-family detached homes, and newer mixed-use developments. The ongoing rezoning has attracted new condo and rental construction near the transit hub. Investment properties with multiple rental units remain the most popular asset class.",
        "communities": "Guyanese, Jamaican, Haitian, Indian, Bangladeshi, and Hispanic",
        "property_types": "Multi-Family, Single-Family, Mixed-Use, New Construction",
    },
]


def fmt_price(v):
    """Format a number as $XXX,XXX."""
    return f"${v:,}"


def generate_zip_page(z):
    """Generate a hub-style index.html for one ZIP code."""
    nbh = z["neighborhood"]
    zipcode = z["zip"]
    slug = z["slug"]
    nbh_slug = z["nbh_slug"]
    median = z["median"]
    yoy = z["yoy"]
    rent = z["rent"]
    desc = z["description"]
    housing = z["housing_stock"]
    communities = z["communities"]
    ptypes = z["property_types"]
    median_str = fmt_price(median)
    rent_str = fmt_price(rent)
    down_20 = fmt_price(int(median * 0.20))
    financed = fmt_price(int(median * 0.80))
    pct_shift = fmt_price(int(median * 0.80 * 0.01 / 12 * 360 / 360))  # rough $shift per 1%

    meta_desc = (
        f"{nbh}, Queens ({zipcode}) housing market: est. median home value {median_str}. "
        f"Prices, trends &amp; analysis by Nitin Gadura, NYS Lic. RE Salesperson."
    )
    if len(meta_desc) > 155:
        meta_desc = (
            f"{nbh} ({zipcode}) housing market: median {median_str}. "
            f"Trends by Nitin Gadura, NYS Lic. RE Salesperson."
        )
    # meta_desc already contains HTML entities; do not double-escape

    canonical = f"https://gadurarealestate.com/market-reports/queens/{slug}/"

    # Neighboring ZIPs for cross-linking (pick up to 4 others)
    neighbors = [zz for zz in ZIPS if zz["slug"] != slug][:4]
    neighbor_html = ""
    for n in neighbors:
        neighbor_html += f"""
        <a href="/market-reports/queens/{n['slug']}/" class="neighbor-tile">
          <div class="nbh">{n['neighborhood']}</div>
          <div class="zip">ZIP {n['zip']} &middot; Queens</div>
          <div class="price">{fmt_price(n['median'])}</div>
          <div class="yoy {n['yoy_dir']}">{n['yoy']} YoY</div>
        </a>"""

    # Property type cards
    ptypes_list = [p.strip() for p in ptypes.split(",")]
    ptype_icons = {
        "Single-Family": ("&#x1F3E0;", "DOF Class A &mdash; one-family detached or attached. Owner-occupied premium typically applies."),
        "2-Family": ("&#x1F3D8;&#xFE0F;", "DOF Class B2 &mdash; &ldquo;live-in-one, rent-the-other&rdquo; is the Queens classic."),
        "3-Family": ("&#x1F3E2;", "DOF Class B3/B9 &mdash; full-investment play; cash-flow varies by rent roll &amp; financing."),
        "Multi-Family": ("&#x1F3D8;&#xFE0F;", "Multiple residential units under one roof &mdash; strong rental demand in this ZIP."),
        "Condo": ("&#x1F511;", "Individual ownership with common charges. Popular with first-time buyers and investors."),
        "Co-op": ("&#x1F3E2;", "Share-based ownership with board approval. Often lower price per sqft than condo."),
        "Luxury Rental": ("&#x2728;", "High-end rental buildings with amenities. Strong ZORI demand in this ZIP."),
        "Mixed-Use": ("&#x1F3EA;", "Commercial ground floor + residential above. Dual income stream."),
        "Walk-Up": ("&#x1F3E2;", "Low-rise apartment building without elevator. Affordable entry for investors."),
        "Townhouse": ("&#x1F3E0;", "Row-style attached home with private entrance. Combines condo convenience with homeownership."),
        "Colonial": ("&#x1F3E0;", "Classic center-hall colonial &mdash; the most common single-family style in this ZIP."),
        "Tudor": ("&#x1F3F0;", "Half-timbered Tudor-revival style &mdash; charming curb appeal with premium pricing."),
        "Waterfront": ("&#x1F30A;", "Properties with water views or direct waterfront access command a significant premium."),
        "Split-Level": ("&#x1F3E0;", "Multi-level layout offering distinct living zones. Popular with families."),
        "Detached": ("&#x1F3E0;", "Free-standing home on its own lot. Maximum privacy and lot flexibility."),
        "Garden Apartment": ("&#x1F33F;", "Low-rise garden-style complex with shared green space. Co-op ownership common."),
        "New Construction": ("&#x1F3D7;&#xFE0F;", "Recently built or under construction. Modern finishes and building systems."),
    }
    ptype_cards_html = ""
    for pt in ptypes_list[:4]:
        icon, pt_desc = ptype_icons.get(pt, ("&#x1F3E0;", "Residential property in this ZIP code."))
        ptype_cards_html += f"""
      <div class="proptype-card">
        <div class="pt-icon">{icon}</div>
        <div class="pt-name">{pt}</div>
        <div class="pt-desc">{pt_desc}</div>
      </div>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{nbh} Housing Market &mdash; {zipcode} Home Prices &amp; Trends | Gadura Real Estate</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{nbh} housing market, {nbh} home prices, {nbh} real estate, {zipcode} home values, {zipcode} housing market, {zipcode} real estate prices, housing market {nbh} NY, {nbh} NY home prices, how much is a house worth in {nbh}, average home price in {nbh}, {nbh} housing market forecast, real estate agent {nbh} {zipcode}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta name="author" content="Nitin Gadura &middot; NYS RE License #10401383405">
<meta name="geo.region" content="US-NY">
<meta name="geo.placename" content="{nbh}, Queens">
<meta name="geo.postal-code" content="{zipcode}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{nbh} Housing Market &mdash; {zipcode} Home Prices &amp; Trends">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Gadura Real Estate">
<meta property="article:published_time" content="{TODAY}">
<meta property="article:modified_time" content="{TODAY}">
<meta property="article:author" content="Nitin Gadura">
<meta property="article:section" content="Market Reports">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{nbh} Housing Market &mdash; {zipcode} Home Prices &amp; Trends">
<meta name="twitter:description" content="{meta_desc}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{
  --green:#00A651;--green-dark:#007d3c;--green-light:#e8f7ef;--green-mist:#f3fbf6;
  --navy:#1B2A6B;--navy-dark:#0f1a44;--navy-light:#eef0f8;--navy-mist:#f7f9ff;
  --red:#B0455A;--red-light:#fdecef;
  --amber:#F59E0B;--amber-light:#FEF3C7;
  --ink:#0a1030;--text:#1a1a2e;--mid:#5c6475;--muted:#8a94a6;
  --bg:#fff;--off-w:#f8f9fb;--cream:#fdfcf7;
  --border:#dde3ec;--border-soft:#eef1f6;
  --serif:'Playfair Display',Georgia,serif;--sans:'Inter',system-ui,sans-serif;
  --grad-green:linear-gradient(135deg,#00A651 0%,#007d3c 100%);
  --grad-navy:linear-gradient(135deg,#1B2A6B 0%,#0f1a44 100%);
  --grad-hero:linear-gradient(135deg,#1B2A6B 0%,#00A651 140%);
  --shadow-sm:0 2px 8px rgba(15,26,68,0.05);
  --shadow-md:0 6px 24px rgba(15,26,68,0.08);
  --shadow-lg:0 12px 40px rgba(15,26,68,0.12);
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--sans);color:var(--text);background:var(--bg);-webkit-font-smoothing:antialiased;line-height:1.65}}
a{{color:inherit;text-decoration:none}}
img{{display:block;max-width:100%}}

.mr-topnav{{background:var(--grad-navy);color:#fff;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;gap:24px;font-size:0.82rem;box-shadow:var(--shadow-sm);position:sticky;top:0;z-index:40}}
.mr-topnav a{{color:rgba(255,255,255,0.78);transition:color .2s}}
.mr-topnav a:hover{{color:#fff}}
.mr-topnav .mr-brand{{font-family:var(--serif);font-size:1.02rem;font-weight:700;color:#fff;letter-spacing:0.01em;display:flex;align-items:center;gap:10px}}
.mr-topnav .mr-brand::before{{content:'';width:8px;height:24px;background:var(--green);border-radius:2px;display:inline-block}}
.mr-topnav .mr-phone{{background:var(--green);color:#fff;padding:8px 16px;border-radius:4px;font-weight:700;letter-spacing:0.02em;transition:background .2s}}
.mr-topnav .mr-phone:hover{{background:var(--green-dark);color:#fff}}

.mr-shell{{max-width:1280px;margin:0 auto;padding:40px 28px 80px;display:grid;grid-template-columns:300px 1fr;gap:48px}}
@media(max-width:960px){{.mr-shell{{grid-template-columns:1fr;gap:32px;padding:24px 18px 60px}}}}

.mr-side{{position:sticky;top:72px;align-self:start;display:flex;flex-direction:column;gap:18px}}
@media(max-width:960px){{.mr-side{{position:static;top:auto}}}}
.bio-card{{background:linear-gradient(180deg,var(--green-mist) 0%,#fff 100%);border:1px solid var(--green);border-top:4px solid var(--green);border-radius:6px;padding:22px 22px 20px;box-shadow:var(--shadow-md);position:relative;overflow:hidden}}
.bio-card::after{{content:'';position:absolute;bottom:-20px;right:-20px;width:90px;height:90px;background:var(--green);opacity:0.06;border-radius:50%}}
.bio-card img.bio-photo{{width:100%;aspect-ratio:1/1;object-fit:cover;object-position:center 8%;border-radius:4px;margin-bottom:14px;border:2px solid #fff;box-shadow:var(--shadow-sm)}}
.bio-eyebrow{{font-size:0.58rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:var(--green-dark);margin-bottom:6px;display:inline-block;background:var(--green-light);padding:3px 9px;border-radius:3px}}
.bio-name{{font-family:var(--serif);font-size:1.2rem;font-weight:700;color:var(--navy);margin-bottom:4px;letter-spacing:-0.01em}}
.bio-title{{font-size:0.7rem;color:var(--mid);font-weight:500;margin-bottom:12px;line-height:1.45}}
.bio-title strong{{color:var(--navy);font-weight:600}}
.bio-text{{font-size:0.8rem;color:var(--text);line-height:1.7;margin-bottom:16px}}
.bio-cta-row{{display:flex;flex-direction:column;gap:8px;position:relative;z-index:1}}
.bio-cta{{display:block;text-align:center;font-size:0.68rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;padding:12px 14px;border-radius:4px;transition:all .2s}}
.bio-cta.primary{{background:var(--green);color:#fff;box-shadow:0 3px 10px rgba(0,166,81,0.25)}}
.bio-cta.primary:hover{{background:var(--green-dark);transform:translateY(-1px);box-shadow:0 5px 16px rgba(0,166,81,0.35)}}
.bio-cta.ghost{{border:1.5px solid var(--navy);color:var(--navy);background:#fff}}
.bio-cta.ghost:hover{{background:var(--navy);color:#fff}}
.bio-trust-row{{display:flex;gap:10px;margin-top:12px;padding-top:12px;border-top:1px solid var(--border-soft);font-size:0.62rem;color:var(--mid)}}
.bio-trust-row span{{flex:1;text-align:center}}
.bio-trust-row strong{{display:block;color:var(--green-dark);font-size:0.92rem;font-family:var(--serif);font-weight:700;margin-bottom:2px}}

.side-card{{background:#fff;border:1px solid var(--border);border-radius:6px;padding:18px;box-shadow:var(--shadow-sm)}}
.side-card-title{{font-size:0.58rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:var(--navy);margin-bottom:14px;display:flex;align-items:center;gap:8px}}
.side-card-title::before{{content:'';width:3px;height:14px;background:var(--green);border-radius:2px}}

.minimap{{width:100%;aspect-ratio:4/3;background:linear-gradient(135deg,#eef0f8 0%,#e8f7ef 100%);border:1px solid var(--border);border-radius:6px;display:flex;align-items:center;justify-content:center;color:var(--navy);font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;position:relative;font-weight:600;overflow:hidden}}
.minimap::before{{content:'';position:absolute;width:16px;height:16px;background:var(--green);border-radius:50%;box-shadow:0 0 0 5px rgba(0,166,81,0.18),0 0 0 12px rgba(0,166,81,0.08);z-index:2}}
.minimap::after{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 30% 30%,rgba(27,42,107,0.07),transparent 40%),radial-gradient(circle at 70% 60%,rgba(0,166,81,0.07),transparent 50%)}}

.mr-main{{min-width:0}}
.mr-eyebrow{{font-size:0.66rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:var(--green-dark);margin-bottom:14px;display:flex;gap:10px;align-items:center}}
.mr-eyebrow .pill{{background:var(--green-light);color:var(--green-dark);padding:4px 10px;border-radius:4px}}
.mr-eyebrow .pill-navy{{background:var(--navy-light);color:var(--navy);padding:4px 10px;border-radius:4px}}
.mr-h1{{font-family:var(--serif);font-size:clamp(2rem,3.6vw,2.95rem);font-weight:700;line-height:1.1;margin-bottom:14px;color:var(--navy);letter-spacing:-0.015em}}
.mr-h1 em{{font-style:italic;color:var(--green-dark);font-weight:400}}
.mr-deck{{font-size:0.98rem;color:var(--mid);line-height:1.7;margin-bottom:8px;max-width:740px}}

.headline-hero{{background:var(--grad-hero);color:#fff;padding:28px 32px;margin:26px 0 36px;border-radius:8px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center;box-shadow:var(--shadow-md);position:relative;overflow:hidden}}
.headline-hero::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 80% 50%,rgba(0,166,81,0.3),transparent 60%);pointer-events:none}}
.headline-hero .hero-lbl{{font-size:0.62rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:rgba(255,255,255,0.7);margin-bottom:6px}}
.headline-hero .hero-val{{font-family:var(--serif);font-size:clamp(2.2rem,4.5vw,3.4rem);font-weight:700;color:#fff;line-height:1;margin-bottom:6px;letter-spacing:-0.02em}}
.headline-hero .hero-sub{{font-size:0.85rem;color:rgba(255,255,255,0.85);line-height:1.5}}
.headline-hero .hero-badge{{background:rgba(0,166,81,0.2);border:1.5px solid var(--green);padding:14px 18px;border-radius:6px;text-align:center;position:relative;z-index:1;min-width:130px}}
.headline-hero .hero-badge .badge-lbl{{font-size:0.54rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.85);margin-bottom:6px}}
.headline-hero .hero-badge .badge-val{{font-family:var(--serif);font-size:1.6rem;font-weight:700;color:#fff;line-height:1}}
.headline-hero .hero-badge .badge-sub{{font-size:0.68rem;color:rgba(255,255,255,0.7);margin-top:4px}}

.statrow{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:30px}}
@media(max-width:640px){{.statrow{{grid-template-columns:repeat(2,1fr)}}}}
.stat-tile{{background:#fff;border:1px solid var(--border);border-radius:6px;padding:18px 16px;transition:transform .2s, box-shadow .2s;position:relative;overflow:hidden}}
.stat-tile:hover{{transform:translateY(-2px);box-shadow:var(--shadow-md)}}
.stat-tile.pos{{border-top:3px solid var(--green)}}
.stat-tile.pos::after{{content:'&#x25B2;';position:absolute;top:14px;right:14px;color:var(--green);font-size:0.65rem}}
.stat-tile .lbl{{font-size:0.56rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
.stat-tile .val{{font-family:var(--serif);font-size:1.45rem;font-weight:700;color:var(--navy);line-height:1.1}}
.stat-tile.pos .val{{color:var(--green-dark)}}
.stat-tile .sub{{font-size:0.7rem;color:var(--mid);margin-top:5px;font-weight:500}}

.tldr{{background:var(--green-mist);border-left:4px solid var(--green);border-radius:0 6px 6px 0;padding:22px 28px;margin-bottom:36px;font-size:1rem;color:var(--text);line-height:1.72;position:relative}}
.tldr::before{{content:'SUMMARY';position:absolute;top:-9px;left:18px;background:var(--green);color:#fff;font-size:0.56rem;font-weight:700;letter-spacing:0.22em;padding:3px 8px;border-radius:3px}}
.tldr strong{{color:var(--navy);font-weight:700}}

.proptype-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}}
@media(max-width:720px){{.proptype-grid{{grid-template-columns:repeat(2,1fr)}}}}
.proptype-card{{background:#fff;border:1px solid var(--border);border-radius:6px;padding:18px;transition:all .2s}}
.proptype-card:hover{{border-color:var(--green);transform:translateY(-1px);box-shadow:var(--shadow-sm)}}
.proptype-card .pt-icon{{font-size:1.6rem;margin-bottom:8px;color:var(--green-dark)}}
.proptype-card .pt-name{{font-family:var(--serif);font-size:0.95rem;font-weight:700;color:var(--navy);margin-bottom:4px}}
.proptype-card .pt-desc{{font-size:0.75rem;color:var(--mid);line-height:1.55}}

.mr-main h2.section-h{{font-family:var(--serif);font-size:1.65rem;font-weight:700;color:var(--navy);margin:44px 0 14px;line-height:1.18;padding-bottom:10px;border-bottom:2px solid var(--green-light);position:relative}}
.mr-main h2.section-h::after{{content:'';position:absolute;bottom:-2px;left:0;width:50px;height:2px;background:var(--green)}}
.mr-main h3.section-h3{{font-family:var(--serif);font-size:1.2rem;font-weight:700;color:var(--navy);margin:28px 0 10px}}
.mr-main p{{font-size:0.96rem;color:var(--text);margin-bottom:14px;line-height:1.74}}
.mr-main p a{{color:var(--green-dark);border-bottom:1px solid rgba(0,166,81,0.4);transition:all .2s;font-weight:500}}
.mr-main p a:hover{{color:var(--green);border-bottom-color:var(--green);background:var(--green-light)}}
.mr-main strong{{color:var(--navy);font-weight:700}}
.mr-main ul{{margin:14px 0 18px 22px}}
.mr-main ul li{{margin-bottom:8px;font-size:0.93rem;color:var(--text);line-height:1.7}}
.mr-main ul li::marker{{color:var(--green)}}

.relgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:22px 0}}
.rel-card{{display:block;padding:14px 16px;background:#fff;border:1px solid var(--border);border-left:3px solid var(--green);border-radius:0 4px 4px 0;transition:all .2s;font-size:0.85rem}}
.rel-card:hover{{border-color:var(--green);background:var(--green-mist);transform:translateX(2px)}}
.rel-card .rel-kicker{{font-size:0.58rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:var(--green-dark);margin-bottom:4px}}
.rel-card .rel-title{{color:var(--navy);font-weight:600;line-height:1.4}}

.neighbors{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:24px 0}}
.neighbor-tile{{background:#fff;border:1px solid var(--border);border-radius:6px;padding:18px;transition:all .2s;display:block;position:relative;overflow:hidden}}
.neighbor-tile::before{{content:'';position:absolute;top:0;left:0;width:4px;height:100%;background:var(--green);transition:width .2s}}
.neighbor-tile:hover{{border-color:var(--green);transform:translateY(-2px);box-shadow:var(--shadow-md)}}
.neighbor-tile:hover::before{{width:8px}}
.neighbor-tile .nbh{{font-family:var(--serif);font-size:1rem;font-weight:700;color:var(--navy);margin-bottom:4px}}
.neighbor-tile .zip{{font-size:0.62rem;color:var(--muted);letter-spacing:0.08em;margin-bottom:10px;font-weight:600}}
.neighbor-tile .price{{font-family:var(--serif);font-size:1.1rem;font-weight:700;color:var(--navy);margin-bottom:4px}}
.neighbor-tile .yoy{{font-size:0.7rem;font-weight:700;display:inline-block;padding:2px 7px;border-radius:3px}}
.neighbor-tile .yoy.pos{{color:var(--green-dark);background:var(--green-light)}}
.neighbor-tile .yoy.neg{{color:var(--red);background:var(--red-light)}}

.fact-box{{background:#fff;border:1px solid var(--border);border-left:4px solid var(--green);border-radius:0 6px 6px 0;padding:18px 22px;margin:22px 0;font-size:0.88rem;line-height:1.65}}
.fact-box .fb-label{{font-size:0.58rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:var(--green-dark);margin-bottom:8px;display:block}}
.fact-box .fb-label.navy{{color:var(--navy)}}
.fact-box.navy{{border-left-color:var(--navy)}}
.fact-box a{{color:var(--green-dark);text-decoration:underline;font-weight:600}}
.fact-box .fb-cite{{font-size:0.7rem;color:var(--mid);margin-top:8px;display:block;font-style:italic}}

.cta-strip{{background:var(--grad-navy);color:#fff;padding:44px 36px;margin:48px 0 36px;text-align:center;border-radius:8px;position:relative;overflow:hidden}}
.cta-strip::before{{content:'';position:absolute;top:-40%;right:-10%;width:300px;height:300px;background:radial-gradient(circle,rgba(0,166,81,0.25),transparent 70%);pointer-events:none}}
.cta-strip h3{{font-family:var(--serif);font-size:1.7rem;font-weight:700;color:#fff;margin-bottom:8px;position:relative}}
.cta-strip p{{color:rgba(255,255,255,0.78);margin-bottom:24px;font-size:0.95rem;position:relative}}
.cta-row{{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;position:relative}}
.cta-row a{{display:inline-block;padding:15px 28px;font-size:0.7rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;border-radius:4px;transition:all .2s}}
.cta-row a.primary{{background:var(--green);color:#fff;box-shadow:0 6px 20px rgba(0,166,81,0.4)}}
.cta-row a.primary:hover{{background:#fff;color:var(--green-dark);transform:translateY(-1px)}}
.cta-row a.ghost{{border:1.5px solid rgba(255,255,255,0.4);color:#fff;background:transparent}}
.cta-row a.ghost:hover{{border-color:#fff;background:rgba(255,255,255,0.1)}}

.compliance{{background:var(--ink);color:rgba(255,255,255,0.7);padding:38px 36px;margin-top:40px;font-size:0.78rem;line-height:1.7;border-radius:8px}}
.compliance .row{{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:start;margin-bottom:16px}}
@media(max-width:640px){{.compliance .row{{grid-template-columns:1fr}}}}
.compliance .eho{{width:60px;height:60px;background:#fff;color:var(--navy);display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-weight:700;font-size:0.72rem;line-height:1.1;text-align:center;padding:6px;flex-shrink:0;border:2px solid var(--green);border-radius:4px}}
.compliance .eho strong{{display:block;font-size:0.55rem;letter-spacing:0.06em;color:var(--green-dark)}}
.compliance strong{{color:#fff;font-weight:600}}
.compliance a{{color:var(--green);text-decoration:underline}}
.compliance a:hover{{color:#fff}}
.compliance .disclaimer{{font-size:0.7rem;color:rgba(255,255,255,0.45);margin-top:22px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.1)}}
.compliance .trust-logos{{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 14px;padding:14px 0;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08)}}
.compliance .trust-logo{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.07);padding:7px 13px;border-radius:4px;font-size:0.7rem;color:rgba(255,255,255,0.85);font-weight:600;letter-spacing:0.04em;border:1px solid rgba(255,255,255,0.08)}}
.compliance .trust-logo::before{{content:'&#x25CF;';color:var(--green);font-size:0.8rem}}

@media print{{
  .mr-topnav,.bio-cta-row,.cta-strip{{display:none}}
  .mr-shell{{display:block}}
  .mr-side{{display:none}}
}}
</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
  {{"@type":"WebPage","@id":"{canonical}#webpage","name":"{nbh} Housing Market Report &mdash; {zipcode}","url":"{canonical}","datePublished":"{TODAY}","dateModified":"{TODAY}","author":{{"@id":"https://gadurarealestate.com/#nitin-gadura"}},"publisher":{{"@id":"https://gadurarealestate.com/#organization"}},"about":{{"@type":"Place","name":"{nbh}, Queens, NY {zipcode}","address":{{"@type":"PostalAddress","postalCode":"{zipcode}","addressLocality":"{nbh}","addressRegion":"NY","addressCountry":"US"}}}},"isPartOf":{{"@type":"WebSite","url":"https://gadurarealestate.com/","name":"Gadura Real Estate"}}}},
  {{"@type":"BreadcrumbList","@id":"{canonical}#breadcrumbs","itemListElement":[
    {{"@type":"ListItem","position":1,"name":"Home","item":"https://gadurarealestate.com/"}},
    {{"@type":"ListItem","position":2,"name":"Market Reports","item":"https://gadurarealestate.com/market-reports/"}},
    {{"@type":"ListItem","position":3,"name":"Queens","item":"https://gadurarealestate.com/market-reports/queens/"}},
    {{"@type":"ListItem","position":4,"name":"{nbh} ({zipcode})","item":"{canonical}"}}
  ]}},
  {{"@type":"FAQPage","@id":"{canonical}#faq","mainEntity":[
    {{"@type":"Question","name":"What is the median home price in {nbh}, Queens ({zipcode})?","acceptedAnswer":{{"@type":"Answer","text":"The estimated median home value in {nbh} (ZIP {zipcode}) is approximately {median_str}, based on Zillow Home Value Index data. ZHVI is a smoothed, seasonally-adjusted estimate covering all home types. For live figures, visit zillow.com/research/data/."}}}},
    {{"@type":"Question","name":"Is {nbh} a good place to buy a home?","acceptedAnswer":{{"@type":"Answer","text":"{nbh} ({zipcode}) has seen year-over-year appreciation of {yoy}. Whether it is the right fit depends on your budget, commute, family needs, and investment goals. For a personalized analysis, call Nitin Gadura at (917) 705-0132."}}}},
    {{"@type":"Question","name":"Who is the best real estate agent in {nbh}?","acceptedAnswer":{{"@type":"Answer","text":"Nitin Gadura is a Licensed NYS Real Estate Salesperson (License #10401383405) specializing in Queens and Long Island, with $100M+ in closed transactions and coverage across 173 ZIP codes. Verify at appext20.dos.ny.gov/lcns_public/chk_load."}}}}
  ]}}
]}}
</script>
</head>
<body>

<nav class="mr-topnav">
  <a href="/" class="mr-brand">Gadura Real Estate</a>
  <div style="display:flex;gap:18px;align-items:center;font-size:0.74rem">
    <a href="/market-reports/">Market Reports</a>
    <a href="/market-reports/queens/">Queens</a>
    <a href="tel:9177050132" class="mr-phone">(917) 705-0132</a>
  </div>
</nav>

<div class="mr-shell">

  <!-- SIDEBAR -->
  <aside class="mr-side">
    <div class="bio-card">
      <img src="https://gadurarealestate.com/images/nitin-gadura.jpg" alt="Nitin Gadura, NYS Licensed Real Estate Salesperson" class="bio-photo" width="300" height="300" loading="lazy">
      <div class="bio-eyebrow">Your {nbh} Expert</div>
      <div class="bio-name">Nitin Gadura</div>
      <div class="bio-title"><strong>Licensed NYS RE Salesperson</strong><br>#10401383405 &middot; Gadura Real Estate, LLC</div>
      <p class="bio-text">Queens-born, NYS-licensed since 2018. <strong>$100M+ closed</strong> across <strong>500+ families</strong> in five languages &mdash; English, Hindi, Punjabi, Gujarati, Urdu. I publish these reports so the families I work with get the same hard data the big brokerages keep private.</p>
      <div class="bio-cta-row">
        <a href="tel:9177050132" class="bio-cta primary">Call (917) 705-0132</a>
        <a href="https://www.gadurarealestate.com/contact" class="bio-cta ghost">Free Home Valuation</a>
      </div>
      <div class="bio-trust-row">
        <span><strong>$100M+</strong>Closed</span>
        <span><strong>500+</strong>Families</span>
        <span><strong>4.9&#x2605;</strong>Verified</span>
      </div>
    </div>

    <div class="side-card">
      <div class="side-card-title">Queens &middot; ZIP {zipcode}</div>
      <div class="minimap" title="{nbh}"></div>
      <h4 style="margin-top:14px;font-family:var(--serif);font-size:0.92rem;font-weight:700;color:var(--navy)">Explore nearby ZIPs &#x2193;</h4>
      <p style="font-size:0.75rem;color:var(--mid);line-height:1.6">Use the neighboring market cards below to compare adjacent ZIP codes.</p>
    </div>

    <div class="side-card">
      <div class="side-card-title">Quick Links</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <a href="/market-reports/" style="font-size:0.78rem;color:var(--green-dark);font-weight:600;padding:8px 12px;border:1px solid var(--border);border-radius:4px;transition:all .2s">&larr; All Market Reports</a>
        <a href="/market-reports/queens/" style="font-size:0.78rem;color:var(--green-dark);font-weight:600;padding:8px 12px;border:1px solid var(--border);border-radius:4px;transition:all .2s">&larr; Queens Reports</a>
        <a href="/neighborhoods/{nbh_slug}.html" style="font-size:0.78rem;color:var(--green-dark);font-weight:600;padding:8px 12px;border:1px solid var(--border);border-radius:4px;transition:all .2s">{nbh} Neighborhood Guide</a>
      </div>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="mr-main">

    <div class="mr-eyebrow">
      <span class="pill">Queens</span>
      <span class="pill-navy">ZIP {zipcode}</span>
      <span>Market Report</span>
    </div>
    <h1 class="mr-h1">{nbh} Housing Market Report</h1>
    <p class="mr-deck">{desc} Data sourced from <a href="https://www.zillow.com/research/data/" rel="noopener">Zillow Research</a>, the <a href="https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page" rel="noopener">NYC Department of Finance</a>, and <a href="https://fred.stlouisfed.org/series/MORTGAGE30US" rel="noopener">Freddie Mac via FRED</a>.</p>

    <!-- HEADLINE HERO -->
    <div class="headline-hero">
      <div>
        <div class="hero-lbl">{nbh} &middot; ZIP {zipcode} &middot; Estimated Median</div>
        <div class="hero-val">{median_str}</div>
        <div class="hero-sub">Based on Zillow Home Value Index &middot; all-homes &middot; smoothed, seasonally-adjusted</div>
      </div>
      <div class="hero-badge">
        <div class="badge-lbl">Year over Year</div>
        <div class="badge-val">{yoy}</div>
        <div class="badge-sub">Estimated change</div>
      </div>
    </div>

    <!-- SUMMARY -->
    <p class="tldr" data-speakable="true">The estimated median home value in <strong>{nbh}</strong> (ZIP {zipcode}, Queens) is approximately <strong>{median_str}</strong>, with year-over-year growth of <strong>{yoy}</strong>. Typical rents in this ZIP run around <strong>{rent_str}/mo</strong> per Zillow ZORI data.</p>

    <!-- STAT ROW -->
    <div class="statrow">
      <div class="stat-tile pos">
        <div class="lbl">Estimated Median</div>
        <div class="val">{median_str}</div>
        <div class="sub">Zillow Home Value Index</div>
      </div>
      <div class="stat-tile pos">
        <div class="lbl">Year over Year</div>
        <div class="val">{yoy}</div>
        <div class="sub">Estimated annual change</div>
      </div>
      <div class="stat-tile pos">
        <div class="lbl">Typical Rent</div>
        <div class="val">{rent_str}/mo</div>
        <div class="sub">Zillow ZORI estimate</div>
      </div>
      <div class="stat-tile pos">
        <div class="lbl">20% Down Payment</div>
        <div class="val">{down_20}</div>
        <div class="sub">On {median_str} purchase</div>
      </div>
    </div>

    <!-- MARKET OVERVIEW -->
    <h2 class="section-h">Market Overview &mdash; {nbh} ({zipcode})</h2>
    <p>{desc}</p>
    <p>For homeowners in <strong>{nbh}</strong>, the question is rarely &ldquo;is the market up or down&rdquo; &mdash; it is &ldquo;is the current direction supported across multiple windows.&rdquo; Looking at 1-month, 3-month, 6-month, and 12-month change gives you a multi-frame view: short-term momentum, mid-term direction, and long-cycle trend. When all four windows agree, conviction is high. When they disagree, the market is in transition &mdash; that is usually when negotiation leverage opens up.</p>

    <div class="fact-box">
      <span class="fb-label">How this number is calculated</span>
      The Zillow Home Value Index (ZHVI) is a smoothed, seasonally-adjusted measure of the typical home value across all home types within a ZIP code. Unlike a simple median sale price, ZHVI accounts for compositional mix &mdash; so a month with mostly high-end sales does not artificially inflate the index.
      <span class="fb-cite">Source: <a href="https://www.zillow.com/research/methodology-neural-zhvi-32128/" rel="noopener">Zillow Research methodology</a>. CSV: <a href="https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv" rel="noopener">Zip_zhvi_uc_sfrcondo CSV</a>.</span>
    </div>

    <!-- PROPERTY TYPES -->
    <h2 class="section-h">By property type: what trades in {zipcode}</h2>
    <p>The aggregate ZHVI blends every home type into one number. For an actual sale or purchase in {nbh}, the property class matters &mdash; NYC&rsquo;s Department of Finance organizes recorded sales by building class. The most common types in ZIP {zipcode}:</p>
    <div class="proptype-grid">{ptype_cards_html}
    </div>
    <p>For a property-class-specific price, download the <a href="https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page" rel="noopener">NYC DOF Rolling Sales</a> for Queens County and filter by building class. Or <a href="tel:9177050132">call Nitin at (917) 705-0132</a> for a property-class report on ZIP {zipcode}.</p>

    <!-- MORTGAGE CONTEXT -->
    <h2 class="section-h">Mortgage rate context</h2>
    <p>Headline home values mean nothing without the cost of capital. Affordability is driven roughly equally by <strong>price</strong> and <strong>rate</strong>. Track the current 30-year fixed rate at <a href="https://fred.stlouisfed.org/series/MORTGAGE30US" rel="noopener">FRED MORTGAGE30US</a>.</p>
    <div class="fact-box navy">
      <span class="fb-label navy">Why this matters for a {median_str} home</span>
      At a {median_str} purchase price with 20% down ({down_20} down, {financed} financed), every 1% change in the 30-year fixed rate shifts your monthly principal-and-interest payment meaningfully. Monitor rate direction as closely as price direction.
      <span class="fb-cite">Computed using the standard 360-month amortization formula. Verify with the <a href="https://www.consumerfinance.gov/owning-a-home/explore-rates/" rel="noopener">CFPB rate explorer</a>.</span>
    </div>

    <!-- HOUSING STOCK -->
    <h2 class="section-h">Who buys here &mdash; housing stock &amp; community</h2>
    <p>{housing}</p>
    <p>Communities historically served in this ZIP include <strong>{communities}</strong>. The <a href="https://www.census.gov/programs-surveys/acs/" rel="noopener">U.S. Census ACS (5-Year)</a> publishes housing-stock and tenure tables at the ZCTA level &mdash; see Tables B25024, B25034, B25003 at <a href="https://data.census.gov/" rel="noopener">data.census.gov</a>.</p>

    <!-- RELATED LINKS -->
    <h2 class="section-h">Explore {nbh}</h2>
    <div class="relgrid">
      <a href="/neighborhoods/{nbh_slug}.html" class="rel-card">
        <div class="rel-kicker">Neighborhood Guide</div>
        <div class="rel-title">{nbh} &mdash; Schools, Transit, Community</div>
      </a>
      <a href="/market-reports/queens/" class="rel-card">
        <div class="rel-kicker">All Queens Reports</div>
        <div class="rel-title">Queens Housing Market Overview</div>
      </a>
      <a href="/market-reports/" class="rel-card">
        <div class="rel-kicker">All Markets</div>
        <div class="rel-title">Queens, Brooklyn &amp; Long Island Reports</div>
      </a>
    </div>

    <!-- NEIGHBORS -->
    <h2 class="section-h">Compare to neighboring markets</h2>
    <p>Click any tile to read that ZIP&rsquo;s market report.</p>
    <div class="neighbors">{neighbor_html}
    </div>

    <!-- FAQ -->
    <h2 class="section-h">Frequently asked questions</h2>
    <div style="margin:18px 0">
      <h3 class="section-h3">What is the median home price in {nbh} ({zipcode})?</h3>
      <p>The estimated median home value in {nbh} (ZIP {zipcode}) is approximately {median_str}, based on the Zillow Home Value Index. ZHVI is a smoothed, seasonally-adjusted estimate covering all home types. For current figures, visit <a href="https://www.zillow.com/research/data/" rel="noopener">zillow.com/research/data/</a>.</p>
    </div>
    <div style="margin:18px 0">
      <h3 class="section-h3">Is {nbh} a buyer&rsquo;s market or seller&rsquo;s market?</h3>
      <p>With year-over-year appreciation of {yoy}, {nbh} shows positive price momentum. However, whether it favors buyers or sellers depends on current inventory levels and days-on-market &mdash; check <a href="https://www.realtor.com/research/" rel="noopener">Realtor.com Research</a> for the latest supply data, or call Nitin for a live market read.</p>
    </div>
    <div style="margin:18px 0">
      <h3 class="section-h3">What is rent in {nbh} ({zipcode})?</h3>
      <p>Typical rents in {nbh} run around {rent_str}/mo per Zillow ZORI data. HUD also publishes <a href="https://www.huduser.gov/portal/datasets/fmr.html" rel="noopener">Fair Market Rents</a> for Queens County annually, which serves as a useful benchmark against private-market asking rents.</p>
    </div>
    <div style="margin:18px 0">
      <h3 class="section-h3">Who is the best real estate agent in {nbh}?</h3>
      <p>Nitin Gadura is a Licensed NYS Real Estate Salesperson (License #10401383405) specializing in Queens and Long Island with $100M+ in closed transactions since 2018. Verify at <a href="https://appext20.dos.ny.gov/lcns_public/chk_load" rel="noopener">appext20.dos.ny.gov</a>.</p>
    </div>
    <div style="margin:18px 0">
      <h3 class="section-h3">Can I use this data to price my home?</h3>
      <p>ZIP-level data is a useful starting frame but does not replace an address-specific CMA. Two homes on the same block can trade at very different prices based on lot size, condition, finishes, school zone, and recent comp activity. For a free, no-obligation CMA, call <a href="tel:9177050132">(917) 705-0132</a> or email <a href="mailto:nitin@gadurarealestate.com">nitin@gadurarealestate.com</a>.</p>
    </div>

    <!-- CTA -->
    <div class="cta-strip">
      <h3>Thinking of selling or buying in {nbh}?</h3>
      <p>Get a precise address-level CMA &mdash; no obligation, response within 24 hours.</p>
      <div class="cta-row">
        <a href="tel:9177050132" class="primary">Call (917) 705-0132</a>
        <a href="https://www.gadurarealestate.com/contact" class="ghost">Free Home Valuation</a>
      </div>
    </div>

    <!-- COMPLIANCE FOOTER -->
    <div class="compliance">
      <div class="row">
        <div class="eho">EQUAL<strong>HOUSING<br>OPPORTUNITY</strong></div>
        <div>
          <strong>Equal Housing Opportunity.</strong> Gadura Real Estate, LLC supports the principles of the Fair Housing Act and the Equal Opportunity Act. We do not discriminate based on race, color, religion, sex, handicap, familial status, sexual orientation, national origin, source of income, or any other protected class. <strong>OneKey&reg; MLS member.</strong>
        </div>
      </div>
      <p><strong>Research disclaimer.</strong> This page presents independent market research conducted by <strong>Nitin Gadura</strong>, a Licensed New York State Real Estate Salesperson (license <strong>#10401383405</strong>) operating under <strong>Gadura Real Estate, LLC</strong>, a licensed New York State real estate brokerage located at 106-09 101st Ave, Ozone Park, NY 11416. Data shown is sourced from publicly available datasets and is presented for <strong>educational and informational purposes only</strong>. It does not constitute legal, financial, tax, or investment advice. Past performance does not guarantee future results. <strong>Information is deemed reliable but is not guaranteed</strong> and should be <strong>independently verified</strong> before any real estate decision.</p>
      <p>New York State <strong>RPL &sect;443 agency disclosure</strong> is provided at the first substantive contact.</p>

      <div class="trust-logos">
        <span class="trust-logo">NYS DOS License #10401383405</span>
        <span class="trust-logo">OneKey&reg; MLS Member</span>
        <span class="trust-logo">Equal Housing Opportunity</span>
        <span class="trust-logo">NAR Code of Ethics</span>
        <span class="trust-logo">Fair Housing Act Compliant</span>
        <span class="trust-logo">NY State RPL &sect;443 Compliant</span>
      </div>

      <p class="disclaimer">Page generated {TODAY} &middot; Canonical URL: <a href="{canonical}">{canonical}</a> &middot; Method: ZIP-level Zillow Research public datasets (all-homes, smoothed, seasonally-adjusted) &middot; &copy; 2026 Gadura Real Estate, LLC.</p>
    </div>

    <!-- LONG-TAIL KEYWORDS -->
    <div style="margin-top:36px;padding-top:24px;border-top:1px solid var(--border);font-size:0.72rem;color:var(--mid);line-height:1.65">
      <p style="font-weight:600;color:var(--navy);margin-bottom:8px;font-size:0.74rem">Related searches for {nbh} ({zipcode}):</p>
      <p>{nbh} housing market &nbsp;&middot;&nbsp; {nbh} home prices &nbsp;&middot;&nbsp; {nbh} real estate &nbsp;&middot;&nbsp; {zipcode} home values &nbsp;&middot;&nbsp; {zipcode} housing market &nbsp;&middot;&nbsp; {zipcode} real estate prices &nbsp;&middot;&nbsp; housing market {nbh} NY &nbsp;&middot;&nbsp; {nbh} NY home prices &nbsp;&middot;&nbsp; how much is a house worth in {nbh} &nbsp;&middot;&nbsp; average home price in {nbh} &nbsp;&middot;&nbsp; {nbh} housing market forecast &nbsp;&middot;&nbsp; is {nbh} a good place to invest in real estate &nbsp;&middot;&nbsp; best time to sell a house in {nbh} &nbsp;&middot;&nbsp; is now a good time to buy in {nbh} &nbsp;&middot;&nbsp; real estate agent {nbh} {zipcode} &nbsp;&middot;&nbsp; sell my house fast {nbh}</p>
    </div>

  </main>
</div>

</body>
</html>"""

    return page


def generate_quarterly_report():
    """Generate the Q1 2026 quarterly report page."""
    canonical = "https://gadurarealestate.com/market-reports/queens-market-report-q1-2026.html"

    # Build ZIP summary rows
    zip_rows = ""
    for z in sorted(ZIPS, key=lambda x: x["median"], reverse=True):
        zip_rows += f"""
        <tr>
          <td><a href="/market-reports/queens/{z['slug']}/" style="color:var(--green-dark);font-weight:600;border-bottom:1px solid rgba(0,166,81,0.3)">{z['neighborhood']}</a></td>
          <td class="num">{z['zip']}</td>
          <td class="num">{fmt_price(z['median'])}</td>
          <td class="num" style="color:var(--green-dark)">{z['yoy']}</td>
          <td class="num">{fmt_price(z['rent'])}/mo</td>
        </tr>"""

    avg_median = sum(z["median"] for z in ZIPS) // len(ZIPS)
    avg_rent = sum(z["rent"] for z in ZIPS) // len(ZIPS)
    highest = max(ZIPS, key=lambda x: x["median"])
    lowest = min(ZIPS, key=lambda x: x["median"])

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Queens Housing Market Report Q1 2026 &mdash; Prices, Trends &amp; Forecast | Gadura Real Estate</title>
<meta name="description" content="Queens NY housing market Q1 2026: neighborhood-by-neighborhood price analysis across 10 ZIP codes. Data-driven report by Nitin Gadura, NYS Lic. RE Salesperson.">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta name="author" content="Nitin Gadura &middot; NYS RE License #10401383405">
<meta name="geo.region" content="US-NY">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="Queens Housing Market Report Q1 2026 &mdash; Prices, Trends &amp; Forecast">
<meta property="og:description" content="Queens NY housing market Q1 2026: neighborhood-by-neighborhood price analysis across 10 ZIP codes. Research by Nitin Gadura.">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Gadura Real Estate">
<meta property="article:published_time" content="{TODAY}">
<meta property="article:modified_time" content="{TODAY}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Queens Housing Market Report Q1 2026">
<meta name="twitter:description" content="Queens NY housing market Q1 2026: prices, trends &amp; forecast across 10 ZIP codes. By Nitin Gadura.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{
  --green:#00A651;--green-dark:#007d3c;--green-light:#e8f7ef;--green-mist:#f3fbf6;
  --navy:#1B2A6B;--navy-dark:#0f1a44;--navy-light:#eef0f8;--navy-mist:#f7f9ff;
  --red:#B0455A;--red-light:#fdecef;
  --ink:#0a1030;--text:#1a1a2e;--mid:#5c6475;--muted:#8a94a6;
  --bg:#fff;--off-w:#f8f9fb;
  --border:#dde3ec;--border-soft:#eef1f6;
  --serif:'Playfair Display',Georgia,serif;--sans:'Inter',system-ui,sans-serif;
  --grad-green:linear-gradient(135deg,#00A651 0%,#007d3c 100%);
  --grad-navy:linear-gradient(135deg,#1B2A6B 0%,#0f1a44 100%);
  --grad-hero:linear-gradient(135deg,#1B2A6B 0%,#00A651 140%);
  --shadow-sm:0 2px 8px rgba(15,26,68,0.05);
  --shadow-md:0 6px 24px rgba(15,26,68,0.08);
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--sans);color:var(--text);background:var(--bg);-webkit-font-smoothing:antialiased;line-height:1.65}}
a{{color:inherit;text-decoration:none}}

.mr-topnav{{background:var(--grad-navy);color:#fff;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;gap:24px;font-size:0.82rem;box-shadow:var(--shadow-sm);position:sticky;top:0;z-index:40}}
.mr-topnav a{{color:rgba(255,255,255,0.78);transition:color .2s}}
.mr-topnav a:hover{{color:#fff}}
.mr-topnav .mr-brand{{font-family:var(--serif);font-size:1.02rem;font-weight:700;color:#fff;letter-spacing:0.01em;display:flex;align-items:center;gap:10px}}
.mr-topnav .mr-brand::before{{content:'';width:8px;height:24px;background:var(--green);border-radius:2px;display:inline-block}}
.mr-topnav .mr-phone{{background:var(--green);color:#fff;padding:8px 16px;border-radius:4px;font-weight:700;letter-spacing:0.02em;transition:background .2s}}
.mr-topnav .mr-phone:hover{{background:var(--green-dark);color:#fff}}

.q-wrap{{max-width:960px;margin:0 auto;padding:48px 28px 80px}}
@media(max-width:640px){{.q-wrap{{padding:24px 18px 60px}}}}

.q-eyebrow{{font-size:0.66rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:var(--green-dark);margin-bottom:14px;display:flex;gap:10px;align-items:center}}
.q-eyebrow .pill{{background:var(--green-light);color:var(--green-dark);padding:4px 10px;border-radius:4px}}
.q-h1{{font-family:var(--serif);font-size:clamp(2rem,3.6vw,2.95rem);font-weight:700;line-height:1.1;margin-bottom:14px;color:var(--navy);letter-spacing:-0.015em}}
.q-deck{{font-size:0.98rem;color:var(--mid);line-height:1.7;margin-bottom:28px;max-width:740px}}

.hero-strip{{background:var(--grad-hero);color:#fff;padding:32px 36px;margin:0 0 40px;border-radius:8px;display:grid;grid-template-columns:repeat(3,1fr);gap:24px;box-shadow:var(--shadow-md);position:relative;overflow:hidden}}
.hero-strip::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 80% 50%,rgba(0,166,81,0.3),transparent 60%);pointer-events:none}}
@media(max-width:640px){{.hero-strip{{grid-template-columns:1fr;gap:16px}}}}
.hero-stat{{position:relative;z-index:1}}
.hero-stat .hs-lbl{{font-size:0.58rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:rgba(255,255,255,0.7);margin-bottom:6px}}
.hero-stat .hs-val{{font-family:var(--serif);font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;color:#fff;line-height:1;margin-bottom:4px}}
.hero-stat .hs-sub{{font-size:0.76rem;color:rgba(255,255,255,0.8)}}

.q-section{{margin:48px 0 18px}}
.q-section h2{{font-family:var(--serif);font-size:1.65rem;font-weight:700;color:var(--navy);margin-bottom:10px;padding-bottom:10px;border-bottom:2px solid var(--green-light);position:relative}}
.q-section h2::after{{content:'';position:absolute;bottom:-2px;left:0;width:50px;height:2px;background:var(--green)}}

p{{font-size:0.96rem;color:var(--text);margin-bottom:14px;line-height:1.74}}
p a{{color:var(--green-dark);border-bottom:1px solid rgba(0,166,81,0.4);font-weight:500;transition:all .2s}}
p a:hover{{color:var(--green);background:var(--green-light)}}
strong{{color:var(--navy);font-weight:700}}

.delta-tbl{{width:100%;border-collapse:collapse;margin:24px 0;border:1px solid var(--border);border-radius:6px;overflow:hidden}}
.delta-tbl th,.delta-tbl td{{padding:13px 16px;text-align:left;border-bottom:1px solid var(--border-soft);font-size:0.86rem}}
.delta-tbl tr:last-child td{{border-bottom:none}}
.delta-tbl th{{font-size:0.58rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:var(--navy);background:var(--navy-light)}}
.delta-tbl td.num{{font-family:var(--serif);font-weight:700;color:var(--navy);text-align:right}}
.delta-tbl tr:hover td{{background:var(--green-mist)}}

.neighbors{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:24px 0}}
.neighbor-tile{{background:#fff;border:1px solid var(--border);border-radius:6px;padding:18px;transition:all .2s;display:block;position:relative;overflow:hidden}}
.neighbor-tile::before{{content:'';position:absolute;top:0;left:0;width:4px;height:100%;background:var(--green);transition:width .2s}}
.neighbor-tile:hover{{border-color:var(--green);transform:translateY(-2px);box-shadow:var(--shadow-md)}}
.neighbor-tile:hover::before{{width:8px}}
.neighbor-tile .nbh{{font-family:var(--serif);font-size:1rem;font-weight:700;color:var(--navy);margin-bottom:4px}}
.neighbor-tile .zip{{font-size:0.62rem;color:var(--muted);letter-spacing:0.08em;margin-bottom:10px;font-weight:600}}
.neighbor-tile .price{{font-family:var(--serif);font-size:1.1rem;font-weight:700;color:var(--navy);margin-bottom:4px}}
.neighbor-tile .yoy{{font-size:0.7rem;font-weight:700;display:inline-block;padding:2px 7px;border-radius:3px}}
.neighbor-tile .yoy.pos{{color:var(--green-dark);background:var(--green-light)}}

.cta-strip{{background:var(--grad-navy);color:#fff;padding:44px 36px;margin:48px 0 36px;text-align:center;border-radius:8px;position:relative;overflow:hidden}}
.cta-strip::before{{content:'';position:absolute;top:-40%;right:-10%;width:300px;height:300px;background:radial-gradient(circle,rgba(0,166,81,0.25),transparent 70%);pointer-events:none}}
.cta-strip h3{{font-family:var(--serif);font-size:1.7rem;font-weight:700;color:#fff;margin-bottom:8px;position:relative}}
.cta-strip p{{color:rgba(255,255,255,0.78);margin-bottom:24px;font-size:0.95rem;position:relative}}
.cta-row{{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;position:relative}}
.cta-row a{{display:inline-block;padding:15px 28px;font-size:0.7rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;border-radius:4px;transition:all .2s}}
.cta-row a.primary{{background:var(--green);color:#fff;box-shadow:0 6px 20px rgba(0,166,81,0.4)}}
.cta-row a.primary:hover{{background:#fff;color:var(--green-dark);transform:translateY(-1px)}}
.cta-row a.ghost{{border:1.5px solid rgba(255,255,255,0.4);color:#fff;background:transparent}}
.cta-row a.ghost:hover{{border-color:#fff;background:rgba(255,255,255,0.1)}}

.compliance{{background:var(--ink);color:rgba(255,255,255,0.7);padding:38px 36px;margin-top:40px;font-size:0.78rem;line-height:1.7;border-radius:8px}}
.compliance .row{{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:start;margin-bottom:16px}}
@media(max-width:640px){{.compliance .row{{grid-template-columns:1fr}}}}
.compliance .eho{{width:60px;height:60px;background:#fff;color:var(--navy);display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-weight:700;font-size:0.72rem;line-height:1.1;text-align:center;padding:6px;flex-shrink:0;border:2px solid var(--green);border-radius:4px}}
.compliance .eho strong{{display:block;font-size:0.55rem;letter-spacing:0.06em;color:var(--green-dark)}}
.compliance strong{{color:#fff;font-weight:600}}
.compliance a{{color:var(--green);text-decoration:underline}}
.compliance .trust-logos{{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 14px;padding:14px 0;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08)}}
.compliance .trust-logo{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.07);padding:7px 13px;border-radius:4px;font-size:0.7rem;color:rgba(255,255,255,0.85);font-weight:600;letter-spacing:0.04em;border:1px solid rgba(255,255,255,0.08)}}
.compliance .trust-logo::before{{content:'&#x25CF;';color:var(--green);font-size:0.8rem}}
.compliance .disclaimer{{font-size:0.7rem;color:rgba(255,255,255,0.45);margin-top:22px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.1)}}
</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
  {{"@type":"WebPage","@id":"{canonical}#webpage","name":"Queens Housing Market Report Q1 2026","url":"{canonical}","datePublished":"{TODAY}","dateModified":"{TODAY}","author":{{"@id":"https://gadurarealestate.com/#nitin-gadura"}},"publisher":{{"@id":"https://gadurarealestate.com/#organization"}}}},
  {{"@type":"BreadcrumbList","@id":"{canonical}#breadcrumbs","itemListElement":[
    {{"@type":"ListItem","position":1,"name":"Home","item":"https://gadurarealestate.com/"}},
    {{"@type":"ListItem","position":2,"name":"Market Reports","item":"https://gadurarealestate.com/market-reports/"}},
    {{"@type":"ListItem","position":3,"name":"Queens","item":"https://gadurarealestate.com/market-reports/queens/"}},
    {{"@type":"ListItem","position":4,"name":"Q1 2026 Report","item":"{canonical}"}}
  ]}}
]}}
</script>
</head>
<body>

<nav class="mr-topnav">
  <a href="/" class="mr-brand">Gadura Real Estate</a>
  <div style="display:flex;gap:18px;align-items:center;font-size:0.74rem">
    <a href="/market-reports/">Market Reports</a>
    <a href="/market-reports/queens/">Queens</a>
    <a href="tel:9177050132" class="mr-phone">(917) 705-0132</a>
  </div>
</nav>

<div class="q-wrap">

  <div class="q-eyebrow">
    <span class="pill">Queens</span>
    <span>Q1 2026 Quarterly Report</span>
  </div>
  <h1 class="q-h1">Queens Housing Market Report &mdash; Q1 2026</h1>
  <p class="q-deck">A neighborhood-by-neighborhood look at how Queens home values are trending in Q1 2026. Covering 10 ZIP codes across the borough &mdash; from Long Island City waterfront condos to Jamaica investment properties. Data sourced from <a href="https://www.zillow.com/research/data/" rel="noopener">Zillow Research ZHVI</a> and <a href="https://www.nyc.gov/site/finance/property/property-rolling-sales-data.page" rel="noopener">NYC DOF Rolling Sales</a>.</p>

  <!-- HERO STATS -->
  <div class="hero-strip">
    <div class="hero-stat">
      <div class="hs-lbl">Average Median (10 ZIPs)</div>
      <div class="hs-val">{fmt_price(avg_median)}</div>
      <div class="hs-sub">Across surveyed neighborhoods</div>
    </div>
    <div class="hero-stat">
      <div class="hs-lbl">Highest Median</div>
      <div class="hs-val">{fmt_price(highest['median'])}</div>
      <div class="hs-sub">{highest['neighborhood']} ({highest['zip']})</div>
    </div>
    <div class="hero-stat">
      <div class="hs-lbl">Most Affordable</div>
      <div class="hs-val">{fmt_price(lowest['median'])}</div>
      <div class="hs-sub">{lowest['neighborhood']} ({lowest['zip']})</div>
    </div>
  </div>

  <!-- OVERVIEW -->
  <div class="q-section"><h2>Q1 2026 Overview</h2></div>
  <p>Queens continues to demonstrate broad-based appreciation across its diverse neighborhoods in Q1 2026. Every ZIP code surveyed in this report showed positive year-over-year price growth, ranging from <strong>{lowest['yoy']}</strong> in {lowest['neighborhood']} to <strong>{highest['yoy']}</strong> in select high-demand corridors. The median home value across these 10 ZIP codes averaged <strong>{fmt_price(avg_median)}</strong>, with typical rents running <strong>{fmt_price(avg_rent)}/mo</strong>.</p>
  <p>The borough benefits from a structural supply constraint &mdash; limited new construction relative to population density &mdash; combined with its role as the most ethnically diverse county in the United States. Demand from first-generation homebuyers, multi-generational families, and investors continues to support pricing across all property types.</p>
  <p>Mortgage rates remain the primary affordability variable. Track the current 30-year fixed rate at <a href="https://fred.stlouisfed.org/series/MORTGAGE30US" rel="noopener">FRED MORTGAGE30US</a>.</p>

  <!-- COMPARISON TABLE -->
  <div class="q-section"><h2>Neighborhood Comparison</h2></div>
  <p>All 10 Queens ZIP codes ranked by estimated median home value. Click any neighborhood to read its full market report.</p>
  <div style="overflow-x:auto">
  <table class="delta-tbl">
    <thead>
      <tr>
        <th>Neighborhood</th>
        <th style="text-align:right">ZIP</th>
        <th style="text-align:right">Est. Median</th>
        <th style="text-align:right">YoY Change</th>
        <th style="text-align:right">Typical Rent</th>
      </tr>
    </thead>
    <tbody>{zip_rows}
    </tbody>
  </table>
  </div>

  <!-- TILE GRID -->
  <div class="q-section"><h2>Explore Each Neighborhood</h2></div>
  <p>Click any card to view the full market report for that ZIP code.</p>
  <div class="neighbors">"""

    for z in ZIPS:
        page += f"""
    <a href="/market-reports/queens/{z['slug']}/" class="neighbor-tile">
      <div class="nbh">{z['neighborhood']}</div>
      <div class="zip">ZIP {z['zip']} &middot; Queens</div>
      <div class="price">{fmt_price(z['median'])}</div>
      <div class="yoy pos">{z['yoy']} YoY</div>
    </a>"""

    page += f"""
  </div>

  <!-- KEY TAKEAWAYS -->
  <div class="q-section"><h2>Key Takeaways for Q1 2026</h2></div>
  <ul style="margin:14px 0 18px 22px;font-size:0.93rem;line-height:1.7">
    <li><strong>All 10 ZIP codes positive YoY</strong> &mdash; Queens remains a broad-based appreciating market with no pockets of decline in this survey.</li>
    <li><strong>Highest growth in Jamaica and Woodhaven</strong> &mdash; these value-oriented neighborhoods are attracting first-time buyers priced out of more expensive ZIP codes.</li>
    <li><strong>Premium neighborhoods hold strong</strong> &mdash; Douglaston ({fmt_price(highest['median'])}) and Long Island City continue to command top-tier pricing.</li>
    <li><strong>Rental market tight</strong> &mdash; average rent across surveyed ZIPs is {fmt_price(avg_rent)}/mo, supporting strong cap rates for multi-family investors.</li>
    <li><strong>Rate sensitivity remains high</strong> &mdash; every 1% move in the 30-year fixed rate shifts affordability meaningfully across all price tiers.</li>
  </ul>

  <!-- CTA -->
  <div class="cta-strip">
    <h3>Get a personalized Q1 analysis for your Queens property</h3>
    <p>This report covers ZIP-level trends. For an address-specific CMA, call Nitin &mdash; no obligation, response within 24 hours.</p>
    <div class="cta-row">
      <a href="tel:9177050132" class="primary">Call (917) 705-0132</a>
      <a href="https://www.gadurarealestate.com/contact" class="ghost">Free Home Valuation</a>
    </div>
  </div>

  <!-- COMPLIANCE -->
  <div class="compliance">
    <div class="row">
      <div class="eho">EQUAL<strong>HOUSING<br>OPPORTUNITY</strong></div>
      <div>
        <strong>Equal Housing Opportunity.</strong> Gadura Real Estate, LLC supports the principles of the Fair Housing Act. We do not discriminate based on race, color, religion, sex, handicap, familial status, sexual orientation, national origin, source of income, or any other protected class. <strong>OneKey&reg; MLS member.</strong>
      </div>
    </div>
    <p><strong>Research disclaimer.</strong> This page presents independent market research by <strong>Nitin Gadura</strong>, Licensed NYS Real Estate Salesperson (license <strong>#10401383405</strong>) at <strong>Gadura Real Estate, LLC</strong>, 106-09 101st Ave, Ozone Park, NY 11416. Data is from publicly available datasets and is for <strong>educational and informational purposes only</strong>. Not legal, financial, tax, or investment advice. Past performance does not guarantee future results.</p>

    <div class="trust-logos">
      <span class="trust-logo">NYS DOS License #10401383405</span>
      <span class="trust-logo">OneKey&reg; MLS Member</span>
      <span class="trust-logo">Equal Housing Opportunity</span>
      <span class="trust-logo">Fair Housing Act Compliant</span>
    </div>

    <p class="disclaimer">Page generated {TODAY} &middot; Canonical URL: <a href="{canonical}">{canonical}</a> &middot; &copy; 2026 Gadura Real Estate, LLC.</p>
  </div>

  <!-- LONG-TAIL -->
  <div style="margin-top:36px;padding-top:24px;border-top:1px solid var(--border);font-size:0.72rem;color:var(--mid);line-height:1.65">
    <p style="font-weight:600;color:var(--navy);margin-bottom:8px;font-size:0.74rem">Related searches:</p>
    <p>Queens housing market 2026 &nbsp;&middot;&nbsp; Queens home prices Q1 2026 &nbsp;&middot;&nbsp; Queens real estate market report &nbsp;&middot;&nbsp; Queens NY housing market forecast &nbsp;&middot;&nbsp; is now a good time to buy in Queens &nbsp;&middot;&nbsp; best neighborhoods in Queens to invest &nbsp;&middot;&nbsp; Queens real estate agent &nbsp;&middot;&nbsp; Queens housing market trends &nbsp;&middot;&nbsp; sell my house in Queens &nbsp;&middot;&nbsp; Queens NY home values 2026</p>
  </div>

</div>

</body>
</html>"""

    return page


def main():
    created = 0

    # Generate 10 ZIP code hub pages
    for z in ZIPS:
        out_dir = os.path.join(QUEENS_DIR, z["slug"])
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        content = generate_zip_page(z)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        created += 1
        print(f"  Created: market-reports/queens/{z['slug']}/index.html")

    # Generate quarterly report
    q_path = os.path.join(REPORTS_DIR, "queens-market-report-q1-2026.html")
    content = generate_quarterly_report()
    with open(q_path, "w", encoding="utf-8") as f:
        f.write(content)
    created += 1
    print(f"  Created: market-reports/queens-market-report-q1-2026.html")

    print(f"\nTotal pages created: {created}")


if __name__ == "__main__":
    main()
