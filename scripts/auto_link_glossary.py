#!/usr/bin/env python3
"""
auto_link_glossary.py — Auto-link first occurrence of every glossary term
across blog posts and topical-hub pages. Builds the internal link graph
that Google's PageRank rewards.

How it works:
- Reads the glossary terms list (defined below)
- For each blog post + topical-hub page, finds the FIRST occurrence of each term
  in body text (skips inside <a>, <h1>, <h2>, <script>, <style>)
- Wraps that first occurrence in <a href="/glossary/#anchor"> tag
- Idempotent: skips terms already linked
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each entry: (term as it appears in text, glossary anchor on /glossary/)
GLOSSARY_TERMS = [
    ("FHA loan", "F"),
    ("FHA loans", "F"),
    ("SONYMA", "S"),
    ("HomeReady", "H"),
    ("VA loan", "V"),
    ("co-op", "C"),
    ("condop", "C"),
    ("condo", "C"),
    ("CMA", "C"),
    ("Comparative Market Analysis", "C"),
    ("board package", "B"),
    ("buyer-broker agreement", "B"),
    ("buydown", "B"),
    ("DTI", "D"),
    ("mansion tax", "M"),
    ("MLS", "M"),
    ("OneKey® MLS", "O"),
    ("OneKey MLS", "O"),
    ("mortgage recording tax", "M"),
    ("RPTT", "R"),
    ("PMI", "P"),
    ("pre-approval", "P"),
    ("flip tax", "F"),
    ("title insurance", "T"),
    ("transfer tax", "T"),
    ("escrow", "E"),
    ("earnest money", "E"),
    ("attorney", "A"),
    ("ARM", "A"),
    ("1031 exchange", "1"),
    ("short sale", "S"),
    ("LLC", "L"),
    ("land lease", "L"),
    ("HOA", "H"),
    ("rider", "R"),
    ("NAR settlement", "N"),
    ("owner-occupant", "O"),
    ("TIC", "T"),
    ("in-contract", "I"),
    ("IDX", "I"),
    ("down payment", "D"),
]

# Pages we'll auto-link.
TARGETS = [
    "blog/**/*.html",
    "first-time-homebuyer/*.html",
    "multi-family-investment/*.html",
    "co-op-board-help/*.html",
    "1031-exchange/*.html",
    "fha-loans-nyc/*.html",
    "buy.html",
    "sell.html",
    "closing-costs-nyc-guide.html",
    "coop-board-package-help-queens.html",
    "1031-exchange-queens.html",
    "fsbo-selling-without-broker-nyc.html",
    "flat-fee-vs-full-service.html",
    "short-sale-queens-ny.html",
    "inherited-property-sale-queens.html",
    "divorce-home-sale-queens.html",
    "senior-downsizing-queens.html",
    "market-reports/*.html",
]

# Skip linking inside these tags
SKIP_TAGS = {"a", "h1", "h2", "h3", "h4", "title", "script", "style", "code", "pre", "option", "label"}


def make_link(term: str, anchor: str) -> str:
    return f'<a href="/glossary/#{anchor}" class="glossary-link" title="{term} — see glossary">{term}</a>'


def link_first_occurrence(html: str, term: str, anchor: str) -> tuple[str, bool]:
    """Wrap the first body occurrence of `term` in a glossary link."""
    # Already linked? skip
    if f'/glossary/#{anchor}' in html and term.lower() in html.lower():
        # Already has at least one link — just don't add more
        if html.count(make_link(term, anchor)) > 0:
            return html, False
    # Build pattern: term boundary, but NOT inside skip tags.
    # Strategy: split on tags, only operate on text segments.
    pattern = re.compile(r'(' + re.escape(term) + r')(?![^<]*>)', re.IGNORECASE)
    # Walk the HTML chunk-by-chunk, skipping inside SKIP_TAGS.
    out = []
    i = 0
    skip_depth = 0
    skip_tag_re = re.compile(
        r'<\s*(/?)\s*(' + "|".join(SKIP_TAGS) + r')\b[^>]*>',
        re.IGNORECASE
    )
    replaced = False
    pos = 0
    chunks = []
    last = 0
    for m in skip_tag_re.finditer(html):
        chunks.append((html[last:m.start()], False))   # plain
        chunks.append((m.group(0), True))  # tag (skip)
        is_close = bool(m.group(1))
        if is_close:
            pass  # skip_depth flips handled in walk
        last = m.end()
    chunks.append((html[last:], False))

    out_pieces = []
    depth = 0
    for content, is_tag in chunks:
        if is_tag:
            # Check open vs close
            if re.match(r'<\s*/', content):
                depth = max(0, depth - 1)
            else:
                # opening tag
                if not content.endswith("/>"):
                    depth += 1
            out_pieces.append(content)
        else:
            if depth > 0 or replaced:
                out_pieces.append(content)
            else:
                # Try one replacement in this chunk
                new_content, n = pattern.subn(
                    lambda mm: make_link(mm.group(1), anchor),
                    content,
                    count=1
                )
                if n:
                    replaced = True
                out_pieces.append(new_content)
    return "".join(out_pieces), replaced


def collect_targets() -> list[Path]:
    seen = set()
    out = []
    for pat in TARGETS:
        for p in ROOT.glob(pat):
            if not p.is_file() or p.suffix != ".html":
                continue
            if p in seen:
                continue
            seen.add(p)
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    pages = collect_targets()
    total_links = 0
    files_touched = 0
    for p in pages:
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new = html
        added = 0
        for term, anchor in GLOSSARY_TERMS:
            # Skip if already linked anywhere in page
            if f'href="/glossary/#{anchor}"' in new and term.lower() in new.lower():
                # Check actual link
                pass
            new, did = link_first_occurrence(new, term, anchor)
            if did:
                added += 1
        if added and args.apply and new != html:
            p.write_text(new, encoding="utf-8")
            files_touched += 1
        total_links += added
    print(f"  Total glossary links added: {total_links}")
    print(f"  Files touched: {files_touched}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
