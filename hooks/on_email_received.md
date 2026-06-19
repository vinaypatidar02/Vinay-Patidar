# Hook: on_email_received
# Stage 5 — TO BE BUILT
#
# LEARNING NOTE — Polling vs Event-Driven Hooks
# ============================================================
# True real-time email hooks require a push mechanism (Gmail
# push notifications via Pub/Sub). For our learning project,
# we'll use a polling approach — Claude checks Gmail every
# N minutes using a scheduled task.
#
# This is an important architectural decision to understand:
#   Push model  = instant, more complex setup, needs a server
#   Pull/Poll   = slight delay, simpler, works locally
#
# For a job search (where a 2-hour delay is fine), polling
# is the right choice. You'll learn the push model when you
# scale up.
#
# THIS HOOK:
#   Type: Scheduled polling (every 2 hours, or on-demand)
#   Trigger: Run Gmail MCP search for unprocessed job emails
#   Filter: Emails in last 48 hours, not labelled "job-processed"
#   For each matching email:
#     STEP 1: Extract sender, subject, body
#     STEP 2: Classify using CLAUDE.md section 7 keyword map
#     STEP 3: Pass classified email to agents/tracker.md
#     STEP 4: Label email as "job-processed" in Gmail (via MCP)
#
# TO BE WRITTEN IN STAGE 5
