# Agent: application_prep
# Stage 4 — TO BE BUILT
#
# LEARNING NOTE — Agent Handoffs
# ============================================================
# This agent is triggered AFTER job_scout has run and you have
# manually changed a job's status to "Approved" in job_tracker.json.
# (In Stage 5, the on_job_approved hook will trigger this automatically.)
#
# This illustrates a key agent design pattern: agents don't call
# each other directly — they communicate via shared state (the
# job_tracker.json file). This loose coupling means each agent
# can be tested, rerun, or replaced independently.
#
# This agent will:
#   STEP 1: Read job_tracker.json → find all entries with status "Approved"
#           AND resume_path = null (not yet prepped)
#   STEP 2: For each → fetch the JD from jd_url (web fetch)
#   STEP 3: Invoke skills/tailor_resume.md → generate tailored resume text
#   STEP 4: Render resume as PDF → save to outputs/applications/[folder]/resume.pdf
#   STEP 5: Invoke skills/draft_cover_letter.md → save cover_letter.md
#   STEP 6: Write meta.json to application folder
#   STEP 7: Update job_tracker.json → status "Prep Complete", add file paths
#   STEP 8: Print confirmation for each application prepared
#
# TO BE WRITTEN IN STAGE 4
