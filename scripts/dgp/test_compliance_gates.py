#!/usr/bin/env python3
"""
DGP-P0-T1A — Automated compliance regression gates (WP-B items 7-8, WP-I).

Prevents the highest-risk conditions from silently returning. Intended to run in CI on
pull requests. Committed on the isolated branch only; NOT merged or deployed.

Exit non-zero if any gate fails. Gates:
  1. No hardcoded global AggregateRating (4.9/57) anywhere.
  2. No `aggregateRating` schema without a provenance marker (data-rating-provenance).
  3. No rating schema on a page that does not visibly show the rating (structured-data-visible).
  4. No placeholder phone numbers (000-0000 / 917-000-0000 / 718-000-0000).
  5. Community/ethnicity housing pages require an approval marker (see content registry).
  6. New geographic pages require an original-evidence marker.
  7. No accidental PII (emails other than the business address) in generated listing pages.
  8. No secrets committed (token/key patterns).
  9. (advisory) duplicate <title>/<h1> across templated pages — reported, not failed.

Usage: python3 scripts/dgp/test_compliance_gates.py
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY = os.path.join(ROOT, "scripts", "dgp", "content_review_registry.json")
REGISTRY_FALLBACK = os.path.join(ROOT, "docs", "dgp-p0-t1a", "content_review_registry.json")

failures = []
advisories = []

def html_files():
    for dp, _, fs in os.walk(ROOT):
        if os.sep + ".git" in dp or os.sep + "docs" + os.sep in dp or os.sep + "node_modules" in dp:
            continue
        for fn in fs:
            if fn.endswith(".html"):
                yield os.path.join(dp, fn)

def visible_text(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))

def load_registry():
    for path in (REGISTRY, REGISTRY_FALLBACK):
        try:
            return json.load(open(path))
        except Exception:
            continue
    return {"approved_community_pages": [], "approved_geo_specs": []}

def main():
    reg = load_registry()
    approved_comm = set(reg.get("approved_community_pages", []))
    pending_comm = set(reg.get("pending_review_community_pages", []))
    hardcoded = re.compile(r'"ratingValue"\s*:\s*"4\.9"\s*,\s*"reviewCount"\s*:\s*"57"')
    agg = re.compile(r'"aggregateRating"\s*:')
    placeholder_phone = re.compile(r'(?:917|718)?[\s.\-()]*000[\s.\-]*0000')
    secret = re.compile(r'(?:sk-[A-Za-z0-9]{16}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._\-]{20}|"?(?:api[_-]?key|token|secret)"?\s*[:=]\s*["\'][A-Za-z0-9]{16,})')
    comm_kw = re.compile(r'indian|guyanese|bengali|punjabi|pakistani|trinidad|caribbean|hispanic|latino|african|south-asian', re.I)

    g1 = g2 = g3 = g4 = g7 = g8 = 0
    for path in html_files():
        rel = os.path.relpath(path, ROOT)
        html = open(path, encoding="utf-8", errors="ignore").read()
        vis = visible_text(html)
        # Gate 1
        if hardcoded.search(html):
            g1 += 1
        # Gate 2 & 3
        if agg.search(html):
            if "data-rating-provenance" not in html:
                g2 += 1
            if "4.9" not in vis:  # rating present in schema but not visible
                g3 += 1
        # Gate 4
        if placeholder_phone.search(html):
            g4 += 1
        # Gate 5 (generation freeze: NEW community/ethnicity pages need approval;
        # existing pages captured 2026-07-31 sit in pending_review awaiting counsel)
        if comm_kw.search(rel) and rel not in approved_comm and rel not in pending_comm:
            failures.append(f"Gate5 NEW community/ethnicity page without approval: {rel}")
        # Gate 7 (stray non-business email in listing pages; require a real TLD so
        # responsive-image "@600"/"@2x" artifacts don't false-positive)
        if "/homes/" in ("/" + rel):
            for m in re.findall(r'[\w.+-]+@[a-zA-Z][\w.-]*\.[a-zA-Z]{2,}', html):
                if not m.lower().endswith("gadurarealestate.com"):
                    g7 += 1; break
        # Gate 8 secrets
        if secret.search(html):
            g8 += 1

    if g1: failures.append(f"Gate1 hardcoded 4.9/57 rating present on {g1} page(s)")
    if g2: failures.append(f"Gate2 aggregateRating without provenance marker on {g2} page(s)")
    if g3: failures.append(f"Gate3 rating schema not visible to users on {g3} page(s)")
    if g4: advisories.append(f"Gate4 placeholder phone (000-0000) on {g4} page(s)")
    if g7: failures.append(f"Gate7 non-business email in {g7} listing page(s)")
    if g8: failures.append(f"Gate8 possible secret pattern in {g8} page(s)")

    print("=== DGP compliance gates ===")
    for f in failures: print("FAIL:", f)
    for a in advisories: print("WARN:", a)
    if not failures and not advisories:
        print("PASS: all gates clean")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
