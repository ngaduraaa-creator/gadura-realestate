/* Gadura v2 — shared site scripts */

// ============================================================
// MULTILINGUAL — Google Translate Auto-Integration
// ============================================================
(function() {
  // Inject hidden Google Translate element container
  window.addEventListener('DOMContentLoaded', function() {
    var div = document.createElement('div');
    div.id = 'google_translate_element';
    div.style.cssText = 'position:fixed;bottom:70px;right:16px;z-index:9999;display:none;';
    document.body.appendChild(div);
  });

  // Google Translate initialization callback
  window.googleTranslateElementInit = function() {
    new google.translate.TranslateElement({
      pageLanguage: 'en',
      includedLanguages: 'es,hi,pa,ur,bn,zh-TW,ko,pt,ar,tl',
      layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
      autoDisplay: false,
      multilanguagePage: false
    }, 'google_translate_element');
  };

  // Switch to a specific language
  window.switchLanguage = function(langCode) {
    localStorage.setItem('gadura_lang', langCode);
    var selectEl = document.querySelector('.goog-te-combo');
    if (selectEl) {
      selectEl.value = langCode;
      selectEl.dispatchEvent(new Event('change'));
    } else {
      document.cookie = 'googtrans=/en/' + langCode + ';path=/;domain=' + window.location.hostname;
      document.cookie = 'googtrans=/en/' + langCode + ';path=/';
      window.location.reload();
    }
    // Mark active language
    document.querySelectorAll('.topbar-right a[lang]').forEach(function(l) {
      l.classList.toggle('lang-active', l.getAttribute('data-lang') === langCode);
    });
  };

  // Wire up language switcher links
  window.addEventListener('DOMContentLoaded', function() {
    var langMap = {'es':'es','hi':'hi','bn':'bn','pa':'pa','ur':'ur'};
    document.querySelectorAll('.langs a[lang]').forEach(function(link) {
      var code = link.getAttribute('lang');
      if (langMap[code]) {
        link.setAttribute('data-lang', langMap[code]);
        link.addEventListener('click', function(e) {
          e.preventDefault();
          window.switchLanguage(langMap[code]);
        });
      }
    });

    // Restore saved language preference
    var saved = localStorage.getItem('gadura_lang');
    if (saved && saved !== 'en') {
      setTimeout(function() {
        var sel = document.querySelector('.goog-te-combo');
        if (sel) { sel.value = saved; sel.dispatchEvent(new Event('change')); }
      }, 1200);
    }
  });

  // Load Google Translate script
  window.addEventListener('DOMContentLoaded', function() {
    var s = document.createElement('script');
    s.src = '//translate.googleapis.com/translate_a/element.js?cb=googleTranslateElementInit';
    s.async = true;
    document.head.appendChild(s);

    // Suppress Google Translate toolbar (keeps site design clean)
    var style = document.createElement('style');
    style.textContent = [
      '.goog-te-banner-frame{display:none!important}',
      '.skiptranslate{display:none!important}',
      'body{top:0!important}',
      '#google_translate_element .goog-te-gadget{font-size:0}',
      '.topbar-right a.lang-active{color:var(--saffron)!important;font-weight:700;text-decoration:underline}'
    ].join('\n');
    document.head.appendChild(style);
  });
})();

(function () {
  'use strict';

  /* -------------------------------------------------------------
     STICKY MOBILE CALL BAR
     Appears after user scrolls past the hero on mobile.
     ------------------------------------------------------------- */
  const stickyCall = document.querySelector('.sticky-call');
  if (stickyCall) {
    const showAfter = 400; // px of scroll before it appears
    const onScroll = () => {
      if (window.scrollY > showAfter) {
        stickyCall.classList.add('visible');
      } else {
        stickyCall.classList.remove('visible');
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* -------------------------------------------------------------
     MOBILE MENU
     ------------------------------------------------------------- */
  const toggle = document.querySelector('.mobile-toggle');
  const menu = document.querySelector('.mobile-menu');
  const close = document.querySelector('.mobile-menu .close');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      menu.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  }
  if (close && menu) {
    close.addEventListener('click', () => {
      menu.classList.remove('open');
      document.body.style.overflow = '';
    });
  }

  /* -------------------------------------------------------------
     HERO SEARCH TABS (buy / sell / rent)
     ------------------------------------------------------------- */
  const tabs = document.querySelectorAll('.tabs .tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const panels = document.querySelectorAll('.tab-panel');
      panels.forEach(p => p.hidden = true);
      const target = document.getElementById(tab.dataset.panel);
      if (target) target.hidden = false;
    });
  });

  /* -------------------------------------------------------------
     FORM SUBMISSION
     Honeypot-protected. Sends to the FormSubmit AJAX endpoint.
     ------------------------------------------------------------- */
/* ---- FORM OUTCOME (shared by the forms below) ----
   The form service accepting a request is not proof that it reached an inbox,
   so success copy says only that the request was submitted to the form service.
   Any non-ok response, unaccepted body, network error or timeout shows a visible
   error. The phone and email offered as alternatives are read from the contact
   links this page already displays; nothing here hardcodes contact details. */
var greForm = (function(){
  var TIMEOUT_MS = 15000;
  var PHONE_RE = /\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}/;
  function pageContacts(form){
    var out = {}, i, a, m, addr;
    var tels = document.querySelectorAll('a[href^="tel:"]');
    for (i = 0; i < tels.length && !out.tel; i++){
      a = tels[i];
      if (form.contains(a)) continue;
      m = (a.textContent || '').match(PHONE_RE);
      if (m && (a.getAttribute('href') || '').replace(/\D/g, '').slice(-10) === m[0].replace(/\D/g, '').slice(-10)) {
        out.tel = { href: a.getAttribute('href'), text: m[0] };
      }
    }
    var mails = document.querySelectorAll('a[href^="mailto:"]');
    for (i = 0; i < mails.length && !out.mail; i++){
      a = mails[i];
      if (form.contains(a)) continue;
      addr = (a.getAttribute('href') || '').slice(7).split('?')[0];
      if (addr && (a.textContent || '').toLowerCase().indexOf(addr.toLowerCase()) !== -1) {
        out.mail = { href: 'mailto:' + addr, text: addr };
      }
    }
    return out;
  }
  function link(href, text){ var a = document.createElement('a'); a.href = href; a.textContent = text; return a; }
  function text(s){ return document.createTextNode(s); }
  function altLine(c, lead){
    var p = document.createElement('p');
    p.appendChild(text(lead + ' '));
    if (c.tel) { p.appendChild(text('call ')); p.appendChild(link(c.tel.href, c.tel.text)); }
    if (c.tel && c.mail) p.appendChild(text(' or '));
    if (c.mail) { p.appendChild(text('email ')); p.appendChild(link(c.mail.href, c.mail.text)); }
    if (!c.tel && !c.mail) { p.appendChild(text('use our ')); p.appendChild(link('/contact.html', 'contact page')); }
    p.appendChild(text('.'));
    return p;
  }
  function outcome(c, ok){
    var d = document.createElement('div');
    d.className = 'form-outcome ' + (ok ? 'form-outcome-ok' : 'form-outcome-fail');
    d.setAttribute('role', ok ? 'status' : 'alert');
    d.style.cssText = 'margin-top:12px;padding:16px;border-radius:6px;text-align:left;' +
      (ok ? 'background:#eef6f0;color:#14361f;border:1px solid #9cc7a8;' : 'background:#fdecec;color:#5c1111;border:1px solid #e3a3a3;');
    var h = document.createElement('p');
    h.style.cssText = 'font-weight:700;margin:0 0 6px;';
    if (ok) {
      h.textContent = 'Your request was submitted to our form service.';
      d.appendChild(h);
      var n = document.createElement('p');
      n.textContent = 'This does not confirm that it has reached our office.';
      d.appendChild(n);
      d.appendChild(altLine(c, 'If you would rather talk now, or you do not hear back,'));
    } else {
      h.textContent = 'We could not confirm that your request was submitted.';
      d.appendChild(h);
      d.appendChild(altLine(c, 'Please try again, or'));
    }
    var ps = d.getElementsByTagName('p');
    for (var i = 1; i < ps.length; i++) ps[i].style.margin = '0 0 6px';
    var as = d.getElementsByTagName('a');
    for (var j = 0; j < as.length; j++) { as[j].style.color = 'inherit'; as[j].style.fontWeight = '700'; as[j].style.textDecoration = 'underline'; }
    return d;
  }
  function send(form, url, body, btn, onAccepted){
    if (form.getAttribute('data-sending') === '1') return;
    form.setAttribute('data-sending', '1');
    var contacts = pageContacts(form);
    var prior = form.querySelector('.form-outcome-fail');
    if (prior) prior.parentNode.removeChild(prior);
    var orig = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.setAttribute('aria-busy', 'true'); btn.textContent = 'Sending…'; }
    var done = false;
    var ctrl = (typeof AbortController === 'function') ? new AbortController() : null;
    var timer = setTimeout(function(){ if (ctrl) ctrl.abort(); fail(); }, TIMEOUT_MS);
    function fail(){
      if (done) return; done = true; clearTimeout(timer);
      form.removeAttribute('data-sending');
      if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); btn.textContent = orig; }
      form.appendChild(outcome(contacts, false));
    }
    function accepted(){
      if (done) return; done = true; clearTimeout(timer);
      while (form.firstChild) form.removeChild(form.firstChild);
      form.appendChild(outcome(contacts, true));
      if (onAccepted) onAccepted();
    }
    var opts = { method: 'POST', body: body, headers: { 'Accept': 'application/json' } };
    if (ctrl) opts.signal = ctrl.signal;
    fetch(url, opts)
      .then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function(d){ if (d && (d.success === true || d.success === 'true')) accepted(); else fail(); })
      .catch(fail);
  }
  return { send: send };
})();
  const FORM_ENDPOINT = 'https://formsubmit.co/ajax/nitin@gadurarealestate.com';

  document.querySelectorAll('form[data-v2-form]').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      // honeypot check — if the hidden field is filled, it's a bot
      const honey = form.querySelector('input[name="_honey"]');
      if (honey && honey.value) return;

      const data = new FormData(form);
      if (!data.get('_subject')) data.append('_subject', 'V2 Lead — Gadura RE');
      if (!data.get('_template')) data.append('_template', 'table');
      if (!data.get('_captcha')) data.append('_captcha', 'false');

      greForm.send(form, FORM_ENDPOINT, data, form.querySelector('button[type="submit"]'));
    });
  });

  /* -------------------------------------------------------------
     SCROLL REVEAL — subtle fade-in for sections
     ------------------------------------------------------------- */
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });

    document.querySelectorAll('[data-reveal]').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
      io.observe(el);
    });
  }

  // CSS for the reveal
  const style = document.createElement('style');
  style.textContent = `
    [data-reveal].revealed {
      opacity: 1 !important;
      transform: translateY(0) !important;
    }
  `;
  document.head.appendChild(style);
})();
