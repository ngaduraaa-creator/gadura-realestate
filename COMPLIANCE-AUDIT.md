# Gadura Real Estate — NY Compliance Audit
**Auditor:** NY Real Estate Law Compliance Review  
**Date:** April 17, 2026  
**Scope:** gadurarealestate.com — 5 pages reviewed  
**Authority:** NY Exec Law Art 15, NY RPL §443, NY RPL §265-b, NY RPL §462, TSCA Title IV §1018, HUD Fair Housing Act, NAR Code of Ethics Articles 12 & 17, NY DOS Rule 175.25

---

## SUMMARY SCORECARD

| Page | Fair Housing | License Disclosure | Agency Disclosure | PCDA | Lead Paint | Wire Fraud | Foreclosure §265-b | Advertising Standards |
|------|-------------|-------------------|-------------------|------|-----------|------------|-------------------|----------------------|
| v2/index.html | PASS | PARTIAL | PARTIAL | MISSING | N/A | PASS | N/A | PARTIAL |
| inherited-house-queens.html | PASS | PARTIAL | MISSING | **CRITICAL MISSING** | **CRITICAL MISSING** | PASS | N/A | PARTIAL |
| selling-before-foreclosure-queens.html | PASS | PARTIAL | MISSING | MISSING | MISSING | PASS | PARTIAL | PARTIAL |
| index.html (v1) | PASS | PASS | PASS | MISSING | MISSING | PASS | N/A | **ISSUE** |
| sell.html | PARTIAL | PASS | PASS | MISSING | MISSING | PASS | N/A | **ISSUE** |

---

## ISSUE INDEX BY SEVERITY

### CRITICAL (Legal exposure — fix before any page goes live)

1. [C-1] Property Condition Disclosure — Missing from inherited-house-queens.html (seller page)
2. [C-2] Lead Paint Disclosure — Missing from inherited-house-queens.html
3. [C-3] Lead Paint Disclosure — Missing from selling-before-foreclosure-queens.html
4. [C-4] Foreclosure Consulting Disclosure (§265-b) — Incomplete on foreclosure page
5. [C-5] Rating Conflict — sell.html JSON-LD shows ratingValue "5" / reviewCount "27" while all other pages show 4.9 / 57

### HIGH (Regulatory requirement — fix before launch)

6. [H-1] Agency Disclosure — v2/index.html has link but no inline text
7. [H-2] Agency Disclosure — Both situation pages have no disclosure at all
8. [H-3] Broker License Number — Missing from inherited-house-queens.html footer
9. [H-4] Short Sale Implied Approval — Foreclosure page implies guaranteed lender approval
10. [H-5] Property Condition Disclosure — Missing from sell.html (seller-facing page)
11. [H-6] Property Condition Disclosure — Missing from v2/index.html sell tab
12. [H-7] Vinod Gadura Broker License — Missing from inherited-house-queens.html agent sections
13. [H-8] NAR Settlement Disclosure — sell.html footer does not include it (v1 index.html does)

### MEDIUM (Best practice — fix soon)

14. [M-1] EHO Logo vs Text — v2 pages use text only; HUD recommends the actual logo on print/web advertising
15. [M-2] Lawful Source of Income — sell.html EHO bar omits NY-specific "source of lawful income" protected class
16. [M-3] Market Data Sourcing — sell.html market snapshot (Q1 2026 data) has no caveat on recency
17. [M-4] Case Study Placeholder — inherited-house-queens.html has unverified/placeholder case study (NAR Art 12)
18. [M-5] Case Study Placeholder — foreclosure page has a composite/fictional case study
19. [M-6] "30–45 Days" Close Claims — Foreclosure page says "30–45 days to contract" in options comparison as guaranteed; needs qualifier
20. [M-7] "97% List-to-Sale Ratio" — sell.html claims this metric with no sourcing disclaimer
21. [M-8] Testimonials — sell.html shows "Priya M." / "Devika K." which differ from v1 index.html testimonials (same initials, different first names); needs verification they are real reviews
22. [M-9] Google Rating Banner (v1 index.html) — Shows "5.0" in a Google banner at line 635, contradicting the "4.9" stated everywhere else on the same page

### LOW (Advisory — fix at next revision)

23. [L-1] RESPA — No referral disclosure for estate sale company referrals mentioned on inherited-house-queens.html
24. [L-2] Tenant Protection Act — No seller guidance pages; if any are added, tenant rights must be addressed
25. [L-3] IDX Disclaimer — sell.html footer IDX language is present but does not include the OneKey® copyright date
26. [L-4] Vinod's broker license absent from v2 agent card (only #10991238487 in footer, not in the agent card itself)

---

## DETAILED FINDINGS WITH EXACT FIXES

---

### [C-1] CRITICAL — Property Condition Disclosure Missing: inherited-house-queens.html

**Requirement:** NY RPL §462 (Property Condition Disclosure Act). Every seller-facing page that facilitates a listing must inform sellers they are required to complete a Property Condition Disclosure Statement (PCDS) or pay the buyer a $500 credit at closing.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`

**Location:** The legal-section (around line 607–647) covers probate and tax topics but has no PCDS reference.

**Fix — Insert the following as a new `<div class="legal-item">` inside the `.legal-grid` div, after the "Selling As-Is vs. Making Updates" item (after line 641):**

```html
<div class="legal-item">
  <h3>Property Condition Disclosure Statement (PCDS)</h3>
  <p>New York law (RPL §462) requires that sellers of residential real property complete and deliver a Property Condition Disclosure Statement to the buyer before the signing of a binding contract of sale. Sellers who choose not to complete the form must instead provide the buyer with a $500 credit at closing. This requirement applies to estate and inherited property sales. We will provide you with the PCDS form and walk you through completing it accurately.</p>
</div>
```

---

### [C-2] CRITICAL — Lead Paint Disclosure Missing: inherited-house-queens.html

**Requirement:** TSCA Title IV, Section 1018 (42 U.S.C. §4852d). For sales of residential property built before 1978, sellers must disclose known lead-based paint hazards and provide buyers the EPA pamphlet "Protect Your Family From Lead in Your Home." Queens housing stock is overwhelmingly pre-1978. Any page targeting sellers of inherited homes must flag this.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`

**Fix — Add to the legal-grid (after the PCDS item added above):**

```html
<div class="legal-item">
  <h3>Lead Paint Disclosure — Homes Built Before 1978</h3>
  <p>Federal law (42 U.S.C. §4852d) requires sellers of homes built before 1978 to disclose any known lead-based paint hazards and provide buyers with the EPA pamphlet "Protect Your Family From Lead in Your Home." Most Queens homes were built well before 1978 — if you are selling an inherited property, your agent will provide you the required Lead Paint Disclosure form before the contract is signed. Failure to comply can result in fines up to $11,000 per violation.</p>
</div>
```

---

### [C-3] CRITICAL — Lead Paint Disclosure Missing: selling-before-foreclosure-queens.html

**Same federal requirement as C-2.** The pre-foreclosure page targets sellers in financial distress — many of whom own older Queens homes. There is no lead paint reference anywhere on this page.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`

**Fix — Add the following item to the `.legal-grid` section (after the "Short sales require lender approval" item, around line 974), before the closing `</div>` of the legal-grid:**

```html
<div class="legal-item">
  <div class="legal-item-label">Federal Requirement</div>
  <h4>Lead Paint Disclosure — Pre-1978 Homes</h4>
  <p>Federal law requires sellers of homes built before 1978 to disclose known lead-based paint hazards and provide buyers the EPA pamphlet "Protect Your Family From Lead in Your Home." This applies to pre-foreclosure and short sales equally. We provide the required disclosure form — it does not delay the sale.</p>
</div>
```

Also add the PCDS disclosure here:

```html
<div class="legal-item">
  <div class="legal-item-label">NY State Requirement</div>
  <h4>Property Condition Disclosure Statement</h4>
  <p>New York RPL §462 requires sellers to provide buyers with a completed Property Condition Disclosure Statement before signing a contract, or pay the buyer a $500 credit at closing. This applies to pre-foreclosure sales. We will prepare and provide this form for you.</p>
</div>
```

---

### [C-4] CRITICAL — Foreclosure Consulting Disclosure: selling-before-foreclosure-queens.html

**Requirement:** NY RPL §265-b. Any party providing "distressed property consulting services" must:
1. Include in all advertising a statement that free help is available from HUD-approved counseling agencies
2. Not charge a fee before the service is performed
3. Not claim to be a licensed attorney or offer legal services

The page references cnycn.org correctly at line 986 but buries it in a "Watch out" callout about scams. The §265-b disclosure must be **prominently displayed** — it cannot merely be embedded in a paragraph about scam warnings. The page also does not affirmatively state that Gadura charges no upfront fees.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`

**Fix — Add the following block immediately before the lead form section (before `<section class="form-section"`, around line 999):**

```html
<!-- NY RPL §265-b Foreclosure Counseling Disclosure — REQUIRED -->
<div style="background:#fff3cd;border:2px solid #e6b800;padding:1.5rem 2rem;margin:0;border-left:5px solid #e6b800;">
  <div style="font-weight:700;font-size:0.95rem;margin-bottom:0.6rem;color:#5a4000;">
    Free Foreclosure Counseling Available — New York Law
  </div>
  <p style="font-size:0.88rem;color:#5a4000;line-height:1.65;margin:0;">
    If you are at risk of foreclosure, free help is available from HUD-approved housing counseling agencies. 
    Contact the <strong><a href="https://cnycn.org" rel="noopener" target="_blank" style="color:#5a4000;">Center for NYC Neighborhoods</a></strong> at 
    <strong>(646) 786-0888</strong>, or call <strong>311</strong> and ask for foreclosure counseling. 
    Gadura Real Estate LLC is a licensed real estate brokerage, not a foreclosure consulting company. 
    We do not charge any fee until your property closes — our commission is paid only at the time of closing from sale proceeds. 
    We do not offer legal advice; for legal guidance on your foreclosure, consult a licensed New York real estate attorney.
  </p>
</div>
```

---

### [C-5] CRITICAL — Rating Conflict in JSON-LD: sell.html

**Requirement:** NAR Code of Ethics Article 12; NY DOS advertising standards. All claims must be accurate and consistent.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`

**Problem:** The JSON-LD schema at lines 37–47 reads:
```json
"aggregateRating": { "@type": "AggregateRating", "ratingValue": "5", "reviewCount": "27", "bestRating": "5" }
```

But every other page on the site — and the body text of sell.html itself (line 621) — states **4.9 stars / 57 reviews**. Also, the hero section of sell.html at line 621 reads "27 Five-Star Zillow Reviews" — Zillow reviews (27) and Google reviews (57) are separate pools. They must not be conflated. Publishing "5.0" in structured data when actual rating is 4.9 is a false advertising violation.

**Fix — Replace lines 37–47 in sell.html:**

```json
"aggregateRating": {
  "@type": "AggregateRating",
  "ratingValue": "4.9",
  "reviewCount": "57",
  "bestRating": "5",
  "worstRating": "1",
  "description": "Based on Google Reviews"
}
```

And replace the sell hero trust text at line 621:
```
CURRENT: <strong>27</strong> &nbsp;Five-Star Zillow Reviews
REPLACE: <strong>27</strong> &nbsp;Five-Star Zillow Reviews &nbsp;·&nbsp; <strong>57</strong> Google Reviews
```

Add a note or tooltip clarifying these are different review sources.

Also update the v1 index.html Google Reviews banner (line 635) which shows "5.0" instead of "4.9":
**File:** `/Users/nidhigadura/Jagex/gadura-realestate/index.html`, line 635:
```
CURRENT: <span style="font-size:26px;font-weight:800;color:#1B2A6B;font-family:'Playfair Display',serif;">5.0</span>
REPLACE: <span style="font-size:26px;font-weight:800;color:#1B2A6B;font-family:'Playfair Display',serif;">4.9</span>
```

---

### [H-1] HIGH — Agency Disclosure (NY RPL §443): v2/index.html

**Requirement:** NY RPL §443 requires that agency disclosure be made at first substantive contact. Websites must either include the full agency disclosure text OR make it unambiguously clear that it will be provided before any substantive discussion.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/index.html`

**Problem:** The footer at line 711 links to `about.html#compliance` with the text "Agency Disclosure (NY RPL §443)" — this is a link only, not disclosure text. HUD and DOS guidance requires the disclosure to be accessible and visible on the page, not just buried in a footer link.

**Fix — In the footer-bottom section, after the `<div class="fair-housing">` block (after line 720), add:**

```html
<div class="agency-disclosure" style="margin-top:1.2rem;font-size:0.82rem;color:rgba(247,241,232,0.65);line-height:1.65;border-top:1px solid rgba(247,241,232,0.12);padding-top:1.2rem;">
  <strong style="color:rgba(247,241,232,0.85);">Agency Disclosure (NY RPL §443):</strong>
  Before working with a real estate professional in New York, you should understand that different brokerage relationships are available, which include buyer's agency, seller's agency, and dual agency (representing both buyer and seller). Gadura Real Estate LLC will provide you with an Agency Disclosure Form at or before the first substantive contact regarding a specific property. A copy of the NYS Agency Disclosure Form is available at <a href="https://gadurarealestate.com/about.html#compliance" style="color:var(--saffron);">gadurarealestate.com/about</a>.
</div>
```

---

### [H-2] HIGH — Agency Disclosure Missing: Both Situation Pages

**Same requirement as H-1.** Neither `inherited-house-queens.html` nor `selling-before-foreclosure-queens.html` contains any agency disclosure language — not even a link.

**Files:**  
- `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`
- `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`

Both pages have identical footer structures. The footer-bottom div exists but only shows the link "Agency Disclosure (NY RPL §443)" at lines 857 and 1238 respectively — same issue as v2/index.html.

**Fix for both pages — Same fix as H-1:** Add the inline agency disclosure text block in each page's footer-bottom, after the `<div class="fair-housing">` closing tag.

Use the same replacement HTML block shown in H-1.

---

### [H-3] HIGH — Broker License Number Missing: inherited-house-queens.html Agent Section

**Requirement:** NY DOS Rule 175.25. Broker's name and license number must appear prominently on all advertising material.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`

**Problem:** The agent CTA section (lines 775–790) shows Nitin's number (NYS Lic. #10401383405 at line 1167 in the foreclosure page, but NOT on the inherited page). The inherited page agent CTA section (around line 775) has no license number displayed at all and no broker name with license. The footer copyright line (line 861) has `NYS Broker Lic. #10991238487` — but DOS Rule 175.25 requires this to be prominent, not just in a copyright notice.

**Fix — Add to the agent CTA section note (after line 788 `<p class="agent-cta-note">`), replace with:**

```html
<p class="agent-cta-note">Available 7 days a week. Evening appointments available.</p>
<p class="agent-cta-note" style="margin-top:0.5rem;">
  Nitin K. Gadura, Licensed Real Estate Salesperson, NYS Lic. #10401383405<br>
  Supervised by Vinod K. Gadura, Licensed Real Estate Broker, NYS Lic. #10991238487<br>
  Gadura Real Estate LLC · 106-09 101st Ave, Ozone Park, NY 11416
</p>
```

---

### [H-4] HIGH — Short Sale Implied Approval: selling-before-foreclosure-queens.html

**Requirement:** NAR Code of Ethics Article 12; NY DOS advertising standards. Short sale pages must not imply guaranteed lender approval.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`

**Problem:** Line 884 in the process steps states: "If there is a shortfall, we've already coordinated a short sale approval with your lender." This implies approval is a certainty. Short sale approval is never guaranteed — lenders can reject, demand higher payoffs, or counter.

**Fix — Replace line 884:**
```
CURRENT: "If there is a shortfall, we've already coordinated a short sale approval with your lender."
REPLACE: "If there is a shortfall, we will work with your lender to seek short sale approval — note that lender approval is required and is not guaranteed. We initiate this process as early as possible to maximize your options."
```

Also at line 974, the legal item on short sales states:
```
"We handle short sales and will work with your lender directly."
```
This is fine as worded. No change needed there.

---

### [H-5] HIGH — Property Condition Disclosure Missing: sell.html

**Requirement:** NY RPL §462. The sell.html page is the primary seller-facing page and has no reference to the PCDS requirement.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`

**Fix — Add the following to the FAQ section (insert as a new FAQ item after the "Do you handle two-family" item, before the closing `</div>` of the FAQ flex container around line 1051):**

```html
<div class="faq-item fade-in delay-3">
  <button class="faq-q" aria-expanded="false">
    What is the Property Condition Disclosure Statement?
    <svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18"><polyline points="6 9 12 15 18 9"/></svg>
  </button>
  <div class="faq-a">
    New York Real Property Law §462 requires that sellers of residential real property complete and deliver a Property Condition Disclosure Statement (PCDS) to the buyer before signing a binding contract of sale. The PCDS is a standardized form asking about the physical condition of the property — roof, plumbing, electrical, environmental conditions, and more. Sellers who choose not to complete it must provide the buyer a $500 credit at closing. We will provide you the form and help you complete it accurately. This is a seller obligation — not optional.
  </div>
</div>
```

Also add to the sell page footer legal text (line 1182), after "No specific sale price or timeline is guaranteed.":

```
NY RPL §462 requires sellers to complete a Property Condition Disclosure Statement or provide a $500 buyer credit at closing.
```

---

### [H-6] HIGH — Property Condition Disclosure Missing: v2/index.html

**Same requirement as H-5.** The sell tab of the homepage hero form directs sellers to submit valuations but never mentions the PCDS requirement.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/index.html`

**Fix — In the sell tab panel (around line 305), add after the submit button and before the closing `</div>` of the sell panel:**

```html
<p class="hint center" style="margin-top:0.6rem;font-size:0.75rem;">
  NY sellers are required to complete a Property Condition Disclosure Statement (RPL §462) or provide a $500 buyer credit. We'll walk you through this.
</p>
```

---

### [H-7] HIGH — Broker Identity in Inherited Page Agent Section

**Requirement:** NY DOS Rule 175.25. Every advertisement must identify the licensed broker.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`

The agent CTA section (lines 775–790) promotes Nitin exclusively without identifying the supervising broker or the brokerage. The fix in H-3 above covers this — implement H-3 fix.

---

### [H-8] HIGH — NAR Settlement Disclosure Missing: sell.html

**Requirement:** Post-August 2024 NAR Settlement. All seller-facing pages should disclose that buyer representation agreements are now required before touring properties, and that commission arrangements have changed.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`

**Problem:** The footer legal section (line 1182) is present but does not mention the NAR settlement or buyer representation agreement requirement. The v1 index.html footer includes this language but sell.html does not.

**Fix — Add to the footer legal paragraph (line 1182), at the end:**

```
In accordance with the 2024 NAR Settlement, buyer representation agreements are required prior to touring properties. Contact us for details on buyer representation options.
```

---

### [M-1] MEDIUM — EHO Logo vs Text: v2 Pages

**Requirement:** HUD guidelines state that the Equal Housing Opportunity logo (house-with-equal-sign) should appear on all advertising material, or the text "Equal Housing Opportunity" printed in type clearly visible in size.

**Files:** All v2 pages use text only: `<strong style="color:var(--cream);">Equal Housing Opportunity.</strong>` — no logo.

**Finding:** Text-only is technically permissible under HUD regulations for websites but using the actual logo is best practice and more defensible. The v1 index.html and sell.html both include an SVG logo (lines 793–796 and 1080–1083 respectively) — the v2 pages should match.

**Fix — In all v2 pages, replace the fair-housing text-only div with the following (example for v2/index.html, lines 717–720):**

```html
<div class="fair-housing" style="display:flex;align-items:flex-start;gap:1rem;">
  <svg viewBox="0 0 50 50" width="36" height="36" aria-label="Equal Housing Opportunity" style="flex-shrink:0;margin-top:2px;">
    <rect width="50" height="50" fill="#1a1410" rx="2"/>
    <path d="M25 8L8 22h5v20h10V30h4v12h10V22h5z" fill="#f7f1e8"/>
    <text x="25" y="46" text-anchor="middle" fill="#f7f1e8" font-size="5.5" font-family="Arial,sans-serif">EQUAL HOUSING</text>
  </svg>
  <span>
    <strong style="color:var(--cream);">Equal Housing Opportunity.</strong>
    All real estate advertised herein is subject to the Federal Fair Housing Act and New York State Executive Law §296. We do not discriminate on the basis of race, color, religion, sex, handicap, familial status, national origin, source of lawful income (including Section 8 vouchers), or any other protected class. In accordance with the 2024 NAR Settlement, buyer representation agreements are required prior to touring properties.
  </span>
</div>
```

Apply to all three v2 pages (v2/index.html line 717, inherited-house-queens.html line 863, selling-before-foreclosure-queens.html line 1244).

---

### [M-2] MEDIUM — EHO Missing "Source of Lawful Income": sell.html

**Requirement:** NY Exec Law §296-a adds "source of lawful income" (including Section 8 housing vouchers) as a protected class — unique to New York and not in the federal list. This must be included in all NY real estate advertising.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`, line 1086:

```
CURRENT: "...handicap, familial status, national origin, or any other protected class."
REPLACE: "...handicap, familial status, national origin, source of lawful income (including Section 8 vouchers), or any other protected class."
```

Note: v1 index.html (line 799) and all v2 pages correctly include this language. sell.html is the outlier.

---

### [M-3] MEDIUM — Market Data Sourcing: sell.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`, lines 779–798.

The "Queens Market Snapshot — Q1 2026" card presents specific figures (Median $710,000, 34 days, 98.2% list-to-sale, +4.8% YoY) as current facts. A disclaimer exists at line 799 ("Source: OneKey® MLS data, Q1 2026. All information deemed reliable but not guaranteed.") which is good. However the urgency bar (line 703) presents "Median days on market is 34 days" as a fact without any qualifier.

**Fix — Replace line 703:**
```
CURRENT: "Queens Seller's Market 2026: Median days on market is <strong>34 days</strong>."
REPLACE: "Queens Seller's Market 2026: Median days on market is approx. <strong>34 days</strong> (OneKey® MLS, Q1 2026 — conditions vary by neighborhood and property type)."
```

---

### [M-4] MEDIUM — Placeholder Case Study: inherited-house-queens.html (NAR Art. 12)

**Requirement:** NAR Code of Ethics Article 12 — all claims must be honest and verifiable.

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`, lines 587–602.

**Problem:** The case study (the $580K cash offer vs $661K MLS sale story) appears alongside a note at lines 596–602 explicitly flagging it as a placeholder: "Note to site owner: Replace the above with a real client story before launch."

This placeholder content — a fictional case study with specific dollar figures — must **not be published live**. If this page is already indexed or live, the specific figures ($661,000, $81,000 more, 19 days) are unverifiable and constitute potentially false advertising under NAR Article 12 and NY DOS advertising standards.

**Action Required:** Replace with a real, verified client story with client permission (first names only), or replace the entire block with general language such as:

```html
<div class="case-study-card" data-reveal>
  <span class="case-study-label">Our Approach</span>
  <blockquote>
    Estate properties require patience and the right buyer — not just the fastest close. 
    Our team has helped Queens families navigate inherited sales where an early cash investor 
    offer was significantly below what a properly marketed listing ultimately achieved. 
    We will give you both numbers so you can make an informed decision.
  </blockquote>
  <p style="margin-top:1.2rem;font-size:0.88rem;color:var(--ink-soft);">
    <a href="https://gadurarealestate.com/reviews.html">Read verified client reviews →</a>
  </p>
</div>
```

---

### [M-5] MEDIUM — Placeholder Case Study: selling-before-foreclosure-queens.html (NAR Art. 12)

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`, lines 901–936.

**Problem:** The case study has a placeholder warning ("Replace before launch") at line 901, but the actual story text and numbers ARE present (lines 914–935: "$420K investor offer → $511K final price → $87K to seller → 34 days"). This is a composite/illustrative story, not a verified real transaction.

Same issue as M-4 — fictional dollar figures in advertising constitute a potential false advertising violation.

**Action Required:** Same as M-4. Either verify with a real client story (get written permission) or replace with general language as shown in M-4 above.

---

### [M-6] MEDIUM — Guaranteed Close Timeline Claims: selling-before-foreclosure-queens.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/selling-before-foreclosure-queens.html`, lines 825–826 and 871.

**Problem 1** — The options comparison card (line 825–826) states as a "good" outcome: "30–45 days to contract in most Queens neighborhoods" as if this is a guaranteed Gadura outcome for pre-foreclosure sellers. This framing implies a guarantee of timeline.

**Problem 2** — Step 5 of the process (line 871) states: "We price for 30–45."

**Fix — Add qualifiers:**

Line 826:
```
CURRENT: "30–45 days to contract in most Queens neighborhoods"
REPLACE: "Target: 30–45 days to contract in most Queens neighborhoods (market conditions and property apply)"
```

Line 871:
```
CURRENT: "We price for 30–45."
REPLACE: "We price for a 30–45 day timeline where market conditions allow — no specific timeline is guaranteed."
```

---

### [M-7] MEDIUM — "97% List-to-Sale Ratio" Claim: sell.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`, lines 720 and 772.

**Problem:** Line 720 shows "97%" as a Gadura stat labeled "List-to-Sale Ratio." Line 772 states "Our sellers average 97% of list price." This is an advertised performance claim. If this is not documented by actual transaction data, it violates NAR Article 12 and NY DOS advertising standards. The market snapshot card at line 789 shows "98.2%" as a market-wide figure from OneKey® MLS — these two numbers will confuse consumers.

**Action Required:** Verify this 97% figure against actual closed transaction records. If it cannot be verified, replace with the market figure or remove.

If verified, add a qualifier:
```
"Our sellers have averaged 97% of list price across transactions closed 2020–2025 (based on Gadura Real Estate LLC closed sales data)."
```

---

### [M-8] MEDIUM — Testimonial Verification: sell.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`, lines 900–930.

**Problem:** The sell page shows three testimonials with initials and neighborhood but slightly different details than the same "clients" appear in v1 index.html:
- "Rajesh P." (index.html line 556) vs "Rajesh S." (sell.html line 904) — same Ozone Park seller, different last initial
- "Priya & Amit S." (index.html, buyers in Richmond Hill) vs "Priya M." (sell.html, seller in Richmond Hill) — possibly two different people or an error
- "Daljeet & Simran K." (index.html, investors in Jamaica) vs "Devika K." (sell.html, seller in Jamaica)

Under NAR Article 12, testimonials must be from actual clients. Inconsistent initial attribution across pages raises authenticity questions.

**Action Required:** Standardize testimonials to match actual Google Reviews. Each testimonial should link to or note the platform it was sourced from. Do not use composite or illustrative testimonials.

---

### [M-9] MEDIUM — Google Rating Banner Shows 5.0: v1 index.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/index.html`, line 635.

**Problem:** The "Google Reviews" banner widget shows "5.0" in large type with five stars while:
- The same page's stats bar shows "4.9 stars / 57 reviews"
- The structured data shows "4.9"
- The Google review link points to a real listing that shows 4.9

A "5.0" claim when the actual rating is 4.9 is a false advertising violation.

**Fix:**
```
CURRENT: <span style="font-size:26px;...">5.0</span>
REPLACE: <span style="font-size:26px;...">4.9</span>
```

Also update the subtext (line 639):
```
CURRENT: "50+ verified Google reviews for Gadura Real Estate"
REPLACE: "57 verified Google reviews for Gadura Real Estate"
```

---

### [L-1] LOW — RESPA Referral: inherited-house-queens.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/v2/situations/inherited-house-queens.html`, line 737.

**Problem:** The FAQ item "Do we have to clean out the house before selling?" mentions: "We can connect you with estate sale companies to handle the contents before closing." RESPA (12 U.S.C. §2607) prohibits receiving kickbacks for referrals involving a real estate settlement service. If Gadura has any referral arrangement with estate sale companies or receives any compensation, this must be disclosed.

**Action Required:** If no referral arrangement exists, add: "We have no financial relationship with any estate sale companies we may mention." If one does exist, add a full RESPA-compliant referral disclosure.

---

### [L-2] LOW — Tenant Protection Act Advisory

**Finding:** No current pages appear to contain guidance on evicting tenants from investment or inherited properties. If situation pages for "selling a tenant-occupied property" are added in future, they must not advise sellers in ways that could constitute unlawful eviction guidance under NY's Tenant Protection Act of 2019. Flag for any new content development.

---

### [L-3] LOW — IDX Copyright Date: sell.html

**File:** `/Users/nidhigadura/Jagex/gadura-realestate/sell.html`, line 1182.

The IDX disclaimer in the footer does not include the OneKey® copyright year. While not strictly a legal violation, OneKey® MLS membership terms typically require the copyright notice.

**Fix — In the footer legal paragraph, add:**
```
"...IDX data provided exclusively for consumers' personal, non-commercial use. © 2026 OneKey® MLS. All Rights Reserved."
```

---

## UNIVERSAL COMPLIANCE FOOTER BLOCK

The following HTML block should replace the current `footer-bottom` closing content on **every page** of the site. It covers EHO, license disclosure, agency disclosure, wire fraud, PCDS notice, and NAR settlement — all in one place.

```html
<!-- ================================================================
     UNIVERSAL COMPLIANCE FOOTER — Required on every page
     Covers: Fair Housing, License Disclosure, Agency Disclosure,
     PCDS Notice, NAR Settlement, Wire Fraud
     NY Exec Law §296, NY RPL §443, NY RPL §462, NY DOS Rule 175.25
     ================================================================ -->
<div class="compliance-footer" style="background:#111;color:rgba(255,255,255,0.6);font-size:0.78rem;line-height:1.7;padding:2rem 0;border-top:1px solid rgba(255,255,255,0.08);">
  <div class="wrap" style="max-width:1200px;margin:0 auto;padding:0 1.5rem;">

    <!-- Wire Fraud Warning -->
    <div style="background:#7f1d1d;color:#fff;padding:0.8rem 1.2rem;margin-bottom:1.5rem;border-left:4px solid #fbbf24;font-size:0.82rem;">
      <strong>⚠ Wire Fraud Warning:</strong> Gadura Real Estate LLC will <strong>NEVER</strong> send wire transfer instructions by email or text. If you receive any such request, call <a href="tel:+17188500010" style="color:#fbbf24;font-weight:700;">(718) 850-0010</a> immediately before transferring any funds.
    </div>

    <!-- EHO + License Block -->
    <div style="display:flex;gap:1.2rem;align-items:flex-start;margin-bottom:1.2rem;">
      <!-- EHO Logo (SVG) -->
      <svg viewBox="0 0 50 50" width="40" height="40" aria-label="Equal Housing Opportunity logo" style="flex-shrink:0;margin-top:2px;">
        <rect width="50" height="50" fill="#1B2A6B" rx="2"/>
        <path d="M25 8L8 22h5v20h10V30h4v12h10V22h5z" fill="#fff"/>
        <text x="25" y="46" text-anchor="middle" fill="#fff" font-size="5.5" font-family="Arial,sans-serif" font-weight="700">EQUAL HOUSING</text>
      </svg>
      <div>
        <strong style="color:rgba(255,255,255,0.85);">Equal Housing Opportunity.</strong>
        All real estate advertised herein is subject to the Federal Fair Housing Act (42 U.S.C. §3604) and New York State Executive Law §296, which make it illegal to advertise any preference, limitation, or discrimination because of race, color, religion, sex, handicap, familial status, national origin, <strong>source of lawful income (including Section 8 housing vouchers)</strong>, military status, age, marital status, sexual orientation, gender identity, or any other protected class under applicable law. Gadura Real Estate LLC is pledged to the letter and spirit of equal housing opportunity.
      </div>
    </div>

    <!-- Agency Disclosure -->
    <p style="margin-bottom:1rem;">
      <strong style="color:rgba(255,255,255,0.85);">Agency Disclosure (NY RPL §443):</strong>
      Before working with a real estate professional in New York State, you should understand that different brokerage relationships are available, which include buyer's agency, seller's agency, and dual agency (broker representing both buyer and seller in the same transaction). Gadura Real Estate LLC will provide you with a written Agency Disclosure Form at or before the first substantive contact regarding a specific property. Dual agency requires the informed written consent of both buyer and seller.
    </p>

    <!-- PCDS Notice -->
    <p style="margin-bottom:1rem;">
      <strong style="color:rgba(255,255,255,0.85);">Property Condition Disclosure (NY RPL §462):</strong>
      Sellers of residential real property in New York are required to complete and deliver a Property Condition Disclosure Statement to the buyer prior to signing a binding contract of sale, or provide the buyer with a $500 credit at closing. This obligation applies to all residential sales, including estate, as-is, and pre-foreclosure sales.
    </p>

    <!-- Lead Paint Notice -->
    <p style="margin-bottom:1rem;">
      <strong style="color:rgba(255,255,255,0.85);">Lead Paint Disclosure (42 U.S.C. §4852d):</strong>
      Federal law requires sellers of homes built before 1978 to disclose any known lead-based paint hazards and provide buyers with the EPA pamphlet "Protect Your Family From Lead in Your Home." Most homes in Queens were built prior to 1978. This disclosure will be provided by your agent before contract execution.
    </p>

    <!-- NAR Settlement -->
    <p style="margin-bottom:1rem;">
      <strong style="color:rgba(255,255,255,0.85);">NAR Settlement (Effective August 2024):</strong>
      Written buyer representation agreements are required before touring properties. Commission arrangements are negotiable. Contact us for details on buyer representation options and how our compensation is structured.
    </p>

    <!-- License & Brokerage Identity -->
    <p style="margin-bottom:1rem;border-top:1px solid rgba(255,255,255,0.1);padding-top:1rem;">
      <strong style="color:rgba(255,255,255,0.85);">Gadura Real Estate LLC</strong>
      is licensed by the New York State Department of State.
      <strong>Vinod K. Gadura</strong>, Licensed Real Estate Broker/Owner — NYS Broker License #10991238487.
      All salespersons licensed by the NYS Department of State and supervised by the licensed broker.
      Principal office: 106-09 101st Ave, Ozone Park, NY 11416. Tel: (718) 850-0010.
    </p>

    <!-- CMA Disclaimer -->
    <p style="margin-bottom:1rem;">
      Free home valuations provided by Gadura Real Estate LLC are Comparative Market Analyses (CMAs) — a professional opinion of value prepared by a licensed salesperson or broker. A CMA is <strong>not</strong> a licensed appraisal. For a certified appraisal for legal or financial purposes, consult a NYS-certified real estate appraiser. No specific sale price or timeline is guaranteed.
    </p>

    <!-- IDX / MLS Disclaimer -->
    <p style="margin-bottom:0.5rem;">
      The data relating to real estate for sale or lease on this website comes in part from the OneKey® MLS. Real estate listings held by brokerage firms other than Gadura Real Estate LLC are marked with the OneKey® MLS logo. IDX information is provided exclusively for consumers' personal, non-commercial use and may not be used for any purpose other than to identify prospective properties consumers may be interested in purchasing. Information is deemed reliable but not guaranteed. © 2026 OneKey® MLS. All Rights Reserved.
    </p>

    <!-- Copyright + Legal Links -->
    <div style="display:flex;flex-wrap:wrap;gap:1rem;justify-content:space-between;align-items:center;margin-top:1.2rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.08);">
      <span>© 2026 Gadura Real Estate LLC · NYS Broker Lic. #10991238487 · OneKey® MLS Member · REBNY Member</span>
      <div style="display:flex;gap:1rem;flex-wrap:wrap;">
        <a href="/privacy-policy.html" style="color:rgba(255,255,255,0.45);">Privacy Policy</a>
        <a href="/terms.html" style="color:rgba(255,255,255,0.45);">Terms of Use</a>
        <a href="/fair-housing.html" style="color:rgba(255,255,255,0.45);">Fair Housing Statement</a>
        <a href="/about.html#compliance" style="color:rgba(255,255,255,0.45);">Agency Disclosure</a>
        <a href="/about.html#nar-settlement" style="color:rgba(255,255,255,0.45);">NAR Settlement Notice</a>
        <a href="/terms.html#accessibility" style="color:rgba(255,255,255,0.45);">Accessibility</a>
      </div>
    </div>

  </div>
</div>
<!-- END UNIVERSAL COMPLIANCE FOOTER -->
```

---

## IMPLEMENTATION PRIORITY CHECKLIST

### Before Any Page Goes Live (Critical)
- [ ] [C-1] Add PCDS disclosure to inherited-house-queens.html
- [ ] [C-2] Add lead paint disclosure to inherited-house-queens.html
- [ ] [C-3] Add lead paint + PCDS disclosure to selling-before-foreclosure-queens.html
- [ ] [C-4] Add prominent §265-b foreclosure counseling disclosure block
- [ ] [C-5] Fix rating conflict: sell.html JSON-LD to 4.9/57; fix "5.0" banner in index.html

### Before Launch (High — Regulatory)
- [ ] [H-1] Add inline agency disclosure text to v2/index.html footer
- [ ] [H-2] Add inline agency disclosure text to both situation pages
- [ ] [H-3] Add broker/salesperson license numbers to inherited page agent CTA
- [ ] [H-4] Soften "short sale approval" language to remove implied guarantee
- [ ] [H-5] Add PCDS reference to sell.html FAQ
- [ ] [H-6] Add PCDS hint to v2/index.html sell form panel
- [ ] [H-8] Add NAR settlement language to sell.html footer

### Within 30 Days (Medium — Best Practice)
- [ ] [M-1] Add EHO logo SVG to all v2 page fair-housing blocks
- [ ] [M-2] Add "source of lawful income" to sell.html EHO statement
- [ ] [M-3] Qualify urgency bar market data claim
- [ ] [M-4] Replace or verify inherited-house case study — obtain real client permission
- [ ] [M-5] Replace or verify foreclosure page case study — obtain real client permission
- [ ] [M-6] Add timeline qualifiers to foreclosure options comparison
- [ ] [M-7] Verify and document 97% list-to-sale claim with actual transaction records
- [ ] [M-8] Standardize testimonials across pages; link to actual Google Reviews
- [ ] [M-9] Fix "5.0" → "4.9" and "50+" → "57" in v1 index.html Google banner

### Next Revision Cycle (Low — Advisory)
- [ ] [L-1] Add RESPA no-referral-fee disclosure for estate sale company mentions
- [ ] [L-2] Flag for tenant-protection compliance if any new tenant-occupied-sale content is created
- [ ] [L-3] Add OneKey® MLS copyright year to sell.html IDX disclaimer

---

## PAGES WITH STRONGEST COMPLIANCE (REFERENCE)

The **v1 index.html** (`/Users/nidhigadura/Jagex/gadura-realestate/index.html`) is the most compliant page on the site:
- Has EHO logo (SVG) + full text (line 793–799)
- Includes "source of lawful income" protected class
- Has explicit agency disclosure language (line 799)
- Has wire fraud bar (lines 810–825)
- Has broker license number in multiple locations
- Has NAR settlement language (line 917)

Use this page as the template for compliance when building new pages.

---

## LEGAL DISCLAIMER ON THIS AUDIT

This compliance audit is a professional opinion prepared for the benefit of Gadura Real Estate LLC and is not legal advice. Real estate law is subject to change. Before publishing any content touching on agency relationships, fair housing, foreclosure, or lead paint disclosure, you should have the specific language reviewed by a licensed New York real estate attorney. Nothing in this document creates an attorney-client relationship.
