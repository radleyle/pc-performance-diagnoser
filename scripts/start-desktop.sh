#!/usr/bin/env bash
# Start collector, API, and the native desktop app.
# Run from project root: ./scripts/start-desktop.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv — run: python3 -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "Rust is required for the desktop app."
  echo "Install from https://rustup.rs then run this script again."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

mkdir -p logs

if [[ -f logs/desktop-pids.txt ]]; then
  echo "Background services may already be running. Stop them first: ./scripts/stop-desktop.sh"
  exit 1
fi

echo "Starting collector..."
python -m collector.main > logs/collector.log 2>&1 &
COLLECTOR_PID=$!

echo "Starting API..."
uvicorn api.main:app \
  --reload \
  --reload-dir api \
  --reload-dir collector \
  --reload-dir engine \
  > logs/api.log 2>&1 &
API_PID=$!

echo "$COLLECTOR_PID $API_PID" > logs/desktop-pids.txt

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti :"$port" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Port $port in use — stopping leftover process for desktop dev..."
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

# Desktop dev server (browser dev can keep using 5173)
free_port 1420

echo ""
echo "Collector and API started in the background."
echo "Launching desktop app (first run may compile Rust for a few minutes)..."
echo ""

cleanup() {
  echo ""
  echo "Stopping background services..."
  kill "$COLLECTOR_PID" "$API_PID" 2>/dev/null || true
  rm -f logs/desktop-pids.txt
}

trap cleanup EXIT INT TERM

(
  cd dashboard
  npm run desktop
)
