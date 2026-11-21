/* Rental-owner contact attribution.
   When a visitor taps a call, text or email link inside an owner block or signpost
   (elements carrying data-ll-block), send one GA4 event naming the channel and the
   block's page code. It runs only where the page already loads GA4 (window.gtag);
   it makes no request of its own and never reads what the visitor types. */
(function () {
  'use strict';
  function onClick(e) {
    var t = e.target;
    var link = t && t.closest ? t.closest('a[data-owner-contact]') : null;
    if (!link || typeof window.gtag !== 'function') return;
    var box = link.closest('[data-ll-block]');
    window.gtag('event', 'owner_contact_click', {
      owner_channel: link.getAttribute('data-owner-contact'),
      owner_block: box ? box.getAttribute('data-ll-block') : 'none',
      transport_type: 'beacon'
    });
  }
  document.addEventListener('click', onClick, true);
})();
