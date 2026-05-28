#!/usr/bin/env python3
"""Add missing alt text to images across all pages.

The audit found 531 images missing alt attributes.
Strategy: For each <img> without alt, generate alt text from:
1. The filename (e.g., nitin-gadura.jpg → "Nitin Gadura")
2. The surrounding context (parent section, heading)
3. A sensible default
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Known image filenames → good alt text
KNOWN_ALTS = {
    'nitin-gadura': 'Nitin Gadura, Licensed Real Estate Agent',
    'gadura-real-estate': 'Gadura Real Estate LLC Logo',
    'gadura-realestate': 'Gadura Real Estate LLC Logo',
    'og-default': 'Gadura Real Estate - Queens and Long Island NY',
    'headshot': 'Gadura Real Estate Agent Headshot',
    'hero': 'Queens and Long Island Real Estate',
    'logo': 'Gadura Real Estate Logo',
    'favicon': 'Gadura Real Estate',
    'fair-housing': 'Equal Housing Opportunity Logo',
    'equal-housing': 'Equal Housing Opportunity Logo',
    'mls': 'Multiple Listing Service Logo',
    'realtor': 'Realtor Association Logo',
    'idx': 'IDX Broker Powered Listings',
}


def filename_to_alt(src):
    """Generate alt text from image filename."""
    if not src:
        return 'Gadura Real Estate'

    # Extract filename without extension
    basename = os.path.splitext(os.path.basename(src))[0]

    # Check known filenames
    for key, alt in KNOWN_ALTS.items():
        if key in basename.lower():
            return alt

    # Convert filename to readable text
    alt = basename.replace('-', ' ').replace('_', ' ').title()

    # Clean up common patterns
    alt = re.sub(r'\d{3,}', '', alt).strip()  # Remove long numbers
    if not alt or len(alt) < 3:
        return 'Gadura Real Estate property image'

    return alt


def fix_file(filepath):
    """Add alt text to images missing it. Returns count of fixes."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    fixes = 0

    # Pattern: <img ... > without alt attribute
    # Match img tags that don't have alt=
    def add_alt(match):
        nonlocal fixes
        tag = match.group(0)

        # Already has alt attribute
        if re.search(r'\balt\s*=', tag, re.I):
            return tag

        # Extract src for context
        src_match = re.search(r'src\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        src = src_match.group(1) if src_match else ''

        alt = filename_to_alt(src)
        fixes += 1

        # Insert alt before the closing >
        if tag.endswith('/>'):
            return tag[:-2] + f' alt="{alt}" />'
        elif tag.endswith('>'):
            return tag[:-1] + f' alt="{alt}">'
        return tag

    content = re.sub(r'<img\b[^>]*>', add_alt, content, flags=re.I)

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

    print(f"\n=== ALT TEXT FIX COMPLETE ===")
    print(f"Files updated: {total_files}")
    print(f"Images fixed: {total_fixes}")


if __name__ == '__main__':
    main()
