#!/usr/bin/env python3
"""Lead-path integrity gate.

Checks that every lead field on the site sits in a form that can send it,
that success copy appears only where a submission path exists, and that
pages carry no unmeasured response-time or immediacy wording, no phone link
that shows one number and dials another, no link to a dead IDX account URL
and no calculator link to a redirect page. Other gates do not cover these:
test_compliance_gates.py checks claim language, test_phone_consistency.py
checks tel: hrefs, the sitemap gate checks eligibility.

THE CHECKS (each prints its own section; exit 1 if any FAILS)
---------------------------------------------------------------
L1 LEAD FIELD OUTSIDE A WORKING FORM                              (baselined)
   A name / email / phone / message field that is not inside a form that can
   send it. "Working" means one of:
     W1 method=POST to https://formsubmit.co/<address>   (native post)
     W2 data-gre-form with a FormSubmit action that js/main.js accepts
        (https://formsubmit.co/<address>, not .../ajax/...), on a page that
        loads /js/main.js, whose data-gre-form handler reaches the send path
     W3 onsubmit="fn(...)" and an inline function fn that reaches a sink
     W4 the form id is bound by a script on the page that has a submit
        listener and reaches a sink
     W5 method=GET to a same-site page that itself has a working lead form
   Sinks: fetch, XMLHttpRequest, sendBeacon, greForm.send, mailto:,
   formsubmit.co, form.submit(). A native FormSubmit form whose same-site
   _next target does not exist is NOT working (the visitor lands on a 404).
L2 SUCCESS COPY WITHOUT A SUBMISSION PATH                       (no baseline)
   (a) a script that handles submit, cancels it, shows success copy, and
       reaches no sink -- the "fake thank-you"
   (b) success copy in the visible page on a page with no working form that
       no form names as its _next landing page
   (c) js/main.js: the data-gre-form submit handler cancels the submit but
       does not call greForm.send / fetch, or greForm.send reaches neither
       fetch nor XMLHttpRequest
L3 RESPONSE-TIME OR IMMEDIACY PROMISE WITHOUT A MEASURED SOURCE  (baselined)
   "we respond within N hours", "same-day response", "instant alerts",
   "the moment a new home hits the MLS", "notified the moment ... becomes
   available", "first to know", an email / notification / alert "within
   minutes", "24/7 support" ... in visible text or
   JSON-LD. A phrase passes only if MEASURED_SOURCES names it with a source,
   a retrieval date and a measured period.
L4 PHONE LINK DISPLAYS ONE NUMBER AND DIALS / TEXTS ANOTHER      (baselined)
   tel: and sms: anchors. The tel: baseline IS test_phone_consistency.BASELINE
   -- imported, not copied, so the two gates cannot drift. sms: has its own
   baseline.
L5 LINK TO A DEAD IDX ACCOUNT URL                               (no baseline)
   Any reference, in any text file under the root, to an IDX-subdomain path
   recorded in DEAD_IDX_PATHS (each with its HTTP status, the date it was
   checked and the working replacement). Host and path match case-insensitively.
L6 CALCULATOR LINK TO A REDIRECT STUB                            (baselined)
   An anchor whose text says "calculator" and whose target is a meta-refresh
   redirect page. Baselined per link ("<page> -> <target>"), not per count.
G  GENERATORS (scripts/, excluding scripts/dgp/)                (no baseline)
   No generator may carry an L3 phrase or an L5 dead path. The pages are
   scanned too.

BASELINES only shrink. A file not in a baseline, or a baselined file whose
count goes UP, fails. Entries that stop firing are printed as CLEARED so the
baseline gets trimmed. Do not add entries to make the gate pass.

Run:  python3 scripts/dgp/test_lead_path_integrity.py          (exit 0 / 1)
      python3 scripts/dgp/test_lead_path_integrity.py --list   (every finding)
      python3 scripts/dgp/test_lead_path_integrity.py --emit-baseline
Reads the working tree (or --root DIR) and writes nothing. Built-in fixtures
run first on every invocation; a detector that stops detecting fails the gate.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

_spec = importlib.util.spec_from_file_location("phone_gate", HERE / "test_phone_consistency.py")
phone_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(phone_gate)

SKIP_DIRS = {".git", "node_modules", "audit_exports", ".claude", "ai-monitoring"}
TEXT_SUFFIXES = {".html", ".htm", ".js", ".mjs", ".py", ".json", ".txt", ".xml", ".md", ".yml", ".yaml"}
SITE = "https://gadurarealestate.com"

# ---------------------------------------------------------------- registries
# L5. Each entry: HTTP status by GET, when, and the working replacement.
DEAD_IDX_PATHS: dict[str, str] = {
    "/idx/useraccount/newaccount":
        "HTTP 404 'Requested URL Does Not Exist' by GET 2026-11-17T18:47:59Z; "
        "working sign-up: /idx/usersignup.php (HTTP 200, 'User Signup')",
    "/idx/useraccount/userlogin":
        "HTTP 404 by GET 2026-11-17T18:47:59Z; "
        "working login: /idx/userlogin.php (HTTP 200, 'Existing Users')",
}
IDX_HOST = "homes.gadurarealestate.com"

# L3. A phrase is allowed only with all three fields filled from a measured
# record. Key = lower-case phrase.
MEASURED_SOURCES: dict[str, dict[str, str]] = {
    # "we respond within 2 hours": {"source": "...", "retrieved": "YYYY-MM-DD",
    #                               "period": "YYYY-MM-DD..YYYY-MM-DD"},
}

# L1. Baseline: lead fields outside a working form, per file. Seller pages,
# pending owner decision. Recorded 2026-11-17.
L1_BASELINE: dict[str, int] = {
    "sell/index.html": 3,
    "seller-leads/expired-listings-queens.html": 3,
    "seller-leads/fsbo-queens.html": 2,
    "seller-leads/index.html": 3,
    "seller-leads/sell-home-fast-brooklyn.html": 3,
    "seller-leads/sell-home-fast-long-island.html": 3,
    "seller-leads/sell-home-fast-queens.html": 3,
    "seller-leads/why-isnt-my-home-selling.html": 3,
}
# Operator tools that are noindex and not a visitor lead path. The exemption
# lapses automatically if the page loses its noindex.
L1_EXEMPT: dict[str, str] = {
    "admin/index.html": "operator tool; edits listing data, not a visitor inquiry",
}

# L3. Baseline: wording with no measured source, per file, outside this
# change set. Each group is pending owner decision.
L3_BASELINE: dict[str, int] = {
    # Policy page wording.
    "accessibility.html": 1,
    # Service page wording.
    "services/property-management.html": 1,
    # Listing-alert wording. Counts for for-sale/, jeevanpreet-singh/ and
    # index.html include "first to know" / "notified immediately" wording,
    # first measured 2026-11-18.
    "faq/index.html": 3,
    "first-time-buyer-guide/index.html": 2,
    "for-sale/index.html": 3,
    "blog/open-houses-queens-ny.html": 1,
    "index.html": 1,
    "jagman-dhaliwal/index.html": 2,
    "jeevanpreet-singh/index.html": 3,
    # Price-band page copy.
    "homes-for-sale/homes-1m-to-1-5m-in-brooklyn.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-jamaica-estates.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-jamaica.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-long-island.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-nassau-county.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-ozone-park.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-queens-long-island.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-queens.html": 1,
    "homes-for-sale/homes-1m-to-1-5m-in-richmond-hill.html": 1,
    "homes-for-sale/homes-500k-to-750k-in-elmont.html": 1,
    "homes-for-sale/homes-500k-to-750k-in-long-island.html": 1,
    "homes-for-sale/homes-500k-to-750k-in-nassau-county.html": 1,
    "homes-for-sale/homes-500k-to-750k-in-queens-long-island.html": 1,
    "homes-for-sale/homes-500k-to-750k-in-queens.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-brooklyn.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-elmont.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-jamaica.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-long-island.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-nassau-county.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-ozone-park.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-queens-long-island.html": 1,
    "homes-for-sale/homes-750k-to-1m-in-queens.html": 1,
    "homes-for-sale/homes-over-1-5m-in-jamaica-estates.html": 1,
    "homes-for-sale/homes-over-1-5m-in-jamaica.html": 1,
    "homes-for-sale/homes-over-1-5m-in-queens-long-island.html": 1,
    "homes-for-sale/homes-over-1-5m-in-queens.html": 1,
}


# L6. Baseline: calculator links to redirect pages outside this change set
# (home-equity calculator page; pending follow-up).
L6_BASELINE: dict[str, int] = {
    "home-value/free-cma-queens.html -> home-value/home-equity-calculator.html": 1,
    "services/index.html -> home-value/home-equity-calculator.html": 1,
}

# sms: anchors that show one business line and text the other; pending the
# same decision as the tel: baseline. First measured 2026-11-17.
SMS_BASELINE: dict[str, int] = {
    "market-reports/queens/ozone-park-11416/2024/index.html": 1,
    "market-reports/queens/ozone-park-11416/2026-04/index.html": 1,
    "market-reports/queens/richmond-hill-11418/2026-04/index.html": 1,
}

# ---------------------------------------------------------------- patterns
LEAD_NAME = re.compile(
    r"(?:^|[_\-\s\[])(?:name|fname|lname|first[_-]?name|last[_-]?name|full[_-]?name|"
    r"email|e-mail|phone|tel|telephone|mobile|cell|message|comments?)(?:$|[_\-\s\]])", re.I)
LEAD_AUTOCOMPLETE = {"name", "given-name", "family-name", "email", "tel", "tel-national"}
NON_LEAD_INPUT = {"hidden", "submit", "button", "search", "checkbox", "radio", "range",
                  "reset", "image", "file", "number", "date", "color", "url", "password"}
SINK = re.compile(r"fetch\s*\(|XMLHttpRequest|sendBeacon|greForm\.send|mailto:|formsubmit\.co|"
                  r"\.submit\s*\(\s*\)|\.requestSubmit\s*\(", re.I)
SUBMIT_MARK = re.compile(r"addEventListener\(\s*['\"]submit['\"]|\.onsubmit\s*=|on:submit", re.I)
SUCCESS = re.compile(
    r"thank(?:s| you)[\s,.!]*(?:for (?:your|contacting|reaching|submitting)|[-—–:]? ?(?:we|your|nitin))|"
    r"your (?:request|message|inquiry|enquiry|information|details|submission) "
    r"(?:has been|was|is) (?:sent|received|submitted|delivered)|"
    r"we(?:'ve| have) (?:received|got) your|successfully (?:sent|submitted)|"
    r"\b(?:message|request|form) (?:sent|submitted)[.!]|we(?:'ll| will) be in touch", re.I)
_N = r"(?:\d+|one|two|three|an?|a few|24|48|72)"
_UNIT = r"(?:minutes?|mins?|hours?|hrs?|business[- ]days?|days?)"
PROMISES = [
    re.compile(r"\b(?:we|i|nitin|our (?:team|office|agents?)|an agent|someone)\b(?:'ll| will| usually| typically| always| can)?"
               r"\s+(?:respond|reply|call you(?: back)?|get back to you|contact you|follow up|be in touch|reach out|text you)"
               r"\b[^.<>]{0,40}?\b(?:within|in under|in less than|under)\s+" + _N + r"[\s-]*" + _UNIT + r"\b", re.I),
    re.compile(r"\b(?:response|reply|callback|call-back|turnaround)(?: time)?\s+(?:of|within|in|under)\s+(?:about\s+)?"
               + _N + r"[\s-]*" + _UNIT + r"\b", re.I),
    re.compile(r"\bsame[- ]day (?:response|reply|call ?back|callback|answer)", re.I),
    re.compile(r"\b(?:instant|immediate)(?:ly)?\s+(?:e-?mail\s+|mls\s+|listing\s+)?"
               r"(?:alerts?|responses?|repl(?:y|ies)|notifications?|call ?backs?|answers?|updates?)\b", re.I),
    re.compile(r"\bthe (?:moment|minute|second|instant)\b[^.<>]{0,40}?\b(?:hits?|lists?|is listed|enters?|comes? on|"
               r"becomes? available|goes? live|is posted)\b", re.I),
    re.compile(r"\bnotified\b[^.<>]{0,20}?\b(?:the (?:moment|minute|second|instant)|as soon as|immediately|instantly|"
               r"right away)\b", re.I),
    re.compile(r"\bfirst to (?:know|hear)\b", re.I),
    re.compile(r"\b(?:e-?mails?|notifications?|alerts?|notices?|texts?)\b[^.<>]{0,60}?\bwithin (?:minutes|seconds|"
               r"the hour|an hour)\b|\bwithin (?:minutes|seconds)\b[^.<>]{0,40}?\b(?:e-?mails?|notifications?|"
               r"notified|alerts?|alerted)\b", re.I),
    re.compile(r"\b24/7 (?:maintenance|support|service|response|availability|access)\b|"
               r"\b(?:available|reachable|answering|on call) 24/7\b", re.I),
]
# js/main.js sends a data-gre-form form only when its action starts with
# https://formsubmit.co/ and not with https://formsubmit.co/ajax/.
GRE_ACTION = re.compile(r"^https://formsubmit\.co/(?!ajax/)\S+$")
GRE_SELECTOR = re.compile(r"""querySelectorAll\(\s*['"][^'"]*\[data-gre-form\][^'"]*['"]\s*\)""")
SEND_PATH = re.compile(r"greForm\.send\s*\(|\bfetch\s*\(|XMLHttpRequest|sendBeacon")
NET_CALL = re.compile(r"\bfetch\s*\(|XMLHttpRequest|sendBeacon")
CALC_WORD = re.compile(r"calculator", re.I)
REFRESH = re.compile(r"<meta[^>]+http-equiv=[\"']refresh[\"'][^>]*content=[\"']\s*0", re.I)
NOINDEX = re.compile(r"<meta[^>]+name=[\"']robots[\"'][^>]*noindex", re.I)
SCRIPT_BLOCK = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
STYLE_BLOCK = re.compile(r"<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
COMMENT = re.compile(r"<!--.*?-->", re.S)
SMS_ANCHOR = re.compile(r'<a\b[^>]*href=["\']sms:([^"\'?&]*)[^"\']*["\'][^>]*>(.*?)</a>', re.I | re.S)
ANCHOR = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.I | re.S)
HREF = re.compile(r'href=["\']([^"\']*)["\']', re.I)


# ---------------------------------------------------------------- parsing
class PageScan(HTMLParser):
    """Forms, lead fields (with their form), and nothing else."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, str]] = []
        self.fields: list[dict] = []
        self._stack: list[int] = []
        self._template = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "template":
            self._template += 1
        elif tag == "form":
            self.forms.append(a)
            self._stack.append(len(self.forms) - 1)
        elif tag in ("input", "textarea") and not self._template:
            t = (a.get("type") or "text").lower()
            if tag == "input" and t in NON_LEAD_INPUT:
                return
            names = " ".join([a.get("name", ""), a.get("id", "")])
            lead = (tag == "textarea" or t in ("email", "tel")
                    or bool(LEAD_NAME.search(" " + names + " "))
                    or a.get("autocomplete", "").lower() in LEAD_AUTOCOMPLETE)
            if a.get("name", "").lower() in ("_honey", "_gotcha"):
                lead = False
            if lead:
                self.fields.append({"form": self._stack[-1] if self._stack else None,
                                    "form_attr": a.get("form", ""), "name": a.get("name", "")})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "form" and self._stack:
            self._stack.pop()
        elif tag == "template" and self._template:
            self._template -= 1


def inline_scripts(html: str) -> list[str]:
    return [body for attrs, body in SCRIPT_BLOCK.findall(html)
            if "src=" not in attrs.lower() and "ld+json" not in attrs.lower()]


def script_srcs(html: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']', html, re.I)]


def visible_text(html: str) -> str:
    t = COMMENT.sub(" ", html)
    t = SCRIPT_BLOCK.sub(" ", t)
    t = STYLE_BLOCK.sub(" ", t)
    t = TAG.sub(" ", t)
    t = t.replace("&nbsp;", " ").replace("&#39;", "'").replace("&rsquo;", "'").replace("&amp;", "&")
    return re.sub(r"\s+", " ", t)


def jsonld_text(html: str) -> str:
    return " ".join(body for attrs, body in SCRIPT_BLOCK.findall(html) if "ld+json" in attrs.lower())


def function_body(code: str, name: str) -> str:
    m = re.search(r"function\s+" + re.escape(name) + r"\s*\(", code)
    if not m:
        m = re.search(r"\b" + re.escape(name) + r"\s*[:=]\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>)", code)
    if not m:
        return ""
    return block_at(code, code.find("{", m.end()))


def block_at(code: str, i: int) -> str:
    """The brace-balanced block starting at code[i] == '{' (bounded)."""
    if i < 0:
        return ""
    depth = 0
    for j in range(i, min(len(code), i + 20000)):
        if code[j] == "{":
            depth += 1
        elif code[j] == "}":
            depth -= 1
            if depth == 0:
                return code[i:j + 1]
    return code[i:i + 20000]


def strip_js_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
    return re.sub(r"(?<![:'\"\\/])//[^\n]*", " ", code)


def gre_handler_status(main_js: str) -> dict:
    """How js/main.js treats forms marked data-gre-form.

    handler: the body of the callback that main.js runs for each
    form[data-gre-form] (None if there is none). ok: the handler adds a
    submit listener and reaches the send path (greForm.send / fetch / XHR),
    and greForm.send, if called, itself reaches fetch or XMLHttpRequest."""
    code = strip_js_comments(main_js)
    m = GRE_SELECTOR.search(code)
    if not m:
        return {"handler": None, "ok": False, "reason": "js/main.js has no data-gre-form handler"}
    body = block_at(code, code.find("{", m.end()))
    if not SUBMIT_MARK.search(body):
        return {"handler": body, "ok": False, "reason": "data-gre-form handler adds no submit listener"}
    if not SEND_PATH.search(body):
        cancels = "preventDefault" in body
        return {"handler": body, "ok": False, "cancels": cancels,
                "reason": "data-gre-form handler " + ("cancels the submit and " if cancels else "")
                          + "does not call greForm.send / fetch"
                          + (" (shows success copy)" if SUCCESS.search(body) else "")}
    if re.search(r"greForm\.send\s*\(", body) and not NET_CALL.search(body):
        send = function_body(code, "send")
        if not NET_CALL.search(send):
            return {"handler": body, "ok": False, "cancels": "preventDefault" in body,
                    "reason": "greForm.send reaches neither fetch nor XMLHttpRequest"}
    return {"handler": body, "ok": True, "reason": "data-gre-form handler reaches the send path"}


def resolve(rel_page: str, href: str) -> str | None:
    """Same-site href -> repo-relative file path (or None if off-site)."""
    h = href.strip()
    if h.startswith(SITE):
        h = h[len(SITE):] or "/"
    if not h or h.startswith(("http:", "https:", "mailto:", "tel:", "sms:", "#", "javascript:", "//")):
        return None
    h = h.split("#")[0].split("?")[0]
    if h.startswith("/"):
        p = pathlib.PurePosixPath(h.lstrip("/"))
    else:
        p = pathlib.PurePosixPath(rel_page).parent / h
    parts: list[str] = []
    for part in p.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    s = "/".join(parts)
    if s == "" or h.endswith("/"):
        return (s + "/index.html").lstrip("/")
    if not re.search(r"\.[A-Za-z0-9]{2,5}$", s):
        return s + "/index.html"
    return s


# ---------------------------------------------------------------- the model
class Site:
    def __init__(self, root: pathlib.Path, files: dict[str, str] | None = None) -> None:
        self.root = root
        if files is None:
            files = {}
            for p in root.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                rel = p.relative_to(root)
                if any(part in SKIP_DIRS for part in rel.parts):
                    continue
                files[rel.as_posix()] = p.read_text(encoding="utf-8", errors="replace")
        self.files = files
        self.html = {k: v for k, v in files.items() if k.endswith((".html", ".htm"))}
        self.main_js = files.get("js/main.js", "")
        self.gre = gre_handler_status(self.main_js)
        self._scan: dict[str, PageScan] = {}
        self._working: dict[str, list[tuple[bool, str]]] = {}
        self.next_targets = self._next_targets()

    def scan(self, rel: str) -> PageScan:
        if rel not in self._scan:
            ps = PageScan()
            try:
                ps.feed(self.html[rel])
            except Exception:  # malformed markup: keep what was parsed
                pass
            self._scan[rel] = ps
        return self._scan[rel]

    def _next_targets(self) -> set[str]:
        out = set()
        rx = re.compile(r'name=["\']_next["\'][^>]*value=["\']([^"\']+)["\']|'
                        r'value=["\']([^"\']+)["\'][^>]*name=["\']_next["\']', re.I)
        for rel, html in self.html.items():
            for a, b in rx.findall(html):
                tgt = resolve(rel, a or b)
                if tgt:
                    out.add(tgt)
        return out

    def loads_main_js(self, html: str) -> bool:
        return any(re.search(r"(?:^|/)js/main\.js(?:\?|$)", s) for s in script_srcs(html))

    def form_working(self, rel: str, idx: int, depth: int = 0) -> tuple[bool, str]:
        html = self.html[rel]
        form = self.scan(rel).forms[idx]
        raw_action = form.get("action", "")
        action = raw_action.strip()
        method = (form.get("method") or "get").strip().lower()
        scripts = inline_scripts(html)
        fid = form.get("id", "")
        if method == "post" and re.match(r"^https://formsubmit\.co/[^/\s]+$", action):
            nxt = re.search(r'name=["\']_next["\'][^>]*value=["\']([^"\']+)["\']', self._form_html(rel, idx))
            if nxt:
                tgt = resolve(rel, nxt.group(1))
                if tgt and tgt not in self.html:
                    return False, f"W1 native post, but _next {nxt.group(1)} does not exist"
            return True, "W1 native FormSubmit post"
        if "data-gre-form" in form and self.loads_main_js(html):
            if not GRE_ACTION.match(raw_action):
                return False, f"data-gre-form, but js/main.js skips action {raw_action or '(none)'}"
            if not self.gre["ok"]:
                return False, f"data-gre-form, but {self.gre['reason']}"
            return True, "W2 data-gre-form + FormSubmit action + /js/main.js handler"
        m = re.match(r"\s*(?:return\s+)?([A-Za-z_$][\w$]*)\s*\(", form.get("onsubmit", ""))
        if m:
            body = "".join(function_body(s, m.group(1)) for s in scripts)
            if SINK.search(body):
                return True, f"W3 onsubmit={m.group(1)}() reaches a sink"
        if fid:
            id_rx = re.compile(r"getElementById\(\s*['\"]" + re.escape(fid) + r"['\"]\s*\)|"
                               r"querySelector(?:All)?\(\s*['\"]#" + re.escape(fid) + r"\b")
            pools = list(scripts) + ([self.main_js] if self.loads_main_js(html) else [])
            for code in pools:
                if id_rx.search(code) and SUBMIT_MARK.search(code) and SINK.search(code):
                    return True, f"W4 #{fid} bound by a script with a submit listener and a sink"
        if method == "get" and depth == 0:
            tgt = resolve(rel, action) if action else None
            if tgt and tgt in self.html and tgt != rel:
                ps = self.scan(tgt)
                for j in range(len(ps.forms)):
                    if any(f["form"] == j for f in ps.fields) and self.form_working(tgt, j, 1)[0]:
                        return True, f"W5 GET hand-off to {tgt}, which has a working lead form"
        return False, f"no submission path (method={method}, action={action or '(none)'}, id={fid or '(none)'})"

    def _form_html(self, rel: str, idx: int) -> str:
        # Same order as PageScan: comments and script bodies hold no parsed forms.
        html = SCRIPT_BLOCK.sub(" ", COMMENT.sub(" ", self.html[rel]))
        starts = [m.start() for m in re.finditer(r"<form\b", html, re.I)]
        if idx >= len(starts):
            return ""
        end = html.find("</form>", starts[idx])
        return html[starts[idx]: end if end > 0 else len(html)]

    def working(self, rel: str) -> list[tuple[bool, str]]:
        if rel not in self._working:
            self._working[rel] = [self.form_working(rel, i) for i in range(len(self.scan(rel).forms))]
        return self._working[rel]


# ---------------------------------------------------------------- checks
def check_l1(site: Site) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for rel, html in site.html.items():
        ps = site.scan(rel)
        if not ps.fields:
            continue
        if rel in L1_EXEMPT and NOINDEX.search(html):
            continue
        ids = {f.get("id"): i for i, f in enumerate(ps.forms) if f.get("id")}
        work = site.working(rel)
        for fld in ps.fields:
            idx = fld["form"] if fld["form"] is not None else ids.get(fld["form_attr"])
            if idx is None:
                out[rel].append(f"field '{fld['name'] or '?'}' is outside any <form>")
            elif not work[idx][0]:
                out[rel].append(f"field '{fld['name'] or '?'}' in form #{idx}: {work[idx][1]}")
    return dict(out)


def _fake_success(code: str) -> bool:
    if not (SUBMIT_MARK.search(code) and "preventDefault" in code and SUCCESS.search(code)):
        return False
    return not SINK.search(code)


def check_l2(site: Site) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for rel, code in site.files.items():
        if rel.startswith("js/") and rel.endswith(".js") and _fake_success(code):
            out[rel].append("script handles submit, cancels it, shows success copy, reaches no sink")
    if site.gre["handler"] is not None and not site.gre["ok"] and site.gre.get("cancels"):
        out["js/main.js"].append(site.gre["reason"])
    for rel, html in site.html.items():
        for n, code in enumerate(inline_scripts(html)):
            if _fake_success(code):
                out[rel].append(f"inline script #{n} handles submit, cancels it, shows success copy, reaches no sink")
        for fm in re.finditer(r'onsubmit=["\']\s*(?:return\s+)?([A-Za-z_$][\w$]*)\s*\(', html, re.I):
            body = "".join(function_body(s, fm.group(1)) for s in inline_scripts(html))
            if body and "preventDefault" in html and SUCCESS.search(body) and not SINK.search(body):
                out[rel].append(f"onsubmit={fm.group(1)}() shows success copy and reaches no sink")
        m = SUCCESS.search(visible_text(html))
        if m and rel not in site.next_targets and not any(ok for ok, _ in site.working(rel)):
            out[rel].append(f"success copy '{m.group(0)[:60]}' on a page with no working form "
                            f"that no form names as its _next")
    return dict(out)


def promises_in(text: str) -> list[str]:
    hits = []
    for rx in PROMISES:
        for m in rx.finditer(text):
            phrase = re.sub(r"\s+", " ", m.group(0)).strip()
            if phrase.lower() in MEASURED_SOURCES and _measured(MEASURED_SOURCES[phrase.lower()]):
                continue
            hits.append(phrase)
    return hits


def _measured(entry: dict[str, str]) -> bool:
    return all(entry.get(k, "").strip() for k in ("source", "retrieved", "period"))


def check_l3(site: Site) -> dict[str, list[str]]:
    out = {}
    for rel, html in site.html.items():
        hits = promises_in(visible_text(html)) + promises_in(jsonld_text(html))
        if hits:
            out[rel] = hits
    return out


def check_l4(site: Site) -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    tel: dict[str, list[tuple[str, str]]] = defaultdict(list)
    sms: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel, html in site.html.items():
        for rx, bucket in ((phone_gate.ANCHOR, tel), (SMS_ANCHOR, sms)):
            for href, inner in rx.findall(html):
                shown = phone_gate.PHONE_IN_TEXT.search(TAG.sub(" ", inner))
                if not shown:
                    continue
                displayed = phone_gate.digits("".join(shown.groups()))
                dialed = phone_gate.digits(href)
                if displayed != dialed:
                    bucket[rel].append((displayed, dialed))
    return dict(tel), dict(sms)


def check_l5(site: Site) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    me = "scripts/dgp/" + pathlib.Path(__file__).name
    for rel, text in site.files.items():
        if rel == me:
            continue
        for path in DEAD_IDX_PATHS:
            for m in re.finditer(re.escape(IDX_HOST) + r"[^\s\"'<>]*?" + re.escape(path), text, re.I):
                out[rel].append(path)
    return dict(out)


def check_l6(site: Site) -> dict[str, list[str]]:
    stubs = {rel for rel, html in site.html.items() if REFRESH.search(html[:20000])}
    out: dict[str, list[str]] = defaultdict(list)
    for rel, html in site.html.items():
        for attrs, inner in ANCHOR.findall(COMMENT.sub(" ", html)):
            if not CALC_WORD.search(TAG.sub(" ", inner)):
                continue
            h = HREF.search(attrs)
            tgt = resolve(rel, h.group(1)) if h else None
            if tgt and tgt in stubs:
                label = re.sub(r"\s+", " ", TAG.sub(" ", inner)).strip()[:60]
                out[f"{rel} -> {tgt}"].append(f"'{label}' (redirect page)")
    return dict(out)


def check_generators(site: Site) -> list[str]:
    out = []
    for rel, text in site.files.items():
        if not rel.startswith("scripts/") or rel.startswith("scripts/dgp/"):
            continue
        if not rel.endswith((".py", ".js", ".mjs")):
            continue
        for phrase in promises_in(text):
            out.append(f"{rel}: promise '{phrase[:70]}'")
        for path in DEAD_IDX_PATHS:
            if path.lower() in text.lower():
                out.append(f"{rel}: dead IDX path {path}")
    return out


# ---------------------------------------------------------------- reporting
def compare(found: dict[str, list], baseline: dict[str, int]) -> tuple[list[str], list[tuple[str, int, int]], list[str], int]:
    new = sorted(r for r in found if r not in baseline)
    worse = sorted((r, baseline[r], len(found[r])) for r in found if r in baseline and len(found[r]) > baseline[r])
    cleared = sorted(r for r in baseline if r not in found)
    outstanding = sum(len(found[r]) for r in found if r in baseline and len(found[r]) <= baseline[r])
    return new, worse, cleared, outstanding


def section(name: str, found: dict[str, list], baseline: dict[str, int] | None,
            failures: list[str], verbose: bool, why: str = "") -> None:
    total = sum(len(v) for v in found.values())
    if baseline is None:
        if found:
            print(f"\nFAIL {name}: {total} finding(s) in {len(found)} file(s)")
            for rel in sorted(found)[: (None if verbose else 15)]:
                for item in found[rel][: (None if verbose else 3)]:
                    print(f"    {rel}: {item}")
            failures.append(f"{name}: {total}")
        else:
            print(f"\nok   {name}: 0 findings")
        return
    new, worse, cleared, outstanding = compare(found, baseline)
    if new or worse:
        print(f"\nFAIL {name}: {len(new)} un-baselined file(s), {len(worse)} baselined file(s) got worse")
        for rel in new[: (None if verbose else 15)]:
            for item in found[rel][: (None if verbose else 3)]:
                print(f"    NEW  {rel}: {item}")
        for rel, allowed, now in worse:
            print(f"    WORSE {rel}: baseline {allowed} -> {now}")
        failures.append(f"{name}: {len(new)} new file(s), {len(worse)} worse")
    else:
        print(f"\nok   {name}: no new findings")
    if outstanding:
        print(f"     OUTSTANDING (baselined{': ' + why if why else ''}): {outstanding} in "
              f"{len([r for r in found if r in baseline])} file(s)")
        if verbose:
            for rel in sorted(r for r in found if r in baseline):
                for item in found[rel]:
                    print(f"       {rel}: {item}")
    if cleared:
        print(f"     CLEARED - remove from baseline: {', '.join(cleared)}")


def run(site: Site, verbose: bool = False, emit: bool = False) -> int:
    l1, l2, l3 = check_l1(site), check_l2(site), check_l3(site)
    tel, sms = check_l4(site)
    l5, l6, gen = check_l5(site), check_l6(site), check_generators(site)
    if emit:
        for name, found in (("L1_BASELINE", l1), ("L3_BASELINE", l3), ("L6_BASELINE", l6), ("SMS_BASELINE", sms)):
            print(f"{name}: dict[str, int] = {{")
            for rel in sorted(found):
                print(f"    {rel!r}: {len(found[rel])},")
            print("}")
        return 0
    print("=== lead-path integrity gate ===")
    print(f"html files: {len(site.html)}   forms: {sum(len(site.scan(r).forms) for r in site.html)}   "
          f"lead fields: {sum(len(site.scan(r).fields) for r in site.html)}")
    failures: list[str] = []
    section("L1 lead field outside a working form", l1, L1_BASELINE, failures, verbose,
            "seller pages, pending owner decision")
    section("L2 success copy without a submission path", l2, None, failures, verbose)
    section("L3 response/immediacy promise without a measured source", l3, L3_BASELINE, failures, verbose,
            "pending owner decision; see L3_BASELINE")
    tel_fmt = {r: [f"shows {phone_gate.pretty(a)} dials {phone_gate.pretty(b)}" for a, b in v] for r, v in tel.items()}
    sms_fmt = {r: [f"shows {phone_gate.pretty(a)} texts {phone_gate.pretty(b)}" for a, b in v] for r, v in sms.items()}
    section("L4 tel: display/dial mismatch", tel_fmt, phone_gate.BASELINE, failures, verbose,
            "same baseline as test_phone_consistency.py, pending owner decision")
    section("L4 sms: display/text mismatch", sms_fmt, SMS_BASELINE, failures, verbose,
            "pending owner decision, as tel:")
    section("L5 link to a dead IDX account URL", l5, None, failures, verbose)
    section("L6 calculator link to a redirect stub", l6, L6_BASELINE, failures, verbose,
            "home-equity calculator redirect page, pending follow-up")
    section("G  generator carries a promise or dead path", {"scripts/": gen} if gen else {}, None, failures, verbose)
    if failures:
        print("\nFAILED: " + "; ".join(failures))
        print("  Fix the page or its generator. Do NOT add entries to a baseline to make this pass.")
        return 1
    print("\nPASS - lead paths: no new defects.")
    return 0


# ---------------------------------------------------------------- fixtures
def _page(body: str, head: str = "") -> str:
    return f"<!doctype html><html><head>{head}</head><body>{body}<script defer src=\"/js/main.js\"></script></body></html>"


FIX_SEND = "var greForm=(function(){function send(f,u,b){fetch(u,{method:'POST',body:b})}return{send:send}})();"
FIX_HANDLER = ("Array.prototype.forEach.call(document.querySelectorAll('form[data-gre-form]'),function(form){"
               "form.addEventListener('submit',function(e){e.preventDefault();BODY})});")
FIX_MAIN = FIX_SEND + FIX_HANDLER.replace("BODY", "greForm.send(form,'u',new FormData(form))")


def selftest() -> list[str]:
    """Each detector must fire on its defect and stay quiet on the repaired shape."""
    fails: list[str] = []

    def site(files: dict[str, str]) -> Site:
        return Site(pathlib.Path("/nonexistent"), dict({"js/main.js": FIX_MAIN}, **files))

    def expect(label: str, got: bool, want: bool) -> None:
        if got != want:
            fails.append(f"fixture {label}: expected {'finding' if want else 'no finding'}")

    inp = '<input type="text" name="name"><input type="email" name="email"><input type="tel" name="phone">'
    expect("L1 fields with no form", "a.html" in check_l1(site({"a.html": _page(inp + "<button>Go</button>")})), True)
    expect("L1 native formsubmit form", "a.html" in check_l1(site({"a.html": _page(
        f'<form action="https://formsubmit.co/x@example.com" method="POST">{inp}</form>')})), False)
    expect("L1 data-gre-form", "a.html" in check_l1(site({"a.html": _page(
        f'<form action="https://formsubmit.co/x@example.com" method="POST" data-gre-form>{inp}</form>')})), False)
    expect("L1 data-gre-form with no FormSubmit action", "a.html" in check_l1(site({"a.html": _page(
        f'<form method="POST" data-gre-form>{inp}</form>')})), True)
    expect("L1 data-gre-form with an ajax/ action", "a.html" in check_l1(site({"a.html": _page(
        f'<form action="https://formsubmit.co/ajax/x@example.com" method="POST" data-gre-form>{inp}</form>')})), True)
    gre_get = f'<form action="https://formsubmit.co/x@example.com" method="get" data-gre-form>{inp}</form>'
    expect("L1 data-gre-form script path (GET + FormSubmit action)",
           "a.html" in check_l1(site({"a.html": _page(gre_get)})), False)
    expect("L1 data-gre-form script path, handler sends nothing", "a.html" in check_l1(site({
        "a.html": _page(gre_get), "js/main.js": FIX_SEND + FIX_HANDLER.replace("BODY", "")})), True)
    expect("L1 form with no action and no script", "a.html" in check_l1(site({"a.html": _page(
        f'<form method="post">{inp}</form>')})), True)
    expect("L1 onsubmit -> mailto", "a.html" in check_l1(site({"a.html": _page(
        f'<form method="post" onsubmit="go(event)">{inp}</form>'
        '<script>function go(e){e.preventDefault();location.href="mailto:x@example.com"}</script>')})), False)
    expect("L1 id bound with fetch", "a.html" in check_l1(site({"a.html": _page(
        f'<form id="f1" method="post">{inp}</form><script>var f=document.getElementById("f1");'
        'f.addEventListener("submit",function(e){e.preventDefault();fetch("https://formsubmit.co/ajax/x")})</script>')})), False)
    expect("L1 native post whose _next is missing", "a.html" in check_l1(site({"a.html": _page(
        f'<form action="https://formsubmit.co/x@example.com" method="POST">'
        f'<input type="hidden" name="_next" value="https://gadurarealestate.com/gone.html">{inp}</form>')})), True)
    expect("L1 GET hand-off to a working form", "a.html" in check_l1(site({
        "a.html": _page('<form action="/b.html" method="get"><input type="text" name="name"></form>'),
        "b.html": _page(f'<form action="https://formsubmit.co/x@example.com" method="POST">{inp}</form>')})), False)
    expect("L1 field attached by form= attribute", "a.html" in check_l1(site({"a.html": _page(
        f'<form id="z" action="https://formsubmit.co/x@example.com" method="POST"></form>'
        '<input type="email" name="email" form="z">')})), False)
    expect("L1 honeypot only", "a.html" in check_l1(site({"a.html": _page('<input type="text" name="_honey">')})), False)

    fake = ('<form id="f2">' + inp + '</form><script>document.getElementById("f2").addEventListener("submit",'
            'function(e){e.preventDefault();this.innerHTML="Thank you! We will be in touch."})</script>')
    expect("L2 fake thank-you script", "a.html" in check_l2(site({"a.html": _page(fake)})), True)
    expect("L2 honest script with fetch", "a.html" in check_l2(site({"a.html": _page(fake.replace(
        'this.innerHTML', 'fetch("https://formsubmit.co/ajax/x");this.innerHTML'))})), False)
    fake_handler = (FIX_SEND + FIX_HANDLER.replace("BODY", "form.innerHTML='Thank you! We will be in touch.'")
                    + "function other(){fetch('y')}")
    expect("L2 main.js data-gre-form handler shows success, sends nothing",
           "js/main.js" in check_l2(site({"js/main.js": fake_handler})), True)
    expect("L2 main.js data-gre-form handler calls greForm.send", "js/main.js" in check_l2(site({})), False)
    expect("L2 main.js greForm.send reaches no fetch", "js/main.js" in check_l2(site({"js/main.js":
        "var greForm=(function(){function send(f){f.innerHTML='Thank you! We will be in touch.'}return{send:send}})();"
        + FIX_HANDLER.replace("BODY", "greForm.send(form)") + "function other(){fetch('y')}"})), True)
    expect("L2 static success copy, no form, not a _next", "a.html" in check_l2(site({"a.html": _page(
        "<p>Your request has been sent.</p>")})), True)
    expect("L2 static success copy on a _next landing page", "t.html" in check_l2(site({
        "t.html": _page("<p>Your request was submitted.</p>"),
        "a.html": _page('<form action="https://formsubmit.co/x@example.com" method="POST">'
                        '<input type="hidden" name="_next" value="https://gadurarealestate.com/t.html">'
                        + inp + "</form>")})), False)

    for text, want in (("We respond within 24 hours.", True), ("We will call you back in under 15 minutes", True),
                       ("Get instant email alerts the moment a new home hits the MLS", True),
                       ("same-day response guaranteed", True), ("24/7 maintenance coordination", True),
                       ("register to be notified the moment a matching home becomes available", True),
                       ("Be the first to know when homes hit the market", True),
                       ("Email notification within minutes of a new listing", True),
                       ("you get an email - usually within minutes", True),
                       ("LIRR and the tunnel are all within minutes.", False),
                       ("The E train runs 24/7.", False), ("Manhattan in 28 minutes by train", False),
                       ("Create a free account to save searches.", False)):
        expect(f"L3 '{text}'", bool(promises_in(text)), want)
    MEASURED_SOURCES["we respond within 24 hours"] = {"source": "call log", "retrieved": "", "period": ""}
    expect("L3 registry entry without dates does not excuse", bool(promises_in("We respond within 24 hours.")), True)
    MEASURED_SOURCES["we respond within 24 hours"] = {"source": "call log", "retrieved": "2026-01-01",
                                                      "period": "2025-10-01..2025-12-31"}
    expect("L3 fully sourced registry entry excuses", bool(promises_in("We respond within 24 hours.")), False)
    del MEASURED_SOURCES["we respond within 24 hours"]

    t, s = check_l4(site({"a.html": _page('<a href="sms:+19175550100">Text (917) 555-0199</a>'
                                         '<a href="tel:+19175550100">(917) 555-0100</a>')}))
    expect("L4 sms mismatch", "a.html" in s, True)
    expect("L4 tel match", "a.html" in t, False)

    expect("L5 dead IDX sign-up", "a.html" in check_l5(site({"a.html": _page(
        f'<a href="https://{IDX_HOST}/idx/useraccount/newaccount">Sign up</a>')})), True)
    expect("L5 dead IDX log-in, other letter case", "a.html" in check_l5(site({"a.html": _page(
        f'<a href="https://{IDX_HOST}/idx/UserAccount/UserLogin">Log in</a>')})), True)
    expect("L5 working IDX sign-up", "a.html" in check_l5(site({"a.html": _page(
        f'<a href="https://{IDX_HOST}/idx/usersignup.php">Sign up</a>')})), False)
    expect("L5 dead path in a generator", bool(check_generators(site({
        "scripts/x.py": f"HTML = '<a href=\"https://{IDX_HOST}/idx/useraccount/newaccount\">'"}))), True)
    expect("G promise in a generator", bool(check_generators(site({
        "scripts/x.py": "COPY = 'We respond within 2 hours'"}))), True)

    stub = '<html><head><meta http-equiv="refresh" content="0;url=/b.html"></head><body></body></html>'
    expect("L6 calculator link to stub", "a.html -> c.html" in check_l6(site({
        "c.html": stub, "a.html": _page('<a href="/c.html">Sell or Rent Calculator</a>')})), True)
    expect("L6 calculator link to real page", bool(check_l6(site({
        "c.html": _page("<h1>Calc</h1>"), "a.html": _page('<a href="/c.html">Mortgage Calculator</a>')}))), False)
    swapped = check_l6(site({"c.html": stub, "d.html": stub,
                             "a.html": _page('<a href="/d.html">Sell or Rent Calculator</a>')}))
    expect("L6 baseline is per link: same count, other target", bool(compare(swapped, {"a.html -> c.html": 1})[0]), True)
    return fails


def main() -> int:
    global ROOT
    args = sys.argv[1:]
    if "--root" in args:
        ROOT = pathlib.Path(args[args.index("--root") + 1]).resolve()
    fx = selftest()
    if fx:
        print("=== lead-path integrity gate: FIXTURES FAILED ===")
        for f in fx:
            print("    " + f)
        return 1
    print("fixtures: all detectors fire on their defect and pass the repaired shape")
    return run(Site(ROOT), verbose="--list" in args, emit="--emit-baseline" in args)


if __name__ == "__main__":
    raise SystemExit(main())
