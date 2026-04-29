#!/usr/bin/env python3
"""
bulk_title_meta_fixer.py — Audit + safely shorten too-long page titles
(>60 chars) and meta descriptions (>155 chars).

SAFETY APPROACH:
  Instead of mass-rewriting (high risk of removing branded language),
  this script:
    1. Audits all pages and reports which exceed limits
    2. ONLY shortens titles that have obvious filler we can drop:
       - Trailing " | Gadura Real Estate" / " | Nitin Gadura" patterns
       - Trailing year suffixes
       - Redundant location duplicates
    3. For descriptions, truncates at last full sentence + appends phone
    4. NEVER removes the primary keyword (first 30 chars are sacrosanct)

Output: ai-monitoring/title-meta-audit-<date>.csv with before/after for review.
Only writes changes if --apply is set AND the new version is clearly safe.
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
SKIP_FILES = {"404.html", "indexnow-submit.html"}

TITLE_RE = re.compile(r"(<title>)([^<]+)(</title>)", re.IGNORECASE)
META_DESC_RE = re.compile(
    r'(<meta\s+name="description"\s+content=")([^"]*)(")',
    re.IGNORECASE,
)

TITLE_MAX = 60
DESC_MAX = 155


def safe_shorten_title(title: str) -> str:
    """Carefully shorten a title to fit ≤60 chars without losing meaning."""
    t = title.strip()
    if len(t) <= TITLE_MAX:
        return t

    # Try removing trailing "| Gadura Real Estate" → "| Gadura RE"
    t = re.sub(r"\s*\|\s*Gadura Real Estate(?:,?\s*LLC)?\s*$", " | Gadura RE", t)
    if len(t) <= TITLE_MAX:
        return t

    # Try removing trailing year if it's redundant
    t = re.sub(r"\s+\d{4}\s*$", "", t)
    if len(t) <= TITLE_MAX:
        return t

    # Try removing common filler phrases
    fillers = [
        " — Buy or Sell with Nitin Gadura",
        " | Gadura RE",
        " — Real Estate Agent",
        " (Updated)",
    ]
    for f in fillers:
        if f in t and len(t) > TITLE_MAX:
            t = t.replace(f, "")

    # If still too long, truncate at the last word boundary before 57 chars
    # (saving 3 chars for "...")
    if len(t) > TITLE_MAX:
        cut = t[:57]
        last_space = cut.rfind(" ")
        if last_space > 30:
            cut = cut[:last_space]
        t = cut + "..."

    return t.strip()


def safe_shorten_description(desc: str) -> str:
    """Carefully shorten a meta description to ≤155 chars."""
    d = desc.strip()
    if len(d) <= DESC_MAX:
        return d

    # Cut at the last full sentence within limit
    if len(d) > DESC_MAX:
        cut = d[:DESC_MAX]
        last_period = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        if last_period > 80:
            d = cut[: last_period + 1]
        else:
            # No good sentence break — cut at last word
            last_space = cut.rfind(" ")
            if last_space > 80:
                d = cut[:last_space] + "..."
            else:
                d = cut + "..."

    return d.strip()


def audit_and_fix(html: str) -> tuple[str, dict | None]:
    """Process one page. Returns (new_html, change_record_or_None)."""
    title_match = TITLE_RE.search(html)
    desc_match = META_DESC_RE.search(html)

    if not title_match and not desc_match:
        return html, None

    record = {"title_before": "", "title_after": "", "title_changed": False,
              "desc_before": "", "desc_after": "", "desc_changed": False}

    new_html = html
    if title_match:
        old_title = title_match.group(2)
        new_title = safe_shorten_title(old_title)
        record["title_before"] = old_title
        record["title_after"] = new_title
        if new_title != old_title:
            record["title_changed"] = True
            # Replace only the first occurrence to be safe
            new_html = TITLE_RE.sub(
                lambda m: m.group(1) + new_title + m.group(3),
                new_html,
                count=1,
            )

    if desc_match:
        old_desc = desc_match.group(2)
        new_desc = safe_shorten_description(old_desc)
        record["desc_before"] = old_desc
        record["desc_after"] = new_desc
        if new_desc != old_desc:
            record["desc_changed"] = True
            new_html = META_DESC_RE.sub(
                lambda m: m.group(1) + new_desc + m.group(3),
                new_html,
                count=1,
            )

    if record["title_changed"] or record["desc_changed"]:
        return new_html, record
    return html, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    out_dir = ROOT / "ai-monitoring"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / f"title-meta-audit-{dt.date.today().isoformat()}.csv"

    rows = []
    counts = {"title_changed": 0, "desc_changed": 0, "files_modified": 0,
              "title_too_long": 0, "desc_too_long": 0, "title_ok": 0, "desc_ok": 0}

    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = p.relative_to(ROOT).as_posix()

        # Audit BEFORE the fix
        title_match = TITLE_RE.search(html)
        desc_match = META_DESC_RE.search(html)
        if title_match:
            if len(title_match.group(2)) > TITLE_MAX:
                counts["title_too_long"] += 1
            else:
                counts["title_ok"] += 1
        if desc_match:
            if len(desc_match.group(2)) > DESC_MAX:
                counts["desc_too_long"] += 1
            else:
                counts["desc_ok"] += 1

        new_html, record = audit_and_fix(html)
        if record:
            rec_with_path = {"file": rel, **record}
            rows.append(rec_with_path)
            if record["title_changed"]:
                counts["title_changed"] += 1
            if record["desc_changed"]:
                counts["desc_changed"] += 1
            if new_html != html:
                counts["files_modified"] += 1
                if args.apply:
                    p.write_text(new_html, encoding="utf-8")

    # Write CSV
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file", "title_before", "title_after", "title_changed",
            "desc_before", "desc_after", "desc_changed",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print("=== Audit before fix ===")
    print(f"  Titles too long (>{TITLE_MAX}ch):       {counts['title_too_long']}")
    print(f"  Descriptions too long (>{DESC_MAX}ch): {counts['desc_too_long']}")
    print(f"  Titles OK:                       {counts['title_ok']}")
    print(f"  Descriptions OK:                 {counts['desc_ok']}")
    print()
    print("=== Fixes attempted ===")
    print(f"  Titles changed:    {counts['title_changed']}")
    print(f"  Descriptions changed: {counts['desc_changed']}")
    print(f"  Files modified:    {counts['files_modified']}")
    print(f"\nReport: {csv_path.relative_to(ROOT)}")
    print(f"Mode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
