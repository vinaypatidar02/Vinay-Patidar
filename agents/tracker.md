# Agent: tracker
# Stage 4 — TO BE BUILT
#
# LEARNING NOTE — Agents that update state
# ============================================================
# The tracker agent introduces an important pattern: reading,
# merging, and writing back to a shared JSON file safely.
#
# The RULE in CLAUDE.md is: always READ first, then MERGE,
# then WRITE BACK. Never overwrite the whole file blindly.
# This prevents data loss when the file is updated between reads.
#
# This agent will:
#   STEP 1: Receive a classified email object (from on_email_received hook)
#           containing: sender, subject, body, date, extracted_status,
#           extracted_tracking_url (if any)
#   STEP 2: Read data/job_tracker.json
#   STEP 3: Fuzzy-match sender domain + company name keywords to find
#           the matching application entry
#   STEP 4: If match found:
#             - Update status field
#             - Append to status_history[]
#             - Append to emails_received[]
#             - Add tracking_url if extracted
#             - Write back to job_tracker.json
#   STEP 5: If no match found:
#             - Append to data/unmatched_emails.json
#             - Print warning to terminal
#   STEP 6: Confirm what was updated (or not) to terminal
#
# TO BE WRITTEN IN STAGE 4
