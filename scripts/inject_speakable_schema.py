#!/usr/bin/env python3
"""
inject_speakable_schema.py — Add Speakable schema to FAQ-heavy pages so voice
assistants (Alexa, Siri, Google Assistant) read the right content aloud.

Marker: id="ai-speakable-schema". Idempotent.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER_ID = "ai-speakable-schema"

SPEAKABLE_BLOCK = '''<script type="application/ld+json" id="ai-speakable-schema">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [
      ".answer-first",
      ".answer-first strong",
      "h1",
      "h2",
      ".faq-item .q",
      ".faq-item p",
      ".hero .lede",
      ".lede",
      "[data-speakable]"
    ],
    "xpath": [
      "/html/body//h1",
      "/html/body//*[@class='answer-first']"
    ]
  }
}
</script>'''

GLOBS = [
    "*.html",
    "**/*.html",
]
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "node_modules"}
SKIP_FILES = {"404.html"}

SCRIPT_RE = re.compile(
    rf'<script type="application/ld\+json" id="{MARKER_ID}">.*?</script>\s*',
    re.DOTALL | re.IGNORECASE,
)


def collect():
    seen = set()
    out = []
    for pat in GLOBS:
        for p in ROOT.glob(pat):
            if not p.is_file() or p.suffix != ".html":
                continue
            if p.name in SKIP_FILES:
                continue
            if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
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
    pages = collect()
    counts = {"inserted": 0, "replaced": 0, "noop": 0}
    for p in pages:
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only inject on pages with .answer-first or FAQ-style content (real candidates)
        if ".answer-first" not in html and "faq-item" not in html and "answer-first" not in html:
            counts["noop"] += 1
            continue
        if MARKER_ID in html:
            new_html, n = SCRIPT_RE.subn(SPEAKABLE_BLOCK + "\n", html, count=1)
            counts["replaced"] += 1
        elif "</head>" in html:
            new_html = html.replace("</head>", f"{SPEAKABLE_BLOCK}\n</head>", 1)
            counts["inserted"] += 1
        else:
            counts["noop"] += 1
            continue
        if args.apply and new_html != html:
            p.write_text(new_html, encoding="utf-8")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
