#!/usr/bin/env python3
"""
build_price_pages.py — Generates SUBSTANTIVE buyer-intent landing pages
("Homes for Sale Under $750K in Queens", "$1M+ Homes in Nassau County", ...).

Each page is backed by REAL matching listings from homes/ + live market stats,
so it targets high-intent searches without being thin/doorway content.
Pages are only generated where >=2 real listings match the (scope, price-tier).

Run from repo root:  python3 scripts/build_price_pages.py
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import rebuild_property_pages as rp

REPO    = rp.REPO
BASE    = rp.BASE_URL
OUTDIR  = os.path.join(REPO, 'homes-for-sale')

# city → region
QUEENS = {'Ozone Park','South Ozone Park','Ozone Park North','Richmond Hill','South Richmond Hill',
          'Richmond Hill S.','Jamaica','Jamaica Estates','South Jamaica','Woodhaven','Howard Beach',
          'Queens Village','Springfield Gardens','St. Albans','Rosedale','Cambria Heights','Kew Gardens',
          'Briarwood','Middle Village','Glendale','Far Rockaway','Hollis','Holliswood','Forest Hills'}
NASSAU = {'Elmont','Valley Stream','Baldwin','Hempstead','West Hempstead','Lynbrook','Rockville Centre',
          'Merrick','Freeport','Franklin Square','Floral Park','Garden City','Mineola','New Hyde Park'}
SUFFOLK = {'North Babylon','Selden','Holbrook','Amityville','Lindenhurst'}

def region_of(city):
    if city in QUEENS: return 'Queens'
    if city in NASSAU: return 'Nassau County'
    if city in SUFFOLK: return 'Suffolk County'
    if city == 'Brooklyn': return 'Brooklyn'
    return None

# price tiers: (slug, label, low, high)
TIERS = [
    ('under-500k',   'Under $500,000',    0,        500000),
    ('500k-to-750k', '$500K to $750K',    500000,   750000),
    ('750k-to-1m',   '$750K to $1M',      750000,   1000000),
    ('1m-to-1-5m',   '$1M to $1.5M',      1000000,  1500000),
    ('over-1-5m',    '$1.5M and Up',      1500000,  10**9),
]

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def money(n):
    return '$' + rp.fmt_int(n)

PAGE_CSS = """<style>
:root{--navy:#1b2a6b;--green:#00a651;--gold:#00a651}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;color:#1b2433;background:#fff}
.bp-head{background:var(--navy);color:#fff;padding:14px 0}
.bp-in,.bp-wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.bp-head-in{display:flex;align-items:center;justify-content:space-between;gap:16px;max-width:1180px;margin:0 auto;padding:0 20px}
.bp-head img{height:40px}.bp-head nav a{color:rgba(255,255,255,.85);text-decoration:none;font-weight:600;font-size:.85rem;margin-left:16px}
.bp-head nav a:hover{color:var(--gold)}
.bp-hero{background:linear-gradient(135deg,#1b2a6b,#16284a);color:#fff;padding:42px 0 34px}
.bp-bc{font-size:.8rem;color:rgba(255,255,255,.6);margin-bottom:10px}.bp-bc a{color:rgba(255,255,255,.75);text-decoration:none}
.bp-hero h1{font-family:'Playfair Display',serif;font-size:clamp(1.7rem,1.1rem+2.4vw,2.9rem);margin:0 0 10px}
.bp-hero p{color:rgba(255,255,255,.82);max-width:65ch;margin:0;font-size:1.04rem;line-height:1.6}
.bp-snap{display:flex;flex-wrap:wrap;gap:26px;margin-top:20px}
.bp-snap div{display:flex;flex-direction:column}.bp-snap b{font-family:'Playfair Display',serif;font-size:1.7rem;color:var(--gold)}
.bp-snap span{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.65)}
.bp-wrap{padding:34px 20px 56px}
.bp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:18px;margin:6px 0 30px}
.bp-card{display:block;text-decoration:none;color:inherit;border:1px solid #e6eaf1;border-radius:12px;overflow:hidden;background:#fff;transition:transform .15s,box-shadow .15s}
.bp-card:hover{transform:translateY(-4px);box-shadow:0 16px 40px -20px rgba(12,23,51,.5)}
.bp-card img{width:100%;height:165px;object-fit:cover;background:#e8edf4}
.bp-card .b{padding:13px 15px 15px}.bp-card .p{font-weight:800;color:var(--navy);font-size:1.18rem}
.bp-card .a{color:#36405c;font-size:.92rem;margin:4px 0 0}.bp-card .m{color:#8a90a3;font-size:.8rem;margin-top:5px}
.bp-cta{background:#f7f9fc;border:1px solid #e6eaf1;border-radius:12px;padding:22px;margin:10px 0 28px}
.bp-cta h2{margin:0 0 8px;color:var(--navy);font-family:'Playfair Display',serif}
.bp-cta a.btn{display:inline-block;background:var(--green);color:#fff;font-weight:700;padding:11px 20px;border-radius:8px;text-decoration:none;margin-top:6px}
.bp-links{margin:8px 0 0}.bp-links h3{color:var(--navy);font-size:1.05rem;margin:18px 0 8px}
.bp-chip{display:inline-block;background:#f1f4f9;border:1px solid #e2e8f1;color:var(--navy);text-decoration:none;padding:6px 13px;border-radius:99px;font-size:.84rem;font-weight:600;margin:0 6px 8px 0}
.bp-chip:hover{background:var(--navy);color:#fff}
.bp-body{max-width:75ch;color:#36405c;line-height:1.75}.bp-body h2{color:var(--navy);font-family:'Playfair Display',serif;margin:26px 0 8px}
.bp-foot{background:var(--navy);color:rgba(255,255,255,.7);padding:28px 0;font-size:.85rem;line-height:1.7}.bp-foot a{color:rgba(255,255,255,.85)}
</style>"""

def card(d):
    img = d['image'] or 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&q=70&fit=crop'
    price = money(d['price']) if d['price'] else 'Contact for price'
    m = (f"{d['beds']} bd · {d['baths']} ba" + (f" · {rp.fmt_int(d['sqft'])} sqft" if d['sqft'] and int(d['sqft'])>1 else '')) if d['beds'] else d['type_label']
    return (f'<a class="bp-card" href="/homes/{rp.esc(d["slug"])}/">'
            f'<img src="{rp.esc(img)}" alt="{rp.esc(rp.full_address(d))}" loading="lazy" width="265" height="165">'
            f'<div class="b"><div class="p">{rp.esc(price)}</div>'
            f'<p class="a">{rp.esc(d["street"])}, {rp.esc(d["city"])}</p>'
            f'<div class="m">{rp.esc(m)}</div></div></a>')

def build(scope_name, tier, matches, sibling_tiers, region_cities, idx_link):
    tslug, tlabel, lo, hi = tier
    slug = f'homes-{tslug}-in-{slugify(scope_name)}'
    title = f'Homes for Sale {tlabel} in {scope_name}, NY'
    url = f'{BASE}/homes-for-sale/{slug}.html'
    prices = [d['price'] for d in matches if d['price']]
    lo_p, hi_p = (min(prices), max(prices)) if prices else (0, 0)
    avg = sum(prices)//len(prices) if prices else 0
    cities_ct = {}
    for d in matches: cities_ct[d['city']] = cities_ct.get(d['city'],0)+1
    cities_str = ', '.join(f'{c} ({n})' for c,n in sorted(cities_ct.items(), key=lambda x:-x[1]))

    meta = (f'Browse {len(matches)} homes for sale {tlabel.lower()} in {scope_name}, NY with Gadura Real Estate. '
            f'Prices from {money(lo_p)} to {money(hi_p)}. Call (917) 705-0132.')
    snap = (f'<div><b>{len(matches)}</b><span>Homes in range</span></div>'
            f'<div><b>{money(lo_p)}</b><span>From</span></div>'
            f'<div><b>{money(hi_p)}</b><span>Up to</span></div>'
            f'<div><b>{money(avg)}</b><span>Average</span></div>')
    cards = ''.join(card(d) for d in sorted(matches, key=lambda x:-(x['price'] or 0)))

    sib = ''.join(f'<a class="bp-chip" href="/homes-for-sale/homes-{s}-in-{slugify(scope_name)}.html">{lbl}</a>'
                  for s,lbl,_,_ in sibling_tiers if (s,lbl)!=(tslug,tlabel))
    nbhd = ''.join(f'<a class="bp-chip" href="/neighborhoods/{slugify(c)}.html">{c}</a>' for c in sorted(region_cities)[:14])

    intro = (f'Looking for homes for sale {tlabel.lower()} in {scope_name}? '
             f'Gadura Real Estate currently represents {len(matches)} '
             f'{"property" if len(matches)==1 else "properties"} in this price range, '
             f'from {money(lo_p)} to {money(hi_p)} (average {money(avg)}), across '
             f'{cities_str}. As a family-owned brokerage serving {scope_name} since 2006, '
             f'we know exactly what your budget buys here — and we speak six languages in-house.')

    page = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{rp.esc(title)} | Gadura Real Estate</title>
<meta name="description" content="{rp.esc(meta)}">
<link rel="canonical" href="{url}"><meta name="robots" content="index, follow">
<meta property="og:title" content="{rp.esc(title)}"><meta property="og:description" content="{rp.esc(meta)}">
<meta property="og:url" content="{url}"><link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
{PAGE_CSS}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"CollectionPage","name":"{rp.esc(title)}","url":"{url}","description":"{rp.esc(meta)}","about":{{"@type":"Place","name":"{rp.esc(scope_name)}, NY"}}}}</script>
</head><body>
<header class="bp-head"><div class="bp-head-in">
  <a href="/"><img src="{rp.LOGO}" alt="Gadura Real Estate LLC"></a>
  <nav><a href="/">Home</a><a href="/homes-for-sale/all-listings.html">All Listings</a><a href="/neighborhoods/">Neighborhoods</a><a href="/sell.html">Sell</a><a href="tel:{rp.PHONE_TEL}">{rp.PHONE_DISP}</a></nav>
</div></header>
<section class="bp-hero"><div class="bp-wrap" style="padding:0">
  <div class="bp-bc"><a href="/">Home</a> › <a href="/homes-for-sale/all-listings.html">Homes for Sale</a> › {rp.esc(scope_name)} › {rp.esc(tlabel)}</div>
  <h1>{rp.esc(title)}</h1>
  <p>{rp.esc(intro)}</p>
  <div class="bp-snap">{snap}</div>
</div></section>
<main class="bp-wrap">
  <div class="bp-grid">{cards}</div>
  <div class="bp-cta">
    <h2>See every live listing in this range</h2>
    <p>New homes hit the market daily. Get the full, real-time OneKey® MLS results or set up free instant alerts.</p>
    <a class="btn" href="{idx_link}" target="_blank" rel="noopener">View Live MLS Results →</a>
    &nbsp; <a class="btn" style="background:#1b2a6b" href="/listing-alerts.html">Get Free Listing Alerts →</a>
  </div>
  <div class="bp-links">
    <h3>Other price ranges in {rp.esc(scope_name)}</h3>{sib}
    <h3>Neighborhoods in {rp.esc(scope_name)}</h3>{nbhd}
  </div>
  <div class="bp-body">
    <h2>Buying {rp.esc(tlabel.lower())} in {rp.esc(scope_name)}</h2>
    <p>Whether you're a first-time buyer, an investor, or trading up, {rp.esc(scope_name)} offers strong long-term value. Our team will pull comparable sales, line up showings, and negotiate hard on your behalf — at no cost to you as a buyer. Call <a href="tel:{rp.PHONE_TEL}">{rp.PHONE_DISP}</a> or browse <a href="/homes-for-sale/all-listings.html">all our current listings</a>.</p>
  </div>
</main>
<footer class="bp-foot"><div class="bp-wrap" style="padding:0">
  <strong>Gadura Real Estate, LLC</strong> · {rp.OFFICE_ADDR} · <a href="tel:{rp.PHONE_TEL}">{rp.PHONE_DISP}</a><br>
  Listing data via the IDX program of OneKey® MLS. Information deemed reliable but not guaranteed. Equal Housing Opportunity. © 2026 Gadura Real Estate, LLC.
</div></footer>
</body></html>'''
    with open(os.path.join(OUTDIR, slug + '.html'), 'w', encoding='utf-8') as f:
        f.write(page)
    return url


def main():
    listings = {}
    for slug in os.listdir(rp.HOMES_DIR):
        p = os.path.join(rp.HOMES_DIR, slug, 'index.html')
        if not os.path.isfile(p): continue
        d = rp.extract(slug, open(p, encoding='utf-8').read())
        if d and d['street']: listings[slug] = d
    all_list = list(listings.values())

    # scopes: regions + top neighborhoods (>=5 listings)
    region_map = {}
    for d in all_list:
        r = region_of(d['city'])
        if r: region_map.setdefault(r, set()).add(d['city'])
    city_counts = {}
    for d in all_list: city_counts[d['city']] = city_counts.get(d['city'],0)+1
    top_nbhds = [c for c,n in city_counts.items() if n >= 5 and c not in region_map]

    scopes = []  # (name, predicate, region_cities)
    for r, cities in region_map.items():
        scopes.append((r, (lambda cs: (lambda d: d['city'] in cs))(cities), cities))
    scopes.append(('Long Island', (lambda d: d['city'] in (NASSAU | SUFFOLK)), NASSAU | SUFFOLK))
    scopes.append(('Queens & Long Island', (lambda d: region_of(d['city']) in ('Queens','Nassau County','Suffolk County')),
                   QUEENS | NASSAU | SUFFOLK))
    for c in top_nbhds:
        scopes.append((c, (lambda cc: (lambda d: d['city']==cc))(c), {c}))

    OUT_OK = []
    for name, pred, region_cities in scopes:
        scoped = [d for d in all_list if pred(d)]
        city_q = re.sub(r'\s+', '+', name)
        idx_link = f'https://homes.gadurarealestate.com/idx/map/mapsearch?city={city_q}&statusCategory=active&srt=newest'
        for tier in TIERS:
            _, _, lo, hi = tier
            matches = [d for d in scoped if d['price'] and lo <= d['price'] < hi]
            if len(matches) >= 2:
                url = build(name, tier, matches, TIERS, region_cities, idx_link)
                OUT_OK.append((url, name, tier[1], len(matches)))

    # sitemap
    urls = ''.join(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>2026-06-25</lastmod>\n'
                   f'    <changefreq>daily</changefreq>\n    <priority>0.7</priority>\n  </url>\n'
                   for u,_,_,_ in OUT_OK)
    with open(os.path.join(REPO, 'sitemap-buyer.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + urls + '</urlset>\n')

    print(f'Generated {len(OUT_OK)} buyer-intent price-tier pages:')
    for u, name, tl, n in OUT_OK:
        print(f'  {name:24} {tl:16} ({n} listings)  {u.split("/")[-1]}')
    print(f'\nsitemap-buyer.xml written ({len(OUT_OK)} URLs)')


if __name__ == '__main__':
    main()
