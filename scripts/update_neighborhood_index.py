#!/usr/bin/env python3
"""Add new neighborhood links to the neighborhoods hub page and update sitemap."""
import re, json
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"

NEW_HOODS = [
    ("laurelton","Laurelton","Queens"),("rosedale","Rosedale","Queens"),
    ("st-albans","St. Albans","Queens"),("cambria-heights","Cambria Heights","Queens"),
    ("queens-village","Queens Village","Queens"),("glen-oaks","Glen Oaks","Queens"),
    ("springfield-gardens","Springfield Gardens","Queens"),("far-rockaway","Far Rockaway","Queens"),
    ("arverne","Arverne","Queens"),("richmond-hill-south","Richmond Hill South","Queens"),
    ("ozone-park-north","Ozone Park North","Queens"),
    ("malverne","Malverne","Long Island"),("east-rockaway","East Rockaway","Long Island"),
    ("cedarhurst","Cedarhurst","Long Island"),("baldwin","Baldwin","Long Island"),
    ("freeport","Freeport","Long Island"),("merrick","Merrick","Long Island"),
    ("wantagh","Wantagh","Long Island"),("woodmere","Woodmere","Long Island"),
    ("hewlett","Hewlett","Long Island"),("inwood","Inwood","Long Island"),
    ("north-woodmere","North Woodmere","Long Island"),("seaford","Seaford","Long Island"),
    ("east-meadow","East Meadow","Long Island"),("uniondale","Uniondale","Long Island"),
    ("carle-place","Carle Place","Long Island"),
    ("canarsie","Canarsie","Brooklyn"),("east-flatbush","East Flatbush","Brooklyn"),
    ("flatlands","Flatlands","Brooklyn"),("mill-basin","Mill Basin","Brooklyn"),
    ("marine-park","Marine Park","Brooklyn"),("georgetown-brooklyn","Georgetown","Brooklyn"),
    ("bergen-beach","Bergen Beach","Brooklyn"),("flatbush","Flatbush","Brooklyn"),
]

# Update neighborhoods/index.html — add new links
index_file = BASE / "neighborhoods" / "index.html"
if index_file.exists():
    content = index_file.read_text(encoding="utf-8", errors="ignore")
    
    # Build new links HTML grouped by area
    queens_links = "\n".join(
        f'          <a href="/neighborhoods/{slug}.html" class="neighborhood-card">'
        f'<span class="card-area">Queens</span><span class="card-name">{name}</span></a>'
        for slug, name, area in NEW_HOODS if area == "Queens"
        if f'/neighborhoods/{slug}.html' not in content
    )
    li_links = "\n".join(
        f'          <a href="/neighborhoods/{slug}.html" class="neighborhood-card">'
        f'<span class="card-area">Long Island</span><span class="card-name">{name}</span></a>'
        for slug, name, area in NEW_HOODS if area == "Long Island"
        if f'/neighborhoods/{slug}.html' not in content
    )
    bk_links = "\n".join(
        f'          <a href="/neighborhoods/{slug}.html" class="neighborhood-card">'
        f'<span class="card-area">Brooklyn</span><span class="card-name">{name}</span></a>'
        for slug, name, area in NEW_HOODS if area == "Brooklyn"
        if f'/neighborhoods/{slug}.html' not in content
    )
    
    new_section = f"""
  <!-- New neighborhoods added 2026-04-20 -->
  <section style="max-width:1200px;margin:2rem auto;padding:0 1.5rem;">
    <h2 style="font-family:'Playfair Display',serif;color:#0F1A40;margin-bottom:1.5rem;">More Queens Neighborhoods</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;">
{queens_links}
    </div>
    <h2 style="font-family:'Playfair Display',serif;color:#0F1A40;margin:2rem 0 1.5rem;">More Long Island Communities</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;">
{li_links}
    </div>
    <h2 style="font-family:'Playfair Display',serif;color:#0F1A40;margin:2rem 0 1.5rem;">More Brooklyn Neighborhoods</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;">
{bk_links}
    </div>
  </section>
  <style>
    .neighborhood-card{{display:flex;flex-direction:column;padding:1rem;background:#fff;border:1px solid #e0e0e0;border-radius:10px;text-decoration:none;transition:border-color .2s,box-shadow .2s;}}
    .neighborhood-card:hover{{border-color:#00A651;box-shadow:0 4px 12px rgba(0,166,81,.15);}}
    .card-area{{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem;}}
    .card-name{{font-size:1rem;font-weight:600;color:#0F1A40;}}
  </style>"""
    
    # Insert before </main> or </body>
    if '</main>' in content:
        content = content.replace('</main>', new_section + '\n</main>', 1)
    else:
        content = content.replace('</body>', new_section + '\n</body>', 1)
    
    index_file.write_text(content, encoding="utf-8")
    print("✓ Updated neighborhoods/index.html with 34 new neighborhood links")

# Rebuild sitemap with all pages including new ones
import re as re2
from datetime import date
TODAY = "2026-04-20"
SKIP_DIRS = {".git","node_modules","scripts","admin","data"}
REDIRECT_RE = re2.compile(r'<meta\s+http-equiv=["\']refresh["\']', re2.IGNORECASE)
NOINDEX_RE  = re2.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re2.IGNORECASE)

def file_to_url(f):
    rel = f.relative_to(BASE)
    parts = rel.parts
    if parts[-1] == 'index.html':
        return '/' + '/'.join(parts[:-1]) + '/' if len(parts) > 1 else '/'
    return '/' + str(rel)

def priority(url):
    if url == '/': return 1.0
    if url in ('/buy.html','/sell.html','/contact.html'): return 0.95
    if '/neighborhoods/' in url: return 0.87
    if '/blog/' in url: return 0.75
    if '/community/' in url: return 0.85
    if '/v2/' in url: return 0.88
    if '/services/' in url: return 0.85
    return 0.80

all_urls = []
for html_file in sorted(BASE.rglob("*.html")):
    parts = html_file.relative_to(BASE).parts
    if any(p in SKIP_DIRS for p in parts): continue
    c = html_file.read_text(encoding="utf-8", errors="ignore")
    if NOINDEX_RE.search(c): continue
    if REDIRECT_RE.search(c) and len(c) < 800: continue
    all_urls.append(file_to_url(html_file))

entries = []
for url in sorted(set(all_urls)):
    full = DOMAIN + url
    cf = "weekly" if url == "/" else "monthly"
    entries.append(f'  <url><loc>{full}</loc><lastmod>{TODAY}</lastmod><changefreq>{cf}</changefreq><priority>{priority(url):.2f}</priority></url>')

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "\n".join(entries)
sitemap += "\n</urlset>\n"
(BASE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
print(f"✓ Sitemap updated: {len(entries)} URLs (was 338)")
