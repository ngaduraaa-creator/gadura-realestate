#!/usr/bin/env python3
"""Phone-number consistency gate.

WHY THIS EXISTS
---------------
Two separate phone failures have reached production on this site.

1. A DIGIT TRANSPOSITION.  Three indexed market-report pages published
   (718) 750-0010 -- a transposition of the real office line (718) 850-0010 --
   in both the visible text and the tel: href, across 8 CTA buttons. It was
   live from 2026-06-08 until PR #102 merged on 2026-09-15. Two of the three
   were Ozone Park pages, the core farm area. Nothing detected it for three
   months; it was found by hand.

2. A DISPLAY/DIAL SPLIT.  115 anchors across 110 files show one number and
   dial the other. A visitor reads (718) 850-0010, taps, and reaches
   (917) 705-0132 -- or the reverse. On mobile, where the tap is the whole
   interaction, the displayed number is decorative and the href is what runs.

Neither is visible to the existing guards. check_schema_policy.py validates
schema shape, test_compliance_gates.py checks claim language, and
test_ai_surface_claims.py scans non-HTML surfaces. None compares what a phone
link SAYS against what it DOES.

This gate closes that gap. It is the regression test PR #102 never got.

THE TWO CHECKS
--------------
TRANSPOSED (hard failure, never baselineable)
    Any occurrence of a known-wrong number, in any tracked text file --
    HTML, generator, sitemap, llms.txt, JSON. These are not judgement calls:
    (718) 750-0010 is not a number this business has ever owned. There is no
    baseline escape hatch, because the only correct count is zero, and because
    a stale branch reintroducing it is exactly how it would come back.

MISMATCH (baselined)
    An anchor whose visible text contains a phone number different from the
    one in its tel: href. 115 exist today. Fixing them requires first deciding
    WHICH line is the public brokerage number -- a business decision for the
    broker, not an engineering change -- so this gate does not pick a winner.
    It records the known count per file in BASELINE and fails on:
      - a mismatch in a file not in BASELINE      (a NEW regression)
      - MORE mismatches in a baselined file       (an existing file getting worse)
    It passes, while printing the outstanding debt, when findings are exactly
    what BASELINE records.

Shrink BASELINE toward {} as files are corrected. Do not add entries to
silence a new problem -- that is what the transposition check exists to
prevent, and adding a baseline for a real regression defeats the gate.

WHY THE BASELINE WILL NOT SILENTLY ROT
--------------------------------------
Entries that stop firing are reported as CLEARED so the baseline gets trimmed
rather than quietly outliving the problem it described.

Run:  python3 scripts/dgp/test_phone_consistency.py      (exit 0 pass / 1 fail)
      python3 scripts/dgp/test_phone_consistency.py --emit-baseline
      python3 scripts/dgp/test_phone_consistency.py --list   (full finding list)

Reads the working tree and writes nothing.
"""
from __future__ import annotations

import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Directories that are not part of the published site or are machine-generated.
SKIP_DIRS = {".git", "node_modules", "audit_exports", ".claude", "ai-monitoring"}

# Text surfaces the transposition check sweeps. HTML alone is not enough: the
# number reached production through hand-edited pages, and a generator holding
# it would re-emit it on the next build.
TEXT_SUFFIXES = {".html", ".htm", ".js", ".py", ".json", ".txt", ".xml", ".md"}

# Numbers this business has never owned, as bare digits (no country code).
# Keep the reason attached -- a bare number list rots into folklore.
KNOWN_WRONG: dict[str, str] = {
    "7187500010": "digit transposition of the office line (718) 850-0010; "
                  "live 2026-06-08 to 2026-09-15, fixed by PR #102",
}

# Generators must read data/business-contact.json, not carry their own copy of
# the number. A literal here is how 16 copies accumulated across two languages
# and how a corrected number could be reverted by the next build.
# Every script under scripts/ except the gates themselves (scripts/dgp/), which
# legitimately name the numbers they hunt for. Discovered, not listed: the first
# version of this check kept an allowlist of two files and reported "ok" while a
# third generator, build_specialty_feeds.py, still hardcoded the number.
def generators() -> list[str]:
    out = []
    for p in sorted((ROOT / "scripts").rglob("*")):
        if p.suffix not in {".py", ".js"} or not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if rel.parts[:2] == ("scripts", "dgp"):
            continue
        out.append(str(rel))
    return out
PHONE_LITERAL = re.compile(
    r"\(\d{3}\)\s*\d{3}-\d{4}"   # (917) 705-0132
    r"|\+1\d{10}"                  # +19177050132
)

ANCHOR = re.compile(r'<a\b[^>]*href=["\']tel:([^"\']*)["\'][^>]*>(.*?)</a>', re.I | re.S)
TAG = re.compile(r"<[^>]+>")
PHONE_IN_TEXT = re.compile(
    r"(?:\+?1[\s.\-]?)?\(?(\d{3})\)?[\s.\-]?(\d{3})[\s.\-]?(\d{4})"
)

# Known mismatch counts per file, recorded 2026-09-22 against origin/main
# merged into guard/ai-surface-compliance. Blocked on the broker deciding
# which line is the public brokerage number -- see the module docstring.
BASELINE: dict[str, int] = {
    'best-listing-agent-queens.html': 1,
    'blog/bay-ridge-market-report-2026.html': 1,
    'blog/flatbush-market-report-2026.html': 1,
    'blog/how-to-choose-real-estate-agent-queens.html': 1,
    'blog/investment-property-queens-brooklyn.html': 1,
    'blog/jamaica-market-report-2026.html': 1,
    'blog/nassau-county-real-estate-guide.html': 1,
    'blog/new-construction-homes-queens-li.html': 1,
    'blog/nyc-closing-costs-explained.html': 1,
    'blog/queens-ny-relocation-guide.html': 1,
    'blog/real-estate-investment-queens.html': 1,
    'blog/rent-vs-buy-queens-ny.html': 1,
    'blog/richmond-hill-market-report-2026.html': 1,
    'blog/short-sale-guide-queens-ny.html': 1,
    'blog/south-asian-multigenerational-homes.html': 1,
    'blog/south-ozone-park-market-report-2026.html': 1,
    'blog/woodhaven-market-report-2026.html': 1,
    'calculators/1031-timeline.html': 1,
    'calculators/fha-self-sufficiency.html': 1,
    'calculators/mortgage.html': 1,
    'faq/buying-home-brooklyn.html': 1,
    'faq/buying-home-long-island.html': 1,
    'faq/buying-home-queens.html': 1,
    'faq/coop-vs-condo.html': 1,
    'faq/first-time-buyers-nyc.html': 1,
    'faq/real-estate-investing-nyc.html': 1,
    'faq/renting-vs-buying.html': 1,
    'hindi-speaking-real-estate-agent-queens.html': 1,
    'home-value/hollis-home-value.html': 1,
    'home-value/index.html': 1,
    'home-value/ozone-park-home-value.html': 1,
    'home-value/south-jamaica-home-value.html': 1,
    'home-value/south-ozone-park-home-value.html': 1,
    'market-reports/index.html': 1,
    'market-reports/queens-market-report-q1-2026.html': 1,
    'market-reports/queens/index.html': 1,
    'market-reports/queens/ozone-park-11416/2024/index.html': 1,
    'market-reports/queens/ozone-park-11416/2026-04/index.html': 2,
    'market-reports/queens/richmond-hill-11418/2026-04/index.html': 2,
    'market-reports/queens/richmond-hill-11418/index.html': 1,
    'neighborhoods/astoria.html': 1,
    'neighborhoods/bayside.html': 1,
    'neighborhoods/bethpage.html': 1,
    'neighborhoods/brooklyn/windsor-terrace.html': 1,
    'neighborhoods/corona.html': 1,
    'neighborhoods/douglaston.html': 1,
    'neighborhoods/elmhurst.html': 1,
    'neighborhoods/elmont.html': 1,
    'neighborhoods/farmingdale.html': 1,
    'neighborhoods/floral-park.html': 1,
    'neighborhoods/flushing.html': 1,
    'neighborhoods/forest-hills.html': 1,
    'neighborhoods/franklin-square.html': 1,
    'neighborhoods/garden-city.html': 1,
    'neighborhoods/glendale.html': 1,
    'neighborhoods/great-neck.html': 1,
    'neighborhoods/hempstead.html': 1,
    'neighborhoods/hicksville.html': 1,
    'neighborhoods/jericho.html': 1,
    'neighborhoods/levittown.html': 1,
    'neighborhoods/little-neck.html': 1,
    'neighborhoods/long-beach.html': 1,
    'neighborhoods/lynbrook.html': 1,
    'neighborhoods/maspeth.html': 1,
    'neighborhoods/massapequa.html': 1,
    'neighborhoods/middle-village.html': 1,
    'neighborhoods/mineola.html': 1,
    'neighborhoods/oceanside.html': 1,
    'neighborhoods/port-washington.html': 1,
    'neighborhoods/rego-park.html': 1,
    'neighborhoods/ridgewood.html': 1,
    'neighborhoods/rockaway-beach.html': 1,
    'neighborhoods/rockville-centre.html': 1,
    'neighborhoods/roslyn.html': 1,
    'neighborhoods/sunnyside.html': 1,
    'neighborhoods/syosset.html': 1,
    'neighborhoods/westbury.html': 1,
    'neighborhoods/whitestone.html': 1,
    'neighborhoods/woodside.html': 1,
    'nitin-gadura/index.html': 1,
    'press/index.html': 1,
    'punjabi-speaking-real-estate-agent-queens.html': 1,
    'rentals/apartments-for-rent-astoria.html': 1,
    'rentals/apartments-for-rent-flushing.html': 1,
    'rentals/apartments-for-rent-howard-beach.html': 1,
    'rentals/apartments-for-rent-jamaica-queens.html': 1,
    'rentals/apartments-for-rent-ozone-park.html': 1,
    'rentals/apartments-for-rent-richmond-hill.html': 1,
    'rentals/index.html': 1,
    'resources/index.html': 1,
    'sell-home-richmond-hill.html': 1,
    'sell/index.html': 2,
    'seller-leads/index.html': 1,
    'seller-leads/sell-home-fast-long-island.html': 1,
    'services/buy-home-queens-long-island.html': 1,
    'services/commercial-real-estate.html': 1,
    'services/luxury-homes.html': 1,
    'services/multi-family-homes.html': 2,
    'services/rent-queens-long-island.html': 1,
    'v2/index.html': 1,
    'v2/neighborhoods/ozone-park.html': 1,
    'v2/sell-bn.html': 1,
    'v2/sell-es.html': 1,
    'v2/sell-pa.html': 1,
    'v2/sell-ur.html': 1,
    'v2/situations/sell-my-house-fast-ozone-park.html': 1,
    'v2/situations/selling-before-foreclosure-queens.html': 1,
    'v2/situations/selling-house-during-divorce-ny.html': 1,
    'v2/situations/selling-house-in-probate-ny.html': 2,
    'v2/situations/selling-tenant-occupied-property-ny.html': 1,
}


def digits(raw: str) -> str:
    """Bare 10-digit form, dropping a leading US country code."""
    d = re.sub(r"\D", "", raw)
    if len(d) == 11 and d.startswith("1"):
        return d[1:]
    return d


def pretty(d: str) -> str:
    return f"({d[0:3]}) {d[3:6]}-{d[6:10]}" if len(d) == 10 else d or "(empty)"


def walk() -> list[pathlib.Path]:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return out


def scan() -> tuple[dict[str, list[str]], dict[str, list[tuple[str, str]]], Counter]:
    """Return (transposed, mismatches, href_distribution), all keyed by relpath."""
    transposed: dict[str, list[str]] = defaultdict(list)
    mismatches: dict[str, list[tuple[str, str]]] = defaultdict(list)
    href_dist: Counter = Counter()

    for path in walk():
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # This file is the registry of wrong numbers; it names them on purpose.
        if rel != str(pathlib.Path(__file__).relative_to(ROOT)):
            bare = re.sub(r"\D", "", text)
            for wrong in KNOWN_WRONG:
                if wrong in bare:
                    transposed[rel].append(wrong)

        if path.suffix.lower() not in {".html", ".htm"}:
            continue

        for href, inner in ANCHOR.findall(text):
            dialed = digits(href)
            href_dist[dialed] += 1
            shown = PHONE_IN_TEXT.search(TAG.sub(" ", inner))
            if not shown:
                # A "Call Now" button with no number in the label cannot
                # contradict itself. Nothing to check.
                continue
            displayed = digits("".join(shown.groups()))
            if displayed != dialed:
                mismatches[rel].append((displayed, dialed))

    return dict(transposed), dict(mismatches), href_dist


def main() -> int:
    emit = "--emit-baseline" in sys.argv
    verbose = "--list" in sys.argv

    transposed, mismatches, href_dist = scan()

    if emit:
        print("BASELINE: dict[str, int] = {")
        for rel in sorted(mismatches):
            print(f'    {rel!r}: {len(mismatches[rel])},')
        print("}")
        return 0

    print("=== phone consistency gate ===")
    print(f"tel: anchors scanned : {sum(href_dist.values())}")
    print("dialed number distribution:")
    for num, count in href_dist.most_common(6):
        print(f"    {pretty(num):<18} {count}")

    failures: list[str] = []

    # --- check 1: known-wrong numbers, no baseline escape ------------------
    if transposed:
        total = sum(len(v) for v in transposed.values())
        print(f"\nFAIL: known-wrong number present in {len(transposed)} file(s)")
        for rel in sorted(transposed):
            for wrong in sorted(set(transposed[rel])):
                print(f"    {pretty(wrong)}  {rel}")
                print(f"        why wrong: {KNOWN_WRONG[wrong]}")
        failures.append(f"{total} known-wrong number occurrence(s)")
    else:
        print(f"\nok  no known-wrong numbers ({len(KNOWN_WRONG)} pattern(s) checked)")

    # --- check 2: generators must not hardcode a number ---------------------
    hardcoded: list[tuple[str, str]] = []
    gens = generators()
    for rel in gens:
        f = ROOT / rel
        for lineno, line in enumerate(f.read_text(encoding="utf-8",
                                                  errors="replace").splitlines(), 1):
            for hit in PHONE_LITERAL.findall(line):
                hardcoded.append((f"{rel}:{lineno}", hit))

    if hardcoded:
        print(f"\nFAIL: {len(hardcoded)} hardcoded phone literal(s) in generator(s)")
        for where, hit in hardcoded[:15]:
            print(f"    {hit}  {where}")
        print("    Generators must read data/business-contact.json instead.")
        failures.append(f"{len(hardcoded)} hardcoded generator literal(s)")
    else:
        print(f"ok  no phone literals in {len(gens)} script(s) under scripts/ "
              f"(they read data/business-contact.json)")

    # --- check 3: display/dial mismatches, baselined ------------------------
    new_files: list[str] = []
    worsened: list[tuple[str, int, int]] = []
    outstanding = 0

    for rel in sorted(mismatches):
        found = len(mismatches[rel])
        allowed = BASELINE.get(rel)
        if allowed is None:
            new_files.append(rel)
        elif found > allowed:
            worsened.append((rel, allowed, found))
        else:
            outstanding += found

    cleared = [rel for rel in BASELINE if rel not in mismatches]

    if new_files:
        print(f"\nFAIL: display/dial mismatch in {len(new_files)} un-baselined file(s)")
        for rel in new_files[:20]:
            for displayed, dialed in mismatches[rel][:3]:
                print(f"    shows {pretty(displayed)}  dials {pretty(dialed)}  {rel}")
        if len(new_files) > 20:
            print(f"    ... and {len(new_files) - 20} more (--list for all)")
        failures.append(f"{len(new_files)} file(s) with new mismatches")

    if worsened:
        print(f"\nFAIL: {len(worsened)} baselined file(s) got worse")
        for rel, allowed, found in worsened:
            print(f"    {rel}: baseline {allowed} -> {found}")
        failures.append(f"{len(worsened)} file(s) regressed past baseline")

    if outstanding:
        direction: Counter = Counter()
        for rel in mismatches:
            if rel in BASELINE:
                for displayed, dialed in mismatches[rel]:
                    direction[(displayed, dialed)] += 1
        print(f"\nOUTSTANDING (baselined — AWAITING BROKER DECISION ON PUBLIC LINE):")
        print(f"    {outstanding} mismatch(es) across "
              f"{len([r for r in mismatches if r in BASELINE])} file(s)")
        for (displayed, dialed), count in direction.most_common():
            print(f"    shows {pretty(displayed)} -> dials {pretty(dialed)}   x{count}")
        if verbose:
            for rel in sorted(r for r in mismatches if r in BASELINE):
                print(f"      {len(mismatches[rel]):>3}  {rel}")

    if cleared:
        print(f"\nCLEARED — remove these from BASELINE ({len(cleared)}):")
        for rel in sorted(cleared)[:20]:
            print(f"    {rel}")

    if failures:
        print("\nFAILED: " + "; ".join(failures))
        print("  Do NOT add these to BASELINE to make the gate pass.")
        return 1

    print(f"\nPASS — no new phone inconsistencies. "
          f"{outstanding} baselined mismatch(es) still outstanding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
