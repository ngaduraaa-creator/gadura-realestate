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


# ── Page template ───────────────────────────────────────────────────
def build_page(d):
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
  </aside>
</div>

<!-- Mobile sticky bar -->
<div class="pd-mobilebar">
  <a href="tel:{PHONE_TEL}" class="pd-mb-call">{phone_svg} Call Nitin</a>
  <a href="{esc(wa_url)}" class="pd-mb-wa" target="_blank" rel="noopener">{wa_svg} WhatsApp</a>
</div>

<!-- Floating WhatsApp -->
<a href="{esc(wa_url)}" class="pd-wa-bubble" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">{wa_svg}</a>

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


# ── Main ────────────────────────────────────────────────────────────
def main():
    slugs = sorted(d for d in os.listdir(HOMES_DIR)
                   if os.path.isdir(os.path.join(HOMES_DIR, d)))
    updated, skipped, errors = 0, 0, []

    print(f'Rebuilding {len(slugs)} property pages with luxury template...\n')
    for slug in slugs:
        page = os.path.join(HOMES_DIR, slug, 'index.html')
        if not os.path.exists(page):
            skipped += 1
            continue
        with open(page, 'r', encoding='utf-8') as f:
            html_txt = f.read()
        d = extract(slug, html_txt)
        if not d or not d['street']:
            print(f'  SKIP  {slug} — could not extract data')
            errors.append(slug)
            skipped += 1
            continue
        with open(page, 'w', encoding='utf-8') as f:
            f.write(build_page(d))
        print(f'  OK    {slug}  —  {full_address(d)}  ({price_block(d)[0]})')
        updated += 1

    print(f'\n{"─"*64}\nRebuilt : {updated}\nSkipped : {skipped}')
    if errors:
        print('Errors  :', errors)


if __name__ == '__main__':
    main()
