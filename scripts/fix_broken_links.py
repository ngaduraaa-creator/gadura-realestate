#!/usr/bin/env python3
"""Fix broken internal links across the entire site.

Broken patterns found:
1. /neighborhoods/nassau/[town].html  → should be /long-island/nassau/[town].html
2. /neighborhoods/suffolk/[town].html → should be /long-island/suffolk/[town].html

These broken links appear in:
- /long-island/nassau/index.html (68 broken links)
- /long-island/suffolk/index.html (70 broken links)
- 14 market report pages
- Any other pages linking to these paths
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Link replacements: old prefix → new prefix
LINK_FIXES = {
    '/neighborhoods/nassau/': '/long-island/nassau/',
    '/neighborhoods/suffolk/': '/long-island/suffolk/',
}

def fix_file(filepath):
    """Fix broken links in a single HTML file. Returns count of fixes."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    total_fixes = 0

    for old_prefix, new_prefix in LINK_FIXES.items():
        # Fix href attributes
        pattern = re.compile(r'href="' + re.escape(old_prefix))
        matches = pattern.findall(content)
        if matches:
            content = pattern.sub('href="' + new_prefix, content)
            total_fixes += len(matches)

        # Fix canonical URLs
        pattern2 = re.compile(r'content="https://gadurarealestate\.com' + re.escape(old_prefix))
        matches2 = pattern2.findall(content)
        if matches2:
            content = pattern2.sub('content="https://gadurarealestate.com' + new_prefix, content)
            total_fixes += len(matches2)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return total_fixes


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    total_files_fixed = 0
    total_links_fixed = 0

    for filepath in html_files:
        fixes = fix_file(filepath)
        if fixes > 0:
            rel = os.path.relpath(filepath, SITE_ROOT)
            print(f"  Fixed {fixes} links in {rel}")
            total_files_fixed += 1
            total_links_fixed += fixes

    print(f"\n=== BROKEN LINKS FIX COMPLETE ===")
    print(f"Files fixed: {total_files_fixed}")
    print(f"Links fixed: {total_links_fixed}")


if __name__ == '__main__':
    main()
