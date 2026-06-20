#!/usr/bin/env python3
"""
apify_cache.py — Cache layer for Apify LinkedIn scrape results
==============================================================
LEARNING NOTE — Why cache scrape results?

Each Apify call costs money ($0.003/job) and time (30–90 seconds).
Running job_scout.md with 6 keywords × 3 locations = 18 API calls.
If you re-run the scout on the same day (e.g. testing, debugging),
you'd pay for the same data twice.

This cache stores results keyed by (keyword, location, date).
Before calling Apify, job_scout checks the cache. If a result
< 24 hours old exists, it uses that instead. Apify is only called
when the cache is stale or missing.

Cache location: data/apify_cache/
Cache format:   one JSON file per (keyword, location) pair
Cache TTL:      24 hours by default (configurable)

Usage (from job_scout agent or directly):
  from scripts.apify_cache import CachedScraper
  scraper = CachedScraper()
  results = scraper.get("Analytics Lead", "London, United Kingdom")
  # Returns cached data if < 24h old, else calls Apify

Direct CLI (for inspection):
  python3 scripts/apify_cache.py status        ← show cache contents
  python3 scripts/apify_cache.py clear         ← delete all cache files
  python3 scripts/apify_cache.py clear --old   ← delete only stale entries
"""

import json, sys, re, time, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from urllib import request, error

ROOT       = Path(__file__).parent.parent
CACHE_DIR  = ROOT / "data" / "apify_cache"
ENV_FILE   = ROOT / ".env"
CACHE_TTL  = 24   # hours — configurable

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Load API token ────────────────────────────────────────────────────────────
def load_token():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("APIFY_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None

# ── Cache key → filename ──────────────────────────────────────────────────────
def cache_key(keyword: str, location: str) -> str:
    """Generate a safe filename from keyword + location."""
    raw = f"{keyword.lower().strip()}_{location.lower().strip()}"
    safe = re.sub(r'[^a-z0-9]+', '_', raw).strip('_')
    return safe

def cache_path(keyword: str, location: str) -> Path:
    return CACHE_DIR / f"{cache_key(keyword, location)}.json"

# ── Cache read/write ──────────────────────────────────────────────────────────
def read_cache(keyword: str, location: str) -> dict | None:
    """Return cached data if it exists and is within TTL. Else return None."""
    path = cache_path(keyword, location)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text())
        fetched_at = datetime.fromisoformat(cached["fetched_at"])
        age_hours  = (datetime.now() - fetched_at).total_seconds() / 3600
        if age_hours < CACHE_TTL:
            print(f"  [cache] HIT  {keyword} / {location} "
                  f"({age_hours:.1f}h old, TTL={CACHE_TTL}h)")
            return cached["results"]
        else:
            print(f"  [cache] STALE {keyword} / {location} "
                  f"({age_hours:.1f}h old, TTL={CACHE_TTL}h) — will re-scrape")
            return None
    except Exception:
        return None

def write_cache(keyword: str, location: str, results: list):
    """Write results to cache with timestamp."""
    path = cache_path(keyword, location)
    payload = {
        "keyword":    keyword,
        "location":   location,
        "fetched_at": datetime.now().isoformat(),
        "ttl_hours":  CACHE_TTL,
        "count":      len(results),
        "results":    results,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"  [cache] WRITE {keyword} / {location} → {len(results)} jobs cached")

# ── Apify call ────────────────────────────────────────────────────────────────
ACTOR   = "nexgendata~linkedin-jobs-scraper"
API_BASE = "https://api.apify.com/v2"

def call_apify(keyword: str, location: str,
               max_jobs: int = 25, token: str = None) -> list:
    """Call Apify actor and wait for results. Returns list of job dicts."""
    if not token:
        token = load_token()
    if not token:
        raise ValueError("APIFY_TOKEN not found in .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    def api(method, path, body=None):
        url  = f"{API_BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req  = request.Request(url, data=data, headers=headers, method=method)
        with request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    print(f"  [apify] Calling actor for: {keyword} / {location} (max {max_jobs})")
    run = api("POST", f"/acts/{ACTOR}/runs", {
        "keywords":          keyword,
        "location":          location,
        "maxJobs":           max_jobs,
        "jobType":           "full-time",
        "fetchDescriptions": True,
    })
    run_id = run["data"]["id"]
    print(f"  [apify] Run ID: {run_id}")

    for attempt in range(36):   # max 3 minutes
        time.sleep(5)
        status_resp = api("GET", f"/actor-runs/{run_id}")
        status      = status_resp["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break

    if status != "SUCCEEDED":
        raise RuntimeError(f"Apify run {run_id} ended with status: {status}")

    dataset_id = status_resp["data"]["defaultDatasetId"]
    items_resp = api("GET", f"/datasets/{dataset_id}/items?format=json&clean=true")
    items = items_resp.get("items", items_resp) if isinstance(items_resp, dict) else items_resp
    print(f"  [apify] Fetched {len(items)} results")
    return items

# ── CachedScraper — main interface ────────────────────────────────────────────
class CachedScraper:
    """
    Drop-in replacement for direct Apify calls in job_scout.md.
    Checks cache first, calls Apify only when needed.

    Usage in job_scout context:
        scraper = CachedScraper()
        results = scraper.get("Analytics Lead", "London, United Kingdom")
    """
    def __init__(self, ttl_hours: int = CACHE_TTL, token: str = None):
        self.ttl   = ttl_hours
        self.token = token or load_token()
        self.stats = {"cache_hits": 0, "apify_calls": 0, "total_jobs": 0}

    def get(self, keyword: str, location: str, max_jobs: int = 25) -> list:
        cached = read_cache(keyword, location)
        if cached is not None:
            self.stats["cache_hits"] += 1
            self.stats["total_jobs"] += len(cached)
            return cached

        # Cache miss → call Apify
        self.stats["apify_calls"] += 1
        results = call_apify(keyword, location, max_jobs, self.token)
        write_cache(keyword, location, results)
        self.stats["total_jobs"] += len(results)
        return results

    def get_batch(self, searches: list[tuple], max_jobs: int = 25) -> list:
        """
        Run multiple (keyword, location) searches, deduplicating by job_url.
        searches: [(keyword, location), ...]
        Returns: combined deduplicated list of job dicts.
        """
        seen_urls = set()
        combined  = []
        for keyword, location in searches:
            results = self.get(keyword, location, max_jobs)
            for job in results:
                url = job.get("job_url") or job.get("url") or ""
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    combined.append(job)
                elif not url:
                    combined.append(job)

        print(f"\n  [cache] Batch complete:")
        print(f"    Cache hits:   {self.stats['cache_hits']}")
        print(f"    Apify calls:  {self.stats['apify_calls']}")
        print(f"    Total unique: {len(combined)} jobs")
        return combined

    def summary(self):
        return self.stats

# ── CLI — cache status and management ────────────────────────────────────────
def cli_status():
    files = sorted(CACHE_DIR.glob("*.json"))
    if not files:
        print("\n  Cache is empty.\n")
        return
    print(f"\n  {'File':<45} {'Keyword':<25} {'Location':<25} {'Jobs':>5} {'Age':>8} {'Status'}")
    print(f"  {'-'*120}")
    for f in files:
        try:
            d = json.loads(f.read_text())
            age = (datetime.now() - datetime.fromisoformat(d["fetched_at"])).total_seconds()/3600
            status = "✓ fresh" if age < CACHE_TTL else "✗ stale"
            print(f"  {f.name:<45} {d.get('keyword',''):<25} "
                  f"{d.get('location',''):<25} {d.get('count',0):>5} "
                  f"{age:>6.1f}h {status}")
        except Exception as e:
            print(f"  {f.name:<45} ERROR: {e}")
    print()

def cli_clear(old_only=False):
    files = list(CACHE_DIR.glob("*.json"))
    removed = 0
    for f in files:
        if old_only:
            try:
                d = json.loads(f.read_text())
                age = (datetime.now() - datetime.fromisoformat(d["fetched_at"])).total_seconds()/3600
                if age < CACHE_TTL:
                    continue
            except:
                pass
        f.unlink()
        removed += 1
    label = "stale" if old_only else "all"
    print(f"\n  Removed {removed} {label} cache files.\n")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        cli_status()
    elif mode == "clear":
        old_only = "--old" in sys.argv
        cli_clear(old_only)
    else:
        print(__doc__)
