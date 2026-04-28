#!/usr/bin/env python3
"""
build_topical_hubs.py — Generate 5 topical cluster hub pages.

Topical clusters are the highest-value SEO architecture in 2026:
- Each hub is the "pillar" page for a topic
- Subtopic pages link UP to the hub via internal anchor links
- Hub links DOWN to all subtopic pages
- AI engines treat the hub as the canonical authority for that topic

Hubs built here:
1. /first-time-homebuyer/index.html
2. /multi-family-investment/index.html
3. /co-op-board-help/index.html
4. /1031-exchange/index.html
5. /fha-loans-nyc/index.html
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HUB_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="https://gadurarealestate.com/{slug}/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="https://gadurarealestate.com/{slug}/">
<meta property="og:type" content="article">
<meta property="og:image" content="https://gadurarealestate.com/images/nitin-gadura-headshot.jpg">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta name="author" content="Nitin Gadura">
<link rel="icon" href="/images/logo-icon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--green:#00A651;--navy:#1B2A6B;--dark-navy:#0F1A40;--light:#f5f5f5;--text:#333;--border:#ddd}}
  body{{font-family:'Open Sans',sans-serif;color:var(--text);line-height:1.7;background:#fff}}
  a{{color:var(--navy);text-decoration:none}} a:hover{{color:var(--green)}}
  header{{background:var(--navy);color:#fff;padding:14px 0;position:sticky;top:0;z-index:100}}
  .container{{max-width:980px;margin:0 auto;padding:0 24px}}
  .header-inner{{display:flex;justify-content:space-between;align-items:center}}
  .logo{{color:#fff;font-weight:700}} nav a{{color:#fff;margin-left:18px;font-size:14px}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--dark-navy));color:#fff;padding:64px 0 48px}}
  .hero h1{{font-family:Montserrat;font-size:clamp(28px,4vw,42px);margin-bottom:14px;line-height:1.3}}
  .hero .lede{{font-size:18px;max-width:780px;opacity:.95;margin-bottom:18px}}
  .hero .badges{{display:flex;flex-wrap:wrap;gap:8px}}
  .hero .badge{{background:rgba(255,255,255,.18);padding:6px 14px;border-radius:18px;font-size:13px;backdrop-filter:blur(6px)}}
  .answer-first{{background:#fff8e1;border-left:4px solid var(--green);padding:24px;margin:32px 0;border-radius:6px;font-size:17px}}
  .answer-first strong{{color:var(--navy)}}
  section{{padding:42px 0;border-bottom:1px solid var(--border)}}
  section h2{{font-family:Montserrat;color:var(--navy);font-size:28px;margin-bottom:16px;line-height:1.3}}
  section h3{{font-family:Montserrat;color:var(--navy);font-size:20px;margin:22px 0 10px}}
  section p{{margin-bottom:14px}} ul{{margin:0 0 16px 22px}} li{{margin-bottom:6px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:18px}}
  .card{{background:var(--light);padding:22px;border-radius:8px;border-left:3px solid var(--green)}}
  .card h4{{font-family:Montserrat;color:var(--navy);font-size:17px;margin-bottom:8px}}
  .card a.cta{{display:inline-block;margin-top:8px;font-weight:600;color:var(--green);font-size:14px}}
  .step-list{{counter-reset:step;list-style:none;padding:0;margin-top:18px}}
  .step-list li{{counter-increment:step;padding:18px 22px 18px 60px;background:var(--light);border-radius:8px;margin-bottom:10px;position:relative}}
  .step-list li::before{{content:counter(step);position:absolute;left:18px;top:18px;width:30px;height:30px;background:var(--green);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-family:Montserrat}}
  .faq-item{{padding:18px 22px;background:var(--light);border-radius:8px;margin-bottom:10px}}
  .faq-item .q{{font-weight:700;color:var(--navy);margin-bottom:8px}}
  .agent-card{{background:linear-gradient(135deg,#fff,var(--light));border:2px solid var(--green);border-radius:12px;padding:28px;margin:32px 0;display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center}}
  .agent-card img{{width:120px;height:120px;border-radius:50%;border:3px solid var(--green);object-fit:cover}}
  .btn{{display:inline-block;padding:12px 24px;border-radius:6px;background:var(--green);color:#fff;font-weight:600}}
  footer{{background:var(--dark-navy);color:rgba(255,255,255,.85);padding:32px 0;text-align:center;font-size:13px}}
  footer a{{color:rgba(255,255,255,.85)}}
  @media(max-width:640px){{.agent-card{{grid-template-columns:1fr;text-align:center}}.agent-card img{{margin:0 auto}}}}
</style>

<script type="application/ld+json" id="ai-hub-howto">
{howto_jsonld}
</script>

<script type="application/ld+json" id="ai-hub-faq">
{faq_jsonld}
</script>

<script type="application/ld+json" id="ai-hub-breadcrumb">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://gadurarealestate.com/"}},
    {{"@type": "ListItem", "position": 2, "name": "Resources", "item": "https://gadurarealestate.com/resources.html"}},
    {{"@type": "ListItem", "position": 3, "name": "{topic}", "item": "https://gadurarealestate.com/{slug}/"}}
  ]
}}
</script>
</head>
<body data-page-type="topical-hub" data-topic="{slug}">

<header>
  <div class="container header-inner">
    <a href="/" class="logo">Gadura Real Estate</a>
    <nav>
      <a href="/buy.html">Buy</a>
      <a href="/sell.html">Sell</a>
      <a href="/resources.html">Resources</a>
      <a href="tel:+19177050132">📞 (917) 705-0132</a>
    </nav>
  </div>
</header>

<section class="hero">
  <div class="container">
    <h1>{h1}</h1>
    <p class="lede">{hero_lede}</p>
    <div class="badges">{hero_badges}</div>
  </div>
</section>

<div class="container">

<div class="answer-first">
<strong>{answer_first_lead}</strong> {answer_first_body} Free 30-minute consultation in English, Hindi, Punjabi, Bengali, Spanish, or Guyanese Creole. Call <a href="tel:+19177050132"><strong>(917) 705-0132</strong></a>.
</div>

<section>
<h2>The Step-by-Step Process</h2>
<ol class="step-list">
{steps_html}
</ol>
</section>

<section>
<h2>Key Things to Know</h2>
<div class="grid">
{cards_html}
</div>
</section>

<section>
<h2>Frequently Asked Questions</h2>
{faq_html}
</section>

<section>
<h2>Related Resources</h2>
<ul>
{related_links}
</ul>
</section>

<div class="agent-card">
  <img src="/images/nitin-gadura-headshot.jpg" alt="Nitin Gadura, Licensed NYS Real Estate Salesperson">
  <div>
    <h3 style="font-family:Montserrat;color:var(--navy);margin-bottom:6px">Need personal guidance on {topic_lower}?</h3>
    <p style="margin-bottom:12px;color:#555">Nitin Gadura, NYS Salesperson #10401383405. 7+ years experience, $100M+ closed, multilingual. Free consultation.</p>
    <a class="btn" href="tel:+19177050132">📞 Call (917) 705-0132</a>
  </div>
</div>

</div>

<footer>
  <div class="container">
    <p><strong>Gadura Real Estate, LLC</strong> · 106-09 101st Ave, Ozone Park, NY 11416 · NYS Firm Broker License #10991238487 · Authored by <a href="/author/nitin-gadura.html">Nitin Gadura</a> · © 2026</p>
  </div>
</footer>

</body>
</html>
"""

HUBS = [
    {
        "slug": "first-time-homebuyer",
        "topic": "First-Time Homebuyer Guide (NYC + Long Island)",
        "topic_lower": "first-time homebuying",
        "title": "First-Time Homebuyer Guide NYC + Long Island 2026 | Gadura Real Estate",
        "meta_desc": "Complete first-time homebuyer guide for NYC + Long Island: FHA, SONYMA, HomeReady, VA loans, $15K down-payment grants, every step explained. By Nitin Gadura, NYS Salesperson.",
        "h1": "First-Time Homebuyer Guide — NYC + Long Island",
        "hero_lede": "Every step of buying your first home in New York: pre-approval, programs, neighborhoods, offers, inspection, closing. Multilingual representation, 4.9★ rating.",
        "hero_badges": [
            "FHA · SONYMA · HomeReady · VA",
            "$15K Down-Payment Grant",
            "Hindi · Punjabi · Bengali · Spanish",
        ],
        "answer_first_lead": "Buying your first home in NYC or Long Island?",
        "answer_first_body": "The most important first move is pulling all 3 credit scores and getting pre-approved with at least 2 lenders before you start touring. FHA + SONYMA stacked together can put you in a Queens 1-family with 3.5% down and a $15K state grant — but only if you know to ask. Nitin Gadura has helped 500+ first-time buyers across all 5 boroughs and Long Island.",
        "steps": [
            ("Pull all 3 credit scores", "AnnualCreditReport.com is free. Lenders use the middle score; if it's under 620, work on it before applying. FHA accepts down to 580 with 3.5% down."),
            ("Get pre-approved with 2–3 lenders", "Rate spreads of 0.25% are normal. Compare not just rate but origination fees, points, and lender credits. Don't pay for credit pulls — most lenders waive within 30-day shopping window."),
            ("Apply for SONYMA + check FHA limits", "SONYMA's $15K Down-Payment Assistance Loan stacks with FHA. Income limits by county (~$140K for 1–2 person household in Queens/Nassau). Purchase-price limit ~$827K Queens 1-family."),
            ("Sign a buyer-broker agreement", "Required since the August 2024 NAR settlement. Negotiable. Sets your buyer-side commission and any retainer. Your agent should explain every line."),
            ("Tour 5–10 properties before any offer", "Calibrates your eye. Get familiar with what each price band actually buys in your target neighborhoods. We narrow neighborhoods first, then properties."),
            ("Make a written offer", "Includes price, mortgage contingency, inspection contingency, attorney-review rider, time-of-essence clauses. NY uses 10% earnest money — much higher than other US markets."),
            ("Inspection + attorney review", "5–10 business days typical. NY uses lawyers (not title companies) for closings. Inspection findings are normal — repair credits, not deal collapse."),
            ("Loan underwriting + appraisal", "30–45 days typical. Don't open new credit lines, change jobs, or move large sums during this period — any of those can re-trigger underwriting."),
            ("Close at attorney's office", "Bring driver's license, certified check for closing costs, and the patience for 1–3 hours of signing. Deed recorded within 14 days."),
        ],
        "cards": [
            ("FHA loans accept 580 credit + 3.5% down", "Most lenders push conventional even when FHA is the better choice. Get a written rate comparison for both."),
            ("SONYMA = up to $15K free", "First-time buyer + income/price limits. Stacks with FHA for very low effective down. Money via DPAL forgivable loan."),
            ("Multi-family is house-hacking on FHA", "Buy a 2-family, owner-occupy one unit, rent the other. FHA self-sufficiency requires rent to cover ~75% of mortgage. Common in Queens."),
            ("Co-ops have stricter rules than condos", "Board approval, financial DTI requirements (often 28%/36%), and post-closing maintenance reserves. Plan for 6–8 weeks of board package."),
            ("NY closing costs run 2–4% buyer-side", "Mortgage recording tax (1.8–1.925%), attorney ($1.5–3.5K), title insurance (~0.5–1%), lender fees, prepaid taxes/insurance."),
            ("Mansion tax kicks in at $1M+", "1% tier from $1M, climbs to 3.9% on $25M+. Paid by buyer in NY State. Often missed in initial budget calculations."),
        ],
        "faqs": [
            ("How much do I need to save for a NYC first home?", "For an FHA loan on a $725K Queens median home: 3.5% down ($25,375) + closing costs (~$30K) = ~$55K total. SONYMA's $15K grant cuts the down payment to ~$10K. Plan ~$60K total cash needed conservatively."),
            ("What credit score do I need?", "FHA: 580+ for 3.5% down (some lenders require 620). Conventional: 620+ minimum. VA: lender-dependent (often 580+). Best rates start at 740+. Check all 3 scores at AnnualCreditReport.com."),
            ("How long does the process take?", "Pre-approval to close: typical 60–90 days. Faster is possible (45 days) with cash or strong financing. Co-ops add 4–8 weeks for board package."),
            ("Should I use FHA or conventional?", "FHA: lower credit / lower down / has MIP for life of loan. Conventional: higher credit / can drop PMI at 78% LTV / cheaper long-term if you have 20% down. We model both for every client."),
            ("What's a buyer-broker agreement?", "Written contract between you and your agent. Required since Aug 2024 NAR settlement. Sets buyer-side commission. Negotiable — we walk you through it line by line."),
        ],
        "related": [
            ("/buy.html", "Full buyer's guide"),
            ("/closing-costs-nyc-guide.html", "NYC closing-costs breakdown"),
            ("/coop-board-package-help-queens.html", "Co-op board package guide"),
            ("/multi-family-investment/", "Multi-family investment hub"),
            ("/fha-loans-nyc/", "FHA loans NYC hub"),
            ("/glossary/", "NY real estate glossary"),
        ],
    },
    {
        "slug": "multi-family-investment",
        "topic": "Multi-Family Investment Property NYC",
        "topic_lower": "multi-family investment",
        "title": "Multi-Family Investment Property NYC + Long Island | 2-Fam, 3-Fam Guide",
        "meta_desc": "Complete guide to 2-family, 3-family, and multi-family investment property in Queens, Brooklyn, and Long Island. Cap rates, FHA self-sufficiency, house-hacking, by Nitin Gadura.",
        "h1": "Multi-Family Investment in NYC + Long Island",
        "hero_lede": "Buy a 2-family or 3-family — owner-occupy one unit, rent the rest. The single best wealth-building path for NYC first-generation buyers.",
        "hero_badges": [
            "2-fam · 3-fam · Small mixed-use",
            "House-hack with FHA at 3.5% down",
            "Cap rate analysis included",
        ],
        "answer_first_lead": "Want to buy a 2-family or 3-family in Queens?",
        "answer_first_body": "House-hacking with FHA at 3.5% down is the single most powerful wealth-building tool for NYC first-time buyers. You owner-occupy one unit, rent the others, and the rental income covers ~75% of your mortgage. We close 2-fam and 3-fam deals in Ozone Park, Richmond Hill, Howard Beach, and along the Queens corridor every month.",
        "steps": [
            ("Get FHA-approved with multi-family expertise", "Many lenders only know single-family FHA. You need a lender who's done FHA self-sufficiency calculations. We refer to specific lenders."),
            ("Run rent-comp analysis on the target neighborhoods", "Ozone Park rents differ from Richmond Hill by $200–$400 per unit. We pull rent comps with the listing analysis."),
            ("Calculate FHA self-sufficiency", "75% of the OTHER unit's rent must cover the entire mortgage payment. Many properties don't pencil — we know which do."),
            ("Tour 2-fams in your budget", "Inspect electrical separation, separate gas/electric meters, certificate of occupancy, and any illegal conversions before falling in love."),
            ("Review rent rolls + leases (if tenanted)", "Tenants in possession have rights. Read every lease. Get estoppel certificates from each tenant before going under contract."),
            ("Make offer + inspection + close", "Same as single-family but inspection covers each unit separately. Cap rate, GRM, and DSCR all factor into the analysis."),
        ],
        "cards": [
            ("FHA self-sufficiency is the unlock", "75% of the OTHER unit's rent must cover the FULL mortgage. Many Queens 2-fams pencil at $750K–$900K. Each unit ~$2,200/mo gross."),
            ("3-family beats 2-family on cash flow", "More units, more rent. But also more management. Most first-time owner-occupants start with 2-family."),
            ("Owner-occupy 12 months minimum", "FHA owner-occupant requirement. After that, you can move out and rent all units. Many investors stack 2-fams this way over 5+ years."),
            ("Watch for illegal conversions", "Many older Queens homes have a 'finished basement' that's legally not a unit. Don't pay for non-conforming square footage. CO is everything."),
            ("Cap rate vs cash-on-cash", "Cap rate (NOI / price) is the building's quality. Cash-on-cash (annual cash flow / cash invested) is your actual return. Both matter."),
            ("LLC for non-owner-occupied", "Once you move out, transfer to LLC for liability protection + tax benefits. Use a CPA who knows NY real estate."),
        ],
        "faqs": [
            ("Can I buy a Queens 2-family with FHA at 3.5% down?", "Yes — FHA allows 1-4 unit owner-occupant with 3.5% down at 580+ credit. The OTHER unit's rent (75% counted) must support self-sufficiency. Common Queens 2-fams ($750–$900K) pencil with rents at $2,200+ on the secondary unit."),
            ("What's a good cap rate for Queens 2-family?", "5–6.5% is typical for owner-occupant 2-fams in Queens (lower than pure investment because owner-occupants accept lower returns for the housing benefit). Pure investors look for 7%+. Long Island runs slightly lower (4–5.5%)."),
            ("Should I buy 2-family or single-family for first home?", "Math on 2-family is almost always better long-term — rental income covers most of mortgage. But it's also more management. We model both for every client and let the numbers decide."),
            ("How do I evict a problem tenant in NY?", "NY has strong tenant protections. Holdover or non-payment requires court process (3–9 months typical). Always vet tenants thoroughly upfront — credit, income, references."),
            ("What's the best Queens neighborhood for multi-family?", "Ozone Park, Richmond Hill, South Ozone Park, Howard Beach, Woodhaven for affordability. Astoria, Long Island City for appreciation. Each has different cap-rate dynamics."),
        ],
        "related": [
            ("/buy.html", "Buyer's guide"),
            ("/first-time-homebuyer/", "First-time buyer hub"),
            ("/fha-loans-nyc/", "FHA loans hub"),
            ("/1031-exchange/", "1031 exchange hub"),
            ("/neighborhoods/queens/ozone-park.html", "Ozone Park neighborhood guide"),
            ("/neighborhoods/queens/richmond-hill.html", "Richmond Hill neighborhood guide"),
        ],
    },
    {
        "slug": "co-op-board-help",
        "topic": "Co-op Board Package Help Queens & NYC",
        "topic_lower": "co-op board packages",
        "title": "Co-op Board Package Help Queens & NYC | Application Prep, Interview Coaching",
        "meta_desc": "Complete co-op board package help for Queens, Manhattan, and Brooklyn. Step-by-step application prep, financial statement, reference letters, interview coaching. Free consultation: (917) 705-0132.",
        "h1": "Co-op Board Package Help — Queens, Manhattan, Brooklyn",
        "hero_lede": "Get approved on the first try. Step-by-step prep of your financial statement, references, and board interview. Specialty in Forest Hills, Rego Park, Kew Gardens, Bayside.",
        "hero_badges": [
            "First-try approval rate",
            "4–8 week process",
            "Interview coaching included",
        ],
        "answer_first_lead": "Buying a Queens or NYC co-op?",
        "answer_first_body": "The board package matters more than the offer price. Many qualified buyers get rejected because their package was sloppy, not because their finances were weak. We've prepared hundreds of Queens co-op board packages — Forest Hills, Rego Park, Kew Gardens, Briarwood — and we know exactly what each board cares about.",
        "steps": [
            ("Get the building's specific package requirements", "Every co-op board has its own form. Some want 2 years of returns, some want 3. Some require 1 year of maintenance in reserves, some require 2. Get the exact list first."),
            ("Assemble financial documentation", "Last 2 years tax returns (signed), last 3 pay stubs, last 3 months bank/brokerage statements, current credit report, employment verification letter, loan commitment letter."),
            ("Reference letters", "Typically 2 personal, 2 professional, 1 landlord (if currently renting). Boards judge whether the letter-writer is high-quality, not just whether they exist. Brief them carefully."),
            ("Personal financial statement", "Single sheet listing assets, liabilities, monthly income/expenses. Critical to format cleanly. We have templates board members are used to seeing."),
            ("Cover letter", "Optional but increasingly common. 1 page introducing yourself + your relationship to the building. Emphasize stability, community fit, long-term commitment."),
            ("Submit + wait for interview invitation", "4–8 weeks typical. Some boards interview every applicant; others only borderline ones. The interview is mandatory in most NYC co-ops."),
            ("Board interview prep", "30–60 minute interview. Standard questions: why this building, what's your career, how stable is your income, are you planning a family. We do mock interviews."),
            ("Approval / next steps", "Approval typically takes 1–2 weeks post-interview. If approved, schedule closing. If denied (rare with prep), the board doesn't owe you a reason."),
        ],
        "cards": [
            ("Boards judge stability over wealth", "A $100K stable income with 2 years on the same job beats a $200K income with frequent job changes. Stability wins."),
            ("DTI of 28%/36% is the unwritten rule", "Front-end (housing) ≤28% of gross income. Back-end (all debt) ≤36%. Many co-ops enforce stricter than your lender."),
            ("Maintenance reserves matter", "Most boards want 1–2 years of maintenance in liquid reserves at closing. Plan for this in the cash budget."),
            ("Some boards reject FHA outright", "Especially older Manhattan and Forest Hills co-ops. Always pre-qualify the building before falling in love."),
            ("Pet policies are board-set", "Many co-ops have weight limits, breed restrictions, or no-pet policies. If you have pets, screen aggressively before touring."),
            ("Subletting is restricted", "Most NYC co-ops require you to live in the unit for 1–2 years before subletting, then permit subletting only 1–2 years out of 5. Check the bylaws."),
        ],
        "faqs": [
            ("How long does the board package process take?", "From submission to approval: 4–8 weeks typical for Queens, 6–10 weeks for Manhattan. Plan for 10 weeks total contract-to-close on a co-op."),
            ("What's a typical Queens co-op board interview like?", "30–60 minutes with 3–7 board members. Standard questions about income stability, career, why this building. Be respectful, brief, and professional. Bring 1 set of printed materials in case they ask."),
            ("Can I be rejected after getting financing approval?", "Yes — board approval is separate from lender approval. Boards reject for any non-discriminatory reason and don't have to explain. Strong package + interview prep dramatically reduces rejection risk."),
            ("Do I need a buyer's agent for co-op transactions?", "Strongly recommended. Co-op offering plans, proprietary leases, and house rules each have unique nuances. An experienced buyer's agent has read hundreds of these documents."),
            ("Are co-ops cheaper than condos?", "Per square foot, yes — typically 20–40% cheaper. But monthly maintenance can be higher, financing is harder, and resale is slower. Net total cost of ownership is often comparable."),
        ],
        "related": [
            ("/coop-board-package-help-queens.html", "Original Queens co-op page"),
            ("/buy.html", "Buyer's guide"),
            ("/first-time-homebuyer/", "First-time buyer hub"),
            ("/closing-costs-nyc-guide.html", "NYC closing costs"),
            ("/glossary/", "NY real estate glossary"),
        ],
    },
    {
        "slug": "1031-exchange",
        "topic": "1031 Exchange — Queens & NYC Investors",
        "topic_lower": "1031 exchanges",
        "title": "1031 Exchange Queens NY | Defer Capital Gains on Investment Property",
        "meta_desc": "Complete 1031 like-kind exchange guide for Queens & NYC investors: 45/180-day timelines, qualified intermediary, replacement property strategy. Free consultation: (917) 705-0132.",
        "h1": "1031 Like-Kind Exchange — Queens & NYC Investors",
        "hero_lede": "Defer capital-gains tax by rolling investment-property sale proceeds into a new property within strict IRS timelines. We coordinate every step: identification, replacement, qualified intermediary.",
        "hero_badges": [
            "45-day identification window",
            "180-day exchange close",
            "Qualified Intermediary coordinated",
        ],
        "answer_first_lead": "Want to defer capital gains on a Queens investment-property sale?",
        "answer_first_body": "IRS Section 1031 lets you roll proceeds from a sold investment property into a new \"like-kind\" property and defer 100% of the capital-gains tax. Strict timelines apply: 45 days to identify replacement property, 180 days to close. Requires a Qualified Intermediary (we coordinate). Common in Queens for 2-fam-to-2-fam swaps and Queens-to-Long-Island upgrades.",
        "steps": [
            ("Engage a Qualified Intermediary BEFORE closing", "QI must hold sale proceeds — you cannot touch the money or the exchange fails. Engage QI before sale closing. We refer to QIs we've worked with."),
            ("Close the relinquished (sold) property", "Sale proceeds wire directly to QI's escrow account. Day 0 of the 45-day clock starts at this closing."),
            ("Identify replacement property within 45 days", "Written identification to QI. Three options: 3-property rule (any 3 properties), 200% rule (any number, total FMV ≤200% of relinquished), 95% rule (must close 95% of identified)."),
            ("Negotiate + go under contract", "Replacement property must be 'like-kind' (any US investment real estate works — strict definition is loose for real estate). Cannot be primary residence."),
            ("Close within 180 days of relinquished sale", "Hard deadline. QI wires funds to closing. If you close 1 day late, the exchange fails and the entire gain becomes taxable."),
            ("File IRS Form 8824 with that year's tax return", "Reports the exchange. Don't miss this — preserves the deferral. CPA familiar with 1031 strongly recommended."),
        ],
        "cards": [
            ("'Like-kind' is broader than it sounds", "Any US investment real estate qualifies for any other US investment real estate. 2-fam in Queens → SFR in Long Island works. 2-fam → commercial works. Even 2-fam → vacant land works."),
            ("Boot is taxed", "If your replacement property is cheaper than the sold one, the difference (cash 'boot') is taxed at capital-gains rates. Plan to either roll into more expensive property or accept partial tax."),
            ("Reverse exchanges are possible but harder", "Buy first, sell later. Requires QI to hold replacement property for up to 180 days. More expensive QI fees. Used when the deal you want appears before yours sells."),
            ("Multi-asset 1031 can swap several properties", "Sell 3 small properties → buy 1 larger one (or vice versa). Aggregation rules apply. Useful for portfolio consolidation."),
            ("DST for passive 1031", "Delaware Statutory Trust shares qualify as 1031 replacement. Passive ownership of large commercial properties. 5–7% typical yield. Used by retiring landlords."),
            ("State taxes follow federal", "NY State recognizes 1031 deferral. NYC does too. But some states (CA notably) have their own rules — talk to CPA."),
        ],
        "faqs": [
            ("What qualifies as 'like-kind' for a 1031 exchange?", "Any US investment-grade real estate qualifies for any other US investment-grade real estate. Single-family, multi-family, commercial, retail, industrial, vacant land, leasehold interests — all interchangeable. Cannot be primary residence or fix-and-flip."),
            ("Can I 1031 a Queens 2-family into a Long Island single-family?", "Yes — both are investment real estate. As long as you don't owner-occupy the LI single-family, the exchange works."),
            ("How much does a Qualified Intermediary cost?", "$800–$1,500 for standard exchange; $2,500+ for reverse exchange. Coordinated with closing attorneys."),
            ("Can I 1031 multiple times?", "Yes — there's no limit. Investors do 'forever 1031' to defer indefinitely. Heirs receive stepped-up basis, eliminating the deferred gain entirely. This is one of the most powerful wealth-building tools in US real estate."),
            ("What if my replacement property is delayed past 180 days?", "Exchange fails. Full capital gains owed in the year of relinquished sale. Plan for 30+ day buffer; we identify backup properties at the 45-day mark just in case."),
        ],
        "related": [
            ("/1031-exchange-queens.html", "Original 1031 Queens page"),
            ("/multi-family-investment/", "Multi-family investment hub"),
            ("/sell.html", "Selling guide"),
            ("/closing-costs-nyc-guide.html", "NYC closing costs"),
            ("/glossary/", "NY real estate glossary"),
        ],
    },
    {
        "slug": "fha-loans-nyc",
        "topic": "FHA Loans in NYC + Long Island",
        "topic_lower": "FHA loans",
        "title": "FHA Loans NYC + Long Island | 3.5% Down, 580 Credit | Complete Guide",
        "meta_desc": "FHA loans in NYC + Long Island: 3.5% down at 580+ credit, condo/co-op FHA approval lookup, multi-family self-sufficiency, MIP rules. By Nitin Gadura, NYS Salesperson.",
        "h1": "FHA Loans in NYC + Long Island — 3.5% Down Path to Homeownership",
        "hero_lede": "Federally-insured mortgage with the lowest down-payment requirement and the most forgiving credit score. The right tool for first-time buyers who want to stop renting.",
        "hero_badges": [
            "3.5% down at 580+ credit",
            "Stacks with SONYMA $15K grant",
            "Multi-family + 1-4 unit owner-occupant",
        ],
        "answer_first_lead": "Want to buy in NYC or Long Island with FHA?",
        "answer_first_body": "FHA loans accept 580+ credit at 3.5% down (down to 500 with 10% down on some lenders). Stacks beautifully with SONYMA's $15K Down-Payment Assistance Loan. The catch in NYC: many co-ops and condos have FHA approval limits per building — you have to pre-qualify the building. We know which Queens, Brooklyn, and Long Island buildings accept FHA.",
        "steps": [
            ("Check your credit score", "AnnualCreditReport.com is free. FHA accepts 580+ for 3.5% down. Below 580, plan 4–6 months to bring it up before applying."),
            ("Get pre-approved with FHA-experienced lenders", "Not every lender does heavy FHA volume. Get quotes from at least 2 FHA-specialists. Compare rate + MIP + lender fees."),
            ("Stack SONYMA if eligible", "First-time buyer + income/price limits. SONYMA's $15K DPAL forgives over time. Reduces effective down payment."),
            ("Pre-qualify the building (condo/co-op)", "Check FHA Approved Condominium List. Co-ops require board approval AND FHA approval (rare in older NYC buildings)."),
            ("Tour FHA-eligible properties", "Single-family is always FHA-eligible. 2-fam, 3-fam, 4-fam owner-occupant works (with self-sufficiency rules). Co-ops: very restricted."),
            ("Get appraisal scheduled", "FHA appraisals are stricter than conventional — they assess habitability + safety. Some pre-1978 properties need lead-paint disclosures."),
            ("Close + start paying MIP", "FHA charges 1.75% upfront mortgage insurance + monthly MIP. MIP stays for life of loan if down payment <10%, drops at 11 years if down payment ≥10%."),
        ],
        "cards": [
            ("3.5% down is the headline", "$725K Queens median × 3.5% = $25,375 down. Plus closing costs (~$30K). SONYMA cuts effective down to ~$10K."),
            ("MIP for life of loan", "FHA's mortgage insurance does NOT drop off automatically — must refinance to remove. Plan for refi at 5+ years if rates allow."),
            ("Loan limits by county", "FHA loan limit Queens/Nassau 2026: ~$1,089,300 single-family. Multi-family ratchets up by unit count."),
            ("Property condition matters", "FHA requires property to meet HUD habitability standards. Major systems (roof, HVAC, plumbing) must be functional. Sellers often resist FHA over conventional for this reason."),
            ("Multi-family owner-occupant works", "1-4 unit FHA allowed for owner-occupants. Self-sufficiency rule: 75% of OTHER units' rent must cover full mortgage. Strong for Queens 2-fams."),
            ("FHA condo approval is building-specific", "Building must be on HUD's FHA Approved Condominium List. Many newer NYC buildings ARE approved; many older co-ops are NOT."),
        ],
        "faqs": [
            ("Can I buy a NYC condo with FHA?", "Yes — if the building is on HUD's FHA Approved Condominium List. Most newer (post-2010) NYC condos are approved. Most older co-ops are NOT. Pre-qualify the building before falling in love."),
            ("Will sellers accept my FHA offer?", "Sometimes. Some Queens sellers and listing agents have a stigma against FHA, fearing the appraisal will fail. We coach buyers on how to make their FHA offer competitive (escalation clauses, larger earnest money, faster timelines)."),
            ("How long does FHA underwriting take?", "30–45 days typical, slightly longer than conventional. Plan 60-day contract-to-close on FHA financing contingency."),
            ("Can I refinance out of FHA later?", "Yes — once you have 20% equity (via appreciation + paydown), refinance to conventional and drop the MIP entirely. Common play 3–7 years post-purchase in appreciating NYC markets."),
            ("FHA limits in Queens 2026?", "Single-family: $1,089,300. 2-fam: $1,394,775. 3-fam: $1,685,850. 4-fam: $2,095,200. Updated annually by HUD."),
        ],
        "related": [
            ("/buy.html", "Full buyer's guide"),
            ("/first-time-homebuyer/", "First-time buyer hub"),
            ("/multi-family-investment/", "Multi-family investment hub"),
            ("/co-op-board-help/", "Co-op board package hub"),
            ("/closing-costs-nyc-guide.html", "NYC closing costs"),
            ("/glossary/", "NY real estate glossary"),
        ],
    },
]


def render_hub(h: dict) -> str:
    steps_html = "\n".join(
        f'  <li><strong>{title}.</strong> {body}</li>' for title, body in h["steps"]
    )
    cards_html = "\n".join(
        f'  <div class="card"><h4>{title}</h4><p>{body}</p></div>'
        for title, body in h["cards"]
    )
    faq_html = "\n".join(
        f'  <div class="faq-item"><div class="q">{q}</div><p>{a}</p></div>'
        for q, a in h["faqs"]
    )
    related_links = "\n".join(
        f'  <li><a href="{href}">{label}</a></li>' for href, label in h["related"]
    )
    badges_html = "".join(f'<span class="badge">{b}</span>' for b in h["hero_badges"])

    # HowTo schema
    import json
    howto = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": h["topic"],
        "description": h["meta_desc"],
        "image": "https://gadurarealestate.com/images/nitin-gadura-headshot.jpg",
        "totalTime": "PT60M",
        "step": [
            {"@type": "HowToStep", "position": i + 1, "name": title, "text": body}
            for i, (title, body) in enumerate(h["steps"])
        ],
        "author": {
            "@type": "Person",
            "name": "Nitin Gadura",
            "url": "https://gadurarealestate.com/author/nitin-gadura.html",
        },
    }
    faq_jsonld_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in h["faqs"]
        ],
    }

    return HUB_TEMPLATE.format(
        title=h["title"],
        meta_desc=h["meta_desc"],
        slug=h["slug"],
        topic=h["topic"],
        topic_lower=h["topic_lower"],
        h1=h["h1"],
        hero_lede=h["hero_lede"],
        hero_badges=badges_html,
        answer_first_lead=h["answer_first_lead"],
        answer_first_body=h["answer_first_body"],
        steps_html=steps_html,
        cards_html=cards_html,
        faq_html=faq_html,
        related_links=related_links,
        howto_jsonld=json.dumps(howto, indent=2, ensure_ascii=False),
        faq_jsonld=json.dumps(faq_jsonld_data, indent=2, ensure_ascii=False),
    )


def main() -> int:
    for h in HUBS:
        out_dir = ROOT / h["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"
        out_path.write_text(render_hub(h), encoding="utf-8")
        print(f"  wrote {out_path.relative_to(ROOT)}")
    print(f"\nDone. {len(HUBS)} topical hubs generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
