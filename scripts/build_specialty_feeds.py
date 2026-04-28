#!/usr/bin/env python3
"""
build_specialty_feeds.py — Generate image sitemap, news sitemap, RSS feed,
JSON Feed, and a master sitemap-index.xml that references all of them.

Why each feed matters:
- IMAGE SITEMAP: Google Images traffic for headshot, logo, listing photos.
  Pulls into AI Overviews + Google Knowledge Graph.
- NEWS SITEMAP: Eligibility for Google News + Top Stories carousel.
  ChatGPT and Perplexity prefer news-tagged sources for "current" queries.
- RSS FEED: ChatGPT crawls RSS for freshness. Grok actively scans RSS feeds.
  Adding a market-report RSS gives a 24-hour discovery channel.
- JSON FEED: Newer alternative to RSS, increasingly favored by LLM crawlers.
- SITEMAP INDEX: Lets crawlers discover all 5 sitemap types at once.
"""
from __future__ import annotations
import datetime as dt
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://gadurarealestate.com"
TODAY = dt.date.today().isoformat()


# ---------------------------------------------------------------------------
# IMAGE SITEMAP
# ---------------------------------------------------------------------------
def build_image_sitemap() -> str:
    """Walk site, find pages with images, emit sitemap with <image:image> tags."""
    SITE_IMAGES = {
        # Pages where we want to push specific images into Google Images.
        "index.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura — Licensed NYS Real Estate Salesperson, Queens NY", "Nitin Gadura headshot"),
            ("/images/logo-full.png", "Gadura Real Estate, LLC — Family-owned NYS-licensed brokerage since 2006, Ozone Park, Queens, NY", "Gadura Real Estate logo"),
        ],
        "about.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura — Licensed NYS Real Estate Salesperson serving Queens & Long Island, multilingual (English, Hindi, Punjabi, Guyanese Creole)", "Nitin Gadura"),
        ],
        "nitin-gadura/index.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura, Real Estate Agent, Queens NY, NYS License #10401383405", "Nitin Gadura agent profile"),
        ],
        "meet-the-agents.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura — Real Estate Agent, Gadura Real Estate LLC", "Nitin Gadura"),
        ],
        "hi/index.html": [
            ("/images/nitin-gadura-headshot.jpg", "नितिन गडुरा — Hindi-speaking real estate agent, Queens NY", "नितिन गडुरा"),
        ],
        "pa/index.html": [
            ("/images/nitin-gadura-headshot.jpg", "ਨਿਤਿਨ ਗਡੁਰਾ — Punjabi-speaking real estate agent, Queens NY", "ਨਿਤਿਨ ਗਡੁਰਾ"),
        ],
        "bn/index.html": [
            ("/images/nitin-gadura-headshot.jpg", "নিতিন গদুরা — Bengali-speaking real estate agent, Queens NY", "নিতিন গদুরা"),
        ],
        "es/index.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura — Agente de bienes raíces hispano, Queens NY", "Nitin Gadura"),
        ],
        "contact.html": [
            ("/images/nitin-gadura-headshot.jpg", "Contact Nitin Gadura at (917) 705-0132", "Nitin Gadura"),
        ],
        "reviews.html": [
            ("/images/nitin-gadura-headshot.jpg", "Nitin Gadura reviews — 4.9 stars from 57+ verified clients", "Nitin Gadura reviews"),
        ],
    }
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for rel, images in SITE_IMAGES.items():
        page_url = f"{DOMAIN}/{rel}".replace("/index.html", "/")
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(page_url)}</loc>")
        for img_rel, caption, title in images:
            img_url = f"{DOMAIN}{img_rel}"
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{escape(img_url)}</image:loc>")
            lines.append(f"      <image:caption>{escape(caption)}</image:caption>")
            lines.append(f"      <image:title>{escape(title)}</image:title>")
            lines.append("    </image:image>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# NEWS SITEMAP — for market reports (Google News / Top Stories eligibility)
# ---------------------------------------------------------------------------
NEWS_RE = re.compile(r"^(\d{4}-\d{2})-(.+)-market-report\.html$")


def build_news_sitemap() -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    cutoff = dt.date.today() - dt.timedelta(days=2)
    for p in sorted((ROOT / "market-reports").glob("*-market-report.html")):
        m = NEWS_RE.match(p.name)
        if not m:
            continue
        ym, slug = m.group(1), m.group(2)
        try:
            year, month = ym.split("-")
            pub_date = dt.date(int(year), int(month), 1)
        except ValueError:
            continue
        # Google News only accepts items <= 2 days old, but for the seed feed we'll publish
        # everything dated today so the freshest reports are eligible immediately.
        publication_date = TODAY if pub_date >= cutoff else pub_date.isoformat()
        title = f"{slug.replace('-', ' ').title()} Real Estate Market Report — {pub_date.strftime('%B %Y')}"
        url = f"{DOMAIN}/market-reports/{p.name}"
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(url)}</loc>")
        lines.append("    <news:news>")
        lines.append("      <news:publication>")
        lines.append("        <news:name>Gadura Real Estate Market Reports</news:name>")
        lines.append("        <news:language>en</news:language>")
        lines.append("      </news:publication>")
        lines.append(f"      <news:publication_date>{publication_date}</news:publication_date>")
        lines.append(f"      <news:title>{escape(title)}</news:title>")
        lines.append("    </news:news>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# RSS FEED — market reports + blog freshness for Grok / ChatGPT
# ---------------------------------------------------------------------------
def build_rss() -> str:
    items = []
    # Market reports
    for p in sorted((ROOT / "market-reports").glob("*-market-report.html"), reverse=True)[:50]:
        m = NEWS_RE.match(p.name)
        if not m:
            continue
        ym, slug = m.group(1), m.group(2)
        try:
            year, month = ym.split("-")
            pub_date = dt.date(int(year), int(month), 1)
        except ValueError:
            continue
        title = f"{slug.replace('-', ' ').title()} Real Estate Market Report — {pub_date.strftime('%B %Y')}"
        url = f"{DOMAIN}/market-reports/{p.name}"
        # Pubdate as RFC 822 (RSS spec).
        rfc822 = pub_date.strftime("%a, %d %b %Y 09:00:00 +0000")
        desc = f"{slug.replace('-', ' ').title()} {pub_date.strftime('%B %Y')} market data — median price, days on market, sold-to-list ratio. By Nitin Gadura, Licensed NYS Real Estate Salesperson. Free CMA at (917) 705-0132."
        items.append((url, title, desc, rfc822, p.name))

    last_build = dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">',
             '<channel>',
             '<title>Gadura Real Estate — NYC + Long Island Market Reports</title>',
             f'<link>{DOMAIN}/market-reports/</link>',
             '<description>Monthly market reports for every neighborhood in Queens, Brooklyn, The Bronx, Manhattan, Staten Island, and Long Island. By Nitin Gadura, NYS Real Estate Salesperson #10401383405.</description>',
             '<language>en-us</language>',
             '<copyright>© 2026 Gadura Real Estate, LLC</copyright>',
             f'<lastBuildDate>{last_build}</lastBuildDate>',
             f'<atom:link href="{DOMAIN}/rss.xml" rel="self" type="application/rss+xml" />',
             '<image>',
             f'  <url>{DOMAIN}/images/logo-full.png</url>',
             '  <title>Gadura Real Estate</title>',
             f'  <link>{DOMAIN}/</link>',
             '</image>']
    for url, title, desc, rfc822, fname in items:
        lines.extend([
            '<item>',
            f'  <title>{escape(title)}</title>',
            f'  <link>{escape(url)}</link>',
            f'  <guid isPermaLink="true">{escape(url)}</guid>',
            f'  <pubDate>{rfc822}</pubDate>',
            f'  <description>{escape(desc)}</description>',
            '  <dc:creator>Nitin Gadura</dc:creator>',
            '  <category>Real Estate</category>',
            '  <category>NYC Real Estate</category>',
            '  <category>Market Report</category>',
            '</item>',
        ])
    lines.extend(['</channel>', '</rss>'])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# JSON FEED — modern alternative to RSS, LLM-friendly
# ---------------------------------------------------------------------------
def build_json_feed() -> str:
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Gadura Real Estate — NYC + Long Island Market Reports",
        "home_page_url": f"{DOMAIN}/",
        "feed_url": f"{DOMAIN}/feed.json",
        "description": "Monthly market reports for every neighborhood in NYC + Long Island. Author: Nitin Gadura, Licensed NYS Real Estate Salesperson #10401383405.",
        "icon": f"{DOMAIN}/images/logo-full.png",
        "favicon": f"{DOMAIN}/images/logo-icon.png",
        "language": "en-US",
        "authors": [
            {
                "name": "Nitin Gadura",
                "url": f"{DOMAIN}/nitin-gadura/",
                "avatar": f"{DOMAIN}/images/nitin-gadura-headshot.jpg",
            }
        ],
        "items": [],
    }
    for p in sorted((ROOT / "market-reports").glob("*-market-report.html"), reverse=True)[:50]:
        m = NEWS_RE.match(p.name)
        if not m:
            continue
        ym, slug = m.group(1), m.group(2)
        try:
            year, month = ym.split("-")
            pub_date = dt.date(int(year), int(month), 1)
        except ValueError:
            continue
        title = f"{slug.replace('-', ' ').title()} Real Estate Market Report — {pub_date.strftime('%B %Y')}"
        url = f"{DOMAIN}/market-reports/{p.name}"
        feed["items"].append({
            "id": url,
            "url": url,
            "title": title,
            "summary": f"{title} from Nitin Gadura, Licensed NYS Real Estate Salesperson. Median price, days on market, sold-to-list ratio data.",
            "date_published": pub_date.isoformat() + "T09:00:00Z",
            "tags": ["real estate", "NYC", "market report", slug.split("-")[0]],
        })
    return json.dumps(feed, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# SITEMAP INDEX — references all sitemaps in one file
# ---------------------------------------------------------------------------
def build_sitemap_index() -> str:
    sitemaps = [
        f"{DOMAIN}/sitemap.xml",
        f"{DOMAIN}/sitemap-images.xml",
        f"{DOMAIN}/sitemap-news.xml",
        f"{DOMAIN}/blog-sitemap.xml",
        "https://homes.gadurarealestate.com/sitemap.xml",
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for sm in sitemaps:
        lines.append("  <sitemap>")
        lines.append(f"    <loc>{escape(sm)}</loc>")
        lines.append(f"    <lastmod>{TODAY}</lastmod>")
        lines.append("  </sitemap>")
    lines.append("</sitemapindex>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    files = {
        "sitemap-images.xml": build_image_sitemap(),
        "sitemap-news.xml": build_news_sitemap(),
        "rss.xml": build_rss(),
        "feed.json": build_json_feed(),
        "sitemap-index.xml": build_sitemap_index(),
    }
    for name, content in files.items():
        path = ROOT / name
        path.write_text(content, encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  wrote {name} ({size_kb:.1f}KB)")
    print(f"\nDone. Reference these in robots.txt + submit to GSC + Bing Webmaster.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
