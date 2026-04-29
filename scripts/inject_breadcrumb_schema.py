#!/usr/bin/env python3
"""
inject_breadcrumb_schema.py — Auto-generate BreadcrumbList JSON-LD for every
page based on its path. Critical for Google SERP appearance — Google displays
breadcrumb trails directly in search results and uses them to disambiguate
similar pages.

Marker: id="ai-breadcrumb-schema". Idempotent.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://gadurarealestate.com"
MARKER_ID = "ai-breadcrumb-schema"

SCRIPT_RE = re.compile(
    rf'<script type="application/ld\+json" id="{MARKER_ID}">.*?</script>\s*',
    re.DOTALL | re.IGNORECASE,
)

# Path segment → human-readable label for the breadcrumb trail.
SEGMENT_LABELS = {
    "neighborhoods": "Neighborhoods",
    "long-island": "Long Island",
    "nassau": "Nassau County",
    "suffolk": "Suffolk County",
    "queens": "Queens",
    "brooklyn": "Brooklyn",
    "manhattan": "Manhattan",
    "bronx": "The Bronx",
    "staten-island": "Staten Island",
    "zip": "ZIP Code",
    "community": "Community",
    "agents": "Agents",
    "services": "Services",
    "market-reports": "Market Reports",
    "blog": "Blog",
    "faq": "FAQ",
    "first-time-homebuyer": "First-Time Homebuyer Guide",
    "multi-family-investment": "Multi-Family Investment",
    "co-op-board-help": "Co-op Board Package Help",
    "1031-exchange": "1031 Exchange",
    "fha-loans-nyc": "FHA Loans NYC",
    "calculators": "Calculators",
    "glossary": "Glossary",
    "press": "Press",
    "author": "Author",
    "nitin-gadura": "Nitin Gadura",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "es": "Español",
    "pa": "ਪੰਜਾਬੀ",
}


def humanize_slug(slug: str) -> str:
    """Convert a slug to a human-readable label."""
    if slug in SEGMENT_LABELS:
        return SEGMENT_LABELS[slug]
    # Strip common suffixes
    s = slug.replace(".html", "")
    if s.endswith("-real-estate-agent-queens"):
        s = s[: -len("-real-estate-agent-queens")] + " Real Estate Agent Queens"
    elif s.endswith("-market-report"):
        # 2026-05-astoria-market-report → "Astoria Market Report"
        parts = s.split("-")
        if len(parts) >= 4 and parts[0].isdigit():
            neighborhood = "-".join(parts[2:-2]).replace("-", " ").title()
            return f"{neighborhood} Market Report"
    elif s.endswith("-queens"):
        s = s[: -len("-queens")] + " Queens"
    elif s.endswith("-nyc"):
        s = s[: -len("-nyc")] + " NYC"
    s = s.replace("-", " ").title()
    return s


def build_breadcrumbs(rel_path: str) -> list[dict]:
    """Build the breadcrumb trail as a list of (name, url) pairs."""
    parts = rel_path.split("/")
    trail = [{"name": "Home", "url": f"{DOMAIN}/"}]
    accumulated = ""
    for i, part in enumerate(parts):
        if not part or part == "index.html":
            continue
        accumulated = (accumulated + "/" + part).lstrip("/")
        url = f"{DOMAIN}/{accumulated}"
        if accumulated.endswith("/index.html"):
            url = f"{DOMAIN}/{accumulated[:-len('index.html')]}"
        # For terminal item, use the page-derived label
        if i == len(parts) - 1:
            label = humanize_slug(part)
        else:
            label = SEGMENT_LABELS.get(part, humanize_slug(part))
        trail.append({"name": label, "url": url})
    return trail


def build_schema(trail: list[dict]) -> str:
    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "name": item["name"],
            "item": item["url"],
        }
        for i, item in enumerate(trail)
    ]
    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    return (
        f'<script type="application/ld+json" id="{MARKER_ID}">\n'
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + "\n</script>"
    )


SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}
SKIP_FILES = {"404.html", "indexnow-submit.html", "idx-wrapper.html"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    counts = {"inserted": 0, "replaced": 0, "noop": 0}
    pages = list(ROOT.rglob("*.html"))
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        # Skip homepage (no breadcrumb needed; root of trail)
        if rel == "index.html":
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "</head>" not in html:
            counts["noop"] += 1
            continue
        trail = build_breadcrumbs(rel)
        block = build_schema(trail)
        if MARKER_ID in html:
            new_html, n = SCRIPT_RE.subn(block + "\n", html, count=1)
            counts["replaced"] += 1 if n else 0
        else:
            new_html = html.replace("</head>", f"{block}\n</head>", 1)
            counts["inserted"] += 1
        if args.apply and new_html != html:
            p.write_text(new_html, encoding="utf-8")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
