# CLAUDE.md — Job Automation Project
# UK Analytics Job Search — Vinay Patidar
#
# ============================================================
# LEARNING NOTE — What is CLAUDE.md?
# ============================================================
# CLAUDE.md is a special file that Claude Code reads automatically
# at the start of every session in this project folder.
# Think of it as the "system prompt" for your project.
#
# Key behaviours:
#   - Claude reads this BEFORE doing anything in this folder
#   - Every agent, skill, and hook in this project inherits
#     the context defined here
#   - You can have a root CLAUDE.md (this file) AND sub-folder
#     CLAUDE.md files — sub-folder ones extend, not replace, root
#   - Keep it factual and instructional — Claude acts on it literally
#
# Convention used in this file:
#   [CONTEXT]   = facts Claude should know
#   [RULE]      = hard constraint Claude must always follow
#   [DEFAULT]   = behaviour unless overridden per-task
#   [LEARNING]  = explanation for the developer (you)
# ============================================================


# ─────────────────────────────────────────────────────────────
# 1. PROJECT IDENTITY
# ─────────────────────────────────────────────────────────────

[CONTEXT] This project automates the UK job search for Vinay Patidar,
a Lead Analytics professional with 8+ years of experience.

[CONTEXT] The project is also a structured learning exercise covering:
Claude Code, CLAUDE.md, Skills, Agents, MCP Servers, and Hooks —
in that order across 5 stages.

[CONTEXT] Current stage: STAGE 2 — MCP Servers (Gmail + Apify)
Update this line as each stage is completed.

[CONTEXT] All state is stored locally. No Google Drive or Google Sheets
are used at this stage. The single source of truth is:
  data/job_tracker.json         ← application pipeline
  data/master_resume.pdf        ← base CV, never modified
  outputs/applications/         ← one folder per application


# ─────────────────────────────────────────────────────────────
# 2. CANDIDATE PROFILE
# ─────────────────────────────────────────────────────────────

[CONTEXT] Name: Vinay Patidar
[CONTEXT] Current location: Bengaluru, India
[CONTEXT] Target country: United Kingdom
[CONTEXT] Visa: Requires Skilled Worker Visa sponsorship.
          Only apply to roles explicitly stating visa sponsorship
          is available, or where the company is a known sponsor.

[CONTEXT] Total experience: 8+ years in Product, Growth, and Commercial Analytics

[CONTEXT] Career summary:
  - Lead Business Analyst @ Flipkart (Apr 2025 – Mar 2026)
    CRM analytics, incrementality testing, experimentation, grocery growth
    Key metric: 40% growth in Grocery visits, propensity models targeting
    70% of potential customers while reaching only 30% of user base

  - Analytics Manager @ BeepKart (Jul 2023 – Nov 2024)
    Dynamic Pricing Algorithm design, geo-clustering, procurement efficiency
    Key metric: 30%+ improvement in procurement efficiency, team of 5

  - Lead Business Analyst @ DeHaat (Jul 2021 – Jul 2023)
    Collections analytics, customer scoring, KPI frameworks
    Key metric: 30% reduction in overdue outstanding, team of 3

  - Senior Data Analyst @ Quinbay/Coviam (Oct 2020 – Jul 2021)
    Analytics architecture, A/B testing, search conversion tracking

  - Data Analyst @ Coviam Technology (May 2017 – Sep 2020)
    150+ Tableau dashboards, XGBoost delivery prediction (85% accuracy)

[CONTEXT] Core expertise areas (use these for JD matching):
  Product Analytics, Growth Analytics, Experimentation & Incrementality Testing,
  Pricing & Commercial Optimization, Customer Lifecycle Analytics,
  KPI Strategy & Business Intelligence, Analytics Transformation,
  Stakeholder Management, Strategic Decision-Making,
  CRM Analytics, Customer Segmentation, Propensity Modeling,
  Behavioral Analytics, Conversion Optimization, Retention Analytics

[CONTEXT] Technical stack:
  SQL, Python, Tableau, Looker Studio, BigQuery, Amazon Redshift,
  Google Analytics, Firebase, Apache Airflow, XGBoost

[CONTEXT] Agile & collaboration tools (real, in-use experience):
  Jira, Confluence, and Atlassian suite for sprint planning and analytics delivery.
  Git for version control. Agile/Scrum methodologies applied to analytics team workflows
  at Flipkart, BeepKart, and DeHaat.
  Use this when JDs mention: Agile, Scrum, Jira, sprint-based delivery, cross-functional
  collaboration tools, or team delivery frameworks.

[CONTEXT] AI fluency & automation (current, actively developing):
  Completed Claude 101 and Claude Code 101 (Anthropic Skilljar, 2026).
  Currently building an end-to-end AI-powered job application automation workflow
  using Claude Code, MCP servers, agents, skills, and hooks — demonstrating hands-on
  capability in LLM workflows, prompt engineering, and agentic automation.
  Use this when JDs mention: AI/ML fluency, LLM tools, automation, workflow engineering,
  prompt engineering, or modern data tooling beyond traditional BI.

[CONTEXT] Marketing measurement (learning + adjacent real experience):
  Currently in active self-study of Marketing Mix Modelling (MMM) and
  Multi-Touch Attribution (MTA) — Robyn (Meta's open-source MMM), Meridian (Google),
  Shapley-value MTA frameworks.
  Has applied heuristic attribution logic in practice at Flipkart (incrementality testing,
  CRM campaign measurement) and BeepKart (conversion attribution across seller/buyer journeys).
  Use this when JDs mention: MMM, MTA, attribution modelling, marketing effectiveness,
  media mix, campaign ROI measurement — frame as "strong adjacent foundation +
  active upskilling" rather than claiming direct MMM delivery experience.
  RULE: Never claim to have delivered full MMM/MTA models. Frame accurately as:
  practical incrementality/attribution experience + active study of MMM/MTA frameworks.

[CONTEXT] Team leadership — use explicitly for Manager-level roles:
  - Flipkart: Managed and mentored a team of analysts on CRM, experimentation,
    and grocery growth analytics. Drove hiring, workload allocation, and capability building.
  - BeepKart: Built and led a team of 5 analysts. Introduced structured analytics
    delivery using Agile ceremonies, Jira-based sprint tracking, and Confluence documentation.
  - DeHaat: Led a team of 3 analysts. Mentored on SQL, modelling, and stakeholder
    communication. Elevated team output quality and delivery consistency.
  Use this when JDs mention: people management, team building, mentoring, analyst
  leadership, hiring, capability development, or managing junior/mid-level team members.

[CONTEXT] Resume variants available (all in data/):
  master_resume.pdf         ← General/default, balanced across all domains
  product_resume.pdf        ← Emphasises product analytics, experimentation, A/B testing,
                               customer journey, conversion optimisation
  customer_resume.pdf       ← Emphasises CRM, lifecycle, retention, segmentation,
                               propensity modelling, customer growth strategy
  USE SELECTION RULE: skill tailor_resume.md will choose the best base variant
  based on JD domain before further tailoring. See Section 5 for selection logic.

[CONTEXT] Education: B.Tech Mining Engineering, IIT (BHU) Varanasi, 2016 (GPA 7.67/10)

[CONTEXT] Certifications:
  Data Science using SAS and R (Analytix Labs),
  Managing Big Data with MySQL (Coursera),
  Data Visualization with Tableau (Coursera),
  Mastering Data Analysis in Excel (Coursera),
  Claude 101 — Anthropic Skilljar (2026),
  Claude Code 101 — Anthropic Skilljar (2026)


# ─────────────────────────────────────────────────────────────
# 3. JOB SEARCH PREFERENCES
# ─────────────────────────────────────────────────────────────

[CONTEXT] Target roles (match any of these titles or close equivalents):
  - Analytics Lead
  - Lead Business Analyst
  - Lead Product Analyst
  - Lead Data Analyst
  - Analytics Manager
  - Product Analytics Manager
  - Data Analytics Manager
  - Senior Analytics Manager
  - Senior Data Analyst (only if Lead/Manager-level scope is evident in JD)
  - Head of Analytics (if scope matches 8-year experience level)
  - Growth Analytics Lead / Manager
  - Principal Data Analyst / Principal Analytics Manager
  - Insights Lead / Insights Manager (if analytics-heavy, not pure reporting)

[RULE] Salary threshold: £85,000 per annum (lower bound of acceptable range).
       - Salary range stated, upper end > £85k (e.g. £75k–£95k) → SHORTLIST.
       - Salary range stated, both ends below £85k → DO NOT shortlist.
       - Single salary figure below £85k → DO NOT shortlist.
       - No salary stated → do not disqualify, flag as "Salary TBC".

[CONTEXT] Preferred UK locations — ranked by combined population size and
  working-age (16–64) share per ONS mid-2024 estimates:

  TIER 1 — Primary (large city, strong analytics market)
    1. London          — 8.8M, dominant tech/fintech/analytics hub
    2. Manchester      — ~600K, lowest median age in UK (30.4), 70.8% working-age
    3. Birmingham      — 1.1M, large talent pool, growing tech sector

  TIER 2 — Strong secondaries (high working-age share, London-accessible, fast-growing)
    4. Leeds           — ~800K, major financial and digital cluster
    5. Reading         — ~220K, 72%+ working-age, largest non-city in England,
                         strong Thames Valley corporate hub, ~25 min to London
    6. Milton Keynes   — ~300K, fastest-growing UK city (14.9% over decade),
                         high working-age, ~35 min to London
    7. Cambridge       — ~150K, 73.7% working-age (highest in UK), 17.3% growth,
                         leading tech/biotech cluster, ~50 min to London
    8. Oxford          — ~160K, 72.4% working-age, major knowledge economy,
                         ~60 min to London
    9. Leicester       — ~370K, diverse economy, growing analytics sector
   10. Coventry        — ~370K, strong digital economy, 20 min to Birmingham
   11. Nottingham      — ~330K, median age 31.3, solid working-age share
   12. Northampton     — ~220K, 7th fastest-growing UK city, ~65 min to London

  TIER 3 — Consider only if role score ≥ 85 AND explicitly remote/hybrid
    - Bristol, Brighton & Hove, Luton, Watford, Slough, Guildford

[RULE] Do not shortlist roles in Scotland, Wales, Northern Ireland, or any
       location not in Tier 1–3 above. Tier 3 requires fit score ≥ 85 AND
       role explicitly states ≤ 2 days/week in office.

[CONTEXT] Industry preference:
  STRONGLY PREFERRED: Product-led companies (tech, fintech, ecommerce,
  marketplace, SaaS, consumer apps)

  ACCEPTABLE: Non-product companies (consulting, services, agencies)
  only if the role is an exceptional match (fit score ≥ 88)
  AND the company is well-known (FTSE 250 or equivalent).

  AVOID: Pure staffing agencies, outsourcing firms, body-shopping roles.

[RULE] Visa sponsorship is non-negotiable. Always check whether the
       company holds a UK Skilled Worker sponsor licence or states
       visa sponsorship in the JD. If unknown, flag as "Sponsorship Unconfirmed"
       rather than rejecting.

[DEFAULT] When in doubt on fit, flag for human review rather than auto-reject.


# ─────────────────────────────────────────────────────────────
# 4. FIT SCORING RUBRIC
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] This section teaches agents HOW to score a job.
# Rather than leaving scoring logic inside each agent prompt,
# we centralise it here so all agents share the same definition
# of "good fit". This is a key CLAUDE.md pattern.
# ─────────────────────────────────────────────────────────────

[CONTEXT] Fit scoring is on a 0–100 scale. Breakdown:

  ROLE TITLE MATCH           (0–20 points)
    20 = exact or near-exact match to target roles
    10 = adjacent role (e.g. Data Lead, Insights Manager)
     0 = unrelated title

  DOMAIN MATCH               (0–25 points)
    25 = product/growth/ecommerce/marketplace/fintech
    15 = other tech or data-heavy industry
     5 = services/consulting
     0 = unrelated domain

  SKILLS MATCH               (0–25 points)
    Score based on overlap with: SQL, Python, Tableau, BigQuery,
    Redshift, Looker, experimentation, pricing, CRM analytics.
    25 = 7+ skills match
    15 = 4–6 skills match
     5 = 1–3 skills match

  SENIORITY MATCH            (0–15 points)
    15 = Lead / Manager level, 5–10 years experience expected
    10 = slightly senior (Director-adjacent) but reachable
     5 = slightly junior but interesting
     0 = clear mismatch (junior IC or VP+)

  LOCATION                   (0–10 points)
    10 = London
     8 = Manchester / Birmingham
     6 = Nottingham / satellite city
     0 = outside acceptable range

  VISA SPONSORSHIP           (0–5 points)
    5  = explicitly confirmed
    3  = company is a known sponsor (check common knowledge)
    0  = no mention (flag, do not reject)
   -10 = explicitly states "no sponsorship" → auto-reject

[RULE] Auto-shortlist if score ≥ 75 AND visa is not rejected.
[RULE] Flag for human review if score 60–74.
[RULE] Auto-reject if score < 60 OR visa sponsorship explicitly denied.


# ─────────────────────────────────────────────────────────────
# 5. RESUME & COVER LETTER RULES
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] These rules constrain the tailor_resume and
# draft_cover_letter skills. Centralising them here means
# you can update tone/style in ONE place and all skills
# automatically inherit the change.
# ─────────────────────────────────────────────────────────────

[RULE] Never fabricate experience, metrics, or skills.
       Only restructure, reorder, and rephrase what exists
       in data/master_resume.pdf, data/product_resume.pdf,
       or data/customer_resume.pdf.

[RULE] Do not change any numbers or metrics in the resume
       (e.g. 40%, 30%, 85%, 70/30 split). These are real.

[DEFAULT] Resume base variant selection (applied by tailor_resume skill):
  IF JD is product/growth/ecommerce/marketplace/SaaS/engineering-adjacent
    → start from data/product_resume.pdf
  IF JD is CRM/retention/lifecycle/customer success/marketing analytics
    → start from data/customer_resume.pdf
  IF JD is commercial/pricing/operations/general analytics
    → start from data/master_resume.pdf
  When ambiguous, prefer product_resume.pdf as the default variant.

[DEFAULT] Resume format — generated by scripts/pdf_renderer.py (reportlab):
  Layout:    True two-column: teal sidebar (32% width) + white content area (68%)
  Left col:  Name (22.86pt) → Profession → Contact → Core Expertise → Skills → Certs
             Section headers: slightly-darker-teal bars (#006996), white label text
  Right col: Summary → Work History → Education
             Section headers: teal 13.24pt Regular
             Role titles: Helvetica-Bold, lighter dark (#525252)
             Company names: Helvetica-Oblique, 9.02pt
             Tenure: right-aligned, light grey, "Apr 2025 – Mar 2026" format
             Bullet dots: small filled circles, 1.1pt radius
  Fonts:     Helvetica throughout (Regular/Bold/Oblique as specified per element)
  Colours:   Sidebar #0074A6, section bars #006996, body #363C49, tenure #8C8C8C
  Page size: A4, zero outer margin (sidebar bleeds to edge)
  File naming: [Company]_[RoleTitle]_[YYYYMMDD].pdf
  Certs order: Claude/Anthropic certs first, then rest in original order

[DEFAULT] Resume length: Maximum 2 pages.

[DEFAULT] Bullet point style: Action verb + context + metric.
          Example: "Led experimentation programme across 3 product
          verticals, improving conversion by 18%."

[DEFAULT] Cover letter format — match the eBay sample cover letter exactly:
  Header:    Same two-column layout as resume (name + title left, contact right)
  Opening:   City + date (e.g. "London, 2026-06-17")
             Then: "[Company] Hiring Team"
  Salutation: "Dear Hiring Team,"
  Structure: 4 paragraphs (based on eBay sample — not 3):
    Para 1: Role excitement + why this company specifically + alignment summary
    Para 2: Most relevant experience mapped to JD (specific, with metrics)
    Para 3: Broader strategic value — additional experiences that reinforce fit
    Para 4: Forward-looking — what excites you about this company's mission
             + call to action
  Closing:   "Kind regards," + Name + Phone + Email
  Tone:      Confident, specific, warm — not generic, not stiff
  Length:    350–450 words (eBay sample was ~420 — this is the right length)

[RULE] Cover letter must name the company and role title in paragraph 1.
       No generic openers like "I am writing to apply for..."
       Opening must express genuine, specific enthusiasm for THIS company.

[RULE] Cover letter output format: PDF only.
       File naming: [Company]_CoverLetter_[YYYYMMDD].pdf
       Use the same reportlab styling as the resume for visual consistency.
       Both files saved to the application's output folder.


# ─────────────────────────────────────────────────────────────
# 6. APPLICATION TRACKING
# ─────────────────────────────────────────────────────────────

[CONTEXT] Tracker file: data/job_tracker.json
          This is the single source of truth for all applications.

[CONTEXT] Valid status values and what triggers each:
  "Shortlisted"          → Job scored ≥ 75, awaiting human approval
  "Approved"             → Human approved, ready for application prep
  "Prep Complete"        → Resume + cover letter generated and saved
  "Applied"              → Application submitted, confirmation received
  "Under Review"         → Recruiter/ATS confirmed active review
  "Interview Scheduled"  → Interview invite received
  "Assessment"           → Take-home task or online test received
  "Offer Received"       → Offer email received
  "Rejected"             → Rejection email received
  "Withdrawn"            → Candidate chose to withdraw

[RULE] DUPLICATE PREVENTION — Critical. Before adding any job to job_tracker.json
       or triggering application prep, check ALL of these signals:
         1. jd_url exact match
         2. career_page_url exact match
         3. Fuzzy match: same company name + same role title (within edit distance 2)
       If ANY match is found regardless of current status, DO NOT re-add or re-apply.
       Log a warning: "DUPLICATE SKIPPED: [Company] [Role] already exists as [status]"

[CONTEXT] job_tracker.json is pre-seeded with 52 historical applications imported
       from Vinay_Job_Tracker.xlsx on 2026-06-18 (source="excel_import").
       33 are Rejected, 19 are Applied (still in progress). Duplicate check covers all.

[CONTEXT] Notable multi-application companies: Wise (6 roles — all Rejected), 
       Harnham (3 roles — all Rejected), Hastings Direct (2 roles — both Rejected).
       A new role at these companies is NOT a duplicate if the role title is distinct.

[CONTEXT] The 19 active "Applied" entries from Excel have no jd_url. When Gmail
       receives emails from those companies, the tracker agent should match by
       company name fuzzy match and update their status accordingly.

[RULE] Never delete an entry from job_tracker.json.
       Only update status and append to status_history[].

[CONTEXT] Output folder convention:
  outputs/applications/[Company]_[RoleShortName]_[YYYYMMDD]/
    ├── [Company]_[RoleTitle]_[YYYYMMDD].pdf      ← tailored resume
    ├── [Company]_CoverLetter_[YYYYMMDD].pdf      ← cover letter (PDF, not .md)
    └── meta.json          ← JD URL, career page URL, tracking URL, notes


# ─────────────────────────────────────────────────────────────
# 7. EMAIL STATUS MAPPING
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] This section is read by the on_email_received hook
# and the tracker agent. Defining the mapping here (not inside
# the hook) means you can add new patterns without touching
# agent code — just update CLAUDE.md.
# ─────────────────────────────────────────────────────────────

[CONTEXT] When the Gmail hook fires, classify the email using
          these subject/body keyword patterns → status mapping:

  KEYWORDS                              → STATUS UPDATE
  ─────────────────────────────────────────────────────
  "application received" /
  "we've received your application" /
  "thank you for applying"              → "Applied"
                                          + extract tracking URL if present

  "under review" /
  "being considered" /
  "shortlisted" /
  "progressing your application"        → "Under Review"

  "invite you to interview" /
  "schedule an interview" /
  "interview invitation" /
  "speak with you"                      → "Interview Scheduled"
                                          + extract date/time if present

  "online assessment" /
  "take-home task" /
  "technical test" /
  "complete the following"              → "Assessment"
                                          + extract deadline if present

  "pleased to offer" /
  "offer of employment" /
  "formal offer"                        → "Offer Received"

  "unfortunately" /
  "not successful" /
  "not moving forward" /
  "we won't be progressing"            → "Rejected"

[RULE] Match application to email using BOTH signals together:
       1. Company: fuzzy-match sender domain or company name in email body
          against company field in job_tracker.json.
       2. Role: fuzzy-match role title keywords in email subject/body
          against role field in job_tracker.json.
       A match requires BOTH signals to align. If company matches multiple
       entries, use role keywords to disambiguate (e.g. Wise has 6 entries).
       Fall back to company-only match only if the email contains no role
       title signal at all — and flag it as "low-confidence match" in the log.

[RULE] If no match found, log the email to data/unmatched_emails.json
       for manual review. Never silently discard an email.

[RULE] Always append to status_history[], never overwrite it.


# ─────────────────────────────────────────────────────────────
# 8. PROJECT FILE MAP
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] This section tells Claude what each file does so
# it can navigate the project confidently without you explaining
# it each session. This is especially important for agents that
# run across multiple steps.
# ─────────────────────────────────────────────────────────────

[CONTEXT] Project structure and file purposes:

  CLAUDE.md                        ← YOU ARE HERE. Read first, always.

  mcp.json                         ← MCP server configs (Stage 2)
                                      Defines Gmail and Apify connections

  skills/score_job.md              ← Skill: score a JD against profile
  skills/tailor_resume.md          ← Skill: select variant + rewrite resume for JD
  skills/draft_cover_letter.md     ← Skill: write targeted cover letter as PDF

  agents/job_scout.md              ← Agent: scrape → deduplicate → score → shortlist
  agents/application_prep.md       ← Agent: tailor resume + cover letter (both PDFs)
  agents/tracker.md                ← Agent: update job_tracker.json from emails

  hooks/on_job_approved.md         ← Hook: triggers application_prep
  hooks/on_email_received.md       ← Hook: triggers tracker status update

  data/master_resume.pdf           ← General/commercial resume — never modify
  data/product_resume.pdf          ← Product/growth/experimentation variant
  data/customer_resume.pdf         ← CRM/lifecycle/retention variant
  data/job_tracker.json            ← Application pipeline state
  data/unmatched_emails.json       ← Emails that couldn't be matched

  scripts/pdf_renderer.py          ← Renders resume + cover letter as styled PDFs
                                      Matches Vinay's exact uploaded format (reportlab)
                                      Called by tailor_resume and draft_cover_letter skills
                                      Run standalone: python3 scripts/pdf_renderer.py test

  outputs/applications/            ← One subfolder per application
                                      Each contains: resume PDF + cover letter PDF + meta.json


# ─────────────────────────────────────────────────────────────
# 9. STAGE COMPLETION LOG
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] Track your own progress here. This also helps Claude
# know what's been built vs what's still pending when you start
# a new session mid-project.
# ─────────────────────────────────────────────────────────────

[CONTEXT] Stage completion status:
  ✅ Stage 1 — CLAUDE.md & project scaffold       COMPLETE
  ✅ Stage 2 — MCP Servers (Gmail + Apify)        COMPLETE
  ⏳ Stage 3 — Skills (score, tailor, cover)      PENDING
  ⏳ Stage 4 — Agents (scout, prep, tracker)      PENDING
  ⏳ Stage 5 — Hooks & orchestration              PENDING


# ─────────────────────────────────────────────────────────────
# 10. GLOBAL BEHAVIOURAL RULES
# ─────────────────────────────────────────────────────────────

[RULE] Always read CLAUDE.md before starting any task in this project.

[RULE] Always read the relevant skill file before executing a skill.

[RULE] Never modify data/master_resume.pdf.

[RULE] Never modify a completed application folder's resume.pdf.
       If a re-tailoring is needed, create a new dated folder.

[RULE] When writing to job_tracker.json, read the current file first,
       merge the update, then write back. Never overwrite blindly.

[RULE] Log all actions taken to the terminal so the developer can
       follow what the agent is doing and why. This is a learning
       project — transparency is more important than brevity.

[RULE] If uncertain about a decision (e.g. borderline fit score,
       ambiguous visa status), pause and ask for human input
       rather than making an assumption silently.

# ─────────────────────────────────────────────────────────────
# 11. MCP SERVER CONFIGURATION (Stage 2)
# ─────────────────────────────────────────────────────────────
#
# [LEARNING] MCP (Model Context Protocol) servers give Claude
# "hands" to reach external systems. Each server exposes a set
# of tools Claude can call like functions. The server handles
# auth, rate limits, and data formatting — Claude just calls
# the tool with parameters and gets structured data back.
#
# Two servers are configured in mcp.json:
#
# 1. APIFY — LinkedIn job scraper
#    Tool: run_actor(actor_id, input)
#    Actor: nexgendata/linkedin-jobs-scraper
#    What it does: scrapes LinkedIn job search results without
#    login, returns structured JSON (job_title, company_name,
#    location, salary, job_type, posted_date, description, job_url)
#    NOTE: does NOT return apply/career page URL natively —
#    career_page_url must be filled in manually after job approval
#    Config: needs APIFY_TOKEN in .env
#    Test: python3 scripts/test_apify_scrape.py
#
# 2. GMAIL — Email reading and labelling
#    Tools: search_messages, get_message, add_label
#    What it does: reads job-related emails, extracts status
#    signals, labels processed emails to avoid double-processing
#    Config: needs Gmail OAuth (run scripts/gmail_auth.js once)
#    Connected: already active in Claude.ai — local auth
#    needed only for Claude Code sessions
#
# [CONTEXT] mcp.json uses ${ENV_VAR} substitution for secrets.
#   Never hardcode tokens in mcp.json — always reference .env.
#   The .env file is gitignored and never committed.
#
# [CONTEXT] Apify actor selection rationale:
#   nexgendata/linkedin-jobs-scraper was chosen because:
#   - No LinkedIn login required (uses public guest API)
#   - Pay-per-use, no monthly rental fee ($0.003/job extracted)
#   - Returns structured JSON with description text for enrichment
#   - fetchDescriptions flag enables full JD text for scoring
#   - Maintained by NexGenData (140+ actors, active support)
#
# [RULE] When calling the Apify LinkedIn actor, always pass:
#   maxJobs: max 25 per call      (avoid hitting rate limits)
#   fetchDescriptions: true       (needed by score_job + enrich_jobs)
#   location: full name           (e.g. "London, United Kingdom")
#   jobType: "full-time"          (filter out contract/part-time)