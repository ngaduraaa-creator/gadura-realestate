#!/usr/bin/env python3
"""DGP-P0-XW1 deterministic safety test: FAIL if any denylisted placeholder URL
appears in any generated sitemap. Run in CI and before every public-site deploy."""
import os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
deny = {l.strip().rstrip('/') for l in open(os.path.join(ROOT,"scripts/dgp/placeholder_sitemap_denylist.txt"))
        if l.strip() and not l.startswith("#")}
bad = []
for sm in glob.glob(os.path.join(ROOT, "sitemap*.xml")):
    locs = {u.rstrip('/') for u in re.findall(r"<loc>(.*?)</loc>", open(sm).read())}
    hits = deny & locs
    for h in sorted(hits): bad.append(f"{os.path.basename(sm)}: {h}")
print("=== placeholder denylist gate ===")
for b in bad: print("FAIL:", b)
print(f"PASS: 0 of {len(deny)} denylisted URLs in sitemaps" if not bad else f"{len(bad)} violation(s)")
sys.exit(1 if bad else 0)
