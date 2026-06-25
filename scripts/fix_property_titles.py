#!/usr/bin/env python3
"""
fix_property_titles.py — Rewrites <title> and og:title on all 91 property pages
so Google shows the full address as the clickable link.

Before: 101-16 95th Street | Gadura Real Estate
After:  101-16 95th Street, Ozone Park, NY 11416

Extracts the address from each page's JSON-LD PostalAddress block,
which is the authoritative source (not the filename).

Run from repo root:
  python3 scripts/fix_property_titles.py
"""
import os, re, json, sys

REPO      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOMES_DIR = os.path.join(REPO, 'homes')


def extract_address(html: str):
    """Pull PostalAddress out of JSON-LD embedded in the page."""
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(block)
        except Exception:
            continue
        # handle both plain object and @graph array
        nodes = data.get('@graph', [data]) if isinstance(data, dict) else []
        if isinstance(data, list):
            nodes = data
        for node in nodes:
            if isinstance(node, dict):
                addr = node.get('address') or node.get('location')
                if isinstance(addr, dict) and addr.get('streetAddress'):
                    return addr
    return None


def build_title(addr: dict) -> str:
    """Build 'Street, City, NY ZIP' from a PostalAddress dict."""
    street  = (addr.get('streetAddress') or '').strip()
    city    = (addr.get('addressLocality') or '').strip()
    state   = (addr.get('addressRegion') or 'NY').strip()
    zipcode = (addr.get('postalCode') or '').strip()

    title = street
    if city:
        title += ', ' + city
    if state:
        title += ', ' + state
    if zipcode:
        title += ' ' + zipcode
    return title


def fix_page(path: str) -> tuple[bool, str]:
    """Rewrite title + og:title in one page. Returns (changed, message)."""
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    addr = extract_address(html)
    if not addr:
        return False, 'no JSON-LD address found'

    new_title = build_title(addr)
    if not new_title or new_title == ', NY ':
        return False, f'address came back empty: {addr}'

    og_title = new_title + ' — For Sale | Gadura Real Estate'

    # Replace <title>...</title>
    new_html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{new_title}</title>',
        html,
        count=1,
    )

    # Replace og:title content="..."
    new_html = re.sub(
        r'(<meta\s+property=["\']og:title["\'][^>]+content=["\'])[^"\']*(["\'])',
        lambda m: m.group(1) + og_title + m.group(2),
        new_html,
        count=1,
    )
    # Also handle reversed attribute order: content="..." property="og:title"
    new_html = re.sub(
        r'(<meta\s+content=["\'])[^"\']*(["\'][^>]+property=["\']og:title["\'])',
        lambda m: m.group(1) + og_title + m.group(2),
        new_html,
        count=1,
    )

    # Replace H1 — must match title exactly so Google doesn't rewrite it
    new_html = re.sub(
        r'(<h1[^>]*>)[^<]*(</h1>)',
        lambda m: m.group(1) + new_title + m.group(2),
        new_html,
        count=1,
    )

    if new_html == html:
        return False, f'no title tag found to replace ({new_title})'

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    return True, new_title


def main():
    if not os.path.isdir(HOMES_DIR):
        print(f'ERROR: homes/ directory not found at {HOMES_DIR}')
        sys.exit(1)

    slugs = [d for d in os.listdir(HOMES_DIR)
             if os.path.isdir(os.path.join(HOMES_DIR, d))]
    slugs.sort()

    updated = 0
    skipped = 0
    errors  = []

    print(f'Processing {len(slugs)} property pages...\n')

    for slug in slugs:
        page = os.path.join(HOMES_DIR, slug, 'index.html')
        if not os.path.exists(page):
            print(f'  SKIP  {slug}/ — no index.html')
            skipped += 1
            continue

        changed, info = fix_page(page)
        if changed:
            print(f'  OK    {slug}/')
            print(f'        → {info}')
            updated += 1
        else:
            print(f'  SKIP  {slug}/ — {info}')
            if 'not found' in info or 'came back' in info:
                errors.append(slug)
            skipped += 1

    print(f'\n{"─"*60}')
    print(f'Updated : {updated}')
    print(f'Skipped : {skipped}')
    if errors:
        print(f'Errors  : {len(errors)} pages — check manually:')
        for e in errors:
            print(f'  homes/{e}/')


if __name__ == '__main__':
    main()
