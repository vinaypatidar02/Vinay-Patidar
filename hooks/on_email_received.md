# Hook: on_email_received
# Stage 5 — ACTIVE
#
# ============================================================
# LEARNING NOTE — Polling vs Push
# ============================================================
# True real-time email hooks need Gmail Pub/Sub push webhooks
# (a publicly-accessible server). For a local project, polling
# is simpler and a 2-hour delay is fine for job search emails.
# This hook uses Claude Code's scheduled execution or is run
# manually on demand.
# ============================================================

# ── TRIGGER ───────────────────────────────────────────────────
# Type: Scheduled polling — every 2 hours, or run manually.
#
# Three modes:
#   NORMAL (default) — processes last 48 hours of emails
#     claude "check email"
#
#   BACKFILL with custom age — you control how far back to go
#     claude "check email last 30 days"   ← any number you choose
#     claude "check email last 45 days"
#     claude "check email backfill"       ← defaults to 35 days
#
#   Why not "all email": You have 1000+ emails. Scanning all is
#   wasteful and costly. Since you started applying ~1 month ago,
#   35 days covers everything. Use a higher number if needed.
#
# ── INBOX ONLY — deleted emails are NOT read ──────────────────
# Gmail's search API only searches INBOX and sent mail by default.
# It does NOT search Trash or Spam unless you explicitly add
# "in:trash" or "in:spam" to the query.
# Our queries never include those — so deleted emails are safe.

# ── STEP 1 — DETERMINE MODE AND AGE ──────────────────────────
# Parse number from prompt if present:
#   "check email last 30 days"  → days = 30
#   "check email last 45 days"  → days = 45
#   "check email backfill"      → days = 35 (default backfill)
#   "check email"               → days = 2  (normal, 48h)
#
# Set time_filter = newer_than:{days}d
# Log: "[hook] MODE: normal|backfill  scanning last {days} days"

# ── STEP 2 — SEARCH GMAIL (INBOX ONLY) ──────────────────────
# Use Gmail MCP tool: search_messages
# Scope: inbox only — Trash and Spam are automatically excluded.
#
# Query (both modes — only time window differs):
#   newer_than:{days}d -label:job-processed
#   subject:(application OR interview OR offer OR assessment OR
#            "thank you for applying" OR "your application" OR
#            "next steps" OR "technical test" OR unfortunately)
#
# Additional match — also include emails where sender domain
# matches any company domain in job_tracker.json
# (catches emails without standard subject keywords).
#
# In backfill mode: remove -label:job-processed so already-labelled
# emails are re-read. The tracker is idempotent — it won't duplicate.
#
# For each matching email, fetch full content via get_message.
# Log: "[hook] Found X candidate emails to process"

# ── STEP 3 — CLASSIFY EMAIL ──────────────────────────────────
# For each email, use Claude API to classify it — NOT keyword matching.
# Keyword matching is brittle; Claude understands recruiter intent
# regardless of phrasing.
#
# Call the Anthropic API with this prompt for each email:
#   System: "You are classifying recruiter emails for a job tracker.
#            Given subject + body, return JSON with:
#            is_job_related (bool), status (one of: Applied / Under Review /
#            Interview Scheduled / Assessment / Offer Received / Rejected /
#            Not Relevant), tracking_url (string or null), notes (reason).
#            Focus on intent not exact words. If ambiguous, pick more advanced status."
#   User:   "Subject: <subject>\n\nBody:\n<body>"
#
# The full prompt lives in scripts/test_email_tracker.py (CLASSIFIER_PROMPT).
# The same prompt is used in both the test script and the live hook.
#
# If API call fails → fall back to _keyword_fallback() in test_email_tracker.py
# If is_job_related = false or status = "Not Relevant" → skip this email
#
# Build classified email object for agents/tracker.md:
# {
#   "sender_email":     "<sender>",
#   "sender_domain":    "<domain>",
#   "subject":          "<subject>",
#   "body":             "<body>",
#   "received_date":    "<YYYY-MM-DD>",
#   "extracted_status": "<status from Claude>",
#   "extracted_url":    "<tracking_url or null>",
#   "extracted_date":   "<interview/deadline if mentioned, else null>",
#   "confidence":       "high",   ← Claude classification is always high confidence
#   "classification_notes": "<Claude's reason>"
# }

# ── STEP 4 — INVOKE TRACKER AGENT ────────────────────────────
# For each classified email:
#   Pass classified email object to agents/tracker.md
#   The tracker agent handles:
#     - company + role fuzzy matching
#     - status update (never downgrades)
#     - appending to status_history[] and emails_received[]
#     - writing back to job_tracker.json
#     - running python3 scripts/sheets_sync.py push

# ── STEP 5 — LABEL PROCESSED EMAILS ─────────────────────────
# After tracker.md completes for each email:
#   Use Gmail MCP tool: add_label → "job-processed"
#   This prevents re-processing on the next NORMAL poll.
#   In BACKFILL mode, already-labelled emails are re-read but
#   the tracker agent skips updates that would not change status,
#   so labelling them again is harmless.
# Log: "[hook] Labelled [N] emails as job-processed"

# ── STEP 6 — SUMMARY ─────────────────────────────────────────
# Print:
#   ═══════════════════════════════════════════
#    Email Check — <datetime>  [MODE: normal|backfill]
#   ═══════════════════════════════════════════
#    Emails scanned:     X
#    Job-related:        Y
#    Matched + updated:  Z
#    Unmatched:          W  (check data/unmatched_emails.json)
#    Already up-to-date: V  (no status change needed)
#    Labelled processed: Y
#   ═══════════════════════════════════════════
#   Next: open Google Sheet to review updated statuses

# ── IMPLEMENTATION — macOS cron (after Stage 5 setup) ────────
# Add to crontab (crontab -e) for automatic polling every 2 hours:
#   0 */2 * * * cd ~/Projects/job-automation && source .venv/bin/activate && claude "check email" >> logs/email_hook.log 2>&1
#
# First run backfill — last 35 days only (run once manually):
#   cd ~/Projects/job-automation && source .venv/bin/activate && claude "check email backfill"
# Estimated cost: < $0.10 (Haiku 4.5, ~50-80 job emails × $0.001 each)
