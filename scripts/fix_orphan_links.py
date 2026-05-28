#!/usr/bin/env python3
"""Fix orphan pages by adding internal links.

The audit found 333+ orphan pages with no incoming internal links.
The biggest groups:
- 259 ZIP code pages under /zip/
- 40 market report pages
- 7 community pages

Strategy: Add a related links section to neighborhood pages that
links to their ZIP code pages and market reports.
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ZIP → neighborhood mapping
ZIP_NEIGHBORHOODS = {
    '11414': ('Howard Beach', 'howard-beach'),
    '11415': ('Kew Gardens', 'kew-gardens'),
    '11416': ('Ozone Park', 'ozone-park'),
    '11417': ('Ozone Park', 'ozone-park'),
    '11418': ('Richmond Hill', 'richmond-hill'),
    '11419': ('Richmond Hill', 'richmond-hill'),
    '11420': ('South Ozone Park', 'south-ozone-park'),
    '11421': ('Woodhaven', 'woodhaven'),
    '11423': ('Hollis', 'hollis'),
    '11426': ('Bellerose', 'bellerose'),
    '11427': ('Queens Village', 'queens-village'),
    '11428': ('Queens Village', 'queens-village'),
    '11429': ('Queens Village', 'queens-village'),
    '11432': ('Jamaica', 'jamaica'),
    '11433': ('Jamaica', 'jamaica'),
    '11434': ('Jamaica', 'jamaica'),
    '11435': ('Jamaica', 'jamaica'),
    '11436': ('Jamaica', 'jamaica'),
    '11040': ('New Hyde Park', 'new-hyde-park'),
    '11042': ('New Hyde Park', 'new-hyde-park'),
    '11580': ('Valley Stream', 'valley-stream'),
    '11581': ('Valley Stream', 'valley-stream'),
    '11582': ('Valley Stream', 'valley-stream'),
}


def add_zip_links_to_neighborhoods():
    """Add links from neighborhood pages to their ZIP code pages."""
    fixes = 0
    zip_dir = os.path.join(SITE_ROOT, 'zip')
    if not os.path.isdir(zip_dir):
        return 0

    # Group ZIPs by neighborhood
    from collections import defaultdict
    hood_zips = defaultdict(list)
    for zipfile in sorted(os.listdir(zip_dir)):
        if zipfile.endswith('.html'):
            zipcode = zipfile.replace('.html', '')
            if zipcode in ZIP_NEIGHBORHOODS:
                hood_name, hood_slug = ZIP_NEIGHBORHOODS[zipcode]
                hood_zips[hood_slug].append(zipcode)

    for hood_slug, zips in hood_zips.items():
        hood_file = os.path.join(SITE_ROOT, 'neighborhoods', f'{hood_slug}.html')
        if not os.path.exists(hood_file):
            continue

        with open(hood_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Check if ZIP links already exist
        if '/zip/' in content:
            continue

        # Build ZIP links section
        zip_links = '\n'.join(
            f'    <li><a href="/zip/{z}.html">{z} ZIP Code Guide</a></li>'
            for z in zips
        )
        section = f'''
  <!-- ZIP Code Quick Links -->
  <section style="background:#f8f9fa;padding:1.5rem;border-radius:8px;margin:1.5rem 0;">
    <h3 style="color:#0b2545;margin:0 0 .75rem;">ZIP Code Guides</h3>
    <ul style="list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.5rem;">
{zip_links}
    </ul>
  </section>
'''
        # Insert before </main> or before the last </section>
        if '</main>' in content:
            content = content.replace('</main>', section + '</main>', 1)
        elif '</article>' in content:
            content = content.replace('</article>', section + '</article>', 1)
        else:
            # Insert before </body>
            content = content.replace('</body>', section + '</body>', 1)

        with open(hood_file, 'w', encoding='utf-8') as f:
            f.write(content)
        fixes += 1

    return fixes


def add_market_report_links():
    """Add links from neighborhood pages to matching market reports."""
    fixes = 0
    mr_dir = os.path.join(SITE_ROOT, 'market-reports')
    if not os.path.isdir(mr_dir):
        return 0

    # Find ZIP-based market reports
    for mrfile in os.listdir(mr_dir):
        if not mrfile.endswith('.html') or mrfile == 'index.html':
            continue

        # Extract ZIP from filename like "11417-ozone-park-market-report.html"
        m = re.match(r'(\d{5})-', mrfile)
        if not m:
            continue

        zipcode = m.group(1)
        if zipcode not in ZIP_NEIGHBORHOODS:
            continue

        hood_name, hood_slug = ZIP_NEIGHBORHOODS[zipcode]
        hood_file = os.path.join(SITE_ROOT, 'neighborhoods', f'{hood_slug}.html')
        if not os.path.exists(hood_file):
            continue

        with open(hood_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        mr_link = f'/market-reports/{mrfile}'
        if mr_link in content:
            continue

        # Add market report link
        link_html = f'    <li><a href="{mr_link}">{hood_name} {zipcode} Market Report</a></li>\n'

        # Find the ZIP Code Guides section and add after it, or add new section
        if '<!-- ZIP Code Quick Links -->' in content:
            # Add market report link after the ZIP section
            insert_point = content.find('<!-- ZIP Code Quick Links -->')
            section_end = content.find('</section>', insert_point)
            if section_end > 0:
                mr_section = f'''
  <!-- Market Reports -->
  <section style="background:#e8f4e8;padding:1.5rem;border-radius:8px;margin:1.5rem 0;">
    <h3 style="color:#0b2545;margin:0 0 .75rem;">Market Reports</h3>
    <ul style="list-style:none;padding:0;margin:0;">
{link_html}    </ul>
  </section>
'''
                content = content[:section_end + len('</section>')] + mr_section + content[section_end + len('</section>'):]

                with open(hood_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixes += 1

    return fixes


def add_community_links_to_hub():
    """Add community page links to the community hub and neighborhoods hub."""
    fixes = 0
    comm_dir = os.path.join(SITE_ROOT, 'community')
    hub_file = os.path.join(SITE_ROOT, 'neighborhoods.html')

    if not os.path.isdir(comm_dir) or not os.path.exists(hub_file):
        return 0

    with open(hub_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if '/community/' in content:
        return 0  # Already has community links

    # Build community links
    comm_pages = sorted(glob.glob(os.path.join(comm_dir, '*.html')))
    comm_pages = [p for p in comm_pages if not p.endswith('index.html')]

    if not comm_pages:
        return 0

    links = []
    for p in comm_pages:
        name = os.path.basename(p).replace('.html', '').replace('-', ' ').title()
        rel = '/' + os.path.relpath(p, SITE_ROOT)
        links.append(f'    <li><a href="{rel}">{name}</a></li>')

    section = f'''
  <!-- Community Pages -->
  <section style="background:#fff8e1;padding:1.5rem;border-radius:8px;margin:2rem 0;">
    <h3 style="color:#0b2545;margin:0 0 .75rem;">Community Resources</h3>
    <ul style="list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.5rem;">
{chr(10).join(links)}
    </ul>
  </section>
'''

    if '</main>' in content:
        content = content.replace('</main>', section + '</main>', 1)
    else:
        content = content.replace('</body>', section + '</body>', 1)

    with open(hub_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return 1


def main():
    zip_fixes = add_zip_links_to_neighborhoods()
    print(f"ZIP code links added to {zip_fixes} neighborhood pages")

    mr_fixes = add_market_report_links()
    print(f"Market report links added to {mr_fixes} neighborhood pages")

    comm_fixes = add_community_links_to_hub()
    print(f"Community links added to {comm_fixes} hub pages")

    print(f"\n=== ORPHAN LINK FIX COMPLETE ===")
    print(f"Total pages updated: {zip_fixes + mr_fixes + comm_fixes}")


if __name__ == '__main__':
    main()
