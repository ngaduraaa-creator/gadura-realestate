/* Gadura v2 — shared site scripts */

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
     Honeypot-protected. Sends to a forwarding service endpoint.
     Replace FORM_ENDPOINT with your actual Formspree/Basin/etc URL.
     ------------------------------------------------------------- */
  const FORM_ENDPOINT = 'https://formspree.io/f/REPLACE_WITH_YOUR_ID';

  document.querySelectorAll('form[data-v2-form]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // honeypot check — if the hidden field is filled, it's a bot
      const honey = form.querySelector('input[name="_gotcha"]');
      if (honey && honey.value) return;

      const btn = form.querySelector('button[type="submit"]');
      const originalText = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

      const data = new FormData(form);

      try {
        const res = await fetch(form.action || FORM_ENDPOINT, {
          method: 'POST',
          body: data,
          headers: { 'Accept': 'application/json' }
        });
        if (res.ok) {
          form.innerHTML = `
            <div style="text-align:center; padding:2rem 0;">
              <div style="font-family:var(--serif); font-size:1.8rem; color:var(--brick); margin-bottom:0.8rem;">Thank you.</div>
              <p style="margin:0 auto 1.5rem;">We'll call you within 2 hours during business hours (Mon–Sat 9am–7pm).</p>
              <a class="btn btn-primary" href="tel:+19177050132">Can't wait? Call Nitin now: (917) 705-0132</a>
            </div>
          `;
        } else {
          throw new Error('Submission failed');
        }
      } catch (err) {
        if (btn) { btn.disabled = false; btn.textContent = originalText; }
        alert('Something went wrong. Please call us directly at (718) 850-0010.');
      }
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
