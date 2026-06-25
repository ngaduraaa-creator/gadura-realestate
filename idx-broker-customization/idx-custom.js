/* ════════════════════════════════════════════════════════════════
   Gadura Real Estate — IDX Broker Custom JavaScript
   Paste into: IDX Broker Dashboard → Designs → Custom Initial Output
   (wrap the whole thing in <script>…</script> in that field), OR add to
   the Dynamic Wrapper just before </body>.

   Adds to every listing page (works alongside idx-custom.css):
     • Nitin's headshot in the agent box
     • Phone number reformatted to (917) 705-0132
     • "Call Nitin to Inquire" green CTA
     • "Chat on WhatsApp" button — pre-filled with the property address,
       opens WhatsApp Web on desktop and the WhatsApp app on mobile
     • Floating WhatsApp bubble

   IDX loads listing content asynchronously, so this uses a MutationObserver
   and re-runs safely (idempotent — never double-injects).
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var WA   = '19177050132';          // wa.me format (no +)
  var TEL  = '+19177050132';
  var DISP = '(917) 705-0132';
  var PHOTO = 'https://gadurarealestate.com/images/nitin-gadura-headshot.jpg';

  var WA_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-1.6-.8-2.7-1.4-3.7-3.2-.3-.5.3-.5.8-1.5.1-.2 0-.4 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.3 5.2 4.6 2 .8 2.7.9 3.7.8.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3M12 2a10 10 0 00-8.6 15l-1.3 4.7 4.8-1.3A10 10 0 1012 2z"/></svg>';

  function waUrl() {
    var a = document.querySelector('#IDX-detailsAddressStreet');
    var addr = a ? a.textContent.trim() : 'this property';
    var msg = "Hi Nitin, I'm interested in " + addr + '. Is it still available? (' + location.href + ')';
    return 'https://wa.me/' + WA + '?text=' + encodeURIComponent(msg);
  }

  function enhance() {
    var box = document.querySelector('#IDX-contactInfo');
    if (!box) return;

    // 1. Reformat the phone number text
    box.querySelectorAll('a[href^="tel:"]').forEach(function (a) {
      if (/^\d{10}$/.test(a.textContent.trim())) a.textContent = DISP;
    });

    // 2. Headshot
    if (!box.querySelector('.gre-agent-photo')) {
      var img = document.createElement('img');
      img.className = 'gre-agent-photo';
      img.src = PHOTO; img.alt = 'Nitin Gadura'; img.width = 96; img.height = 96;
      box.insertBefore(img, box.firstChild);
    }

    // 3. Call + WhatsApp CTAs
    if (!box.querySelector('.gre-cta-call')) {
      var url = waUrl();
      var call = document.createElement('a');
      call.className = 'gre-cta gre-cta-call'; call.href = TEL;
      call.innerHTML = '<span class="sub">Call Nitin to Inquire</span><span class="num">' + DISP + '</span>';
      var wa = document.createElement('a');
      wa.className = 'gre-cta gre-cta-wa'; wa.href = url; wa.target = '_blank'; wa.rel = 'noopener';
      wa.innerHTML = WA_SVG + ' Chat on WhatsApp';
      box.appendChild(call); box.appendChild(wa);
    }

    // 4. Floating WhatsApp bubble
    if (!document.getElementById('gre-wa-bubble')) {
      var bub = document.createElement('a');
      bub.id = 'gre-wa-bubble'; bub.href = waUrl(); bub.target = '_blank'; bub.rel = 'noopener';
      bub.setAttribute('aria-label', 'Chat on WhatsApp'); bub.innerHTML = WA_SVG;
      document.body.appendChild(bub);
    }
  }

  // Run now + whenever IDX swaps in new content
  function init() {
    enhance();
    var obs = new MutationObserver(function () { enhance(); });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
