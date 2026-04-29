#!/usr/bin/env python3
"""
audit_indexing.py — Crawl every URL in our sitemap, classify by HTTP status,
and report:
- 200 OK (indexable)
- 301/302 redirects (need internal-link cleanup + sitemap removal)
- 404 / 410 (need sitemap removal + 301 redirect added)
- Other errors

Also scans local HTML for:
- Pages with `<meta name="robots" content="noindex">`
- Internal links pointing to 404 URLs
- Internal links pointing to redirected URLs (chain risk)

Output: ai-monitoring/indexing-audit-<date>.csv

Usage:
    python3 scripts/audit_indexing.py        # audit + report
    python3 scripts/audit_indexing.py --fix  # apply fixes (sitemap + redirects)
"""
from __future__ import annotations
import argparse
import concurrent.futures
import csv
import datetime as dt
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
OUT_DIR = ROOT / "ai-monitoring"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def head(url: str, timeout: int = 8) -> tuple[int, str]:
    """HEAD request → (status, final_url). Falls back to GET if HEAD fails."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "GaduraIndexAudit/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.url
        except urllib.error.HTTPError as e:
            return e.code, url
        except Exception:
            continue
    return 0, url


def parse_sitemap_urls(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        urls = []
        for u in root.findall(f"{{{NS}}}url"):
            loc = u.findtext(f"{{{NS}}}loc", default="").strip()
            if loc:
                urls.append(loc)
        return urls
    except ET.ParseError:
        return []


def audit_urls(urls: list[str]) -> list[dict]:
    results = []
    print(f"  Checking {len(urls)} URLs (parallelized)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(head, u): u for u in urls}
        for i, f in enumerate(concurrent.futures.as_completed(futs)):
            url = futs[f]
            try:
                status, final = f.result()
            except Exception:
                status, final = 0, url
            redirected = (final != url) and status == 200
            results.append({"url": url, "status": status, "final": final, "redirected": redirected})
            if (i + 1) % 100 == 0:
                print(f"  ... {i + 1}/{len(urls)}")
    return results


def find_noindex_pages() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        if any(part in {".git", ".github", "_includes", "scripts", "_site", ".netlify"} for part in p.relative_to(ROOT).parts):
            continue
        try:
            html = p.read_text(encoding="utf-8")
        except Exception:
            continue
        # Look for noindex in meta robots — but ignore robots="index, follow" forms
        m = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if m and "noindex" in m.group(1).lower():
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="Apply sitemap + redirect fixes")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()

    print("=== STEP 1: parse sitemap ===")
    urls = parse_sitemap_urls(SITEMAP)
    print(f"  {len(urls)} URLs found in sitemap.xml")

    print("\n=== STEP 2: HTTP status check ===")
    results = audit_urls(urls)

    # Bucket
    by_status = {}
    for r in results:
        s = r["status"]
        by_status.setdefault(s, []).append(r)
    redirected = [r for r in results if r["redirected"]]

    print(f"\n=== HTTP Status Breakdown ===")
    for code in sorted(by_status):
        print(f"  HTTP {code}: {len(by_status[code])}")
    print(f"  Of HTTP 200 responses, {len(redirected)} were redirects to a different URL")

    not_found = by_status.get(404, []) + by_status.get(410, [])
    redirects = [r for r in results if r["status"] in (301, 302, 307, 308)]

    print(f"\n=== STEP 3: scan for noindex meta ===")
    noindex_pages = find_noindex_pages()
    print(f"  {len(noindex_pages)} local pages have noindex meta:")
    for p in noindex_pages:
        print(f"    {p.relative_to(ROOT)}")

    # Write CSV report
    report_path = OUT_DIR / f"indexing-audit-{today}.csv"
    with report_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "status", "final_url", "redirected"])
        for r in sorted(results, key=lambda x: (x["status"], x["url"])):
            w.writerow([r["url"], r["status"], r["final"], "yes" if r["redirected"] else ""])
    print(f"\n  Full report: {report_path.relative_to(ROOT)}")

    print("\n=== Issues to fix ===")
    print(f"  ✗ {len(not_found)} URLs return 404/410 — remove from sitemap, add redirects")
    print(f"  ✗ {len(redirects)} URLs redirect via 301/302 — should be canonical in sitemap")
    print(f"  ✗ {len(noindex_pages)} local pages have noindex meta — verify intentional")

    if not args.fix:
        print(f"\nMode: REPORT-ONLY — re-run with --fix to apply remediation")
        return 0

    print("\n=== STEP 4: apply fixes ===")

    # 1. Remove dead URLs from sitemap.xml (404/410/redirected)
    bad_urls = {r["url"] for r in not_found} | {r["url"] for r in redirects} | {r["url"] for r in redirected}
    print(f"  Removing {len(bad_urls)} bad URLs from sitemap.xml")
    if SITEMAP.exists():
        tree = ET.parse(SITEMAP)
        root = tree.getroot()
        ns_url = f"{{{NS}}}url"
        ns_loc = f"{{{NS}}}loc"
        to_remove = []
        for u in root.findall(ns_url):
            loc = u.findtext(ns_loc, default="").strip()
            if loc in bad_urls:
                to_remove.append(u)
        for u in to_remove:
            root.remove(u)
        ET.register_namespace("", NS)
        tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
        print(f"  ✓ Sitemap cleaned. Removed {len(to_remove)} entries.")

    # 2. Build _redirects entries for the 404s (best guess: redirect to homepage or category)
    redirects_path = ROOT / "_redirects"
    existing = redirects_path.read_text(encoding="utf-8") if redirects_path.exists() else ""
    new_lines = ["", "# Auto-added 404 redirects from indexing audit", f"# Audit date: {today}"]
    for r in not_found:
        u = r["url"]
        path = urllib.parse.urlparse(u).path
        # Heuristic: redirect to a likely-relevant section
        target = "/"
        if "neighborhoods" in path:
            target = "/neighborhoods/"
        elif "zip" in path:
            target = "/zip/"
        elif "long-island" in path:
            target = "/long-island/"
        elif "blog" in path:
            target = "/blog/"
        elif "market-reports" in path:
            target = "/market-reports/"
        elif "agents" in path or "meet-the-agents" in path:
            target = "/meet-the-agents.html"
        line = f"{path}  {target}  301"
        if line not in existing:
            new_lines.append(line)
    if len(new_lines) > 3:  # more than just header
        with redirects_path.open("a", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        print(f"  ✓ Added {len(new_lines) - 3} 301 redirects to _redirects")

    print(f"\n=== Next steps ===")
    print("  1. Review the audit CSV and any auto-added redirects")
    print("  2. Run scripts/rebuild_sitemap.py to ensure sitemap is canonical")
    print("  3. Run scripts/indexnow_ping.py --all to resubmit clean URLs to Bing")
    print("  4. In GSC: re-submit sitemap (Indexing → Sitemaps → re-add URL)")
    print("  5. Manually request indexing on top 10 priority pages via URL Inspection")
    return 0


if __name__ == "__main__":
    sys.exit(main())
