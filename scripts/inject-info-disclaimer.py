#!/usr/bin/env python3
"""Inject a 'not legal/tax/financial advice' informational disclaimer into
tax/finance educational content pages (glossary + tax/finance blog posts).

These pages publish specific tax rates, loan limits, and program dollar
amounts. A brokerage is not a law/tax/lending firm, so this reduces liability
and is standard practice. Idempotent via marker. Placed just before the legal
footer (or before </body> if the footer marker is absent).
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MARKER = "GRE_INFO_DISCLAIMER"

DISCLAIMER = f"""<!-- {MARKER}_START -->
<aside class="gre-info-disclaimer" role="note" aria-label="Informational disclaimer" style="max-width:820px;margin:2rem auto;padding:1rem 1.25rem;background:#fbfaf5;border:1px solid #e8dfc2;border-radius:8px;font-size:0.85rem;line-height:1.6;color:#555;font-style:italic;">
<strong>Informational only &mdash; not legal, tax, or financial advice.</strong> This page explains general New York real estate concepts. Tax rates, loan limits, program terms, and eligibility change over time and vary by individual situation. Verify current details and obtain advice for your specific circumstances from a licensed attorney, CPA or tax advisor, or mortgage lender before acting. Gadura Real Estate, LLC is a licensed New York real estate broker &mdash; not a law, tax, or lending firm.
</aside>
<!-- {MARKER}_END -->
"""

# Blog slugs that publish tax/finance/legal specifics.
FIN_KEYWORDS = re.compile(
    r"(tax|mortgage|mansion|transfer|star|flip|closing-cost|1031|capital-gain|"
    r"down-payment|down_payment|sonyma|fha|homefirst|abatement|421-a|421a|j-51|"
    r"j51|assistance|exemption|grievance|escrow|refinanc|cema|lien)",
    re.I,
)

targets = []
# all glossary term pages
gdir = os.path.join(ROOT, "glossary")
if os.path.isdir(gdir):
    for f in os.listdir(gdir):
        if f.endswith(".html") and f != "index.html":
            targets.append(os.path.join(gdir, f))
# tax/finance blog posts
bdir = os.path.join(ROOT, "blog")
if os.path.isdir(bdir):
    for f in os.listdir(bdir):
        if f.endswith(".html") and FIN_KEYWORDS.search(f):
            targets.append(os.path.join(bdir, f))

updated = skipped = 0
for path in sorted(set(targets)):
    s = open(path, encoding="utf-8").read()
    if MARKER in s or "</body>" not in s:
        skipped += 1
        continue
    if "GRE_LEGAL_FOOTER_START" in s:
        s = s.replace("<!-- GRE_LEGAL_FOOTER_START -->",
                      DISCLAIMER + "<!-- GRE_LEGAL_FOOTER_START -->", 1)
    else:
        s = s.replace("</body>", DISCLAIMER + "</body>", 1)
    open(path, "w", encoding="utf-8").write(s)
    updated += 1
    print(f"UPDATED {os.path.relpath(path, ROOT)}")

print(f"\nDone. Injected disclaimer into {updated} pages, skipped {skipped}.")
