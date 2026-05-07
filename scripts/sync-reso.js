#!/usr/bin/env node
/**
  * sync-reso.js — IDX Broker API Sync v5 (5/6)
  * Full-power listing sync for Queens, Brooklyn, Nassau, Suffolk
  *
  * Strategy:
  *  1. GET /clients/listcomponents to discover MLS component IDs (cities, counties)
  *  2. POST /clients/savedlinks to create broad area saved searches (auto-bootstraps)
  *  3. GET /clients/savedlinks to enumerate all saved link UIDs
  *  4. GET /clients/results/{uid}?pageSize=500&page=N to paginate every saved link
  *  5. GET /clients/featured to always include agent-curated listings
  *  6. Deduplicate, enrich, write data/listings.json
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
                        } else {
                                   console.log(`  Response body: ${data.slice(0, 300)}`);
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
                        console.log(`  Response: ${data.slice(0, 400)}`);
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

// ─── Component discovery ─────────────────────────────────────────────────────

async function discoverComponents() {
   console.log('\n[1] Discovering MLS list components...');
   const components = await idxGet(`/clients/listcomponents/${IDX_ID}`);
   if (!components) {
        console.log('  Could not fetch listcomponents — will rely on existing saved links');
        return null;
   }
   console.log('  Component keys:', Object.keys(components).join(', '));
   return components;
}

// ─── Saved link bootstrap ────────────────────────────────────────────────────

const TARGET_AREAS = [
 { name: 'Queens NY',       city: 'Queens',    state: 'NY' },
 { name: 'Brooklyn NY',     city: 'Brooklyn',  state: 'NY' },
 { name: 'Nassau County NY',city: 'Nassau County', state: 'NY' },
 { name: 'Suffolk County NY',city: 'Suffolk County', state: 'NY' },
 { name: 'Long Island City NY', city: 'Long Island City', state: 'NY' },
 { name: 'Flushing NY',     city: 'Flushing',  state: 'NY' },
 { name: 'Jamaica NY',      city: 'Jamaica',   state: 'NY' },
 { name: 'Bayside NY',      city: 'Bayside',   state: 'NY' },
 { name: 'Forest Hills NY', city: 'Forest Hills', state: 'NY' },
 { name: 'Astoria NY',      city: 'Astoria',   state: 'NY' },
 ];

async function bootstrapSavedLinks(components) {
   console.log('\n[2] Checking/creating saved links...');

  // Get existing saved links
  const existing = await idxGet('/clients/savedlinks');
   const existingNames = new Set();
   const existingUids = [];

  if (existing && typeof existing === 'object') {
       const entries = Array.isArray(existing) ? existing : Object.values(existing);
       for (const link of entries) {
              if (link && link.linkName) existingNames.add(link.linkName);
              if (link && link.uid) existingUids.push(link.uid);
       }
       console.log(`  Found ${existingUids.length} existing saved links`);
  }

  // Try to find city component IDs from listcomponents
  let cityComponents = null;
   if (components) {
        // IDX Broker listcomponents returns city lists under various keys
     for (const key of ['cities', 'city', 'Cities']) {
            if (components[key]) { cityComponents = components[key]; break; }
     }
        // Sometimes it's nested under the IDX ID
     if (!cityComponents && components[IDX_ID]) {
            for (const key of ['cities', 'city', 'Cities']) {
                     if (components[IDX_ID][key]) { cityComponents = components[IDX_ID][key]; break; }
            }
     }
   }

  if (cityComponents) {
       console.log(`  City components available: ${Object.keys(cityComponents).length} cities`);
       // Log sample to understand structure
     const sample = Object.entries(cityComponents).slice(0, 5);
       for (const [k,v] of sample) console.log(`    ${k}: ${JSON.stringify(v)}`);
  }

  // Attempt to create saved links for each target area
  const created = [];
   for (const area of TARGET_AREAS) {
        if (existingNames.has(area.name)) {
               console.log(`  Skipping "${area.name}" — already exists`);
               continue;
        }

     // Build the queryString that IDX Broker expects
     // Format: idxID=c056&pt=res&a_propStatus[]=Active&a_city[]=Queens&hp=50000000&lp=0
     const queryString = [
            `idxID=${IDX_ID}`,
            `pt=sfr`,          // property type: single family (broadest)
            `a_propStatus[]=Active`,
            `a_city[]=${encodeURIComponent(area.city)}`,
            `a_stateOrProvince[]=${area.state}`,
            `hp=50000000`,
            `lp=0`,
          ].join('&');

     console.log(`  Creating saved link: "${area.name}"`);
        const result = await idxPost('/clients/savedlinks', {
               idxID:       IDX_ID,
               linkName:    area.name,
               queryString: queryString,
               linkTitle:   area.name,
               pageSize:    500,
        });

     if (result.status >= 200 && result.status < 300) {
            console.log(`  ✓ Created: "${area.name}"`);
            created.push(area.name);
            // Small delay to avoid rate limiting
          await new Promise(r => setTimeout(r, 500));
     } else {
            console.log(`  ✗ Failed to create "${area.name}": status ${result.status}`);

          // Try alternate property type formats
          const altQueryString = [
                   `idxID=${IDX_ID}`,
                   `pt=res`,
                   `a_propStatus[]=Active`,
                   `a_city[]=${encodeURIComponent(area.city)}`,
                   `hp=50000000`,
                   `lp=0`,
                 ].join('&');

          const result2 = await idxPost('/clients/savedlinks', {
                   idxID:       IDX_ID,
                   linkName:    area.name + ' (res)',
                   queryString: altQueryString,
                   linkTitle:   area.name,
          });
            if (result2.status >= 200 && result2.status < 300) {
                     console.log(`  ✓ Created with alt params: "${area.name}"`);
                     created.push(area.name);
            }
            await new Promise(r => setTimeout(r, 500));
     }
   }

  console.log(`  Created ${created.length} new saved links`);
   return created.length;
}

// ─── Fetch all results from saved links ──────────────────────────────────────

async function fetchSavedLinkResults() {
   console.log('\n[3] Fetching all saved link results...');
   const savedLinks = await idxGet('/clients/savedlinks');
   if (!savedLinks) { console.log('  No saved links found'); return []; }

  const links = Array.isArray(savedLinks) ? savedLinks : Object.values(savedLinks);
   console.log(`  Found ${links.length} saved links to process`);

  const allListings = [];
   const seen = new Set();

  for (const link of links) {
       const uid = link.uid || link.linkUID;
       if (!uid) continue;
       console.log(`  Fetching results for link: ${link.linkName || uid}`);

     let page = 1;
       let keepGoing = true;
       while (keepGoing) {
              const results = await idxGet(`/clients/results/${uid}?pageSize=500&page=${page}`);
              if (!results) { keepGoing = false; break; }

         // Results can be an object keyed by listing ID, or an array
         const listings = Array.isArray(results) ? results : Object.values(results);
              if (listings.length === 0) { keepGoing = false; break; }

         console.log(`    Page ${page}: ${listings.length} listings`);

         for (const listing of listings) {
                  const id = listing.listingID || listing.idxID || listing.mlsID || listing.listingId;
                  if (id && !seen.has(id)) {
                             seen.add(id);
                             allListings.push(normalise(listing));
                  }
         }

         // If we got fewer than 500, we're on the last page
         if (listings.length < 500) { keepGoing = false; } else { page++; }
              await new Promise(r => setTimeout(r, 200)); // rate limit
       }
  }

  console.log(`  Total unique listings from saved links: ${allListings.length}`);
   return allListings;
}

// ─── Fetch featured listings ──────────────────────────────────────────────────

async function fetchFeatured() {
   console.log('\n[4] Fetching featured listings...');
   const data = await idxGet('/clients/featured');
   if (!data) return [];

  const listings = Array.isArray(data) ? data : Object.values(data);
   console.log(`  Featured listings: ${listings.length}`);
   return listings.map(normalise);
}

// ─── Fetch properties endpoint (fallback) ────────────────────────────────────

async function fetchProperties() {
   console.log('\n[5] Trying /clients/properties endpoint...');
   const data = await idxGet(`/clients/properties/${IDX_ID}`);
   if (!data) {
        console.log('  /clients/properties not available');
        return [];
   }
   const listings = Array.isArray(data) ? data : Object.values(data);
   console.log(`  Properties endpoint returned: ${listings.length}`);
   return listings.map(normalise);
}

// ─── Fetch search results directly ───────────────────────────────────────────

async function fetchSearchResults() {
   console.log('\n[6] Trying direct search endpoints...');
   const allListings = [];
   const seen = new Set();

  // Try the /clients/listing endpoint (requires ancillarykey but worth trying)
  const listingData = await idxGet('/clients/listing');
   if (listingData) {
        const listings = Array.isArray(listingData) ? listingData : Object.values(listingData);
        console.log(`  /clients/listing returned: ${listings.length}`);
        for (const l of listings) {
               const id = l.listingID || l.idxID || l.mlsID;
               if (id && !seen.has(id)) { seen.add(id); allListings.push(normalise(l)); }
        }
   }

  // Try systemlinks as another source of saved searches
  const systemLinks = await idxGet('/clients/systemlinks');
   if (systemLinks) {
        const links = Array.isArray(systemLinks) ? systemLinks : Object.values(systemLinks);
        console.log(`  System links found: ${links.length}`);
        for (const link of links) {
               const uid = link.uid || link.linkUID;
               if (!uid) continue;
               const results = await idxGet(`/clients/results/${uid}?pageSize=500`);
               if (results) {
                        const listings = Array.isArray(results) ? results : Object.values(results);
                        console.log(`    System link ${uid}: ${listings.length} listings`);
                        for (const l of listings) {
                                   const id = l.listingID || l.idxID || l.mlsID;
                                   if (id && !seen.has(id)) { seen.add(id); allListings.push(normalise(l)); }
                        }
               }
               await new Promise(r => setTimeout(r, 200));
        }
   }

  return allListings;
}

// ─── Normalise a listing to consistent shape ──────────────────────────────────

function normalise(raw) {
   const price = parseInt(
        (raw.listPrice || raw.ListPrice || raw.currentPrice || raw.price || '0')
          .toString().replace(/[^0-9]/g, ''), 10
      ) || 0;

  const address = [
       raw.address     || raw.streetNumber && `${raw.streetNumber} ${raw.streetName}` || '',
       raw.city        || raw.cityName || '',
       raw.state       || raw.stateOrProvince || 'NY',
       raw.zipcode     || raw.postalCode || '',
     ].filter(Boolean).join(', ');

  // Photo handling — IDX Broker returns image URLs in multiple formats
  const photos = [];
   if (raw.image && raw.image.url)        photos.push(raw.image.url);
   if (raw.image && typeof raw.image === 'string') photos.push(raw.image);
   if (raw.photos && Array.isArray(raw.photos)) photos.push(...raw.photos.map(p => p.url || p));
   if (raw.mainPhoto)                     photos.push(raw.mainPhoto);
   if (raw.photo)                         photos.push(raw.photo);
   if (photos.length === 0)               photos.push('/assets/images/placeholder.jpg');

  // Slug generation
  const slugBase = [
       (raw.address || raw.streetName || '').replace(/[^a-z0-9]+/gi, '-'),
       (raw.city || raw.cityName || 'ny').replace(/[^a-z0-9]+/gi, '-'),
       (raw.listingID || raw.idxID || raw.mlsID || Math.random().toString(36).slice(2)),
     ].join('-').toLowerCase().replace(/-+/g, '-').replace(/^-|-$/g, '');

  return {
       id:           raw.listingID || raw.idxID || raw.mlsID || raw.listingId || '',
       slug:         slugBase,
       address:      address,
       city:         raw.city     || raw.cityName        || '',
       state:        raw.state    || raw.stateOrProvince  || 'NY',
       zip:          raw.zipcode  || raw.postalCode       || '',
       county:       raw.county   || raw.countyOrParish   || '',
       price:        price,
       beds:         parseInt(raw.bedrooms   || raw.BedroomsTotal   || raw.beds  || 0, 10),
       baths:        parseFloat(raw.bathrooms || raw.BathroomsTotalDecimal || raw.baths || 0),
       sqft:         parseInt(raw.sqft       || raw.LivingArea       || raw.squareFeet || 0, 10),
       lotSize:      raw.lotSize  || raw.LotSizeAcres      || '',
       yearBuilt:    parseInt(raw.yearBuilt  || raw.YearBuilt        || 0, 10) || null,
       propType:     raw.propType || raw.PropertyType      || raw.propertyType || '',
       status:       raw.propStatus || raw.StandardStatus  || raw.status || 'Active',
       description:  raw.remarksConcat || raw.PublicRemarks || raw.description || '',
       photos:       photos,
       lat:          parseFloat(raw.latitude  || raw.Latitude  || 0) || null,
       lng:          parseFloat(raw.longitude || raw.Longitude || 0) || null,
       mlsNumber:    raw.listingID || raw.mlsNumber || raw.ListingId || '',
       agentID:      raw.agentID  || raw.ListAgentMlsId || '',
       isOurListing: OUR_AGENTS.length > 0 &&
                          OUR_AGENTS.includes(raw.agentID || raw.ListAgentMlsId || ''),
       lastSync:     new Date().toISOString(),
  };
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
   console.log('=== IDX Broker Sync v5 (5/6) ===');
   console.log(`Target: Queens, Brooklyn, Nassau, Suffolk — IDX ID: ${IDX_ID}`);
   console.log(`Time: ${new Date().toISOString()}\n`);

  // Ensure output directory exists
  const dataDir = path.join(__dirname, '..', 'data');
   if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

  // Load existing listings as a safety net
  let existing = [];
   if (fs.existsSync(OUT_FILE)) {
        try { existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8')); }
        catch(e) { existing = []; }
        console.log(`Loaded ${existing.length} existing listings from disk`);
   }

  // Step 1: Discover MLS components (for saved link creation)
  const components = await discoverComponents();

  // Step 2: Bootstrap saved links for our target areas
  await bootstrapSavedLinks(components);

  // Step 3: Pull all saved link results
  const savedResults = await fetchSavedLinkResults();

  // Step 4: Pull featured listings
  const featured = await fetchFeatured();

  // Step 5: Try /clients/properties
  const properties = await fetchProperties();

  // Step 6: Try other endpoints
  const searchResults = await fetchSearchResults();

  // Merge everything, deduplicate by listing ID
  console.log('\n[7] Merging and deduplicating...');
   const seen = new Map();

  // Existing listings are lowest priority (overwritten by fresh data)
  for (const l of existing) {
       if (l.id) seen.set(l.id, l);
  }
   // Fresh data overwrites
  for (const l of [...searchResults, ...properties, ...savedResults, ...featured]) {
       if (l.id) seen.set(l.id, l);
  }

  const merged = Array.from(seen.values());
   console.log(`  Final unique listings: ${merged.length}`);
   console.log(`    From saved links:  ${savedResults.length}`);
   console.log(`    From featured:     ${featured.length}`);
   console.log(`    From properties:   ${properties.length}`);
   console.log(`    From search:       ${searchResults.length}`);
   console.log(`    Carried from disk: ${existing.length}`);

  // Sort: our listings first, then by price desc
  merged.sort((a, b) => {
       if (a.isOurListing && !b.isOurListing) return -1;
       if (!a.isOurListing && b.isOurListing)  return 1;
       return b.price - a.price;
  });

  // Write output
  fs.writeFileSync(OUT_FILE, JSON.stringify(merged, null, 2));
   console.log(`\n✓ Wrote ${merged.length} listings to ${OUT_FILE}`);

  // Summary by city
  const byCityMap = {};
   for (const l of merged) {
        const c = l.city || 'Unknown';
        byCityMap[c] = (byCityMap[c] || 0) + 1;
   }
   const topCities = Object.entries(byCityMap)
     .sort((a,b) => b[1]-a[1])
     .slice(0, 15);
   console.log('\nTop cities:');
   for (const [city, count] of topCities) {
        console.log(`  ${city}: ${count}`);
   }

  if (merged.length === 0) {
       console.error('\n⚠ WARNING: 0 listings synced. Check API key and saved links in IDX Broker dashboard.');
       process.exit(1);
  }
}

main().catch(err => {
   console.error('Fatal error:', err);
   process.exit(1);
});
