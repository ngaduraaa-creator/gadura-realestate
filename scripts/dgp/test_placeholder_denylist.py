#!/usr/bin/env python3
"""DGP-P0-XW1 deterministic safety test: FAIL if any denylisted placeholder URL
appears in any generated sitemap.

FEED-AWARE EXEMPTION (2026-09-14, reworked 2026-09-25)
-------------------------------------------------------
The denylist is frozen: it records the 92 URLs that were fabricated placeholder
listings during XW1, and it is never edited to make a build pass.

Some of those addresses have since become REAL inventory. The IDX feed now
carries active, photo-backed, MLS-identified records for them, and the generator
emits the same canonical URL it emitted when they were placeholders — because
the URL is derived from the address, not from provenance. String matching alone
therefore cannot tell "fabricated page at this address" from "real listing at
this address", and on 2026-08-22 it blocked two live listings, failing
build-pages.yml and leaving ALL real listings out of every sitemap.

This guard resolves that by asking the authoritative feed, not by editing the
denylist. A denylisted URL is permitted ONLY when the feed independently proves
the address is real inventory right now, and the evidence for that URL is
unambiguous.

2026-09-25 REWORK — do not cherry-pick the 2026-09-14 version (commit 800adf6c2).
WEB-18 independent review (2026-09-23/24, 12/12 agents, 5/5 lenses, 6/6
adversarial refuters) found that version UNSOUND, with 4 BLOCKING findings,
each with a reproduced counterexample against the live feed data. This file
fixes all four; see the docstrings on qualifying_records(), _record_qualifies(),
and the fixtures file (test_denylist_feed_aware.py) for what changed and why.
Summary:
  B1  Ambiguity was computed AFTER filtering out non-qualifying records, so a
      URL with one qualifying record and one non-qualifying record (e.g. one
      has a placeholder-only photo) was silently treated as unambiguous and
      exempted. Grouping now happens on EVERY record at a URL, before any
      quality filter runs — an address is ambiguous the moment two distinct
      feed records claim it, regardless of whether one of them would fail
      the quality bar on its own.
  B2  Staleness was judged from the newest lastSync in the WHOLE feed, so a
      record the sync had not returned in weeks could still be used as
      exemption evidence as long as some other record was fresh. Each
      record's OWN lastSync is now checked against FEED_MAX_AGE_HOURS before
      it can qualify, in addition to the existing feed-level freshness gate.

AUTHORITATIVE ARTIFACT
    data/listings.json — the IDX Broker API sync output, written by
    scripts/sync-reso.js and consumed by scripts/build-property-pages.js.
    It is the same artifact the build already trusts to generate pages.

FIELDS USED AS EVIDENCE (per record)
    address, city, state, zip   -> canonical URL (must match exactly)
    status                      -> must be an active-inventory status
    photos[]                    -> >=1 real http photo, excluding
                                   unsplash/placeholder, matching the
                                   generator's own SITEMAP-REJECT filter
    mlsNumber                   -> must be present (provenance)
    lastSync                    -> must be within FEED_MAX_AGE_HOURS of now,
                                   checked per-record, not just feed-wide

The canonical URL derivation is a faithful port of build-property-pages.js:
    normalize()  street = address.split(',')[0]
    addressSlug()  slugify([street, city, state, zip].join(' '))
    slugify()    lowercase -> [^a-z0-9]+ to '-' -> strip leading/trailing '-'
    url          BASE_URL + '/homes/' + slug + '/'
If that derivation ever drifts from the generator, this guard fails closed
(URLs stop matching, so nothing is exempted).

DENY BY DEFAULT. A denylisted URL stays blocked when the feed is missing,
unreadable, malformed, not a list, stale beyond FEED_MAX_AGE_HOURS, or when the
address does not map to EXACTLY ONE qualifying record. Two records sharing one
canonical URL (e.g. two distinct units at the same street address) is
ambiguous and is therefore denied — the guard cannot tell which listing the
page is for — even if only one of the two records would otherwise qualify.

Run: python3 scripts/dgp/test_placeholder_denylist.py   (exit 0 pass / 1 fail)
"""
from __future__ import annotations

import gzip
import posixpath
import urllib.parse
import json
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "https://gadurarealestate.com"
DENYLIST = os.path.join(ROOT, "scripts/dgp/placeholder_sitemap_denylist.txt")
FEED = os.path.join(ROOT, "data/listings.json")

# sync-listings.yml runs on cron '0 */4 * * *'. 24h tolerates five consecutive
# missed syncs before the feed -- or an individual record within it -- is
# treated as unreliable evidence.
FEED_MAX_AGE_HOURS = 24

# Statuses that represent live inventory. Anything else (Sold, Closed,
# Withdrawn, Expired, Cancelled, or unrecognised) does not qualify.
ACTIVE_STATUSES = {"active", "pending", "coming soon", "active under contract"}

PLACEHOLDER_MEDIA = re.compile(r"unsplash|placeholder", re.IGNORECASE)

# A <loc> may carry a namespace prefix, attributes, CDATA, or pad/wrap its URL in whitespace.
LOC_RE = re.compile(r"<(?:[\w-]+:)?loc\b[^>]*>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</(?:[\w-]+:)?loc>")
SITE_HOSTS = {"gadurarealestate.com", "www.gadurarealestate.com"}
SITEMAP_NAME = re.compile(r"sitemap.*\.xml(\.gz)?$", re.I)


def _local_path(url: str) -> str | None:
    """Map a same-site URL to a repo path the way a crawler would fetch it
    (case-insensitive host, dot segments removed). None if not this site."""
    parts = urllib.parse.urlsplit(url.strip())
    if parts.scheme.lower() not in ("http", "https") or parts.netloc.lower() not in SITE_HOSTS:
        return None
    path = posixpath.normpath("/" + parts.path.lstrip("/"))
    return os.path.join(ROOT, path.lstrip("/"))


def read_sitemap(path: str) -> str:
    raw = open(path, "rb").read()
    if path.lower().endswith(".gz"):
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


def sitemap_files() -> tuple[list[str], list[str]]:
    """Every sitemap the site publishes, and any problem found discovering them.

    Sources: any root file named *sitemap*.xml[.gz] (case-insensitive); every
    Sitemap: line in robots.txt for this site; every child listed in a
    <sitemapindex>, followed recursively. A declared or indexed sitemap that is
    missing, outside the repo, or unreadable is a problem -- the gate cannot
    vouch for what it cannot read, so it fails rather than skipping."""
    root_real = os.path.realpath(ROOT)
    problems: list[str] = []
    queue = [os.path.join(ROOT, f) for f in sorted(os.listdir(ROOT)) if SITEMAP_NAME.search(f)]
    robots = os.path.join(ROOT, "robots.txt")
    if os.path.exists(robots):
        for line in open(robots, encoding="utf-8"):
            key, _, val = line.split("#", 1)[0].partition(":")
            if key.strip().lower() != "sitemap":
                continue
            local = _local_path(val)
            if local is None:
                continue
            if not os.path.isfile(local):
                problems.append(f"robots.txt declares {val.strip()} but it is not in the repo")
            queue.append(local)
    found: set[str] = set()
    while queue:
        path = os.path.realpath(queue.pop(0))
        if path in found or not os.path.isfile(path):
            continue
        if not path.startswith(root_real + os.sep):
            problems.append(f"sitemap outside the repo: {path}"); continue
        found.add(path)
        try:
            text = read_sitemap(path)
        except (OSError, UnicodeDecodeError, EOFError) as exc:
            problems.append(f"{os.path.basename(path)}: unreadable ({type(exc).__name__})"); continue
        if re.search(r"<(?:[\w-]+:)?sitemapindex\b", text):
            for u in LOC_RE.findall(text):
                child = _local_path(u)
                if child is None:
                    continue
                if not os.path.isfile(child):
                    problems.append(f"{os.path.basename(path)} lists {u} but it is not in the repo")
                queue.append(child)
    return sorted(found), problems


def slugify(value: str) -> str:
    """Port of slugify() in build-property-pages.js."""
    s = str(value or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"^-+|-+$", "", s)


def canonical_url(raw: dict) -> str:
    """Port of normalize() + addressSlug() in build-property-pages.js."""
    addr = (raw.get("address") or "").strip()
    street = addr.split(",")[0].strip() or addr
    city = (raw.get("city") or raw.get("neighborhood") or "").strip()
    state = re.sub(r"^,|,$", "", str(raw.get("state") or "NY")).strip() or "NY"
    zipc = (raw.get("zip") or raw.get("postalCode") or "").strip()
    slug = slugify(" ".join(p for p in (street, city, state, zipc) if p))
    return f"{BASE_URL}/homes/{slug}/"


def normalize_url(url: str) -> str:
    """Compare on scheme+host+path only: drop query, fragment, trailing slash.

    Case is preserved on the path deliberately. Generated slugs are always
    lowercase, so an upper/mixed-case variant is NOT the same resource as far
    as this guard is concerned and must not inherit an exemption.
    """
    u = str(url or "").strip()
    u = u.split("#", 1)[0].split("?", 1)[0]
    m = re.match(r"(?i)^(https?://[^/]+)(.*)$", u)
    if m:
        u = m.group(1).lower() + m.group(2)
    if u.endswith("/index.html"):
        u = u[: -len("index.html")]
    return u.rstrip("/")


def _parse_timestamp(raw: str) -> dt.datetime | None:
    """Parse an ISO-8601 lastSync stamp to an aware UTC datetime, or None."""
    raw = str(raw or "").strip()
    if not raw:
        return None
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _age_hours(stamp: dt.datetime) -> float:
    return (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds() / 3600.0


def _record_age_hours(raw: dict) -> float | None:
    """This record's own lastSync age in hours, or None if unstamped/unparseable."""
    parsed = _parse_timestamp(raw.get("lastSync"))
    return _age_hours(parsed) if parsed is not None else None


def _record_qualifies(raw: dict) -> bool:
    """Does this ONE record, on its own, count as live, current inventory?

    All four evidence requirements are checked here, including the record's
    own freshness (WEB-18 finding B2, 2026-09-25 fix): a record whose own
    lastSync is older than FEED_MAX_AGE_HOURS cannot qualify even when other
    records in the same feed pull are fresh. sync-reso.js carries forward
    every previously-seen record indefinitely with its old lastSync and old
    status, so stale-but-still-listed records are the steady state, not an
    edge case -- roughly half of today's feed is >7 days stale.
    """
    status = str(raw.get("status") or "").strip().lower()
    if status not in ACTIVE_STATUSES:
        return False
    if not str(raw.get("mlsNumber") or "").strip():
        return False
    age = _record_age_hours(raw)
    if age is None or age > FEED_MAX_AGE_HOURS:
        return False
    photos = [
        p for p in (raw.get("photos") or [])
        if isinstance(p, str) and p.startswith("http")
        and not PLACEHOLDER_MEDIA.search(p)
    ]
    return bool(photos)


def qualifying_records(feed: list) -> tuple[dict, list[str], set[str]]:
    """Map canonical URL -> [the one qualifying record], for URLs that have
    exactly one feed record AND that record qualifies. Also returns the
    ambiguity notes and the set of URLs denied specifically for ambiguity
    (as opposed to simply having no qualifying record), for a clearer FAIL
    message in main().

    Grouping-before-filtering (WEB-18 finding B1, 2026-09-25 fix): every
    record is grouped by its canonical URL FIRST, with no quality filter
    applied yet. Two DISTINCT records claiming one URL is ambiguous and is
    denied regardless of whether one of them would individually qualify --
    filtering the weak one out before grouping used to make the ambiguity
    invisible. This is what silently exempted the live MLS 999236/986483
    collision: 999236's only photo is a local placeholder path, so the old
    code dropped it before the two records were ever compared, leaving
    986483 looking like the sole, unambiguous claimant of that URL.
    """
    by_url: dict[str, list[dict]] = {}
    for raw in feed:
        if not isinstance(raw, dict):
            continue
        by_url.setdefault(normalize_url(canonical_url(raw)), []).append(raw)

    result: dict[str, list[dict]] = {}
    notes: list[str] = []
    ambiguous_urls: set[str] = set()
    for url, recs in by_url.items():
        if len(recs) > 1:
            mls = ", ".join(str(r.get("mlsNumber")) for r in recs)
            notes.append(f"ambiguous: {len(recs)} records map to {url} (MLS {mls})")
            ambiguous_urls.add(url)
            continue
        if _record_qualifies(recs[0]):
            result[url] = recs
    return result, notes, ambiguous_urls


def feed_age_hours(data: list) -> float | None:
    """Hours since the newest per-record lastSync stamp, or None if absent.

    This is the FEED-LEVEL freshness gate: is the sync pipeline itself still
    running at all? It is deliberately separate from the PER-RECORD check in
    _record_qualifies() -- a feed can be actively syncing (this check passes)
    while a specific record hasn't been returned by IDX in weeks (that
    record still fails on its own).

    Freshness is read from the DATA, not the file's mtime. mtime is unusable
    here for two independent reasons:
      * locally, it records when git last wrote the file, not when the feed
        synced — a branch that has not pulled shows a stale mtime on current
        data, and vice versa;
      * in CI, actions/checkout stamps every file with the checkout time, so
        mtime would report a months-dead feed as fresh.
    lastSync is written by scripts/sync-reso.js:497 at sync time and travels
    with the record, so it means the same thing in both places.
    """
    stamps = [_parse_timestamp(r.get("lastSync")) for r in data if isinstance(r, dict)]
    stamps = [s for s in stamps if s is not None]
    if not stamps:
        return None
    return _age_hours(max(stamps))


def load_feed(path: str = FEED) -> tuple[list | None, str]:
    """Return (records, reason_if_unusable). Deny-by-default on any problem."""
    if not os.path.exists(path):
        return None, "feed artifact missing"
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        return None, f"feed malformed ({type(exc).__name__})"
    if not isinstance(data, list):
        return None, "feed is not a list"
    age_h = feed_age_hours(data)
    if age_h is None:
        return None, "feed carries no usable lastSync stamp"
    if age_h > FEED_MAX_AGE_HOURS:
        return None, f"feed stale ({age_h:.1f}h > {FEED_MAX_AGE_HOURS}h since last sync)"
    return data, ""


def main() -> int:
    deny = {
        normalize_url(l) for l in open(DENYLIST, encoding="utf-8")
        if l.strip() and not l.lstrip().startswith("#")
    }

    # Read the module-global FEED at call time, not via load_feed()'s default
    # parameter (which binds FEED once, at def time, and would then ignore a
    # test monkeypatch of the module global -- see run_main_end_to_end() in
    # test_denylist_feed_aware.py).
    feed, feed_problem = load_feed(FEED)
    if feed is None:
        by_url, ambiguity_notes, ambiguous_urls = {}, [], set()
    else:
        by_url, ambiguity_notes, ambiguous_urls = qualifying_records(feed)

    bad: list[str] = []
    exempted: list[str] = []

    sitemaps, discovery_problems = sitemap_files()
    bad.extend(f"sitemap discovery: {p}" for p in discovery_problems)
    for sm in sitemaps:
        try:
            locs = {normalize_url(u) for u in LOC_RE.findall(read_sitemap(sm))}
        except (OSError, UnicodeDecodeError, EOFError):
            continue  # already reported by sitemap_files()
        for hit in sorted(deny & locs):
            recs = by_url.get(hit, [])
            if len(recs) == 1:
                exempted.append(f"{os.path.basename(sm)}: {hit}  (MLS {recs[0].get('mlsNumber')})")
            else:
                if feed is None:
                    why = feed_problem
                elif hit in ambiguous_urls:
                    why = "2+ feed records map to this URL — ambiguous, denied regardless of individual record quality"
                else:
                    why = "no active, current, photo-backed, MLS-identified feed record"
                bad.append(f"{os.path.basename(sm)}: {hit}  <- {why}")

    print("=== placeholder denylist gate (feed-aware, reworked 2026-09-25) ===")
    print(f"denylist entries: {len(deny)}")
    print(f"sitemaps scanned: {len(sitemaps)} ({', '.join(os.path.basename(s) for s in sitemaps)})")
    if feed is None:
        print(f"feed: UNUSABLE — {feed_problem}; all denylisted URLs denied")
    else:
        print(f"feed: {len(feed)} records, {len(by_url)} qualifying canonical URL(s)")
        for n in ambiguity_notes:
            print(f"  note: {n}")
    for e in exempted:
        print("EXEMPT:", e)
    for b in bad:
        print("FAIL:", b)
    if bad:
        print(f"{len(bad)} violation(s)")
    else:
        print(f"PASS: 0 of {len(deny)} denylisted URLs unjustified in sitemaps"
              f"{f' ({len(exempted)} feed-backed exemption(s))' if exempted else ''}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
