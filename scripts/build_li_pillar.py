#!/usr/bin/env python3
"""
build_li_pillar.py — generate the Long Island pillar page (long-island/index.html)
and add a "Long Island" link to the sitewide plain-<nav> menu.

Audit findings (high): the 126-page Long Island cluster has NO pillar/hub page,
nothing links /long-island/, it's absent from the global nav, and 63 pages sit
>=4 clicks deep. This creates the authoritative LI entity/hub page linking every
Nassau + Suffolk town page with keyword-rich anchors, and exposes it sitewide.

Idempotent. Stdlib only.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "long-island" / "index.html"
DOMAIN = "https://gadurarealestate.com"

NAV_OLD = '<a href="/neighborhoods/">Neighborhoods</a>'
NAV_NEW = '<a href="/neighborhoods/">Neighborhoods</a>\n      <a href="/long-island/">Long Island</a>'
NAV_OLD2 = '<a href="/neighborhoods.html">Neighborhoods</a>'
NAV_NEW2 = '<a href="/neighborhoods.html">Neighborhoods</a>\n      <a href="/long-island/">Long Island</a>'


def town_name(p: Path) -> str:
    """Derive display name from slug; prefer the page's <h1>/<title> town if clean."""
    slug = p.stem
    slug = re.sub(r"-(nassau|suffolk)$", "", slug)
    name = slug.replace("-", " ").title()
    fixes = {"Ny": "NY", "Li ": "LI "}
    for a, b in fixes.items():
        name = name.replace(a, b)
    return name


def collect(county: str) -> list[tuple[str, str]]:
    d = ROOT / "long-island" / county
    out = []
    for p in sorted(d.glob("*.html")):
        if p.name == "index.html":
            continue
        out.append((town_name(p), f"/long-island/{county}/{p.name}"))
    return out


def link_grid(items: list[tuple[str, str]]) -> str:
    links = []
    for name, href in items:
        links.append(
            f'<a href="{html.escape(href)}" style="display:block;padding:10px 14px;'
            f'background:#fff;border:1px solid rgba(11,34,64,.12);border-radius:6px;'
            f'color:#1b2a6b;text-decoration:none;font-size:.95rem;">'
            f'Homes for sale in {html.escape(name)}</a>'
        )
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));'
            'gap:10px;margin:1.2rem 0 2.5rem;">' + "\n".join(links) + "</div>")


def build_page(nassau: list, suffolk: list) -> str:
    total = len(nassau) + len(suffolk)
    towns_schema = ",".join(
        f'{{"@type":"City","name":{name!r}}}'.replace("'", '"')
        for name, _ in (nassau + suffolk)[:40]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Long Island Homes for Sale — Nassau &amp; Suffolk County | Gadura Real Estate</title>
<meta name="description" content="Browse homes for sale across {total} Long Island towns. Nassau County &amp; Suffolk County houses, expert local agents, multilingual service. Family-owned since 2006. Call (718) 850-0010.">
<link rel="canonical" href="{DOMAIN}/long-island/">
<meta name="robots" content="index, follow">
<meta property="og:title" content="Long Island Homes for Sale — Nassau &amp; Suffolk County">
<meta property="og:description" content="Your Long Island real estate hub: {total} town guides across Nassau and Suffolk County with a family-owned brokerage.">
<meta property="og:url" content="{DOMAIN}/long-island/">
<meta property="og:type" content="website">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="stylesheet" href="/css/style.css">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","@id":"{DOMAIN}/long-island/#webpage","url":"{DOMAIN}/long-island/","name":"Long Island Homes for Sale — Nassau & Suffolk County","description":"Hub for {total} Long Island town guides.","isPartOf":{{"@id":"{DOMAIN}/#website"}},"about":{{"@type":"Place","name":"Long Island, NY","containsPlace":[{towns_schema}]}},"provider":{{"@id":"{DOMAIN}/#brokerage"}}}}</script>
<script type="application/ld+json" id="ai-breadcrumb-schema">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{DOMAIN}/"}},{{"@type":"ListItem","position":2,"name":"Long Island","item":"{DOMAIN}/long-island/"}}]}}</script>
</head>
<body data-page-type="pillar_hub" data-location="Long Island">

<header>
  <div class="header-inner" style="max-width:1200px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;">
    <a href="/" style="font-weight:700;font-size:1.15rem;color:#1b2a6b;text-decoration:none;">Gadura Real Estate</a>
    <nav>
      <a href="/buy.html">Buy</a>
      <a href="/sell.html">Sell</a>
      <a href="/neighborhoods/">Neighborhoods</a>
      <a href="/long-island/">Long Island</a>
      <a href="/meet-the-agents.html">Agents</a>
      <a href="tel:+17188500010">(718) 850-0010</a>
    </nav>
  </div>
</header>
<nav data-gre-breadcrumb aria-label="Breadcrumb" style="max-width:1200px;margin:0 auto;padding:10px 20px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;font-size:.82rem;color:#5b6675;"><a href="/" style="color:#1b2a6b;text-decoration:none;">Home</a><span aria-hidden="true" style="margin:0 7px;color:#9aa4b2;">&rsaquo;</span><span style="color:#5b6675;">Long Island</span></nav>

<main style="max-width:1200px;margin:0 auto;padding:0 20px 3rem;">

  <section style="background:linear-gradient(160deg,#14215c,#1b2a6b 60%,#25368a);color:#fff;border-radius:12px;padding:clamp(2.2rem,5vw,4rem) clamp(1.4rem,4vw,3rem);margin:1rem 0 2.5rem;">
    <p style="text-transform:uppercase;letter-spacing:.2em;font-size:.75rem;color:#8fd6ae;margin:0 0 .8rem;">Nassau County · Suffolk County · Since 2006</p>
    <h1 style="font-size:clamp(1.9rem,4.5vw,3.2rem);line-height:1.12;margin:0 0 1rem;color:#fff;">Long Island Homes for Sale</h1>
    <p style="max-width:62ch;color:rgba(255,255,255,.88);line-height:1.7;margin:0 0 1.5rem;">Explore {total} Long Island communities with a family-owned brokerage that knows every one of them. From Valley Stream and Hicksville to Babylon and the Hamptons approaches — multilingual agents, honest guidance, and buyer &amp; seller representation across Nassau and Suffolk County.</p>
    <p style="margin:0;"><a href="/home-valuation.html" style="display:inline-block;background:#00a651;color:#fff;font-weight:700;padding:.85rem 1.6rem;border-radius:6px;text-decoration:none;">Free Home Valuation</a>
    <a href="/contact.html" style="display:inline-block;color:#fff;border:1.5px solid rgba(255,255,255,.5);padding:.85rem 1.6rem;border-radius:6px;text-decoration:none;margin-left:.6rem;">Talk to an Agent</a></p>
  </section>

  <section>
    <h2 style="color:#14215c;font-size:clamp(1.5rem,3vw,2.1rem);margin-bottom:.4rem;">Nassau County Homes for Sale</h2>
    <p style="color:#5b6675;max-width:70ch;line-height:1.7;">Closer to Queens with top school districts and commuter-friendly LIRR lines — <a href="/long-island/nassau/index.html" style="color:#1b2a6b;">browse the full Nassau County guide</a> or jump into a town:</p>
    {link_grid(nassau)}
  </section>

  <section>
    <h2 style="color:#14215c;font-size:clamp(1.5rem,3vw,2.1rem);margin-bottom:.4rem;">Suffolk County Homes for Sale</h2>
    <p style="color:#5b6675;max-width:70ch;line-height:1.7;">More space, newer builds, and waterfront value further east — <a href="/long-island/suffolk/index.html" style="color:#1b2a6b;">browse the full Suffolk County guide</a> or pick a town:</p>
    {link_grid(suffolk)}
  </section>

  <section style="background:#f4f6f9;border:1px solid rgba(11,34,64,.12);border-radius:10px;padding:1.6rem;margin-top:1rem;">
    <h2 style="color:#14215c;font-size:1.25rem;margin-bottom:.6rem;">Also serving Queens &amp; Brooklyn</h2>
    <p style="color:#5b6675;line-height:1.7;margin:0;">Moving from the boroughs? Start with our
      <a href="/neighborhoods.html" style="color:#1b2a6b;">Queens &amp; Brooklyn neighborhood guides</a>,
      check <a href="/market-reports/" style="color:#1b2a6b;">monthly market reports</a>,
      browse <a href="/homes-for-sale/all-listings.html" style="color:#1b2a6b;">all listings</a>,
      or search by <a href="/zip/" style="color:#1b2a6b;">ZIP code</a>.</p>
  </section>

</main>

<footer style="background:#14215c;color:rgba(255,255,255,.8);padding:2rem 20px;text-align:center;font-size:.85rem;margin-top:2rem;">
  <p style="margin:0 0 .5rem;"><strong style="color:#fff;">Gadura Real Estate LLC</strong> · 106-09 101st Ave, Ozone Park, NY 11416 · <a href="tel:+17188500010" style="color:#8fd6ae;">(718) 850-0010</a></p>
  <p style="margin:0;">Licensed NYS Real Estate Broker · Serving Queens, Brooklyn, Nassau &amp; Suffolk since 2006</p>
</footer>

</body>
</html>
"""


def patch_nav() -> int:
    n = 0
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith((".git", "v2/", "_includes/", "scripts/", "admin/")):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if '/long-island/"' in t and 'href="/long-island/">Long Island</a>' in t:
            continue
        nt = t
        if NAV_OLD in nt and NAV_NEW not in nt:
            nt = nt.replace(NAV_OLD, NAV_NEW, 1)
        elif NAV_OLD2 in nt and NAV_NEW2 not in nt:
            nt = nt.replace(NAV_OLD2, NAV_NEW2, 1)
        if nt != t:
            p.write_text(nt, encoding="utf-8")
            n += 1
    return n


def main() -> int:
    nassau = collect("nassau")
    suffolk = collect("suffolk")
    print(f"Nassau towns: {len(nassau)} | Suffolk towns: {len(suffolk)}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build_page(nassau, suffolk), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    if "--no-nav" not in sys.argv:
        n = patch_nav()
        print(f"Added 'Long Island' to the nav on {n} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
