#!/usr/bin/env python3
"""
test_apify_scrape.py — Validate LinkedIn job scraper before Stage 3
====================================================================
LEARNING NOTE — Why test the scraper in isolation?

In agent development, always validate each external dependency in
isolation before building logic on top of it. If the Apify actor
returns data in an unexpected shape, you want to discover that NOW
— not after you've written 200 lines of scoring logic.

This script:
  1. Fires a minimal LinkedIn scrape (3 jobs, London, Analytics Lead)
  2. Prints the raw response so you can see exact field names/types
  3. Saves it to data/test_scrape_output.json for inspection
  4. Shows which fields map to our job_tracker.json schema

Run:
  python3 scripts/test_apify_scrape.py

Expected output (abridged):
  [apify] Starting run for actor: nexgendata/linkedin-jobs-scraper
  [apify] Run ID: abc123...  Status: RUNNING
  [apify] Waiting for completion...
  [apify] Fetched 3 results
  [field map]
    job_title    → role
    company_name → company
    location     → location
    job_url      → jd_url
    description  → used by score_job skill
    salary       → salary_stated
  [saved] data/test_scrape_output.json
"""

import json, os, time, sys
from pathlib import Path
from urllib import request, error
from urllib.parse import urlencode

# ── Load token from .env ──────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
token    = None
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("APIFY_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break

if not token or token == "your_apify_api_token_here":
    print("ERROR: APIFY_TOKEN not set in .env")
    print("  Get it from: https://console.apify.com → Settings → Integrations")
    sys.exit(1)

ACTOR   = "nexgendata~linkedin-jobs-scraper"
BASE    = "https://api.apify.com/v2"
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type":  "application/json",
}

def api(method, path, body=None):
    url  = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req  = request.Request(url, data=data, headers=HEADERS, method=method)
    with request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

# ── Minimal scrape input ──────────────────────────────────────────────────────
SCRAPE_INPUT = {
    "keywords":           "Analytics Lead",
    "location":           "London, United Kingdom",
    "maxJobs":            3,          # keep tiny for test
    "jobType":            "full-time",
    "fetchDescriptions":  True,
}

# Allow --age flag to override posting age from command line
# Usage: python3 scripts/test_apify_scrape.py --age 1
_age = 7  # default
if "--age" in sys.argv:
    try:
        _age = int(sys.argv[sys.argv.index("--age") + 1])
    except (IndexError, ValueError):
        print("Usage: python3 scripts/test_apify_scrape.py --age <days>")
        sys.exit(1)

SCRAPE_INPUT["datePosted"] = (
    "past-24-hours" if _age <= 1 else
    "past-week"     if _age <= 7 else
    "past-month"    if _age <= 30 else ""
)

print("\n[apify] Starting test scrape...")
print(f"  Actor:    {ACTOR}")
print(f"  Query:    {SCRAPE_INPUT['keywords']} in {SCRAPE_INPUT['location']}")
print(f"  Max jobs: {SCRAPE_INPUT['maxJobs']}")

# ── Start run ─────────────────────────────────────────────────────────────────
try:
    run = api("POST", f"/acts/{ACTOR}/runs", SCRAPE_INPUT)
except error.HTTPError as e:
    print(f"\nERROR starting run: HTTP {e.code}")
    print(e.read().decode())
    sys.exit(1)

run_id = run["data"]["id"]
print(f"\n[apify] Run started — ID: {run_id}")
print("[apify] Polling for completion (this usually takes 30–90 seconds)...")

# ── Poll until done ───────────────────────────────────────────────────────────
for attempt in range(30):   # max ~2.5 minutes
    time.sleep(5)
    status_resp = api("GET", f"/actor-runs/{run_id}")
    status      = status_resp["data"]["status"]
    print(f"  [{attempt*5+5}s] Status: {status}")
    if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
        break

if status != "SUCCEEDED":
    print(f"\nERROR: Run ended with status '{status}'")
    print("  Check run details at: https://console.apify.com/actors/runs/" + run_id)
    sys.exit(1)

# ── Fetch results ─────────────────────────────────────────────────────────────
dataset_id = status_resp["data"]["defaultDatasetId"]
items_resp = api("GET", f"/datasets/{dataset_id}/items?format=json&clean=true")
items      = items_resp.get("items", items_resp) if isinstance(items_resp, dict) else items_resp

print(f"\n[apify] ✓ Fetched {len(items)} results")

# ── Show raw field names from first result ────────────────────────────────────
if items:
    print("\n[raw fields from first result]")
    first = items[0]
    for k, v in first.items():
        preview = str(v)[:80].replace('\n', ' ')
        print(f"  {k:<25} = {preview}")

# ── Field mapping to job_tracker schema ──────────────────────────────────────
# nexgendata/linkedin-jobs-scraper actual output fields:
print("\n[field map — raw actor output → job_tracker.json]")
FIELD_MAP = {
    # Native fields returned by nexgendata actor
    "job_title":      "role",
    "company_name":   "company",
    "location":       "location",
    "job_url":        "jd_url",
    "salary":         "salary_stated (native — often empty)",
    "job_type":       "→ used for filtering (full-time)",
    "posted_date":    "→ used for freshness filter",
    "description":    "→ passed to enrich_jobs.py + score_job skill",
    # Enriched by enrich_jobs.py (parsed from description text):
    "compensation_extracted": "structured salary — lower/upper/currency/display",
    "experience_years":       "min_yrs / max_yrs / display",
    "work_mode":              "Remote / Hybrid / On-site",
    # career_page_url is NOT returned natively — must be filled manually
    # after approval by opening the LinkedIn URL and clicking Apply
    "career_page_url":        "null until manually entered post-approval",
    "ats_type":               "detected from description text if ATS URL present",
}
for raw, mapped in FIELD_MAP.items():
    present = "✓" if raw in (items[0] if items else {}) else "?"
    print(f"  {present}  {raw:<20} → {mapped}")

# ── Save raw output ───────────────────────────────────────────────────────────
out_path = Path(__file__).parent.parent / "data" / "test_scrape_output.json"
out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))
print(f"\n[saved] {out_path}")
print("  Open this file to inspect the full raw structure before Stage 3.")
print("\n[RESULT] Apify LinkedIn scraper is working correctly ✓")
print("         Running enrichment step now...\n")

# ── Auto-run enrichment ───────────────────────────────────────────────────────
import subprocess
enrich_script = Path(__file__).parent / "enrich_jobs.py"
subprocess.run([sys.executable, str(enrich_script)], check=True)
