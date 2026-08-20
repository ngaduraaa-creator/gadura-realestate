# Repository Guidance

This file is **public**. GitHub Pages publishes this repository at its root, so
every tracked file — including this one — is retrievable at
`https://gadurarealestate.com/CLAUDE.md`.

Keep this file limited to engineering rules that are safe to publish. Business
strategy, competitive analysis, marketing tactics, claims deliberations,
compliance discussions, credentials, and internal operating context must **not**
be added here. See "Local operator context" below for where those belong.

## Publishing model

- Static HTML/CSS/JS. No build step.
- GitHub Pages serves branch `main` from the repository root.
- **Anything committed becomes a public URL.** There is no private directory,
  no server-side include, and no ignore mechanism that prevents publication of
  a tracked file. `robots.txt` only asks crawlers; it does not prevent
  retrieval.
- Before adding any file, ask whether it is acceptable at a public URL.

## Repository conventions

- Edit source files directly; there is no compile step.
- Generated page families are produced by scripts in `scripts/`. Change the
  generator, not the generated output, or the next run will overwrite the edit.
- Keep commits scoped to a single concern with a descriptive message.

## Automation safety

- Workflows must stage an explicit allowlist of their own verified outputs.
  Never `git add -A` or `git add -u`. See `scripts/ci_stage_manifest.py`, which
  classifies every changed path and fails closed on anything unexpected.
- Audit output, test fixtures, reports, and scratch files must be written
  outside the repository, never committed.
- Content generators must fail closed: if authoritative input data is missing,
  incomplete, or covers an unfinished period, exit non-zero and write nothing.
  Never substitute a default, placeholder, or derived value for a real figure.

## Content integrity

- Published statistics require a real source, a retrieval date, and a defined
  reporting period. No fallback constants.
- Do not publish a reporting period before it has ended.
- Never set a publication date in the future.
- Structured data must match what is visible on the page.

## Testing

- Run tests from outside the publishable tree.
- When testing scripts that inspect working-tree state, do not use
  `git checkout -- .` or `git clean -fd` for cleanup — they destroy
  uncommitted work. Clean only the specific fixture paths you created.

## Local operator context

Complete operational context — business goals, target markets, keyword
strategy, contact routing, and internal workflow — is intentionally **not** in
this repository. It lives in an untracked local file:

    CLAUDE.local.md      (gitignored; never commit)

Run `scripts/check_local_context.sh` to verify your local context file is
present and correctly ignored.
