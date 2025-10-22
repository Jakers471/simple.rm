# Test Management System

Comprehensive CLI tools for managing tests in the Simple Risk Manager project.

## Quick Start

### Interactive Menu (Recommended)
```bash
# Run the main test menu
./scripts/test-management/test_menu.py

# Or from anywhere in the project
python3 scripts/test-management/test_menu.py
```

### Bash Commands (Fast Access)
```bash
# Source the test commands
source scripts/test-management/run_tests.sh

# Now use any test command
test-all        # Run all tests
test-unit       # Run unit tests
test-cov        # Run with coverage
test-fast       # Run in parallel
test-watch      # Auto-run on changes
```

## Available Tools

### 1. Test Menu (`test_menu.py`)
**Main interactive CLI for all test operations**

Features:
- Run all tests or specific test suites
- Execute tests with coverage reports
- Run tests in parallel for faster execution
- Quick smoke tests for rapid feedback
- View test logs with filtering
- View coverage reports and dashboards
- Clean test cache and artifacts
- Install/update test dependencies
- Watch mode for continuous testing

Usage:
```bash
./scripts/test-management/test_menu.py
```

### 2. Quick Test Runner (`run_tests.sh`)
**Bash script with convenient test aliases**

Commands:
```bash
# Basic test execution
test-all              # Run all tests
test-unit             # Run unit tests only
test-integration      # Run integration tests
test-e2e              # Run E2E tests
test-smoke            # Run quick smoke tests

# Coverage
test-cov              # Run tests with coverage report
test-cov-summary      # Show coverage summary

# Specific tests
test-mod <name>       # Run specific module tests
test-mark <marker>    # Run tests with marker
test-pattern <term>   # Run tests matching pattern
test-failed           # Re-run failed tests

# Monitoring
test-watch            # Watch mode (auto-run on changes)
test-list             # List all available tests

# Maintenance
test-clean            # Clean test cache
test-setup            # Install test dependencies

# Advanced
test-fast             # Run tests in parallel
test-timeout <sec>    # Run with timeout
test-verbose          # Run with verbose output
test-report           # Generate HTML report
test-json             # Export results to JSON
```

### 3. Test Watcher (`test_watch.py`)
**Automatically run tests when files change**

Features:
- Monitors source and test files
- Automatically runs related tests
- Smart test selection based on changed files
- Real-time feedback
- Color-coded output

Usage:
```bash
# Start watching with default interval (1 second)
./scripts/test-management/test_watch.py

# Custom check interval
./scripts/test-management/test_watch.py --interval 2.0
```

### 4. Log Viewer (`log_viewer.py`)
**Interactive test log viewer and analyzer**

Features:
- Browse recent test execution logs
- View log summaries with test results
- Display full logs with color coding
- Filter and search log content
- Quick identification of failures and errors
- File size and timestamp information

Usage:
```bash
./scripts/test-management/log_viewer.py
```

Interactive options:
- `[number]` - View log summary
- `[number]f` - View full log
- `[number]s` - Search/filter log
- `q` - Quit

### 5. Coverage Reporter (`coverage_report.py`)
**Interactive coverage analysis dashboard**

Features:
- Overall coverage summary
- Coverage breakdown by module
- Identify files with low coverage
- Generate HTML coverage reports
- Visual progress bars
- Color-coded feedback

Usage:
```bash
./scripts/test-management/coverage_report.py
```

Menu options:
1. Overall Summary - Complete coverage statistics
2. Coverage by Module - Module-level analysis
3. Files with Low Coverage - Find areas needing tests
4. Generate HTML Report - Create browsable report
5. Coverage Trends - Historical tracking (coming soon)

## Color Coding

All tools use consistent color coding:
- **Green** (✓) - Success, passing tests, high coverage
- **Red** (✗) - Failures, errors, low coverage
- **Yellow** (⚠) - Warnings, medium coverage
- **Cyan** (ℹ) - Information messages
- **Blue** - Headers and sections

## Log Files

Test execution logs are saved to:
```
logs/tests/test_run_YYYYMMDD_HHMMSS.log
```

Each test run creates a timestamped log file for later review.

## Coverage Reports

HTML coverage reports are generated in:
```
htmlcov/index.html
```

View detailed line-by-line coverage analysis in your browser.

## Requirements

Minimum requirements:
- Python 3.8+
- pytest
- pytest-cov

Optional for enhanced features:
- pytest-xdist (parallel execution)
- pytest-watch (watch mode)
- coverage (detailed reports)

Install all dependencies:
```bash
# Using test menu
./scripts/test-management/test_menu.py
# Select option 13: Install/Update Test Dependencies

# Or manually
pip install pytest pytest-cov pytest-xdist pytest-watch coverage
```

## Workflow Examples

### Daily Development Workflow
```bash
# 1. Start watch mode in one terminal
./scripts/test-management/test_watch.py

# 2. Code in your editor
# 3. Tests run automatically on save
# 4. Get instant feedback
```

### Pre-Commit Workflow
```bash
# Run all tests
source scripts/test-management/run_tests.sh
test-all

# If failures, view details
./scripts/test-management/log_viewer.py

# Fix issues, then re-run failed tests
test-failed
```

### Coverage Review Workflow
```bash
# 1. Run tests with coverage
test-cov

# 2. Review coverage dashboard
./scripts/test-management/coverage_report.py

# 3. Identify low-coverage files
# 4. Add tests for uncovered code
# 5. Verify improvement
test-cov
```

### Fast Development Cycle
```bash
# Quick smoke test (fastest)
test-smoke

# If smoke tests pass, run all unit tests
test-unit

# If all pass, run full suite
test-all
```

## Tips and Best Practices

1. **Use Watch Mode** during development for instant feedback
2. **Run Smoke Tests** frequently for quick validation
3. **Review Logs** when tests fail for detailed diagnostics
4. **Monitor Coverage** to ensure adequate testing
5. **Clean Cache** if you encounter strange test behavior
6. **Use Parallel Execution** for faster test runs
7. **Filter Tests** by marker or pattern to focus on specific areas

## Troubleshooting

### Tests not running
```bash
# Check pytest is installed
pip install pytest

# Verify test discovery
test-list
```

### Coverage not working
```bash
# Install coverage tools
pip install pytest-cov coverage

# Clean cache and re-run
test-clean
test-cov
```

### Watch mode not detecting changes
```bash
# Increase check interval
./scripts/test-management/test_watch.py --interval 2.0
```

### Logs not showing
```bash
# Ensure logs directory exists
mkdir -p logs/tests

# Run tests to generate logs
test-all
```

## Future Enhancements

Planned features:
- [ ] Coverage trend tracking over time
- [ ] Test performance benchmarking
- [ ] Automatic test generation suggestions
- [ ] Integration with CI/CD pipelines
- [ ] Test flakiness detection
- [ ] Parallel test execution optimization
- [ ] Test dependency visualization
- [ ] Custom test report templates

## Support

For issues or questions:
1. Check this README
2. Review log files for error details
3. Verify dependencies are installed
4. Check project documentation

## Scripts Overview

| Script | Purpose | Interactive | Use Case |
|--------|---------|-------------|----------|
| `test_menu.py` | Main test interface | Yes | Primary test management |
| `run_tests.sh` | Quick commands | No | Fast command-line access |
| `test_watch.py` | Auto-run on changes | No | Development workflow |
| `log_viewer.py` | View test logs | Yes | Debugging failures |
| `coverage_report.py` | Coverage analysis | Yes | Test quality review |

Choose the right tool for your task!
