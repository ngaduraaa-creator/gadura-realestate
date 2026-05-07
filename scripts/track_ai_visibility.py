#!/usr/bin/env python3
"""
track_ai_visibility.py — Daily/weekly AI visibility tracker.

For each priority query, hit the available AI-search APIs and check whether:
- gadurarealestate.com / nitingadura.com is cited as a source
- Nitin Gadura is mentioned by name
- Gadura Real Estate is mentioned

Output: ai-monitoring/ai-visibility-<date>.csv with per-query, per-engine results.

Currently supports:
- Perplexity Sonar API (PERPLEXITY_API_KEY required)
- Brave Search Summarizer (BRAVE_API_KEY optional, free tier)
- Manual entry for ChatGPT/Gemini/Grok (logged for human verification)

Run weekly via GitHub Actions or cron.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PRIORITY_QUERIES = [
    # Brand
    ("brand", "Nitin Gadura real estate agent"),
    ("brand", "Gadura Real Estate Queens"),
    # High-intent buyer
    ("buyer", "best real estate agent in Queens NY"),
    ("buyer", "Hindi speaking real estate agent in NYC"),
    ("buyer", "Punjabi speaking real estate agent Queens"),
    ("buyer", "Bengali speaking real estate agent NYC"),
    ("buyer", "Guyanese real estate agent Queens"),
    ("buyer", "first time homebuyer Queens"),
    ("buyer", "FHA loan real estate agent Queens NY"),
    ("buyer", "SONYMA grant Queens"),
    ("buyer", "multi family investment Queens"),
    # Seller
    ("seller", "best agent to sell my Queens home"),
    ("seller", "inherited property sale Queens NY"),
    # Geographic
    ("local", "real estate agent Ozone Park"),
    ("local", "real estate agent Richmond Hill Queens"),
    ("local", "real estate agent Floral Park NY"),
    ("local", "real estate agent Long Island"),
    # NY-specific knowledge
    ("expert", "NY mansion tax calculator"),
    ("expert", "NYC closing costs explained"),
    ("expert", "Queens co-op board package process"),
    ("expert", "1031 exchange NY real estate"),
]

OUR_DOMAINS = ["gadurarealestate.com", "nitingadura.com"]
OUR_NAMES = ["Nitin Gadura", "Gadura Real Estate"]


def query_perplexity(api_key: str, q: str) -> dict:
    """Hit Perplexity Sonar API."""
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": q}],
        "max_tokens": 800,
    }
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])
        return {"text": content, "citations": citations, "engine": "perplexity"}
    except urllib.error.HTTPError as e:
        return {"text": "", "citations": [], "engine": "perplexity", "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"text": "", "citations": [], "engine": "perplexity", "error": str(e)[:80]}


def analyze(result: dict) -> dict:
    """Determine if Nitin/Gadura RE was mentioned/cited."""
    text = result.get("text", "")
    citations = result.get("citations", [])
    out = {
        "engine": result.get("engine", "?"),
        "name_mentioned": any(n.lower() in text.lower() for n in OUR_NAMES),
        "domain_cited": any(d in c for c in citations for d in OUR_DOMAINS) if citations else False,
        "citations_count": len(citations),
        "error": result.get("error", ""),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["perplexity", "all"], default="all")
    ap.add_argument("--manual-template", action="store_true",
                    help="Generate a CSV template for manual ChatGPT/Gemini/Grok results")
    args = ap.parse_args()

    out_dir = ROOT / "ai-monitoring"
    out_dir.mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    csv_path = out_dir / f"ai-visibility-{today}.csv"

    rows = []
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "")

    if args.manual_template:
        # Just emit the template — user fills in manually
        for category, q in PRIORITY_QUERIES:
            for engine in ["chatgpt", "gemini", "grok", "perplexity", "claude", "copilot"]:
                rows.append({
                    "date": today,
                    "category": category,
                    "query": q,
                    "engine": engine,
                    "name_mentioned": "",
                    "domain_cited": "",
                    "position": "",
                    "notes": "",
                })
    else:
        for category, q in PRIORITY_QUERIES:
            print(f"  Querying: {q}")
            results = []
            if perplexity_key and args.engine in ("perplexity", "all"):
                results.append(query_perplexity(perplexity_key, q))

            if not results:
                # No API keys — write a manual-entry row
                rows.append({
                    "date": today,
                    "category": category,
                    "query": q,
                    "engine": "manual_required",
                    "name_mentioned": "",
                    "domain_cited": "",
                    "position": "",
                    "notes": "No PERPLEXITY_API_KEY set. Run query manually + fill in.",
                })
                continue

            for r in results:
                a = analyze(r)
                rows.append({
                    "date": today,
                    "category": category,
                    "query": q,
                    "engine": a["engine"],
                    "name_mentioned": "yes" if a["name_mentioned"] else "no",
                    "domain_cited": "yes" if a["domain_cited"] else "no",
                    "position": "",
                    "notes": a.get("error", ""),
                })

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "date", "category", "query", "engine",
            "name_mentioned", "domain_cited", "position", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    # Quick summary
    name_hits = sum(1 for r in rows if r["name_mentioned"] == "yes")
    domain_hits = sum(1 for r in rows if r["domain_cited"] == "yes")
    print(f"\n=== AI Visibility Tracker ({today}) ===")
    print(f"  Queries: {len(PRIORITY_QUERIES)}")
    print(f"  Total rows: {len(rows)}")
    print(f"  Name mentions: {name_hits}")
    print(f"  Domain citations: {domain_hits}")
    print(f"  Report: {csv_path.relative_to(ROOT)}")
    if not perplexity_key and not args.manual_template:
        print("\n  ℹ Set PERPLEXITY_API_KEY env var to enable automated tracking.")
        print("    Free tier: 5 queries/day at https://www.perplexity.ai/settings/api")
    return 0


if __name__ == "__main__":
    sys.exit(main())
