"""
pdf_renderer.py  —  Resume & Cover Letter PDF Generator  v6
===========================================================
All values extracted directly from master_resume.pdf via pdfplumber.

KEY CORRECTIONS IN v6:
  - Sidebar section bars: very slightly darker teal #006996
    (black 10% opacity over #0074A6) — barely perceptible darkening
  - Tenure dates: lighter grey #8C8C8C — visually recedes behind role title
  - Role/company/bullets: no indent gap — start at left edge of right col
    (tenure is now right-aligned so the old date-column space is freed)

EXACT VALUES:
  Sidebar bg:        #0074A6  (0.0, 0.4588, 0.6549)
  Sidebar sec bars:  #006996  (0.0, 0.413,  0.589)  — very slightly darker teal
  All sidebar text:  #FFFFFF  white
  Right-col headers: #0074A6  teal, 13.24pt Regular
  Body text:         #363C49  (0.2118, 0.2392, 0.2863) warm dark slate
  Tenure text:       #8C8C8C  (0.55, 0.55, 0.55)  lighter grey
  Dividers:          #DEDEDE  0.6pt
  Company names:     italic 9.02pt
  Role titles:       regular 10.23pt
  Bullets:           regular 7.82pt
"""

import sys, json, textwrap
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# ── Colours ────────────────────────────────────────────────────────────────────
TEAL        = colors.Color(0.0,    0.4588, 0.6549)  # #0074A6 sidebar bg
TEAL_DARK   = colors.Color(0.0,    0.413,  0.589 )  # #006996 section bars — black 10% opacity over teal (very slightly darker)
BLACK       = colors.Color(0.0,    0.0,    0.0   )
WHITE       = colors.Color(1.0,    1.0,    1.0   )
DIVIDER     = colors.Color(0.8745, 0.8745, 0.8745)  # #DEDEDE
DARK        = colors.Color(0.2118, 0.2392, 0.2863)  # #363C49 all body text
TENURE_GREY = colors.Color(0.55,   0.55,   0.55  )  # lighter grey for tenure dates
ROLE_BOLD   = colors.Color(0.32,   0.32,   0.32  )  # #525252 bold role/degree — lighter than DARK, not too light

# ── Page geometry ──────────────────────────────────────────────────────────────
PW, PH   = A4                   # 595.28 × 841.89 pts
SB_W     = 190.73               # sidebar width
RX       = SB_W
RW       = PW - SB_W
SPAD     = 14.0                 # sidebar left padding
RPAD     = 14.0                 # right-col left padding from RX
RRIGHT   = PW - 14.0            # right-col right edge
RTW      = RRIGHT - (RX+RPAD)  # right-col text width

# Date-col and role-col x positions
# With tenure now right-aligned, role/company/bullets start at the left
# edge of the right column — no indentation gap needed.
DATE_X   = RX + RPAD            # 204.9 — left edge of right col
ROLE_X   = RX + RPAD            # same as DATE_X — no indent gap
ROLE_TW  = RRIGHT - ROLE_X      # full text width

# ── Font sizes (pts, from PDF) ─────────────────────────────────────────────────
FS_NAME   = 22.86   # sidebar name
FS_PROF   = 10.23   # sidebar profession lines
FS_SHEAD  = 13.24   # sidebar section header labels
FS_SLBL   = 10.23   # sidebar field labels (Email, Phone…)
FS_SVAL   =  9.02   # sidebar field values
FS_SITEM  =  7.82   # sidebar list items
FS_RCHEAD = 13.24   # right-col section headers (teal)
FS_ROLE   = 10.23   # job role title
FS_CODATE =  9.02   # company name + date
FS_BULLET =  7.82   # bullet text
FS_CLLBL  = 10.23   # cert name
FS_CLVAL  =  9.02   # cert provider
SEC_BAR_H = 25.3    # section bar height

MONTH_SHORT = {
    "01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
    "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec",
}

def fmt_date(raw):
    """'2025-04-2026-03'  →  'Apr 2025 – Mar 2026'"""
    parts = str(raw).split("-")
    if len(parts) == 4:
        y1,m1,y2,m2 = parts[0],parts[1],parts[2],parts[3]
        return f"{MONTH_SHORT.get(m1,m1)} {y1} – {MONTH_SHORT.get(m2,m2)} {y2}"
    return raw

# ─────────────────────────────────────────────────────────────────────────────
# Canvas helpers
# ─────────────────────────────────────────────────────────────────────────────

def cy(y_top, fs=0):
    return PH - y_top - fs

def draw_sidebar_bg(c):
    c.setFillColor(TEAL)
    c.rect(0, 0, SB_W, PH, fill=1, stroke=0)

def draw_section_bar(c, y_top, label):
    """Darker-teal bar with white label."""
    bar_canvas_y = cy(y_top) - SEC_BAR_H
    c.setFillColor(TEAL_DARK)
    c.rect(0, bar_canvas_y, SB_W, SEC_BAR_H, fill=1, stroke=0)
    text_y = bar_canvas_y + (SEC_BAR_H - FS_SHEAD) / 2 + 1
    c.setFillColor(WHITE)
    c.setFont("Helvetica", FS_SHEAD)          # Regular weight, matching PDF
    c.drawString(SPAD, text_y, label)
    return y_top + SEC_BAR_H

def divider_line(c, y_top):
    c.setFillColor(DIVIDER)
    c.rect(RX+RPAD, cy(y_top), RTW, 0.6, fill=1, stroke=0)
    return y_top + 1.5

def rc_section_header(c, y_top, text):
    """Teal, 13.24pt Regular — matches 'Work History' and 'Education' in PDF."""
    c.setFillColor(TEAL)
    c.setFont("Helvetica", FS_RCHEAD)         # Regular, not bold
    c.drawString(RX+RPAD, cy(y_top, FS_RCHEAD), text)
    return y_top + FS_RCHEAD + 3

def sb_line(c, y_top, text, size=None, indent=None):
    """Single sidebar line — always white, always Regular."""
    fs = size or FS_SITEM
    xi = indent if indent is not None else SPAD
    c.setFillColor(WHITE)
    c.setFont("Helvetica", fs)
    c.drawString(xi, cy(y_top, fs), text)
    return y_top + fs * 1.6

def sb_wrapped(c, y_top, text, size=None, indent=None):
    """Sidebar wrapped text."""
    fs     = size or FS_SITEM
    xi     = indent if indent is not None else SPAD
    avail  = SB_W - xi - 6
    cpl    = max(1, int(avail / (fs * 0.52)))
    lines  = textwrap.wrap(text, width=cpl) or [text]
    c.setFillColor(WHITE)
    c.setFont("Helvetica", fs)
    for ln in lines:
        c.drawString(xi, cy(y_top, fs), ln)
        y_top += fs * 1.45
    return y_top + fs * 0.15

def rc_para(c, x, y_top, text, fs, color, italic=False, bold=False, tw=None):
    """Wrapped paragraph in right column. italic and bold are mutually exclusive."""
    avail = tw if tw is not None else (RRIGHT - x)
    if italic:   fn = "Helvetica-Oblique"
    elif bold:   fn = "Helvetica-Bold"
    else:        fn = "Helvetica"
    style = ParagraphStyle("p", fontName=fn, fontSize=fs,
                           leading=fs*1.45, textColor=color)
    p = Paragraph(text, style)
    w, h = p.wrap(avail, PH)
    p.drawOn(c, x, cy(y_top) - h)
    return y_top + h + 1.5

def rc_bullet(c, y_top, text):
    fs = FS_BULLET
    avail = RRIGHT - ROLE_X - 10
    style = ParagraphStyle("b", fontName="Helvetica", fontSize=fs,
                           leading=fs*1.48, textColor=DARK)
    p = Paragraph(text, style)
    w, h = p.wrap(avail, PH)
    p.drawOn(c, ROLE_X+10, cy(y_top) - h)
    c.setFillColor(DARK)
    c.circle(ROLE_X+3.5, cy(y_top) - fs*0.65, 1.1, fill=1, stroke=0)
    return y_top + h + 2.5

def check_page(c, y_top, needed=60):
    if y_top + needed > PH - 20:
        c.showPage()
        draw_sidebar_bg(c)
        return 18
    return y_top

# ─────────────────────────────────────────────────────────────────────────────
# RESUME
# ─────────────────────────────────────────────────────────────────────────────

def build_resume(data: dict, output_path: str):
    c = rl_canvas.Canvas(output_path, pagesize=A4)
    draw_sidebar_bg(c)

    # ── LEFT COLUMN ──────────────────────────────────────────────────────────
    y = 14.0

    # Name — 22.86pt white Regular
    c.setFillColor(WHITE)
    c.setFont("Helvetica", FS_NAME)
    c.drawString(SPAD, cy(y, FS_NAME), data["name"])
    y += FS_NAME + 9                          # 9pt gap name → profession

    # Profession lines — 10.23pt white Regular
    for line in data.get("title_lines", []):
        c.setFillColor(WHITE)
        c.setFont("Helvetica", FS_PROF)
        c.drawString(SPAD, cy(y, FS_PROF), line)
        y += FS_PROF * 1.35
    y += 5

    # CONTACT
    y = draw_section_bar(c, y, "Contact")
    y += 7
    contact = data.get("contact", {})
    for label, value in [
        ("Email",    contact.get("email","")),
        ("Phone",    contact.get("phone","")),
        ("Address",  contact.get("address","")),
        ("LinkedIn", contact.get("linkedin","")),
    ]:
        if not value: continue
        y = sb_line(c, y, label, size=FS_SLBL)   # Regular (not bold) — matches PDF
        y -= 3
        if label == "Address":
            parts = [p.strip() for p in value.split(",",1)]
            for i,pt in enumerate(parts):
                suffix = "," if i==0 and len(parts)>1 else ""
                y = sb_wrapped(c, y, pt+suffix, size=FS_SVAL)
        else:
            y = sb_wrapped(c, y, value, size=FS_SVAL)
        y += 3
    y += 4

    # CORE EXPERTISE
    y = draw_section_bar(c, y, "Core Expertise")
    y += 7
    for item in data.get("core_expertise", []): y = sb_wrapped(c, y, item, size=FS_SITEM)
    y += 6

    # SKILLS
    y = draw_section_bar(c, y, "Skills")
    y += 7
    for skill in data.get("skills", []): y = sb_line(c, y, skill, size=FS_SITEM)
    y += 6

    # CERTIFICATES — claude certs first, then rest
    if data.get("certifications"):
        y = draw_section_bar(c, y, "Certificates")
        y += 7
        certs = data["certifications"]
        # Split claude vs others
        claude_certs = [c2 for c2 in certs if "claude" in c2.lower() or "anthropic" in c2.lower()]
        other_certs  = [c2 for c2 in certs if c2 not in claude_certs]
        ordered = claude_certs + other_certs
        for cert in ordered:
            nm, pv = (cert.split(" — ",1) if " — " in cert
                      else cert.split(" - ",1) if " - " in cert
                      else (cert,""))
            y = sb_wrapped(c, y, nm, size=FS_CLLBL)
            y -= 3
            if pv: y = sb_wrapped(c, y, pv, size=FS_CLVAL)
            y += 5

    # ── RIGHT COLUMN ─────────────────────────────────────────────────────────
    yr = 14.0

    # Summary — 7.82pt Regular dark
    if data.get("summary"):
        yr = rc_para(c, RX+RPAD, yr, data["summary"], FS_BULLET, DARK, tw=RTW)
        yr += 5

    # Work History
    yr = divider_line(c, yr)
    yr = rc_section_header(c, yr, "Work History")
    yr = divider_line(c, yr)
    yr += 5

    for job in data.get("work_history", []):
        yr = check_page(c, yr, needed=70)

        tenure = fmt_date(job.get("dates",""))

        # Row: role title left (bold, lighter dark), tenure right-aligned grey
        role_avail = ROLE_TW - c.stringWidth(tenure, "Helvetica", FS_CODATE) - 8
        style_role = ParagraphStyle("r", fontName="Helvetica-Bold", fontSize=FS_ROLE,
                                    leading=FS_ROLE*1.3, textColor=ROLE_BOLD)
        p_role = Paragraph(job["role"], style_role)
        _, role_h = p_role.wrap(role_avail, PH)
        p_role.drawOn(c, ROLE_X, cy(yr) - role_h)
        # Tenure right-aligned, lighter grey
        c.setFillColor(TENURE_GREY)
        c.setFont("Helvetica", FS_CODATE)
        c.drawRightString(RRIGHT, cy(yr, FS_CODATE), tenure)
        yr += max(role_h, FS_CODATE) + 2

        # Company italic below role
        yr = rc_para(c, ROLE_X, yr, f"{job['company']}, {job.get('location','')}",
                     FS_CODATE, DARK, italic=True, tw=ROLE_TW)
        yr += 2

        for bullet in job.get("bullets",[]):
            yr = check_page(c, yr, needed=28)
            yr = rc_bullet(c, yr, bullet)
        yr += 7

    # Education
    yr = check_page(c, yr, needed=50)
    yr = divider_line(c, yr)
    yr = rc_section_header(c, yr, "Education")
    yr = divider_line(c, yr)
    yr += 5
    for edu in data.get("education",[]):
        yr = rc_para(c, ROLE_X, yr, edu["degree"], FS_ROLE, ROLE_BOLD, bold=True, tw=ROLE_TW)
        detail = edu["institution"]
        if edu.get("dates"): detail += f" · {edu['dates']}"
        if edu.get("gpa"):   detail += f" · GPA: {edu['gpa']}"
        yr = rc_para(c, ROLE_X, yr, detail, FS_CODATE, DARK, italic=True, tw=ROLE_TW)
        yr += 4

    c.save()
    print(f"[pdf_renderer] Resume → {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# COVER LETTER
# ─────────────────────────────────────────────────────────────────────────────

def build_cover_letter(data: dict, output_path: str):
    c = rl_canvas.Canvas(output_path, pagesize=A4)
    draw_sidebar_bg(c)

    # ── LEFT COLUMN ──────────────────────────────────────────────────────────
    y = 14.0
    c.setFillColor(WHITE)
    c.setFont("Helvetica", FS_NAME)
    c.drawString(SPAD, cy(y, FS_NAME), data["name"])
    y += FS_NAME + 10

    for line in data.get("title_lines", []):
        c.setFillColor(WHITE)
        c.setFont("Helvetica", FS_PROF)
        c.drawString(SPAD, cy(y, FS_PROF), line)
        y += FS_PROF * 1.4
    y += 8

    y = draw_section_bar(c, y, "Contact")
    y += 8
    contact = data.get("contact", {})
    for label, value in [
        ("Email",    contact.get("email","")),
        ("Phone",    contact.get("phone","")),
        ("Address",  contact.get("address","")),
        ("LinkedIn", contact.get("linkedin","")),
    ]:
        if not value: continue
        y = sb_line(c, y, label, size=FS_SLBL)
        y -= 3
        y = sb_wrapped(c, y, value, size=FS_SVAL)
        y += 5

    # ── RIGHT COLUMN ─────────────────────────────────────────────────────────
    # Use larger font and generous spacing since cover letter has room
    CL_FS   = 10.5
    CL_LEAD = CL_FS * 1.65
    MID     = colors.Color(0.30, 0.30, 0.30)

    def cl_line(text, y_top, italic=False, color=None, fs=None):
        fsize = fs or CL_FS
        col   = color or MID
        fn    = "Helvetica-Oblique" if italic else "Helvetica"
        c.setFillColor(col)
        c.setFont(fn, fsize)
        c.drawString(RX+RPAD, cy(y_top, fsize), text)
        return y_top + fsize * 1.6

    def cl_para(text, y_top, color=None, fs=None):
        fsize  = fs or CL_FS
        col    = color or MID
        style  = ParagraphStyle("cl", fontName="Helvetica", fontSize=fsize,
                                leading=fsize*1.65, textColor=col)
        p = Paragraph(text, style)
        w, h = p.wrap(RTW, PH)
        p.drawOn(c, RX+RPAD, cy(y_top) - h)
        return y_top + h

    yr = 20.0
    yr = cl_line(data.get("date",""),      yr, color=MID)
    yr += CL_FS * 0.8
    yr = cl_line(data.get("recipient",""), yr, color=DARK)
    yr += CL_FS * 0.5
    yr = cl_line(data.get("salutation","Dear Hiring Team,"), yr, color=DARK)
    yr += CL_FS * 1.6

    for para in data.get("paragraphs",[]):
        yr = cl_para(para, yr)
        yr += CL_FS * 1.8     # full blank line between paragraphs

    yr += CL_FS * 0.8
    yr = cl_line(data.get("closing","Kind regards,"), yr, color=MID)
    yr += CL_FS * 2.0
    yr = cl_line(data["name"], yr, color=DARK)
    yr += CL_FS * 0.8
    for val in [contact.get("phone",""), contact.get("email","")]:
        if val:
            yr = cl_line(val, yr, color=MID, fs=CL_FS*0.95)
            yr += CL_FS * 0.5

    c.save()
    print(f"[pdf_renderer] Cover letter → {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_RESUME = {
    "name": "Vinay Patidar",
    "title_lines": ["Lead Product, Growth &", "Commercial Analytics Professional"],
    "contact": {
        "email":    "vinay_patidar02@yahoo.com",
        "phone":    "+91 8871717951",
        "address":  "Bengaluru, Karnataka 560035",
        "linkedin": "linkedin.com/in/vinay-patidar-vp02",
    },
    "core_expertise": [
        "Product Analytics","Growth Analytics",
        "Experimentation & A/B Testing",
        "Pricing & Commercial Optimization",
        "Customer Lifecycle Analytics",
        "KPI Strategy & Business Intelligence",
        "Strategic Decision-Making",
        "Stakeholder Management","Analytics Transformation",
    ],
    "skills": ["SQL","Tableau","Python","Looker Studio","BigQuery","Amazon Redshift"],
    "summary": (
        "Lead Product & Commercial Analytics professional with 8+ years of experience "
        "driving experimentation, customer growth, strategic decision-making, and pricing "
        "optimisation across ecommerce and technology businesses. Proven track record of "
        "building scalable KPI frameworks, leading cross-functional analytics initiatives, "
        "and delivering measurable business impact. Experienced in partnering with product, "
        "growth, operations, and leadership teams to solve complex business problems in "
        "high-growth environments."
    ),
    "work_history": [
        {
            "company":"Flipkart (Ecommerce)","location":"Bengaluru",
            "role":"Lead Business Analyst","dates":"2025-04-2026-03",
            "bullets":[
                "Led CRM analytics, incrementality testing, and experimentation for customer growth, driving 40% growth in Grocery visits and improved cohort monetisation.",
                "Developed customer propensity models capturing 70% of potential Grocery customers while targeting only 30% of the user base.",
                "Built automated KPI frameworks and scalable reporting standards improving decision-making consistency across product and growth teams.",
                "Managed analysts and drove cross-functional experimentation, behavioural analytics, and commercial modelling to optimise reseller behaviour and pricing elasticity.",
            ],
        },
        {
            "company":"BeepKart (Used 2W)","location":"Bengaluru",
            "role":"Analytics Manager","dates":"2023-07-2024-11",
            "bullets":[
                "Designed a Dynamic Pricing Algorithm reducing inventory holding from 40 to 25 days through optimised pricing and inventory decisions.",
                "Improved procurement efficiency by 30%+ through geo-clustering, lead-density optimisation, and resource allocation modelling.",
                "Led Agile analytics delivery using Jira/Confluence; managed and mentored a team of 5 analysts.",
            ],
        },
        {
            "company":"DeHaat (Agriculture Technology)","location":"Bengaluru",
            "role":"Lead Business Analyst","dates":"2021-07-2023-07",
            "bullets":[
                "Reduced overdue outstanding by 30% through data-driven collections prioritisation using customer risk segmentation.",
                "Developed customer scoring models improving engagement, targeting, and sales conversion. Led a team of 3 analysts.",
            ],
        },
        {
            "company":"Quinbay/Coviam Technology","location":"Bengaluru",
            "role":"Senior Data Analyst","dates":"2020-10-2021-07",
            "bullets":["Built search conversion tracking pipelines; conducted A/B tests via Firebase to optimise search and conversion."],
        },
        {
            "company":"Coviam Technology (Ecommerce)","location":"Bengaluru",
            "role":"Data Analyst","dates":"2017-05-2020-09",
            "bullets":[
                "Developed 150+ Tableau dashboards and 100+ data marts across 50+ microservices.",
                "Built an XGBoost delivery prediction model achieving 85% accuracy.",
            ],
        },
    ],
    "education": [{"degree":"Mining Engineering, B.Tech","institution":"IIT (BHU), Varanasi","dates":"2012 – 2016","gpa":"7.67/10"}],
    "certifications": [
        "Data Science using SAS and R — Analytix Labs",
        "Managing Big Data with MySQL — Coursera",
        "Data Visualization with Tableau — Coursera",
        "Mastering Data Analysis in Excel — Coursera",
        "Claude 101 — Anthropic Skilljar (2026)",
        "Claude Code 101 — Anthropic Skilljar (2026)",
    ],
}

SAMPLE_COVER = {
    "name": "Vinay Patidar",
    "title_lines": ["Lead Product, Growth &", "Commercial Analytics Professional"],
    "contact": {
        "email":    "vinay_patidar02@yahoo.com",
        "phone":    "+91 8871717951",
        "address":  "Bengaluru, Karnataka 560035",
        "linkedin": "linkedin.com/in/vinay-patidar-vp02",
    },
    "date":       "London, 2026-06-17",
    "recipient":  "Monzo Hiring Team",
    "salutation": "Dear Hiring Team,",
    "paragraphs": [
        "I am delighted to apply for the Analytics Manager role at Monzo. With over 8 years "
        "of experience across ecommerce and fintech-adjacent businesses, I have led analytics "
        "initiatives spanning customer growth, CRM experimentation, pricing optimisation, and "
        "KPI strategy. Monzo's customer-obsessed, data-driven culture is precisely the kind "
        "of environment where I do my best work.",

        "At Flipkart, I led CRM analytics and incrementality testing for Grocery growth — "
        "developing propensity models that identified 70% of high-potential customers while "
        "reaching only 30% of the base, and building automated KPI frameworks that gave "
        "leadership real-time visibility into cohort health and campaign ROI. At BeepKart, "
        "I designed a Dynamic Pricing Algorithm that reduced inventory holding from 40 to 25 "
        "days, and led a team of 5 analysts delivering experimentation and strategic insights "
        "in an Agile delivery model.",

        "Across my career I have consistently worked at the intersection of analytics, product "
        "strategy, and stakeholder management — mentoring teams, running cross-functional "
        "experimentation programmes, and translating complex data into decisions that move "
        "business metrics. I am also actively developing AI fluency through Anthropic's "
        "Claude Code programme, building agentic automation workflows that extend what "
        "analytics teams can deliver.",

        "What excites me most about Monzo is the scale of customer data and the genuine "
        "opportunity to improve people's financial lives through precision analytics. I would "
        "welcome the chance to discuss how my background in experimentation, lifecycle "
        "analytics, and team leadership can contribute to Monzo's next phase of growth. "
        "Thank you for your time and consideration.",
    ],
    "closing": "Kind regards,",
}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    if mode == "test":
        out = Path(__file__).parent.parent / "outputs" / "applications" / "_test_output"
        out.mkdir(parents=True, exist_ok=True)
        build_resume(SAMPLE_RESUME,      str(out / "sample_resume.pdf"))
        build_cover_letter(SAMPLE_COVER, str(out / "sample_cover_letter.pdf"))
        print(f"\nOutputs → {out}")
    elif mode == "resume":
        with open(sys.argv[2]) as f: data = json.load(f)
        build_resume(data, sys.argv[3])
    elif mode == "cover":
        with open(sys.argv[2]) as f: data = json.load(f)
        build_cover_letter(data, sys.argv[3])
