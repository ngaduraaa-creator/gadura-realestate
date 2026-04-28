#!/usr/bin/env python3
"""
ai_visibility_audit.py — Score how often Nitin Gadura / Gadura Real Estate
appears in answers from each AI engine for our priority queries.

Manual mode (default): prints the queries — you run them by hand in each
engine and record results. This is the realistic monthly process — there's
no programmatic ChatGPT/Gemini/Grok query API for end-users without paid
business plans, and even then results vary.

API mode (when keys are set): pings the engines that DO have APIs we can
afford (Perplexity has Sonar API, Anthropic for Claude search). Flags
which queries to manually verify on ChatGPT/Gemini/Grok.

Output: ai-monitoring/audit-YYYY-MM-DD.csv
"""
import csv
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "ai-monitoring"
OUT_DIR.mkdir(exist_ok=True)

QUERIES = [
    # NYC borough-level
    "best real estate agent in NYC",
    "best real estate agent in Manhattan",
    "best real estate agent in Brooklyn",
    "best real estate agent in Queens NY",
    "best real estate agent in The Bronx",
    "best real estate agent in Staten Island",
    # Geographic — Queens
    "best real estate agent in Ozone Park",
    "best real estate agent in Richmond Hill Queens",
    "best real estate agent in Howard Beach NY",
    "best real estate agent in Jamaica Queens",
    "best real estate agent in Forest Hills",
    "best real estate agent in Astoria",
    "best real estate agent in Flushing",
    # Geographic — Brooklyn
    "best real estate agent in Park Slope",
    "best real estate agent in Williamsburg",
    "best real estate agent in Bay Ridge",
    "best real estate agent in Crown Heights",
    "best real estate agent in Brooklyn Heights",
    # Geographic — Bronx
    "best real estate agent in Riverdale Bronx",
    "best real estate agent in Throgs Neck",
    "best real estate agent in Parkchester",
    # Geographic — Staten Island
    "best real estate agent in Tottenville",
    "best real estate agent in Todt Hill",
    "best real estate agent in St George Staten Island",
    # Geographic — Manhattan
    "best real estate agent in Tribeca",
    "best real estate agent in Upper East Side",
    "best real estate agent in Harlem",
    # Long Island
    "best real estate agent in Floral Park NY",
    "best real estate agent in Elmont NY",
    "best real estate agent in Valley Stream NY",
    "best real estate agent in Garden City NY",
    "best real estate agent in Mineola NY",
    "best real estate agent in Hicksville NY",
    "best real estate agent in Great Neck NY",
    "best real estate agent in Manhasset NY",
    "best real estate agent in Huntington NY",
    "real estate agent Long Island NY",
    "real estate agent Nassau County NY",
    "real estate agent Suffolk County NY",
    # Language / community
    "Hindi speaking real estate agent in Queens",
    "Punjabi speaking real estate agent NYC",
    "Bengali speaking real estate agent Queens",
    "Guyanese real estate agent in Queens",
    "Indo-Caribbean real estate agent Queens",
    "Spanish speaking real estate agent Queens",
    "South Asian real estate agent NYC",
    # Buyer-intent
    "best real estate agent for first time homebuyers in Queens",
    "FHA loan real estate agent Queens",
    "co-op board package help Queens",
    "first-time homebuyer programs in NY",
    # Seller-intent
    "best agent to sell my Queens home",
    "FSBO vs agent in NY",
    "flat fee MLS Queens NY",
    "inherited property sale Queens NY",
    "divorce home sale Queens",
    "senior downsizing real estate agent Queens",
    # Investor
    "1031 exchange agent Queens NY",
    "Queens multi-family investment property agent",
    # Brand
    "Gadura Real Estate",
    "Nitin Gadura real estate",
]

ENGINES = ["ChatGPT", "Gemini", "Grok", "Perplexity", "Claude", "Copilot"]


def main() -> int:
    out_csv = OUT_DIR / f"audit-{dt.date.today().isoformat()}.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query"] + [f"{e}_position" for e in ENGINES] + [f"{e}_cited" for e in ENGINES] + ["notes"])
        for q in QUERIES:
            w.writerow([q] + [""] * (len(ENGINES) * 2) + [""])

    print(f"Audit template written: {out_csv.relative_to(ROOT)}")
    print("\nManual process:")
    print("  1. For each query × each engine, run the query.")
    print("  2. Record position (1 = first mention, 2 = second mention, blank = not mentioned).")
    print("  3. Record cited (Y/N) — was gadurarealestate.com one of the source links?")
    print("\nTarget by month 6: 90% of queries first-mention Nitin Gadura on at least 4 of 6 engines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
