# Agent: job_scout
# Stage 4 — ACTIVE
#
# ============================================================
# LEARNING NOTE — Agent vs Skill
# ============================================================
# This agent orchestrates the full scrape-to-shortlist pipeline.
# It calls the Apify MCP tool, runs enrich_jobs.py, invokes the
# score_job skill for each result, writes to job_tracker.json,
# and syncs to Google Sheets. Skills do one thing; this agent
# coordinates many things in sequence.
# ============================================================

# ── PREREQUISITES ─────────────────────────────────────────────
# Before running, confirm:
#   - APIFY_TOKEN is set in .env
#   - data/job_tracker.json exists and is valid JSON
#   - Python venv is active (.venv/bin/activate)
#   - scripts/enrich_jobs.py and scripts/apify_cache.py are present

# ── STEP 1 — SCRAPE (with cache) ─────────────────────────────
# Call scripts/run_scout.py directly — do NOT interpret --age or
# --expanded flags yourself. Pass them straight to the script.
#
# Mapping of user prompts → exact command to run:
#
#   "run scout"                → python3 scripts/run_scout.py
#   "run scout --age 1"        → python3 scripts/run_scout.py --age 1
#   "run scout --age 7"        → python3 scripts/run_scout.py --age 7
#   "run scout --expanded"     → python3 scripts/run_scout.py --expanded
#   "run scout --age 1 --expanded" → python3 scripts/run_scout.py --age 1 --expanded
#
# The script handles everything:
#   - Argument parsing (age, expanded)
#   - Cache check + cost estimate printed before any Apify call
#   - Confirmation prompt (user types Y to proceed)
#   - CachedScraper.get_batch() with correct post_age_days
#   - Saves raw output to data/test_scrape_output.json
#   - Calls enrich_jobs.py automatically as a subprocess
#
# DEFAULT behaviour (no flags): 5 searches, age 7 days
# NEVER default to expanded list or age values not explicitly passed.

# ── STEP 2 — ENRICH ──────────────────────────────────────────
# Run enrichment as a subprocess:
#   python3 scripts/enrich_jobs.py
#
# This adds to each job:
#   compensation_extracted, experience_years, work_mode,
#   career_page_url (if ATS URL in description), ats_type, is_easy_apply
# Output is sorted newest-first and saved to data/enriched_scrape_output.json.
#
# Read enriched output for the next steps.
# Log: "[scout] Enriched X jobs, sorted newest-first"

# ── STEP 3 — SCORE & CLASSIFY ────────────────────────────────
# For each job in enriched output (newest first):
#   Invoke skills/score_job.md with the job object.
#   The skill runs the duplicate check internally and returns:
#     action: "shortlist" | "review" | "reject" | "skip"
#
#   Collect results into four buckets:
#     shortlisted  → action = "shortlist"
#     review       → action = "review"
#     rejected     → action = "reject"
#     skipped      → action = "skip" (duplicates)
#
# Log each result:
#   "✓ SHORTLIST  [score] [Company] / [Role] / [Location]"
#   "⚠ REVIEW    [score] [Company] / [Role] / [Location]"
#   "✗ REJECT    [score] [Company] / [Role] — [reason]"
#   "— SKIP      [Company] / [Role] — duplicate of [existing_id]"

# ── STEP 4 — WRITE TO TRACKER ────────────────────────────────
# For shortlisted and review jobs (NOT rejected or skipped):
#   1. Read data/job_tracker.json (always read before writing)
#   2. Build a new entry:
#      {
#        "id":                     "app_<NNN>",     ← next sequential ID
#        "source":                 "job_scout_agent",
#        "job_id":                 "<from scrape>",
#        "company":                "<company_name>",
#        "role":                   "<job_title>",
#        "jd_url":                 "<job_url>",
#        "career_page_url":        "<from enrichment or null>",
#        "fit_score":              <integer>,
#        "fit_score_breakdown":    <from score_job output>,
#        "visa_sponsorship_status": "<from score_job output>",
#        "salary_stated":          "<from score_job output>",
#        "salary_meets_threshold": <bool or null>,
#        "location":               "<location>",
#        "work_mode":              "<from enrichment>",
#        "experience_req":         "<from enrichment>",
#        "ats_type":               "<from enrichment>",
#        "is_easy_apply":          <bool>,
#        "posted_date":            "<from scrape>",
#        "applied_date":           null,
#        "status":                 "Shortlisted" | "Review Needed",
#        "status_history": [
#          { "status": "Shortlisted", "date": "<today>", "source": "job_scout_agent" }
#        ],
#        "tracking_url":           null,
#        "resume_path":            null,
#        "cover_letter_path":      null,
#        "emails_received":        [],
#        "notes":                  "<any flags e.g. 'Salary TBC'>",
#        "flags":                  ["Salary TBC", ...]
#      }
#   3. Append to applications[] array
#   4. Write back to data/job_tracker.json (merge, never overwrite blindly)
#
# Log: "[scout] Wrote X entries to job_tracker.json"

# ── STEP 5 — SYNC TO GOOGLE SHEETS ───────────────────────────
# Run: python3 scripts/sheets_sync.py push
# This updates the Google Sheet with all new shortlisted entries
# so you can review, edit status, and paste career_page_url.
# Log: "[scout] Google Sheet updated"

# ── STEP 6 — SUMMARY ─────────────────────────────────────────
# Print a clean summary:
#   ═══════════════════════════════════════
#    Job Scout Run — <date>
#   ═══════════════════════════════════════
#    Raw scraped:     X
#    After enrichment: X
#    Shortlisted:     X  ← added to tracker + sheet
#    For review:      X  ← added to tracker + sheet
#    Auto-rejected:   X  ← logged only
#    Duplicates:      X  ← skipped
#   ───────────────────────────────────────
#    Next step: open Google Sheet, review shortlisted jobs,
#    paste career_page_url, set status → Approved,
#    then run: python3 scripts/sheets_sync.py pull
#   ═══════════════════════════════════════

# ── ERROR HANDLING ────────────────────────────────────────────
# If Apify call fails → log error + HTTP code, abort gracefully
# If enrich_jobs.py fails → log error, abort (do not score raw data)
# If score_job returns unexpected shape → log + skip that job, continue
# If job_tracker.json write fails → log error, do not exit silently
