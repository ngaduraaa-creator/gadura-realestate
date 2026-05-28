#!/usr/bin/env python3
"""Rebuild sitemap.xml to fix:
- 267 indexable pages not in sitemap
- 18 non-canonical pages in sitemap
- 8 noindex pages in sitemap

Strategy: Scan all HTML files, check if indexable (no noindex, has canonical),
and build a clean sitemap.xml.
"""
import os
import re
import glob
from datetime import date

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = 'https://gadurarealestate.com'
TODAY = date.today().isoformat()

# Directories/files to exclude from sitemap
EXCLUDE_PATTERNS = [
    '/.git/', '/v2/', '/_includes/', '/admin/', '/scripts/',
    '/docs/', '/research/', '/.claude/', '/.netlify/',
    '/.well-known/', '/well-known/',
]

EXCLUDE_FILES = [
    '404.html', 'indexnow-submit.html',
]


def is_indexable(filepath, content):
    """Check if a page should be in the sitemap."""
    rel = os.path.relpath(filepath, SITE_ROOT)

    # Skip excluded paths
    for pattern in EXCLUDE_PATTERNS:
        if pattern in '/' + rel:
            return False

    # Skip excluded files
    basename = os.path.basename(rel)
    if basename in EXCLUDE_FILES:
        return False

    # Skip noindex pages
    if re.search(r'<meta\s+name=["\']robots["\']\s+content="[^"]*noindex', content, re.I):
        return False
    if re.search(r'content="[^"]*noindex[^"]*"\s+name=["\']robots["\']', content, re.I):
        return False

    # Must be a proper HTML page
    if '</head>' not in content:
        return False

    return True


def get_canonical(filepath, content):
    """Get canonical URL for a page."""
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', content, re.I)
    if m:
        return m.group(1)

    # Build from filepath
    rel = os.path.relpath(filepath, SITE_ROOT)
    if rel.endswith('/index.html'):
        rel = rel[:-len('index.html')]
    return f'{DOMAIN}/{rel}'


def get_priority(rel_path):
    """Assign priority based on page type."""
    if rel_path in ('index.html', ''):
        return '1.0'
    if rel_path in ('buy.html', 'sell.html', 'contact.html', 'about.html'):
        return '0.9'
    if rel_path.startswith('neighborhoods/') and '/' not in rel_path[len('neighborhoods/'):]:
        return '0.8'
    if rel_path.startswith('homes-for-sale/'):
        return '0.8'
    if rel_path.startswith('neighborhoods/'):
        return '0.7'
    if rel_path.startswith('long-island/'):
        return '0.7'
    if rel_path.startswith('market-reports/'):
        return '0.7'
    if rel_path.startswith('blog/'):
        return '0.6'
    if rel_path.startswith('community/'):
        return '0.7'
    if rel_path.startswith('services/'):
        return '0.7'
    if rel_path.startswith('homes/'):
        return '0.5'
    return '0.6'


def get_changefreq(rel_path):
    if rel_path.startswith('homes/'):
        return 'weekly'
    if rel_path.startswith('market-reports/'):
        return 'monthly'
    if rel_path.startswith('blog/'):
        return 'monthly'
    if rel_path.startswith('neighborhoods/'):
        return 'weekly'
    return 'weekly'


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    urls = []
    seen_canonicals = set()

    for filepath in sorted(html_files):
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        if not is_indexable(filepath, content):
            continue

        canonical = get_canonical(filepath, content)

        # Skip duplicate canonicals
        if canonical in seen_canonicals:
            continue
        seen_canonicals.add(canonical)

        rel = os.path.relpath(filepath, SITE_ROOT)
        priority = get_priority(rel)
        changefreq = get_changefreq(rel)

        urls.append((canonical, priority, changefreq))

    # Sort: higher priority first, then alphabetically
    urls.sort(key=lambda x: (-float(x[1]), x[0]))

    # Build sitemap XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url, priority, changefreq in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url}</loc>')
        xml_lines.append(f'    <lastmod>{TODAY}</lastmod>')
        xml_lines.append(f'    <changefreq>{changefreq}</changefreq>')
        xml_lines.append(f'    <priority>{priority}</priority>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')

    sitemap_path = os.path.join(SITE_ROOT, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines) + '\n')

    print(f"=== SITEMAP REBUILT ===")
    print(f"Total URLs: {len(urls)}")
    print(f"Written to: sitemap.xml")


if __name__ == '__main__':
    main()
