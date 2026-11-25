#!/usr/bin/env python3
"""Speed-to-lead gate: every FormSubmit form must carry _honey and a live _webhook.

WHY
  FormSubmit emails info@ on each submission, but nobody sees an email in
  time. Each form's `_webhook` points FormSubmit at the gadura-lead-relay
  Worker, which pings Discord #leads. A form without `_webhook` is a lead
  that arrives silently; a form without `_honey` invites bot spam into that
  channel. Pages are hand-edited and copied, so a new page can easily drop
  either field -- this gate catches it.

CHECKS (per <form action="https://formsubmit.co/...">, in tracked *.html)
  1. has an <input name="_honey">
  2. has an <input name="_webhook"> whose value is https://<host>/formsubmit
     with a `k` token and `p` equal to that file's own path
  3. the relay URL is not the PENDING placeholder (release blocker until the
     Worker is deployed and the injector re-run with the real URL)
  plus self-tests of the injector (insertion, idempotency, rewrite).

Run: python3 scripts/dgp/test_formsubmit_lead_relay.py
Exit 0 = pass, 1 = fail.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import inject_lead_relay_fields as inj  # noqa: E402


def self_tests() -> list[str]:
    errs: list[str] = []
    value = inj.webhook_value("https://relay.example/formsubmit", "tok_0123456789abcdef", "/a b.html")
    src = (
        '<div>\n  <form action="https://formsubmit.co/info@gadurarealestate.com" method="POST">\n'
        '    <input type="hidden" name="_captcha" value="false">\n  </form>\n'
        '  <form action="/search"><input name="q"></form>\n</div>\n'
    )
    once, n1 = inj.inject(src, value)
    twice, n2 = inj.inject(once, value)
    if n1 != 1 or once.count('name="_honey"') != 1 or once.count('name="_webhook"') != 1:
        errs.append("self-test: injector did not add exactly one _honey and one _webhook")
    if '<form action="/search"><input name="q"></form>' not in once:
        errs.append("self-test: injector touched a non-FormSubmit form")
    if n2 != 0 or twice != once:
        errs.append("self-test: injector is not idempotent")
    if "\n    <input type=\"text\" name=\"_honey\"" not in once:
        errs.append("self-test: inserted field does not follow the form's indentation")
    other = inj.webhook_value("https://relay2.example/formsubmit", "tok_0123456789abcdef", "/x.html")
    rewritten, n3 = inj.inject(once, other)
    if n3 != 1 or "relay2.example" not in rewritten or rewritten.count('name="_webhook"') != 1:
        errs.append("self-test: injector did not rewrite an existing _webhook in place")
    existing_honey = src.replace('<input type="hidden" name="_captcha"', '<input type="text" name="_honey" style="display:none">\n    <input type="hidden" name="_captcha"')
    kept, _ = inj.inject(existing_honey, value)
    if kept.count('name="_honey"') != 1:
        errs.append("self-test: injector duplicated an existing _honey")
    if "&amp;p=/a%20b.html" not in value:
        errs.append("self-test: _webhook value is not attribute-escaped / path-encoded")
    return errs


def check_site() -> tuple[list[str], list[str], int]:
    errs: list[str] = []
    pending: list[str] = []
    forms = 0
    for rel in inj.tracked_html_files():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "formsubmit.co" not in text:
            continue
        for m in inj.FORM_OPEN_RE.finditer(text):
            forms += 1
            close = inj.FORM_CLOSE_RE.search(text, m.end())
            body = text[m.end(): close.start() if close else len(text)]
            line = text.count("\n", 0, m.start()) + 1
            where = f"{rel}:{line}"
            if not inj.HONEY_RE.search(body):
                errs.append(f"{where}: FormSubmit form has no _honey field")
            w = inj.WEBHOOK_RE.search(body)
            if not w:
                errs.append(f"{where}: FormSubmit form has no _webhook field")
                continue
            url = urlsplit(html.unescape(w.group(2)))
            q = parse_qs(url.query)
            if url.scheme != "https" or url.path != "/formsubmit" or not q.get("k"):
                errs.append(f"{where}: _webhook is not https://<host>/formsubmit?k=...")
            if q.get("p", [""])[0] != inj.page_path_for(rel):
                errs.append(f"{where}: _webhook p= does not match this page's path")
            if url.netloc == urlsplit(inj.PLACEHOLDER_RELAY_URL).netloc or q.get("k", [""])[0] == inj.PLACEHOLDER_TOKEN:
                pending.append(where)
    return errs, pending, forms


def main() -> int:
    errs = self_tests()
    site_errs, pending, forms = check_site()
    errs += site_errs
    print(f"FormSubmit forms scanned: {forms}")
    for e in errs[:50]:
        print(f"FAIL {e}")
    if len(errs) > 50:
        print(f"... and {len(errs) - 50} more")
    if pending:
        print(f"FAIL release blocker: {len(pending)} forms still carry the PENDING relay placeholder "
              f"(first: {pending[0]}). Deploy gadura-lead-relay, then re-run "
              "scripts/inject_lead_relay_fields.py --apply --relay-url ... --token-file ...")
    ok = not errs and not pending
    print("PASS" if ok else f"FAILED ({len(errs)} structural, {len(pending)} placeholder)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
