#!/usr/bin/env python3
"""Swap IDX Broker URLs from gadurarealestate.idxbroker.com to homes.gadurarealestate.com.

Run AFTER the CNAME `homes` -> `gadurarealestate.idxbroker.com` is live and
`https://homes.gadurarealestate.com` resolves with the IDX content.

The script:
  1. Replaces every reference to `gadurarealestate.idxbroker.com` with
     `homes.gadurarealestate.com` across all .html, .xml, .txt, .js, .json
     files in the project.
  2. Skips .git, node_modules, scripts (this file), and assets_bak.
  3. Reports counts per file and a total summary.

Idempotent — running twice produces no diff.

Usage:
    python3 scripts/swap-idx-subdomain.py            # dry run (shows changes)
    python3 scripts/swap-idx-subdomain.py --apply    # actually write
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = "gadurarealestate.idxbroker.com"
NEW = "homes.gadurarealestate.com"
SKIP_DIRS = {".git", "node_modules", "scripts", "assets_bak", "v2"}
EXTS = {".html", ".xml", ".txt", ".js", ".json", ".md", ".css"}


def walk_files() -> list[Path]:
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.suffix.lower() not in EXTS:
            continue
        out.append(p)
    return out


def main() -> None:
    apply = "--apply" in sys.argv
    files = walk_files()
    total_swaps = 0
    affected_files = 0

    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if OLD not in text:
            continue
        count = text.count(OLD)
        new_text = text.replace(OLD, NEW)
        affected_files += 1
        total_swaps += count
        rel = p.relative_to(ROOT)
        print(f"  {count:>4}x  {rel}")
        if apply:
            p.write_text(new_text, encoding="utf-8")

    print()
    print(f"{'APPLIED' if apply else 'DRY RUN'}: {total_swaps} swaps across {affected_files} files")
    if not apply:
        print("Run again with --apply to write the changes.")


if __name__ == "__main__":
    main()
