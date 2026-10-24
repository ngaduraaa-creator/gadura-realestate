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
 * Listing-truth rules:
 *   - Fails closed. An empty or unreadable feed, or a record without address,
 *     MLS #, status, type, price or lastSync, or with a status other than
 *     Active or Pending, exits non-zero BEFORE anything is written.
 *   - Every page states the feed status and the date the IDX feed last returned
 *     the record ("IDX feed as of ..."). Nothing is inferred beyond the feed.
 *   - Lease records (type containing "lease" or "rent") are labelled for lease,
 *     never "for sale", and sale pages never list them under "More Homes".
 *   - Pending is never marked available (no schema.org InStock).
 *   - A record the IDX feed has not returned for more than 7 days never gets a
 *     NEW page and is not submitted in the sitemap.
 *
 * Listing-truth rules (freshness, photos, tracking):
 *   - Freshness comes ONLY from the record's own lastSync (ISO-8601 UTC as
 *     sync-reso.js writes it), measured from this run's start time. Another
 *     record's lastSync, the file's commit or modification time and any
 *     feed-level time are never used. Missing, malformed or future lastSync
 *     fails closed (nothing written); a future lastSync never counts as fresh.
 *     fresh <=> 0 <= build time - lastSync <= STALE_DAYS (7) days.
 *   - A stale record's existing page is regenerated with a dated "not
 *     confirmed" notice, no schema.org availability, and dated og:title.
 *   - Two records sharing an address slug: the page shows the record with the
 *     newest own lastSync; a tie goes to the larger MLS number (independent of
 *     feed order). One DECISION line per record is logged (MLS number only).
 *   - IDX photos are NOT displayed (gallery, og:image, JSON-LD image, card
 *     backgrounds) until the broker confirms display rights
 *     (IDX_PHOTO_DISPLAY_CONFIRMED). The feed's photos still count as photo
 *     provenance for the sitemap rule.
 *   - Tracking state is preserved per page: an existing page's GRE_GA4 block is
 *     copied verbatim; a page without one (or a new page) gets none. Tracking
 *     code outside the GRE_GA4 markers fails closed.
 *   - Pending records are never described as "for sale" (Offered: Sale pending).
 *   - A stale record never presents itself as currently available: its page
 *     shows "Not confirmed by the listing feed since <lastSync date>" next to
 *     the price and status (the feed status text itself is kept), its meta
 *     description says the same, and its schema.org offer has no availability.
 *     A "More Homes" card for a stale record carries the same line.
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
// Contact details come from data/business-contact.json so that one edit there
// changes every generated surface. They used to be hardcoded here and in
// scripts/generate_market_report.py, which is how a page family could silently
// revert a corrected number on the next build.
const CONTACT       = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'business-contact.json'), 'utf8'));
const PHONE_DISPLAY = CONTACT.phone_display;
const PHONE_TEL     = CONTACT.phone_tel;
const PLACEHOLDER   = '/assets/images/placeholder.jpg';

// Freshness: a record is confirmed only by its OWN lastSync.
const STALE_DAYS = 7;           // the sync runs every ~4h
const DAY_MS     = 86400000;
const ISO_UTC    = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d{1,3})?Z$/;

// IDX photo display rights are unconfirmed (the broker has not confirmed them). While false, no feed photo URL is
// written to any page. Changing this needs the broker's written confirmation of display rights.
const IDX_PHOTO_DISPLAY_CONFIRMED = false;

// Tracking state of an existing page is preserved; nothing here adds tracking to a page.
const GA4_BLOCK_RE = /<!-- GRE_GA4_START -->[\s\S]*?<!-- GRE_GA4_END -->\n?/;
const TRACKING_RE  = /googletagmanager\.com|google-analytics\.com|\bgtag\s*\(|\bdataLayer\b|fbq\s*\(|clarity\.ms|hotjar/i;

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

// ── Listing-truth helpers ────────────────────────────────────────────────────
const LISTABLE_STATUSES = ['Active', 'Pending'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// 'lease' for Commercial Lease / rentals, 'sale' otherwise. Decided from the feed's type only.
function listingKind(l) {
  return /lease|rent/i.test(l.type || '') ? 'lease' : 'sale';
}

// Calendar date (UTC) on which the IDX feed last returned this record, e.g. "Oct 19, 2026".
// This is when the feed confirmed the record, not a list date (the feed has none).
function feedDate(l) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(l.lastSync || ''));
  return m ? `${MONTHS[Number(m[2]) - 1]} ${Number(m[3])}, ${m[1]}` : '';
}

// Strict lastSync parse: ISO-8601 UTC and a real calendar time, else NaN.
function parseLastSync(v) {
  if (typeof v !== 'string') return NaN;
  const m = ISO_UTC.exec(v);
  if (!m) return NaN;
  const t = Date.parse(v);
  if (Number.isNaN(t)) return NaN;
  const d = new Date(t);
  if (d.getUTCFullYear() !== Number(m[1]) || d.getUTCMonth() + 1 !== Number(m[2]) || d.getUTCDate() !== Number(m[3])
      || d.getUTCHours() !== Number(m[4]) || d.getUTCMinutes() !== Number(m[5]) || d.getUTCSeconds() !== Number(m[6])) return NaN;
  return t;
}

// Freshness of ONE record at buildMs, from that record's own lastSync and nothing else.
function freshness(l, buildMs) {
  if (l.lastSync == null || l.lastSync === '') return { valid: false, fresh: false, ageDays: null, rule: 'LASTSYNC_MISSING' };
  const t = parseLastSync(l.lastSync);
  if (Number.isNaN(t)) return { valid: false, fresh: false, ageDays: null, rule: 'LASTSYNC_MALFORMED' };
  if (t > buildMs)     return { valid: false, fresh: false, ageDays: null, rule: 'LASTSYNC_FUTURE' };
  const age = buildMs - t;
  const fresh = age <= STALE_DAYS * DAY_MS;
  return { valid: true, fresh, ageDays: Math.floor(age / DAY_MS), rule: fresh ? 'FRESH_LE_7D' : 'STALE_GT_7D' };
}

// Which of two records sharing a slug the page shows: newest own lastSync; tie -> larger MLS number.
function mlsKey(l) {
  const m = String(l.mlsNumber || '');
  return /^\d+$/.test(m) ? [0, Number(m), m] : [1, 0, m];
}
function preferRecord(a, b) {
  const ta = parseLastSync(a.lastSync), tb = parseLastSync(b.lastSync);
  if (ta !== tb) return ta > tb;
  const ka = mlsKey(a), kb = mlsKey(b);
  for (let i = 0; i < 3; i++) if (ka[i] !== kb[i]) return ka[i] > kb[i];
  return false;
}

// Tracking block an existing page already carries ('' if none). Unmarked tracking -> error.
function existingTracking(file) {
  if (!fs.existsSync(file)) return { block: '', state: 'none (new page)' };
  const html = fs.readFileSync(file, 'utf8');
  const m = GA4_BLOCK_RE.exec(html);
  const rest = m ? html.replace(m[0], '') : html;
  if (TRACKING_RE.test(rest)) return { error: 'tracking code outside the GRE_GA4 markers; cannot preserve it exactly' };
  return { block: m ? m[0] : '', state: m ? 'GRE_GA4 block preserved verbatim' : 'none' };
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
    status:      (raw.status || '').trim(),   // no default: validateFeed() rejects a record without one
    badge:       (raw.badge || '').trim(),
    description: (raw.description || '').trim(),
    agent:       (raw.agent || '').trim(),
    agentPhone:  (raw.agentPhone || '').trim(),
    brokerage:   (raw.brokerage || '').trim(),
    lat:         raw.lat != null ? Number(raw.lat) : null,
    lng:         raw.lng != null ? Number(raw.lng) : null,
    photos,
    // Carried verbatim, never defaulted: sync-reso.js stamps lastSync on a record each time IDX returns it,
    // so it is the only evidence in the feed of when the listing was last confirmed.
    lastSync:    raw.lastSync || null,
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
function buildPageHtml(l, slug, nearby, opts) {
  const fresh     = opts.fresh;        // from this record's own lastSync only (freshness())
  const tracking  = opts.tracking;     // the existing page's GRE_GA4 block verbatim, or ''
  const addr      = fullAddress(l);
  const shortAddr = shortAddress(l);
  const pageUrl   = `${BASE_URL}/homes/${slug}/`;
  const priceStr  = formatPrice(l.price);
  const bbl       = bedBathLabel(l);
  const photos    = IDX_PHOTO_DISPLAY_CONFIRMED ? l.photos : [];   // feed photos are not displayed (rights unconfirmed)
  const hero      = photos[0] || '';
  const year      = new Date().getFullYear();
  const isLease   = listingKind(l) === 'lease';
  const isActive  = l.status === 'Active';
  const asOf      = feedDate(l);
  const ogBase    = isLease ? 'For Lease' : (isActive ? 'For Sale' : 'Sale Pending');
  const ogSuffix  = fresh ? ogBase : `${ogBase} as of ${asOf}`;
  const staleLine = fresh ? ''
    : `    <p class="stale-line"><b>Not confirmed by the listing feed since ${escHtml(asOf)}.</b> The feed has not returned this listing since then, so its current status is not confirmed.</p>\n`;
  const noun      = isLease ? 'Property' : 'Home';

  const statusColor = !fresh ? '#6b7280'
                    : /active|just|new/i.test(l.status) ? '#16a34a'
                    : /pend|contract/i.test(l.status)   ? '#d97706'
                    : '#b91c1c';
  const badgeText = fresh ? (l.badge || l.status) : `Last confirmed ${asOf}`;

  // Every claim below comes from the feed record; status and price are dated to the feed.
  const view = photos.length ? 'View photos and details' : 'View details';
  const staleNote = fresh ? '' : ` Not confirmed by the listing feed since ${asOf}.`;
  const metaDesc = isLease
    ? `${shortAddr}: ${l.type} listing offered for lease, listed lease price ${priceStr}, status ${l.status} (IDX feed as of ${asOf}).${staleNote} ${view} or contact Gadura Real Estate.`
    : isActive
      ? `${shortAddr} is a ${l.type} listing for sale at ${priceStr}, status Active (IDX feed as of ${asOf}).${staleNote}${bbl ? ' ' + bbl + '.' : ''} ${view} or contact Gadura Real Estate.`
      : `${shortAddr}: ${l.type} listing with a pending sale, status ${l.status} (IDX feed as of ${asOf}); list price ${priceStr}.${staleNote}${bbl ? ' ' + bbl + '.' : ''} ${view} or contact Gadura Real Estate.`;

  // Property attributes table (only rows with values)
  const facts = [
    ['Status',     l.status],
    ['Offered',    isLease ? 'For lease' : (isActive ? 'For sale' : 'Sale pending')],
    [isLease ? 'Lease price' : 'Price', l.price ? priceStr : ''],
    ['IDX feed date', asOf],
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
          <span class="badge" style="background:${statusColor}">${escHtml(badgeText)}</span>
        </div>
${thumbs ? `        <div class="strip">\n${thumbs}\n        </div>` : ''}
      </div>`;
  } else {
    galleryHtml = `
      <div class="gallery">
        <div class="hero hero-empty">
          <span class="badge" style="background:${statusColor}">${escHtml(badgeText)}</span>
          <div class="hero-empty-msg">No listing photos are shown on this page.</div>
        </div>
      </div>`;
  }

  // Map
  const mapHtml = (l.lat && l.lng)
    ? `<iframe title="Map of ${escHtml(addr)}" src="https://www.google.com/maps?q=${l.lat},${l.lng}&z=15&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>`
    : `<iframe title="Map of ${escHtml(addr)}" src="https://www.google.com/maps?q=${encodeURIComponent(addr)}&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>`;

  // Nearby (real internal links from our own dataset). main() passes only records of the
  // same kind (sale or lease) whose page exists after this run, so nothing here can 404.
  const nearbyHtml = nearby.length ? `
      <section class="nearby">
        <h2>${isLease ? 'More Listings for Lease' : 'More Homes'} in ${escHtml(l.city || 'This Area')}</h2>
        <div class="nearby-grid">
${nearby.map(n => `          <a class="ncard" href="/homes/${addressSlug(n)}/">
            <div class="ncard-img"${IDX_PHOTO_DISPLAY_CONFIRMED && n.photos[0] ? ` style="background-image:url('${escHtml(n.photos[0])}')"` : ''}></div>
            <div class="ncard-body">
              <span class="ncard-price">${escHtml(formatPrice(n.price))}</span>
              <span class="ncard-addr">${escHtml(shortAddress(n))}</span>
              <span class="ncard-bbl">${escHtml([n.status, bedBathLabel(n) || n.type].filter(Boolean).join(' · '))}</span>
              <span class="ncard-bbl">IDX feed as of ${escHtml(feedDate(n))}</span>
${opts.isFresh(n) ? '' : `              <span class="ncard-bbl ncard-stale">Not confirmed by the listing feed since ${escHtml(feedDate(n))}</span>\n`}            </div>
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
        // No datePosted: the feed has no list date (lastSync is when IDX last returned the record),
        // and the build date is not a posting date.
        // availability mirrors the feed status: InStock only for an Active record confirmed within
        // STALE_DAYS; Pending and stale records get none (current availability is not known).
        "offers": l.price ? {
          "@type": "Offer",
          "price": l.price,
          "priceCurrency": "USD",
          "businessFunction": isLease ? "http://purl.org/goodrelations/v1#LeaseOut" : undefined,
          "availability": (isActive && fresh) ? "https://schema.org/InStock" : undefined
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
        "numberOfBedrooms": l.beds || undefined,
        "floorSize": (l.sqft && l.sqft > 1) ? { "@type": "QuantitativeValue", "value": l.sqft, "unitCode": "FTK" } : undefined
      },
      {
        "@type": "BreadcrumbList",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/" },
          ...(isLease
            ? [{ "@type": "ListItem", "position": 2, "name": shortAddr, "item": pageUrl }]
            : [{ "@type": "ListItem", "position": 2, "name": "Homes For Sale", "item": BASE_URL + "/homes-for-sale/" },
               { "@type": "ListItem", "position": 3, "name": shortAddr, "item": pageUrl }])
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
  <meta property="og:title" content="${escHtml(addr + ' — ' + ogSuffix)}">
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
    .wrap>main,.wrap>.side{min-width:0}  /* photo widths must not widen the phone layout */

    /* Gallery */
    .gallery{margin-bottom:22px}
    .hero{position:relative;border-radius:12px;overflow:hidden}
    .hero img{width:100%;height:440px;object-fit:cover;display:block}
    .hero-empty{height:300px;background:linear-gradient(135deg,#0a2540,#13395f);display:flex;align-items:center;justify-content:center}
    .hero-empty-msg{color:#cde;font-size:1rem;font-weight:600;text-align:center;padding:0 20px}
    @media(max-width:600px){.hero img{height:250px}}
    .badge{position:absolute;top:14px;left:14px;color:#fff;font-size:.72rem;font-weight:800;padding:5px 12px;border-radius:5px;text-transform:uppercase;letter-spacing:.06em}
    .strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:8px}
    .strip img{width:100%;height:104px;object-fit:cover;border-radius:8px}

    /* Price + address */
    .price{font-size:2.2rem;font-weight:800;color:var(--navy);margin:4px 0 2px}
    .price-note{font-size:.82rem;color:var(--muted);margin:0 0 4px}
    .asof{font-size:.85rem;color:#334;margin:0 0 10px}
    .stale-line{font-size:.88rem;color:#7c2d12;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:8px 12px;margin:6px 0 10px}
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
    .ncard-stale{color:#9a3412;font-weight:600}

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
    .lead .lead-call{display:block;background:var(--green);color:#fff;text-align:center;text-decoration:none;padding:13px;border-radius:8px;font-weight:800;font-size:.95rem;margin-bottom:10px}
    .lead .lead-call:hover,.lead .lead-call:focus{background:var(--green-d)}
    .lead .lead-link{display:block;color:#fff;font-size:.86rem;margin:6px 0}
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
${tracking}</head>
<body>

<header class="nav">
  <a href="/" class="logo"><img src="/images/logo-icon.png" alt="Gadura Real Estate" onerror="this.style.display='none'"><span>Gadura Real Estate</span></a>
  <nav class="links" aria-label="Main">
    <a href="/homes-for-sale/">Homes For Sale</a>
    <a href="/neighborhoods/">Neighborhoods</a>
    <a href="/home-value/">Home Value</a>
    <a href="/listing-alerts.html">Listing Alerts</a>
    <a href="/about.html">About</a>
  </nav>
  <a href="tel:${PHONE_TEL}" class="cta">${PHONE_DISPLAY}</a>
</header>

<nav class="crumb" aria-label="Breadcrumb">
  <a href="/">Home</a><span>›</span>
  ${isLease ? '' : `<a href="/homes-for-sale/">Homes For Sale</a><span>›</span>
  ${l.city ? `<a href="/homes-for-sale/">${escHtml(l.city)}</a><span>›</span>` : ''}`}
  <span>${escHtml(l.street)}</span>
</nav>

<div class="wrap">
  <main id="main-content">
${galleryHtml}

    <p class="price">${escHtml(priceStr)}</p>
${isLease ? `    <p class="price-note">For lease. Listed lease price; the listing feed does not state the lease period.</p>\n` : ''}${staleLine}    <p class="asof">Status: <b>${escHtml(l.status)}</b> · ${isLease ? 'lease price' : 'price'} and status as reported by the OneKey&reg; MLS IDX feed as of ${escHtml(asOf)}.</p>
    <h1 class="addr">${escHtml(addr)}</h1>

    <div class="stats">
      ${l.beds ? `<div class="stat"><b>${escHtml(String(l.beds))}</b><span>Bedrooms</span></div>` : ''}
      ${l.baths ? `<div class="stat"><b>${escHtml(String(l.baths))}</b><span>Bathrooms</span></div>` : ''}
      ${l.sqft && l.sqft > 1 ? `<div class="stat"><b>${escHtml(formatNumber(l.sqft))}</b><span>Sq Ft</span></div>` : ''}
      ${l.type ? `<div class="stat"><b style="font-size:1rem">${escHtml(l.type)}</b><span>Type</span></div>` : ''}
    </div>

    ${l.description ? `<section><h2>About This ${noun}</h2><p class="desc">${escHtml(l.description)}</p></section>` : ''}

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
      <h3>Interested in This ${noun}?</h3>
      <p>${!fresh ? `The OneKey&reg; MLS IDX feed last returned this listing on ${escHtml(asOf)}; its current status is not confirmed. For details, contact the Gadura Real Estate office by phone or email.`
        : isActive ? 'For photos, a showing or pricing details, contact the Gadura Real Estate office by phone or email.'
        : `This listing's status is ${escHtml(l.status)}. For details, contact the Gadura Real Estate office by phone or email.`}</p>
      <div class="contact-options">
        <a class="lead-call" href="tel:${PHONE_TEL}">Call ${PHONE_DISPLAY}</a>
        <a class="lead-link" href="mailto:info@gadurarealestate.com">Email info@gadurarealestate.com</a>
        <a class="lead-link" href="/contact.html">Go to the contact page</a>
      </div>
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
    <a href="/home-value/">Home Value</a>
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
  let noAddress = 0;
  for (const r of raw) {
    const n = normalize(r);
    if (!n || !n.street) { noAddress++; continue; }
    const key = n.mlsNumber || addressSlug(n);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(n);
  }
  out.recordsWithoutAddress = noAddress;   // validateFeed() refuses to build if any
  return out;
}

// ── Fail closed on missing or incomplete feed data ───────────────────────────
// Nothing has been written when this runs. Any problem exits non-zero and leaves
// homes/ and sitemap-listings.xml exactly as they were.
function validateFeed(listings, buildMs) {
  const problems = [];
  if (listings.recordsWithoutAddress) problems.push(`${listings.recordsWithoutAddress} record(s) without an address`);
  if (listings.length === 0) problems.push('the feed holds no listings');
  for (const l of listings) {
    const id = l.mlsNumber || l.street;
    if (!l.mlsNumber) problems.push(`${id}: no MLS number`);
    if (!LISTABLE_STATUSES.includes(l.status)) problems.push(`${id}: status ${JSON.stringify(l.status)} is not one of ${LISTABLE_STATUSES.join('/')}`);
    if (!l.type) problems.push(`${id}: no property type, so sale or lease cannot be told`);
    if (!(l.price > 0)) problems.push(`${id}: no price`);
    const f = freshness(l, buildMs);
    if (f.rule === 'LASTSYNC_MISSING')   problems.push(`${id}: no lastSync`);
    if (f.rule === 'LASTSYNC_MALFORMED') problems.push(`${id}: lastSync ${JSON.stringify(l.lastSync)} is not an ISO-8601 UTC time`);
    if (f.rule === 'LASTSYNC_FUTURE')    problems.push(`${id}: lastSync ${l.lastSync} is after this run's start (${new Date(buildMs).toISOString()}); a future time never counts as fresh`);
  }
  if (problems.length) {
    for (const p of problems) console.error('  ✗ FEED-REJECT', p);
    console.error(`FAIL-CLOSED: ${problems.length} feed problem(s); no page and no sitemap was written.`);
    process.exit(1);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────
function main() {
  // The build time is read once; every freshness decision in this run is measured from it.
  const BUILD_MS = Date.now();
  const listings = loadListings();
  validateFeed(listings, BUILD_MS);
  console.log(`Building from ${listings.length} feed records at ${new Date(BUILD_MS).toISOString()}…`);
  const fr = new Map(listings.map(l => [l, freshness(l, BUILD_MS)]));
  const decisions = new Map();     // record -> { page, sitemap }

  // One page per address slug. Two feed records can share a slug (two units at one street
  // address); the page shows the record with the newest own lastSync (tie: larger MLS number),
  // and the collision is logged for the broker.
  const bySlug = new Map();
  for (const l of listings) {
    const slug = addressSlug(l);
    const cur = bySlug.get(slug);
    if (!cur) { bySlug.set(slug, l); continue; }
    const keep = preferRecord(l, cur) ? l : cur;
    const drop = keep === l ? cur : l;
    console.log(`  ! SLUG_COLLISION ${slug}: MLS ${cur.mlsNumber} and ${l.mlsNumber}; page shows MLS ${keep.mlsNumber} (newer own lastSync, tie -> larger MLS number)`);
    decisions.set(drop, { page: 'OMITTED_SLUG_COLLISION', sitemap: '-', rule: `SLUG_SHARED_WITH_${keep.mlsNumber}_NEWER_OWN_LASTSYNC` });
    bySlug.set(slug, keep);
  }

  // Per-record staleness. sync-reso.js stamps lastSync each time IDX returns a record, and a
  // record IDX stops returning keeps its last values (including status) frozen. So a record
  // not confirmed for more than STALE_DAYS never gets a NEW page and is not put in the
  // sitemap. An existing page is regenerated with a dated "not confirmed" notice but not
  // submitted; deleting indexed pages is an owner decision, not a build step.
  const isStale = (l) => !fr.get(l).fresh;
  const ageDays = (l) => fr.get(l).ageDays;

  // Broker containment: the same file scripts/dgp/test_placeholder_denylist.py enforces.
  // A missing file is fatal; nothing has been written yet.
  const DENYLIST_FILE = path.join(__dirname, 'dgp', 'placeholder_sitemap_denylist.txt');
  const SITEMAP_DENYLIST = new Set(
    fs.readFileSync(DENYLIST_FILE, 'utf8')
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#'))
      .map(line => line.replace(/\/$/, ''))
  );

  const plan = [];
  for (const [slug, l] of bySlug) {
    const pageExists = fs.existsSync(path.join(HOMES_DIR, slug, 'index.html'));
    if (isStale(l) && !pageExists) {
      console.log(`  ⊘ SKIP_STALE (${ageDays(l)}d unconfirmed, no existing page):`, slug);
      decisions.set(l, { page: 'OMITTED_STALE_NO_PAGE', sitemap: '-', rule: fr.get(l).rule });
      continue;
    }
    plan.push({ slug, l });
  }

  if (fs.existsSync(HOMES_DIR)) {
    for (const d of fs.readdirSync(HOMES_DIR)) {
      if (!bySlug.has(d) && fs.existsSync(path.join(HOMES_DIR, d, 'index.html'))) {
        console.log('  ! ORPHAN_PAGE (no feed record; left in place, not in the sitemap; owner decides):', d);
      }
    }
  }

  // Render everything before writing anything. "More Homes" cards: same city, same kind
  // (sale or lease), never this page, and only pages that exist after this run.
  const trackingErrors = [];
  const out = plan.map(({ slug, l }) => {
    const nearby = plan
      .filter(p => p.slug !== slug
        && (p.l.city || '').toLowerCase() === (l.city || '').toLowerCase()
        && listingKind(p.l) === listingKind(l))
      .slice(0, 3)
      .map(p => p.l);
    const tr = existingTracking(path.join(HOMES_DIR, slug, 'index.html'));
    if (tr.error) { trackingErrors.push(`${slug}: ${tr.error}`); return null; }
    return { slug, l, tracking: tr.state, html: buildPageHtml(l, slug, nearby, { fresh: !isStale(l), isFresh: (n) => !isStale(n), tracking: tr.block }) };
  });
  if (trackingErrors.length) {
    for (const e of trackingErrors) console.error('  ✗ TRACKING-REJECT', e);
    console.error(`FAIL-CLOSED: ${trackingErrors.length} page(s) carry tracking this generator cannot preserve exactly; no page and no sitemap was written.`);
    process.exit(1);
  }

  const today = new Date(BUILD_MS).toISOString().split('T')[0];
  const sitemapUrls = [];
  fs.mkdirSync(HOMES_DIR, { recursive: true });
  for (const { slug, l, html, tracking } of out) {
    const dir = path.join(HOMES_DIR, slug);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'index.html'), html, 'utf8');

    const url = `${BASE_URL}/homes/${slug}/`;
    // DGP-P0-R1B sitemap-eligibility: never advertise placeholder/mock listings.
    // A listing enters the sitemap ONLY with real photo provenance (no stock/placeholder
    // media), a real MLS number, no broker containment, and a record IDX confirmed
    // within STALE_DAYS. Rejections are logged with reason codes.
    const _photos = (l.photos || []).filter(p => typeof p === 'string' && p.startsWith('http') && !/unsplash|placeholder/i.test(p));
    let sm = 'SITEMAP_INCLUDED';
    if (_photos.length === 0) { sm = 'SITEMAP_REJECT_PLACEHOLDER_LISTING'; console.log('  ✗ SITEMAP-REJECT PLACEHOLDER_LISTING (no real media):', slug); }
    else if (!l.mlsNumber) { sm = 'SITEMAP_REJECT_NO_PROVENANCE'; console.log('  ✗ SITEMAP-REJECT NO_PROVENANCE (no MLS id):', slug); }
    else if (SITEMAP_DENYLIST.has(url.replace(/\/$/, ''))) { sm = 'SITEMAP_REJECT_BROKER_DENYLIST'; console.log('  ✗ SITEMAP-REJECT BROKER_DENYLIST (contained, needs broker release):', slug); }
    else if (isStale(l)) { sm = 'SITEMAP_REJECT_STALE_RECORD'; console.log(`  ✗ SITEMAP-REJECT STALE_RECORD (${ageDays(l)}d unconfirmed by IDX):`, slug); }
    else sitemapUrls.push(url);
    decisions.set(l, { page: isStale(l) ? 'PAGE_STALE_NOT_CONFIRMED_NOTICE' : 'PAGE_FRESH', sitemap: sm, rule: fr.get(l).rule });
    console.log(`  ✓ ${url} (${listingKind(l)}, ${l.status}, IDX feed as of ${feedDate(l)}, ${isStale(l) ? 'stale' : 'fresh'}, tracking: ${tracking})`);
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

  // One line per feed record, keyed by MLS number only (no address).
  for (const l of listings) {
    const d = decisions.get(l) || { page: 'UNDECIDED', sitemap: '-', rule: '-' };
    const f = fr.get(l);
    console.log(`DECISION mls=${l.mlsNumber} page=${d.page} sitemap=${d.sitemap} lastSync=${l.lastSync} basis=own_lastSync ageDays=${f.ageDays} rule=${d.rule} build=${new Date(BUILD_MS).toISOString()}`);
  }

  console.log(`\n✅ Generated ${out.length} pages; ${sitemapUrls.length} in sitemap-listings.xml (lastmod ${today})`);
}

// ── Entry point / module surface ─────────────────────────────────────────────
// Running the file builds pages. Requiring it exposes the loader, the slug rule and the
// freshness rule so a checker can ask which pages SHOULD exist without reimplementing them.
if (require.main === module) {
  main();
}

module.exports = { slugify, addressSlug, loadListings, HOMES_DIR, LISTINGS_JSON, STALE_DAYS, parseLastSync, freshness, preferRecord, listingKind };
