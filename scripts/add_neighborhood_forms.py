#!/usr/bin/env python3
"""
Add compact lead capture forms to all neighborhood pages that don't have one.

Scans neighborhoods/ recursively, skips index.html and files with existing
formsubmit forms, and inserts a lead capture section before the wire-fraud-bar,
footer, or </main> — whichever comes first.
"""

import os
import re
import sys
from typing import Optional

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "neighborhoods")


def extract_neighborhood_name(html: str) -> str:
    """Extract neighborhood name from H1 or title tag."""
    # Try H1 first
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if h1_match:
        raw = h1_match.group(1)
        # Truncate at <br> or <span> to avoid subtitle text
        for tag in [r"<br\s*/?>", r"<span[\s>]"]:
            br_match = re.search(tag, raw, re.IGNORECASE)
            if br_match:
                raw = raw[: br_match.start()]
        text = re.sub(r"<[^>]+>", "", raw).strip()
        # Clean common suffixes
        for suffix in [
            ", Queens, NY",
            ", Brooklyn, NY",
            ", Long Island, NY",
            ", NY",
            " Real Estate",
            " Homes for Sale",
        ]:
            if text.lower().endswith(suffix.lower()):
                text = text[: -len(suffix)].strip()
        # Remove trailing patterns
        for suffix in [
            " — Every Neighborhood, One Local Agent",
            " — Buy or Sell with Nitin Gadura",
        ]:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
        # Remove leading patterns like "Real Estate Agent in "
        for prefix in [
            "Your Trusted Real Estate Agent in ",
            "Your Trusted Real Estate Agent on ",
            "Real Estate Agent in ",
            "Real Estate in ",
            "Homes for Sale in ",
            "Top Real Estate Agent in ",
            "Best Real Estate Agent in ",
        ]:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
        # Skip redirect pages
        if text.lower() in ("redirecting...", "redirecting"):
            pass  # fall through to title
        elif text:
            return text

    # Fallback to title tag
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        # Take first segment before pipe or dash separator
        for sep in [" | ", " — ", " - ", " – "]:
            if sep in title:
                title = title.split(sep)[0].strip()
                break
        for suffix in [" Real Estate Agent", " Real Estate", " Homes"]:
            if title.lower().endswith(suffix.lower()):
                title = title[: -len(suffix)].strip()
        if title:
            return title

    return "This Neighborhood"


def build_form_html(neighborhood_name: str) -> str:
    """Build the lead capture form HTML with the neighborhood name in the subject."""
    subject = f"Neighborhood Lead — {neighborhood_name}"
    return f"""
<!-- Neighborhood Lead Capture -->
<section style="background:#f0fdf4;border:2px solid #bbf7d0;border-radius:12px;padding:28px;margin:32px auto;max-width:640px;text-align:center;">
  <h3 style="font-family:'Playfair Display',serif;color:#1B2A6B;font-size:1.3rem;margin:0 0 8px;">Looking to Buy or Sell in This Area?</h3>
  <p style="color:#475569;font-size:0.9rem;margin:0 0 16px;">Get expert guidance from a local specialist. Free consultation — no pressure.</p>
  <form action="https://formsubmit.co/Nitink.gadura@gmail.com" method="POST" style="display:grid;gap:10px;max-width:400px;margin:0 auto 12px;">
    <input type="hidden" name="_subject" value="{subject}">
    <input type="hidden" name="_captcha" value="false">
    <input type="hidden" name="_template" value="table">
    <input type="text" name="name" placeholder="Your Name" required style="padding:12px;border:1px solid #d1d5db;border-radius:6px;font-size:0.95rem;">
    <input type="tel" name="phone" placeholder="Phone Number" required style="padding:12px;border:1px solid #d1d5db;border-radius:6px;font-size:0.95rem;">
    <input type="email" name="email" placeholder="Email (optional)" style="padding:12px;border:1px solid #d1d5db;border-radius:6px;font-size:0.95rem;">
    <button type="submit" style="background:#00A651;color:#fff;font-weight:700;font-size:1rem;padding:14px;border:none;border-radius:6px;cursor:pointer;">Get Free Consultation</button>
  </form>
  <p style="margin:0;"><a href="tel:9177050132" style="color:#1B2A6B;font-weight:600;font-size:1.05rem;">Or Call (917) 705-0132</a></p>
</section>
"""


def find_insertion_point(html: str) -> Optional[int]:
    """Find the best insertion point: wire-fraud-bar div > footer > </main>."""
    # 1. Look for wire-fraud-bar div (the actual div, not the CSS style block)
    #    Match the div tag with class="wire-fraud-bar", not style definitions
    for match in re.finditer(r'<div[^>]*class=["\']wire-fraud-bar["\']', html, re.IGNORECASE):
        pos = match.start()
        # Make sure this isn't inside a <style> block
        last_style_open = html.rfind("<style", 0, pos)
        last_style_close = html.rfind("</style>", 0, pos)
        if last_style_open > last_style_close:
            # We're inside a <style> tag, skip this match
            continue
        # Walk back to the start of any preceding comment like <!-- WIRE FRAUD -->
        search_back = html[max(0, pos - 200) : pos]
        comment_match = re.search(r"<!--[^>]*WIRE\s*FRAUD[^>]*-->\s*$", search_back, re.IGNORECASE)
        if comment_match:
            return pos - len(search_back) + comment_match.start()
        return pos

    # 2. Look for <footer
    footer_match = re.search(r"<footer[\s>]", html, re.IGNORECASE)
    if footer_match:
        # Walk back past any comment
        pos = footer_match.start()
        search_back = html[max(0, pos - 200) : pos]
        comment_match = re.search(r"<!--[^>]*-->\s*$", search_back)
        if comment_match:
            return pos - len(search_back) + comment_match.start()
        return pos

    # 3. Look for </main>
    main_match = re.search(r"</main>", html, re.IGNORECASE)
    if main_match:
        return main_match.start()

    return None


def process_file(filepath: str) -> bool:
    """Process a single HTML file. Returns True if form was inserted."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Skip if already has formsubmit
    if "formsubmit" in html.lower():
        return False

    insertion_point = find_insertion_point(html)
    if insertion_point is None:
        return False

    neighborhood_name = extract_neighborhood_name(html)
    form_html = build_form_html(neighborhood_name)

    new_html = html[:insertion_point] + form_html + "\n" + html[insertion_point:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_html)

    return True


def main():
    if not os.path.isdir(BASE_DIR):
        print(f"ERROR: neighborhoods directory not found at {BASE_DIR}")
        sys.exit(1)

    updated = 0
    skipped_formsubmit = 0
    skipped_index = 0
    skipped_no_insertion = 0
    errors = 0
    updated_files = []

    for root, _dirs, files in os.walk(BASE_DIR):
        for filename in sorted(files):
            if not filename.endswith(".html"):
                continue

            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, BASE_DIR)

            # Skip index.html files
            if filename == "index.html":
                skipped_index += 1
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                if "formsubmit" in content.lower():
                    skipped_formsubmit += 1
                    continue

                if process_file(filepath):
                    updated += 1
                    neighborhood_name = extract_neighborhood_name(content)
                    updated_files.append((relpath, neighborhood_name))
                    print(f"  + {relpath} ({neighborhood_name})")
                else:
                    skipped_no_insertion += 1
                    print(f"  ? {relpath} (no insertion point found)")

            except Exception as e:
                errors += 1
                print(f"  ! {relpath} ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS")
    print(f"=" * 60)
    print(f"  Files updated:                {updated}")
    print(f"  Skipped (already has form):    {skipped_formsubmit}")
    print(f"  Skipped (index.html):          {skipped_index}")
    print(f"  Skipped (no insertion point):  {skipped_no_insertion}")
    print(f"  Errors:                        {errors}")
    print(f"  Total HTML files scanned:      {updated + skipped_formsubmit + skipped_index + skipped_no_insertion + errors}")
    print(f"=" * 60)

    if updated_files:
        print(f"\nSample subjects that will appear in email:")
        for relpath, name in updated_files[:5]:
            print(f"  Neighborhood Lead — {name}")
        if len(updated_files) > 5:
            print(f"  ... and {len(updated_files) - 5} more")


if __name__ == "__main__":
    main()
