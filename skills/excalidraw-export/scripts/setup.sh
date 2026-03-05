#!/usr/bin/env bash
# Setup script for excalidraw-export skill
# Checks prerequisites and installs missing dependencies

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "=== excalidraw-export setup ==="
echo

# 1. Check Python 3
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    ok "Python 3 found: $PY_VER"
else
    fail "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# 2. Check/install SVG->PNG backend
echo
echo "Checking SVG-to-PNG backend..."
if command -v resvg &>/dev/null; then
    ok "resvg is installed (recommended, best CJK support)"
elif command -v rsvg-convert &>/dev/null; then
    ok "rsvg-convert is available (via librsvg)"
elif python3 -c "import cairosvg" 2>/dev/null; then
    ok "cairosvg is installed (note: may have issues with embedded woff2 fonts)"
else
    warn "No SVG-to-PNG backend found"
    echo "  Installing resvg via Homebrew..."
    if command -v brew &>/dev/null && brew install resvg 2>/dev/null; then
        ok "resvg installed successfully"
    else
        warn "Could not auto-install resvg"
        echo "  Please install manually (pick one):"
        echo "    brew install resvg         (recommended, best CJK support)"
        echo "    brew install librsvg       (rsvg-convert)"
        echo "    pip install cairosvg       (may have font issues)"
        echo
        echo "  SVG output will still work, but PNG export requires one of these."
    fi
fi

# 3. Test kroki.io connectivity
echo
echo "Testing kroki.io connectivity..."
if python3 -c "
import urllib.request
req = urllib.request.Request('https://kroki.io/health', headers={'User-Agent': 'excalidraw-export-skill/1.0'})
urllib.request.urlopen(req, timeout=10)
" 2>/dev/null; then
    ok "kroki.io is reachable"
else
    warn "Cannot reach kroki.io - check internet connection"
    echo "  The skill requires internet access to render diagrams."
fi

echo
echo "=== Setup complete ==="
