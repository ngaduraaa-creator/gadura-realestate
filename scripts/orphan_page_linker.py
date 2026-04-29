#!/usr/bin/env python3
"""
orphan_page_linker.py — Detect orphan pages (pages with zero internal inbound
links) and propose contextual links from authoritative parent pages.

Approach:
1. Build a map of every <a href="..."> outbound link across the entire site
2. Identify orphan pages (in sitemap but not linked anywhere)
3. For each orphan, find the most relevant "parent" page based on URL structure
4. Add a contextual link from the parent's "Related neighborhoods" or footer block

Idempotent. Won't add duplicate links. Conservative: only adds 1 inbound link
per orphan from the most-relevant parent.
"""
from __future__ import annotations
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "gadurarealestate.com"
SKIP_PARTS = {".git", ".github", "_includes", "scripts", "_site", ".netlify", "well-known", "node_modules"}
SKIP_FILES = {"404.html", "indexnow-submit.html", "idx-wrapper.html"}

HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)


def normalize(url: str) -> str:
    """Convert to relative path form like 'neighborhoods/queens.html'."""
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
        if DOMAIN not in parsed.netloc:
            return ""  # external
        path = parsed.path
    elif url.startswith("//"):
        return ""
    elif url.startswith("/"):
        path = url
    else:
        return ""
    if path.endswith("/"):
        path += "index.html"
    return path.lstrip("/")


def find_parent_for_orphan(orphan_path: str, all_pages: set[str]) -> str | None:
    """Find the best parent page to link from."""
    parts = orphan_path.split("/")
    # Try walking up the path
    for i in range(len(parts) - 1, 0, -1):
        parent_dir = "/".join(parts[:i])
        # Try parent directory's index.html
        parent_index = f"{parent_dir}/index.html"
        if parent_index in all_pages and parent_index != orphan_path:
            return parent_index
        # Try parent directory's [name].html
        parent_html = f"{parent_dir}.html"
        if parent_html in all_pages and parent_html != orphan_path:
            return parent_html
    # Fallback: homepage
    if "index.html" in all_pages:
        return "index.html"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # Step 1: collect all pages
    all_pages: set[str] = set()
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_PARTS for part in p.relative_to(ROOT).parts):
            continue
        if p.name in SKIP_FILES:
            continue
        rel = p.relative_to(ROOT).as_posix()
        all_pages.add(rel)

    # Step 2: build inbound link map
    inbound: dict[str, set[str]] = defaultdict(set)
    for src_rel in all_pages:
        try:
            html = (ROOT / src_rel).read_text(encoding="utf-8")
        except Exception:
            continue
        for match in HREF_RE.findall(html):
            target = normalize(match)
            if target and target in all_pages and target != src_rel:
                inbound[target].add(src_rel)

    # Step 3: identify orphans
    orphans = [page for page in all_pages if not inbound[page]]
    print(f"Total pages:  {len(all_pages)}")
    print(f"Orphan pages: {len(orphans)}")

    if not orphans:
        print("No orphans found — nothing to do.")
        return 0

    # Step 4: for each orphan, find the best parent and add a link
    fixes = []
    for orphan in orphans[:50]:  # cap at 50 per run for safety
        parent = find_parent_for_orphan(orphan, all_pages)
        if not parent:
            continue
        # Determine link text from orphan filename
        slug = Path(orphan).stem.replace("-", " ").title()
        if slug == "Index":
            slug = Path(orphan).parts[-2].replace("-", " ").title() if len(Path(orphan).parts) > 1 else "Page"
        href = "/" + orphan.replace("/index.html", "/")
        fixes.append({"parent": parent, "orphan_link": href, "anchor_text": slug})

    print(f"\nProposing {len(fixes)} new internal links")
    if args.apply:
        # Group fixes by parent to add as a VISIBLE "Related" footer block.
        # CRITICAL: NEVER hide these links (display:none + aria-hidden = cloaking
        # = manual action risk). Links must be genuinely visible and useful.
        by_parent = defaultdict(list)
        for fix in fixes:
            by_parent[fix["parent"]].append(fix)

        modified_count = 0
        for parent, parent_fixes in by_parent.items():
            parent_path = ROOT / parent
            html = parent_path.read_text(encoding="utf-8")
            # Build a visible "More from this section" block
            links = "\n".join(
                f'    <li><a href="{f["orphan_link"]}">{f["anchor_text"]}</a></li>'
                for f in parent_fixes
            )
            block = f"""
<!-- Auto-generated: contextual links to related pages -->
<aside class="related-resources" style="margin:32px 0;padding:24px;background:#f5f5f5;border-radius:8px;">
  <h3 style="font-family:Montserrat,sans-serif;color:#1B2A6B;font-size:18px;margin-bottom:12px;">More from this section</h3>
  <ul style="list-style:disc;padding-left:24px;line-height:1.8;">
{links}
  </ul>
</aside>
"""
            # Skip if already added
            if 'class="related-resources"' in html:
                continue
            # Insert before </body> or before the footer
            if "<footer" in html:
                new_html = re.sub(r"<footer", block + "<footer", html, count=1)
            elif "</body>" in html:
                new_html = html.replace("</body>", block + "</body>", 1)
            else:
                continue
            parent_path.write_text(new_html, encoding="utf-8")
            modified_count += 1
        print(f"  Modified {modified_count} parent pages with VISIBLE related-links blocks")

    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
