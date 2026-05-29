#!/usr/bin/env python3
"""Batch-insert lead capture CTA into all blog posts."""

import os
import glob
import re

BLOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog")

CTA_BLOCK = """
<!-- Lead Capture CTA -->
<section style="background:linear-gradient(135deg,#1B2A6B,#0d3a24);border-radius:16px;padding:40px 32px;text-align:center;margin:48px auto;max-width:680px;">
  <h2 style="font-family:'Playfair Display',serif;color:#fff;font-size:1.6rem;margin:0 0 8px;">Need Expert Advice?</h2>
  <p style="color:rgba(255,255,255,0.75);margin:0 0 20px;font-size:0.95rem;">Talk to a local Queens &amp; Long Island real estate expert. Free consultation, no obligation.</p>
  <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:16px;">
    <a href="tel:9177050132" style="display:inline-block;background:#00A651;color:#fff;font-weight:700;font-size:1rem;padding:14px 28px;border-radius:8px;text-decoration:none;">Call (917) 705-0132</a>
    <a href="/sell-my-house/" style="display:inline-block;background:rgba(255,255,255,0.12);color:#fff;font-weight:600;font-size:0.95rem;padding:14px 28px;border-radius:8px;text-decoration:none;border:1px solid rgba(255,255,255,0.25);">Free Home Valuation</a>
  </div>
  <p style="color:rgba(255,255,255,0.45);font-size:0.78rem;margin:0;">Nitin Gadura &middot; Licensed NYS Real Estate Salesperson &middot; Gadura Real Estate LLC</p>
</section>
"""

SKIP_FILES = {"index.html", "blog.css"}

def process_file(filepath):
    """Insert CTA into a single blog post. Returns True if modified."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if CTA already present
    if "Need Expert Advice?" in content:
        return False

    # Strategy 1: Insert before wire-fraud-bar div
    # Match the opening div tag with class="wire-fraud-bar"
    wf_match = re.search(r'<div[^>]*class="wire-fraud-bar"', content)
    if wf_match:
        insert_pos = wf_match.start()
        new_content = content[:insert_pos] + CTA_BLOCK + "\n" + content[insert_pos:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    # Strategy 2: Insert before </main>
    main_match = content.rfind("</main>")
    if main_match != -1:
        new_content = content[:main_match] + CTA_BLOCK + "\n" + content[main_match:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    # Strategy 3: Insert before <footer
    footer_match = re.search(r"<footer", content)
    if footer_match:
        insert_pos = footer_match.start()
        new_content = content[:insert_pos] + CTA_BLOCK + "\n" + content[insert_pos:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    html_files = glob.glob(os.path.join(BLOG_DIR, "*.html"))
    updated = 0
    skipped_existing = 0
    skipped_no_anchor = 0
    files_processed = []

    for filepath in sorted(html_files):
        basename = os.path.basename(filepath)
        if basename in SKIP_FILES:
            continue

        result = process_file(filepath)
        if result:
            updated += 1
            files_processed.append(basename)
        elif "Need Expert Advice?" in open(filepath, encoding="utf-8").read():
            skipped_existing += 1
        else:
            skipped_no_anchor += 1
            print(f"  WARNING: No insertion point found in {basename}")

    print(f"\n=== CTA Insertion Complete ===")
    print(f"Files updated:          {updated}")
    print(f"Already had CTA:        {skipped_existing}")
    print(f"No insertion point:     {skipped_no_anchor}")
    print(f"Total blog posts:       {updated + skipped_existing + skipped_no_anchor}")

    if files_processed:
        print(f"\nUpdated files:")
        for f in files_processed:
            print(f"  + {f}")


if __name__ == "__main__":
    main()
