/*
 * idx-758-attribution.js
 * ------------------------------------------------------------------
 * OneKey(R) MLS / NAR IDX Policy 7.58 — per-listing broker attribution
 * for homes.gadurarealestate.com (idxID c056, IDX-wrapper-standard).
 *
 * WHAT THIS DOES (interim mitigation, client-side only):
 *   On LISTING DETAIL pages, IDX Broker already renders the per-listing
 *   credit ("Listing courtesy of <Agent> with <Firm>") but buries it at the
 *   very BOTTOM of the page (~absTop 5481 of 5610px), inside the MLS
 *   disclaimer block. This script lifts that same data into a prominent,
 *   high-contrast credit directly under the address near the TOP of the page,
 *   at a font size equal to the median listing-data size (16px), using the
 *   OneKey-preferred "Listed by" phrasing.
 *
 * WHAT THIS CANNOT DO (hard data limitation — see COMPLIANCE-7.58-attribution.md):
 *   - It cannot add the listing participant's PHONE or EMAIL: that data is
 *     not delivered to the page by IDX Broker for third-party listings, so
 *     there is nothing client-side to surface. Do NOT substitute Gadura's own
 *     number — 7.58 requires the *listing* broker's contact, and using the
 *     display broker's number is itself a violation.
 *   - It cannot add attribution to SEARCH-RESULTS cards: the listing office
 *     name is not present in the results-card DOM at all.
 *   Both gaps require an IDX Broker dashboard / support change to make the
 *   data available. This script only fixes detail-page PROMINENCE + PHRASING.
 *
 * INSTALL: paste inside the <script>...</script> block in
 *   IDX dashboard -> Designs -> Custom Initial Output (or alongside idx-custom.js).
 * Idempotent and safe to run repeatedly; re-applies on IDX ajax re-render.
 */
(function () {
  'use strict';

  var MARKER = 'gre-idx-attribution';

  // Only act on listing-detail pages.
  function isDetailPage() {
    return /\/idx\/details\//i.test(location.pathname) ||
      !!document.querySelector('#IDX-main.IDX-category-details, #IDX-detailsPageContainer');
  }

  // Find the unclassed <div> whose own text is the "Listing courtesy of ..." credit.
  function findCourtesySource() {
    var scope = document.querySelectorAll('#IDX-detailsPageContainer div, #IDX-main div');
    for (var i = 0; i < scope.length; i++) {
      var el = scope[i];
      var direct = Array.prototype.filter
        .call(el.childNodes, function (n) { return n.nodeType === 3; })
        .map(function (n) { return n.textContent; })
        .join('')
        .trim();
      if (/listing courtesy of/i.test(direct)) return el;
    }
    return null;
  }

  function inject() {
    if (!isDetailPage()) return;
    if (document.querySelector('.' + MARKER)) return; // already present

    var src = findCourtesySource();
    if (!src) return; // courtesy not in DOM yet (ajax) — observer will retry

    var raw = src.textContent.replace(/\s+/g, ' ').trim();
    // Normalize "Listing courtesy of X with Y ." -> "Listed by X with Y"
    var text = raw.replace(/^Listing courtesy of/i, 'Listed by').replace(/\s*\.\s*$/, '').trim();
    if (!text) return;

    var el = document.createElement('div');
    el.className = MARKER;
    el.setAttribute('role', 'note');
    el.setAttribute('aria-label', 'Listing broker attribution');
    el.textContent = text;

    // Insert in a reasonably prominent location: right after the address block.
    var anchor =
      document.querySelector('#IDX-detailsAddress') ||
      document.querySelector('#IDX-detailsBasicInfo') ||
      document.querySelector('#IDX-detailsFields');

    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(el, anchor.nextSibling);
    } else {
      var main = document.querySelector('#IDX-detailsMain, #IDX-detailsPageContainer');
      if (main) main.insertBefore(el, main.firstChild);
    }
  }

  // Run now + on DOM ready.
  if (document.readyState !== 'loading') inject();
  else document.addEventListener('DOMContentLoaded', inject);

  // IDX re-renders detail content via ajax; re-inject if our node is removed.
  var pending = false;
  var mo = new MutationObserver(function () {
    if (pending) return;
    pending = true;
    setTimeout(function () { pending = false; inject(); }, 150);
  });
  try { mo.observe(document.body, { childList: true, subtree: true }); } catch (e) {}
})();
