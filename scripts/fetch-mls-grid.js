#!/usr/bin/env node
/**
 * Gadura Real Estate — MLS GRID Listings Fetcher
 * ================================================
 * Data source: MLS GRID (https://mlsgrid.com) — the official RESO API feed for
 * OneKey® MLS, the same source KW.com and major portals use.
 *
 * Setup:
 *   1. Apply at https://mlsgrid.com  (requires OneKey® MLS membership)
 *   2. Get your Bearer token from the MLS GRID dashboard
 *   3. Add MLSGRID_TOKEN as a GitHub Secret (Settings → Secrets → Actions)
 *   4. This script runs automatically via .github/workflows/update-listings.yml
 *
 * Run manually:
 *   MLSGRID_TOKEN=your_token node scripts/fetch-mls-grid.js
 */

'use strict';

const https = require('https');
const fs    = require('fs');
const path  = require('path');

// ─── Credentials & config ─────────────────────────────────────────────────────
const TOKEN        = process.env.MLSGRID_TOKEN;
const DATA_FILE    = path.join(__dirname, '..', 'data', 'listings.json');
const ORIGINATING_SYSTEM = 'onekey2';  // OneKey® MLS identifier in MLS GRID
const MAX_PER_PAGE = 500;
const MAX_PRICE    = 3500000;
const MIN_PRICE    = 450000;

// ─── Target geographies ───────────────────────────────────────────────────────
const QUEENS_CITIES = [
  'Ozone Park', 'South Ozone Park', 'Richmond Hill', 'South Richmond Hill',
  'Jamaica', 'Jamaica Estates', 'Woodhaven', 'Glendale', 'Middle Village',
  'Queens Village', 'Cambria Heights', 'Springfield Gardens', 'St. Albans',
  'Rosedale', 'Howard Beach', 'Kew Gardens', 'Forest Hills', 'Briarwood',
  'Hollis', 'Fresh Meadows', 'Maspeth', 'Rego Park', 'Jackson Heights',
  'Elmhurst', 'Corona', 'Bayside', 'Flushing', 'Whitestone', 'College Point',
  'Rockaway Beach', 'Far Rockaway', 'Laurelton', 'Queens Village',
  'Floral Park', 'Glen Oaks', 'Bellrose', 'Bellerose'
];

// Brooklyn neighborhoods that appear in OneKey® MLS as "Brooklyn" city
// We'll also filter by ZIP code for accuracy
const BROOKLYN_ZIPS = [
  '11207', '11208', '11203', '11210', '11212', '11236',
  '11221', '11233', '11216', '11225', '11226', '11213',
  '11205', '11220', '11219', '11228', '11204', '11223',
  '11224', '11229', '11230', '11231', '11232', '11234',
  '11235', '11237', '11238', '11239'
];

const LI_CITIES = [
  'Elmont', 'Valley Stream', 'Hempstead', 'Freeport', 'Lynbrook',
  'Baldwin', 'Rockville Centre', 'Merrick', 'Far Rockaway',
  'North Valley Stream', 'Lakeview', 'Roosevelt', 'Uniondale',
  'Garden City', 'West Hempstead', 'Floral Park', 'New Hyde Park',
  'East Meadow', 'Westbury', 'Carle Place', 'Mineola', 'Levittown',
  'Oceanside', 'Island Park', 'Long Beach', 'Cedarhurst', 'Lawrence',
  'Hewlett', 'Woodmere', 'Woodsburgh', 'Malverne', 'East Rockaway'
];

// RESO fields to request
const SELECT_FIELDS = [
  'ListingId', 'ListPrice', 'OriginalListPrice',
  'BedroomsTotal', 'BathroomsTotal', 'BathroomsFull', 'BathroomsHalf',
  'LivingArea', 'LotSizeArea', 'LotSizeUnits',
  'PropertyType', 'PropertySubType', 'StandardStatus',
  'City', 'StateOrProvince', 'PostalCode', 'CountyOrParish',
  'StreetNumber', 'StreetDirPrefix', 'StreetName', 'StreetSuffix', 'UnitNumber',
  'ListAgentFullName', 'ListAgentDirectPhone', 'ListAgentEmail',
  'ListOfficeName', 'ListOfficePhone',
  'Latitude', 'Longitude',
  'DaysOnMarket', 'CumulativeDaysOnMarket',
  'PublicRemarks', 'YearBuilt', 'ParkingTotal',
  'ListingContractDate', 'ModificationTimestamp',
  'OriginatingSystemName', 'OriginatingSystemID',
  'MediaChangeTimestamp'
].join(',');

// ─── HTTP helpers ─────────────────────────────────────────────────────────────
function fetchJSON(url, token) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
        'User-Agent': 'GaduraRealEstate/1.0 (listings-sync)'
      }
    };
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 401) { reject(new Error('Unauthorized — check MLSGRID_TOKEN')); return; }
        if (res.statusCode === 403) { reject(new Error('Forbidden — token may not have access to this MLS')); return; }
        if (res.statusCode === 429) { reject(new Error('Rate limited — try again later')); return; }
        if (res.statusCode >= 400) { reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 300)}`)); return; }
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('JSON parse error: ' + e.message + '\nRaw: ' + data.slice(0, 200))); }
      });
    }).on('error', reject);
  });
}

// ─── Build OData filter string ────────────────────────────────────────────────
function buildCityFilter(cities) {
  return cities.map(c => `City eq '${c.replace(/'/g, "''")}'`).join(' or ');
}

function buildZipFilter(zips) {
  return zips.map(z => `PostalCode eq '${z}'`).join(' or ');
}

function buildBaseFilter(geoFilter) {
  return `OriginatingSystemName eq '${ORIGINATING_SYSTEM}' and StandardStatus eq 'Active' and ListPrice ge ${MIN_PRICE} and ListPrice le ${MAX_PRICE} and (${geoFilter})`;
}

// ─── Paginated fetch ──────────────────────────────────────────────────────────
async function fetchAllPages(filter, label) {
  const results = [];
  let skip = 0;

  while (true) {
    const url = [
      'https://api.mlsgrid.com/v2/Property',
      `?$filter=${encodeURIComponent(filter)}`,
      `&$top=${MAX_PER_PAGE}`,
      `&$skip=${skip}`,
      `&$select=${encodeURIComponent(SELECT_FIELDS)}`,
      '&$expand=Media($select=MediaURL,Order,MediaCategory)',  // include photos
      '&$orderby=DaysOnMarket asc'
    ].join('');

    console.log(`[${label}] Fetching page (skip=${skip})…`);
    let data;
    try {
      data = await fetchJSON(url, TOKEN);
    } catch (e) {
      console.warn(`[${label}] Fetch error at skip=${skip}:`, e.message);
      break;
    }

    const page = data.value || [];
    console.log(`[${label}]   Got ${page.length} records`);
    results.push(...page);

    // Stop if we got fewer than a full page (no more data)
    if (page.length < MAX_PER_PAGE) break;
    skip += MAX_PER_PAGE;

    // Safety: don't fetch more than 5000 records per market
    if (results.length >= 5000) { console.warn(`[${label}] Hit 5000 record cap`); break; }
  }

  console.log(`[${label}] Total: ${results.length} listings`);
  return results;
}

// ─── Transform RESO record → listings.json entry ─────────────────────────────
function transform(p, marketPrefix) {
  // Build address string
  const parts = [p.StreetNumber, p.StreetDirPrefix, p.StreetName, p.StreetSuffix, p.UnitNumber ? `#${p.UnitNumber}` : ''];
  const address = parts.filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();

  // Normalize baths
  const baths = p.BathroomsTotal
    || ((p.BathroomsFull || 0) + (p.BathroomsHalf ? 0.5 : 0))
    || 0;

  // Normalize property type
  const type = normalizeType(p.PropertyType, p.PropertySubType);

  // Badge
  const dom = p.DaysOnMarket || 0;
  const badge = dom <= 3 ? 'Just Listed' : dom <= 14 ? 'New' : '';

  return {
    id: `${marketPrefix}-${p.ListingId}`,
    mlsNumber: p.ListingId || '',
    address,
    city: p.City || '',
    state: p.StateOrProvince || 'NY',
    zip: p.PostalCode || '',
    price: p.ListPrice || 0,
    beds: p.BedroomsTotal || 0,
    baths,
    sqft: p.LivingArea || null,
    lotSize: p.LotSizeArea ? `${p.LotSizeArea} ${p.LotSizeUnits || 'sqft'}` : null,
    type,
    status: p.StandardStatus || 'Active',
    badge,
    photo: getPrimaryPhoto(p.Media),
    photos: getPhotos(p.Media),
    url: `contact.html`,
    description: (p.PublicRemarks || '').trim().substring(0, 400),
    agent: p.ListAgentFullName || '',
    agentPhone: p.ListAgentDirectPhone || '',
    brokerage: p.ListOfficeName || '',
    source: 'OneKey® MLS',
    neighborhood: p.City || '',
    lat: p.Latitude || null,
    lng: p.Longitude || null,
    yearBuilt: p.YearBuilt || null,
    parking: p.ParkingTotal || null,
    daysOnMarket: dom,
    listedDate: p.ListingContractDate || null,
    updatedAt: new Date().toISOString()
  };
}

function getPrimaryPhoto(media) {
  if (!Array.isArray(media) || media.length === 0) return null;
  // Sort by Order ascending, pick first
  const sorted = [...media].sort((a, b) => (a.Order || 0) - (b.Order || 0));
  return sorted[0].MediaURL || null;
}

function getPhotos(media) {
  if (!Array.isArray(media) || media.length === 0) return [];
  return [...media]
    .sort((a, b) => (a.Order || 0) - (b.Order || 0))
    .map(m => m.MediaURL)
    .filter(Boolean)
    .slice(0, 10);
}

function normalizeType(propertyType, subType) {
  const t = (propertyType  || '').toLowerCase();
  const s = (subType       || '').toLowerCase();
  if (s.includes('triplex'))                                          return 'Triplex';
  if (s.includes('duplex') || s.includes('two family') || s.includes('2 family') || t.includes('multi'))
                                                                      return '2-Family';
  if (s.includes('condominium') || s.includes('condo'))               return 'Condo';
  if (s.includes('co-op') || s.includes('cooperative'))               return 'Co-Op';
  if (s.includes('townhouse') || s.includes('town house'))            return 'Townhouse';
  if (t.includes('commercial') || t.includes('mixed'))                return 'Mixed Use';
  return '1-Family';
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log('\n════════════════════════════════════════════════');
  console.log('Gadura Real Estate — MLS GRID Fetch');
  console.log('Started:', new Date().toISOString());
  console.log('════════════════════════════════════════════════\n');

  if (!TOKEN) {
    console.error('ERROR: MLSGRID_TOKEN environment variable not set.');
    console.error('');
    console.error('To get your token:');
    console.error('  1. Apply at https://mlsgrid.com (requires OneKey® MLS membership)');
    console.error('  2. Add MLSGRID_TOKEN as a GitHub Secret:');
    console.error('     → Your repo → Settings → Secrets → Actions → New secret');
    console.error('');
    process.exit(1);
  }

  // Load existing data (preserve activeListings + soldListings which are manually managed)
  const existing = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));

  // ── Fetch in parallel ──
  const [queensRaw, brooklynRaw, liRaw] = await Promise.all([
    fetchAllPages(buildBaseFilter(buildCityFilter(QUEENS_CITIES)), 'Queens')
      .catch(e => { console.error('[Queens] Failed:', e.message); return []; }),
    fetchAllPages(buildBaseFilter(buildZipFilter(BROOKLYN_ZIPS)), 'Brooklyn')
      .catch(e => { console.error('[Brooklyn] Failed:', e.message); return []; }),
    fetchAllPages(buildBaseFilter(buildCityFilter(LI_CITIES)), 'Long Island')
      .catch(e => { console.error('[Long Island] Failed:', e.message); return []; })
  ]);

  // ── Separate Woodhaven/Ozone Park into their own bucket for the map ──
  const woodhavenCities = new Set(['Ozone Park', 'South Ozone Park', 'Woodhaven', 'Richmond Hill', 'South Richmond Hill']);
  const woodhavenListings = queensRaw
    .filter(p => woodhavenCities.has(p.City))
    .map(p => transform(p, 'woodhaven'));

  const queensListings = queensRaw
    .filter(p => !woodhavenCities.has(p.City))
    .map(p => transform(p, 'queens'));

  const brooklynListings = brooklynRaw.map(p => transform(p, 'brooklyn'));
  const liListings       = liRaw.map(p => transform(p, 'li'));

  // ── Build updated JSON ──
  const updated = {
    lastUpdated: new Date().toISOString(),
    source: 'OneKey® MLS via MLS GRID RESO API',
    attribution: 'The data relating to real estate for sale on this website appears in part through the OneKey® MLS Broker Reciprocity program, a voluntary cooperative exchange of property listing data between licensed real estate brokerage firms. Information deemed reliable but not guaranteed. © OneKey® MLS. All Rights Reserved.',
    activeListings:    existing.activeListings  || [],   // preserved: our own listings
    areaListings:      existing.areaListings    || [],   // preserved: manually curated
    woodhavenListings,
    queensListings,
    brooklynListings,
    longIslandListings: liListings,
    soldListings:      existing.soldListings    || []    // preserved: sold history
  };

  fs.writeFileSync(DATA_FILE, JSON.stringify(updated, null, 2));

  console.log('\n════════════════════════════════════════════════');
  console.log('✅ listings.json updated successfully');
  console.log(`   Woodhaven/OzonePark: ${woodhavenListings.length}`);
  console.log(`   Queens (other):      ${queensListings.length}`);
  console.log(`   Brooklyn:            ${brooklynListings.length}`);
  console.log(`   Long Island:         ${liListings.length}`);
  console.log(`   Total area:          ${woodhavenListings.length + queensListings.length + brooklynListings.length + liListings.length}`);
  console.log('════════════════════════════════════════════════\n');
}

main().catch(err => {
  console.error('\n[FATAL]', err.message);
  process.exit(1);
});
