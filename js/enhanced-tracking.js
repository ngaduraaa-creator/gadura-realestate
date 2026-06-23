/* =========================================================
   GADURA REAL ESTATE — ENHANCED GA4 TRACKING
   ─────────────────────────────────────────────────────────
   GA4 Measurement ID: G-9TM4LDZ7DD
   Modular tracking: scroll depth, time on page, CTA clicks,
   blog reads, neighborhood views, form interactions,
   outbound links, market reports, calculators, referrals.
   ========================================================= */
(function () {
  'use strict';

  /* ── Guard: gtag must exist ── */
  function ga(event, params) {
    if (typeof window.gtag === 'function') {
      window.gtag('event', event, params);
    }
  }

  var path = window.location.pathname;

  /* =========================================================
     1. SCROLL DEPTH TRACKING
     Fire events at 25%, 50%, 75%, 90% scroll milestones.
     Throttled to max once per second.
     ========================================================= */
  (function () {
    var milestones = [25, 50, 75, 90];
    var fired = {};
    var ticking = false;

    function getScrollPercent() {
      var docHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      var winHeight = window.innerHeight;
      var scrollTop = window.scrollY || window.pageYOffset;
      if (docHeight <= winHeight) return 100;
      return Math.round((scrollTop / (docHeight - winHeight)) * 100);
    }

    function checkScroll() {
      var pct = getScrollPercent();
      for (var i = 0; i < milestones.length; i++) {
        var m = milestones[i];
        if (pct >= m && !fired[m]) {
          fired[m] = true;
          ga('scroll_depth', {
            event_category: 'Engagement',
            event_label: m + '%',
            value: m
          });
        }
      }
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        ticking = true;
        setTimeout(checkScroll, 1000);
      }
    }, { passive: true });
  })();

  /* =========================================================
     2. TIME ON PAGE ENGAGEMENT
     Fire 'engaged_session' at 30s, 60s, 120s.
     ========================================================= */
  (function () {
    var milestones = [30, 60, 120];
    var idx = 0;

    function scheduleNext() {
      if (idx >= milestones.length) return;
      var delay = idx === 0
        ? milestones[0] * 1000
        : (milestones[idx] - milestones[idx - 1]) * 1000;
      setTimeout(function () {
        ga('engaged_session', {
          event_category: 'Engagement',
          event_label: milestones[idx] + 's',
          value: milestones[idx]
        });
        idx++;
        scheduleNext();
      }, delay);
    }

    scheduleNext();
  })();

  /* =========================================================
     3. CTA BUTTON / LINK CLICK TRACKING
     Track ALL clicks on elements with class 'cta' or
     'btn-primary', or href containing tel:, mailto:, whatsapp.
     Uses event delegation for dynamic elements.
     ========================================================= */
  (function () {
    document.addEventListener('click', function (e) {
      var el = e.target.closest('a, button');
      if (!el) return;

      var href = el.getAttribute('href') || '';
      var classList = el.className || '';
      var isCta = /\bcta\b/i.test(classList) || /\bbtn-primary\b/i.test(classList);
      var isTel = /^tel:/i.test(href);
      var isMailto = /^mailto:/i.test(href);
      var isWhatsApp = /whatsapp/i.test(href);

      if (!isCta && !isTel && !isMailto && !isWhatsApp) return;

      var label = el.textContent.trim().substring(0, 80) || href;
      var category = 'CTA Click';
      if (isTel) category = 'Phone Click';
      else if (isMailto) category = 'Email Click';
      else if (isWhatsApp) category = 'WhatsApp Click';

      ga('cta_click', {
        event_category: category,
        event_label: label,
        link_url: href
      });
    }, { passive: true });
  })();

  /* =========================================================
     4. BLOG ARTICLE READ TRACKING
     On /blog/ pages: article_view on load, plus scroll depth
     milestones within the article content area.
     ========================================================= */
  (function () {
    if (path.indexOf('/blog') === -1) return;

    /* article_view on load */
    var title = document.title;
    ga('article_view', {
      event_category: 'Blog',
      event_label: title
    });

    /* Article scroll depth */
    var article = document.querySelector('article')
      || document.querySelector('.blog-content')
      || document.querySelector('.post-content')
      || document.querySelector('main');
    if (!article) return;

    var articleMilestones = [25, 50, 75, 100];
    var articleFired = {};
    var articleTicking = false;

    function checkArticleScroll() {
      var rect = article.getBoundingClientRect();
      var articleTop = rect.top + window.scrollY;
      var articleHeight = article.offsetHeight;
      var scrollBottom = window.scrollY + window.innerHeight;
      var read = scrollBottom - articleTop;
      var pct = Math.min(100, Math.max(0, Math.round((read / articleHeight) * 100)));

      for (var i = 0; i < articleMilestones.length; i++) {
        var m = articleMilestones[i];
        if (pct >= m && !articleFired[m]) {
          articleFired[m] = true;
          ga('article_read_' + m, {
            event_category: 'Blog',
            event_label: title,
            value: m
          });
        }
      }
      articleTicking = false;
    }

    window.addEventListener('scroll', function () {
      if (!articleTicking) {
        articleTicking = true;
        setTimeout(checkArticleScroll, 1000);
      }
    }, { passive: true });
  })();

  /* =========================================================
     5. NEIGHBORHOOD PAGE VIEW TRACKING
     If URL contains /neighborhoods/, fire neighborhood_view
     with the neighborhood name extracted from the path.
     ========================================================= */
  (function () {
    if (path.indexOf('/neighborhoods/') === -1 && path.indexOf('/neighborhoods.html') === -1) return;

    var neighborhood = 'All Neighborhoods';
    /* Extract neighborhood from path: /neighborhoods/ozone-park/ -> Ozone Park */
    var match = path.match(/\/neighborhoods\/([^\/]+)/);
    if (match) {
      neighborhood = match[1]
        .replace(/-/g, ' ')
        .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
    }

    ga('neighborhood_view', {
      event_category: 'Neighborhood',
      event_label: neighborhood
    });
  })();

  /* =========================================================
     6. FORM FIELD INTERACTION TRACKING
     Track form_start on first focus of any form field.
     Track form_abandon if user leaves page without submitting.
     ========================================================= */
  (function () {
    var forms = document.querySelectorAll('form');
    if (!forms.length) return;

    forms.forEach(function (form) {
      var started = false;
      var submitted = false;
      var formName = form.id || form.getAttribute('name') || 'unknown';

      /* form_start: first interaction with any field */
      var fields = form.querySelectorAll('input, select, textarea');
      fields.forEach(function (field) {
        field.addEventListener('focus', function () {
          if (started) return;
          started = true;
          ga('form_start', {
            event_category: 'Form',
            event_label: formName
          });
        }, { passive: true, once: false });
      });

      /* Track submission */
      form.addEventListener('submit', function () {
        submitted = true;
      });

      /* form_abandon: started but not submitted */
      window.addEventListener('beforeunload', function () {
        if (started && !submitted) {
          ga('form_abandon', {
            event_category: 'Form',
            event_label: formName
          });
        }
      });
    });
  })();

  /* =========================================================
     7. OUTBOUND LINK TRACKING
     Track clicks on links going to external domains.
     ========================================================= */
  (function () {
    var currentHost = window.location.hostname;

    document.addEventListener('click', function (e) {
      var link = e.target.closest('a[href]');
      if (!link) return;

      var href = link.getAttribute('href') || '';
      /* Skip non-http links, anchors, tel/mailto (tracked elsewhere) */
      if (!/^https?:\/\//i.test(href)) return;

      try {
        var url = new URL(href);
        if (url.hostname === currentHost) return;

        ga('outbound_click', {
          event_category: 'Outbound Link',
          event_label: url.hostname,
          link_url: href
        });
      } catch (err) {
        /* malformed URL, skip */
      }
    }, { passive: true });
  })();

  /* =========================================================
     8. MARKET REPORT ENGAGEMENT
     If on /market-reports/ page, track market_report_view.
     ========================================================= */
  (function () {
    if (path.indexOf('/market-reports') === -1) return;

    var reportName = document.title || 'Market Report';
    ga('market_report_view', {
      event_category: 'Market Reports',
      event_label: reportName
    });
  })();

  /* =========================================================
     9. CALCULATOR USAGE TRACKING
     If on /mortgage-calculator/ or /calculators/, track
     calculator_use on first interaction with calc fields.
     ========================================================= */
  (function () {
    if (path.indexOf('/mortgage-calculator') === -1 && path.indexOf('/calculators') === -1) return;

    var tracked = false;
    var calcForm = document.getElementById('mortgage-calc')
      || document.querySelector('.calculator')
      || document.querySelector('form');
    if (!calcForm) return;

    calcForm.addEventListener('input', function () {
      if (tracked) return;
      tracked = true;
      ga('calculator_use', {
        event_category: 'Calculator',
        event_label: path
      });
    }, { passive: true });

    /* Also fire a view event */
    ga('calculator_view', {
      event_category: 'Calculator',
      event_label: path
    });
  })();

  /* =========================================================
     10. REFERRAL PAGE TRACKING
     If on /referral/, track referral_page_view.
     ========================================================= */
  (function () {
    if (path.indexOf('/referral') === -1) return;

    ga('referral_page_view', {
      event_category: 'Referral',
      event_label: document.title || 'Referral Page'
    });
  })();

})();
