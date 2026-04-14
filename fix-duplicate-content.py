#!/usr/bin/env python3
"""
Fix Google spam penalty risks across all neighborhood pages:
1. Remove duplicate FAQPage schema (identical Q&A across pages)
2. Move inline CSS to external stylesheet (stop repeating 175 lines per page)
3. Remove duplicate "How Nitin Sells" 6-step process section
4. Reduce CTA repetition (keep hero + form, remove sidebar CTA box)
"""

import os
import re
import glob

SITE_DIR = "/Users/nidhigadura/Jagex/gadura-realestate"
NEIGHBORHOODS_DIR = os.path.join(SITE_DIR, "neighborhoods")

def get_all_neighborhood_files():
    """Find all HTML files in neighborhoods/ including brooklyn/ subdirectory."""
    files = glob.glob(os.path.join(NEIGHBORHOODS_DIR, "*.html"))
    files += glob.glob(os.path.join(NEIGHBORHOODS_DIR, "brooklyn", "*.html"))
    return sorted(files)

def remove_faq_schema(html):
    """Remove FAQPage JSON-LD schema block (the duplicated one)."""
    # Match the FAQPage script block
    pattern = r'<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"FAQPage".*?</script>'
    result = re.sub(pattern, '', html, flags=re.DOTALL)
    return result

def remove_inline_css(html):
    """Remove the massive inline <style> block and replace with link to stylesheet.
    Keep only the small wire-fraud-bar style block."""
    # Remove the big inline style block (starts with *{box-sizing and contains .container, .hero, etc.)
    pattern = r'<style>\s*\*\{box-sizing:border-box.*?</style>'
    result = re.sub(pattern, '', html, flags=re.DOTALL)

    # Add neighborhood stylesheet link if not already present
    if 'neighborhood-pages.css' not in result:
        result = result.replace(
            '<link rel="stylesheet" href="/css/style.css">',
            '<link rel="stylesheet" href="/css/style.css">\n<link rel="stylesheet" href="/css/neighborhood-pages.css">'
        )
    return result

def remove_selling_process_section(html):
    """Remove the duplicate 'How Nitin Sells Your X Home' section.
    Replace with a short link to a consolidated selling process page."""

    # Find the selling process section
    pattern = r'<!-- SELLING PROCESS -->.*?</section>'

    def replace_with_link(match):
        # Extract neighborhood name from the section
        text = match.group(0)
        return '''<!-- SELLING PROCESS — See consolidated page -->
<section class="section section-alt">
  <div class="container" style="text-align:center;padding:48px 0">
    <h2 class="section-title">Ready to Sell? Here's How It Works</h2>
    <p class="section-sub" style="margin:0 auto 24px">Nitin's 6-step selling process has helped dozens of Queens homeowners get top dollar. From your free market analysis to closing day — every detail is handled.</p>
    <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap">
      <a href="/services/selling-process.html" class="btn-green">See the Full Selling Process</a>
      <a href="tel:9177050132" class="btn-outline-white" style="border-color:#1B2A6B;color:#1B2A6B">Call (917) 705-0132</a>
    </div>
  </div>
</section>'''

    result = re.sub(pattern, replace_with_link, html, flags=re.DOTALL)
    return result

def remove_extra_cta_box(html):
    """Remove the sidebar CTA box that duplicates the hero CTA.
    This is the dark box with 'Ready to find out what your X home is worth?'"""
    # This appears inside the selling process section's two-col layout
    # After removing the selling process, this should be gone too
    # But let's also catch any standalone ones
    pattern = r'<div style="align-self:center">\s*<div style="background:linear-gradient\(135deg,#0F1A40,#1B2A6B\).*?</div>\s*</div>\s*</div>'
    result = re.sub(pattern, '', html, flags=re.DOTALL)
    return result

def count_cta_phrases(html):
    """Count 'Free Home Valuation' occurrences."""
    return len(re.findall(r'free.*?home.*?valuation', html, re.IGNORECASE))

def process_file(filepath):
    """Apply all fixes to a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    html = original
    changes = []

    # 1. Remove FAQ schema
    if '"FAQPage"' in html:
        html = remove_faq_schema(html)
        changes.append("Removed duplicate FAQPage schema")

    # 2. Remove inline CSS
    if '*{box-sizing:border-box' in html and 'neighborhood-pages.css' not in html:
        html = remove_inline_css(html)
        changes.append("Moved inline CSS to external stylesheet")

    # 3. Remove selling process section
    if '<!-- SELLING PROCESS -->' in html:
        html = remove_selling_process_section(html)
        changes.append("Replaced duplicate selling process with consolidated link")

    # Clean up extra blank lines
    html = re.sub(r'\n{4,}', '\n\n', html)

    if html != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        return changes
    return []

def main():
    files = get_all_neighborhood_files()
    print(f"Found {len(files)} neighborhood pages to fix\n")

    total_changes = 0
    for filepath in files:
        relpath = os.path.relpath(filepath, SITE_DIR)
        changes = process_file(filepath)
        if changes:
            total_changes += len(changes)
            print(f"  FIXED: {relpath}")
            for c in changes:
                print(f"    - {c}")
        else:
            print(f"  SKIP:  {relpath} (no changes needed)")

    print(f"\nDone. Applied {total_changes} fixes across {len(files)} files.")

if __name__ == "__main__":
    main()
