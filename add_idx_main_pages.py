#!/usr/bin/env python3
"""
Add live IDX iFrame sections to all remaining top-level content pages.
Each page gets a search filter relevant to that page's context.
"""

import os, re

BASE = "/Users/nidhigadura/Jagex/gadura-realestate"

# page filename → (section heading, IDX search params, context blurb)
PAGES = {
    # ── High-traffic content pages ──────────────────────────────────────────
    "sell.html": (
        "What's Selling Near You Right Now",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421,11413,11422,11412,11423,11432,11433,11434&statusCategory=active&srt=newest",
        "See what comparable homes in your area are listed for today — real-time pricing data to set your strategy."
    ),
    "map-sold.html": (
        "Recently Sold Homes — Queens & Long Island",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421,11413,11422&statusCategory=active&srt=newest",
        "Browse current active listings alongside our sales history."
    ),
    "hindi-speaking-real-estate-agent-queens.html": (
        "Active Listings in Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Browse available homes across Queens and Long Island — updated daily from OneKey® MLS."
    ),
    "punjabi-speaking-real-estate-agent-queens.html": (
        "Active Listings in Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Browse available homes across Queens and Long Island — updated daily from OneKey® MLS."
    ),
    "resources.html": (
        "Browse Active Listings",
        "county=Queens&statusCategory=active&srt=newest",
        "Find your next home while using our buyer and seller resources."
    ),
    "neighborhoods.html": (
        "Search All Queens & Long Island Listings",
        "county=Queens&statusCategory=active&srt=newest",
        "Live MLS search across every neighborhood we serve."
    ),
    "portal.html": (
        "Live MLS Search — Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Full MLS access powered by OneKey® MLS via IDX Broker."
    ),
    # ── Agent / company pages ────────────────────────────────────────────────
    "about.html": (
        "Our Current Listings",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421&statusCategory=active&srt=newest",
        "Active listings from Gadura Real Estate, LLC — updated daily."
    ),
    "reviews.html": (
        "See What's Available Now",
        "county=Queens&statusCategory=active&srt=newest&lp=600000&hp=1500000",
        "Ready to be the next success story? Browse active listings and call us today."
    ),
    "meet-the-agents.html": (
        "Our Active Listings",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421&statusCategory=active&srt=newest",
        "Properties currently listed by Gadura Real Estate agents."
    ),
    "agents.html": (
        "Our Active Listings",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421&statusCategory=active&srt=newest",
        "Properties currently listed by our team — updated daily."
    ),
    "contact.html": (
        "Browse Active Listings Before You Call",
        "county=Queens&statusCategory=active&srt=newest",
        "See what's available in your target neighborhood, then reach out and we'll set up a showing."
    ),
    # ── Contextual article pages ─────────────────────────────────────────────
    "1031-exchange-queens.html": (
        "Investment & Multi-Family Listings — Queens & Long Island",
        "pt=2&county=Queens&statusCategory=active&srt=newest",
        "Browse multi-family and investment properties eligible for 1031 exchange — updated daily."
    ),
    "closing-costs-nyc-guide.html": (
        "Active Listings in Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest&lp=500000&hp=1200000",
        "Now that you know your closing costs — browse what's available in your budget."
    ),
    "coop-board-package-help-queens.html": (
        "Co-op Listings in Queens",
        "pt=3&county=Queens&statusCategory=active&srt=newest",
        "Browse available co-ops in Queens — we handle the board package from start to finish."
    ),
    "divorce-home-sale-queens.html": (
        "Active Listings — Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Whether buying out a spouse or finding your next home, browse available properties."
    ),
    "flat-fee-vs-full-service.html": (
        "See What Full-Service Listings Look Like",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421&statusCategory=active&srt=newest",
        "Our current full-service listings — professional photos, MLS exposure, and expert negotiation."
    ),
    "fsbo-selling-without-broker-nyc.html": (
        "See How Professional Listings Compare",
        "ccz=zipcode&zipcode=11416,11417,11418,11419,11420,11414,11421&statusCategory=active&srt=newest",
        "Our active listings — full MLS exposure, professional photography, and expert pricing strategy."
    ),
    "inherited-property-sale-queens.html": (
        "Active Listings — Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Whether selling an inherited home or finding your next one, we can help."
    ),
    "senior-downsizing-queens.html": (
        "Condos & Co-ops for Downsizing — Queens & Long Island",
        "pt=3,4&county=Queens&statusCategory=active&srt=newest&bd=1&bd_max=2",
        "Browse 1–2 bedroom condos and co-ops in Queens — ideal for downsizing buyers."
    ),
    "short-sale-queens-ny.html": (
        "Active Listings — Queens & Long Island",
        "county=Queens&statusCategory=active&srt=newest",
        "Browse available homes in your target area while we work through the short sale process."
    ),
}

IDX_SECTION = """\n
<!-- ═══ LIVE IDX LISTINGS — homes.gadurarealestate.com ═══ -->
<section style="max-width:1100px;margin:40px auto;padding:0 20px 40px;">
  <h2 style="color:#1B2A6B;border-bottom:3px solid #00A651;padding-bottom:8px;margin-bottom:6px;">
    {heading}
  </h2>
  <p style="color:#555;font-size:.92rem;margin:0 0 14px;">
    {blurb}
    <a href="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&statusCategory=active&srt=newest"
       target="_blank" rel="noopener" style="color:#00A651;font-weight:600;"> View full search →</a> ·
    <a href="/map-available.html" style="color:#1B2A6B;">Map search →</a>
  </p>

  <div id="idx-load-{uid}" style="background:#f0f4ff;border:2px solid #e0e8ff;border-radius:8px;padding:20px;text-align:center;color:#1B2A6B;font-size:.95rem;">
    ⏳ Loading live listings…
  </div>

  <iframe
    id="idx-frame-{uid}"
    src="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&srt=newest"
    width="100%" height="820" frameborder="0" scrolling="yes"
    title="{heading}"
    style="display:none;border:none;width:100%;height:820px;border-radius:8px;"
    loading="lazy" allow="geolocation"
  ></iframe>

  <div id="idx-fall-{uid}" style="display:none;background:#f8f9ff;border:1px solid #dce4ff;border-radius:10px;padding:28px;text-align:center;">
    <p style="font-size:1.05rem;color:#1B2A6B;font-weight:700;margin:0 0 8px;">{heading}</p>
    <p style="color:#555;font-size:.9rem;margin:0 0 18px;">{blurb}</p>
    <a href="https://homes.gadurarealestate.com/idx/search/advanced?idxID=a001&{params}&srt=newest"
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

def make_uid(slug):
    return re.sub(r'[^a-z0-9]', '', slug)[:14]

def inject(filepath, heading, params, blurb):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    if "idx-embed-frame" in html or "idx-frame-" in html or "idx-listings-section" in html:
        return "SKIP (already has IDX)"

    uid  = make_uid(os.path.basename(filepath).replace(".html",""))
    blurb_safe = blurb.replace("{","{{").replace("}","}}")
    section = IDX_SECTION.format(heading=heading, params=params, blurb=blurb, uid=uid)

    if "<footer" in html:
        idx = html.index("<footer")
        html = html[:idx] + section + html[idx:]
    elif "</body>" in html:
        idx = html.index("</body>")
        html = html[:idx] + section + html[idx:]
    else:
        return "SKIP (no injection point)"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return "DONE"

def main():
    done, skipped = [], []
    for fname, (heading, params, blurb) in PAGES.items():
        fpath = os.path.join(BASE, fname)
        if not os.path.exists(fpath):
            print(f"  ⚠️  {fname} — FILE NOT FOUND")
            continue
        r = inject(fpath, heading, params, blurb)
        icon = "✅" if r == "DONE" else "⏭ "
        print(f"  {icon} {fname} — {r}")
        (done if r == "DONE" else skipped).append(fname)

    print(f"\n{'='*55}")
    print(f"  Updated : {len(done)}")
    print(f"  Skipped : {len(skipped)}")

if __name__ == "__main__":
    main()
