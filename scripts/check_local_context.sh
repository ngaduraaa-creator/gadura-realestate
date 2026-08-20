#!/usr/bin/env bash
# check_local_context.sh — verify local operator context is present AND unpublishable.
# Exits 0 only if CLAUDE.local.md exists, is ignored by git, and is untracked.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
F=CLAUDE.local.md
fail=0
printf 'repo: %s\n' "$(pwd)"
if [ -f "$F" ]; then printf '  ok    %s exists\n' "$F"
else printf '  MISS  %s absent — copy the preserved operator context into it\n' "$F"; fail=1; fi
if git check-ignore -q "$F" 2>/dev/null; then printf '  ok    %s is gitignored\n' "$F"
else printf '  FAIL  %s is NOT gitignored — it could be published\n' "$F"; fail=1; fi
if git ls-files --error-unmatch "$F" >/dev/null 2>&1; then
  printf '  FAIL  %s is TRACKED — remove it from the index immediately\n' "$F"; fail=1
else printf '  ok    %s is untracked\n' "$F"; fi
# High-signal leakage markers only. Generic nouns like "strategy" appear in the
# public file's own prohibition text, so matching them produced false positives.
if [ -f CLAUDE.md ] && grep -qiE 'AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|AIza[0-9A-Za-z_-]{35}|KEYWORD-MAP|myshopify|api[_-]?key[[:space:]]*[:=]' CLAUDE.md; then
  printf '  WARN  public CLAUDE.md matched a leakage marker — review before commit\n'; fi
[ "$fail" -eq 0 ] && printf 'PASS\n' || printf 'FAIL\n'
exit "$fail"
