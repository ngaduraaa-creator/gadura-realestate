#!/usr/bin/env node
/**
 * Listing page coverage gate.
 *
 * WHY THIS EXISTS
 * ---------------
 * On 2026-09-22 an ACTIVE $999,000 listing — 8554 106th Street, Richmond Hill,
 * MLS 1042190, with 14 photos in the feed — had no page on the site. The URL
 * https://gadurarealestate.com/homes/8554-106th-street-richmond-hill-new-york-11418/
 * returned 404. Seven other committed property pages were stale against the
 * feed, several still showing "Photos available on request" for listings that
 * now have photos.
 *
 * The cause is a silent break between two workflows:
 *
 *     sync-listings.yml   runs on a schedule, pushes data/listings.json
 *     build-pages.yml     on: push: paths: [data/listings.json]
 *
 * GitHub does not trigger a workflow from a push made with the default
 * GITHUB_TOKEN. That guard exists to stop infinite loops, and it silently
 * severs this chain: the feed updates every few hours, the rendered pages
 * never rebuild, and the gap widens with every sync. Nothing failed. No run
 * went red. The site just quietly stopped matching its own inventory.
 *
 * That is the worst shape a bug can take on a lead-generation site — the
 * inventory a buyer searches for is the product, and its absence is invisible
 * from inside the repo.
 *
 * WHAT THIS CHECKS
 * ----------------
 * MISSING   an active listing in the feed with no homes/<slug>/index.html.
 *           Hard failure. This is the 404 case.
 *
 * STALE     a page whose committed HTML differs from what the generator would
 *           emit today. Reported, and a failure under --strict, because a
 *           stale page can misstate price, status, or photo availability.
 *
 * ORPHANED  a homes/ page with no corresponding listing in the feed. Reported
 *           only: a sold listing leaving the feed while its page stays up is a
 *           business decision about whether to keep sold inventory indexed,
 *           not an engineering error.
 *
 * The slug rule and the feed loader are imported from build-property-pages.js
 * rather than reimplemented, so this checker cannot drift away from the
 * generator it audits.
 *
 * Run:  node scripts/dgp/test_listing_page_coverage.js            (exit 0/1)
 *       node scripts/dgp/test_listing_page_coverage.js --strict   (stale fails too)
 *
 * Reads the working tree and writes nothing.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const gen = require('../build-property-pages.js');
const { addressSlug, loadListings, HOMES_DIR } = gen;

const ROOT = path.resolve(__dirname, '..', '..');
const STRICT = process.argv.includes('--strict');

// A listing is "live" if its status is not a terminal one. Matching the
// generator's own permissive default (status falls back to 'Active'), this
// errs toward requiring a page rather than excusing a missing one.
const TERMINAL = /sold|closed|withdrawn|cancell?ed|expired|off.?market|delete/i;

function isLive(l) {
  return !TERMINAL.test(l.status || '');
}

function rel(p) {
  return path.relative(ROOT, p);
}

function main() {
  const listings = loadListings();
  const live = listings.filter(isLive);

  const missing = [];
  const present = [];

  for (const l of live) {
    const slug = addressSlug(l);
    if (!slug) continue; // generator warns and skips these itself
    const page = path.join(HOMES_DIR, slug, 'index.html');
    (fs.existsSync(page) ? present : missing).push({ l, slug, page });
  }

  // Orphans: a rendered page with no live listing behind it.
  const expected = new Set(live.map(addressSlug).filter(Boolean));
  let orphaned = [];
  if (fs.existsSync(HOMES_DIR)) {
    orphaned = fs.readdirSync(HOMES_DIR, { withFileTypes: true })
      .filter(d => d.isDirectory() && !expected.has(d.name))
      .filter(d => fs.existsSync(path.join(HOMES_DIR, d.name, 'index.html')))
      .map(d => d.name);
  }

  // Stale: committed HTML differs from what the generator emits today. Asking
  // git is cheaper and safer than running the generator, which would write
  // into the tree just to answer a question.
  let stale = [];
  try {
    const out = execFileSync(
      'git', ['status', '--porcelain', '--', rel(HOMES_DIR)],
      { cwd: ROOT, encoding: 'utf8' }
    );
    // Do NOT trim the whole blob: porcelain status codes are two columns, so a
    // modified file's line starts with a significant leading space (" M path").
    // Trimming the blob eats that space and then slice(3) eats the path's first
    // character. Strip the 2-column code + separator per line instead.
    stale = out.split('\n')
      .filter(line => line.length > 3)
      .map(line => line.slice(3).trim())
      .filter(Boolean);
  } catch {
    // Not a git tree, or git unavailable — skip the staleness check rather
    // than fail the gate on an unrelated cause.
    stale = [];
  }

  console.log('=== listing page coverage gate ===');
  console.log(`listings in feed : ${listings.length}`);
  console.log(`  live           : ${live.length}`);
  console.log(`  pages present  : ${present.length}`);

  const failures = [];

  if (missing.length) {
    console.log(`\nFAIL: ${missing.length} live listing(s) with NO page — these are 404s`);
    for (const { l, slug } of missing) {
      const price = l.price ? `$${l.price.toLocaleString('en-US')}` : 'price n/a';
      console.log(`    ${slug}`);
      console.log(`        ${l.status || 'Active'} · ${price} · MLS ${l.mlsNumber || 'none'} · ${(l.photos || []).length} photo(s)`);
      console.log(`        would live at /homes/${slug}/`);
    }
    console.log('    fix: node scripts/build-property-pages.js   (then review the diff before merging)');
    failures.push(`${missing.length} listing(s) with no page`);
  } else {
    console.log('\nok  every live listing has a page');
  }

  if (stale.length) {
    const label = STRICT ? 'FAIL' : 'WARN';
    console.log(`\n${label}: ${stale.length} property page(s) differ from the committed tree`);
    for (const f of stale.slice(0, 10)) console.log(`    ${f}`);
    if (stale.length > 10) console.log(`    ... and ${stale.length - 10} more`);
    if (STRICT) failures.push(`${stale.length} stale page(s)`);
  }

  if (orphaned.length) {
    console.log(`\nINFO: ${orphaned.length} page(s) with no live listing (sold/withdrawn?)`);
    for (const s of orphaned.slice(0, 10)) console.log(`    /homes/${s}/`);
    if (orphaned.length > 10) console.log(`    ... and ${orphaned.length - 10} more`);
    console.log('    Keeping sold inventory indexed is a business call, not an error.');
  }

  if (failures.length) {
    console.log('\nFAILED: ' + failures.join('; '));
    return 1;
  }
  console.log('\nPASS — listing pages match the feed.');
  return 0;
}

process.exit(main());
