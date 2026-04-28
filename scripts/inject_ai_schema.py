#!/usr/bin/env python3
"""
inject_ai_schema.py — Inject the canonical AI-master-schema JSON-LD block
into every high-priority page.

Usage:
    python3 scripts/inject_ai_schema.py            # dry-run (default)
    python3 scripts/inject_ai_schema.py --apply    # actually write

The block is idempotent: identified by id="ai-master-schema" on the
<script> tag. Re-runs replace the existing block in-place.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "_includes" / "ai-master-schema.html"
MARKER_ID = "ai-master-schema"

# High-priority pages — every AI engine touch-point.
PRIORITY_GLOBS = [
    "index.html",
    "about.html",
    "contact.html",
    "agents.html",
    "meet-the-agents.html",
    "neighborhoods.html",
    "reviews.html",
    "buy.html",
    "sell.html",
    "resources.html",
    "hindi-speaking-real-estate-agent-queens.html",
    "punjabi-speaking-real-estate-agent-queens.html",
    "1031-exchange-queens.html",
    "coop-board-package-help-queens.html",
    "divorce-home-sale-queens.html",
    "inherited-property-sale-queens.html",
    "senior-downsizing-queens.html",
    "short-sale-queens-ny.html",
    "fsbo-selling-without-broker-nyc.html",
    "flat-fee-vs-full-service.html",
    "closing-costs-nyc-guide.html",
    "nitin-gadura/index.html",
    "about-us/index.html",
    "neighborhoods/index.html",
    "community/index.html",
    "community/indian-community.html",
    "community/guyanese-community.html",
    "community/bengali-community.html",
    "services/index.html",
    "our-listings/index.html",
    "past-sales/index.html",
]

# Glob patterns — apply across folders too.
GLOB_PATTERNS = [
    "neighborhoods/**/*.html",
    "neighborhoods/*.html",
    "community/*.html",
    "agents/*.html",
    "agents/**/*.html",
    "services/*.html",
    "market-reports/*.html",
    "blog/*.html",
    "faq/*.html",
    "home-value/*.html",
    "long-island/**/*.html",
    "zip/*.html",
]

# Skip these — they have their own schema or are non-content.
SKIP_GLOBS = {
    "404.html",
    "indexnow-submit.html",
    "idx-wrapper.html",
    "portal.html",
    "v2/**",
    "_includes/**",
    "scripts/**",
    "admin/**",
    "research/**",
    "docs/**",
}


def load_schema_block() -> str:
    raw = SCHEMA_FILE.read_text(encoding="utf-8")
    # Inject id marker so we can find/replace later.
    return raw.replace(
        '<script type="application/ld+json">',
        f'<script type="application/ld+json" id="{MARKER_ID}">',
        1,
    )


def collect_targets() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for rel in PRIORITY_GLOBS:
        p = ROOT / rel
        if p.is_file() and p not in seen:
            seen.add(p)
            out.append(p)
    for pattern in GLOB_PATTERNS:
        for p in ROOT.glob(pattern):
            if not p.is_file() or p.suffix != ".html" or p in seen:
                continue
            rel = p.relative_to(ROOT).as_posix()
            if any(rel == s or rel.startswith(s.rstrip("*")) for s in SKIP_GLOBS):
                continue
            seen.add(p)
            out.append(p)
    return out


SCRIPT_RE = re.compile(
    rf'<script type="application/ld\+json" id="{MARKER_ID}">.*?</script>\s*',
    re.DOTALL | re.IGNORECASE,
)


def inject(html: str, block: str) -> tuple[str, str]:
    """Returns (new_html, action) where action is 'inserted' / 'replaced' / 'noop'."""
    if MARKER_ID in html:
        new_html, n = SCRIPT_RE.subn(block + "\n", html, count=1)
        if n:
            return new_html, "replaced"
        return html, "noop"
    # Insert just before </head>.
    if "</head>" not in html:
        return html, "noop"
    return html.replace("</head>", f"{block}\n</head>", 1), "inserted"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    if not SCHEMA_FILE.exists():
        print(f"ERROR: schema file missing: {SCHEMA_FILE}")
        return 1
    block = load_schema_block().rstrip()

    targets = collect_targets()
    print(f"Targets: {len(targets)} pages")

    counts = {"inserted": 0, "replaced": 0, "noop": 0, "skipped_no_head": 0}
    for p in targets:
        try:
            html = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ! cannot read {p.relative_to(ROOT)}: {e}")
            continue
        new_html, action = inject(html, block)
        if action == "noop" and "</head>" not in html:
            counts["skipped_no_head"] += 1
            continue
        counts[action] += 1
        if args.apply and new_html != html:
            p.write_text(new_html, encoding="utf-8")

    print("\nResults:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN — re-run with --apply'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
