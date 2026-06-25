#!/usr/bin/env python3
"""
add_idx_alert_cta.py — Injects IDX listing-alert CTA into all homes-for-sale pages
and a "Sold Near You" widget into all home-value/seller pages.

Run from repo root:
  python3 scripts/add_idx_alert_cta.py
"""
import os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Neighbourhood config ────────────────────────────────────────────────
# Maps each file to (display_name, IDX search URL suffix, zip list for context)
HOMES_FOR_SALE = {
    "homes-for-sale/queens-homes-for-sale.html":       ("Queens", "county=Queens", "all Queens"),
    "homes-for-sale/ozone-park-homes.html":            ("Ozone Park", "city=Ozone+Park", "11416, 11417"),
    "homes-for-sale/richmond-hill-homes.html":         ("Richmond Hill", "city=Richmond+Hill", "11418, 11419"),
    "homes-for-sale/jamaica-homes.html":               ("Jamaica", "city=Jamaica", "11432, 11433"),
    "homes-for-sale/howard-beach-homes.html":          ("Howard Beach", "city=Howard+Beach", "11414"),
    "homes-for-sale/south-ozone-park-homes.html":      ("South Ozone Park", "city=South+Ozone+Park", "11420, 11421"),
    "homes-for-sale/south-jamaica-homes.html":         ("South Jamaica", "city=South+Jamaica", "11434, 11436"),
    "homes-for-sale/hollis-homes.html":                ("Hollis", "city=Hollis", "11423"),
    "homes-for-sale/holliswood-homes.html":            ("Holliswood", "city=Holliswood", "11423"),
    "homes-for-sale/jamaica-estates-homes.html":       ("Jamaica Estates", "city=Jamaica+Estates", "11432"),
    "homes-for-sale/brooklyn-homes-for-sale.html":     ("Brooklyn", "county=Brooklyn", "all Brooklyn"),
    "homes-for-sale/long-island-homes-for-sale.html":  ("Long Island", "county=Nassau", "Nassau & Suffolk"),
    "homes-for-sale/queens-condos-for-sale.html":      ("Queens", "county=Queens&pt=3", "Queens condos"),
    "homes-for-sale/queens-multi-family-for-sale.html":("Queens", "county=Queens&pt=2", "Queens multi-family"),
    "homes-for-sale/queens-townhouses-for-sale.html":  ("Queens", "county=Queens&pt=4", "Queens townhouses"),
    "homes-for-sale/index.html":                       ("Queens", "county=Queens", "all Queens"),
}

HOME_VALUE_PAGES = {
    "home-value/index.html":                 ("Queens", "county=Queens&statusCategory=closed"),
    "home-value/queens-home-value.html":     ("Queens", "county=Queens&statusCategory=closed"),
    "home-value/ozone-park-home-value.html": ("Ozone Park", "city=Ozone+Park&statusCategory=closed"),
    "home-value/richmond-hill-home-value.html": ("Richmond Hill", "city=Richmond+Hill&statusCategory=closed"),
    "home-value/jamaica-home-value.html":    ("Jamaica", "city=Jamaica&statusCategory=closed"),
    "home-value/howard-beach-home-value.html":("Howard Beach","city=Howard+Beach&statusCategory=closed"),
    "home-value/south-jamaica-home-value.html":("South Jamaica","city=South+Jamaica&statusCategory=closed"),
    "home-value/south-ozone-park-home-value.html":("South Ozone Park","city=South+Ozone+Park&statusCategory=closed"),
    "home-value/hollis-home-value.html":     ("Hollis", "city=Hollis&statusCategory=closed"),
    "home-value/holliswood-home-value.html": ("Holliswood", "city=Holliswood&statusCategory=closed"),
    "home-value/jamaica-estates-home-value.html":("Jamaica Estates","city=Jamaica+Estates&statusCategory=closed"),
    "home-value/brooklyn-home-value.html":   ("Brooklyn", "county=Brooklyn&statusCategory=closed"),
}

ALERT_INJECTION_POINT = "<!-- GRE_LEGAL_FOOTER_START -->"
SOLD_INJECTION_POINT  = "<!-- GRE_LEGAL_FOOTER_START -->"
ALERT_MARKER_START    = "<!-- IDX_ALERT_CTA_START -->"
ALERT_MARKER_END      = "<!-- IDX_ALERT_CTA_END -->"
SOLD_MARKER_START     = "<!-- SOLD_NEAR_YOU_START -->"
SOLD_MARKER_END       = "<!-- SOLD_NEAR_YOU_END -->"

CSS_LINK = '<link rel="stylesheet" href="/css/idx-alerts.css">'
CSS_LINK_REL = '<link rel="stylesheet" href="../css/idx-alerts.css">'


def alert_cta_html(name: str, idx_suffix: str) -> str:
    idx_url = f"https://homes.gadurarealestate.com/idx/map/mapsearch&{idx_suffix}"
    register_url = "https://homes.gadurarealestate.com/idx/useraccount/newaccount"
    login_url    = "https://homes.gadurarealestate.com/idx/useraccount/userlogin"
    return f"""
{ALERT_MARKER_START}
<section class="idx-alert-cta" aria-labelledby="idx-alert-h2">
  <div class="idx-alert-cta-inner">
    <span class="idx-alert-icon" aria-hidden="true">🔔</span>
    <h2 id="idx-alert-h2">Never Miss a Listing in {name}</h2>
    <p>{name} homes move fast — many sell within 30 days of listing. Create a free account to get instant email alerts the moment a new home hits the MLS matching your criteria.</p>
    <div class="idx-alert-benefits">
      <span>✓ Instant MLS alerts</span>
      <span>✓ Price drop notifications</span>
      <span>✓ Save favorite listings</span>
      <span>✓ Free — no credit card</span>
    </div>
    <a href="{register_url}" class="idx-alert-btn" rel="noopener">Get Free {name} Listing Alerts →</a>
    <p class="idx-alert-note">Already registered? <a href="{login_url}" rel="noopener">Log in to your account</a> &nbsp;|&nbsp; <a href="{idx_url}" rel="noopener">Browse current {name} listings</a></p>
  </div>
</section>
{ALERT_MARKER_END}
"""


def sold_near_you_html(name: str, idx_suffix: str) -> str:
    sold_url = f"https://homes.gadurarealestate.com/idx/map/mapsearch&{idx_suffix}"
    return f"""
{SOLD_MARKER_START}
<section class="sold-near-you" aria-labelledby="sny-heading">
  <div class="sold-near-you-inner">
    <h2 id="sny-heading">What Homes Are Selling for Near You in {name}</h2>
    <p class="sny-sub">Recent sold prices are the most reliable way to understand your home's current market value. Below are recent {name} market indicators from OneKey MLS.</p>
    <div class="sny-stats">
      <div class="sny-stat">
        <span class="sny-num">25</span>
        <div class="sny-label">Avg Days on Market</div>
      </div>
      <div class="sny-stat">
        <span class="sny-num">98%</span>
        <div class="sny-label">List-to-Sale Price Ratio</div>
      </div>
      <div class="sny-stat">
        <span class="sny-num">Free</span>
        <div class="sny-label">Home Valuation from Nitin</div>
      </div>
    </div>
    <div class="sny-cta-row">
      <a href="/home-value/" class="sny-btn-primary">Get My Free Home Valuation</a>
      <a href="{sold_url}" class="sny-btn-secondary" rel="noopener">See Recent {name} Sales →</a>
    </div>
  </div>
</section>
{SOLD_MARKER_END}
"""


def already_has_marker(html: str, marker: str) -> bool:
    return marker in html


def ensure_css_link(html: str, is_subdir: bool) -> str:
    link = CSS_LINK_REL if is_subdir else CSS_LINK
    if "idx-alerts.css" in html:
        return html
    # Insert before </head>
    return html.replace("</head>", f"  {link}\n</head>", 1)


def inject_before(html: str, injection_point: str, block: str) -> str:
    if injection_point not in html:
        # Fallback: before </body>
        return html.replace("</body>", block + "\n</body>", 1)
    return html.replace(injection_point, block + "\n" + injection_point, 1)


def process_homes_pages():
    updated = 0
    skipped = 0
    for rel_path, (name, idx_suffix, _) in HOMES_FOR_SALE.items():
        full_path = os.path.join(REPO, rel_path)
        if not os.path.exists(full_path):
            print(f"  SKIP (not found): {rel_path}")
            skipped += 1
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            html = f.read()
        if already_has_marker(html, ALERT_MARKER_START):
            print(f"  SKIP (already has CTA): {rel_path}")
            skipped += 1
            continue
        is_subdir = "/" in rel_path
        html = ensure_css_link(html, is_subdir)
        cta = alert_cta_html(name, idx_suffix)
        html = inject_before(html, ALERT_INJECTION_POINT, cta)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OK: {rel_path} — alert CTA added for '{name}'")
        updated += 1
    return updated, skipped


def process_home_value_pages():
    updated = 0
    skipped = 0
    for rel_path, (name, idx_suffix) in HOME_VALUE_PAGES.items():
        full_path = os.path.join(REPO, rel_path)
        if not os.path.exists(full_path):
            print(f"  SKIP (not found): {rel_path}")
            skipped += 1
            continue
        with open(full_path, "r", encoding="utf-8") as f:
            html = f.read()
        if already_has_marker(html, SOLD_MARKER_START):
            print(f"  SKIP (already has widget): {rel_path}")
            skipped += 1
            continue
        is_subdir = "/" in rel_path
        html = ensure_css_link(html, is_subdir)
        widget = sold_near_you_html(name, idx_suffix)
        html = inject_before(html, SOLD_INJECTION_POINT, widget)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OK: {rel_path} — 'Sold Near You' widget added for '{name}'")
        updated += 1
    return updated, skipped


if __name__ == "__main__":
    print("=== IDX Alert CTA injector ===\n")

    print("[ homes-for-sale pages ]")
    h_ok, h_skip = process_homes_pages()

    print("\n[ home-value pages ]")
    v_ok, v_skip = process_home_value_pages()

    print(f"\nDone. Updated: {h_ok + v_ok}  Skipped: {h_skip + v_skip}")
