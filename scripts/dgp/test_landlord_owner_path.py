#!/usr/bin/env python3
"""Rental-owner (landlord) path gate.

scripts/build_owner_path_blocks.py renders the owner contact block, the hub's
scope section and the owner signposts from data/landlord-owner-path.json and
data/business-contact.json. This gate fails if:

  1. any configured page is stale against the generator, or lacks its region;
  2. a removed phrase comes back on a configured page (visible text or JSON-LD),
     including through a regeneration from an old source;
  3. the hub shows a services list that is not backed by an owner_services entry;
  4. FAQPage JSON-LD on a configured page asks a question the page does not show;
  5. an owner block lacks the brokerage name and licensee title (19 NYCRR 175.25),
     links somewhere that does not exist, or carries a figure or a promise;
  6. the generator stops failing closed (self-tests on copies in a temp dir);
  7. the click-attribution script starts making requests of its own;
  8. a configured page has an element left open or closed twice (tag balance);
  9. a removed phrase, guarantee wording near rent/payment/portion, first-person
     service wording or a household-type descriptor appears in visible text,
     JSON-LD, <title>, meta description/keywords, og:* or twitter:*;
 10. any configured page links a /community/ group page;
 11. a configured page carries an HTML comment with status wording, the data
     file has a key outside the documented set, or the generator renders an
     HTML comment other than its region markers;
 12. a page mentions texting while the public number is not in sms_lines.
Checks 8-12 run against built-in bad fixtures first (rule self-tests), so a
check that stops matching fails the gate.

Run:  python3 scripts/dgp/test_landlord_owner_path.py      (exit 0 pass / 1 fail)
Reads the working tree; fixtures go to a temporary directory outside the repo.
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_PATH = ROOT / "scripts" / "build_owner_path_blocks.py"
CFG_PATH = ROOT / "data" / "landlord-owner-path.json"
HUB = "/services/landlord-services-queens.html"
NAV_LINK = f'<a href="{HUB}"'

# Phrases removed from the owner and rental pages. Each must stay off every configured
# page, in visible text and in JSON-LD. Keep the label with the pattern.
FORBIDDEN = [
    (r"property management services", "service wording not used on these pages"),
    (r"full[- ]service (?:landlord|leasing|building management|property)", "service wording not used on these pages"),
    (r"tenant placement", "service wording not used on these pages"),
    (r"pre-?screened", "tenant-matching wording"),
    (r"\bpipeline\b", "tenant-matching wording"),
    (r"7[- ]days? a week|seven days a week|7-day", "availability wording"),
    (r"handles? everything|handle it all|entire process", "full-service wording"),
    (r"pre-HQS|pre-inspection walk", "inspection-service wording"),
    (r"helped dozens", "track-record wording"),
    (r"guarantee[ds]? (?:rent|payment)|government[- ]guaranteed|gov't guaranteed|guarantees the rest|government-backed check",
     "guarantee wording"),
    (r"vacanc(?:y|ies) fast|rent it out fast|fill(?:s)? (?:the unit|vacancies) faster|immediately match", "speed wording"),
    (r"within 24 hours|same[- ]day|right away", "response-time wording"),
    (r"motivated to (?:maintain|sign)", "renter generalisation"),
    (r"household composition", "screening wording"),
    (r"\b40x\b|650\+", "screening figure without a source"),
    (r"languages of Queens", "language wording"),
    (r"highest (?:section 8|cityfheps) demand", "neighborhood demand list"),
    (r"local law 152", "citation for CO detectors"),
    (r"guarantor services", "service wording not used on these pages"),
]
# Any /community/ page other than the hub itself (relative or absolute URL).
COMMUNITY_LINK = re.compile(r'href="(?:https?://(?:www\.)?gadurarealestate\.com)?/community/(?!index\.html"|")[^"#?]+', re.I)
GUARANTEE = re.compile(r"guarantee\w*(?:\W+\w+){0,6}?\W+(?:rent|payments?|portion)\b"
                       r"|\b(?:rent|payments?|portion)(?:\W+\w+){0,4}?\W+guarantee\w*", re.I)
# Descriptors of a neighborhood or unit by the kind of household or resident.
HOUSEHOLD = re.compile(
    r"family[- ](?:friendly|oriented)|famil(?:y|ies) seeking|(?:young|growing|small) families"
    r"|(?:great|perfect|ideal|popular|good|best|suited) (?:for|with|among|to) (?:young |growing |small |single |new )?"
    r"(?:famil(?:y|ies)|couples|singles|single renters|students|retirees|seniors|professionals|newcomers|immigrants)"
    r"|kid[- ]friendly|child[- ]friendly|empty[- ]nesters?|young professionals|students and newcomers"
    r"|single renters and couples|adults?[- ]only|(?:no|without) (?:kids|children)", re.I)
# First-person service wording ("we screen your tenants", "Nitin will collect the rent").
SERVICE = re.compile(r"\b(?:we|we'll|our team|nitin|gadura real estate)\s+(?:will\s+|can\s+|also\s+)?"
                     r"(?:screen|collect|handle|manage|place|find|market|list|show|vet|qualify|fill)\w*\s+"
                     r"(?:(?:the|your|all|every|qualified|reliable)\s+)*(?:tenants?|renters?|rents?|repairs?|units?|property"
                     r"|properties|showings?|vacanc\w+|apartments?|leases?|maintenance)\b", re.I)
STATUS_COMMENT = re.compile(r"<!--(?:(?!-->).)*?\b(?:confirm\w*|pending|todo|fixme|tbd|review\w*|approv\w*|unverified"
                            r"|draft|internal)\b(?:(?!-->).)*-->", re.I | re.S)
DATA_KEYS = {"_README", "email", "sms_lines", "hub_path", "renter_path", "pages", "evidenced_scope",
             "owner_services"}
TEXT_MENTION = re.compile(r'\bcall, text\b|\btext or email\b|\btext and email\b|\btext us\b|href="sms:', re.I)
PAIRED = ("a", "div", "section", "aside", "article", "nav", "header", "footer", "main", "ul", "ol", "table", "tr",
          "span", "strong", "em", "b", "i", "h1", "h2", "h3", "h4", "h5", "h6", "script", "style", "button", "form",
          "label", "select", "textarea", "details", "summary", "figure", "figcaption", "blockquote", "p", "li")
FIGURE = re.compile(r"\$\s?\d|\d+\s?%|\b\d+\s?(?:days?|hours?|weeks?)\b", re.I)
PROMISE = re.compile(r"\b(?:within|today|asap|immediately|instant|fast|quick|same[- ]day|24/7|best|top|#1|expert|specialist|trusted|guarantee)", re.I)


def load_generator():
    spec = importlib.util.spec_from_file_location("owner_gen", GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The shared legal footer (IDX attribution, licence lines) is owned elsewhere; its
# "takedown requests honored within 24 hours" is an IDX policy line, not an owner promise.
LEGAL_FOOTER = re.compile(r'<footer class="gre-legal-footer".*?</footer>', re.S)


def visible(src: str) -> str:
    t = re.sub(r"<(script|style|noscript|template)\b.*?</\1>", " ", src, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def jsonld(src: str) -> list:
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            out.append({"@type": "UNPARSEABLE"})
            continue
        for x in (d if isinstance(d, list) else d.get("@graph", [d])):
            out.append(x)
    return out


def meta_text(src: str) -> str:
    """<title> plus the content of meta description, keywords, og:* and twitter:* tags."""
    out = [m.group(1) for m in re.finditer(r"<title[^>]*>(.*?)</title>", src, re.S | re.I)]
    for tag in re.findall(r"<meta\b[^>]*>", src, re.I):
        key = re.search(r'\b(?:name|property)\s*=\s*"([^"]+)"', tag, re.I)
        val = re.search(r'\bcontent\s*=\s*"([^"]*)"', tag, re.I)
        if key and val and re.match(r"(?:description|keywords|og:|twitter:)", key.group(1), re.I):
            out.append(val.group(1))
    return " | ".join(html.unescape(x) for x in out)


def tag_balance(src: str) -> dict:
    """open-minus-close count per element that needs an end tag (comments, script/style bodies ignored)."""
    t = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    t = re.sub(r"(<(script|style)\b[^>]*>).*?(</\2>)", r"\1\3", t, flags=re.S | re.I)
    out: dict = {}
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>", t):
        tag = m.group(2).lower()
        if tag in PAIRED and not m.group(3):
            out[tag] = out.get(tag, 0) + (-1 if m.group(1) else 1)
    return {k: v for k, v in out.items() if v}


def content_checks(rel: str, src: str, sms_ok: bool) -> list[str]:
    """Checks 8-12 on one page's source. Pure: used on the configured pages and on the rule fixtures."""
    fails = []
    bal = tag_balance(src)
    if bal:
        fails.append(f"{rel}: tag balance (open minus close) is not zero: {bal}")
    vis_content = visible(LEGAL_FOOTER.sub(" ", src))
    ld_text = json.dumps(jsonld(src), ensure_ascii=False)
    meta = meta_text(src)
    for where, text in (("visible", vis_content), ("JSON-LD", ld_text), ("meta", meta)):
        if where == "meta":
            for pat, why in FORBIDDEN:
                m = re.search(pat, text, re.I)
                if m:
                    fails.append(f"{rel}: meta text has {m.group(0)!r} - {why}")
        for rx, why in ((GUARANTEE, "guarantee wording near rent/payment/portion"),
                        (HOUSEHOLD, "household-type descriptor"),
                        (SERVICE, "first-person service wording")):
            m = rx.search(text)
            if m:
                fails.append(f"{rel}: {where} text has {m.group(0)!r} - {why}")
    m = COMMUNITY_LINK.search(src)
    if m:
        fails.append(f"{rel}: links a /community/ group page ({m.group(0)[6:]})")
    m = STATUS_COMMENT.search(src)
    if m:
        fails.append(f"{rel}: HTML comment with status wording: {m.group(0)[:60]!r}")
    if not sms_ok:
        m = TEXT_MENTION.search(LEGAL_FOOTER.sub(" ", src))
        if m:
            fails.append(f"{rel}: mentions texting ({m.group(0)!r}) but the public number is not in sms_lines")
    return fails


# Each rule fixture must be flagged by content_checks; CLEAN must not be.
CLEAN = ('<html><head><title>Owner guide</title><meta name="description" content="Rules with sources.">'
         '<meta name="keywords" content="landlord queens"></head><body><p>Call or email us. '
         '<a href="/community/">Communities</a></p></body></html>')
RULE_FIXTURES = [
    ("tag balance: unclosed link", CLEAN.replace("<p>Call", '<p>For owners, <a href="/x.html"></p><p>Call'), "tag balance"),
    ("tag balance: extra </div>", CLEAN.replace("</body>", "</div></body>"), "tag balance"),
    ("forbidden phrase in <title>", CLEAN.replace("Owner guide", "Property Management Services"), "meta text has"),
    ("forbidden phrase in meta description", CLEAN.replace("Rules with sources.", "Tenant placement for owners."), "meta text has"),
    ("forbidden phrase in keywords", CLEAN.replace("landlord queens", "guaranteed rent section 8 queens ny"), "meta text has"),
    ("forbidden phrase in og:description", CLEAN.replace("</head>", '<meta property="og:description" content="We handle everything."></head>'), "meta text has"),
    ("forbidden phrase in twitter:title", CLEAN.replace("</head>", '<meta name="twitter:title" content="Rent it out fast"></head>'), "meta text has"),
    ("guarantee near portion (visible)", CLEAN.replace("Call or email us.", "This contract guarantees the government's portion of rent."), "guarantee wording"),
    ("guarantee near payment (JSON-LD)", CLEAN.replace("</head>", '<script type="application/ld+json">{"@type":"Article","description":"Payments are guaranteed by the city"}</script></head>'), "guarantee wording"),
    ("service wording in other words", CLEAN.replace("Call or email us.", "We screen your tenants, collect the rent and handle repairs."), "first-person service wording"),
    ("household descriptor (visible)", CLEAN.replace("Call or email us.", "A family-friendly block near the park."), "household-type descriptor"),
    ("household descriptor (meta)", CLEAN.replace("Rules with sources.", "Great for young families."), "household-type descriptor"),
    ("community group link", CLEAN.replace('href="/community/"', 'href="/community/example-community.html"'), "/community/ group page"),
    ("community group link, absolute URL", CLEAN.replace('href="/community/"', 'href="https://gadurarealestate.com/community/example/"'), "/community/ group page"),
    ("status comment", CLEAN.replace("<body>", "<body><!-- TODO: confirm item 3 -->"), "status wording"),
    ("text mention without sms line", CLEAN.replace("Call or email us.", "Call, text or email us."), "mentions texting"),
    ("sms link without sms line", CLEAN.replace("</p></body>", '<a href="sms:+10000000000">Text</a></p></body>'), "mentions texting"),
]


def rule_selftests(fails: list[str]) -> int:
    if content_checks("fixture/clean.html", CLEAN, False):
        fails.append(f"rule selftest: clean fixture flagged: {content_checks('fixture/clean.html', CLEAN, False)}")
    for label, src, expect in RULE_FIXTURES:
        got = content_checks("fixture/bad.html", src, False)
        if not any(expect in g for g in got):
            fails.append(f"rule selftest: '{label}' not caught (expected a '{expect}' failure, got {got})")
    return 1 + len(RULE_FIXTURES)


def region(src: str, name: str) -> list[str]:
    return re.findall(rf"<!-- LL-OWNER-{name}:START\b.*?-->(.*?)<!-- LL-OWNER-{name}:END -->", src, re.S)


def check_pages(cfg: dict, contact_digits: str, fails: list[str]) -> int:
    n = 0
    sms_ok = contact_digits in {re.sub(r"\D", "", str(x))[-10:] for x in cfg["sms_lines"]}
    for rel, page in cfg["pages"].items():
        f = ROOT / rel
        if not f.is_file():
            fails.append(f"{rel}: configured page missing")
            continue
        src = f.read_text(encoding="utf-8")
        vis = visible(src)
        vis_content = visible(LEGAL_FOOTER.sub(" ", src))
        ld_text = json.dumps(jsonld(src), ensure_ascii=False)
        code = page["code"]
        # 1/5. regions present, carry the page code, 175.25 identity, live links, no figure or promise
        for name, want in (("BLOCK", page.get("block")), ("SIGNPOST", page.get("signpost")), ("SCOPE", page.get("block") == "hub")):
            regs = region(src, name)
            if want and len(regs) != 1:
                fails.append(f"{rel}: expected one LL-OWNER-{name} region, found {len(regs)}")
                continue
            for r in regs:
                if name != "SCOPE" and f'data-ll-block="{code}"' not in r:
                    fails.append(f"{rel}: {name} region does not carry page code {code}")
                rv = visible(r)
                if name == "BLOCK":
                    if "Gadura Real Estate, LLC" not in rv or "Licensed Real Estate Salesperson" not in rv:
                        fails.append(f"{rel}: owner block lacks brokerage name or licensee title (175.25)")
                    tel = re.findall(r'href="tel:\+1(\d{10})"', r)
                    if tel != [contact_digits]:
                        fails.append(f"{rel}: owner block call link does not dial the business-contact.json number")
                    if f"web ref {code}" not in html.unescape(re.sub(r"%([0-9A-F]{2})", lambda m: chr(int(m.group(1), 16)), r)):
                        fails.append(f"{rel}: owner block prefill lacks 'web ref {code}'")
                for href in re.findall(r'href="(/[^"#?]*)', r):
                    target = ROOT / href.lstrip("/")
                    if not (target.is_file() or (target / "index.html").is_file()):
                        fails.append(f"{rel}: {name} region links to missing {href}")
                if name != "SCOPE" and FIGURE.search(rv):
                    fails.append(f"{rel}: {name} region shows a figure: {FIGURE.search(rv).group(0)!r}")
                if PROMISE.search(rv):
                    fails.append(f"{rel}: {name} region carries promise/rank wording: {PROMISE.search(rv).group(0)!r}")
        # 2. removed claims stay removed (visible text and JSON-LD)
        for pat, why in FORBIDDEN:
            for where, text in (("visible", vis_content), ("JSON-LD", ld_text)):
                m = re.search(pat, text, re.I)
                if m:
                    fails.append(f"{rel}: {where} text has {m.group(0)!r} - {why}")
        # 8-12. tag balance, meta + guarantee + household wording, community links, status comments, texting
        fails.extend(content_checks(rel, src, sms_ok))
        # 4. FAQPage questions must be on the page
        for x in jsonld(src):
            if x.get("@type") == "FAQPage":
                for q in x.get("mainEntity", []):
                    if " ".join(q.get("name", "").split())[:50] not in vis:
                        fails.append(f"{rel}: FAQPage JSON-LD question not shown on page: {q.get('name','')[:60]!r}")
        # owner entry: renter-side pages and the two service pages carry the Landlords nav link
        if page.get("signpost") in ("rentals", "renter") or page.get("block") == "hub" or rel == "services/property-management.html":
            if NAV_LINK not in src or ">Landlords</a>" not in src:
                fails.append(f"{rel}: missing 'Landlords' nav entry to the owner page")
        n += 1
    return n


def check_scope(cfg: dict, fails: list[str]) -> None:
    hub = (ROOT / HUB.lstrip("/")).read_text(encoding="utf-8")
    scope = region(hub, "SCOPE")
    if len(scope) != 1:
        fails.append("hub: scope region missing")
        return
    if "<!--" in scope[0]:
        fails.append("hub: the scope region carries an HTML comment; it must render only visible content")
    services = cfg["owner_services"]
    heading = "Services the firm offers rental owners" in scope[0]
    if heading != bool(services):
        fails.append("hub: the services list must render exactly when owner_services has entries")
    for svc in services:
        if f'<li class="ll-service">{html.escape(svc["copy"])}</li>' not in scope[0]:
            fails.append(f"hub: owner_services entry not rendered: {svc['copy'][:40]!r}")


def selftests(gen, fails: list[str]) -> int:
    """Fail-closed behaviour, on copies in a temp dir (nothing in the repo is touched)."""
    ran = 0
    with tempfile.TemporaryDirectory(prefix="ll-owner-") as td:
        tmp = Path(td)
        (tmp / "data").mkdir()
        shutil.copy(ROOT / "data" / "business-contact.json", tmp / "data" / "business-contact.json")
        cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
        hub_rel = HUB.lstrip("/")
        (tmp / hub_rel).parent.mkdir(parents=True, exist_ok=True)
        page = ("<html><head></head><body>\n<!-- LL-OWNER-BLOCK:START -->\n<!-- LL-OWNER-BLOCK:END -->\n"
                "<!-- LL-OWNER-SCOPE:START -->\n<!-- LL-OWNER-SCOPE:END -->\n</body></html>")
        (tmp / hub_rel).write_text(page, encoding="utf-8")
        renter_rel = cfg["renter_path"].lstrip("/")
        (tmp / renter_rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / renter_rel).write_text("<html><head></head><body></body></html>", encoding="utf-8")
        (tmp / "fair-housing.html").write_text("x", encoding="utf-8")
        base = dict(cfg, pages={hub_rel: {"code": "LL-01", "block": "hub", "signpost": None}})

        def attempt(c):
            (tmp / "data" / "landlord-owner-path.json").write_text(json.dumps(c), encoding="utf-8")
            gen.ROOT, gen.CONTACT_FILE, gen.CFG_FILE = tmp, tmp / "data" / "business-contact.json", tmp / "data" / "landlord-owner-path.json"
            try:
                contact, c2 = gen.load()
                return "ok", gen.render_page(hub_rel, page, c2["pages"][hub_rel], contact, c2)
            except gen.Stop as exc:
                return "stop", str(exc)

        st, out = attempt(base)
        ran += 1
        if st != "ok" or "ll-service" in out or "Services the firm offers" in out or "<!--" in region(out, "SCOPE")[0]:
            fails.append("selftest: baseline render with no owner_services should show no services list and no comment")
        for label, mutate in (
            ("owner_services entry with a key other than copy", lambda c: c.update({"owner_services": [{"copy": "Example service.", "note": "x"}]})),
            ("owner_services entry with empty copy", lambda c: c.update({"owner_services": [{"copy": " "}]})),
            ("owner_services entry not an object", lambda c: c.update({"owner_services": ["Example service."]})),
            ("owner_services not a list", lambda c: c.update({"owner_services": {"a": 1}})),
            ("malformed email", lambda c: c.update({"email": "not-an-email"})),
            ("sms_lines not a list", lambda c: c.update({"sms_lines": True})),
        ):
            c = json.loads(json.dumps(base))
            mutate(c)
            st, _ = attempt(c)
            ran += 1
            if st != "stop":
                fails.append(f"selftest: generator did not stop on {label}")
        # Text button fails closed when the public number is not a listed SMS line
        c = json.loads(json.dumps(base))
        c["sms_lines"] = []
        st, out = attempt(c)
        ran += 1
        if st != "ok" or "sms:" in out or "Call or email" not in out:
            fails.append("selftest: Text button must disappear when the public number is not in sms_lines")
        # ... and appears only when the public number is listed
        c = json.loads(json.dumps(base))
        c["sms_lines"] = [json.loads((tmp / "data" / "business-contact.json").read_text(encoding="utf-8"))["phone_tel"]]
        st, out = attempt(c)
        ran += 1
        if st != "ok" or "sms:" not in out or "Call, text or email" not in out:
            fails.append("selftest: Text button should render when the public number is listed in sms_lines")
        # An owner_services entry renders visibly
        c = json.loads(json.dumps(base))
        c["owner_services"] = [{"copy": "TEST-COPY"}]
        st, out = attempt(c)
        ran += 1
        if st != "ok" or '<li class="ll-service">TEST-COPY</li>' not in out:
            fails.append("selftest: an owner_services entry should render visibly")
        # Missing markers stop the run
        try:
            contact, c2 = gen.load()
            gen.render_page(hub_rel, "<html><head></head><body></body></html>", c2["pages"][hub_rel], contact, c2)
            fails.append("selftest: a page without its markers should stop the run")
        except gen.Stop:
            pass
        ran += 1
    return ran


def main() -> int:
    fails: list[str] = []
    print("=== landlord owner-path gate ===")
    gen = load_generator()
    try:
        contact, cfg = gen.load()
    except gen.Stop as exc:
        print(f"FAIL: generator inputs: {exc}")
        return 1
    stale = []
    for rel, page in cfg["pages"].items():
        src = (ROOT / rel).read_text(encoding="utf-8")
        try:
            if gen.render_page(rel, src, page, contact, cfg) != src:
                stale.append(rel)
        except gen.Stop as exc:
            fails.append(f"{rel}: {exc}")
    for rel in stale:
        fails.append(f"{rel}: stale; run python3 scripts/build_owner_path_blocks.py --apply")
    n = check_pages(cfg, gen.digits(contact["phone_tel"]), fails)
    check_scope(cfg, fails)
    gen_src = GEN_PATH.read_text(encoding="utf-8")
    if re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", gen_src):
        fails.append("generator holds an email address; it belongs in data/landlord-owner-path.json")
    js = (ROOT / "js" / "owner-contact.js").read_text(encoding="utf-8")
    if re.search(r"\b(fetch|XMLHttpRequest|sendBeacon|Image\(|WebSocket)\b", js):
        fails.append("js/owner-contact.js makes a request of its own; it may only call an existing gtag")
    extra = sorted(set(json.loads(CFG_PATH.read_text(encoding="utf-8"))) - DATA_KEYS)
    if extra:
        fails.append(f"data/landlord-owner-path.json: unexpected key(s) {extra}; allowed: {sorted(DATA_KEYS)}")
    m = re.search(r"<!--(?! LL-OWNER-)", gen_src)
    if m:
        fails.append("generator renders an HTML comment other than the LL-OWNER-* region markers")
    rules = rule_selftests(fails)
    ran = selftests(load_generator(), fails)
    print(f"pages checked: {n}; generator self-tests: {ran}; rule self-tests: {rules}; forbidden patterns: {len(FORBIDDEN)}")
    if fails:
        print(f"\nFAIL: {len(fails)} problem(s)")
        for f in fails:
            print(f"    {f}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
