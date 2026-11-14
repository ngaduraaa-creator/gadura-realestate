# Editing the /join/ recruiting pages

**This file is public.** `gadurarealestate.com/docs/JOIN_EDITING.md` is a live URL,
like every other tracked file in this repository. Keep it to engineering rules
that are safe to publish. Capability gaps, unverified claims, consent status and
approval state are **not** safe to publish and must not be restated here — an
earlier revision of the page headers leaked exactly that in an HTML comment.

## Rules

Every factual statement about Gadura on a `/join/` page must trace to a fact
already published and reviewed elsewhere on this site, or to a cited third-party
source carrying its publisher, date, population and sample size.

Do not add, without a written owner release:

- compensation terms of any kind
- roster or agent-count claims
- agent photographs, names as endorsement, or testimonials
- training, mentorship or coaching programme claims
- lead provision, in any volume
- production figures, sales volume, awards or rankings
- language-capability claims
- response-time promises — these were removed site-wide deliberately in A3.1
- best / top / #1 / expert / leading / trusted — NY advertising substantiation

## Approval state

Tracked outside this repository, in the war-room register. Ask the owner.

## Build

The six pages share chrome and were assembled from `thank-you.html` (PR #110).
Edit the HTML directly; there is no build step. Keep the shared header, the
legal footer, and the GA4 block byte-identical across all six.
