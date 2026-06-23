#!/usr/bin/env python3
"""Fix HTML pages with meta descriptions longer than 155 characters.

Scans all HTML files (excluding _includes/), intelligently truncates
long meta descriptions at sentence or word boundaries, and writes
the trimmed content back.
"""
import os
import re
from dataclasses import dataclass
from typing import Optional


SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_LEN = 155
ELLIPSIS = "…"  # "..."
AGENT_FRAGMENTS = [
    "Nitin Gadura",
    "(917) 705-0132",
    "917-705-0132",
    "Gadura Real Estate",
]

# Matches <meta name="description" content="..."> with either attribute order
META_DESC_RE = re.compile(
    r'(<meta\s+)'
    r'(?:'
    r'name="description"\s+content="([^"]*)"'
    r'|'
    r'content="([^"]*)"\s+name="description"'
    r')'
    r'(\s*/?>)',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TrimResult:
    filepath: str
    original: str
    trimmed: str


def find_html_files(root: str) -> list[str]:
    """Recursively find all .html files, excluding _includes/."""
    results: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip _includes directory
        if "_includes" in dirpath.split(os.sep):
            continue
        # Prune _includes from future traversal
        dirnames[:] = [d for d in dirnames if d != "_includes"]
        for fname in filenames:
            if fname.endswith(".html"):
                results.append(os.path.join(dirpath, fname))
    return sorted(results)


def extract_agent_suffix(text: str) -> Optional[str]:
    """If text ends with agent info (name/phone), return that suffix."""
    for frag in AGENT_FRAGMENTS:
        idx = text.rfind(frag)
        if idx == -1:
            continue
        # Look back for a natural separator before the fragment
        before = text[:idx].rstrip()
        for sep in [". ", " - ", " -- ", " | ", ", "]:
            sep_idx = before.rfind(sep)
            if sep_idx != -1:
                suffix = text[sep_idx + len(sep) - 1 :].strip()
                # only use if the suffix part itself is short enough
                if len(suffix) < 60:
                    return " " + suffix.lstrip()
        # If no separator found, try using everything from the fragment onward
        suffix = text[idx:].strip()
        if len(suffix) < 60:
            return " " + suffix
    return None


def truncate_description(text: str) -> str:
    """Intelligently truncate a meta description to MAX_LEN characters.

    Strategy:
    1. Try to cut at a sentence boundary (. ! ?) that fits
    2. If no sentence boundary, cut at last complete word
    3. Append ellipsis
    4. Try to preserve agent name/phone if it fits
    """
    if len(text) <= MAX_LEN:
        return text

    # Reserve space for ellipsis
    budget = MAX_LEN - len(ELLIPSIS)

    # Try to find agent info to preserve
    agent_suffix = extract_agent_suffix(text)

    # --- Attempt 1: sentence boundary ---
    # Find all sentence-ending positions within budget
    sentence_ends = []
    for m in re.finditer(r'[.!?](?:\s|$)', text):
        end_pos = m.start() + 1  # include the punctuation
        if end_pos <= MAX_LEN:
            sentence_ends.append(end_pos)

    if sentence_ends:
        # Use the longest sentence-boundary cut that fits
        best_cut = text[: sentence_ends[-1]].rstrip()
        # If it's too short (less than 80 chars), skip sentence boundary
        if len(best_cut) >= 80:
            # Try appending agent suffix if it fits
            if agent_suffix and len(best_cut + agent_suffix) <= MAX_LEN:
                return best_cut + agent_suffix
            return best_cut

    # --- Attempt 2: word boundary ---
    # Find last space within budget
    truncated = text[:budget]
    last_space = truncated.rfind(" ")
    if last_space > 40:
        truncated = truncated[:last_space].rstrip()
    else:
        # Very long word; just hard-cut at budget (unlikely for English)
        truncated = truncated.rstrip()

    # Strip trailing punctuation fragments (comma, dash, etc.)
    truncated = truncated.rstrip(",-;:")

    # Try appending agent suffix if it fits
    if agent_suffix:
        candidate = truncated + agent_suffix
        if len(candidate) <= MAX_LEN:
            return candidate
        # Try shorter truncated + suffix
        shorter_budget = MAX_LEN - len(agent_suffix) - len(ELLIPSIS)
        if shorter_budget > 80:
            shorter = text[:shorter_budget]
            last_sp = shorter.rfind(" ")
            if last_sp > 40:
                shorter = shorter[:last_sp].rstrip().rstrip(",-;:")
                return shorter + ELLIPSIS + agent_suffix

    return truncated + ELLIPSIS


def process_file(filepath: str) -> Optional[TrimResult]:
    """Process a single HTML file. Returns TrimResult if modified, else None."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError):
        return None

    match = META_DESC_RE.search(content)
    if not match:
        return None

    # content is in group 2 (name-first) or group 3 (content-first)
    original_desc = match.group(2) if match.group(2) is not None else match.group(3)

    if len(original_desc) <= MAX_LEN:
        return None

    trimmed_desc = truncate_description(original_desc)

    # Rebuild the meta tag preserving original structure
    prefix = match.group(1)
    suffix = match.group(4)
    if match.group(2) is not None:
        new_tag = f'{prefix}name="description" content="{trimmed_desc}"{suffix}'
    else:
        new_tag = f'{prefix}content="{trimmed_desc}" name="description"{suffix}'

    new_content = content[: match.start()] + new_tag + content[match.end() :]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
    except (OSError, IOError) as e:
        print(f"  ERROR writing {filepath}: {e}")
        return None

    return TrimResult(
        filepath=filepath,
        original=original_desc,
        trimmed=trimmed_desc,
    )


def main() -> None:
    print(f"Site root: {SITE_ROOT}")
    print(f"Max description length: {MAX_LEN} characters")
    print()

    html_files = find_html_files(SITE_ROOT)
    print(f"Found {len(html_files)} HTML files (excluding _includes/)")
    print()

    results: list[TrimResult] = []
    files_with_desc = 0
    files_already_ok = 0

    for filepath in html_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except (OSError, IOError):
            continue

        match = META_DESC_RE.search(content)
        if not match:
            continue

        files_with_desc += 1
        original_desc = match.group(2) if match.group(2) is not None else match.group(3)

        if len(original_desc) <= MAX_LEN:
            files_already_ok += 1
            continue

        result = process_file(filepath)
        if result:
            results.append(result)

    # --- Summary ---
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total HTML files scanned:        {len(html_files)}")
    print(f"Files with meta description:     {files_with_desc}")
    print(f"Already within {MAX_LEN} chars:     {files_already_ok}")
    print(f"Trimmed (over {MAX_LEN} chars):      {len(results)}")
    print()

    if not results:
        print("No files needed trimming.")
        return

    # Length distribution of trimmed results
    lengths = [len(r.trimmed) for r in results]
    print(f"Trimmed description lengths:")
    print(f"  Min: {min(lengths)} chars")
    print(f"  Max: {max(lengths)} chars")
    print(f"  Avg: {sum(lengths) / len(lengths):.0f} chars")
    print()

    # Show examples (up to 5)
    sample_count = min(5, len(results))
    print(f"--- Example Before/After ({sample_count} of {len(results)}) ---")
    print()
    for i, r in enumerate(results[:sample_count], 1):
        rel_path = os.path.relpath(r.filepath, SITE_ROOT)
        print(f"  [{i}] {rel_path}")
        print(f"      BEFORE ({len(r.original)} chars):")
        print(f"        {r.original[:120]}...")
        print(f"      AFTER  ({len(r.trimmed)} chars):")
        print(f"        {r.trimmed}")
        print()

    # Verify no description exceeds limit
    over_limit = [r for r in results if len(r.trimmed) > MAX_LEN]
    if over_limit:
        print(f"WARNING: {len(over_limit)} descriptions still over {MAX_LEN} chars!")
        for r in over_limit[:3]:
            print(f"  {os.path.relpath(r.filepath, SITE_ROOT)}: {len(r.trimmed)} chars")
    else:
        print(f"All trimmed descriptions are within {MAX_LEN} characters.")


if __name__ == "__main__":
    main()
