/* ════════════════════════════════════════════════════════════════════════
   Gadura Real Estate — IDX Broker Compliance JavaScript
   File: listing-detail-overrides.js
   Apply in: IDX Broker → Design → Website → Subheaders → Level "Global" →
             "Turn WYSIWYG Off", wrapped in <script>…</script>.
             Runs on EVERY IDX page (detail + search/map results).

   Implements compliance fixes:
     #3 Phone formatting    9177050132 -> (917) 705-0132 / tel:+19177050132
     #4 Status badge        prominent colour-coded badge by address + price
     #6 SHIELD notice        "By submitting this form…" above every contact form
     #7 reCAPTCHA disclosure  enforce correct text + Google policy links
     #8 Similar Listings      replace "No listings found" with same-origin
                              deep-link cards (county / price ±20% / same type)
     #1/#2/#5 Footer          relocate the global footer to the page bottom, or
                              inject it defensively, with EHO + license + OneKey

   Safety (hardened after adversarial review):
     • idempotent — presence/dataset guards on every injection
     • phone rewrite is SCOPED to contact containers (never the whole body),
       so it can't corrupt MLS numbers / listing IDs
     • similar-listings text is HTML-escaped (no DOM-XSS from MLS fields)
     • MutationObserver suppresses its own mutations + disconnects around runs
       (no infinite loop / churn), debounced
     • each fix wrapped in try/catch so one failure never breaks IDX
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
  function topPriceSpan() {
    return $all('span, div').filter(function (e) {
      return e.childElementCount === 0 && /^\$[\d,]+$/.test((e.textContent || '').trim());
    })[0] || null;
  }

  // ── #3 PHONE FORMATTING (scoped — never scans the whole body) ─────────
  function formatPhones() {
    // tel: links anywhere are safe to normalise
    $all('a[href^="tel:"]').forEach(function (a) {
      if ((a.getAttribute('href') || '').replace(/\D/g, '') === PHONE_RAW) a.setAttribute('href', 'tel:' + PHONE_TEL);
      if ((a.textContent || '').replace(/\D/g, '') === PHONE_RAW) a.textContent = PHONE_DISP;
    });
    // bare-text replacement ONLY inside known contact/footer containers, once each
    $all('#IDX-contactInfo, .IDX-contactInfo, .IDX-contact-information, .gre-compliance-footer').forEach(function (scope) {
      if (scope.getAttribute('data-gre-phone') === '1') return;
      var walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, null);
      var nodes = [], n;
      while ((n = walker.nextNode())) {
        if (n.nodeValue.indexOf(PHONE_RAW) > -1 && n.parentNode &&
            !/SCRIPT|STYLE|TEXTAREA|INPUT|SELECT|OPTION/.test(n.parentNode.nodeName)) nodes.push(n);
      }
      nodes.forEach(function (node) { node.nodeValue = node.nodeValue.split(PHONE_RAW).join(PHONE_DISP); });
      scope.setAttribute('data-gre-phone', '1');
    });
  }

  // ── #4 STATUS BADGE (by address + price; refreshes on listing change) ─
  function injectStatusBadge() {
    var addrEl = $('#IDX-detailsAddressStreet') || $('.IDX-detailsAddress');
    if (!addrEl) return; // detail pages only — no work on search/map pages
    var addrKey = (addrEl.textContent || '').replace(/\s+/g, ' ').trim();

    var existing = $('.gre-status-badge');
    if (existing && existing.getAttribute('data-gre-for') === addrKey) return; // current
    if (existing) existing.parentNode && existing.parentNode.removeChild(existing); // stale

    var statusEl = $('.IDX-field-propStatus');
    var status = statusEl ? (statusEl.textContent || '').replace(/\s+/g, ' ').replace(/^Status\s*/i, '').trim() : '';
    if (!status) {
      var scope = $('#IDX-detailsAside') || addrEl.parentNode || document;
      var span = $all('.IDX-text, span', scope).filter(function (s) {
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
    badge.textContent = status;                 // textContent — no XSS
    badge.setAttribute('data-gre-for', addrKey);

    // place beside the price if present, else right after the address line
    var price = topPriceSpan();
    var anchor = price || addrEl;
    anchor.parentNode.insertBefore(badge, anchor.nextSibling);
  }

  // ── #6 SHIELD ACT FORM NOTICE ────────────────────────────────────────
  function injectFormNotice() {
    var forms = $all('#IDX-detailscontactContactForm, form.IDX-contactForm, .IDX-contactForm');
    $all('form').forEach(function (f) {
      if (forms.indexOf(f) < 0 &&
          f.querySelector('input[name="email"], input[type="email"], input.IDX-form__element--PL')) forms.push(f);
    });
    forms.forEach(function (form) {
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

  // ── #7 reCAPTCHA DISCLOSURE FIX (idempotent, only when broken) ────────
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
  // IDX Broker's map search uses a literal "&" after the path (verified live:
  // /idx/map/mapsearch&county=Queens&lp=…&hp=… renders filtered results). This
  // is IDX's URL convention, not a query string — do NOT change "&" to "?".
  var ICONS = {
    county: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M5 21V7l8-4 8 4v14M9 9h.01M9 13h.01M9 17h.01M15 9h.01M15 13h.01M15 17h.01"/></svg>',
    price:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    city:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M9 21V8l-6 4M9 8l6-4 6 4M21 21V8M14 21v-4h-4v4"/></svg>'
  };
  function money(n) { return '$' + Number(n).toLocaleString('en-US'); }
  function enc(v) { return encodeURIComponent(v).replace(/%20/g, '+'); }
  // Build a card as a DOM node. All MLS-sourced text goes in via textContent,
  // so a hostile/garbage field like county = 'Queens<img src=x onerror=…>' is
  // rendered as literal text and can NEVER execute (no innerHTML for dynamic
  // data). innerHTML is used only for the static, hard-coded icon SVG.
  function makeCard(href, iconSvg, title, sub) {
    var a = document.createElement('a');
    a.className = 'gre-similar-card';
    a.href = href;              // always our own https://homes.gadurarealestate.com/idx/… URL
    a.target = '_blank';
    a.rel = 'noopener';

    var iconWrap = document.createElement('span');
    iconWrap.className = 'gre-similar-icon';
    iconWrap.innerHTML = iconSvg;            // static constant — no dynamic data

    var textWrap = document.createElement('span');
    textWrap.className = 'gre-similar-text';
    var t = document.createElement('span');
    t.className = 'gre-similar-title';
    t.textContent = title;                   // MLS-sourced → textContent (safe)
    var s = document.createElement('span');
    s.className = 'gre-similar-sub';
    s.textContent = sub;                     // MLS-sourced → textContent (safe)
    textWrap.appendChild(t);
    textWrap.appendChild(s);

    var arrow = document.createElement('span');
    arrow.className = 'gre-similar-arrow';
    arrow.textContent = '›';            // ›

    a.appendChild(iconWrap);
    a.appendChild(textWrap);
    a.appendChild(arrow);
    return a;
  }
  function injectSimilarListings() {
    var box = $('#IDX-detailsSimilar');
    if (!box) return;
    var empty = /No listings found/i.test(box.textContent || '') || !box.querySelector('a[href*="/idx/details/listing/"]');
    if (!empty || box.querySelector('.gre-similar')) return;

    var county  = fieldValue('IDX-field-countyName', 'County');            // "Queens"
    var subType = fieldValue('IDX-field-propSubType', 'Property Sub Type'); // "Single Family Residence"
    var city = '';
    var addr = $('.IDX-detailsAddress');
    if (addr) {
      var m = (addr.textContent || '').match(/,?\s*([A-Za-z .'-]+),\s*NY\s*\d{5}/);
      if (m) city = m[1].trim();
    }
    var price = topPriceSpan() ? parseInt(topPriceSpan().textContent.replace(/[^\d]/g, ''), 10) : 0;
    if (!county && !city) return;

    var cards = [];
    var statusSort = '&statusCategory=active&srt=newest';
    var geo = county ? 'county=' + enc(county) : 'city=' + enc(city);

    // Card 1 — full match: same county + price ±20% + same sub-type
    if (price) {
      var lo = Math.round(price * 0.8), hi = Math.round(price * 1.2);
      var sub = subType ? '&a_propSubType%5B%5D=' + enc(subType) : '';
      var hrefP = IDX_BASE + '/idx/map/mapsearch&' + geo + '&lp=' + lo + '&hp=' + hi + sub + statusSort;
      cards.push(makeCard(hrefP, ICONS.price, 'Similar homes nearby',
        money(lo) + ' – ' + money(hi) + (subType ? ' · ' + subType : '') + (county ? ' · ' + county + ' County' : '')));
    }
    // Card 2 — broad fallback: same county
    if (county) {
      cards.push(makeCard(IDX_BASE + '/idx/map/mapsearch&county=' + enc(county) + statusSort,
        ICONS.county, 'More homes in ' + county + ' County', 'Browse all active listings'));
    }
    // Card 3 — same city / neighborhood
    if (city) {
      cards.push(makeCard(IDX_BASE + '/idx/map/mapsearch&city=' + enc(city) + statusSort,
        ICONS.city, 'More homes in ' + city, 'Nearby active listings'));
    }
    if (!cards.length) return;

    $all('*', box).forEach(function (el) {
      if (el.children.length === 0 && /No listings found/i.test((el.textContent || '').trim())) el.remove();
    });
    var grid = document.createElement('div');
    grid.className = 'gre-similar-grid';
    cards.forEach(function (c) { grid.appendChild(c); });
    var wrap = document.createElement('div');
    wrap.className = 'gre-similar';
    wrap.appendChild(grid);
    box.appendChild(wrap);
  }

  // ── OneKey logo onerror → text fallback (never show a broken image) ──
  function wireOneKeyFallback() {
    $all('img.gre-onekey-logo').forEach(function (img) {
      if (img.getAttribute('data-gre-wired')) return;
      img.setAttribute('data-gre-wired', '1');
      img.onerror = function () {
        if (!this.parentNode) return;
        var span = document.createElement('span');
        span.className = 'gre-onekey-text';
        span.textContent = 'OneKey® MLS';
        this.parentNode.replaceChild(span, this);
      };
    });
  }

  // ── #1/#2/#5 FOOTER — relocate-to-bottom (once) + defensive inject ───
  function injectFooter() {
    var existing = document.querySelector('.gre-compliance-footer');
    if (existing) {
      if (!existing.getAttribute('data-gre-relocated')) {
        existing.setAttribute('data-gre-relocated', '1');
        var bubble = document.getElementById('gre-wa-bubble');
        if (bubble && bubble.parentNode === document.body) document.body.insertBefore(existing, bubble);
        else document.body.appendChild(existing);
      }
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
            '<span class="gre-cf-license">Licensed Real Estate Broker, State of New York &middot; NYS Firm Broker License #10991238487 &middot; Supervising Broker: Vinod K. Gadura</span></div>' +
          '<div class="gre-cf-contact">106-09 101st Ave, Ozone Park, NY 11416 &middot; ' +
            '<a href="tel:' + PHONE_TEL + '">' + PHONE_DISP + '</a> &middot; ' +
            '<a href="mailto:nitin@gadurarealestate.com">nitin@gadurarealestate.com</a></div>' +
          '<div class="gre-cf-logos">' +
            '<span class="gre-eho-logo" role="img" aria-label="Equal Housing Opportunity">' + EHO +
              '<span>Equal Housing Opportunity</span></span>' +
            '<img class="gre-onekey-logo" src="' + BASE + '/images/onekey-mls-idx-logo.png" ' +
              'alt="OneKey MLS — IDX Participant" width="120" height="32" loading="lazy">' +
          '</div>' +
        '</div>' +
        '<p class="gre-cf-disclaimer">The data relating to real estate for sale on this website comes in part from the Internet Data Exchange (IDX) Program of OneKey® MLS. ' +
          'Real-estate listings held by brokerage firms other than Gadura Real Estate, LLC are marked with the OneKey® MLS logo; detailed information about them includes the name of the listing broker. ' +
          'This information is provided exclusively for consumers’ personal, non-commercial use and may not be used for any purpose other than to identify prospective properties consumers may be interested in purchasing. ' +
          'All information is deemed reliable but not guaranteed and should be independently verified. © 2026 OneKey® MLS. All rights reserved. Equal Housing Opportunity.</p>' +
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
    footer.setAttribute('data-gre-relocated', '1');
    footer.innerHTML = html;
    document.body.appendChild(footer);
  }

  // ── Remove IDX forced "You must register to view this page" gate ──────
  // The site owner does not want mandatory registration blocking visitors.
  // PERMANENT fix is the IDX dashboard (Account → Lead Management →
  // Registration → "off" / unlimited views); this dismisses the modal client-
  // side as a fallback, scoped strictly to the registration dialog + overlay.
  // NOTE: only for standard IDX data. If any feed is VOW (registration required
  // by MLS rule), do NOT use this — remove this function from the pipeline.
  function dismissRegistration() {
    var marks = $all('.IDX-registrationModal, .IDX-registration-force, .IDX-registration');
    if (!marks.length) return;
    marks.forEach(function (m) {
      var dialog = (m.closest && m.closest('.ui-dialog')) || m;
      if (dialog && dialog.parentNode) dialog.parentNode.removeChild(dialog);
    });
    $all('.ui-widget-overlay').forEach(function (o) { o.parentNode && o.parentNode.removeChild(o); });
    // restore scrolling IDX locks while the modal is open
    if (document.documentElement) document.documentElement.style.overflow = '';
    if (document.body) document.body.style.overflow = '';
  }

  // ── orchestration ────────────────────────────────────────────────────
  var observer = null, timer = null;
  function run() {
    if (observer) observer.disconnect(); // suppress our own mutations
    [dismissRegistration, formatPhones, injectStatusBadge, injectFormNotice, fixRecaptcha,
     injectSimilarListings, wireOneKeyFallback, injectFooter]
      .forEach(function (fn) { try { fn(); } catch (e) { /* never break IDX */ } });
    if (observer) observer.observe(document.body, { childList: true, subtree: true });
  }

  function isOurNode(node) {
    return node.nodeType === 1 &&
      ((node.className && String(node.className).indexOf('gre-') > -1) || node.id === 'gre-wa-bubble');
  }
  function init() {
    run();
    observer = new MutationObserver(function (muts) {
      // ignore mutations that only added/removed our own gre- nodes
      var meaningful = muts.some(function (m) {
        var added = Array.prototype.some.call(m.addedNodes, function (nd) { return nd.nodeType === 1 && !isOurNode(nd); });
        return added || m.removedNodes.length > 0;
      });
      if (!meaningful) return;
      clearTimeout(timer);
      timer = setTimeout(run, 300); // debounce IDX's async re-renders
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
