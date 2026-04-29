#!/usr/bin/env python3
"""
bulk_og_injector.py — Add proper Open Graph + Twitter Card tags to every page
that's missing them, with PER-PAGE-TYPE images (not just the logo).

OG image strategy:
- Neighborhood pages → /images/og/neighborhood-default.jpg (or specific if exists)
- Market reports → /images/og/market-report-default.jpg
- Author / press / glossary → /images/nitin-gadura-headshot.jpg
- Topical hubs → /images/og/topical-default.jpg
- Language landing pages → /images/og/multilingual.jpg
- Default fallback → /images/nitin-gadura-headshot.jpg (better than logo)

Idempotent. Only adds tags that are missing — does not overwrite existing ones.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://gadurarealestate.com"
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}
SKIP_FILES = {"404.html", "indexnow-submit.html", "idx-wrapper.html"}

# Defaults per page type
HEADSHOT = f"{DOMAIN}/images/nitin-gadura-headshot.jpg"
LOGO = f"{DOMAIN}/images/logo-full.png"

OG_IMAGE_RULES = [
    # (path-prefix, image-url)
    ("neighborhoods/manhattan/", f"{DOMAIN}/images/og/manhattan.jpg"),
    ("neighborhoods/brooklyn/", f"{DOMAIN}/images/og/brooklyn.jpg"),
    ("neighborhoods/queens/", f"{DOMAIN}/images/og/queens.jpg"),
    ("neighborhoods/bronx/", f"{DOMAIN}/images/og/bronx.jpg"),
    ("neighborhoods/staten-island/", f"{DOMAIN}/images/og/staten-island.jpg"),
    ("long-island/nassau/", f"{DOMAIN}/images/og/long-island.jpg"),
    ("long-island/suffolk/", f"{DOMAIN}/images/og/long-island.jpg"),
    ("market-reports/", f"{DOMAIN}/images/og/market-report.jpg"),
    ("blog/", f"{DOMAIN}/images/og/blog.jpg"),
    ("zip/", f"{DOMAIN}/images/og/zip-code.jpg"),
    ("community/", f"{DOMAIN}/images/og/community.jpg"),
    ("first-time-homebuyer/", f"{DOMAIN}/images/og/first-time-buyer.jpg"),
    ("multi-family-investment/", f"{DOMAIN}/images/og/multi-family.jpg"),
    ("co-op-board-help/", f"{DOMAIN}/images/og/coop.jpg"),
    ("1031-exchange/", f"{DOMAIN}/images/og/1031.jpg"),
    ("fha-loans-nyc/", f"{DOMAIN}/images/og/fha.jpg"),
    ("hi/", f"{DOMAIN}/images/og/hindi.jpg"),
    ("bn/", f"{DOMAIN}/images/og/bengali.jpg"),
    ("es/", f"{DOMAIN}/images/og/spanish.jpg"),
    ("pa/", f"{DOMAIN}/images/og/punjabi.jpg"),
    ("author/", HEADSHOT),
    ("press/", HEADSHOT),
    ("glossary/", HEADSHOT),
    ("nitin-gadura/", HEADSHOT),
    # Default fallback
    ("", HEADSHOT),
]


def og_image_for(rel: str) -> str:
    for prefix, image in OG_IMAGE_RULES:
        if rel.startswith(prefix):
            return image
    return HEADSHOT


TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)
META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE)
CANONICAL_RE = re.compile(r'<link\s+rel="canonical"\s+href="([^"]*)"', re.IGNORECASE)


def has_tag(html: str, name: str, prop: bool = False) -> bool:
    """Check if html has og:X or twitter:X tag."""
    attr = "property" if prop else "name"
    pattern = rf'<meta\s+{attr}="{re.escape(name)}"'
    return bool(re.search(pattern, html, re.IGNORECASE))


def inject_og_tags(html: str, rel: str) -> tuple[str, list[str]]:
    """Inject any missing OG/Twitter tags. Returns (new_html, list_of_added_tags)."""
    title_match = TITLE_RE.search(html)
    desc_match = META_DESC_RE.search(html)
    canonical_match = CANONICAL_RE.search(html)

    if not title_match:
        return html, []  # No <title>, skip

    title = title_match.group(1).strip()
    description = desc_match.group(1).strip() if desc_match else ""
    canonical = canonical_match.group(1).strip() if canonical_match else f"{DOMAIN}/{rel}".replace("/index.html", "/")
    image = og_image_for(rel)

    # Determine type
    if rel.startswith("blog/") or rel.startswith("market-reports/"):
        og_type = "article"
    elif rel.startswith("author/") or rel.startswith("nitin-gadura/"):
        og_type = "profile"
    else:
        og_type = "website"

    additions = []

    # OG tags
    if not has_tag(html, "og:title", prop=True):
        additions.append(f'<meta property="og:title" content="{title}" />')
    if description and not has_tag(html, "og:description", prop=True):
        additions.append(f'<meta property="og:description" content="{description}" />')
    if not has_tag(html, "og:type", prop=True):
        additions.append(f'<meta property="og:type" content="{og_type}" />')
    if not has_tag(html, "og:url", prop=True):
        additions.append(f'<meta property="og:url" content="{canonical}" />')
    if not has_tag(html, "og:image", prop=True):
        additions.append(f'<meta property="og:image" content="{image}" />')
    if not has_tag(html, "og:site_name", prop=True):
        additions.append('<meta property="og:site_name" content="Gadura Real Estate" />')
    if not has_tag(html, "og:locale", prop=True):
        # Map page language
        if rel.startswith("hi/"):
            locale = "hi_IN"
        elif rel.startswith("bn/"):
            locale = "bn_IN"
        elif rel.startswith("es/"):
            locale = "es_US"
        elif rel.startswith("pa/"):
            locale = "pa_IN"
        else:
            locale = "en_US"
        additions.append(f'<meta property="og:locale" content="{locale}" />')

    # Twitter cards
    if not has_tag(html, "twitter:card"):
        additions.append('<meta name="twitter:card" content="summary_large_image" />')
    if not has_tag(html, "twitter:title"):
        additions.append(f'<meta name="twitter:title" content="{title}" />')
    if description and not has_tag(html, "twitter:description"):
        additions.append(f'<meta name="twitter:description" content="{description}" />')
    if not has_tag(html, "twitter:image"):
        additions.append(f'<meta name="twitter:image" content="{image}" />')

    if not additions:
        return html, []

    block = "\n".join(additions) + "\n"

    # Insert before </head>
    if "</head>" not in html:
        return html, []

    new_html = html.replace("</head>", block + "</head>", 1)
    return new_html, additions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    total_pages = 0
    pages_updated = 0
    total_tags_added = 0
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        rel = p.relative_to(ROOT).as_posix()
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        total_pages += 1
        new_html, added = inject_og_tags(html, rel)
        if added:
            pages_updated += 1
            total_tags_added += len(added)
            if args.apply:
                p.write_text(new_html, encoding="utf-8")

    print("=== Summary ===")
    print(f"  Total HTML pages scanned: {total_pages}")
    print(f"  Pages with tags added:    {pages_updated}")
    print(f"  Total tags added:         {total_tags_added}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
