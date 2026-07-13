"""Live process listing and safe termination."""

from __future__ import annotations

import signal

import psutil

from collector.process_groups import normalize_app_name

_frozen_pids: set[int] = set()


def list_live_processes(limit: int = 25) -> list[dict]:
    """Return running processes with PID, sorted by memory."""
    rows: list[dict] = []

    for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        try:
            info = proc.info
            memory_info = info.get("memory_info")
            if memory_info is None:
                continue

            rows.append(
                {
                    "pid": info["pid"],
                    "process_name": info.get("name") or "unknown",
                    "memory_mb": memory_info.rss / (1024**2),
                    "cpu_percent": info.get("cpu_percent") or 0.0,
                    "frozen": info["pid"] in _frozen_pids,
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    rows.sort(key=lambda row: row["memory_mb"], reverse=True)
    return rows[:limit]


def kill_process(pid: int) -> dict:
    """Terminate a process by PID."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        proc.wait(timeout=3)
        return {"ok": True, "pid": pid, "name": name, "message": f"Stopped {name}"}
    except psutil.TimeoutExpired:
        proc.kill()
        return {"ok": True, "pid": pid, "message": "Process force-stopped"}
    except psutil.NoSuchProcess:
        return {"ok": False, "pid": pid, "message": "Process not found"}
    except psutil.AccessDenied:
        return {"ok": False, "pid": pid, "message": "Permission denied"}
    except Exception as exc:
        return {"ok": False, "pid": pid, "message": str(exc)}


def freeze_process(pid: int) -> dict:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.send_signal(signal.SIGSTOP)
        _frozen_pids.add(pid)
        return {"ok": True, "pid": pid, "name": name, "message": f"Paused {name}"}
    except psutil.NoSuchProcess:
        return {"ok": False, "pid": pid, "message": "Process not found"}
    except psutil.AccessDenied:
        return {"ok": False, "pid": pid, "message": "Permission denied"}
    except Exception as exc:
        return {"ok": False, "pid": pid, "message": str(exc)}


def resume_process(pid: int) -> dict:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.send_signal(signal.SIGCONT)
        _frozen_pids.discard(pid)
        return {"ok": True, "pid": pid, "name": name, "message": f"Resumed {name}"}
    except psutil.NoSuchProcess:
        _frozen_pids.discard(pid)
        return {"ok": False, "pid": pid, "message": "Process not found"}
    except psutil.AccessDenied:
        return {"ok": False, "pid": pid, "message": "Permission denied"}
    except Exception as exc:
        return {"ok": False, "pid": pid, "message": str(exc)}


def quit_app_group(app_name: str) -> dict:
    """Terminate all processes that belong to an app group."""
    terminated = 0
    errors: list[str] = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or ""
            if normalize_app_name(name) != app_name:
                continue
            proc.terminate()
            terminated += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            errors.append(name)
            continue

    if terminated == 0:
        return {"ok": False, "message": f"No running processes found for {app_name}"}

    return {
        "ok": True,
        "message": f"Stopped {terminated} process(es) for {app_name}",
        "terminated": terminated,
        "errors": errors,
    }
