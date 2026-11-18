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
  7. the click-attribution script starts making requests of its own.

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
COMMUNITY_LINK = re.compile(r'href="/community/[a-z-]+-community\.html"')
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


def region(src: str, name: str) -> list[str]:
    return re.findall(rf"<!-- LL-OWNER-{name}:START\b.*?-->(.*?)<!-- LL-OWNER-{name}:END -->", src, re.S)


def check_pages(cfg: dict, contact_digits: str, fails: list[str]) -> int:
    n = 0
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
        if rel.startswith("rentals/") and COMMUNITY_LINK.search(src):
            fails.append(f"{rel}: links a /community/ group page from a rentals page")
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
    ran = selftests(load_generator(), fails)
    print(f"pages checked: {n}; generator self-tests: {ran}; forbidden patterns: {len(FORBIDDEN)}")
    if fails:
        print(f"\nFAIL: {len(fails)} problem(s)")
        for f in fails:
            print(f"    {f}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
