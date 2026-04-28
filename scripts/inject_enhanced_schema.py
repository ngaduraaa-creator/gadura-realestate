#!/usr/bin/env python3
"""
inject_enhanced_schema.py — Inject the Service/Review/Speakable layer
across high-value pages alongside the master schema.

Idempotent. Marker: id="ai-enhanced-schema".
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "_includes" / "ai-enhanced-schema.html"
MARKER_ID = "ai-enhanced-schema"

# Pages where Review/Service schema makes sense (homepage, agent, services, FAQ).
TARGETS = [
    "index.html",
    "about.html",
    "contact.html",
    "agents.html",
    "meet-the-agents.html",
    "reviews.html",
    "buy.html",
    "sell.html",
    "resources.html",
    "neighborhoods.html",
    "1031-exchange-queens.html",
    "coop-board-package-help-queens.html",
    "fsbo-selling-without-broker-nyc.html",
    "flat-fee-vs-full-service.html",
    "hindi-speaking-real-estate-agent-queens.html",
    "punjabi-speaking-real-estate-agent-queens.html",
    "nitin-gadura/index.html",
    "neighborhoods/index.html",
    "community/index.html",
    "community/indian-community.html",
    "community/guyanese-community.html",
    "community/bengali-community.html",
    "services/index.html",
    "hi/index.html",
    "bn/index.html",
    "es/index.html",
    "pa/index.html",
]

SCRIPT_RE = re.compile(
    rf'<script type="application/ld\+json" id="{MARKER_ID}">.*?</script>\s*',
    re.DOTALL | re.IGNORECASE,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    block = SCHEMA_FILE.read_text(encoding="utf-8").rstrip()
    counts = {"inserted": 0, "replaced": 0, "noop": 0, "missing": 0}
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            counts["missing"] += 1
            continue
        html = p.read_text(encoding="utf-8")
        if MARKER_ID in html:
            new_html, n = SCRIPT_RE.subn(block + "\n", html, count=1)
            action = "replaced" if n else "noop"
        elif "</head>" in html:
            new_html = html.replace("</head>", f"{block}\n</head>", 1)
            action = "inserted"
        else:
            action = "noop"
            new_html = html
        counts[action] += 1
        if args.apply and new_html != html:
            p.write_text(new_html, encoding="utf-8")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
