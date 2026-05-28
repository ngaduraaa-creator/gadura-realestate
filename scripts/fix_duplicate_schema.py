#!/usr/bin/env python3
"""Remove duplicate AI Master Schema injections.

The inject_ai_schema.py script was run 3x, leaving triple-duplicated
schema blocks on 1,174 pages. This is causing ~1,244 structured data
validation errors.

Strategy: Keep the FIRST complete ai-master-schema block + its preceding
comment. Remove all subsequent duplicates.
"""
import os
import re
import glob

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pattern: the comment block + the script block that follows it
# We match each complete "comment + script" pair
SCHEMA_COMMENT = r'<!--\s*\n\s*AI MASTER SCHEMA[^>]*?-->\n'
SCHEMA_BLOCK = r'<script type="application/ld\+json" id="ai-master-schema">[\s\S]*?</script>'

def fix_file(filepath):
    """Remove duplicate ai-master-schema blocks. Returns number of duplicates removed."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Count occurrences
    comment_count = len(re.findall(r'AI MASTER SCHEMA', content))
    script_count = len(re.findall(r'id="ai-master-schema"', content))

    if comment_count <= 1 and script_count <= 1:
        return 0  # No duplicates

    original = content

    # Strategy: find all the comment+script pairs, keep only the first one
    # First, handle the comments — keep only the first one
    # The pattern is: <!--\n  AI MASTER SCHEMA ... -->\n
    comment_pattern = re.compile(
        r'<!--\s*\n\s*AI MASTER SCHEMA — canonical Person \+ RealEstateAgent \+ Brand entity graph\s*\n'
        r'\s*Injected on every key buyer/seller-intent page.*?\n'
        r'\s*DO NOT EDIT INLINE.*?\n'
        r'-->\s*\n',
        re.DOTALL
    )

    comments = list(comment_pattern.finditer(content))
    if len(comments) > 1:
        # Remove all but the first comment
        # Work backwards to preserve positions
        for match in reversed(comments[1:]):
            content = content[:match.start()] + content[match.end():]

    # Now handle the script blocks — keep only the first one
    script_pattern = re.compile(
        r'<script type="application/ld\+json" id="ai-master-schema">\s*\n'
        r'\{[\s\S]*?\}\s*\n'
        r'</script>',
        re.DOTALL
    )

    scripts = list(script_pattern.finditer(content))
    if len(scripts) > 1:
        for match in reversed(scripts[1:]):
            content = content[:match.start()] + content[match.end():]

    # Clean up any resulting blank lines (3+ consecutive newlines → 2)
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        removed = max(comment_count - 1, 0) + max(script_count - 1, 0)
        return removed

    return 0


def main():
    html_files = glob.glob(os.path.join(SITE_ROOT, '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if '/.git/' not in f]

    total_files = 0
    total_removed = 0

    for filepath in html_files:
        removed = fix_file(filepath)
        if removed > 0:
            rel = os.path.relpath(filepath, SITE_ROOT)
            print(f"  Removed {removed} duplicates from {rel}")
            total_files += 1
            total_removed += removed

    print(f"\n=== DUPLICATE SCHEMA FIX COMPLETE ===")
    print(f"Files fixed: {total_files}")
    print(f"Total duplicate blocks removed: {total_removed}")


if __name__ == '__main__':
    main()
