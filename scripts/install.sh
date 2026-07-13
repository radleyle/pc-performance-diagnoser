#!/usr/bin/env bash
# One-time setup for PC Performance Diagnoser.
# Run from anywhere: ./scripts/install.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== PC Performance Diagnoser — install ==="
echo "Project: $ROOT"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.12+ and retry."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required. Install Node 20+ and retry."
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Installing dashboard dependencies..."
(
  cd dashboard
  npm install
)

if command -v cargo >/dev/null 2>&1; then
  echo "Rust found — desktop app ready."
else
  echo ""
  echo "Rust not found. Browser mode works; for the desktop app install Rust:"
  echo "  https://rustup.rs"
fi

mkdir -p logs

echo ""
echo "=== Install complete ==="
echo ""
echo "Launch the app:"
echo "  ./scripts/start-desktop.sh"
echo ""
echo "Or open the macOS launcher:"
echo "  open scripts/Launch\\ Diagnoser.command"
echo ""
