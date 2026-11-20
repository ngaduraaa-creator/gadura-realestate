/*
 * career-explorer.js — progressive enhancement for /join/explorer/
 *
 * DESIGN RULE: the page is complete and useful with this file absent.
 *
 * All four paths and all their guidance are in the static HTML. Without JS a
 * visitor reads every path top to bottom, and a crawler indexes every word.
 * This file only *narrows* what is shown once somebody says which one they
 * are. It never fetches, never injects guidance, never gates content behind a
 * click. If it fails to load, the page degrades to a long article rather than
 * an empty shell.
 *
 * PRIVACY — the hard rules for this file.
 *   - No personally identifying information is collected. There are no free
 *     text inputs in the tool at all; every answer is a fixed, hand-written
 *     option, so there is nothing a visitor can type for us to mishandle.
 *   - Nothing is persisted. No localStorage, no sessionStorage, no cookie.
 *     Reloading the page starts over, deliberately.
 *   - Answers are kept in a module-scoped object that dies with the page.
 *   - Analytics receive the PATH and the hand-written option VALUES only, and
 *     only because both are strings this repository wrote. They are not
 *     derived from anything the visitor supplied.
 *
 * HONESTY — what this tool must never do.
 *   - No compatibility score, match percentage, grade or ranking. There is no
 *     model behind such a number and inventing one would be the exact species
 *     of claim the rest of this section exists to avoid.
 *   - No statement about earnings, splits, fees or lead volume.
 *   - Completing this does not qualify anybody for anything, and the copy says
 *     so where a visitor might otherwise assume it.
 *
 * It is a router with useful reading attached, and it should stay one.
 */
(function () {
  'use strict';

  var root = document.getElementById('explorer');
  if (!root) return;

  /* Dies with the page. Never written to storage. */
  var answers = { path: null };

  function track(name, params) {
    if (typeof window.gtag !== 'function') return;
    try { window.gtag('event', name, params || {}); } catch (e) { /* never break the page */ }
  }

  function panels() {
    return Array.prototype.slice.call(root.querySelectorAll('[data-path-panel]'));
  }

  function show(path) {
    answers.path = path;

    panels().forEach(function (p) {
      var mine = p.getAttribute('data-path-panel') === path;
      p.hidden = !mine;
      /* Reset any refinement inside a panel we are leaving, so returning to it
         does not show a stale answer the visitor has forgotten giving. */
      if (!mine) {
        p.querySelectorAll('[data-refine] button[aria-pressed="true"]')
          .forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        p.querySelectorAll('[data-answer-for]').forEach(function (a) { a.hidden = true; });
      }
    });

    root.querySelectorAll('[data-path-choice]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-path-choice') === path));
    });

    var intro = document.getElementById('explorer-intro');
    if (intro) intro.hidden = true;
    var reset = document.getElementById('explorer-reset');
    if (reset) reset.hidden = false;

    track('recruiting_segment_selected', { recruiting_segment: 'explorer', cta: 'path-' + path });

    var panel = root.querySelector('[data-path-panel="' + path + '"]');
    if (panel) {
      var h = panel.querySelector('h2, h3');
      if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
      panel.scrollIntoView({ block: 'start', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
    }
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function resetAll() {
    panels().forEach(function (p) { p.hidden = false; });
    root.querySelectorAll('[data-path-choice]').forEach(function (b) {
      b.setAttribute('aria-pressed', 'false');
    });
    root.querySelectorAll('[data-answer-for]').forEach(function (a) { a.hidden = true; });
    root.querySelectorAll('[data-refine] button').forEach(function (b) {
      b.setAttribute('aria-pressed', 'false');
    });
    var intro = document.getElementById('explorer-intro');
    if (intro) intro.hidden = false;
    var reset = document.getElementById('explorer-reset');
    if (reset) reset.hidden = true;
    answers = { path: null };
    root.scrollIntoView({ block: 'start', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
  }

  root.addEventListener('click', function (ev) {
    var choice = ev.target.closest('[data-path-choice]');
    if (choice) { ev.preventDefault(); show(choice.getAttribute('data-path-choice')); return; }

    var reset = ev.target.closest('#explorer-reset');
    if (reset) { ev.preventDefault(); resetAll(); return; }

    var opt = ev.target.closest('[data-refine] button');
    if (opt) {
      ev.preventDefault();
      var group = opt.closest('[data-refine]');
      var key = group.getAttribute('data-refine');
      var val = opt.getAttribute('data-value');

      group.querySelectorAll('button').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === opt));
      });

      /* Reveal the hand-written answer for this option. Nothing is generated;
         every answer below exists in the static HTML and is simply unhidden. */
      var panel = opt.closest('[data-path-panel]');
      panel.querySelectorAll('[data-answer-for^="' + key + ':"]').forEach(function (a) {
        a.hidden = a.getAttribute('data-answer-for') !== key + ':' + val;
      });

      /* Hand-written key and value only. Never anything the visitor typed —
         there is no free text in this tool to send. */
      track('recruiting_explorer_refined', {
        recruiting_segment: 'explorer',
        path: answers.path || 'unknown',
        question: key,
        choice: val
      });
      return;
    }

    var cta = ev.target.closest('[data-rec-cta]');
    if (cta) {
      track('recruiting_cta_click', {
        recruiting_segment: 'explorer',
        cta: cta.getAttribute('data-rec-cta')
      });
    }
  });

  /* Keyboard: the choices are real <button>s, so Enter and Space already work.
     Only arrow-key roving is added, and only within a group. */
  root.addEventListener('keydown', function (ev) {
    if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
    var btn = ev.target.closest('[data-path-choice], [data-refine] button');
    if (!btn) return;
    var sibs = Array.prototype.slice.call(
      btn.parentElement.querySelectorAll('[data-path-choice], button')
    );
    var i = sibs.indexOf(btn);
    if (i < 0) return;
    var next = sibs[(i + (ev.key === 'ArrowRight' ? 1 : sibs.length - 1)) % sibs.length];
    if (next) { next.focus(); ev.preventDefault(); }
  });

  /* Enhancement is live: collapse to the chooser and let the visitor pick.
     Done last so a throw above leaves the full static page visible. */
  root.setAttribute('data-enhanced', 'true');
  panels().forEach(function (p) { p.hidden = true; });
  var staticNote = document.getElementById('explorer-static-note');
  if (staticNote) staticNote.hidden = true;

  track('recruiting_explorer_ready', { recruiting_segment: 'explorer' });
})();
