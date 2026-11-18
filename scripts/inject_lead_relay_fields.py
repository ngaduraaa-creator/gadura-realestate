#!/usr/bin/env python3
"""Add the speed-to-lead hidden fields to every FormSubmit form on the site.

For each <form action="https://formsubmit.co/..."> in a tracked *.html file:
  * adds  <input type="text" name="_honey" ...>   if the form has no _honey field
  * adds  <input type="hidden" name="_webhook" ...> if missing, or rewrites its
    value if it differs from the configured relay URL.

The _webhook value points FormSubmit at the gadura-lead-relay Cloudflare Worker,
which pings the Discord #leads channel. It carries:
  k = RELAY_TOKEN (shared token; it is visible in page source by design --
      it stops random scanners, it is not the Discord secret)
  p = the page path, so the ping says which page the lead came from.
The Discord webhook URL itself is NEVER written here; it lives only as a
Worker secret.

Idempotent: a second run with the same arguments changes nothing.

Usage
  python3 scripts/inject_lead_relay_fields.py            # dry run, placeholder URL
  python3 scripts/inject_lead_relay_fields.py --apply \
      --relay-url https://gadura-lead-relay.<sub>.workers.dev/formsubmit \
      --token-file ~/.gadura-lead-relay-token

Without --relay-url/--token-file the PENDING placeholder is used; the gate
scripts/dgp/test_formsubmit_lead_relay.py fails while the placeholder is
present, so it cannot ship silently.
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_RELAY_URL = "https://gadura-lead-relay.pending-deploy.workers.dev/formsubmit"
PLACEHOLDER_TOKEN = "PENDING"

FORM_OPEN_RE = re.compile(
    r'<form\b[^>]*\baction\s*=\s*"https://formsubmit\.co/[^"]*"[^>]*>', re.IGNORECASE
)
FORM_CLOSE_RE = re.compile(r"</form\s*>", re.IGNORECASE)
HONEY_RE = re.compile(r'<input\b[^>]*\bname\s*=\s*"_honey"[^>]*>', re.IGNORECASE)
WEBHOOK_RE = re.compile(r'(<input\b[^>]*\bname\s*=\s*"_webhook"[^>]*\bvalue\s*=\s*")([^"]*)(")', re.IGNORECASE)
WEBHOOK_ANY_RE = re.compile(r'<input\b[^>]*\bname\s*=\s*"_webhook"[^>]*>', re.IGNORECASE)

HONEY_INPUT = '<input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">'


def webhook_value(relay_url: str, token: str, page_path: str) -> str:
    """Attribute-escaped _webhook value for one page."""
    url = f"{relay_url}?k={quote(token, safe='')}&p={quote(page_path, safe='/._-')}"
    return html.escape(url, quote=True)


def page_path_for(rel: Path) -> str:
    return "/" + rel.as_posix()


def _indent_after(text: str, pos: int) -> str:
    """Indentation of the first non-blank line after `pos`, used for inserted lines."""
    m = re.compile(r"\n([ \t]*)\S").search(text, pos)
    return m.group(1) if m else ""


def inject(text: str, value: str) -> tuple[str, int]:
    """Return (new_text, number_of_forms_changed). Pure function."""
    out: list[str] = []
    cursor = 0
    changed = 0
    for m in FORM_OPEN_RE.finditer(text):
        if m.start() < cursor:
            continue
        close = FORM_CLOSE_RE.search(text, m.end())
        end = close.start() if close else len(text)
        body = text[m.end():end]
        new_body = body
        if WEBHOOK_ANY_RE.search(new_body):
            new_body = WEBHOOK_RE.sub(lambda w: w.group(1) + value + w.group(3), new_body, count=1)
        additions = []
        if not HONEY_RE.search(body):
            additions.append(HONEY_INPUT)
        if not WEBHOOK_ANY_RE.search(body):
            additions.append(f'<input type="hidden" name="_webhook" value="{value}">')
        if additions:
            indent = _indent_after(text, m.end())
            new_body = "".join(f"\n{indent}{a}" for a in additions) + new_body
        out.append(text[cursor:m.end()])
        out.append(new_body)
        cursor = end
        if new_body != body:
            changed += 1
    out.append(text[cursor:])
    return "".join(out), changed


def tracked_html_files() -> list[Path]:
    res = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [Path(p) for p in res.stdout.splitlines() if p]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--relay-url", default=PLACEHOLDER_RELAY_URL)
    ap.add_argument("--token-file", type=Path, help="file holding RELAY_TOKEN (never pass the token on argv)")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args(argv)

    token = PLACEHOLDER_TOKEN
    if args.token_file:
        token = args.token_file.expanduser().read_text().strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-]{16,128}", token):
            print("ERROR: token must be 16-128 chars of [A-Za-z0-9_-]", file=sys.stderr)
            return 2
    if not re.fullmatch(r"https://[a-z0-9.\-]+/formsubmit", args.relay_url):
        print("ERROR: --relay-url must look like https://<host>/formsubmit", file=sys.stderr)
        return 2

    files_changed = forms_changed = 0
    for rel in tracked_html_files():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        if "formsubmit.co" not in text:
            continue
        new_text, n = inject(text, webhook_value(args.relay_url, token, page_path_for(rel)))
        if n:
            files_changed += 1
            forms_changed += n
            if args.apply:
                path.write_text(new_text, encoding="utf-8")
    mode = "APPLIED" if args.apply else "DRY RUN"
    placeholder = " (PLACEHOLDER relay URL/token -- replace before release)" if token == PLACEHOLDER_TOKEN else ""
    print(f"{mode}: {forms_changed} forms in {files_changed} files{placeholder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
