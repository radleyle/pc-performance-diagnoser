# PC Performance Diagnoser

Monitor your computer's CPU and memory in real time, detect performance problems with rule-based checks, and get plain-English explanations from a local AI.

**The key idea:** code detects issues from real OS metrics. The LLM only explains what was already found — it does not guess.

```
Collector → SQLite → Detection engine → FastAPI → Dashboard + Ollama
```

---

## Features

- **Live metrics** — CPU %, available RAM, and top processes collected every 5 seconds
- **Time-series storage** — metrics saved locally in SQLite for charts and trend detection
- **Rule-based alerts** — flags low RAM, memory hogs, rapid memory drops, and sustained high CPU
- **REST API** — FastAPI endpoints for metrics, processes, diagnosis, and AI analysis
- **Web dashboard** — live charts, process table, alerts, and an **Analyze** button
- **Local AI** — uses [Ollama](https://ollama.com) to explain results (no API key required)

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

You need **three terminals** (plus Ollama running in the background).

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

1. **Charts** — CPU % (blue) and available RAM in MB (green) over the last hour. Refreshes every 5 seconds.
2. **Alerts** — shows `ok`, `warning`, or `critical` based on detection rules. Lists active issues when found.
3. **Top processes** — memory and CPU usage for the heaviest processes from the latest snapshot.
4. **Analyze now** — runs detection, sends the JSON result to Ollama, and displays a plain-English summary. The first call may take 10–30 seconds.

> **Tip:** If charts are empty, make sure the collector has been running for a few minutes so data accumulates.

---

## API reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API health check |
| `/metrics` | GET | CPU/RAM time-series (`?minutes=60`, max 10080) |
| `/processes` | GET | Top processes from the latest snapshot |
| `/diagnose` | POST | Run detection engine, return JSON issues |
| `/analyze` | POST | Run detection + Ollama explanation |

**Examples:**

```bash
curl http://127.0.0.1:8000/health

curl "http://127.0.0.1:8000/metrics?minutes=60"

curl -X POST http://127.0.0.1:8000/diagnose

curl -X POST http://127.0.0.1:8000/analyze
```

---

## Detection rules

Rule-based checks only — no machine learning.

| Issue | Condition | Severity |
|-------|-----------|----------|
| RAM critical | Available RAM < 500 MB | High |
| RAM warning | Available RAM < 1 GB or used > 90% | Medium |
| Process memory hog | Single process > 1 GB RSS | Medium |
| Memory overflow | Available RAM dropped > 50% in 60s | High |
| High CPU | CPU > 90% for 3 consecutive samples (~15s) | Medium |

Example diagnosis JSON:

```json
{
  "status": "critical",
  "issues": [
    {
      "type": "ram_critical",
      "severity": "high",
      "message": "Only 280 MB RAM available",
      "evidence": { "ram_available_mb": 280, "ram_used_percent": 96.2 }
    }
  ],
  "top_processes": [
    { "name": "Google Chrome", "memory_mb": 2100 }
  ]
}
```

---

## Data storage

Metrics are stored in a local SQLite database:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/PCDiagnoser/data.db` |
| Windows | `%LOCALAPPDATA%/PCDiagnoser/data.db` |
| Linux | `~/.local/share/PCDiagnoser/data.db` |

**Tables:** `metrics`, `process_snapshots`, `diagnoses`

Check how much data has been collected:

```bash
python scripts/check_data.py
```

---

## Utility scripts

| Script | Purpose |
|--------|---------|
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

16 unit tests cover each detection rule (RAM, process hogs, memory overflow, high CPU, and status logic).

---

## Project structure

```
pc-performance-diagnoser/
├── collector/
│   ├── main.py          # Background loop: OS → SQLite every 5s
│   ├── collect.py       # psutil collection logic
│   └── db.py            # SQLite helpers
├── engine/
│   ├── detect.py        # Rule-based detection
│   ├── schemas.py       # Pydantic models for diagnosis JSON
│   └── llm.py           # Ollama integration
├── api/
│   ├── main.py          # FastAPI app + CORS
│   └── routes.py        # HTTP endpoints
├── dashboard/
│   └── src/
│       ├── App.tsx              # Main layout + auto-refresh
│       ├── MetricsChart.tsx     # CPU/RAM charts (Recharts)
│       ├── AlertsPanel.tsx      # Active issues
│       ├── ProcessTable.tsx     # Top processes
│       ├── AnalyzePanel.tsx     # AI explanation button
│       └── api.ts               # API client
├── scripts/             # Utility and test scripts
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
| `/analyze` returns 503 | Start Ollama (`ollama serve` or open the Ollama app) |
| `model not found` | Run `ollama pull llama3.2` |
| Uvicorn keeps reloading | Use `--reload-dir` flags (see Running the app) to avoid watching `.venv` |
| Alerts always `ok` with old data | Detection uses the last 60 minutes of metrics — restart the collector |

---

## Tech stack

| Layer | Tool |
|-------|------|
| Metrics collection | Python + psutil |
| Storage | SQLite |
| Detection | Python (threshold rules) |
| API | FastAPI + Uvicorn |
| Dashboard | React + TypeScript + Recharts |
| AI explanations | Ollama (llama3.2) |
| Tests | pytest |

---

## License

MIT

## Author

**Nguyen Le**
