#!/usr/bin/env python3
"""
Add live IDX iFrame sections to all neighborhood pages.
Uses homes.gadurarealestate.com with zip/city filters per neighborhood.
"""

import os, re

BASE = "/Users/nidhigadura/Jagex/gadura-realestate/neighborhoods"
IDX_BASE = "https://homes.gadurarealestate.com/idx/search/advanced"

# Full neighborhood data map: slug -> (display_name, IDX search params)
NEIGHBORHOODS = {
    # ── Queens ──────────────────────────────────────────────────────────────
    "arverne":              ("Arverne",              "ccz=zipcode&zipcode=11692"),
    "astoria":              ("Astoria",              "ccz=zipcode&zipcode=11102,11103,11105,11106"),
    "bayside":              ("Bayside",              "ccz=zipcode&zipcode=11359,11360,11361"),
    "bellerose":            ("Bellerose",            "ccz=zipcode&zipcode=11426"),
    "briarwood":            ("Briarwood",            "ccz=zipcode&zipcode=11435"),
    "cambria-heights":      ("Cambria Heights",      "ccz=zipcode&zipcode=11411"),
    "corona":               ("Corona",               "ccz=zipcode&zipcode=11368"),
    "douglaston":           ("Douglaston",           "ccz=zipcode&zipcode=11363"),
    "elmhurst":             ("Elmhurst",             "ccz=zipcode&zipcode=11373"),
    "far-rockaway":         ("Far Rockaway",         "ccz=zipcode&zipcode=11691,11694"),
    "floral-park":          ("Floral Park",          "ccz=zipcode&zipcode=11001,11004"),
    "flushing":             ("Flushing",             "ccz=zipcode&zipcode=11354,11355,11356,11357,11358"),
    "forest-hills":         ("Forest Hills",         "ccz=zipcode&zipcode=11375"),
    "fresh-meadows":        ("Fresh Meadows",        "ccz=zipcode&zipcode=11365,11366"),
    "glen-oaks":            ("Glen Oaks",            "ccz=zipcode&zipcode=11004"),
    "glendale":             ("Glendale",             "ccz=zipcode&zipcode=11385"),
    "hollis":               ("Hollis",               "ccz=zipcode&zipcode=11423"),
    "howard-beach":         ("Howard Beach",         "ccz=zipcode&zipcode=11414"),
    "jackson-heights":      ("Jackson Heights",      "ccz=zipcode&zipcode=11372"),
    "jamaica":              ("Jamaica",              "ccz=zipcode&zipcode=11432,11433,11434,11435,11436"),
    "jamaica-estates":      ("Jamaica Estates",      "ccz=zipcode&zipcode=11432"),
    "kew-gardens":          ("Kew Gardens",          "ccz=zipcode&zipcode=11415"),
    "laurelton":            ("Laurelton",            "ccz=zipcode&zipcode=11413"),
    "little-neck":          ("Little Neck",          "ccz=zipcode&zipcode=11362"),
    "long-island-city":     ("Long Island City",     "ccz=zipcode&zipcode=11101"),
    "maspeth":              ("Maspeth",              "ccz=zipcode&zipcode=11378"),
    "middle-village":       ("Middle Village",       "ccz=zipcode&zipcode=11379"),
    "new-hyde-park":        ("New Hyde Park",        "ccz=zipcode&zipcode=11040,11042"),
    "ozone-park":           ("Ozone Park",           "ccz=zipcode&zipcode=11416,11417"),
    "ozone-park-homes":     ("Ozone Park",           "ccz=zipcode&zipcode=11416,11417"),
    "ozone-park-north":     ("Ozone Park North",     "ccz=zipcode&zipcode=11417"),
    "queens":               ("Queens",               "county=Queens"),
    "queens-village":       ("Queens Village",       "ccz=zipcode&zipcode=11427,11428,11429"),
    "rego-park":            ("Rego Park",            "ccz=zipcode&zipcode=11374"),
    "richmond-hill":        ("Richmond Hill",        "ccz=zipcode&zipcode=11418,11419"),
    "richmond-hill-south":  ("South Richmond Hill",  "ccz=zipcode&zipcode=11419"),
    "ridgewood":            ("Ridgewood",            "ccz=zipcode&zipcode=11385"),
    "rockaway-beach":       ("Rockaway Beach",       "ccz=zipcode&zipcode=11693"),
    "rosedale":             ("Rosedale",             "ccz=zipcode&zipcode=11422"),
    "south-jamaica":        ("South Jamaica",        "ccz=zipcode&zipcode=11433,11434"),
    "south-ozone-park":     ("South Ozone Park",     "ccz=zipcode&zipcode=11420"),
    "springfield-gardens":  ("Springfield Gardens",  "ccz=zipcode&zipcode=11413"),
    "st-albans":            ("St. Albans",           "ccz=zipcode&zipcode=11412"),
    "sunnyside":            ("Sunnyside",            "ccz=zipcode&zipcode=11104"),
    "whitestone":           ("Whitestone",           "ccz=zipcode&zipcode=11357"),
    "woodhaven":            ("Woodhaven",            "ccz=zipcode&zipcode=11421"),
    "woodside":             ("Woodside",             "ccz=zipcode&zipcode=11377"),
    # ── Nassau County ────────────────────────────────────────────────────────
    "baldwin":              ("Baldwin",              "ccz=zipcode&zipcode=11510"),
    "bethpage":             ("Bethpage",             "ccz=zipcode&zipcode=11714"),
    "carle-place":          ("Carle Place",          "ccz=zipcode&zipcode=11514"),
    "cedarhurst":           ("Cedarhurst",           "ccz=zipcode&zipcode=11516"),
    "east-meadow":          ("East Meadow",          "ccz=zipcode&zipcode=11554"),
    "east-rockaway":        ("East Rockaway",        "ccz=zipcode&zipcode=11518"),
    "elmont":               ("Elmont",               "ccz=zipcode&zipcode=11003"),
    "farmingdale":          ("Farmingdale",          "ccz=zipcode&zipcode=11735"),
    "franklin-square":      ("Franklin Square",      "ccz=zipcode&zipcode=11010"),
    "freeport":             ("Freeport",             "ccz=zipcode&zipcode=11520"),
    "garden-city":          ("Garden City",          "ccz=zipcode&zipcode=11530"),
    "great-neck":           ("Great Neck",           "ccz=zipcode&zipcode=11020,11021,11023,11024"),
    "hempstead":            ("Hempstead",            "ccz=zipcode&zipcode=11550,11551"),
    "hewlett":              ("Hewlett",              "ccz=zipcode&zipcode=11557"),
    "hicksville":           ("Hicksville",           "ccz=zipcode&zipcode=11801"),
    "inwood":               ("Inwood",               "ccz=zipcode&zipcode=11096"),
    "jericho":              ("Jericho",              "ccz=zipcode&zipcode=11753"),
    "levittown":            ("Levittown",            "ccz=zipcode&zipcode=11756"),
    "long-beach":           ("Long Beach",           "ccz=zipcode&zipcode=11561"),
    "lynbrook":             ("Lynbrook",             "ccz=zipcode&zipcode=11563"),
    "malverne":             ("Malverne",             "ccz=zipcode&zipcode=11565"),
    "manhasset":            ("Manhasset",            "ccz=zipcode&zipcode=11030"),
    "massapequa":           ("Massapequa",           "ccz=zipcode&zipcode=11758"),
    "merrick":              ("Merrick",              "ccz=zipcode&zipcode=11566"),
    "mineola":              ("Mineola",              "ccz=zipcode&zipcode=11501"),
    "north-woodmere":       ("North Woodmere",       "ccz=zipcode&zipcode=11581"),
    "oceanside":            ("Oceanside",            "ccz=zipcode&zipcode=11572"),
    "port-washington":      ("Port Washington",      "ccz=zipcode&zipcode=11050"),
    "rockville-centre":     ("Rockville Centre",     "ccz=zipcode&zipcode=11570"),
    "roslyn":               ("Roslyn",               "ccz=zipcode&zipcode=11576"),
    "seaford":              ("Seaford",              "ccz=zipcode&zipcode=11783"),
    "syosset":              ("Syosset",              "ccz=zipcode&zipcode=11791"),
    "uniondale":            ("Uniondale",            "ccz=zipcode&zipcode=11553"),
    "valley-stream":        ("Valley Stream",        "ccz=zipcode&zipcode=11580,11581,11582"),
    "wantagh":              ("Wantagh",              "ccz=zipcode&zipcode=11793"),
    "westbury":             ("Westbury",             "ccz=zipcode&zipcode=11590"),
    "woodmere":             ("Woodmere",             "ccz=zipcode&zipcode=11598"),
    # ── Brooklyn (bonus) ─────────────────────────────────────────────────────
    "brooklyn":             ("Brooklyn",             "county=Kings"),
    "canarsie":             ("Canarsie",             "ccz=zipcode&zipcode=11236"),
    "east-flatbush":        ("East Flatbush",        "ccz=zipcode&zipcode=11203"),
    "flatbush":             ("Flatbush",             "ccz=zipcode&zipcode=11226,11210"),
    "flatlands":            ("Flatlands",            "ccz=zipcode&zipcode=11234"),
    "bergen-beach":         ("Bergen Beach",         "ccz=zipcode&zipcode=11234"),
    "marine-park":          ("Marine Park",          "ccz=zipcode&zipcode=11234"),
    "mill-basin":           ("Mill Basin",           "ccz=zipcode&zipcode=11234"),
    "georgetown-brooklyn":  ("Georgetown",           "ccz=zipcode&zipcode=11234"),
    # ── Long Island ──────────────────────────────────────────────────────────
    "long-island":          ("Long Island",          "county=Nassau,Suffolk"),
}

IDX_SECTION_TEMPLATE = """
  <!-- ═══════════════════════════════════════════════════════════════
       LIVE MLS LISTINGS — homes.gadurarealestate.com
       ═══════════════════════════════════════════════════════════════ -->
  <div id="idx-listings-section" style="margin:40px 0;padding:0;">
    <h2 style="color:#1B2A6B;border-bottom:3px solid #00A651;padding-bottom:8px;margin-bottom:6px;">
      Active Listings in {name}
    </h2>
    <p style="color:#555;font-size:.92rem;margin:0 0 14px;">
      Live MLS data via <a href="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest" target="_blank" rel="noopener" style="color:#00A651;font-weight:600;">OneKey® MLS</a> · Updated daily ·
      <a href="/map-available.html" style="color:#1B2A6B;">View on map →</a>
    </p>

    <!-- Loading bar -->
    <div id="idx-loading-bar" style="background:#f0f4ff;border:2px solid #e0e8ff;border-radius:8px;padding:20px;text-align:center;font-size:.95rem;color:#1B2A6B;">
      ⏳ Loading live {name} listings…
    </div>

    <!-- iFrame embed -->
    <iframe
      id="idx-embed-frame"
      src="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest"
      width="100%" height="820" frameborder="0" scrolling="yes"
      title="Homes for Sale in {name} — Live MLS Listings"
      style="display:none;border:none;width:100%;height:820px;border-radius:8px;overflow:hidden;"
      loading="lazy" allow="geolocation"
    ></iframe>

    <!-- Fallback CTA (shows if iFrame blocked) -->
    <div id="idx-fallback" style="display:none;background:#f8f9ff;border:1px solid #dce4ff;border-radius:10px;padding:28px;text-align:center;">
      <p style="font-size:1.05rem;color:#1B2A6B;font-weight:700;margin:0 0 8px;">Browse {name} Homes For Sale</p>
      <p style="color:#555;font-size:.9rem;margin:0 0 18px;">Click below to open live MLS listings in a new tab.</p>
      <a href="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest"
         target="_blank" rel="noopener"
         style="display:inline-block;background:#00A651;color:#fff;padding:12px 28px;border-radius:6px;font-weight:700;text-decoration:none;font-size:1rem;margin:4px;">
        View Active Listings →
      </a>
      <a href="/map-available.html"
         style="display:inline-block;background:#1B2A6B;color:#fff;padding:12px 28px;border-radius:6px;font-weight:700;text-decoration:none;font-size:1rem;margin:4px;">
        Map Search →
      </a>
    </div>

    <script>
    (function() {{
      var frame   = document.getElementById('idx-embed-frame');
      var loader  = document.getElementById('idx-loading-bar');
      var fallback= document.getElementById('idx-fallback');
      var loaded  = false;

      frame.addEventListener('load', function() {{
        loaded = true;
        loader.style.display  = 'none';
        frame.style.display   = 'block';
      }});

      setTimeout(function() {{
        if (!loaded) {{
          loader.style.display   = 'none';
          fallback.style.display = 'block';
        }}
      }}, 11000);
    }})();
    </script>
  </div>
  <!-- ═══════════════════════════════════════════════════════════════ -->
"""

def inject_idx(filepath, name, params):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    # Skip if already has IDX section
    if "idx-listings-section" in html or "idx-embed-frame" in html:
        return "SKIP (already has IDX)"

    section = IDX_SECTION_TEMPLATE.format(name=name, params=params)

    # Strategy: insert before the first <h2 inside the main content div
    # Look for the main content wrapper
    insert_markers = [
        # After the hero / stats block — find the first <div style="max-width:1100px
        r'(<div[^>]*max-width:1100px[^>]*>)',
        # Or after the first breadcrumb/hero section — before the first <h2
        r'(<h2[^>]*color:#1B2A6B[^>]*>Why )',
    ]

    injected = False
    for pattern in insert_markers:
        match = re.search(pattern, html)
        if match:
            insert_pos = match.start()
            # For the first pattern, insert AFTER the opening div tag
            if 'max-width:1100px' in pattern:
                insert_pos = match.end()
            html = html[:insert_pos] + section + html[insert_pos:]
            injected = True
            break

    if not injected:
        # Fallback: insert before </main> or before the footer
        for tag in ['</main>', '<footer', '<div class="legal"']:
            if tag in html:
                idx = html.index(tag)
                html = html[:idx] + section + html[idx:]
                injected = True
                break

    if not injected:
        return "SKIP (no insertion point found)"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return "DONE"


def main():
    html_files = [f for f in os.listdir(BASE) if f.endswith(".html")]
    results = {"done": [], "skipped": [], "missing": []}

    for fname in sorted(html_files):
        slug = fname.replace(".html", "")
        filepath = os.path.join(BASE, fname)

        if slug not in NEIGHBORHOODS:
            results["missing"].append(slug)
            continue

        name, params = NEIGHBORHOODS[slug]
        result = inject_idx(filepath, name, params)

        if result.startswith("DONE"):
            results["done"].append(slug)
            print(f"  ✅  {slug}")
        else:
            results["skipped"].append(f"{slug} ({result})")
            print(f"  ⏭  {slug} — {result}")

    print(f"\n{'='*55}")
    print(f"  Updated : {len(results['done'])} pages")
    print(f"  Skipped : {len(results['skipped'])} pages")
    print(f"  No map  : {len(results['missing'])} slugs (not in data map)")
    if results["missing"]:
        print("  Missing slugs:", ", ".join(results["missing"]))

if __name__ == "__main__":
    main()
