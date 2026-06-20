#!/usr/bin/env python3
"""
test_email_tracker.py — Test email status updates against existing applications
================================================================================
LEARNING NOTE — Why test the tracker in isolation?

Before wiring the full Gmail hook → tracker → sheets pipeline, this script
lets you test the tracker agent logic directly. It simulates what happens when
the on_email_received hook passes a classified email to agents/tracker.md.

This script does NOT call Gmail. Instead it:
  1. Shows your 19 active "Applied" entries (imported from Excel)
  2. Lets you simulate an incoming email for any of them
  3. Runs the same matching + status update logic the tracker agent uses
  4. Writes the result to job_tracker.json (real write, not a dry-run)
  5. Syncs to Google Sheets if configured

This confirms the tracker logic works BEFORE you connect Gmail.
After confirming, run the real backfill:
  claude "check email all"

Usage:
  python3 scripts/test_email_tracker.py          ← interactive mode
  python3 scripts/test_email_tracker.py --dry    ← show active entries, no writes
"""

import json, sys, re
from pathlib import Path
from datetime import datetime
from urllib import request as urllib_request

ROOT    = Path(__file__).parent.parent
TRACKER = ROOT / "data" / "job_tracker.json"

# ── Status pipeline order — never downgrade ───────────────────────────────────
PIPELINE = ["Shortlisted", "Approved", "Prep Complete", "Applied",
            "Under Review", "Interview Scheduled", "Assessment",
            "Offer Received", "Rejected", "Withdrawn"]

VALID_STATUSES = {
    "Applied", "Under Review", "Interview Scheduled",
    "Assessment", "Offer Received", "Rejected", "Not Relevant"
}

def pipeline_rank(status):
    try: return PIPELINE.index(status)
    except: return -1

# ── Claude API email classifier ───────────────────────────────────────────────
CLASSIFIER_PROMPT = """You are classifying a recruiter email for a job application tracker.

Given the email subject and body, determine:
1. status: What is the application status this email signals?
2. is_job_related: Is this email about a job application at all?
3. tracking_url: Any application tracking URL in the body (null if none)
4. notes: Brief reason for your classification (1 sentence)

Valid status values (choose exactly one):
- "Applied"             — confirmation that application was received
- "Under Review"        — actively being considered, shortlisted, progressing
- "Interview Scheduled" — invited to interview or call
- "Assessment"          — asked to complete a test, task, or assessment
- "Offer Received"      — job offer extended
- "Rejected"            — application unsuccessful, not progressing
- "Not Relevant"        — not a job application email (newsletter, spam, etc.)

IMPORTANT:
- Recruiters write in many ways. Focus on INTENT not exact words.
- "We've reviewed your profile and..." followed by next steps = Under Review
- "Regret to inform", "on this occasion", "position has been filled" = Rejected
- "Would love to chat", "quick call", "speak with you" = Interview Scheduled
- Any form of test, task, case study, coding challenge = Assessment
- Thank you for applying / we have received = Applied
- If genuinely ambiguous between two statuses, pick the more advanced one

Respond ONLY with valid JSON, no markdown, no explanation:
{
  "is_job_related": true/false,
  "status": "<one of the valid values above>",
  "tracking_url": "<url string or null>",
  "notes": "<brief reason>"
}"""

def classify_email_claude(subject: str, body: str) -> dict:
    """
    Use Claude API to classify an email into a job application status.
    Much more robust than keyword matching — handles any recruiter phrasing.
    Returns dict with: is_job_related, status, tracking_url, notes
    """
    user_message = f"Subject: {subject}\n\nBody:\n{body[:3000]}"  # cap at 3000 chars

    payload = {
        "model":      "claude-haiku-4-5-20251001",  # Haiku: $1/$5 per MTok — sufficient for classification
        "max_tokens": 300,
        "messages":   [{"role": "user", "content": user_message}],
        "system":     CLASSIFIER_PROMPT,
    }

    req = urllib_request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type":      "application/json",
            "anthropic-version": "2023-06-01",
            # API key is injected by the Anthropic platform when running in Claude.ai
            # For local runs, set ANTHROPIC_API_KEY in .env
        },
        method="POST"
    )

    # Load API key from .env for local runs
    env_file = ROOT / ".env"
    api_key  = None
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    if api_key:
        req.add_header("x-api-key", api_key)

    try:
        with urllib_request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        raw  = data["content"][0]["text"].strip()
        # Strip markdown fences if present
        raw  = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        # Validate status
        if result.get("status") not in VALID_STATUSES:
            result["status"] = "Not Relevant"
        return result
    except Exception as e:
        print(f"  ⚠ Claude API error: {e}")
        print(f"  Falling back to keyword classification...")
        return _keyword_fallback(subject, body)

def _keyword_fallback(subject: str, body: str) -> dict:
    """Last-resort keyword classifier if API call fails."""
    STATUS_KEYWORDS = {
        "Applied":             ["application received","thank you for applying",
                                "we've received","received your application"],
        "Under Review":        ["under review","being considered","shortlisted",
                                "progressing","reviewing your application"],
        "Interview Scheduled": ["invite you to interview","interview invitation",
                                "schedule an interview","speak with you",
                                "quick call","love to chat"],
        "Assessment":          ["online assessment","take-home","technical test",
                                "complete the following","coding challenge","case study"],
        "Offer Received":      ["pleased to offer","offer of employment","formal offer"],
        "Rejected":            ["unfortunately","not successful","not moving forward",
                                "on this occasion","regret to inform",
                                "position has been filled","won't be progressing"],
    }
    text = (subject + " " + body).lower()
    for status, keywords in STATUS_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                url = re.search(r'https?://[^\s<>"]+', body)
                return {
                    "is_job_related": True,
                    "status": status,
                    "tracking_url": url.group(0) if url else None,
                    "notes": f"Keyword match: '{kw}'"
                }
    return {
        "is_job_related": False,
        "status": "Not Relevant",
        "tracking_url": None,
        "notes": "No keywords matched"
    }


# ── Company alias map ─────────────────────────────────────────────────────────
# Maps known aliases / abbreviations → canonical name as it appears in tracker.
# Add entries here whenever you notice a mismatch between email and tracker.
COMPANY_ALIASES = {
    # Financial / banking
    "jpmc":               "JPMorgan Chase",
    "jp morgan":          "JPMorgan Chase",
    "j.p. morgan":        "JPMorgan Chase",
    "jpmorgan":           "JPMorgan Chase",
    "jpmorgan chase":     "JPMorgan Chase",
    # Recruiters / agencies that email on behalf of companies
    "greenhouse":         None,   # ATS platform — match by role only
    "lever":              None,
    "workday":            None,
    "ashby":              None,
    "smartrecruiters":    None,
    # Add more as you encounter them:
    # "amzn":             "Amazon",
    # "meta platforms":   "Meta",
}

# ATS sender domains — emails come from these domains on behalf of companies
# Company name must be extracted from email body/subject instead
ATS_DOMAINS = {
    "greenhouse.io", "lever.co", "myworkdayjobs.com", "ashbyhq.com",
    "smartrecruiters.com", "icims.com", "taleo.net", "bamboohr.com",
    "teamtailor.com", "personio.de", "workable.com", "recruitee.com",
    "pinpointhq.com", "jobvite.com", "successfactors.com",
}


def normalise_company(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for comparison."""
    name = name.lower().strip()
    name = re.sub(r"[&,\.\-\(\)]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    # Strip common suffixes that vary between sources
    for suffix in [" ltd", " limited", " plc", " inc", " llc",
                   " group", " technologies", " technology",
                   " solutions", " services", " global"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name


def company_tokens(name: str) -> set:
    """Return meaningful word tokens from a company name."""
    norm = normalise_company(name)
    return {t for t in norm.split() if len(t) > 2}


def companies_match(a: str, b: str) -> bool:
    """
    Robust company matching that handles:
    - Exact normalised match
    - One is substring of the other (post-normalisation)
    - Alias map lookup
    - Token overlap (≥ 1 meaningful shared token)
    - Abbreviations (JPMC vs JPMorgan Chase)
    """
    a_norm = normalise_company(a)
    b_norm = normalise_company(b)

    # Direct normalised match
    if a_norm == b_norm:
        return True
    # Substring either direction
    if a_norm in b_norm or b_norm in a_norm:
        return True

    # Alias lookup — check if either resolves to same canonical name
    a_canon = COMPANY_ALIASES.get(a_norm, a_norm)
    b_canon = COMPANY_ALIASES.get(b_norm, b_norm)
    if a_canon and b_canon:
        if normalise_company(a_canon) == normalise_company(b_canon):
            return True

    # Token overlap — at least 1 meaningful shared word
    a_tok = company_tokens(a)
    b_tok = company_tokens(b)
    if a_tok & b_tok:
        return True

    # Initialism check — e.g. "JPMC" matches "JPMorgan Chase"
    # Build initialism from multi-word company name
    a_words = a_norm.split()
    b_words = b_norm.split()
    if len(b_words) >= 2:
        b_init = "".join(w[0] for w in b_words)
        if a_norm == b_init:
            return True
    if len(a_words) >= 2:
        a_init = "".join(w[0] for w in a_words)
        if b_norm == a_init:
            return True

    return False


def extract_company_from_text(text: str, known_companies: list) -> list:
    """
    Scan full email text for mentions of known company names.
    Returns list of matching companies found.
    """
    found = []
    text_lower = text.lower()
    for company in known_companies:
        norm = normalise_company(company)
        if not norm:
            continue
        # Direct name mention in text
        if norm in text_lower:
            found.append(company)
            continue
        # Any alias mention
        for alias, canonical in COMPANY_ALIASES.items():
            if canonical and normalise_company(canonical) == norm:
                if alias in text_lower:
                    found.append(company)
                    break
    return found


def find_match(tracker_apps, sender_email, sender_domain, subject, body):
    """
    Robust application matching using multiple signals:

    Signal A — Sender domain (if not an ATS platform):
        Match sender domain against company names in tracker.

    Signal B — Company name in full email text:
        Scan entire subject + body for company name mentions.
        Uses normalisation, alias map, token overlap, and initialism check.

    Signal C — Role keyword match:
        Among company matches, find the specific role using title words.

    Returns (matched_app, confidence) or (None, reason_string).
    """
    full_text   = (subject + " " + body)
    full_lower  = full_text.lower()
    domain_base = sender_domain.lower().replace("www.", "").split(".")[0]
    is_ats      = any(ats in sender_domain.lower() for ats in ATS_DOMAINS)

    known_companies = list({a.get("company", "") for a in tracker_apps if a.get("company")})

    # ── Signal A: domain match (skip for ATS senders) ────────────────────────
    domain_matched = []
    if not is_ats:
        for app in tracker_apps:
            if companies_match(domain_base, app.get("company", "")):
                domain_matched.append(app)

    # ── Signal B: company name in full email text ─────────────────────────────
    text_matched_companies = extract_company_from_text(full_text, known_companies)
    text_matched = [a for a in tracker_apps
                    if a.get("company", "") in text_matched_companies]

    # Combine, deduplicate
    all_company_matches = list({a["id"]: a for a in domain_matched + text_matched}.values())

    if not all_company_matches:
        return None, "no_company_match"

    # ── Signal C: role keyword match ──────────────────────────────────────────
    for app in all_company_matches:
        role_words = [w for w in app.get("role", "").lower().split()
                      if len(w) > 3 and w not in {"lead", "data", "with", "your", "this", "that"}]
        if any(w in full_lower for w in role_words):
            return app, "high"

    # Single company match without role signal
    if len(all_company_matches) == 1:
        return all_company_matches[0], "low"

    # Multiple company matches, no role signal to disambiguate
    return None, "multiple_matches"


def update_tracker(app_id, new_status, email_record, tracker):
    """Apply status update to tracker entry. Returns True if changed."""
    apps = {a["id"]: a for a in tracker["applications"]}
    if app_id not in apps:
        return False

    app = apps[app_id]
    current_status = app.get("status", "")
    current_rank   = pipeline_rank(current_status)
    new_rank       = pipeline_rank(new_status)

    changed = False

    # Only upgrade status, never downgrade
    if new_rank > current_rank:
        app["status"] = new_status
        app.setdefault("status_history", []).append({
            "status": new_status,
            "date":   email_record["received_date"],
            "source": "test_email_tracker"
        })
        changed = True

    # Always append email record
    app.setdefault("emails_received", []).append(email_record)

    # Extract tracking URL if present
    if email_record.get("tracking_url") and not app.get("tracking_url"):
        app["tracking_url"] = email_record["tracking_url"]
        changed = True

    # Write back
    tracker["applications"] = list(apps.values())
    TRACKER.write_text(json.dumps(tracker, indent=2, ensure_ascii=False))
    return changed

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry" in sys.argv

    tracker = json.loads(TRACKER.read_text())
    apps    = tracker["applications"]

    # Show active (non-rejected) applications
    active = [a for a in apps if a.get("status") not in ("Rejected","Withdrawn","Offer Received")]
    applied = [a for a in active if a.get("source") == "excel_import"]

    print(f"\n{'='*60}")
    print(f"  Email Tracker Test — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"\n  Active applications: {len(active)}")
    print(f"  Excel-imported (19 applied): {len(applied)}")
    print(f"\n  ALL ACTIVE APPLICATIONS:")
    print(f"  {'#':<4} {'Company':<30} {'Role':<35} {'Status'}")
    print(f"  {'-'*100}")
    for i, a in enumerate(active, 1):
        print(f"  {i:<4} {a.get('company',''):<30} {a.get('role',''):<35} {a.get('status','')}")

    if dry_run:
        print(f"\n  [dry-run] No writes performed.")
        print(f"  Run without --dry to simulate an email update.")
        return

    print(f"\n{'─'*60}")
    print("  SIMULATE AN INCOMING EMAIL")
    print("  Enter details to test the matching + update logic.")
    print(f"{'─'*60}\n")

    sender    = input("  Sender email (e.g. jobs@monzo.com): ").strip()
    subject   = input("  Email subject: ").strip()
    print("  Email body (paste text, then press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    body = "\n".join(lines).strip()

    domain = sender.split("@")[-1] if "@" in sender else sender

    # Classify using Claude API (with keyword fallback)
    print(f"\n  Classifying email via Claude API...")
    result = classify_email_claude(subject, body)

    if not result["is_job_related"] or result["status"] == "Not Relevant":
        print(f"\n  ℹ Email classified as not job-related.")
        print(f"  Reason: {result.get('notes','')}")
        print(f"  If this is wrong, check that the email body contains enough context.")
        return

    status = result["status"]
    url    = result.get("tracking_url")

    print(f"\n  Classified as: {status}")
    print(f"  Reason:        {result.get('notes','')}")
    if url: print(f"  Tracking URL:  {url}")

    # Match — pass full sender email + domain
    matched_app, confidence = find_match(active, sender, domain, subject, body)

    if not matched_app:
        reason_map = {
            "no_company_match":  f"No company in tracker matched sender '{sender}' or email text.",
            "multiple_matches":  "Multiple companies matched — cannot safely assign without role signal.",
        }
        print(f"\n  ✗ {reason_map.get(confidence, 'No match found.')}")
        print(f"  Tip: Check COMPANY_ALIASES in the script to add '{domain}' → company name.")

        # Log unmatched
        unmatched_path = ROOT / "data" / "unmatched_emails.json"
        unmatched = json.loads(unmatched_path.read_text())
        unmatched["unmatched_emails"].append({
            "logged_date":  datetime.now().strftime("%Y-%m-%d"),
            "sender_email": sender,
            "subject":      subject,
            "body_snippet": body[:200],
            "reason":       confidence or "no_company_match"
        })
        unmatched_path.write_text(json.dumps(unmatched, indent=2))
        return

    print(f"\n  Matched: {matched_app.get('company')} / {matched_app.get('role')}")
    print(f"  Confidence: {confidence}")
    print(f"  Current status: {matched_app.get('status')}")
    print(f"  New status:     {status}")

    if pipeline_rank(status) <= pipeline_rank(matched_app.get("status","")):
        print(f"\n  ℹ Status not upgraded — '{status}' is not higher than '{matched_app.get('status')}'")
        print(f"    Email recorded but status unchanged.")

    confirm = input(f"\n  Apply this update to job_tracker.json? [Y/n]: ").strip().lower()
    if confirm in ("", "y", "yes"):
        email_record = {
            "received_date":    datetime.now().strftime("%Y-%m-%d"),
            "subject":          subject,
            "sender":           sender,
            "status_extracted": status,
            "tracking_url":     url,
            "confidence":       confidence
        }
        changed = update_tracker(matched_app["id"], status, email_record, tracker)

        if changed:
            print(f"\n  ✓ job_tracker.json updated")
            print(f"    {matched_app.get('company')} / {matched_app.get('role')} → {status}")
        else:
            print(f"\n  ℹ Email recorded, no status change (not an upgrade)")

        # Push to sheets if configured
        env = {}
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()

        if env.get("GOOGLE_SHEET_ID") and (ROOT / "data" / "google_service_account.json").exists():
            print(f"\n  Syncing to Google Sheet...")
            import subprocess
            result = subprocess.run(
                ["python3", "scripts/sheets_sync.py", "push"],
                capture_output=True, text=True, cwd=ROOT
            )
            if result.returncode == 0:
                print(f"  ✓ Google Sheet updated")
            else:
                print(f"  ⚠ Sheet sync failed: {result.stderr[:100]}")
        else:
            print(f"\n  ℹ Google Sheets not configured — skipping sync")
            print(f"    Set up sheets_sync.py to see updates in the Sheet")
    else:
        print("  Cancelled — no changes made.")

    print(f"\n  Test complete. Check data/job_tracker.json to verify.")
    print(f"  When ready for the real backfill: claude 'check email all'\n")

if __name__ == "__main__":
    main()
