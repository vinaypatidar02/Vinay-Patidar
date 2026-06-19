# Skill: score_job
# Stage 3 — TO BE BUILT
#
# LEARNING NOTE — What is a Skill file?
# ============================================================
# A skill is a self-contained prompt template that teaches Claude
# HOW to do one specific thing well. Skills are invoked by agents
# (not directly by users). They receive inputs, do one job, and
# return a structured output.
#
# Unlike CLAUDE.md which sets global context, a skill file is
# TASK-SPECIFIC. Think of skills as the specialist functions
# your agents call when they need expert help.
#
# Skill files typically contain:
#   - INPUT spec:   what data this skill expects
#   - INSTRUCTIONS: step-by-step what Claude should do
#   - OUTPUT spec:  exact format of the return value
#   - EXAMPLES:     sample input → output pairs
#   - CONSTRAINTS:  what this skill must never do
#
# This skill will:
#   INPUT:  A job description (text or URL content)
#   PROCESS: Score it against the candidate profile in CLAUDE.md
#            using the fit scoring rubric (section 4)
#   OUTPUT: JSON with fit_score, breakdown, recommendation, flags
#
# TO BE WRITTEN IN STAGE 3
