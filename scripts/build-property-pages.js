#!/usr/bin/env node
/**
  * build-property-pages.js  v2
  * Reads data/listings.json and generates SEO-ready individual HTML property pages at:
  *   homes/{address-slug}/index.html
  *
  * Each page includes:
  *   - Professional design matching main site (nav, footer, colors)
  *   - Full address as H1, price, beds/baths/sqft stats bar
  *   - Photo gallery (all listing photos)
  *   - Property description
  *   - Key facts grid (type, status, MLS #, ZIP, lot size, year built)
  *   - Google Maps embed showing property location
  *   - "Schedule a Showing" contact form sidebar
  *   - IDX Broker nearby listings iframe
  *   - JSON-LD: RealEstateListing + PostalAddress + BreadcrumbList
  *   - OpenGraph tags for social sharing
  *   - Canonical URL
  *   - Correct sitemap dates (today)
  *
  * Run: node scripts/build-property-pages.js
  */

'use strict';

const fs   = require('fs');
const path = require('path');

// ── Paths ──────────────────────────────────────────────────────────────────
const ROOT          = path.resolve(__dirname, '..');
const LISTINGS_JSON = path.join(ROOT, 'data', 'listings.json');
const HOMES_DIR     = path.join(ROOT, 'homes');
const SITEMAP_OUT   = path.join(ROOT, 'sitemap-listings.xml');
const BASE_URL      = 'https://gadurarealestate.com';

// ── Helpers ────────────────────────────────────────────────────────────────
function slugify(str) {
   return (str || '')
     .toLowerCase()
     .replace(/[^a-z0-9]+/g, '-')
     .replace(/^-+|-+$/g, '');
}

function addressSlug(listing) {
   const parts = [
        listing.address,
        listing.city,
        listing.state,
        listing.zip
      ].filter(Boolean);
   return slugify(parts.join(' '));
}

function formatPrice(price) {
   if (!price) return 'Contact for Price';
   return '$' + Number(price).toLocaleString('en-US');
}

function formatNumber(n) {
   if (!n) return '';
   return Number(n).toLocaleString('en-US');
}

function escHtml(s) {
   return String(s || '')
     .replace(/&/g, '&amp;')
     .replace(/</g, '&lt;')
     .replace(/>/g, '&gt;')
     .replace(/"/g, '&quot;');
}

function bedBathLabel(listing) {
   const parts = [];
   if (listing.beds)  parts.push(listing.beds + ' bed');
   if (listing.baths) parts.push(listing.baths + ' bath');
   if (listing.sqft && listing.sqft > 1)  parts.push(formatNumber(listing.sqft) + ' sqft');
   return parts.join(' · ');
}

function getPhotos(listing) {
   if (!listing.image) return [];
   const imgs = [];
   // listing.image can be an object keyed by index or an array
  const src = listing.image;
   const keys = Object.keys(src).sort((a, b) => Number(a) - Number(b));
   for (const k of keys) {
        const entry = src[k];
        if (entry && entry.url) imgs.push(entry.url);
   }
   return imgs;
}

function getIdxSlug(listing) {
   // IDX Broker detail URL format: /idx/details/listing/c056/{mlsNumber}/{address-slug}
  const addrPart = slugify(
       [listing.address, listing.city, listing.state, listing.zip].filter(Boolean).join(' ')
     );
   return addrPart;
}

// ── HTML template ──────────────────────────────────────────────────────────
function buildPageHtml(listing, slug) {
   const fullAddress  = [listing.address, listing.city, listing.state, listing.zip].filter(Boolean).join(', ');
   const shortAddress = listing.address + (listing.city ? ', ' + listing.city : '');
   const pageUrl      = BASE_URL + '/homes/' + slug + '/';
   const priceStr     = formatPrice(listing.price);
   const bbl          = bedBathLabel(listing);
   const photos       = getPhotos(listing);
   const heroPhoto    = photos[0] || '';
   const mlsNum       = listing.mlsNumber || '';
   const idxSlug      = getIdxSlug(listing);
   const idxDetailUrl = `https://homes.gadurarealestate.com/idx/details/listing/c056/${mlsNum}/${idxSlug}`;
   const idxNearby    = `https://homes.gadurarealestate.com/idx/map/mapsearch?city=${encodeURIComponent(listing.city || 'Richmond Hill')}`;
   const todayDate    = new Date().toISOString().split('T')[0];

  // Status badge color
  const statusColor  = listing.status === 'Active' ? '#16a34a' : '#b91c1c';
   const statusLabel  = listing.status || 'Active';

  // Meta description
  const metaDesc = listing.price
     ? `${shortAddress} is a ${listing.type || 'property'} listed for sale at ${priceStr}. ${bbl ? 'This is a ' + bbl + ' property.' : ''} View photos, details, and contact Gadura Real Estate.`
       : `${shortAddress} — ${listing.type || 'property'} listed with Gadura Real Estate. View photos and details or contact us for pricing.`;

  // Key facts
  const facts = [
   { label: 'Status',     value: statusLabel },
   { label: 'Type',       value: listing.type || '' },
   { label: 'Sub-Type',   value: listing.subType || '' },
   { label: 'Bedrooms',   value: listing.beds || '' },
   { label: 'Bathrooms',  value: listing.baths || '' },
   { label: 'Sq Ft',      value: listing.sqft && listing.sqft > 1 ? formatNumber(listing.sqft) : '' },
   { label: 'ZIP Code',   value: listing.zip || '' },
   { label: 'MLS #',      value: mlsNum },
   { label: 'City',       value: listing.city || '' },
     ].filter(f => f.value);

  // Photo gallery HTML
  const galleryHtml = photos.length > 0 ? `
      <div class="gre-gallery">
            <div class="gre-hero-photo">
                    <img src="${escHtml(heroPhoto)}" alt="${escHtml(fullAddress)}" loading="eager" width="900" height="600">
                            <span class="gre-status-badge" style="background:${statusColor}">${escHtml(statusLabel)}</span>
                                  </div>
                                        ${photos.length > 1 ? `
                                              <div class="gre-photo-strip">
                                                      ${photos.slice(1, 5).map((p, i) => `<img src="${escHtml(p)}" alt="${escHtml(fullAddress)} photo ${i+2}" loading="lazy">`).join('')}
                                                            </div>` : ''}
                                                                </div>` : '';

  // Key facts grid
  const factsHtml = facts.map(f => `
        <div class="gre-fact">
                <span class="gre-fact-label">${escHtml(f.label)}</span>
                        <span class="gre-fact-value">${escHtml(String(f.value))}</span>
                              </div>`).join('');

  // JSON-LD
  const jsonLd = {
       "@context": "https://schema.org",
       "@graph": [
        {
                 "@type": "RealEstateListing",
                 "name": fullAddress,
                 "url": pageUrl,
                 "description": listing.description || metaDesc,
                 "image": heroPhoto || undefined,
                 "datePosted": todayDate,
                 "offers": listing.price ? {
                            "@type": "Offer",
                            "price": listing.price,
                            "priceCurrency": "USD",
                            "availability": "https://schema.org/InStock"
                 } : undefined,
                 "address": {
                            "@type": "PostalAddress",
                            "streetAddress": listing.address,
                            "addressLocality": listing.city,
                            "addressRegion": "NY",
                            "postalCode": listing.zip,
                            "addressCountry": "US"
                 },
                 "numberOfRooms": listing.beds || undefined,
                 "floorSize": listing.sqft && listing.sqft > 1 ? {
                            "@type": "QuantitativeValue",
                            "value": listing.sqft,
                            "unitCode": "FTK"
                 } : undefined
        },
        {
                 "@type": "BreadcrumbList",
                 "itemListElement": [
                  { "@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/" },
                  { "@type": "ListItem", "position": 2, "name": "Listings", "item": BASE_URL + "/listings/" },
                  { "@type": "ListItem", "position": 3, "name": shortAddress, "item": pageUrl }
                          ]
        }
            ]
  };

  return `<!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${escHtml(shortAddress)} | ${escHtml(priceStr)} | Gadura Real Estate</title>
          <meta name="description" content="${escHtml(metaDesc)}">
            <link rel="canonical" href="${escHtml(pageUrl)}">
              <meta property="og:type" content="website">
                <meta property="og:title" content="${escHtml(shortAddress + ' — ' + priceStr + ' | Gadura Real Estate')}">
                  <meta property="og:description" content="${escHtml(metaDesc)}">
                    ${heroPhoto ? `<meta property="og:image" content="${escHtml(heroPhoto)}">` : ''}
                      <meta property="og:url" content="${escHtml(pageUrl)}">
                        <meta name="twitter:card" content="summary_large_image">
                          <link rel="stylesheet" href="/css/main.css">
                                                           <script type="application/ld+json">${JSON.stringify(jsonLd, null, 0).replace(/"undefined"/g, 'null')}</script>
                                                             <style>
                                                                 /* ── Property Detail Page Styles ────────────────────────── */
                                                                     body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; color: #1a1a1a; background: #fff; }

                                                                         /* Nav */
                                                                             .gre-prop-nav { background: #0a2540; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }
                                                                                 .gre-prop-nav a { color: #fff; text-decoration: none; }
                                                                                     .gre-prop-nav .gre-logo { font-size: 1.1rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
                                                                                         .gre-prop-nav .gre-logo img { height: 36px; width: auto; }
                                                                                             .gre-prop-nav .gre-nav-links { display: flex; gap: 20px; font-size: 0.9rem; }
                                                                                                 .gre-prop-nav .gre-nav-links a:hover { color: #6fcf97; }
                                                                                                     .gre-prop-nav .gre-nav-cta { background: #16a34a; color: #fff; padding: 8px 16px; border-radius: 4px; font-weight: 600; font-size: 0.85rem; }
                                                                                                         .gre-prop-nav .gre-nav-cta:hover { background: #15803d; }
                                                                                                         
                                                                                                             /* Breadcrumb */
                                                                                                                 .gre-breadcrumb { padding: 10px 24px; font-size: 0.82rem; color: #666; background: #f8f9fa; border-bottom: 1px solid #e5e7eb; }
                                                                                                                     .gre-breadcrumb a { color: #0a2540; text-decoration: none; }
                                                                                                                         .gre-breadcrumb a:hover { text-decoration: underline; }
                                                                                                                             .gre-breadcrumb span { margin: 0 6px; }
                                                                                                                             
                                                                                                                                 /* Main layout */
                                                                                                                                     .gre-prop-wrap { max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; display: grid; grid-template-columns: 1fr 320px; gap: 32px; }
                                                                                                                                         @media (max-width: 768px) { .gre-prop-wrap { grid-template-columns: 1fr; } }
                                                                                                                                         
                                                                                                                                             /* Gallery */
                                                                                                                                                 .gre-gallery { margin-bottom: 20px; }
                                                                                                                                                     .gre-hero-photo { position: relative; border-radius: 8px; overflow: hidden; }
                                                                                                                                                         .gre-hero-photo img { width: 100%; height: 420px; object-fit: cover; display: block; }
                                                                                                                                                             @media (max-width: 600px) { .gre-hero-photo img { height: 240px; } }
                                                                                                                                                                 .gre-status-badge { position: absolute; top: 14px; left: 14px; background: #16a34a; color: #fff; font-size: 0.78rem; font-weight: 700; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
                                                                                                                                                                     .gre-photo-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 6px; }
                                                                                                                                                                         .gre-photo-strip img { width: 100%; height: 100px; object-fit: cover; border-radius: 4px; }
                                                                                                                                                                         
                                                                                                                                                                             /* Price & address */
                                                                                                                                                                                 .gre-prop-price { font-size: 2rem; font-weight: 800; color: #0a2540; margin: 0 0 4px; }
                                                                                                                                                                                     .gre-prop-address { font-size: 1.05rem; color: #444; margin: 0 0 16px; }
                                                                                                                                                                                     
                                                                                                                                                                                         /* Stats bar */
                                                                                                                                                                                             .gre-stats-bar { display: flex; gap: 0; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; margin-bottom: 20px; }
                       .gre-stat { flex: 1; text-align: center; padding: 12px 8px; border-right: 1px solid #e5e7eb; }
                           .gre-stat:last-child { border-right: none; }
                               .gre-stat-val { font-size: 1.4rem; font-weight: 700; color: #0a2540; display: block; }
                                   .gre-stat-lbl { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: #888; }

                                       /* Description */
                                           .gre-section { margin-bottom: 28px; }
                                               .gre-section h2 { font-size: 1.1rem; font-weight: 700; color: #0a2540; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 14px; }
                                                   .gre-desc { font-size: 0.95rem; line-height: 1.65; color: #333; }

                                                       /* Key facts */
                                                           .gre-facts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
                                                               .gre-fact { background: #f8f9fa; border-radius: 6px; padding: 10px 14px; }
                                                                   .gre-fact-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: #888; display: block; margin-bottom: 2px; }
                                                                       .gre-fact-value { font-size: 0.95rem; font-weight: 600; color: #1a1a1a; }

                                                                           /* Map */
                                                                               .gre-map { border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; }
                                                                                   .gre-map iframe { width: 100%; height: 280px; border: none; display: block; }

                                                                                       /* Nearby listings */
                                                                                           .gre-nearby { margin-top: 32px; }
                                                                                               .gre-nearby h2 { font-size: 1.1rem; font-weight: 700; color: #0a2540; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 14px; }
                                                                                                   .gre-nearby-frame { width: 100%; height: 520px; border: 1px solid #e5e7eb; border-radius: 8px; display: block; }

                                                                                                       /* Sidebar */
                                                                                                           .gre-sidebar { }
                                                                                                               .gre-contact-card { background: #0a2540; color: #fff; border-radius: 10px; padding: 22px 20px; margin-bottom: 20px; position: sticky; top: 20px; }
                                                                                                                   .gre-contact-card h3 { margin: 0 0 6px; font-size: 1rem; font-weight: 700; }
                                                                                                                       .gre-contact-card p { margin: 0 0 16px; font-size: 0.85rem; color: #b0c4d8; }
                                                                                                                           .gre-contact-card input, .gre-contact-card textarea {
                                                                                                                                 width: 100%; box-sizing: border-box; padding: 9px 12px; border: none; border-radius: 5px;
                                                                                                                                       font-size: 0.9rem; margin-bottom: 10px; background: rgba(255,255,255,0.1);
                                                                                                                                             color: #fff; placeholder-color: #aaa;
                                                                                                                                                 }
                                                                                                                                                     .gre-contact-card input::placeholder, .gre-contact-card textarea::placeholder { color: #8ca0b8; }
                                                                                                                                                         .gre-contact-card textarea { height: 80px; resize: vertical; }
                                                                                                                                                             .gre-btn-schedule {
                                                                                                                                                                   display: block; width: 100%; background: #16a34a; color: #fff; text-align: center;
                                                                                                                                                                         padding: 12px; border-radius: 6px; font-weight: 700; font-size: 0.95rem;
                                                                                                                                                                               text-decoration: none; border: none; cursor: pointer; box-sizing: border-box;
                                                                                                                                                                                   }
                                                                                                                                                                                       .gre-btn-schedule:hover { background: #15803d; }
                                                                                                                                                                                           .gre-phone-card { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 16px; text-align: center; }
                                                                                                                                                                                               .gre-phone-card a { color: #15803d; font-size: 1.1rem; font-weight: 700; text-decoration: none; }
                                                                                                                                                                                                   .gre-phone-card p { margin: 4px 0 0; font-size: 0.8rem; color: #666; }
                                                                                                                                                                                                   
                                                                                                                                                                                                       /* IDX attribution */
                                                                                                                                                                                                           .gre-idx-attr { font-size: 0.72rem; color: #888; line-height: 1.5; margin-top: 16px; padding-top: 14px; border-top: 1px solid #e5e7eb; }
                                                                                                                                                                                                           
                                                                                                                                                                                                               /* Footer */
                                                                                                                                                                                                                   .gre-prop-footer { background: #0a2540; color: #8ca0b8; font-size: 0.8rem; padding: 28px 24px; text-align: center; line-height: 1.7; }
                                                                                                                                                                                                                       .gre-prop-footer a { color: #6fcf97; text-decoration: none; }
                                                                                                                                                                                                                           .gre-prop-footer .gre-footer-links { display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; margin-bottom: 12px; }
                                                                                                                                                                                                                             </style>
                                                                                                                                                                                                                             </head>
                                                                                                                                                                                                                             <body>
                                                                                                                                                                                                                             
                                                                                                                                                                                                                             <!-- Navigation -->
                                                                                                                                                                                                                             <header class="gre-prop-nav">
                                                                                                                                                                                                                               <a href="/" class="gre-logo">
                                                                                                                                                                                                                                   <img src="/images/gre-logo.png" alt="Gadura Real Estate" onerror="this.style.display='none'">
                                                                                                                                                                                                                                       <span>Gadura Real Estate</span>
                                                                                                                                                                                                                                         </a>
                                                                                                                                                                                                                                           <nav class="gre-nav-links" aria-label="Main">
                                                                                                                                                                                                                                               <a href="/">Home</a>
                                                                                                                                                                                                                                                   <a href="/listings/">MLS Search</a>
                                                                                                                                                                                                                                                       <a href="/neighborhoods/">Neighborhoods</a>
                                                                                                                                                                                                                                                           <a href="/sell.html">Sell</a>
                                                                                                                                                                                                                                                               <a href="/meet-the-agents.html">Agents</a>
                                                                                                                                                                                                                                                                   <a href="/contact.html">Contact</a>
                                                                                                                                                                                                                                                                     </nav>
                                                                                                                                                                                                                                                                       <a href="tel:+17188500010" class="gre-nav-cta">(718) 850-0010</a>
                                                                                                                                                                                                                                                                       </header>
                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                       <!-- Breadcrumb -->
                                                                                                                                                                                                                                                                       <nav class="gre-breadcrumb" aria-label="Breadcrumb">
                                                                                                                                                                                                                                                                         <a href="/">Home</a><span>›</span>
                                                                                                                                                                                                                                                                           <a href="/listings/">Listings</a><span>›</span>
                                                                                                                                                                                                                                                                             <span>${escHtml(shortAddress)}</span>
                                                                                                                                                                                                                                                                             </nav>
                                                                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                                             <!-- Main Content -->
                                                                                                                                                                                                                                                                             <div class="gre-prop-wrap">
                                                                                                                                                                                                                                                                               <main id="main-content">
                                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                   <!-- Gallery -->
                                                                                                                                                                                                                                                                                       ${galleryHtml}
                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                           <!-- Price & Address -->
                                                                                                                                                                                                                                                                                               <p class="gre-prop-price">${escHtml(priceStr)}</p>
                                                                                                                                                                                                                                                                                                   <p class="gre-prop-address">${escHtml(fullAddress)}</p>
                                                                                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                                                                       <!-- Stats Bar -->
                                                                                                                                                                                                                                                                                                           <div class="gre-stats-bar">
                                                                                                                                                                                                                                                                                                                 ${listing.beds ? `<div class="gre-stat"><span class="gre-stat-val">${escHtml(String(listing.beds))}</span><span class="gre-stat-lbl">Bedrooms</span></div>` : ''}
                                                                                                                                                                                                                                                                                                                       ${listing.baths ? `<div class="gre-stat"><span class="gre-stat-val">${escHtml(String(listing.baths))}</span><span class="gre-stat-lbl">Bathrooms</span></div>` : ''}
                                                                                                                                                                                                                                                                                                                             ${listing.sqft && listing.sqft > 1 ? `<div class="gre-stat"><span class="gre-stat-val">${escHtml(formatNumber(listing.sqft))}</span><span class="gre-stat-lbl">Sq Ft</span></div>` : ''}
                                                                                                                                                                                                                                                                                                                                   ${listing.type ? `<div class="gre-stat"><span class="gre-stat-val">${escHtml(listing.type)}</span><span class="gre-stat-lbl">Type</span></div>` : ''}
                                                                                                                                                                                                                                                                                                                                       </div>
                                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                           <!-- Description -->
                                                                                                                                                                                                                                                                                                                                               ${listing.description ? `
                                                                                                                                                                                                                                                                                                                                                   <section class="gre-section">
                                                                                                                                                                                                                                                                                                                                                         <h2>About This Property</h2>
                                                                                                                                                                                                                                                                                                                                                               <p class="gre-desc">${escHtml(listing.description)}</p>
                                                                                                                                                                                                                                                                                                                                                                   </section>` : ''}
                                                                                                                                                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                                                                                                                                       <!-- Key Facts -->
                                                                                                                                                                                                                                                                                                                                                                           <section class="gre-section">
                                                                                                                                                                                                                                                                                                                                                                                 <h2>Property Details</h2>
                                                                                                                                                                                                                                                                                                                                                                                       <div class="gre-facts-grid">
                                                                                                                                                                                                                                                                                                                                                                                               ${factsHtml}
                                                                                                                                                                                                                                                                                                                                                                                                     </div>
                                                                                                                                                                                                                                                                                                                                                                                                         </section>
                                                                                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                                                                                             <!-- Map -->
                                                                                                                                                                                                                                                                                                                                                                                                                 <section class="gre-section">
                                                                                                                                                                                                                                                                                                                                                                                                                       <h2>Location</h2>
                                                                                                                                                                                                                                                                                                                                                                                                                             <div class="gre-map">
                                                                                                                                                                                                                                                                                                                                                                                                                                     <iframe
                                                                                                                                                                                                                                                                                                                                                                                                                                               title="Map of ${escHtml(fullAddress)}"
                                                                                                                                                                                                                                                                                                                                                                                                                                                         src="https://www.google.com/maps?q=${encodeURIComponent(fullAddress)}&output=embed"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                   loading="lazy"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                             referrerpolicy="no-referrer-when-downgrade"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       allowfullscreen>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               </iframe>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         </section>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             <!-- Nearby Listings -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 <section class="gre-nearby">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       <h2>More Homes Near ${escHtml(listing.city || 'This Area')}</h2>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             <iframe
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     class="gre-nearby-frame"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             src="${escHtml(idxNearby)}"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     title="Homes for sale near ${escHtml(fullAddress)}"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             loading="lazy">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   </iframe>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       </section>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           <!-- IDX Attribution -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               <p class="gre-idx-attr">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     Listing data displayed on this page comes from the OneKey&reg; MLS Internet Data Exchange (IDX) program.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           Information is deemed reliable but not guaranteed. &copy; ${new Date().getFullYear()} OneKey&reg; MLS.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 All rights reserved. <a href="/idx-policy.html">IDX &amp; VOW Policy</a>.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     </p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       </main><!-- /main -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         <!-- Sidebar -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           <aside class="gre-sidebar" aria-label="Contact agent">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               <div class="gre-contact-card">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     <h3>Interested in This Home?</h3>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           <p>Contact our team — we respond within minutes.</p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 <form action="/contact.html" method="get">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         <input type="hidden" name="property" value="${escHtml(fullAddress)}">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 <input type="text" name="name" placeholder="Your Name" required>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         <input type="tel" name="phone" placeholder="Phone Number">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 <input type="email" name="email" placeholder="Email Address" required>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         <textarea name="message" placeholder="Message (optional)">I'm interested in ${escHtml(shortAddress)}.</textarea>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 <button type="submit" class="gre-btn-schedule">Request Info →</button>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       </form>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               <div class="gre-phone-card">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     <a href="tel:+17188500010">(718) 850-0010</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           <p>Call or text us any time</p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   ${heroPhoto ? `
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       <div style="margin-top:16px; text-align:center;">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             <a href="${escHtml(idxDetailUrl)}" target="_blank" rel="noopener"
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      style="display:inline-block; background:#0a2540; color:#fff; padding:10px 18px; border-radius:6px; font-size:0.85rem; text-decoration:none; font-weight:600;">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              View Full IDX Listing →
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        </div>` : ''}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          </aside>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          </div><!-- /gre-prop-wrap -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          <!-- Footer -->
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          <footer class="gre-prop-footer">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            <div class="gre-footer-links">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <a href="/listings/">MLS Search</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    <a href="/sell.html">Sell</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <a href="/neighborhoods/">Neighborhoods</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            <a href="/meet-the-agents.html">Agents</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <a href="/contact.html">Contact</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    <a href="/idx-policy.html">IDX Policy</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <a href="/privacy-policy.html">Privacy</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            <a href="/fair-housing.html">Fair Housing</a>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>Gadura Real Estate, LLC &mdash; 106-09 101st Ave, Ozone Park, NY 11416</p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  <p>Licensed Real Estate Broker, State of New York &bull; <a href="tel:+17188500010">(718) 850-0010</a></p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    <p>&copy; ${new Date().getFullYear()} Gadura Real Estate, LLC. All rights reserved.</p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </footer>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </body>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </html>`;
}

// ── Main ───────────────────────────────────────────────────────────────────
function main() {
   // Load listings
  if (!fs.existsSync(LISTINGS_JSON)) {
       console.error('listings.json not found:', LISTINGS_JSON);
       process.exit(1);
  }
   const data = JSON.parse(fs.readFileSync(LISTINGS_JSON, 'utf8'));

  // Collect all listings from all arrays
  const allListings = [
       ...(data.activeListings  || []),
       ...(data.areaListings    || []),
       ...(data.queensListings  || []),
     ];

  // Deduplicate by mlsNumber
  const seen = new Set();
   const listings = allListings.filter(l => {
        if (!l.mlsNumber || seen.has(l.mlsNumber)) return false;
        seen.add(l.mlsNumber);
        return true;
   });

  console.log(`Building ${listings.length} property pages…`);

  fs.mkdirSync(HOMES_DIR, { recursive: true });

  const todayDate = new Date().toISOString().split('T')[0];
   const sitemapUrls = [];

  for (const listing of listings) {
       const slug   = addressSlug(listing);
       if (!slug) { console.warn('Skipping listing with no address:', listing.mlsNumber); continue; }

     const dir    = path.join(HOMES_DIR, slug);
       const outFile = path.join(dir, 'index.html');
       const html   = buildPageHtml(listing, slug);

     fs.mkdirSync(dir, { recursive: true });
       fs.writeFileSync(outFile, html, 'utf8');

     const pageUrl = BASE_URL + '/homes/' + slug + '/';
       sitemapUrls.push({ url: pageUrl, date: todayDate });
       console.log('  ✓', pageUrl);
  }

  // Write sitemap-listings.xml with TODAY's date
  const sitemapXml = `<?xml version="1.0" encoding="UTF-8"?>
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${sitemapUrls.map(u => `  <url>
      <loc>${u.url}</loc>
          <lastmod>${u.date}</lastmod>
              <changefreq>daily</changefreq>
                  <priority>0.8</priority>
                    </url>`).join('\n')}
                    </urlset>`;

  fs.writeFileSync(SITEMAP_OUT, sitemapXml, 'utf8');
   console.log(`\n✅ Generated ${sitemapUrls.length} pages + sitemap-listings.xml`);
   console.log(`   Sitemap lastmod: ${todayDate}`);
}

main();
