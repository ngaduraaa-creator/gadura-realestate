#!/usr/bin/env python3
"""Task 6: Fix and standardize all structured data / schema markup."""

import re, json
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"

COMPANY = {
    "name": "Gadura Real Estate LLC",
    "phone": "(718) 850-0010",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "110-20 Rockaway Blvd",
        "addressLocality": "South Ozone Park",
        "addressRegion": "NY",
        "postalCode": "11420",
        "addressCountry": "US"
    },
    "url": DOMAIN,
    "logo": f"{DOMAIN}/images/logo-full.png",
    "image": f"{DOMAIN}/images/logo-full.png",
}

def file_to_url(f: Path) -> str:
    rel = f.relative_to(BASE)
    parts = rel.parts
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    return "/" + str(rel)

def get_page_type(f: Path) -> str:
    s = str(f)
    if "/blog/" in s:           return "blog"
    if "/neighborhoods/" in s:  return "neighborhood"
    if "/community/" in s:      return "community"
    if "/services/" in s:       return "service"
    if "/agents/" in s:         return "agent_list"
    if f.name == "index.html" and f.parent == BASE: return "home"
    # Agent pages (dirs named after person)
    agent_dirs = ["nitin-gadura","vinod-gadura","gaurav-bhardwaj","bhupinder-gill",
                  "jagman-dhaliwal","jeevanpreet-singh","kumar-ramudit","manpreet-kaur",
                  "md-ali","miguel-cane","ravi-kapoor","rushneet-kaur","stephanie-silva",
                  "wazid-mohammed","zahid-ali","gurvinder-singh","jaqueline-silva"]
    for a in agent_dirs:
        if f"/{a}/" in s or f"/{a}\\" in s:
            return "agent"
    return "general"

def get_breadcrumb(f: Path) -> dict:
    url = file_to_url(f)
    parts_str = url.strip("/")
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"}]
    if parts_str:
        segments = parts_str.split("/")
        pos = 2
        path_so_far = ""
        for i, seg in enumerate(segments):
            path_so_far += "/" + seg
            name = seg.replace("-", " ").replace(".html", "").title()
            item = DOMAIN + path_so_far + ("/" if i < len(segments)-1 else "")
            crumbs.append({"@type": "ListItem", "position": pos, "name": name, "item": item})
            pos += 1
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": crumbs
    }

SCHEMA_BLOCK_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL
)

stats = {"schema_fixed": 0, "schema_added": 0, "breadcrumb_added": 0, "files_changed": 0}

for html_file in sorted(BASE.rglob("*.html")):
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    original = content
    url_path = file_to_url(html_file)
    page_type = get_page_type(html_file)

    # ── Find existing JSON-LD blocks ───────────────────────────────────────
    blocks = SCHEMA_BLOCK_RE.findall(content)
    parsed_schemas = []
    has_schema = bool(blocks)
    has_breadcrumb = False
    has_local_biz = False
    has_faq = False
    has_article = False
    has_person = False

    for raw in blocks:
        raw = raw.strip()
        try:
            schema = json.loads(raw)
            schemas = schema if isinstance(schema, list) else [schema]
            for s in schemas:
                t = s.get("@type", "")
                types = t if isinstance(t, list) else [t]
                if "BreadcrumbList" in types:     has_breadcrumb = True
                if any(x in types for x in ["LocalBusiness","RealEstateAgent"]): has_local_biz = True
                if "FAQPage" in types:            has_faq = True
                if any(x in types for x in ["Article","BlogPosting"]): has_article = True
                if "Person" in types:             has_person = True

                # ── Fix common issues ──────────────────────────────────────
                # Ensure @context is present
                if "@context" not in s:
                    s["@context"] = "https://schema.org"
                # Fix LocalBusiness missing required fields
                if any(x in types for x in ["LocalBusiness","RealEstateAgent"]):
                    if "telephone" not in s:
                        s["telephone"] = COMPANY["phone"]
                    if "address" not in s:
                        s["address"] = COMPANY["address"]
                    if "url" not in s:
                        s["url"] = DOMAIN
                    if "name" not in s:
                        s["name"] = COMPANY["name"]
                # Fix Article missing required fields
                if any(x in types for x in ["Article","BlogPosting"]):
                    if "publisher" not in s:
                        s["publisher"] = {
                            "@type": "Organization",
                            "name": COMPANY["name"],
                            "logo": {"@type": "ImageObject", "url": COMPANY["logo"]}
                        }
                    if "author" not in s:
                        s["author"] = {"@type": "Organization", "name": COMPANY["name"]}
                    if "image" not in s:
                        s["image"] = COMPANY["image"]

            parsed_schemas.append(json.dumps(schema, indent=2))
        except json.JSONDecodeError:
            parsed_schemas.append(raw)

    # ── Replace existing blocks with fixed versions ──────────────────────
    if parsed_schemas:
        fixed_block_iter = iter(parsed_schemas)
        def replacer(m):
            try:
                fixed = next(fixed_block_iter)
                return f'<script type="application/ld+json">\n{fixed}\n</script>'
            except StopIteration:
                return m.group(0)
        new_content = SCHEMA_BLOCK_RE.sub(replacer, content)
        if new_content != content:
            content = new_content
            stats["schema_fixed"] += 1

    # ── Add missing schemas ────────────────────────────────────────────────
    new_schemas = []

    # Add BreadcrumbList if missing (all pages except homepage)
    if not has_breadcrumb and url_path != "/":
        new_schemas.append(get_breadcrumb(html_file))
        stats["breadcrumb_added"] += 1

    # Add page-type-specific schema if completely missing
    if not has_schema:
        if page_type == "blog" and not has_article:
            title_m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_m.group(1).strip() if title_m else "Blog Post"
            new_schemas.append({
                "@context": "https://schema.org",
                "@type": "BlogPosting",
                "headline": title[:110],
                "author": {"@type": "Organization", "name": COMPANY["name"]},
                "publisher": {
                    "@type": "Organization",
                    "name": COMPANY["name"],
                    "logo": {"@type": "ImageObject", "url": COMPANY["logo"]}
                },
                "datePublished": "2026-04-20",
                "dateModified": "2026-04-20",
                "image": COMPANY["image"],
                "url": DOMAIN + url_path
            })
        elif page_type in ("neighborhood", "community", "service", "general"):
            title_m = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_m.group(1).strip() if title_m else "Page"
            desc_m = re.search(r'<meta\s+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            desc = desc_m.group(1).strip() if desc_m else ""
            new_schemas.append({
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title,
                "description": desc,
                "url": DOMAIN + url_path,
                "isPartOf": {"@type": "WebSite", "name": COMPANY["name"], "url": DOMAIN}
            })
        stats["schema_added"] += 1

    if new_schemas:
        block = "\n".join(
            f'<script type="application/ld+json">\n{json.dumps(s, indent=2)}\n</script>'
            for s in new_schemas
        )
        if '</head>' in content:
            content = content.replace('</head>', block + '\n</head>', 1)

    if content != original:
        html_file.write_text(content, encoding="utf-8")
        stats["files_changed"] += 1

print("=== TASK 6 RESULTS ===")
print(f"Schema blocks fixed (validation errors):  {stats['schema_fixed']}")
print(f"Schema added to pages with none:          {stats['schema_added']}")
print(f"BreadcrumbList added:                     {stats['breadcrumb_added']}")
print(f"Total files modified:                     {stats['files_changed']}")
