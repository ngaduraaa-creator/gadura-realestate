#!/usr/bin/env python3
"""ci_stage_manifest.py — fail-closed generated-output manifest (Gate B).

WHY THIS EXISTS
---------------
This repository is published at its ROOT by GitHub Pages: every tracked file
becomes a public URL. The market-report job previously staged with a bare
repository-wide `git add -A`, so any file present in the runner workspace at
commit time — a stray audit CSV, a .DS_Store, a scratch file, an editor
backup — was committed and published. Incident V2-INC-01 also showed that a
generator can emit content nobody reviewed; staging must therefore be an
allowlist derived from what the approved pipeline actually produces, never a
sweep of whatever happens to be on disk.

CONTRACT
--------
Classify EVERY modified / deleted / untracked path in the worktree. A path may
be staged only if it falls in one of three proven-output categories:

  REPORT       market-reports/**/*.html
               produced by generate_market_report.py, then rewritten by
               bulk_og_injector.py --path market-reports and the schema
               injectors. New files are permitted here and only here.

  FEED         exactly: sitemap.xml, sitemap-index.xml, sitemap-images.xml,
               sitemap-news.xml, rss.xml, feed.json
               produced by rebuild_sitemap.py / build_specialty_feeds.py.
               Modification only — these are tracked files.

  SCHEMA_HTML  a TRACKED, MODIFIED *.html inside the authoritative target set
               of inject_ai_schema.py and/or inject_faqpage_schema.py. The set
               is obtained by importing each injector and calling its own
               collect_targets(), so scope can never drift from the injectors.
               Modification only.

Anything else fails the run (exit 2) and nothing is staged:
  - deletions of any kind (this job must never remove content)
  - workflow / .github changes, including self-modification
  - scripts/, *.py, *.yml, *.js, *.css, *.md, internal docs, dotfiles
  - untracked files anywhere outside market-reports/
  - *.html modified outside the injectors' declared scope

The manifest is written OUTSIDE the repository (default $RUNNER_TEMP) and
uploaded as a workflow artifact, so it can never be committed or published.

EXIT CODES
  0  all changes validated; validated paths printed to stdout, one per line
  2  at least one violation, or a usage error. Every diagnostic line on stderr
     is prefixed "[stage-manifest]" so a caller can distinguish a real
     violation from an interpreter/startup failure that also exits 2.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = "[stage-manifest]"

FEEDS = {
    "sitemap.xml",
    "sitemap-index.xml",
    "sitemap-images.xml",
    "sitemap-news.xml",
    "rss.xml",
    "feed.json",
}

INJECTORS = ("inject_ai_schema", "inject_faqpage_schema")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def injector_scope() -> set[str]:
    """Authoritative schema-injector target set, from the injectors themselves."""
    scope: set[str] = set()
    for name in INJECTORS:
        path = ROOT / "scripts" / f"{name}.py"
        if not path.exists():
            print(f"{TAG} FATAL: injector missing: {path}", file=sys.stderr)
            raise SystemExit(2)
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        collect = getattr(mod, "collect_targets", None)
        if collect is None:
            print(f"{TAG} FATAL: {name} exposes no collect_targets()", file=sys.stderr)
            raise SystemExit(2)
        for p in collect():
            scope.add(Path(p).resolve().relative_to(ROOT).as_posix())
    return scope


def porcelain() -> list[tuple[str, str]]:
    """[(xy_status, path)] for every change, including untracked."""
    out = []
    for entry in git("status", "--porcelain=v1", "-uall", "-z").split("\0"):
        if not entry:
            continue
        out.append((entry[:2], entry[3:]))
    return out


def classify(xy: str, path: str, scope: set[str]) -> tuple[str, str]:
    """Return (category, reason). category == 'VIOLATION' means fail."""
    untracked = xy == "??"
    if "D" in xy:
        return "VIOLATION", "deletion — this job must never remove content"

    if path.startswith(".github/") or path.endswith((".yml", ".yaml")):
        return "VIOLATION", "workflow/CI definition (self-modification forbidden)"

    if path.startswith("scripts/") or path.endswith(".py"):
        return "VIOLATION", "generator/tooling source must not be rewritten by a run"

    if path.endswith((".js", ".css", ".md", ".txt", ".csv")) or Path(path).name.startswith("."):
        return "VIOLATION", "unrelated asset / internal document / dotfile"

    if path in FEEDS:
        if untracked:
            return "VIOLATION", "feed output appeared as an untracked file"
        return "FEED", "sitemap/feed regeneration"

    if path.startswith("market-reports/") and path.endswith(".html"):
        return "REPORT", "new market report" if untracked else "market report rewritten"

    if path.endswith(".html"):
        if untracked:
            return "VIOLATION", "untracked HTML outside market-reports/"
        if path in scope:
            return "SCHEMA_HTML", "schema injection inside declared injector scope"
        return "VIOLATION", "tracked HTML modified OUTSIDE declared injector scope"

    return "VIOLATION", "path matches no proven-output category"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True,
                    help="where to write the manifest (MUST be outside the repo)")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    try:
        manifest_path.relative_to(ROOT)
    except ValueError:
        pass  # good: outside the repository
    else:
        print(f"{TAG} FAIL: manifest path is inside the repository and would be "
              f"published: {manifest_path}", file=sys.stderr)
        return 2

    scope = injector_scope()
    changes = porcelain()

    allowed: list[str] = []
    violations: list[dict] = []
    records: list[dict] = []

    for xy, path in changes:
        cat, reason = classify(xy, path, scope)
        records.append({"status": xy, "path": path, "category": cat, "reason": reason})
        (violations if cat == "VIOLATION" else allowed).append(
            {"path": path, "status": xy, "reason": reason} if cat == "VIOLATION" else path
        )

    manifest = {
        "head": git("rev-parse", "HEAD").strip(),
        "injector_scope_size": len(scope),
        "total_changes": len(changes),
        "allowed": allowed,
        "violations": violations,
        "records": records,
        "verdict": "FAIL" if violations else "PASS",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    counts: dict[str, int] = {}
    for r in records:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    print(f"{TAG} HEAD={manifest['head'][:9]} changes={len(changes)} "
          f"scope={len(scope)}", file=sys.stderr)
    for k in ("REPORT", "FEED", "SCHEMA_HTML", "VIOLATION"):
        if k in counts:
            print(f"{TAG}   {k:<12} {counts[k]}", file=sys.stderr)

    if violations:
        print(f"{TAG} FAIL — refusing to stage:", file=sys.stderr)
        for v in violations[:40]:
            print(f"{TAG}   {v['status']} {v['path']}  <- {v['reason']}", file=sys.stderr)
        if len(violations) > 40:
            print(f"{TAG}   ... +{len(violations) - 40} more", file=sys.stderr)
        return 2

    if not allowed:
        print(f"{TAG} no generated output to stage", file=sys.stderr)
        return 0

    for p in allowed:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
