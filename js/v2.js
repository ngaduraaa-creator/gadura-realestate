/* ============================================================
   Gadura Real Estate — v2 interactions
   ============================================================ */
(function () {
  'use strict';

  /* ---- Year ---- */
  var yr = document.getElementById('yr');
  if (yr) yr.textContent = new Date().getFullYear();

  /* ---- Header scrolled state ---- */
  var header = document.getElementById('siteHeader');
  var onScroll = function () {
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 20);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- Mobile drawer ---- */
  var drawer = document.getElementById('mobileDrawer');
  var backdrop = document.getElementById('drawerBackdrop');
  var openBtn = document.getElementById('hamburger');
  var closeBtn = document.getElementById('mobileClose');
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
    if (openBtn) openBtn.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  }
  if (openBtn) openBtn.addEventListener('click', function () { setDrawer(true); });
  if (closeBtn) closeBtn.addEventListener('click', function () { setDrawer(false); });
  if (backdrop) backdrop.addEventListener('click', function () { setDrawer(false); });
  if (drawer) drawer.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { setDrawer(false); });
  });

  /* ---- Hero slideshow ---- */
  var slides = document.querySelectorAll('#heroMedia .slide');
  if (slides.length > 1 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var i = 0;
    setInterval(function () {
      slides[i].classList.remove('active');
      i = (i + 1) % slides.length;
      slides[i].classList.add('active');
    }, 6000);
  }

  /* ---- Search intent tabs (Buy / Sell / Rent) ---- */
  var stabs = document.querySelectorAll('.search-tabs .stab');
  if (stabs.length) {
    stabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var panel = tab.getAttribute('data-panel');
        stabs.forEach(function (t) { t.classList.toggle('active', t === tab); });
        document.querySelectorAll('.searchbar .search-panel').forEach(function (p) {
          p.classList.toggle('active', p.getAttribute('data-panel') === panel);
        });
      });
    });
  }

  /* ---- IDX search → live IDX Broker map search ----
     Confirmed-working params (from existing site links):
       city, county, statusCategory, srt,
       a_propSubType[], a_numUnitsTotal[]
     Beds / baths / max-price are passed through with the form's
     own field names (bd_low / tb_low / hp). IDX Broker ignores
     params it doesn't recognise, so an unknown key never errors —
     worst case the user lands on a valid location/type result and
     refines on the IDX side. Adjust TYPE_MAP/RANGE if the live
     IDX uses different keys.
  */
  var IDX_BASE = 'https://homes.gadurarealestate.com/idx/map/mapsearch';
  var TYPE_MAP = {
    sfr:    { 'a_propSubType[]': 'Single Family Residence' },
    multi2: { 'a_numUnitsTotal[]': '2' },
    multi3: { 'a_numUnitsTotal[]': '3' },
    condo:  { 'a_propSubType[]': 'Condominium' }
  };
  var form = document.getElementById('idxSearch');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var params = new URLSearchParams();
      params.set('statusCategory', 'active');
      params.set('srt', 'newest');

      var loc = form.querySelector('#sf-loc');
      if (loc && loc.value.trim()) params.set('city', loc.value.trim());

      var type = form.querySelector('#sf-type');
      if (type && type.value && TYPE_MAP[type.value]) {
        var map = TYPE_MAP[type.value];
        Object.keys(map).forEach(function (k) { params.append(k, map[k]); });
      }

      ['sf-beds', 'sf-baths', 'sf-price'].forEach(function (id) {
        var el = form.querySelector('#' + id);
        if (el && el.value && el.name) params.set(el.name, el.value);
      });

      window.location.href = IDX_BASE + '?' + params.toString();
    });
  }

  /* ---- Scroll reveal ---- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (r) { io.observe(r); });
  } else {
    reveals.forEach(function (r) { r.classList.add('in'); });
  }

  /* ---- Exit-intent / delayed lead modal (once per session) ---- */
  var modal = document.getElementById('leadModal');
  var modalClose = document.getElementById('modalClose');
  var shown = false;
  function showModal() {
    if (shown || !modal) return;
    if (sessionStorage.getItem('gre_lead_modal')) return;
    shown = true;
    modal.classList.add('open');
    sessionStorage.setItem('gre_lead_modal', '1');
  }
  function hideModal() { if (modal) modal.classList.remove('open'); }
  if (modal) {
    if (modalClose) modalClose.addEventListener('click', hideModal);
    modal.addEventListener('click', function (e) { if (e.target === modal) hideModal(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideModal(); });
    // Desktop: exit intent. Mobile: 25s dwell.
    document.addEventListener('mouseout', function (e) {
      if (e.clientY <= 0) showModal();
    });
    setTimeout(showModal, 25000);
  }
})();
