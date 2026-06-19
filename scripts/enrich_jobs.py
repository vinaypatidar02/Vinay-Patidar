#!/usr/bin/env python3
"""
enrich_jobs.py — Post-processing enrichment for raw Apify scrape output
========================================================================
LEARNING NOTE — Why a separate enrichment step?

The actor (nexgendata/linkedin-jobs-scraper) returns core fields
natively: job_title, company_name, location, salary, job_type,
posted_date, and description. This script adds three enriched fields
by parsing the description text:
  1. compensation_extracted — structured salary (lower/upper/currency)
     supplements the native salary field which LinkedIn often leaves blank
  2. experience_years       — years of experience requirement
  3. work_mode              — Remote / Hybrid / On-site

NOTE: career_page_url (the real ATS apply URL) is NOT available from
the actor. LinkedIn's public API does not expose it for unauthenticated
requests. It defaults to null and must be filled in manually when you
approve a job — open the LinkedIn URL, click Apply, copy the redirect.

Run:
  python3 scripts/enrich_jobs.py

Input:  data/test_scrape_output.json   (from test_apify_scrape.py)
Output: data/enriched_scrape_output.json
"""

import json, re, sys
from pathlib import Path
from typing import Optional

ROOT     = Path(__file__).parent.parent
RAW_PATH = ROOT / "data" / "test_scrape_output.json"
OUT_PATH = ROOT / "data" / "enriched_scrape_output.json"

if not RAW_PATH.exists():
    print(f"ERROR: {RAW_PATH} not found.")
    print("  Run python3 scripts/test_apify_scrape.py first.")
    sys.exit(1)

jobs = json.loads(RAW_PATH.read_text())
print(f"\n[enrich] Loaded {len(jobs)} jobs from {RAW_PATH.name}")


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTOR 1 — Compensation (parsed from description text)
# Supplements the native salary field which LinkedIn often leaves blank.
# ─────────────────────────────────────────────────────────────────────────────
def extract_compensation(text: str, native_salary: str = "") -> dict:
    """
    Priority:
      1. Use native salary field if it contains a number
      2. Parse description text for salary ranges / single figures
      3. Soft signals: competitive / DOE / negotiable
      4. Not stated
    Returns: found, display, currency, lower, upper, source
    """
    if not text:
        text = ""

    CURRENCIES = {"£": "GBP", "$": "USD", "€": "EUR"}

    def parse_amount(s: str) -> Optional[int]:
        s = s.replace(",", "").strip()
        if s.lower().endswith("k"):
            try: return int(float(s[:-1]) * 1000)
            except: return None
        try: return int(float(s))
        except: return None

    def find_in(src: str, source_label: str):
        # Range: £80,000–£100,000 / £80k - £120k / $120,000 to $150,000
        pattern = r"""
            (£|\$|€)\s*
            ([\d,]+(?:\.\d+)?k?)\s*
            (?:–|-|to|and)\s*
            (?:£|\$|€)?\s*
            ([\d,]+(?:\.\d+)?k?)
            (?:\s*(?:per\s+(?:year|annum|pa|month)|pa|p\.a\.|/yr))?
        """
        m = re.search(pattern, src, re.IGNORECASE | re.VERBOSE)
        if m:
            cur = CURRENCIES.get(m.group(1), "unknown")
            lo  = parse_amount(m.group(2))
            hi  = parse_amount(m.group(3))
            return {"found": True, "source": source_label,
                    "display": f"{m.group(1)}{m.group(2)} – {m.group(1)}{m.group(3)}",
                    "currency": cur, "lower": lo, "upper": hi, "raw": m.group(0).strip()}

        # Single: Up to £95k / From £85,000 / £90,000
        m2 = re.search(r"(Up\s+to|From|circa|~)?\s*(£|\$|€)\s*([\d,]+(?:\.\d+)?k?)",
                       src, re.IGNORECASE)
        if m2:
            cur    = CURRENCIES.get(m2.group(2), "unknown")
            amount = parse_amount(m2.group(3))
            prefix = (m2.group(1) or "").strip()
            lo     = None if prefix.lower() in ("up to",) else amount
            hi     = amount if prefix.lower() in ("up to",) else None
            return {"found": True, "source": source_label,
                    "display": f"{prefix} {m2.group(2)}{m2.group(3)}".strip(),
                    "currency": cur, "lower": lo, "upper": hi,
                    "raw": m2.group(0).strip()}
        return None

    # 1. Native salary field first
    if native_salary and re.search(r"[\d£$€]", native_salary):
        result = find_in(native_salary, "native_field")
        if result: return result

    # 2. Description text
    result = find_in(text, "description")
    if result: return result

    # 3. Soft signals
    soft = re.search(
        r"\b(competitive\s+(?:salary|compensation|package)|"
        r"doe|depending\s+on\s+experience|negotiable|market\s+rate)\b",
        text, re.IGNORECASE)
    if soft:
        return {"found": True, "source": "description",
                "display": "Competitive / DOE", "currency": None,
                "lower": None, "upper": None, "raw": soft.group(0)}

    return {"found": False, "display": "Not stated", "source": "none",
            "currency": None, "lower": None, "upper": None, "raw": None}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTOR 2 — Years of experience
# ─────────────────────────────────────────────────────────────────────────────
def extract_experience_years(text: str) -> dict:
    """
    Extracts years of experience requirement from description.
    Returns: found, min_yrs, max_yrs, display
    """
    if not text:
        return {"found": False, "min_yrs": None, "max_yrs": None,
                "display": "Not specified"}

    # Range: 3-5 years / 3 to 5 years
    m = re.search(
        r"(\d+)\s*(?:-|to|–|and)\s*(\d+)\s+years?(?:'s?)?\s*"
        r"(?:of\s+)?(?:relevant\s+)?experience",
        text, re.IGNORECASE)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return {"found": True, "min_yrs": lo, "max_yrs": hi,
                "display": f"{lo}–{hi} years"}

    # Single: 5+ years / at least 6 years / minimum 4 years
    m2 = re.search(
        r"(?:at\s+least\s+|minimum\s+(?:of\s+)?)?(\d+)\+?\s+years?"
        r"(?:'s?)?\s*(?:of\s+)?(?:relevant\s+)?experience",
        text, re.IGNORECASE)
    if m2:
        yrs = int(m2.group(1))
        return {"found": True, "min_yrs": yrs, "max_yrs": None,
                "display": f"{yrs}+ years"}

    # Soft: several years / extensive experience
    if re.search(r"\bseveral\s+years\b|\bextensive\s+experience\b", text, re.I):
        return {"found": True, "min_yrs": None, "max_yrs": None,
                "display": "Several years (not specified)"}

    return {"found": False, "min_yrs": None, "max_yrs": None,
            "display": "Not specified"}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTOR 3 — Work mode (replaces office_name)
# ─────────────────────────────────────────────────────────────────────────────
def extract_work_mode(text: str, native_work_type: str = "") -> str:
    """
    Returns: "Remote" | "Hybrid (Xd/week)" | "Hybrid" | "On-site" | "Unknown"
    Checks native work_type field first, then parses description.
    """
    # Native field from actor (e.g. "Remote", "Hybrid", "On-site")
    if native_work_type:
        nt = native_work_type.lower()
        if "remote" in nt:   return "Remote"
        if "hybrid" in nt:   return "Hybrid"
        if "on-site" in nt or "onsite" in nt: return "On-site"

    if not text:
        return "Unknown"

    if re.search(r"\bfully\s+remote\b|\b100%\s+remote\b", text, re.I):
        return "Remote"
    if re.search(r"\bhybrid\b", text, re.I):
        days = re.search(
            r"(\d+)\s+days?\s+(?:per\s+week\s+)?(?:in|(?:in\s+)?(?:the\s+)?office)",
            text, re.I)
        return f"Hybrid ({days.group(1)}d/week)" if days else "Hybrid"
    if re.search(r"\bon[- ]?site\b|\bin[- ]?office\b|\boffice[- ]?based\b", text, re.I):
        return "On-site"
    return "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENRICHMENT LOOP
# ─────────────────────────────────────────────────────────────────────────────
enriched = []
stats    = {"compensation": 0, "experience": 0, "apply_url": 0}

for i, job in enumerate(jobs):
    desc        = job.get("description", "") or ""
    nat_salary  = str(job.get("salary", "") or "")
    nat_wtype   = str(job.get("work_type", "") or job.get("workType", "") or "")

    # career_page_url — LinkedIn's public API does not expose the real ATS
    # apply URL in unauthenticated scrapes. It must be filled in manually.
    # Workflow: when a job is approved, open its LinkedIn URL, click Apply,
    # copy the redirect URL (Greenhouse/Lever/Workday etc.) and paste it into
    # job_tracker.json career_page_url field before application prep runs.
    # The enrich step checks description text as a last-resort fallback only.
    ATS_PATTERNS = {
        "greenhouse":      r"https?://(?:boards\.)?greenhouse\.io/[\w/-]+",
        "lever":           r"https?://jobs\.lever\.co/[\w/-]+",
        "workday":         r"https?://[\w-]+\.myworkdayjobs\.com/[\w/-]+",
        "ashby":           r"https?://jobs\.ashbyhq\.com/[\w/-]+",
        "smartrecruiters": r"https?://jobs\.smartrecruiters\.com/[\w/-]+",
        "icims":           r"https?://[\w-]+\.icims\.com/jobs/[\w/-]+",
        "bamboohr":        r"https?://[\w-]+\.bamboohr\.com/jobs/[\w/-]+",
        "teamtailor":      r"https?://[\w-]+\.teamtailor\.com/jobs/[\w/-]+",
    }
    career_page_url = None
    ats_type = "unknown"
    for name, pattern in ATS_PATTERNS.items():
        m = re.search(pattern, desc, re.IGNORECASE)
        if m:
            career_page_url = m.group(0)
            ats_type = name
            break
    is_easy = bool(re.search(r"\beasy\s*apply\b", desc, re.IGNORECASE))

    comp      = extract_compensation(desc, nat_salary)
    exp       = extract_experience_years(desc)
    work_mode = extract_work_mode(desc, nat_wtype)

    print(f"\n[enrich] {i+1}/{len(jobs)}: "
          f"{job.get('job_title','?')} @ {job.get('company_name','?')}")
    print(f"  compensation: {'✓ ' + comp['display'] if comp['found'] else '✗ not stated'}")
    print(f"  experience:   {'✓ ' + exp['display'] if exp['found'] else '✗ not specified'}")
    print(f"  work mode:    {work_mode}")
    if career_page_url:
        print(f"  career URL:   ✓ found in description ({ats_type}): {career_page_url[:60]}")
    elif is_easy:
        print(f"  career URL:   ⚠ Easy Apply (no external URL)")
    else:
        print(f"  career URL:   — needs manual input after approval")

    if comp['found']:  stats["compensation"] += 1
    if exp['found']:   stats["experience"]   += 1
    if career_page_url: stats["apply_url"]   += 1

    enriched.append({
        **job,
        "compensation_extracted": comp,
        "experience_years":       exp,
        "work_mode":              work_mode,
        "career_page_url":        career_page_url,   # null until manually filled
        "ats_type":               ats_type,
        "is_easy_apply":          is_easy,
    })

OUT_PATH.write_text(json.dumps(enriched, indent=2, ensure_ascii=False))
n = len(jobs)
print(f"""
[enrich] ────────────────────────────────────────
  Jobs processed: {n}
  Compensation:   {stats['compensation']}/{n} found
  Experience:     {stats['experience']}/{n} found
  Apply URL:      {stats['apply_url']}/{n} found
[saved] {OUT_PATH}
[enrich] ────────────────────────────────────────
""")