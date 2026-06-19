# Agent: job_scout
# Stage 4 — TO BE BUILT
#
# LEARNING NOTE — What is an Agent file?
# ============================================================
# An agent is a multi-step orchestrator. Unlike a skill (which
# does ONE thing), an agent chains multiple skills and MCP tool
# calls together to complete an end-to-end workflow.
#
# Key difference from skills:
#   Skill  = does one thing, returns output, no side effects
#   Agent  = coordinates multiple skills + tools, reads/writes
#             files, calls MCP servers, updates state
#
# Agents in Claude Code are written as instructional markdown.
# Claude Code reads the agent file and executes it step-by-step,
# calling tools and skills as described.
#
# This agent will:
#   STEP 1: Read job search preferences from CLAUDE.md
#   STEP 2: Call Apify MCP → scrape LinkedIn jobs with filters
#           (location: UK cities, roles: target titles, date: last 7 days)
#   STEP 3: For each job → invoke skills/score_job.md
#   STEP 4: Auto-shortlist jobs with score ≥ 75 → write to job_tracker.json
#   STEP 5: Flag jobs scoring 60–74 → write with status "Review Needed"
#   STEP 6: Auto-reject jobs < 60 or explicit no-sponsorship → log only
#   STEP 7: Print summary to terminal: X shortlisted, Y flagged, Z rejected
#
# TO BE WRITTEN IN STAGE 4
