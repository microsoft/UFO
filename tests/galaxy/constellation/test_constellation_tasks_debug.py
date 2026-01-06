"""
Detailed debug to see the tasks field issue
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def debug_tasks_field(log_file_path: str):
    """Debug the tasks field in constellation_before"""

    with open(log_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check line 2 which had the issue
    line = lines[1]  # 0-indexed
    log_entry = json.loads(line.strip())

    if "constellation_before" in log_entry and log_entry["constellation_before"]:
        const_before_str = log_entry["constellation_before"]
        const_before = json.loads(const_before_str)

        print("constellation_before structure:")
        print(f"  constellation_id: {const_before.get('constellation_id')}")
        print(f"  state: {const_before.get('state')}")
        print(f"  tasks type: {type(const_before.get('tasks'))}")

        tasks = const_before.get("tasks")
        if isinstance(tasks, str):
            print(f"\n  [WARN] Tasks is a STRING (should be dict)")
            print(f"  Tasks value (first 500 chars):")
            print(f"  {tasks[:500]}")
        elif isinstance(tasks, dict):
            print(f"\n  [OK] Tasks is a DICT (correct)")
            print(f"  Number of tasks: {len(tasks)}")

        print("\n" + "=" * 80 + "\n")

    # Check line 1 which worked
    line = lines[0]
    log_entry = json.loads(line.strip())

    if "constellation_after" in log_entry and log_entry["constellation_after"]:
        const_after_str = log_entry["constellation_after"]
        const_after = json.loads(const_after_str)

        print("constellation_after (line 1) structure:")
        print(f"  constellation_id: {const_after.get('constellation_id')}")
        print(f"  state: {const_after.get('state')}")
        print(f"  tasks type: {type(const_after.get('tasks'))}")

        tasks = const_after.get("tasks")
        if isinstance(tasks, str):
            print(f"\n  ⚠️  Tasks is a STRING (should be dict)")
            print(f"  Tasks value (first 500 chars):")
            print(f"  {tasks[:500]}")
        elif isinstance(tasks, dict):
            print(f"\n  [OK] Tasks is a DICT (correct)")
            print(f"  Number of tasks: {len(tasks)}")


if __name__ == "__main__":
    log_file = project_root / "logs" / "galaxy" / "task_1" / "response.log"
    debug_tasks_field(str(log_file))
