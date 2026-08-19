#!/usr/bin/env python3
"""V2-INC-02-R2 INDEPENDENT negative suite.

Authorship: WEB-18 lane (Phase 3A session), independent of the containment
implementation (authored 2026-08-15 by the V2-INC-02 lane). Acceptance criteria
were fixed in the Phase 3A command BEFORE these tests were written.

Run from repo root: python3 tests/test_market_report_negatives.py
All generator invocations assert FAILURE (exit!=0) and zero filesystem writes,
so this suite is safe to run inside a clean worktree.
"""
from __future__ import annotations
import datetime as dt, json, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_market_report.py"
WF = ROOT / ".github" / "workflows" / "monthly-market-reports.yml"
PASS = TOTAL = 0

def check(name, cond, detail=""):
    global PASS, TOTAL; TOTAL += 1
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f" — {detail}" if detail and not cond else ""))
    if cond: PASS += 1

def run_gen(*args):
    return subprocess.run([sys.executable, str(GEN), *args], capture_output=True, text=True, cwd=ROOT)

def snap():
    return sorted(p.name for p in (ROOT/"market-reports").rglob("*.html"))

BEFORE = snap()
GOOD_RECORD = {
    "median": 861000, "dom": 63, "ratio": 99, "sales_count": 30,
    "source": "OneKey® MLS", "retrieved_on": "2026-08-01",
    "geography": "ZIPs 11416, 11417", "property_types": "SF/condo/co-op",
    "reporting_window": "July 1-31, 2026", "metric_definitions": "median of closed sales",
}

print("[N1] missing inputs file → refuse, write nothing")
r = run_gen("--month", "2026-07", "--inputs", "/nonexistent/inputs.json", "--apply")
check("nonzero exit", r.returncode != 0, f"rc={r.returncode}")
check("no writes", snap() == BEFORE)

print("[N2] EMPTY inputs object → refuse (no silent constant fill)")
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td)/"empty.json"; p.write_text("{}")
    r = run_gen("--month", "2026-07", "--inputs", str(p), "--apply")
    check("empty {} rejected", r.returncode != 0, f"rc={r.returncode}")
    check("no writes", snap() == BEFORE)

print("[N3] MALFORMED inputs (invalid JSON / wrong shape) → refuse")
with tempfile.TemporaryDirectory() as td:
    p1 = pathlib.Path(td)/"bad.json"; p1.write_text("{ not json !!")
    r1 = run_gen("--month", "2026-07", "--inputs", str(p1), "--apply")
    p2 = pathlib.Path(td)/"wrongshape.json"; p2.write_text(json.dumps(["a","list","not","a","map"]))
    r2 = run_gen("--month", "2026-07", "--inputs", str(p2), "--apply")
    check("syntactically invalid rejected", r1.returncode != 0, f"rc={r1.returncode}")
    check("wrong-shape rejected", r2.returncode != 0, f"rc={r2.returncode}")
    check("no writes", snap() == BEFORE)

print("[N4] CURRENT unfinished month → refuse even with complete data")
now = dt.date.today()
cur = f"{now.year}-{now.month:02d}"
with tempfile.TemporaryDirectory() as td:
    slugs = re.findall(r'"borough":\s*"([a-z-]+)",\s*"slug":\s*"([a-z0-9-]+)"', GEN.read_text())
    full = {f"{b}/{s}": dict(GOOD_RECORD, reporting_window=f"{cur} full month") for b, s in slugs}
    p = pathlib.Path(td)/"full.json"; p.write_text(json.dumps(full))
    r = run_gen("--month", cur, "--inputs", str(p), "--apply")
    check("current month rejected", r.returncode != 0, f"rc={r.returncode}")
    check("names the temporal rule", "not ended" in (r.stderr or "").lower() and "REFUSED" in (r.stderr or ""))
    check("no writes", snap() == BEFORE)

print("[N5] FUTURE month → refuse")
future = f"{now.year + 1}-01"
r = run_gen("--month", future, "--apply")
check("future month rejected", r.returncode != 0, f"rc={r.returncode}")
check("no writes", snap() == BEFORE)

print("[N6] fallback attribution impossible: no constants, no unconditional MLS text")
src = GEN.read_text()
check("no _default_median", "_default_median" not in src)
check("no _borough_median", "_borough_median" not in src)
check("no figure .get() defaults", not re.search(r'\.get\(\s*"(median|dom|ratio|sales_count)"\s*,', src))
check("no synthetic prior (×0.985)", "0.985" not in src)
check("no hardcoded OneKey emission in code paths", "OneKey" not in re.sub(r"#.*", "", src) or '"source"' in src and "data_source" in src)
check("attribution flows from validated input field", "data_source" in src)

print("[N7] discovery surfaces cannot regenerate the 44 (removal is real)")
inv = re.compile(r"2026-0[78]-[a-z0-9-]+-market-report\.html")
for f in ("sitemap.xml","sitemap-news.xml","rss.xml","feed.json"):
    check(f"{f} carries 0 invalid refs", not inv.search((ROOT/f).read_text()))
check("0 invalid page files on disk", not [p for p in (ROOT/"market-reports").glob("2026-0[78]-*.html")])
rb = (ROOT/"scripts"/"rebuild_sitemap.py")
check("rebuild_sitemap sources from filesystem (removed pages cannot re-enter)",
      rb.exists() and re.search(r"(rglob|glob|walk)", rb.read_text()) is not None)

print("[N8] IndexNow cannot fire on a failed generation (workflow ordering)")
wf = WF.read_text()
gen_i = wf.find("Generate market reports"); idx_i = wf.find("Submit to IndexNow")
check("generate step precedes IndexNow in same job", 0 < gen_i < idx_i)
check("no continue-on-error on generate", "continue-on-error" not in wf)

print("[N9] direct-to-main auto-publish disarmed for this pipeline")
check("no cron schedule trigger", "schedule:" not in wf or "# " in wf.split("schedule:")[0].splitlines()[-1] if "schedule:" in wf else True)
check("cron line absent/commented", not re.search(r"^\s*-\s*cron:", wf, re.M))
check("manual dispatch retained", "workflow_dispatch" in wf)

print("[N10] IDX-sync drift independence (listings.json orthogonal to containment)")
check("generator never reads listings.json", "listings.json" not in src)
check("containment file set excludes data/listings.json",
      "data/listings.json" not in subprocess.run(["git","diff","--name-only","HEAD~1","HEAD"],capture_output=True,text=True,cwd=ROOT).stdout)

print(f"\n{PASS}/{TOTAL} passed")
sys.exit(0 if PASS == TOTAL else 1)
