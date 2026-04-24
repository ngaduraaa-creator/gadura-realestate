#!/usr/bin/env python3
"""Generate Open Graph share images (1200x630 PNG) for Gadura Real Estate pages.

Produces /images/og/<slug>.png for a defined set of templates. Run on demand;
idempotent — overwrites existing files.

Design: navy background, gold accent bar, brand lockup top-left, large title
bottom-left, URL + phone footer.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "images" / "og"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1200, 630
NAVY = (11, 37, 69)          # #0b2545
NAVY_DEEP = (8, 26, 49)      # darker variant for gradient
GOLD = (232, 197, 71)        # #e8c547
WHITE = (255, 255, 255)
LIGHT = (227, 233, 242)

# Try a decent system font; fall back to default if unavailable.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]
FONT_REG_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


FONT_TITLE = load_font(FONT_CANDIDATES, 72)
FONT_TITLE_SM = load_font(FONT_CANDIDATES, 58)
FONT_EYEBROW = load_font(FONT_REG_CANDIDATES, 26)
FONT_BRAND = load_font(FONT_CANDIDATES, 34)
FONT_META = load_font(FONT_REG_CANDIDATES, 22)


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(slug: str, eyebrow: str, title: str) -> Path:
    img = Image.new("RGB", (W, H), NAVY_DEEP)
    draw = ImageDraw.Draw(img)

    # Gradient-ish effect: paint a lighter navy band across upper 60%
    for y in range(0, int(H * 0.62)):
        t = y / (H * 0.62)
        r = int(NAVY_DEEP[0] + (NAVY[0] - NAVY_DEEP[0]) * t)
        g = int(NAVY_DEEP[1] + (NAVY[1] - NAVY_DEEP[1]) * t)
        b = int(NAVY_DEEP[2] + (NAVY[2] - NAVY_DEEP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Gold accent bar (left rail)
    draw.rectangle([(0, 0), (12, H)], fill=GOLD)

    # Top-right corner mark: gold dot grid
    for gx in range(0, 7):
        for gy in range(0, 4):
            cx = W - 60 - gx * 16
            cy = 40 + gy * 16
            draw.ellipse([(cx - 3, cy - 3), (cx + 3, cy + 3)], fill=GOLD)

    # Brand lockup top-left
    draw.text((60, 54), "GADURA REAL ESTATE", font=FONT_BRAND, fill=WHITE)
    draw.text((60, 96), "Queens · Brooklyn · Long Island", font=FONT_META, fill=LIGHT)

    # Eyebrow tag
    if eyebrow:
        eyebrow_upper = eyebrow.upper()
        bbox = draw.textbbox((0, 0), eyebrow_upper, font=FONT_EYEBROW)
        tag_w = bbox[2] - bbox[0] + 36
        tag_h = bbox[3] - bbox[1] + 16
        tag_x = 60
        tag_y = 240
        draw.rounded_rectangle(
            [(tag_x, tag_y), (tag_x + tag_w, tag_y + tag_h)],
            radius=tag_h // 2,
            fill=GOLD,
        )
        draw.text((tag_x + 18, tag_y + 4), eyebrow_upper, font=FONT_EYEBROW, fill=NAVY)

    # Title — auto-shrink if too many lines at the big size
    font = FONT_TITLE
    lines = wrap(draw, title, font, max_width=W - 140)
    if len(lines) > 3:
        font = FONT_TITLE_SM
        lines = wrap(draw, title, font, max_width=W - 140)

    line_h = font.size + 14
    y = 320
    for line in lines[:4]:
        draw.text((60, y), line, font=font, fill=WHITE)
        y += line_h

    # Footer
    draw.rectangle([(0, H - 72), (W, H)], fill=NAVY_DEEP)
    draw.text((60, H - 56), "gadurarealestate.com", font=FONT_META, fill=GOLD)
    draw.text(
        (W - 280, H - 56),
        "(917) 705-0132",
        font=FONT_META,
        fill=LIGHT,
    )

    out = OUT_DIR / f"{slug}.png"
    img.save(out, "PNG", optimize=True)
    return out


TEMPLATES = [
    ("default", "", "Queens · Brooklyn · Long Island Real Estate"),
    ("home", "Family-owned NY brokerage", "Honest Real Estate in Queens, Brooklyn & Long Island"),
    ("buy", "Buyer's side", "Find Your Queens or Long Island Home"),
    ("sell", "Seller's side", "Sell Your Queens Home for What It's Worth"),
    ("blog", "Real estate blog", "Queens Real Estate Analysis You Can Actually Use"),
    ("market-reports", "Monthly by ZIP", "NY Market Reports — Median Price, DOM, Supply"),
    ("neighborhoods", "126 neighborhoods", "Queens, Brooklyn & Long Island Neighborhood Guides"),
    ("about-nitin", "Broker profile", "Nitin Gadura — NY Licensed Real Estate Broker"),
    ("listings", "Live OneKey® MLS", "Queens · Brooklyn · Nassau · Suffolk MLS Search"),
    ("past-sales", "Transaction history", "Past Sales — Gadura Real Estate Closed Deals"),
    ("open-houses", "This weekend", "Queens & Long Island Open Houses"),
    ("hindi-agent", "Hindi-speaking broker", "Queens Hindi-Speaking Real Estate Agent"),
    ("punjabi-agent", "Punjabi-speaking broker", "Queens Punjabi-Speaking Real Estate Agent"),
    ("contact", "Free 15-min consult", "Talk to Nitin Gadura — (917) 705-0132"),
    # Post-specific OG for the highest-value comparison/guide content
    ("astoria-vs-sunnyside", "Neighborhood comparison", "Astoria vs Sunnyside — 2026 Buyer's Guide"),
    ("queens-commuter", "Commuter ranking", "Best Commuter Neighborhoods in Queens 2026"),
    ("forest-hills-vs-rego-park", "Neighborhood comparison", "Forest Hills vs Rego Park — 2026 Buyer's Guide"),
    ("first-time-buyer", "First-time buyer", "First-Time Home Buyer in Queens — 2026 Guide"),
    ("closing-costs", "Transaction costs", "NYC Closing Costs Explained — 2026"),
    ("mansion-tax", "Transfer tax", "NYC Mansion Tax Explained — 2026"),
]


def main() -> None:
    for slug, eyebrow, title in TEMPLATES:
        path = render(slug, eyebrow, title)
        print(f"  wrote {path.relative_to(ROOT)}")
    print(f"\nDone. {len(TEMPLATES)} images in {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
