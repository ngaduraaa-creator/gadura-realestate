#!/usr/bin/env python3
"""
DGP-P0-T2C — Sitemap & canonical regression gates (Work Package J).
Run in CI on every PR: python3 scripts/dgp/test_sitemap_canonical_gates.py
Exit non-zero on any FAIL. Exceptions live ONLY in sitemap_eligibility.EXCEPTION_REGISTRY.
"""
import os, re, sys, glob
import xml.dom.minidom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sitemap_eligibility as SE

ROOT = SE.ROOT
fails, warns = [], []

def main():
    dis = SE.robots_disallows()
    all_urls = []
    for sm in sorted(glob.glob(os.path.join(ROOT, "sitemap*.xml"))):
        name = os.path.basename(sm)
        raw = open(sm, encoding="utf-8", errors="ignore").read()
        # malformed XML
        try:
            xml.dom.minidom.parseString(raw)
        except Exception as e:
            fails.append(f"{name}: MALFORMED_XML {e}"); continue
        if name in ("sitemap-index.xml", "sitemap-images.xml"):
            continue  # index + non-HTML types: controlled exceptions (WP-F)
        locs = re.findall(r"<loc>(.*?)</loc>", raw)
        # duplicates within one sitemap
        if len(locs) != len(set(locs)):
            fails.append(f"{name}: DUPLICATE_URLS ({len(locs)-len(set(locs))})")
        seen = set()
        for u in locs:
            all_urls.append(u)
            if not u.startswith(SE.APPROVED_HOST):
                fails.append(f"{name}: UNAPPROVED_HOST_OR_VENDOR {u}"); continue
            ok, reason = SE.check(u, robots_disallows=dis, seen=seen)
            if not ok:
                fails.append(f"{name}: {reason} {u}")
    # canonical hygiene across pages: no http:// canonicals, no www canonicals
    bad_canon = 0
    for dp, _, fs in os.walk(ROOT):
        if any(x in dp for x in (os.sep+".git", os.sep+"docs", os.sep+"evidence", os.sep+"node_modules")):
            continue
        for fn in fs:
            if not fn.endswith(".html"): continue
            h = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            m = SE.CANON_RE.search(h)
            if m and (m.group(1).startswith("http://") or "://www.gadurarealestate.com" in m.group(1)):
                bad_canon += 1
    if bad_canon:
        fails.append(f"CANONICAL_HTTP_OR_WWW on {bad_canon} page(s)")
    # homepage-variant internal links must not persist
    n_www = 0
    for dp, _, fs in os.walk(ROOT):
        if any(x in dp for x in (os.sep+".git", os.sep+"docs", os.sep+"evidence")): continue
        for fn in fs:
            if not fn.endswith(".html"): continue
            h = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            n_www += len(re.findall(r'href="https?://www\.gadurarealestate\.com', h))
    if n_www:
        fails.append(f"WWW_INTERNAL_LINKS remain: {n_www}")
    # AggregateRating must not return without provenance (mirror of T1A Gate 2)
    n_rating = 0
    for dp, _, fs in os.walk(ROOT):
        if any(x in dp for x in (os.sep+".git", os.sep+"docs", os.sep+"evidence")): continue
        for fn in fs:
            if not fn.endswith(".html"): continue
            h = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            if '"aggregateRating"' in h and "data-rating-provenance" not in h:
                n_rating += 1
    if n_rating:
        fails.append(f"AGGREGATERATING_WITHOUT_PROVENANCE on {n_rating} page(s)")
    # determinism: regenerating must be stable (sorted unique locs)
    for sm in sorted(glob.glob(os.path.join(ROOT, "sitemap*.xml"))):
        name = os.path.basename(sm)
        if name in ("sitemap-index.xml", "sitemap-images.xml"): continue
        locs = re.findall(r"<loc>(.*?)</loc>", open(sm).read())
        if locs != sorted(set(locs)):
            warns.append(f"{name}: NONDETERMINISTIC_ORDER (not sorted-unique)")
    print("=== sitemap/canonical gates ===")
    for f in fails: print("FAIL:", f)
    for w in warns: print("WARN:", w)
    if not fails and not warns: print("PASS: all gates clean")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
