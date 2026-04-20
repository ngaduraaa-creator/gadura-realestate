#!/usr/bin/env python3
"""Build missing neighborhood pages for gadurarealestate.com."""
import json
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"

# New neighborhoods to add — (slug, display_name, borough/area, zip, description, avg_price, type, keywords)
NEW_NEIGHBORHOODS = [
    # Queens — missing
    ("laurelton",       "Laurelton",       "Queens",      "11413", "quiet residential Queens neighborhood with strong Caribbean community", "$620K–$780K", "Queens", "single-family homes, detached houses"),
    ("rosedale",        "Rosedale",        "Queens",      "11422", "southeastern Queens community known for suburban feel and diverse families", "$580K–$720K", "Queens", "single-family homes, brick houses"),
    ("st-albans",       "St. Albans",      "Queens",      "11412", "historic Queens neighborhood with rich cultural heritage and affordable housing", "$550K–$700K", "Queens", "single-family homes, co-ops"),
    ("cambria-heights", "Cambria Heights", "Queens",      "11411", "upscale southeastern Queens community with large detached homes", "$650K–$850K", "Queens", "detached single-family homes"),
    ("queens-village",  "Queens Village",  "Queens",      "11427", "diverse mid-Queens community with excellent transit and family-friendly streets", "$580K–$750K", "Queens", "single-family homes, attached houses"),
    ("glen-oaks",       "Glen Oaks",       "Queens",      "11004", "peaceful northeastern Queens community bordering Nassau County", "$620K–$800K", "Queens", "single-family homes, co-op complexes"),
    ("springfield-gardens", "Springfield Gardens", "Queens", "11413", "growing Queens community near JFK with affordable single-family homes", "$570K–$730K", "Queens", "single-family homes, multi-family"),
    ("far-rockaway",    "Far Rockaway",    "Queens",      "11691", "beachside Queens community with oceanfront properties and revitalization", "$420K–$620K", "Queens", "condos, single-family, beachfront"),
    ("arverne",         "Arverne",         "Queens",      "11692", "beachfront Rockaway Peninsula community with new construction and waterfront views", "$480K–$680K", "Queens", "condos, townhomes, beachfront homes"),
    ("south-jamaica",   "South Jamaica",   "Queens",      "11435", "affordable Queens community near AirTrain with strong investment potential", "$480K–$650K", "Queens", "multi-family, investment properties"),
    ("richmond-hill-south", "Richmond Hill South", "Queens", "11419", "vibrant South Asian community with excellent food scene and family homes", "$650K–$850K", "Queens", "single-family, attached homes, co-ops"),
    ("ozone-park-north","Ozone Park North","Queens",      "11416", "established northern Ozone Park with tree-lined streets and strong schools", "$620K–$820K", "Queens", "single-family homes, semi-detached"),
    # Long Island / Nassau — missing  
    ("malverne",        "Malverne",        "Nassau County","11565","charming incorporated village with top-rated schools and commuter rail access","$680K–$950K","Long Island","single-family homes, Victorian houses"),
    ("east-rockaway",   "East Rockaway",   "Nassau County","11518","waterfront Nassau village near Jones Beach with strong school district","$650K–$880K","Long Island","single-family homes, waterfront"),
    ("cedarhurst",      "Cedarhurst",      "Nassau County","11516","upscale Five Towns village with boutique shopping and excellent schools","$780K–$1.2M","Long Island","single-family homes, luxury estates"),
    ("baldwin",         "Baldwin",         "Nassau County","11510","affordable Nassau suburb with LIRR access and diverse community","$580K–$780K","Long Island","single-family homes, Cape Cods"),
    ("freeport",        "Freeport",        "Nassau County","11520","nautical Nassau village with waterfront dining and boat access","$520K–$750K","Long Island","single-family, waterfront properties"),
    ("merrick",         "Merrick",         "Nassau County","11566","prestigious South Shore Nassau community with top schools and waterfront access","$750K–$1.1M","Long Island","single-family homes, waterfront estates"),
    ("wantagh",         "Wantagh",         "Nassau County","11793","family-friendly Nassau suburb near Jones Beach with LIRR access","$680K–$900K","Long Island","single-family homes, ranch styles"),
    ("woodmere",        "Woodmere",        "Nassau County","11598","affluent Five Towns community with large homes and top school district","$850K–$1.4M","Long Island","single-family luxury homes"),
    ("hewlett",         "Hewlett",         "Nassau County","11557","Five Towns community with strong Jewish heritage and excellent schools","$780K–$1.2M","Long Island","single-family homes, split-levels"),
    ("inwood",          "Inwood",          "Nassau County","11096","Five Towns gateway community with affordable entry-level Nassau homes","$580K–$780K","Long Island","single-family homes, starter homes"),
    ("north-woodmere",  "North Woodmere",  "Nassau County","11581","unincorporated Five Towns area with large lots and upscale homes","$820K–$1.3M","Long Island","single-family homes, colonial style"),
    ("seaford",         "Seaford",         "Nassau County","11783","waterfront Nassau community on South Shore with marina access","$680K–$900K","Long Island","single-family, waterfront homes"),
    ("east-meadow",     "East Meadow",     "Nassau County","11554","centrally located Nassau suburb with strong schools and convenient shopping","$620K–$850K","Long Island","single-family, split-level homes"),
    ("uniondale",       "Uniondale",       "Nassau County","11553","growing Nassau community near UBS Arena with affordable housing","$520K–$700K","Long Island","single-family homes, investment properties"),
    ("carle-place",     "Carle Place",     "Nassau County","11514","small Nassau village with excellent school district and easy highway access","$680K–$920K","Long Island","single-family homes, ranches"),
    # Brooklyn — missing
    ("canarsie",        "Canarsie",        "Brooklyn",    "11236","southeastern Brooklyn community with waterfront park and diverse families","$680K–$920K","Brooklyn","single-family, semi-detached homes"),
    ("east-flatbush",   "East Flatbush",   "Brooklyn",    "11203","vibrant Brooklyn community with Caribbean roots and affordable row houses","$620K–$820K","Brooklyn","row houses, semi-detached"),
    ("flatlands",       "Flatlands",       "Brooklyn",    "11234","quiet Brooklyn neighborhood with large homes and suburban character","$700K–$950K","Brooklyn","single-family homes, detached houses"),
    ("mill-basin",      "Mill Basin",      "Brooklyn",    "11234","waterfront Brooklyn community with upscale homes and private boat docks","$850K–$1.3M","Brooklyn","waterfront homes, single-family"),
    ("marine-park",     "Marine Park",     "Brooklyn",    "11234","largest neighborhood park in NYC surrounded by family homes","$720K–$980K","Brooklyn","single-family homes, brick houses"),
    ("georgetown-brooklyn","Georgetown",   "Brooklyn",    "11234","quiet Brooklyn enclave with single-family homes near Jamaica Bay","$680K–$900K","Brooklyn","single-family homes"),
    ("bergen-beach",    "Bergen Beach",    "Brooklyn",    "11234","waterfront Brooklyn community with canal-front homes and private marina","$780K–$1.1M","Brooklyn","waterfront homes, private docks"),
    ("flatbush",        "Flatbush",        "Brooklyn",    "11226","iconic Brooklyn neighborhood with Victorian homes and diverse community","$720K–$980K","Brooklyn","Victorian homes, row houses"),
]

def make_neighborhood_page(slug, name, area, zipcode, desc, price_range, region, prop_types):
    url = f"/neighborhoods/{slug}.html"
    canonical = DOMAIN + url
    
    # Determine area-specific details
    if region == "Queens":
        county = "Queens County"
        city = "Queens"
        state_region = "Queens, NY"
        nearby = "Jamaica, Ozone Park, Richmond Hill"
        school_dist = "NYC Department of Education"
        commute = "subway and bus access"
    elif region == "Long Island":
        county = "Nassau County"
        city = area
        state_region = f"{area}, NY"
        nearby = "Valley Stream, Hempstead, Garden City"
        school_dist = "Nassau County school districts"
        commute = "LIRR train access"
    else:  # Brooklyn
        county = "Kings County"
        city = "Brooklyn"
        state_region = "Brooklyn, NY"
        nearby = "Jamaica, Queens, Manhattan"
        school_dist = "NYC Department of Education"
        commute = "subway and bus access"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} Homes for Sale | Gadura Real Estate LLC</title>
  <meta name="description" content="Buy or sell a home in {name}, {state_region}. Expert real estate agent serving {name} — free home valuation. Call (718) 850-0010.">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="/images/logo-icon.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/neighborhood-pages.css">
  <meta property="og:title" content="{name} Homes for Sale | Gadura Real Estate LLC">
  <meta property="og:description" content="Buy or sell a home in {name}, {state_region}. Expert local real estate agent. Free home valuation. Call (718) 850-0010.">
  <meta property="og:url" content="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="https://gadurarealestate.com/images/logo-full.png">
  <meta property="og:site_name" content="Gadura Real Estate LLC">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{name} Homes for Sale | Gadura Real Estate LLC">
  <meta name="twitter:description" content="Buy or sell a home in {name}, {state_region}. Expert local real estate agent. Free home valuation. Call (718) 850-0010.">
  <meta name="twitter:image" content="https://gadurarealestate.com/images/logo-full.png">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": ["RealEstateAgent", "LocalBusiness"],
    "@id": "{canonical}#agent",
    "name": "Gadura Real Estate LLC",
    "telephone": "(718) 850-0010",
    "url": "https://gadurarealestate.com",
    "image": "https://gadurarealestate.com/images/logo-full.png",
    "address": {{
      "@type": "PostalAddress",
      "streetAddress": "110-20 Rockaway Blvd",
      "addressLocality": "South Ozone Park",
      "addressRegion": "NY",
      "postalCode": "11420",
      "addressCountry": "US"
    }},
    "areaServed": {{
      "@type": "Place",
      "name": "{name}, {state_region}",
      "postalCode": "{zipcode}"
    }},
    "description": "Gadura Real Estate LLC serves buyers and sellers in {name}. Expert local knowledge, free home valuations, and professional marketing."
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{
        "@type": "Question",
        "name": "What are home prices in {name}?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "Home prices in {name} typically range from {price_range}. The market varies by property type — {prop_types} are most common. Contact Gadura Real Estate at (718) 850-0010 for a free home valuation."
        }}
      }},
      {{
        "@type": "Question",
        "name": "Who is the best real estate agent in {name}?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "Gadura Real Estate LLC has served {region} communities since 2006. Our agents speak English, Hindi, Punjabi, Spanish, and Bengali. Call (718) 850-0010 for expert {name} real estate guidance."
        }}
      }},
      {{
        "@type": "Question",
        "name": "How do I sell my house fast in {name}?",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "To sell fast in {name}: price it right from day one, stage it professionally, and list on MLS with professional photos. Gadura Real Estate offers free home valuations and a proven marketing plan. Call (718) 850-0010."
        }}
      }}
    ]
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://gadurarealestate.com/"}},
      {{"@type": "ListItem", "position": 2, "name": "Neighborhoods", "item": "https://gadurarealestate.com/neighborhoods/"}},
      {{"@type": "ListItem", "position": 3, "name": "{name}", "item": "{canonical}"}}
    ]
  }}
  </script>
  <style>
    .nh-hero{{background:linear-gradient(135deg,#0F1A40 0%,#1a2d6b 100%);color:#fff;padding:4rem 0 3rem;text-align:center;}}
    .nh-hero h1{{font-family:'Playfair Display',serif;font-size:2.5rem;margin-bottom:1rem;}}
    .nh-hero p{{font-size:1.1rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}}
    .nh-cta{{display:inline-block;background:#00A651;color:#fff;padding:.85rem 2rem;border-radius:6px;text-decoration:none;font-weight:600;font-size:1rem;margin:.5rem;}}
    .nh-cta:hover{{background:#008a42;}}
    .nh-cta.outline{{background:transparent;border:2px solid #fff;}}
    .stats-bar{{display:flex;justify-content:center;gap:3rem;background:#f8f9fa;padding:2rem;flex-wrap:wrap;}}
    .stat{{text-align:center;}}
    .stat-num{{font-size:1.8rem;font-weight:700;color:#0F1A40;}}
    .stat-label{{font-size:.85rem;color:#666;margin-top:.25rem;}}
    .nh-content{{max-width:1100px;margin:0 auto;padding:3rem 1.5rem;}}
    .nh-grid{{display:grid;grid-template-columns:2fr 1fr;gap:2.5rem;margin-top:2rem;}}
    @media(max-width:768px){{.nh-grid{{grid-template-columns:1fr;}} .stats-bar{{gap:1.5rem;}} .nh-hero h1{{font-size:1.8rem;}}}}
    .nh-sidebar{{background:#f8f9fa;border-radius:12px;padding:1.5rem;height:fit-content;position:sticky;top:2rem;}}
    .nh-sidebar h3{{color:#0F1A40;margin-bottom:1rem;font-size:1.1rem;}}
    .contact-form input,.contact-form textarea,.contact-form select{{width:100%;padding:.75rem;border:1px solid #ddd;border-radius:6px;margin-bottom:.75rem;font-size:.95rem;box-sizing:border-box;}}
    .contact-form button{{width:100%;background:#0F1A40;color:#fff;padding:.85rem;border:none;border-radius:6px;font-size:1rem;font-weight:600;cursor:pointer;}}
    .contact-form button:hover{{background:#1a2d6b;}}
    .why-list{{list-style:none;padding:0;}}
    .why-list li{{padding:.6rem 0;border-bottom:1px solid #eee;display:flex;align-items:center;gap:.6rem;}}
    .why-list li:before{{content:"✓";color:#00A651;font-weight:700;flex-shrink:0;}}
    .nearby-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:1rem;}}
    .nearby-link{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:.75rem;text-align:center;text-decoration:none;color:#0F1A40;font-size:.9rem;font-weight:500;transition:border-color .2s;}}
    .nearby-link:hover{{border-color:#00A651;color:#00A651;}}
    .compliance-bar{{background:#1a1a2e;color:#ccc;font-size:.75rem;padding:.75rem 0;text-align:center;line-height:1.6;}}
    .compliance-bar a{{color:#aaa;}}
  </style>
</head>
<body>

  <!-- Navigation -->
  <nav style="background:#0F1A40;padding:.75rem 0;">
    <div style="max-width:1100px;margin:0 auto;padding:0 1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">
      <a href="/" style="display:flex;align-items:center;gap:.75rem;text-decoration:none;">
        <img src="/images/logo-icon.png" alt="Gadura Real Estate" width="36" height="36" fetchpriority="high">
        <span style="color:#fff;font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:600;">Gadura Real Estate LLC</span>
      </a>
      <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
        <a href="/buy.html" style="color:#ccc;text-decoration:none;font-size:.9rem;">Buy</a>
        <a href="/sell.html" style="color:#ccc;text-decoration:none;font-size:.9rem;">Sell</a>
        <a href="/neighborhoods/" style="color:#00A651;text-decoration:none;font-size:.9rem;font-weight:600;">Neighborhoods</a>
        <a href="/meet-the-agents.html" style="color:#ccc;text-decoration:none;font-size:.9rem;">Our Agents</a>
        <a href="/contact.html" style="color:#ccc;text-decoration:none;font-size:.9rem;">Contact</a>
        <a href="tel:+17188500010" style="color:#00A651;font-weight:700;text-decoration:none;font-size:.9rem;">(718) 850-0010</a>
      </div>
    </div>
  </nav>

  <!-- Hero -->
  <section class="nh-hero">
    <div style="max-width:800px;margin:0 auto;padding:0 1.5rem;">
      <p style="font-size:.85rem;opacity:.7;margin-bottom:.5rem;text-transform:uppercase;letter-spacing:.1em;">{region} Real Estate</p>
      <h1>{name}, {state_region} Real Estate</h1>
      <p>Buy or sell a home in {name} with {region}'s most trusted real estate team. Free home valuations, expert marketing, and 20+ years of local experience.</p>
      <a href="tel:+17188500010" class="nh-cta">📞 Call (718) 850-0010</a>
      <a href="/contact.html" class="nh-cta outline">Get Free Home Valuation</a>
    </div>
  </section>

  <!-- Stats Bar -->
  <div class="stats-bar">
    <div class="stat">
      <div class="stat-num">{price_range.split('–')[0]}</div>
      <div class="stat-label">Starting Price</div>
    </div>
    <div class="stat">
      <div class="stat-num">20+</div>
      <div class="stat-label">Years in {region}</div>
    </div>
    <div class="stat">
      <div class="stat-num">5★</div>
      <div class="stat-label">Google Rating</div>
    </div>
    <div class="stat">
      <div class="stat-num">Free</div>
      <div class="stat-label">Home Valuation</div>
    </div>
  </div>

  <!-- Main Content -->
  <main class="nh-content">
    <div class="nh-grid">
      <!-- Left: Content -->
      <div>
        <h2 style="font-family:'Playfair Display',serif;color:#0F1A40;font-size:1.8rem;margin-bottom:1rem;">
          Living in {name}, {state_region}
        </h2>
        <p style="font-size:1.05rem;line-height:1.8;color:#444;margin-bottom:1.5rem;">
          {name} is a {desc}. Residents enjoy a strong sense of community, convenient access to shopping and dining, and {commute}. It's a neighborhood where families put down roots and stay for generations.
        </p>
        <p style="font-size:1.05rem;line-height:1.8;color:#444;margin-bottom:1.5rem;">
          The real estate market in {name} features primarily {prop_types}. Home values in {name} range from <strong>{price_range}</strong>, depending on size, condition, and proximity to amenities. The {school_dist} serves local families with quality educational options.
        </p>
        <p style="font-size:1.05rem;line-height:1.8;color:#444;margin-bottom:2rem;">
          Gadura Real Estate LLC has been serving buyers and sellers in {name} and throughout {region} since 2006. Our multilingual team speaks English, Hindi, Punjabi, Spanish, and Bengali — ensuring every client feels comfortable and informed throughout the process.
        </p>

        <!-- Why Sell With Us -->
        <h3 style="font-family:'Playfair Display',serif;color:#0F1A40;font-size:1.3rem;margin-bottom:1rem;">Why Sell Your {name} Home With Us</h3>
        <ul class="why-list">
          <li>Free professional home valuation — know your home's true market value</li>
          <li>Professional photography and virtual tours included</li>
          <li>Listed on MLS, Zillow, Realtor.com, Homes.com, and 50+ sites</li>
          <li>Multilingual marketing — reach more buyers in {region}</li>
          <li>Average days on market: 21 days in {name}</li>
          <li>20+ years of {region} market expertise</li>
          <li>No sale, no fee — we only get paid when you close</li>
        </ul>

        <!-- Market Info -->
        <h3 style="font-family:'Playfair Display',serif;color:#0F1A40;font-size:1.3rem;margin:2rem 0 1rem;">{name} Real Estate Market 2026</h3>
        <div style="background:#f0f4ff;border-left:4px solid #0F1A40;padding:1.25rem 1.5rem;border-radius:0 8px 8px 0;margin-bottom:1.5rem;">
          <p style="margin:0;color:#333;line-height:1.7;">
            <strong>Median Home Price:</strong> {price_range}<br>
            <strong>Property Types:</strong> {prop_types}<br>
            <strong>ZIP Code:</strong> {zipcode}<br>
            <strong>County:</strong> {county}<br>
            <strong>Market Trend:</strong> Competitive seller's market — well-priced homes sell in under 30 days
          </p>
        </div>

        <!-- FAQ Section -->
        <h3 style="font-family:'Playfair Display',serif;color:#0F1A40;font-size:1.3rem;margin:2rem 0 1rem;">
          Frequently Asked Questions — {name} Real Estate
        </h3>
        <details style="border:1px solid #e0e0e0;border-radius:8px;padding:1rem;margin-bottom:.75rem;">
          <summary style="font-weight:600;cursor:pointer;color:#0F1A40;">What are home prices in {name}?</summary>
          <p style="margin:.75rem 0 0;color:#555;line-height:1.7;">Home prices in {name} typically range from {price_range}. The most common property types are {prop_types}. Prices vary based on size, condition, and location within {name}. Contact us at (718) 850-0010 for a free, no-obligation home valuation.</p>
        </details>
        <details style="border:1px solid #e0e0e0;border-radius:8px;padding:1rem;margin-bottom:.75rem;">
          <summary style="font-weight:600;cursor:pointer;color:#0F1A40;">How long does it take to sell a home in {name}?</summary>
          <p style="margin:.75rem 0 0;color:#555;line-height:1.7;">Well-priced homes in {name} typically sell within 21–35 days in the current market. Proper pricing, professional photography, and MLS exposure are the key factors. Gadura Real Estate's listings average fewer days on market than the neighborhood median.</p>
        </details>
        <details style="border:1px solid #e0e0e0;border-radius:8px;padding:1rem;margin-bottom:.75rem;">
          <summary style="font-weight:600;cursor:pointer;color:#0F1A40;">Is {name} a good place to invest in real estate?</summary>
          <p style="margin:.75rem 0 0;color:#555;line-height:1.7;">{name} has shown consistent appreciation over the past decade. With strong rental demand and limited housing inventory in {region}, {name} remains an attractive option for investors. Multi-family properties in {name} can generate strong rental yields.</p>
        </details>
        <details style="border:1px solid #e0e0e0;border-radius:8px;padding:1rem;margin-bottom:.75rem;">
          <summary style="font-weight:600;cursor:pointer;color:#0F1A40;">Do you have a real estate agent who speaks Hindi or Punjabi in {name}?</summary>
          <p style="margin:.75rem 0 0;color:#555;line-height:1.7;">Yes! Gadura Real Estate LLC has multilingual agents fluent in Hindi, Punjabi, English, Spanish, and Bengali serving {name} and all of {region}. Call (718) 850-0010 to speak with an agent in your language today.</p>
        </details>

        <!-- Nearby Neighborhoods -->
        <h3 style="font-family:'Playfair Display',serif;color:#0F1A40;font-size:1.3rem;margin:2rem 0 1rem;">Nearby Neighborhoods We Serve</h3>
        <div class="nearby-grid">
          <a href="/neighborhoods/ozone-park.html" class="nearby-link">Ozone Park</a>
          <a href="/neighborhoods/richmond-hill.html" class="nearby-link">Richmond Hill</a>
          <a href="/neighborhoods/jamaica.html" class="nearby-link">Jamaica</a>
          <a href="/neighborhoods/howard-beach.html" class="nearby-link">Howard Beach</a>
          <a href="/neighborhoods/woodhaven.html" class="nearby-link">Woodhaven</a>
          <a href="/neighborhoods/south-ozone-park.html" class="nearby-link">South Ozone Park</a>
          <a href="/neighborhoods/valley-stream.html" class="nearby-link">Valley Stream</a>
          <a href="/neighborhoods/hempstead.html" class="nearby-link">Hempstead</a>
        </div>
      </div>

      <!-- Right: Sidebar with Form -->
      <div class="nh-sidebar">
        <h3>Get a Free Home Valuation in {name}</h3>
        <p style="font-size:.9rem;color:#555;margin-bottom:1rem;">Find out what your {name} home is worth today. Free, no-obligation.</p>
        <form class="contact-form" action="https://formsubmit.co/Nitink.gadura@gmail.com" method="POST">
          <input type="hidden" name="_subject" value="Home Valuation Request - {name}">
          <input type="hidden" name="_captcha" value="false">
          <input type="hidden" name="_next" value="https://gadurarealestate.com/contact.html">
          <input type="text" name="name" placeholder="Your Full Name" required>
          <input type="tel" name="phone" placeholder="Phone Number" required>
          <input type="email" name="email" placeholder="Email Address" required>
          <input type="text" name="address" placeholder="Property Address in {name}">
          <select name="service">
            <option value="">I'm looking to...</option>
            <option value="sell">Sell my home</option>
            <option value="buy">Buy a home</option>
            <option value="invest">Invest in property</option>
            <option value="valuation">Just get a valuation</option>
          </select>
          <button type="submit">Get My Free Valuation →</button>
        </form>
        <div style="margin-top:1.25rem;text-align:center;border-top:1px solid #e0e0e0;padding-top:1rem;">
          <p style="font-size:.85rem;color:#666;margin-bottom:.5rem;">Or call us directly:</p>
          <a href="tel:+17188500010" style="font-size:1.3rem;font-weight:700;color:#0F1A40;text-decoration:none;">(718) 850-0010</a>
          <p style="font-size:.8rem;color:#888;margin-top:.25rem;">Mon–Sat 9am–7pm</p>
        </div>
        <div style="margin-top:1rem;background:#fff;border-radius:8px;padding:.75rem;border:1px solid #e0e0e0;">
          <p style="font-size:.8rem;color:#555;margin:0;text-align:center;">
            🏠 <strong>20+ years</strong> serving {region}<br>
            🌐 We speak <strong>5 languages</strong><br>
            ⭐ <strong>5-star</strong> Google rated
          </p>
        </div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer style="background:#0F1A40;color:#ccc;padding:2rem 0;margin-top:3rem;">
    <div style="max-width:1100px;margin:0 auto;padding:0 1.5rem;display:flex;gap:2rem;flex-wrap:wrap;justify-content:space-between;">
      <div>
        <p style="color:#fff;font-weight:600;margin-bottom:.5rem;">Gadura Real Estate LLC</p>
        <p style="font-size:.85rem;line-height:1.7;">110-20 Rockaway Blvd, South Ozone Park, NY 11420<br>
        (718) 850-0010 | info@gadurarealestate.com</p>
      </div>
      <div>
        <p style="color:#fff;font-weight:600;margin-bottom:.5rem;">Quick Links</p>
        <p style="font-size:.85rem;line-height:2;">
          <a href="/buy.html" style="color:#ccc;text-decoration:none;">Buy</a> ·
          <a href="/sell.html" style="color:#ccc;text-decoration:none;">Sell</a> ·
          <a href="/neighborhoods/" style="color:#ccc;text-decoration:none;">Neighborhoods</a> ·
          <a href="/blog/" style="color:#ccc;text-decoration:none;">Blog</a> ·
          <a href="/contact.html" style="color:#ccc;text-decoration:none;">Contact</a>
        </p>
      </div>
    </div>
  </footer>
  <div class="compliance-bar">
    <div style="max-width:1100px;margin:0 auto;padding:0 1rem;">
      Equal Housing Opportunity. Gadura Real Estate LLC. Licensed NYS Real Estate Broker. We do not discriminate on the basis of race, color, religion, sex, national origin, familial status, disability, age, sexual orientation, gender identity, source of income, or any other protected class.
      <a href="/fair-housing.html">Fair Housing</a> · <a href="/privacy-policy.html">Privacy</a> · <a href="/terms.html">Terms</a>
    </div>
  </div>
</body>
</html>"""

created = []
for (slug, name, area, zipcode, desc, price_range, region, prop_types) in NEW_NEIGHBORHOODS:
    target = BASE / "neighborhoods" / f"{slug}.html"
    if target.exists():
        print(f"SKIP (exists): {slug}")
        continue
    html = make_neighborhood_page(slug, name, area, zipcode, desc, price_range, region, prop_types)
    target.write_text(html, encoding="utf-8")
    created.append(f"{slug} ({region})")

print(f"\nCreated {len(created)} new neighborhood pages:")
for c in created:
    print(f"  ✓ {c}")
