# Test Results & Reporting Guide

## 🎯 Overview

All test results are automatically saved to `/test-results/` every time you run tests. Agents can read these files to check test status and coverage.

## 📁 What Gets Saved

Every test run automatically generates:

### 1. Coverage Reports (3 formats)
- **HTML:** `test-results/coverage/html/index.html` (open in browser)
- **JSON:** `test-results/coverage/coverage.json` (for agents to parse)
- **XML:** `test-results/coverage/coverage.xml` (for CI/CD)

### 2. Test Reports (2 formats)
- **HTML:** `test-results/reports/report.html` (interactive test report)
- **JUnit XML:** `test-results/reports/junit.xml` (for agents/CI/CD)

### 3. Test Logs
- **Location:** `logs/tests/test_run_YYYYMMDD_HHMMSS.log`
- **Content:** Full pytest output with timestamps
- **Retention:** Last 10 runs kept automatically

## 🚀 Quick Commands

### View Results Dashboard (Recommended)
```bash
./view_test_results.sh
```

### Or from test menu
```bash
./run_tests.sh
# Select option 9: View Test Results Dashboard
```

### Direct pytest run (auto-saves results)
```bash
source venv/bin/activate
pytest tests/
# Results automatically saved to test-results/
```

## 👁️ For Agents: Reading Test Results

### Check Overall Coverage
```bash
cat test-results/coverage/coverage.json | jq '.totals.percent_covered'
# Output: 87.5 (means 87.5% coverage)
```

### Check Test Status
```bash
cat test-results/reports/junit.xml | grep '<testsuite' | grep -oP 'tests="\d+"'
# Shows total tests run

cat test-results/reports/junit.xml | grep '<testsuite' | grep -oP 'failures="\d+"'
# Shows number of failures (should be 0)
```

### Find Uncovered Files
```bash
cat test-results/coverage/coverage.json | jq -r '.files | to_entries[] | select(.value.summary.percent_covered < 90) | "\(.key): \(.value.summary.percent_covered)%"'
```

### Get Failed Test Names
```bash
cat test-results/reports/junit.xml | grep '<failure' -B 3 | grep 'testcase name=' | grep -oP 'name="[^"]*"'
```

## 📊 Test Results Dashboard

Run the dashboard to see:
- ✅ Overall test pass/fail status
- 📊 Coverage percentage (with color coding)
- 🔍 Files below 90% coverage
- 📝 Recent test runs
- ⚠️ Failed tests (if any)

```bash
source venv/bin/activate
python3 scripts/test-management/view_results.py

# Or for specific sections:
python3 scripts/test-management/view_results.py coverage  # Coverage only
python3 scripts/test-management/view_results.py tests     # Test results only
python3 scripts/test-management/view_results.py history   # Recent runs
```

## 🎨 Colored Pytest Output

Now enabled! You'll see:
- 🟢 **Green:** Passing tests
- 🔴 **Red:** Failed tests
- 🟡 **Yellow:** Warnings/Skipped tests
- 🔵 **Blue:** Test names and headers

This works automatically when running:
```bash
./run_tests.sh
# or
source venv/bin/activate
pytest tests/
```

## 📈 Coverage Reports

### HTML Coverage (Visual)
```bash
# Open in browser
open test-results/coverage/html/index.html

# On WSL
explorer.exe test-results/coverage/html/index.html
```

Shows:
- ✅ Green lines = covered
- 🔴 Red lines = NOT covered (need tests!)
- 🟡 Yellow = partially covered
- Click files to see exact uncovered lines

### JSON Coverage (For Agents)
```json
{
  "totals": {
    "percent_covered": 87.5,
    "num_statements": 1234,
    "covered_lines": 1080,
    "missing_lines": 154
  },
  "files": {
    "src/core/enforcement_actions.py": {
      "summary": {
        "percent_covered": 92.3,
        "missing_lines": 8
      },
      "missing_lines": [45, 46, 78, 79, 123, 124, 125, 126]
    }
  }
}
```

## 🔄 Automatic Updates

Results are automatically updated when you run:
- Option 1-8 from test menu (any test execution)
- Direct `pytest` commands
- CI/CD pipelines

**No manual action needed!**

## 📋 For Agent Swarms

### Pre-Implementation Check
```bash
# Agent should verify coverage before implementing new features
COVERAGE=$(cat test-results/coverage/coverage.json | jq '.totals.percent_covered')
if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo "⚠️ Coverage below 90%: Need more tests!"
fi
```

### Post-Implementation Check
```bash
# Agent should verify tests pass after changes
FAILURES=$(grep -oP 'failures="\K\d+' test-results/reports/junit.xml)
if [ "$FAILURES" -gt 0 ]; then
    echo "❌ $FAILURES tests failing! Fix required."
fi
```

### Finding What to Test
```bash
# List files with lowest coverage (highest priority)
cat test-results/coverage/coverage.json | jq -r '.files | to_entries | sort_by(.value.summary.percent_covered) | .[] | "\(.value.summary.percent_covered)% - \(.key)"' | head -10
```

## 🛠️ Menu Options Summary

From `./run_tests.sh` menu:

**Test Execution (1-8):** All auto-save results
- Results → `test-results/`
- Logs → `logs/tests/`

**Test Analysis (9-12):** View saved results
- **9:** Dashboard (all metrics)
- **10:** HTML coverage report
- **11:** HTML test report
- **12:** View test logs

**Maintenance (13-15):** Cleanup and updates
- **13:** Clean cache
- **14:** Update dependencies
- **15:** Watch mode (auto-run)

## 📍 File Locations

```
project-root/
├── test-results/              # ← ALL RESULTS SAVED HERE
│   ├── coverage/
│   │   ├── html/              # Visual coverage (open in browser)
│   │   ├── coverage.json      # Programmatic access
│   │   └── coverage.xml       # CI/CD integration
│   ├── reports/
│   │   ├── report.html        # Visual test report
│   │   └── junit.xml          # Programmatic access
│   └── README.md              # This directory's documentation
│
├── logs/tests/                # Test execution logs
│   └── test_run_*.log         # Timestamped logs
│
├── run_tests.sh               # Main test menu
└── view_test_results.sh       # Quick results viewer
```

## ✅ Success Criteria

**For Agents to check before marking work complete:**

1. **Coverage ≥90%**
   ```bash
   COVERAGE=$(cat test-results/coverage/coverage.json | jq '.totals.percent_covered')
   [ $(echo "$COVERAGE >= 90" | bc) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL"
   ```

2. **Zero Test Failures**
   ```bash
   FAILURES=$(grep -oP 'failures="\K\d+' test-results/reports/junit.xml)
   [ "$FAILURES" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"
   ```

3. **Zero Errors**
   ```bash
   ERRORS=$(grep -oP 'errors="\K\d+' test-results/reports/junit.xml)
   [ "$ERRORS" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL"
   ```

---

**Updated:** Every test run
**Location:** `/test-results/`
**Retention:** Latest reports always available
**Format:** HTML (humans), JSON/XML (agents/CI)
