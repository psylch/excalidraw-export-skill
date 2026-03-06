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

# 2. Check/install fonttools + brotli (for text-to-path font extraction)
echo
echo "Checking Python packages (fonttools + brotli)..."
NEED_PIP=0
if python3 -c "from fontTools.pens.svgPathPen import SVGPathPen" 2>/dev/null; then
    ok "fonttools is installed"
else
    warn "fonttools not found"
    NEED_PIP=1
fi
if python3 -c "import brotli" 2>/dev/null; then
    ok "brotli is installed"
else
    warn "brotli not found (needed for woff2 decompression)"
    NEED_PIP=1
fi
if [ "$NEED_PIP" -eq 1 ]; then
    echo "  Installing fonttools + brotli..."
    if pip3 install fonttools brotli 2>/dev/null; then
        ok "fonttools + brotli installed"
    else
        warn "Could not auto-install. Run: pip install fonttools brotli"
    fi
fi

# 3. Check/install resvg (SVG-to-PNG rasterizer)
echo
echo "Checking resvg..."
if command -v resvg &>/dev/null; then
    ok "resvg is installed (recommended PNG backend)"
else
    warn "resvg not found"
    echo "  Installing resvg via Homebrew..."
    if command -v brew &>/dev/null && brew install resvg 2>/dev/null; then
        ok "resvg installed successfully"
    else
        warn "Could not auto-install resvg. Run: brew install resvg"
    fi
fi

# 4. Check Chrome (optional fallback)
echo
echo "Checking Chrome (optional fallback)..."
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] || command -v google-chrome &>/dev/null; then
    ok "Google Chrome found (optional fallback)"
else
    echo "  Not found. This is optional — resvg + fonttools is the primary backend."
fi

# 5. Test kroki.io connectivity
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
