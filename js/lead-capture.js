/* ============================================================
   GADURA REAL ESTATE — Lead Capture System
   Exit-intent popup + Listing alert bar
   ============================================================ */

(function () {
  'use strict';

  var STORAGE_KEY = 'gre_popup_shown';
  var ALERT_KEY = 'gre_alert_dismissed';

  // ── Popup ────────────────────────────────────────────────
  function buildPopup() {
    var el = document.createElement('div');
    el.id = 'gre-popup';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Get New Listing Alerts');
    el.innerHTML = [
      '<div id="gre-popup-overlay"></div>',
      '<div id="gre-popup-card">',
      '  <button id="gre-popup-close" aria-label="Close">&times;</button>',
      '  <div style="font-size:32px;margin-bottom:12px;">🏠</div>',
      '  <h2 style="font-family:\'Playfair Display\',serif;color:#1B2A6B;font-size:1.5rem;margin:0 0 8px;">Get New Listing Alerts</h2>',
      '  <p style="color:#555;font-size:14px;margin:0 0 20px;line-height:1.6;">Be first to know when homes hit the market in Queens &amp; Long Island — before they sell.</p>',
      '  <form id="gre-popup-form">',
      '    <input type="email" id="gre-popup-email" placeholder="your@email.com" required style="width:100%;padding:11px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:10px;">',
      '    <select id="gre-popup-hood" style="width:100%;padding:11px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:10px;background:#fff;color:#333;">',
      '      <option value="">Neighborhood (optional)</option>',
      '      <option>Ozone Park</option>',
      '      <option>South Ozone Park</option>',
      '      <option>Richmond Hill</option>',
      '      <option>Jamaica</option>',
      '      <option>Howard Beach</option>',
      '      <option>Woodhaven</option>',
      '      <option>Middle Village</option>',
      '      <option>Valley Stream</option>',
      '      <option>Elmont</option>',
      '      <option>Other Queens / Long Island</option>',
      '    </select>',
      '    <select id="gre-popup-price" style="width:100%;padding:11px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:14px;background:#fff;color:#333;">',
      '      <option value="">Price Range (optional)</option>',
      '      <option>Under $500K</option>',
      '      <option>$500K – $750K</option>',
      '      <option>$750K – $1M</option>',
      '      <option>$1M+</option>',
      '    </select>',
      '    <button type="submit" style="width:100%;background:#00A651;color:#fff;border:none;padding:13px;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;font-family:Inter,sans-serif;">Alert Me to New Listings</button>',
      '  </form>',
      '  <div id="gre-popup-success" style="display:none;text-align:center;padding:20px 0;">',
      '    <div style="font-size:40px;margin-bottom:12px;">✅</div>',
      '    <h3 style="color:#1B2A6B;font-family:\'Playfair Display\',serif;">You\'re on the list!</h3>',
      '    <p style="color:#555;font-size:14px;">We\'ll notify you the moment a home matching your criteria hits the market.</p>',
      '  </div>',
      '  <p style="text-align:center;font-size:11px;color:#aaa;margin-top:12px;">No spam. Unsubscribe anytime.</p>',
      '</div>',
    ].join('\n');

    // Styles
    var style = document.createElement('style');
    style.textContent = [
      '#gre-popup-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:99998;}',
      '#gre-popup-card{position:fixed;bottom:0;left:50%;transform:translateX(-50%) translateY(100%);width:min(460px,96vw);background:#fff;border-radius:20px 20px 0 0;padding:32px 28px 28px;z-index:99999;box-shadow:0 -8px 40px rgba(0,0,0,.18);transition:transform .4s cubic-bezier(.16,1,.3,1);}',
      '#gre-popup-card.open{transform:translateX(-50%) translateY(0);}',
      '#gre-popup-close{position:absolute;top:14px;right:16px;background:none;border:none;font-size:24px;color:#aaa;cursor:pointer;line-height:1;}',
      '#gre-popup-close:hover{color:#333;}',
      '#gre-popup{display:none;}',
      '#gre-popup.visible{display:block;}',
    ].join('');
    document.head.appendChild(style);
    document.body.appendChild(el);

    // Events
    document.getElementById('gre-popup-overlay').addEventListener('click', closePopup);
    document.getElementById('gre-popup-close').addEventListener('click', closePopup);
    document.getElementById('gre-popup-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = document.getElementById('gre-popup-email').value;
      var hood = document.getElementById('gre-popup-hood').value;
      var price = document.getElementById('gre-popup-price').value;
      // Save locally
      localStorage.setItem('gre_subscriber', JSON.stringify({ email: email, hood: hood, price: price, ts: Date.now() }));
      // POST to Formspree (replace with real endpoint)
      fetch('https://formspree.io/f/xwkgjqpr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ email: email, neighborhood: hood, priceRange: price, source: 'popup' })
      }).catch(function () {});
      document.getElementById('gre-popup-form').style.display = 'none';
      document.getElementById('gre-popup-success').style.display = 'block';
      sessionStorage.setItem(STORAGE_KEY, '1');
      setTimeout(closePopup, 3000);
    });
  }

  function openPopup() {
    if (sessionStorage.getItem(STORAGE_KEY)) return;
    var el = document.getElementById('gre-popup');
    if (!el) return;
    el.classList.add('visible');
    setTimeout(function () {
      var card = document.getElementById('gre-popup-card');
      if (card) card.classList.add('open');
    }, 20);
    sessionStorage.setItem(STORAGE_KEY, '1');
  }

  function closePopup() {
    var card = document.getElementById('gre-popup-card');
    if (card) card.classList.remove('open');
    setTimeout(function () {
      var el = document.getElementById('gre-popup');
      if (el) el.classList.remove('visible');
    }, 400);
  }

  // ── Alert Bar ───────────────────────────────────────────
  function buildAlertBar() {
    if (sessionStorage.getItem(ALERT_KEY)) return;
    var bar = document.createElement('div');
    bar.id = 'gre-alert-bar';
    bar.innerHTML = [
      '<span style="font-size:13px;flex:1;">🏠 Get notified when new homes hit the market in Queens &amp; Long Island</span>',
      '<div style="display:flex;gap:10px;align-items:center;flex-shrink:0;">',
      '  <input type="email" id="gre-bar-email" placeholder="your@email.com" aria-label="Email for listing alerts" style="padding:7px 12px;border-radius:6px;border:none;font-size:13px;width:180px;">',
      '  <button id="gre-bar-btn" style="background:#00A651;color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;">Alert Me</button>',
      '  <button id="gre-bar-close" aria-label="Dismiss" style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:0 4px;opacity:.7;line-height:1;">&times;</button>',
      '</div>',
    ].join('');

    var barStyle = document.createElement('style');
    barStyle.textContent = '#gre-alert-bar{position:fixed;bottom:0;left:0;right:0;background:#1B2A6B;color:#fff;padding:10px 20px;display:flex;align-items:center;gap:16px;z-index:9997;font-family:Inter,sans-serif;box-shadow:0 -2px 16px rgba(0,0,0,.2);}@media(max-width:600px){#gre-alert-bar input{width:120px;}#gre-alert-bar span{display:none;}}';
    document.head.appendChild(barStyle);
    document.body.appendChild(bar);

    document.getElementById('gre-bar-close').addEventListener('click', function () {
      bar.remove();
      sessionStorage.setItem(ALERT_KEY, '1');
    });

    document.getElementById('gre-bar-btn').addEventListener('click', function () {
      var email = document.getElementById('gre-bar-email').value;
      if (!email || !email.includes('@')) { document.getElementById('gre-bar-email').focus(); return; }
      localStorage.setItem('gre_subscriber', JSON.stringify({ email: email, source: 'bar', ts: Date.now() }));
      fetch('https://formspree.io/f/xwkgjqpr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ email: email, source: 'alert-bar' })
      }).catch(function () {});
      bar.innerHTML = '<span style="font-size:14px;font-weight:600;text-align:center;width:100%;">✅ You\'re on the list! We\'ll alert you to new listings.</span>';
      setTimeout(function () { bar.remove(); sessionStorage.setItem(ALERT_KEY, '1'); }, 3000);
    });
  }

  // ── Init ────────────────────────────────────────────────
  function init() {
    buildPopup();
    buildAlertBar();

    // Show popup: 45s delay OR exit intent
    var timer = setTimeout(openPopup, 45000);

    document.addEventListener('mouseleave', function handler(e) {
      if (e.clientY < 10) {
        clearTimeout(timer);
        openPopup();
        document.removeEventListener('mouseleave', handler);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
