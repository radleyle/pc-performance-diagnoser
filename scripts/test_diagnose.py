"""Run the detection engine against real SQLite data."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.detect import run_diagnosis


def main() -> None:
    print("=== Detection engine test ===\n")

    result = run_diagnosis(minutes=60)

    print(f"Status: {result.status}")
    print(f"Issues found: {len(result.issues)}\n")

    if result.issues:
        print("Issues:")
        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.type}: {issue.message}")
    else:
        print("No issues detected — system looks OK based on current rules.")

    print("\nTop processes:")
    for proc in result.top_processes[:5]:
        print(f"  {proc.name}: {proc.memory_mb:.0f} MB")

    print("\nFull JSON (what the API/LLM will use later):")
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()