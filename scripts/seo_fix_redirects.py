#!/usr/bin/env python3
"""Fix remaining broken targets: create v2 redirect pages and missing pages."""

import os, re
from pathlib import Path

BASE = Path("/Users/nidhigadura/Jagex/gadura-realestate")
DOMAIN = "https://gadurarealestate.com"

# Broken targets that need redirect stubs (non-asset, non-existing)
BROKEN_TARGETS = {
    "/agency-disclosure.html": "/fair-housing.html",
    "/privacy.html": "/privacy-policy.html",
    "/accessibility.html": "/about.html",
    "/home-value/home-equity-calculator.html": "/home-value/",
    "/home-value/sell-or-rent-calculator.html": "/home-value/",
    "/home-value/free-cma-queens.html": "/home-value/",
    "/v2/buy.html": "/buy.html",
    "/v2/sell.html": "/sell.html",
    "/v2/about.html": "/about.html",
    "/v2/selling/": "/v2/selling/first-time-home-seller-guide-queens.html",
    "/v2/resources/": "/v2/resources/ny-home-seller-legal-checklist.html",
    "/v2/neighborhoods/": "/neighborhoods/",
    "/v2/neighborhoods/richmond-hill.html": "/neighborhoods/richmond-hill.html",
    "/v2/neighborhoods/south-ozone-park.html": "/neighborhoods/south-ozone-park.html",
    "/v2/neighborhoods/jamaica.html": "/neighborhoods/jamaica.html",
    "/v2/neighborhoods/howard-beach.html": "/neighborhoods/howard-beach.html",
    "/v2/neighborhoods/woodhaven.html": "/neighborhoods/woodhaven.html",
    "/v2/neighborhoods/jamaica-estates.html": "/neighborhoods/jamaica-estates.html",
    "/v2/neighborhoods/kew-gardens.html": "/neighborhoods/kew-gardens.html",
    "/v2/neighborhoods/astoria.html": "/neighborhoods/astoria.html",
    "/v2/neighborhoods/bayside.html": "/neighborhoods/bayside.html",
    "/v2/zip-codes/11417.html": "/neighborhoods/ozone-park.html",
    "/neighborhoods/ozone-park-homes.html": "/neighborhoods/ozone-park.html",
    "/homes-for-sale/queens-townhouses-for-sale.html": "/for-sale/",
}

created = []
for broken_url, dest_url in BROKEN_TARGETS.items():
    full_dest = DOMAIN + dest_url
    stub = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Redirecting... | Gadura Real Estate LLC</title>
  <meta http-equiv="refresh" content="0;url={full_dest}">
  <link rel="canonical" href="{full_dest}">
  <script>window.location.replace("{full_dest}");</script>
</head>
<body>
  <p>Redirecting... <a href="{full_dest}">Click here</a></p>
</body>
</html>"""

    # Determine file path
    if broken_url.endswith("/"):
        target = BASE / broken_url.lstrip("/") / "index.html"
    else:
        target = BASE / broken_url.lstrip("/")

    # Skip if it's an existing non-HTML file
    if target.exists() and target.suffix != ".html":
        print(f"SKIP (non-html exists): {target}")
        continue

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stub, encoding="utf-8")
        created.append(str(target))
        print(f"Created: {broken_url} -> {dest_url}")

print(f"\nCreated {len(created)} redirect stubs")
