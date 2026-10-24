/* =========================================================
   GADURA REAL ESTATE — MOBILE NAV (standalone)
   For pages that have a hamburger menu but do not load js/main.js.
   The block below is a byte-identical copy of the MOBILE NAV block in js/main.js.
   ========================================================= */

/* ---- MOBILE NAV ---- */
/* js/mobile-nav.js carries this same block for pages that do not load main.js; keep the two identical. */
(function(){
  if (window.__greMobileNav) return;
  var ham = document.querySelector('.hamburger');
  if (!ham) return;
  // Menu: the .mobile-nav overlay if the page has one, else the header <nav id="nav">, else the element the
  // hamburger's aria-controls names. css/style.css collapses #nav at <=768px only when scripting is enabled,
  // so with JavaScript off the header links stay inline.
  var overlay = document.querySelector('.mobile-nav');
  var ctl = ham.getAttribute('aria-controls');
  var menu = overlay || document.getElementById('nav') || (ctl ? document.getElementById(ctl) : null);
  if (!menu) return;
  // css/style.css failsafe: if this script arrives after the 8s fallback has already shown the header links inline
  // and hidden the hamburger, leave the page in that state instead of collapsing it again.
  if (getComputedStyle(document.documentElement).getPropertyValue('--gre-nav-failsafe').trim()) return;
  window.__greMobileNav = true;
  var header = ham.closest ? ham.closest('header') : null;
  var closeBtn = menu.querySelector('.mobile-close');
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  var mq = window.matchMedia ? window.matchMedia('(max-width: 768px)') : null;
  function isOpen(){ return menu.classList.contains('open') || menu.classList.contains('is-open'); }
  function place(open){ // fit the open menu between the header and the bottom of the screen
    var s = menu.style, vh = window.visualViewport ? window.visualViewport.height : document.documentElement.clientHeight;
    if (!open) { if (overlay) { s.top = s.bottom = s.height = ''; } else { s.maxHeight = ''; } return; }
    if (overlay) { // starts below the header, so the hamburger stays visible as a close control
      var t = header ? Math.max(0, Math.round(header.getBoundingClientRect().bottom)) : 0;
      s.top = t + 'px'; s.bottom = 'auto'; s.height = Math.max(0, Math.round(vh - t)) + 'px';
    } else if (getComputedStyle(menu).overflowY !== 'visible') {
      s.maxHeight = Math.max(160, Math.round(vh - menu.getBoundingClientRect().top)) + 'px';
    }
  }
  function focusables(){ // hamburger first, then the menu's visible controls
    var list = [ham];
    Array.prototype.forEach.call(menu.querySelectorAll(FOCUSABLE), function(el){ if (el.getClientRects().length) list.push(el); });
    return list;
  }
  function setNav(open, refocus){
    menu.classList.toggle('open', open);
    if (!open) menu.classList.remove('is-open'); // some pages' own inline script also toggles .is-open
    place(open);
    if (overlay) document.body.style.overflow = open ? 'hidden' : '';
    document.documentElement.classList.toggle('nav-open', open); // css lifts a header that contains the overlay
    ham.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var first = menu.querySelector('a[href]'); if (first) first.focus({ preventScroll: true }); }
    else if (refocus) ham.focus({ preventScroll: true });
  }
  if (menu.id) ham.setAttribute('aria-controls', menu.id);
  ham.setAttribute('aria-expanded', isOpen() ? 'true' : 'false');
  document.documentElement.classList.add('nav-js');
  // Capture phase: read the state before any page-level click handler on the button has changed it.
  var wasOpen = false;
  document.addEventListener('click', function(e){ if (ham.contains(e.target)) wasOpen = isOpen(); }, true);
  ham.addEventListener('click', function(){ setNav(!wasOpen, true); });
  if (closeBtn) closeBtn.addEventListener('click', function(){ setNav(false, true); });
  document.addEventListener('click', function(e){ // a tap outside the menu, or on one of its links, closes it
    if (!isOpen() || ham.contains(e.target) || (closeBtn && closeBtn.contains(e.target))) return;
    var link = e.target.closest ? e.target.closest('a[href]') : null;
    if (!menu.contains(e.target) || (link && menu.contains(link))) setNav(false, false);
  });
  document.addEventListener('keydown', function(e){
    if (!isOpen()) return;
    if (e.key === 'Escape' || e.key === 'Esc') { setNav(false, true); return; }
    if (e.key !== 'Tab') return;
    var list = focusables(), n = list.length, i = list.indexOf(document.activeElement);
    e.preventDefault(); // keep keyboard focus inside the open menu
    list[i < 0 ? (e.shiftKey ? n - 1 : 0) : (i + (e.shiftKey ? n - 1 : 1)) % n].focus();
  });
  window.addEventListener('resize', function(){ if (isOpen()) { if (mq && !mq.matches) setNav(false, false); else place(true); } });
})();
