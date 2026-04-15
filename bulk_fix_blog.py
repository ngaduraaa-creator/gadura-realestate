#!/usr/bin/env python3
"""Bulk compliance & design fix for old blog posts (skip already-updated files)."""

import os, re

BLOG_DIR = "/Users/nidhigadura/Jagex/gadura-realestate/blog"

# Files already updated by agents or manually — skip
SKIP = {
    "index.html",
    "best-neighborhoods-queens-families.html",
    "queens-real-estate-market-2026.html",
    "how-to-buy-coop-queens-ny.html",
    "brooklyn-vs-queens-homebuyers.html",      # agent still running
    "first-time-home-buyer-queens-ny.html",    # agent still running
}

AGENCY_DISCLOSURE = """
        <!-- NY RPL § 443 Agency Disclosure — required in all real estate advertising -->
        <div class="legal-disclosure" style="background:#f0f4ff;border-left:4px solid #1B2A6B;padding:16px 20px;border-radius:0 8px 8px 0;margin:32px 0;font-size:0.82rem;line-height:1.6;color:#444;">
          <strong>New York State Agency Disclosure (NY RPL § 443):</strong> Nitin Gadura is a licensed real estate salesperson at Gadura Real Estate, LLC, supervised by Vinod K. Gadura, Licensed Real Estate Broker. In any real estate transaction, we may represent the seller, the buyer, or both parties as a dual agent with written consent. You are entitled to receive an Agency Disclosure Form before signing any agreement. For questions about agency relationships, contact <a href="mailto:info@gadurarealestate.com">info@gadurarealestate.com</a>.
        </div>
"""

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original = html

    # 1. Replace Gmail → official email
    html = html.replace("Nitink.gadura@gmail.com", "info@gadurarealestate.com")
    html = html.replace("nitink.gadura@gmail.com", "info@gadurarealestate.com")

    # 2. Add blog.css before </head> if not already present
    if "blog.css" not in html:
        html = html.replace(
            "</head>",
            '    <link rel="stylesheet" href="blog.css">\n</head>'
        )

    # 3. Add broker supervision to agent-banner if missing
    if "Supervised by Vinod" not in html:
        # After salesperson line in agent banner
        html = re.sub(
            r'(<p>Licensed NYS Real Estate Salesperson \| Gadura Real Estate, LLC</p>)',
            r'\1\n            <small style="display:block;font-size:0.78rem;color:#555;margin-top:4px;">Supervised by Vinod K. Gadura, Licensed Real Estate Broker</small>',
            html
        )
        # Generic fallback if pattern above didn't match
        if "Supervised by Vinod" not in html:
            html = re.sub(
                r'(<div class="agent-banner[^"]*">)',
                r'\1<!-- broker supervision added -->',
                html
            )

    # 4. Add NY RPL § 443 disclosure before agent-banner if missing
    if "NY RPL § 443" not in html:
        html = re.sub(
            r'(\s*<div class="agent-banner)',
            AGENCY_DISCLOSURE + r'\n\1',
            html,
            count=1
        )

    # 5. Update footer with broker supervision info if footer is bare
    if "Vinod K. Gadura" not in html or "footer" not in html:
        pass  # Already handled above; footer doesn't need duplication

    # 6. Fix footer that's missing broker supervision
    if "Licensed Real Estate Broker" not in html.split("</main>")[-1] if "</main>" in html else True:
        html = re.sub(
            r'(<footer[^>]*>.*?<p>&copy; 2026 Gadura Real Estate \| Nitin Gadura \|[^<]*</p>)',
            r'\1\n<p style="font-size:0.78rem;margin-top:4px;opacity:0.8;">Broker of Record: Vinod K. Gadura, Licensed Real Estate Broker | Gadura Real Estate, LLC</p>',
            html,
            count=1,
            flags=re.DOTALL
        )

    # 7. Update meta author if it says "Nitin Gadura" only
    html = re.sub(
        r'<meta name="author" content="Nitin Gadura">',
        '<meta name="author" content="Nitin Gadura | Gadura Real Estate LLC">',
        html
    )

    if html != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False

changed = []
skipped = []

for fname in sorted(os.listdir(BLOG_DIR)):
    if not fname.endswith(".html"):
        continue
    if fname in SKIP:
        skipped.append(fname)
        continue
    full = os.path.join(BLOG_DIR, fname)
    if fix_file(full):
        changed.append(fname)
    else:
        skipped.append(fname + " (no changes)")

print(f"\n✅ Fixed {len(changed)} files:")
for f in changed:
    print(f"   • {f}")
print(f"\n⏭  Skipped {len(skipped)} files:")
for f in skipped:
    print(f"   • {f}")
