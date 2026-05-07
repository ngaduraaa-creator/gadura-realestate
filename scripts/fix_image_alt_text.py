#!/usr/bin/env python3
"""
fix_image_alt_text.py — Audit and bulk-fix missing/empty alt attributes on <img>.

For each <img> without alt:
- Derive a descriptive alt from the filename + page H1 + page context
- Skip pure decorative images (where role="presentation" or aria-hidden="true")

Idempotent. Conservative — never overwrites existing alt text.

Output: ai-monitoring/alt-audit-<date>.csv
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}

IMG_RE = re.compile(r"<img\s([^>]*?)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*["\']([^"\']*)["\']')
TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)
H1_RE = re.compile(r"<h1[^>]*>(.+?)</h1>", re.IGNORECASE | re.DOTALL)


def parse_attrs(attrs_str: str) -> dict:
    return {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(attrs_str)}


def derive_alt(src: str, page_title: str, page_h1: str) -> str:
    """Derive a useful alt from image filename + page context."""
    # Extract filename
    fname = src.split("/")[-1]
    fname = fname.split("?")[0]
    base = fname.rsplit(".", 1)[0]
    # Convert hyphens / underscores to spaces, title-case
    parts = base.replace("_", "-").split("-")
    label = " ".join(p for p in parts if p and not p.isdigit())
    label = label.strip()

    # Specific filename matchers
    if "headshot" in src.lower() or "nitin-gadura" in src.lower():
        return "Nitin Gadura, Licensed NYS Real Estate Salesperson"
    if "logo" in src.lower():
        return "Gadura Real Estate, LLC logo"
    if "gaurav" in src.lower():
        return "Gaurav Bhardwaj, PSA Certified Real Estate Salesperson at Gadura Real Estate"
    if "vinod" in src.lower():
        return "Vinod K. Gadura, founder and supervising broker of Gadura Real Estate, LLC"
    if "thumb" in src.lower() and "video" in src.lower():
        return f"Video thumbnail — {page_h1 or page_title}"

    # Real estate listings
    if any(w in src.lower() for w in ["listing", "house", "home", "property"]):
        if page_h1:
            return f"Listing photo — {page_h1.strip()}"
        return f"Real estate listing photo — {label or 'NYC property'}"

    # Neighborhood images
    if "neighborhood" in src.lower() or "ozone" in src.lower() or "queens" in src.lower():
        return f"{label or 'Neighborhood'} photo — Gadura Real Estate"

    # Generic fallback
    if label:
        return f"{label} — {page_title.split('|')[0].strip() if '|' in page_title else page_title}"[:120]
    return f"Image on {page_title.split('|')[0].strip() if '|' in page_title else 'Gadura Real Estate'}"[:120]


def fix_page(html: str) -> tuple[str, int, list[dict]]:
    """Returns (new_html, count_fixed, list_of_records)."""
    title_m = TITLE_RE.search(html)
    page_title = title_m.group(1).strip() if title_m else ""
    h1_m = H1_RE.search(html)
    page_h1 = re.sub(r"<[^>]+>", "", h1_m.group(1)).strip() if h1_m else ""

    records = []
    fixed = 0

    def replace_img(match):
        nonlocal fixed
        attrs_str = match.group(1)
        attrs = parse_attrs(attrs_str)
        # Skip if alt already exists (even empty alt="" is intentional decorative)
        if "alt" in attrs:
            return match.group(0)
        # Skip explicit decorative
        if attrs.get("role") == "presentation" or attrs.get("aria-hidden") == "true":
            return match.group(0)
        src = attrs.get("src", "")
        if not src:
            return match.group(0)
        # Derive alt
        alt = derive_alt(src, page_title, page_h1)
        # Escape quotes
        alt = alt.replace('"', "&quot;")
        # Insert alt at the end of attrs
        new_attrs = attrs_str.rstrip() + f' alt="{alt}"'
        records.append({"src": src, "derived_alt": alt})
        fixed += 1
        return f"<img {new_attrs}>"

    new_html = IMG_RE.sub(replace_img, html)
    return new_html, fixed, records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    out_dir = ROOT / "ai-monitoring"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / f"alt-audit-{dt.date.today().isoformat()}.csv"

    counts = {"files_scanned": 0, "files_modified": 0, "alts_added": 0}
    rows = []

    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name == "404.html":
            continue
        counts["files_scanned"] += 1
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new_html, fixed, records = fix_page(html)
        if fixed > 0:
            counts["files_modified"] += 1
            counts["alts_added"] += fixed
            rel = p.relative_to(ROOT).as_posix()
            for r in records:
                rows.append({"file": rel, **r})
            if args.apply:
                p.write_text(new_html, encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "src", "derived_alt"])
        writer.writeheader()
        writer.writerows(rows)

    print("=== Image Alt-Text Audit ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"  Report: {csv_path.relative_to(ROOT)}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
