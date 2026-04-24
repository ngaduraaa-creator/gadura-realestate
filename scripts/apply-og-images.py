#!/usr/bin/env python3
"""Rewrite og:image and twitter:image meta tags for a curated set of pages.

Maps page paths to a slug under /images/og/<slug>.png. Leaves all other pages
alone (they'll continue to use the existing logo fallback).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAPPING: dict[str, str] = {
    "index.html": "home",
    "buy.html": "buy",
    "sell.html": "sell",
    "blog/index.html": "blog",
    "market-reports/index.html": "market-reports",
    "neighborhoods.html": "neighborhoods",
    "agents/nitin-gadura.html": "about-nitin",
    "listings/index.html": "listings",
    "past-sales/index.html": "past-sales",
    "open-houses/index.html": "open-houses",
    "hindi-speaking-real-estate-agent-queens.html": "hindi-agent",
    "punjabi-speaking-real-estate-agent-queens.html": "punjabi-agent",
    "contact.html": "contact",
    "blog/astoria-vs-sunnyside-queens.html": "astoria-vs-sunnyside",
    "blog/queens-commuter-neighborhoods.html": "queens-commuter",
    "blog/forest-hills-vs-rego-park.html": "forest-hills-vs-rego-park",
    "blog/first-time-home-buyer-queens-ny.html": "first-time-buyer",
    "closing-costs-nyc-guide.html": "closing-costs",
    "blog/nyc-mansion-tax-explained.html": "mansion-tax",
}

OG_IMG_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\'][^"\']*["\']\s*/?>',
    re.IGNORECASE,
)
TW_IMG_RE = re.compile(
    r'<meta\s+name=["\']twitter:image["\']\s+content=["\'][^"\']*["\']\s*/?>',
    re.IGNORECASE,
)
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)


def apply(path: Path, slug: str) -> str:
    url = f"https://gadurarealestate.com/images/og/{slug}.png"
    og = f'<meta property="og:image" content="{url}">'
    og_alt = '<meta property="og:image:alt" content="Gadura Real Estate — Queens · Brooklyn · Long Island">'
    og_w = '<meta property="og:image:width" content="1200">'
    og_h = '<meta property="og:image:height" content="630">'
    tw = f'<meta name="twitter:image" content="{url}">'

    text = path.read_text(encoding="utf-8")
    original = text

    if OG_IMG_RE.search(text):
        text = OG_IMG_RE.sub(og, text, count=1)
        changed = "replaced og:image"
    else:
        text = HEAD_END_RE.sub(f"  {og}\n</head>", text, count=1)
        changed = "inserted og:image"

    if TW_IMG_RE.search(text):
        text = TW_IMG_RE.sub(tw, text, count=1)
    else:
        text = HEAD_END_RE.sub(f"  {tw}\n</head>", text, count=1)

    if "og:image:width" not in text:
        text = HEAD_END_RE.sub(f"  {og_w}\n  {og_h}\n  {og_alt}\n</head>", text, count=1)

    if text == original:
        return "no change"
    path.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    updated = 0
    missing = []
    for rel, slug in MAPPING.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
            continue
        result = apply(p, slug)
        print(f"  {rel} -> og/{slug}.png ({result})")
        updated += 1
    if missing:
        print(f"\nMissing files (skipped): {missing}")
    print(f"\nUpdated {updated} pages.")


if __name__ == "__main__":
    main()
