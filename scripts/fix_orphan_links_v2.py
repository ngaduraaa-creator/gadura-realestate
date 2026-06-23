#!/usr/bin/env python3
"""
fix_orphan_links_v2.py — Add internal links TO orphan pages from their logical parent/hub pages.

146 orphan pages (zero incoming internal links) across 7 categories:
  1. Blog orphans (9)       → /blog/index.html
  2. Calculator orphans (4) → /services/index.html, /resources/index.html
  3. Guide orphans (4)      → /blog/index.html + community pages
  4. Home-value orphans (3) → /services/index.html
  5. Home listing orphans (~93) → respective neighborhood pages
  6. Agent bio orphans (14) → /meet-the-agents.html
  7. Other orphans (misc)   → logical parents

Rules:
  - Read each target page first; understand structure
  - Insert links in contextually appropriate locations
  - Use descriptive anchor text from orphan's <title> tag
  - Don't duplicate existing links
  - UTF-8 encoding
  - Do NOT modify _includes/ files
"""

import os
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict
from typing import Optional

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")

# ── Counters ──────────────────────────────────────────────────────────
stats = {
    "orphans_fixed": 0,
    "files_modified": set(),
    "errors": [],
    "skipped_already_linked": 0,
    "skipped_missing_parent": 0,
}


# ── Helpers ───────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    """Read file content, return empty string if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""


def write_file(path: Path, content: str) -> None:
    """Write content to file."""
    path.write_text(content, encoding="utf-8")


def extract_title(html: str) -> str:
    """Extract text from <title> tag."""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        title = m.group(1).strip()
        # Strip common suffixes
        for suffix in [
            " | Gadura Real Estate",
            " | Gadura RE",
            " — Gadura Real Estate",
            " - Gadura Real Estate",
            " | Gadura Real Estate LLC",
        ]:
            if title.endswith(suffix):
                title = title[: -len(suffix)].strip()
        return title
    return ""


def extract_h1(html: str) -> str:
    """Extract text from first <h1> tag."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def link_exists(parent_html: str, orphan_path: str) -> bool:
    """Check if a link to the orphan already exists in the parent page."""
    # Normalize path variants
    variants = [orphan_path]
    if orphan_path.startswith("/"):
        variants.append(orphan_path[1:])
    else:
        variants.append("/" + orphan_path)
    # Also check without index.html
    for v in list(variants):
        if v.endswith("/index.html"):
            variants.append(v[:-10])  # trailing /
            variants.append(v[:-11])  # no trailing /
    for v in variants:
        if f'href="{v}"' in parent_html or f"href='{v}'" in parent_html:
            return True
    return False


def get_anchor_text(orphan_path: str) -> str:
    """Get good anchor text for an orphan page."""
    full = BASE / orphan_path.lstrip("/")
    html = read_file(full)
    title = extract_title(html)
    if title:
        return title
    h1 = extract_h1(html)
    if h1:
        return h1
    # Fallback: derive from path
    name = orphan_path.rstrip("/").split("/")[-1]
    if name == "index.html":
        name = orphan_path.rstrip("/").split("/")[-2]
    return name.replace("-", " ").replace(".html", "").title()


def add_link_record(orphan_path: str, parent_path: str):
    """Record a successfully linked orphan."""
    stats["orphans_fixed"] += 1
    stats["files_modified"].add(str(parent_path))


# ── 1. Blog orphans ──────────────────────────────────────────────────

BLOG_ORPHANS = [
    "blog/best-mortgage-lenders-queens-ny.html",
    "blog/downsizing-guide-queens-seniors.html",
    "blog/new-construction-homes-queens-li.html",
    "blog/nyc-first-generation-homebuyer-guide.html",
    "blog/open-houses-queens-ny.html",
    "blog/queens-gentrification-neighborhoods-2026.html",
    "blog/queens-real-estate-market-forecast-2026.html",
    "blog/real-estate-agent-vs-ibuyer-queens.html",
    "blog/veterans-home-buying-queens-ny.html",
]

BLOG_CATEGORY_MAP = {
    "blog/best-mortgage-lenders-queens-ny.html": "Buying",
    "blog/downsizing-guide-queens-seniors.html": "Selling",
    "blog/new-construction-homes-queens-li.html": "Buying",
    "blog/nyc-first-generation-homebuyer-guide.html": "Buying",
    "blog/open-houses-queens-ny.html": "Buying",
    "blog/queens-gentrification-neighborhoods-2026.html": "Neighborhood",
    "blog/queens-real-estate-market-forecast-2026.html": "Market",
    "blog/real-estate-agent-vs-ibuyer-queens.html": "Selling",
    "blog/veterans-home-buying-queens-ny.html": "Buying",
}


def fix_blog_orphans():
    """Add 9 blog orphans to /blog/index.html."""
    print("\n── 1. Blog orphans ──")
    blog_index = BASE / "blog" / "index.html"
    html = read_file(blog_index)
    if not html:
        stats["errors"].append("blog/index.html not found")
        return

    cards_html = ""
    linked = 0

    for orphan in BLOG_ORPHANS:
        fname = orphan.split("/")[-1]
        if (link_exists(html, orphan)
                or link_exists(html, "/" + orphan)
                or link_exists(html, fname)):
            print(f"  SKIP (already linked): {orphan}")
            stats["skipped_already_linked"] += 1
            continue
        anchor = get_anchor_text(orphan)
        cat = BLOG_CATEGORY_MAP.get(orphan, "Guide")
        fname = orphan.split("/")[-1]
        cards_html += f"""    <a href="{fname}" class="blog-card-new">
      <div class="card-accent-bar"></div>
      <div class="card-body">
        <span class="card-category">{cat}</span>
        <h3>{anchor}</h3>
        <div class="card-footer">
          <span class="card-arrow">Read Article →</span>
        </div>
      </div>
    </a>
"""
        linked += 1
        print(f"  LINKED: {orphan} → blog/index.html")

    if linked == 0:
        print("  No new blog links needed.")
        return

    # Insert before the CTA Box (the <!-- CTA Box --> comment or the div with gradient)
    new_section = f"""
  <h2 class="blog-section-title" id="more-guides">More Guides &amp; Resources</h2>
  <div class="blog-grid-new three-col">
{cards_html}  </div>
"""

    # Find the CTA box
    cta_marker = "<!-- CTA Box -->"
    if cta_marker in html:
        html = html.replace(cta_marker, new_section + "\n  " + cta_marker)
    else:
        # Fallback: insert before the "Have a Specific Question?" div
        fallback = '<div style="background:linear-gradient(135deg,#1B2A6B,#0d3a24)'
        idx = html.find(fallback)
        if idx > 0:
            html = html[:idx] + new_section + "\n  " + html[idx:]
        else:
            stats["errors"].append("Could not find insertion point in blog/index.html")
            return

    write_file(blog_index, html)
    for orphan in BLOG_ORPHANS:
        fname = orphan.split("/")[-1]
        if not link_exists(read_file(blog_index), fname):
            continue
        add_link_record(orphan, "blog/index.html")
    stats["files_modified"].add("blog/index.html")
    print(f"  Added {linked} blog cards to blog/index.html")


# ── 2. Calculator orphans ────────────────────────────────────────────

CALCULATOR_ORPHANS = [
    "calculators/1031-timeline.html",
    "calculators/closing-costs.html",
    "calculators/fha-self-sufficiency.html",
    "calculators/mansion-tax.html",
]


def fix_calculator_orphans():
    """Add 4 calculator orphans to /services/index.html and /resources/index.html."""
    print("\n── 2. Calculator orphans ──")

    for parent_rel in ["services/index.html", "resources/index.html"]:
        parent_path = BASE / parent_rel
        html = read_file(parent_path)
        if not html:
            print(f"  SKIP: {parent_rel} not found")
            continue

        links_html = ""
        linked = 0
        for orphan in CALCULATOR_ORPHANS:
            if link_exists(html, "/" + orphan):
                print(f"  SKIP (already in {parent_rel}): {orphan}")
                stats["skipped_already_linked"] += 1
                continue
            anchor = get_anchor_text(orphan)
            links_html += f'      <a href="/{orphan}" style="display:block;padding:16px 18px;background:#fff;border-left:4px solid #e8c547;border-radius:6px;text-decoration:none;color:#0b2545;"><strong style="display:block;font-size:1rem;">{anchor} →</strong><span style="font-size:.85rem;color:#555;">Free online calculator</span></a>\n'
            linked += 1

        if linked == 0:
            continue

        calc_section = f"""
<section class="section" style="background:#f0f8ff;border-top:1px solid #b3d4fc;">
  <div class="container" style="max-width:1100px;">
    <h2 style="text-align:center;margin:0 0 8px;color:#0b2545;">Free Real Estate Calculators</h2>
    <p style="text-align:center;color:#555;margin:0 0 24px;">Estimate costs, plan timelines, and make informed decisions with our free tools.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;">
{links_html}    </div>
  </div>
</section>
"""

        # Insert before the first footer
        footer_pattern = re.search(r"<footer[\s>]", html)
        if footer_pattern:
            idx = footer_pattern.start()
            html = html[:idx] + calc_section + "\n" + html[idx:]
            write_file(parent_path, html)
            for orphan in CALCULATOR_ORPHANS:
                add_link_record(orphan, parent_rel)
            stats["files_modified"].add(parent_rel)
            print(f"  Added {linked} calculator links to {parent_rel}")
        else:
            stats["errors"].append(f"No footer found in {parent_rel}")


# ── 3. Guide orphans ─────────────────────────────────────────────────

GUIDE_ORPHANS = {
    "guides/fha-loan-real-estate-agent-queens.html": [
        "blog/index.html",
    ],
    "guides/guyanese-real-estate-agent-queens.html": [
        "blog/index.html",
        "community/guyanese-community.html",
    ],
    "guides/how-to-find-real-estate-agent-queens.html": [
        "blog/index.html",
        "about.html",
    ],
    "guides/indian-real-estate-agent-queens.html": [
        "blog/index.html",
        "community/indian-community.html",
    ],
}


def fix_guide_orphans():
    """Add 4 guide orphans to blog index + relevant community/about pages."""
    print("\n── 3. Guide orphans ──")

    # Collect guides that need to go into the blog index
    # (they were already handled in the blog section above via the new section)
    # Now handle the community/about page links

    for orphan, parents in GUIDE_ORPHANS.items():
        anchor = get_anchor_text(orphan)
        for parent_rel in parents:
            if parent_rel == "blog/index.html":
                # Already in the blog section we add a card
                parent_path = BASE / parent_rel
                html = read_file(parent_path)
                if link_exists(html, "/" + orphan):
                    print(f"  SKIP (already in blog): {orphan}")
                    stats["skipped_already_linked"] += 1
                    continue
                # Add to the "More Guides" section we already created, or insert standalone
                fname = orphan.split("/")[-1]
                card = f"""    <a href="/{orphan}" class="blog-card-new">
      <div class="card-accent-bar"></div>
      <div class="card-body">
        <span class="card-category">Guide</span>
        <h3>{anchor}</h3>
        <div class="card-footer">
          <span class="card-arrow">Read Guide →</span>
        </div>
      </div>
    </a>
"""
                # Insert into the "More Guides" grid we already created
                marker = '<h2 class="blog-section-title" id="more-guides">'
                if marker in html:
                    # Find the closing </div> of the grid
                    grid_start = html.find("blog-grid-new three-col", html.find(marker))
                    if grid_start > 0:
                        # Find the </div> closing this grid
                        close_div = html.find("</div>", grid_start)
                        if close_div > 0:
                            html = html[:close_div] + card + "  " + html[close_div:]
                            write_file(parent_path, html)
                            add_link_record(orphan, parent_rel)
                            stats["files_modified"].add(parent_rel)
                            print(f"  LINKED: {orphan} → {parent_rel}")
                            continue

                # Fallback: add as standalone section
                link_block = f"""
<div style="margin:20px 0;padding:16px;background:#f8f9fa;border-left:4px solid #1B2A6B;border-radius:6px;">
  <a href="/{orphan}" style="color:#1B2A6B;font-weight:600;text-decoration:none;">{anchor} →</a>
</div>
"""
                cta = '<div style="background:linear-gradient(135deg,#1B2A6B,#0d3a24)'
                idx = html.find(cta)
                if idx > 0:
                    html = html[:idx] + link_block + html[idx:]
                    write_file(parent_path, html)
                    add_link_record(orphan, parent_rel)
                    stats["files_modified"].add(parent_rel)
                    print(f"  LINKED: {orphan} → {parent_rel}")
                continue

            # Community/about pages
            parent_path = BASE / parent_rel
            html = read_file(parent_path)
            if not html:
                print(f"  SKIP: {parent_rel} not found")
                stats["skipped_missing_parent"] += 1
                continue

            if link_exists(html, "/" + orphan):
                print(f"  SKIP (already in {parent_rel}): {orphan}")
                stats["skipped_already_linked"] += 1
                continue

            link_block = f"""
<div style="margin:20px 0;padding:16px;background:#f8f9fa;border-left:4px solid #1B2A6B;border-radius:6px;">
  <a href="/{orphan}" style="color:#1B2A6B;font-weight:600;text-decoration:none;font-size:1rem;">{anchor} →</a>
  <p style="margin:4px 0 0;font-size:.85rem;color:#666;">Expert guidance for your home search in Queens.</p>
</div>
"""
            # Insert before the first footer
            footer_match = re.search(r"<footer[\s>]", html)
            if footer_match:
                idx = footer_match.start()
                html = html[:idx] + link_block + "\n" + html[idx:]
                write_file(parent_path, html)
                add_link_record(orphan, parent_rel)
                stats["files_modified"].add(parent_rel)
                print(f"  LINKED: {orphan} → {parent_rel}")
            else:
                stats["errors"].append(f"No footer in {parent_rel} for guide {orphan}")


# ── 4. Home-value orphans ────────────────────────────────────────────

HOME_VALUE_ORPHANS = [
    "home-value/free-cma-queens.html",
    "home-value/home-equity-calculator.html",
    "home-value/sell-or-rent-calculator.html",
]


def fix_home_value_orphans():
    """Add 3 home-value orphans to /services/index.html."""
    print("\n── 4. Home-value orphans ──")

    parent_rel = "services/index.html"
    parent_path = BASE / parent_rel
    html = read_file(parent_path)
    if not html:
        stats["errors"].append(f"{parent_rel} not found")
        return

    links_html = ""
    linked = 0
    for orphan in HOME_VALUE_ORPHANS:
        if link_exists(html, "/" + orphan):
            print(f"  SKIP (already linked): {orphan}")
            stats["skipped_already_linked"] += 1
            continue
        anchor = get_anchor_text(orphan)
        links_html += f'      <a href="/{orphan}" style="display:block;padding:16px 18px;background:#fff;border-left:4px solid #00A651;border-radius:6px;text-decoration:none;color:#0b2545;"><strong style="display:block;font-size:1rem;">{anchor} →</strong><span style="font-size:.85rem;color:#555;">Free home valuation tool</span></a>\n'
        linked += 1

    if linked == 0:
        print("  No new home-value links needed.")
        return

    section = f"""
<section class="section" style="background:#f0fdf4;border-top:1px solid #bbf7d0;">
  <div class="container" style="max-width:1100px;">
    <h2 style="text-align:center;margin:0 0 8px;color:#0b2545;">Home Valuation Tools</h2>
    <p style="text-align:center;color:#555;margin:0 0 24px;">Find out what your home is worth with our free tools — CMA reports, equity calculators, and rent vs. sell analysis.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;">
{links_html}    </div>
  </div>
</section>
"""

    # Insert before the calculators section we may have added, or before footer
    calc_marker = "Free Real Estate Calculators"
    if calc_marker in html:
        idx = html.find(calc_marker)
        # Go back to find the <section before it
        section_start = html.rfind("<section", 0, idx)
        if section_start > 0:
            html = html[:section_start] + section + "\n" + html[section_start:]
        else:
            footer_match = re.search(r"<footer[\s>]", html)
            if footer_match:
                html = html[: footer_match.start()] + section + "\n" + html[footer_match.start() :]
    else:
        footer_match = re.search(r"<footer[\s>]", html)
        if footer_match:
            html = html[: footer_match.start()] + section + "\n" + html[footer_match.start() :]
        else:
            stats["errors"].append(f"No footer in {parent_rel}")
            return

    write_file(parent_path, html)
    for orphan in HOME_VALUE_ORPHANS:
        add_link_record(orphan, parent_rel)
    stats["files_modified"].add(parent_rel)
    print(f"  Added {linked} home-value links to {parent_rel}")


# ── 5. Home listing orphans ──────────────────────────────────────────

# Neighborhood name → possible page paths (relative to BASE)
NEIGHBORHOOD_ALIASES = {
    "ozone-park": ["neighborhoods/ozone-park.html", "neighborhoods/ozone-park/index.html"],
    "south-ozone-park": ["neighborhoods/south-ozone-park.html", "neighborhoods/south-ozone-park/index.html", "neighborhoods/ozone-park.html"],
    "richmond-hill": ["neighborhoods/richmond-hill.html", "neighborhoods/richmond-hill/index.html"],
    "south-richmond-hill": ["neighborhoods/south-richmond-hill.html", "neighborhoods/south-richmond-hill/index.html", "neighborhoods/richmond-hill.html"],
    "howard-beach": ["neighborhoods/howard-beach.html", "neighborhoods/howard-beach/index.html"],
    "jamaica": ["neighborhoods/jamaica.html", "neighborhoods/jamaica/index.html"],
    "jamaica-estates": ["neighborhoods/jamaica-estates.html", "neighborhoods/jamaica-estates/index.html", "neighborhoods/jamaica.html"],
    "woodhaven": ["neighborhoods/woodhaven.html", "neighborhoods/woodhaven/index.html"],
    "brooklyn": ["neighborhoods/brooklyn.html", "neighborhoods/brooklyn/index.html"],
    "valley-stream": ["neighborhoods/valley-stream.html", "neighborhoods/valley-stream/index.html"],
    "elmont": ["neighborhoods/elmont.html", "neighborhoods/elmont/index.html"],
    "queens-village": ["neighborhoods/queens-village.html", "neighborhoods/queens-village/index.html"],
    "baldwin": ["neighborhoods/baldwin.html", "neighborhoods/baldwin/index.html"],
    "freeport": ["neighborhoods/freeport.html", "neighborhoods/freeport/index.html"],
    "middle-village": ["neighborhoods/middle-village.html", "neighborhoods/middle-village/index.html"],
    "kew-gardens": ["neighborhoods/kew-gardens.html", "neighborhoods/kew-gardens/index.html"],
    "briarwood": ["neighborhoods/briarwood.html", "neighborhoods/briarwood/index.html"],
    "glendale": ["neighborhoods/glendale.html", "neighborhoods/glendale/index.html"],
    "far-rockaway": ["neighborhoods/far-rockaway.html", "neighborhoods/far-rockaway/index.html"],
    "cambria-heights": ["neighborhoods/cambria-heights.html", "neighborhoods/cambria-heights/index.html"],
    "springfield-gardens": ["neighborhoods/springfield-gardens.html", "neighborhoods/springfield-gardens/index.html"],
    "st-albans": ["neighborhoods/st-albans.html", "neighborhoods/st-albans/index.html"],
    "rosedale": ["neighborhoods/rosedale.html", "neighborhoods/rosedale/index.html"],
    "hempstead": ["neighborhoods/hempstead.html", "neighborhoods/hempstead/index.html"],
    "rockville-centre": ["neighborhoods/rockville-centre.html", "neighborhoods/rockville-centre/index.html"],
    "merrick": ["neighborhoods/merrick.html", "neighborhoods/merrick/index.html"],
    "lynbrook": ["neighborhoods/lynbrook.html", "neighborhoods/lynbrook/index.html"],
    "north-babylon": ["neighborhoods/north-babylon.html", "neighborhoods/north-babylon/index.html"],
    "east-new-york": ["neighborhoods/east-new-york.html", "neighborhoods/east-new-york/index.html"],
    "hollis": ["neighborhoods/hollis.html", "neighborhoods/hollis/index.html"],
    "holliswood": ["neighborhoods/holliswood.html", "neighborhoods/holliswood/index.html"],
}


def guess_neighborhood(dirname: str) -> str:
    """Given a home listing directory name, guess the neighborhood slug."""
    # Pattern: [address]-[neighborhood]-ny-[zip] or [address]-[neighborhood]-new-york-[zip]
    # Remove state/zip suffix patterns
    name = dirname.lower()

    # Known neighborhood names to search for (longest first to avoid partial match)
    neighborhoods = [
        "south-richmond-hill", "south-ozone-park", "jamaica-estates",
        "richmond-hill", "springfield-gardens", "cambria-heights",
        "queens-village", "ozone-park", "howard-beach", "jamaica",
        "far-rockaway", "middle-village", "kew-gardens", "valley-stream",
        "rockville-centre", "north-babylon", "east-new-york",
        "woodhaven", "brooklyn", "glendale", "briarwood", "elmont",
        "baldwin", "freeport", "hempstead", "lynbrook", "merrick",
        "rosedale", "st-albans", "hollis", "holliswood",
    ]

    for n in neighborhoods:
        if n in name:
            return n

    # Try to extract from the address pattern
    # Typical: 97-33-89th-street-ozone-park-ny-11416
    # Strip zip and state
    stripped = re.sub(r"-(?:ny|new-york)-\d{5}$", "", name)
    # The neighborhood is typically the last part after the street name
    # Try splitting on common street suffixes
    for suffix in ["-street-", "-st-", "-avenue-", "-ave-", "-road-", "-rd-",
                   "-boulevard-", "-blvd-", "-place-", "-pl-", "-drive-", "-dr-",
                   "-lane-", "-ln-", "-court-", "-ct-", "-terrace-"]:
        idx = stripped.rfind(suffix)
        if idx > 0:
            after = stripped[idx + len(suffix):]
            if after:
                return after

    return ""


def find_neighborhood_page(neighborhood: str) -> Optional[Path]:
    """Find the actual neighborhood page file."""
    candidates = NEIGHBORHOOD_ALIASES.get(neighborhood, [
        f"neighborhoods/{neighborhood}.html",
        f"neighborhoods/{neighborhood}/index.html",
    ])
    for c in candidates:
        p = BASE / c
        if p.exists():
            return p
    return None


def fix_home_listing_orphans():
    """Add home listing orphans to their respective neighborhood pages."""
    print("\n── 5. Home listing orphans ──")

    homes_dir = BASE / "homes"
    if not homes_dir.exists():
        stats["errors"].append("homes/ directory not found")
        return

    # Group homes by neighborhood
    neighborhood_homes = defaultdict(list)
    unmatched = []

    for home_dir in sorted(homes_dir.iterdir()):
        if not home_dir.is_dir():
            continue
        index_file = home_dir / "index.html"
        if not index_file.exists():
            continue

        dirname = home_dir.name
        neighborhood = guess_neighborhood(dirname)

        if neighborhood:
            neighborhood_homes[neighborhood].append(dirname)
        else:
            unmatched.append(dirname)

    # For each neighborhood, add links to the neighborhood page
    total_linked = 0
    for neighborhood, homes in sorted(neighborhood_homes.items()):
        page = find_neighborhood_page(neighborhood)
        if not page:
            # Try fallback pages
            for fb in ["our-listings/index.html", "past-sales/index.html", "homes-for-sale/index.html"]:
                fp = BASE / fb
                if fp.exists():
                    page = fp
                    break

        if not page:
            for h in homes:
                stats["skipped_missing_parent"] += 1
            print(f"  SKIP: No page found for neighborhood '{neighborhood}' ({len(homes)} homes)")
            continue

        html = read_file(page)
        page_rel = str(page.relative_to(BASE))

        # Collect links that need to be added
        new_links = []
        for home_dirname in homes:
            home_path = f"/homes/{home_dirname}/"
            if link_exists(html, home_path) or link_exists(html, f"/homes/{home_dirname}/index.html"):
                stats["skipped_already_linked"] += 1
                continue
            anchor = get_anchor_text(f"homes/{home_dirname}/index.html")
            new_links.append((home_path, anchor, home_dirname))

        if not new_links:
            continue

        # Build the properties section
        links_html = ""
        for path, anchor, dirname in new_links:
            # Create a readable address from the dirname
            addr_parts = dirname.split("-")
            # Remove zip and state
            clean = re.sub(r"-(?:ny|new-york)-\d{5}$", "", dirname)
            readable_addr = clean.replace("-", " ").title()
            links_html += f'    <li style="margin-bottom:8px;"><a href="{path}" style="color:#1B2A6B;text-decoration:none;font-weight:500;">{anchor if anchor != dirname.replace("-", " ").title() else readable_addr}</a></li>\n'

        display_name = neighborhood.replace("-", " ").title()
        properties_section = f"""
<!-- Properties in {display_name} — auto-linked by fix_orphan_links_v2.py -->
<aside style="margin:32px 0;padding:24px;background:#f8f9fa;border-radius:8px;border-left:4px solid #1B2A6B;">
  <h3 style="font-family:Montserrat,sans-serif;color:#1B2A6B;font-size:18px;margin-bottom:12px;">Properties in {display_name}</h3>
  <ul style="list-style:none;padding:0;line-height:1.8;">
{links_html}  </ul>
  <p style="margin:12px 0 0;font-size:.85rem;color:#666;">Explore our featured listings in {display_name}. <a href="/contact.html" style="color:#00A651;">Contact us</a> for a private showing.</p>
</aside>
"""

        # Insert before the lead capture section or before footer
        # Look for the CTA / lead capture section
        insert_markers = [
            "<!-- Neighborhood Lead Capture -->",
            "Looking to Buy or Sell in This Area?",
            '<section style="background:#f0fdf4;',
        ]
        inserted = False
        for marker in insert_markers:
            idx = html.find(marker)
            if idx > 0:
                # Go back to find the start of the section/element
                if marker.startswith("<"):
                    html = html[:idx] + properties_section + "\n" + html[idx:]
                else:
                    # Find the element that contains this marker
                    line_start = html.rfind("\n", 0, idx)
                    if line_start < 0:
                        line_start = 0
                    html = html[:line_start] + properties_section + html[line_start:]
                inserted = True
                break

        if not inserted:
            # Insert before the first footer
            footer_match = re.search(r"<footer[\s>]", html)
            if footer_match:
                html = html[: footer_match.start()] + properties_section + "\n" + html[footer_match.start() :]
                inserted = True

        if inserted:
            write_file(page, html)
            for _, _, dirname in new_links:
                add_link_record(f"homes/{dirname}/index.html", page_rel)
                total_linked += 1
            stats["files_modified"].add(page_rel)
            print(f"  LINKED: {len(new_links)} homes → {page_rel}")

    # Handle unmatched homes — link from our-listings or homes-for-sale
    if unmatched:
        fallback_pages = ["our-listings/index.html", "past-sales/index.html", "homes-for-sale/index.html"]
        fallback = None
        for fb in fallback_pages:
            fp = BASE / fb
            if fp.exists():
                fallback = fp
                break

        if fallback:
            html = read_file(fallback)
            fb_rel = str(fallback.relative_to(BASE))
            new_links = []
            for dirname in unmatched:
                home_path = f"/homes/{dirname}/"
                if link_exists(html, home_path):
                    stats["skipped_already_linked"] += 1
                    continue
                anchor = get_anchor_text(f"homes/{dirname}/index.html")
                new_links.append((home_path, anchor, dirname))

            if new_links:
                links_html = ""
                for path, anchor, dirname in new_links:
                    readable = re.sub(r"-(?:ny|new-york)-\d{5}$", "", dirname).replace("-", " ").title()
                    links_html += f'    <li style="margin-bottom:8px;"><a href="{path}" style="color:#1B2A6B;text-decoration:none;font-weight:500;">{anchor if anchor != dirname.replace("-", " ").title() else readable}</a></li>\n'

                section = f"""
<!-- Additional Properties — auto-linked by fix_orphan_links_v2.py -->
<aside style="margin:32px 0;padding:24px;background:#f8f9fa;border-radius:8px;border-left:4px solid #1B2A6B;">
  <h3 style="font-family:Montserrat,sans-serif;color:#1B2A6B;font-size:18px;margin-bottom:12px;">More Properties</h3>
  <ul style="list-style:none;padding:0;line-height:1.8;">
{links_html}  </ul>
</aside>
"""
                footer_match = re.search(r"<footer[\s>]", html)
                if footer_match:
                    html = html[: footer_match.start()] + section + "\n" + html[footer_match.start() :]
                    write_file(fallback, html)
                    for _, _, dirname in new_links:
                        add_link_record(f"homes/{dirname}/index.html", fb_rel)
                        total_linked += 1
                    stats["files_modified"].add(fb_rel)
                    print(f"  LINKED: {len(new_links)} unmatched homes → {fb_rel}")
        else:
            print(f"  WARNING: {len(unmatched)} homes could not be matched to any page")
            for d in unmatched:
                stats["skipped_missing_parent"] += 1

    print(f"  Total home listings linked: {total_linked}")


# ── 6. Agent bio orphans ─────────────────────────────────────────────

AGENT_ORPHANS = [
    "bhupinder-gill/index.html",
    "gaurav-bhardwaj/index.html",
    "gurvinder-singh/index.html",
    "jagman-dhaliwal/index.html",
    "jaqueline-silva/index.html",
    "jeevanpreet-singh/index.html",
    "kumar-ramudit/index.html",
    "manpreet-kaur/index.html",
    "md-ali/index.html",
    "miguel-cane/index.html",
    "nitin-gadura/index.html",
    "ravi-kapoor/index.html",
    "rushneet-kaur/index.html",
    "stephanie-silva/index.html",
]

# Note: We also check for top-level .html versions like /bhupinder-gill.html


def fix_agent_orphans():
    """Ensure all agent bio pages are linked from /meet-the-agents.html."""
    print("\n── 6. Agent bio orphans ──")

    parent_path = BASE / "meet-the-agents.html"
    html = read_file(parent_path)
    if not html:
        stats["errors"].append("meet-the-agents.html not found")
        return

    linked = 0
    for orphan in AGENT_ORPHANS:
        agent_slug = orphan.split("/")[0]  # e.g. "bhupinder-gill"
        # Check if already linked (as /agent-slug/ or /agent-slug/index.html or /agent-slug.html)
        if (link_exists(html, f"/{agent_slug}/")
                or link_exists(html, f"/{agent_slug}/index.html")
                or link_exists(html, f"/{agent_slug}.html")
                or link_exists(html, f"{agent_slug}/")
                or link_exists(html, f"{agent_slug}.html")):
            print(f"  SKIP (already linked): {orphan}")
            stats["skipped_already_linked"] += 1
            continue

        anchor = get_anchor_text(orphan)
        if not anchor or anchor == "Index":
            anchor = agent_slug.replace("-", " ").title()

        # Add link before footer
        link_block = f"""
<div style="margin:8px 20px;padding:14px 18px;background:#f8f9fa;border-left:3px solid #1B2A6B;border-radius:6px;display:inline-block;">
  <a href="/{agent_slug}/" style="color:#1B2A6B;font-weight:600;text-decoration:none;">{anchor} — View Full Bio →</a>
</div>
"""
        footer_match = re.search(r"<footer[\s>]", html)
        if footer_match:
            idx = footer_match.start()
            html = html[:idx] + link_block + "\n" + html[idx:]
            linked += 1
            add_link_record(orphan, "meet-the-agents.html")
            print(f"  LINKED: {orphan} → meet-the-agents.html")

    if linked > 0:
        write_file(parent_path, html)
        stats["files_modified"].add("meet-the-agents.html")
        print(f"  Added {linked} agent bio links")
    else:
        print("  All agents already linked.")


# ── 7. Other orphans ─────────────────────────────────────────────────

OTHER_ORPHANS = {
    "faq/index.html": ["about.html"],
    "resources/index.html": ["services/index.html"],
    "portfolio/index.html": ["about.html"],
    "sell/index.html": ["services/index.html"],
    "privacy.html": [],  # Usually in footer already
    "press/release-2026-04-29.html": ["about.html"],
    "moving-to/index.html": ["services/index.html"],
}


def fix_other_orphans():
    """Add miscellaneous orphan links to their logical parents."""
    print("\n── 7. Other orphans ──")

    for orphan, parents in OTHER_ORPHANS.items():
        orphan_path = BASE / orphan
        if not orphan_path.exists():
            print(f"  SKIP (file missing): {orphan}")
            continue

        anchor = get_anchor_text(orphan)

        for parent_rel in parents:
            parent_path = BASE / parent_rel
            html = read_file(parent_path)
            if not html:
                print(f"  SKIP: {parent_rel} not found")
                stats["skipped_missing_parent"] += 1
                continue

            if link_exists(html, "/" + orphan) or link_exists(html, "/" + orphan.replace("/index.html", "/")):
                print(f"  SKIP (already in {parent_rel}): {orphan}")
                stats["skipped_already_linked"] += 1
                continue

            # Determine the link href
            href = "/" + orphan
            if orphan.endswith("/index.html"):
                href = "/" + orphan.replace("/index.html", "/")

            link_block = f"""
<div style="margin:12px 0;padding:14px 18px;background:#f8f9fa;border-left:4px solid #1B2A6B;border-radius:6px;">
  <a href="{href}" style="color:#1B2A6B;font-weight:600;text-decoration:none;font-size:1rem;">{anchor} →</a>
</div>
"""
            # Insert before the first footer
            footer_match = re.search(r"<footer[\s>]", html)
            if footer_match:
                idx = footer_match.start()
                html = html[:idx] + link_block + "\n" + html[idx:]
                write_file(parent_path, html)
                add_link_record(orphan, parent_rel)
                stats["files_modified"].add(parent_rel)
                print(f"  LINKED: {orphan} → {parent_rel}")
            else:
                stats["errors"].append(f"No footer in {parent_rel} for {orphan}")


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("fix_orphan_links_v2.py — Linking orphan pages")
    print(f"Base directory: {BASE}")
    print("=" * 60)

    # Run all fixers in order (blog must go first since guides add to its section)
    fix_blog_orphans()
    fix_calculator_orphans()
    fix_guide_orphans()
    fix_home_value_orphans()
    fix_home_listing_orphans()
    fix_agent_orphans()
    fix_other_orphans()

    # Final report
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Orphans fixed (links added):  {stats['orphans_fixed']}")
    print(f"  Files modified:               {len(stats['files_modified'])}")
    print(f"  Skipped (already linked):     {stats['skipped_already_linked']}")
    print(f"  Skipped (parent missing):     {stats['skipped_missing_parent']}")

    if stats["files_modified"]:
        print("\n  Modified files:")
        for f in sorted(stats["files_modified"]):
            print(f"    - {f}")

    if stats["errors"]:
        print(f"\n  Errors ({len(stats['errors'])}):")
        for e in stats["errors"]:
            print(f"    ! {e}")

    print()
    return 0 if stats["orphans_fixed"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
