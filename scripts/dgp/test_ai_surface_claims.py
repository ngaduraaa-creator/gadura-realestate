#!/usr/bin/env python3
"""AI-surface claims gate.

WHY THIS EXISTS
---------------
The LA-3B0J compliance work removed the self-serving AggregateRating (4.9 / 57
reviews) and the unsupported superlatives from ~1,224 HTML pages. It held: the
HTML is clean.

The claims survived anyway — on the AI-facing surfaces.

Both existing guards are scoped to HTML and cannot see these files:
    scripts/check_schema_policy.py     -> root.rglob("*.html")
    scripts/dgp/test_compliance_gates.py -> fn.endswith(".html")

So llms.txt and llms-full.txt kept serving "4.9 stars — 57+ verified reviews",
"Top Listing Brokerage", "Best listing agent" and "top-rated" to exactly the
consumers those files exist for: ChatGPT, Perplexity, Claude, Gemini and Google
AI Overviews. llms.txt is advertised in robots.txt, so it is actively
discoverable. Claims scrubbed from a surface search engines discount had moved
to one AI engines are built to trust.

This gate closes the scope gap: it scans the NON-HTML surfaces the other two
guards structurally cannot reach.

BASELINE
--------
Two files are in violation right now. Removing those claims is a BROKER and
COUNSEL decision about advertising representations, not an engineering change,
so this gate does not silently rewrite them. Instead the known violations are
recorded in BASELINE below and reported loudly on every run.

The gate FAILS on:
  - any violation in a file not in BASELINE  (a NEW regression)
  - any NEW claim type in a baselined file   (an existing file getting worse)

The gate PASSES, while printing the outstanding debt, when the only findings
are exactly what BASELINE records. Shrink BASELINE to {} as the content is
cleared. Do not add entries to silence a new problem.

Run: python3 scripts/dgp/test_ai_surface_claims.py    (exit 0 pass / 1 fail)
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Non-HTML surfaces intended for machine/AI consumption. Add new ones here as
# they are introduced; a surface not listed is a surface nobody is checking.
SURFACES = [
    "llms.txt",
    "llms-full.txt",
    "ai.txt",
    "feed.json",
    "rss.xml",
    "ai-plugin.json",
    ".well-known/ai-plugin.json",
    "humans.txt",
    ".well-known/humans.txt",
]

# Claim classes prohibited by the governed advertising position (LA-3B0x) and,
# for the rating, by Google's policy against self-serving review markup.
CLAIMS = {
    "self_serving_rating": (
        r"\b4\.9\b(?![\d])",
        "self-serving star rating (the AggregateRating removed from HTML)",
    ),
    "review_count": (
        r"\b\d{2,}\+?\s*(?:verified\s+)?reviews?\b",
        "unsupported aggregate review count",
    ),
    "superlative_best": (
        r"\bbest\s+(?:listing\s+)?(?:agent|brokerage|realtor)\b",
        "unsupported superlative ('best ... agent/brokerage')",
    ),
    "superlative_top": (
        r"\btop[-\s]rated\b|\btop\s+listing\s+brokerage\b|\btop\s+\d+%",
        "unsupported superlative ('top-rated' / 'top listing brokerage')",
    ),
    # "#1" only when written as a claim. `#\s?1` also matched the markdown
    # heading "## 1. Business Overview", so the space variant is dropped and
    # heading lines are stripped before scanning (see scan()).
    "number_one": (
        r"#1\b|\bnumber\s+one\b",
        "unsupported #1 claim",
    ),
    "guarantee": (
        r"\bguarantee(?:d|s)?\b",
        "guarantee language",
    ),
}

# Known, accepted-for-now violations. AWAITING BROKER + COUNSEL REVIEW.
# Recorded 2026-08-31. Shrink to {} as content is cleared.
BASELINE: dict[str, set[str]] = {
    "llms.txt": {
        "self_serving_rating",
        "review_count",
        "superlative_best",
        "superlative_top",
    },
    "llms-full.txt": {
        "self_serving_rating",
        "review_count",
    },
}


def scannable(text: str) -> str:
    """Strip constructs that produce false positives rather than real claims.

    Two were found on the first run against llms-full.txt:

      * Markdown headings — "## 1. Business Overview" tripped the #1 pattern.
      * Quoted example search queries — these files list the questions they
        expect to answer, e.g.
            - "Best agent for buying a two-family home in Jamaica, Queens"
        That is an anticipated user query, not the brokerage calling itself
        best. Treating it as a claim would train people to ignore this gate.

    Both are removed before matching. A claim written as ordinary prose is
    still caught; only these two containers are exempt.
    """
    # drop markdown heading lines
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s.*$", " ", text)
    # drop double-quoted spans (example queries, cited question text)
    text = re.sub(r"\"[^\"\n]{0,200}\"", " ", text)
    return text


def scan(path: pathlib.Path) -> set[str]:
    text = scannable(path.read_text(encoding="utf-8", errors="ignore"))
    return {
        key
        for key, (pattern, _) in CLAIMS.items()
        if re.search(pattern, text, re.IGNORECASE)
    }


def main() -> int:
    present = [(s, ROOT / s) for s in SURFACES if (ROOT / s).is_file()]
    if not present:
        print("FAIL: none of the known AI-facing surfaces exist — check SURFACES")
        return 1

    regressions: list[str] = []
    outstanding: list[str] = []

    for rel, path in present:
        found = scan(path)
        allowed = BASELINE.get(rel, set())
        new = found - allowed
        for key in sorted(new):
            regressions.append(f"  {rel}: {key} — {CLAIMS[key][1]}")
        for key in sorted(found & allowed):
            outstanding.append(f"  {rel}: {key} — {CLAIMS[key][1]}")

    # A baselined entry that no longer fires means the content was cleaned;
    # say so, so BASELINE gets trimmed instead of quietly rotting.
    cleared: list[str] = []
    for rel, keys in BASELINE.items():
        path = ROOT / rel
        found = scan(path) if path.is_file() else set()
        for key in sorted(keys - found):
            cleared.append(f"  {rel}: {key}")

    print(f"AI-surface claims gate — scanned {len(present)} surface(s)")
    for rel, _ in present:
        print(f"    {rel}")

    if outstanding:
        print()
        print("OUTSTANDING (baselined — AWAITING BROKER + COUNSEL REVIEW):")
        for line in outstanding:
            print(line)
        print("  These are served to ChatGPT/Perplexity/Claude/Gemini today.")

    if cleared:
        print()
        print("CLEARED — remove these from BASELINE:")
        for line in cleared:
            print(line)

    if regressions:
        print()
        print("FAIL — new claim(s) on an AI-facing surface:")
        for line in regressions:
            print(line)
        print()
        print("  Do NOT add these to BASELINE to make the gate pass.")
        print("  Remove the claim, or get broker sign-off and record it deliberately.")
        return 1

    print()
    print(f"PASS — no new claims. {len(outstanding)} baselined item(s) still outstanding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
