#!/usr/bin/env node
/**
 * sync-idx.js — IDX Broker API Sync
 * Pulls ALL active MLS listings for Queens, Brooklyn & Long Island
 * via the IDX Broker REST API and writes data/listings.json
 *
 * GitHub Secret required: IDX_BROKER_API_KEY
 * Run: node scripts/sync-reso.js
 */

'use strict';
const https = require('https');
const fs    = require('fs');
const path  = require('path');

// ── Config ────────────────────────────────────────────────────────────────────
const API_KEY    = process.env.IDX_BROKER_API_KEY;
const API_BASE   = 'api.idxbroker.com';
const API_VER    = '1.8.0';
const OUT_FILE   = path.join(__dirname, '..', 'data', 'listings.json');

// Agent IDs — used to flag "our own" listings as activeListings
const OUR_AGENTS = [
  process.env.AGENT_ID_NITIN  || '',
  process.env.AGENT_ID_VINOD  || '',
  process.env.AGENT_ID_GAURAV || '',
].filter(Boolean);

if (!API_KEY) {
  console.error('❌  IDX_BROKER_API_KEY secret is not set.');
  process.exit(1);
}

// ── HTTP helper ───────────────────────────────────────────────────────────────
function idxGet(endpoint) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_BASE,
      path: endpoint,
      method: 'GET',
      headers: {
        accesskey: API_KEY,
        outputtype: 'json',
        apiversion: API_VER,
      },
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

// ── Normalise a raw IDX Broker listing object ─────────────────────────────────
function normaliseListing(raw, idxKey) {
  const adv = raw.advanced || {};
  return {
    id:          idxKey || raw.listingID || '',
    mlsNumber:   raw.listingID   || '',
    address:     raw.address     || '',
    city:        raw.cityName    || adv.city || '',
    state:       raw.state       || 'NY',
    zip:         raw.zipcode     || '',
    price:       parseInt(raw.listingPrice || raw.price || 0, 10),
    beds:        parseInt(raw.bedrooms     || 0, 10),
    baths:       parseFloat(raw.totalBaths || raw.fullBaths || 0),
    sqft:        parseInt(raw.sqFt         || 0, 10),
    type:        raw.propType    || raw.idxPropType || 'Residential',
    subType:     raw.propSubType || '',
    status:      raw.propStatus  || raw.idxStatus || 'Active',
    description: raw.remarksConcat || '',
    image:       raw.image        || (raw.mediaData && raw.mediaData[0] && raw.mediaData[0].url) || '',
    listingAgentID: raw.listingAgentID || '',
    detailsURL:  raw.fullDetailsURL || raw.detailsURL || '',
    yearBuilt:   parseInt(adv.yearBuilt  || raw.yearBuilt || 0, 10),
    acres:       raw.acres       || '',
    latitude:    raw.latitude    || '',
    longitude:   raw.longitude   || '',
    dateAdded:   raw.dateAdded   || '',
  };
}

// ── Fetch ALL featured/active listings ────────────────────────────────────────
async function fetchFeatured() {
  console.log('  Fetching featured listings…');
  const res = await idxGet('/clients/featured');
  if (res.status !== 200 || !res.body || !res.body.data) {
    console.warn('  ⚠  featured returned', res.status);
    return [];
  }
  return Object.entries(res.body.data).map(([k, v]) => normaliseListing(v, k));
}

// ── Fetch ALL listings for one IDX saved search (paginated) ───────────────────
async function fetchSearchResults(linkUID, labelForLog) {
  const results = [];
  let start = 0;
  const count = 100; // IDX Broker max per page
  let total   = null;

  console.log(`  Fetching saved-search "${labelForLog}" (uid ${linkUID})…`);

  while (true) {
    const res = await idxGet(`/clients/results/${linkUID}?start=${start}&count=${count}`);
    if (res.status !== 200) {
      console.warn(`  ⚠  ${labelForLog} page start=${start} returned ${res.status}`);
      break;
    }

    const body = res.body;

    // First page — grab total
    if (total === null) {
      total = parseInt(body.total || body.count || 0, 10);
      console.log(`    total listings: ${total}`);
    }

    const data = body.data || body;
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) break;

    Object.entries(data).forEach(([k, v]) => results.push(normaliseListing(v, k)));

    start += count;
    if (start >= total || Object.keys(data).length < count) break;

    // Be polite — 300 ms between pages
    await new Promise(r => setTimeout(r, 300));
  }

  console.log(`    fetched ${results.length} listings from "${labelForLog}"`);
  return results;
}

// ── Get saved-search links from IDX Broker ───────────────────────────────────
async function fetchSavedLinks() {
  console.log('  Fetching saved search links…');
  const res = await idxGet('/clients/savedlinks');
  if (res.status !== 200) {
    console.warn('  ⚠  savedlinks returned', res.status);
    return [];
  }
  // Returns array of {uid, name, url, …}
  const items = Array.isArray(res.body) ? res.body : Object.values(res.body || {});
  return items;
}

// ── Fetch system links (built-in pages like map search, featured, etc.) ───────
async function fetchSystemLinks() {
  const res = await idxGet('/clients/systemlinks');
  if (res.status !== 200) return [];
  return Array.isArray(res.body) ? res.body : Object.values(res.body || {});
}

// ── Deduplicate listings by MLS number ───────────────────────────────────────
function dedup(listings) {
  const seen = new Set();
  return listings.filter(l => {
    const key = l.mlsNumber || l.id;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log('\n🏠  IDX Broker listing sync starting…');
  console.log(`    API version : ${API_VER}`);
  console.log(`    Our agents  : ${OUR_AGENTS.join(', ') || '(none set)'}`);

  // 1. Load existing listings.json so we never discard sold/off-market history
  let existing = { activeListings:[], areaListings:[], queensListings:[], brooklynListings:[], longIslandListings:[], soldListings:[] };
  try {
    existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8'));
  } catch { /* first run */ }

  // 2. Fetch featured (our own listings on IDX Broker)
  const featured = await fetchFeatured();

  // 3. Fetch saved searches if any exist
  const savedLinks = await fetchSavedLinks();
  console.log(`  Found ${savedLinks.length} saved search link(s):`, savedLinks.map(l => l.name || l.uid).join(', '));

  const savedResults = [];
  for (const link of savedLinks) {
    const batch = await fetchSearchResults(link.uid, link.name || link.uid);
    savedResults.push(...batch);
    await new Promise(r => setTimeout(r, 500));
  }

  // 4. Try system links results (e.g. map-search result pages)
  const sysLinks = await fetchSystemLinks();
  console.log(`  System links: ${sysLinks.map(l => l.name).join(', ')}`);

  // 5. Combine everything
  const allFresh = dedup([...featured, ...savedResults]);
  console.log(`\n  Total unique active listings fetched: ${allFresh.length}`);

  // 6. Split into categories
  const activeListings     = allFresh.filter(l => OUR_AGENTS.includes(l.listingAgentID));
  const queensListings     = allFresh.filter(l => {
    const c = (l.city || '').toLowerCase();
    return ['richmond hill','south richmond hill','ozone park','south ozone park','woodhaven','jamaica','forest hills','kew gardens','flushing','astoria','jackson heights','elmhurst','corona','rego park','maspeth','ridgewood','glendale','middle village','howard beach','richmond hill'].some(q => c.includes(q));
  });
  const brooklynListings   = allFresh.filter(l => {
    const c = (l.city || '').toLowerCase();
    return ['brooklyn','flatbush','brownsville','canarsie','east new york','bedford-stuyvesant','bushwick','crown heights','park slope','bay ridge','bensonhurst','borough park','sunset park','red hook','cobble hill','carroll gardens','boerum hill','prospect heights','windsor terrace','kensington','ditmas park','flatlands','sheepshead bay','marine park','mill basin','gravesend','coney island','brighton beach','manhattan beach','gerritsen beach','floyd bennett','homecrest','mapleton'].some(q => c.includes(q));
  });
  const longIslandListings = allFresh.filter(l => {
    const state = (l.state || '').toUpperCase();
    const c = (l.city || '').toLowerCase();
    return state === 'NY' && !queensListings.includes(l) && !brooklynListings.includes(l) &&
      ['hempstead','elmont','valley stream','lynbrook','malverne','rockville centre','baldwin','merrick','bellmore','wantagh','seaford','levittown','hicksville','westbury','garden city','mineola','new hyde park','great neck','manhasset','port washington','roslyn','syosset','jericho','woodbury','oyster bay','glen cove','long beach','freeport','oceanside','massapequa','farmingdale','bethpage','plainview','huntington','commack','smithtown','hauppauge','brentwood','central islip','bay shore','islip','east islip'].some(q => c.includes(q));
  });

  // Listings not in any specific area bucket → general area listings
  const categorised = new Set([...activeListings, ...queensListings, ...brooklynListings, ...longIslandListings].map(l => l.id));
  const areaListings = allFresh.filter(l => !categorised.has(l.id));

  // Keep existing sold listings (IDX Broker active feed won't include them)
  const soldListings = existing.soldListings || [];

  const output = {
    lastSynced: new Date().toISOString(),
    totalCount: allFresh.length,
    activeListings,
    areaListings,
    queensListings,
    brooklynListings,
    longIslandListings,
    soldListings,
  };

  fs.writeFileSync(OUT_FILE, JSON.stringify(output, null, 2));

  console.log('\n✅  listings.json written');
  console.log(`    activeListings    : ${activeListings.length}`);
  console.log(`    queensListings    : ${queensListings.length}`);
  console.log(`    brooklynListings  : ${brooklynListings.length}`);
  console.log(`    longIslandListings: ${longIslandListings.length}`);
  console.log(`    areaListings      : ${areaListings.length}`);
  console.log(`    soldListings      : ${soldListings.length} (preserved)`);
  console.log(`    TOTAL             : ${allFresh.length}`);
}

main().catch(err => {
  console.error('❌  Sync failed:', err);
  process.exit(1);
});
