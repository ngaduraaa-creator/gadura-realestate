#!/usr/bin/env python3
"""Build the homeowner contact block from data/seller-contact-block.json.

The block lives between two markers on each page listed in the data file:

    <!-- seller-contact:start -->
    ...generated...
    <!-- seller-contact:end -->

Usage:
    python3 scripts/build_seller_contact_block.py           # check (default): exit 1 on drift
    python3 scripts/build_seller_contact_block.py --write   # rewrite the block on every listed page
    python3 scripts/build_seller_contact_block.py --print   # print the rendered block

A page without exactly one marker pair is an error in both modes: the markers
are placed by hand once, the content between them is always generated.
Standard library only. Reads data/, writes only the listed pages (--write).
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seller-contact-block.json"
E164 = re.compile(r"\+1\d{10}")
START = "<!-- seller-contact:start -->"
END = "<!-- seller-contact:end -->"
REQUIRED = ("version", "heading", "intro", "phone_display", "phone_tel", "sms_lines", "email",
            "email_subject", "cma_href", "cma_label", "cma_note", "process_href", "process_label",
            "broker_line", "disclosure_href", "disclosure_label", "track_clicks", "pages")

STYLE = (
    ".gre-sc{border:2px solid #1B2A6B;border-radius:10px;padding:22px 20px;margin:32px 0;background:#fff;"
    "font-family:inherit;color:#222;line-height:1.55}"
    ".gre-sc h2{color:#1B2A6B;margin:0 0 6px;font-size:1.35rem}"
    ".gre-sc .gre-sc-intro{margin:0 0 16px}"
    ".gre-sc ul{list-style:none;margin:0 0 14px;padding:0;display:flex;flex-wrap:wrap;gap:10px}"
    ".gre-sc li{margin:0}"
    ".gre-sc a.gre-sc-btn{display:inline-block;min-height:44px;box-sizing:border-box;padding:11px 18px;border-radius:6px;"
    "border:2px solid #1B2A6B;color:#1B2A6B;background:#fff;font-weight:700;text-decoration:none}"
    ".gre-sc a.gre-sc-btn.gre-sc-primary{background:#1B2A6B;color:#fff}"
    ".gre-sc a.gre-sc-btn:hover,.gre-sc a.gre-sc-btn:focus-visible{background:#F5A623;border-color:#F5A623;color:#111}"
    ".gre-sc a.gre-sc-btn:focus-visible{outline:3px solid #111;outline-offset:2px}"
    ".gre-sc .gre-sc-fine{font-size:.85rem;color:#444;margin:6px 0 0}"
    ".gre-sc .gre-sc-fine a{color:#1B2A6B}"
    "@media (max-width:480px){.gre-sc ul{flex-direction:column}.gre-sc a.gre-sc-btn{display:block;text-align:center}}"
)

TRACK = (
    "(function(){var b=document.getElementById('seller-contact');if(!b)return;"
    "b.addEventListener('click',function(e){var a=e.target&&e.target.closest?e.target.closest('a[data-sc]'):null;"
    "if(a&&typeof window.gtag==='function'){window.gtag('event','seller_contact_click',"
    "{method:a.getAttribute('data-sc'),block_version:b.getAttribute('data-seller-contact')});}});})();"
)


def load(path: pathlib.Path = DATA) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise SystemExit(f"{path}: missing keys {missing}")
    if not isinstance(data["pages"], list) or not data["pages"]:
        raise SystemExit(f"{path}: 'pages' must be a non-empty list")
    if "text_enabled" in data:
        raise SystemExit(f"{path}: 'text_enabled' was replaced by 'sms_lines' (the lines that show a Text action)")
    lines = data["sms_lines"]
    if not isinstance(lines, list) or not all(isinstance(x, str) and E164.fullmatch(x) for x in lines):
        raise SystemExit(f"{path}: 'sms_lines' must be a list of +1XXXXXXXXXX numbers (may be empty)")
    return data


def text_on(d: dict) -> bool:
    """The Text action is offered only for a line listed in sms_lines (fail closed)."""
    return d["phone_tel"] in d["sms_lines"]


def render(d: dict) -> str:
    e = lambda s: html.escape(str(s), quote=True)  # noqa: E731
    mail = f"mailto:{d['email']}?subject={quote(d['email_subject'])}"
    actions = [f'<li><a class="gre-sc-btn gre-sc-primary" href="tel:{e(d["phone_tel"])}" data-sc="call">'
               f'Call {e(d["phone_display"])}</a></li>']
    if text_on(d):
        actions.append(f'<li><a class="gre-sc-btn" href="sms:{e(d["phone_tel"])}" data-sc="text">'
                       f'Text {e(d["phone_display"])}</a></li>')
    actions.append(f'<li><a class="gre-sc-btn" href="{e(mail)}" data-sc="email">Email {e(d["email"])}</a></li>')
    actions.append(f'<li><a class="gre-sc-btn" href="{e(d["cma_href"])}" data-sc="cma">{e(d["cma_label"])}</a></li>')
    lines = [
        f'<section class="gre-sc" id="seller-contact" aria-labelledby="seller-contact-heading" '
        f'data-seller-contact="v{e(d["version"])}">',
        f"<style>{STYLE}</style>",
        f'<h2 id="seller-contact-heading">{e(d["heading"])}</h2>',
        f'<p class="gre-sc-intro">{e(d["intro"])}</p>',
        "<ul>", *actions, "</ul>",
        f'<p class="gre-sc-fine">{e(d["cma_note"])} <a href="{e(d["process_href"])}">{e(d["process_label"])}</a>.</p>',
        f'<p class="gre-sc-fine">{e(d["broker_line"])} · '
        f'<a href="{e(d["disclosure_href"])}">{e(d["disclosure_label"])}</a></p>',
    ]
    if d["track_clicks"]:
        lines.append(f"<script>{TRACK}</script>")
    lines.append("</section>")
    return "\n".join(lines)


def splice(page_html: str, block: str, rel: str) -> str:
    if page_html.count(START) != 1 or page_html.count(END) != 1:
        raise ValueError(f"{rel}: expected exactly one '{START}' and one '{END}' "
                         f"(found {page_html.count(START)} / {page_html.count(END)})")
    a = page_html.index(START) + len(START)
    b = page_html.index(END)
    if b < a:
        raise ValueError(f"{rel}: end marker precedes start marker")
    return page_html[:a] + "\n" + block + "\n" + page_html[b:]


def run(write: bool, root: pathlib.Path = ROOT) -> int:
    d = load(root / "data" / "seller-contact-block.json")
    block = render(d)
    bad = 0
    for rel in d["pages"]:
        p = root / rel
        if not p.is_file():
            print(f"MISSING PAGE  {rel}")
            bad += 1
            continue
        cur = p.read_text(encoding="utf-8")
        try:
            new = splice(cur, block, rel)
        except ValueError as exc:
            print(f"MARKERS       {exc}")
            bad += 1
            continue
        if new == cur:
            print(f"ok            {rel}")
        elif write:
            p.write_text(new, encoding="utf-8")
            print(f"written       {rel}")
        else:
            print(f"DRIFT         {rel} (run with --write)")
            bad += 1
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--print", action="store_true")
    a = ap.parse_args()
    if a.print:
        print(render(load()))
        return 0
    return run(write=a.write)


if __name__ == "__main__":
    sys.exit(main())
