#!/usr/bin/env python3
"""
Batch-update all GRE HTML files:
  1. Add favicon link tags (if missing)
  2. Replace all text-based logo HTML with SVG image tags
"""
import os, re, glob

BASE = '/Users/nidhigadura/Jagex/gadura-realestate'

LOGO_IMG = '<img src="/images/gre-logo.svg" alt="Gadura Real Estate LLC" style="height:44px;width:auto;">'
LOGO_IMG_FTR = '<img src="/images/gre-logo.svg" alt="Gadura Real Estate LLC" style="height:44px;width:auto;filter:brightness(0) invert(1);">'

FAVICON = (
    '  <link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
    '  <link rel="shortcut icon" href="/favicon.svg">\n'
)

def fix(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        html = f.read()
    orig = html

    # ── 1. Favicon ──────────────────────────────────────────────────────────
    if '/favicon.svg' not in html:
        # insert before first <link rel="stylesheet"> or fallback to </head>
        if '<link rel="stylesheet"' in html:
            html = html.replace('<link rel="stylesheet"', FAVICON + '<link rel="stylesheet"', 1)
        elif '<link rel=' in html:
            html = re.sub(r'(<link rel=)', FAVICON + r'\1', html, count=1)
        elif '</head>' in html:
            html = html.replace('</head>', FAVICON + '</head>', 1)

    # ── 2. Pattern A – logo-mark + logo-text inside nav anchor ────────────
    # <a ... class="logo" ...>
    #   <div class="logo-mark">GRE</div>
    #   <div class="logo-text">…</div>
    # </a>
    html = re.sub(
        r'(<a[^>]+class="logo"[^>]*>)\s*<div class="logo-mark"[^>]*>GRE</div>\s*<div class="logo-text">.*?</div>',
        r'\1' + LOGO_IMG,
        html, flags=re.DOTALL
    )

    # ── 3. Pattern B – standalone logo-mark (footer, no logo-text sibling) ─
    html = re.sub(
        r'<div class="logo-mark"[^>]*>GRE</div>',
        LOGO_IMG_FTR,
        html
    )

    # ── 4. Pattern C – logo-badge inside nav anchor ────────────────────────
    html = re.sub(
        r'(<a[^>]+class="logo"[^>]*>)\s*<div class="logo-badge">GRE</div>\s*<div[^>]*>.*?</div>',
        r'\1' + LOGO_IMG,
        html, flags=re.DOTALL
    )

    # ── 5. Pattern D – inline span logo (header nav) ──────────────────────
    html = re.sub(
        r'<span class="logo-name">GADURA</span><span class="logo-sub">REAL ESTATE(?:, LLC)?</span>',
        LOGO_IMG,
        html
    )
    # Variant in some files: logo-name/logo-sub as separate children of <a class="logo">
    html = re.sub(
        r'(<a[^>]+class="logo"[^>]*>)\s*<span class="logo-name">GADURA</span>\s*<span class="logo-sub">REAL ESTATE(?:, LLC)?</span>',
        r'\1' + LOGO_IMG,
        html, flags=re.DOTALL
    )

    # ── 6. Pattern E – footer div.logo with span children ─────────────────
    html = re.sub(
        r'<div class="logo">\s*<span class="logo-name">GADURA</span>\s*<span class="logo-sub">REAL ESTATE(?:, LLC)?</span>\s*</div>',
        '<div class="logo">' + LOGO_IMG_FTR + '</div>',
        html
    )

    # ── 7. Variant: <a class="logo"> wrapping <span>GADURA</span><span>... ─
    # (already handled above, but catch remaining orphan spans)
    html = re.sub(
        r'<span class="logo-name">GADURA</span>\s*<span class="logo-sub">REAL ESTATE(?:, LLC)?</span>',
        LOGO_IMG,
        html
    )

    # ── 8. Inline-style span versions (logo-name/logo-sub with style=) ────
    # e.g. <span class="logo-name" style="...">GADURA</span><span class="logo-sub" style="...">REAL ESTATE, LLC</span>
    html = re.sub(
        r'<span class="logo-name"[^>]*>GADURA</span>\s*<span class="logo-sub"[^>]*>REAL ESTATE(?:, LLC)?</span>',
        LOGO_IMG,
        html
    )

    # ── 9. Remove redundant text div that follows an already-placed SVG img ─
    # Pattern: <img src="/images/gre-logo.svg"...><div style="..."><span class="logo-name"...>...</span><span class="logo-sub"...>...</span></div>
    html = re.sub(
        r'(<img src="/images/gre-logo\.svg"[^>]+>)\s*<div[^>]*>\s*<span class="logo-name"[^>]*>[^<]*</span>\s*<span class="logo-sub"[^>]*>[^<]*</span>\s*</div>',
        r'\1',
        html
    )

    # ── 10. Combo in footer: existing SVG text + redundant logo-name/sub spans ─
    html = re.sub(
        r'(<img src="/images/gre-logo\.svg"[^>]+>)\s*<span class="logo-name"[^>]*>[^<]*</span>\s*<span class="logo-sub"[^>]*>[^<]*</span>',
        r'\1',
        html
    )

    if html != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    return False


html_files = glob.glob(os.path.join(BASE, '**/*.html'), recursive=True)
# Skip index.html – already updated in previous session
skip = {os.path.join(BASE, 'index.html')}

changed, skipped = 0, 0
for fp in sorted(html_files):
    if fp in skip:
        skipped += 1
        continue
    if fix(fp):
        changed += 1
        print(f'  ✓  {fp.replace(BASE+"/", "")}')

print(f'\nDone: {changed} updated, {skipped} skipped, {len(html_files)-changed-skipped} unchanged')
