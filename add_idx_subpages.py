#!/usr/bin/env python3
"""
Inject live IDX iFrame sections into all neighborhood sub-pages.
Inserts before <footer so it appears at the bottom of content.
"""

import os, re

BASE = "/Users/nidhigadura/Jagex/gadura-realestate/neighborhoods"

# Parent neighborhood folder → (display_name, IDX params)
PARENT_MAP = {
    "arverne":           ("Arverne",              "ccz=zipcode&zipcode=11692"),
    "astoria":           ("Astoria",              "ccz=zipcode&zipcode=11102,11103,11105,11106"),
    "baldwin":           ("Baldwin",              "ccz=zipcode&zipcode=11510"),
    "bayside":           ("Bayside",              "ccz=zipcode&zipcode=11359,11360,11361"),
    "bellerose":         ("Bellerose",            "ccz=zipcode&zipcode=11426"),
    "bethpage":          ("Bethpage",             "ccz=zipcode&zipcode=11714"),
    "briarwood":         ("Briarwood",            "ccz=zipcode&zipcode=11435"),
    "cambria-heights":   ("Cambria Heights",      "ccz=zipcode&zipcode=11411"),
    "carle-place":       ("Carle Place",          "ccz=zipcode&zipcode=11514"),
    "corona":            ("Corona",               "ccz=zipcode&zipcode=11368"),
    "douglaston":        ("Douglaston",           "ccz=zipcode&zipcode=11363"),
    "east-meadow":       ("East Meadow",          "ccz=zipcode&zipcode=11554"),
    "east-rockaway":     ("East Rockaway",        "ccz=zipcode&zipcode=11518"),
    "elmhurst":          ("Elmhurst",             "ccz=zipcode&zipcode=11373"),
    "elmont":            ("Elmont",               "ccz=zipcode&zipcode=11003"),
    "far-rockaway":      ("Far Rockaway",         "ccz=zipcode&zipcode=11691,11694"),
    "farmingdale":       ("Farmingdale",          "ccz=zipcode&zipcode=11735"),
    "floral-park":       ("Floral Park",          "ccz=zipcode&zipcode=11001,11004"),
    "flushing":          ("Flushing",             "ccz=zipcode&zipcode=11354,11355,11356,11357,11358"),
    "forest-hills":      ("Forest Hills",         "ccz=zipcode&zipcode=11375"),
    "franklin-square":   ("Franklin Square",      "ccz=zipcode&zipcode=11010"),
    "freeport":          ("Freeport",             "ccz=zipcode&zipcode=11520"),
    "fresh-meadows":     ("Fresh Meadows",        "ccz=zipcode&zipcode=11365,11366"),
    "garden-city":       ("Garden City",          "ccz=zipcode&zipcode=11530"),
    "glen-oaks":         ("Glen Oaks",            "ccz=zipcode&zipcode=11004"),
    "glendale":          ("Glendale",             "ccz=zipcode&zipcode=11385"),
    "great-neck":        ("Great Neck",           "ccz=zipcode&zipcode=11020,11021,11023,11024"),
    "hempstead":         ("Hempstead",            "ccz=zipcode&zipcode=11550,11551"),
    "hewlett":           ("Hewlett",              "ccz=zipcode&zipcode=11557"),
    "hicksville":        ("Hicksville",           "ccz=zipcode&zipcode=11801"),
    "hollis":            ("Hollis",               "ccz=zipcode&zipcode=11423"),
    "holliswood":        ("Holliswood",           "ccz=zipcode&zipcode=11423"),
    "howard-beach":      ("Howard Beach",         "ccz=zipcode&zipcode=11414"),
    "inwood":            ("Inwood",               "ccz=zipcode&zipcode=11096"),
    "jackson-heights":   ("Jackson Heights",      "ccz=zipcode&zipcode=11372"),
    "jamaica":           ("Jamaica",              "ccz=zipcode&zipcode=11432,11433,11434,11435,11436"),
    "jamaica-estates":   ("Jamaica Estates",      "ccz=zipcode&zipcode=11432"),
    "jericho":           ("Jericho",              "ccz=zipcode&zipcode=11753"),
    "kew-gardens":       ("Kew Gardens",          "ccz=zipcode&zipcode=11415"),
    "laurelton":         ("Laurelton",            "ccz=zipcode&zipcode=11413"),
    "levittown":         ("Levittown",            "ccz=zipcode&zipcode=11756"),
    "little-neck":       ("Little Neck",          "ccz=zipcode&zipcode=11362"),
    "long-beach":        ("Long Beach",           "ccz=zipcode&zipcode=11561"),
    "long-island-city":  ("Long Island City",     "ccz=zipcode&zipcode=11101"),
    "lynbrook":          ("Lynbrook",             "ccz=zipcode&zipcode=11563"),
    "malverne":          ("Malverne",             "ccz=zipcode&zipcode=11565"),
    "manhasset":         ("Manhasset",            "ccz=zipcode&zipcode=11030"),
    "maspeth":           ("Maspeth",              "ccz=zipcode&zipcode=11378"),
    "massapequa":        ("Massapequa",           "ccz=zipcode&zipcode=11758"),
    "merrick":           ("Merrick",              "ccz=zipcode&zipcode=11566"),
    "middle-village":    ("Middle Village",       "ccz=zipcode&zipcode=11379"),
    "mineola":           ("Mineola",              "ccz=zipcode&zipcode=11501"),
    "new-hyde-park":     ("New Hyde Park",        "ccz=zipcode&zipcode=11040,11042"),
    "north-woodmere":    ("North Woodmere",       "ccz=zipcode&zipcode=11581"),
    "oceanside":         ("Oceanside",            "ccz=zipcode&zipcode=11572"),
    "ozone-park":        ("Ozone Park",           "ccz=zipcode&zipcode=11416,11417"),
    "port-washington":   ("Port Washington",      "ccz=zipcode&zipcode=11050"),
    "queens-village":    ("Queens Village",       "ccz=zipcode&zipcode=11427,11428,11429"),
    "rego-park":         ("Rego Park",            "ccz=zipcode&zipcode=11374"),
    "richmond-hill":     ("Richmond Hill",        "ccz=zipcode&zipcode=11418,11419"),
    "ridgewood":         ("Ridgewood",            "ccz=zipcode&zipcode=11385"),
    "rockaway-beach":    ("Rockaway Beach",       "ccz=zipcode&zipcode=11693"),
    "rockville-centre":  ("Rockville Centre",     "ccz=zipcode&zipcode=11570"),
    "rosedale":          ("Rosedale",             "ccz=zipcode&zipcode=11422"),
    "roslyn":            ("Roslyn",               "ccz=zipcode&zipcode=11576"),
    "seaford":           ("Seaford",              "ccz=zipcode&zipcode=11783"),
    "south-jamaica":     ("South Jamaica",        "ccz=zipcode&zipcode=11433,11434"),
    "south-ozone-park":  ("South Ozone Park",     "ccz=zipcode&zipcode=11420"),
    "springfield-gardens":("Springfield Gardens", "ccz=zipcode&zipcode=11413"),
    "st-albans":         ("St. Albans",           "ccz=zipcode&zipcode=11412"),
    "sunnyside":         ("Sunnyside",            "ccz=zipcode&zipcode=11104"),
    "syosset":           ("Syosset",              "ccz=zipcode&zipcode=11791"),
    "uniondale":         ("Uniondale",            "ccz=zipcode&zipcode=11553"),
    "valley-stream":     ("Valley Stream",        "ccz=zipcode&zipcode=11580,11581,11582"),
    "wantagh":           ("Wantagh",              "ccz=zipcode&zipcode=11793"),
    "westbury":          ("Westbury",             "ccz=zipcode&zipcode=11590"),
    "whitestone":        ("Whitestone",           "ccz=zipcode&zipcode=11357"),
    "woodhaven":         ("Woodhaven",            "ccz=zipcode&zipcode=11421"),
    "woodmere":          ("Woodmere",             "ccz=zipcode&zipcode=11598"),
    "woodside":          ("Woodside",             "ccz=zipcode&zipcode=11377"),
}

# Brooklyn sub-neighborhood pages → their own zip codes
BROOKLYN_MAP = {
    "bay-ridge":                  ("Bay Ridge",                 "ccz=zipcode&zipcode=11209"),
    "bedford-stuyvesant":         ("Bed-Stuy",                  "ccz=zipcode&zipcode=11221,11233"),
    "bensonhurst":                ("Bensonhurst",               "ccz=zipcode&zipcode=11204,11214"),
    "borough-park":               ("Borough Park",              "ccz=zipcode&zipcode=11219"),
    "brighton-beach":             ("Brighton Beach",            "ccz=zipcode&zipcode=11235"),
    "brooklyn-heights":           ("Brooklyn Heights",          "ccz=zipcode&zipcode=11201"),
    "brownsville":                ("Brownsville",               "ccz=zipcode&zipcode=11212"),
    "bushwick":                   ("Bushwick",                  "ccz=zipcode&zipcode=11221,11237"),
    "canarsie":                   ("Canarsie",                  "ccz=zipcode&zipcode=11236"),
    "clinton-hill":               ("Clinton Hill",              "ccz=zipcode&zipcode=11238"),
    "cobble-hill":                ("Cobble Hill",               "ccz=zipcode&zipcode=11201"),
    "crown-heights":              ("Crown Heights",             "ccz=zipcode&zipcode=11213,11225"),
    "downtown-brooklyn":          ("Downtown Brooklyn",         "ccz=zipcode&zipcode=11201"),
    "dyker-heights":              ("Dyker Heights",             "ccz=zipcode&zipcode=11228"),
    "east-flatbush":              ("East Flatbush",             "ccz=zipcode&zipcode=11203"),
    "east-new-york":              ("East New York",             "ccz=zipcode&zipcode=11207,11208"),
    "flatbush":                   ("Flatbush",                  "ccz=zipcode&zipcode=11226,11210"),
    "flatlands":                  ("Flatlands",                 "ccz=zipcode&zipcode=11234"),
    "fort-greene":                ("Fort Greene",               "ccz=zipcode&zipcode=11205"),
    "georgetown-brooklyn":        ("Georgetown",                "ccz=zipcode&zipcode=11234"),
    "gravesend":                  ("Gravesend",                 "ccz=zipcode&zipcode=11223"),
    "greenpoint":                 ("Greenpoint",                "ccz=zipcode&zipcode=11222"),
    "kensington":                 ("Kensington",                "ccz=zipcode&zipcode=11218"),
    "marine-park":                ("Marine Park",               "ccz=zipcode&zipcode=11234"),
    "midwood":                    ("Midwood",                   "ccz=zipcode&zipcode=11230"),
    "mill-basin":                 ("Mill Basin",                "ccz=zipcode&zipcode=11234"),
    "park-slope":                 ("Park Slope",                "ccz=zipcode&zipcode=11215,11217"),
    "prospect-heights":           ("Prospect Heights",          "ccz=zipcode&zipcode=11238"),
    "prospect-lefferts-gardens":  ("Prospect Lefferts Gardens", "ccz=zipcode&zipcode=11225"),
    "red-hook":                   ("Red Hook",                  "ccz=zipcode&zipcode=11231"),
    "sheepshead-bay":             ("Sheepshead Bay",            "ccz=zipcode&zipcode=11235"),
    "sunset-park":                ("Sunset Park",               "ccz=zipcode&zipcode=11220,11232"),
    "williamsburg":               ("Williamsburg",              "ccz=zipcode&zipcode=11211,11249"),
    "windsor-terrace":            ("Windsor Terrace",           "ccz=zipcode&zipcode=11218"),
}

IDX_SECTION = """
<!-- ═══ LIVE IDX LISTINGS — homes.gadurarealestate.com ═══ -->
<section style="max-width:1100px;margin:40px auto;padding:0 20px 40px;">
  <h2 style="color:#1B2A6B;border-bottom:3px solid #00A651;padding-bottom:8px;margin-bottom:6px;">
    Active Listings in {name}
  </h2>
  <p style="color:#555;font-size:.92rem;margin:0 0 14px;">
    Live MLS data via <a href="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest" target="_blank" rel="noopener" style="color:#00A651;font-weight:600;">OneKey® MLS</a> · Updated daily ·
    <a href="/map-available.html" style="color:#1B2A6B;">View on map →</a>
  </p>

  <div id="idx-load-{uid}" style="background:#f0f4ff;border:2px solid #e0e8ff;border-radius:8px;padding:20px;text-align:center;color:#1B2A6B;font-size:.95rem;">
    ⏳ Loading live {name} listings…
  </div>

  <iframe
    id="idx-frame-{uid}"
    src="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest"
    width="100%" height="820" frameborder="0" scrolling="yes"
    title="Homes for Sale in {name} — Live MLS"
    style="display:none;border:none;width:100%;height:820px;border-radius:8px;"
    loading="lazy" allow="geolocation"
  ></iframe>

  <div id="idx-fall-{uid}" style="display:none;background:#f8f9ff;border:1px solid #dce4ff;border-radius:10px;padding:28px;text-align:center;">
    <p style="font-size:1.05rem;color:#1B2A6B;font-weight:700;margin:0 0 8px;">Browse {name} Homes For Sale</p>
    <p style="color:#555;font-size:.9rem;margin:0 0 18px;">Live MLS listings — opens in a new tab.</p>
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
  (function(){{
    var fr=document.getElementById('idx-frame-{uid}');
    var ld=document.getElementById('idx-load-{uid}');
    var fb=document.getElementById('idx-fall-{uid}');
    var ok=false;
    fr.addEventListener('load',function(){{ok=true;ld.style.display='none';fr.style.display='block';}});
    setTimeout(function(){{if(!ok){{ld.style.display='none';fb.style.display='block';}}}},11000);
  }})();
  </script>
</section>
<!-- ═══ END IDX LISTINGS ═══ -->
"""

def make_uid(filepath):
    # Short unique ID from path
    return re.sub(r'[^a-z0-9]', '', filepath.lower())[-12:]

def inject(filepath, name, params):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    if "idx-embed-frame" in html or "idx-frame-" in html or "idx-listings-section" in html:
        return "SKIP"

    uid = make_uid(filepath)
    section = IDX_SECTION.format(name=name, params=params, uid=uid)

    # Inject before <footer (consistent across all page types)
    if "<footer" in html:
        idx = html.index("<footer")
        html = html[:idx] + section + "\n" + html[idx:]
    elif "</body>" in html:
        idx = html.index("</body>")
        html = html[:idx] + section + "\n" + html[idx:]
    else:
        return "SKIP (no injection point)"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return "DONE"


def main():
    done, skipped, unknown = [], [], []

    for folder in sorted(os.listdir(BASE)):
        folder_path = os.path.join(BASE, folder)
        if not os.path.isdir(folder_path):
            continue

        # ── Brooklyn sub-neighborhood flat files ──────────────────────────
        if folder == "brooklyn":
            for fname in sorted(os.listdir(folder_path)):
                if not fname.endswith(".html") or fname == "index.html":
                    continue
                slug = fname.replace(".html", "")
                fpath = os.path.join(folder_path, fname)
                if slug in BROOKLYN_MAP:
                    name, params = BROOKLYN_MAP[slug]
                    r = inject(fpath, name, params)
                    (done if r == "DONE" else skipped).append(f"brooklyn/{slug}")
                    print(f"  {'✅' if r=='DONE' else '⏭ '} brooklyn/{slug} — {r}")
                else:
                    unknown.append(f"brooklyn/{slug}")
                    print(f"  ❓  brooklyn/{slug} — no map entry")
            continue

        # ── Deep sub-pages (buying-guide/, faq/, etc.) ────────────────────
        if folder not in PARENT_MAP:
            continue

        name, params = PARENT_MAP[folder]

        for root, dirs, files in os.walk(folder_path):
            for fname in sorted(files):
                if not fname.endswith(".html"):
                    continue
                fpath = os.path.join(root, fname)
                rel = fpath.replace(BASE + "/", "")
                r = inject(fpath, name, params)
                (done if r == "DONE" else skipped).append(rel)
                print(f"  {'✅' if r=='DONE' else '⏭ '} {rel} — {r}")

    print(f"\n{'='*55}")
    print(f"  Updated : {len(done)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Unknown : {len(unknown)}")
    if unknown:
        print("  Unknown:", ", ".join(unknown))

if __name__ == "__main__":
    main()
