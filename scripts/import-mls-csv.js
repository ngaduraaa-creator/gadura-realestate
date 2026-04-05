#!/usr/bin/env node
/**
 * Gadura Real Estate — MLS CSV Importer
 * =======================================
 * Use this to import listings directly from your MLS Matrix export.
 * This is the IMMEDIATE option — no API credentials needed.
 *
 * HOW TO EXPORT FROM MATRIX:
 *   1. Log into https://www.mlsmatrix.com
 *   2. Search for listings (your zip codes, Active or Sold)
 *   3. Select All → Export → "Spreadsheet" (CSV format)
 *   4. Save the file as:  data/mls-export.csv
 *   5. Run:  node scripts/import-mls-csv.js
 *
 * The script reads data/mls-export.csv and updates data/listings.json
 */

'use strict';

const fs   = require('fs');
const path = require('path');

const INPUT  = path.join(__dirname, '..', 'data', 'mls-export.csv');
const OUTPUT = path.join(__dirname, '..', 'data', 'listings.json');
const EXISTING_OUTPUT = fs.existsSync(OUTPUT) ? JSON.parse(fs.readFileSync(OUTPUT, 'utf8')) : {};

// ─── CSV Parser ───────────────────────────────────────────────────────────────
function parseCSV(text) {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  if (lines.length < 2) return [];

  const headers = parseCSVLine(lines[0]).map(h => h.trim().replace(/^"|"$/g, ''));
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const values = parseCSVLine(lines[i]);
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = (values[idx] || '').trim().replace(/^"|"$/g, '');
    });
    rows.push(obj);
  }
  return rows;
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    if (line[i] === '"') {
      if (inQuotes && line[i + 1] === '"') { current += '"'; i++; }
      else { inQuotes = !inQuotes; }
    } else if (line[i] === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += line[i];
    }
  }
  result.push(current);
  return result;
}

// ─── Field Aliases ────────────────────────────────────────────────────────────
// OneKey® Matrix CSV headers vary — this maps common variants to a standard name
const FIELD_ALIASES = {
  // Price
  'List Price': 'price',      'Close Price': 'closePrice',
  'Sold Price': 'closePrice', 'Price': 'price',

  // Address
  'Address': 'address',       'Street Address': 'address',
  'Street #': 'streetNum',    'Street Number': 'streetNum',
  'Street Name': 'streetName','Full Address': 'address',

  // Location
  'City': 'city',             'Town': 'city',
  'State': 'state',           'Zip': 'zip',
  'Zip Code': 'zip',          'Postal Code': 'zip',

  // Property details
  'Beds': 'beds',             'Bedrooms': 'beds',       'BR': 'beds',
  'Full Baths': 'baths',      'Bathrooms': 'baths',
  'Sq Ft': 'sqft',            'Sqft': 'sqft',
  'Square Feet': 'sqft',      'Living Area': 'sqft',

  // Property type
  'Type': 'type',             'Property Type': 'type',
  'Sub Type': 'subType',      'Style': 'subType',

  // Status
  'Status': 'status',         'ML Status': 'status',

  // MLS ID
  'MLS #': 'mlsNumber',       'ML#': 'mlsNumber',
  'Listing ID': 'mlsNumber',  'List Number': 'mlsNumber',

  // Agent
  'List Agent': 'agent',      'Listing Agent': 'agent',
  'Co-List Agent': 'coAgent', 'Selling Agent': 'agent',

  // Dates
  'Close Date': 'closeDate',  'Sold Date': 'closeDate',
  'List Date': 'listDate',    'Days on Market': 'dom',

  // Remarks
  'Remarks': 'description',   'Public Remarks': 'description',
  'Comments': 'description',

  // Photos
  'Photo URL': 'photo',       'Main Photo': 'photo',
  'Primary Photo': 'photo',
};

function normalizeRow(row) {
  const out = {};
  for (const [key, value] of Object.entries(row)) {
    const mapped = FIELD_ALIASES[key];
    if (mapped) {
      out[mapped] = value;
    } else {
      // Keep unmapped fields too
      out[key] = value;
    }
  }

  // Build address if split
  if (!out.address && (out.streetNum || out.streetName)) {
    out.address = `${out.streetNum || ''} ${out.streetName || ''}`.trim();
  }

  // Parse numbers
  out.price      = parseFloat((out.price || '0').replace(/[$,]/g, '')) || 0;
  out.closePrice = parseFloat((out.closePrice || '0').replace(/[$,]/g, '')) || 0;
  out.beds       = parseInt(out.beds) || 0;
  out.baths      = parseFloat(out.baths) || 0;
  out.sqft       = parseInt((out.sqft || '0').replace(/,/g, '')) || 0;

  return out;
}

function makeId(row, idx) {
  if (row.mlsNumber) return `mls-${row.mlsNumber}`;
  return `csv-${idx}`;
}

function fallbackPhoto(type) {
  const photos = {
    '2-Family':     'https://images.unsplash.com/photo-1576941089067-2de3c901e126?w=800&q=80&fit=crop',
    'Multi-Family': 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80&fit=crop',
    'Commercial':   'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80&fit=crop',
    'default':      'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&q=80&fit=crop',
  };
  return photos[type] || photos.default;
}

// ─── Main ────────────────────────────────────────────────────────────────────
function main() {
  if (!fs.existsSync(INPUT)) {
    console.log(`\n❌  File not found: ${INPUT}`);
    console.log('\nTo use this importer:');
    console.log('  1. Log into https://www.mlsmatrix.com');
    console.log('  2. Run a search for Active listings in your zip codes');
    console.log('  3. Select All → Export → Spreadsheet (CSV)');
    console.log(`  4. Save the file to: ${INPUT}`);
    console.log('  5. Re-run: node scripts/import-mls-csv.js\n');
    process.exit(1);
  }

  console.log(`\n[csv-import] Reading: ${INPUT}`);
  const raw = fs.readFileSync(INPUT, 'utf8');
  const rows = parseCSV(raw);
  console.log(`[csv-import] Parsed ${rows.length} rows`);

  const activeListings = [];
  const soldListings   = [];

  rows.forEach((row, idx) => {
    const r = normalizeRow(row);
    const status = (r.status || '').toLowerCase();
    const isSold = status.includes('sold') || status.includes('closed') || r.closeDate;

    const listing = {
      id:          makeId(r, idx),
      mlsNumber:   r.mlsNumber    || '',
      address:     r.address      || '',
      city:        r.city         || '',
      state:       r.state        || 'NY',
      zip:         r.zip          || '',
      price:       isSold ? (r.closePrice || r.price) : r.price,
      beds:        r.beds,
      baths:       r.baths,
      sqft:        r.sqft,
      type:        r.subType || r.type || '',
      status:      isSold ? 'Sold' : 'For Sale',
      badge:       isSold ? 'Sold' : (parseInt(r.dom) <= 7 ? 'Just Listed' : ''),
      photo:       r.photo || fallbackPhoto(r.subType || r.type),
      photos:      r.photo ? [r.photo] : [],
      description: r.description  || '',
      agent:       r.agent        || 'Gadura Real Estate LLC',
      source:      'OneKey® MLS',
      updatedAt:   new Date().toISOString(),
    };

    if (isSold) {
      listing.soldDate = r.closeDate ? r.closeDate.slice(0, 7) : '';
      soldListings.push(listing);
    } else {
      activeListings.push(listing);
    }
  });

  console.log(`[csv-import] Active: ${activeListings.length}, Sold: ${soldListings.length}`);

  // Merge with existing data (keep any entries not in this export)
  const existingActive = (EXISTING_OUTPUT.activeListings || []).filter(
    ex => !activeListings.find(n => n.mlsNumber && n.mlsNumber === ex.mlsNumber)
  );
  const existingSold = (EXISTING_OUTPUT.soldListings || []).filter(
    ex => !soldListings.find(n => n.mlsNumber && n.mlsNumber === ex.mlsNumber)
  );

  const output = {
    lastUpdated:    new Date().toISOString(),
    source:         'OneKey® MLS',
    attribution:    'All listing data © OneKey® MLS. Deemed reliable but not guaranteed.',
    activeListings: [...activeListings, ...existingActive].slice(0, 50),
    areaListings:   EXISTING_OUTPUT.areaListings || [],
    soldListings:   [...soldListings, ...existingSold].slice(0, 60),
  };

  fs.writeFileSync(OUTPUT, JSON.stringify(output, null, 2));
  console.log(`[csv-import] ✅ Wrote ${output.activeListings.length} active + ${output.soldListings.length} sold`);
  console.log(`[csv-import]    → ${OUTPUT}`);
  console.log('[csv-import] Now commit and push: git add data/listings.json && git commit -m "listings: update from MLS export" && git push\n');
}

main();
