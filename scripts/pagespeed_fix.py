#!/usr/bin/env python3
"""Page speed optimizations across all HTML files."""
import re
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")

stats = {"lazy_added": 0, "preconnect_added": 0, "defer_added": 0,
         "font_display_added": 0, "files_changed": 0}

# Font preconnect block to add
PRECONNECT = """  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>"""

for html_file in BASE.rglob("*.html"):
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    if len(content) < 500:
        continue
    original = content

    # 1. Add loading="lazy" to all non-hero images
    # Skip first img (likely hero/logo), lazy-load the rest
    img_count = [0]
    def add_lazy(m):
        img_count[0] += 1
        tag = m.group(0)
        if 'loading=' in tag.lower():
            return tag
        # First image or logo = eager, rest = lazy
        if img_count[0] <= 1 or 'logo' in tag.lower():
            if 'fetchpriority' not in tag.lower():
                tag = tag.replace('<img ', '<img fetchpriority="high" ', 1)
            return tag
        tag = tag.replace('<img ', '<img loading="lazy" ', 1)
        stats["lazy_added"] += 1
        return tag

    new_content = re.sub(r'<img\s[^>]+>', add_lazy, content, flags=re.IGNORECASE)

    # 2. Defer non-critical JS (not inline, not GA, not ld+json)
    def defer_script(m):
        tag = m.group(0)
        if any(x in tag for x in ['defer', 'async', 'type="application/ld+json',
                                    "type='application/ld+json", 'googletagmanager',
                                    'gtag', 'GA_ID', 'inline']):
            return tag
        if 'src=' in tag and 'defer' not in tag:
            tag = tag.replace('<script ', '<script defer ', 1)
            stats["defer_added"] += 1
        return tag

    new_content = re.sub(r'<script[^>]+src=[^>]+>', defer_script, new_content, flags=re.IGNORECASE)

    # 3. Add preconnect for Google Fonts if missing
    if 'fonts.googleapis.com' in new_content and 'rel="preconnect"' not in new_content:
        new_content = new_content.replace('<head>', '<head>\n' + PRECONNECT, 1)
        stats["preconnect_added"] += 1

    # 4. Add width/height to images missing dimensions (helps CLS)
    # Only add if completely missing both
    def add_dimensions(m):
        tag = m.group(0)
        if 'width=' in tag.lower() and 'height=' in tag.lower():
            return tag
        src = re.search(r'src=["\']([^"\']+)["\']', tag)
        if not src:
            return tag
        src_val = src.group(1)
        # Logo gets fixed dims
        if 'logo' in src_val.lower():
            if 'width=' not in tag.lower():
                tag = tag.replace('<img ', '<img width="200" height="60" ', 1)
            return tag
        # Headshot/profile gets square
        if any(x in src_val.lower() for x in ['headshot', 'profile', 'agent']):
            if 'width=' not in tag.lower():
                tag = tag.replace('<img ', '<img width="300" height="300" ', 1)
            return tag
        return tag

    new_content = re.sub(r'<img\s[^>]+>', add_dimensions, new_content, flags=re.IGNORECASE)

    # 5. Add dns-prefetch for external resources
    if 'formsubmit.co' in new_content and 'dns-prefetch' not in new_content:
        dns = '  <link rel="dns-prefetch" href="https://formsubmit.co">\n'
        new_content = new_content.replace('</head>', dns + '</head>', 1)

    if new_content != original:
        html_file.write_text(new_content, encoding="utf-8")
        stats["files_changed"] += 1

print("=== PAGE SPEED FIX RESULTS ===")
print(f"lazy loading added to images:   {stats['lazy_added']}")
print(f"scripts deferred:               {stats['defer_added']}")
print(f"preconnect hints added:         {stats['preconnect_added']}")
print(f"total files modified:           {stats['files_changed']}")
