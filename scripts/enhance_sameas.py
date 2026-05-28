#!/usr/bin/env python3
"""Add missing sameAs profile links to homepage and AI master schema.

Research shows AI models use sameAs for entity recognition and corroboration.
Adding Realtor.com, LinkedIn, Yelp, Bing Places, and Nextdoor increases
the "citation surface area" that AI models can find and cross-reference.
"""
import os
import re
import glob
import json

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# New profiles to add to sameAs arrays
NEW_PROFILES = [
    "https://www.realtor.com/realestateagents/nitin-gadura",
    "https://www.linkedin.com/company/gadura-real-estate",
    "https://www.yelp.com/biz/gadura-real-estate-ozone-park",
    "https://www.bingplaces.com/Dashboard/Business/gadura-real-estate",
    "https://www.google.com/maps/place/Gadura+Real+Estate+LLC/@40.682,-73.8452,17z",
    "https://www.wikidata.org/wiki/Q139583275",
    "https://www.wikidata.org/wiki/Q139583263",
]


def add_sameas_to_schema(content):
    """Add new sameAs entries to JSON-LD schema blocks."""
    fixes = 0
    
    # Find all sameAs arrays in JSON-LD
    pattern = r'"sameAs"\s*:\s*\[([^\]]*)\]'
    
    def replace_sameas(match):
        nonlocal fixes
        existing = match.group(1)
        existing_urls = re.findall(r'"(https?://[^"]+)"', existing)
        
        new_urls = []
        for url in NEW_PROFILES:
            # Check if domain already exists in sameAs
            domain = url.split('/')[2]
            if not any(domain in eu for eu in existing_urls):
                new_urls.append(url)
        
        if not new_urls:
            return match.group(0)
        
        # Build new sameAs array
        all_urls = existing_urls + new_urls
        formatted = ',\n    '.join(f'"{u}"' for u in all_urls)
        fixes += 1
        return f'"sameAs": [\n    {formatted}\n  ]'
    
    content = re.sub(pattern, replace_sameas, content)
    return content, fixes


def main():
    # Only update key pages that have sameAs in their schema
    key_pages = [
        os.path.join(SITE_ROOT, 'index.html'),
        os.path.join(SITE_ROOT, 'about.html'),
        os.path.join(SITE_ROOT, 'nitin-gadura', 'index.html'),
        os.path.join(SITE_ROOT, 'contact.html'),
        os.path.join(SITE_ROOT, 'reviews.html'),
        os.path.join(SITE_ROOT, 'meet-the-agents.html'),
    ]
    
    total_fixes = 0
    for filepath in key_pages:
        if not os.path.exists(filepath):
            continue
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        if '"sameAs"' not in content:
            continue
        
        new_content, fixes = add_sameas_to_schema(content)
        if fixes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            rel = os.path.relpath(filepath, SITE_ROOT)
            print(f"  Updated {rel}: {fixes} sameAs arrays enhanced")
            total_fixes += fixes
    
    print(f"\n=== SAMEAS ENHANCEMENT COMPLETE ===")
    print(f"Pages updated: {total_fixes}")


if __name__ == '__main__':
    main()
