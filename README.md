# PC Performance Diagnoser

Monitor your computer's CPU, memory, and disk in real time, detect performance problems with rule-based checks, and get plain-English explanations from a local AI.

**The key idea:** code detects issues from real OS metrics. The LLM only explains what was already found — it does not guess.

```
Collector → SQLite → Detection engine → FastAPI → Desktop app (or browser) + Ollama
```

---

## Quick start (returning users)

**First time on this machine?** Run once:

```bash
./scripts/install.sh
```

Then launch:

```bash
source .venv/bin/activate
./scripts/start-desktop.sh
```

Or double-click **`scripts/Launch Diagnoser.command`** in Finder.

This starts the collector and API in the background and opens the **native desktop window**. The desktop app remembers your project folder and can auto-start the backend on future launches.

When you're done:

```bash
./scripts/stop-desktop.sh
```

Close the desktop window with the normal macOS close button (or Ctrl+C in the terminal that launched it).

---

## First-time setup

Follow these steps once on a new machine.

### Step 1 — Install prerequisites

| Tool | Version | Required? | Purpose |
|------|---------|-----------|---------|
| Python | 3.12+ | Yes | Collector, API, detection engine |
| Node.js | 20+ | Yes | Dashboard / desktop UI |
| Rust | 1.77+ | For desktop app | Native window (`rustup.rs`) |
| Ollama | latest | Optional | AI explanations (Smart Scan) |

**Supported OS:** macOS, Windows, and Linux for the collector and API. The native desktop app is currently set up for **macOS**.

### Step 2 — Clone the project

```bash
git clone https://github.com/radleyle/pc-performance-diagnoser.git
cd pc-performance-diagnoser
```

### Step 3 — One-command install

From the project root:

```bash
./scripts/install.sh
```

This creates `.venv`, installs Python + npm dependencies, and prepares the desktop app.

Or set up manually:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4 — Set up the dashboard

```bash
cd dashboard
npm install
cd ..
```

### Step 5 — Install Rust (desktop app only)

Skip this if you only want the browser version.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Restart your terminal, then verify:

```bash
cargo --version
```

### Step 6 — Set up Ollama (optional, for Smart Scan)

1. Install from [ollama.com](https://ollama.com)
2. Pull the default model:

```bash
ollama pull llama3.2
```

3. Verify Ollama is running:

```bash
ollama list
```

---

## How to launch the app

### Recommended — native desktop app (macOS)

**What you get:** a real app window, native notifications, sidebar navigation, light/dark mode.

**One command** (from project root):

```bash
source .venv/bin/activate
./scripts/start-desktop.sh
```

What happens:

1. **Collector** starts in the background — reads CPU, RAM, disk, and processes every 5 seconds
2. **API** starts in the background — serves data on port 8000
3. **Desktop window** opens — your main UI

> **First launch** compiles Rust and can take 1–2 minutes. Later launches are much faster.

**Stop background services** when finished:

```bash
./scripts/stop-desktop.sh
```

**Logs** (if something goes wrong):

```bash
tail -f logs/collector.log
tail -f logs/api.log
```

---

### Alternative — browser dashboard

Use this if you don't have Rust installed, or prefer developing in a browser tab.

**One command:**

```bash
source .venv/bin/activate
./scripts/start.sh
```

Open `http://localhost:5173` in your browser. Stop with `./scripts/stop.sh`.

**Manual (three terminals)** — useful for debugging:

| Terminal | Command |
|----------|---------|
| 1 — Collector | `python -m collector.main` |
| 2 — API | `uvicorn api.main:app --reload --reload-dir api --reload-dir collector --reload-dir engine` |
| 3 — Dashboard | `cd dashboard && npm run dev` |

Then open `http://localhost:5173`.

---

### Installable macOS app (optional)

Build a `.app` you can drag to Applications:

```bash
cd dashboard
npm run desktop:build
```

Output:

```
dashboard/src-tauri/target/release/bundle/macos/PC Performance Diagnoser.app
```

> The `.app` can **auto-start** the collector and API when launched from the project directory (or when `PCDIAGNOSER_ROOT` points at the repo). If you copy the `.app` elsewhere without the Python backend, use `./scripts/start-desktop.sh` first or start services manually.

---

## How to use the product

Once the app is open, the UI refreshes every **5 seconds** automatically.

### Check that everything is connected

At the top of the window, look for green status dots:

| Indicator | Meaning |
|-----------|---------|
| **API** | API server is reachable |
| **Collector** | Metrics are being saved (shows seconds since last snapshot) |
| **Ollama** | AI is available for Smart Scan |
| **Live · 5s** | Dashboard is auto-refreshing |

If you see **API error** or **Failed to fetch**, the API is not running — restart with `./scripts/start-desktop.sh`.

---

### Sidebar tabs

Use the left sidebar to switch views:

#### Overview (home screen)

Your main health dashboard.

1. **System status hero** — big green/yellow/red indicator with headline ("Your system looks healthy", etc.) and live CPU, RAM, and disk numbers
2. **Alerts** — current `ok` / `warning` / `critical` status and any active issues
3. **Smart Scan** — click **Run smart scan** to run detection + ask Ollama for a plain-English explanation (10–30 seconds). When done, you're taken to History automatically
4. **Disk** — disk free space with a ring gauge and usage bar (overview)
5. **What changed** — compares now vs 1 hour ago (needs ~1 hour of collector history)
6. **Export** — download a JSON report of diagnosis, comparison, and top processes

Panels like Storage, What changed, and Export can be **collapsed** — click the panel header to fold them away.

#### Performance

Full-width chart showing CPU % (blue), available RAM (green), and disk used % (orange) over time. Use **15m / 1h / 6h** buttons to change the time window.

> Charts need a few minutes of collector data before they look meaningful.

#### Storage

Deep disk management in one place:

1. **Folder breakdown** — sizes of top-level folders (cached; **Rescan** for fresh data)
2. **Large files** — adjustable threshold (250 MB–2 GB), **Show in Finder**, cached results
3. **Safe cleanup** — preview Trash and caches, confirm twice (including typing `DELETE`)
4. **Startup items** — read-only list of macOS LaunchAgents that run at login

> Scans are cached for 1 hour. Cached results load instantly; use **Rescan** when you need fresh numbers.

#### Processes

Live running processes with PID, memory, and CPU. Use **Stop** to terminate a process (confirmation required). Refreshes every 5 seconds.

#### History

Past Smart Scan results with timestamps, status badges, and AI explanations.

---

### Settings in the header

| Control | What it does |
|---------|--------------|
| **Alerts** dropdown | **Warnings + critical** (default), **Critical only**, or **Off** — native notifications when status worsens |
| **Light mode** (sidebar footer) | Toggle light/dark theme — aurora blue/green palette (saved automatically) |

If the API is not running, a **setup banner** appears with install/launch steps and a **Retry connection** button.

### Menu bar tray (desktop)

When running the Tauri app, a **tray icon** stays in the macOS menu bar. Click it to reopen the window, or use the menu for **Open Diagnoser** / **Quit**. Closing the window stops the auto-started collector and API.

---

### Typical daily workflow

```
1. ./scripts/start-desktop.sh
2. Glance at Overview — is status green?
3. Check Alerts if yellow/red
4. Open Performance tab if you want to see trends
5. Run Smart Scan if you want an AI explanation
6. Close the window when done
7. ./scripts/stop-desktop.sh
```

---

### What runs behind the scenes

You do **not** need to interact with these directly, but it helps to know:

| Component | What it does | Port |
|-----------|--------------|------|
| Collector | Reads OS metrics every 5s, saves to SQLite | — |
| API | Serves metrics, alerts, and AI endpoint | 8000 |
| Desktop / browser | Displays the UI | 1420 (desktop dev) or 5173 (browser) |
| Ollama | Local LLM for Smart Scan | 11434 |

```
┌─────────────┐     ┌────────┐     ┌─────────────┐     ┌──────────────┐
│  Collector  │────▶│ SQLite │◀────│     API     │◀────│ Desktop app  │
│  (Python)   │     │  local │     │  (FastAPI)  │     │  or browser  │
└─────────────┘     └────────┘     └──────┬──────┘     └──────────────┘
                                          │
                                          ▼ (Smart Scan only)
                                   ┌─────────────┐
                                   │   Ollama    │
                                   └─────────────┘
```

---

## Features

### Core
- Live metrics — CPU %, RAM, disk, and top processes every 5 seconds
- Time-series storage — SQLite for charts and trend detection
- Rule-based alerts — low RAM, memory hogs, rapid memory drops, high CPU, low disk
- REST API — metrics, processes, diagnosis, and AI analysis
- Local AI — Ollama explains findings (no API key)

### Dashboard & desktop (v1.5)
- **Insights tab** — weekly digest, app impact scores, network check, baseline learning, boot audit, AI action suggestions
- **Why slow now?** — one-click short-window slowdown report on Overview
- **Memory leak detection**, baseline anomalies, network latency, and battery warnings in alerts
- **Scheduled scans** — automatic daily diagnosis from the collector (configurable in `config.yaml`)
- **Storage extras** — folder growth, duplicates, developer junk, Photos/iCloud/Time Machine hints
- **Process controls** — pause/resume, quit all helpers for an app, impact scores
- **Startup toggles** — enable/disable user LaunchAgents
- **Per-alert Explain** — Ollama explains individual issues
- **Onboarding wizard** + **compact mode** toggle
- All v1.4 features: one-command install, cached storage scans, configurable alerts, setup banner

---

## Configuration

Edit `config.yaml` at the project root to tune collection and alert thresholds:

```yaml
collector:
  interval_seconds: 5
  retention_days: 7

thresholds:
  ram_critical_mb: 500
  ram_warning_mb: 1024
  disk_critical_free_gb: 2.0
  disk_warning_free_gb: 10.0
  # ... see config.yaml for all options
```

Restart the collector after changing config.

---

## Detection rules

Thresholds are configurable in `config.yaml`. No machine learning.

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

## API reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API, collector, and Ollama status |
| `/metrics` | GET | CPU/RAM/disk time-series (`?minutes=60`) |
| `/processes` | GET | Top processes (`?grouped=true` default) |
| `/processes/live` | GET | Live processes with PID (`?limit=25`) |
| `/processes/{pid}/kill` | POST | Terminate a process by PID |
| `/storage/breakdown` | GET | Home folder sizes (`?limit=10&refresh=false`) |
| `/storage/large-files` | GET | Large files (`?min_mb=500&limit=15&refresh=false`) |
| `/storage/reveal` | POST | Reveal path in Finder (`{"path": "..."}`) |
| `/cleanup/preview` | GET | Safe cleanup options and reclaimable space |
| `/cleanup/run` | POST | Run selected cleanup actions (`action_ids`) |
| `/startup-items` | GET | macOS login/launch items (read-only) |
| `/summary` | GET | Now vs N minutes ago (`?minutes_ago=60`) |
| `/report` | GET | Full export: diagnosis + comparison + processes |
| `/diagnoses` | GET | Past AI analyses (`?limit=20`) |
| `/diagnose` | POST | Run detection engine |
| `/analyze` | POST | Run detection + Ollama explanation |

API docs: `http://127.0.0.1:8000/docs`

---

## Data storage

| OS | Database path |
|----|---------------|
| macOS | `~/Library/Application Support/PCDiagnoser/data.db` |
| Windows | `%LOCALAPPDATA%/PCDiagnoser/data.db` |
| Linux | `~/.local/share/PCDiagnoser/data.db` |

Check collected data:

```bash
python scripts/check_data.py
```

---

## Utility scripts

| Script | Purpose |
|--------|---------|
| `scripts/install.sh` | **First-time setup** — venv, pip, npm in one command |
| `scripts/Launch Diagnoser.command` | **Double-click launcher** for macOS Finder |
| `scripts/start-desktop.sh` | **Recommended** — collector + API + desktop app |
| `scripts/stop-desktop.sh` | Stop background services from desktop mode |
| `scripts/start.sh` | Collector + API + browser dashboard |
| `scripts/stop.sh` | Stop services from browser mode |
| `scripts/check_data.py` | Row counts and time span in SQLite |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **API error** / Failed to fetch | Run `./scripts/start-desktop.sh` or start uvicorn manually on port 8000 |
| Charts empty | Wait a few minutes for collector data, or restart the collector |
| Collector shows **stale** | Collector isn't running — restart with `start-desktop.sh` |
| Disk panel empty | Restart the collector (old DB rows may lack disk columns) |
| **What changed?** empty | Needs ~1 hour of continuous collector history |
| Smart Scan fails (503) | Start Ollama (`ollama serve` or open the Ollama app) |
| `model not found` | Run `ollama pull llama3.2` |
| Port 1420 already in use | Another desktop dev session — run `./scripts/stop-desktop.sh` |
| Port 5173 already in use | Browser dev server is running — that's fine; desktop uses port 1420 |
| Storage scan slow / empty | First scan walks your home folder — wait or retry |
| Cleanup failed | Grant Full Disk Access if Trash empty fails on macOS |
| Tray icon missing | Rebuild desktop app after updating Tauri |
| Desktop won't start | Install Rust from [rustup.rs](https://rustup.rs), then retry |
| First desktop launch slow | Normal — Rust compiles on first run (1–2 min) |
| No notifications | Enable **Alerts** in the header; allow notifications in macOS System Settings |
| Alerts always `ok` | Detection uses the last 60 minutes — restart the collector |

**Verify services manually:**

```bash
curl http://127.0.0.1:8000/health
python scripts/check_data.py
```

---

## Running tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

39 tests cover detection rules, storage cache, disk scan, API routes, cleanup, and reveal safety.

---

## Tech stack

| Layer | Tool |
|-------|------|
| Metrics collection | Python + psutil |
| Storage | SQLite |
| Detection | Python (threshold rules) |
| API | FastAPI + Uvicorn |
| UI | React + TypeScript + Recharts |
| Desktop app | Tauri 2 (Rust + native WebView) |
| AI explanations | Ollama (llama3.2) |

---

## Author

**Nguyen Le**
