#!/usr/bin/env python3
"""Fix title and meta description length issues.

- 60 titles over 60 chars → trim to 60
- 20 descriptions over 160 chars → trim to 155
- 118 descriptions under 120 chars → expand with context
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def shorten_title(title):
    """Shorten title to ~60 chars while keeping it meaningful."""
    if len(title) <= 60:
        return title

    # Try removing " | Gadura Real Estate" suffix first
    shortened = re.sub(r'\s*\|\s*Gadura Real Estate\s*$', '', title)
    if len(shortened) <= 60:
        return shortened

    # Try removing secondary phrases after |
    parts = title.split('|')
    if len(parts) >= 3:
        # Keep first part + last part (brand)
        candidate = f"{parts[0].strip()} | Gadura Real Estate"
        if len(candidate) <= 60:
            return candidate

    # Just keep first part
    first = parts[0].strip()
    if len(first) <= 60:
        return first

    # Truncate intelligently at word boundary
    truncated = first[:57]
    last_space = truncated.rfind(' ')
    if last_space > 40:
        truncated = truncated[:last_space]
    return truncated + '...'


def expand_description(desc, title, filepath):
    """Expand short descriptions to 120-155 chars."""
    if len(desc) >= 120:
        return desc

    rel = os.path.relpath(filepath, SITE_ROOT)

    # Add contextual suffix based on page type
    suffixes = [
        " Contact Nitin Gadura at 917-705-0132 for expert guidance.",
        " Gadura Real Estate serves Queens, Brooklyn, and Long Island NY.",
        " Call Gadura Real Estate at 917-705-0132 for a free consultation.",
        " Expert real estate services in Queens and Long Island, New York.",
    ]

    for suffix in suffixes:
        expanded = desc.rstrip('.') + '.' + suffix
        if 120 <= len(expanded) <= 160:
            return expanded

    # If still too short, add location context
    if 'queens' in rel.lower() or 'queens' in desc.lower():
        expanded = desc.rstrip('.') + '. Serving Ozone Park, Richmond Hill, Jamaica, Howard Beach, and all of Queens NY.'
    elif 'brooklyn' in rel.lower() or 'brooklyn' in desc.lower():
        expanded = desc.rstrip('.') + '. Serving all Brooklyn neighborhoods. Call 917-705-0132.'
    elif 'long-island' in rel.lower() or 'nassau' in rel.lower() or 'suffolk' in rel.lower():
        expanded = desc.rstrip('.') + '. Serving Nassau and Suffolk County, Long Island NY. Call 917-705-0132.'
    else:
        expanded = desc.rstrip('.') + '. Gadura Real Estate LLC — Queens and Long Island NY. Call 917-705-0132.'

    # Truncate if too long
    if len(expanded) > 160:
        expanded = expanded[:157] + '...'

    return expanded


def shorten_description(desc):
    """Shorten description to under 160 chars."""
    if len(desc) <= 160:
        return desc

    # Try to cut at sentence boundary
    truncated = desc[:157]
    last_period = truncated.rfind('.')
    if last_period > 100:
        return truncated[:last_period + 1]

    # Cut at word boundary
    last_space = truncated.rfind(' ')
    if last_space > 120:
        return truncated[:last_space] + '...'

    return truncated + '...'


def fix_file(filepath):
    """Fix title and description length issues."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if '</head>' not in content:
        return 0
    if re.search(r'noindex', content, re.I):
        return 0

    original = content
    fixes = 0

    # Fix title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.I | re.S)
    if title_match:
        title = title_match.group(1).strip()
        if len(title) > 60:
            new_title = shorten_title(title)
            content = content.replace(
                f'<title>{title}</title>',
                f'<title>{new_title}</title>'
            )
            # Also update og:title if it matches old title
            content = content.replace(
                f'content="{title}"',
                f'content="{new_title}"'
            )
            fixes += 1

    # Fix description
    desc_match = re.search(r'(name="description"\s+content=")([^"]*)"', content, re.I)
    if not desc_match:
        desc_match = re.search(r'(content=")([^"]*)("\s+name="description")', content, re.I)

    if desc_match:
        desc = desc_match.group(2)
        title = title_match.group(1).strip() if title_match else ''

        if len(desc) > 160:
            new_desc = shorten_description(desc)
            content = content.replace(
                f'content="{desc}"',
                f'content="{new_desc}"',
                1
            )
            fixes += 1
        elif 0 < len(desc) < 120:
            new_desc = expand_description(desc, title, filepath)
            content = content.replace(
                f'content="{desc}"',
                f'content="{new_desc}"',
                1
            )
            fixes += 1

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return fixes


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    total_files = 0
    total_fixes = 0

    for filepath in html_files:
        fixes = fix_file(filepath)
        if fixes > 0:
            total_files += 1
            total_fixes += fixes

    print(f"\n=== TITLE/DESC LENGTH FIX COMPLETE ===")
    print(f"Files updated: {total_files}")
    print(f"Total fixes: {total_fixes}")


if __name__ == '__main__':
    main()
