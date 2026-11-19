#!/usr/bin/env python3
"""Seller contact block gate.

WHAT IT CHECKS (exit 1 if any check fails)
-------------------------------------------
B1 GENERATED   Every page listed in data/seller-contact-block.json carries
               exactly one seller-contact marker pair, and the content between
               the markers is exactly what scripts/build_seller_contact_block.py
               renders from the data file. A hand edit to one page, or a data
               change that was never written out, fails here.
B2 BLOCK RULES The rendered block:
               - has one tel: link; has one sms: link only when the call line
                 is listed in sms_lines (the lines that show a Text action) and
                 none otherwise; each shows the number it dials, and both use
                 the data file's line;
               - has one mailto: link to the data file's inbox;
               - promises no response time and no immediacy (the PROMISES
                 patterns of test_lead_path_integrity.py plus WORDS_TIME);
               - carries no superiority, situation or group wording
                 (WORDS_RANK, WORDS_SITUATION, WORDS_GROUP);
               - carries no figure other than its phone number and "RPL 443";
               - names the brokerage and its licence title, says a CMA is not
                 an appraisal and that there is no obligation;
               - links only to pages that exist; the CMA link points at an
                 element id on its target page that holds a working lead form
                 (same definition as test_lead_path_integrity.py).
B3 REMOVED     Phrases removed from the pages that carry or receive the block
               (GUARDED) stay removed: visible text, meta descriptions and
               JSON-LD are scanned. A regeneration or a merge of an older copy
               that brings one back fails here.
B4 GENERATORS  No script under scripts/ (other than scripts/dgp/) emits a
               GUARDED phrase, so a generator cannot reintroduce it.
F  FIXTURES    Built-in fixtures prove each rule still fails on a defect.

SCOPE
-----
The word lists (WORDS_*, GUARDED, GENERATOR_DENY) are a minimum check, not
a complete one: wording that avoids every listed term can still be wrong
for this block. A change to the block's copy in
data/seller-contact-block.json, or to a guarded page, needs a human review
before release, whatever this gate reports. B3 reads the static HTML of the
guarded pages (visible text, quoted alt / title / aria-label and meta
content values, JSON-LD as written, with character references decoded);
B4 reads scripts/ only. Text added at runtime by other scripts is outside
both.

Run:  python3 scripts/dgp/test_seller_contact_block.py [--root DIR]
Reads the tree and writes nothing. Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import html as html_mod
import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_lead_path_integrity as lp  # noqa: E402

WORDS_TIME = re.compile(
    r"\b(?:within|today|tonight|tomorrow|overnight|asap|right away|immediate(?:ly)?|instant(?:ly)?|quick(?:ly)?|fast|"
    r"same[- ]day|business days?|24/7|hours?|minutes?|soon|promptly|shortly|guaranteed? (?:response|reply|call))\b", re.I)
WORDS_RANK = re.compile(
    r"\b(?:best|top|number one|no\.\s?1|expert|experts|specialists?|trusted|leading|premier|"
    r"unmatched|unbeatable|unrivall?ed|go-to|most experienced|highest[- ]rated|guarantee[ds]?|proven|award\w*)\b"
    r"|(?<![\w#])#\s?1\b", re.I)
WORDS_SITUATION = re.compile(
    r"\b(?:foreclos\w*|probate|inherit\w*|divorc\w*|separat\w*|widow\w*|loved one|executors?|heirs?|estate sale|death|"
    r"deceased|bankrupt\w*|behind on|underwater|liens?|tax arrears|hardship|job loss|evict\w*|distress\w*|downsiz\w*|"
    r"empty[- ]nest\w*|seniors?|retire\w*|relocat\w*|short sale|cash offer|we buy)\b", re.I)
WORDS_GROUP = re.compile(
    r"\b(?:hindi|punjabi|bengali|bangla|urdu|spanish|languages?|bilingual|multilingual|community|"
    r"communities|indian|south asian|caribbean|guyanese|hispanic|latino|desi|famil(?:y|ies)|children|kids|schools?|"
    r"immigra\w*|ethnic\w*|cultur\w*|faith|religio\w*|churche?s?|temples?|mosques?|gurdwaras?|mandirs?|synagogues?)\b",
    re.I)
# Each sample must match its list (checked in the fixtures), so a list edit cannot silently drop a term.
WORD_SAMPLES = [
    ("time", "We reply the same business day"), ("time", "Hear back by tomorrow"),
    ("rank", "Queens' most experienced team"), ("rank", "The #1 choice"), ("rank", "Unbeatable service"),
    ("rank", "Your go-to agent"), ("rank", "Highest-rated in Queens"),
    ("situation", "Lost a loved one?"), ("situation", "Empty nesters"), ("situation", "Underwater on your mortgage?"),
    ("situation", "Going through a separation?"),
    ("group", "Growing family?"), ("group", "Young family"), ("group", "Near the gurdwara"), ("group", "Close to the mosque"),
    ("group", "For immigrant owners"), ("group", "Near good schools"),
]
REQUIRED_TEXT = ("Gadura Real Estate, LLC", "Licensed Real Estate Broker", "not an appraisal", "no obligation")

ANCHOR = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.I | re.S)
HREF = re.compile(r'href=["\']([^"\']*)["\']', re.I)

# Phrases removed from these pages. Patterns, not page snapshots: any copy of
# the old wording, from any source, fails.
GUIDES = [
    r"listing specialists", r"\bExpert (?:advice|guide)\b", r"median sale price", r"days on market",
    r"have appreciated", r"perceived value", r"#1 Mistake", r"1\.825%", r"1\.425%", r"0\.65%",
    r"typically 5[–-]6%", r"\$1,200[–-]\$2,500", r"seller-side costs of approximately",
    r"3 business days", r"32% faster", r"7 seconds", r"We've listed and sold", r"3D tours",
    r"specialist — no obligation", r"Highest-ROI", r"% appreciation", r"downsizing or relocating",
    r"results in a sale price above list", r"families relocating",
]
GUARDED: dict[str, list[str]] = {
    "neighborhoods/ozone-park/selling-guide/index.html": GUIDES,
    "neighborhoods/richmond-hill/selling-guide/index.html": GUIDES,
    "neighborhoods/queens-village/selling-guide/index.html": GUIDES,
    "home-valuation.html": [
        r"\$100M", r"~30 days", r"6 languages", r"under contract within", r"beat the online estimates",
        r"other agents never reach", r"free expert", r"expert CMA", r"expert Comparative",
        r"actually knows your block", r"100% free &(?:amp; )?private", r"100% free & private",
        r"strongest supportable price", r"favor sellers", r"block by block and price",
        r"protects — real dollars", r"prices to win", r"strong offers fast", r"since 2006",
        r"neighbors you can trust",
    ],
}
# Distinctive phrases from the guarded pages that no generator may emit (B4).
# Generic phrases (for example a sales-volume figure) are left to the claim
# gates, which cover every page; this list is about the guarded pages.
GENERATOR_DENY = [
    r"listing specialists", r"1\.825%", r"3 business days in NY", r"most go under contract",
    r"We've listed and sold homes throughout", r"Highest-ROI pre-sale", r"First impressions account for 7 seconds",
]


def load_builder(root: pathlib.Path):
    spec = importlib.util.spec_from_file_location("build_seller_contact_block",
                                                  root / "scripts" / "build_seller_contact_block.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def digits(s: str) -> str:
    d = re.sub(r"\D", "", s)
    return d[1:] if len(d) == 11 and d.startswith("1") else d


def block_text(block: str) -> str:
    return html_mod.unescape(lp.visible_text(block))


def check_block(block: str, data: dict, site_html: dict[str, str] | None, site: "lp.Site | None") -> list[str]:
    errs: list[str] = []
    if "text_enabled" in data or not isinstance(data.get("sms_lines"), list):
        return ["B2 data file: 'sms_lines' (list) is required and 'text_enabled' is not allowed"]
    line = digits(data["phone_tel"])
    tels, smss, mails, internal = [], [], [], []
    for attrs, inner in ANCHOR.findall(block):
        m = HREF.search(attrs)
        if not m:
            continue
        href, shown = m.group(1), lp.TAG.sub(" ", inner)
        if href.startswith("tel:"):
            tels.append((href, shown))
        elif href.startswith("sms:"):
            smss.append((href, shown))
        elif href.startswith("mailto:"):
            mails.append(href)
        elif href.startswith("/"):
            internal.append(href)
        elif not href.startswith("https://"):
            errs.append(f"B2 unexpected link target {href!r}")
    if len(tels) != 1:
        errs.append(f"B2 expected 1 tel: link, found {len(tels)}")
    want_sms = 1 if data["phone_tel"] in data["sms_lines"] else 0
    if len(smss) != want_sms:
        errs.append(f"B2 expected {want_sms} sms: link(s), found {len(smss)}")
    for kind, items in (("tel", tels), ("sms", smss)):
        for href, shown in items:
            dial = digits(href.split(":", 1)[1].split("?")[0])
            seen = lp.phone_gate.PHONE_IN_TEXT.search(shown)
            if dial != line:
                errs.append(f"B2 {kind}: link dials a line other than the data file's")
            if not seen or digits("".join(seen.groups())) != dial:
                errs.append(f"B2 {kind}: link does not show the number it dials")
    if len(mails) != 1 or mails[0].split(":", 1)[1].split("?")[0].lower() != data["email"].lower():
        errs.append("B2 expected exactly one mailto: link to the data file's inbox")
    text = block_text(block)
    for rx in lp.PROMISES:
        for m in rx.finditer(text):
            errs.append(f"B2 response/immediacy promise: {m.group(0)!r}")
    for name, rx in (("time", WORDS_TIME), ("rank", WORDS_RANK), ("situation", WORDS_SITUATION), ("group", WORDS_GROUP)):
        for m in rx.finditer(text):
            errs.append(f"B2 {name} wording: {m.group(0)!r}")
    bare = text.replace(data["phone_display"], " ")
    bare = re.sub(r"RPL\s*§\s*443", " ", bare)
    if re.search(r"\d", bare):
        errs.append(f"B2 figure in block text: {re.findall(r'[^ ]*[0-9][^ ]*', bare)[:3]}")
    for req in REQUIRED_TEXT:
        if req.lower() not in text.lower():
            errs.append(f"B2 missing required text {req!r}")
    if site_html is not None:
        for href in internal:
            path, _, frag = href.partition("#")
            tgt = lp.resolve("index.html", path)
            if not tgt or tgt not in site_html:
                errs.append(f"B2 link target does not exist: {href}")
                continue
            if href == data["cma_href"]:
                errs += check_cma_target(tgt, frag, site_html, site)
    return errs


def check_cma_target(tgt: str, frag: str, site_html: dict[str, str], site: "lp.Site | None") -> list[str]:
    html = site_html[tgt]
    if not frag:
        return [f"B2 CMA link has no #fragment pointing at the form section on {tgt}"]
    m = re.search(r'\bid=["\']' + re.escape(frag) + r'["\']', html)
    if not m:
        return [f"B2 CMA fragment #{frag} not found on {tgt}"]
    clean = lp.SCRIPT_BLOCK.sub(" ", lp.COMMENT.sub(" ", html))
    pos = clean.find(m.group(0))
    starts = [x.start() for x in re.finditer(r"<form\b", clean, re.I)]
    after = [i for i, st in enumerate(starts) if st > pos]
    if not after:
        return [f"B2 no <form> after #{frag} on {tgt}"]
    if site is None:
        return []
    ok, why = site.form_working(tgt, after[0])
    if not ok:
        return [f"B2 CMA form on {tgt} has no submission path: {why}"]
    if not any(f["form"] == after[0] for f in site.scan(tgt).fields):
        return [f"B2 CMA form on {tgt} has no lead fields"]
    return []


# Double-quoted and single-quoted values are read separately (one group each): a double-quoted value may hold
# an apostrophe and a single-quoted one a double quote, and neither ends the value.
META_CONTENT = re.compile(r'<meta\b[^>]*?(?<![\w-])content=(?:"([^"]*)"|\'([^\']*)\')', re.I)
ATTR_TEXT = re.compile(r'\b(?:alt|title|aria-label)=(?:"([^"]*)"|\'([^\']*)\')', re.I)


def page_text(html: str) -> str:
    metas = " ".join(dq + sq for dq, sq in META_CONTENT.findall(html))
    attrs = " ".join(dq + sq for dq, sq in ATTR_TEXT.findall(html))
    text = " ".join((lp.visible_text(html), lp.jsonld_text(html), metas, attrs))
    return re.sub(r"\s+", " ", html_mod.unescape(text).replace("\xa0", " "))


def check_pages(root: pathlib.Path, builder, data: dict, site_html: dict[str, str]) -> list[str]:
    errs = []
    block = builder.render(data)
    for rel in data["pages"]:
        html = site_html.get(rel)
        if html is None:
            errs.append(f"B1 listed page missing: {rel}")
            continue
        try:
            if builder.splice(html, block, rel) != html:
                errs.append(f"B1 block on {rel} differs from the generator output (run the builder with --write)")
        except ValueError as exc:
            errs.append(f"B1 {exc}")
        if html.count('id="seller-contact"') != 1:
            errs.append(f"B1 {rel}: id=seller-contact must appear exactly once")
    return errs


def check_guarded(site_html: dict[str, str], guarded: dict[str, list[str]]) -> list[str]:
    errs = []
    for rel, pats in guarded.items():
        html = site_html.get(rel)
        if html is None:
            errs.append(f"B3 guarded page missing: {rel}")
            continue
        text = page_text(html)
        for pat in pats:
            for m in re.finditer(pat, text, re.I):
                errs.append(f"B3 {rel}: removed phrase is back: {m.group(0)!r}")
    return errs


def check_generators(files: dict[str, str]) -> list[str]:
    errs = []
    for rel, text in files.items():
        if not rel.startswith("scripts/") or rel.startswith("scripts/dgp/"):
            continue
        for pat in GENERATOR_DENY:
            if re.search(pat, text):
                errs.append(f"B4 {rel} emits a removed phrase: /{pat}/")
    return errs


def selftest(builder, data: dict, site_html: dict[str, str], site: "lp.Site") -> list[str]:
    """Each fixture must FAIL; returns the fixtures that did not."""
    misses = []

    def expect_fail(name, d=None, block=None):
        d = d or data
        b = block if block is not None else builder.render(d)
        if not check_block(b, d, site_html, site):
            misses.append(name)

    def mut(**kw):
        d = copy.deepcopy(data)
        d.update(kw)
        return d

    expect_fail("promise in intro", mut(intro=data["intro"] + " We will call you back within 24 hours."))
    expect_fail("immediacy word", mut(intro=data["intro"] + " Get an answer today."))
    expect_fail("rank word", mut(heading="Queens' top listing expert"))
    expect_fail("situation word", mut(intro="Facing foreclosure or probate? Ask us."))
    expect_fail("group word", mut(intro="We serve the Punjabi community."))
    expect_fail("figure", mut(cma_note=data["cma_note"] + " Homes sell in 25 days."))
    expect_fail("no broker title", mut(broker_line="Gadura Real Estate, LLC"))
    expect_fail("no appraisal caveat", mut(cma_note="Free CMA."))
    expect_fail("dead CMA page", mut(cma_href="/no-such-page.html#get-cma"))
    expect_fail("CMA fragment missing", mut(cma_href=data["cma_href"].split("#")[0] + "#nope"))
    expect_fail("CMA without fragment", mut(cma_href=data["cma_href"].split("#")[0]))
    ids = re.findall(r'\bid=["\']([\w-]+)["\']', site_html.get("agency-disclosure.html", ""))
    if ids and not re.search(r"<form\b", site_html["agency-disclosure.html"], re.I):
        expect_fail("CMA page without form", mut(cma_href=f"/agency-disclosure.html#{ids[0]}"))
    else:
        misses.append("CMA page without form (fixture page changed: pick another form-less page)")
    # Text action: fixtures run for both states, whatever the data file holds today.
    d_on, d_off = mut(sms_lines=[data["phone_tel"]]), mut(sms_lines=[])
    on_block = builder.render(d_on)
    if 'href="sms:' not in on_block or 'href="sms:' in builder.render(d_off):
        misses.append("builder does not follow sms_lines (Text must render only for a listed line)")
    expect_fail("sms dials another line", d=d_on, block=on_block.replace(f'sms:{data["phone_tel"]}', "sms:+19995550100", 1))
    expect_fail("text link missing while line listed", d=d_on,
                block=re.sub(r'<li><a [^>]*href="sms:[^>]*>.*?</a></li>\n?', "", on_block))
    expect_fail("text link shown for a line not in sms_lines", d=d_off, block=on_block)
    expect_fail("legacy text_enabled key", d=dict(d_on, text_enabled=True))
    bad = builder.render(data).replace(f'Call {data["phone_display"]}', "Call (999) 555-0100", 1)
    expect_fail("tel shows another number", block=bad)
    expect_fail("second mailto", block=builder.render(data).replace("</ul>", '<li><a href="mailto:x@example.com">x</a></li></ul>', 1))
    # B1 / B3 / B4 fixtures
    rel = data["pages"][0]
    drift = dict(site_html)
    drift[rel] = site_html[rel].replace(data["heading"], data["heading"] + " Today", 1)
    if not check_pages(None, builder, data, drift):
        misses.append("B1 hand-edited block")
    nomark = dict(site_html)
    nomark[rel] = site_html[rel].replace(builder.START, "", 1)
    if not check_pages(None, builder, data, nomark):
        misses.append("B1 missing marker")
    back = dict(site_html)
    back["home-valuation.html"] = site_html["home-valuation.html"].replace("</main>", "<p>$100M+ in sales</p></main>", 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase")
    back = dict(site_html)
    back[rel] = site_html[rel].replace("<h1", '<meta name="description" content="Expert advice from Ozone Park listing specialists"><h1', 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase in meta")
    back = dict(site_html)
    back[rel] = site_html[rel].replace("<h1", "<p>Expert&#160;guide</p><h1", 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase with a character reference")
    back = dict(site_html)
    back[rel] = site_html[rel].replace("<h1", '<img src="/x.png" alt="Our listing specialists"><h1', 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase in an alt attribute")
    # Quoting: an apostrophe inside a double-quoted value, or a double quote inside a single-quoted one, must not
    # end the value before a removed phrase.
    hv = "home-valuation.html"
    back = dict(site_html)
    back[hv] = site_html[hv].replace("</head>", '<meta name="description" content="Your home\'s value: a free expert CMA"></head>', 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase in a meta description after an apostrophe")
    back = dict(site_html)
    back[hv] = site_html[hv].replace("</head>", "<meta name='description' content='A \"free expert\" CMA'></head>", 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase in a single-quoted meta value")
    back = dict(site_html)
    back[rel] = site_html[rel].replace("<h1", '<img src="/x.png" alt="Ozone Park\'s listing specialists"><h1', 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored phrase in an alt attribute after an apostrophe")
    back = dict(site_html)
    back[rel] = site_html[rel].replace("<h1", "<p>The neighborhood attracts first-time buyers, investors, and families "
                                       "relocating from more expensive parts of Queens.</p><h1", 1)
    if not check_guarded(back, GUARDED):
        misses.append("B3 restored guide sentence")
    if not check_generators({"scripts/x.py": "print('Our listing specialists')"}):
        misses.append("B4 generator")
    # Word lists: every sample must match its list, and two of them must also fail the whole block.
    words = {"time": WORDS_TIME, "rank": WORDS_RANK, "situation": WORDS_SITUATION, "group": WORDS_GROUP}
    for kind, sample in WORD_SAMPLES:
        if not words[kind].search(sample):
            misses.append(f"{kind} list does not match {sample!r}")
    expect_fail("group wording (second list)", mut(intro="Growing family? Ask us about your home."))
    expect_fail("situation wording (second list)", mut(intro="Lost a loved one? Ask us about the home."))
    return misses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(HERE.parents[1]))
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    builder = load_builder(root)
    data = json.loads((root / "data" / "seller-contact-block.json").read_text(encoding="utf-8"))
    site = lp.Site(root)
    site_html = site.html
    sections = [
        ("B1 GENERATED", check_pages(root, builder, data, site_html)),
        ("B2 BLOCK RULES", check_block(builder.render(data), data, site_html, site)),
        ("B3 REMOVED", check_guarded(site_html, GUARDED)),
        ("B4 GENERATORS", check_generators(site.files)),
    ]
    misses = selftest(builder, data, site_html, site)
    sections.append(("F FIXTURES (each must fail)", [f"fixture did not fail: {m}" for m in misses]))
    rc = 0
    for name, errs in sections:
        print(f"{name}: {'PASS' if not errs else 'FAIL'}")
        for e in errs:
            print(f"   {e}")
        rc |= bool(errs)
    print(f"pages with the block: {len(data['pages'])}; guarded pages: {len(GUARDED)}; "
          f"guarded phrases: {sum(len(v) for v in GUARDED.values())}")
    print("RESULT:", "PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
