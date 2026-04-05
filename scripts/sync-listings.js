#!/usr/bin/env node
/**
 * Gadura Real Estate — MLS / Zillow / Homes.com Sync
 * ====================================================
 * This script is the engine behind the automated listing system.
 *
 * Flow:
 *   1. Fetch Zillow profile pages for Vinod, Gaurav + Nitin (their listings/sold tab)
 *   2. Fetch homes.com profile pages for agents who have one
 *   3. Merge, deduplicate, and compare against current listings.json
 *   4. If anything changed → update listings.json + trigger Netlify rebuild
 *
 * Run manually:  node scripts/sync-listings.js
 * Scheduled:     GitHub Actions (.github/workflows/sync-listings.yml) — every 4 hours
 * Webhook:       POST https://api.netlify.com/build_hooks/YOUR_HOOK_ID
 */

const https = require('https');
const http  = require('http');
const fs    = require('fs');
const path  = require('path');

// ─── Config ──────────────────────────────────────────────────────────────────
const CONFIG = {
  listingsFile: path.join(__dirname, '..', 'data', 'listings.json'),
  netlifyBuildHook: process.env.NETLIFY_BUILD_HOOK || '',
  agents: [
    {
      name: 'Nitin Gadura',
      zillow: 'https://www.zillow.com/profile/NitinGadura106',
      homes:  'https://www.homes.com/real-estate-agents/nitin-gadura/9t6kfc5/',
    },
    {
      name: 'Gaurav Bhardwaj',
      zillow: 'https://www.zillow.com/profile/Gaurav2018',
      homes:  null,
    },
    {
      name: 'Vinod Gadura',
      zillow: 'https://www.zillow.com/profile/vinodgadura',
      homes:  null,
    },
  ],
};

// ─── HTTP helpers ─────────────────────────────────────────────────────────────
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
  'Cache-Control': 'no-cache',
};

function fetchURL(url, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, { headers: HEADERS }, (res) => {
      // Follow redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchURL(res.headers.location, timeoutMs).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.setTimeout(timeoutMs, () => { req.destroy(); reject(new Error('timeout: ' + url)); });
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Zillow parser ────────────────────────────────────────────────────────────
function parseZillowProfile(html) {
  const listings = [];

  // Zillow embeds listing data in __NEXT_DATA__ JSON
  const nextDataMatch = html.match(/<script id="__NEXT_DATA__" type="application\/json">([\s\S]*?)<\/script>/);
  if (nextDataMatch) {
    try {
      const nextData = JSON.parse(nextDataMatch[1]);
      // Walk the tree looking for listing arrays
      const str = JSON.stringify(nextData);

      // Extract property objects with price + address
      const priceAddressRx = /"price":(\d+).*?"streetAddress":"([^"]+)".*?"city":"([^"]+)".*?"state":"([^"]+)".*?"zipcode":"([^"]+)"/g;
      let m;
      while ((m = priceAddressRx.exec(str)) !== null) {
        const price = parseInt(m[1]);
        if (price < 100000) continue; // filter out noise
        listings.push({
          price,
          address: m[2],
          city: m[3],
          state: m[4],
          zip: m[5],
          source: 'zillow',
        });
      }
    } catch(e) {
      // fall through to regex approach
    }
  }

  // Regex fallback — parse Open Graph / meta tags
  const ogTitle = html.match(/<meta property="og:title" content="([^"]+)"/);
  if (ogTitle) {
    const priceMatch = ogTitle[1].match(/\$[\d,]+/);
    if (priceMatch) {
      const addrMatch = ogTitle[1].match(/at (.+?) in/i);
      listings.push({
        price: parseInt(priceMatch[0].replace(/[$,]/g, '')),
        address: addrMatch ? addrMatch[1] : '',
        source: 'zillow-meta',
      });
    }
  }

  // Extract listing URLs from href
  const listingUrls = [...new Set(
    [...html.matchAll(/href="(\/homedetails\/[^"]+)"/g)].map(m => 'https://www.zillow.com' + m[1])
  )];

  // Extract photo URLs
  const photoUrls = [...new Set(
    [...html.matchAll(/https:\/\/photos\.zillowstatic\.com\/fp\/[a-f0-9]+-[^"'\s]+\.jpg/g)].map(m => m[0])
  )].filter(u => u.includes('-p_') || u.includes('-h_'));

  // Extract prices
  const prices = [...html.matchAll(/\$[\d,]{5,}/g)].map(m => parseInt(m[0].replace(/[$,]/g, ''))).filter(p => p > 100000);

  return { listings, listingUrls, photoUrls, prices };
}

// ─── Homes.com parser ─────────────────────────────────────────────────────────
function parseHomesComProfile(html) {
  const listings = [];

  // Extract property links
  const propertyLinks = [...new Set(
    [...html.matchAll(/href="(\/property\/[^"?]+)"/g)].map(m => 'https://www.homes.com' + m[1])
  )];

  // Extract primary photos
  const photoRx = /https:\/\/images\.homes\.com\/listings\/\d+\/[^"'\s]+primaryphoto[^"'\s]*\.jpg/g;
  const photos = [...new Set([...html.matchAll(photoRx)].map(m => m[0]))];

  // Extract address slugs and map to proper addresses
  propertyLinks.forEach((url, i) => {
    const slugMatch = url.match(/\/property\/([^/]+)\//);
    if (!slugMatch) return;
    const slug = slugMatch[1];
    // Convert slug: "10773-129th-st-south-richmond-hill-ny" → address parts
    const parts = slug.split('-');
    const stateIdx = parts.lastIndexOf('ny') !== -1 ? parts.lastIndexOf('ny') : parts.length - 1;
    const cityParts = [];
    let streetEnd = stateIdx - 1;
    // heuristic: city usually 2-3 words before state abbreviation
    for (let j = Math.max(2, streetEnd - 2); j <= streetEnd; j++) cityParts.push(parts[j]);
    const rawAddress = parts.slice(0, Math.max(2, streetEnd - 2)).join('-').toUpperCase();

    listings.push({
      address: rawAddress,
      city: cityParts.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
      state: 'NY',
      url,
      photo: photos[i] || '',
      source: 'homes.com',
    });
  });

  // Also grab status + price pairs from page text
  const forSaleRx = /For Sale \$([\d,]+)/g;
  const soldRx    = /Sold \$([\d,]+)/g;
  const forSalePrices = [...html.matchAll(forSaleRx)].map(m => ({ status: 'For Sale', price: parseInt(m[1].replace(/,/g,'')) }));
  const soldPrices    = [...html.matchAll(soldRx)].map(m => ({ status: 'Sold', price: parseInt(m[1].replace(/,/g,'')) }));
  const allPrices = [...forSalePrices, ...soldPrices];

  // Merge price into listing by index
  listings.forEach((l, i) => {
    if (allPrices[i]) {
      l.price = allPrices[i].price;
      l.status = allPrices[i].status;
    }
  });

  return { listings, photos };
}

// ─── Fetch individual listing page to get more details ────────────────────────
async function enrichFromHomesListing(url) {
  try {
    const { status, body } = await fetchURL(url);
    if (status !== 200) return {};

    const bedsMatch   = body.match(/(\d+)\s*(?:bed|bd)/i);
    const bathsMatch  = body.match(/([\d.]+)\s*(?:bath|ba)/i);
    const sqftMatch   = body.match(/([\d,]+)\s*(?:sq\s*ft|sqft)/i);
    const priceMatch  = body.match(/\$\s*([\d,]+)/);
    const typeMatch   = body.match(/(?:single|multi|2-family|1-family|condo|coop|townhouse)/i);

    // Primary photo
    const photoRx = /https:\/\/images\.homes\.com\/listings\/\d+\/[^"'\s]+primaryphoto[^"'\s]*\.jpg/;
    const photoMatch = body.match(photoRx);

    // All photos
    const allPhotosRx = /https:\/\/images\.homes\.com\/listings\/\d+\/[^"'\s]+(?:photo|building)[^"'\s]*\.jpg/g;
    const allPhotos = [...new Set([...body.matchAll(allPhotosRx)].map(m => m[0]))].slice(0, 8);

    return {
      beds:   bedsMatch  ? parseInt(bedsMatch[1])            : null,
      baths:  bathsMatch ? parseFloat(bathsMatch[1])         : null,
      sqft:   sqftMatch  ? parseInt(sqftMatch[1].replace(/,/g,'')) : null,
      price:  priceMatch ? parseInt(priceMatch[1].replace(/,/g,'')) : null,
      type:   typeMatch  ? typeMatch[0]                      : null,
      photo:  photoMatch ? photoMatch[0]                     : (allPhotos[0] || ''),
      photos: allPhotos,
    };
  } catch(e) {
    return {};
  }
}

// ─── Main sync ────────────────────────────────────────────────────────────────
async function syncListings() {
  console.log('\n[sync-listings] ══════════════════════════════════════');
  console.log('[sync-listings] Starting at', new Date().toISOString());

  const current = JSON.parse(fs.readFileSync(CONFIG.listingsFile, 'utf8'));
  const allKnownUrls = new Set([
    ...current.activeListings.map(l => l.url),
    ...current.soldListings.map(l => l.url),
  ]);

  const newActive = [];
  const newSold   = [];

  // ── Pull from each agent's homes.com profile ──
  for (const agent of CONFIG.agents) {
    if (!agent.homes) continue;
    console.log(`\n[sync-listings] Checking homes.com for ${agent.name}…`);

    try {
      const { status, body } = await fetchURL(agent.homes);
      console.log(`[sync-listings]   Status: ${status}`);

      if (status === 200) {
        const { listings } = parseHomesComProfile(body);
        console.log(`[sync-listings]   Found ${listings.length} listing URLs`);

        for (const listing of listings.slice(0, 20)) {
          if (!listing.url || allKnownUrls.has(listing.url)) continue;

          console.log(`[sync-listings]   NEW → enriching ${listing.url}`);
          await sleep(1500); // polite delay
          const details = await enrichFromHomesListing(listing.url);

          const enriched = {
            id: 'listing-' + Date.now() + '-' + Math.random().toString(36).slice(2,6),
            address: details.address || listing.address,
            city:    listing.city    || 'Queens',
            state:   'NY',
            zip:     listing.zip     || '',
            price:   details.price   || listing.price || 0,
            beds:    details.beds    || null,
            baths:   details.baths   || null,
            sqft:    details.sqft    || null,
            type:    details.type    || 'Residential',
            status:  listing.status  || 'For Sale',
            soldDate: listing.status === 'Sold' ? new Date().toISOString().slice(0,7) : '',
            photo:   details.photo   || listing.photo || '',
            photos:  details.photos  || (listing.photo ? [listing.photo] : []),
            url:     listing.url,
            description: '',
            source:  'homes.com',
            mlsNumber: '',
            agentName: agent.name,
            syncedAt: new Date().toISOString(),
          };

          allKnownUrls.add(listing.url);

          if (enriched.status === 'For Sale') {
            newActive.push(enriched);
          } else {
            newSold.push(enriched);
          }
        }
      }
    } catch(e) {
      console.error(`[sync-listings]   homes.com error for ${agent.name}:`, e.message);
    }

    await sleep(2000);
  }

  // ── Pull from each agent's Zillow profile ──
  for (const agent of CONFIG.agents) {
    console.log(`\n[sync-listings] Checking Zillow for ${agent.name}…`);

    try {
      const { status, body } = await fetchURL(agent.zillow);
      console.log(`[sync-listings]   Status: ${status}`);

      if (status === 200) {
        const { listingUrls, photoUrls, prices } = parseZillowProfile(body);
        console.log(`[sync-listings]   Found ${listingUrls.length} listing URLs on Zillow`);

        listingUrls.slice(0, 10).forEach((url, i) => {
          if (allKnownUrls.has(url)) return;
          const price = prices[i] || 0;
          const photo = photoUrls[i] || '';

          const listing = {
            id: 'zillow-' + Date.now() + '-' + i,
            address: '',
            city: 'Queens',
            state: 'NY',
            zip: '',
            price,
            beds: null, baths: null, sqft: null,
            type: 'Residential',
            status: 'For Sale',
            soldDate: '',
            photo,
            photos: photo ? [photo] : [],
            url,
            description: '',
            source: 'zillow',
            mlsNumber: '',
            agentName: agent.name,
            syncedAt: new Date().toISOString(),
          };
          allKnownUrls.add(url);
          newActive.push(listing);
        });
      } else {
        console.log(`[sync-listings]   Zillow blocked (${status}) — will retry next cycle`);
      }
    } catch(e) {
      console.error(`[sync-listings]   Zillow error:`, e.message);
    }

    await sleep(3000);
  }

  // ── Write updated file if anything changed ──
  if (newActive.length || newSold.length) {
    console.log(`\n[sync-listings] ✅ Found ${newActive.length} new active + ${newSold.length} new sold listings`);

    current.activeListings = [...newActive, ...current.activeListings];
    current.soldListings   = [...newSold, ...current.soldListings];
    current.lastUpdated    = new Date().toISOString().split('T')[0];

    fs.writeFileSync(CONFIG.listingsFile, JSON.stringify(current, null, 2));
    console.log('[sync-listings] listings.json updated');

    // Trigger Netlify rebuild via build hook
    if (CONFIG.netlifyBuildHook) {
      await triggerNetlifyBuild(CONFIG.netlifyBuildHook);
    } else {
      console.log('[sync-listings] No NETLIFY_BUILD_HOOK set — skipping webhook trigger');
      console.log('[sync-listings] Set it as a GitHub Actions secret: NETLIFY_BUILD_HOOK');
    }
  } else {
    console.log('\n[sync-listings] No new listings found — nothing to update');
  }

  console.log('[sync-listings] Done at', new Date().toISOString());
  return { newActive: newActive.length, newSold: newSold.length };
}

// ─── Trigger Netlify rebuild via build hook ───────────────────────────────────
function triggerNetlifyBuild(hookUrl) {
  return new Promise((resolve, reject) => {
    const url = new URL(hookUrl);
    const req = https.request({
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: { 'Content-Length': 0 },
    }, (res) => {
      console.log('[sync-listings] Netlify build triggered — HTTP', res.statusCode);
      resolve();
    });
    req.on('error', (e) => {
      console.error('[sync-listings] Build hook error:', e.message);
      resolve(); // don't fail the whole job
    });
    req.end();
  });
}

syncListings().catch(console.error);
