#!/usr/bin/env python3
"""
rebuild_property_pages.py — Rebuilds every homes/{slug}/index.html with the
luxury property-detail template (css/property-detail.css).

Data is read from each page's *existing* embedded JSON-LD + body (so it works
even though data/listings.json is currently empty — it never destroys data).

Captures: address, price, beds, baths, sqft, description, type, hero image,
IDX/MLS detail link, MLS number, status. Then writes a polished page with:
  - Sticky agent card (Nitin's headshot, license, office number)
  - "Call Today to Inquire" band
  - WhatsApp chat (web + mobile via wa.me)
  - Contact form, map, key facts, breadcrumb, legal footer

Run from repo root:
  python3 scripts/rebuild_property_pages.py
"""
import os, re, json, html as ihtml

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOMES_DIR = os.path.join(REPO, 'homes')
BASE_URL  = 'https://gadurarealestate.com'

# ── Contact constants ───────────────────────────────────────────────
AGENT_NAME   = 'Nitin Gadura'
AGENT_TITLE  = 'Licensed Real Estate Salesperson'
AGENT_FIRM   = 'Gadura Real Estate, LLC'
AGENT_PHOTO  = '/images/nitin-gadura-headshot.jpg'
PHONE_DISP   = '(917) 705-0132'
PHONE_TEL    = '+19177050132'
PHONE_WA     = '19177050132'          # wa.me format (no +)
EMAIL        = 'nitin@gadurarealestate.com'
OFFICE_ADDR  = '106-09 101st Ave, Ozone Park, NY 11416'
LICENSE      = 'NYS Broker Lic. #10991238487'
LOGO         = '/images/logo-full.png'

TYPE_LABELS = {
    'SingleFamilyResidence': 'Single-Family Home',
    'MultiFamilyResidence':  'Multi-Family Home',
    'Apartment':             'Condo / Co-op',
    'House':                 'Single-Family Home',
    'Store':                 'Commercial',
    'LocalBusiness':         'Commercial',
}
# label → specific schema.org @type written back to output (keeps re-runs idempotent)
LABEL_TO_SCHEMA = {
    'Single-Family Home': 'SingleFamilyResidence',
    'Multi-Family Home':  'MultiFamilyResidence',
    'Condo / Co-op':      'Apartment',
    'Commercial':         'Store',
    'Property':           'SingleFamilyResidence',
}


def derive_type(t0, description):
    """Return a friendly label, inferring from description for generic types."""
    if t0 in TYPE_LABELS:
        return TYPE_LABELS[t0]
    desc = (description or '').lower()
    if any(k in desc for k in ('commercial', 'retail', 'storefront', 'office space',
                               'mixed-use', 'mixed use', 'warehouse')):
        return 'Commercial'
    if any(k in desc for k in ('2-family', 'two-family', '2 family', '3-family',
                               'three-family', 'multi-family', 'multifamily', 'duplex')):
        return 'Multi-Family Home'
    if any(k in desc for k in ('condo', 'co-op', 'coop', 'apartment', 'studio')):
        return 'Condo / Co-op'
    return 'Single-Family Home'


# ── Extraction ──────────────────────────────────────────────────────
def jsonld_nodes(html_txt):
    """Yield every dict node from all JSON-LD blocks (handles @graph)."""
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
                            html_txt, re.DOTALL):
        try:
            data = json.loads(block)
        except Exception:
            continue
        if isinstance(data, dict) and '@graph' in data:
            for n in data['@graph']:
                if isinstance(n, dict):
                    yield n
        elif isinstance(data, dict):
            yield data
        elif isinstance(data, list):
            for n in data:
                if isinstance(n, dict):
                    yield n


def extract(slug, html_txt):
    listing = None
    for node in jsonld_nodes(html_txt):
        if node.get('address') and node.get('@type') not in ('BreadcrumbList',):
            listing = node
            break
    if not listing:
        return None

    addr = listing.get('address', {})
    t = listing.get('@type')
    t0 = t[0] if isinstance(t, list) else t

    offers = listing.get('offers', {}) or {}
    price = offers.get('price') or 0
    try:
        price = int(price)
    except Exception:
        price = 0

    floor = listing.get('floorSize', {}) or {}
    sqft = floor.get('value') or 0

    # IDX detail link + MLS number — prefer JSON-LD (idempotent), fall back to body
    idx_link = ''
    m = re.search(r'https?://homes\.gadurarealestate\.com/idx/details/listing/c056/\d+[^"\'\s]*', html_txt)
    if m:
        idx_link = m.group(0)
    mls = ''
    ident = listing.get('identifier')
    if isinstance(ident, dict) and str(ident.get('name', '')).upper() == 'MLS':
        mls = str(ident.get('value', ''))
    if not mls:
        m = re.search(r'MLS\s*#?\s*([0-9]{6,})(?!["\'<])', html_txt)
        if m:
            mls = m.group(1)

    # status
    status = 'Active'
    m = re.search(r'(Pending|Sold|Active|Coming Soon)', html_txt)
    # prefer an explicit availability mapping
    avail = offers.get('availability', '')
    if 'SoldOut' in avail:
        status = 'Sold'
    elif 'PreOrder' in avail or 'LimitedAvailability' in avail:
        status = 'Pending'

    state = (addr.get('addressRegion') or 'NY').strip().strip(',')
    return {
        'slug':        slug,
        'street':      (addr.get('streetAddress') or '').strip(),
        'city':        (addr.get('addressLocality') or '').strip(),
        'state':       state,
        'zip':         (addr.get('postalCode') or '').strip(),
        'price':       price,
        'beds':        listing.get('numberOfRooms') or 0,
        'baths':       listing.get('numberOfBathroomsTotal') or 0,
        'sqft':        sqft,
        'description': (listing.get('description') or '').strip(),
        'type_label':  derive_type(t0, listing.get('description')),
        'image':       listing.get('image') or '',
        'idx_link':    idx_link,
        'mls':         mls,
        'status':      status,
        'date':        listing.get('datePosted') or '2026-06-25',
    }


# ── Formatting helpers ──────────────────────────────────────────────
def esc(s):
    return ihtml.escape(str(s or ''), quote=True)


def fmt_int(n):
    try:
        return f'{int(n):,}'
    except Exception:
        return str(n)


def price_block(d):
    p = d['price']
    if not p:
        return 'Contact for Price', ''
    if p < 50000:   # monthly rental
        return f'${fmt_int(p)}', '<span class="pd-price-unit">/mo</span>'
    return f'${fmt_int(p)}', ''


def full_address(d):
    a = d['street']
    if d['city']:
        a += ', ' + d['city']
    if d['state']:
        a += ', ' + d['state']
    if d['zip']:
        a += ' ' + d['zip']
    return a


# ── Mortgage calculator + related listings (Park-Assets-style) ──────
MORT_CSS = """<style id="pd-extra">
.pd-mort{background:#f7f9fc;border:1px solid #e6eaf1;border-radius:14px;padding:22px;display:grid;gap:20px}
@media(min-width:680px){.pd-mort{grid-template-columns:1fr 1fr;align-items:start}}
.pd-mort-grid{display:grid;gap:14px}
.pd-mort-field{display:flex;flex-direction:column;gap:6px;font-size:.82rem;font-weight:600;color:#1b2a6b}
.pd-mort-field input,.pd-mort-field select{padding:10px 12px;border:1px solid #d3dae6;border-radius:8px;font:inherit;font-weight:600;color:#1b2a6b;background:#fff}
.pd-mort-field input[type=range]{padding:0;accent-color:#00a651}
.pd-mort-result{background:#1b2a6b;color:#fff;border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:12px}
.pd-mort-total{display:flex;flex-direction:column;gap:2px;border-bottom:1px solid rgba(255,255,255,.15);padding-bottom:12px}
.pd-mort-total span{font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.7)}
.pd-mort-total strong{font-family:'Playfair Display',serif;font-size:2.1rem;color:#00a651;line-height:1}
.pd-mort-break{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.pd-mort-break li{display:flex;justify-content:space-between;font-size:.9rem;color:rgba(255,255,255,.85)}
.pd-mort-break b{color:#fff}
.pd-mort-dp{border-top:1px solid rgba(255,255,255,.15);padding-top:8px}
.pd-mort-cta{display:block;text-align:center;background:#00a651;color:#fff;font-weight:700;padding:12px;border-radius:8px;text-decoration:none;margin-top:4px}
.pd-mort-cta:hover{background:#00853f}
.pd-mort-fine{font-size:.66rem;color:rgba(255,255,255,.5);margin:0;line-height:1.5}
.pd-related{margin-top:22px;background:#fff;border:1px solid #e6eaf1;border-radius:14px;padding:18px}
.pd-related-title{font-family:'Playfair Display',serif;font-size:1.2rem;color:#1b2a6b;margin:0 0 8px}
.pd-rel-card{display:flex;gap:12px;padding:11px 0;border-bottom:1px solid #eef1f6;text-decoration:none;color:inherit;transition:transform .15s}
.pd-rel-card:last-of-type{border-bottom:0}
.pd-rel-card:hover{transform:translateX(3px)}
.pd-rel-card img{width:96px;height:70px;object-fit:cover;border-radius:8px;flex:none;background:#e8edf4}
.pd-rel-info{display:flex;flex-direction:column;justify-content:center;gap:2px}
.pd-rel-price{font-weight:800;color:#1b2a6b}
.pd-rel-addr{font-size:.82rem;color:#48506a;line-height:1.3}
.pd-rel-bb{font-size:.74rem;color:#8a90a3}
.pd-related-all{display:inline-block;margin-top:12px;color:#00a651;font-weight:700;text-decoration:none;font-size:.9rem}
.pd-related-all:hover{text-decoration:underline}
</style>"""

MORT_JS = """<script>
(function(){
  var $=function(id){return document.getElementById(id);};
  var price=$('mc-price'),dp=$('mc-dp'),rate=$('mc-rate'),term=$('mc-term');
  if(!price) return;
  function money(n){return '$'+Math.round(n).toLocaleString('en-US');}
  function calc(){
    var P=+price.value||0, d=+dp.value||0, r=(+rate.value||0)/100/12, n=(+term.value||30)*12;
    var loan=P*(1-d/100);
    var pi = r>0 ? loan*r*Math.pow(1+r,n)/(Math.pow(1+r,n)-1) : (n? loan/n : 0);
    var tax=P*0.012/12, ins=P*0.0035/12;
    $('mc-dp-pct').textContent=d;
    $('mc-pi').textContent=money(pi);
    $('mc-tax').textContent=money(tax);
    $('mc-ins').textContent=money(ins);
    $('mc-dpamt').textContent=money(P*d/100);
    $('mc-total').textContent=money(pi+tax+ins);
  }
  [price,dp,rate,term].forEach(function(x){x.addEventListener('input',calc);});
  calc();
})();
</script>"""


def build_mortgage(d):
    """Interactive mortgage calculator pre-filled with the listing price."""
    price = d['price'] if d['price'] and d['price'] >= 50000 else 700000
    return f'''<section class="pd-section" id="mortgage">
      <h2>Mortgage Calculator</h2>
      <div class="pd-section-rule"></div>
      <div class="pd-mort">
        <div class="pd-mort-grid">
          <label class="pd-mort-field"><span>Home Price ($)</span>
            <input type="number" id="mc-price" value="{price}" min="0" step="1000"></label>
          <label class="pd-mort-field"><span>Down Payment (<b id="mc-dp-pct">20</b>%)</span>
            <input type="range" id="mc-dp" min="0" max="50" value="20"></label>
          <label class="pd-mort-field"><span>Interest Rate (%)</span>
            <input type="number" id="mc-rate" value="6.5" step="0.05" min="0"></label>
          <label class="pd-mort-field"><span>Loan Term</span>
            <select id="mc-term"><option value="30">30 years</option><option value="20">20 years</option><option value="15">15 years</option></select></label>
        </div>
        <div class="pd-mort-result">
          <div class="pd-mort-total"><span>Estimated Monthly Payment</span><strong id="mc-total">$—</strong></div>
          <ul class="pd-mort-break">
            <li><span>Principal &amp; Interest</span><b id="mc-pi">$—</b></li>
            <li><span>Property Tax (est.)</span><b id="mc-tax">$—</b></li>
            <li><span>Home Insurance (est.)</span><b id="mc-ins">$—</b></li>
            <li class="pd-mort-dp"><span>Down Payment</span><b id="mc-dpamt">$—</b></li>
          </ul>
          <a href="tel:{PHONE_TEL}" class="pd-mort-cta">Get Pre-Approved — Talk to a Realtor</a>
          <p class="pd-mort-fine">Estimates only, for planning purposes. Taxes &amp; insurance vary by property and are approximate. Not a loan offer or commitment to lend.</p>
        </div>
      </div>
    </section>'''


def build_related(d, related):
    """Sidebar 'More Homes in {city}' cards linking to other listing pages."""
    if not related:
        return ''
    cards = ''
    for r in related:
        img = r['image'] or 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=200&q=70&fit=crop'
        price_s = ('$' + fmt_int(r['price'])) if r['price'] else 'Contact for price'
        bb = f"{r['beds']} bd · {r['baths']} ba" if r['beds'] else r['type_label']
        loc = ', '.join(x for x in (r['street'], r['city']) if x)
        cards += (f'<a class="pd-rel-card" href="/homes/{esc(r["slug"])}/">'
                  f'<img src="{esc(img)}" alt="{esc(loc)}" loading="lazy" width="96" height="70">'
                  f'<div class="pd-rel-info"><span class="pd-rel-price">{esc(price_s)}</span>'
                  f'<span class="pd-rel-addr">{esc(loc)}</span>'
                  f'<span class="pd-rel-bb">{esc(bb)}</span></div></a>')
    title_city = d['city'] or 'Queens & Long Island'
    return (f'<div class="pd-related"><h3 class="pd-related-title">More Homes in {esc(title_city)}</h3>'
            f'{cards}<a class="pd-related-all" href="/homes-for-sale/queens-homes-for-sale.html">View all listings →</a></div>')


def pick_related(d, all_list, n=4):
    """Up to n related listings: same city first (closest price), then nearest by price."""
    same = [x for x in all_list if x['city'] == d['city'] and x['slug'] != d['slug']]
    same.sort(key=lambda x: abs((x['price'] or 0) - (d['price'] or 0)))
    if len(same) >= n:
        return same[:n]
    chosen = {x['slug'] for x in same}
    others = [x for x in all_list if x['slug'] != d['slug'] and x['slug'] not in chosen]
    others.sort(key=lambda x: abs((x['price'] or 0) - (d['price'] or 0)))
    return (same + others)[:n]


# ── Page template ───────────────────────────────────────────────────
def build_page(d, related=None):
    fa          = full_address(d)
    page_url    = f'{BASE_URL}/homes/{d["slug"]}/'
    price_str, price_unit = price_block(d)
    hero        = d['image'] or 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=1200&q=80&fit=crop'
    idx_link    = d['idx_link'] or f'https://homes.gadurarealestate.com/idx/map/mapsearch?city={d["city"].replace(" ", "+")}'
    maps_q      = re.sub(r'\s+', '+', fa)
    map_src     = f'https://www.google.com/maps?q={maps_q}&output=embed'

    wa_msg = f"Hi Nitin, I'm interested in {fa}. Is it still available? ({page_url})"
    wa_url = f'https://wa.me/{PHONE_WA}?text=' + re.sub(r'\s+', '%20', wa_msg).replace(',', '%2C').replace("'", '%27')

    bbs = ''
    if d['beds']:
        bbs = '{} bed · {} bath'.format(d['beds'], d['baths'])
        if d['sqft'] and int(d['sqft']) > 1:
            bbs += ' · {} sqft'.format(fmt_int(d['sqft']))
        bbs += '. '
    meta_desc = ('{} — {} for sale at {}. {}Contact {} at {} for a private showing.'
                 .format(fa, d['type_label'].lower(), price_str, bbs, AGENT_NAME, PHONE_DISP))

    # ── Stats ──
    stats = []
    if d['beds']:  stats.append((d['beds'], 'Bedrooms'))
    if d['baths']: stats.append((d['baths'], 'Bathrooms'))
    if d['sqft'] and int(d['sqft']) > 1: stats.append((fmt_int(d['sqft']), 'Sq Ft'))
    stats.append((d['type_label'].split()[0], 'Type'))
    stats_html = ''.join(
        f'<div class="pd-stat"><span class="pd-stat-val">{esc(v)}</span>'
        f'<span class="pd-stat-lbl">{esc(l)}</span></div>'
        for v, l in stats
    )

    # ── Facts ──
    facts = [
        ('Status', d['status']),
        ('Property Type', d['type_label']),
        ('Bedrooms', d['beds']),
        ('Bathrooms', d['baths']),
        ('Living Area', f'{fmt_int(d["sqft"])} sq ft' if d['sqft'] and int(d['sqft']) > 1 else ''),
        ('City', d['city']),
        ('ZIP Code', d['zip']),
        ('MLS #', d['mls']),
    ]
    facts_html = ''.join(
        f'<div class="pd-fact"><span class="pd-fact-label">{esc(l)}</span>'
        f'<span class="pd-fact-value">{esc(v)}</span></div>'
        for l, v in facts if v
    )

    desc_html = ''
    if d['description']:
        paras = [p.strip() for p in re.split(r'\n{2,}', d['description']) if p.strip()] or [d['description']]
        desc_html = ''.join(f'<p>{esc(p)}</p>' for p in paras)
    else:
        desc_html = (f'<p>{esc(fa)} is a {d["type_label"].lower()} available through '
                     f'{AGENT_FIRM}. Contact {AGENT_NAME} for full details, disclosures, '
                     f'and a private showing.</p>')

    status_class = {'Pending': ' is-pending', 'Sold': ' is-sold'}.get(d['status'], '')

    # New Park-Assets-style modules
    mort_html    = build_mortgage(d)
    related_html = build_related(d, related or [])

    # ── JSON-LD (regenerated, clean) ──
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": [LABEL_TO_SCHEMA.get(d['type_label'], 'SingleFamilyResidence'), "RealEstateListing"],
                "name": fa,
                "url": page_url,
                "description": d['description'] or meta_desc,
                "image": hero,
                "datePosted": d['date'],
                "offers": {
                    "@type": "Offer",
                    "price": d['price'],
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "seller": {
                        "@type": "RealEstateAgent",
                        "name": AGENT_FIRM,
                        "telephone": PHONE_TEL,
                        "url": BASE_URL
                    }
                } if d['price'] else None,
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": d['street'],
                    "addressLocality": d['city'],
                    "addressRegion": d['state'],
                    "postalCode": d['zip'],
                    "addressCountry": "US"
                },
                "numberOfRooms": d['beds'] or None,
                "numberOfBathroomsTotal": d['baths'] or None,
                "identifier": {"@type": "PropertyValue", "name": "MLS", "value": d['mls']} if d['mls'] else None,
                "floorSize": {"@type": "QuantitativeValue", "value": d['sqft'], "unitCode": "FTK"} if d['sqft'] and int(d['sqft']) > 1 else None
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Homes For Sale", "item": BASE_URL + "/homes-for-sale/queens-homes-for-sale.html"},
                    {"@type": "ListItem", "position": 3, "name": fa, "item": page_url}
                ]
            }
        ]
    }
    jsonld_str = json.dumps(jsonld).replace('"seller": null', '').replace(', null', '')
    # strip null-valued keys cleanly
    jsonld_str = re.sub(r',\s*"[^"]+":\s*null', '', json.dumps(jsonld))

    wa_svg = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-1.6-.8-2.7-1.4-3.7-3.2-.3-.5.3-.5.8-1.5.1-.2 0-.4 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.3 5.2 4.6 2 .8 2.7.9 3.7.8.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3M12 2a10 10 0 00-8.6 15l-1.3 4.7 4.8-1.3A10 10 0 1012 2z"/></svg>')
    phone_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3 19.5 19.5 0 01-6-6 19.8 19.8 0 01-3-8.6A2 2 0 014.1 2h3a2 2 0 012 1.7c.1 1 .4 1.9.7 2.8a2 2 0 01-.5 2.1L8.1 9.8a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.4c.9.3 1.8.6 2.8.7a2 2 0 011.7 2z"/></svg>'
    mail_svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/></svg>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(fa)}</title>
<meta name="description" content="{esc(meta_desc)}">
<link rel="canonical" href="{esc(page_url)}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(fa)} — For Sale | Gadura Real Estate">
<meta property="og:description" content="{esc(meta_desc)}">
<meta property="og:image" content="{esc(hero)}">
<meta property="og:url" content="{esc(page_url)}">
<meta property="og:site_name" content="Gadura Real Estate LLC">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(fa)}">
<meta name="twitter:description" content="{esc(meta_desc)}">
<meta name="twitter:image" content="{esc(hero)}">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/property-detail.css">
{MORT_CSS}
<script type="application/ld+json">{jsonld_str}</script>
</head>
<body class="pd-body">

<!-- Top bar -->
<div class="pd-topbar">
  <div class="pd-topbar-inner">
    <span>📍 {OFFICE_ADDR} &nbsp;·&nbsp; Mon–Sat 9–7, Sun 10–5</span>
    <span>Call or text <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a> &nbsp;·&nbsp; <a href="mailto:{EMAIL}">{EMAIL}</a></span>
  </div>
</div>

<!-- Header -->
<header class="pd-header">
  <div class="pd-header-inner">
    <a href="/" class="pd-logo" aria-label="Gadura Real Estate home">
      <img src="{LOGO}" alt="Gadura Real Estate LLC" width="200" height="60">
    </a>
    <nav class="pd-nav" aria-label="Main navigation">
      <a href="/homes-for-sale/queens-homes-for-sale.html">Homes For Sale</a>
      <a href="/neighborhoods/">Neighborhoods</a>
      <a href="/home-value/">Home Value</a>
      <a href="/listing-alerts.html">Listing Alerts</a>
      <a href="/about.html">About</a>
    </nav>
    <a href="tel:{PHONE_TEL}" class="pd-header-cta">{PHONE_DISP}</a>
  </div>
</header>

<!-- Breadcrumb -->
<nav class="pd-breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a><span>›</span>
  <a href="/homes-for-sale/queens-homes-for-sale.html">Homes For Sale</a><span>›</span>
  {esc(d['city'])}<span>›</span>{esc(d['street'])}
</nav>

<!-- Hero -->
<section class="pd-hero">
  <div class="pd-hero-media">
    <span class="pd-status-badge{status_class}">{esc(d['status'])}</span>
    <img src="{esc(hero)}" alt="{esc(fa)}" width="1200" height="540" fetchpriority="high">
    <a href="{esc(idx_link)}" class="pd-photos-btn" target="_blank" rel="noopener">View all photos on MLS →</a>
  </div>
</section>

<!-- Headline -->
<div class="pd-headline">
  <div>
    <p class="pd-price">{esc(price_str)}{price_unit}</p>
    <h1 class="pd-address">{esc(fa)}</h1>
  </div>
  <div class="pd-headline-quick">
    <a href="tel:{PHONE_TEL}" class="pd-quick-btn pd-quick-call">{phone_svg} Call</a>
    <a href="{esc(wa_url)}" class="pd-quick-btn pd-quick-wa" target="_blank" rel="noopener">{wa_svg} WhatsApp</a>
  </div>
</div>

<!-- Stats -->
<div class="pd-stats">
  <div class="pd-stats-inner">{stats_html}</div>
</div>

<!-- Main -->
<div class="pd-main">
  <main>
    <section class="pd-section pd-about">
      <h2>About This Home</h2>
      <div class="pd-section-rule"></div>
      {desc_html}
    </section>

    <section class="pd-section">
      <h2>Property Details</h2>
      <div class="pd-section-rule"></div>
      <div class="pd-facts-grid">{facts_html}</div>
    </section>

    {mort_html}

    <section class="pd-section">
      <h2>Location</h2>
      <div class="pd-section-rule"></div>
      <iframe class="pd-map-frame" src="{esc(map_src)}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Map of {esc(fa)}"></iframe>
    </section>

    <section class="pd-inquire-band">
      <p class="pd-inquire-eyebrow">Interested in this property?</p>
      <h2>Call Today to Inquire About This Home</h2>
      <p>Speak directly with {AGENT_NAME} — schedule a private showing, request disclosures, or ask any question.</p>
      <div class="pd-inquire-actions">
        <a href="tel:{PHONE_TEL}" class="pd-inquire-call">{phone_svg} {PHONE_DISP}</a>
        <a href="{esc(wa_url)}" class="pd-inquire-wa" target="_blank" rel="noopener">{wa_svg} Chat on WhatsApp</a>
      </div>
    </section>
  </main>

  <!-- Agent sidebar -->
  <aside class="pd-sidebar">
    <div class="pd-agent-card">
      <div class="pd-agent-top">
        <img src="{AGENT_PHOTO}" alt="{AGENT_NAME}, {AGENT_TITLE}" class="pd-agent-photo" width="104" height="104">
        <p class="pd-agent-name">{AGENT_NAME}</p>
        <p class="pd-agent-title">{AGENT_TITLE}</p>
        <p class="pd-agent-firm">{AGENT_FIRM}</p>
        <div class="pd-agent-badges">
          <span class="pd-agent-badge">OneKey® MLS</span>
          <span class="pd-agent-badge">REALTOR®</span>
          <span class="pd-agent-badge">Equal Housing</span>
        </div>
      </div>
      <div class="pd-agent-cta">
        <a href="tel:{PHONE_TEL}" class="pd-cta pd-cta-call">
          <span class="pd-cta-sub">Call to Inquire</span>
          <span class="pd-cta-num">{PHONE_DISP}</span>
        </a>
        <a href="{esc(wa_url)}" class="pd-cta pd-cta-wa" target="_blank" rel="noopener">{wa_svg} Chat on WhatsApp</a>
        <a href="mailto:{EMAIL}?subject=Inquiry: {esc(fa)}" class="pd-cta pd-cta-email">{mail_svg} Email Nitin</a>
      </div>
      <form class="pd-form" action="https://formsubmit.co/{EMAIL}" method="POST">
        <p class="pd-form-title">Request a Showing</p>
        <input type="hidden" name="_subject" value="Showing request: {esc(fa)}">
        <input type="hidden" name="Property" value="{esc(fa)}">
        <input type="hidden" name="_template" value="table">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="email" name="email" placeholder="Email address" required>
        <input type="tel" name="phone" placeholder="Phone number">
        <textarea name="message" placeholder="I'd like to schedule a showing for {esc(fa)}.">I'd like to schedule a showing for {esc(fa)}.</textarea>
        <button type="submit" class="pd-form-submit">Send to Nitin</button>
        <p class="pd-form-fine">By submitting you agree to be contacted about this property. {LICENSE}</p>
      </form>
    </div>
    {related_html}
  </aside>
</div>

<!-- Mobile sticky bar -->
<div class="pd-mobilebar">
  <a href="tel:{PHONE_TEL}" class="pd-mb-call">{phone_svg} Call Nitin</a>
  <a href="{esc(wa_url)}" class="pd-mb-wa" target="_blank" rel="noopener">{wa_svg} WhatsApp</a>
</div>

<!-- Floating WhatsApp -->
<a href="{esc(wa_url)}" class="pd-wa-bubble" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">{wa_svg}</a>

{MORT_JS}

<!-- Footer -->
<footer class="pd-footer">
  <div class="pd-footer-inner">
    <p><strong>{AGENT_FIRM}</strong> · {OFFICE_ADDR} · <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a><br>
    Licensed Real Estate Broker, State of New York · {LICENSE} · Supervising Broker: Vinod K. Gadura.</p>
    <p>Listing data comes in part from the Internet Data Exchange (IDX) program of OneKey® MLS. Information deemed reliable but not guaranteed. IDX information is provided exclusively for consumers' personal, non-commercial use. © 2026 OneKey® MLS. Equal Housing Opportunity.</p>
    <div class="pd-footer-links">
      <a href="/homes-for-sale/queens-homes-for-sale.html">Homes For Sale</a>
      <a href="/listing-alerts.html">Listing Alerts</a>
      <a href="/home-value/">Home Value</a>
      <a href="/privacy-policy.html">Privacy</a>
      <a href="/idx-policy.html">IDX & VOW Policy</a>
      <a href="/fair-housing.html">Fair Housing</a>
      <a href="/accessibility.html">Accessibility</a>
    </div>
    <p class="pd-footer-copy">© 2026 {AGENT_FIRM}. All rights reserved.</p>
  </div>
</footer>

</body>
</html>
'''


DIR_CSS = """<style>
:root{--navy:#1b2a6b;--green:#00a651;--gold:#00a651}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;color:#1b2433;background:#fff}
.dir-head{background:var(--navy);color:#fff;padding:14px 0}
.dir-head-in,.dir-wrap{max-width:1200px;margin:0 auto;padding:0 20px}
.dir-head-in{display:flex;align-items:center;justify-content:space-between;gap:16px}
.dir-head img{height:38px;background:#fff;padding:6px 12px;border-radius:9px}
.dir-head nav a{color:rgba(255,255,255,.85);text-decoration:none;font-size:.85rem;font-weight:600;margin-left:18px}
.dir-head nav a:hover{color:var(--gold)}
.dir-hero{background:linear-gradient(135deg,#1b2a6b,#16284a);color:#fff;padding:46px 0 38px}
.dir-hero h1{font-family:'Playfair Display',serif;font-size:clamp(1.8rem,1.2rem+2.4vw,3rem);margin:0 0 10px}
.dir-hero p{color:rgba(255,255,255,.8);max-width:60ch;margin:0;font-size:1.05rem}
.dir-hero .dir-count{display:inline-block;margin-top:16px;background:var(--gold);color:var(--navy);font-weight:800;padding:7px 16px;border-radius:4px;font-size:.9rem}
.dir-wrap{padding:34px 20px 60px}
.dir-toc{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:30px}
.dir-toc a{background:#f1f4f9;border:1px solid #e2e8f1;color:var(--navy);text-decoration:none;padding:6px 13px;border-radius:99px;font-size:.82rem;font-weight:600}
.dir-toc a:hover{background:var(--navy);color:#fff}
.dir-city{font-family:'Playfair Display',serif;color:var(--navy);font-size:1.5rem;margin:34px 0 4px;border-bottom:2px solid var(--gold);padding-bottom:8px;display:inline-block}
.dir-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px;margin-top:18px}
.dir-card{display:block;text-decoration:none;color:inherit;border:1px solid #e6eaf1;border-radius:12px;overflow:hidden;background:#fff;transition:transform .15s,box-shadow .15s}
.dir-card:hover{transform:translateY(-4px);box-shadow:0 16px 40px -20px rgba(12,23,51,.5)}
.dir-card img{width:100%;height:170px;object-fit:cover;background:#e8edf4}
.dir-card .b{padding:14px 16px 16px}
.dir-card .p{font-weight:800;color:var(--navy);font-size:1.2rem}
.dir-card .a{color:#36405c;font-size:.95rem;margin:4px 0 0;line-height:1.3}
.dir-card .m{color:#8a90a3;font-size:.82rem;margin-top:6px}
.dir-foot{background:var(--navy);color:rgba(255,255,255,.7);padding:30px 0;font-size:.85rem;line-height:1.7}
.dir-foot a{color:rgba(255,255,255,.85)}
</style>"""


def write_directory(listings):
    """Build a crawlable directory hub linking EVERY listing page (grouped by
    city) so Google can discover them all + visitors can browse. Internal
    linking is the #1 driver of getting listing pages indexed."""
    from collections import OrderedDict
    by_city = OrderedDict()
    for d in sorted(listings.values(), key=lambda x: (x['city'], -(x['price'] or 0))):
        by_city.setdefault(d['city'] or 'Other', []).append(d)

    def anchor(c):
        return re.sub(r'[^a-z0-9]+', '-', c.lower()).strip('-')

    toc = ''.join(f'<a href="#{anchor(c)}">{esc(c)} ({len(v)})</a>' for c, v in by_city.items())

    sections = ''
    for city, items in by_city.items():
        cards = ''
        for d in items:
            img = d['image'] or 'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&q=70&fit=crop'
            price = ('$' + fmt_int(d['price'])) if d['price'] else 'Contact for price'
            mline = (f"{d['beds']} bd · {d['baths']} ba" + (f" · {fmt_int(d['sqft'])} sqft" if d['sqft'] and int(d['sqft']) > 1 else '')) if d['beds'] else d['type_label']
            cards += (f'<a class="dir-card" href="/homes/{esc(d["slug"])}/">'
                      f'<img src="{esc(img)}" alt="{esc(full_address(d))}" loading="lazy" width="270" height="170">'
                      f'<div class="b"><div class="p">{esc(price)}</div>'
                      f'<p class="a">{esc(d["street"])}, {esc(d["city"])} {esc(d["zip"])}</p>'
                      f'<div class="m">{esc(mline)}</div></div></a>')
        sections += (f'<h2 class="dir-city" id="{anchor(city)}">Homes for Sale in {esc(city)}, NY</h2>'
                     f'<div class="dir-grid">{cards}</div>')

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>All Homes for Sale — Queens, Brooklyn & Long Island | Gadura Real Estate</title>
<meta name="description" content="Browse all {len(listings)} homes for sale across Queens, Brooklyn & Long Island with Gadura Real Estate. Single-family, multi-family, condos & co-ops. Call (917) 705-0132.">
<link rel="canonical" href="{BASE_URL}/homes-for-sale/all-listings.html">
<meta name="robots" content="index, follow">
<meta property="og:title" content="All Homes for Sale — Queens, Brooklyn & Long Island | Gadura Real Estate">
<meta property="og:description" content="Browse every active listing with Gadura Real Estate across Queens & Long Island.">
<meta property="og:url" content="{BASE_URL}/homes-for-sale/all-listings.html">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
{DIR_CSS}
</head>
<body>
<header class="dir-head"><div class="dir-head-in">
  <a href="/"><img src="{LOGO}" alt="Gadura Real Estate LLC"></a>
  <nav><a href="/">Home</a><a href="/homes-for-sale/all-listings.html">All Listings</a><a href="/neighborhoods/">Neighborhoods</a><a href="/sell.html">Sell</a><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></nav>
</div></header>

<section class="dir-hero"><div class="dir-wrap" style="padding-top:0;padding-bottom:0">
  <h1>Homes for Sale in Queens, Brooklyn &amp; Long Island</h1>
  <p>Browse every active listing represented by Gadura Real Estate — single-family, multi-family, condos &amp; co-ops across the neighborhoods we know best.</p>
  <span class="dir-count">{len(listings)} Listings Available</span>
</div></section>

<main class="dir-wrap">
  <nav class="dir-toc" aria-label="Jump to city">{toc}</nav>
  {sections}
</main>

<footer class="dir-foot"><div class="dir-wrap" style="padding-top:0;padding-bottom:0">
  <strong>Gadura Real Estate, LLC</strong> · {OFFICE_ADDR} · <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a><br>
  Listing data via the IDX program of OneKey® MLS. Information deemed reliable but not guaranteed. Equal Housing Opportunity. © 2026 Gadura Real Estate, LLC.
</div></footer>
</body>
</html>
'''
    out_dir = os.path.join(REPO, 'homes-for-sale')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'all-listings.html'), 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'homes-for-sale/all-listings.html written: {len(listings)} listings across {len(by_city)} cities')


def write_sitemap(listings):
    """Emit sitemap-listings.xml covering every listing page (fixes 9/91 gap)."""
    urls = ['  <url>\n    <loc>' + BASE_URL + '/homes-for-sale/all-listings.html</loc>\n'
            '    <lastmod>2026-06-25</lastmod>\n    <changefreq>daily</changefreq>\n'
            '    <priority>0.9</priority>\n  </url>']
    for d in sorted(listings.values(), key=lambda x: x['slug']):
        loc = f'{BASE_URL}/homes/{d["slug"]}/'
        lastmod = d.get('date') or '2026-06-25'
        urls.append(
            f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n'
            f'    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>'
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(urls) + '\n</urlset>\n')
    out = os.path.join(REPO, 'sitemap-listings.xml')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'\nsitemap-listings.xml written: {len(urls)} listing URLs')


# ── Main ────────────────────────────────────────────────────────────
def main():
    slugs = sorted(d for d in os.listdir(HOMES_DIR)
                   if os.path.isdir(os.path.join(HOMES_DIR, d)))

    # Pass 1 — extract every listing (so related-listings can cross-link)
    listings, errors = {}, []
    for slug in slugs:
        page = os.path.join(HOMES_DIR, slug, 'index.html')
        if not os.path.exists(page):
            continue
        with open(page, 'r', encoding='utf-8') as f:
            html_txt = f.read()
        d = extract(slug, html_txt)
        if not d or not d['street']:
            errors.append(slug)
            continue
        listings[slug] = d

    all_list = list(listings.values())
    print(f'Rebuilding {len(listings)} property pages '
          f'(mortgage calc + related listings)...\n')

    # Pass 2 — write each page with its related listings
    updated = 0
    for slug, d in sorted(listings.items()):
        related = pick_related(d, all_list)
        page = os.path.join(HOMES_DIR, slug, 'index.html')
        with open(page, 'w', encoding='utf-8') as f:
            f.write(build_page(d, related))
        print(f'  OK    {slug}  —  {full_address(d)}  ({price_block(d)[0]})')
        updated += 1

    write_directory(listings)
    write_sitemap(listings)

    print(f'\n{"─"*64}\nRebuilt : {updated}\nSkipped : {len(errors)}')
    if errors:
        print('Errors  :', errors)


if __name__ == '__main__':
    main()
