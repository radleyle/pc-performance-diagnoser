"""Network connectivity and latency checks."""

from __future__ import annotations

import socket
import subprocess
import sys
import time


def _dns_latency_ms(host: str = "one.one.one.one") -> float | None:
    start = time.perf_counter()
    try:
        socket.getaddrinfo(host, 443)
        return round((time.perf_counter() - start) * 1000, 1)
    except OSError:
        return None


def _ping_latency_ms(host: str = "1.1.1.1") -> float | None:
    if sys.platform == "darwin":
        cmd = ["ping", "-c", "1", "-W", "1000", host]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", host]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            if "time=" in line:
                part = line.split("time=")[1].split()[0]
                return float(part.replace("ms", ""))
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None
    return None


def check_network_status() -> dict:
    dns_ms = _dns_latency_ms()
    ping_ms = _ping_latency_ms()
    latency = ping_ms or dns_ms

    status = "ok"
    message = "Network looks healthy"
    if latency is None:
        status = "warning"
        message = "Could not measure network latency"
    elif latency > 500:
        status = "warning"
        message = f"High network latency ({latency:.0f} ms)"

    return {
        "status": status,
        "message": message,
        "dns_latency_ms": dns_ms,
        "ping_latency_ms": ping_ms,
        "active_connections": _active_connection_count(),
    }


def _active_connection_count() -> int | None:
    try:
        import psutil

        return len(psutil.net_connections(kind="inet"))
    except Exception:
        return None
