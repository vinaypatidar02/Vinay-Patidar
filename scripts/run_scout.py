#!/usr/bin/env python3
"""
run_scout.py — Job Scout Runner
================================
Claude Code calls this script directly. Real CLI arguments — no ambiguity.

Usage:
  python3 scripts/run_scout.py                    # default: 5 searches, age 7
  python3 scripts/run_scout.py --age 1            # today's postings only
  python3 scripts/run_scout.py --age 7            # last week (default)
  python3 scripts/run_scout.py --expanded         # 10 searches instead of 5
  python3 scripts/run_scout.py --age 1 --expanded # today, all 10 searches

This script is what job_scout.md Step 1 calls. It handles:
  - Argument parsing (age, expanded flag)
  - Cache check and cost transparency before any Apify call
  - Calling CachedScraper with the right parameters
  - Saving raw output to data/test_scrape_output.json
  - Calling enrich_jobs.py as a subprocess
"""

import sys, json, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Parse arguments ───────────────────────────────────────────────────────────
args        = sys.argv[1:]
expanded    = "--expanded" in args
age         = 7   # default

if "--age" in args:
    idx = args.index("--age")
    try:
        age = int(args[idx + 1])
    except (IndexError, ValueError):
        print("ERROR: --age requires a number, e.g. --age 1")
        sys.exit(1)

# ── Search lists ──────────────────────────────────────────────────────────────
SEARCHES_DEFAULT = [
    ("Analytics Lead",        "London, United Kingdom"),
    ("Analytics Manager",     "London, United Kingdom"),
    ("Lead Data Analyst",     "London, United Kingdom"),
    ("Analytics Lead",        "Manchester, United Kingdom"),
    ("Analytics Manager",     "Manchester, United Kingdom"),
]

SEARCHES_EXPANDED = [
    ("Analytics Lead",          "London, United Kingdom"),
    ("Lead Data Analyst",       "London, United Kingdom"),
    ("Lead Business Analyst",   "London, United Kingdom"),
    ("Analytics Manager",       "London, United Kingdom"),
    ("Lead Product Analyst",    "London, United Kingdom"),
    ("Data Analytics Manager",  "London, United Kingdom"),
    ("Analytics Lead",          "Manchester, United Kingdom"),
    ("Analytics Manager",       "Manchester, United Kingdom"),
    ("Analytics Lead",          "Birmingham, United Kingdom"),
    ("Analytics Manager",       "Birmingham, United Kingdom"),
]

searches = SEARCHES_EXPANDED if expanded else SEARCHES_DEFAULT

# ── Map age to LinkedIn filter ────────────────────────────────────────────────
# LinkedIn only supports fixed buckets — no arbitrary day count
if age <= 1:
    date_filter = "past-24-hours"
    age_label   = "today only (past 24h)"
elif age <= 7:
    date_filter = "past-week"
    age_label   = f"last week (--age {age} maps to past-week)"
elif age <= 30:
    date_filter = "past-month"
    age_label   = f"last month (--age {age} maps to past-month)"
else:
    date_filter = ""
    age_label   = "all time"

# ── Cost transparency ─────────────────────────────────────────────────────────
print(f"\n[scout] ──────────────────────────────────────────")
print(f"[scout] Search list:  {'expanded (10)' if expanded else 'default (5)'}")
print(f"[scout] Posting age:  {age_label}")
print(f"[scout] Max possible cost: {len(searches)} searches × 25 jobs × $0.003 = "
      f"${len(searches) * 25 * 0.003:.2f} (actual will be lower)")
print(f"[scout] ──────────────────────────────────────────\n")

# ── Check cache first ─────────────────────────────────────────────────────────
from scripts.apify_cache import CachedScraper, read_cache

cache_hits  = sum(1 for kw, loc in searches if read_cache(kw, loc) is not None)
apify_calls = len(searches) - cache_hits
print(f"[scout] Cache status: {cache_hits}/{len(searches)} searches cached "
      f"→ {apify_calls} will call Apify")

if apify_calls == 0:
    print(f"[scout] All results from cache — $0.00 cost")
else:
    est = apify_calls * 25 * 0.003
    print(f"[scout] Estimated max cost for {apify_calls} Apify call(s): ${est:.2f}")

confirm = input("\nProceed? [Y/n]: ").strip().lower()
if confirm not in ("", "y", "yes"):
    print("[scout] Aborted.")
    sys.exit(0)

# ── Run scrape ────────────────────────────────────────────────────────────────
scraper = CachedScraper(post_age_days=age)
results = scraper.get_batch(searches, max_jobs=25, post_age_days=age)

# Save raw output
raw_path = ROOT / "data" / "test_scrape_output.json"
raw_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"\n[scout] Saved {len(results)} raw jobs → {raw_path}")

# ── Run enrichment ────────────────────────────────────────────────────────────
print(f"\n[scout] Running enrichment...")
result = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "enrich_jobs.py")],
    cwd=ROOT
)
if result.returncode != 0:
    print("[scout] ERROR: enrich_jobs.py failed — aborting")
    sys.exit(1)

print(f"\n[scout] Done. Enriched output → data/enriched_scrape_output.json")
print(f"[scout] Next: Claude Code reads enriched output and runs score_job skill")
