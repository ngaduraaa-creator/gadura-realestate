#!/usr/bin/env python3
"""Inject the site's GA4 block into pages that are missing it.

Idempotent. The block is delimited by GRE_GA4_START / GRE_GA4_END markers, so a
page that already carries it is skipped, and re-running never stacks tags.

Why this exists: 16 of the 17 /agents/*.html pages and both team-hub pages
shipped without GA4, so the entire agent surface was unmeasurable. Only
agents/nitin-gadura.html had the tag. Everything else recorded nothing, which
means "the agent pages get no engagement" was never a finding -- it was an
absence of instrumentation.

Usage:
    python3 scripts/inject_ga4.py --check            # report only, exit 1 if gaps
    python3 scripts/inject_ga4.py --apply PATH...    # inject into the given files
"""

import argparse
import re
import sys
from pathlib import Path

GA_ID = "G-9TM4LDZ7DD"

START = "<!-- GRE_GA4_START -->"
END = "<!-- GRE_GA4_END -->"

# Byte-for-byte the block already live on agents/nitin-gadura.html. Keeping it
# identical matters: a second variant would fragment the property's config.
BLOCK = f"""{START}
<!-- GA4 analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  var GA_ID = '{GA_ID}';
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', GA_ID, {{
    anonymize_ip: true,
    send_page_view: true,
    cookie_flags: 'SameSite=None;Secure'
  }});
</script>
{END}
"""

# Any existing GA4/GTM loader, however it was added. Checked before injecting so
# a page tagged by some other mechanism is left alone rather than double-tagged.
HAS_ANALYTICS = re.compile(
    r"googletagmanager\.com/(?:gtag/js|gtm\.js)|GRE_GA4_START", re.I
)

HEAD_CLOSE = re.compile(r"</head\s*>", re.I)


def status(path: Path) -> str:
    """One of: tagged, missing, no-head."""
    html = path.read_text(encoding="utf-8", errors="replace")
    if HAS_ANALYTICS.search(html):
        return "tagged"
    if not HEAD_CLOSE.search(html):
        return "no-head"
    return "missing"


def inject(path: Path) -> bool:
    """Insert the block immediately before </head>. Returns True if changed."""
    html = path.read_text(encoding="utf-8")
    if HAS_ANALYTICS.search(html):
        return False
    m = HEAD_CLOSE.search(html)
    if not m:
        return False
    # Insert before the FIRST </head> only.
    out = html[: m.start()] + BLOCK + html[m.start() :]
    path.write_text(out, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--apply", action="store_true", help="write changes")
    ap.add_argument(
        "--check",
        action="store_true",
        help="report untagged pages and exit 1 if any are found",
    )
    args = ap.parse_args()

    paths = args.paths or sorted(
        list(Path("agents").glob("*.html"))
        + [Path("agents.html"), Path("meet-the-agents.html")]
    )
    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("no files matched", file=sys.stderr)
        return 2

    missing, tagged, nohead = [], [], []
    for p in paths:
        s = status(p)
        {"missing": missing, "tagged": tagged, "no-head": nohead}[s].append(p)

    if args.check or not args.apply:
        for p in missing:
            print(f"MISSING  {p}")
        for p in nohead:
            print(f"NO-HEAD  {p}")
        print(
            f"\n{len(tagged)} tagged, {len(missing)} missing, "
            f"{len(nohead)} without a </head>, of {len(paths)} checked"
        )
        return 1 if (missing or nohead) else 0

    changed = [p for p in missing if inject(p)]
    for p in changed:
        print(f"injected {p}")
    if nohead:
        for p in nohead:
            print(f"SKIPPED (no </head>) {p}", file=sys.stderr)
    print(f"\n{len(changed)} injected, {len(tagged)} already tagged")
    return 1 if nohead else 0


if __name__ == "__main__":
    sys.exit(main())
