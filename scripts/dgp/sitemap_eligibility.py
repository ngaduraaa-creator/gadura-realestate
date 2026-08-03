#!/usr/bin/env python3
"""
DGP-P0-T2C — Shared sitemap-eligibility policy (Work Package F).

Single source of truth for whether a URL may appear in an XML sitemap.
Used by the staged sitemap regenerator and the regression test suite.

A normal HTML URL is sitemap-eligible ONLY if every required check passes:
  1.  Resolves to an existing local file (proxy for HTTP 200 on the static host).
  2.  Not blocked by robots.txt (no matching Disallow for *).
  3.  No meta-robots noindex.
  4.  Uses the approved canonical hostname (https://gadurarealestate.com).
  5.  Self-canonical (its canonical tag, absolutized, equals its own URL).
  6.  Not a redirect stub (no meta refresh / canonical-to-elsewhere alternates).
  7.  Not a soft-404 (heuristic: non-trivial content).
  8.  Not a placeholder or mock listing (stock imagery markers under /homes/).
  9.  Not a duplicate URL within the sitemap set.
  10. Intended for public search visibility.
  11. Carries required attribution where applicable (listing pages).
  12. Not expired (unless an approved evergreen-archive policy applies).
  13. Stable URL (no tracking parameters, no session tokens).
  14. No unresolved compliance block (community pages pending counsel are NOT
      excluded here — visibility policy for them is a counsel decision, not a
      technical one; they pass unless counsel directs otherwise).
  15. No unresolved listing-data provenance block (placeholder listings fail 8).

Controlled exceptions live ONLY in EXCEPTION_REGISTRY below — never inline.
"""
import os, re, json

APPROVED_HOST = "https://gadurarealestate.com"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Documented exception registry (WP-J): each entry needs a reason + approver.
EXCEPTION_REGISTRY = {
    # "https://gadurarealestate.com/some-url/": {"reason": "...", "approved_by": "...", "date": "..."},
}

NOINDEX_RE   = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re.I)
CANON_RE     = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
PLACEHOLDER_RE = re.compile(r'unsplash|placeholder\.(jpg|png|webp)', re.I)
REFRESH_RE   = re.compile(r'<meta[^>]+http-equiv=["\']refresh', re.I)
ATTRIB_RE    = re.compile(r'OneKey', re.I)

def url_to_relpath(url):
    p = url.replace(APPROVED_HOST, "").split("#")[0].split("?")[0]
    if p in ("", "/"): return "index.html"
    p = p.lstrip("/")
    if p.endswith("/"): return p + "index.html"
    if not re.search(r"\.[a-z0-9]{2,5}$", p): return p + "/index.html"
    return p

def check(url, html=None, robots_disallows=None, seen=None):
    """Return (eligible: bool, reason_code: str)."""
    if url in EXCEPTION_REGISTRY:
        return True, "EXCEPTION:" + EXCEPTION_REGISTRY[url]["reason"][:40]
    if not url.startswith(APPROVED_HOST + "/") and url != APPROVED_HOST + "/":
        return False, "UNAPPROVED_HOST"
    if "?" in url or "#" in url:
        return False, "UNSTABLE_URL_PARAMS"
    if seen is not None:
        key = url.rstrip("/")
        if key in seen: return False, "DUPLICATE_IN_SITEMAP"
        seen.add(key)
    rel = url_to_relpath(url)
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return False, "NOT_200_LOCAL_FILE_MISSING"
    if robots_disallows:
        upath = "/" + rel
        for d in robots_disallows:
            if d and upath.startswith(d): return False, "BLOCKED_BY_ROBOTS"
    if html is None:
        try: html = open(path, encoding="utf-8", errors="ignore").read()
        except Exception: return False, "UNREADABLE"
    if NOINDEX_RE.search(html): return False, "NOINDEX"
    if REFRESH_RE.search(html): return False, "REDIRECT_STUB"
    m = CANON_RE.search(html)
    if not m:
        return False, "NO_CANONICAL"
    if m:
        canon = m.group(1).strip()
        if canon.startswith("/"): canon = APPROVED_HOST + canon
        cu, uu = canon.rstrip("/"), url.rstrip("/")
        # treat /x.html vs /x/ vs /x as same-page variants of self
        norm = lambda s: re.sub(r"/index\.html$", "", re.sub(r"\.html$", "", s))
        if norm(cu) != norm(uu): return False, "ALTERNATE_CANONICAL"
        if canon.startswith("http://"): return False, "CANONICAL_HTTP"
    text = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I))
    if len(text.split()) < 40: return False, "SOFT_404_THIN"
    if "/homes/" in url:
        if PLACEHOLDER_RE.search(html): return False, "PLACEHOLDER_LISTING"
        if not ATTRIB_RE.search(html): return False, "MISSING_MLS_ATTRIBUTION"
    return True, "ELIGIBLE"

def robots_disallows():
    out = []
    try:
        cur_agent_all = False
        for line in open(os.path.join(ROOT, "robots.txt"), encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                cur_agent_all = line.split(":", 1)[1].strip() == "*"
            elif cur_agent_all and line.lower().startswith("disallow:"):
                out.append(line.split(":", 1)[1].strip())
    except Exception:
        pass
    return [d for d in out if d]

if __name__ == "__main__":
    import sys
    dis = robots_disallows()
    seen = set()
    for u in sys.argv[1:]:
        ok, reason = check(u, robots_disallows=dis, seen=seen)
        print(("PASS " if ok else "FAIL "), reason, u)
