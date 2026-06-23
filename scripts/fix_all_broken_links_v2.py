#!/usr/bin/env python3
"""
fix_all_broken_links_v2.py
--------------------------
Fixes three categories of issues across all HTML pages in gadura-realestate:

1. Broken market-report date links for ZIP codes that lack monthly pages
2. Missing meta descriptions on v2/ redirect stubs
3. Missing Twitter card meta tags on market-reports/queens/ozone-park-11416/2024/index.html
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path("/Users/nidhigadura/Jagex/gadura-realestate")

# ── Counters ──────────────────────────────────────────────────────────────────
stats = {
    "files_modified": 0,
    "links_fixed": 0,
    "meta_descriptions_added": 0,
    "twitter_cards_added": 0,
    "files_scanned": 0,
}

modified_files = set()


def read_file(path):
    """Read file with utf-8 and fallback error handling."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] Could not read {path}: {e}")
        return None


def write_file(path, content):
    """Write file with utf-8 encoding."""
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  [ERROR] Could not write {path}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# ISSUE 1: Fix broken market-report date links
# ─────────────────────────────────────────────────────────────────────────────

BROKEN_ZIPS = [
    "long-island-city-11101",
    "flushing-11358",
    "astoria-11105",
    "astoria-11103",
    "douglaston-11363",
    "fresh-meadows-11365",
    "whitestone-11357",
    "bayside-11361",
    "woodhaven-11421",
    "jamaica-11432",
]

# Build a single regex that matches href="/market-reports/queens/[broken-zip]/YYYY-MM/"
# Captures: group(1)=zip slug, group(2)=date portion (e.g. "2024-09/")
_zip_alt = "|".join(re.escape(z) for z in BROKEN_ZIPS)
BROKEN_LINK_RE = re.compile(
    r'href="(/market-reports/queens/(' + _zip_alt + r')/\d{4}-\d{2}/)"'
)


def fix_broken_links():
    """Scan all HTML files (excluding _includes/) and rewrite broken date links."""
    print("\n=== ISSUE 1: Fixing broken market-report date links ===")
    total_fixed = 0
    files_touched = 0

    for html_path in ROOT.rglob("*.html"):
        # Skip _includes directory
        if "_includes" in html_path.parts:
            continue

        stats["files_scanned"] += 1
        content = read_file(html_path)
        if content is None:
            continue

        matches = BROKEN_LINK_RE.findall(content)
        if not matches:
            continue

        count_before = len(matches)

        def replace_link(m):
            zip_slug = m.group(2)
            return f'href="/market-reports/queens/{zip_slug}/"'

        new_content = BROKEN_LINK_RE.sub(replace_link, content)

        if new_content != content:
            if write_file(html_path, new_content):
                rel = html_path.relative_to(ROOT)
                print(f"  Fixed {count_before} link(s) in {rel}")
                total_fixed += count_before
                files_touched += 1
                modified_files.add(str(html_path))

    stats["links_fixed"] = total_fixed
    print(f"\n  Total links fixed: {total_fixed} across {files_touched} file(s)")


# ─────────────────────────────────────────────────────────────────────────────
# ISSUE 2: Add missing meta descriptions to v2/ pages
# ─────────────────────────────────────────────────────────────────────────────

# Explicit meta descriptions for specific pages
EXPLICIT_META = {
    "v2/sell.html": (
        "Sell your Queens or Long Island home with Gadura Real Estate. "
        "Free market analysis. Call Nitin Gadura (917) 705-0132."
    ),
    "v2/about.html": (
        "About Gadura Real Estate LLC — serving Queens and Long Island "
        "home buyers and sellers. Meet Nitin Gadura."
    ),
    "v2/buy.html": (
        "Find homes for sale in Queens and Long Island with Gadura Real Estate. "
        "Browse listings and call (917) 705-0132."
    ),
    "v2/selling/index.html": (
        "Selling your home in Queens? Get a free home valuation from "
        "Gadura Real Estate. Call (917) 705-0132."
    ),
    "v2/resources/index.html": (
        "Real estate resources for Queens and Long Island buyers and sellers "
        "from Gadura Real Estate LLC."
    ),
    "v2/zip-codes/11417.html": (
        "Homes for sale in ZIP code 11417, Queens NY. "
        "Market data and listings from Gadura Real Estate."
    ),
}


def _neighborhood_name_from_filename(filename):
    """Convert 'south-ozone-park.html' -> 'South Ozone Park'."""
    stem = Path(filename).stem
    return stem.replace("-", " ").title()


def _generate_neighborhood_description(name):
    """Generate meta description for a neighborhood page."""
    return (
        f"{name} real estate — homes for sale, market data, "
        f"and community info from Gadura Real Estate."
    )


def add_meta_descriptions():
    """Add meta description tags to v2/ pages that are missing them."""
    print("\n=== ISSUE 2: Adding missing meta descriptions to v2/ pages ===")
    added = 0

    # Collect all target files
    targets = {}

    # Explicit pages
    for rel_path, desc in EXPLICIT_META.items():
        full_path = ROOT / rel_path
        if full_path.exists():
            targets[full_path] = desc
        else:
            print(f"  [WARN] File not found: {rel_path}")

    # Neighborhood pages (excluding ozone-park.html which already has one,
    # and index.html which gets its own description if needed)
    neighborhoods_dir = ROOT / "v2" / "neighborhoods"
    if neighborhoods_dir.exists():
        for html_file in sorted(neighborhoods_dir.glob("*.html")):
            if html_file.name == "index.html":
                # Skip index -- not a neighborhood page
                continue
            if html_file in targets:
                continue
            name = _neighborhood_name_from_filename(html_file.name)
            targets[html_file] = _generate_neighborhood_description(name)

    # Process each target
    for file_path, description in sorted(targets.items()):
        content = read_file(file_path)
        if content is None:
            continue

        # Check if meta description already exists
        if re.search(r'<meta\s+name=["\']description["\']', content, re.IGNORECASE):
            rel = file_path.relative_to(ROOT)
            print(f"  [SKIP] Already has meta description: {rel}")
            continue

        # Build the meta tag
        meta_tag = f'  <meta name="description" content="{description}">'

        # Strategy: insert after the last of charset/viewport/title/meta-refresh,
        # before the next tag. We look for the <title>...</title> line and insert after it.
        # Since these are redirect stubs, the pattern is:
        #   <meta charset="UTF-8">
        #   <title>...</title>
        # We insert the description after the title line.

        title_pattern = re.compile(r'([ \t]*<title>.*?</title>)', re.IGNORECASE)
        title_match = title_pattern.search(content)

        if title_match:
            insert_pos = title_match.end()
            new_content = (
                content[:insert_pos] + "\n" + meta_tag + content[insert_pos:]
            )
        else:
            # Fallback: insert before </head>
            head_close = content.find("</head>")
            if head_close == -1:
                print(f"  [WARN] No </head> found in {file_path.relative_to(ROOT)}")
                continue
            new_content = (
                content[:head_close] + meta_tag + "\n" + content[head_close:]
            )

        if new_content != content:
            if write_file(file_path, new_content):
                rel = file_path.relative_to(ROOT)
                print(f"  Added meta description to {rel}")
                added += 1
                modified_files.add(str(file_path))

    stats["meta_descriptions_added"] = added
    print(f"\n  Total meta descriptions added: {added}")


# ─────────────────────────────────────────────────────────────────────────────
# ISSUE 3: Add missing Twitter card to market report page
# ─────────────────────────────────────────────────────────────────────────────

def add_twitter_card():
    """Add Twitter card meta tags to ozone-park-11416/2024/index.html if missing."""
    print("\n=== ISSUE 3: Adding missing Twitter card to market report 2024 ===")

    target = ROOT / "market-reports" / "queens" / "ozone-park-11416" / "2024" / "index.html"
    if not target.exists():
        print(f"  [WARN] File not found: {target.relative_to(ROOT)}")
        return

    content = read_file(target)
    if content is None:
        return

    # Check if twitter:card already exists
    if re.search(r'<meta\s+name=["\']twitter:card["\']', content, re.IGNORECASE):
        print("  [SKIP] Twitter card tags already present")
        return

    # Extract OG values for the twitter tags
    og_title_m = re.search(
        r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']*)["\']',
        content, re.IGNORECASE,
    )
    og_desc_m = re.search(
        r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']*)["\']',
        content, re.IGNORECASE,
    )
    og_url_m = re.search(
        r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']*)["\']',
        content, re.IGNORECASE,
    )

    tw_title = og_title_m.group(1) if og_title_m else (
        "Ozone Park Housing Market 2024 — Year in Review"
    )
    tw_desc = og_desc_m.group(1) if og_desc_m else (
        "Ozone Park, Queens (11416) 2024 year-in-review. "
        "Researched by Nitin Gadura — (917) 705-0132."
    )
    tw_url = og_url_m.group(1) if og_url_m else (
        "https://gadurarealestate.com/market-reports/queens/ozone-park-11416/2024/"
    )

    twitter_block = (
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{tw_title}">\n'
        f'<meta name="twitter:description" content="{tw_desc}">\n'
        '<meta name="twitter:image" content="https://gadurarealestate.com/images/logo-full.png">\n'
        f'<meta name="twitter:url" content="{tw_url}">'
    )

    # Insert after the last OG meta tag block (find the last og: line)
    og_positions = [m.end() for m in re.finditer(
        r'<meta\s+property=["\']og:[^"\']*["\'][^>]*>', content
    )]
    # Also consider article: meta tags
    article_positions = [m.end() for m in re.finditer(
        r'<meta\s+property=["\']article:[^"\']*["\'][^>]*>', content
    )]

    all_positions = og_positions + article_positions
    if all_positions:
        insert_pos = max(all_positions)
        new_content = content[:insert_pos] + "\n" + twitter_block + content[insert_pos:]
    else:
        # Fallback: insert before </head>
        head_close = content.find("</head>")
        if head_close == -1:
            print("  [WARN] No </head> found")
            return
        new_content = content[:head_close] + twitter_block + "\n" + content[head_close:]

    if new_content != content:
        if write_file(target, new_content):
            print(f"  Added Twitter card tags to {target.relative_to(ROOT)}")
            stats["twitter_cards_added"] = 1
            modified_files.add(str(target))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  fix_all_broken_links_v2.py")
    print("  Gadura Real Estate — HTML bulk fixer")
    print("=" * 70)

    fix_broken_links()
    add_meta_descriptions()
    add_twitter_card()

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Files scanned (Issue 1):      {stats['files_scanned']}")
    print(f"  Total files modified:         {len(modified_files)}")
    print(f"  Broken links fixed:           {stats['links_fixed']}")
    print(f"  Meta descriptions added:      {stats['meta_descriptions_added']}")
    print(f"  Twitter cards added:          {stats['twitter_cards_added']}")
    print("=" * 70)

    # List all modified files
    if modified_files:
        print("\n  Modified files:")
        for f in sorted(modified_files):
            print(f"    {Path(f).relative_to(ROOT)}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
