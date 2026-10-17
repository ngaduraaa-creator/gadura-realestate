#!/usr/bin/env python3
"""Regression fixtures for the feed-aware denylist exemption.

Covers the acceptance criteria for "Make the DGP denylist feed-aware":
  * the two live listing URLs that failed build-pages.yml on 2026-08-22 pass
    when backed by an active feed record, and fail when that record is removed,
    made inactive, stripped of photos, or address-mismatched
  * a genuine placeholder URL stays blocked even though it looks like a listing
  * deny-by-default when the feed is missing, malformed, not a list, or stale
  * ambiguity (two records -> one canonical URL) stays denied
  * normalization boundaries: trailing slash, query, fragment, case,
    prefix-vs-exact

Runs entirely on in-memory fixtures. Reads no sitemap and writes nothing.

Run: python3 scripts/dgp/test_denylist_feed_aware.py   (exit 0 pass / 1 fail)
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("guard", HERE / "test_placeholder_denylist.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

LISA = "https://gadurarealestate.com/homes/25-lisa-drive-dix-hills-new-york-11746"
JAMAICA = "https://gadurarealestate.com/homes/10522-jamaica-avenue-richmond-hill-new-york-11418"

PASS = FAIL = 0


def check(name: str, got, want) -> None:
    global PASS, FAIL
    if got == want:
        PASS += 1
        print(f"  ok    {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}\n          got={got!r}\n          want={want!r}")


def rec(address, city, zipc, mls, status="Active", photos=None, state="New York"):
    return {
        "address": address, "city": city, "state": state, "zip": zipc,
        "mlsNumber": mls, "status": status,
        "photos": ["https://s3.amazonaws.com/mlsphotos/a.jpg"] if photos is None else photos,
    }


LISA_REC = rec("25 Lisa Drive, Dix Hills, New York, 11746", "Dix Hills", "11746", "998692")
JAM_A = rec("10522 Jamaica Avenue, Richmond Hill, New York, 11418", "Richmond Hill", "11418", "999236")
JAM_B = rec("10522 Jamaica Avenue, Richmond Hill, New York, 11418", "Richmond Hill", "11418", "986483")


def exempt(url: str, feed: list) -> bool:
    """True if the guard would permit this denylisted URL given this feed."""
    by_url, _ = guard.qualifying_records(feed)
    return len(by_url.get(guard.normalize_url(url), [])) == 1


print("=== canonical URL derivation matches the generator ===")
check("25 Lisa Drive -> XW1 denylisted URL",
      guard.normalize_url(guard.canonical_url(LISA_REC)), guard.normalize_url(LISA))
check("10522 Jamaica Ave -> XW1 denylisted URL",
      guard.normalize_url(guard.canonical_url(JAM_A)), guard.normalize_url(JAM_B and JAMAICA))

print("\n=== the two build-breaking URLs: backed vs not ===")
check("LISA passes when backed by one active record", exempt(LISA, [LISA_REC]), True)
check("LISA fails when the record is REMOVED", exempt(LISA, []), False)
check("LISA fails when the record is INACTIVE (Sold)",
      exempt(LISA, [dict(LISA_REC, status="Sold")]), False)
check("LISA fails when the record has NO photos",
      exempt(LISA, [dict(LISA_REC, photos=[])]), False)
check("LISA fails when photos are placeholder media only",
      exempt(LISA, [dict(LISA_REC, photos=["https://images.unsplash.com/x.jpg"])]), False)
check("LISA fails when the record has NO MLS number",
      exempt(LISA, [dict(LISA_REC, mlsNumber="")]), False)
check("LISA fails on ADDRESS MISMATCH (different street)",
      exempt(LISA, [rec("27 Lisa Drive, Dix Hills, New York, 11746", "Dix Hills", "11746", "998692")]), False)
check("LISA fails on ZIP mismatch",
      exempt(LISA, [rec("25 Lisa Drive, Dix Hills, New York, 11747", "Dix Hills", "11747", "998692")]), False)

print("\n=== ambiguity must stay denied ===")
check("JAMAICA denied when TWO records map to one URL", exempt(JAMAICA, [JAM_A, JAM_B]), False)
check("JAMAICA permitted when exactly ONE record remains", exempt(JAMAICA, [JAM_A]), True)

print("\n=== a genuine placeholder stays blocked ===")
fake = "https://gadurarealestate.com/homes/1025-vermont-street-brooklyn-ny-11207"
check("fabricated listing path NOT exempt against the real feed",
      exempt(fake, [LISA_REC, JAM_A]), False)
check("fabricated path not exempt even with an EMPTY feed", exempt(fake, []), False)

print("\n=== normalization boundaries (must not broaden eligibility) ===")
check("trailing slash is equivalent", exempt(LISA + "/", [LISA_REC]), True)
check("query string stripped", exempt(LISA + "/?utm_source=x", [LISA_REC]), True)
check("fragment stripped", exempt(LISA + "/#photos", [LISA_REC]), True)
check("UPPERCASE path is NOT exempt", exempt(LISA.upper(), [LISA_REC]), False)
check("prefix is NOT exempt (deeper path)", exempt(LISA + "/gallery", [LISA_REC]), False)
check("truncated prefix is NOT exempt",
      exempt("https://gadurarealestate.com/homes/25-lisa-drive", [LISA_REC]), False)
check("different host is NOT exempt",
      exempt(LISA.replace("gadurarealestate.com", "example.com"), [LISA_REC]), False)

print("\n=== deny-by-default when the feed is unusable ===")
with tempfile.TemporaryDirectory() as td:
    missing = os.path.join(td, "nope.json")
    check("missing feed -> unusable", guard.load_feed(missing)[0], None)

    bad = os.path.join(td, "bad.json")
    open(bad, "w").write("{not json")
    check("malformed feed -> unusable", guard.load_feed(bad)[0], None)

    notlist = os.path.join(td, "obj.json")
    json.dump({"listings": []}, open(notlist, "w"))
    check("feed not a list -> unusable", guard.load_feed(notlist)[0], None)

    def stamp(hours_ago: float) -> str:
        t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours_ago)
        return t.isoformat().replace("+00:00", "Z")

    stale = os.path.join(td, "stale.json")
    json.dump([dict(LISA_REC, lastSync=stamp(guard.FEED_MAX_AGE_HOURS + 1))], open(stale, "w"))
    feed, why = guard.load_feed(stale)
    check("stale feed (lastSync too old) -> unusable", feed, None)
    check("stale reason mentions staleness", "stale" in why, True)

    nostamp = os.path.join(td, "nostamp.json")
    json.dump([LISA_REC], open(nostamp, "w"))   # no lastSync at all
    feed, why = guard.load_feed(nostamp)
    check("feed with NO lastSync -> unusable", feed, None)
    check("reason mentions missing stamp", "lastSync" in why, True)

    fresh = os.path.join(td, "fresh.json")
    json.dump([dict(LISA_REC, lastSync=stamp(1))], open(fresh, "w"))
    check("fresh feed (lastSync 1h ago) -> usable", len(guard.load_feed(fresh)[0] or []), 1)

    # mtime must NOT influence the verdict — CI checkout rewrites it.
    old = time.time() - 90 * 24 * 3600
    os.utime(fresh, (old, old))
    check("ancient mtime does not make a fresh feed stale",
          len(guard.load_feed(fresh)[0] or []), 1)
    os.utime(stale, (time.time(), time.time()))
    check("fresh mtime does not rescue a stale feed", guard.load_feed(stale)[0], None)

print(f"\n{PASS}/{PASS + FAIL} passed")
sys.exit(1 if FAIL else 0)
