#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON:-python3}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  printf 'Python executable not found: %s\n' "$PYTHON_BIN" >&2
  exit 1
fi
if ! command -v tesseract >/dev/null 2>&1; then
  printf 'Tesseract OCR is required. Install it and ensure it is on PATH.\n' >&2
  exit 1
fi

"$PYTHON_BIN" -m compileall -q main.py src tests examples
"$PYTHON_BIN" -m pytest -q
"$PYTHON_BIN" examples/run_synthetic_demo.py
"$PYTHON_BIN" -m bandit -q -r src -ll

printf '\nAll local verification checks passed.\n'
