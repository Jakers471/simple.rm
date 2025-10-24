# Working with AI - Testing Workflow

## Quick Reference: Test Commands

```bash
python run_tests.py          # Interactive menu
[1] All tests               # Run everything
[2] Unit tests only         # Fast, no external deps
[3] Integration tests       # Requires TopstepX SDK
[4] E2E tests              # Full workflows
[5] Coverage report        # Terminal output
[6] HTML coverage          # Browser report
[7] Specific test file     # Target one file
[8] Pattern match          # Run tests matching pattern
[9] Last failed            # Rerun only failures
```

## Workflow 1: Starting Fresh - Run Unit Tests

**Step 1:** Run unit tests
```bash
python run_tests.py
# Select: [2] Unit tests only
```

**Step 2:** Check results
- GREEN: All passed → Move to Integration Tests
- RED: Failures detected → Go to Workflow 2

## Workflow 2: Unit Test Failed - Fix Process

**Step 1:** Identify failure
```bash
# Check latest report
cat test_reports/latest.txt
```

**Step 2:** Copy error to AI
```
This test failed:

FAILED tests/unit/rules/test_daily_realized_loss.py::test_loss_limit_exceeded

AssertionError: Expected DENY, got ALLOW
```

**Step 3:** AI analyzes and suggests fix
- AI reads the test file
- AI reads the implementation file
- AI provides specific code change

**Step 4:** Apply fix
```bash
# AI will edit the file directly or provide code
```

**Step 5:** Rerun failed tests
```bash
python run_tests.py
# Select: [9] Rerun last failed tests
```

**Step 6:** Repeat until GREEN
- If still RED: Copy new error to AI
- If GREEN: Move to Integration Tests

## Workflow 3: Integration Tests

**Prerequisites:**
- TopstepX SDK installed
- Valid .env credentials
- API access working

**Step 1:** Run integration tests
```bash
python run_tests.py
# Select: [3] Integration tests
```

**Step 2:** Common failures
- "Authentication failed" → Check .env credentials
- "SDK not found" → Run: pip install topstepx-sdk
- "API timeout" → Check network/API status

**Step 3:** If integration fails
```
Copy to AI:
"Integration test failed: [paste error]
Check if it's a config issue or real bug"
```

## Workflow 4: E2E Tests

**Purpose:** Test complete user workflows

**Step 1:** Run E2E tests
```bash
python run_tests.py
# Select: [4] E2E tests
```

**Step 2:** E2E tests verify
- Full trading scenarios
- Multi-rule interactions
- State persistence
- Error recovery

**Step 3:** If E2E fails
- Usually indicates integration issues
- Check test_reports/latest.txt
- Copy full scenario to AI

## Workflow 5: Adding New Features (TDD)

**Step 1:** Write test FIRST (should fail RED)
```python
def test_new_feature():
    """Test new feature that doesn't exist yet"""
    result = new_feature()
    assert result == expected
```

**Step 2:** Run test (expect RED)
```bash
python run_tests.py
# Select: [7] Specific test file
# Enter: tests/unit/test_new_feature.py
```

**Step 3:** Tell AI
```
"This test fails as expected (RED):
[paste test code]

Please implement minimal code to make it pass"
```

**Step 4:** AI implements code

**Step 5:** Rerun test (expect GREEN)
```bash
python run_tests.py
# Select: [9] Rerun last failed tests
```

**Step 6:** Refactor if needed
- Keep test GREEN
- Improve code quality
- Run tests after each change

## Workflow 6: Coverage Analysis

**Step 1:** Generate coverage report
```bash
python run_tests.py
# Select: [5] Coverage report (terminal)
```

**Step 2:** Look for modules <90%
```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/core/pnl_tracker.py             45      8    82%  ← Low coverage
src/rules/daily_loss.py            123      2    98%  ← Good
```

**Step 3:** Tell AI
```
"Need tests for: src/core/pnl_tracker.py
Current coverage: 82%
Missing lines: [from report]"
```

**Step 4:** AI creates tests

**Step 5:** Verify coverage improved
```bash
python run_tests.py
# Select: [5] Coverage report
```

## Workflow 7: HTML Coverage Reports

**Step 1:** Generate HTML report
```bash
python run_tests.py
# Select: [6] HTML coverage report
```

**Step 2:** Open in browser
```bash
# Report saved to: htmlcov/index.html
# Open with browser or:
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html      # Mac
start htmlcov/index.html     # Windows
```

**Step 3:** Navigate HTML report
- Click module name
- See uncovered lines in RED
- Covered lines in GREEN

**Step 4:** Show AI uncovered code
```
"These lines are uncovered in src/core/pnl_tracker.py:
[screenshot or paste lines 45-52]

Create tests to cover them"
```

## Workflow 8: Debugging Test Failures

**Step 1:** Run with verbose output
```bash
pytest tests/unit/test_file.py -v -s
```

**Step 2:** Common issues

**Import errors:**
```bash
# Fix: Check PYTHONPATH
export PYTHONPATH=/home/jakers/projects/simple-risk-manager/simple risk manager:$PYTHONPATH
```

**Fixture errors:**
```bash
# Copy to AI:
"Test fails with fixture error:
[paste error]"
```

**Assertion failures:**
```bash
# Copy to AI:
"Expected X but got Y:
[paste full assertion with values]"
```

**Step 3:** Add debug output
```python
# Temporary debug (remove after fix)
print(f"DEBUG: variable = {variable}")
import pdb; pdb.set_trace()  # Breakpoint
```

## Workflow 9: Pattern-Based Testing

**Step 1:** Run tests matching pattern
```bash
python run_tests.py
# Select: [8] Run tests matching pattern
# Enter: test_daily
```

**Use cases:**
- `test_daily` → All daily loss tests
- `test_symbol` → All symbol-related tests
- `test_auth` → All authorization tests
- `RealizedLoss` → All realized loss tests

## Workflow 10: Continuous Testing

**During development:**
```bash
# Terminal 1: Edit code
# Terminal 2: Watch tests
pytest tests/unit -f  # Rerun on file change
```

**Before commit:**
```bash
# Run all tests
python run_tests.py
# Select: [1] All tests

# Check coverage
python run_tests.py
# Select: [5] Coverage report
```

**AI interaction:**
```
"Running all tests before commit.
Here's the output:
[paste results]

Any issues?"
```

## Best Practices with AI

**1. Always provide full context:**
```
BAD:  "Test failed"
GOOD: "test_daily_realized_loss.py::test_limit_exceeded failed
       Expected: DENY
       Got: ALLOW
       Here's the test code: [paste]"
```

**2. Share test reports:**
```bash
cat test_reports/latest.txt | pbcopy  # Mac
cat test_reports/latest.txt | xclip   # Linux
```

**3. Use specific commands:**
```
BAD:  "Run tests"
GOOD: "Run: pytest tests/unit/rules/test_daily_loss.py -v"
```

**4. Reference file paths:**
```
"Edit: /home/jakers/projects/simple-risk-manager/simple risk manager/src/rules/daily_loss.py
Line 45: Change threshold from 100 to 200"
```

**5. Verify fixes:**
```
"Applied your fix.
Rerunning: pytest tests/unit/rules/test_daily_loss.py
Result: [paste]"
```

## Common AI Prompts

**For new features:**
```
"Need to add feature X that does Y.
Please:
1. Write failing test first
2. Show me the test code
3. I'll confirm it fails
4. Then implement feature"
```

**For bug fixes:**
```
"Bug: [describe behavior]
Expected: [what should happen]
Actual: [what happens]
Test that fails: [paste test output]
Please suggest fix"
```

**For refactoring:**
```
"This code works but is messy:
[paste code]

Refactor while keeping tests green:
[paste test file that covers it]"
```

**For coverage:**
```
"Coverage is 75% on this module:
[paste coverage output]

Missing lines: 45-52, 67-71
Generate tests for uncovered code"
```

## Troubleshooting

**Tests won't run:**
```bash
# Check Python environment
python --version  # Should be 3.12+

# Check pytest installed
pytest --version

# Check PYTHONPATH
echo $PYTHONPATH
```

**Import errors:**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="/home/jakers/projects/simple-risk-manager/simple risk manager:$PYTHONPATH"

# Or run from project root
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
python run_tests.py
```

**Fixture errors:**
```bash
# Check conftest.py exists
ls tests/conftest.py
ls tests/fixtures/

# Verify fixture imports
grep -r "def sample_account" tests/
```

**Coverage not generating:**
```bash
# Install coverage.py
pip install coverage

# Run manually
coverage run -m pytest tests/unit
coverage report
```

## Summary: Daily Testing Routine

**Morning start:**
1. `python run_tests.py` → [2] Unit tests
2. Fix any failures with AI
3. Get all unit tests GREEN

**During development:**
1. Write test first (TDD)
2. Implement feature
3. Run `[9] Last failed` until GREEN
4. Check coverage periodically

**Before commit/push:**
1. `python run_tests.py` → [1] All tests
2. `python run_tests.py` → [5] Coverage report
3. Ensure >90% coverage
4. All tests GREEN

**Weekly:**
1. Generate HTML coverage
2. Review uncovered code
3. Add missing tests
4. Update test documentation

---

**File Location:** /home/jakers/projects/simple-risk-manager/simple risk manager/docs/testing/WORKING_WITH_AI.md

**Quick Access:**
```bash
cat docs/testing/WORKING_WITH_AI.md
```
