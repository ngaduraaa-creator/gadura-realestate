/*
 * recruiting-analytics.js — measurement and form behaviour for /join/.
 *
 * Two jobs, deliberately in one file because they share the form element:
 *   1. GA4 events for the recruiting funnel
 *   2. Client-side validation and honest error states on the enquiry form
 *
 * PRIVACY — the hard rule for this file.
 * No name, email, phone, licence number, free-text message or any other personal
 * detail is ever passed to GA4, placed in a URL, or written to the dataLayer.
 * Events carry the SHAPE of an interaction (which segment, which CTA, whether a
 * select has a value) and never its CONTENT. The site's GA4 property has
 * automatic user-provided-data collection switched on, which makes this stricter
 * than usual: anything put in a parameter here could be retained.
 *
 * HONESTY — on naming.
 * The form does a native POST and FormSubmit redirects to /thank-you.html, so
 * this page cannot observe whether anything was delivered. The event is
 * therefore `recruiting_form_submit` — an ATTEMPT. There is deliberately no
 * `..._success` event, because this code is not in a position to know. That
 * matches /thank-you.html, which tells the visitor in as many words that it
 * cannot confirm the message reached the office.
 */
(function () {
  'use strict';

  var hasGtag = function () { return typeof window.gtag === 'function'; };

  function track(name, params) {
    if (!hasGtag()) return;
    try {
      window.gtag('event', name, params || {});
    } catch (e) {
      /* Measurement must never break the page. */
    }
  }

  /* Which funnel page is this? Derived from the path only -- never from
     anything the visitor typed. */
  function segment() {
    var p = window.location.pathname.replace(/\/+$/, '');
    if (p === '/join') return 'hub';
    var m = p.match(/^\/join\/([a-z-]+)$/);
    return m ? m[1] : 'other';
  }

  var SEG = segment();

  /* ---------------------------------------------------------------- views */
  track('recruiting_page_view', { recruiting_segment: SEG });

  /* ------------------------------------------------------------ cta clicks */
  /* Every tracked CTA carries data-rec-cta with a hand-written, non-personal
     label. Anything without that attribute is not tracked. */
  document.addEventListener('click', function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest('[data-rec-cta]') : null;
    if (!el) return;
    var label = el.getAttribute('data-rec-cta') || 'unlabelled';
    var evName = label.indexOf('segment-') === 0
      ? 'recruiting_segment_selected'
      : (label.indexOf('resource-') === 0 || label.indexOf('-to-') !== -1
          ? 'resource_to_recruiting_click'
          : 'recruiting_cta_click');
    track(evName, { recruiting_segment: SEG, cta: label });
  }, { passive: true });

  /* ----------------------------------------------------------------- form */
  var form = document.getElementById('rec-form');
  if (!form) return;

  var started = false;
  form.addEventListener('input', function () {
    if (started) return;
    started = true;
    track('recruiting_form_start', { recruiting_segment: SEG });
  }, { passive: true, once: false });

  function fieldWrap(input) {
    return input.closest('.jn-field') || input.closest('.jn-consent');
  }

  function errorFor(input) {
    var id = input.getAttribute('aria-describedby');
    return id ? document.getElementById(id) : null;
  }

  function setInvalid(input, invalid) {
    var wrap = fieldWrap(input);
    var err = errorFor(input);
    if (wrap) {
      if (invalid) { wrap.setAttribute('data-invalid', ''); }
      else { wrap.removeAttribute('data-invalid'); }
    }
    if (err) { err.hidden = !invalid; }
    input.setAttribute('aria-invalid', invalid ? 'true' : 'false');
  }

  /* Deliberately permissive: a shape check, not an RFC validator. Rejecting a
     real address is worse than accepting an odd one, because the cost of a
     false rejection is a lost enquiry. */
  function emailLooksUsable(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim());
  }

  function validate() {
    var bad = [];
    Array.prototype.forEach.call(form.querySelectorAll('[required]'), function (input) {
      var ok;
      if (input.type === 'checkbox') ok = input.checked;
      else if (input.type === 'email') ok = emailLooksUsable(input.value);
      else ok = input.value.trim() !== '';
      setInvalid(input, !ok);
      if (!ok) bad.push(input);
    });
    return bad;
  }

  /* Live-clear an error once the visitor fixes it, so the page stops shouting. */
  form.addEventListener('change', function (ev) {
    var t = ev.target;
    if (!t || !t.hasAttribute || !t.hasAttribute('required')) return;
    if (t.getAttribute('aria-invalid') !== 'true') return;
    var ok = t.type === 'checkbox' ? t.checked
      : t.type === 'email' ? emailLooksUsable(t.value)
      : t.value.trim() !== '';
    if (ok) setInvalid(t, false);
  });

  var summary = document.getElementById('rf-form-err');
  var submitting = false;

  form.addEventListener('submit', function (ev) {
    if (submitting) { ev.preventDefault(); return; }   /* duplicate guard */

    var bad = validate();
    if (bad.length) {
      ev.preventDefault();
      if (summary) summary.hidden = false;
      bad[0].focus();
      if (bad[0].scrollIntoView) bad[0].scrollIntoView({ block: 'center', behavior: 'smooth' });
      track('recruiting_form_error', {
        recruiting_segment: SEG,
        /* A COUNT and the field NAMES -- never the values the visitor typed. */
        invalid_count: bad.length,
        invalid_fields: bad.map(function (i) { return i.name || i.id; }).join(',')
      });
      return;
    }

    if (summary) summary.hidden = true;
    submitting = true;

    var btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Sending…';
    }

    /* An ATTEMPT, not a delivery. See the header comment. The selects carry
       hand-written option text, no free input, so they are safe to report --
       but name, email, phone, market and message are never touched. */
    var pick = function (id) {
      var el = document.getElementById(id);
      return el && el.value ? el.value : '(not given)';
    };
    track('recruiting_form_submit', {
      recruiting_segment: SEG,
      licence_status: pick('rf-licence'),
      interest: pick('rf-interest'),
      experience: pick('rf-exp'),
      closed_sides: pick('rf-sides')
    });

    /* Native POST proceeds; FormSubmit redirects to /thank-you.html. If the
       browser is still here after a few seconds the redirect did not happen, so
       give the visitor the form back and a route that does not depend on it. */
    window.setTimeout(function () {
      submitting = false;
      if (btn) { btn.disabled = false; btn.textContent = 'Send my enquiry'; }
      if (summary) summary.hidden = false;
    }, 8000);
  });
})();
