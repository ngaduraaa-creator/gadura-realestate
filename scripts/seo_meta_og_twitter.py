#!/usr/bin/env python3
"""Tasks 4, 5, 7, 8: Fix meta descriptions, titles, OG tags, Twitter cards."""

import re
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"
DEFAULT_IMG = "https://gadurarealestate.com/images/logo-full.png"
SITE_NAME = "Gadura Real Estate LLC"

def file_to_url(f: Path) -> str:
    rel = f.relative_to(BASE)
    parts = rel.parts
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    return "/" + str(rel)

def truncate(text: str, max_len: int) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    # Try to cut at sentence or word boundary
    for sep in [". ", "! ", "? ", ", ", " "]:
        idx = cut.rfind(sep)
        if idx > max_len * 0.7:
            return cut[:idx + (1 if sep.endswith(" ") else 0)].rstrip(" ,")
    return cut[:max_len - 3].rstrip() + "..."

def shorten_title(title: str) -> str:
    """Shorten title to under 60 chars."""
    title = title.strip()
    if len(title) <= 60:
        return title
    # Remove common long suffixes
    for suffix in [" – Gadura Real Estate LLC", " | Gadura Real Estate LLC",
                   " – Queens & Long Island Homes For Sale", " - Gadura Real Estate LLC",
                   " | Queens NY Real Estate", " | Queens & Long Island",
                   " Queens & Long Island"]:
        if title.endswith(suffix):
            short = title[:-len(suffix)].strip(" –|")
            brand = " | Gadura RE"
            if len(short + brand) <= 60:
                return short + brand
            return truncate(short, 60)
    # Generic shorten
    if " | " in title:
        parts = title.split(" | ")
        if len(parts[0]) + len(" | Gadura RE") <= 60:
            return parts[0] + " | Gadura RE"
        return truncate(parts[0], 60)
    return truncate(title, 60)

def get_page_type(f: Path) -> str:
    parts = f.parts
    path_str = str(f)
    if "/blog/" in path_str:
        return "article"
    return "website"

stats = {"meta_desc_fixed": 0, "title_fixed": 0, "og_added": 0, "twitter_added": 0, "files_changed": 0}

for html_file in sorted(BASE.rglob("*.html")):
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    original = content
    url_path = file_to_url(html_file)
    canonical_url = DOMAIN + url_path
    og_type = get_page_type(html_file)

    # ── Extract current title ──────────────────────────────────────────────
    title_m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    cur_title = title_m.group(1).strip() if title_m else ""

    # ── Extract current meta description ──────────────────────────────────
    desc_m = re.search(r'<meta\s+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']|'
                       r'<meta\s+content=["\']([^"\']*)["\'][^>]*name=["\']description["\']',
                       content, re.IGNORECASE)
    cur_desc = (desc_m.group(1) or desc_m.group(2) or "").strip() if desc_m else ""

    # ── Task 5: Shorten title ──────────────────────────────────────────────
    if cur_title and len(cur_title) > 60:
        new_title = shorten_title(cur_title)
        if new_title != cur_title:
            content = re.sub(r'(<title[^>]*>).*?(</title>)', 
                           lambda m: m.group(1) + new_title + m.group(2),
                           content, count=1, flags=re.IGNORECASE | re.DOTALL)
            cur_title = new_title
            stats["title_fixed"] += 1

    # ── Task 4: Shorten meta description ─────────────────────────────────
    if cur_desc and len(cur_desc) > 160:
        new_desc = truncate(cur_desc, 155)
        if new_desc != cur_desc:
            content = content.replace(cur_desc, new_desc, 1)
            cur_desc = new_desc
            stats["meta_desc_fixed"] += 1

    # Use title/desc for OG (fallback values)
    og_title = cur_title[:60] if cur_title else SITE_NAME
    og_desc = cur_desc[:155] if cur_desc else f"Buy, sell, and rent homes in Queens & Long Island with {SITE_NAME}. Call (718) 850-0010."

    # ── Check existing OG tags ─────────────────────────────────────────────
    has_og_title    = bool(re.search(r'og:title',       content, re.IGNORECASE))
    has_og_desc     = bool(re.search(r'og:description', content, re.IGNORECASE))
    has_og_image    = bool(re.search(r'og:image',       content, re.IGNORECASE))
    has_og_url      = bool(re.search(r'og:url',         content, re.IGNORECASE))
    has_og_type     = bool(re.search(r'og:type',        content, re.IGNORECASE))
    has_og_sitename = bool(re.search(r'og:site_name',   content, re.IGNORECASE))

    has_tw_card   = bool(re.search(r'twitter:card',        content, re.IGNORECASE))
    has_tw_title  = bool(re.search(r'twitter:title',       content, re.IGNORECASE))
    has_tw_desc   = bool(re.search(r'twitter:description', content, re.IGNORECASE))
    has_tw_image  = bool(re.search(r'twitter:image',       content, re.IGNORECASE))

    og_needed = not (has_og_title and has_og_desc and has_og_image and has_og_url and has_og_type and has_og_sitename)
    tw_needed = not (has_tw_card and has_tw_title and has_tw_desc and has_tw_image)

    if not og_needed and not tw_needed:
        if content != original:
            html_file.write_text(content, encoding="utf-8")
            stats["files_changed"] += 1
        continue

    # Build missing tags block
    new_tags = ""

    # ── Task 7: OG tags ────────────────────────────────────────────────────
    if not has_og_title:
        new_tags += f'  <meta property="og:title" content="{og_title}">\n'
    if not has_og_desc:
        new_tags += f'  <meta property="og:description" content="{og_desc}">\n'
    if not has_og_url:
        new_tags += f'  <meta property="og:url" content="{canonical_url}">\n'
    if not has_og_type:
        new_tags += f'  <meta property="og:type" content="{og_type}">\n'
    if not has_og_image:
        new_tags += f'  <meta property="og:image" content="{DEFAULT_IMG}">\n'
    if not has_og_sitename:
        new_tags += f'  <meta property="og:site_name" content="{SITE_NAME}">\n'

    # ── Task 8: Twitter tags ───────────────────────────────────────────────
    if not has_tw_card:
        new_tags += f'  <meta name="twitter:card" content="summary_large_image">\n'
    if not has_tw_title:
        new_tags += f'  <meta name="twitter:title" content="{og_title}">\n'
    if not has_tw_desc:
        new_tags += f'  <meta name="twitter:description" content="{og_desc}">\n'
    if not has_tw_image:
        new_tags += f'  <meta name="twitter:image" content="{DEFAULT_IMG}">\n'

    if new_tags:
        # Insert before </head>
        if '</head>' in content:
            content = content.replace('</head>', new_tags + '</head>', 1)
            if not has_og_title:
                stats["og_added"] += 1
            if not has_tw_card:
                stats["twitter_added"] += 1

    if content != original:
        html_file.write_text(content, encoding="utf-8")
        stats["files_changed"] += 1

print("=== TASKS 4, 5, 7, 8 RESULTS ===")
print(f"Title tags shortened (>60 chars):      {stats['title_fixed']}")
print(f"Meta descriptions shortened (>160):    {stats['meta_desc_fixed']}")
print(f"Pages with new/completed OG tags:      {stats['og_added']}")
print(f"Pages with new Twitter card tags:      {stats['twitter_added']}")
print(f"Total files modified:                  {stats['files_changed']}")
