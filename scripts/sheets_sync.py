#!/usr/bin/env python3
"""
sheets_sync.py — Bidirectional sync: job_tracker.json ↔ Google Sheet
======================================================================
LEARNING NOTE — Why a sync layer rather than replacing job_tracker.json?

Agents need fast, offline, atomic reads/writes → local JSON.
You need a human-readable, clickable, editable view → Google Sheets.
A sync layer gives both. Agents write to JSON; this script pushes
to Sheets so you can see and edit. When you edit Sheets (status,
career_page_url, notes), this script pulls those changes back to JSON.

Two modes:
  push  — JSON → Sheets  (run after scrape/score/enrich)
  pull  — Sheets → JSON  (run before application prep, to pick up
                           your edits: status=Approved, career_page_url)

Usage:
  python3 scripts/sheets_sync.py push
  python3 scripts/sheets_sync.py pull

Setup (one-time, see README in this file):
  1. Create Google Cloud project, enable Sheets API + Drive API
  2. Create Service Account, download JSON key → save as
     data/google_service_account.json
  3. Create a new Google Sheet, share it with the service account email
  4. Copy the Sheet ID from the URL into .env as GOOGLE_SHEET_ID

Sheet structure (one row per application):
  Col A: id                (internal — for workflow matching, not for sharing)
  Col B: reference         (Company — Role, shareable with referral contacts)
  Col C: job_id            (LinkedIn job ID from scrape — shareable identifier)
  Col D: company           (read-only)
  Col E: role              (read-only)
  Col F: location          (read-only)
  Col G: posted_date       (read-only)
  Col H: fit_score         (read-only, populated after Stage 3)
  Col I: salary_stated     (read-only)
  Col J: work_mode         (read-only)
  Col K: experience_req    (read-only)
  Col L: status            ← YOU EDIT THIS — change to "Approved" when ready
                             NOTE: only change to Approved AFTER filling Col M
  Col M: career_page_url   ← PASTE ATS URL HERE FIRST (before setting Approved)
  Col N: applied_date      (read-only)
  Col O: notes             ← YOU CAN ADD NOTES / referral contact name here
  Col P: visa_sponsorship  (read-only)
  Col Q: ats_type          (read-only)

  IMPORTANT EDIT ORDER:
    1. Paste career_page_url in Col M
    2. THEN change status to "Approved" in Col L
    3. THEN run: python3 scripts/sheets_sync.py pull
    application_prep agent will only fire when BOTH are present.
"""

import json, sys, os
from pathlib import Path
from datetime import datetime

ROOT        = Path(__file__).parent.parent
TRACKER     = ROOT / "data" / "job_tracker.json"
SA_FILE     = ROOT / "data" / "google_service_account.json"
ENV_FILE    = ROOT / ".env"

# ── Load env vars ─────────────────────────────────────────────────────────────
env = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

SHEET_ID = env.get("GOOGLE_SHEET_ID", "")

# ── Validate setup ────────────────────────────────────────────────────────────
def check_setup():
    errors = []
    if not SA_FILE.exists():
        errors.append(
            f"Service account file not found: {SA_FILE}\n"
            "  → Follow setup steps in this file's docstring"
        )
    if not SHEET_ID:
        errors.append(
            "GOOGLE_SHEET_ID not set in .env\n"
            "  → Create a Google Sheet, copy its ID from the URL\n"
            "    (the long string between /d/ and /edit)\n"
            "  → Add to .env: GOOGLE_SHEET_ID=your_sheet_id_here"
        )
    if errors:
        print("\n[sheets_sync] Setup incomplete:")
        for e in errors: print(f"  ✗ {e}")
        sys.exit(1)

# ── Connect to Google Sheets ──────────────────────────────────────────────────
def get_sheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("\n[sheets_sync] Missing dependencies. Install with:")
        print("  pip install gspread google-auth")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(str(SA_FILE), scopes=scopes)
    gc     = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)

# ── Column definitions ────────────────────────────────────────────────────────
HEADERS = [
    "id", "reference", "job_id", "company", "role", "location", "posted_date",
    "fit_score", "salary_stated", "work_mode", "experience_req",
    "status",           # ← user editable
    "jd_url",
    "career_page_url",  # ← user editable
    "applied_date",
    "notes",            # ← user editable
    "visa_sponsorship_status",
    "ats_type",
]

# Columns the user is allowed to edit — pulled back during pull
USER_EDITABLE = {"status", "career_page_url", "notes"}

def app_to_row(app: dict) -> list:
    """Convert a job_tracker.json application entry to a sheet row."""
    exp = app.get("experience_years", {}) or {}
    company = app.get("company", "")
    role    = app.get("role", "")
    ref     = f"{company} — {role}"
    return [
        app.get("id", ""),
        ref,
        app.get("job_id", ""),
        app.get("company", ""),
        app.get("role", ""),
        app.get("location", ""),
        app.get("applied_date") or app.get("posted_date", ""),
        app.get("fit_score", ""),
        app.get("salary_stated", ""),
        app.get("work_mode", ""),
        exp.get("display", ""),
        app.get("status", ""),
        app.get("jd_url", ""),
        app.get("career_page_url", "") or "",
        app.get("applied_date", "") or "",
        app.get("notes", "") or "",
        app.get("visa_sponsorship_status", ""),
        app.get("ats_type", "") or "",
    ]

# ─────────────────────────────────────────────────────────────────────────────
# PUSH: job_tracker.json → Google Sheets
# ─────────────────────────────────────────────────────────────────────────────
def push():
    print("\n[sheets_sync] PUSH: job_tracker.json → Google Sheets")
    check_setup()

    tracker = json.loads(TRACKER.read_text())
    apps    = tracker["applications"]
    print(f"  {len(apps)} applications to sync")

    wb = get_sheet()

    # ── Applications sheet ────────────────────────────────────────────────────
    try:
        ws = wb.worksheet("Applications")
    except Exception:
        ws = wb.add_worksheet("Applications", rows=500, cols=len(HEADERS))
        print("  Created 'Applications' worksheet")

    # Write headers with formatting hint (bold row 1)
    ws.update("A1", [HEADERS])

    # Write all application rows
    rows = [app_to_row(a) for a in apps]
    if rows:
        ws.update(f"A2", rows)

    # Clear any rows beyond current data (handles deletions)
    last_row = len(rows) + 2
    total_rows = ws.row_count
    if total_rows > last_row:
        ws.delete_rows(last_row, total_rows)

    # Make JD URL and Career Page URL clickable
    for i, app in enumerate(apps, start=2):
        jd  = app.get("jd_url", "")
        cp  = app.get("career_page_url", "") or ""
        if jd:
            ws.update_cell(i, HEADERS.index("jd_url") + 1,
                          f'=HYPERLINK("{jd}","View JD")')
        if cp:
            ws.update_cell(i, HEADERS.index("career_page_url") + 1,
                          f'=HYPERLINK("{cp}","Apply")')

    print(f"  ✓ Pushed {len(rows)} rows to 'Applications' sheet")

    # ── Add dropdowns for user-editable columns ───────────────────────────────
    # Uses Google Sheets API batchUpdate for data validation rules.
    # Only applied to data rows (row 2 onwards), not the header.
    if len(rows) > 0:
        try:
            _apply_dropdowns(wb, ws, len(rows))
            print(f"  ✓ Dropdowns applied to status and career_page_url columns")
        except Exception as e:
            print(f"  ⚠ Dropdown setup failed (non-critical): {e}")

    print(f"  Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


def _apply_dropdowns(wb, ws, num_rows: int):
    """
    Apply data validation dropdowns to user-editable columns.
    Uses raw Sheets API batchUpdate — no extra dependencies needed.

    Dropdowns:
      Col L (status, index 11)      — valid pipeline statuses
      Col M (career_page_url, 13)   — hint values: EASY_APPLY or paste URL
        (can't enforce URL format via dropdown, so we add a note dropdown
         that reminds you of the two valid entry types)
    """
    STATUS_COL    = HEADERS.index("status")           # 0-indexed = 11
    CAREER_COL    = HEADERS.index("career_page_url")  # 0-indexed = 13

    STATUS_VALUES = [
        "Shortlisted", "Approved", "Prep Complete", "Applied",
        "Under Review", "Interview Scheduled", "Assessment",
        "Offer Received", "Rejected", "Withdrawn"
    ]

    CAREER_HINTS = [
        "EASY_APPLY",
        "Paste ATS URL here",
    ]

    spreadsheet_id = wb.id
    creds          = wb.client.auth

    # Build Sheets API request using gspread's underlying service
    # gspread exposes the raw service via client.auth._default_http
    # We use requests directly with the service account token
    import json as _json
    from google.auth.transport.requests import Request as GARequest

    # Refresh credentials if needed
    if not creds.valid:
        creds.refresh(GARequest())

    token = creds.token

    def col_range(col_0idx):
        """Build GridRange dict for a full column (data rows only)."""
        return {
            "sheetId":          ws.id,
            "startRowIndex":    1,               # row 2 (0-indexed)
            "endRowIndex":      num_rows + 1,
            "startColumnIndex": col_0idx,
            "endColumnIndex":   col_0idx + 1,
        }

    def dropdown_rule(values, col_0idx, strict=True):
        return {
            "setDataValidation": {
                "range": col_range(col_0idx),
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": v} for v in values],
                    },
                    "showCustomUi":  True,
                    "strict":        strict,
                }
            }
        }

    requests = [
        dropdown_rule(STATUS_VALUES, STATUS_COL, strict=True),
        # career_page_url: show hint dropdown but not strict
        # (user needs to paste a real URL too, so we can't enforce a fixed list)
        dropdown_rule(CAREER_HINTS, CAREER_COL, strict=False),
    ]

    import urllib.request as _ureq
    url     = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"
    payload = _json.dumps({"requests": requests}).encode()
    req     = _ureq.Request(url, data=payload, method="POST")
    req.add_header("Authorization",  f"Bearer {token}")
    req.add_header("Content-Type",   "application/json")

    with _ureq.urlopen(req, timeout=20) as resp:
        resp.read()   # consume response


# ─────────────────────────────────────────────────────────────────────────────
# PULL: Google Sheets → job_tracker.json (user-editable columns only)
# ─────────────────────────────────────────────────────────────────────────────
def pull():
    print("\n[sheets_sync] PULL: Google Sheets → job_tracker.json")
    print("  Reading user-editable columns: status, career_page_url, notes")
    check_setup()

    tracker = json.loads(TRACKER.read_text())
    apps    = {a["id"]: a for a in tracker["applications"]}

    wb = get_sheet()
    try:
        ws = wb.worksheet("Applications")
    except Exception:
        print("  ✗ 'Applications' worksheet not found — run push first")
        sys.exit(1)

    rows = ws.get_all_records()   # list of dicts keyed by header row
    updated = 0

    for row in rows:
        app_id = str(row.get("id", "")).strip()
        if not app_id or app_id not in apps:
            continue

        app     = apps[app_id]
        changed = []

        for col in USER_EDITABLE:
            sheet_val = str(row.get(col, "") or "").strip()
            local_val = str(app.get(col, "") or "").strip()

            # Skip HYPERLINK formula values — extract raw URL
            if sheet_val.startswith("=HYPERLINK"):
                import re
                m = re.search(r'HYPERLINK\("([^"]+)"', sheet_val)
                sheet_val = m.group(1) if m else ""

            if sheet_val and sheet_val != local_val:
                # Status change — record in history
                if col == "status" and sheet_val != local_val:
                    if "status_history" not in app:
                        app["status_history"] = []
                    app["status_history"].append({
                        "status": sheet_val,
                        "date":   datetime.now().strftime("%Y-%m-%d"),
                        "source": "sheets_sync_pull",
                    })
                app[col] = sheet_val
                changed.append(f"{col}: '{local_val}' → '{sheet_val}'")

        if changed:
            updated += 1
            print(f"  ✓ {app.get('company')} / {app.get('role')}")
            for c in changed: print(f"      {c}")

    # Write back
    tracker["applications"] = list(apps.values())
    TRACKER.write_text(json.dumps(tracker, indent=2, ensure_ascii=False))

    print(f"\n  {updated} applications updated in job_tracker.json")
    if updated == 0:
        print("  (No changes detected in user-editable columns)")


# ─────────────────────────────────────────────────────────────────────────────
# SETUP INSTRUCTIONS (printed when run without args)
# ─────────────────────────────────────────────────────────────────────────────
SETUP_GUIDE = """
sheets_sync.py — One-time Setup
═══════════════════════════════

Step 1 — Install dependencies (in your venv):
  pip install gspread google-auth

Step 2 — Create Google Cloud credentials:
  a. Go to https://console.cloud.google.com
  b. Select your existing 'job-automation' project
     (or create a new one)
  c. APIs & Services → Enable APIs:
       - Google Sheets API
       - Google Drive API
  d. APIs & Services → Credentials →
     + Create Credentials → Service Account
       Name: job-automation-sheets
       Click Create, skip optional steps
  e. Click the service account email → Keys →
     Add Key → Create new key → JSON → Download
  f. Rename the downloaded file to:
       google_service_account.json
     Move it to your project's data/ folder

Step 3 — Create your Google Sheet:
  a. Go to https://sheets.google.com → New spreadsheet
  b. Name it: "Job Application Tracker"
  c. Share it with the service account email
     (found in google_service_account.json as "client_email")
     → Give it Editor access
  d. Copy the Sheet ID from the URL:
     https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
  e. Add to .env:
     GOOGLE_SHEET_ID=SHEET_ID_HERE

Step 4 — Test:
  python3 scripts/sheets_sync.py push
  (Then open your Sheet — you should see all applications)

Step 5 — Workflow:
  After every scrape+enrich:   python3 scripts/sheets_sync.py push
  Before approving jobs:       python3 scripts/sheets_sync.py pull
  After editing sheet:         python3 scripts/sheets_sync.py pull
"""

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "push":
        push()
    elif mode == "pull":
        pull()
    else:
        print(SETUP_GUIDE)
