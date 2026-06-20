# Skill: draft_cover_letter
# Stage 3 — ACTIVE
#
# ============================================================
# LEARNING NOTE — Skills that call other skills
# ============================================================
# This skill consumes the OUTPUT of tailor_resume.md (the
# tailored resume JSON) plus the JD text. It does NOT re-read
# the base resume PDFs — it works from what tailor_resume
# already selected and prioritised. This avoids duplication
# of work and keeps the cover letter consistent with the resume.
# ============================================================

# ── INPUT ────────────────────────────────────────────────────
# {
#   "job": <score_job.md output object>,
#   "jd_text": "<full job description text>",
#   "tailored_resume": <tailor_resume.md output JSON>,
#   "today": "<YYYY-MM-DD>"
# }

# ── INSTRUCTIONS ─────────────────────────────────────────────
# Write a 4-paragraph cover letter (350–450 words) following the
# eBay sample format from CLAUDE.md Section 5.
#
# PARAGRAPH 1 — Role excitement + company alignment + summary (80–100 words)
#   - Open with genuine, specific enthusiasm for THIS company
#   - Name the company and exact role title in sentence 1
#   - Reference something specific about the company (product, culture,
#     mission, recent news if known — do not fabricate)
#   - State the breadth of experience in 1 sentence
#   - End with the alignment between your background and the role focus
#   FORBIDDEN: "I am writing to apply", "I am excited to apply for this role",
#              any generic opener not naming the specific company
#
# PARAGRAPH 2 — Most relevant experience mapped to JD (120–150 words)
#   - Pick the 2–3 most relevant bullets from tailored_resume.work_history
#   - Map them directly to requirements stated in the JD
#   - Always include at least one specific metric
#   - Mention the company context (Flipkart, BeepKart, etc.)
#   - If JD emphasises experimentation → lead with Flipkart incrementality testing
#   - If JD emphasises CRM/lifecycle → lead with propensity models (70/30)
#   - If JD emphasises pricing/commercial → lead with BeepKart DPA
#   - If JD emphasises team leadership → mention team sizes explicitly
#
# PARAGRAPH 3 — Broader strategic value (80–100 words)
#   - Surface 1–2 experiences from OTHER roles not covered in Para 2
#   - Include any of the following if JD mentions them:
#       Agile/Jira → "structured Agile delivery using Jira and Confluence"
#       AI/LLM → "building agentic workflow automation via Anthropic Claude Code"
#       MMM/attribution → "strong incrementality foundation + active MMM/MTA study"
#       Stakeholder mgmt → cross-functional work with Product/Engineering/Leadership
#   - Frame as additive value on top of Para 2, not repetition
#
# PARAGRAPH 4 — Forward-looking + call to action (60–80 words)
#   - What specifically excites you about THIS company's mission or product
#   - 1 concrete thing you would want to work on or improve
#   - Professional closing + invitation to discuss
#   - Do not be generic — reference something real about the company
#
# CLOSING FORMAT:
#   "Kind regards,"
#   [blank line]
#   "Vinay Patidar"
#   "+91 8871717951"
#   "vinay_patidar02@yahoo.com"

# ── OUTPUT ───────────────────────────────────────────────────
# Return a JSON object ready to pass to scripts/pdf_renderer.py:
# {
#   "name": "Vinay Patidar",
#   "title_lines": <same as tailored_resume.title_lines>,
#   "contact": <same as tailored_resume.contact>,
#   "core_expertise": [],   ← empty for cover letter sidebar
#   "skills": [],           ← empty for cover letter sidebar
#   "date": "London, <today YYYY-MM-DD>",
#   "recipient": "<Company Name> Hiring Team",
#   "salutation": "Dear Hiring Team,",
#   "paragraphs": [
#     "<paragraph 1 text>",
#     "<paragraph 2 text>",
#     "<paragraph 3 text>",
#     "<paragraph 4 text>"
#   ],
#   "closing": "Kind regards,"
# }

# ── CONSTRAINTS ───────────────────────────────────────────────
# NEVER open with a generic sentence. Company name must appear in sentence 1.
# NEVER fabricate company facts — only reference what is verifiably known.
# NEVER claim direct MMM/MTA delivery experience.
# NEVER exceed 450 words across 4 paragraphs.
# NEVER use the same opening verb/phrase as another cover letter — vary them.
# Use UK English spelling throughout (organisation, optimisation, behaviour).
