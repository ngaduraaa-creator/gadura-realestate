# OneKey® MLS / NAR IDX Policy 7.58 — Per-Listing Broker Attribution Audit

**Site:** homes.gadurarealestate.com (idxID `c056`, IDX-wrapper-standard, IDX Broker "Precision" template)
**Audited:** 2026-06-25 (live DOM inspection, logged-out public view)
**Auditor note:** This is a compliance requirement with **automatic-fine provisions** — up to **$5,000 first offense / $15,000 subsequent** (OneKey Rules & Procedures). Treat as priority.

---

## The rule (what must appear on every IDX listing)

OneKey's implementation of NAR Policy Statement 7.58 requires each individual IDX
listing to display, **per listing**:

1. the **name of the listing firm**, and
2. the **name of the listing agent**, and
3. the **email OR phone number** provided by the listing participant,

…in a **reasonably prominent location**, in a **readily visible color and a
typeface not smaller than the median** used in the display of listing data, using
**"Listed by" / "Listing [brokerage/agent]"** phrasing (not "Presented by").

This per-listing credit is **distinct** from the site-level data-source notice
("Data services provided by IDX Broker") and the OneKey © / MLS disclaimer.

---

## Findings

### 1. Search-results pages — ❌ NON-COMPLIANT (attribution entirely absent)

Checked both result layouts:

| Layout | URL pattern | Per-listing attribution |
|---|---|---|
| Map search | `/idx/map/mapsearch&county=Queens&statusCategory=active&srt=newest` | `.listing-card__courtesy` slot exists ×100 but is **empty (0 populated)**; slot is styled at **10px** (< 16px median) |
| Standard list | `/idx/results/listings?...` | **No courtesy element at all** on the 45 cards |

- A populated card renders only: `Status · Price · Beds · Baths · Address · "Call Listing Agent"`.
- A full-page scan found **zero** third-party brokerage names (Elliman / Sotheby / Realty / Compass = 0). The listing office name **is not present in the results-card DOM or data attributes** — only Gadura's own name appears (in the page header/footer).
- Only the site-level **"Data services provided by IDX Broker"** notice (16px) is shown — that is *not* listing-broker attribution.

**Verdict:** No listing firm, agent, or contact is shown per listing on results. Clear gap.

### 2. Listing-detail pages — ⚠️ PARTIAL (firm + agent shown; placement weak; **no phone/email**)

The per-listing credit **does** render and **correctly varies per listing**, confirmed across multiple brokerages:

- `Listing courtesy of Nitin K. Gadura with Gadura Real Estate LLC.` (own)
- `Listing courtesy of Lisa Gelman … with Douglas Elliman Real Estate.`
- `Listing courtesy of Aisabomen Musa-Agboneni with Malonium Realty Group.`
- `Listing courtesy of MaryBeth O'Hara with Ellis Sotheby's Intl Realty.`

| Requirement | Status | Evidence |
|---|---|---|
| Listing **firm** name shown | ✅ | present per listing |
| Listing **agent** name shown | ✅ | present per listing |
| Typeface ≥ median | ✅ | credit = **16px**; median listing-data font = **16px** |
| Readily visible color | ✅ | `rgb(50,59,64)` dark gray on white = high contrast |
| **Reasonably prominent location** | ⚠️ | credit sits at **absTop 5481 of 5610px — the very bottom of the page**, in the disclaimer block. The dedicated `#IDX-detailsCourtesy` slot near the top exists but is **empty**. |
| **Email or phone** of listing participant | ❌ | **Missing.** Format is "Agent with Firm." with no contact. |
| "Listed by" phrasing | ⚠️ | uses "Listing courtesy of" (clearly identifies the listing broker, but OneKey prefers "Listed by"/"Listing") |

**Critical data finding:** A full scan of the rendered DOM, every inline `<script>`,
and `window` globals (`window.listing` is a string; `window.idx` is jQuery;
`window.idxDataLayer` is the GTM array) found **no listing-office phone or email
anywhere** for third-party listings. The only phone present is Gadura's own
(917-705-0132). **The contact data is simply not delivered to the page.**

---

## Why a purely injected fix is not sufficient on its own

Injected HTML/CSS/JS can only restyle, reposition, or duplicate data **already in the
page**. The two missing pieces are missing *data*, not missing *styling*:

- **Phone/email** (detail + results): not in the DOM, scripts, or JS objects → injection cannot fabricate it.
- **Office name on results cards**: not in the card DOM → injection cannot fabricate it.

Putting Gadura's own number on another broker's listing would **not** satisfy 7.58 (it
requires the *listing* participant's contact) and would itself be a violation. So full
compliance requires IDX Broker to **output the data** (dashboard setting and/or support/feed),
not just CSS.

---

## Remediation

### A. Required for full compliance — IDX Broker dashboard / support (supplies the missing data)

1. **Enable per-listing broker attribution on search results.** In the IDX dashboard
   (Listing Display / search-results field settings), turn on the listing
   office / "Courtesy of" output for results cards. The empty `.listing-card__courtesy`
   slot already in the map template indicates IDX is built to populate it once enabled.
2. **Add the listing participant's phone/email to the detail-page courtesy**, and move it
   to a prominent position using "Listed by" phrasing. If the office phone/email is not
   available to toggle, open an **IDX Broker support ticket** citing *OneKey 7.58 broker
   attribution* and ask them to enable the compliant attribution string for the OneKey feed.
3. If IDX says the OneKey feed does not pass office phone/email, escalate to **OneKey MLS
   data-services** — this becomes a feed/config matter, and OneKey can advise the compliant
   minimum for their market.

### B. Interim mitigation — injected, deployable today (this folder)

Files: **`idx-758-attribution.js`** + **`idx-758-attribution.css`**

- On **detail pages**, lifts the existing "Listing courtesy of …" data into a prominent,
  high-contrast **"Listed by [Agent] with [Firm]"** block placed **directly under the
  address** at **16px** (= median; verified live: moved from absTop 5481 → **absTop 110**,
  color navy `#0c1733`, weight 600, "Listed by" phrasing).
- Idempotent; re-applies on IDX ajax re-render; runs only on `/idx/details/` pages.
- **Limitation:** still cannot add phone/email (data absent), and does **not** touch results
  pages. It improves *prominence + phrasing + size* on detail pages but is **not a complete
  7.58 fix** — pursue (A) in parallel.

**Install:** paste `idx-758-attribution.css` into *Designs → Global CSS* and the contents of
`idx-758-attribution.js` inside the `<script>` block in *Designs → Custom Initial Output*
(alongside the existing `idx-custom.*`). Verified live against the standard wrapper on
2026-06-25.

---

## One-line bottom line

> Detail pages show the listing **firm + agent** at a compliant size but bury it at the page
> bottom and **omit the required phone/email**; search-results pages show **no per-listing
> attribution at all**. The injected fix fixes detail-page prominence/phrasing today, but the
> missing **contact info** and **results-page** attribution require an **IDX Broker
> setting/support change** because that data is not present in the page.

### Sources
- [NAR Policy Statement 7.58 (IDX)](https://www.nar.realtor/handbook-on-multiple-listing-policy/advertising-print-and-electronic-section-1-internet-data-exchange-idx-policy-policy-statement-7-58)
- [OneKey® MLS Rules and Procedures](https://support.onekeymls.com/hc/en-us/articles/29238087786260-OneKey-MLS-Rules-and-Procedures)
- [OneKey® MLS — IDX Policy Requirements](https://www.onekeymlsny.com/idx-options/idx-policy-requirements/)
- [OneKey® MLS — Rules & Procedures Violation Overview (fines)](https://support.onekeymls.com/hc/en-us/articles/37010139901204-Rules-and-Procedures-Violation-Overview)
- [Listing Broker Contact Information Required on IDX Display](https://www.realmls.com/listing-broker-contact-information-required-on-idx-display/)
