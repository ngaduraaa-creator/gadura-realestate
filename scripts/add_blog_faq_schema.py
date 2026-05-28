#!/usr/bin/env python3
"""
add_blog_faq_schema.py — Add FAQPage JSON-LD schema to blog posts.

Scans all .html files in blog/ (excluding index.html), skips any that already
have FAQPage schema, extracts H2/H3 headings with their following paragraph
content, generates 3-5 FAQ Q&A pairs, and inserts a FAQPage JSON-LD block
before </head>.
"""

import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"
FAQ_MARKER = "blog-faq-schema"
MAX_FAQ = 5
MIN_FAQ = 3


class HeadingBlock(NamedTuple):
    level: int
    heading: str
    content: str


def strip_html_tags(text: str) -> str:
    """Remove HTML tags and decode entities."""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def heading_to_question(heading: str) -> str:
    """Turn a heading into a natural question."""
    h = heading.strip().rstrip("?")

    # Already a question
    if re.match(r"^(what|how|why|when|where|who|which|is|are|can|do|does|should|will)\b", h, re.I):
        return h + "?"

    # Patterns: "X vs Y" -> "How does X compare to Y?"
    vs_match = re.match(r"^(.+?)\s+(?:vs\.?|versus)\s+(.+)$", h, re.I)
    if vs_match:
        return f"How does {vs_match.group(1).strip()} compare to {vs_match.group(2).strip()}?"

    # Patterns with leading letter+period (e.g. "A. Bayside — Northeastern Queens")
    labeled = re.match(r"^[A-Z]\.\s*(.+)$", h)
    if labeled:
        h = labeled.group(1).strip()

    # Remove trailing location qualifiers after em-dash for cleaner questions
    dash_split = re.split(r"\s*[—–]\s*", h, maxsplit=1)
    if len(dash_split) == 2 and len(dash_split[0]) > 10:
        topic = dash_split[0].strip()
        location = dash_split[1].strip()
        return f"What should buyers know about {topic} in {location}?"

    # Numbered sections like "1. ..." or "Step 1: ..."
    numbered = re.match(r"^(?:step\s+)?\d+[.:]\s*(.+)$", h, re.I)
    if numbered:
        h = numbered.group(1).strip()

    # General transformation
    return f"What is important to know about {h}?"


def truncate_answer(text: str, max_chars: int = 300) -> str:
    """Truncate answer text to max_chars at a sentence boundary."""
    if len(text) <= max_chars:
        return text

    # Find last sentence break before max_chars
    truncated = text[:max_chars]
    last_period = truncated.rfind(". ")
    if last_period > 100:
        return truncated[: last_period + 1]

    last_period = truncated.rfind(".")
    if last_period > 100:
        return truncated[: last_period + 1]

    return truncated.rstrip() + "..."


def extract_heading_blocks(html: str) -> list[HeadingBlock]:
    """Extract H2/H3 headings and the paragraph text that follows them."""
    # Pattern: find <h2> or <h3>, capture heading text, then capture
    # following <p> tags until the next heading or end of main content
    heading_pattern = re.compile(
        r"<(h[23])\b[^>]*>(.*?)</\1>",
        re.IGNORECASE | re.DOTALL,
    )

    blocks: list[HeadingBlock] = []
    matches = list(heading_pattern.finditer(html))

    for i, m in enumerate(matches):
        level = int(m.group(1)[1])
        heading_raw = strip_html_tags(m.group(2))

        if not heading_raw or len(heading_raw) < 5:
            continue

        # Skip generic headings that do not make good FAQ questions
        skip_patterns = [
            r"^(about|contact|talk to|schedule|related|continue|call|get your free)",
            r"^(author|legal|disclaimer|disclosure|wire fraud|footer)",
            r"^(table of contents|in this|quick|at a glance)",
            r"^(faq|frequently asked)",
        ]
        if any(re.match(pat, heading_raw, re.I) for pat in skip_patterns):
            continue

        # Get text between this heading and the next heading (or end)
        start_pos = m.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            # Try to find closing </main> or </article> or next <section>
            end_markers = [
                html.find("</main>", start_pos),
                html.find("</article>", start_pos),
                html.find('<section class="related', start_pos),
                html.find('<div class="author-box"', start_pos),
            ]
            valid_ends = [e for e in end_markers if e > start_pos]
            end_pos = min(valid_ends) if valid_ends else start_pos + 2000

        between = html[start_pos:end_pos]

        # Extract paragraph content
        paragraphs = re.findall(
            r"<p\b[^>]*>(.*?)</p>",
            between,
            re.IGNORECASE | re.DOTALL,
        )
        content_parts = [strip_html_tags(p) for p in paragraphs if strip_html_tags(p)]
        content = " ".join(content_parts)

        if len(content) < 30:
            continue

        blocks.append(HeadingBlock(level=level, heading=heading_raw, content=content))

    return blocks


def select_faq_blocks(blocks: list[HeadingBlock]) -> list[HeadingBlock]:
    """Select 3-5 blocks that make the best FAQ pairs, preferring H2 headings."""
    if len(blocks) <= MAX_FAQ:
        return blocks[:MAX_FAQ]

    # Prefer H2 headings first, then H3
    h2_blocks = [b for b in blocks if b.level == 2]
    h3_blocks = [b for b in blocks if b.level == 3]

    selected: list[HeadingBlock] = []

    # Take up to MAX_FAQ from H2s first
    for b in h2_blocks:
        if len(selected) >= MAX_FAQ:
            break
        selected.append(b)

    # Fill remaining slots with H3s
    for b in h3_blocks:
        if len(selected) >= MAX_FAQ:
            break
        selected.append(b)

    return selected


def build_faq_schema(qa_pairs: list[dict[str, str]]) -> str:
    """Build the FAQPage JSON-LD script block."""
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"],
                },
            }
            for qa in qa_pairs
        ],
    }
    return (
        f'<script type="application/ld+json" id="{FAQ_MARKER}">\n'
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + "\n</script>"
    )


def has_faqpage_schema(html: str) -> bool:
    """Check if the file already has any FAQPage schema."""
    return "FAQPage" in html


def inject_schema(html: str, schema_block: str) -> str:
    """Insert the schema block before </head>."""
    if "</head>" not in html:
        return html
    return html.replace("</head>", f"{schema_block}\n</head>", 1)


def process_file(filepath: Path) -> tuple[str, int]:
    """Process a single blog post file. Returns (status, faq_count)."""
    html = filepath.read_text(encoding="utf-8")

    if has_faqpage_schema(html):
        return "skipped (already has FAQPage)", 0

    blocks = extract_heading_blocks(html)
    selected = select_faq_blocks(blocks)

    if len(selected) < MIN_FAQ:
        return f"skipped (only {len(selected)} usable headings, need {MIN_FAQ}+)", 0

    qa_pairs = []
    for block in selected:
        question = heading_to_question(block.heading)
        answer = truncate_answer(block.content)
        qa_pairs.append({"question": question, "answer": answer})

    schema_block = build_faq_schema(qa_pairs)
    new_html = inject_schema(html, schema_block)

    if new_html == html:
        return "skipped (no </head> tag found)", 0

    filepath.write_text(new_html, encoding="utf-8")
    return "updated", len(qa_pairs)


def main() -> int:
    if not BLOG_DIR.is_dir():
        print(f"ERROR: Blog directory not found: {BLOG_DIR}")
        return 1

    blog_files = sorted(
        p
        for p in BLOG_DIR.glob("*.html")
        if p.name != "index.html"
    )

    print(f"Found {len(blog_files)} blog post files (excluding index.html)")
    print("=" * 70)

    updated_count = 0
    skipped_count = 0
    total_faqs = 0

    for filepath in blog_files:
        status, faq_count = process_file(filepath)
        if status == "updated":
            updated_count += 1
            total_faqs += faq_count
            print(f"  UPDATED: {filepath.name} ({faq_count} FAQs added)")
        else:
            skipped_count += 1
            print(f"  SKIPPED: {filepath.name} - {status}")

    print("=" * 70)
    print(f"Updated: {updated_count} blog posts")
    print(f"Skipped: {skipped_count} blog posts")
    print(f"Total FAQ pairs added: {total_faqs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
