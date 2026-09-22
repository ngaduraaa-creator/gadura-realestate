#!/usr/bin/env python3
"""DGP-P0-XW1 deterministic safety test: FAIL if any denylisted placeholder URL
appears in any generated sitemap.

FEED-AWARE EXEMPTION (2026-09-14)
---------------------------------
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
the address is real inventory right now.

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
canonical URL (e.g. two rental units at the same street address) is ambiguous
and is therefore denied — the guard cannot tell which listing the page is for.

Run: python3 scripts/dgp/test_placeholder_denylist.py   (exit 0 pass / 1 fail)
"""
from __future__ import annotations

import glob
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
# missed syncs before the feed is treated as unreliable evidence.
FEED_MAX_AGE_HOURS = 24

# Statuses that represent live inventory. Anything else (Sold, Closed,
# Withdrawn, Expired, Cancelled, or unrecognised) does not qualify.
ACTIVE_STATUSES = {"active", "pending", "coming soon", "active under contract"}

PLACEHOLDER_MEDIA = re.compile(r"unsplash|placeholder", re.IGNORECASE)


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
    return u.rstrip("/")


def qualifying_records(feed: list) -> tuple[dict, list[str]]:
    """Map canonical URL -> list of records that qualify as live inventory."""
    by_url: dict[str, list[dict]] = {}
    notes: list[str] = []
    for raw in feed:
        if not isinstance(raw, dict):
            continue
        status = str(raw.get("status") or "").strip().lower()
        if status not in ACTIVE_STATUSES:
            continue
        if not str(raw.get("mlsNumber") or "").strip():
            continue
        photos = [
            p for p in (raw.get("photos") or [])
            if isinstance(p, str) and p.startswith("http")
            and not PLACEHOLDER_MEDIA.search(p)
        ]
        if not photos:
            continue
        by_url.setdefault(normalize_url(canonical_url(raw)), []).append(raw)
    for url, recs in by_url.items():
        if len(recs) > 1:
            mls = ", ".join(str(r.get("mlsNumber")) for r in recs)
            notes.append(f"ambiguous: {len(recs)} records map to {url} (MLS {mls})")
    return by_url, notes


def feed_age_hours(data: list) -> float | None:
    """Hours since the newest per-record lastSync stamp, or None if absent.

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
    stamps = []
    for r in data:
        if not isinstance(r, dict):
            continue
        raw = str(r.get("lastSync") or "").strip()
        if not raw:
            continue
        try:
            iso = raw.replace("Z", "+00:00")
            stamps.append(dt.datetime.fromisoformat(iso))
        except ValueError:
            continue
    if not stamps:
        return None
    newest = max(stamps)
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - newest).total_seconds() / 3600.0


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

    feed, feed_problem = load_feed()
    by_url, ambiguity_notes = ({}, []) if feed is None else qualifying_records(feed)

    bad: list[str] = []
    exempted: list[str] = []

    for sm in sorted(glob.glob(os.path.join(ROOT, "sitemap*.xml"))):
        locs = {
            normalize_url(u)
            for u in re.findall(r"<loc>(.*?)</loc>", open(sm, encoding="utf-8").read())
        }
        for hit in sorted(deny & locs):
            recs = by_url.get(hit, [])
            if len(recs) == 1:
                exempted.append(f"{os.path.basename(sm)}: {hit}  (MLS {recs[0].get('mlsNumber')})")
            else:
                if feed is None:
                    why = feed_problem
                elif len(recs) > 1:
                    why = f"{len(recs)} feed records map to this URL — ambiguous"
                else:
                    why = "no active, photo-backed, MLS-identified feed record"
                bad.append(f"{os.path.basename(sm)}: {hit}  <- {why}")

    print("=== placeholder denylist gate (feed-aware) ===")
    print(f"denylist entries: {len(deny)}")
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
