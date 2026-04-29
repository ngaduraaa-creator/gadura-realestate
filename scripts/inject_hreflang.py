#!/usr/bin/env python3
"""
inject_hreflang.py — Bulk-inject hreflang tags so multi-language pages
cross-reference each other. Critical for international SEO.

Currently only the language landing pages (/, /hi/, /bn/, /es/, /pa/) have
hreflang. This injects the same set into the homepage + every borough hub
+ every neighborhood page so Google understands the language relationships.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HREFLANG_BLOCK = '''<link rel="alternate" hreflang="en" href="https://gadurarealestate.com/">
<link rel="alternate" hreflang="hi" href="https://gadurarealestate.com/hi/">
<link rel="alternate" hreflang="pa" href="https://gadurarealestate.com/pa/">
<link rel="alternate" hreflang="bn" href="https://gadurarealestate.com/bn/">
<link rel="alternate" hreflang="es" href="https://gadurarealestate.com/es/">
<link rel="alternate" hreflang="x-default" href="https://gadurarealestate.com/">'''

MARKER = '<!-- ai-hreflang-block -->'

GLOBS = ["*.html", "**/*.html"]
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "node_modules"}
SKIP_FILES = {"404.html"}

# Language pages already have their own hreflang sets — don't override them.
LANGUAGE_DIRS = {"hi", "bn", "es", "pa"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    counts = {"inserted": 0, "already_present": 0, "skipped_lang_page": 0, "noop": 0}
    block_with_marker = MARKER + "\n" + HREFLANG_BLOCK + "\n"
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        # Skip language pages — they have their own per-page hreflang.
        rel_parts = p.relative_to(ROOT).parts
        if rel_parts and rel_parts[0] in LANGUAGE_DIRS:
            counts["skipped_lang_page"] += 1
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if MARKER in html:
            counts["already_present"] += 1
            continue
        # Skip if any <link rel="alternate" hreflang exists already (handcrafted)
        if re.search(r'rel="alternate"\s+hreflang', html):
            counts["already_present"] += 1
            continue
        if "</head>" not in html:
            counts["noop"] += 1
            continue
        new_html = html.replace("</head>", block_with_marker + "</head>", 1)
        counts["inserted"] += 1
        if args.apply:
            p.write_text(new_html, encoding="utf-8")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
