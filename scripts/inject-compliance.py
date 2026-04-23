#!/usr/bin/env python3
"""
Inject into every .html page under the site root:
  1. Link to /css/senior-friendly.css (if missing)
  2. Link to /js/senior-tools.js (if missing)
  3. The master legal footer (if missing)
Idempotent via marker comments.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SKIP_DIRS = {'.git', 'node_modules', 'scripts', '_includes', 'admin', 'v2', 'research', 'portfolio'}
FOOTER = open(os.path.join(ROOT, '_includes', 'legal-footer.html')).read().strip()

CSS_TAG = '<link rel="stylesheet" href="/css/senior-friendly.css">'
JS_TAG  = '<script src="/js/senior-tools.js" defer></script>'

FOOTER_MARKER = 'GRE_LEGAL_FOOTER_START'
CSS_MARKER = '/css/senior-friendly.css'
JS_MARKER  = '/js/senior-tools.js'

updated = 0
skipped = 0

for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith('.html'): continue
        path = os.path.join(dirpath, f)
        rel = os.path.relpath(path, ROOT)
        try:
            s = open(path, encoding='utf-8').read()
        except Exception as e:
            print(f'SKIP read error {rel}: {e}'); continue

        if '<html' not in s or '</body>' not in s:
            skipped += 1; continue

        orig = s

        if CSS_MARKER not in s:
            s = s.replace('</head>', '  ' + CSS_TAG + '\n</head>', 1)

        if JS_MARKER not in s:
            s = s.replace('</head>', '  ' + JS_TAG + '\n</head>', 1)

        if FOOTER_MARKER not in s:
            s = s.replace('</body>', FOOTER + '\n</body>', 1)

        if s != orig:
            open(path, 'w', encoding='utf-8').write(s)
            updated += 1
            print(f'UPDATED {rel}')
        else:
            skipped += 1

print(f'\nDone. Updated {updated} files, skipped {skipped}.')
