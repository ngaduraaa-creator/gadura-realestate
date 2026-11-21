#!/usr/bin/env python3
"""build_owner_path_blocks.py — render the rental-owner (landlord) contact blocks,
the owner-page scope section and the owner signposts into the pages that carry them.

    python3 scripts/build_owner_path_blocks.py            # --check (default): exit 1 if any page is stale
    python3 scripts/build_owner_path_blocks.py --apply    # write the rendered markup

Inputs (nothing else):
    data/business-contact.json     phone_display, phone_tel, legal_name, street_address,
                                   locality, region, postal_code (the single place to change the phone)
    data/landlord-owner-path.json  email, sms_lines, pages, evidenced_scope,
                                   owner_services

Each page lists which parts it carries. The script replaces only the text between
its own markers:
    <!-- LL-OWNER-BLOCK:START --> ... <!-- LL-OWNER-BLOCK:END -->
    <!-- LL-OWNER-SCOPE:START --> ... <!-- LL-OWNER-SCOPE:END -->        (hub only)
    <!-- LL-OWNER-SIGNPOST:START --> ... <!-- LL-OWNER-SIGNPOST:END -->
and makes sure the page head links /css/owner-path.css and /js/owner-contact.js.

Fails closed: a missing or inconsistent input, a page without its markers, or an
owner_services entry that is not an object holding only a non-empty copy stops
the run with exit 2 and nothing is written.

owner_services renders as a visible list only when it has entries; an empty list
renders nothing (no heading, no placeholder, no comment).

The Text button is shown only when the public number in business-contact.json is
one of the lines listed in sms_lines. If the list is empty, or the public number
is switched to a line that is not listed, the block offers call and email only.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CONTACT_FILE = ROOT / "data" / "business-contact.json"
CFG_FILE = ROOT / "data" / "landlord-owner-path.json"

CSS_TAG = '<link rel="stylesheet" href="/css/owner-path.css">'
JS_TAG = '<script src="/js/owner-contact.js" defer></script>'
GEN_NOTE = "rendered by scripts/build_owner_path_blocks.py from data/landlord-owner-path.json; edit that file, not this markup"
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

BLOCK_HEAD = {
    "hub": ("Talk to us about your rental",
            "Tell us about the unit and what you are deciding."),
    "standard": ("Own a rental? Talk to us about it",
                 "Tell us about the unit and what you are deciding."),
    "brooklyn": ("Own a rental in Brooklyn?",
                 "Tell us where the unit is and what you are deciding."),
}
SIGNPOST_TEXT = {
    "rentals": ("For rental owners",
                "<strong>Own a rental?</strong> Owners have their own page: New York landlord rules with sources, "
                "owner guides, and a direct line to a licensed salesperson by {channels}."),
    "renter": ("Own a rental instead?",
               "This page is for renters. If you own a rental unit, the owner page has New York landlord rules "
               "with sources and a direct line to a licensed salesperson."),
    "voucher": ("For rental owners",
                "Own a rental and want to know how this program works for owners? Read the "
                "<a href=\"{guide}\">landlord guide</a>, or go to the owner page to reach a licensed salesperson."),
}


class Stop(Exception):
    pass


def digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")[-10:]


def load() -> tuple[dict, dict]:
    try:
        contact = json.loads(CONTACT_FILE.read_text(encoding="utf-8"))
        cfg = json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Stop(f"cannot read inputs: {exc}")
    need = ("phone_display", "phone_tel", "legal_name", "street_address", "locality", "region", "postal_code")
    missing = [k for k in need if not str(contact.get(k, "")).strip()]
    if missing:
        raise Stop(f"business-contact.json missing {missing}")
    if len(digits(contact["phone_tel"])) != 10 or digits(contact["phone_display"]) != digits(contact["phone_tel"]):
        raise Stop("business-contact.json phone_display and phone_tel are not the same 10-digit number")
    if not EMAIL_RE.match(cfg.get("email", "")):
        raise Stop("landlord-owner-path.json email is missing or malformed")
    lines = cfg.get("sms_lines")
    if not isinstance(lines, list) or any(len(digits(str(x))) != 10 for x in lines):
        raise Stop("landlord-owner-path.json sms_lines must be a list of 10-digit numbers (may be empty)")
    for key in ("hub_path", "renter_path"):
        if not str(cfg.get(key, "")).startswith("/") or not (ROOT / cfg[key].lstrip("/")).is_file():
            raise Stop(f"landlord-owner-path.json {key} does not point at a page in the repo")
    services = cfg.get("owner_services")
    if not isinstance(services, list):
        raise Stop("landlord-owner-path.json owner_services must be a list (may be empty)")
    for i, svc in enumerate(services):
        if not isinstance(svc, dict) or set(svc) != {"copy"} or not str(svc["copy"]).strip():
            raise Stop(f"owner_services[{i}] must be an object with one key, copy, holding the visible text")
    seen = set()
    for rel, p in cfg.get("pages", {}).items():
        code = p.get("code", "")
        if not re.match(r"^LL-\d{2}$", code) or code in seen:
            raise Stop(f"{rel}: page code missing, malformed or duplicated")
        seen.add(code)
        if p.get("block") not in (None, "hub", "standard", "brooklyn"):
            raise Stop(f"{rel}: unknown block variant")
        if p.get("signpost") not in (None, "rentals", "renter", "voucher"):
            raise Stop(f"{rel}: unknown signpost variant")
        if p.get("signpost") == "voucher" and not (ROOT / str(p.get("guide", "")).lstrip("/")).is_file():
            raise Stop(f"{rel}: voucher signpost needs a guide page that exists")
    return contact, cfg


def render_block(code: str, variant: str, contact: dict, cfg: dict) -> str:
    title, lede = BLOCK_HEAD[variant]
    tel = "+1" + digits(contact["phone_tel"])
    shown = html.escape(contact["phone_display"])
    email = cfg["email"]
    sms_body = quote(f"Hi, I own a rental property and have a question. (web ref {code})")
    subject = quote(f"Rental owner question (web ref {code})")
    body = quote("Neighborhood or ZIP code:\r\nUnit type and size:\r\nAvailable from:\r\n"
                 "Also weighing a sale? (yes / no / not sure):\r\n")
    sms = texts_ok(contact, cfg)
    actions = [f'<li><a class="ll-btn ll-btn-primary" href="tel:{tel}" data-owner-contact="call">Call {shown}</a></li>']
    if sms:
        actions.append(f'<li><a class="ll-btn" href="sms:{tel}?&amp;body={sms_body}" data-owner-contact="text">Text {shown}</a></li>')
    actions.append(f'<li><a class="ll-btn" href="mailto:{email}?subject={subject}&amp;body={body}" '
                   f'data-owner-contact="email">Email {html.escape(email)}</a></li>')
    channels = "Call, text or email" if sms else "Call or email"
    addr = (f'{html.escape(contact["legal_name"])} &middot; {html.escape(contact["street_address"])}, '
            f'{html.escape(contact["locality"])}, {html.escape(contact["region"])} {html.escape(contact["postal_code"])}')
    return "\n".join([
        f"<!-- LL-OWNER-BLOCK:START ({GEN_NOTE}) -->",
        f'<section class="ll-owner" id="owner-contact" data-ll-block="{code}" aria-labelledby="ll-owner-h">',
        f'  <h2 id="ll-owner-h">{title}</h2>',
        f'  <p class="ll-owner-lede">{channels} Nitin Gadura, Licensed Real Estate Salesperson with '
        f'{html.escape(contact["legal_name"])}. {lede}</p>',
        '  <ul class="ll-owner-actions">',
        *("    " + a for a in actions),
        "  </ul>",
        '  <p class="ll-owner-tip"><strong>Useful to mention:</strong> the neighborhood or ZIP code, the type and size of '
        "the unit, when it will be available, and whether you are also weighing a sale.</p>",
        f'  <p class="ll-owner-id">{addr} &middot; Nitin Gadura, Licensed Real Estate Salesperson</p>',
        '  <p class="ll-owner-fh">Equal Housing Opportunity. We do not screen, steer or advertise by any protected class, '
        'including lawful source of income such as a housing voucher. <a href="/fair-housing.html">Fair housing policy</a></p>',
        "</section>",
        "<!-- LL-OWNER-BLOCK:END -->",
    ])


def render_scope(cfg: dict) -> str:
    lines = [f"<!-- LL-OWNER-SCOPE:START ({GEN_NOTE}) -->",
             '<section class="ll-scope" aria-labelledby="ll-scope-h">',
             '  <h2 id="ll-scope-h">Who you would be dealing with</h2>',
             "  <ul>"]
    lines += [f"    <li>{item}</li>" for item in cfg["evidenced_scope"]]
    lines.append("  </ul>")
    services = cfg["owner_services"]
    if services:
        lines += ['  <h3>Services the firm offers rental owners</h3>', "  <ul>"]
        lines += [f'    <li class="ll-service">{html.escape(svc["copy"])}</li>' for svc in services]
        lines.append("  </ul>")
    lines += ["</section>", "<!-- LL-OWNER-SCOPE:END -->"]
    return "\n".join(lines)


def texts_ok(contact: dict, cfg: dict) -> bool:
    """True only when the public number is a listed SMS line."""
    return digits(contact["phone_tel"]) in {digits(str(x)) for x in cfg["sms_lines"]}


def render_signpost(code: str, kind: str, page: dict, contact: dict, cfg: dict) -> str:
    k, text = SIGNPOST_TEXT[kind]
    text = text.replace("{guide}", html.escape(page.get("guide", "")))
    text = text.replace("{channels}", "call, text or email" if texts_ok(contact, cfg) else "call or email")
    return "\n".join([
        f"<!-- LL-OWNER-SIGNPOST:START ({GEN_NOTE}) -->",
        f'<aside class="ll-signpost" data-ll-block="{code}" aria-label="For rental owners">',
        f'  <p class="ll-signpost-k">{k}</p>',
        f"  <p>{text}</p>",
        f'  <a class="ll-signpost-link" href="{cfg["hub_path"]}" data-owner-contact="to-owner-page">Landlord &amp; owner help &rarr;</a>',
        "</aside>",
        "<!-- LL-OWNER-SIGNPOST:END -->",
    ])


def region(name: str) -> re.Pattern:
    return re.compile(rf"<!-- LL-OWNER-{name}:START\b.*?-->.*?<!-- LL-OWNER-{name}:END -->", re.S)


def render_page(rel: str, src: str, page: dict, contact: dict, cfg: dict) -> str:
    out = src
    wants = {"BLOCK": page.get("block"), "SIGNPOST": page.get("signpost"), "SCOPE": page.get("block") == "hub"}
    for name, want in wants.items():
        hits = region(name).findall(out)
        if want and len(hits) != 1:
            raise Stop(f"{rel}: expected exactly one LL-OWNER-{name} marker pair, found {len(hits)}")
        if not want and hits:
            raise Stop(f"{rel}: carries an LL-OWNER-{name} region it is not configured for")
    if page.get("block"):
        out = region("BLOCK").sub(lambda m: render_block(page["code"], page["block"], contact, cfg), out)
    if page.get("block") == "hub":
        out = region("SCOPE").sub(lambda m: render_scope(cfg), out)
    if page.get("signpost"):
        out = region("SIGNPOST").sub(lambda m: render_signpost(page["code"], page["signpost"], page, contact, cfg), out)
    if "</head>" not in out:
        raise Stop(f"{rel}: no </head>")
    for tag in (CSS_TAG, JS_TAG):
        if tag not in out:
            out = out.replace("</head>", f"{tag}\n</head>", 1)
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    try:
        contact, cfg = load()
        rendered = {}
        for rel, page in cfg["pages"].items():
            f = ROOT / rel
            if not f.is_file():
                raise Stop(f"{rel}: page does not exist")
            src = f.read_text(encoding="utf-8")
            rendered[rel] = (src, render_page(rel, src, page, contact, cfg))
    except Stop as exc:
        print(f"STOP (nothing written): {exc}", file=sys.stderr)
        return 2
    stale = [rel for rel, (src, new) in rendered.items() if src != new]
    if apply:
        for rel in stale:
            (ROOT / rel).write_text(rendered[rel][1], encoding="utf-8")
        print(f"wrote {len(stale)} of {len(rendered)} page(s)")
        return 0
    if stale:
        print(f"STALE: {len(stale)} page(s) differ from the rendered owner-path markup:")
        for rel in stale:
            print(f"    {rel}")
        print("Run: python3 scripts/build_owner_path_blocks.py --apply")
        return 1
    print(f"ok  {len(rendered)} page(s) match data/landlord-owner-path.json + data/business-contact.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
