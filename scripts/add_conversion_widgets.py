#!/usr/bin/env python3
"""
Inject conversion widget CSS + JS references into all HTML pages.
Adds: css/conversion-widgets.css + js/conversion-widgets.js
Skips: admin pages, files that already have it, v2/ directory
"""
import os
import re

BASE = '/Users/nidhigadura/Jagex/gadura-realestate'
SKIP_DIRS = {'node_modules', '.git', 'admin', 'scripts', 'data'}

CSS_LINK = '<link rel="stylesheet" href="{prefix}css/conversion-widgets.css">'
JS_SCRIPT = '<script src="{prefix}js/conversion-widgets.js" defer></script>'

stats = {'updated': 0, 'skipped': 0, 'errors': 0}

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for fname in files:
        if not fname.endswith('.html'):
            continue

        filepath = os.path.join(root, fname)
        rel = os.path.relpath(filepath, BASE)

        # Skip admin and non-public pages
        if rel.startswith('admin/'):
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            stats['errors'] += 1
            continue

        # Skip if already has conversion widgets
        if 'conversion-widgets' in content:
            stats['skipped'] += 1
            continue

        # Skip if no </head> tag (not a full HTML page)
        if '</head>' not in content:
            stats['skipped'] += 1
            continue

        # Calculate relative prefix based on directory depth
        depth = rel.count('/')
        prefix = '../' * depth if depth > 0 else ''

        css_tag = CSS_LINK.format(prefix=prefix)
        js_tag = JS_SCRIPT.format(prefix=prefix)

        modified = content

        # Add CSS before </head>
        modified = modified.replace('</head>', f'  {css_tag}\n</head>', 1)

        # Add JS before </body>
        if '</body>' in modified:
            modified = modified.replace('</body>', f'  {js_tag}\n</body>', 1)

        if modified != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified)
            stats['updated'] += 1

print(f"\n✅ Conversion widgets injected:")
print(f"   Updated: {stats['updated']} pages")
print(f"   Skipped: {stats['skipped']} (already had or not applicable)")
print(f"   Errors:  {stats['errors']}")
