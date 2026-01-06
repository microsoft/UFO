"""
Summary of constellation parsing test results from response.log

ISSUE IDENTIFIED:
================
The constellation_before field in lines 2-5 contains INVALID data where the "tasks"
field is a Python string representation instead of a proper JSON object/dict.

WORKING CASES:
- Line 1: constellation_after [OK] (tasks is dict)
- Line 2: constellation_after [OK] (tasks is dict)
- Line 3: constellation_after [OK] (tasks is dict)
- Line 4: constellation_after [OK] (tasks is dict)

FAILING CASES:
- Line 2: constellation_before [FAIL] (tasks is string: "{'t1': {...}}")
- Line 3: constellation_before [FAIL] (tasks is string: "{'t1': {...}}")
- Line 4: constellation_before [FAIL] (tasks is string: "{'t1': {...}}")
- Line 5: constellation_before [FAIL] (tasks is string: "{'t1': {...}}")
- Line 5: constellation_after [FAIL] (tasks is string: "{'t1': {...}}")

ROOT CAUSE:
===========
When creating constellation_before, the code is using str() or repr() on the tasks
dictionary instead of properly serializing it to JSON. This results in:

  WRONG:  "tasks": "{'t1': {'task_id': 't1', ...}}"  <- Python str representation
  RIGHT:  "tasks": {"t1": {"task_id": "t1", ...}}    <- Proper JSON

IMPACT:
=======
TaskConstellation.from_json() CANNOT parse constellation_before from lines 2-5
because from_dict() expects tasks to be a dictionary, not a string.

RECOMMENDATION:
===============
Fix the code that generates constellation_before to use json.dumps() or
TaskConstellation.to_json() instead of str() or repr().

The issue is likely in the code that logs constellation_before. Look for:
  - str(constellation.to_dict())
  - repr(constellation.to_dict())
  - or manual dictionary construction with str() on nested objects

Should be:
  - constellation.to_json()
  - json.dumps(constellation.to_dict())
"""

print(__doc__)

# Now let's verify with actual test
import json
import sys
from pathlib import Path

# Add project root to path (go up 3 levels: constellation -> galaxy -> tests -> root)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from galaxy.constellation.task_constellation import TaskConstellation


def test_working_vs_broken():
    """Test both working and broken cases"""

    log_file = project_root / "logs" / "galaxy" / "task_1" / "response.log"
    with open(log_file, "r") as f:
        lines = f.readlines()

    print("\n" + "=" * 80)
    print("ACTUAL TEST RESULTS")
    print("=" * 80 + "\n")

    # Test working case: Line 1 constellation_after
    print("[OK] WORKING CASE: Line 1 - constellation_after")
    log1 = json.loads(lines[0])
    const_after_str = log1["constellation_after"]
    try:
        constellation = TaskConstellation.from_json(json_data=const_after_str)
        print(f"  Successfully parsed!")
        print(f"  - ID: {constellation.constellation_id}")
        print(f"  - Tasks: {constellation.task_count}")
        print(f"  - State: {constellation.state.value}\n")
    except Exception as e:
        print(f"  Failed: {e}\n")

    # Test broken case: Line 2 constellation_before
    print("[FAIL] BROKEN CASE: Line 2 - constellation_before")
    log2 = json.loads(lines[1])
    const_before_str = log2["constellation_before"]
    try:
        constellation = TaskConstellation.from_json(json_data=const_before_str)
        print(f"  Unexpectedly succeeded!\n")
    except Exception as e:
        print(f"  Failed as expected: {type(e).__name__}: {e}\n")

    # Show the problematic data
    print("=" * 80)
    print("PROBLEMATIC DATA EXAMPLE (Line 2 constellation_before)")
    print("=" * 80)
    const_before = json.loads(const_before_str)
    print(f"Type of 'tasks' field: {type(const_before['tasks'])}")
    print(f"Value (first 300 chars): {str(const_before['tasks'])[:300]}...")


if __name__ == "__main__":
    test_working_vs_broken()
