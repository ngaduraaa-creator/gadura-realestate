#!/usr/bin/env node
/**
 * Gadura Real Estate — OneKey® MLS RESO Web API Sync
 * ====================================================
 * Fetches LIVE listings directly from OneKey® MLS using the official
 * RESO Web API (the only legal, compliant way to display MLS data).
 *
 * HOW TO GET CREDENTIALS:
 *   1. Log into https://www.mlsmatrix.com  (your OneKey MLS portal)
 *   2. Navigate to: My Matrix → My Account → RESO API Access
 *      OR email OneKey support: memberservices@onekeymls.com
 *      OR call: (631) 661-4800
 *   3. Request "RESO Web API / IDX data credentials"
 *   4. They will provide:
 *        - API Base URL (e.g. https://api.mlsgrid.com/v2/)
 *        - Client ID
 *        - Client Secret
 *   5. Add those 3 values as GitHub Secrets (see MLS-SETUP.md)
 *
 * RUN MANUALLY:
 *   RESO_TOKEN=yourtoken RESO_BASE_URL=https://... node scripts/sync-reso.js
 *
 * SCHEDULED:
 *   GitHub Actions → .github/workflows/sync-listings.yml (every 4 hours)
 */

'use strict';

const https  = require('https');
const http   = require('http');
const fs     = require('fs');
const path   = require('path');

// ─── Config ──────────────────────────────────────────────────────────────────
const CONFIG = {
  // Set these as GitHub Secrets (or local env vars for testing)
  baseUrl:      process.env.RESO_BASE_URL      || '',
  token:        process.env.RESO_ACCESS_TOKEN  || '',
  clientId:     process.env.RESO_CLIENT_ID     || '',
  clientSecret: process.env.RESO_CLIENT_SECRET || '',
  tokenUrl:     process.env.RESO_TOKEN_URL     || '',

  // Output file — read by the website
  outputFile: path.join(__dirname, '..', 'data', 'listings.json'),

  // Which MLS areas to pull (OneKey® MLS area codes for Queens / Long Island)
  // See: https://www.onekeymls.com/search-mls
  targetZips: [
    '11416','11417','11418','11419','11420','11421', // Ozone Park area
    '11001','11003','11010','11040',                  // Elmont / Valley Stream area
    '11101','11102','11103','11104','11105','11106',  // Astoria / Long Island City
    '11354','11355','11356','11357','11358',          // Flushing / Whitestone
    '11366','11367','11375','11377','11378','11379',  // Forest Hills / Rego Park
    '11385','11432','11433','11434','11435','11436',  // Woodhaven / Jamaica
    '11550','11551','11552','11553',                  // Hempstead
  ],

  // Gadura agents — filter to "our listings" vs "area comps"
  agentMlsIds: [
    // Add your MLS member IDs here (found in Matrix under My Account)
    process.env.AGENT_ID_NITIN   || '',
    process.env.AGENT_ID_VINOD   || '',
    process.env.AGENT_ID_GAURAV  || '',
  ].filter(Boolean),

  // Max listings to pull per request
  pageSize: 50,
};

// ─── RESO Field Map ───────────────────────────────────────────────────────────
// Maps RESO standard field names → our internal schema
const RESO_SELECT_ACTIVE = [
  'ListingKey','ListingId','ListPrice',
  'BedsTotal','BathroomsTotalInteger','LivingArea',
  'PropertyType','PropertySubType','StructureType',
  'UnparsedAddress','StreetNumber','StreetName','City','StateOrProvince','PostalCode',
  'StandardStatus','MlsStatus',
  'PublicRemarks','ListAgentFullName','ListAgentMlsId',
  'Media','PhotosCount',
  'LotSizeAcres','LotSizeSquareFeet',
  'YearBuilt','DaysOnMarket',
  'Latitude','Longitude',
].join(',');

const RESO_SELECT_SOLD = [
  'ListingKey','ListingId','ClosePrice','ListPrice',
  'BedsTotal','BathroomsTotalInteger','LivingArea',
  'PropertyType','PropertySubType',
  'UnparsedAddress','StreetNumber','StreetName','City','StateOrProvince','PostalCode',
  'StandardStatus','CloseDate',
  'PublicRemarks','ListAgentFullName','CloseAgentFullName',
  'Media','PhotosCount',
  'YearBuilt',
  'Latitude','Longitude',
].join(',');

// ─── HTTP helpers ─────────────────────────────────────────────────────────────

function resoFetch(url, token) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const options = {
      hostname: parsed.hostname,
      path:     parsed.pathname + parsed.search,
      method:   'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
        'User-Agent': 'GaduraRealEstate-IDX/1.0 (info@gadurarealestate.com)',
      },
    };
    const proto = parsed.protocol === 'https:' ? https : http;
    const req = proto.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 400) {
          reject(new Error(`RESO API error ${res.statusCode}: ${data.slice(0, 200)}`));
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error(`JSON parse error: ${e.message}`));
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(30000, () => { req.destroy(new Error('Request timeout')); });
    req.end();
  });
}

async function getOAuthToken() {
  if (!CONFIG.tokenUrl || !CONFIG.clientId || !CONFIG.clientSecret) return null;
  return new Promise((resolve, reject) => {
    const body = `grant_type=client_credentials&client_id=${encodeURIComponent(CONFIG.clientId)}&client_secret=${encodeURIComponent(CONFIG.clientSecret)}&scope=api`;
    const parsed = new URL(CONFIG.tokenUrl);
    const options = {
      hostname: parsed.hostname,
      path:     parsed.pathname,
      method:   'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(body),
      },
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', c => { data += c; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed.access_token || null);
        } catch { resolve(null); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── RESO → GRE Schema Transform ─────────────────────────────────────────────

function transformActive(r) {
  const photos = (r.Media || [])
    .sort((a, b) => (a.Order || 0) - (b.Order || 0))
    .map(m => m.MediaURL || m.MediaUrl || '')
    .filter(Boolean);

  const fallback = 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&q=80&fit=crop';

  return {
    id:          r.ListingKey  || r.ListingId,
    mlsNumber:   r.ListingId   || '',
    address:     r.UnparsedAddress || `${r.StreetNumber} ${r.StreetName}`.trim(),
    city:        r.City        || '',
    state:       r.StateOrProvince || 'NY',
    zip:         r.PostalCode  || '',
    price:       r.ListPrice   || 0,
    beds:        r.BedsTotal   || 0,
    baths:       r.BathroomsTotalInteger || 0,
    sqft:        r.LivingArea  || 0,
    type:        r.PropertySubType || r.PropertyType || '',
    status:      'For Sale',
    badge:       r.DaysOnMarket <= 7 ? 'Just Listed' : '',
    daysOnMarket: r.DaysOnMarket || 0,
    photo:       photos[0] || fallback,
    photos:      photos.length > 0 ? photos : [fallback],
    description: r.PublicRemarks || '',
    agent:       r.ListAgentFullName || 'Gadura Real Estate LLC',
    agentMlsId:  r.ListAgentMlsId || '',
    lat:         r.Latitude  || null,
    lng:         r.Longitude || null,
    url:         `https://www.onekeymls.com/listing/${r.ListingId || r.ListingKey}`,
    source:      'OneKey® MLS',
    updatedAt:   new Date().toISOString(),
  };
}

function transformSold(r) {
  const photos = (r.Media || [])
    .map(m => m.MediaURL || m.MediaUrl || '')
    .filter(Boolean);

  return {
    id:          r.ListingKey  || r.ListingId,
    mlsNumber:   r.ListingId   || '',
    address:     r.UnparsedAddress || `${r.StreetNumber} ${r.StreetName}`.trim(),
    city:        r.City        || '',
    state:       r.StateOrProvince || 'NY',
    zip:         r.PostalCode  || '',
    price:       r.ClosePrice  || r.ListPrice || 0,
    beds:        r.BedsTotal   || 0,
    baths:       r.BathroomsTotalInteger || 0,
    sqft:        r.LivingArea  || 0,
    type:        r.PropertySubType || r.PropertyType || '',
    status:      'Sold',
    badge:       'Sold',
    soldDate:    r.CloseDate   ? r.CloseDate.slice(0, 7) : '',
    photo:       photos[0] || 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&q=80&fit=crop',
    photos:      photos,
    agent:       r.ListAgentFullName || r.CloseAgentFullName || 'Gadura Real Estate LLC',
    lat:         r.Latitude  || null,
    lng:         r.Longitude || null,
    url:         `https://www.onekeymls.com/listing/${r.ListingId || r.ListingKey}`,
    source:      'OneKey® MLS',
  };
}

// ─── Main Sync ─────────────────────────────────────────────────────────────────

async function buildFilter(status) {
  // Build OData filter
  const zipFilter = CONFIG.targetZips.map(z => `PostalCode eq '${z}'`).join(' or ');
  if (status === 'Active') {
    return `StandardStatus eq 'Active' and (${zipFilter})`;
  }
  if (status === 'Closed') {
    // Sold in last 12 months
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    const dateStr = oneYearAgo.toISOString().slice(0, 10);
    return `StandardStatus eq 'Closed' and CloseDate ge ${dateStr} and (${zipFilter})`;
  }
  return '';
}

async function fetchAll(token, status, select) {
  const results = [];
  const filter = await buildFilter(status);
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
    const params = new URLSearchParams({
      '$filter':  filter,
      '$select':  select,
      '$orderby': status === 'Active' ? 'DaysOnMarket asc' : 'CloseDate desc',
      '$top':     CONFIG.pageSize,
      '$skip':    skip,
      '$count':   'true',
    });

    const url = `${CONFIG.baseUrl.replace(/\/$/, '')}/Property?${params}`;
    console.log(`[reso] Fetching ${status} listings (skip=${skip})…`);

    try {
      const data = await resoFetch(url, token);
      const items = data.value || data['@odata.value'] || [];
      results.push(...items);
      skip += items.length;
      hasMore = items.length === CONFIG.pageSize;
      console.log(`[reso]   Got ${items.length} records (total so far: ${results.length})`);
    } catch (err) {
      console.error(`[reso] Error fetching ${status}: ${err.message}`);
      break;
    }
  }

  return results;
}

async function main() {
  console.log('\n[reso] ── OneKey® MLS RESO Sync Starting ──────────────────');
  console.log(`[reso] ${new Date().toISOString()}`);

  // ── Check credentials ─────────────────────────────────────────────────────
  let token = CONFIG.token;

  if (!token && CONFIG.tokenUrl) {
    console.log('[reso] Getting OAuth token…');
    token = await getOAuthToken();
    if (!token) {
      console.error('[reso] ❌ OAuth token request failed');
    }
  }

  if (!token || !CONFIG.baseUrl) {
    console.log('[reso] ⚠️  No RESO credentials configured.');
    console.log('[reso]    Set these environment variables / GitHub Secrets:');
    console.log('[reso]      RESO_BASE_URL       = your MLS API base URL');
    console.log('[reso]      RESO_ACCESS_TOKEN   = your bearer token');
    console.log('[reso]    OR for OAuth2:');
    console.log('[reso]      RESO_TOKEN_URL      = OAuth token endpoint');
    console.log('[reso]      RESO_CLIENT_ID      = your client ID');
    console.log('[reso]      RESO_CLIENT_SECRET  = your client secret');
    console.log('[reso]');
    console.log('[reso]    See MLS-SETUP.md for instructions on getting credentials.');
    console.log('[reso]    Keeping existing listings.json unchanged.');
    process.exit(0); // don't fail the GitHub Action
  }

  // ── Fetch active listings ─────────────────────────────────────────────────
  const rawActive = await fetchAll(token, 'Active', RESO_SELECT_ACTIVE);
  console.log(`[reso] Active listings fetched: ${rawActive.length}`);

  // ── Fetch sold listings (last 12 months) ──────────────────────────────────
  const rawSold = await fetchAll(token, 'Closed', RESO_SELECT_SOLD);
  console.log(`[reso] Sold listings fetched: ${rawSold.length}`);

  // ── Separate OUR listings vs area comps ───────────────────────────────────
  let ourActive = rawActive;
  let areaActive = [];

  if (CONFIG.agentMlsIds.length > 0) {
    ourActive  = rawActive.filter(r => CONFIG.agentMlsIds.includes(r.ListAgentMlsId));
    areaActive = rawActive.filter(r => !CONFIG.agentMlsIds.includes(r.ListAgentMlsId));
    console.log(`[reso] Our active listings: ${ourActive.length}, Area comps: ${areaActive.length}`);
  }

  // ── Transform to GRE schema ───────────────────────────────────────────────
  const output = {
    lastUpdated:    new Date().toISOString(),
    source:         'OneKey® MLS',
    attribution:    'All listing data © OneKey® MLS. Deemed reliable but not guaranteed.',
    activeListings: ourActive.slice(0, 20).map(transformActive),
    areaListings:   areaActive.slice(0, 50).map(transformActive),
    soldListings:   rawSold.slice(0, 30).map(transformSold),
  };

  // ── Write to file ─────────────────────────────────────────────────────────
  const dir = path.dirname(CONFIG.outputFile);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  fs.writeFileSync(CONFIG.outputFile, JSON.stringify(output, null, 2));
  console.log(`[reso] ✅ Wrote ${output.activeListings.length} active + ${output.soldListings.length} sold listings`);
  console.log(`[reso]    → ${CONFIG.outputFile}`);
  console.log('[reso] ── Sync Complete ─────────────────────────────────────\n');
}

main().catch(err => {
  console.error('[reso] FATAL:', err.message);
  process.exit(1);
});
