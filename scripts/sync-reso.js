#!/usr/bin/env node
/**
   * sync-reso.js — IDX Broker API Sync v3 (5/6 version)
   * Pulls ALL active MLS listings for Queens, Brooklyn & Long Island
   * via the IDX Broker REST API and writes data/listings.json
   *
   * Strategy:
   *  1. Auto-create saved searches (Queens / Brooklyn / Nassau / Suffolk)
   *     via POST /clients/savedlinks if they don't already exist
   *  2. Pull results from each saved search (paginated)
   *  3. Always include featured listings too
   *
   * GitHub Secret required: IDX_BROKER_API_KEY
   * Run: node scripts/sync-reso.js
   */
'use strict';

const https = require('https');
const fs    = require('fs');
const path  = require('path');
const qs    = require('querystring');

// ── Config ──────────────────────────────────────────────────────────────────
const API_KEY  = process.env.IDX_BROKER_API_KEY;
const API_BASE = 'api.idxbroker.com';
const API_VER  = '1.8.0';
const OUT_FILE = path.join(__dirname, '..', 'data', 'listings.json');

const OUR_AGENTS = [
    process.env.AGENT_ID_NITIN  || '',
    process.env.AGENT_ID_VINOD  || '',
    process.env.AGENT_ID_GAURAV || '',
  ].filter(Boolean);

if (!API_KEY) {
    console.error('❌  IDX_BROKER_API_KEY secret is not set.');
    process.exit(1);
}

// ── HTTP helper (GET) ────────────────────────────────────────────────────────
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
                            'Content-Type': 'application/x-www-form-urlencoded',
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

// ── HTTP helper (POST) ───────────────────────────────────────────────────────
function idxPost(endpoint, formData) {
    return new Promise((resolve, reject) => {
          const postData = qs.stringify(formData);
          const options = {
                  hostname: API_BASE,
                  path:     endpoint,
                  method:   'POST',
                  headers: {
                            accesskey:       API_KEY,
                            outputtype:      'json',
                            apiversion:      API_VER,
                            'Content-Type':  'application/x-www-form-urlencoded',
                            'Content-Length': Buffer.byteLength(postData),
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
          req.write(postData);
          req.end();
    });
}

// ── Normalise a raw IDX Broker listing object ────────────────────────────────
function normaliseListing(raw, idxKey) {
    const adv = raw.advanced || {};
    const photos = [];
    if (Array.isArray(raw.mediaData)) {
          raw.mediaData.forEach(m => { if (m && m.url) photos.push(m.url); });
    }
    if (raw.image && !photos.length) {
          if (typeof raw.image === 'string') photos.push(raw.image);
          else if (typeof raw.image === 'object') {
                  Object.values(raw.image).forEach(v => { if (v && v.url) photos.push(v.url); });
          }
    }
    return {
          id:             idxKey || raw.listingID || '',
          mlsNumber:      raw.listingID || '',
          address:        raw.address || '',
          city:           raw.cityName || raw.city || adv.city || '',
          state:          raw.state || 'NY',
          zip:            raw.zipcode || raw.zip || '',
          price:          parseInt(raw.listingPrice || raw.price || 0, 10),
          beds:           parseInt(raw.bedrooms || 0, 10),
          baths:          parseFloat(raw.totalBaths || raw.fullBaths || 0),
          sqft:           parseInt(raw.sqFt || 0, 10),
          type:           raw.propType || raw.idxPropType || 'Residential',
          subType:        raw.propSubType || '',
          status:         raw.propStatus || raw.idxStatus || 'Active',
          description:    raw.remarksConcat || raw.remarks || '',
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
          pool:           adv.pool || '',
          lotSize:        raw.lotSize || adv.lotSize || '',
          taxes:          adv.taxes || '',
          hoaDues:        adv.hoaDues || '',
    };
}

// ── Fetch featured listings ──────────────────────────────────────────────────
async function fetchFeatured() {
    console.log('  📌 Fetching featured listings…');
    const res = await idxGet('/clients/featured');
    if (res.status !== 200 || !res.body || !res.body.data) {
          console.warn(`  ⚠ featured returned ${res.status}`);
          return [];
    }
    const items = Object.entries(res.body.data).map(([k, v]) => normaliseListing(v, k));
    console.log(`     → ${items.length} featured listings`);
    return items;
}

// ── Get existing saved links ──────────────────────────────────────────────────
async function fetchSavedLinks() {
    const res = await idxGet('/clients/savedlinks');
    if (res.status === 204 || res.status !== 200) return [];
    const items = Array.isArray(res.body) ? res.body : Object.values(res.body || {});
    return items;
}

// ── Create a saved search via API ─────────────────────────────────────────────
// IDX Broker savedlinks POST params: linkName, idxID, propertyTypes[], counties[], cities[]
async function createSavedLink(name, searchParams) {
    console.log(`  ➕ Creating saved search: "${name}"…`);
    const res = await idxPost('/clients/savedlinks', { linkName: name, ...searchParams });
    if (res.status === 200 || res.status === 201) {
          const uid = res.body && (res.body.id || res.body.linkID || res.body.uid);
          console.log(`     ✅ Created: uid=${uid}`);
          return uid;
    }
    console.warn(`  ⚠ Create "${name}" returned ${res.status}:`, typeof res.body === 'string' ? res.body.substring(0, 200) : JSON.stringify(res.body).substring(0, 200));
    return null;
}

// ── Fetch all results from a saved link (paginated) ───────────────────────────
async function fetchResults(linkUID, labelForLog) {
    const results = [];
    let start = 0;
    const count = 100;
    let total = null;

  console.log(`  📂 Fetching results for "${labelForLog}" (uid ${linkUID})…`);

  while (true) {
        const res = await idxGet(`/clients/results/${linkUID}?start=${start}&count=${count}&rf[]=*`);

      if (res.status === 204) { console.log('     → 0 results'); break; }
        if (res.status !== 200) {
                console.warn(`  ⚠ results page start=${start} returned ${res.status}`);
                if (typeof res.body === 'string') console.warn('    body:', res.body.substring(0, 300));
                break;
        }

      const body = res.body;
        if (total === null) {
                total = parseInt(body.total || body.count || 0, 10);
                if (!total && body.data) total = Object.keys(body.data).length;
                console.log(`     total: ${total}`);
                if (total === 0) break;
        }

      const data = body.data || body;
        if (!data || typeof data !== 'object') break;
        const entries = Object.entries(data);
        if (entries.length === 0) break;

      entries.forEach(([k, v]) => {
              if (v && typeof v === 'object' && !Array.isArray(v)) {
                        results.push(normaliseListing(v, k));
              }
      });

      start += count;
        if (start >= total || entries.length < count) break;
        await new Promise(r => setTimeout(r, 300));
  }

  console.log(`     → fetched ${results.length} from "${labelForLog}"`);
    return results;
}

// ── Deduplicate by MLS number ─────────────────────────────────────────────────
function dedup(listings) {
    const seen = new Set();
    return listings.filter(l => {
          const key = l.mlsNumber || l.id;
          if (!key || seen.has(key)) return false;
          seen.add(key);
          return true;
    });
}

// ── Geography classification ──────────────────────────────────────────────────
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
    'gerritsen beach','homecrest','mapleton','williamsburg','greenpoint','dumbo',
    'brooklyn heights','fort greene','clinton hill','east flatbush',
    'cypress hills','dyker heights','bath beach','midwood','bed-stuy',
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
    'deer park','wyandanch','east meadow','uniondale','franklin square',
    'carle place','woodmere','hewlett','cedarhurst','lawrence','inwood',
  ]);

function classifyCity(city) {
    const c = (city || '').toLowerCase().trim();
    if (QUEENS_CITIES.has(c)) return 'queens';
    if (BROOKLYN_CITIES.has(c)) return 'brooklyn';
    if (LI_CITIES.has(c)) return 'longisland';
    for (const q of QUEENS_CITIES) if (c.includes(q)) return 'queens';
    for (const b of BROOKLYN_CITIES) if (c.includes(b)) return 'brooklyn';
    for (const l of LI_CITIES) if (c.includes(l)) return 'longisland';
    return 'area';
}

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
    console.log('\n🏠  IDX Broker listing sync v3 starting… (5/6 version)');
    console.log(`    API version : ${API_VER}`);
    console.log(`    Our agents  : ${OUR_AGENTS.join(', ') || '(none set)'}`);

  // 1. Load existing listings.json
  let existing = {
        activeListings: [], areaListings: [], queensListings: [],
        brooklynListings: [], longIslandListings: [], soldListings: []
  };
    try { existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8')); }
    catch { /* first run */ }

  // 2. Featured listings (always available)
  const featured = await fetchFeatured();

  // 3. Get existing saved links
  console.log('\n  🔗 Checking existing saved search links…');
    let savedLinks = await fetchSavedLinks();
    console.log(`     → found ${savedLinks.length} existing link(s):`, savedLinks.map(l => l.linkName || l.name || l.uid).join(', ') || 'none');

  // 4. Bootstrap: create broad saved searches if not present
  const NEEDED = [
    { name: 'Queens All Active', params: { 'counties[]': 'Queens' } },
    { name: 'Brooklyn All Active', params: { 'counties[]': 'Kings' } },
    { name: 'Nassau All Active', params: { 'counties[]': 'Nassau' } },
    { name: 'Suffolk All Active', params: { 'counties[]': 'Suffolk' } },
      ];

  const existingNames = new Set(savedLinks.map(l => (l.linkName || l.name || '').toLowerCase()));
    let newLinksCreated = false;

  for (const needed of NEEDED) {
        if (!existingNames.has(needed.name.toLowerCase())) {
                const uid = await createSavedLink(needed.name, needed.params);
                if (uid) {
                          savedLinks.push({ uid, linkName: needed.name });
                          newLinksCreated = true;
                          await new Promise(r => setTimeout(r, 500));
                }
        } else {
                console.log(`  ✓ Saved search already exists: "${needed.name}"`);
        }
  }

  if (newLinksCreated) {
        // Re-fetch to get correct UIDs
      console.log('  🔄 Re-fetching saved links after creation…');
        await new Promise(r => setTimeout(r, 1000));
        savedLinks = await fetchSavedLinks();
        console.log(`     → now have ${savedLinks.length} link(s)`);
  }

  // 5. Fetch results from all saved searches
  const savedResults = [];
    for (const link of savedLinks) {
          const uid = link.uid || link.id || link.linkID;
          const name = link.linkName || link.name || String(uid);
          if (!uid) { console.warn('  ⚠ link has no uid:', link); continue; }
          const batch = await fetchResults(uid, name);
          savedResults.push(...batch);
          await new Promise(r => setTimeout(r, 500));
    }

  // 6. Combine + deduplicate
  const allFresh = dedup([...featured, ...savedResults]);
    console.log(`\n    Total unique active listings fetched: ${allFresh.length}`);

  // 7. Classify into geo buckets
  const activeListings     = allFresh.filter(l => OUR_AGENTS.includes(l.listingAgentID));
    const queensListings     = [];
    const brooklynListings   = [];
    const longIslandListings = [];
    const areaListings       = [];

  for (const l of allFresh) {
        if (OUR_AGENTS.includes(l.listingAgentID)) continue;
        const bucket = classifyCity(l.city);
        if      (bucket === 'queens')     queensListings.push(l);
        else if (bucket === 'brooklyn')   brooklynListings.push(l);
        else if (bucket === 'longisland') longIslandListings.push(l);
        else                              areaListings.push(l);
  }

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
