# Constellation Parsing Tests

This directory contains tests for validating `TaskConstellation.from_json()` and `from_dict()` methods with real log data.

## Test Files

### 1. `test_constellation_parsing.py`
**Main test script** - Comprehensive test that validates parsing of `constellation_before` and `constellation_after` fields from response logs.

**Usage:**
```bash
python tests/galaxy/constellation/test_constellation_parsing.py
```

**What it tests:**
- Parses each line in `logs/galaxy/task_1/response.log`
- Tests both `constellation_before` and `constellation_after` fields
- Reports success/failure for each parsing attempt
- Provides detailed error messages

### 2. `test_constellation_parsing_debug.py`
**Debug utility** - Examines the structure of constellation JSON data to identify format issues.

**Usage:**
```bash
python tests/galaxy/constellation/test_constellation_parsing_debug.py
```

**What it does:**
- Inspects JSON structure
- Identifies data type issues
- Validates JSON format
- Reports problematic fields

### 3. `test_constellation_tasks_debug.py`
**Detailed field inspector** - Focuses on debugging the `tasks` field specifically.

**Usage:**
```bash
python tests/galaxy/constellation/test_constellation_tasks_debug.py
```

**What it does:**
- Examines the `tasks` field in detail
- Compares working vs broken examples
- Shows actual data types
- Identifies string vs dict issues

### 4. `test_constellation_summary.py`
**Comprehensive summary** - Provides a full analysis with examples and recommendations.

**Usage:**
```bash
python tests/galaxy/constellation/test_constellation_summary.py
```

**What it provides:**
- Summary of all test results
- Root cause analysis
- Code examples showing the problem
- Recommendations for fixes

## Test Data

These tests use log data from:
```
logs/galaxy/task_1/response.log
```

This is a JSONL (JSON Lines) file where each line contains a response log entry with:
- `constellation_before`: State before modification
- `constellation_after`: State after modification

## Known Issues

### Issue: String Representation in Tasks Field

**Problem:** Some `constellation_before` entries contain malformed data where the `tasks` field is a Python string representation instead of a proper JSON object.

**Example of broken data:**
```json
{
  "tasks": "{'t1': {'task_id': 't1', ...}}"  // WRONG - Python str
}
```

**Example of correct data:**
```json
{
  "tasks": {"t1": {"task_id": "t1", ...}}   // CORRECT - JSON object
}
```

**Root Cause:** The logging code is using `str()` or `repr()` instead of `json.dumps()` when serializing the constellation.

**Fix:** Update the code that generates `constellation_before` to use proper JSON serialization.

## Test Results Summary

Based on the last test run with `logs/galaxy/task_1/response.log`:

| Field | Success Rate | Notes |
|-------|-------------|-------|
| `constellation_after` | 80% (4/5) | Line 5 failed |
| `constellation_before` | 0% (0/4) | All failed due to string repr in tasks field |
| **Overall** | 44.4% (4/9) | See detailed report in `docs/CONSTELLATION_PARSING_TEST_REPORT.md` |

## Related Documentation

- Full test report: `docs/CONSTELLATION_PARSING_TEST_REPORT.md`
- TaskConstellation implementation: `galaxy/constellation/task_constellation.py`

## Running All Tests

### Quick Start - Run All Tests

```bash
# Activate virtual environment
.\scripts\activate.ps1

# Run all tests in sequence
python tests/galaxy/constellation/run_all_tests.py
```

### Run Individual Tests

```bash
# Activate virtual environment
.\scripts\activate.ps1

# Run main test
python tests/galaxy/constellation/test_constellation_parsing.py

# Run debug tests if issues found
python tests/galaxy/constellation/test_constellation_parsing_debug.py
python tests/galaxy/constellation/test_constellation_tasks_debug.py

# Run comprehensive summary
python tests/galaxy/constellation/test_constellation_summary.py
```

## Expected Output

When tests pass:
```
✓ Successfully parsed constellation_after
  - Constellation ID: constellation_2753954b_20251021_180630
  - Tasks: 5
  - Dependencies: 4
  - State: created
```

When tests fail:
```
✗ Failed to parse constellation_before: AttributeError: 'str' object has no attribute 'items'
```
