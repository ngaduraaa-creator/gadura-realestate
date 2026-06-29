#!/usr/bin/env node
/**
 * build-property-pages.js  v3
 * ============================
 * Reads data/listings.json and generates SEO-ready, fully self-contained
 * individual HTML property pages at:  homes/{address-slug}/index.html
 *
 * v3 fixes (vs v2):
 *   - Reads BOTH data shapes: a flat array (sync-reso.js) AND the bucketed
 *     object {queensListings, brooklynListings, ...} (fetch-mls-grid.js).
 *   - Uses the real `photos` array (was reading a non-existent `image` object).
 *   - No external CSS dependency (old template linked a missing /css/main.css).
 *   - Removes the dead "View MLS" iframe pointing at the blank IDX subdomain;
 *     "More homes nearby" is now generated from our own dataset (real internal
 *     links Google can follow).
 *   - Park-Assets-style layout: photo gallery, full description, full property
 *     attributes table, agent card, working map, schema, OG, breadcrumb.
 *   - Skips placeholder-only listings gracefully (no fake stock photos shipped
 *     as if they were the real home).
 *
 * Run: node scripts/build-property-pages.js
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ── Paths ────────────────────────────────────────────────────────────────────
const ROOT          = path.resolve(__dirname, '..');
const LISTINGS_JSON = path.join(ROOT, 'data', 'listings.json');
const HOMES_DIR     = path.join(ROOT, 'homes');
const SITEMAP_OUT   = path.join(ROOT, 'sitemap-listings.xml');
const BASE_URL      = 'https://gadurarealestate.com';
const PHONE_DISPLAY = '(917) 705-0132';
const PHONE_TEL     = '+19177050132';
const PLACEHOLDER   = '/assets/images/placeholder.jpg';

// ── Generic helpers ──────────────────────────────────────────────────────────
function slugify(str) {
  return String(str || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function formatPrice(price) {
  if (!price || Number(price) <= 0) return 'Contact for Price';
  return '$' + Number(price).toLocaleString('en-US');
}

function formatNumber(n) {
  if (!n || Number(n) <= 1) return '';
  return Number(n).toLocaleString('en-US');
}

function escHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Normalize a listing from EITHER data shape into one canonical object ──────
function normalize(raw) {
  if (!raw || typeof raw !== 'object') return null;

  // Street = first comma-chunk of address (handles "25 Lisa Drive, Dix Hills, NY, 11746"
  // as well as a bare "445 Peninsula Boulevard").
  const rawAddr = (raw.address || '').trim();
  const street  = rawAddr.split(',')[0].trim() || rawAddr;

  const city  = (raw.city || raw.neighborhood || '').trim();
  const state = (raw.state || 'NY').replace(/^,|,$/g, '').trim() || 'NY';
  const zip   = (raw.zip || raw.postalCode || '').trim();

  // Photos: prefer the array; fall back to single photo fields; drop placeholders.
  let photos = [];
  if (Array.isArray(raw.photos))      photos = raw.photos.slice();
  else if (typeof raw.photos === 'string') photos = [raw.photos];
  if (raw.photo)  photos.unshift(raw.photo);
  if (raw.image && typeof raw.image === 'string') photos.unshift(raw.image);
  photos = [...new Set(
    photos.filter(p => typeof p === 'string' && p && p.startsWith('http') && !/placeholder/i.test(p))
  )];

  const mlsNumber = String(raw.mlsNumber || raw.listingID || raw.id || '').trim();

  return {
    mlsNumber,
    street,
    city,
    state,
    zip,
    county:      (raw.county || '').trim(),
    price:       Number(raw.price) || 0,
    beds:        Number(raw.beds) || 0,
    baths:       Number(raw.baths) || 0,
    sqft:        Number(raw.sqft) || 0,
    lotSize:     (raw.lotSize || '').toString().trim(),
    yearBuilt:   raw.yearBuilt || null,
    type:        (raw.type || raw.propType || raw.propertyType || '').trim(),
    status:      (raw.status || 'Active').trim(),
    badge:       (raw.badge || '').trim(),
    description: (raw.description || '').trim(),
    agent:       (raw.agent || '').trim(),
    agentPhone:  (raw.agentPhone || '').trim(),
    brokerage:   (raw.brokerage || '').trim(),
    lat:         raw.lat != null ? Number(raw.lat) : null,
    lng:         raw.lng != null ? Number(raw.lng) : null,
    photos,
  };
}

function fullAddress(l) {
  return [l.street, l.city].filter(Boolean).join(', ')
    + (l.state ? ', ' + l.state : '')
    + (l.zip ? ' ' + l.zip : '');
}

function shortAddress(l) {
  return l.street + (l.city ? ', ' + l.city : '');
}

function addressSlug(l) {
  return slugify([l.street, l.city, l.state, l.zip].filter(Boolean).join(' '));
}

function bedBathLabel(l) {
  const parts = [];
  if (l.beds)  parts.push(l.beds + ' bed');
  if (l.baths) parts.push(l.baths + ' bath');
  if (l.sqft && l.sqft > 1) parts.push(formatNumber(l.sqft) + ' sqft');
  return parts.join(' · ');
}

// ── Page template ────────────────────────────────────────────────────────────
function buildPageHtml(l, slug, nearby) {
  const addr      = fullAddress(l);
  const shortAddr = shortAddress(l);
  const pageUrl   = `${BASE_URL}/homes/${slug}/`;
  const priceStr  = formatPrice(l.price);
  const bbl       = bedBathLabel(l);
  const photos    = l.photos;
  const hero      = photos[0] || '';
  const today     = new Date().toISOString().split('T')[0];
  const year      = new Date().getFullYear();

  const statusColor = /active|just|new/i.test(l.status) ? '#16a34a'
                    : /pend|contract/i.test(l.status)   ? '#d97706'
                    : '#b91c1c';

  const metaDesc = l.price
    ? `${shortAddr} is a ${l.type || 'home'} for sale at ${priceStr}.${bbl ? ' ' + bbl + '.' : ''} View photos, full details, and contact Gadura Real Estate.`
    : `${shortAddr} — ${l.type || 'home'} listed with Gadura Real Estate. View photos and details or contact us.`;

  // Property attributes table (only rows with values)
  const facts = [
    ['Status',     l.status],
    ['Price',      l.price ? priceStr : ''],
    ['Type',       l.type],
    ['Bedrooms',   l.beds || ''],
    ['Bathrooms',  l.baths || ''],
    ['Sq Ft',      l.sqft && l.sqft > 1 ? formatNumber(l.sqft) : ''],
    ['Lot Size',   l.lotSize],
    ['Year Built', l.yearBuilt || ''],
    ['County',     l.county],
    ['City',       l.city],
    ['ZIP',        l.zip],
    ['MLS #',      l.mlsNumber],
  ].filter(([, v]) => v !== '' && v != null);

  const factsRows = facts.map(([k, v]) =>
    `          <div class="fact"><span class="fact-k">${escHtml(k)}</span><span class="fact-v">${escHtml(String(v))}</span></div>`
  ).join('\n');

  // Gallery
  let galleryHtml;
  if (photos.length > 0) {
    const thumbs = photos.slice(1, 5).map((p, i) =>
      `        <img src="${escHtml(p)}" alt="${escHtml(shortAddr)} — photo ${i + 2}" loading="lazy" width="220" height="150">`
    ).join('\n');
    galleryHtml = `
      <div class="gallery">
        <div class="hero">
          <img src="${escHtml(hero)}" alt="${escHtml(addr)}" loading="eager" width="900" height="600">
          <span class="badge" style="background:${statusColor}">${escHtml(l.badge || l.status)}</span>
        </div>
${thumbs ? `        <div class="strip">\n${thumbs}\n        </div>` : ''}
      </div>`;
  } else {
    galleryHtml = `
      <div class="gallery">
        <div class="hero hero-empty">
          <span class="badge" style="background:${statusColor}">${escHtml(l.badge || l.status)}</span>
          <div class="hero-empty-msg">Photos available on request — call ${PHONE_DISPLAY}</div>
        </div>
      </div>`;
  }

  // Map
  const mapHtml = (l.lat && l.lng)
    ? `<iframe title="Map of ${escHtml(addr)}" src="https://www.google.com/maps?q=${l.lat},${l.lng}&z=15&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>`
    : `<iframe title="Map of ${escHtml(addr)}" src="https://www.google.com/maps?q=${encodeURIComponent(addr)}&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>`;

  // Nearby (real internal links from our own dataset)
  const nearbyHtml = nearby.length ? `
      <section class="nearby">
        <h2>More Homes in ${escHtml(l.city || 'This Area')}</h2>
        <div class="nearby-grid">
${nearby.map(n => `          <a class="ncard" href="/homes/${addressSlug(n)}/">
            <div class="ncard-img"${n.photos[0] ? ` style="background-image:url('${escHtml(n.photos[0])}')"` : ''}></div>
            <div class="ncard-body">
              <span class="ncard-price">${escHtml(formatPrice(n.price))}</span>
              <span class="ncard-addr">${escHtml(shortAddress(n))}</span>
              <span class="ncard-bbl">${escHtml(bedBathLabel(n) || (n.type || ''))}</span>
            </div>
          </a>`).join('\n')}
        </div>
      </section>` : '';

  // JSON-LD
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "RealEstateListing",
        "name": addr,
        "url": pageUrl,
        "description": l.description || metaDesc,
        "image": photos.length ? photos.slice(0, 6) : undefined,
        "datePosted": today,
        "offers": l.price ? {
          "@type": "Offer",
          "price": l.price,
          "priceCurrency": "USD",
          "availability": "https://schema.org/InStock"
        } : undefined,
        "address": {
          "@type": "PostalAddress",
          "streetAddress": l.street,
          "addressLocality": l.city,
          "addressRegion": l.state || 'NY',
          "postalCode": l.zip,
          "addressCountry": "US"
        },
        "geo": (l.lat && l.lng) ? { "@type": "GeoCoordinates", "latitude": l.lat, "longitude": l.lng } : undefined,
        "numberOfRooms": l.beds || undefined,
        "floorSize": (l.sqft && l.sqft > 1) ? { "@type": "QuantitativeValue", "value": l.sqft, "unitCode": "FTK" } : undefined
      },
      {
        "@type": "BreadcrumbList",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/" },
          { "@type": "ListItem", "position": 2, "name": "Homes For Sale", "item": BASE_URL + "/homes-for-sale/" },
          { "@type": "ListItem", "position": 3, "name": shortAddr, "item": pageUrl }
        ]
      }
    ]
  };
  const jsonLdStr = JSON.stringify(jsonLd).replace(/"undefined"/g, 'null');

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escHtml(addr)} | Gadura Real Estate</title>
  <meta name="description" content="${escHtml(metaDesc)}">
  <link rel="canonical" href="${escHtml(pageUrl)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="${escHtml(addr + ' — For Sale')}">
  <meta property="og:description" content="${escHtml(metaDesc)}">
  ${hero ? `<meta property="og:image" content="${escHtml(hero)}">` : ''}
  <meta property="og:url" content="${escHtml(pageUrl)}">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">${jsonLdStr}</script>
  <style>
    :root{
      --navy:#0a2540; --navy-2:#0b2545; --green:#16a34a; --green-d:#15803d;
      --ink:#1a1a1a; --muted:#667085; --line:#e5e7eb; --bg:#f7f9fc;
    }
    *{box-sizing:border-box}
    body{font-family:'Helvetica Neue',Arial,sans-serif;margin:0;color:var(--ink);background:#fff;line-height:1.5}
    a{color:inherit}
    img{max-width:100%}

    /* Nav */
    .nav{background:var(--navy);display:flex;align-items:center;justify-content:space-between;padding:12px 24px;gap:16px;flex-wrap:wrap}
    .nav a{color:#fff;text-decoration:none}
    .nav .logo{font-size:1.05rem;font-weight:800;display:flex;align-items:center;gap:8px}
    .nav .logo img{height:34px;width:auto}
    .nav .links{display:flex;gap:18px;font-size:.9rem}
    .nav .links a:hover{color:#6fcf97}
    .nav .cta{background:var(--green);padding:8px 16px;border-radius:6px;font-weight:700;font-size:.85rem}
    .nav .cta:hover{background:var(--green-d)}
    @media(max-width:760px){.nav .links{display:none}}

    /* Breadcrumb */
    .crumb{padding:10px 24px;font-size:.8rem;color:var(--muted);background:var(--bg);border-bottom:1px solid var(--line)}
    .crumb a{color:var(--navy);text-decoration:none}
    .crumb a:hover{text-decoration:underline}
    .crumb span{margin:0 6px;color:#bbb}

    /* Layout */
    .wrap{max-width:1140px;margin:0 auto;padding:24px 20px 56px;display:grid;grid-template-columns:1fr 340px;gap:36px}
    @media(max-width:880px){.wrap{grid-template-columns:1fr}}

    /* Gallery */
    .gallery{margin-bottom:22px}
    .hero{position:relative;border-radius:12px;overflow:hidden}
    .hero img{width:100%;height:440px;object-fit:cover;display:block}
    .hero-empty{height:300px;background:linear-gradient(135deg,#0a2540,#13395f);display:flex;align-items:center;justify-content:center}
    .hero-empty-msg{color:#cde;font-size:1rem;font-weight:600;text-align:center;padding:0 20px}
    @media(max-width:600px){.hero img{height:250px}}
    .badge{position:absolute;top:14px;left:14px;color:#fff;font-size:.72rem;font-weight:800;padding:5px 12px;border-radius:5px;text-transform:uppercase;letter-spacing:.06em}
    .strip{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px}
    .strip img{width:100%;height:104px;object-fit:cover;border-radius:8px}

    /* Price + address */
    .price{font-size:2.2rem;font-weight:800;color:var(--navy);margin:4px 0 2px}
    h1.addr{font-size:1.3rem;font-weight:600;color:#334;margin:0 0 18px;line-height:1.3}

    /* Stat bar */
    .stats{display:flex;border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:26px}
    .stat{flex:1;text-align:center;padding:14px 8px;border-right:1px solid var(--line)}
    .stat:last-child{border-right:none}
    .stat b{display:block;font-size:1.45rem;font-weight:800;color:var(--navy)}
    .stat span{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}

    section{margin-bottom:30px}
    section h2{font-size:1.15rem;font-weight:800;color:var(--navy);border-bottom:2px solid var(--line);padding-bottom:9px;margin:0 0 16px}
    .desc{font-size:.97rem;line-height:1.75;color:#333;white-space:pre-line}

    /* Facts grid */
    .facts{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
    @media(max-width:520px){.facts{grid-template-columns:1fr}}
    .fact{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:11px 14px;display:flex;justify-content:space-between;gap:12px}
    .fact-k{font-size:.74rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
    .fact-v{font-size:.92rem;font-weight:700;color:var(--ink);text-align:right}

    /* Map */
    .map{border-radius:12px;overflow:hidden;border:1px solid var(--line)}
    .map iframe{width:100%;height:320px;border:0;display:block}

    /* Nearby */
    .nearby-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    @media(max-width:680px){.nearby-grid{grid-template-columns:1fr 1fr}}
    .ncard{display:block;border:1px solid var(--line);border-radius:10px;overflow:hidden;text-decoration:none;transition:box-shadow .15s,transform .15s}
    .ncard:hover{box-shadow:0 8px 24px rgba(10,37,64,.13);transform:translateY(-2px)}
    .ncard-img{height:120px;background:#dde6f0 center/cover no-repeat}
    .ncard-body{padding:10px 12px;display:flex;flex-direction:column;gap:2px}
    .ncard-price{font-weight:800;color:var(--navy)}
    .ncard-addr{font-size:.82rem;color:#445}
    .ncard-bbl{font-size:.74rem;color:var(--muted)}

    /* Sidebar */
    .side{position:sticky;top:18px;align-self:start}
    .lead{background:var(--navy);color:#fff;border-radius:14px;padding:22px 20px;margin-bottom:18px}
    .lead h3{margin:0 0 4px;font-size:1.05rem}
    .lead p{margin:0 0 14px;font-size:.83rem;color:#b6c8db}
    .lead input,.lead textarea{width:100%;padding:10px 12px;border:0;border-radius:7px;font-size:.9rem;margin-bottom:10px;background:rgba(255,255,255,.12);color:#fff}
    .lead input::placeholder,.lead textarea::placeholder{color:#9fb3c8}
    .lead textarea{height:74px;resize:vertical}
    .lead button{display:block;width:100%;background:var(--green);color:#fff;border:0;padding:13px;border-radius:8px;font-weight:800;font-size:.95rem;cursor:pointer}
    .lead button:hover{background:var(--green-d)}
    .callcard{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:15px;text-align:center}
    .callcard a{color:var(--green-d);font-size:1.15rem;font-weight:800;text-decoration:none}
    .callcard p{margin:4px 0 0;font-size:.78rem;color:var(--muted)}
    .agentcard{margin-top:16px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:14px;font-size:.82rem;color:#445}
    .agentcard b{color:var(--ink)}
    .attr{font-size:.7rem;color:var(--muted);line-height:1.55;margin-top:18px}

    /* Footer */
    .ft{background:var(--navy);color:#8ca0b8;font-size:.8rem;padding:30px 24px;text-align:center;line-height:1.7}
    .ft a{color:#6fcf97;text-decoration:none}
    .ft .fl{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin-bottom:12px}
  </style>
</head>
<body>

<header class="nav">
  <a href="/" class="logo"><img src="/images/logo-icon.png" alt="Gadura Real Estate" onerror="this.style.display='none'"><span>Gadura Real Estate</span></a>
  <nav class="links" aria-label="Main">
    <a href="/homes-for-sale/">Homes For Sale</a>
    <a href="/neighborhoods/">Neighborhoods</a>
    <a href="/home-value.html">Home Value</a>
    <a href="/listing-alerts.html">Listing Alerts</a>
    <a href="/about.html">About</a>
  </nav>
  <a href="tel:${PHONE_TEL}" class="cta">${PHONE_DISPLAY}</a>
</header>

<nav class="crumb" aria-label="Breadcrumb">
  <a href="/">Home</a><span>›</span>
  <a href="/homes-for-sale/">Homes For Sale</a><span>›</span>
  ${l.city ? `<a href="/homes-for-sale/">${escHtml(l.city)}</a><span>›</span>` : ''}
  <span>${escHtml(l.street)}</span>
</nav>

<div class="wrap">
  <main id="main-content">
${galleryHtml}

    <p class="price">${escHtml(priceStr)}</p>
    <h1 class="addr">${escHtml(addr)}</h1>

    <div class="stats">
      ${l.beds ? `<div class="stat"><b>${escHtml(String(l.beds))}</b><span>Bedrooms</span></div>` : ''}
      ${l.baths ? `<div class="stat"><b>${escHtml(String(l.baths))}</b><span>Bathrooms</span></div>` : ''}
      ${l.sqft && l.sqft > 1 ? `<div class="stat"><b>${escHtml(formatNumber(l.sqft))}</b><span>Sq Ft</span></div>` : ''}
      ${l.type ? `<div class="stat"><b style="font-size:1rem">${escHtml(l.type)}</b><span>Type</span></div>` : ''}
    </div>

    ${l.description ? `<section><h2>About This Home</h2><p class="desc">${escHtml(l.description)}</p></section>` : ''}

    <section>
      <h2>Property Details</h2>
      <div class="facts">
${factsRows}
      </div>
    </section>

    <section>
      <h2>Location</h2>
      <div class="map">${mapHtml}</div>
    </section>
${nearbyHtml}

    <p class="attr">
      Listing data displayed on this page is provided through the OneKey&reg; MLS Internet Data Exchange (IDX) program.
      Information is deemed reliable but not guaranteed. &copy; ${year} OneKey&reg; MLS. All rights reserved.
      <a href="/idx-policy.html">IDX &amp; VOW Policy</a>.
    </p>
  </main>

  <aside class="side" aria-label="Contact agent">
    <div class="lead">
      <h3>Interested in This Home?</h3>
      <p>Get photos, a private showing, and pricing details — we reply within minutes.</p>
      <form action="/contact.html" method="get">
        <input type="hidden" name="property" value="${escHtml(addr)}">
        <input type="text" name="name" placeholder="Your Name" required>
        <input type="tel" name="phone" placeholder="Phone Number">
        <input type="email" name="email" placeholder="Email Address" required>
        <textarea name="message">I'm interested in ${escHtml(shortAddr)}.</textarea>
        <button type="submit">Request Info →</button>
      </form>
    </div>
    <div class="callcard">
      <a href="tel:${PHONE_TEL}">${PHONE_DISPLAY}</a>
      <p>Call or text us any time</p>
    </div>
    ${(l.agent || l.brokerage) ? `<div class="agentcard">
      ${l.agent ? `Listed by <b>${escHtml(l.agent)}</b>` : ''}${l.brokerage ? `<br>${escHtml(l.brokerage)}` : ''}
    </div>` : ''}
  </aside>
</div>

<footer class="ft">
  <div class="fl">
    <a href="/homes-for-sale/">Homes For Sale</a>
    <a href="/neighborhoods/">Neighborhoods</a>
    <a href="/home-value.html">Home Value</a>
    <a href="/listing-alerts.html">Listing Alerts</a>
    <a href="/about.html">About</a>
    <a href="/contact.html">Contact</a>
    <a href="/idx-policy.html">IDX Policy</a>
  </div>
  <p>Gadura Real Estate, LLC &mdash; 106-09 101st Ave, Ozone Park, NY 11416</p>
  <p>Licensed Real Estate Broker, State of New York &bull; <a href="tel:${PHONE_TEL}">${PHONE_DISPLAY}</a></p>
  <p>&copy; ${year} Gadura Real Estate, LLC. All rights reserved.</p>
</footer>

</body>
</html>`;
}

// ── Load + flatten listings from either data shape ───────────────────────────
function loadListings() {
  if (!fs.existsSync(LISTINGS_JSON)) {
    console.error('listings.json not found:', LISTINGS_JSON);
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(LISTINGS_JSON, 'utf8'));

  let raw = [];
  if (Array.isArray(data)) {
    raw = data;                                   // flat array (sync-reso.js)
  } else if (data && typeof data === 'object') {  // bucketed object (fetch-mls-grid.js)
    raw = [
      ...(data.activeListings     || []),
      ...(data.areaListings       || []),
      ...(data.woodhavenListings  || []),
      ...(data.queensListings     || []),
      ...(data.brooklynListings   || []),
      ...(data.longIslandListings || []),
    ];
  }

  // Normalize + dedupe by MLS number (fall back to address slug)
  const seen = new Set();
  const out = [];
  for (const r of raw) {
    const n = normalize(r);
    if (!n || !n.street) continue;
    const key = n.mlsNumber || addressSlug(n);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(n);
  }
  return out;
}

// ── Main ─────────────────────────────────────────────────────────────────────
function main() {
  const listings = loadListings();
  console.log(`Building ${listings.length} property pages…`);

  // Index by city for "nearby"
  const byCity = {};
  for (const l of listings) {
    const c = (l.city || '').toLowerCase();
    (byCity[c] = byCity[c] || []).push(l);
  }

  fs.mkdirSync(HOMES_DIR, { recursive: true });
  const today = new Date().toISOString().split('T')[0];
  const sitemapUrls = [];

  for (const l of listings) {
    const slug = addressSlug(l);
    if (!slug) { console.warn('  skip (no address):', l.mlsNumber); continue; }

    const nearby = (byCity[(l.city || '').toLowerCase()] || [])
      .filter(n => n !== l)
      .slice(0, 3);

    const dir  = path.join(HOMES_DIR, slug);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'index.html'), buildPageHtml(l, slug, nearby), 'utf8');

    const url = `${BASE_URL}/homes/${slug}/`;
    sitemapUrls.push(url);
    console.log('  ✓', url);
  }

  const sitemapXml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapUrls.map(u => `  <url>
    <loc>${u}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`).join('\n')}
</urlset>`;
  fs.writeFileSync(SITEMAP_OUT, sitemapXml, 'utf8');

  console.log(`\n✅ Generated ${sitemapUrls.length} pages + sitemap-listings.xml (lastmod ${today})`);
}

main();
