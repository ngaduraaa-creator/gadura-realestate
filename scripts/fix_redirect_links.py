#!/usr/bin/env python3
"""Fix internal links that point to redirect URLs.

The audit found 600 pages with links pointing to URLs that redirect.
This script updates links to point directly to the final destination,
eliminating redirect chains.
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Known redirect mappings: old URL → new URL
REDIRECT_MAP = {
    # Meta refresh redirects (now also server-side 301s)
    '/privacy.html': '/privacy-policy.html',
    '/neighborhoods/ozone-park-homes.html': '/neighborhoods/ozone-park.html',
    '/neighborhoods/brooklyn/': '/neighborhoods/brooklyn.html',
    '/neighborhoods/brooklyn/index.html': '/neighborhoods/brooklyn.html',
    '/home-value/free-cma-queens.html': '/home-value/',
    '/home-value/sell-or-rent-calculator.html': '/home-value/',
    '/home-value/home-equity-calculator.html': '/home-value/',
    '/homes-for-sale/queens-townhouses-for-sale.html': '/for-sale/',
    '/portfolio/': '/about-us/',
    '/portfolio/index.html': '/about-us/',

    # v2 redirects
    '/v2/sell.html': '/sell.html',
    '/v2/about.html': '/about.html',
    '/v2/buy.html': '/buy.html',
    '/v2/neighborhoods/': '/neighborhoods/',
    '/v2/neighborhoods/index.html': '/neighborhoods/',
    '/v2/neighborhoods/astoria.html': '/neighborhoods/astoria.html',
    '/v2/neighborhoods/bayside.html': '/neighborhoods/bayside.html',
    '/v2/neighborhoods/howard-beach.html': '/neighborhoods/howard-beach.html',
    '/v2/neighborhoods/jamaica-estates.html': '/neighborhoods/jamaica-estates.html',
    '/v2/neighborhoods/jamaica.html': '/neighborhoods/jamaica.html',
    '/v2/neighborhoods/kew-gardens.html': '/neighborhoods/kew-gardens.html',
    '/v2/neighborhoods/richmond-hill.html': '/neighborhoods/richmond-hill.html',
    '/v2/neighborhoods/south-ozone-park.html': '/neighborhoods/south-ozone-park.html',
    '/v2/neighborhoods/woodhaven.html': '/neighborhoods/woodhaven.html',

    # Netlify _redirects rules
    '/agents/index.html': '/meet-the-agents.html',
    '/about/index.html': '/about.html',
    '/contact/index.html': '/contact.html',
    '/buy/index.html': '/buy.html',
    '/sell/index.html': '/sell.html',
    '/index.html': '/',

    # Common typo redirects
    '/queens/': '/neighborhoods/queens.html',
    '/brooklyn/': '/neighborhoods/brooklyn.html',
    '/bronx/': '/neighborhoods/bronx.html',
    '/manhattan/': '/neighborhoods/manhattan.html',
    '/staten-island/': '/neighborhoods/staten-island.html',
}


def fix_file(filepath):
    """Update links pointing to redirect URLs."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    fixes = 0

    for old_url, new_url in REDIRECT_MAP.items():
        # Fix href attributes
        old_pattern = f'href="{old_url}"'
        new_pattern = f'href="{new_url}"'
        if old_pattern in content:
            count = content.count(old_pattern)
            content = content.replace(old_pattern, new_pattern)
            fixes += count

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return fixes


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    total_files = 0
    total_fixes = 0

    for filepath in html_files:
        fixes = fix_file(filepath)
        if fixes > 0:
            rel = os.path.relpath(filepath, SITE_ROOT)
            total_files += 1
            total_fixes += fixes

    print(f"\n=== REDIRECT LINK FIX COMPLETE ===")
    print(f"Files updated: {total_files}")
    print(f"Links updated: {total_fixes}")


if __name__ == '__main__':
    main()
