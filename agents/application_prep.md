# Agent: application_prep
# Stage 4 — ACTIVE
#
# ============================================================
# LEARNING NOTE — Agent Handoffs via Shared State
# ============================================================
# This agent is triggered after sheets_sync.py pull has run
# and updated job_tracker.json with your Sheet edits. It does
# not communicate directly with job_scout — it reads the shared
# state file. This loose coupling means each agent is testable
# and replaceable independently.
# ============================================================

# ── TRIPLE-CONDITION GATE (check before doing anything) ───────
# Only process entries where ALL THREE are true:
#   1. status = "Approved"
#   2. career_page_url is not null and not empty
#   3. resume_path is null (prep not already done)
#
# If status = "Approved" but career_page_url is null:
#   Log: "SKIPPED [Company] / [Role] — career_page_url missing.
#         Paste ATS URL in Google Sheet Col M, then re-run pull."
#   Do NOT process. Move to next entry.
#
# If resume_path is already set:
#   Log: "SKIPPED [Company] / [Role] — already prepped at [resume_path]"
#   Do NOT re-process. This makes the agent safely re-runnable.

# ── FOR EACH QUALIFYING JOB ──────────────────────────────────

# STEP 1 — FETCH JD TEXT
#   Web-fetch the job description from jd_url.
#   If fetch fails (404, timeout, redirected away):
#     Log warning, use description from enriched_scrape_output.json
#     if job_id matches, otherwise proceed with available data.
#   Log: "[prep] Fetched JD for [Company] / [Role]"

# STEP 2 — SELECT RESUME VARIANT
#   Apply selection logic from CLAUDE.md Section 5:
#     product/growth/ecommerce/SaaS → data/product_resume.pdf content
#     CRM/lifecycle/retention/customer → data/customer_resume.pdf content
#     commercial/pricing/general → data/master_resume.pdf content
#   Log: "[prep] Using [variant] resume as base"

# STEP 3 — TAILOR RESUME
#   Invoke skills/tailor_resume.md with:
#     job: <tracker entry>
#     jd_text: <fetched or cached JD>
#     variant: <selected above>
#   Receive tailored resume JSON output.

# STEP 4 — RENDER RESUME PDF
#   Create output folder:
#     outputs/applications/[Company]_[RoleShortName]_[YYYYMMDD]/
#   Write tailored resume JSON to a temp file.
#   Call: python3 scripts/pdf_renderer.py resume <temp.json> <output_path>
#   Output path: [folder]/[Company]_[RoleTitle]_[YYYYMMDD].pdf
#   Confirm file was created.
#   Log: "[prep] Resume PDF → [path]"

# STEP 5 — DRAFT COVER LETTER
#   Invoke skills/draft_cover_letter.md with:
#     job: <tracker entry>
#     jd_text: <same JD text>
#     tailored_resume: <output from Step 3>
#     today: <YYYY-MM-DD>
#   Receive cover letter JSON output.

# STEP 6 — RENDER COVER LETTER PDF
#   Write cover letter JSON to a temp file.
#   Call: python3 scripts/pdf_renderer.py cover <temp.json> <output_path>
#   Output path: [folder]/[Company]_CoverLetter_[YYYYMMDD].pdf
#   Confirm file was created.
#   Log: "[prep] Cover letter PDF → [path]"

# STEP 7 — WRITE meta.json
#   Save to [folder]/meta.json:
#   {
#     "company":          "<company>",
#     "role":             "<role>",
#     "job_id":           "<job_id>",
#     "jd_url":           "<jd_url>",
#     "career_page_url":  "<career_page_url>",
#     "ats_type":         "<ats_type>",
#     "fit_score":        <score>,
#     "resume_variant":   "<product|customer|master>",
#     "prep_date":        "<YYYY-MM-DD>",
#     "notes":            "<any flags from tracker>"
#   }

# STEP 8 — UPDATE job_tracker.json
#   Read current file (never overwrite blindly).
#   Find the entry by id. Update:
#     status:              "Prep Complete"
#     resume_path:         "<relative path to resume PDF>"
#     cover_letter_path:   "<relative path to cover letter PDF>"
#     status_history:      append { "status": "Prep Complete",
#                                   "date": "<today>",
#                                   "source": "application_prep_agent" }
#   Write back to data/job_tracker.json.
#   Log: "[prep] Tracker updated → Prep Complete"

# STEP 9 — SYNC TO GOOGLE SHEETS
#   Run: python3 scripts/sheets_sync.py push
#   This updates the Sheet so you can see "Prep Complete" status
#   and the resume/cover letter paths immediately.
#   Log: "[prep] Google Sheet synced"

# ── COMPLETION SUMMARY ────────────────────────────────────────
# After processing all qualifying jobs, print:
#   ═══════════════════════════════════════
#    Application Prep — <date>
#   ═══════════════════════════════════════
#    Processed:  X jobs
#    Skipped:    Y jobs (career_page_url missing)
#    Skipped:    Z jobs (already prepped)
#   ───────────────────────────────────────
#    Resume + cover letter PDFs are in outputs/applications/
#    Next step: open career_page_url for each job and submit.
#    After submitting, update status to "Applied" in the Sheet
#    or wait for confirmation email to trigger auto-update.
#   ═══════════════════════════════════════
