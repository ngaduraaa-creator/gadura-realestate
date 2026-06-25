# IDX Broker Compliance Fixes — Setup & Placement Guide

Fixes the 8 audit findings on **homes.gadurarealestate.com** (IDX Broker account
`c056`, **dynamic "standard" wrapper**). Three code files + two manual steps.

> The IDX subdomain is hosted by IDX Broker — these files are **pasted into the
> IDX control panel**, not deployed from this repo. The copies here are the
> source of truth and are version-controlled.

---

## Where each file goes (IDX Broker control panel)

A dynamic wrapper has **no Header/Footer HTML field**, so global code goes in
**Custom CSS** (for CSS) and the **Global Subheader** (for HTML + JS).

| File | Control-panel path | Wrap |
|------|--------------------|------|
| `listing-detail-overrides.css` | **Design → Website → Custom CSS** → Level **Global** → CSS Type **Desktop** | paste CSS only (no `<style>`) |
| `global-footer-injection.html` | **Design → Website → Subheaders** → Level **Global** → **"Turn WYSIWYG Off"** | raw HTML |
| `listing-detail-overrides.js` | **Design → Website → Subheaders** → Level **Global** → **"Turn WYSIWYG Off"** | **must** wrap in `<script>…</script>` |

Steps:
1. **CSS** — paste the full `listing-detail-overrides.css` into Custom CSS (Global/Desktop). Save. *(Repeat under CSS Type "Mobile" and "Printable" if you want the styling on those surfaces too.)*
2. **Subheader** — open the Global subheader, click **Turn WYSIWYG Off**, and **append** (don't delete anything already there):
   - the full contents of `global-footer-injection.html`, then
   - the JS wrapped in tags:
     ```html
     <script>
     /* full contents of listing-detail-overrides.js */
     </script>
     ```
   Save.

The Global subheader renders on **every** IDX page (detail, map/search results, saved searches, account). It renders near the **top**, so the JS automatically relocates the footer to the page bottom.

**Do NOT** paste code into Design → Website → **Wrappers** — that only points IDX at the dynamic wrapper source URL.

---

## Two manual steps (required for full compliance)

1. **Upload the official OneKey® MLS IDX logo** (fix #5). The code references
   `https://gadurarealestate.com/images/onekey-mls-idx-logo.png` but does **not**
   create the file. Download the official OneKey MLS IDX-participant logo from
   OneKey's member resources (OneKey member portal / Document Library — do **not**
   use a third-party scraper for a compliance display) and upload it to the main
   site at exactly `/images/onekey-mls-idx-logo.png`. Until then, the JS shows a
   text "OneKey® MLS" fallback so nothing breaks. *(An official Equal Housing
   Opportunity mark is already included as inline SVG — no upload needed.)*
2. **Confirm per-listing broker attribution** (NAR 7.58 / OneKey, separate from
   the 8 items). Each non-Gadura listing must show "Listing courtesy of
   [brokerage]." Verify IDX Broker's native detail/results template still renders
   that credit (these overrides do not hide it). If it's missing, that's a
   separate IDX-feed/config gap to raise with IDX Broker / OneKey.

---

## Forced-registration removal ("You must register to view this page")

The mandatory registration pop-up that blocks visitors before they can view a
listing has been removed — it hurts conversions and isn't needed (leads are
captured by the contact forms instead).

- **Permanent fix (recommended):** IDX Broker → **Account → Lead Management →
  Registration** → turn **off** required registration (or set "properties viewed
  before registration" to unlimited). One toggle, no code.
- **Code fallback (already in `listing-detail-overrides.js`):** `dismissRegistration()`
  removes the `.IDX-registrationModal` dialog + overlay and restores scrolling,
  re-applying if IDX re-injects it.
- **Caveat:** this is for standard **IDX** data only. If any part of your feed is
  **VOW** (registration required by MLS rule), do *not* disable it — remove
  `dismissRegistration` from the pipeline in the JS.

---

## What each fix does

| # | Fix | Handled by |
|---|-----|-----------|
| 1 | **Equal Housing Opportunity** logo + text — global footer, every page | footer HTML + JS (inline HUD SVG), CSS |
| 2 | **NYS license #10991238487** + "Licensed Real Estate Broker, State of New York" — every page footer | footer HTML + JS |
| 3 | **Phone** `9177050132` → **(917) 705-0132**, `tel:+19177050132` | JS (scoped to contact blocks) |
| 4 | **Status badge** by address + price — green Active / amber Pending / grey Sold | JS + CSS |
| 5 | **OneKey® MLS IDX logo** + text disclaimer in footer | footer HTML + JS (+ upload step above) |
| 6 | **Privacy Policy + Terms** links in footer **and** a SHIELD-Act notice by every contact form | footer HTML + JS |
| 7 | **reCAPTCHA disclosure** corrected with Google policy links | JS (enforced idempotently) |
| 8 | **Similar Listings** — secure same-origin deep-link cards (county / price ±20% / type) | JS + CSS |

**Security note (fix #8):** the IDX Broker API key is **never** used client-side
(it would leak the MLS feed). The "Similar Listings" cards deep-link into IDX's
own same-origin map search (`/idx/map/mapsearch&county=…&lp=…&hp=…`), which IDX
filters server-side on click — no key exposed. For real inline comp cards later,
run the API key server-side (e.g. the existing GitHub Action) and serve a JSON.

---

## Notes & caveats

- **Privacy/Terms links** point to `…/privacy-policy.html` and `…/terms.html`
  (the actual pages). Extensionless `/privacy-policy` would 404 on GitHub Pages —
  if you prefer clean URLs, add redirect stubs on the main site and update the two
  links in `global-footer-injection.html` + `listing-detail-overrides.js`.
- **Robustness:** the JS is idempotent, scopes the phone rewrite to contact
  containers (never the whole page, so MLS numbers/IDs are safe), HTML-escapes all
  MLS-sourced text (no XSS), and its MutationObserver ignores its own mutations
  and disconnects during each run (no loop/flicker).
- **SHIELD Act:** the form notice is good transparency but does **not** by itself
  satisfy the Act — it also requires reasonable data-security safeguards (HTTPS on
  submit ✓, access controls on lead data, breach procedures). Handle those
  operationally.
- After pasting, open a listing and a map-search page and confirm: status badge by
  the price, formatted phone, footer with EHO + license # + OneKey logo/text +
  Privacy/Terms links, the SHIELD notice above the contact form, corrected
  reCAPTCHA line, and Similar-Listings cards instead of "No listings found."
