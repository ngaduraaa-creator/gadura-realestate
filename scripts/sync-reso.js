#!/usr/bin/env node
/**
  * sync-reso.js — IDX Broker API Sync v5.3
  * Full-power listing sync for Queens, Brooklyn, Nassau, Suffolk
  *
  * Fixes vs v5.2:
  *  - fixed savedlinks POST: correct IDX Broker v1.8 API format
  *    (only linkName + queryString fields; idxID embedded in queryString)
  *  - do not double-encode city names in queryString
  *  - graceful fallback: if savedlinks 400s, skip and use featured/system links
  *  - do not exit(1) on 0 listings — warn and write empty array instead
  *  - improved systemlinks results fetching
  */
'use strict';

const https   = require('https');
const fs      = require('fs');
const path    = require('path');

const API_KEY  = process.env.IDX_BROKER_API_KEY;
const API_BASE = 'api.idxbroker.com';
const API_VER  = '1.8.0';
const IDX_ID   = 'c056';
const OUT_FILE = path.join(__dirname, '..', 'data', 'listings.json');

const OUR_AGENTS = [
   process.env.AGENT_ID_NITIN  || '',
   process.env.AGENT_ID_VINOD  || '',
   process.env.AGENT_ID_GAURAV || '',
 ].filter(Boolean);

if (!API_KEY) { console.error('IDX_BROKER_API_KEY not set'); process.exit(1); }

// ─── HTTP helpers ──────────────────────────────────────────────────────────────

function idxGet(endpoint) {
   return new Promise((resolve, reject) => {
        const options = {
               hostname: API_BASE,
               path: endpoint,
               method: 'GET',
               headers: {
                        accesskey:   API_KEY,
                        outputtype:  'json',
                        apiversion:  API_VER,
               },
        };
        const req = https.request(options, (res) => {
               let data = '';
               res.on('data', c => data += c);
               res.on('end', () => {
                        console.log(`  GET ${endpoint} → ${res.statusCode}`);
                        if (res.statusCode === 200) {
                                   try { resolve(JSON.parse(data)); } catch(e) { resolve(null); }
                        } else if (res.statusCode === 204) {
                                   console.log(`  Response body: (empty — no content)`);
                                   resolve(null);
                        } else {
                                   console.log(`  Response body: ${data.slice(0, 400)}`);
                                   resolve(null);
                        }
               });
        });
        req.on('error', reject);
        req.end();
   });
}

// PHP-style form serializer. IDX Broker savedlinks POST requires the query as a
// nested array: queryString[idxID]=c056&queryString[a_city][]=Queens — NOT a
// single pre-encoded string. Handles {obj}, [array], and array-valued sub-keys.
function buildPostData(formData) {
   const enc = s => encodeURIComponent(s);
   const parts = [];
   for (const [key, val] of Object.entries(formData)) {
        if (val && typeof val === 'object' && !Array.isArray(val)) {
               for (const [sk, sv] of Object.entries(val)) {
                        if (Array.isArray(sv)) sv.forEach(it => parts.push(`${enc(key)}[${enc(sk)}][]=${enc(it)}`));
                        else parts.push(`${enc(key)}[${enc(sk)}]=${enc(sv)}`);
               }
        } else if (Array.isArray(val)) {
               val.forEach(it => parts.push(`${enc(key)}[]=${enc(it)}`));
        } else {
               parts.push(`${enc(key)}=${enc(val)}`);
        }
   }
   return parts.join('&');
}

function idxPost(endpoint, formData) {
   return new Promise((resolve, reject) => {
        const postData = buildPostData(formData);
        const options = {
               hostname: API_BASE,
               path: endpoint,
               method: 'POST',
               headers: {
                        accesskey:        API_KEY,
                        outputtype:       'json',
                        apiversion:       API_VER,
                        'Content-Type':   'application/x-www-form-urlencoded',
                        'Content-Length': Buffer.byteLength(postData),
               },
        };
        const req = https.request(options, (res) => {
               let data = '';
               res.on('data', c => data += c);
               res.on('end', () => {
                        console.log(`  POST ${endpoint} → ${res.statusCode}`);
                        if (data) console.log(`  Response: ${data.slice(0, 300)}`);
                        if (res.statusCode >= 200 && res.statusCode < 300) {
                                   try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
                                   catch(e) { resolve({ status: res.statusCode, body: data }); }
                        } else {
                                   resolve({ status: res.statusCode, body: data });
                        }
               });
        });
        req.on('error', reject);
        req.write(postData);
        req.end();
   });
}

// ─── Safe listing extractor (handles objects, arrays, nulls) ──────────────────

// IDX Broker responses come in several shapes: a flat array, an object keyed by
// listing id (e.g. {"c056!%998692": {...}}), or a wrapper around such a map
// (e.g. {featured:{...}}). This flattens all of them to a list of listing
// objects, and stamps the listing id from the key when the object lacks one.
function looksLikeListing(o) {
   return o && typeof o === 'object' && (o.address || o.streetName || o.streetNumber ||
          o.listingID || o.idxID || o.listingId || o.listPrice || o.price || o.listingPrice || o.fullDetailsURL);
}
// saved-link / system-link metadata (so we don't mistake it for a nested map)
function looksLikeLinkMeta(o) {
   return o && typeof o === 'object' && (o.linkName || o.linkTitle || o.uid || o.linkUID || o.savedLinkID || o.queryString);
}
function extractListings(data) {
   if (!data) return [];
   const out = [];
   const items = Array.isArray(data) ? data : Object.values(data);
   for (const item of items) {
        if (!item || typeof item !== 'object') continue;
        if (looksLikeListing(item) || looksLikeLinkMeta(item)) { out.push(item); continue; }
        // nested map of listings → flatten, capturing the key as the id
        for (const [k, v] of Object.entries(item)) {
               if (v && typeof v === 'object') {
                        if (!v.listingID && !v.idxID && !v.listingId) {
                                   const num = String(k).split(/[^0-9]+/).filter(Boolean).pop();
                                   if (num) v.listingID = num;
                        }
                        out.push(v);
               }
        }
   }
   return out.filter(item => item && typeof item === 'object');
}

// ─── Component discovery ───────────────────────────────────────────────────────

async function discoverComponents() {
   console.log('\n[1] Discovering MLS list components...');
   let components = await idxGet(`/clients/listcomponents/${IDX_ID}`);
   if (!components) components = await idxGet('/clients/listcomponents');
   if (!components) {
        console.log('  listcomponents unavailable');
        return null;
   }
   const compStr = JSON.stringify(components).slice(0, 500);
   console.log('  listcomponents structure:', compStr);
   return components;
}

// ─── Saved link bootstrap ──────────────────────────────────────────────────────

const TARGET_AREAS = [
 { name: 'Queens NY',           city: 'Queens'           },
 { name: 'Brooklyn NY',         city: 'Brooklyn'         },
 { name: 'Flushing NY',         city: 'Flushing'         },
 { name: 'Jamaica NY',          city: 'Jamaica'          },
 { name: 'Bayside NY',          city: 'Bayside'          },
 { name: 'Forest Hills NY',     city: 'Forest Hills'     },
 { name: 'Astoria NY',          city: 'Astoria'          },
 { name: 'Long Island City NY', city: 'Long Island City' },
 { name: 'Ridgewood NY',        city: 'Ridgewood'        },
 { name: 'Jackson Heights NY',  city: 'Jackson Heights'  },
 ];

/**
 * IDX Broker v1.8 savedlinks POST only accepts two fields:
 *   linkName    — display name for the saved link
 *   queryString — raw URL query string (NOT form-encoded again)
 *
 * The queryString itself should look like:
 *   idxID=c056&a_propStatus[]=Active&a_city[]=Queens&hp=50000000&lp=0
 *
 * Important: do NOT pass idxID as a separate form field.
 * Important: city names go into queryString un-encoded (the whole queryString
 *            value gets encoded by our postData builder, but internally the
 *            brackets and = must be kept).
 */
// Returns queryString OBJECTS (not strings). idxPost serializes them as the
// IDX-required nested array: queryString[idxID]=c056&queryString[a_city][]=Queens
function buildSavedLinkVariants(city) {
  return [
       // Primary: all active listings in the city across the full price range
       { idxID: IDX_ID, a_propStatus: ['Active'], a_city: [city], hp: 100000000, lp: 0 },
       // Fallback: minimal (city only)
       { idxID: IDX_ID, a_city: [city] },
     ];
}

async function bootstrapSavedLinks() {
   console.log('\n[2] Checking/creating saved links...');

  const existingData = await idxGet('/clients/savedlinks');
   const existingNames = new Set();
   if (existingData) {
        const entries = extractListings(existingData);
        for (const link of entries) {
               if (link.linkName) existingNames.add(link.linkName);
        }
        console.log(`  Existing saved link names: ${[...existingNames].join(', ') || 'none'}`);
   } else {
        console.log('  No existing saved links (204 No Content)');
   }

  let created = 0;
   let firstAttemptStatus = null;

  for (const area of TARGET_AREAS) {
       if (existingNames.has(area.name)) {
              console.log(`  Skipping "${area.name}" — already exists`);
              continue;
       }

     let succeeded = false;
       const variants = buildSavedLinkVariants(area.city);

     for (let i = 0; i < variants.length; i++) {
            const qs = variants[i];
            console.log(`  Trying variant ${i + 1} for "${area.name}": ${JSON.stringify(qs).slice(0, 90)}`);

         // IDX v1.8 requires linkName + linkTitle + pageTitle + queryString (object).
         // queryString as an object → idxPost serializes to queryString[key]=value.
         const result = await idxPost('/clients/savedlinks', {
                  linkName:    area.name,
                  linkTitle:   area.name,
                  pageTitle:   area.name + ' Homes For Sale',
                  queryString: qs,
         });

         if (firstAttemptStatus === null) firstAttemptStatus = result.status;

         if (result.status >= 200 && result.status < 300) {
                  console.log(`  ✓ Created: "${area.name}" (variant ${i + 1})`);
                  created++;
                  succeeded = true;
                  break;
         }
            await new Promise(r => setTimeout(r, 300));
     }

     if (!succeeded) {
            console.log(`  ✗ All variants failed for "${area.name}"`);
            // 400/401/403 on the very first area means the API key cannot create
         // saved links (write permission disabled, or the account requires saved
         // searches to be made in the dashboard). Failing for one area means it
         // fails for all — stop hammering the API.
         if (firstAttemptStatus === 400 || firstAttemptStatus === 401 || firstAttemptStatus === 403) {
                  console.log(`  Saved-link creation not permitted via API (status ${firstAttemptStatus}).`);
                  console.log('  → To pull ALL active listings per area, create Saved Searches in the IDX');
                  console.log('    Broker dashboard (Lead Management → Saved Searches); this script will then');
                  console.log('    auto-fetch their results. Featured listings already sync regardless.');
                  break;
         }
     }
  }

  console.log(`  Created ${created} new saved links`);
   return created;
}

// ─── Fetch all results from saved links ───────────────────────────────────────

async function fetchSavedLinkResults() {
   console.log('\n[3] Fetching all saved link results...');
   const savedData = await idxGet('/clients/savedlinks');
   if (!savedData) {
        console.log('  No saved links (204)');
        return [];
   }

  const links = extractListings(savedData);
   console.log(`  Found ${links.length} saved links to process`);

  const allListings = [];
   const seen = new Set();

  for (const link of links) {
       const uid = link.uid || link.linkUID || link.savedLinkID;
       if (!uid) {
              console.log(`  Skipping link without uid: ${JSON.stringify(link).slice(0, 100)}`);
              continue;
       }
       console.log(`  Fetching: "${link.linkName || uid}" (uid=${uid})`);
       let page = 1;
       while (true) {
              const results = await idxGet(`/clients/results/${uid}?pageSize=500&page=${page}`);
              if (!results) break;
              const listings = extractListings(results);
              if (listings.length === 0) break;
              console.log(`    Page ${page}: ${listings.length} listings`);
              for (const listing of listings) {
                       const id = listing.listingID || listing.idxID || listing.mlsID || listing.listingId;
                       if (id && !seen.has(id)) {
                                  seen.add(id);
                                  const n = normalise(listing);
                                  if (n) allListings.push(n);
                       }
              }
              if (listings.length < 500) break;
              page++;
              await new Promise(r => setTimeout(r, 200));
       }
  }

  console.log(`  Total from saved links: ${allListings.length}`);
   return allListings;
}

// ─── Fetch featured listings ───────────────────────────────────────────────────

async function fetchFeatured() {
   console.log('\n[4] Fetching featured listings...');
   const data = await idxGet('/clients/featured');
   if (!data) return [];
   const listings = extractListings(data);
   console.log(`  Featured raw count: ${listings.length}`);
   if (listings.length > 0) {
        console.log('  Sample listing keys:', Object.keys(listings[0]).join(', '));
   }
   const normalised = listings.map(normalise).filter(Boolean);
   console.log(`  Featured after normalise: ${normalised.length}`);
   return normalised;
}

// ─── Fetch systemlinks results ─────────────────────────────────────────────────

async function fetchSystemLinks() {
   console.log('\n[5] Checking system links...');
   const data = await idxGet('/clients/systemlinks');
   if (!data) {
        console.log('  No system links');
        return [];
   }
   const links = extractListings(data);
   console.log(`  System links: ${links.length}`);
   for (const link of links) {
        console.log(`  System link: uid=${link.uid} name="${link.linkName}" url="${link.pageURL || ''}"`);
   }

  const allListings = [];
   const seen = new Set();

  for (const link of links) {
       const uid = link.uid || link.linkUID;
       if (!uid) continue;
       const results = await idxGet(`/clients/results/${uid}?pageSize=500`);
       if (results) {
              const listings = extractListings(results);
              console.log(`  System link "${link.linkName || uid}": ${listings.length} listings`);
              for (const l of listings) {
                       const id = l.listingID || l.idxID || l.mlsID;
                       if (id && !seen.has(id)) {
                                  seen.add(id);
                                  const n = normalise(l);
                                  if (n) allListings.push(n);
                       }
              }
       }
       await new Promise(r => setTimeout(r, 200));
  }
   return allListings;
}

// ─── Fetch via /clients/listing (ancillarykey tier) ───────────────────────────

async function fetchDirectListings() {
   console.log('\n[6] Trying /clients/listing (ancillary tier)...');
   const data = await idxGet('/clients/listing');
   if (!data) {
        console.log('  Not available (expected for standard accounts)');
        return [];
   }
   const listings = extractListings(data);
   console.log(`  Direct listings: ${listings.length}`);
   return listings.map(normalise).filter(Boolean);
}

// ─── Normalise a listing to consistent shape ───────────────────────────────────

function normalise(raw) {
   if (!raw || typeof raw !== 'object') return null;

  const price = parseInt(
       String(raw.listPrice || raw.ListPrice || raw.currentPrice || raw.price || '0')
         .replace(/[^0-9]/g, ''), 10
     ) || 0;

  let addrParts = [];
   if (raw.address) {
        addrParts.push(raw.address);
   } else if (raw.streetNumber || raw.streetName) {
        addrParts.push([raw.streetNumber, raw.streetName].filter(Boolean).join(' '));
   }
   const city  = raw.city  || raw.cityName           || '';
   const state = raw.state || raw.stateOrProvince    || 'NY';
   const zip   = raw.zipcode || raw.postalCode       || '';
   if (city)  addrParts.push(city);
   if (state) addrParts.push(state);
   if (zip)   addrParts.push(zip);
   const address = addrParts.join(', ');

  const photos = [];
   if (raw.image) {
        if (typeof raw.image === 'string') photos.push(raw.image);
        else if (raw.image.url) photos.push(raw.image.url);
   }
   if (raw.mainPhoto) photos.push(raw.mainPhoto);
   if (raw.photo)     photos.push(raw.photo);
   if (Array.isArray(raw.photos)) {
        for (const p of raw.photos) photos.push(typeof p === 'string' ? p : p.url || p.src || '');
   }
   for (let i = 0; i <= 20; i++) {
        const key = `image${i}`;
        if (raw[key]) photos.push(typeof raw[key] === 'string' ? raw[key] : raw[key].url || '');
   }
   const cleanPhotos = [...new Set(photos.filter(p => p && typeof p === 'string' && p.startsWith('http')))];
   if (cleanPhotos.length === 0) cleanPhotos.push('/assets/images/placeholder.jpg');

  const addrSlug = (raw.address || raw.streetName || '').replace(/[^a-z0-9]+/gi, '-').toLowerCase();
   const citySlug = city.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
   const idPart   = (raw.listingID || raw.idxID || raw.mlsID || raw.listingId || '').toString();
   const slug     = [addrSlug, citySlug, idPart]
     .filter(Boolean).join('-').replace(/-+/g, '-').replace(/^-|-$/g, '');

  return {
       id:           String(raw.listingID || raw.idxID || raw.mlsID || raw.listingId || ''),
       slug,
       address,
       city,
       state,
       zip,
       county:       raw.county       || raw.countyOrParish         || '',
       price,
       beds:         parseInt(raw.bedrooms   || raw.BedroomsTotal   || raw.beds  || 0, 10),
       baths:        parseFloat(raw.bathrooms || raw.BathroomsTotalDecimal || raw.baths || 0),
       sqft:         parseInt(raw.sqft       || raw.LivingArea       || raw.squareFeet  || 0, 10),
       lotSize:      String(raw.lotSize      || raw.LotSizeAcres     || ''),
       yearBuilt:    parseInt(raw.yearBuilt  || raw.YearBuilt        || 0, 10) || null,
       propType:     String(raw.propType     || raw.PropertyType     || raw.propertyType || ''),
       status:       String(raw.propStatus   || raw.StandardStatus   || raw.status       || 'Active'),
       description:  String(raw.remarksConcat || raw.PublicRemarks   || raw.description  || ''),
       photos:       cleanPhotos,
       lat:          parseFloat(raw.latitude  || raw.Latitude        || 0) || null,
       lng:          parseFloat(raw.longitude || raw.Longitude       || 0) || null,
       mlsNumber:    String(raw.listingID    || raw.mlsNumber        || raw.ListingId    || ''),
       agentID:      String(raw.agentID      || raw.ListAgentMlsId   || ''),
       isOurListing: OUR_AGENTS.length > 0 && OUR_AGENTS.includes(String(raw.agentID || raw.ListAgentMlsId || '')),
       lastSync:     new Date().toISOString(),
  };
}

// ─── Main ──────────────────────────────────────────────────────────────────────

async function main() {
   console.log('=== IDX Broker Sync v5.3 ===');
   console.log(`Target: Queens, Brooklyn, Nassau, Suffolk — IDX ID: ${IDX_ID}`);
   console.log(`Time: ${new Date().toISOString()}\n`);

  const dataDir = path.join(__dirname, '..', 'data');
   if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

  let existing = [];
   if (fs.existsSync(OUT_FILE)) {
        try {
               const parsed = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8'));
               existing = Array.isArray(parsed) ? parsed : [];
        } catch(e) { existing = []; }
        console.log(`Loaded ${existing.length} existing listings from disk`);
   }

  // Step 1: Discover MLS components (diagnostic only)
  await discoverComponents();

  // Step 2: Bootstrap saved links (best-effort — skip gracefully on 400/403)
  await bootstrapSavedLinks();

  // Step 3–6: Pull from all sources
  const savedResults  = await fetchSavedLinkResults();
   const featured      = await fetchFeatured();
   const systemResults = await fetchSystemLinks();
   const directResults = await fetchDirectListings();

  // Merge and deduplicate
  console.log('\n[7] Merging and deduplicating...');
   const seen = new Map();
   // existing listings first (lowest priority — overwritten by fresh data)
  for (const l of existing) { if (l && l.id) seen.set(l.id, l); }
   // fresh data overrides
  for (const l of [...directResults, ...systemResults, ...savedResults, ...featured]) {
       if (l && l.id) seen.set(l.id, l);
  }
   const merged = Array.from(seen.values());

  console.log(`  Final unique listings: ${merged.length}`);
   console.log(`  Saved links:  ${savedResults.length}`);
   console.log(`  Featured:     ${featured.length}`);
   console.log(`  System links: ${systemResults.length}`);
   console.log(`  Direct:       ${directResults.length}`);
   console.log(`  Carried (disk): ${existing.length}`);

  // Sort: our listings first, then price desc
  merged.sort((a, b) => {
       if (a.isOurListing && !b.isOurListing) return -1;
       if (!a.isOurListing && b.isOurListing) return 1;
       return b.price - a.price;
  });

  fs.writeFileSync(OUT_FILE, JSON.stringify(merged, null, 2));
   console.log(`\n✓ Wrote ${merged.length} listings to ${OUT_FILE}`);

  const byCityMap = {};
   for (const l of merged) {
        const c = l.city || 'Unknown';
        byCityMap[c] = (byCityMap[c] || 0) + 1;
   }
   const topCities = Object.entries(byCityMap).sort((a, b) => b[1] - a[1]).slice(0, 15);
   if (topCities.length > 0) {
        console.log('\nTop cities:');
        for (const [city, count] of topCities) console.log(`  ${city}: ${count}`);
   }

  if (merged.length === 0) {
       // Warn but do NOT exit(1) — avoids blocking the commit step and lets
     // the carried-disk data remain. The API key may simply lack MLS read
     // permission on the savedlinks/results endpoints; that's an account
     // configuration issue, not a code error.
     console.warn('\n⚠ WARNING: 0 listings synced from API.');
       console.warn('Possible causes:');
       console.warn('  1. IDX Broker account savedlinks permission not enabled');
       console.warn('  2. API key needs "MLS" component access in IDX Broker dashboard');
       console.warn('  3. No active MLS listings in the configured areas');
       console.warn('Check https://middleware.idxbroker.com/mgmt/api-permissions');
  }
}

main().catch(err => {
   console.error('Fatal error:', err);
   process.exit(1);
});
