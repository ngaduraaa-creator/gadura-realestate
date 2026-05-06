#!/usr/bin/env node
/**
   * sync-reso.js — IDX Broker API Sync v2 (5/6 version)
   * Pulls ALL active MLS listings for Queens, Brooklyn & Long Island
   * via the IDX Broker REST API and writes data/listings.json
   *
   * Strategy (in order of priority):
   *  1. Saved search links → /clients/results/{linkUID}  (if any exist)
   *  2. MLS search via /clients/search with city/county queries
   *  3. Featured listings → /clients/featured  (always included)
   *
   * GitHub Secret required: IDX_BROKER_API_KEY
   * Run: node scripts/sync-reso.js
   */
'use strict';

const https = require('https');
const fs    = require('fs');
const path  = require('path');

// ── Config ──────────────────────────────────────────────────────────────────
const API_KEY  = process.env.IDX_BROKER_API_KEY;
const API_BASE = 'api.idxbroker.com';
const API_VER  = '1.8.0';
const OUT_FILE = path.join(__dirname, '..', 'data', 'listings.json');

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

// ── HTTP helper ─────────────────────────────────────────────────────────────
function idxGet(endpoint) {
    return new Promise((resolve, reject) => {
          const options = {
                  hostname: API_BASE,
                  path:     endpoint,
                  method:   'GET',
                  headers: {
                            accesskey:  API_KEY,
                            outputtype: 'json',
                            apiversion: API_VER,
                  },
          };
          const req = https.request(options, (res) => {
                  let data = '';
                  res.on('data', chunk => { data += chunk; });
                  res.on('end', () => {
                            try   { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
                            catch { resolve({ status: res.statusCode, body: data }); }
                  });
          });
          req.on('error', reject);
          req.end();
    });
}

// ── Normalise a raw IDX Broker listing object ────────────────────────────────
function normaliseListing(raw, idxKey) {
    const adv = raw.advanced || {};
    // Handle photos — IDX returns mediaData array or single image field
  const photos = [];
    if (Array.isArray(raw.mediaData)) {
          raw.mediaData.forEach(m => { if (m && m.url) photos.push(m.url); });
    } else if (raw.image) {
          photos.push(raw.image);
    }
    return {
          id:             idxKey || raw.listingID || '',
          mlsNumber:      raw.listingID || '',
          address:        raw.address || '',
          city:           raw.cityName || adv.city || '',
          state:          raw.state || 'NY',
          zip:            raw.zipcode || '',
          price:          parseInt(raw.listingPrice || raw.price || 0, 10),
          beds:           parseInt(raw.bedrooms || 0, 10),
          baths:          parseFloat(raw.totalBaths || raw.fullBaths || 0),
          sqft:           parseInt(raw.sqFt || 0, 10),
          type:           raw.propType || raw.idxPropType || 'Residential',
          subType:        raw.propSubType || '',
          status:         raw.propStatus || raw.idxStatus || 'Active',
          description:    raw.remarksConcat || '',
          image:          photos[0] || '',
          photos:         photos,
          listingAgentID: raw.listingAgentID || '',
          detailsURL:     raw.fullDetailsURL || raw.detailsURL || '',
          yearBuilt:      parseInt(adv.yearBuilt || raw.yearBuilt || 0, 10),
          acres:          raw.acres || '',
          latitude:       raw.latitude || '',
          longitude:      raw.longitude || '',
          dateAdded:      raw.dateAdded || '',
          garage:         adv.garage || '',
          basement:       adv.basement || '',
          pool:           adv.pool || '',
          lotSize:        raw.lotSize || adv.lotSize || '',
          taxes:          adv.taxes || '',
          hoaDues:        adv.hoaDues || '',
    };
}

// ── Fetch featured listings (our curated picks) ──────────────────────────────
async function fetchFeatured() {
    console.log('  📌 Fetching featured listings…');
    const res = await idxGet('/clients/featured');
    if (res.status !== 200 || !res.body || !res.body.data) {
          console.warn('  ⚠ featured returned', res.status);
          return [];
    }
    const items = Object.entries(res.body.data).map(([k, v]) => normaliseListing(v, k));
    console.log(`     → ${items.length} featured listings`);
    return items;
}

// ── Fetch all listings via MLS search (paginated) ────────────────────────────
// IDX Broker /clients/search supports county, city, state, propType filters
async function fetchBySearch(params, labelForLog) {
    const results = [];
    let start = 0;
    const count = 100;
    let total = null;

  console.log(`  🔍 Searching: "${labelForLog}"…`);

  while (true) {
        const qs = new URLSearchParams({
                ...params,
                start:     String(start),
                count:     String(count),
                status:    'active',
                outputtype: 'json',
        }).toString();

      const res = await idxGet(`/clients/search?${qs}`);

      if (res.status === 204) {
              console.log(`     → 0 results (204 no content)`);
              break;
      }
        if (res.status !== 200) {
                console.warn(`  ⚠ search "${labelForLog}" page start=${start} returned ${res.status}`);
                if (typeof res.body === 'string') console.warn('    body:', res.body.substring(0, 200));
                break;
        }

      const body = res.body;

      // First page — grab total
      if (total === null) {
              total = parseInt(body.total || body.count || 0, 10);
              console.log(`     total: ${total}`);
              if (total === 0) break;
      }

      const data = body.data || body;
        if (!data || typeof data !== 'object' || Object.keys(data).length === 0) break;

      Object.entries(data).forEach(([k, v]) => results.push(normaliseListing(v, k)));
        start += count;
        if (start >= total || Object.keys(data).length < count) break;

      // Be polite between pages
      await new Promise(r => setTimeout(r, 400));
  }

  console.log(`     → fetched ${results.length} from "${labelForLog}"`);
    return results;
}

// ── Fetch saved search results (paginated) ───────────────────────────────────
async function fetchSearchResults(linkUID, labelForLog) {
    const results = [];
    let start = 0;
    const count = 100;
    let total = null;

  console.log(`  📂 Saved search "${labelForLog}" (uid ${linkUID})…`);

  while (true) {
        const res = await idxGet(`/clients/results/${linkUID}?start=${start}&count=${count}`);
        if (res.status !== 200) {
                console.warn(`  ⚠ ${labelForLog} page start=${start} returned ${res.status}`);
                break;
        }
        const body = res.body;
        if (total === null) {
                total = parseInt(body.total || body.count || 0, 10);
                console.log(`     total: ${total}`);
        }
        const data = body.data || body;
        if (!data || typeof data !== 'object' || Object.keys(data).length === 0) break;
        Object.entries(data).forEach(([k, v]) => results.push(normaliseListing(v, k)));
        start += count;
        if (start >= total || Object.keys(data).length < count) break;
        await new Promise(r => setTimeout(r, 400));
  }

  console.log(`     → fetched ${results.length} from "${labelForLog}"`);
    return results;
}

// ── Get saved search links from IDX Broker ───────────────────────────────────
async function fetchSavedLinks() {
    console.log('  🔗 Fetching saved search links…');
    const res = await idxGet('/clients/savedlinks');
    if (res.status === 204 || res.status !== 200) {
          console.log('     → none found');
          return [];
    }
    const items = Array.isArray(res.body) ? res.body : Object.values(res.body || {});
    console.log(`     → found ${items.length} saved link(s)`);
    return items;
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

// ── Geography helpers ─────────────────────────────────────────────────────────
const QUEENS_CITIES = new Set([
    'richmond hill','south richmond hill','ozone park','south ozone park',
    'woodhaven','jamaica','forest hills','kew gardens','kew garden hills',
    'flushing','astoria','jackson heights','elmhurst','corona','rego park',
    'maspeth','ridgewood','glendale','middle village','howard beach',
    'fresh meadows','jamaica estates','hollis','st albans','springfield gardens',
    'rosedale','laurelton','far rockaway','belle harbor','rockaway park',
    'broad channel','woodside','sunnyside','long island city','hunters point',
    'bayside','whitestone','college point','malba','beechhurst','queens village',
    'bellerose','floral park','glen oaks','little neck','douglaston','auburndale',
    'oakland gardens','cambria heights','brookville',
  ]);

const BROOKLYN_CITIES = new Set([
    'brooklyn','flatbush','brownsville','canarsie','east new york',
    'bedford-stuyvesant','bushwick','crown heights','park slope','bay ridge',
    'bensonhurst','borough park','sunset park','red hook','cobble hill',
    'carroll gardens','boerum hill','prospect heights','windsor terrace',
    'kensington','ditmas park','flatlands','sheepshead bay','marine park',
    'mill basin','gravesend','coney island','brighton beach','manhattan beach',
    'gerritsen beach','floyd bennett','homecrest','mapleton','williamsburg',
    'greenpoint','dumbo','brooklyn heights','fort greene','clinton hill',
    'bed-stuy','east flatbush','cypress hills','highland park','new utrecht',
    'dyker heights','bath beach','gravesend','midwood','prospect lefferts',
  ]);

const LI_CITIES = new Set([
    'hempstead','elmont','valley stream','lynbrook','malverne','rockville centre',
    'baldwin','merrick','bellmore','wantagh','seaford','levittown','hicksville',
    'westbury','garden city','mineola','new hyde park','great neck','manhasset',
    'port washington','roslyn','syosset','jericho','woodbury','oyster bay',
    'glen cove','long beach','freeport','oceanside','massapequa','farmingdale',
    'bethpage','plainview','huntington','commack','smithtown','hauppauge',
    'brentwood','central islip','bay shore','islip','east islip','patchogue',
    'babylon','copiague','amityville','lindenhurst','west babylon','north babylon',
    'deer park','wyandanch','north amityville','north lindenhurst','east meadow',
    'uniondale','east garden city','franklin square','floral park','new cassel',
    'carle place','east williston','old westbury','brookville','upper brookville',
    'woodmere','hewlett','cedarhurst','lawrence','inwood','far rockaway',
    'kings point','lake success','great neck estates','saddle rock',
  ]);

function classifyCity(city) {
    const c = (city || '').toLowerCase().trim();
    if (QUEENS_CITIES.has(c)) return 'queens';
    if (BROOKLYN_CITIES.has(c)) return 'brooklyn';
    if (LI_CITIES.has(c)) return 'longisland';
    // Fuzzy match
  for (const q of QUEENS_CITIES) if (c.includes(q) || q.includes(c)) return 'queens';
    for (const b of BROOKLYN_CITIES) if (c.includes(b) || b.includes(c)) return 'brooklyn';
    for (const l of LI_CITIES) if (c.includes(l) || l.includes(c)) return 'longisland';
    return 'area';
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
    console.log('\n🏠  IDX Broker listing sync v2 starting… (5/6 version)');
    console.log(`    API version : ${API_VER}`);
    console.log(`    Our agents  : ${OUR_AGENTS.join(', ') || '(none set)'}`);

  // 1. Load existing listings.json — never discard history
  let existing = {
        activeListings: [], areaListings: [], queensListings: [],
        brooklynListings: [], longIslandListings: [], soldListings: []
  };
    try { existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8')); }
    catch { /* first run */ }

  // 2. Fetch featured (our curated picks — always works)
  const featured = await fetchFeatured();

  // 3. Fetch saved search links (if any)
  const savedLinks = await fetchSavedLinks();
    const savedResults = [];
    for (const link of savedLinks) {
          const batch = await fetchSearchResults(link.uid, link.name || link.uid);
          savedResults.push(...batch);
          await new Promise(r => setTimeout(r, 600));
    }

  // 4. MLS search queries — broad area sweeps for thousands of listings
  //    IDX Broker search endpoint accepts: idxID (MLS), pt (prop type),
  //    city, zip, county, state, minPrice, maxPrice, bd (beds), ba (baths)
  const searchBatches = [];

  // Queens — by county (Queens County = county of Queens)
  const queensSearch = await fetchBySearch(
    { county: 'Queens' }, 'Queens County — all active'
      );
    searchBatches.push(...queensSearch);
    await new Promise(r => setTimeout(r, 600));

  // Brooklyn (Kings County)
  const brooklynSearch = await fetchBySearch(
    { county: 'Kings' }, 'Kings County (Brooklyn) — all active'
      );
    searchBatches.push(...brooklynSearch);
    await new Promise(r => setTimeout(r, 600));

  // Nassau County (Long Island)
  const nassauSearch = await fetchBySearch(
    { county: 'Nassau' }, 'Nassau County — all active'
      );
    searchBatches.push(...nassauSearch);
    await new Promise(r => setTimeout(r, 600));

  // Suffolk County (Long Island)
  const suffolkSearch = await fetchBySearch(
    { county: 'Suffolk' }, 'Suffolk County — all active'
      );
    searchBatches.push(...suffolkSearch);
    await new Promise(r => setTimeout(r, 600));

  // 5. Combine everything
  const allFresh = dedup([...featured, ...savedResults, ...searchBatches]);
    console.log(`\n    Total unique active listings fetched: ${allFresh.length}`);

  // 6. Classify into buckets
  const activeListings    = allFresh.filter(l => OUR_AGENTS.includes(l.listingAgentID));
    const queensListings    = [];
    const brooklynListings  = [];
    const longIslandListings = [];
    const areaListings      = [];

  for (const l of allFresh) {
        if (OUR_AGENTS.includes(l.listingAgentID)) continue; // already in activeListings
      const bucket = classifyCity(l.city);
        if      (bucket === 'queens')     queensListings.push(l);
        else if (bucket === 'brooklyn')   brooklynListings.push(l);
        else if (bucket === 'longisland') longIslandListings.push(l);
        else                              areaListings.push(l);
  }

  // Keep existing sold listings (active feed won't include them)
  const soldListings = existing.soldListings || [];

  const output = {
        lastSynced:         new Date().toISOString(),
        totalCount:         allFresh.length,
        activeListings,
        areaListings,
        queensListings,
        brooklynListings,
        longIslandListings,
        soldListings,
  };

  fs.writeFileSync(OUT_FILE, JSON.stringify(output, null, 2));

  console.log('\n✅  listings.json written');
    console.log(`    activeListings     : ${activeListings.length}`);
    console.log(`    queensListings     : ${queensListings.length}`);
    console.log(`    brooklynListings   : ${brooklynListings.length}`);
    console.log(`    longIslandListings : ${longIslandListings.length}`);
    console.log(`    areaListings       : ${areaListings.length}`);
    console.log(`    soldListings       : ${soldListings.length} (preserved)`);
    console.log(`    TOTAL              : ${allFresh.length}`);
}

main().catch(err => {
    console.error('❌  Sync failed:', err);
    process.exit(1);
});
