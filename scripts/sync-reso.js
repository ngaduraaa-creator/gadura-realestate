———───────────────────────────────────────────────────────────────→—→──────────────────────────────────────────────────────—───────────────────────────────────────────────────────────—→—────────────────────────────────────────────────────────✓✗—────────────────────────────────────────────────────→───────────────────────────────────────────────────────────────────────────────────────────────────────────────→───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────✓—⚠—#!/usr/bin/env node
/**
  * sync-reso.js — IDX Broker API Sync v5.1 (5/6)
  * Full-power listing sync for Queens, Brooklyn, Nassau, Suffolk
  *
  * Fixes vs v5:
  *  - null-guard in normalise() (featured endpoint wraps listings in object with null entries)
  *  - properly filter null values from all listing arrays
  *  - fixed existing-listings load (was reading array length as 'undefined')
  *  - log full listcomponents structure to diagnose IDX IDs
  *  - improved savedlinks POST: try multiple parameter combinations to find correct format
  */
'use strict';

const https    = require('https');
const fs       = require('fs');
const path     = require('path');

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

// ─── HTTP helpers ────────────────────────────────────────────────────────────

function idxGet(endpoint) {
   return new Promise((resolve, reject) => {
        const options = {
               hostname: API_BASE,
               path:     endpoint,
               method:   'GET',
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

function idxPost(endpoint, formData) {
   return new Promise((resolve, reject) => {
        const postData = Object.entries(formData)
          .map(([k,v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
          .join('&');
        const options = {
               hostname: API_BASE,
               path:     endpoint,
               method:   'POST',
               headers: {
                        accesskey:         API_KEY,
                        outputtype:        'json',
                        apiversion:        API_VER,
                        'Content-Type':    'application/x-www-form-urlencoded',
                        'Content-Length':  Buffer.byteLength(postData),
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

// ─── Safe listing extractor (handles objects, arrays, nulls) ─────────────────

function extractListings(data) {
   if (!data) return [];
   const raw = Array.isArray(data) ? data : Object.values(data);
   return raw.filter(item => item && typeof item === 'object');
}

// ─── Component discovery ─────────────────────────────────────────────────────

async function discoverComponents() {
   console.log('\n[1] Discovering MLS list components...');

  // Try with IDX ID suffix
  let components = await idxGet(`/clients/listcomponents/${IDX_ID}`);
   if (!components) {
        // Try without IDX ID
     components = await idxGet('/clients/listcomponents');
   }
   if (!components) {
        console.log('  listcomponents unavailable — will rely on existing saved links');
        return null;
   }

  // Log full structure for debugging
  const compStr = JSON.stringify(components).slice(0, 2000);
   console.log('  listcomponents structure:', compStr);

  return components;
}

// ─── Saved link bootstrap ────────────────────────────────────────────────────

const TARGET_AREAS = [
 { name: 'Queens NY',            city: 'Queens' },
 { name: 'Brooklyn NY',          city: 'Brooklyn' },
 { name: 'Flushing NY',          city: 'Flushing' },
 { name: 'Jamaica NY',           city: 'Jamaica' },
 { name: 'Bayside NY',           city: 'Bayside' },
 { name: 'Forest Hills NY',      city: 'Forest Hills' },
 { name: 'Astoria NY',           city: 'Astoria' },
 { name: 'Long Island City NY',  city: 'Long Island City' },
 { name: 'Ridgewood NY',         city: 'Ridgewood' },
 { name: 'Jackson Heights NY',   city: 'Jackson Heights' },
 ];

// Different query string formats to try when POSTing saved links
function buildQueryVariants(city) {
   return [
        // Variant 1: standard city search with sfr property type
        `idxID=${IDX_ID}&pt=sfr&a_propStatus[]=Active&a_city[]=${encodeURIComponent(city)}&hp=50000000&lp=0`,
        // Variant 2: res property type
        `idxID=${IDX_ID}&pt=res&a_propStatus[]=Active&a_city[]=${encodeURIComponent(city)}&hp=50000000&lp=0`,
        // Variant 3: no property type filter
        `idxID=${IDX_ID}&a_propStatus[]=Active&a_city[]=${encodeURIComponent(city)}&hp=50000000&lp=0`,
        // Variant 4: city without encoding (some APIs want raw)
        `idxID=${IDX_ID}&pt=res&a_city[]=${city}&hp=50000000&lp=0`,
        // Variant 5: minimal — just city
        `idxID=${IDX_ID}&a_city[]=${encodeURIComponent(city)}`,
      ];
}

async function bootstrapSavedLinks(components) {
   console.log('\n[2] Checking/creating saved links...');

  // Get existing saved links
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

  // Try to find city-based components from listcomponents result
  // IDX Broker returns array with [citiesObj, countiesObj, propertyTypesObj] or similar
  let cityMap = null;
   if (components) {
        const vals = Array.isArray(components) ? components : Object.values(components);
        for (const val of vals) {
               if (val && typeof val === 'object' && !Array.isArray(val)) {
                        const keys = Object.keys(val);
                        if (keys.length > 5) {
                                   console.log(`  Possible city map found (${keys.length} keys), first 5: ${keys.slice(0,5).join(', ')}`);
                                   cityMap = val;
                                   break;
                        }
               }
        }
   }

  let created = 0;
   for (const area of TARGET_AREAS) {
        if (existingNames.has(area.name)) {
               console.log(`  Skipping "${area.name}" — already exists`);
               continue;
        }

     let succeeded = false;
        const variants = buildQueryVariants(area.city);

     for (let i = 0; i < variants.length; i++) {
            const queryString = variants[i];
            console.log(`  Trying variant ${i+1} for "${area.name}": ${queryString.slice(0, 80)}`);

          const result = await idxPost('/clients/savedlinks', {
                   idxID:       IDX_ID,
                   linkName:    area.name,
                   queryString: queryString,
                   linkTitle:   area.name,
          });

          if (result.status >= 200 && result.status < 300) {
                   console.log(`  ✓ Created: "${area.name}" (variant ${i+1})`);
                   created++;
                   succeeded = true;
                   break;
          }

          await new Promise(r => setTimeout(r, 300));
     }

     if (!succeeded) {
            console.log(`  ✗ All variants failed for "${area.name}"`);
     }
   }

  console.log(`  Created ${created} new saved links`);
   return created;
}

// ─── Fetch all results from saved links ──────────────────────────────────────

async function fetchSavedLinkResults() {
   console.log('\n[3] Fetching all saved link results...');
   const savedData = await idxGet('/clients/savedlinks');
   if (!savedData) { console.log('  No saved links (204)'); return []; }

  const links = extractListings(savedData);
   console.log(`  Found ${links.length} saved links to process`);

  const allListings = [];
   const seen = new Set();

  for (const link of links) {
       const uid = link.uid || link.linkUID;
       if (!uid) { console.log(`  Skipping link without uid: ${JSON.stringify(link).slice(0,100)}`); continue; }
       console.log(`  Fetching: "${link.linkName || uid}" (uid=${uid})`);

     let page = 1;
       let keepGoing = true;
       while (keepGoing) {
              const results = await idxGet(`/clients/results/${uid}?pageSize=500&page=${page}`);
              if (!results) { keepGoing = false; break; }

         const listings = extractListings(results);
              if (listings.length === 0) { keepGoing = false; break; }

         console.log(`    Page ${page}: ${listings.length} listings`);

         for (const listing of listings) {
                  const id = listing.listingID || listing.idxID || listing.mlsID || listing.listingId;
                  if (id && !seen.has(id)) {
                             seen.add(id);
                             const n = normalise(listing);
                             if (n) allListings.push(n);
                  }
         }

         if (listings.length < 500) { keepGoing = false; } else { page++; }
              await new Promise(r => setTimeout(r, 200));
       }
  }

  console.log(`  Total from saved links: ${allListings.length}`);
   return allListings;
}

// ─── Fetch featured listings ──────────────────────────────────────────────────

async function fetchFeatured() {
   console.log('\n[4] Fetching featured listings...');
   const data = await idxGet('/clients/featured');
   if (!data) return [];

  const listings = extractListings(data);
   console.log(`  Featured raw count: ${listings.length}`);

  // Log structure of first listing for debugging
  if (listings.length > 0) {
       console.log('  Sample listing keys:', Object.keys(listings[0]).join(', '));
       console.log('  Sample listing:', JSON.stringify(listings[0]).slice(0, 400));
  }

  const normalised = listings.map(normalise).filter(Boolean);
   console.log(`  Featured after normalise: ${normalised.length}`);
   return normalised;
}

// ─── Fetch systemlinks results ────────────────────────────────────────────────

async function fetchSystemLinks() {
   console.log('\n[5] Checking system links...');
   const data = await idxGet('/clients/systemlinks');
   if (!data) { console.log('  No system links'); return []; }

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
              console.log(`    System link "${link.linkName || uid}": ${listings.length} listings`);
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

// ─── Fetch via /clients/listing (ancillarykey tier) ──────────────────────────

async function fetchDirectListings() {
   console.log('\n[6] Trying /clients/listing (ancillary tier)...');
   const data = await idxGet('/clients/listing');
   if (!data) { console.log('  Not available (expected for standard accounts)'); return []; }

  const listings = extractListings(data);
   console.log(`  Direct listings: ${listings.length}`);
   return listings.map(normalise).filter(Boolean);
}

// ─── Normalise a listing to consistent shape ──────────────────────────────────

function normalise(raw) {
   // Guard against null/undefined entries (IDX Broker wraps in objects with null values)
  if (!raw || typeof raw !== 'object') return null;

  const price = parseInt(
       String(raw.listPrice || raw.ListPrice || raw.currentPrice || raw.price || '0')
         .replace(/[^0-9]/g, ''), 10
     ) || 0;

  // Build address from available fields
  let addrParts = [];
   if (raw.address) {
        addrParts.push(raw.address);
   } else if (raw.streetNumber || raw.streetName) {
        addrParts.push([raw.streetNumber, raw.streetName].filter(Boolean).join(' '));
   }
   const city  = raw.city || raw.cityName || '';
   const state = raw.state || raw.stateOrProvince || 'NY';
   const zip   = raw.zipcode || raw.postalCode || '';
   if (city)  addrParts.push(city);
   if (state) addrParts.push(state);
   if (zip)   addrParts.push(zip);
   const address = addrParts.join(', ');

  // Photo handling
  const photos = [];
   if (raw.image) {
        if (typeof raw.image === 'string') photos.push(raw.image);
        else if (raw.image.url)            photos.push(raw.image.url);
   }
   if (raw.mainPhoto) photos.push(raw.mainPhoto);
   if (raw.photo)     photos.push(raw.photo);
   if (Array.isArray(raw.photos)) {
        for (const p of raw.photos) photos.push(typeof p === 'string' ? p : p.url || p.src || '');
   }
   // IDX Broker sometimes uses image0, image1... keys
  for (let i = 0; i <= 20; i++) {
       const key = `image${i}`;
       if (raw[key]) photos.push(typeof raw[key] === 'string' ? raw[key] : raw[key].url || '');
  }
   const cleanPhotos = [...new Set(photos.filter(p => p && typeof p === 'string' && p.startsWith('http')))];
   if (cleanPhotos.length === 0) cleanPhotos.push('/assets/images/placeholder.jpg');

  // Slug generation
  const addrSlug = (raw.address || raw.streetName || '').replace(/[^a-z0-9]+/gi, '-').toLowerCase();
   const citySlug = city.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
   const idPart   = (raw.listingID || raw.idxID || raw.mlsID || raw.listingId || '').toString();
   const slug = [addrSlug, citySlug, idPart]
     .filter(Boolean).join('-').replace(/-+/g, '-').replace(/^-|-$/g, '');

  return {
       id:           String(raw.listingID || raw.idxID || raw.mlsID || raw.listingId || ''),
       slug:         slug,
       address:      address,
       city:         city,
       state:        state,
       zip:          zip,
       county:       raw.county || raw.countyOrParish || '',
       price:        price,
       beds:         parseInt(raw.bedrooms   || raw.BedroomsTotal   || raw.beds   || 0, 10),
       baths:        parseFloat(raw.bathrooms || raw.BathroomsTotalDecimal || raw.baths || 0),
       sqft:         parseInt(raw.sqft       || raw.LivingArea       || raw.squareFeet || 0, 10),
       lotSize:      String(raw.lotSize || raw.LotSizeAcres || ''),
       yearBuilt:    parseInt(raw.yearBuilt  || raw.YearBuilt        || 0, 10) || null,
       propType:     String(raw.propType || raw.PropertyType || raw.propertyType || ''),
       status:       String(raw.propStatus || raw.StandardStatus || raw.status || 'Active'),
       description:  String(raw.remarksConcat || raw.PublicRemarks || raw.description || ''),
       photos:       cleanPhotos,
       lat:          parseFloat(raw.latitude  || raw.Latitude  || 0) || null,
       lng:          parseFloat(raw.longitude || raw.Longitude || 0) || null,
       mlsNumber:    String(raw.listingID || raw.mlsNumber || raw.ListingId || ''),
       agentID:      String(raw.agentID   || raw.ListAgentMlsId || ''),
       isOurListing: OUR_AGENTS.length > 0 &&
                          OUR_AGENTS.includes(String(raw.agentID || raw.ListAgentMlsId || '')),
       lastSync:     new Date().toISOString(),
  };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
   console.log('=== IDX Broker Sync v5.1 (5/6) ===');
   console.log(`Target: Queens, Brooklyn, Nassau, Suffolk — IDX ID: ${IDX_ID}`);
   console.log(`Time: ${new Date().toISOString()}\n`);

  // Ensure output directory
  const dataDir = path.join(__dirname, '..', 'data');
   if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

  // Load existing listings as safety net
  let existing = [];
   if (fs.existsSync(OUT_FILE)) {
        try {
               const parsed = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8'));
               existing = Array.isArray(parsed) ? parsed : [];
        } catch(e) { existing = []; }
        console.log(`Loaded ${existing.length} existing listings from disk`);
   }

  // Step 1: Discover MLS components
  const components = await discoverComponents();

  // Step 2: Bootstrap saved links
  await bootstrapSavedLinks(components);

  // Step 3: Pull saved link results
  const savedResults = await fetchSavedLinkResults();

  // Step 4: Featured listings
  const featured = await fetchFeatured();

  // Step 5: System links
  const systemResults = await fetchSystemLinks();

  // Step 6: Direct listing endpoint
  const directResults = await fetchDirectListings();

  // Merge and deduplicate
  console.log('\n[7] Merging and deduplicating...');
   const seen = new Map();

  for (const l of existing) {
       if (l && l.id) seen.set(l.id, l);
  }
   for (const l of [...directResults, ...systemResults, ...savedResults, ...featured]) {
        if (l && l.id) seen.set(l.id, l);
   }

  const merged = Array.from(seen.values());
   console.log(`  Final unique listings: ${merged.length}`);
   console.log(`    Saved links:    ${savedResults.length}`);
   console.log(`    Featured:       ${featured.length}`);
   console.log(`    System links:   ${systemResults.length}`);
   console.log(`    Direct:         ${directResults.length}`);
   console.log(`    Carried (disk): ${existing.length}`);

  // Sort: our listings first, then price desc
  merged.sort((a, b) => {
       if (a.isOurListing && !b.isOurListing) return -1;
       if (!a.isOurListing && b.isOurListing)  return 1;
       return b.price - a.price;
  });

  // Write output
  fs.writeFileSync(OUT_FILE, JSON.stringify(merged, null, 2));
   console.log(`\n✓ Wrote ${merged.length} listings to ${OUT_FILE}`);

  // City breakdown
  const byCityMap = {};
   for (const l of merged) {
        const c = l.city || 'Unknown';
        byCityMap[c] = (byCityMap[c] || 0) + 1;
   }
   const topCities = Object.entries(byCityMap).sort((a,b) => b[1]-a[1]).slice(0, 15);
   console.log('\nTop cities:');
   for (const [city, count] of topCities) console.log(`  ${city}: ${count}`);

  if (merged.length === 0) {
       console.error('\n⚠ WARNING: 0 listings synced.');
       console.error('Next steps:');
       console.error('  1. Check if IDX Broker account has saved searches in the dashboard');
       console.error('  2. Verify API key permissions');
       console.error('  3. Check listcomponents output above to find correct MLS city IDs');
       process.exit(1);
  }
}

main().catch(err => {
   console.error('Fatal error:', err);
   process.exit(1);
});
