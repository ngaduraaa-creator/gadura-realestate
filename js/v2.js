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
  function drawerFocusables() {
    return drawer ? Array.prototype.slice.call(drawer.querySelectorAll('a[href], button:not([disabled])')) : [];
  }
  function setDrawer(open) {
    if (!drawer) return;
    var wasOpen = drawer.classList.contains('open');
    drawer.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
    if (openBtn) openBtn.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
    if (open && !wasOpen && closeBtn) closeBtn.focus({ preventScroll: true });
    if (!open && wasOpen && openBtn && drawer.contains(document.activeElement)) openBtn.focus({ preventScroll: true });
  }
  if (openBtn && drawer) openBtn.setAttribute('aria-controls', 'mobileDrawer');
  document.addEventListener('keydown', function (e) {
    if (!drawer || !drawer.classList.contains('open')) return;
    if (e.key === 'Escape') {
      setDrawer(false);
      if (openBtn) openBtn.focus();
      return;
    }
    if (e.key !== 'Tab') return;
    var f = drawerFocusables();
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1], active = document.activeElement;
    if (!drawer.contains(active)) { e.preventDefault(); first.focus(); }
    else if (e.shiftKey && active === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && active === last) { e.preventDefault(); first.focus(); }
  });
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

  /* ---- IDX search ----
     NOTE: This IDX Broker account ignores URL filter params on both the map
     (/idx/map/mapsearch) and results (/idx/results/listings) endpoints —
     verified 2026-06-25: city / county / bd / tb / hp / pt all return the same
     unfiltered ~500-listing regional map, and the results endpoint returns a
     2-listing fallback. So the homepage search is a GATEWAY: the Buy/Rent forms
     submit natively to the live map search where users refine with the IDX's
     own (working) in-page filters. To enable true filtered deep-links, fix the
     IDX Broker account (searchable Areas / Saved Links / MLS feed permissions).
  */

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
