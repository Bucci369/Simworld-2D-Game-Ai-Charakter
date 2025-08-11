#!/usr/bin/env bash
# Doppelklick-Starter für das Spiel (erzwingt Python 3.11 im virtuellen Env)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo -e "${GREEN}[StartGame] Starte Spiel...${NC}"

# Finde Python 3.11
PY311="/opt/homebrew/opt/python@3.11/bin/python3.11"
if ! [ -x "$PY311" ]; then
  # Fallback versuchen
  if command -v python3.11 >/dev/null 2>&1; then
    PY311="$(command -v python3.11)"
  else
    echo -e "${RED}[StartGame] Python 3.11 nicht gefunden. Bitte installieren: brew install python@3.11${NC}" >&2
    read -r -p "[Enter zum Beenden]" _
    exit 1
  fi
fi

recreate_venv=false
if [ -d .venv ]; then
  # Prüfe Version der bestehenden venv
  if [ -x .venv/bin/python ]; then
    VENV_VER=$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' || echo "?")
    if [ "$VENV_VER" != "3.11" ]; then
      echo -e "${YELLOW}[StartGame] Existierende venv benutzt Python $VENV_VER -> wird erneuert mit 3.11${NC}"
      rm -rf .venv
      recreate_venv=true
    fi
  else
    recreate_venv=true
  fi
else
  recreate_venv=true
fi

if [ "$recreate_venv" = true ]; then
  echo "[StartGame] Erstelle virtuelle Umgebung mit $PY311"
  "$PY311" -m venv .venv
fi

source .venv/bin/activate

# Sicherstellen, dass 'python' jetzt 3.11 ist
CUR_VER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$CUR_VER" != "3.11" ]; then
  echo -e "${RED}[StartGame] Unerwartete Interpreter-Version ($CUR_VER) in venv. Abbruch.${NC}" >&2
  exit 1
fi

# Dependencies falls pygame fehlt
if ! python -c 'import pygame' 2>/dev/null; then
  echo "[StartGame] Installiere Abhängigkeiten..."
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  python -m pip install -r requirements.txt
else
  echo "[StartGame] pygame bereits installiert."
fi

exec python src/main.py "$@"
