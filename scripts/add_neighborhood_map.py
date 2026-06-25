#!/usr/bin/env python3
"""
add_neighborhood_map.py
Injects a styled "Explore {Neighborhood}" Google-Maps location map into each
neighborhood page that has the consistent #idx-listings-section anchor. The map
appears directly above the live MLS listings embed, giving visitors geographic
context (the map the owner asked for); the existing IDX iframe below it is the
real-photo listings browser. Idempotent — skips pages already done.

Run from repo root:
  python3 scripts/add_neighborhood_map.py
"""
import os, re, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHOR = '<!-- ═══════════════════════════════════════════════════════════════\n       LIVE MLS LISTINGS'
MARK = 'gre-nbhd-map-section'


def nbhd_name(path, page):
    """Prefer the page's own H1 (e.g. 'Ozone Park Real Estate'); fall back to filename."""
    m = re.search(r'<h1[^>]*>\s*([^<]+?)\s*(?:Real Estate|Homes|Neighborhood)?\s*</h1>', page)
    if m:
        name = re.sub(r'\s*(Real Estate|Homes for Sale|Neighborhood Guide).*$', '', m.group(1)).strip()
        if 2 < len(name) < 40:
            return name
    base = os.path.splitext(os.path.basename(path))[0]
    return ' '.join(w.capitalize() for w in base.replace('_', '-').split('-'))


def map_section(name):
    q = re.sub(r'\s+', '+', name) + ',+NY'
    n = html.escape(name)
    return f'''  <!-- {MARK} -->
  <div class="{MARK}" style="margin:40px 0;">
    <h2 style="color:#1B2A6B;border-bottom:3px solid #00A651;padding-bottom:8px;margin-bottom:6px;">Explore {n}</h2>
    <p style="color:#555;font-size:.92rem;margin:0 0 14px;">Get to know the area — transit, schools, parks, and where the homes are. Pan and zoom the map to explore {n} and the surrounding blocks.</p>
    <iframe class="gre-nbhd-map" src="https://www.google.com/maps?q={q}&output=embed" width="100%" height="420" style="border:0;border-radius:12px;box-shadow:0 6px 24px rgba(12,23,51,.10);display:block;" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Map of {n}, New York"></iframe>
  </div>

'''


def main():
    pages = sorted(glob.glob(os.path.join(ROOT, 'neighborhoods', '**', '*.html'), recursive=True))
    updated = skipped = 0
    for p in pages:
        with open(p, encoding='utf-8') as f:
            page = f.read()
        if MARK in page:
            skipped += 1
            continue
        if ANCHOR not in page:
            skipped += 1
            continue
        name = nbhd_name(p, page)
        page = page.replace(ANCHOR, map_section(name) + ANCHOR, 1)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(page)
        updated += 1
    print(f'Neighborhood map injected. Updated: {updated}  Skipped: {skipped}')


if __name__ == '__main__':
    main()
