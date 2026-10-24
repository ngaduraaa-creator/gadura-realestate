#!/usr/bin/env python3
"""Regression fixtures for the feed-aware denylist exemption.

Covers the acceptance criteria for "Make the DGP denylist feed-aware":
  * the two live listing URLs that failed build-pages.yml on 2026-08-22 pass
    when backed by an active feed record, and fail when that record is removed,
    made inactive, stripped of photos, address-mismatched, or STALE
  * a genuine placeholder URL stays blocked even though it looks like a listing
  * deny-by-default when the feed is missing, malformed, not a list, or stale
  * ambiguity (two records -> one canonical URL) stays denied EVEN WHEN ONLY
    ONE of the two records would individually qualify -- the real shape of
    the live MLS 999236/986483 collision, not the two-qualifying-records
    shape the pre-2026-09-25 version of this file tested instead
  * normalization boundaries: trailing slash, query, fragment, case,
    prefix-vs-exact
  * the guard's own main() end to end: denylist + sitemap + feed on disk,
    real exit code, real stdout -- not just the internal helper functions

2026-09-25 REWORK (WEB-18 findings B3 + B4, 2026-09-24 review of 800adf6c2):
  B3  This file used to test qualifying_records(), normalize_url(), and
      load_feed() directly and never called guard.main(). Four deliberate
      mutations of the gate (including making it ignore sitemap <loc>
      normalization entirely) survived all 31 checks -- a disabled gate
      would have read green. See run_main_end_to_end() below: it builds a
      real denylist file, sitemap.xml, and data/listings.json on disk,
      monkeypatches the guard's path globals to point at them, and asserts
      on main()'s actual exit code and printed FAIL/EXEMPT/PASS lines.
  B4  The only ambiguity fixture (JAM_A + JAM_B, both below) gives BOTH
      colliding records real, qualifying photos -- a shape that does not
      exist in the live feed. The real MLS 999236/986483 collision has ONE
      qualifying record (986483: real photos) and ONE that fails the photo
      check on its own (999236: placeholder-only). See JAM_A_PLACEHOLDER
      below and the "real collision shape" section: the URL must stay
      denied even though exactly one of the two records would qualify if it
      were alone.

Runs entirely on in-memory fixtures plus one on-disk end-to-end pass in a
temp directory. Reads no repository file outside that temp directory and
writes nothing to the repository.

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


def stamp(hours_ago: float) -> str:
    t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours_ago)
    return t.isoformat().replace("+00:00", "Z")


def rec(address, city, zipc, mls, status="Active", photos=None, state="New York",
        last_sync_hours_ago=1.0):
    """A realistic, QUALIFYING-by-default record: fresh lastSync (1h ago) is
    now required by guard._record_qualifies() (WEB-18 finding B2, 2026-09-25
    fix), so every fixture must carry one unless it's deliberately testing
    staleness. Pass last_sync_hours_ago=None to omit the field entirely."""
    d = {
        "address": address, "city": city, "state": state, "zip": zipc,
        "mlsNumber": mls, "status": status,
        "photos": ["https://s3.amazonaws.com/mlsphotos/a.jpg"] if photos is None else photos,
    }
    if last_sync_hours_ago is not None:
        d["lastSync"] = stamp(last_sync_hours_ago)
    return d


LISA_REC = rec("25 Lisa Drive, Dix Hills, New York, 11746", "Dix Hills", "11746", "998692")
JAM_A = rec("10522 Jamaica Avenue, Richmond Hill, New York, 11418", "Richmond Hill", "11418", "999236")
JAM_B = rec("10522 Jamaica Avenue, Richmond Hill, New York, 11418", "Richmond Hill", "11418", "986483")
# The REAL shape (WEB-18 finding B4): one qualifying record, one that fails
# the photo check on its own -- not two qualifying records like JAM_A/JAM_B.
JAM_A_PLACEHOLDER = rec(
    "10522 Jamaica Avenue, Richmond Hill, New York, 11418", "Richmond Hill", "11418", "999236",
    photos=["/assets/images/placeholder.jpg"],
)


def exempt(url: str, feed: list) -> bool:
    """True if the guard would permit this denylisted URL given this feed."""
    by_url, _notes, _ambiguous = guard.qualifying_records(feed)
    return len(by_url.get(guard.normalize_url(url), [])) == 1


print("=== canonical URL derivation matches the generator ===")
check("25 Lisa Drive -> XW1 denylisted URL",
      guard.normalize_url(guard.canonical_url(LISA_REC)), guard.normalize_url(LISA))
check("10522 Jamaica Ave -> XW1 denylisted URL",
      guard.normalize_url(guard.canonical_url(JAM_A)), guard.normalize_url(JAMAICA))

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
check("LISA fails when ITS OWN lastSync is stale (25h), even with a fresh sibling record",
      exempt(LISA, [dict(LISA_REC, lastSync=stamp(25)), JAM_B]), False)
check("LISA fails when its lastSync is missing entirely",
      exempt(LISA, [{k: v for k, v in LISA_REC.items() if k != "lastSync"}]), False)
check("LISA passes at 23h (just inside the window)",
      exempt(LISA, [dict(LISA_REC, lastSync=stamp(23))]), True)

print("\n=== ambiguity must stay denied ===")
check("JAMAICA denied when TWO qualifying records map to one URL", exempt(JAMAICA, [JAM_A, JAM_B]), False)
check("JAMAICA permitted when exactly ONE record remains", exempt(JAMAICA, [JAM_A]), True)
print("  --- real collision shape (WEB-18 finding B4): one qualifies alone, one doesn't ---")
check("JAMAICA denied when one record is placeholder-only and the other is real (ambiguous, not exempted on the survivor)",
      exempt(JAMAICA, [JAM_A_PLACEHOLDER, JAM_B]), False)
by_url, notes, ambiguous = guard.qualifying_records([JAM_A_PLACEHOLDER, JAM_B])
check("that ambiguity is reported even though only one record would qualify alone",
      any("999236" in n and "986483" in n for n in notes), True)
check("the URL is in the ambiguous set (drives the gate's FAIL message, not a silent EXEMPT)",
      guard.normalize_url(JAMAICA) in ambiguous, True)

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

    stale = os.path.join(td, "stale.json")
    json.dump([dict(LISA_REC, lastSync=stamp(guard.FEED_MAX_AGE_HOURS + 1))], open(stale, "w"))
    feed, why = guard.load_feed(stale)
    check("stale feed (lastSync too old) -> unusable", feed, None)
    check("stale reason mentions staleness", "stale" in why, True)

    nostamp = os.path.join(td, "nostamp.json")
    json.dump([{k: v for k, v in LISA_REC.items() if k != "lastSync"}], open(nostamp, "w"))
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


def _sitemap(urls: list[str]) -> str:
    body = "".join(f"<url><loc>{u}/</loc></url>" for u in urls)
    return f"<?xml version=\"1.0\"?><urlset>{body}</urlset>"


def _invoke_main(td: str, files: dict[str, list[str] | str | bytes], feed) -> tuple[int, str]:
    """Lay out a denylist, the given root files, and a feed under td, point
    the guard's path globals at them, run guard.main(), return (exit, stdout).
    A list value is written as a sitemap of those URLs; a str or bytes is written
    raw (robots.txt, gzip, hand-written <loc> forms). Names may include
    subdirectories. feed=None writes no feed file; a str feed is written raw."""
    import contextlib
    import io

    os.makedirs(os.path.join(td, "scripts", "dgp"), exist_ok=True)
    os.makedirs(os.path.join(td, "data"), exist_ok=True)
    denylist_path = os.path.join(td, "scripts", "dgp", "placeholder_sitemap_denylist.txt")
    open(denylist_path, "w").write(f"{LISA}\n{JAMAICA}\n{fake}\n")
    feed_path = os.path.join(td, "data", "listings.json")
    if isinstance(feed, str):
        open(feed_path, "w").write(feed)
    elif feed is not None:
        json.dump(feed, open(feed_path, "w"))
    for name, content in files.items():
        path = os.path.join(td, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(content, bytes):
            open(path, "wb").write(content)
        else:
            open(path, "w").write(content if isinstance(content, str) else _sitemap(content))

    orig = (guard.ROOT, guard.DENYLIST, guard.FEED)
    guard.ROOT, guard.DENYLIST, guard.FEED = td, denylist_path, feed_path
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = guard.main()
        return exit_code, buf.getvalue()
    finally:
        guard.ROOT, guard.DENYLIST, guard.FEED = orig


def run_main_end_to_end() -> None:
    """WEB-18 finding B3, 2026-09-25 fix. Exercise guard.main() itself, not
    just its helpers: a real denylist file, a real sitemap, and a real
    data/listings.json on disk, with the guard's path globals monkeypatched
    to point at a temp directory, then check main()'s actual exit code and
    the actual lines it prints. A gate whose main() is broken (e.g. a stray
    change makes it never populate `bad`) would fail this even if every
    helper function above still works in isolation -- which is exactly the
    class of defect that let a disabled gate read green in the reviewed
    version."""
    with tempfile.TemporaryDirectory() as td:
        exit_code, out = _invoke_main(
            td, {"sitemap-listings.xml": [LISA, JAMAICA, fake]}, [LISA_REC, JAM_A_PLACEHOLDER, JAM_B])

        check("main() end-to-end: exit code is 1 (LISA exempt, JAMAICA ambiguous-denied, fake denied)",
              exit_code, 1)
        check("main() end-to-end: LISA is printed as EXEMPT", "EXEMPT:" in out and "lisa-drive" in out, True)
        check("main() end-to-end: JAMAICA is printed as FAIL with the ambiguity reason",
              "FAIL:" in out and "ambiguous" in out and "jamaica" in out, True)
        check("main() end-to-end: the genuine placeholder is printed as FAIL",
              "vermont-street" in out, True)
        check("main() end-to-end: violation count is exactly 2 (JAMAICA + the placeholder)",
              "2 violation(s)" in out, True)


def run_main_multi_sitemap() -> None:
    """WEB-18 re-review finding GATE-3, 2026-09-25: the gate must scan EVERY
    sitemap*.xml, not just the one the listing generator writes. Production
    mirrors this layout: sitemap-listings.xml is empty on main while the
    1,486 published URLs live in sitemap.xml. With a single hardcoded
    sitemap filename the suite could not tell "scans all sitemaps" from
    "scans only sitemap-listings.xml" -- that narrowing passed 42/42."""
    with tempfile.TemporaryDirectory() as td:
        exit_code, out = _invoke_main(
            td,
            {"sitemap-listings.xml": [LISA], "sitemap.xml": [fake]},
            [LISA_REC],
        )
        check("multi-sitemap: a placeholder present ONLY in sitemap.xml still fails the gate",
              exit_code, 1)
        check("multi-sitemap: the violation is attributed to sitemap.xml",
              "FAIL: sitemap.xml:" in out and "vermont-street" in out, True)
        check("multi-sitemap: the exemption in sitemap-listings.xml is still reported",
              "EXEMPT: sitemap-listings.xml:" in out, True)


def _filler(n: int) -> list[str]:
    return [f"https://gadurarealestate.com/blog/filler-post-number-{i:05d}" for i in range(n)]


def _raw_sitemap(*loc_elements: str) -> str:
    return "<?xml version=\"1.0\"?><urlset>" + "".join(f"<url>{e}</url>" for e in loc_elements) + "</urlset>"


ROBOTS = (
    "User-agent: *\n"
    "Sitemap: https://gadurarealestate.com/listings-feed.xml\n"
    "Sitemap: https://example.com/sitemap-other-host.xml\n"
)


def run_main_every_sitemap() -> None:
    """WEB-18 round-2 review, 2026-09-25: the multi-sitemap fixture above only
    ever used two filenames, so a gate hardcoded to those two passed. Origin
    main publishes 8 sitemaps, one of them (blog-sitemap.xml) outside the old
    sitemap*.xml glob. Each case below puts the placeholder in exactly ONE
    file, in a shape a narrowed or brittle scan would miss."""
    def expect_caught(label: str, files: dict, culprit: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, out = _invoke_main(td, files, [LISA_REC])
        check(f"every-sitemap: {label} -> gate fails", code, 1)
        check(f"every-sitemap: {label} -> attributed to {culprit}",
              f"FAIL: {culprit}:" in out and "vermont-street" in out, True)

    big = _filler(2000)
    check("every-sitemap: the large fixture really exceeds 64 KiB",
          len(_sitemap(big + [fake]).encode()) > 65536, True)

    expect_caught("placeholder only in a third sitemap",
                  {"sitemap-listings.xml": [LISA], "sitemap.xml": _filler(3), "sitemap-faq.xml": [fake]},
                  "sitemap-faq.xml")
    expect_caught("placeholder only in the sitemap index",
                  {"sitemap.xml": _filler(3), "sitemap-index.xml": [fake]}, "sitemap-index.xml")
    expect_caught("placeholder only in blog-sitemap.xml",
                  {"sitemap.xml": _filler(3), "blog-sitemap.xml": [fake]}, "blog-sitemap.xml")
    expect_caught("placeholder only in a robots.txt-declared file without 'sitemap' in its name",
                  {"sitemap.xml": _filler(3), "listings-feed.xml": [fake], "robots.txt": ROBOTS},
                  "listings-feed.xml")
    expect_caught("placeholder at the end of a sitemap larger than 64 KiB",
                  {"sitemap.xml": big + [fake]}, "sitemap.xml")
    expect_caught("placeholder in a sitemap sharing URLs with an earlier-sorted one",
                  {"sitemap-faq.xml": _filler(50), "sitemap.xml": _filler(50) + [fake]}, "sitemap.xml")
    for form, loc in (
        ("padded <loc>", f"<loc> {fake}/ </loc>"),
        ("newline-wrapped <loc>", f"<loc>\n    {fake}/\n  </loc>"),
        ("<loc> with an attribute", f"<loc xml:space=\"preserve\">{fake}/</loc>"),
        ("<loc> with a query string", f"<loc>{fake}/?utm_source=gbp</loc>"),
    ):
        expect_caught(form, {"sitemap.xml": _raw_sitemap(*(f"<loc>{u}/</loc>" for u in _filler(3)), loc)},
                      "sitemap.xml")

    with tempfile.TemporaryDirectory() as td:
        code, out = _invoke_main(td, {
            "sitemap-listings.xml": [LISA],
            "sitemap.xml": big,
            "sitemap-faq.xml": _filler(50),
            "blog-sitemap.xml": _filler(3),
            "listings-feed.xml": _filler(3),
            "robots.txt": ROBOTS,
        }, [LISA_REC])
    check("every-sitemap: clean control (same files, no placeholder) passes", code, 0)
    check("every-sitemap: clean control scans exactly the 5 real files",
          "sitemaps scanned: 5 (" in out, True)
    check("every-sitemap: another host's Sitemap: line is ignored", "other-host" not in out, True)


def run_main_round4() -> None:
    """WEB-18 round-3 review (wf_ca82ee4b-ee5), 2026-09-25: realistic regressions and
    parsing gaps that survived the 69-check suite."""
    import gzip as _gz

    def expect(label: str, files: dict, culprit: str | None, feed=None, want_text: str | None = None) -> None:
        with tempfile.TemporaryDirectory() as td:
            code, out = _invoke_main(td, files, [LISA_REC] if feed is None else feed)
        check(f"round4: {label} -> gate fails", code, 1)
        if culprit:
            check(f"round4: {label} -> attributed to {culprit}", f"FAIL: {culprit}:" in out and "vermont-street" in out, True)
        if want_text:
            check(f"round4: {label} -> says {want_text!r}", want_text in out, True)

    base = {"sitemap.xml": _filler(3)}
    expect("Sitemap: line with an inline # comment",
           {**base, "listings-feed.xml": [fake], "robots.txt": "User-agent: *\nSitemap: https://gadurarealestate.com/listings-feed.xml # MLS feed\n"},
           "listings-feed.xml")
    expect("placeholder in the LAST of several Sitemap: lines, mixed-case key and host",
           {**base, "first-feed.xml": _filler(2), "last-feed.xml": [fake],
            "robots.txt": "User-agent: *\nSITEMAP: https://gadurarealestate.com/first-feed.xml\nsitemap: https://GADURAREALESTATE.COM/last-feed.xml\n"},
           "last-feed.xml")
    expect("Sitemap: URL with a dot segment",
           {**base, "dot-feed.xml": [fake], "robots.txt": "User-agent: *\nSitemap: https://gadurarealestate.com/x/../dot-feed.xml\n"},
           "dot-feed.xml")
    with tempfile.TemporaryDirectory() as td:
        _, out = _invoke_main(td, {**base, "dot-feed.xml": _filler(2), "robots.txt": "User-agent: *\nSitemap: https://gadurarealestate.com/x/../dot-feed.xml\n"}, [LISA_REC])
    check("round4: a dot-segment Sitemap: URL resolves like a crawler (no false 'not in the repo')", "sitemap discovery" not in out, True)
    expect("a real <sitemapindex> whose child lives in a subdirectory",
           {**base, "sitemap-index.xml": '<?xml version="1.0"?><sitemapindex><sitemap><loc>https://gadurarealestate.com/homes/listing-feed.xml</loc></sitemap></sitemapindex>',
            "homes/listing-feed.xml": [fake]},
           "listing-feed.xml")
    expect("a sitemap index listing a child that is not in the repo",
           {**base, "sitemap-index.xml": '<?xml version="1.0"?><sitemapindex><sitemap><loc>https://gadurarealestate.com/gone.xml</loc></sitemap></sitemapindex>'},
           None, want_text="sitemap discovery:")
    expect("robots.txt declaring a sitemap that is not in the repo",
           {**base, "robots.txt": "User-agent: *\nSitemap: https://gadurarealestate.com/missing-feed.xml\n"},
           None, want_text="sitemap discovery:")
    for form, loc in (("CDATA <loc>", f"<loc><![CDATA[{fake}/]]></loc>"),
                      ("namespace-prefixed <sm:loc>", f"<sm:loc>{fake}/</sm:loc>"),
                      ("uppercase host", "<loc>" + fake.replace("gadurarealestate.com", "GadurARealEstate.com") + "/</loc>"),
                      ("/index.html path", f"<loc>{fake}/index.html</loc>")):
        expect(form, {"sitemap.xml": _raw_sitemap("<loc>https://gadurarealestate.com/blog/a/</loc>", loc)}, "sitemap.xml")
    expect("root file named Sitemap-extra.xml (capital S)", {**base, "Sitemap-extra.xml": [fake]}, "Sitemap-extra.xml")
    expect("gzip sitemap declared in robots.txt",
           {**base, "sitemap-gz.xml.gz": _gz.compress(_sitemap([fake]).encode()), "robots.txt": "User-agent: *\nSitemap: https://gadurarealestate.com/sitemap-gz.xml.gz\n"},
           "sitemap-gz.xml.gz")
    expect("corrupt gzip sitemap", {**base, "sitemap-bad.xml.gz": b"not gzip"}, None, want_text="unreadable")
    for label, feed in (("missing", None), ("malformed", "{not json"), ("stale", [dict(LISA_REC, lastSync=stamp(guard.FEED_MAX_AGE_HOURS + 5))])):
        with tempfile.TemporaryDirectory() as td:
            if feed is None:
                code, out = _invoke_main(td, {"sitemap.xml": [fake]}, None)
            else:
                code, out = _invoke_main(td, {"sitemap.xml": [fake]}, feed)
        check(f"round4: {label} feed + placeholder -> main() fails closed", code, 1)
        check(f"round4: {label} feed -> reported as unusable", "feed: UNUSABLE" in out, True)


print("\n=== main() end to end (denylist + sitemap + feed on disk) ===")
run_main_end_to_end()
run_main_multi_sitemap()
run_main_every_sitemap()
run_main_round4()

print(f"\n{PASS}/{PASS + FAIL} passed")
sys.exit(1 if FAIL else 0)
