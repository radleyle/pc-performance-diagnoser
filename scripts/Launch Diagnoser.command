#!/usr/bin/env bash
# Double-click launcher for macOS Finder.
# Starts collector, API, and the desktop window.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d ".venv" ]]; then
  osascript -e 'display alert "PC Performance Diagnoser needs setup first." message "Open Terminal in the project folder and run: ./scripts/install.sh"'
  exit 1
fi

exec "$ROOT/scripts/start-desktop.sh"
