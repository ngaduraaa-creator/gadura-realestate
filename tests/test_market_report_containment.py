#!/usr/bin/env python3
"""V2-INC-02 containment regression tests.

Proves the market-report generator fails closed and that the 44 invalid flat
reports (incident V2-INC-01) are gone from every discovery surface, while the
105 ZIP-level NYC DOF reports and prior compliance work remain untouched.

Run from the repository root:  python3 tests/test_market_report_containment.py
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_market_report.py"
INVALID_URL = re.compile(r"2026-0[78]-[a-z-]+-market-report\.html")

PASS = TOTAL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, TOTAL
    TOTAL += 1
    PASS += bool(cond)
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{(' — ' + detail) if detail else ''}")


def load_generator():
    spec = importlib.util.spec_from_file_location("genmr", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_gen(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GEN), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )


def snapshot_reports() -> set[pathlib.Path]:
    return set((ROOT / "market-reports").glob("*-market-report.html"))


def main() -> int:
    gen = load_generator()

    # ---- 1. Fails when the input file is absent -------------------------
    print("[1] generator fails closed on missing input file")
    before = snapshot_reports()
    # 2026-07 is a completed month, so only the missing-input gate can trip.
    r = run_gen("--month", "2026-07", "--apply")
    check("exits nonzero", r.returncode != 0, f"rc={r.returncode}")
    check("explains the refusal", "REFUSED" in r.stderr and "missing" in r.stderr.lower())
    check("writes no report files", snapshot_reports() == before)

    # ---- 2. Fails on incomplete per-neighborhood fields -----------------
    print("[2] generator fails closed on incomplete fields")
    with tempfile.TemporaryDirectory() as td:
        # figures present, provenance absent
        p1 = pathlib.Path(td) / "figures_only.json"
        p1.write_text(json.dumps({
            "queens/ozone-park": {"median": 861000, "dom": 63, "ratio": 99, "sales_count": 30}
        }))
        r = run_gen("--month", "2026-07", "--inputs", str(p1), "--apply")
        check("rejects figures without provenance", r.returncode != 0, f"rc={r.returncode}")
        check("names the missing provenance", "provenance" in r.stderr.lower())

        # provenance present, a figure missing
        p2 = pathlib.Path(td) / "missing_figure.json"
        p2.write_text(json.dumps({
            "queens/ozone-park": {
                "median": 861000, "dom": 63, "ratio": 99,  # sales_count absent
                "source": "OneKey® MLS", "retrieved_on": "2026-08-01",
                "geography": "ZIPs 11416, 11417", "property_types": "SF/condo/co-op",
                "reporting_window": "July 1-31, 2026", "metric_definitions": "median of closed sales",
            }
        }))
        r = run_gen("--month", "2026-07", "--inputs", str(p2), "--apply")
        check("rejects missing figure", r.returncode != 0, f"rc={r.returncode}")
        check("writes nothing on field failure", snapshot_reports() == before)

    # ---- 3. Fails for an unfinished reporting period --------------------
    print("[3] generator fails closed on an unfinished period")
    today = dt.date.today()
    current_month = today.strftime("%Y-%m")
    r = run_gen("--month", current_month, "--apply")
    check("current month refused", r.returncode != 0, f"rc={r.returncode}")
    check("cites the period", "has not ended" in r.stderr)
    future_month = (today.replace(day=1) + dt.timedelta(days=62)).strftime("%Y-%m")
    r = run_gen("--month", future_month, "--apply")
    check("future month refused", r.returncode != 0, f"rc={r.returncode}")
    try:
        gen.validate_month_complete("2026-07", dt.date(2026, 8, 15))
        check("completed month passes the gate", True)
    except Exception as exc:  # noqa: BLE001
        check("completed month passes the gate", False, str(exc))

    # ---- 4. Rejects a future publication date ---------------------------
    print("[4] generator rejects future publication dates")
    raised = False
    try:
        gen.validate_publication_date("2026-08-31", dt.date(2026, 8, 15))
    except gen.InputValidationError:
        raised = True
    check("future datePublished rejected", raised)
    ok = True
    try:
        gen.validate_publication_date("2026-07-31", dt.date(2026, 8, 15))
    except gen.InputValidationError:
        ok = False
    check("past datePublished accepted", ok)

    # ---- 5. No synthetic fallback statistics survive --------------------
    print("[5] no synthetic market statistics remain available")
    src = GEN.read_text(encoding="utf-8")
    check("no _default_median()", "_default_median" not in src)
    check("no _borough_median()", "_borough_median" not in src)
    for bad in ('.get("median",', '.get("dom",', '.get("ratio",', '.get("sales_count",'):
        check(f"no defaulted figure {bad.strip('.')}", bad not in src)
    check("no synthetic prior-month derivation", "* 0.985" not in src)
    check("required-figure contract present", "REQUIRED_FIGURES" in src)
    check("required-provenance contract present", "REQUIRED_PROVENANCE" in src)

    # ---- 6. No unconditional OneKey attribution -------------------------
    print("[6] source attribution comes only from validated input")
    body = src.split('"""', 2)[-1]  # ignore the module docstring
    check("template emits {data_source}", "{data_source}" in body)
    check("no hardcoded OneKey in emitted HTML",
          "Data sourced from OneKey" not in body and "through OneKey" not in body)

    # ---- 7. The 44 invalid reports are gone everywhere -------------------
    print("[7] invalid reports absent from files, sitemaps, feeds, links")
    flat = sorted((ROOT / "market-reports").glob("2026-0[78]-*-market-report.html"))
    check("no invalid report files on disk", not flat, f"{len(flat)} found")
    for surface in ("sitemap.xml", "sitemap-news.xml", "rss.xml", "feed.json"):
        p = ROOT / surface
        hits = len(INVALID_URL.findall(p.read_text(errors="ignore"))) if p.exists() else 0
        check(f"{surface} clean", hits == 0, f"{hits} refs")
    linkers = [p for p in ROOT.rglob("*.html")
               if "/.git/" not in str(p) and INVALID_URL.search(p.read_text(errors="ignore"))]
    check("no surviving internal links", not linkers, f"{len(linkers)} files")

    # ---- 8. ZIP-level DOF reports intact --------------------------------
    print("[8] ZIP-level NYC DOF reports preserved")
    zip_reports = list((ROOT / "market-reports" / "queens").rglob("index.html"))
    check("105 ZIP-level reports present", len(zip_reports) == 105, f"{len(zip_reports)} found")
    dof = [p for p in zip_reports if "Department of Finance" in p.read_text(errors="ignore")]
    check("DOF attribution retained", len(dof) > 0, f"{len(dof)} cite DOF")

    # ---- 9. Prior compliance work intact --------------------------------
    print("[9] LA-3B0G license + LA-3B0J schema protections intact")
    wrong_lic, self_review = [], []
    for p in ROOT.rglob("*.html"):
        if "/.git/" in str(p):
            continue
        t = p.read_text(errors="ignore")
        if "10991238487" in t:
            wrong_lic.append(p)
        if "aggregateRating" in t and "gadurarealestate.com/#brokerage" in t:
            self_review.append(p)
    check("no wrong license number (LA-3B0G)", not wrong_lic, f"{len(wrong_lic)} files")
    check("no self-serving rating markup (LA-3B0J)", not self_review, f"{len(self_review)} files")
    footer = ROOT / "_includes" / "legal-footer.html"
    check("firm license #109926909 preserved",
          "109926909" in footer.read_text(errors="ignore") if footer.exists() else False)

    # ---- 10. Unrelated pages and workflows unchanged ---------------------
    print("[10] containment scope is bounded")
    changed = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                             text=True, cwd=str(ROOT)).stdout.split("\n")
    modified = [ln[3:] for ln in changed if ln.startswith(" M") or ln.startswith("M ")]
    allowed = {
        ".github/workflows/monthly-market-reports.yml",
        "scripts/generate_market_report.py",
        "sitemap.xml", "sitemap-news.xml", "rss.xml", "feed.json",
        "tests/test_market_report_containment.py",
    }
    unexpected = [m for m in modified if m and m not in allowed]
    check("no unrelated file modified", not unexpected, ", ".join(unexpected[:4]))
    other_wf = [p.name for p in (ROOT / ".github" / "workflows").glob("*.yml")
                if p.name != "monthly-market-reports.yml"
                and p.name in [m.split("/")[-1] for m in modified]]
    check("other workflows untouched", not other_wf, ", ".join(other_wf))
    wf = (ROOT / ".github" / "workflows" / "monthly-market-reports.yml").read_text()
    active_cron = [ln for ln in wf.splitlines()
                   if "cron:" in ln and not ln.strip().startswith("#")]
    check("cron schedule disabled", not active_cron, "; ".join(active_cron))
    check("manual dispatch retained", "workflow_dispatch:" in wf)

    print(f"\n{PASS}/{TOTAL} passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())
