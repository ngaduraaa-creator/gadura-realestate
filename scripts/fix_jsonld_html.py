#!/usr/bin/env python3
"""Strip HTML tags from JSON-LD structured data values.

Some pages have HTML markup (<a>, <strong>, etc.) embedded inside
JSON-LD text values, causing schema.org validation errors.
"""
import os
import re
import json
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_html(text):
    """Remove HTML tags from a string, keeping text content."""
    if not isinstance(text, str):
        return text
    # Replace <strong>text</strong> with text
    text = re.sub(r'</?strong>', '', text)
    # Replace <a href="...">text</a> with text
    text = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', text)
    # Replace standalone strong with nothing (malformed)
    text = re.sub(r'\bstrong\b', '', text)
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_json_value(obj):
    """Recursively strip HTML from all string values in a JSON object."""
    if isinstance(obj, str):
        return strip_html(obj)
    elif isinstance(obj, dict):
        return {k: clean_json_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_value(item) for item in obj]
    return obj


def fix_file(filepath):
    """Clean HTML from JSON-LD blocks in a file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    original = content
    fixes = 0

    def replace_jsonld(match):
        nonlocal fixes
        full = match.group(0)
        tag_open = match.group(1)
        json_str = match.group(2)

        # Check if this block has HTML in it
        if '<a ' not in json_str and '<strong' not in json_str and 'strong' not in json_str:
            return full

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Try to fix common issues: truncated strings, HTML tags
            # Strip HTML first then try again
            cleaned = strip_html(json_str)
            # This is too broken to auto-fix - skip
            return full

        cleaned_data = clean_json_value(data)

        if cleaned_data != data:
            fixes += 1
            new_json = json.dumps(cleaned_data, indent=2, ensure_ascii=False)
            return f'{tag_open}{new_json}\n</script>'

        return full

    # Match script blocks with JSON-LD
    content = re.sub(
        r'(<script type="application/ld\+json"[^>]*>)\s*([\s\S]*?)\s*</script>',
        replace_jsonld,
        content
    )

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
            rel = os.path.relpath(filepath, SITE_ROOT)
            print(f"  Fixed {fixes} blocks in {rel}")
            total_files += 1
            total_fixes += fixes

    print(f"\n=== JSON-LD HTML CLEANUP COMPLETE ===")
    print(f"Files fixed: {total_files}")
    print(f"Blocks cleaned: {total_fixes}")


if __name__ == '__main__':
    main()
