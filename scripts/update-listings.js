#!/usr/bin/env node
/**
 * Gadura Real Estate — Auto Listing Updater
 * ==========================================
 * Fetches current listings and sold history from homes.com and Zillow.
 * Updates data/listings.json and triggers a Netlify redeploy.
 *
 * Run manually:   node scripts/update-listings.js
 * Scheduled via:  GitHub Actions (see .github/workflows/update-listings.yml)
 *                 OR Netlify scheduled function
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const LISTINGS_FILE = path.join(__dirname, '..', 'data', 'listings.json');
const NETLIFY_SITE_ID = '2167da3d-4fd0-40a4-a34a-7c7468084a9a';

// ─── Homes.com agent profile pages ───────────────────────────────────────────
const SOURCES = {
  nitin_homes: 'https://www.homes.com/real-estate-agents/nitin-gadura/9t6kfc5/',
  vinod_zillow: 'https://www.zillow.com/profile/vinodgadura',
  nitin_zillow: 'https://www.zillow.com/profile/NitinGadura106',
};

// ─── Fetch helper ─────────────────────────────────────────────────────────────
function fetchPage(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.setTimeout(10000, () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// ─── Parse homes.com listing cards ───────────────────────────────────────────
function parseHomesComListings(html) {
  const listings = [];

  // Extract listing URLs
  const urlRegex = /href="(\/property\/[^"]+)"/g;
  const priceRegex = /\$[\d,]+/g;
  const imgRegex = /https:\/\/images\.homes\.com\/listings\/[^"'\s]+primaryphoto[^"'\s]*/g;

  const urls = [...new Set([...html.matchAll(urlRegex)].map(m => 'https://www.homes.com' + m[1]))];
  const prices = [...html.matchAll(priceRegex)].map(m => parseInt(m[0].replace(/[$,]/g, '')));
  const photos = [...new Set([...html.matchAll(imgRegex)].map(m => m[0]))];

  urls.slice(0, 10).forEach((url, i) => {
    const price = prices[i] || 0;
    const photo = photos[i] || '';
    const addressMatch = url.match(/\/property\/([^/]+)\//);
    const rawAddress = addressMatch ? addressMatch[1].replace(/-/g, ' ') : '';

    listings.push({ url, price, photo, rawAddress });
  });

  return listings;
}

// ─── Main update logic ────────────────────────────────────────────────────────
async function updateListings() {
  console.log('[update-listings] Starting at', new Date().toISOString());

  let current = JSON.parse(fs.readFileSync(LISTINGS_FILE, 'utf8'));
  let changed = false;

  try {
    const html = await fetchPage(SOURCES.nitin_homes);
    const fetched = parseHomesComListings(html);

    // Find new active listings not already in current data
    for (const item of fetched) {
      if (item.price > 500000 && item.photo) {
        const alreadyActive = current.activeListings.some(l => l.url === item.url);
        const alreadySold = current.soldListings.some(l => l.url === item.url);

        if (!alreadyActive && !alreadySold) {
          console.log('[update-listings] NEW LISTING FOUND:', item.url, '$' + item.price);
          current.activeListings.push({
            id: 'active-' + Date.now(),
            address: item.rawAddress,
            city: 'Queens',
            state: 'NY',
            zip: '',
            price: item.price,
            beds: null,
            baths: null,
            sqft: null,
            type: 'Residential',
            status: 'For Sale',
            photo: item.photo,
            photos: [item.photo],
            url: item.url,
            description: '',
            source: 'homes.com',
            mlsNumber: '',
          });
          changed = true;
        }
      }
    }

    console.log('[update-listings] Checked', fetched.length, 'listings from homes.com');
  } catch (err) {
    console.error('[update-listings] homes.com fetch failed:', err.message);
  }

  if (changed) {
    current.lastUpdated = new Date().toISOString().split('T')[0];
    fs.writeFileSync(LISTINGS_FILE, JSON.stringify(current, null, 2));
    console.log('[update-listings] listings.json updated');

    // Trigger Netlify redeploy
    try {
      const result = execSync(
        `netlify deploy --prod --dir . --site ${NETLIFY_SITE_ID}`,
        { cwd: path.join(__dirname, '..'), encoding: 'utf8' }
      );
      console.log('[update-listings] Netlify deploy triggered');
      // Git commit
      execSync('git add data/listings.json && git commit -m "chore: auto-update listings"', {
        cwd: path.join(__dirname, '..'), encoding: 'utf8'
      });
    } catch (e) {
      console.error('[update-listings] Deploy failed:', e.message);
    }
  } else {
    console.log('[update-listings] No changes detected');
  }

  console.log('[update-listings] Done');
}

updateListings().catch(console.error);
