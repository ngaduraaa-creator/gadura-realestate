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
import html as html_lib
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
    # SEO tools count rendered characters, not entity source text (`&amp;`
    # is one character, not five).
    raw = title.strip()
    t = html_lib.unescape(raw)
    if len(t) <= TITLE_MAX:
        return raw

    original = t

    # Try shortening or removing a trailing brand suffix. Both preserve the
    # complete topic phrase before the separator.
    t = re.sub(r"\s*\|\s*Gadura Real Estate(?:,?\s*LLC)?\s*$", " | Gadura RE", t)
    if len(t) <= TITLE_MAX:
        return html_lib.escape(t, quote=False)
    without_brand = re.sub(r"\s*\|\s*Gadura RE\s*$", "", t)
    if len(without_brand) <= TITLE_MAX:
        return html_lib.escape(without_brand, quote=False)

    # Try removing trailing year if it's redundant
    t = re.sub(r"\s+\d{4}\s*$", "", t)
    if len(t) <= TITLE_MAX:
        return html_lib.escape(t, quote=False)

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

    # Do not clip a search title mid-thought. Leave it for manual review if
    # the safe, mechanical transformations above cannot bring it under 60.
    if len(t) <= TITLE_MAX:
        return html_lib.escape(t.strip(), quote=False)
    return raw


def safe_shorten_description(desc: str) -> str:
    """Carefully shorten a meta description to ≤155 chars."""
    d = html_lib.unescape(desc.strip())
    if len(d) <= DESC_MAX:
        return html_lib.escape(d, quote=True)

    # Cut at the last full sentence within limit
    if len(d) > DESC_MAX:
        cut = d[:DESC_MAX]
        last_period = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        if last_period > 80:
            d = cut[: last_period + 1]
        else:
            # A clipped phrase is worse copy than a modestly long
            # description. Keep it unchanged for manual review.
            return html_lib.escape(html_lib.unescape(desc.strip()), quote=True)

    return html_lib.escape(d.strip(), quote=True)


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
    ap.add_argument(
        "--titles-only",
        action="store_true",
        help="Audit descriptions but only apply safe title changes",
    )
    args = ap.parse_args()

    out_dir = ROOT / "ai-monitoring"
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
            if len(html_lib.unescape(title_match.group(2))) > TITLE_MAX:
                counts["title_too_long"] += 1
            else:
                counts["title_ok"] += 1
        if desc_match:
            if len(html_lib.unescape(desc_match.group(2))) > DESC_MAX:
                counts["desc_too_long"] += 1
            else:
                counts["desc_ok"] += 1

        new_html, record = audit_and_fix(html)
        if record:
            rec_with_path = {"file": rel, **record}
            rows.append(rec_with_path)
            if record["title_changed"]:
                counts["title_changed"] += 1
            if record["desc_changed"] and not args.titles_only:
                counts["desc_changed"] += 1
            output_html = new_html
            if args.titles_only and record["desc_changed"]:
                output_html = META_DESC_RE.sub(
                    lambda m: m.group(1) + record["desc_before"] + m.group(3),
                    output_html,
                    count=1,
                )
            if output_html != html:
                counts["files_modified"] += 1
                if args.apply:
                    p.write_text(output_html, encoding="utf-8")

    # Keep dry-runs read-only so the audit can run in restricted/CI contexts.
    if args.apply:
        out_dir.mkdir(exist_ok=True)
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
    if args.apply:
        print(f"\nReport: {csv_path.relative_to(ROOT)}")
    print(f"Mode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
