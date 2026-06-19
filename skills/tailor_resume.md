# Skill: tailor_resume
# Stage 3 — TO BE BUILT
#
# LEARNING NOTE — Skills vs Agents
# ============================================================
# This skill does ONE thing: rewrite the resume for a specific JD.
# It does NOT save the file, update the tracker, or call other skills.
# That's the agent's job (application_prep.md).
#
# This separation is intentional — it's the single responsibility
# principle applied to AI workflows. Each skill is testable
# in isolation, which makes debugging much easier.
#
# This skill will:
#   INPUT:  Job description text + master resume content
#   PROCESS: Identify JD keywords → reorder + rephrase bullets
#            to surface most relevant experience first.
#            NEVER fabricate. Only restructure real content.
#   OUTPUT: Complete rewritten resume as structured text,
#           ready to be rendered as PDF by the agent.
#
# Rules inherited from CLAUDE.md section 5 apply here.
#
# TO BE WRITTEN IN STAGE 3
