#!/usr/bin/env python3
"""Add missing OG tags, Twitter cards, and fix meta descriptions.

Fixes:
- 232 pages missing Open Graph tags
- 287 pages missing Twitter/X cards
- 34 pages with incomplete OG tags
- 1 page with OG URL not matching canonical

Strategy: Parse each HTML file, extract existing title/description/canonical,
and inject missing social tags before </head>.
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = 'https://gadurarealestate.com'
DEFAULT_IMAGE = f'{DOMAIN}/images/og-default.jpg'


def extract_tag(content, pattern):
    """Extract a meta tag value using regex."""
    m = re.search(pattern, content, re.IGNORECASE)
    return m.group(1).strip() if m else None


def get_page_info(content, filepath):
    """Extract title, description, canonical URL from page."""
    title = extract_tag(content, r'<title[^>]*>(.*?)</title>')
    description = extract_tag(content, r'<meta\s+name="description"\s+content="([^"]*)"')
    if not description:
        description = extract_tag(content, r'<meta\s+content="([^"]*)"\s+name="description"')
    canonical = extract_tag(content, r'<link\s+rel="canonical"\s+href="([^"]*)"')
    if not canonical:
        # Build from filepath
        rel = os.path.relpath(filepath, SITE_ROOT)
        canonical = f'{DOMAIN}/{rel}'

    og_title = extract_tag(content, r'<meta\s+property="og:title"\s+content="([^"]*)"')
    og_desc = extract_tag(content, r'<meta\s+property="og:description"\s+content="([^"]*)"')
    og_url = extract_tag(content, r'<meta\s+property="og:url"\s+content="([^"]*)"')
    og_image = extract_tag(content, r'<meta\s+property="og:image"\s+content="([^"]*)"')
    og_type = extract_tag(content, r'<meta\s+property="og:type"\s+content="([^"]*)"')

    tw_card = extract_tag(content, r'<meta\s+name="twitter:card"\s+content="([^"]*)"')
    tw_title = extract_tag(content, r'<meta\s+name="twitter:title"\s+content="([^"]*)"')
    tw_desc = extract_tag(content, r'<meta\s+name="twitter:description"\s+content="([^"]*)"')
    tw_image = extract_tag(content, r'<meta\s+name="twitter:image"\s+content="([^"]*)"')

    return {
        'title': title or '',
        'description': description or '',
        'canonical': canonical,
        'og_title': og_title,
        'og_desc': og_desc,
        'og_url': og_url,
        'og_image': og_image,
        'og_type': og_type,
        'tw_card': tw_card,
        'tw_title': tw_title,
        'tw_desc': tw_desc,
        'tw_image': tw_image,
    }


def build_missing_tags(info):
    """Build HTML for missing OG and Twitter tags."""
    lines = []
    title = info['title']
    desc = info['description']
    url = info['canonical']

    # OG tags
    if not info['og_title']:
        lines.append(f'  <meta property="og:title" content="{_escape(title)}" />')
    if not info['og_desc'] and desc:
        lines.append(f'  <meta property="og:description" content="{_escape(desc)}" />')
    if not info['og_url']:
        lines.append(f'  <meta property="og:url" content="{_escape(url)}" />')
    if not info['og_image']:
        lines.append(f'  <meta property="og:image" content="{DEFAULT_IMAGE}" />')
    if not info['og_type']:
        lines.append(f'  <meta property="og:type" content="website" />')

    # Twitter card tags
    if not info['tw_card']:
        lines.append(f'  <meta name="twitter:card" content="summary_large_image" />')
    if not info['tw_title']:
        lines.append(f'  <meta name="twitter:title" content="{_escape(title)}" />')
    if not info['tw_desc'] and desc:
        lines.append(f'  <meta name="twitter:description" content="{_escape(desc)}" />')
    if not info['tw_image']:
        lines.append(f'  <meta name="twitter:image" content="{DEFAULT_IMAGE}" />')

    return '\n'.join(lines)


def _escape(s):
    """Escape double quotes for HTML attributes."""
    return (s or '').replace('"', '&quot;').replace('&', '&amp;') if s else ''


def fix_og_url_mismatch(content, info):
    """Fix OG URL that doesn't match canonical."""
    if info['og_url'] and info['canonical'] and info['og_url'] != info['canonical']:
        content = content.replace(
            f'content="{info["og_url"]}"',
            f'content="{info["canonical"]}"',
            1  # Only replace the first occurrence (the og:url one)
        )
    return content


def fix_file(filepath):
    """Add missing social tags to a file. Returns count of tags added."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if '</head>' not in content:
        return 0  # Not a proper HTML file

    original = content
    info = get_page_info(content, filepath)

    # Fix OG URL mismatch
    content = fix_og_url_mismatch(content, info)

    # Build missing tags
    new_tags = build_missing_tags(info)
    if new_tags:
        content = content.replace('</head>', new_tags + '\n</head>', 1)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return new_tags.count('\n') + (1 if new_tags else 0)

    return 0


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    total_files = 0
    total_tags = 0

    for filepath in html_files:
        tags = fix_file(filepath)
        if tags > 0:
            rel = os.path.relpath(filepath, SITE_ROOT)
            print(f"  +{tags} tags in {rel}")
            total_files += 1
            total_tags += tags

    print(f"\n=== SOCIAL TAGS FIX COMPLETE ===")
    print(f"Files updated: {total_files}")
    print(f"Total tags added: {total_tags}")


if __name__ == '__main__':
    main()
