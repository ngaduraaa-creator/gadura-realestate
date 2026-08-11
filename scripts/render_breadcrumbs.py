#!/usr/bin/env python3
"""
render_breadcrumbs.py — render a VISIBLE, crawlable breadcrumb on every page that
already declares BreadcrumbList JSON-LD but shows no clickable breadcrumb.

Audit finding (high): ~1,150+ deep pages (zip, long-island, neighborhoods,
market-reports, agents, ...) carry breadcrumb *schema* but no on-page breadcrumb,
so they pass zero link equity UP to their hub/pillar and users can't climb the
hierarchy. Schema alone creates no <a>. This turns the existing
id="ai-breadcrumb-schema" data into real internal links with keyword-rich anchors,
cutting effective click-depth on the biggest money clusters.

Self-styled (inline) so it renders correctly regardless of which stylesheet a
page loads. Idempotent. Static-site safe (stdlib only).

    python3 scripts/render_breadcrumbs.py --dry-run --limit 5   # preview
    python3 scripts/render_breadcrumbs.py                       # apply
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRY = "--dry-run" in sys.argv
LIMIT = None
for a in sys.argv:
    if a.startswith("--limit"):
        LIMIT = int(a.split("=")[1]) if "=" in a else int(sys.argv[sys.argv.index(a) + 1])

EXCLUDE_DIRS = {".git", ".github", ".claude", "_includes", "scripts", "admin",
                "data", "research", "v2", "docs", "ai-citations", "ai-monitoring", "node_modules"}
EXCLUDE_FILES = {"404.html"}
MARKER = 'data-gre-breadcrumb'

LINK = "color:#1b2a6b;text-decoration:none;"
SEP = '<span aria-hidden="true" style="margin:0 7px;color:#9aa4b2;">&rsaquo;</span>'
NAV_OPEN = ('<nav ' + MARKER + ' aria-label="Breadcrumb" '
            'style="max-width:1200px;margin:0 auto;padding:10px 20px;'
            'font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;'
            'font-size:.82rem;line-height:1.6;color:#5b6675;word-break:break-word;">')


def rel_path(url: str) -> str:
    for pre in ("https://gadurarealestate.com", "http://gadurarealestate.com"):
        if url.startswith(pre):
            return url[len(pre):] or "/"
    return url


def extract_breadcrumb(t: str) -> list[dict] | None:
    m = re.search(r'<script type="application/ld\+json" id="ai-breadcrumb-schema"[^>]*>(.*?)</script>',
                  t, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(1).strip())
    except Exception:
        return None
    if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
        items = data.get("itemListElement", [])
        items = sorted(items, key=lambda x: x.get("position", 0))
        out = []
        for it in items:
            name = it.get("name")
            url = it.get("item")
            if name:
                out.append({"name": str(name), "url": str(url) if url else ""})
        return out or None
    return None


def build_nav(items: list[dict]) -> str:
    parts = [NAV_OPEN]
    last = len(items) - 1
    for i, it in enumerate(items):
        name = html.escape(it["name"])
        if i == last or not it["url"]:
            parts.append(f'<span style="color:#5b6675;">{name}</span>')
        else:
            href = html.escape(rel_path(it["url"]))
            parts.append(f'<a href="{href}" style="{LINK}">{name}</a>')
            parts.append(SEP)
    parts.append("</nav>")
    return "".join(parts)


def already_has_visible(t: str) -> bool:
    return (MARKER in t
            or re.search(r'class="[^"]*breadcrumb[^"]*"', t) is not None
            or 'aria-label="Breadcrumb"' in t.replace(MARKER, ""))


def insert(t: str, nav: str) -> str | None:
    # After the first </header>; else right after the opening <body ...>.
    m = re.search(r'</header>', t, re.I)
    if m:
        i = m.end()
        return t[:i] + "\n" + nav + t[i:]
    m = re.search(r'<body[^>]*>', t, re.I)
    if m:
        i = m.end()
        return t[:i] + "\n" + nav + t[i:]
    return None


def collect() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDE_FILES:
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    pages = collect()
    done = skipped_visible = no_schema = no_anchor = 0
    changed = []
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="ignore")
        if already_has_visible(t):
            skipped_visible += 1
            continue
        items = extract_breadcrumb(t)
        if not items or len(items) < 2:
            no_schema += 1
            continue
        nav = build_nav(items)
        nt = insert(t, nav)
        if nt is None:
            no_anchor += 1
            continue
        changed.append((p, nav))
        if not DRY:
            p.write_text(nt, encoding="utf-8")
        done += 1
        if LIMIT and done >= LIMIT:
            break

    print(f"pages scanned: {len(pages)}")
    print(f"breadcrumbs {'would be ' if DRY else ''}rendered: {done}")
    print(f"skipped (already visible): {skipped_visible}")
    print(f"skipped (no/short breadcrumb schema): {no_schema}")
    print(f"skipped (no <header>/<body> anchor): {no_anchor}")
    if DRY and changed:
        print("\n--- sample output ---")
        for p, nav in changed[:3]:
            print(f"\n[{p.relative_to(ROOT)}]")
            print("  " + nav[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
