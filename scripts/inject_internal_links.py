#!/usr/bin/env python3
"""
inject_internal_links.py — Add the 14 specific internal links Ahrefs flagged as
"Internal Link Opportunities" on 2026-04-29.

Each rule: on file X, find the first occurrence of the keyword phrase that
isn't already inside an <a> tag, wrap it in a link to URL Y.

Idempotent — skips files where the link already exists.
Safe — only modifies the FIRST occurrence per page (no keyword stuffing).
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each rule: (file_path, anchor_phrase, target_url)
RULES = [
    ("for-sale/index.html",                                    "average home price in Queens NY",   "/home-value/queens-home-value.html"),
    ("for-sale.html",                                          "average home price in Queens NY",   "/home-value/queens-home-value.html"),
    ("neighborhoods/jamaica/zip-11432/index.html",             "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("neighborhoods/jamaica/zip-11433/index.html",             "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("neighborhoods/jamaica/zip-11434/index.html",             "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("neighborhoods/jamaica/zip-11435/index.html",             "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("neighborhoods/jamaica/zip-11436/index.html",             "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("neighborhoods/jamaica/faq/index.html",                   "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("queens-south/index.html",                                "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("home-value/south-jamaica-home-value.html",               "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("home-value/queens-home-value.html",                      "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("blog/queens-real-estate-market-2026.html",               "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("market-reports/queens-market-report-q1-2026.html",       "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("homes-for-sale/south-jamaica-homes.html",                "South Jamaica",                     "/neighborhoods/south-jamaica/vs-jamaica/"),
    ("senior-downsizing-queens.html",                          "Woodhaven",                         "/neighborhoods/woodhaven/lifestyle/"),
]


def inject_link(html: str, phrase: str, target: str) -> tuple[str, bool]:
    """Wrap first occurrence of phrase in a link to target.
    Skip if already inside <a> tag, or if a link to that target already exists."""
    # Already linked to this target?
    if f'href="{target}"' in html:
        return html, False
    # Find first occurrence of the phrase NOT inside an existing anchor.
    # Conservative: match the phrase, then check the surrounding 100 chars don't contain an open <a> without close.
    pattern = re.compile(r"\b" + re.escape(phrase) + r"\b")
    matches = list(pattern.finditer(html))
    for m in matches:
        start = m.start()
        # Walk backwards 200 chars; if last <a> is more recent than </a>, we're inside a link
        before = html[max(0, start - 300):start]
        last_open = before.rfind("<a ")
        last_close = before.rfind("</a>")
        if last_open > last_close:
            continue  # inside a link already
        # Skip if inside a <script> or <style> tag
        last_script_open = before.rfind("<script")
        last_script_close = before.rfind("</script>")
        if last_script_open > last_script_close:
            continue
        # Replace this single occurrence with the linked version
        new_html = (
            html[:start]
            + f'<a href="{target}">{phrase}</a>'
            + html[m.end():]
        )
        return new_html, True
    return html, False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    counts = {"applied": 0, "skipped_no_phrase": 0, "skipped_already_linked": 0, "missing_file": 0}
    for rel_path, phrase, target in RULES:
        p = ROOT / rel_path
        if not p.exists():
            counts["missing_file"] += 1
            print(f"  ⚠ missing file: {rel_path}")
            continue
        html = p.read_text(encoding="utf-8")
        if f'href="{target}"' in html:
            counts["skipped_already_linked"] += 1
            continue
        new_html, ok = inject_link(html, phrase, target)
        if not ok:
            counts["skipped_no_phrase"] += 1
            continue
        counts["applied"] += 1
        if args.apply:
            p.write_text(new_html, encoding="utf-8")
        print(f"  ✓ {rel_path}: linked '{phrase}' → {target}")
    print("\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
