#!/usr/bin/env python3
"""
Add floating mobile CTA bar to all HTML pages.

Inserts:
  - <link rel="stylesheet" href="/css/mobile-cta.css"> into <head> (after last stylesheet link)
  - Floating CTA HTML div before </body>

Skips:
  - Files in _includes/, v2/, admin/, scripts/ directories
  - Files that already contain 'floating-cta'
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {'_includes', 'v2', 'admin', 'scripts'}

CSS_LINK = '<link rel="stylesheet" href="/css/mobile-cta.css">'

CTA_HTML = """<!-- Floating Mobile CTA -->
<div class="floating-cta" role="complementary" aria-label="Contact">
  <div class="floating-cta-inner">
    <a href="tel:9177050132" class="cta-call">\U0001F4DE Call Now</a>
    <a href="/sell-my-house/" class="cta-text">Free Valuation</a>
  </div>
</div>"""


def should_skip(filepath):
    """Check if file is in a directory we should skip."""
    rel = os.path.relpath(filepath, REPO_ROOT)
    parts = rel.split(os.sep)
    for part in parts:
        if part in SKIP_DIRS:
            return True
    return False


def find_last_stylesheet_pos(content):
    """Find position to insert CSS link after the last <link rel='stylesheet'> in <head>."""
    head_match = re.search(r'</head>', content, re.IGNORECASE)
    if not head_match:
        return None

    head_content = content[:head_match.start()]

    # Find all stylesheet links in <head>
    pattern = re.compile(r'<link[^>]*(?:rel=["\']stylesheet["\']|\.css)[^>]*>', re.IGNORECASE)
    last_match = None
    for match in pattern.finditer(head_content):
        last_match = match

    if last_match:
        # Insert after the last stylesheet link's line
        end_pos = last_match.end()
        # Find end of line
        newline_pos = content.find('\n', end_pos)
        if newline_pos != -1:
            return newline_pos + 1
        return end_pos
    else:
        # No stylesheet links found; insert right before </head>
        return head_match.start()


def process_file(filepath):
    """Process a single HTML file. Returns True if modified."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"  SKIP (read error): {filepath} - {e}")
        return False

    # Already has floating CTA
    if 'floating-cta' in content:
        return False

    # Must have </body> to insert CTA
    body_match = re.search(r'</body>', content, re.IGNORECASE)
    if not body_match:
        return False

    # Must have </head> to insert CSS link
    head_match = re.search(r'</head>', content, re.IGNORECASE)
    if not head_match:
        return False

    modified = content

    # Step 1: Insert CSS link in <head>
    css_insert_pos = find_last_stylesheet_pos(modified)
    if css_insert_pos is not None:
        modified = modified[:css_insert_pos] + '  ' + CSS_LINK + '\n' + modified[css_insert_pos:]

    # Step 2: Insert CTA HTML before </body>
    # Re-find </body> since positions shifted after CSS insertion
    body_match = re.search(r'</body>', modified, re.IGNORECASE)
    if body_match:
        insert_pos = body_match.start()
        modified = modified[:insert_pos] + CTA_HTML + '\n' + modified[insert_pos:]

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    except (IOError, OSError) as e:
        print(f"  SKIP (write error): {filepath} - {e}")
        return False


def main():
    updated = 0
    skipped_dir = 0
    skipped_existing = 0
    skipped_no_body = 0
    errors = 0
    total = 0

    for root, dirs, files in os.walk(REPO_ROOT):
        for filename in files:
            if not filename.endswith('.html'):
                continue

            filepath = os.path.join(root, filename)

            if should_skip(filepath):
                skipped_dir += 1
                continue

            total += 1

            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                errors += 1
                continue

            if 'floating-cta' in content:
                skipped_existing += 1
                continue

            if not re.search(r'</body>', content, re.IGNORECASE):
                skipped_no_body += 1
                continue

            if not re.search(r'</head>', content, re.IGNORECASE):
                skipped_no_body += 1
                continue

            if process_file(filepath):
                updated += 1
            else:
                errors += 1

    print(f"\n{'='*50}")
    print(f"Floating Mobile CTA — Injection Report")
    print(f"{'='*50}")
    print(f"HTML files scanned:      {total}")
    print(f"Files updated:           {updated}")
    print(f"Skipped (excluded dirs): {skipped_dir}")
    print(f"Skipped (already has):   {skipped_existing}")
    print(f"Skipped (no body/head):  {skipped_no_body}")
    print(f"Errors:                  {errors}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
