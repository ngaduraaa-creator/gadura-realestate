#!/usr/bin/env python3
"""
fix_seo_sitemaps.py — one authoritative pass that repairs every sitemap problem
surfaced in the 2026-08 SEO audit:

  1. Re-include the 92 /homes/*/ property pages in sitemap.xml (regression: they
     existed on disk but sitemap.xml had never been regenerated after they landed).
  2. Rebuild sitemap-listings.xml from the real homes/*/ dirs (was empty).
  3. Give every URL a real per-file <lastmod> from its git last-commit date
     (was a single hand-stamped bulk date Google learns to distrust).
  4. Rebuild sitemap-index.xml so it lists ALL first-party child sitemaps that
     actually exist, each with its own real mtime (was 5 stale children).
  5. Prune any <loc> in the child sitemaps whose local file no longer exists
     (kills the 23 dead 2026-05 market-report 404s in sitemap-faq.xml, etc.).

Static-site safe: pure stdlib, no build system. Run from repo root or anywhere:
    python3 scripts/fix_seo_sitemaps.py           # apply
    python3 scripts/fix_seo_sitemaps.py --dry-run # report only
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://gadurarealestate.com"
TODAY = dt.date.today().isoformat()
DRY = "--dry-run" in sys.argv

EXCLUDE_DIRS = {
    ".git", ".github", ".netlify", ".claude",
    "_includes", "scripts", "admin", "data", "research",
    "v2", "docs", "ai-citations", "ai-monitoring",
}
EXCLUDE_FILES = {
    "404.html", "indexnow-submit.html", "idx-wrapper.html", "idx-policy.html",
    "ozone-park-homes.html", "portal.html", "map-sold.html",
}
NOINDEX_PATHS = {
    "neighborhoods/brooklyn/index.html", "portfolio/index.html", "privacy.html",
}

# Child sitemaps we manage. Special-format feeds (news/images) are left to their
# own generators; here we only prune dead <loc>s from the plain page feeds and
# rebuild the two we own outright (listings + the master sitemap.xml).
PRUNE_FEEDS = ["sitemap-faq.xml", "sitemap-buyer.xml", "blog-sitemap.xml"]


def rel_of(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def url_for(rel: str) -> str:
    if rel == "index.html":
        return f"{DOMAIN}/"
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    return f"{DOMAIN}/{rel}"


def file_for(loc: str) -> Path | None:
    """Map a sitemap <loc> back to a local file for existence checks."""
    if not loc.startswith(DOMAIN):
        return None  # cross-host (homes. subdomain) — not ours to check
    path = loc[len(DOMAIN):].split("?")[0].split("#")[0]
    if path in ("", "/"):
        return ROOT / "index.html"
    path = path.lstrip("/")
    if path.endswith("/"):
        return ROOT / path / "index.html"
    return ROOT / path


def priority_for(rel: str) -> tuple[float, str]:
    if rel == "index.html":
        return 1.0, "daily"
    if rel.startswith("nitin-gadura/"):
        return 0.95, "weekly"
    if rel in {"buy.html", "sell.html", "neighborhoods.html", "agents.html",
               "meet-the-agents.html", "contact.html", "about.html", "reviews.html",
               "home-valuation.html"}:
        return 0.9, "weekly"
    if rel.startswith("homes/"):
        return 0.8, "weekly"
    if rel.startswith("homes-for-sale/"):
        return 0.85, "weekly"
    if rel.startswith("neighborhoods/") or rel.startswith("long-island/"):
        return 0.8, "weekly"
    if rel.startswith("community/"):
        return 0.85, "weekly"
    if rel.startswith("zip/"):
        return 0.7, "monthly"
    if rel.startswith("market-reports/"):
        return 0.7, "weekly"
    if rel.startswith("rentals/"):
        return 0.8, "weekly"
    if rel.startswith("blog/"):
        return 0.6, "weekly"
    if rel.startswith(("services/", "home-value/", "agents/")):
        return 0.7, "monthly"
    return 0.5, "monthly"


def git_last_dates() -> dict[str, str]:
    """One pass over git history → {relpath: YYYY-MM-DD of last commit}."""
    dates: dict[str, str] = {}
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--format=%x01%cs", "--name-only"],
            capture_output=True, text=True, check=True,
        ).stdout
    except Exception:
        return dates
    cur = TODAY
    for line in out.splitlines():
        if line.startswith("\x01"):
            cur = line[1:].strip() or TODAY
        elif line.strip():
            dates.setdefault(line.strip(), cur)  # first seen = most recent
    return dates


def lastmod_for(rel: str, dates: dict[str, str]) -> str:
    if rel in dates:
        return dates[rel]
    p = ROOT / rel
    try:
        return dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
    except Exception:
        return TODAY


def collect_pages() -> list[str]:
    out = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDE_FILES:
            continue
        if rel.as_posix() in NOINDEX_PATHS:
            continue
        out.append(rel.as_posix())
    return sorted(out)


def urlset(entries: list[tuple[str, str, float, str]]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, prio, cf in entries:
        lines += ["  <url>", f"    <loc>{escape(loc)}</loc>",
                  f"    <lastmod>{mod}</lastmod>",
                  f"    <changefreq>{cf}</changefreq>",
                  f"    <priority>{prio:.2f}</priority>", "  </url>"]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write(path: Path, content: str, label: str) -> None:
    if DRY:
        print(f"  [dry-run] would write {label}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {label}")


def prune_feed(name: str) -> None:
    """Drop <url> blocks whose <loc> file no longer exists."""
    import re
    fp = ROOT / name
    if not fp.exists():
        return
    xml = fp.read_text(encoding="utf-8")
    blocks = re.findall(r"<url>.*?</url>", xml, re.S)
    kept, dropped = [], []
    for b in blocks:
        m = re.search(r"<loc>(.*?)</loc>", b, re.S)
        if not m:
            continue
        loc = m.group(1).strip()
        f = file_for(loc)
        if f is None or f.exists():
            kept.append(b)
        else:
            dropped.append(loc)
    if dropped:
        print(f"  {name}: pruning {len(dropped)} dead URL(s) (e.g. {dropped[0]})")
        header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        body = "\n".join("  " + b.strip() for b in kept)
        write(fp, header + body + "\n</urlset>\n", name)
    else:
        print(f"  {name}: no dead URLs")


def child_lastmod(name: str, dates: dict[str, str]) -> str:
    # Use the child file's real mtime: files we just regenerated read as today,
    # untouched feeds keep their true date — accurate freshness for Google.
    p = ROOT / name
    try:
        return dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
    except Exception:
        return TODAY


def main() -> int:
    print(f"fix_seo_sitemaps ({'DRY-RUN' if DRY else 'APPLY'}) — root {ROOT}")
    dates = git_last_dates()
    print(f"git dates loaded for {len(dates)} paths")

    # 1+3. Master sitemap.xml — every indexable page, real per-file lastmod.
    pages = collect_pages()
    homes = [r for r in pages if r.startswith("homes/")]
    print(f"pages: {len(pages)} (incl. {len(homes)} /homes/ property pages)")
    entries = [(url_for(r), lastmod_for(r, dates), *priority_for(r)) for r in pages]
    write(ROOT / "sitemap.xml", urlset(entries), f"sitemap.xml ({len(entries)} URLs)")

    # 2. sitemap-listings.xml — the property catalog (all-listings hub + homes/*).
    listing_rels = []
    if (ROOT / "homes-for-sale/all-listings.html").exists():
        listing_rels.append("homes-for-sale/all-listings.html")
    listing_rels += homes
    lentries = [(url_for(r), lastmod_for(r, dates), *priority_for(r)) for r in listing_rels]
    write(ROOT / "sitemap-listings.xml", urlset(lentries),
          f"sitemap-listings.xml ({len(lentries)} URLs)")

    # 5. Prune dead URLs from the plain page feeds.
    for feed in PRUNE_FEEDS:
        prune_feed(feed)

    # 4. sitemap-index.xml — every child sitemap that actually exists, real mtime.
    candidates = [
        "sitemap.xml", "sitemap-images.xml", "sitemap-news.xml", "blog-sitemap.xml",
        "sitemap-faq.xml", "sitemap-listings.xml", "sitemap-buyer.xml",
    ]
    children = [c for c in candidates if (ROOT / c).exists()]
    ix = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for c in children:
        ix += ["  <sitemap>", f"    <loc>{DOMAIN}/{c}</loc>",
               f"    <lastmod>{child_lastmod(c, dates)}</lastmod>", "  </sitemap>"]
    ix.append("</sitemapindex>")
    write(ROOT / "sitemap-index.xml", "\n".join(ix) + "\n",
          f"sitemap-index.xml ({len(children)} children: {', '.join(children)})")

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
