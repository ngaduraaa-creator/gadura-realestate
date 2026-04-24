#!/usr/bin/env python3
"""Internal-link graph audit for gadurarealestate.com.

Outputs:
  - Total pages / total internal links
  - Orphans (0 inbound links, excluding hub index files)
  - Near-orphans (1 inbound link)
  - Broken internal links (href target missing on disk)
  - Top 20 most-linked pages
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urldefrag

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "scripts", "_includes", "data", "v2", "assets_bak"}
HREF_RE = re.compile(r'''href=["']([^"']+)["']''', re.IGNORECASE)

# Pages we tolerate as orphans (index/hub/entry pages that are linked from nav or external)
ORPHAN_WHITELIST = {
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "blog-sitemap.xml",
    "sitemap-index.xml",
}


def walk_html() -> list[Path]:
    pages = []
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        pages.append(p)
    return pages


def normalize(target: str, source_dir: Path) -> str | None:
    """Resolve an href to a site-relative path string, or None if external/unsupported."""
    if not target:
        return None
    target, _ = urldefrag(target)
    target = unquote(target)
    if target.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "#")):
        return None
    if target.startswith("/"):
        rel = target.lstrip("/")
        abs_path = ROOT / rel
    else:
        abs_path = (source_dir / target).resolve()
    try:
        rel_path = abs_path.relative_to(ROOT)
    except ValueError:
        return None
    s = str(rel_path)
    # Normalize directory / root links to index.html
    if s in ("", "."):
        return "index.html"
    if abs_path.is_dir() and abs_path.exists():
        return s.rstrip("/") + "/index.html"
    if s.endswith("/"):
        return s.rstrip("/") + "/index.html"
    return s


def main() -> None:
    pages = walk_html()
    page_set = {str(p.relative_to(ROOT)) for p in pages}

    inbound: Counter[str] = Counter()
    outbound: dict[str, set[str]] = defaultdict(set)
    broken: list[tuple[str, str]] = []

    for page in pages:
        rel = str(page.relative_to(ROOT))
        text = page.read_text(encoding="utf-8", errors="ignore")
        for href in HREF_RE.findall(text):
            tgt = normalize(href, page.parent)
            if tgt is None:
                continue
            outbound[rel].add(tgt)
            if tgt in page_set:
                if tgt != rel:
                    inbound[tgt] += 1
            else:
                # Only flag as broken if it looks like an internal HTML target
                if tgt.endswith(".html") or tgt.endswith("/index.html"):
                    broken.append((rel, tgt))

    print(f"Pages audited: {len(pages)}")
    print(f"Total outbound internal links: {sum(len(v) for v in outbound.values())}")
    print()

    # Orphans
    orphans = sorted(
        p for p in page_set
        if inbound[p] == 0 and Path(p).name not in ORPHAN_WHITELIST
    )
    print(f"Orphan pages (0 inbound, excluding whitelist): {len(orphans)}")
    for p in orphans[:30]:
        print(f"  - {p}")
    if len(orphans) > 30:
        print(f"  ... and {len(orphans) - 30} more")
    print()

    # Near-orphans
    near = sorted(p for p in page_set if inbound[p] == 1)
    print(f"Near-orphans (exactly 1 inbound): {len(near)}")
    for p in near[:20]:
        print(f"  - {p}")
    if len(near) > 20:
        print(f"  ... and {len(near) - 20} more")
    print()

    # Broken
    unique_broken = sorted(set(broken))
    print(f"Broken internal HTML links: {len(unique_broken)}")
    for src, tgt in unique_broken[:30]:
        print(f"  - {src} -> {tgt}")
    if len(unique_broken) > 30:
        print(f"  ... and {len(unique_broken) - 30} more")
    print()

    # Top linked
    print("Top 20 most-linked pages:")
    for page, count in inbound.most_common(20):
        print(f"  {count:>5}  {page}")


if __name__ == "__main__":
    main()
