#!/usr/bin/env python3
"""
clean_duplicate_schema_comments.py — Remove duplicate <!-- AI MASTER SCHEMA -->
header comments. Earlier inject runs added a fresh comment block on every pass
without dedupe — some pages now have 9+ identical comment headers (~1KB bloat
per page).

The actual <script id="ai-master-schema"> block IS deduplicated (marker-based),
only the comment header was orphaned.

Idempotent. Safe to run repeatedly.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The 4-line comment block (with trailing newlines/whitespace).
DUP_BLOCK = re.compile(
    r"<!--\s*\n"
    r"\s*AI MASTER SCHEMA — canonical Person \+ RealEstateAgent \+ Brand entity graph\s*\n"
    r"\s*Injected on every key buyer/seller-intent page for ChatGPT, Gemini, Perplexity, Grok, Claude\.\s*\n"
    r"\s*DO NOT EDIT INLINE — edit this file and re-run scripts/inject_ai_schema\.py\s*\n"
    r"-->\s*",
    re.MULTILINE,
)

SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}


def clean(html: str) -> tuple[str, int]:
    """Returns (new_html, n_blocks_removed). Keeps first occurrence, removes rest."""
    matches = list(DUP_BLOCK.finditer(html))
    if len(matches) <= 1:
        return html, 0
    # Keep first, remove the rest.
    first_end = matches[0].end()
    out_parts = [html[: matches[0].end()]]
    last_end = first_end
    for m in matches[1:]:
        out_parts.append(html[last_end : m.start()])
        last_end = m.end()
    out_parts.append(html[last_end:])
    return "".join(out_parts), len(matches) - 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    n_files = n_blocks = bytes_saved = 0
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new_html, removed = clean(html)
        if removed:
            n_files += 1
            n_blocks += removed
            bytes_saved += len(html) - len(new_html)
            if args.apply:
                p.write_text(new_html, encoding="utf-8")
    print(f"  Files cleaned:        {n_files}")
    print(f"  Duplicate blocks gone:{n_blocks}")
    print(f"  Bytes saved:          {bytes_saved:,} ({bytes_saved/1024:.1f}KB)")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
