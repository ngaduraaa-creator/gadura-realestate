#!/usr/bin/env python3
"""
inject_review_schema.py — add Review + AggregateRating structured data to
reviews.html, sourced from the testimonials VISIBLY displayed on the page
(Google-compliant: schema matches on-page content, honest reviewCount).

Fixes the #1 structured-data audit finding: the site had 0 aggregateRating /
Review nodes despite showing real 5-star client reviews, forfeiting AI-search
weighting and entity-graph rating signals.

Idempotent — safe to re-run. Parses the testimonial cards so the schema stays
in sync with whatever reviews are actually shown.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "reviews.html"
BROKERAGE_ID = "https://gadurarealestate.com/#brokerage"
MARK = "id=\"reviews-aggregate-schema\""


def _clean(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_reviews(t: str) -> list[dict]:
    """Extract the testimonial fields as parallel, document-ordered lists and
    zip them. Only the reviews section uses these classes, so order is 1:1."""
    quotes = [_clean(x).strip('"“”') for x in re.findall(r'class="t-quote"[^>]*>(.*?)</p>', t, re.S)]
    names = [_clean(x) for x in re.findall(r'class="t-name"[^>]*>(.*?)</div>', t, re.S)]
    metas = [_clean(x) for x in re.findall(r'class="t-meta"[^>]*>(.*?)</div>', t, re.S)]
    stars = [x.count("★") for x in re.findall(r'class="t-stars"[^>]*>(.*?)</div>', t, re.S)]
    n = min(len(quotes), len(names))
    if not (len(quotes) == len(names) == len(metas)):
        print(f"WARN: field counts differ (q={len(quotes)} n={len(names)} m={len(metas)}) — zipping {n}")
    reviews = []
    for i in range(n):
        m = re.search(r"([A-Za-z.]+(?:\.com)?)\s*Review", metas[i] if i < len(metas) else "")
        rating = 5 if (i < len(stars) and stars[i] >= 5) else (stars[i] if i < len(stars) and stars[i] else 5)
        reviews.append({
            "author": names[i],
            "body": quotes[i],
            "rating": rating,
            "source": m.group(1) if m else "",
        })
    return reviews


def build_graph(reviews: list[dict]) -> dict:
    count = len(reviews)
    avg = round(sum(r["rating"] for r in reviews) / count, 1) if count else 5.0
    review_nodes = []
    for r in reviews:
        node = {
            "@type": "Review",
            "itemReviewed": {"@id": BROKERAGE_ID},
            "author": {"@type": "Person", "name": r["author"]},
            "reviewRating": {"@type": "Rating", "ratingValue": str(r["rating"]),
                             "bestRating": "5", "worstRating": "1"},
            "reviewBody": r["body"],
        }
        if r["source"]:
            node["publisher"] = {"@type": "Organization", "name": r["source"]}
        review_nodes.append(node)
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "RealEstateAgent",
                "@id": BROKERAGE_ID,
                "name": "Gadura Real Estate LLC",
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": f"{avg:.1f}",
                    "reviewCount": str(count),
                    "bestRating": "5",
                    "worstRating": "1",
                },
            },
            *review_nodes,
        ],
    }


def visible_summary(reviews: list[dict]) -> str:
    count = len(reviews)
    avg = round(sum(r["rating"] for r in reviews) / count, 1) if count else 5.0
    return (
        '<div id="reviews-rating-summary" style="text-align:center;margin:0 auto 1.5rem;'
        'display:inline-flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:.5rem;'
        'padding:.6rem 1.2rem;border:1px solid rgba(11,34,64,.12);border-radius:999px;'
        'font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;font-size:.95rem;color:#1b2a6b;">'
        '<span style="color:#e0a800;letter-spacing:2px;font-size:1.05rem;">★★★★★</span>'
        f'<strong>{avg:.1f}</strong>'
        f'<span style="color:#5b6675;">· {count} featured five-star client reviews</span>'
        '</div>'
    )


def main() -> int:
    t = PAGE.read_text(encoding="utf-8")
    reviews = parse_reviews(t)
    if not reviews:
        print("No testimonials parsed — aborting (no fabricated reviews).")
        return 1
    print(f"Parsed {len(reviews)} visible reviews: {[r['author'] for r in reviews]}")

    if MARK in t:
        # remove the old block so we can re-emit in sync
        t = re.sub(r'<script type="application/ld\+json" ' + MARK + r'>.*?</script>\n?',
                   "", t, flags=re.S)

    graph = build_graph(reviews)
    jsonld = ('<script type="application/ld+json" ' + MARK + '>'
              + json.dumps(graph, ensure_ascii=False) + '</script>')

    # 1) visible summary: insert right before the testimonials-grid (once)
    if 'id="reviews-rating-summary"' not in t:
        t = t.replace('<div class="testimonials-grid">',
                      visible_summary(reviews) + '\n    <div class="testimonials-grid">', 1)

    # 2) JSON-LD: insert just before </body>
    t = t.replace("</body>", jsonld + "\n</body>", 1)

    PAGE.write_text(t, encoding="utf-8")
    avg = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    print(f"Injected AggregateRating {avg:.1f}/5 from {len(reviews)} reviews + {len(reviews)} Review nodes on #brokerage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
