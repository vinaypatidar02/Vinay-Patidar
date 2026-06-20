# Skill: tailor_resume
# Stage 3 — ACTIVE
#
# ============================================================
# LEARNING NOTE — Single Responsibility
# ============================================================
# This skill does ONE thing: produce tailored resume content.
# It does NOT render the PDF, save the file, or update the
# tracker. The application_prep agent handles those steps.
# This separation makes the skill independently testable.
# ============================================================

# ── INPUT ────────────────────────────────────────────────────
# {
#   "job": <score_job.md output object>,
#   "jd_text": "<full job description text>",
#   "variant": "product" | "customer" | "master"  (pre-selected by agent)
# }

# ── STEP 1 — VARIANT SELECTION (if not pre-selected) ─────────
# Read the JD domain and apply this logic from CLAUDE.md Section 5:
#   product/growth/ecommerce/marketplace/SaaS → data/product_resume.pdf
#   CRM/retention/lifecycle/customer/marketing → data/customer_resume.pdf
#   commercial/pricing/operations/general     → data/master_resume.pdf
#   Ambiguous                                 → default to product_resume.pdf
# The selected variant is the BASE. Further tailoring happens on top.

# ── STEP 2 — EXTRACT JD KEYWORDS ─────────────────────────────
# From the JD text, identify:
#   a. Technical skills explicitly mentioned (SQL, Python, Tableau etc.)
#   b. Domain keywords (experimentation, CRM, pricing, segmentation etc.)
#   c. Seniority signals (lead, manager, head of, cross-functional etc.)
#   d. Industry context (fintech, ecommerce, marketplace, SaaS etc.)
#   e. Specific tools or platforms named
# These keywords will be used to prioritise and rephrase bullet points.

# ── STEP 3 — TAILOR BULLET POINTS ────────────────────────────
# For each role in the base resume:
#   - Move bullets that match JD keywords to the TOP of that role
#   - Rephrase bullets to echo JD language where natural
#     (e.g. "customer propensity models" → if JD says "propensity modelling")
#   - Preserve ALL original metrics exactly (40%, 30%, 85%, 70/30)
#   - Do NOT fabricate any experience, metric, or skill
#   - Do NOT remove bullets — only reorder and rephrase
#
# SPECIAL FRAMING RULES (from CLAUDE.md Section 2):
#
#   AI fluency — if JD mentions AI, LLM, automation, ML tools:
#     Surface: "Currently building end-to-end AI workflow automation
#     using Claude Code, MCP servers, agents and hooks"
#     Surface: Claude 101 and Claude Code 101 certifications (list first)
#
#   Agile / Jira — if JD mentions Agile, Scrum, sprint, delivery:
#     Surface Jira, Confluence, Agile ceremonies from BeepKart experience
#
#   MMM / MTA / attribution — if JD mentions these:
#     NEVER claim direct MMM/MTA delivery. Never fabricate.
#     Frame as: "strong incrementality testing foundation (Flipkart) +
#     active study of MMM/MTA frameworks (Robyn, Meridian, Shapley)"
#     NEVER claim direct MMM/MTA delivery
#
#   Team leadership — if JD mentions managing/mentoring/people mgmt:
#     Lead with team sizes: "team of 5 (BeepKart)", "team of 3 (DeHaat)"
#     Mention Agile delivery structure and capability building

# ── STEP 4 — SUMMARY LINE ────────────────────────────────────
# Rewrite the resume summary (top paragraph) to:
#   - Open with the exact job title or very close paraphrase
#   - Reference 1-2 domain keywords from the JD
#   - Keep to 3-4 sentences max
#   - Do not change seniority level or fabricate experience
# Example: if JD is "CRM Analytics Manager":
#   "Customer analytics leader with 8+ years driving CRM strategy,
#    lifecycle experimentation, and retention analytics across ecommerce
#    and technology businesses..."

# ── STEP 5 — PROFESSION LINE ─────────────────────────────────
# Update the sidebar profession line (displayed under name) to
# reflect the target role. Keep to 2 lines max.
# Example: "Lead CRM & Customer Analytics" / "Manager | Retention & Growth"

# ── OUTPUT ───────────────────────────────────────────────────
# Return a JSON object ready to pass to scripts/pdf_renderer.py:
# {
#   "name": "Vinay Patidar",
#   "title_lines": ["<Line 1>", "<Line 2>"],
#   "contact": {
#     "email": "vinay_patidar02@yahoo.com",
#     "phone": "+91 8871717951",
#     "address": "Bengaluru, Karnataka 560035",
#     "linkedin": "linkedin.com/in/vinay-patidar-vp02"
#   },
#   "core_expertise": [<list of 8-10 expertise areas, JD-prioritised>],
#   "skills": ["SQL", "Tableau", "Python", "Looker Studio", "BigQuery", "Amazon Redshift"],
#   "summary": "<tailored summary paragraph>",
#   "work_history": [
#     {
#       "company": "<name>",
#       "location": "Bengaluru",
#       "role": "<role title>",
#       "dates": "<YYYY-MM-YYYY-MM>",   ← pdf_renderer converts to "Apr 2025 – Mar 2026"
#       "bullets": ["<bullet 1>", ...]  ← JD-relevant bullets first
#     }, ...
#   ],
#   "education": [{
#     "degree": "Mining Engineering, B.Tech",
#     "institution": "IIT (BHU), Varanasi",
#     "dates": "2012 – 2016",
#     "gpa": "7.67/10"
#   }],
#   "certifications": [
#     "Claude 101 — Anthropic Skilljar (2026)",
#     "Claude Code 101 — Anthropic Skilljar (2026)",
#     "Data Science using SAS and R — Analytix Labs",
#     "Managing Big Data with MySQL — Coursera",
#     "Data Visualization with Tableau — Coursera",
#     "Mastering Data Analysis in Excel — Coursera"
#   ]
# }
# NOTE: Claude certs ALWAYS listed first per CLAUDE.md Section 5.

# ── CONSTRAINTS ───────────────────────────────────────────────
# NEVER change any metric (40%, 30%, 85%, 70/30).
# NEVER add a skill or tool not in the candidate profile.
# NEVER remove a role from work history — only reorder bullets within roles.
# NEVER claim direct MMM/MTA delivery experience.
# Keep resume to 2 pages maximum when rendered — trim lower-priority
# bullets from older roles (Coviam 2017-2020) if content overflows.
