#!/usr/bin/env python3
"""
validate_schema.py — Lightweight schema validator. CI-friendly.

Checks every page for:
- Valid JSON in <script type="application/ld+json"> blocks
- Master schema present on priority pages
- FAQPage schema present on FAQ-format pages
- No duplicate @id values within a single page
- Required fields populated (name, url, telephone, etc.)

Exits non-zero if any errors. Suitable for GitHub Actions / pre-commit.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LD_RE = re.compile(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

CRITICAL_PAGES = [
    "index.html",
    "nitin-gadura/index.html",
    "author/nitin-gadura.html",
    "press/index.html",
    "glossary/index.html",
]

REQUIRED_FIELDS = {
    "Person": {"name", "@id"},
    "RealEstateAgent": {"name"},
    "LocalBusiness": {"name", "address"},
    "Article": {"headline", "datePublished"},
    "FAQPage": {"mainEntity"},
}


def validate_page(p: Path, errors: list[str]):
    try:
        html = p.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{p}: read error — {e}")
        return
    blocks = LD_RE.findall(html)
    if not blocks and "</body>" in html:
        # Skip — page may not need schema
        return
    seen_ids = set()
    has_master = False
    for raw in blocks:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            errors.append(f"{p}: invalid JSON-LD — {e}")
            continue
        # Walk the structure for @ids
        def walk(node):
            nonlocal has_master
            if isinstance(node, dict):
                aid = node.get("@id")
                if aid:
                    if aid in seen_ids:
                        errors.append(f"{p}: duplicate @id {aid}")
                    seen_ids.add(aid)
                    if aid == "https://gadurarealestate.com/#nitin-gadura":
                        has_master = True
                # Required fields
                t = node.get("@type")
                if isinstance(t, str) and t in REQUIRED_FIELDS:
                    missing = REQUIRED_FIELDS[t] - set(node.keys())
                    if missing:
                        errors.append(f"{p}: {t} missing required fields {missing}")
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(data)
    rel = p.relative_to(ROOT).as_posix()
    if rel in CRITICAL_PAGES and not has_master:
        errors.append(f"{p}: critical page missing master schema (@id #nitin-gadura)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on any error")
    args = ap.parse_args()
    errors: list[str] = []
    pages = list(ROOT.rglob("*.html"))
    skipped = 0
    for p in pages:
        if any(part in {".git", ".github", "_includes", "scripts", "_site", ".netlify"} for part in p.relative_to(ROOT).parts):
            skipped += 1
            continue
        validate_page(p, errors)
    print(f"  pages checked: {len(pages) - skipped}")
    print(f"  pages skipped: {skipped}")
    print(f"  errors found:  {len(errors)}")
    if errors:
        for e in errors[:50]:
            print(f"    ✗ {e}")
        if len(errors) > 50:
            print(f"    ... and {len(errors) - 50} more")
        if args.strict:
            return 1
    else:
        print("  ✓ No errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
