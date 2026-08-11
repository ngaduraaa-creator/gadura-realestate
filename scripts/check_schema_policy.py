#!/usr/bin/env python3
"""Structured-data policy guard (LA-2A / LA-3B0J).

Fails (exit 1) if any deployable HTML attaches self-serving review markup
to Gadura Real Estate's own entity:
  - aggregateRating on the firm's RealEstateAgent/LocalBusiness/Organization
  - Review nodes whose itemReviewed is the firm (by @id or name)

Google's structured-data policy disallows self-serving review/rating
markup on one's own business entity, and firm policy (governed record,
LA-2A) forbids it. Visible testimonials are fine; schema is not.

Run: python3 scripts/check_schema_policy.py   (from repo root)
"""
import json
import pathlib
import re
import sys

OWN_IDS = ("gadurarealestate.com/#brokerage", "gadurarealestate.com/#organization")
OWN_NAMES = ("gadura real estate",)
OWNED_TYPES = ("RealEstateAgent", "LocalBusiness", "Organization",
               "ProfessionalService", "RealEstateBroker")
BLOCK = re.compile(r"application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)


def is_own(node: dict) -> bool:
    nid = str(node.get("@id", "")).lower()
    name = str(node.get("name", "")).lower()
    return any(i in nid for i in OWN_IDS) or any(n in name for n in OWN_NAMES)


def walk(data):
    stack = [data]
    while stack:
        n = stack.pop()
        if isinstance(n, list):
            stack.extend(n)
        elif isinstance(n, dict):
            yield n
            stack.extend(n.values())


def check_file(path: pathlib.Path) -> list[str]:
    problems = []
    text = path.read_text(errors="ignore")
    for m in BLOCK.finditer(text):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue  # malformed blocks are tracked elsewhere
        for node in walk(data):
            t = node.get("@type", "")
            types = t if isinstance(t, list) else [t]
            if any(x in OWNED_TYPES for x in types) and is_own(node):
                if "aggregateRating" in node:
                    problems.append(f"{path}: aggregateRating on own entity")
                if "review" in node or "reviews" in node:
                    problems.append(f"{path}: review property on own entity")
            if "Review" in types:
                item = node.get("itemReviewed", {})
                if isinstance(item, dict) and is_own(item):
                    problems.append(f"{path}: Review with itemReviewed = own entity")
    return problems


def main() -> int:
    root = pathlib.Path(".")
    problems = []
    for p in root.rglob("*.html"):
        if "/.git/" in str(p):
            continue
        problems.extend(check_file(p))
    if problems:
        print("SCHEMA POLICY VIOLATIONS (self-serving review markup):")
        for pr in problems[:40]:
            print("  ", pr)
        print(f"total: {len(problems)}")
        return 1
    print("schema policy OK: no self-serving review/rating markup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
