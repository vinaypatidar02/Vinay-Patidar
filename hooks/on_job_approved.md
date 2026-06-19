# Hook: on_job_approved
# Stage 5 — TO BE BUILT
#
# LEARNING NOTE — What is a Hook in Claude Code?
# ============================================================
# A hook is an event-driven trigger that runs automatically
# when a specific condition is met — without you having to
# invoke an agent manually.
#
# In Claude Code, hooks are implemented using the hooks config
# in your claude_code settings. They watch for specific events:
#   - File changes (PostToolUse on Write/Edit tools)
#   - Command completions
#   - Session starts (UserPromptSubmit)
#   - Pre-tool validation (PreToolUse)
#
# HOOK TYPES YOU'LL LEARN IN STAGE 5:
#   PostToolUse  — fires after Claude uses a tool (e.g. after writing a file)
#   PreToolUse   — fires before Claude uses a tool (can block or modify)
#   UserPromptSubmit — fires when user submits a message
#   Notification — fires when Claude needs your attention
#
# THIS HOOK:
#   Trigger: PostToolUse on job_tracker.json write
#   Condition: Any entry changed to status = "Approved"
#              AND resume_path is still null
#   Action: Automatically invoke agents/application_prep.md
#
# Implementation: Will be added to .claude/settings.json hooks config
#
# TO BE WRITTEN IN STAGE 5
