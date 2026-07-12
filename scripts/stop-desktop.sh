#!/usr/bin/env bash
# Stop collector and API started by scripts/start-desktop.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/logs/desktop-pids.txt"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No logs/desktop-pids.txt found — background services not running."
  exit 0
fi

read -r COLLECTOR_PID API_PID < "$PID_FILE"

for name_pid in "Collector:$COLLECTOR_PID" "API:$API_PID"; do
  name="${name_pid%%:*}"
  pid="${name_pid##*:}"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped $name (PID $pid)"
  else
    echo "$name not running (PID $pid)"
  fi
done

rm -f "$PID_FILE"
echo "Done."
