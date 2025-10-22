# Test Logging System Guide

## Overview

The Simple Risk Manager includes a comprehensive logging system for all tests, providing detailed execution traces, error tracking, and performance monitoring.

## Components

### 1. Logging Configuration (`tests/logging_config.yaml`)

YAML-based logging configuration with:
- **Rotating file handler**: 10MB max file size, 5 backup files
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR
- **Separate handlers**: Console, file, test results, errors
- **Custom formatters**: Detailed timestamps and source location

### 2. Pytest Plugin (`tests/pytest_logging.py`)

Automatic pytest integration that:
- Configures logging at test session start
- Creates log directories automatically
- Logs test execution lifecycle (setup, call, teardown)
- Tracks pass/fail/skip statistics
- Timestamps all test sessions

### 3. Log Utilities (`tests/log_utils.py`)

Helper functions for consistent logging:

```python
from tests.log_utils import (
    log_test_start,
    log_test_pass,
    log_test_fail,
    log_test_skip,
    log_test_info,
    logged_test,
    log_section,
    log_api_call,
    log_database_query
)

# Manual logging
def test_something():
    log_test_start("test_something")
    # ... test code ...
    log_test_pass("test_something", duration=1.234)

# Automatic logging with decorator
@logged_test
def test_automatic():
    assert True
    # Automatically logs start, duration, and result

# Organize test output
def test_suite():
    log_section("API Tests")
    log_subsection("GET Endpoints")
    # ... tests ...

# Track API calls
log_api_call("/api/positions", "GET", 200)

# Track database queries
log_database_query("SELECT", "positions", duration_ms=15.2)
```

### 4. Log Viewer Script (`scripts/test-management/view_logs.sh`)

Command-line utility for analyzing logs:

```bash
# View test results summary
./scripts/test-management/view_logs.sh results

# Live tail execution log
./scripts/test-management/view_logs.sh tail-exec

# Show all failures
./scripts/test-management/view_logs.sh failures

# Show all errors
./scripts/test-management/view_logs.sh errors

# Show passed tests
./scripts/test-management/view_logs.sh passes

# Show skipped tests
./scripts/test-management/view_logs.sh skipped

# Show coverage statistics
./scripts/test-management/view_logs.sh coverage

# Show last test run details
./scripts/test-management/view_logs.sh last-run

# Search logs for specific term
./scripts/test-management/view_logs.sh search "ValueError"

# Archive and clean old logs
./scripts/test-management/view_logs.sh clean
```

## Log Files

### Location: `tests/logs/`

#### `test_execution.log`
- **Level**: DEBUG
- **Content**: Detailed execution trace with timestamps
- **Size**: Rotating, 10MB max, 5 backups
- **Format**: `[YYYY-MM-DD HH:MM:SS] LEVEL [module:line] message`

#### `test_results.log`
- **Level**: INFO
- **Content**: Test results summary (pass/fail/skip)
- **Mode**: Overwritten each run
- **Format**: `YYYY-MM-DD HH:MM:SS | LEVEL | message`

#### `test_errors.log`
- **Level**: ERROR
- **Content**: All errors and failures
- **Mode**: Append
- **Format**: `[YYYY-MM-DD HH:MM:SS] ERROR [module:line] message`

### Subdirectories

- `logs/coverage/` - Coverage reports
- `logs/reports/` - HTML and JSON test reports
- `logs/archive/` - Archived logs (created by clean command)

## Usage Examples

### Running Tests with Logging

```bash
# Run all tests (logging is automatic)
pytest

# Run specific test with verbose output
pytest tests/test_risk_rules.py -v

# Run with live log output
pytest --log-cli-level=INFO

# Run with coverage
pytest --cov=src --cov-report=html:tests/logs/coverage/
```

### Viewing Logs During Development

```bash
# Terminal 1: Run tests
pytest -v

# Terminal 2: Watch execution log
./scripts/test-management/view_logs.sh tail-exec

# Terminal 3: Watch results
./scripts/test-management/view_logs.sh tail-results
```

### Analyzing Test Failures

```bash
# Show all failures
./scripts/test-management/view_logs.sh failures

# Show detailed errors
./scripts/test-management/view_logs.sh errors

# Search for specific error
./scripts/test-management/view_logs.sh search "ConnectionError"

# View last run details
./scripts/test-management/view_logs.sh last-run
```

### Integration with Test Files

Add logging to your test files:

```python
# tests/test_example.py
import pytest
from tests.log_utils import (
    logged_test,
    log_section,
    log_test_info,
    log_api_call
)

def test_suite():
    """Example test suite with logging"""
    log_section("Example Test Suite")

    # Test with manual logging
    def test_manual():
        log_test_info("test_manual", "Testing API endpoint")
        response = api_client.get("/positions")
        log_api_call("/positions", "GET", response.status_code)
        assert response.status_code == 200

    # Test with automatic logging
    @logged_test
    def test_automatic():
        """This test is automatically logged"""
        result = calculate_risk()
        assert result > 0
```

## Pytest Configuration

The logging system integrates with pytest's `conftest.py`:

```python
# tests/conftest.py
import logging

@pytest.fixture
def logger():
    """Get logger instance for tests"""
    return logging.getLogger('test_runner')

def test_with_logger(logger):
    logger.info("Starting complex test")
    # ... test code ...
    logger.debug("Intermediate step complete")
```

## Best Practices

1. **Use decorators for simple tests**: `@logged_test` provides automatic timing and error tracking
2. **Use manual logging for complex tests**: Gives fine-grained control over log messages
3. **Organize with sections**: Use `log_section()` and `log_subsection()` to structure output
4. **Log API interactions**: Track all API calls with `log_api_call()`
5. **Log database queries**: Track database operations with `log_database_query()`
6. **Clean logs regularly**: Archive old logs to save disk space
7. **Review errors promptly**: Check `test_errors.log` after failed runs
8. **Monitor coverage**: Track code coverage trends over time

## Troubleshooting

### Logs not appearing

1. Check that `tests/logging_config.yaml` exists
2. Verify `tests/pytest_logging.py` is loaded
3. Ensure log directories exist: `mkdir -p tests/logs/{coverage,reports}`
4. Check pytest output for configuration errors

### Log files too large

```bash
# Clean old logs
./scripts/test-management/view_logs.sh clean

# Or manually set smaller max file size in logging_config.yaml:
# maxBytes: 5242880  # 5MB instead of 10MB
```

### Permission errors

```bash
# Make log viewer executable
chmod +x scripts/test-management/view_logs.sh

# Fix log directory permissions
chmod 755 tests/logs
```

## Integration with CI/CD

The logging system works seamlessly in CI environments:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --log-cli-level=INFO

- name: Upload test logs
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-logs
    path: tests/logs/

- name: Upload coverage report
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report
    path: tests/logs/coverage/
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review failure trends in `test_results.log`
2. **Monthly**: Archive old logs with `view_logs.sh clean`
3. **Quarterly**: Update logging configuration if needed
4. **After major changes**: Review and update log messages

### Updating Configuration

To modify logging behavior, edit `tests/logging_config.yaml`:

```yaml
# Change log level
root:
  level: INFO  # Change to WARNING to reduce verbosity

# Add new handler
handlers:
  email_errors:
    class: logging.handlers.SMTPHandler
    level: ERROR
    # ... email configuration ...
```

## Related Documentation

- [Testing Guide](TESTING_GUIDE.md) - Main testing documentation
- [Error Handling](../project-specs/SPECS/07-ERROR-HANDLING/) - Error handling specifications
- [pytest Documentation](https://docs.pytest.org/) - Official pytest docs

---

**Note**: Logs are automatically created during test execution. The `.gitignore` file excludes log files from version control.
