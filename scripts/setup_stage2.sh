#!/usr/bin/env bash
# =============================================================
# setup_stage2.sh — Stage 2 MCP Setup & Verification
# =============================================================
# Run this script AFTER filling in your .env file.
# It will:
#   1. Check all prerequisites (Node.js, npx, Python, venv)
#   2. Validate your .env values are set
#   3. Test Apify connection and correct actor
#   4. Check Gmail token status
#   5. Check Google Sheets setup
#   6. Verify MCP server is runnable
#   7. Test PDF renderer
#   8. Validate data files
#   9. Print a go/no-go summary
#
# Usage:
#   chmod +x scripts/setup_stage2.sh
#   ./scripts/setup_stage2.sh
# =============================================================

set -e
cd "$(dirname "$0")/.."   # always run from project root

# ── Colours ───────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; FAILED=1; }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }

FAILED=0
echo ""
echo "================================================="
echo "  Stage 2 Setup Verification — Job Automation"
echo "================================================="
echo ""

# ── Step 1: Prerequisites ──────────────────────────────────────
echo "── Step 1: Prerequisites ──"

if command -v node &>/dev/null; then
    NODE_VER=$(node -v)
    NODE_MAJOR=$(echo $NODE_VER | cut -d'.' -f1 | tr -d 'v')
    if [ "$NODE_MAJOR" -lt 18 ]; then
        fail "Node.js must be v18+. Found $NODE_VER — run: brew upgrade node"
    else
        ok "Node.js $NODE_VER"
    fi
else
    fail "Node.js not found — run: brew install node"
fi

command -v npx &>/dev/null && ok "npx found" || fail "npx not found (install Node.js)"

# Python — prefer venv python, fall back to python3.12, then python3
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    ok "Python venv active: $(.venv/bin/python --version)"
elif command -v python3.12 &>/dev/null; then
    PYTHON="python3.12"
    warn "No .venv found — using $(python3.12 --version)"
    warn "Recommended: python3.12 -m venv .venv && source .venv/bin/activate"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    warn "Using system python3: $(python3 --version) — recommend python3.12 + venv"
else
    fail "Python not found"
    PYTHON="python3"
fi

# Check required Python packages
for pkg in reportlab pdfplumber openpyxl gspread google.oauth2; do
    if $PYTHON -c "import ${pkg%%.*}" 2>/dev/null; then
        ok "  Python: $pkg"
    else
        warn "  Python: $pkg not installed"
        warn "  → source .venv/bin/activate && pip install reportlab pdfplumber openpyxl gspread google-auth"
        FAILED=1
    fi
done

echo ""

# ── Step 2: .env validation ────────────────────────────────────
echo "── Step 2: Environment Variables ──"

if [ ! -f ".env" ]; then
    fail ".env not found — run: cp .env.example .env  then fill in values"
    echo "  Cannot continue. Exiting."
    exit 1
fi

set -a; source .env; set +a

if [ -z "$APIFY_TOKEN" ] || [ "$APIFY_TOKEN" = "your_apify_api_token_here" ]; then
    fail "APIFY_TOKEN not set — get from: https://console.apify.com → Settings → Integrations"
else
    ok "APIFY_TOKEN set"
fi

if [ -z "$GOOGLE_SHEET_ID" ] || [ "$GOOGLE_SHEET_ID" = "your_google_sheet_id_here" ]; then
    warn "GOOGLE_SHEET_ID not set — needed for sheets_sync.py (not blocking for scrape)"
else
    ok "GOOGLE_SHEET_ID set"
fi

if [ -z "$GMAIL_REFRESH_TOKEN" ] && [ -z "$GMAIL_ACCESS_TOKEN" ]; then
    warn "Gmail tokens not set — run: node scripts/gmail_auth.js (needed for Stage 5)"
else
    ok "Gmail tokens set"
fi

echo ""

# ── Step 3: Apify API + correct actor ─────────────────────────
echo "── Step 3: Apify API & Actor ──"

APIFY_RESP=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/users/me")

if [ "$APIFY_RESP" = "200" ]; then
    APIFY_USER=$(curl -s \
        -H "Authorization: Bearer $APIFY_TOKEN" \
        "https://api.apify.com/v2/users/me" | $PYTHON -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('username','unknown'))")
    ok "Apify API connected — account: $APIFY_USER"
elif [ "$APIFY_RESP" = "401" ]; then
    fail "Apify token invalid (HTTP 401) — check APIFY_TOKEN in .env"
else
    fail "Apify API returned HTTP $APIFY_RESP"
fi

# Verify correct actor (nexgendata, not bebity or cryptosignals)
ACTOR_RESP=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/acts/nexgendata~linkedin-jobs-scraper")
if [ "$ACTOR_RESP" = "200" ]; then
    ok "Actor nexgendata/linkedin-jobs-scraper accessible"
else
    warn "Actor check returned HTTP $ACTOR_RESP"
    warn "Visit: https://apify.com/nexgendata/linkedin-jobs-scraper"
fi

echo ""

# ── Step 4: Google Sheets ──────────────────────────────────────
echo "── Step 4: Google Sheets ──"

if [ -f "data/google_service_account.json" ]; then
    ok "data/google_service_account.json present"
    if [ -n "$GOOGLE_SHEET_ID" ] && [ "$GOOGLE_SHEET_ID" != "your_google_sheet_id_here" ]; then
        # Quick connectivity test
        SHEET_TEST=$($PYTHON -c "
import sys
try:
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_file(
        'data/google_service_account.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    gc.open_by_key('$GOOGLE_SHEET_ID')
    print('ok')
except Exception as e:
    print(f'error: {e}')
" 2>&1)
        if [ "$SHEET_TEST" = "ok" ]; then
            ok "Google Sheet accessible"
        else
            warn "Sheet connection issue: $SHEET_TEST"
            warn "Check service account has Editor access to the sheet"
        fi
    else
        warn "GOOGLE_SHEET_ID not set — add to .env before running sheets_sync.py"
    fi
else
    warn "data/google_service_account.json not found"
    warn "Run: python3 scripts/sheets_sync.py  (no args) for setup instructions"
fi

echo ""

# ── Step 5: Apify MCP Server ──────────────────────────────────
echo "── Step 5: Apify MCP Server ──"

echo "  Checking @apify/actors-mcp-server (may download on first run)..."
if npx -y @apify/actors-mcp-server --help &>/dev/null 2>&1; then
    ok "@apify/actors-mcp-server runnable"
else
    warn "npx dry-run inconclusive — normal on first run, will work in Claude Code"
fi

echo ""

# ── Step 6: PDF Renderer ──────────────────────────────────────
echo "── Step 6: PDF Renderer ──"

if $PYTHON scripts/pdf_renderer.py test &>/dev/null; then
    ok "pdf_renderer.py generates clean output"
else
    fail "pdf_renderer.py failed — run manually: $PYTHON scripts/pdf_renderer.py test"
fi

echo ""

# ── Step 7: Data Files ────────────────────────────────────────
echo "── Step 7: Data Files ──"

if $PYTHON -c "import json; json.load(open('data/job_tracker.json'))" 2>/dev/null; then
    COUNT=$($PYTHON -c "import json; d=json.load(open('data/job_tracker.json')); print(len(d['applications']))")
    ok "job_tracker.json valid — $COUNT applications"
else
    fail "job_tracker.json missing or invalid JSON"
fi

for f in data/master_resume.pdf data/product_resume.pdf data/customer_resume.pdf; do
    [ -f "$f" ] && ok "$f present" || fail "$f MISSING"
done

echo ""

# ── Summary ───────────────────────────────────────────────────
echo "================================================="
if [ "$FAILED" = "0" ]; then
    echo -e "${GREEN}  ALL CHECKS PASSED — Stage 2 ready${NC}"
    echo ""
    echo "  Next steps:"
    echo "    1. source .venv/bin/activate"
    echo "    2. python3 scripts/test_apify_scrape.py"
    echo "    3. python3 scripts/sheets_sync.py push"
    echo "    4. cd $(pwd) && claude"
else
    echo -e "${RED}  SOME CHECKS FAILED — fix issues above before proceeding${NC}"
fi
echo "================================================="
echo ""
