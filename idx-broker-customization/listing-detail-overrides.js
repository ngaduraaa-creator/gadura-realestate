/* ════════════════════════════════════════════════════════════════════════
   Gadura Real Estate — IDX Broker Compliance JavaScript
   File: listing-detail-overrides.js
   Apply in: IDX Broker → Designs → "Custom Initial Output" (wrap in
             <script>…</script>), OR the Dynamic Wrapper before </body>.
             Runs on EVERY IDX page.

   Implements compliance fixes:
     #3 Phone formatting    9177050132 -> (917) 705-0132 / tel:+19177050132
     #4 Status badge        prominent colour-coded badge by address + price
     #6 SHIELD notice        "By submitting this form…" above every contact form
     #7 reCAPTCHA disclosure  enforce correct text + Google policy links
     #8 Similar Listings      replace "No listings found" with same-origin
                              deep-link cards (county / price ±20% / city)
     #1/#2/#5 Footer          defensively inject the compliance footer if the
                              global-footer-injection.html field did not render

   Safe by design: idempotent, each fix wrapped in try/catch (a failure in one
   never blocks the others or breaks IDX), re-applies on IDX's async DOM swaps
   via MutationObserver. All injected nodes are namespaced `gre-`.
   ════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var PHONE_RAW  = '9177050132';
  var PHONE_DISP = '(917) 705-0132';
  var PHONE_TEL  = '+19177050132';
  var BASE       = 'https://gadurarealestate.com';
  var IDX_BASE   = 'https://homes.gadurarealestate.com';

  // ── helpers ──────────────────────────────────────────────────────────
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function fieldValue(id, label) {
    var el = document.getElementById(id);
    if (!el) return '';
    var t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (label) t = t.replace(new RegExp('^' + label + '\\s*', 'i'), '');
    return t.trim();
  }

  // ── #3 PHONE FORMATTING ──────────────────────────────────────────────
  function formatPhones() {
    // tel: links — set both text + href
    $all('a[href*="' + PHONE_RAW + '"], a[href^="tel:"]').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.indexOf(PHONE_RAW) > -1 || /^tel:9177050132$/.test(href)) {
        a.setAttribute('href', 'tel:' + PHONE_TEL);
      }
      if ((a.textContent || '').replace(/\D/g, '') === PHONE_RAW) a.textContent = PHONE_DISP;
    });
    // bare text occurrences in the contact block / anywhere safe
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) {
      if (n.nodeValue.indexOf(PHONE_RAW) > -1 &&
          n.parentNode && !/SCRIPT|STYLE|TEXTAREA|INPUT/.test(n.parentNode.nodeName)) {
        nodes.push(n);
      }
    }
    nodes.forEach(function (node) { node.nodeValue = node.nodeValue.split(PHONE_RAW).join(PHONE_DISP); });
  }

  // ── #4 STATUS BADGE ──────────────────────────────────────────────────
  function injectStatusBadge() {
    if ($('.gre-status-badge')) return;
    var statusEl = $('.IDX-field-propStatus');
    var status = statusEl ? (statusEl.textContent || '').replace(/\s+/g, ' ').replace(/^Status\s*/i, '').trim() : '';
    if (!status) {
      // fallback: any IDX-text span carrying a status word
      var span = $all('.IDX-text, span').filter(function (s) {
        return /^(Active|Pending|Sold|Closed|Under Contract|Coming Soon|Accepted Offer|In Contract|Contingent)$/i.test((s.textContent || '').trim());
      })[0];
      status = span ? span.textContent.trim() : '';
    }
    if (!status) return;

    var cls = 'gre-status-sold';
    if (/active|coming soon/i.test(status)) cls = 'gre-status-active';
    else if (/pending|contract|contingent|accepted offer/i.test(status)) cls = 'gre-status-pending';

    var badge = document.createElement('span');
    badge.className = 'gre-status-badge ' + cls;
    badge.textContent = status;

    // place directly beside/below the address + price
    var anchor = $('#IDX-detailsAddressStreet') || $('.IDX-detailsAddress');
    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(badge, anchor.nextSibling);
    }
  }

  // ── #6 SHIELD ACT FORM NOTICE ────────────────────────────────────────
  function injectFormNotice() {
    var forms = $all('#IDX-detailscontactContactForm, form.IDX-contactForm, .IDX-contactForm form, form');
    forms.forEach(function (form) {
      // only forms that collect personal info
      if (!form.querySelector('input[name="email"], input[type="email"]')) return;
      if (form.querySelector('.gre-form-notice')) return;
      var notice = document.createElement('p');
      notice.className = 'gre-form-notice';
      notice.innerHTML = 'By submitting this form, you agree to our ' +
        '<a href="' + BASE + '/privacy-policy.html" target="_blank" rel="noopener">Privacy Policy</a> and ' +
        '<a href="' + BASE + '/terms.html" target="_blank" rel="noopener">Terms of Use</a>.';
      var submit = form.querySelector('#IDX-submitBtn, .IDX-submit-btn, button[type="submit"], input[type="submit"]');
      if (submit && submit.parentNode) submit.parentNode.insertBefore(notice, submit);
      else form.appendChild(notice);
    });
  }

  // ── #7 reCAPTCHA DISCLOSURE FIX (enforce correct text + links) ────────
  function fixRecaptcha() {
    $all('.IDX-googleRecaptchaPolicy').forEach(function (el) {
      var hasPrivacy = el.querySelector('a[href*="policies.google.com/privacy"]');
      var hasTerms = el.querySelector('a[href*="policies.google.com/terms"]');
      var txt = (el.textContent || '').replace(/\s+/g, ' ');
      var broken = !hasPrivacy || !hasTerms || /Google and apply/i.test(txt) || !/Terms of Service apply/i.test(txt);
      if (broken) {
        el.innerHTML = 'This site is protected by reCAPTCHA and the Google ' +
          '<a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Privacy Policy</a> and ' +
          '<a href="https://policies.google.com/terms" target="_blank" rel="noopener">Terms of Service</a> apply.';
      }
    });
  }

  // ── #8 SIMILAR LISTINGS (secure same-origin deep-links) ──────────────
  var ICONS = {
    county: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M5 21V7l8-4 8 4v14M9 9h.01M9 13h.01M9 17h.01M15 9h.01M15 13h.01M15 17h.01"/></svg>',
    price:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    city:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M9 21V8l-6 4M9 8l6-4 6 4M21 21V8M14 21v-4h-4v4"/></svg>'
  };
  function money(n) { return '$' + Number(n).toLocaleString('en-US'); }
  function card(href, icon, title, sub) {
    return '<a class="gre-similar-card" href="' + href + '" target="_blank" rel="noopener">' +
      '<span class="gre-similar-icon">' + icon + '</span>' +
      '<span class="gre-similar-text"><span class="gre-similar-title">' + title + '</span>' +
      '<span class="gre-similar-sub">' + sub + '</span></span>' +
      '<span class="gre-similar-arrow">&rsaquo;</span></a>';
  }
  function injectSimilarListings() {
    var box = $('#IDX-detailsSimilar');
    if (!box) return;
    var txt = (box.textContent || '');
    var empty = /No listings found/i.test(txt) || !box.querySelector('a[href*="/idx/details/listing/"]');
    if (!empty || box.querySelector('.gre-similar')) return;

    var county  = fieldValue('IDX-field-countyName', 'County');          // "Queens"
    var subType = fieldValue('IDX-field-propSubType', 'Property Sub Type'); // "Single Family Residence"
    var city = '';
    var addr = $('.IDX-detailsAddress');
    if (addr) {
      var m = (addr.textContent || '').match(/,?\s*([A-Za-z .'-]+),\s*NY\s*\d{5}/);
      if (m) city = m[1].trim();
    }
    var priceSpan = $all('span, div').filter(function (e) { return /^\$[\d,]+$/.test((e.textContent || '').trim()); })[0];
    var price = priceSpan ? parseInt(priceSpan.textContent.replace(/[^\d]/g, ''), 10) : 0;

    if (!county && !city) return;
    function enc(v) { return encodeURIComponent(v).replace(/%20/g, '+'); }

    var cards = [];
    var statusSort = '&statusCategory=active&srt=newest';
    var geo = county ? 'county=' + enc(county) : 'city=' + enc(city);

    // Card 1 — full match: same county + price ±20% + same property sub-type
    if (price) {
      var lo = Math.round(price * 0.8), hi = Math.round(price * 1.2);
      var sub = subType ? '&a_propSubType%5B%5D=' + enc(subType) : '';
      var hrefP = IDX_BASE + '/idx/map/mapsearch&' + geo + '&lp=' + lo + '&hp=' + hi + sub + statusSort;
      cards.push(card(hrefP, ICONS.price, 'Similar homes nearby',
        money(lo) + ' – ' + money(hi) + (subType ? ' · ' + subType : '') + (county ? ' · ' + county + ' County' : '')));
    }
    // Card 2 — broad fallback: everything in the same county
    if (county) {
      cards.push(card(IDX_BASE + '/idx/map/mapsearch&county=' + enc(county) + statusSort,
        ICONS.county, 'More homes in ' + county + ' County', 'Browse all active listings'));
    }
    // Card 3 — same city/neighborhood
    if (city) {
      cards.push(card(IDX_BASE + '/idx/map/mapsearch&city=' + enc(city) + statusSort,
        ICONS.city, 'More homes in ' + city, 'Nearby active listings'));
    }
    if (!cards.length) return;

    // remove the "No listings found" node, keep any heading
    $all('*', box).forEach(function (el) {
      if (el.children.length === 0 && /No listings found/i.test((el.textContent || '').trim())) el.remove();
    });
    var wrap = document.createElement('div');
    wrap.className = 'gre-similar';
    wrap.innerHTML = '<div class="gre-similar-grid">' + cards.join('') + '</div>';
    box.appendChild(wrap);
  }

  // ── #1/#2/#5 FOOTER — relocate-to-bottom + defensive inject ──────────
  // The IDX Global Subheader renders near the TOP of the content region, so if
  // the footer HTML was pasted there we move it to the true page bottom. If no
  // footer is present at all (e.g. only the JS was pasted) we inject it.
  function injectFooter() {
    var existing = document.querySelector('.gre-compliance-footer');
    if (existing) {
      // already at the very end? leave it. otherwise relocate to body end.
      if (existing !== document.body.lastElementChild) document.body.appendChild(existing);
      return;
    }
    var EHO = '<svg viewBox="0 0 40 40" fill="none" aria-hidden="true">' +
      '<path d="M20 4 L4 17 H8 V35 H32 V17 H36 Z" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>' +
      '<rect x="13" y="22" width="14" height="2.8" rx="0.5" fill="currentColor"/>' +
      '<rect x="13" y="27.6" width="14" height="2.8" rx="0.5" fill="currentColor"/></svg>';
    var html =
      '<div class="gre-cf-inner">' +
        '<div class="gre-cf-top">' +
          '<div class="gre-cf-brand"><strong>Gadura Real Estate, LLC</strong>' +
            '<span class="gre-cf-license">Licensed Real Estate Broker, State of New York &middot; NYS License #10991238487 &middot; Supervising Broker: Vinod K. Gadura</span></div>' +
          '<div class="gre-cf-contact">106-09 101st Ave, Ozone Park, NY 11416 &middot; ' +
            '<a href="tel:' + PHONE_TEL + '">' + PHONE_DISP + '</a> &middot; ' +
            '<a href="mailto:nitin@gadurarealestate.com">nitin@gadurarealestate.com</a></div>' +
          '<div class="gre-cf-logos">' +
            '<span class="gre-eho-logo" role="img" aria-label="Equal Housing Opportunity">' + EHO +
              '<span>Equal Housing Opportunity</span></span>' +
            '<img class="gre-onekey-logo" src="' + BASE + '/images/onekey-mls-idx-logo.png" ' +
              'alt="OneKey MLS — IDX Participant" width="120" height="30" loading="lazy">' +
          '</div>' +
        '</div>' +
        '<p class="gre-cf-disclaimer">Listing data on this site comes in part from the Internet Data Exchange (IDX) program of OneKey® MLS. ' +
          'Real-estate listings held by brokerage firms other than Gadura Real Estate, LLC are marked with the OneKey® MLS logo; detailed ' +
          'information about them includes the name of the listing broker. IDX information is provided exclusively for consumers’ personal, ' +
          'non-commercial use and may not be used for any purpose other than to identify prospective properties. Information is deemed reliable ' +
          'but not guaranteed. © 2026 OneKey® MLS. All rights reserved. Equal Housing Opportunity.</p>' +
        '<nav class="gre-cf-links" aria-label="Legal links">' +
          '<a href="' + BASE + '/privacy-policy.html">Privacy Policy</a>' +
          '<a href="' + BASE + '/terms.html">Terms of Use</a>' +
          '<a href="' + BASE + '/fair-housing.html">Fair Housing</a>' +
          '<a href="' + BASE + '/accessibility.html">Accessibility</a>' +
          '<a href="' + BASE + '/idx-policy.html">IDX &amp; VOW Policy</a>' +
        '</nav>' +
        '<p class="gre-cf-copy">© 2026 Gadura Real Estate, LLC. All rights reserved. Regulated by the New York State Department of State, Division of Licensing Services.</p>' +
      '</div>';
    var footer = document.createElement('footer');
    footer.className = 'gre-compliance-footer';
    footer.setAttribute('role', 'contentinfo');
    footer.setAttribute('aria-label', 'Brokerage and compliance information');
    footer.innerHTML = html;
    document.body.appendChild(footer);
  }

  // ── orchestration ────────────────────────────────────────────────────
  function run() {
    [formatPhones, injectStatusBadge, injectFormNotice, fixRecaptcha, injectSimilarListings, injectFooter]
      .forEach(function (fn) { try { fn(); } catch (e) { /* never break IDX */ } });
  }

  function init() {
    run();
    var t = null;
    var obs = new MutationObserver(function () {
      clearTimeout(t);
      t = setTimeout(run, 250); // debounce IDX's async re-renders
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
