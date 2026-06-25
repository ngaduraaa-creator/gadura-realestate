#!/usr/bin/env node
/**
 * diagnose-idx-api.js — Run this locally to find why listings.json is empty.
 *
 * Usage:
 *   IDX_BROKER_API_KEY=your_key node scripts/diagnose-idx-api.js
 *
 * It tests every relevant IDX Broker v1.8 endpoint and prints exactly
 * what's accessible and what returns data.
 */
'use strict';

const https = require('https');

const API_KEY  = process.env.IDX_BROKER_API_KEY;
const API_BASE = 'api.idxbroker.com';
const API_VER  = '1.8.0';

if (!API_KEY) {
  console.error('ERROR: IDX_BROKER_API_KEY environment variable not set.');
  console.error('Run: IDX_BROKER_API_KEY=your_key node scripts/diagnose-idx-api.js');
  process.exit(1);
}

function idxGet(path) {
  return new Promise((resolve) => {
    const options = {
      hostname: API_BASE,
      path,
      method: 'GET',
      headers: { accesskey: API_KEY, outputtype: 'json', apiversion: API_VER },
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: data.slice(0, 1200) }));
    });
    req.on('error', e => resolve({ status: 0, body: String(e) }));
    req.end();
  });
}

function summarise(body) {
  try {
    const parsed = JSON.parse(body);
    if (Array.isArray(parsed)) return `Array(${parsed.length}) items`;
    if (typeof parsed === 'object') return `Object keys: ${Object.keys(parsed).slice(0, 8).join(', ')}`;
    return String(parsed).slice(0, 80);
  } catch {
    return body.slice(0, 120);
  }
}

const ENDPOINTS = [
  ['/clients/apiversion',    'API version check'],
  ['/clients/featured',      'Featured listings'],
  ['/clients/supplemental',  'Supplemental listings'],
  ['/clients/listing',       'Client listings (Platinum+)'],
  ['/clients/savedlinks',    'Saved links (GET)'],
  ['/clients/systemlinks',   'System links'],
  ['/clients/properties',    'Properties endpoint'],
  ['/mls/approvedMLS',       'Approved MLS list'],
  ['/mls/prices',            'MLS price ranges'],
  ['/mls/cities',            'MLS cities'],
];

async function run() {
  console.log('=== IDX Broker API Diagnostics ===');
  console.log(`API Key: ...${API_KEY.slice(-4)} (last 4 chars)`);
  console.log(`Host: ${API_BASE}\n`);

  let hasData = false;

  for (const [path, label] of ENDPOINTS) {
    const { status, body } = await idxGet(path);
    const icon = status === 200 ? '✓' : status === 204 ? '○' : '✗';
    const summary = status === 200 ? summarise(body) : `HTTP ${status}`;
    console.log(`${icon} [${status}] ${label.padEnd(35)} ${summary}`);
    if (status === 200) hasData = true;
  }

  console.log('\n--- Diagnosis ---');
  if (!hasData) {
    console.log('⚠  ALL endpoints returned errors. Most likely causes:');
    console.log('   1. API key is wrong or expired — regenerate at:');
    console.log('      https://middleware.idxbroker.com/mgmt/api-key');
    console.log('   2. IP restriction on the key — check IDX Broker dashboard');
  } else {
    console.log('API key is valid. Check which endpoints returned 403/404.');
    console.log('To enable savedlinks + results access, go to:');
    console.log('  IDX Broker Dashboard → Leads → API → Permissions');
    console.log('  Enable: savedlinks (read+write), results (read)');
  }

  console.log('\nIDX Broker API docs: https://developers.idxbroker.com/docs');
  console.log('Account permissions: https://middleware.idxbroker.com/mgmt/api-permissions');
}

run().catch(console.error);
