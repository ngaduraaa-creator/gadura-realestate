#!/usr/bin/env python3
"""
freshen_pages.py — Update lastmod dates on top-priority pages and refresh
the "as of" date stamp inside the body. Used to feed Grok's freshness signal.

Run weekly (cron / launchd):
    0 9 * * MON  cd ~/Jagex/gadura-realestate && python3 scripts/freshen_pages.py --apply && python3 scripts/indexnow_ping.py

What it does:
1. Updates `<lastmod>` in sitemap.xml to today for the high-priority pages.
2. Updates an HTML data-attribute `<body data-last-reviewed="YYYY-MM-DD">` on those pages
   so AI engines that read body text see freshness, not just sitemap.

This is NOT spam — only run after you've done some real update (added a market
report, refreshed a neighborhood blurb, added a new listing). The script only
stamps freshness; you still need to make the substantive change.
"""
import argparse
import datetime as dt
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pages that should be touched weekly to maintain Grok freshness signal.
WEEKLY_FRESH = [
    "index.html",
    "buy.html",
    "sell.html",
    "about.html",
    "contact.html",
    "neighborhoods.html",
    "agents.html",
    "meet-the-agents.html",
    "reviews.html",
    "nitin-gadura/index.html",
    "neighborhoods/index.html",
    "community/index.html",
    "community/indian-community.html",
    "community/guyanese-community.html",
    "community/bengali-community.html",
    "hindi-speaking-real-estate-agent-queens.html",
    "punjabi-speaking-real-estate-agent-queens.html",
    "1031-exchange-queens.html",
    "coop-board-package-help-queens.html",
]

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)
URL_OF = lambda rel: f"https://gadurarealestate.com/{rel}".replace("/index.html", "/")
TODAY = dt.date.today().isoformat()


def stamp_html(p: Path) -> bool:
    if not p.exists():
        return False
    html = p.read_text(encoding="utf-8")
    # Insert/update data-last-reviewed on <body>
    new = re.sub(
        r'<body([^>]*?)\s*data-last-reviewed="[^"]*"',
        rf'<body\1',
        html,
    )
    new = re.sub(
        r"<body([^>]*)>",
        rf'<body\1 data-last-reviewed="{TODAY}">',
        new,
        count=1,
    )
    if new != html:
        p.write_text(new, encoding="utf-8")
        return True
    return False


def stamp_sitemap(target_urls: set[str]) -> int:
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        return 0
    tree = ET.parse(sm)
    root = tree.getroot()
    updated = 0
    for url_node in root.findall(f"{{{NS}}}url"):
        loc = url_node.findtext(f"{{{NS}}}loc", default="").strip()
        if loc in target_urls or loc.rstrip("/") + "/" in target_urls:
            lm = url_node.find(f"{{{NS}}}lastmod")
            if lm is None:
                lm = ET.SubElement(url_node, f"{{{NS}}}lastmod")
            lm.text = TODAY
            updated += 1
    tree.write(sm, encoding="utf-8", xml_declaration=True)
    return updated


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not args.apply:
        print("DRY-RUN — would touch:")
        for rel in WEEKLY_FRESH:
            print(f"  {rel}")
        return 0

    targets = {URL_OF(rel) for rel in WEEKLY_FRESH}
    sitemap_n = stamp_sitemap(targets)
    html_n = sum(1 for rel in WEEKLY_FRESH if stamp_html(ROOT / rel))
    print(f"sitemap entries refreshed: {sitemap_n}")
    print(f"body data-last-reviewed updated: {html_n}")
    print(f"\nNext: run `python3 scripts/indexnow_ping.py` to ping Bing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
