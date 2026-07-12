#!/usr/bin/env bash
# Start collector, API, and dashboard in the background.
# Run from project root: ./scripts/start.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv — run: python3 -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

mkdir -p logs

if [[ -f logs/pids.txt ]]; then
  echo "Services may already be running. Stop them first: ./scripts/stop.sh"
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

echo "Starting dashboard..."
(
  cd dashboard
  npm run dev
) > logs/dashboard.log 2>&1 &
DASH_PID=$!

echo "$COLLECTOR_PID $API_PID $DASH_PID" > logs/pids.txt

echo ""
echo "All services started."
echo "  Collector PID: $COLLECTOR_PID"
echo "  API PID:       $API_PID"
echo "  Dashboard PID: $DASH_PID"
echo ""
echo "Logs:"
echo "  tail -f logs/collector.log"
echo "  tail -f logs/api.log"
echo "  tail -f logs/dashboard.log"
echo ""
echo "Stop everything: ./scripts/stop.sh"
