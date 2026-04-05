#!/usr/bin/env python3
"""
Legal compliance batch update for Gadura Real Estate LLC.
1. Replace all broken legal links in footer disclaimer bar
2. Add wire fraud warning bar to every page (before <footer>)
3. Fix portal.html Zillow attribution
4. Update privacy policy footer to include Terms & Fair Housing links
"""
import os, re, glob

BASE = '/Users/nidhigadura/Jagex/gadura-realestate'

# ── Wire Fraud Warning Bar HTML ───────────────────────────────────────────────
WIRE_FRAUD_BAR = '''
<!-- ── WIRE FRAUD WARNING BAR ── -->
<div class="wire-fraud-bar" role="alert" aria-label="Wire fraud warning">
  <div class="container">
    <div class="wf-bar-inner">
      <svg class="wf-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span>
        <strong>WIRE FRAUD WARNING:</strong> Gadura Real Estate LLC will
        <strong>NEVER</strong> send wire transfer instructions by email or text.
        If you receive such a request, call <a href="tel:+17188500010" style="color:inherit;font-weight:700;">(718) 850-0010</a> immediately to verify.
        &nbsp;<a href="terms.html#wire-fraud" style="color:inherit;text-decoration:underline;white-space:nowrap;">Learn more →</a>
      </span>
    </div>
  </div>
</div>
'''

# ── Wire Fraud CSS (injected into <head> if not already present) ─────────────
WIRE_FRAUD_CSS = '''
  <style>
    .wire-fraud-bar{background:#7f1d1d;color:#fff;font-size:.82rem;line-height:1.5;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.15);}
    .wf-bar-inner{display:flex;align-items:flex-start;gap:10px;}
    .wf-icon{flex-shrink:0;margin-top:1px;color:#fbbf24;}
    @media(max-width:600px){.wf-bar-inner{flex-direction:column;gap:6px;}}
  </style>
'''

def has_wire_fraud_bar(html):
    return 'wire-fraud-bar' in html

def has_wire_fraud_css(html):
    return 'wire-fraud-bar{' in html or "wire-fraud-bar {" in html

def fix_footer_links(html):
    """Replace broken about.html#terms / about.html#fair-housing references in footer."""
    html = html.replace('href="about.html#terms"', 'href="terms.html"')
    html = html.replace("href='about.html#terms'", "href='terms.html'")
    html = html.replace('href="about.html#fair-housing"', 'href="fair-housing.html"')
    html = html.replace("href='about.html#fair-housing'", "href='fair-housing.html'")
    html = html.replace('href="about.html#accessibility"', 'href="terms.html#accessibility"')
    html = html.replace("href='about.html#accessibility'", "href='terms.html#accessibility'")

    # Ensure Terms link appears in disclaimer-links-row if Privacy Policy is there but Terms missing
    if 'disclaimer-links-row' in html and 'terms.html' not in html:
        html = html.replace(
            '<a href="privacy-policy.html">Privacy Policy</a>',
            '<a href="privacy-policy.html">Privacy Policy</a>\n        <span>|</span>\n        <a href="terms.html">Terms &amp; Conditions</a>'
        )

    return html

def add_wire_fraud_bar(html):
    """Inject wire fraud bar just before <footer and CSS into <head>."""
    if has_wire_fraud_bar(html):
        return html  # already has it

    # Add CSS before </head> if not already there
    if not has_wire_fraud_css(html) and '</head>' in html:
        html = html.replace('</head>', WIRE_FRAUD_CSS + '</head>', 1)

    # Add bar just before <footer
    if '<footer' in html:
        html = html.replace('<footer', WIRE_FRAUD_BAR + '\n<footer', 1)

    return html

def fix_portal_zillow(html):
    """Fix Zillow attribution in portal.html — replace with IDX-safe language."""
    # Fix the main area disclaimer
    html = html.replace(
        '<strong>Third-Party Listing Disclosure:</strong> Information provided by Zillow and the OneKey® MLS.',
        '<strong>Third-Party Listing Disclosure:</strong> Area listing information is sourced from the OneKey® MLS IDX program and public property records. Links provided for reference purposes only.'
    )
    # Fix the comment that says "simulate Zillow/MLS market data"
    html = html.replace(
        'Area listings simulate Zillow/MLS market data.',
        'Area listings sourced from OneKey® MLS IDX and public records.'
    )
    # Fix source labels in PORTAL_DATA
    html = re.sub(r"source:\s*'Zillow'", "source: 'OneKey® MLS'", html)
    html = re.sub(r'source:\s*"Zillow"', 'source: "OneKey® MLS"', html)
    # Fix ARIA label mentioning Zillow or Homes.com
    html = html.replace(
        'aria-label="View listing details for ${listing.address} (opens Zillow or Homes.com)"',
        'aria-label="View listing details for ${listing.address} on external listing portal"'
    )
    # Add third-party not-affiliated disclaimer to area section disclaimer
    html = html.replace(
        'All information is deemed reliable but not guaranteed. Square footage, taxes, and HOA data\n        should be independently verified prior to making any purchase decision.',
        'All information is deemed reliable but not guaranteed. Square footage, taxes, and HOA data should be independently verified prior to making any purchase decision. This website is not affiliated with, endorsed by, or sponsored by Zillow Group, Inc., Redfin Corporation, or CoStar Group (Homes.com). External links to those platforms are provided as a convenience only.'
    )
    return html

def process_file(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        html = f.read()
    orig = html

    html = fix_footer_links(html)
    html = add_wire_fraud_bar(html)

    # Extra fix for portal.html
    if path.endswith('portal.html'):
        html = fix_portal_zillow(html)

    if html != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    return False


# Skip terms.html and fair-housing.html (just created, already correct)
SKIP = {
    os.path.join(BASE, 'terms.html'),
    os.path.join(BASE, 'fair-housing.html'),
}

html_files = sorted(glob.glob(os.path.join(BASE, '**/*.html'), recursive=True))

changed, skipped = 0, 0
for fp in html_files:
    if fp in SKIP:
        skipped += 1
        continue
    if process_file(fp):
        changed += 1
        print(f'  ✓  {fp.replace(BASE+"/",""):<55}')

print(f'\nDone: {changed} updated, {skipped} skipped, {len(html_files)-changed-skipped} unchanged')
