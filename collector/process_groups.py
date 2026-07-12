"""
Group related OS processes under a single app name.

Examples:
  "Cursor Helper (Renderer)" → "Cursor"
  "Google Chrome Helper (Renderer)" → "Google Chrome"
"""


def normalize_app_name(process_name: str) -> str:
    """
    Strip helper/renderer suffixes to get the parent app name.

    macOS often shows helpers like "App Helper (Renderer)".
    We keep the part before " Helper".
    """
    if " Helper" in process_name:
        return process_name.split(" Helper")[0].strip()
    return process_name.strip()


def group_process_rows(rows) -> list[dict]:
    """
    Combine rows with the same app name.

    Returns a list sorted by total memory (highest first), each item:
      app_name, memory_mb (sum), cpu_percent (sum), process_count
    """
    groups: dict[str, dict] = {}

    for row in rows:
        app_name = normalize_app_name(row["process_name"])
        memory_mb = float(row["memory_mb"])
        cpu = row["cpu_percent"]
        cpu_val = float(cpu) if cpu is not None else 0.0

        if app_name not in groups:
            groups[app_name] = {
                "app_name": app_name,
                "memory_mb": 0.0,
                "cpu_percent": 0.0,
                "process_count": 0,
            }

        groups[app_name]["memory_mb"] += memory_mb
        groups[app_name]["cpu_percent"] += cpu_val
        groups[app_name]["process_count"] += 1

    result = sorted(groups.values(), key=lambda g: g["memory_mb"], reverse=True)

    for group in result:
        group["memory_mb"] = round(group["memory_mb"], 1)
        group["cpu_percent"] = round(group["cpu_percent"], 1)

    return result