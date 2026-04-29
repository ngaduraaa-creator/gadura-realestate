#!/usr/bin/env python3
"""
hreflang_safety_fixer.py — Strip hreflang tags that reference non-existent
translations. Add proper reciprocal hreflang only for languages that exist.

We have 5 languages on the site:
  - en (default)
  - hi (Hindi)
  - bn (Bengali)
  - es (Spanish)
  - pa (Punjabi)

Ahrefs flagged 575 pages with broken hreflang. Almost all are because the site
template references languages that aren't actually translated for that page.
The fix: only emit hreflang for translations that actually exist on disk.

Idempotent. Safe. Run with --apply to write changes.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANGUAGES = {
    "en": "/",          # English is the default at site root
    "hi": "/hi/",       # Hindi
    "bn": "/bn/",       # Bengali
    "es": "/es/",       # Spanish
    "pa": "/pa/",       # Punjabi
}

DOMAIN = "https://gadurarealestate.com"
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}

# Match any existing hreflang link tag.
HREFLANG_RE = re.compile(
    r'<link\s+rel="alternate"\s+hreflang="[^"]+"\s+href="[^"]+"[^>]*/?>',
    re.IGNORECASE,
)

# Match the language switcher block in head (some pages have it inside <link rel="alternate">)
HREFLANG_BLOCK_RE = re.compile(
    r'(<link\s+rel="alternate"\s+hreflang="[^"]+"\s+href="[^"]+"[^>]*/?>\s*\n?)+',
    re.IGNORECASE,
)


def detect_page_language(rel: str) -> str:
    """Determine which language this page is in based on its path."""
    parts = rel.split("/")
    if parts and parts[0] in LANGUAGES and parts[0] != "en":
        return parts[0]
    return "en"


def language_alternative_exists(rel: str, lang: str) -> bool:
    """Check if a translation of this page exists for the given language."""
    if lang == "en":
        # English is the canonical version — use the original path
        path = ROOT / rel
        return path.exists()
    # For non-English: language pages live under /<lang>/ at the root only
    # Currently we only have full landing pages: /hi/, /bn/, /es/, /pa/
    # So only the homepage equivalent has translations
    if rel == "index.html":
        return (ROOT / lang / "index.html").exists()
    return False


def build_hreflang_block(rel: str) -> str:
    """Build the correct hreflang block for this specific page."""
    page_lang = detect_page_language(rel)
    lines = []
    # The current page is canonical for its language
    if page_lang == "en":
        canonical_url = f"{DOMAIN}/{rel}".replace("/index.html", "/")
    else:
        # Non-English language pages
        canonical_url = f"{DOMAIN}/{page_lang}/"

    # Always self-reference
    lines.append(f'<link rel="alternate" hreflang="{page_lang}" href="{canonical_url}" />')

    # Add other language variants ONLY if they exist
    for lang in LANGUAGES:
        if lang == page_lang:
            continue
        if language_alternative_exists(rel, lang):
            if lang == "en":
                alt_url = f"{DOMAIN}/{rel}".replace("/index.html", "/")
            else:
                alt_url = f"{DOMAIN}/{lang}/"
            lines.append(f'<link rel="alternate" hreflang="{lang}" href="{alt_url}" />')

    # x-default always points to English
    if page_lang == "en":
        x_default = f"{DOMAIN}/{rel}".replace("/index.html", "/")
    else:
        x_default = f"{DOMAIN}/"
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{x_default}" />')

    return "\n".join(lines) + "\n"


def fix_page(html: str, rel: str) -> tuple[str, bool]:
    """Strip all existing hreflang tags and replace with the correct block."""
    page_lang = detect_page_language(rel)

    # Only fix language pages (homepage variants) and the homepage itself.
    # For deep neighborhood/zip/etc pages, we have NO translations, so just
    # remove all hreflang tags entirely (no broken refs).
    is_homepage_or_lang = (rel == "index.html" or rel in [f"{l}/index.html" for l in LANGUAGES if l != "en"])

    # Find existing hreflang tags
    existing = HREFLANG_RE.findall(html)
    if not existing and not is_homepage_or_lang:
        return html, False  # nothing to do

    # Strip all existing hreflang
    new_html = HREFLANG_RE.sub("", html)

    if is_homepage_or_lang:
        # Insert proper hreflang block
        block = build_hreflang_block(rel)
        # Insert just after canonical link or in <head>
        if "<link rel=\"canonical\"" in new_html:
            new_html = re.sub(
                r'(<link\s+rel="canonical"[^>]*/?>)',
                r"\1\n" + block.rstrip(),
                new_html,
                count=1,
            )
        elif "</head>" in new_html:
            new_html = new_html.replace("</head>", block + "</head>", 1)

    # Clean up any orphan whitespace from the strip
    new_html = re.sub(r"\n{3,}", "\n\n", new_html)
    return new_html, new_html != html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    counts = {"changed": 0, "unchanged": 0, "tags_stripped": 0, "blocks_added": 0}
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name == "404.html":
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = p.relative_to(ROOT).as_posix()
        before_hreflang_count = len(HREFLANG_RE.findall(html))
        new_html, changed = fix_page(html, rel)
        after_hreflang_count = len(HREFLANG_RE.findall(new_html))

        if changed:
            counts["changed"] += 1
            counts["tags_stripped"] += max(0, before_hreflang_count - after_hreflang_count)
            if args.apply:
                p.write_text(new_html, encoding="utf-8")
        else:
            counts["unchanged"] += 1

    print("=== Summary ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
