#!/usr/bin/env python3
"""check_listing_truth.py -- fail-closed check that every listing the site shows agrees with data/listings.json.

Usage:  python3 scripts/check_listing_truth.py [--root DIR] [--now ISO8601Z] [--report PREFIX] [--freshness-csv FILE]
                                              [--surfaces-csv FILE]
Exit:   0 = PASS, 1 = violations found, 2 = cannot run (feed missing, unreadable, empty or of unknown shape,
        or --now malformed).
        --now fixes the check time (default: the current UTC time). Freshness only ever decays with time, so a
          later check time can only turn a fresh record stale, never the reverse.
        --report PREFIX also writes PREFIX_cards.csv, PREFIX_counts.csv and PREFIX_exclusions.csv.
        --freshness-csv FILE writes one row per feed record: MLS number (no address), decision, the lastSync used,
          age in days, rule. Write it outside the repository (everything committed is published).

The feed (data/listings.json) is the only source of truth used. Nothing is fetched. No git commit time, file
time or feed-level time is used: a record is confirmed only by its OWN lastSync.

FRESHNESS (same rule as scripts/build-property-pages.js)
  lastSync must be ISO-8601 UTC as sync-reso.js writes it (YYYY-MM-DDTHH:MM:SS[.mmm]Z) and a real calendar time;
  missing, malformed or later than the check time -> FEED_LASTSYNC_INVALID (a future lastSync never counts as fresh).
  fresh  <=> 0 <= check time - the record's own lastSync <= 7 days.
  A fresh Active/Pending record must have its page (else MISSING_PAGE_FRESH_RECORD: a generator failure).
  A stale record without a page is an INTENTIONAL omission (recorded in the freshness rows, not a violation).
  Two records sharing a slug: the page shows the record with the newest own lastSync; tie -> larger MLS number.

LISTING CONTEXT (where the wording and count rules apply)
  L1 generated pages homes/<slug>/index.html (whole page, minus feed remarks <p class="desc">);
  L2 hand-written pages under homes-for-sale/ that show a listing card, a listing link or the neutral
     sentence (whole page incl. <title> and description/og/twitter meta);
  L3 portal.html (whole page);
  L4 the "Properties in" aside of any other page that shows listing cards (the aside only).
  In every context <script>, <style>, <nav>, <footer>, a <header> that holds a <nav> or is role="banner", and
  breadcrumb markup are not visible copy and are skipped (navigation labels such as "Homes For Sale" or "Our
  Listings" name a site section, not a record). A section <header> (for example portal.html's) is copy.

LINKS (every tracked text file outside homes/, data/, scripts/, .github/, audit_exports/, reports/,
  node_modules/; generated pages are checked the same way in their own rule below)
  Every occurrence of "homes/" that starts a URL token is resolved: absolute (http://, https://, any letter case,
  with or without www.), protocol-relative (//host/...), root-relative (/homes/...), dot-relative (./, ../, resolved
  against the file's own directory) and bare relative ("homes/..." inside a quoted or unquoted attribute value or a
  quoted string; resolved against the file's directory in HTML, against the site root in other files). Attribute
  values may be double-quoted, single-quoted or unquoted; HTML entities in the token are decoded. A token that
  resolves on this site to /homes/<slug>/, /homes/<slug> or /homes/<slug>/index.html (query and fragment ignored)
  is a listing link. It must be a recognised card (dir-card, bp-card, a "Properties in" aside item; exact form
  href="/homes/<slug>/"), an entry of the all-listings ItemList (exact form https://gadurarealestate.com/homes/
  <slug>/, checked against the cards) or a sitemap-listings.xml <loc> (checked below). Anything else ->
  UNRECOGNISED_LISTING_LINK (the message names the form and whether the target page exists).
  NOT recognised (documented limits): links assembled at run time by script (string concatenation, templates),
  percent-encoded or entity-encoded slashes (%2F, &#47;), a <base href> that changes resolution, redirects,
  links inside images/PDFs or untracked files, and anything under the skipped directories. scripts/ is tooling
  and config (for example the broker sitemap denylist); it displays nothing and is excluded.

FRESHNESS ON EVERY SURFACE
  Every hand-written card, every "More ..." card on a generated page and every generated page is judged by the
  OWN lastSync of the record it shows (never the card's printed date, another record, a file or commit time).
  Stale record (more than 7 days before the check time): the surface must show "Not confirmed by the listing
  feed since <Mon D, YYYY>" with that record's lastSync date (STALE_CARD_UNMARKED / STALE_MARK_DATE); the card
  keeps the feed status text. A generated page shows that line right after the price (STALE_LINE_POSITION), in
  its meta description, and carries no schema.org availability. Fresh record: the line must not appear
  (STALE_MARK_ON_FRESH). A hand-written page that shows listings must carry no schema.org availability at all
  (HANDWRITTEN_SCHEMA_AVAILABILITY): it cannot follow the feed. A JS-rendered portal entry cannot show the line,
  so a portal featured/area entry for a stale record is a violation (STALE_PORTAL_ENTRY).
  --surfaces-csv FILE writes one row per surface (page, surface, slug, MLS number, the lastSync used, age,
  decision, the marker shown); it contains slugs (= street addresses): write it outside the repository.

Hand-written cards:
  - the slug must belong to a feed record with status Active or Pending, and homes/<slug>/index.html must exist;
  - a lease record (propType containing "lease" or "rent") must not appear in a sale context
    (homes-for-sale/*, our-listings/*), and anywhere else its card must say "For lease";
  - the card must show the feed price, "Status: <feed status>", and an "IDX feed as of <date>" date that is not
    later than the record's lastSync date; any type, beds, baths or sqft it shows must equal the feed; it must
    not show baths or sqft the feed does not have; it must not carry an <img>; it must not say
    "Photos on listing page" (no page displays IDX photos until the broker confirms display rights);
  - a price-bracket page may only show records whose feed price is inside the bracket;
  - count statements must say what they count and equal the cards shown (COUNT_LABEL / COUNT_MISMATCH):
    all-listings "Listings shown on this page: N", jump list "<City> (N shown)", ItemList numberOfItems;
    bracket stat "Listings shown on this page: N"; the neutral sentence; portal counters and the portal label
    "Featured listings shown on this page". Inventory labels ("N Homes in range", "N Active Listings") fail.
Wording (listing context only):
  W1 AVAILABILITY_CLAIM   "available now", "now available", "currently available", "still available", "just
                          listed", "newly listed", "new listing(s)", "new to (the) market", "coming soon", "hot
                          listing(s)" -- the feed has no list date and freshness is per record.
  W2 FOR_SALE_ON_NONSALE  "for sale" attached to a Pending or lease record: in its card, on its own generated page
                          (outside navigation), or in the all-listings city heading over a section that holds a
                          card that is not an Active sale record.
  W3 COMPLETENESS_CLAIM   "every/all (of) (the) (our) active|current|available|live listing(s)/home(s)/
                          propert(y|ies)", "every listing", "all (of) our homes/listings/properties", "every home
                          we ..." / "every home for sale": the site shows only records with a page (the 7-day
                          rule omits some). Excluded by rule: the page names "All Listings" / "All Homes for Sale"
                          (no qualifier).
  W4 OWNERSHIP_CLAIM      "our (featured |exclusive )?listings", "our inventory", "our (current|active|available|
                          live) listings/homes/properties", "our (current )?homes for sale", "Gadura (Real
                          Estate)('s) listings / homes for sale / properties", "listed (directly )?by Gadura",
                          "represented by Gadura", "exclusive properties|listings", "homes we represent" -- a
                          violation unless a card on the page shows a record whose isOurListing is true.
  W5 UNRECONCILED_COUNT   "<number> [up to two words] home(s)|listing(s)|propert(y|ies)|house(s)|unit(s)|condo(s)|
                          co-op(s)|apartment(s)|residence(s)|rental(s)|townhome(s)|townhouse(s)" outside the
                          recognised count elements. <number> = digits (with "+"), one..twenty, thirty..ninety
                          (with -one..-nine), dozen(s), hundred(s), thousand(s) ("a dozen homes", "dozens of
                          listings", "fifteen listings", "100+ homes"). Excluded by rule (and listed in the
                          exclusions report):
                          E-C1 number RANGES ("8-15 Active Listings": market-inventory statistics that need a source or
                          removal, which this check does not decide),
                          E-C2 4-digit years, E-C3 phone numbers and prices (removed before matching),
                          E-R1 feed remarks on generated pages (shown verbatim from the IDX record).
  NOT recognised (documented limits): vague quantifiers without a number ("several", "many", "a few",
  "numerous"), numbers written as numerals of other scripts, counts split across two elements, synonyms not
  listed above (for example "fresh on the market", "full, real-time results"), and copy outside listing context.
  Pages that show no feed record (for example the neighbourhood guides under homes-for-sale/ with market statistics,
  buy.html and map-available.html, which render nothing from a flat feed) are outside listing context; their
  wording needs a separate claims review. The feed-shape tripwire below guards the two JS pages.
Generated pages (homes/<slug>/index.html):
  - each must belong to a feed record (no orphan pages); the record the page shows (MLS #) must be the one the
    generator selects; status, price, type, Offered and og:title wording must match the feed AND the record's
    freshness; JSON-LD offers carry the feed price, InStock only for a FRESH Active record, LeaseOut for a lease;
  - a stale record's page must carry the "not confirmed" notice and line; a fresh record's page must not;
  - no feed photo URL may appear (gallery, og:image, JSON-LD image, card backgrounds): IDX photo display rights
    are unconfirmed (awaiting the broker's confirmation);
  - each "More ... in" card must point to an existing page of the same kind and show its status and price;
  - listing links on the page may only be those cards and the page's own absolute URL (canonical, og:url,
    JSON-LD).
sitemap-listings.xml: every <loc> must be a generated page of a fresh record with an MLS number, real feed photo
  provenance and no broker denylist entry; no <lastmod> after the check time.
Feed-shape tripwire: buy.html, map-available.html and portal.html read the bucketed feed shape. If the feed
  ever carries those keys, this check fails (FEED_SHAPE), because it cannot verify what those scripts render.
"""
import argparse, csv, datetime, html, json, os, posixpath, re, subprocess, sys

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LISTABLE = ("Active", "Pending")
BUCKET_KEYS = ("activeListings", "areaListings", "woodhavenListings", "queensListings", "brooklynListings",
               "longIslandListings", "soldListings")
SALE_CONTEXT_PREFIXES = ("homes-for-sale/", "our-listings/")
NEUTRAL = "No current listings are shown on this page."
STALE_DAYS = 7
DAY_S = 86400
ISO_UTC = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d{1,3})?Z$")
SITE_HOSTS = ("gadurarealestate.com", "www.gadurarealestate.com")
CANON_ABS = "https://gadurarealestate.com/homes/%s/"
URL_STOP = set(" \t\r\n\"'<>()=`\\,;{}|^[]")      # characters that end a URL token
LINK_TRAIL = ".,;:!?"                                   # sentence punctuation stripped from a token's end
STALE_MARK = re.compile(r"(?i)not confirmed by the listing feed since ([A-Z][a-z]{2} \d{1,2}, \d{4})")
TEXT_EXT = (".html", ".htm", ".js", ".mjs", ".json", ".xml", ".txt", ".md", ".csv", ".webmanifest", ".svg")
LINK_SKIP_PREFIXES = ("homes/", "data/", "scripts/", ".github/", "audit_exports/", "reports/", "node_modules/")
NOT_CONFIRMED = "has not returned this listing since then"

W1 = re.compile(r"(?i)\b(available now|now available|currently available|still available|just listed|newly listed|"
                r"new listings?|new to (?:the )?market|coming soon|hot listings?)\b")
W3 = re.compile(r"(?i)\b((?:every|all)\s+(?:of\s+)?(?:the\s+)?(?:our\s+)?(?:active|current|available|live)\s+"
                r"(?:listings?|homes?|propert(?:y|ies))|every\s+listing|all\s+(?:of\s+)?our\s+(?:homes?|listings?|"
                r"propert(?:y|ies))|every\s+(?:home|property)\s+(?:we\b|for\s+sale))")
W4 = re.compile(r"(?i)\b(our\s+(?:featured\s+|exclusive\s+)?listings?|our\s+inventory|"
                r"our\s+(?:current|active|available|live)\s+(?:listings?|homes|properties)|"
                r"our\s+(?:current\s+)?homes\s+for\s+sale|"
                r"gadura(?:\s+real\s+estate)?(?:'s|\u2019s)?\s+(?:listings\b|homes\s+for\s+sale|properties)|"
                r"listed\s+(?:directly\s+)?by\s+gadura|"
                r"represented\s+by\s+gadura|exclusive\s+(?:properties|listings)|homes\s+we\s+represent)\b")
_UNITS = "one|two|three|four|five|six|seven|eight|nine"
NUMW = (r"(?:\d[\d,]*|(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:-(?:%s))?|%s|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|dozens?|hundreds?|thousands?)" % (_UNITS, _UNITS))
W5 = re.compile(r"(?i)(?<![\w$.,()/-])(%s)(\s*[-\u2013\u2014]\s*%s|\s+to\s+%s)?\+?\s+(?:[A-Za-z][A-Za-z-]*\s+){0,2}?"
                r"(homes?|listings?|propert(?:y|ies)|houses?|units?|condos?|co-?ops?|apartments?|residences?|rentals?|"
                r"townhomes?|townhouses?)\b" % (NUMW, NUMW, NUMW))


def slugify(s):
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()))


def street_of(addr):
    a = (addr or "").strip()
    return a.split(",")[0].strip() or a


def address_slug(r):
    parts = [street_of(r.get("address")), (r.get("city") or "").strip(),
             (r.get("state") or "NY").strip(",").strip() or "NY", (r.get("zip") or "").strip()]
    return slugify(" ".join(p for p in parts if p))


def kind_of(r):
    return "lease" if re.search(r"lease|rent", r.get("propType") or "", re.I) else "sale"


def money(n):
    return "${:,}".format(int(n))


def parse_iso_utc(v):
    """Strict ISO-8601 UTC -> aware datetime, or None (missing, malformed, or not a real calendar time)."""
    if not isinstance(v, str):
        return None
    m = ISO_UTC.match(v)
    if not m:
        return None
    try:
        frac = m.group(7) or ""
        us = int((frac[1:] + "000000")[:6]) if frac else 0
        return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)),
                                 int(m.group(5)), int(m.group(6)), us, tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def freshness(r, now):
    """(fresh, age_days, rule) from the record's OWN lastSync only."""
    raw = r.get("lastSync")
    if raw in (None, ""):
        return False, None, "LASTSYNC_MISSING"
    t = parse_iso_utc(raw)
    if t is None:
        return False, None, "LASTSYNC_MALFORMED"
    age = (now - t).total_seconds()
    if age < 0:
        return False, None, "LASTSYNC_FUTURE"
    return (age <= STALE_DAYS * DAY_S), int(age // DAY_S), ("FRESH_LE_7D" if age <= STALE_DAYS * DAY_S else "STALE_GT_7D")


def feed_date(r):
    """The record's lastSync calendar date (UTC), e.g. 'Oct 19, 2026'."""
    d = datetime.date.fromisoformat(str(r["lastSync"])[:10])
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def parse_shown_date(s):
    m = re.match(r"([A-Z][a-z]{2}) (\d{1,2}), (\d{4})$", s.strip())
    if not m or m.group(1) not in MONTHS:
        return None
    try:
        return datetime.date(int(m.group(3)), MONTHS.index(m.group(1)) + 1, int(m.group(2)))
    except ValueError:
        return None


def addr_key(street):
    """(house number digits, first street token) -- '12-34 56th St' and '1234 56th Street' agree."""
    m = re.match(r"\s*([\d-]+)\s+(\S+)", street or "")
    return (re.sub(r"\D", "", m.group(1)), m.group(2).lower()) if m else None


def text_of(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def listing_links(f, s):
    """Every URL token in s that resolves to a listing page on this site: list of dicts
    (pos = index of the slug in s, slug, form, token). See LINKS in the module docstring.
    JSON-escaped slashes ("\\/homes\\/x\\/") are found by a second pass (pos -1: never a card)."""
    out = _listing_links(f, s)
    if "\\/" in s:
        seen = {(o["slug"], o["token"].replace("\\/", "/")) for o in out}
        for o in _listing_links(f, s.replace("\\/", "/")):
            if (o["slug"], o["token"]) not in seen:
                out.append(dict(o, pos=-1, form=o["form"] + " (JSON-escaped)"))
    return out


def _listing_links(f, s):
    out = []
    is_html = f.lower().endswith((".html", ".htm"))
    fdir = posixpath.dirname(f)
    for m in re.finditer(r"(?i)homes/", s):
        i = m.start()
        before = s[i - 1] if i > 0 else " "
        if before != "/" and before not in URL_STOP:
            continue                                   # e.g. "new-homes/": another path segment
        a = i
        while a > 0 and s[a - 1] not in URL_STOP:
            a -= 1
        b = m.end()
        while b < len(s) and s[b] not in URL_STOP:
            b += 1
        tok = s[a:b].rstrip(LINK_TRAIL)
        t = html.unescape(tok)
        cut = [k for k, ch in enumerate(t) if ch in URL_STOP]
        t = (t[:cut[0]] if cut else t).rstrip(LINK_TRAIL)
        lead = s[a - 1] if a > 0 else " "
        am = re.match(r"(?i)^(?:(https?):)?//([^/?#]*)(.*)$", t)
        if am:
            host = am.group(2).lower().rsplit("@", 1)[-1].split(":")[0]
            if host not in SITE_HOSTS:
                continue
            path, form = am.group(3), ("absolute" if am.group(1) else "protocol-relative")
        elif re.match(r"(?i)^[a-z][a-z0-9+.-]*:", t):
            continue                                   # mailto:, javascript:, data: ...
        elif t.startswith("/"):
            path, form = t, "root-relative"
        else:
            if not t.startswith(("./", "../")) and lead not in "\"'=`":
                continue                               # bare "homes/x" in prose is not a link
            if is_html:
                path, form = posixpath.join("/" + fdir, t), "relative"
            else:
                path, form = "/" + re.sub(r"^(?:\./|\.\./)+", "", t), "relative (resolved from the site root)"
        path = re.split(r"[?#]", path, maxsplit=1)[0]
        norm = posixpath.normpath(path) if path else ""
        lm = re.match(r"(?i)^/homes/([^/.]+)(/index\.html?)?$", norm)
        if not lm:
            continue
        if lm.group(2):
            form += " /index.html"
        out.append(dict(pos=m.end(), slug=lm.group(1), form=form, token=tok))
    return out


def real_photos(r):
    return [p for p in (r.get("photos") or []) if isinstance(p, str) and p.startswith("http")
            and not re.search(r"unsplash|placeholder", p, re.I)]


def visible_copy(s, drop_desc=False):
    """Visible copy of a page for the wording rules: meta copy + body text, without script/style/nav/header/
    footer/breadcrumb markup (and without feed remarks when drop_desc)."""
    meta = []
    t = re.search(r"(?is)<title>(.*?)</title>", s)
    if t:
        meta.append(t.group(1))
    for m in re.finditer(r'(?is)<meta\s+(?:name|property)="(description|og:title|og:description|twitter:title|'
                         r'twitter:description)"\s+content="([^"]*)"', s):
        meta.append(m.group(2))
    b = re.sub(r"(?is)<head\b.*?</head>", " ", s)
    b = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", b)
    # site chrome only: a <header> that holds navigation or is the banner (a section header is copy), every
    # <footer>, and every <nav>
    b = re.sub(r"(?is)<header\b.*?</header>", lambda m: " " if re.search(r'(?i)<nav\b|role="banner"', m.group(0)) else m.group(0), b)
    b = re.sub(r"(?is)<(nav|footer)\b.*?</\1>", " ", b)
    b = re.sub(r'(?is)<[a-z]+[^>]*class="[^"]*\b(?:crumb|breadcrumbs?)\b[^"]*"[^>]*>.*?</(?:div|ol|ul|p)>', " ", b)
    if drop_desc:
        b = re.sub(r'(?is)<p class="desc">.*?</p>', " ", b)
    # block-level boundaries become a pilcrow so that no phrase rule matches across two elements
    b = re.sub(r"(?i)</?(?:div|p|h[1-6]|li|ul|ol|dl|dt|dd|section|article|aside|main|table|tr|td|th|br|hr|form|"
               r"label|button|select|option)\b[^>]*>", " \u00b6 ", b)
    return text_of(" \u00b6 ".join(meta) + " \u00b6 " + b)


class Checker:
    def __init__(self, root, now):
        self.root = root
        self.now = now
        self.violations = []
        self.cards = []
        self.counts = []
        self.exclusions = []
        self.fresh_rows = []
        self.itemlist_urls = {}
        self.surfaces = []
        self.card_pos = {}          # file -> set of slug positions of recognised cards
        self._links = {}

    def links_in(self, f, s):
        if f not in self._links:
            self._links[f] = listing_links(f, s)
        return self._links[f]

    def surface(self, page, kind, slug, r, marker, extra=""):
        fresh, age, rule = self.fresh[id(r)] if r is not None else (None, "", "NO_FEED_RECORD")
        self.surfaces.append(dict(page=page, surface=kind, slug=slug, mls=r["mlsNumber"] if r else "",
                                  feed_status=r["status"] if r else "", last_sync_used=r["lastSync"] if r else "",
                                  basis="own lastSync of the record shown", age_days=age, rule=rule,
                                  decision=("" if r is None else "FRESH_NO_MARK" if fresh else "STALE_MARK_REQUIRED"),
                                  marker_shown=marker or "", note=extra))

    def stale_rules(self, page, kind, slug, r, text):
        """Stale record -> 'Not confirmed by the listing feed since <its lastSync date>'; fresh -> no such line."""
        mk = STALE_MARK.search(text)
        if r is None:
            return mk
        if not self.is_fresh(r):
            if not mk:
                self.v(page, "STALE_CARD_UNMARKED", "%s for /homes/%s/ shows a record unconfirmed for %s days without "
                       "'Not confirmed by the listing feed since %s'" % (kind, slug, self.fresh[id(r)][1], feed_date(r)))
            elif mk.group(1) != feed_date(r):
                self.v(page, "STALE_MARK_DATE", "%s for /homes/%s/ says not confirmed since %s; the record's own lastSync "
                       "date is %s" % (kind, slug, mk.group(1), feed_date(r)))
        elif mk:
            self.v(page, "STALE_MARK_ON_FRESH", "%s for /homes/%s/ says 'not confirmed' but the record's own lastSync "
                   "is within %d days" % (kind, slug, STALE_DAYS))
        return mk

    def v(self, page, code, msg):
        self.violations.append((page, code, msg))

    # ── feed ────────────────────────────────────────────────────────────────
    def load_feed(self):
        p = os.path.join(self.root, "data", "listings.json")
        try:
            data = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError) as e:
            print("CANNOT RUN: data/listings.json unreadable: %s" % e)
            sys.exit(2)
        if isinstance(data, dict):
            present = [k for k in BUCKET_KEYS if k in data]
            self.v("data/listings.json", "FEED_SHAPE",
                   "feed is a bucketed object (%s): buy.html, map-available.html and portal.html would render "
                   "records this check cannot verify; re-audit before publishing" % ", ".join(present or ["no known keys"]))
            records = [x for k in BUCKET_KEYS for x in (data.get(k) or [])]
        elif isinstance(data, list):
            records = data
        else:
            print("CANNOT RUN: data/listings.json is neither an array nor an object")
            sys.exit(2)
        if not records:
            print("CANNOT RUN: data/listings.json holds no records")
            sys.exit(2)
        need = ("address", "mlsNumber", "status", "propType", "price", "lastSync")
        ok = []
        for i, r in enumerate(records):
            if not isinstance(r, dict):
                self.v("data/listings.json", "FEED_RECORD_INCOMPLETE", "record %d is not an object" % i)
                continue
            miss = [k for k in need if r.get(k) in (None, "")]
            fresh, age, rule = freshness(r, self.now)
            if miss:
                self.v("data/listings.json", "FEED_RECORD_INCOMPLETE", "record %d lacks %s" % (i, ",".join(miss)))
            if rule in ("LASTSYNC_MALFORMED", "LASTSYNC_FUTURE"):
                self.v("data/listings.json", "FEED_LASTSYNC_INVALID", "record %d (MLS %s): %s %r" % (
                    i, r.get("mlsNumber"), rule, r.get("lastSync")))
            if not miss and rule not in ("LASTSYNC_MALFORMED", "LASTSYNC_FUTURE"):
                ok.append(r)
            else:
                self.fresh_rows.append(dict(mls_number=r.get("mlsNumber") or "(none)", decision="FEED_REJECT",
                                            last_sync_used=r.get("lastSync") or "", age_days="",
                                            rule=rule if rule.startswith("LASTSYNC_") else "INCOMPLETE"))
        self.records = ok
        # the record a slug's page shows = the one the generator selects: newest own lastSync, tie -> larger MLS #
        self.by_slug, self.collisions = {}, {}
        for r in self.records:
            s = address_slug(r)
            cur = self.by_slug.get(s)
            if cur is not None:
                self.collisions.setdefault(s, [cur]).append(r)
            if cur is None or self.newer(r, cur):
                self.by_slug[s] = r
        self.by_addr = {}
        for r in self.records:
            k = addr_key(street_of(r["address"]))
            if k:
                self.by_addr.setdefault(k, []).append(r)
        self.fresh = {id(r): freshness(r, self.now) for r in self.records}
        self.own_records = [r for r in self.records if r.get("isOurListing") is True]
        self.photo_urls = set(p for r in self.records for p in (r.get("photos") or []) if isinstance(p, str)
                              and p.startswith("http"))

    @staticmethod
    def mls_key(r):
        m = str(r.get("mlsNumber") or "")
        return (0, int(m), m) if m.isdigit() else (1, 0, m)

    def newer(self, a, b):
        ta, tb = parse_iso_utc(a["lastSync"]), parse_iso_utc(b["lastSync"])
        if ta != tb:
            return ta > tb
        return self.mls_key(a) > self.mls_key(b)

    def is_fresh(self, r):
        return self.fresh[id(r)][0]

    # ── file list ───────────────────────────────────────────────────────────
    def tracked(self):
        try:
            out = subprocess.run(["git", "-C", self.root, "ls-files"], capture_output=True, text=True,
                                 check=True).stdout.split("\n")
            files = [f for f in out if f]
        except (OSError, subprocess.CalledProcessError):
            files = []
            for d, _, fs in os.walk(self.root):
                if "/.git" in d or d.endswith(".git"):
                    continue
                files += [os.path.relpath(os.path.join(d, f), self.root) for f in fs]
        return sorted(f for f in files if os.path.isfile(os.path.join(self.root, f)))

    def html_files(self):
        return [f for f in self.tracked() if f.endswith(".html") and not f.startswith(("audit_exports/", "reports/"))]

    def read(self, f):
        return open(os.path.join(self.root, f), encoding="utf-8", errors="replace").read()

    # ── hand-written cards ──────────────────────────────────────────────────
    CARD_RES = [
        ("dir-card", re.compile(r'<a class="dir-card" href="/homes/([a-z0-9-]+)/">(.*?)</a>', re.S)),
        ("bp-card", re.compile(r'<a class="bp-card" href="/homes/([a-z0-9-]+)/">(.*?)</a>', re.S)),
        ("aside-li", re.compile(r'<li[^>]*><a href="/homes/([a-z0-9-]+)/"[^>]*>([^<]*)</a></li>')),
    ]

    def bracket_of(self, f):
        b = os.path.basename(f)
        def amt(t):
            t = t.replace("-", ".")
            return float(t[:-1]) * (1e6 if t.endswith("m") else 1e3)
        m = re.match(r"homes-(\d+(?:-\d+)?[km])-to-(\d+(?:-\d+)?[km])-in-", b)
        if m:
            return amt(m.group(1)), amt(m.group(2))
        m = re.match(r"homes-over-(\d+(?:-\d+)?[km])-in-", b)
        if m:
            return amt(m.group(1)), float("inf")
        return None

    def check_card(self, f, ctype, slug, inner, sale_context, bracket):
        row = dict(page=f, card=ctype, slug=slug, mls="", feed_status="", feed_kind="", feed_price="",
                   fresh="", shown_price="", shown_status="", shown_asof="", stale_marker="", problems="")
        start = len(self.violations)
        r = self.by_slug.get(slug)
        if r is None:
            self.v(f, "UNKNOWN_LISTING", "card links /homes/%s/ which no feed record produces" % slug)
        if not os.path.isfile(os.path.join(self.root, "homes", slug, "index.html")):
            self.v(f, "MISSING_PAGE", "card links /homes/%s/ which does not exist" % slug)
        t = text_of(inner)
        pm = re.search(r"\$[\d,]+", t)
        sm = re.search(r"Status: (\w+)", t)
        am = re.search(r"IDX feed as of ([A-Z][a-z]{2} \d{1,2}, \d{4})", t)
        row.update(shown_price=pm.group(0) if pm else "", shown_status=sm.group(1) if sm else "",
                   shown_asof=am.group(1) if am else "")
        if "<img" in inner:
            self.v(f, "IMAGE_ON_HANDWRITTEN_CARD", "/homes/%s/ card carries an <img> (%s)" % (
                slug, "stock photo" if "unsplash" in inner else "photo not drawn from the feed by the generator"))
        if re.search(r"(?i)photos on (the )?listing page", t):
            self.v(f, "PHOTO_CLAIM", "/homes/%s/ card says 'Photos on listing page' but no listing page displays IDX "
                   "photos (display rights unconfirmed, awaiting the broker's confirmation)" % slug)
        if r is not None:
            row.update(mls=r["mlsNumber"], feed_status=r["status"], feed_kind=kind_of(r), feed_price=r["price"],
                       fresh=str(self.is_fresh(r)))
            if r["status"] not in LISTABLE:
                self.v(f, "NOT_LISTABLE", "/homes/%s/ feed status %r" % (slug, r["status"]))
            if kind_of(r) == "lease":
                if sale_context:
                    self.v(f, "LEASE_IN_SALE_CONTEXT", "/homes/%s/ is a %s record on a sale page" % (slug, r["propType"]))
                if "For lease" not in t:
                    self.v(f, "LEASE_UNLABELLED", "/homes/%s/ lease card lacks 'For lease'" % slug)
            elif "lease" in t.lower():
                self.v(f, "SALE_LABELLED_LEASE", "/homes/%s/ sale record labelled lease" % slug)
            if (kind_of(r) == "lease" or r["status"] != "Active") and re.search(r"(?i)\bfor sale\b", t):
                self.v(f, "FOR_SALE_ON_NONSALE", "/homes/%s/ card says 'for sale' for a %s %s record" % (
                    slug, r["status"], kind_of(r)))
            if not pm or pm.group(0) != money(r["price"]):
                self.v(f, "PRICE_MISMATCH", "/homes/%s/ shows %s, feed %s" % (slug, pm.group(0) if pm else "no price", money(r["price"])))
            if not sm:
                self.v(f, "STATUS_MISSING", "/homes/%s/ card shows no status (feed %s)" % (slug, r["status"]))
            elif sm.group(1) != r["status"]:
                self.v(f, "STATUS_MISMATCH", "/homes/%s/ shows %s, feed %s" % (slug, sm.group(1), r["status"]))
            if not am:
                self.v(f, "ASOF_MISSING", "/homes/%s/ card shows no 'IDX feed as of' date" % slug)
            else:
                d = parse_shown_date(am.group(1))
                if d is None or d > datetime.date.fromisoformat(str(r["lastSync"])[:10]):
                    self.v(f, "ASOF_AFTER_FEED", "/homes/%s/ as-of %s is later than feed lastSync %s" % (slug, am.group(1), r["lastSync"][:10]))
            bm = re.search(r"(\d+) bd\b", t)
            if bm and int(bm.group(1)) != int(r.get("beds") or 0):
                self.v(f, "BEDS_MISMATCH", "/homes/%s/ shows %s bd, feed %s" % (slug, bm.group(1), r.get("beds")))
            for unit, key in (("ba", "baths"), ("sqft", "sqft")):
                um = re.search(r"([\d.,]+) %s\b" % unit, t)
                fv = float(r.get(key) or 0)
                if um and (fv <= (1 if key == "sqft" else 0) or float(um.group(1).replace(",", "")) != fv):
                    self.v(f, "%s_MISMATCH" % key.upper(), "/homes/%s/ shows %s %s, feed %s" % (slug, um.group(1), unit, r.get(key)))
            tm = re.search(r"(Residential Income|Residential|Commercial Lease|Commercial|Condo|Co-op|Land|Multi-Family)\b", t)
            if tm and tm.group(1) != r["propType"]:
                self.v(f, "TYPE_MISMATCH", "/homes/%s/ shows type %s, feed %s" % (slug, tm.group(1), r["propType"]))
            if bracket and not (bracket[0] <= float(r["price"]) <= bracket[1]):
                self.v(f, "OUT_OF_BRACKET", "/homes/%s/ feed price %s outside this page's range" % (slug, money(r["price"])))
        mk = self.stale_rules(f, ctype, slug, r, t)
        row["stale_marker"] = mk.group(0) if mk else ""
        self.surface(f, ctype, slug, r, row["stale_marker"])
        row["problems"] = ";".join(code for _, code, _ in self.violations[start:])
        self.cards.append(row)
        return r

    def count_row(self, f, statement, stated, recs, match, why=""):
        by, bt = {}, {}
        for r in recs:
            k = "%s/%s" % (r["status"], kind_of(r)) if r else "no-feed-record"
            t = "%s/%s" % (r["status"], r["propType"]) if r else "no-feed-record"
            by[k] = by.get(k, 0) + 1
            bt[t] = bt.get(t, 0) + 1
        self.counts.append(dict(page=f, statement=statement, stated=stated, displayed=len(recs),
                                displayed_by_status_kind=" ".join("%s=%d" % kv for kv in sorted(by.items())),
                                displayed_by_status_proptype=" ".join("%s=%d" % kv for kv in sorted(bt.items())),
                                match=match))
        if not match:
            self.v(f, "COUNT_MISMATCH", "%r states %s, page shows %d%s" % (statement, stated, len(recs), why))

    def check_handwritten(self, f, s):
        sale_context = f.startswith(SALE_CONTEXT_PREFIXES)
        bracket = self.bracket_of(f) if f.startswith("homes-for-sale/") else None
        all_links = self.links_in(f, s)
        per_type = {}
        pos = self.card_pos.setdefault(f, set())
        for ctype, rx in self.CARD_RES:
            for m in rx.finditer(s):
                if ctype == "aside-li" and not self.in_listing_aside(s, m.start()):
                    continue
                r = self.check_card(f, ctype, m.group(1), m.group(2), sale_context, bracket)
                pos.add(m.start(1))
                per_type.setdefault(ctype, []).append((m.group(1), r, m.start()))
        # links outside recognised cards are reported by check_all_links()
        if all_links:
            self.check_handwritten_schema(f, s)
        self.check_counts(f, s, per_type, all_links)
        shown = [r for v in per_type.values() for _, r, _ in v if r is not None]
        ctx = None
        if f.startswith("homes-for-sale/") and (all_links or per_type or NEUTRAL in s):
            ctx = ("L2", s)
        elif f == "portal.html":
            ctx = ("L3", s)
        elif per_type.get("aside-li"):
            asides = [s[a.start():s.find("</aside>", a.start()) + 8] for a in re.finditer(r"<aside", s)
                      if "Properties in" in s[a.start():s.find("</aside>", a.start())]]
            ctx = ("L4", "\n".join(asides))
        if ctx:
            self.check_wording(f, ctx[0], visible_copy(ctx[1]), shown)
        if f == "homes-for-sale/all-listings.html":
            self.check_dir_headings(f, s, per_type.get("dir-card", []))

    def check_handwritten_schema(self, f, s):
        """A hand-written page that shows listings cannot follow the feed: no schema.org availability at all."""
        def walk(x):
            if isinstance(x, dict):
                for k, val in x.items():
                    if k == "availability":
                        yield val
                    yield from walk(val)
            elif isinstance(x, list):
                for val in x:
                    yield from walk(val)
        for ld in re.finditer(r'(?is)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', s):
            try:
                j = json.loads(ld.group(1))
            except ValueError:
                continue
            for val in walk(j):
                self.v(f, "HANDWRITTEN_SCHEMA_AVAILABILITY", "JSON-LD availability %r on a hand-written page that shows "
                       "listings (it cannot follow the feed's per-record freshness)" % (val,))
        if re.search(r"(?i)schema\.org/(?:InStock|LimitedAvailability|PreOrder|OnlineOnly|InStoreOnly)", re.sub(
                r'(?is)<script[^>]*type="application/ld\+json"[^>]*>.*?</script>', " ", s)):
            self.v(f, "HANDWRITTEN_SCHEMA_AVAILABILITY", "schema.org availability value outside JSON-LD on a page that "
                   "shows listings")

    def in_listing_aside(self, s, pos):
        a = s.rfind("<aside", 0, pos)
        return a != -1 and s.find("</aside>", a) > pos and "Properties in" in s[a:pos]

    def check_dir_headings(self, f, s, dirc):
        heads = [(h.start(), h.group(1), text_of(h.group(2))) for h in
                 re.finditer(r'<h2 class="dir-city" id="([^"]+)">(.*?)</h2>', s, re.S)]
        for i, (pos, hid, txt) in enumerate(heads):
            hi = heads[i + 1][0] if i + 1 < len(heads) else len(s)
            inside = [r for _, r, p in dirc if pos < p < hi and r is not None]
            bad = [r for r in inside if kind_of(r) == "lease" or r["status"] != "Active"]
            if re.search(r"(?i)\bfor sale\b", txt) and bad:
                self.v(f, "FOR_SALE_ON_NONSALE", "heading %r is over %d card(s) that are not Active sale records (%s)" % (
                    txt, len(bad), ", ".join("%s %s" % (r["status"], kind_of(r)) for r in bad)))

    def check_wording(self, f, ctx, copy, shown):
        for m in W1.finditer(copy):
            self.v(f, "AVAILABILITY_CLAIM", "%s copy says %r (the feed has no list date; freshness is per record)" % (ctx, m.group(0)))
        for m in W3.finditer(copy):
            self.v(f, "COMPLETENESS_CLAIM", "%s copy says %r but only records with a page are shown" % (ctx, m.group(0)))
        own_shown = [r for r in shown if r.get("isOurListing") is True]
        for m in W4.finditer(copy):
            if not own_shown:
                self.v(f, "OWNERSHIP_CLAIM", "%s copy says %r but no record shown on this page is the brokerage's own "
                       "(isOurListing true: %d of %d feed records)" % (ctx, m.group(0), len(self.own_records), len(self.records)))
        self.check_free_counts(f, ctx, copy)

    # count elements reconciled in check_counts() / check_portal(); removed before the free-text count rule
    RECOGNISED_COUNT = [
        re.compile(r"\bListings shown on this page: \d+\b"),                     # all-listings badge, bracket stat
        re.compile(r"\(\d+ shown\)"),                                            # all-listings jump list
    ]
    SHOWN_LABEL = "Listings shown on this page: "
    PORTAL_FEATURED_LABEL = "Featured listings shown on this page"

    def check_free_counts(self, f, ctx, copy):
        for rx in self.RECOGNISED_COUNT:
            copy = rx.sub(" ", copy)
        # phone numbers and prices are not counts (E-C3): "(NNN) NNN-NNNN", "$N,NNN,NNN"
        copy = re.sub(r"\(?\b\d{3}\)?[ .-]?\d{3}[ .-]\d{4}\b|\+?1?\d{10}\b|\$[\d,.]+[KkMm]?\+?", " \u00b6 ", copy)
        if f == "portal.html":     # static counters reconciled in check_portal(): "#jc-*", "#stat-*"
            copy = re.sub(r"\b\d+\s+(?:Properties Sold|%s)\b" % self.PORTAL_FEATURED_LABEL, " ", copy)
        for m in W5.finditer(copy):
            num, rng = m.group(1), m.group(2)
            if rng:
                self.exclusions.append(dict(page=f, context=ctx, form="RANGE_MARKET_STAT", text=m.group(0),
                                            rule="E-C1 number range = market-inventory statistic (needs a source or removal; not decided here)"))
                continue
            if re.fullmatch(r"(19|20)\d\d", num):
                self.exclusions.append(dict(page=f, context=ctx, form="YEAR", text=m.group(0),
                                            rule="E-C2 4-digit year, not a count"))
                continue
            self.v(f, "UNRECONCILED_COUNT", "%s copy states %r, which is not a recognised count of the cards shown" % (ctx, m.group(0)))

    def count_label(self, f, where, text):
        self.v(f, "COUNT_LABEL", "%s states %r: a count must say what it counts (e.g. 'Listings shown on this page: N'), "
               "not inventory" % (where, text_of(text)))

    def check_counts(self, f, s, per_type, all_links):
        dirc = per_type.get("dir-card", [])
        for m in re.finditer(r'<span class="dir-count">([^<]*)</span>', s):
            mm = re.fullmatch(re.escape(self.SHOWN_LABEL) + r"(\d+)", m.group(1).strip())
            if not mm:
                self.count_label(f, "all-listings badge", m.group(1))
                continue
            n = int(mm.group(1))
            self.count_row(f, m.group(1).strip(), n, [r for _, r, _ in dirc], n == len(dirc))
        toc = re.search(r'<nav class="dir-toc"[^>]*>(.*?)</nav>', s, re.S)
        if toc:
            heads = [(h.start(), h.group(1)) for h in re.finditer(r'<h2 class="dir-city" id="([^"]+)"', s)]
            for a in re.finditer(r'<a href="#([^"]+)">([^<]*)</a>', toc.group(1)):
                cm = re.fullmatch(r"(.*?)\s*\((\d+) shown\)", a.group(2).strip())
                if not cm:
                    if re.search(r"\d", a.group(2)):
                        self.count_label(f, "jump list entry", a.group(2))
                    continue
                hid, n = a.group(1), int(cm.group(2))
                idx = [i for i, (_, h) in enumerate(heads) if h == hid]
                if not idx:
                    self.count_row(f, text_of(a.group(0)), n, [], False)
                    continue
                lo = heads[idx[0]][0]
                hi = heads[idx[0] + 1][0] if idx[0] + 1 < len(heads) else len(s)
                inside = [r for _, r, p in dirc if lo < p < hi]
                self.count_row(f, text_of(a.group(0)), n, inside, n == len(inside))
        for ld in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                j = json.loads(ld.group(1))
            except ValueError:
                continue
            me = j.get("mainEntity") if isinstance(j, dict) else None
            if isinstance(me, dict) and me.get("@type") == "ItemList" and any("/homes/" in str(e.get("url", "")) for e in me.get("itemListElement", [])):
                els = me.get("itemListElement", [])
                urls = sorted(re.sub(r"^https://gadurarealestate\.com/homes/|/$", "", e.get("url", "")) for e in els)
                self.itemlist_urls.setdefault(f, []).extend(urls)
                cards = sorted(x for x, _, _ in dirc)
                ok = me.get("numberOfItems") == len(els) == len(dirc) and urls == cards and \
                    [e.get("position") for e in els] == list(range(1, len(els) + 1))
                self.count_row(f, "JSON-LD ItemList numberOfItems", me.get("numberOfItems"), [r for _, r, _ in dirc], ok)
        bpc = per_type.get("bp-card", [])
        for m in re.finditer(r'<div class="bp-snap">(.*?)</div>\s*</div>', s, re.S):
            mm = re.fullmatch(r'<div><span>%s</span><b>(\d+)</b>' % re.escape(self.SHOWN_LABEL.strip()), m.group(1).strip())
            if not mm:
                self.count_label(f, "bracket stat", m.group(1))
                continue
            n = int(mm.group(1))
            self.count_row(f, "%s%d" % (self.SHOWN_LABEL, n), n, [r for _, r, _ in bpc], n == len(bpc))
        if NEUTRAL in s:
            self.count_row(f, NEUTRAL, 0, [r for v in per_type.values() for _, r, _ in v],
                           not all_links and not any(per_type.values()))

    # ── every listing link in any form, in every tracked text file ─────────
    def check_all_links(self):
        for f in self.tracked():
            if f.startswith(LINK_SKIP_PREFIXES) or not f.lower().endswith(TEXT_EXT):
                continue
            s = self.read(f)
            if "homes/" not in s.lower() and "homes\\/" not in s.lower():
                continue
            if f == "sitemap-listings.xml":
                continue                # every <loc> is checked by check_sitemap()
            cards = self.card_pos.get(f, set())
            allowed_abs = list(self.itemlist_urls.get(f, []))
            for o in self.links_in(f, s):
                if o["pos"] in cards:
                    continue            # a recognised card, checked by check_card()
                if o["token"] == CANON_ABS % o["slug"] and o["slug"] in allowed_abs:
                    allowed_abs.remove(o["slug"])     # an ItemList entry already reconciled with the cards
                    continue
                self.unrecognised(f, o, "outside a recognised card")

    def unrecognised(self, f, o, where):
        page = os.path.isfile(os.path.join(self.root, "homes", o["slug"], "index.html"))
        self.v(f, "UNRECOGNISED_LISTING_LINK", "%s link %r to /homes/%s/ %s (%s)" % (
            o["form"], o["token"][:120], o["slug"], where, "page exists" if page else "NO PAGE: dead link"))

    # ── portal.html (hardcoded JS fallback data) ────────────────────────────
    def check_portal(self, f, s):
        def arr(name):
            if re.search(r"\n  %s: \[\]" % name, s):
                return []
            m = re.search(r"\n  %s: \[(.*?)\n  \]" % name, s, re.S)
            if not m:
                self.v(f, "PORTAL_UNPARSEABLE", "PORTAL_DATA.%s not found" % name)
                return []
            return re.findall(r"\{(.*?)\n    \}", m.group(1), re.S)
        def field(e, k):
            m = re.search(r"\b%s:\s*'([^']*)'" % k, e) or re.search(r"\b%s:\s*([\d.]+)" % k, e)
            return m.group(1) if m else ""
        out = {}
        for name in ("featured", "area", "sold"):
            ents = arr(name)
            recs = []
            for e in ents:
                street = field(e, "address")
                cands = self.by_addr.get(addr_key(street), [])
                r = cands[0] if cands else None
                recs.append(r)
                row = dict(page=f, card="portal-" + name, slug="(js) " + street, mls=r["mlsNumber"] if r else "",
                           feed_status=r["status"] if r else "", feed_kind=kind_of(r) if r else "",
                           feed_price=r["price"] if r else "", fresh="", shown_price=field(e, "price"),
                           shown_status=field(e, "badge"), shown_asof="", problems="")
                start = len(self.violations)
                if name != "sold":
                    if r is None:
                        self.v(f, "UNKNOWN_LISTING", "portal %s entry %r has no feed record" % (name, street))
                    else:
                        if r["status"] not in LISTABLE or kind_of(r) != "sale":
                            self.v(f, "NOT_LISTABLE", "portal %s entry %r: feed %s %s" % (name, street, r["status"], r["propType"]))
                        if str(field(e, "price")) != str(r["price"]):
                            self.v(f, "PRICE_MISMATCH", "portal %s entry %r shows %s, feed %s" % (name, street, field(e, "price"), r["price"]))
                        if field(e, "badge") != r["status"]:
                            self.v(f, "STATUS_MISMATCH", "portal %s entry %r badge %r, feed %s" % (name, street, field(e, "badge"), r["status"]))
                        if "unsplash" in e:
                            self.v(f, "STOCK_PHOTO", "portal %s entry %r uses a stock photo" % (name, street))
                        if not self.is_fresh(r):
                            self.v(f, "STALE_PORTAL_ENTRY", "portal %s entry %r: the record is unconfirmed for %s days and a "
                                   "JS-rendered portal card cannot show 'Not confirmed by the listing feed since %s'" % (
                                       name, street, self.fresh[id(r)][1], feed_date(r)))
                        self.surface(f, "portal-" + name, "(js) " + street, r, "")
                row["problems"] = ";".join(c for _, c, _ in self.violations[start:])
                self.cards.append(row)
            out[name] = recs
        def static(idv):
            m = re.search(r'id="%s">(\d+)<' % idv, s)
            return int(m.group(1)) if m else None
        for idv, name in (("jc-featured", "featured"), ("jc-area", "area"), ("jc-sold", "sold"), ("stat-sold", "sold")):
            n = static(idv)
            if n is not None:
                self.count_row(f, "#%s %d" % (idv, n), n, [r for r in out[name]], n == len(out[name]))
        if "No listings are featured in this section." in s:
            self.count_row(f, "No listings are featured in this section.", 0, out["featured"], not out["featured"])
        n = static("stat-active")
        if n is not None:
            lm = re.search(r'id="stat-active">\d+</div>\s*<div class="stat-label">([^<]*)</div>', s)
            if not lm or lm.group(1).strip() != self.PORTAL_FEATURED_LABEL:
                self.count_label(f, "#stat-active", "%d %s" % (n, lm.group(1) if lm else "(no label)"))
            self.count_row(f, "#stat-active %d %s" % (n, lm.group(1).strip() if lm else ""), n, out["featured"],
                           n == len(out["featured"]))

    # ── generated pages ─────────────────────────────────────────────────────
    def expected_og(self, r):
        base = "For Lease" if kind_of(r) == "lease" else ("For Sale" if r["status"] == "Active" else "Sale Pending")
        return base if self.is_fresh(r) else "%s as of %s" % (base, feed_date(r))

    def check_generated(self, f, s):
        slug = f.split("/")[1]
        r = self.by_slug.get(slug)
        if r is None:
            self.v(f, "ORPHAN_PAGE", "no feed record produces this page; owner decides retire or keep")
            return
        fresh = self.is_fresh(r)
        def fact(k):
            m = re.search(r'<span class="fact-k">%s</span><span class="fact-v">([^<]*)</span>' % re.escape(k), s)
            return html.unescape(m.group(1)) if m else None
        if fact("MLS #") != r["mlsNumber"]:
            self.v(f, "DETAIL_WRONG_RECORD", "page MLS # %s, generator selects %s" % (fact("MLS #"), r["mlsNumber"]))
        if fact("Status") != r["status"]:
            self.v(f, "DETAIL_STATUS_STALE", "page status %s, feed %s" % (fact("Status"), r["status"]))
        pk = "Lease price" if kind_of(r) == "lease" else "Price"
        if fact(pk) != money(r["price"]):
            self.v(f, "DETAIL_PRICE_STALE", "page %s %s, feed %s" % (pk, fact(pk), money(r["price"])))
        want_off = "For lease" if kind_of(r) == "lease" else ("For sale" if r["status"] == "Active" else "Sale pending")
        if fact("Offered") != want_off:
            self.v(f, "DETAIL_OFFERED", "page 'Offered' %s, want %s for a %s %s record" % (fact("Offered"), want_off, r["status"], kind_of(r)))
        if fact("Type") != r["propType"]:
            self.v(f, "DETAIL_TYPE_STALE", "page type %s, feed %s" % (fact("Type"), r["propType"]))
        m = re.search(r'IDX feed as of ([A-Z][a-z]{2} \d{1,2}, \d{4})', s)
        if not m or m.group(1) != feed_date(r):
            self.v(f, "DETAIL_ASOF", "page as-of %s, feed lastSync %s" % (m.group(1) if m else "missing", feed_date(r)))
        og = re.search(r'<meta property="og:title" content="[^"]*— ([^"]*)">', s)
        want = self.expected_og(r)
        if not og or og.group(1) != want:
            self.v(f, "DETAIL_OG_TITLE", "og:title suffix %r, want %r (fresh=%s)" % (og.group(1) if og else None, want, fresh))
        if fresh and NOT_CONFIRMED in s:
            self.v(f, "DETAIL_FRESHNESS", "page says the feed has not returned the listing, but its own lastSync is within %d days" % STALE_DAYS)
        if not fresh and NOT_CONFIRMED not in s:
            self.v(f, "DETAIL_FRESHNESS", "record unconfirmed for %s days but the page lacks the not-confirmed notice" % self.fresh[id(r)][1])
        body = re.sub(r"(?is)<head\b.*?</head>", " ", s)
        mk = self.stale_rules(f, "generated page", slug, r, text_of(re.sub(r'(?is)<a class="ncard".*?</a>', " ", body)))
        if not fresh:
            near = re.search(r'<p class="price">[^<]*</p>\s*(?:<p class="price-note">[^<]*</p>\s*)?<p class="stale-line"><b>'
                             r'Not confirmed by the listing feed since ([A-Z][a-z]{2} \d{1,2}, \d{4})\.</b>', s)
            if not near or near.group(1) != feed_date(r):
                self.v(f, "STALE_LINE_POSITION", "the 'Not confirmed by the listing feed since %s' line is not directly "
                       "after the price" % feed_date(r))
        for mname in ("description", "og:description"):
            mm = re.search(r'<meta (?:name|property)="%s" content="([^"]*)"' % mname, s)
            if mm and (not fresh) != bool(re.search(r"Not confirmed by the listing feed since %s\." % re.escape(feed_date(r)), mm.group(1))):
                self.v(f, "DETAIL_META_FRESHNESS", "%s %s the not-confirmed sentence for a %s record" % (
                    mname, "lacks" if not fresh else "carries", "stale" if not fresh else "fresh"))
        ld_av = []
        if kind_of(r) == "lease" and re.search(r"(?i)for sale at|homes for sale</a><span>›</span>\s*<a", s):
            self.v(f, "DETAIL_LEASE_AS_SALE", "lease page uses sale wording")
        copy = visible_copy(s, drop_desc=True)
        if (kind_of(r) == "lease" or r["status"] != "Active"):
            for mm in re.finditer(r"(?i).{0,40}\bfor sale\b.{0,20}", copy):
                self.v(f, "FOR_SALE_ON_NONSALE", "%s %s page copy says %r" % (r["status"], kind_of(r), mm.group(0).strip()))
        for mm in W1.finditer(copy):
            self.v(f, "AVAILABILITY_CLAIM", "page copy says %r" % mm.group(0))
        for mm in W3.finditer(copy):
            self.v(f, "COMPLETENESS_CLAIM", "page copy says %r" % mm.group(0))
        if r.get("isOurListing") is not True:
            for mm in W4.finditer(copy):
                self.v(f, "OWNERSHIP_CLAIM", "page copy says %r but the feed marks the record not the brokerage's own" % mm.group(0))
        self.check_free_counts(f, "L1", copy)
        for d in re.finditer(r'(?is)<p class="desc">(.*?)</p>', s):
            for mm in list(W1.finditer(text_of(d.group(1)))) + list(W5.finditer(text_of(d.group(1)))):
                self.exclusions.append(dict(page=f, context="L1-remarks", form="FEED_REMARKS", text=mm.group(0),
                                            rule="E-R1 feed remarks are shown verbatim from the IDX record"))
        for url in self.photo_urls:
            if url in s:
                self.v(f, "FEED_PHOTO_DISPLAYED", "page carries a feed photo URL; IDX photo display rights are unconfirmed")
                break
        for ld in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                j = json.loads(ld.group(1))
            except ValueError:
                self.v(f, "DETAIL_JSONLD", "JSON-LD does not parse")
                continue
            for node in (j.get("@graph") or [j]) if isinstance(j, dict) else []:
                if node.get("@type") != "RealEstateListing":
                    continue
                o = node.get("offers") or {}
                if o.get("price") != r["price"]:
                    self.v(f, "DETAIL_OFFER_PRICE", "offers.price %s, feed %s" % (o.get("price"), r["price"]))
                ld_av.append(str(o.get("availability")))
                if (o.get("availability") == "https://schema.org/InStock") != (r["status"] == "Active" and fresh):
                    self.v(f, "DETAIL_OFFER_AVAILABILITY", "availability %s for status %s, fresh=%s" % (o.get("availability"), r["status"], fresh))
                if o.get("availability") not in (None, "https://schema.org/InStock"):
                    self.v(f, "DETAIL_OFFER_AVAILABILITY", "unexpected availability %s" % o.get("availability"))
                if (o.get("businessFunction") == "http://purl.org/goodrelations/v1#LeaseOut") != (kind_of(r) == "lease"):
                    self.v(f, "DETAIL_OFFER_FUNCTION", "businessFunction %s for a %s record" % (o.get("businessFunction"), kind_of(r)))
                if "datePosted" in node:
                    self.v(f, "DETAIL_DATEPOSTED", "datePosted is not in the feed")
                if node.get("image"):
                    self.v(f, "DETAIL_JSONLD_IMAGE", "JSON-LD image present while the page displays no listing photo")
        self.surface(f, "generated page", slug, r, mk.group(0) if mk else "", "schema availability: %s" % (",".join(ld_av) or "none"))
        ncard_pos = set()
        for m in re.finditer(r'<a class="ncard" href="/homes/([a-z0-9-]+)/">(.*?)</a>', s, re.S):
            ncard_pos.add(m.start(1))
            n = self.by_slug.get(m.group(1))
            if m.group(1) == slug:
                self.v(f, "NEARBY_SELF", "nearby card links this page")
            if not os.path.isfile(os.path.join(self.root, "homes", m.group(1), "index.html")):
                self.v(f, "NEARBY_MISSING_PAGE", "nearby card links missing /homes/%s/" % m.group(1))
            if n is None:
                self.v(f, "NEARBY_UNKNOWN", "nearby card /homes/%s/ has no feed record" % m.group(1))
                continue
            if kind_of(n) != kind_of(r):
                self.v(f, "NEARBY_KIND_MIX", "nearby %s card on a %s page" % (kind_of(n), kind_of(r)))
            t = text_of(m.group(2))
            if n["status"] not in t or money(n["price"]) not in t:
                self.v(f, "NEARBY_STALE", "nearby /homes/%s/ card lacks feed status/price" % m.group(1))
            nk = self.stale_rules(f, "nearby card", m.group(1), n, t)
            self.surface(f, "nearby card", m.group(1), n, nk.group(0) if nk else "")
        for o in self.links_in(f, s):
            if o["pos"] in ncard_pos:
                continue
            if o["slug"] == slug and o["token"] == CANON_ABS % slug:
                continue                # the page's own canonical / og:url / JSON-LD url
            self.unrecognised(f, o, "on a generated page outside a nearby card")

    # ── coverage + freshness decisions ──────────────────────────────────────
    def check_coverage(self):
        selected = {id(r) for r in self.by_slug.values()}
        for slug, recs in sorted(self.collisions.items()):
            sel = self.by_slug[slug]
            for r in recs:
                if r is not sel:
                    fresh, age, rule = self.fresh[id(r)]
                    self.fresh_rows.append(dict(mls_number=r["mlsNumber"], decision="OMITTED_SLUG_COLLISION",
                                                last_sync_used=r["lastSync"], age_days=age,
                                                rule="SLUG_SHARED_WITH_%s_NEWER_OWN_LASTSYNC" % sel["mlsNumber"]))
        for slug, r in sorted(self.by_slug.items()):
            fresh, age, rule = self.fresh[id(r)]
            page = os.path.isfile(os.path.join(self.root, "homes", slug, "index.html"))
            if page:
                decision = "PAGE_FRESH" if fresh else "PAGE_STALE_NOT_CONFIRMED_NOTICE"
            elif fresh and r["status"] in LISTABLE:
                decision = "MISSING_PAGE_FRESH_RECORD"
                self.v("homes/%s/" % slug, "MISSING_PAGE_FRESH_RECORD",
                       "MLS %s is %s and confirmed %s day(s) ago but has no page: generator failure" % (r["mlsNumber"], r["status"], age))
            else:
                decision = "OMITTED_STALE_NO_PAGE"
            self.fresh_rows.append(dict(mls_number=r["mlsNumber"], decision=decision, last_sync_used=r["lastSync"],
                                        age_days=age, rule=rule))

    # ── sitemap-listings.xml ────────────────────────────────────────────────
    def check_sitemap(self):
        p = os.path.join(self.root, "sitemap-listings.xml")
        if not os.path.isfile(p):
            return
        s = self.read("sitemap-listings.xml")
        deny = set()
        dp = os.path.join(self.root, "scripts", "dgp", "placeholder_sitemap_denylist.txt")
        if os.path.isfile(dp):
            deny = {l.strip().rstrip("/") for l in open(dp, encoding="utf-8") if l.strip() and not l.startswith("#")}
        else:
            self.v("sitemap-listings.xml", "SITEMAP_DENYLIST_MISSING", "scripts/dgp/placeholder_sitemap_denylist.txt not found")
        for m in re.finditer(r"<loc>([^<]*)</loc>", s):
            u = m.group(1)
            mm = re.match(r"https://gadurarealestate\.com/homes/([a-z0-9-]+)/$", u)
            if not mm:
                self.v("sitemap-listings.xml", "SITEMAP_URL", "unexpected <loc> %s" % u)
                continue
            r = self.by_slug.get(mm.group(1))
            why = []
            if r is None:
                why.append("no feed record")
            else:
                if not self.is_fresh(r):
                    why.append("record unconfirmed for %s days" % self.fresh[id(r)][1])
                if not real_photos(r):
                    why.append("no real photo provenance")
            if not os.path.isfile(os.path.join(self.root, "homes", mm.group(1), "index.html")):
                why.append("no page")
            if u.rstrip("/") in deny:
                why.append("broker denylist")
            if why:
                self.v("sitemap-listings.xml", "SITEMAP_INELIGIBLE", "/homes/%s/: %s" % (mm.group(1), "; ".join(why)))
        for m in re.finditer(r"<lastmod>([^<]*)</lastmod>", s):
            try:
                if datetime.date.fromisoformat(m.group(1)) > self.now.date():
                    self.v("sitemap-listings.xml", "SITEMAP_FUTURE_LASTMOD", m.group(1))
            except ValueError:
                self.v("sitemap-listings.xml", "SITEMAP_LASTMOD", "malformed %r" % m.group(1))

    def check_feed_photos_elsewhere(self):
        if not self.photo_urls:
            return
        for f in self.tracked():
            if f.startswith(LINK_SKIP_PREFIXES) or not f.lower().endswith(TEXT_EXT):
                continue
            s = self.read(f)
            for url in self.photo_urls:
                if url in s:
                    self.v(f, "FEED_PHOTO_DISPLAYED", "hand-written file carries a feed photo URL (IDX photo display rights unconfirmed)")
                    break

    def run(self):
        self.load_feed()
        for f in self.html_files():
            s = self.read(f)
            if re.match(r"homes/[^/]+/index\.html$", f):
                self.check_generated(f, s)
            elif not f.startswith("homes/"):
                self.check_handwritten(f, s)
            if f == "portal.html":
                self.check_portal(f, s)
        self.check_all_links()
        self.check_coverage()
        self.check_sitemap()
        self.check_feed_photos_elsewhere()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--now", help="check time, ISO-8601 UTC (default: now)")
    ap.add_argument("--report")
    ap.add_argument("--freshness-csv")
    ap.add_argument("--surfaces-csv")
    a = ap.parse_args()
    if a.now:
        now = parse_iso_utc(a.now)
        if now is None:
            print("CANNOT RUN: --now must be ISO-8601 UTC, e.g. 2026-10-20T14:00:00Z")
            sys.exit(2)
    else:
        now = datetime.datetime.now(datetime.timezone.utc)
    c = Checker(os.path.abspath(a.root), now)
    c.run()
    if a.report:
        for name, rows in (("cards", c.cards), ("counts", c.counts), ("exclusions", c.exclusions)):
            if rows:
                with open("%s_%s.csv" % (a.report, name), "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                    w.writeheader()
                    w.writerows(rows)
    if a.freshness_csv:
        with open(a.freshness_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["mls_number", "decision", "last_sync_used", "basis", "age_days", "rule",
                                               "check_time"])
            w.writeheader()
            for row in sorted(c.fresh_rows, key=lambda x: str(x["mls_number"])):
                w.writerow(dict(row, basis="own lastSync", check_time=now.strftime("%Y-%m-%dT%H:%M:%SZ")))
    if a.surfaces_csv:
        with open(a.surfaces_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["page", "surface", "slug", "mls", "feed_status", "last_sync_used", "basis",
                                               "age_days", "rule", "decision", "marker_shown", "note", "check_time"])
            w.writeheader()
            for row in c.surfaces:
                w.writerow(dict(row, check_time=now.strftime("%Y-%m-%dT%H:%M:%SZ")))
    print("check time %s; listing cards checked: %d; count statements checked: %d; feed records usable: %d; "
          "surfaces judged for freshness: %d (%d stale); exclusions by rule: %d" % (
              now.strftime("%Y-%m-%dT%H:%M:%SZ"), len(c.cards), len(c.counts), len(c.records), len(c.surfaces),
              sum(1 for x in c.surfaces if x["decision"] == "STALE_MARK_REQUIRED"), len(c.exclusions)))
    for row in sorted(c.fresh_rows, key=lambda x: str(x["mls_number"])):
        print("FRESHNESS %s %s (age %s d, %s)" % (row["mls_number"], row["decision"], row["age_days"], row["rule"]))
    for page, code, msg in c.violations:
        print("FAIL %s %s: %s" % (code, page, msg))
    print("RESULT: %s (%d violations)" % ("PASS" if not c.violations else "FAIL", len(c.violations)))
    sys.exit(1 if c.violations else 0)


if __name__ == "__main__":
    main()
