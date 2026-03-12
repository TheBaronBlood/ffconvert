#!/usr/bin/env bash
# FFConvert Installer — Linux & macOS
# Verwendung: curl -sSL https://DEINE-URL/install.sh | bash

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${BLUE}[→]${NC} $1"; }
ok()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

INSTALL_DIR="$HOME/.local/share/ffconvert"
BIN_DIR="$HOME/.local/bin"
SCRIPT_URL="https://DEINE-URL/ffconvert.py"   # ← hier deine URL eintragen

echo -e "${BOLD}"
echo "  ███████╗███████╗ ██████╗ ██████╗ ███╗   ██╗██╗   ██╗"
echo "  ██╔════╝██╔════╝██╔════╝██╔═══██╗████╗  ██║██║   ██║"
echo "  █████╗  █████╗  ██║     ██║   ██║██╔██╗ ██║██║   ██║"
echo "  ██╔══╝  ██╔══╝  ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝"
echo "  ██║     ██║     ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝ "
echo "  ╚═╝     ╚═╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  v1.0"
echo -e "${NC}"
echo -e "  FFmpeg Terminal Converter — Installer"
echo ""

# ── Python prüfen ─────────────────────────────────────────────────────────────
info "Prüfe Python 3 ..."
if command -v python3 &>/dev/null; then
    PY=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    MAJOR=$(echo "$PY" | cut -d. -f1)
    MINOR=$(echo "$PY" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
        ok "Python $PY gefunden"
        PYTHON=python3
    else
        err "Python 3.8+ erforderlich (gefunden: $PY)"
    fi
else
    err "Python 3 nicht gefunden. Bitte installieren: https://python.org"
fi

# ── ffmpeg prüfen ─────────────────────────────────────────────────────────────
info "Prüfe ffmpeg ..."
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg gefunden"
else
    warn "ffmpeg nicht gefunden – versuche automatische Installation ..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v brew &>/dev/null; then
        brew install ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm ffmpeg
    else
        err "Konnte ffmpeg nicht installieren. Bitte manuell installieren."
    fi
    ok "ffmpeg installiert"
fi

# ── Textual installieren ───────────────────────────────────────────────────────
info "Installiere Textual (TUI Framework) ..."
$PYTHON -m pip install textual --quiet --upgrade
ok "Textual installiert"

# ── Dateien kopieren ──────────────────────────────────────────────────────────
info "Installiere FFConvert nach $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Lokal oder remote laden
if [ -f "./ffconvert.py" ]; then
    cp ./ffconvert.py "$INSTALL_DIR/ffconvert.py"
else
    curl -sSL "$SCRIPT_URL" -o "$INSTALL_DIR/ffconvert.py"
fi
ok "Programm installiert"

# ── Launcher erstellen ────────────────────────────────────────────────────────
info "Erstelle Launcher ..."
cat > "$BIN_DIR/ffconvert" << EOF
#!/usr/bin/env bash
exec $PYTHON "$INSTALL_DIR/ffconvert.py" "\$@"
EOF
chmod +x "$BIN_DIR/ffconvert"

# ── PATH prüfen ───────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR ist nicht im PATH"
    SHELL_RC="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
    echo "" >> "$SHELL_RC"
    echo "# FFConvert" >> "$SHELL_RC"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    warn "PATH zu $SHELL_RC hinzugefügt — bitte Terminal neu starten oder:"
    echo -e "  ${BOLD}source $SHELL_RC${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Installation abgeschlossen!${NC}"
echo ""
echo -e "  Starten mit:  ${BOLD}ffconvert${NC}"
echo "  Oder direkt:  python3 $INSTALL_DIR/ffconvert.py"
echo ""
