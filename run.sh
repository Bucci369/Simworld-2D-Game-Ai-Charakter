#!/usr/bin/env bash
set -euo pipefail

PY311="/opt/homebrew/opt/python@3.11/bin/python3.11"
if ! [ -x "$PY311" ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PY311=$(command -v python3.11)
  else
    echo "[run.sh] Python 3.11 nicht gefunden (brew install python@3.11)" >&2
    exit 1
  fi
fi

recreate=false
if [ -d .venv ]; then
  if [ -x .venv/bin/python ]; then
    ver=$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' || echo '?')
    [ "$ver" != "3.11" ] && recreate=true
  else
    recreate=true
  fi
else
  recreate=true
fi

if [ "$recreate" = true ]; then
  echo "[run.sh] Erstelle/Erneuere venv mit $PY311"
  rm -rf .venv
  "$PY311" -m venv .venv
fi

source .venv/bin/activate

if ! python -c 'import pygame' 2>/dev/null; then
  echo "[run.sh] Installiere Dependencies"
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  python -m pip install -r requirements.txt
fi

exec python src/main.py "$@"
