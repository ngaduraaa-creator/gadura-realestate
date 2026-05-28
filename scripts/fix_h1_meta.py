#!/usr/bin/env python3
"""Add missing H1 tags and meta descriptions.

- 93 pages missing H1 (mostly property listing pages)
- 27 pages missing meta descriptions
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract_title(content):
    m = re.search(r'<title[^>]*>(.*?)</title>', content, re.I | re.S)
    return m.group(1).strip() if m else ''


def extract_h1(content):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.I | re.S)
    return m.group(1).strip() if m else ''


def has_meta_desc(content):
    return bool(re.search(r'name=["\']description["\']', content, re.I))


def has_h1(content):
    return bool(re.search(r'<h1', content, re.I))


def title_to_description(title, filepath):
    """Generate a meta description from the title and filepath."""
    rel = os.path.relpath(filepath, SITE_ROOT)

    # Property pages
    if rel.startswith('homes/'):
        addr = title.split('|')[0].strip() if '|' in title else title
        return f"View property details for {addr}. Contact Nitin Gadura at Gadura Real Estate for a showing. Call 917-705-0132."

    # v2 pages (old version)
    if rel.startswith('v2/'):
        return f"Gadura Real Estate LLC — {title.split('|')[0].strip()}. Queens and Long Island real estate services."

    # Neighborhood pages
    if 'neighborhood' in rel:
        return f"{title.split('|')[0].strip()} — homes for sale, market data, and community info from Gadura Real Estate."

    # Home value pages
    if 'home-value' in rel:
        return f"{title.split('|')[0].strip()} — free tools from Gadura Real Estate. Call 917-705-0132."

    # Default
    clean = title.split('|')[0].strip()
    return f"{clean} — Gadura Real Estate LLC, serving Queens and Long Island NY. Call 917-705-0132."


def fix_file(filepath):
    """Add missing H1 and/or meta description. Returns count of fixes."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if '</head>' not in content:
        return 0

    original = content
    fixes = 0
    title = extract_title(content)

    # Skip pages that shouldn't be indexed
    if re.search(r'noindex', content, re.I):
        return 0

    # Add meta description if missing
    if not has_meta_desc(content) and title:
        desc = title_to_description(title, filepath)
        # Truncate to 160 chars
        if len(desc) > 160:
            desc = desc[:157] + '...'
        desc_tag = f'  <meta name="description" content="{desc}">\n'
        # Insert after <title> tag
        content = re.sub(
            r'(</title>)',
            r'\1\n' + desc_tag,
            content,
            count=1
        )
        fixes += 1

    # Add H1 if missing
    if not has_h1(content) and title:
        h1_text = title.split('|')[0].strip()
        # Find <main> or first <section> or <body> to insert H1
        if '<main' in content:
            content = re.sub(
                r'(<main[^>]*>)',
                r'\1\n  <h1 style="font-size:1.8rem;color:#0b2545;margin:1rem 0;">' + h1_text + '</h1>',
                content,
                count=1
            )
            fixes += 1
        elif '<section' in content:
            content = re.sub(
                r'(<section[^>]*>)',
                r'\1\n  <h1 style="font-size:1.8rem;color:#0b2545;margin:1rem 0;">' + h1_text + '</h1>',
                content,
                count=1
            )
            fixes += 1
        elif '<body' in content:
            content = re.sub(
                r'(<body[^>]*>)',
                r'\1\n  <h1 style="font-size:1.8rem;color:#0b2545;margin:1rem 0;">' + h1_text + '</h1>',
                content,
                count=1
            )
            fixes += 1

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
            print(f"  +{fixes} fixes in {rel}")
            total_files += 1
            total_fixes += fixes

    print(f"\n=== H1 + META DESCRIPTION FIX COMPLETE ===")
    print(f"Files updated: {total_files}")
    print(f"Total fixes: {total_fixes}")


if __name__ == '__main__':
    main()
