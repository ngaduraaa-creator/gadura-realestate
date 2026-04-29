#!/usr/bin/env python3
"""
audit_image_alts.py — Find <img> tags missing alt text and bulk-fix.

Strategy:
- Detect alt-less <img> tags
- Auto-generate descriptive alt based on src filename + page context
- Fix in place

Why: Image alt text is one of the strongest SEO signals for image search +
accessibility. Empty alts are an SEO + WCAG violation.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IMG_RE = re.compile(r'<img\s+([^>]*?)/?>', re.IGNORECASE)
ALT_RE = re.compile(r'\salt\s*=', re.IGNORECASE)
SRC_RE = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


def derive_alt(src: str, page_title: str, h1: str) -> str:
    fname = src.split("/")[-1].rsplit(".", 1)[0]
    fname = re.sub(r"[-_]+", " ", fname).strip().title()
    # Defaults for known pictures
    LOOKUP = {
        "Nitin-Gadura-Headshot": "Nitin Gadura, Licensed NYS Real Estate Salesperson",
        "Logo-Full": "Gadura Real Estate, LLC logo",
        "Logo-Icon": "Gadura Real Estate icon",
        "Logo-Text": "Gadura Real Estate wordmark",
        "Gaurav-Bhardwaj-Headshot": "Gaurav Bhardwaj, Real Estate Agent at Gadura Real Estate",
    }
    if fname in LOOKUP:
        return LOOKUP[fname]
    # Page-context aware
    page_clean = re.sub(r"<[^>]+>", "", h1 or page_title or "").strip()
    if fname and page_clean:
        return f"{fname} — {page_clean[:80]}"
    return fname or "Gadura Real Estate"


def fix_html(html: str) -> tuple[str, int, int]:
    title_m = TITLE_RE.search(html)
    h1_m = H1_RE.search(html)
    page_title = title_m.group(1).strip() if title_m else ""
    h1 = h1_m.group(1).strip() if h1_m else ""

    fixed = 0
    skipped = 0

    def repl(match):
        nonlocal fixed, skipped
        attrs = match.group(1)
        if ALT_RE.search(attrs):
            skipped += 1
            return match.group(0)
        src_m = SRC_RE.search(attrs)
        if not src_m:
            skipped += 1
            return match.group(0)
        alt = derive_alt(src_m.group(1), page_title, h1)
        # Escape quotes for HTML attribute safety
        alt = alt.replace('"', "&quot;")
        new_attrs = attrs.rstrip() + f' alt="{alt}"'
        fixed += 1
        return f"<img {new_attrs}>"

    new_html = IMG_RE.sub(repl, html)
    return new_html, fixed, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total_fixed = 0
    total_skipped = 0
    files_touched = 0
    for p in ROOT.rglob("*.html"):
        if any(part in {".git", ".github", "_includes", "scripts", "_site", ".netlify"} for part in p.relative_to(ROOT).parts):
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new_html, fixed, skipped = fix_html(html)
        total_fixed += fixed
        total_skipped += skipped
        if fixed and args.apply and new_html != html:
            p.write_text(new_html, encoding="utf-8")
            files_touched += 1
    print(f"  alt added:   {total_fixed}")
    print(f"  alt present: {total_skipped}")
    print(f"  files touched: {files_touched}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
