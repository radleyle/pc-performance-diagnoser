# PC Performance Diagnoser

Monitor your computer's CPU, memory, and disk in real time, detect performance problems with rule-based checks, and get plain-English explanations from a local AI.

**The key idea:** code detects issues from real OS metrics. The LLM only explains what was already found — it does not guess.

```
Collector → SQLite → Detection engine → FastAPI → Dashboard + Ollama
```

---

## Features

### Core (v1.0)
- **Live metrics** — CPU %, available RAM, and top processes collected every 5 seconds
- **Time-series storage** — metrics saved locally in SQLite for charts and trend detection
- **Rule-based alerts** — flags low RAM, memory hogs, rapid memory drops, and sustained high CPU
- **REST API** — FastAPI endpoints for metrics, processes, diagnosis, and AI analysis
- **Web dashboard** — live charts, process table, alerts, and an **Analyze** button
- **Local AI** — uses [Ollama](https://ollama.com) to explain results (no API key required)

### v1.1
- **Service health panel** — collector and Ollama status at a glance
- **Diagnosis history** — past AI analyses with timestamps
- **Process grouping** — Chrome helpers, Cursor renderers, etc. rolled up by app
- **Two-column layout** — chart on the left, panels on the right
- **Chart time ranges** — 15m / 1h / 6h buttons
- **Disk space** — free GB, usage %, bar chart, and low-disk alerts

### v1.2
- **Configurable thresholds** — edit `config.yaml` instead of Python constants
- **Data retention** — auto-purges snapshots older than 7 days (configurable)
- **Disk on chart** — orange disk-used % line alongside CPU and RAM
- **What changed?** — compares now vs 1 hour ago (CPU, RAM, disk, top process)
- **Export report** — download JSON snapshot of diagnosis + comparison
- **Desktop notifications** — browser alerts when status goes critical
- **One-command startup** — `./scripts/start.sh` launches all three services

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Collector, API, detection engine |
| Node.js | 20+ | React dashboard |
| Ollama | latest | Local LLM for `/analyze` (optional but needed for AI button) |

**Supported OS:** macOS, Windows, and Linux (via `psutil`).

---

## Installation

### 1. Clone and set up Python

```bash
git clone https://github.com/radleyle/pc-performance-diagnoser.git
cd pc-performance-diagnoser

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Ollama (for AI explanations)

Install from [ollama.com](https://ollama.com), then pull the default model:

```bash
ollama pull llama3.2
```

Verify Ollama is running:

```bash
ollama list
```

### 3. Set up the dashboard

```bash
cd dashboard
npm install
cd ..
```

---

## Running the app

### Option A — one command (macOS/Linux)

```bash
source .venv/bin/activate
./scripts/start.sh
```

Stop everything:

```bash
./scripts/stop.sh
```

Logs are written to `logs/`. The dashboard URL appears in `logs/dashboard.log` (usually `http://localhost:5173`).

### Option B — three terminals

**Terminal 1 — Collector** (gathers metrics every 5 seconds):

```bash
source .venv/bin/activate
python -m collector.main
```

**Terminal 2 — API** (serves data on port 8000):

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --reload-dir api --reload-dir collector --reload-dir engine
```

**Terminal 3 — Dashboard** (web UI on port 5173 or 5174):

```bash
cd dashboard
npm run dev
```

Open the URL shown in the terminal (usually `http://localhost:5173`).

| Service | URL |
|---------|-----|
| Dashboard | `http://localhost:5173` |
| API | `http://127.0.0.1:8000` |
| API docs (Swagger) | `http://127.0.0.1:8000/docs` |
| Ollama | `http://127.0.0.1:11434` |

---

## Using the dashboard

1. **Charts** — CPU % (blue), available RAM in MB (green), disk used % (orange). Use 15m / 1h / 6h buttons to change the window. Refreshes every 5 seconds.
2. **Disk space** — free GB and usage bar with color-coded status.
3. **What changed?** — compares current metrics to ~1 hour ago (needs collector history).
4. **Alerts** — shows `ok`, `warning`, or `critical` based on detection rules.
5. **AI analysis** — runs detection, then asks Ollama for a plain-English summary.
6. **Export report** — downloads a JSON file with diagnosis, comparison, and top processes.
7. **Top processes** — grouped by app (Chrome, Cursor, etc.) with memory and CPU.
8. **Diagnosis history** — past AI analyses.
9. **Desktop alerts** — toggle in the header; browser notifies you when status goes critical.

> **Tip:** If charts are empty, make sure the collector has been running for a few minutes so data accumulates.

---

## Configuration

Edit `config.yaml` at the project root to tune collection and alert thresholds:

```yaml
collector:
  interval_seconds: 5
  retention_days: 7
  cleanup_every_cycles: 720

thresholds:
  ram_critical_mb: 500
  ram_warning_mb: 1024
  disk_critical_free_gb: 2.0
  disk_warning_free_gb: 10.0
  # ... see config.yaml for all options
```

Restart the collector after changing config.

---

## API reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API, collector, and Ollama status |
| `/metrics` | GET | CPU/RAM/disk time-series (`?minutes=60`, max 10080) |
| `/processes` | GET | Top processes (`?grouped=true` default) |
| `/summary` | GET | Now vs N minutes ago (`?minutes_ago=60`) |
| `/report` | GET | Full export: diagnosis + comparison + processes |
| `/diagnoses` | GET | Past AI analyses (`?limit=20`) |
| `/diagnose` | POST | Run detection engine, return JSON issues |
| `/analyze` | POST | Run detection + Ollama explanation |

**Examples:**

```bash
curl http://127.0.0.1:8000/health

curl "http://127.0.0.1:8000/metrics?minutes=60"

curl "http://127.0.0.1:8000/summary?minutes_ago=60"

curl http://127.0.0.1:8000/report -o report.json

curl -X POST http://127.0.0.1:8000/diagnose

curl -X POST http://127.0.0.1:8000/analyze
```

---

## Detection rules

Rule-based checks only — no machine learning. Thresholds are configurable in `config.yaml`.

| Issue | Condition | Severity |
|-------|-----------|----------|
| RAM critical | Available RAM < 500 MB | High |
| RAM warning | Available RAM < 1 GB or used > 90% | Medium |
| Process memory hog | Single process > 1 GB RSS | Medium |
| Memory overflow | Available RAM dropped > 50% in 60s | High |
| High CPU | CPU > 90% for 3 consecutive samples (~15s) | Medium |
| Disk critical | Free disk < 2 GB | High |
| Disk warning | Free disk < 10 GB or used > 90% | Medium |

---

## Data storage

Metrics are stored in a local SQLite database:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/PCDiagnoser/data.db` |
| Windows | `%LOCALAPPDATA%/PCDiagnoser/data.db` |
| Linux | `~/.local/share/PCDiagnoser/data.db` |

**Tables:** `metrics`, `process_snapshots`, `diagnoses`

Rows older than `retention_days` (default 7) are purged automatically by the collector.

Check how much data has been collected:

```bash
python scripts/check_data.py
```

---

## Utility scripts

| Script | Purpose |
|--------|---------|
| `scripts/start.sh` | Start collector + API + dashboard in background |
| `scripts/stop.sh` | Stop services started by `start.sh` |
| `scripts/check_data.py` | Show row counts and time span in SQLite |
| `scripts/collect_once.py` | Run one collection cycle and print results |
| `scripts/test_diagnose.py` | Run the detection engine against stored data |
| `scripts/test_psutil.py` | Quick check that OS metrics can be read |

---

## Running tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

21 unit tests cover each detection rule (RAM, disk, process hogs, memory overflow, high CPU, and status logic).

---

## Project structure

```
pc-performance-diagnoser/
├── config.yaml          # Thresholds and retention settings
├── collector/
│   ├── main.py          # Background loop: OS → SQLite every 5s
│   ├── collect.py       # psutil collection logic
│   ├── db.py            # SQLite helpers + retention purge
│   └── process_groups.py
├── engine/
│   ├── config.py        # Load config.yaml
│   ├── detect.py        # Rule-based detection
│   ├── summary.py       # Now-vs-then comparison
│   ├── schemas.py       # Pydantic models
│   └── llm.py           # Ollama integration
├── api/
│   ├── main.py          # FastAPI app + CORS
│   ├── routes.py        # HTTP endpoints
│   └── system_status.py
├── dashboard/
│   └── src/
│       ├── App.tsx              # Main layout + auto-refresh
│       ├── MetricsChart.tsx     # CPU/RAM/disk charts
│       ├── DiskPanel.tsx        # Disk space bar
│       ├── WhatChangedPanel.tsx # 1h comparison
│       ├── ExportPanel.tsx      # JSON report download
│       ├── AlertsPanel.tsx      # Active issues
│       ├── ProcessTable.tsx     # Top processes
│       ├── AnalyzePanel.tsx     # AI explanation button
│       ├── ServiceStatus.tsx    # Collector/Ollama health
│       ├── DiagnosisHistory.tsx # Past analyses
│       └── api.ts               # API client
├── scripts/             # Utility and startup scripts
├── tests/               # pytest unit tests
└── requirements.txt
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dashboard shows "Failed to fetch" | Make sure uvicorn is running on port 8000 |
| CORS error in browser console | Restart the API after editing `api/main.py` |
| Charts empty | Run `python -m collector.main` for a few minutes |
| Disk panel empty | Restart collector after upgrading — old rows lack disk columns |
| "What changed?" needs history | Leave collector running for at least 1 hour |
| `/analyze` returns 503 | Start Ollama (`ollama serve` or open the Ollama app) |
| `model not found` | Run `ollama pull llama3.2` |
| Uvicorn keeps reloading | Use `--reload-dir` flags (see Running the app) |
| Alerts always `ok` with old data | Detection uses the last 60 minutes — restart the collector |
| No desktop notifications | Allow notifications in browser settings; toggle is in the header |

---

## Tech stack

| Layer | Tool |
|-------|------|
| Metrics collection | Python + psutil |
| Storage | SQLite |
| Detection | Python (threshold rules) |
| Configuration | YAML |
| API | FastAPI + Uvicorn |
| Dashboard | React + TypeScript + Recharts |
| AI explanations | Ollama (llama3.2) |
| Tests | pytest |

---

## License

MIT

## Author

**Nguyen Le**
