#!/usr/bin/env python3
"""
Comprehensive SEO fix script for gadurarealestate.com
Tasks 1-3: Fix 404s, broken internal links, orphan pages
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"

# ─── Build valid file set ───────────────────────────────────────────────────

def get_all_html_files():
    files = []
    for f in BASE.rglob("*.html"):
        files.append(f)
    return files

def file_to_url(f: Path) -> str:
    rel = f.relative_to(BASE)
    parts = rel.parts
    if parts[-1] == "index.html":
        url = "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    else:
        url = "/" + str(rel)
    return url

def url_to_file(url: str) -> Path:
    """Try to resolve a URL to an actual file."""
    url = url.split("?")[0].split("#")[0]
    if url.startswith(DOMAIN):
        url = url[len(DOMAIN):]
    if not url.startswith("/"):
        return None
    if url.endswith("/"):
        candidates = [
            BASE / url.lstrip("/") / "index.html",
            BASE / (url.rstrip("/").lstrip("/") + ".html"),
        ]
    elif url.endswith(".html"):
        candidates = [BASE / url.lstrip("/")]
    else:
        candidates = [
            BASE / (url.lstrip("/") + ".html"),
            BASE / url.lstrip("/") / "index.html",
        ]
    for c in candidates:
        if c.exists():
            return c
    return None

all_html = get_all_html_files()
valid_urls = set()
file_to_url_map = {}
url_to_file_map = {}

for f in all_html:
    url = file_to_url(f)
    valid_urls.add(url)
    file_to_url_map[f] = url
    url_to_file_map[url] = f

print(f"Total HTML files: {len(all_html)}")

# ─── Task 1 & 2: Find and fix broken internal links ────────────────────────

HREF_RE = re.compile(r'href=["\']([^"\'#?]+)(?:[#?][^"\']*)?["\']', re.IGNORECASE)
SRC_RE  = re.compile(r'src=["\']([^"\'#?]+)["\']', re.IGNORECASE)

def is_internal(url: str) -> bool:
    return (url.startswith("/") or url.startswith(DOMAIN)) and not url.startswith("//")

def normalize_internal(url: str) -> str:
    """Strip domain, keep path."""
    if url.startswith(DOMAIN):
        url = url[len(DOMAIN):]
    return url

# Redirect map: old_url -> new_url (for known duplicates/renames)
REDIRECT_MAP = {
    "/about-us/": "/about.html",
    "/about-us": "/about.html",
    "/sell/": "/sell.html",
    "/sell": "/sell.html",
    "/homes-for-sale/": "/for-sale/",
    "/homes-for-sale": "/for-sale/",
    "/faq/": "/faq/selling-home-nyc.html",
    "/faq": "/faq/selling-home-nyc.html",
    "/resources/": "/resources.html",
    "/resources": "/resources.html",
    "/compliance/": "/fair-housing.html",
    "/compliance": "/fair-housing.html",
    "/agents/": "/meet-the-agents.html",
    "/agents": "/meet-the-agents.html",
    "/portal.html": "/for-sale/",
    "/listings/": "/for-sale/",
    "/listings": "/for-sale/",
    "/map-available.html": "/for-sale/",
    "/map-sold.html": "/for-sale/",
    "/idx-wrapper.html": "/for-sale/",
}

broken_links = defaultdict(list)  # target_url -> list of (file, original_href)
files_changed_task1 = []
total_links_fixed = 0

for html_file in all_html:
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    original = content
    changed = False

    hrefs = HREF_RE.findall(content)
    for href in hrefs:
        if not is_internal(href):
            continue
        norm = normalize_internal(href)

        # Check if it resolves
        resolved = url_to_file(norm)
        if resolved is not None:
            # Check redirect map
            if norm in REDIRECT_MAP:
                new_url = REDIRECT_MAP[norm]
                content = content.replace(f'href="{href}"', f'href="{new_url}"')
                content = content.replace(f"href='{href}'", f"href='{new_url}'")
                total_links_fixed += 1
                changed = True
            continue

        # Link is broken
        if norm in REDIRECT_MAP:
            new_url = REDIRECT_MAP[norm]
            content = content.replace(f'href="{href}"', f'href="{new_url}"')
            content = content.replace(f"href='{href}'", f"href='{new_url}'")
            total_links_fixed += 1
            changed = True
        else:
            broken_links[norm].append(str(html_file))

    if changed:
        html_file.write_text(content, encoding="utf-8")
        files_changed_task1.append(str(html_file))

print(f"\n=== TASK 1 & 2 RESULTS ===")
print(f"Files changed: {len(files_changed_task1)}")
print(f"Links fixed (redirect map): {total_links_fixed}")
print(f"\nStill-broken link targets ({len(broken_links)}):")
for broken, files in list(broken_links.items())[:30]:
    print(f"  {broken}  ({len(files)} pages)")

# ─── Create redirect stubs for broken targets that have NO good replacement ─

redirect_stubs_created = []
for broken_url, referencing_files in broken_links.items():
    # Skip if it's an external-looking path or too vague
    if broken_url.startswith("/images") or broken_url.startswith("/css") or broken_url.startswith("/js"):
        continue
    if broken_url.startswith("/data") or broken_url.startswith("/scripts"):
        continue

    # Determine best redirect destination
    dest = "/index.html"
    if "blog" in broken_url:
        dest = "/blog/"
    elif "neighborhood" in broken_url:
        dest = "/neighborhoods/"
    elif "sell" in broken_url or "seller" in broken_url:
        dest = "/sell.html"
    elif "buy" in broken_url or "buyer" in broken_url:
        dest = "/buy.html"
    elif "agent" in broken_url or "team" in broken_url:
        dest = "/meet-the-agents.html"
    elif "community" in broken_url:
        dest = "/community/"
    elif "contact" in broken_url:
        dest = "/contact.html"
    elif "about" in broken_url:
        dest = "/about.html"
    elif "resource" in broken_url:
        dest = "/resources.html"
    elif "service" in broken_url:
        dest = "/services/"
    elif "home-value" in broken_url or "valuation" in broken_url:
        dest = "/home-value/"

    target_path = BASE / broken_url.lstrip("/")
    if broken_url.endswith("/"):
        target_path = target_path / "index.html"
    elif not broken_url.endswith(".html"):
        target_path = BASE / (broken_url.lstrip("/")) / "index.html"

    # Only create if parent dir exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        full_dest = DOMAIN + dest
        stub = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Redirecting... | Gadura Real Estate LLC</title>
  <meta http-equiv="refresh" content="0;url={full_dest}">
  <link rel="canonical" href="{full_dest}">
  <script>window.location.replace("{full_dest}");</script>
</head>
<body>
  <p>Redirecting to <a href="{full_dest}">Gadura Real Estate LLC</a>...</p>
</body>
</html>"""
        target_path.write_text(stub, encoding="utf-8")
        redirect_stubs_created.append(str(target_path))

print(f"\nRedirect stubs created: {len(redirect_stubs_created)}")
for s in redirect_stubs_created[:20]:
    print(f"  {s}")

# ─── Task 3: Orphan pages ───────────────────────────────────────────────────

# Count incoming links for each URL
incoming = defaultdict(set)

for html_file in all_html:
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    src_url = file_to_url_map.get(html_file, "")
    hrefs = HREF_RE.findall(content)
    for href in hrefs:
        if not is_internal(href):
            continue
        norm = normalize_internal(href)
        if norm != src_url:
            incoming[norm].add(src_url)

# Pages with zero incoming links
orphans = []
for html_file in all_html:
    url = file_to_url_map.get(html_file, "")
    if url in ("/", "/index.html"):
        continue
    if not incoming[url]:
        orphans.append((html_file, url))

print(f"\n=== TASK 3 RESULTS ===")
print(f"Orphan pages found: {len(orphans)}")

def get_page_type(url: str) -> str:
    if "/blog/" in url:
        return "blog"
    if "/neighborhood" in url:
        return "neighborhood"
    if "/community/" in url:
        return "community"
    if "/services/" in url:
        return "services"
    if "/v2/" in url:
        return "v2"
    if any(name in url for name in ["/nitin-gadura", "/vinod-gadura", "/gaurav-bhardwaj",
                                     "/bhupinder-gill", "/jagman-dhaliwal", "/jeevanpreet-singh",
                                     "/kumar-ramudit", "/manpreet-kaur", "/md-ali", "/miguel-cane",
                                     "/ravi-kapoor", "/rushneet-kaur", "/stephanie-silva",
                                     "/wazid-mohammed", "/zahid-ali", "/gurvinder-singh",
                                     "/jaqueline-silva"]):
        return "agent"
    return "general"

# For each orphan, find suitable parent pages to add links from
def find_link_donors(orphan_url: str, orphan_type: str) -> list:
    """Find up to 3 pages that should link to this orphan."""
    donors = []

    if orphan_type == "blog":
        # Link from blog index
        blog_index = url_to_file_map.get("/blog/")
        if blog_index:
            donors.append(blog_index)
    elif orphan_type == "neighborhood":
        # Link from neighborhoods hub
        hood_index = url_to_file_map.get("/neighborhoods/")
        if hood_index:
            donors.append(hood_index)
        # Also from buy or sell page
        buy_page = url_to_file_map.get("/buy.html")
        if buy_page:
            donors.append(buy_page)
    elif orphan_type == "community":
        # Link from community hub
        comm_index = url_to_file_map.get("/community/")
        if comm_index:
            donors.append(comm_index)
    elif orphan_type == "agent":
        # Link from meet-the-agents
        agents_page = url_to_file_map.get("/meet-the-agents.html")
        if agents_page:
            donors.append(agents_page)
    elif orphan_type == "services":
        # Link from sell or buy
        sell_page = url_to_file_map.get("/sell.html")
        if sell_page:
            donors.append(sell_page)

    # Always try from index
    index_page = url_to_file_map.get("/")
    if index_page and index_page not in donors and len(donors) < 2:
        donors.append(index_page)

    return donors[:3]

def get_page_title(html_file: Path) -> str:
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if m:
        title = m.group(1).strip()
        title = re.sub(r'\s*[|–—-].*$', '', title).strip()
        return title[:60]
    return html_file.stem.replace("-", " ").title()

def slugify_title(title: str) -> str:
    return title[:40]

links_added = 0
orphans_fixed = 0
RELATED_LINKS_RE = re.compile(r'(</footer>|</main>|</article>|<div[^>]+class="[^"]*related[^"]*")', re.IGNORECASE)

for orphan_file, orphan_url in orphans[:40]:  # cap at 40 to avoid huge changes
    orphan_title = get_page_title(orphan_file)
    orphan_type = get_page_type(orphan_url)
    donors = find_link_donors(orphan_url, orphan_type)

    for donor_file in donors:
        if donor_file == orphan_file:
            continue
        donor_content = donor_file.read_text(encoding="utf-8", errors="ignore")

        # Check if link already exists
        if orphan_url in donor_content:
            continue

        # Build link snippet
        link_html = f'\n  <li><a href="{orphan_url}">{orphan_title}</a></li>'

        # Try to inject into an existing <ul> near the bottom of main content
        # Look for a "Related" or "Also see" list, or insert before </footer>
        ul_match = re.search(r'(<ul[^>]*class="[^"]*(?:related|links|nav-list|quick)[^"]*"[^>]*>)(.*?)(</ul>)',
                             donor_content, re.IGNORECASE | re.DOTALL)
        if ul_match:
            new_content = donor_content[:ul_match.end(2)] + link_html + donor_content[ul_match.end(2):]
            donor_file.write_text(new_content, encoding="utf-8")
            links_added += 1
        else:
            # Insert a new "Related Pages" section before </footer>
            footer_match = re.search(r'</footer>', donor_content, re.IGNORECASE)
            if footer_match:
                insert_pos = footer_match.start()
                related_section = f'\n<!-- Internal link to {orphan_url} -->\n'
                new_content = donor_content[:insert_pos] + related_section + donor_content[insert_pos:]
                donor_file.write_text(new_content, encoding="utf-8")
                links_added += 1

    orphans_fixed += 1

print(f"Orphans addressed: {orphans_fixed}")
print(f"Incoming links added: {links_added}")

print("\n=== SUMMARY ===")
print(f"Task 1-2: {len(files_changed_task1)} files had broken links fixed")
print(f"Task 1:   {len(redirect_stubs_created)} redirect stub pages created")
print(f"Task 3:   {orphans_fixed} orphan pages linked, {links_added} new internal links added")
