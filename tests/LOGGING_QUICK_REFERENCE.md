# Test Logging Quick Reference

## Quick Commands

```bash
# View results summary
./scripts/test-management/view_logs.sh results

# Live tail execution
./scripts/test-management/view_logs.sh tail-exec

# Show failures
./scripts/test-management/view_logs.sh failures

# Show errors
./scripts/test-management/view_logs.sh errors

# Search logs
./scripts/test-management/view_logs.sh search "ERROR_TEXT"

# Clean old logs
./scripts/test-management/view_logs.sh clean
```

## Quick Code Snippets

### Basic Logging
```python
from tests.log_utils import logged_test

@logged_test
def test_something():
    assert True
```

### Manual Logging
```python
from tests.log_utils import log_test_start, log_test_pass

def test_manual():
    log_test_start("test_manual")
    # ... test code ...
    log_test_pass("test_manual", duration=1.5)
```

### Section Organization
```python
from tests.log_utils import log_section, log_subsection

def test_suite():
    log_section("Risk Rules Tests")
    log_subsection("Daily Loss Limit")
    # ... tests ...
```

### API Call Logging
```python
from tests.log_utils import log_api_call

response = client.get("/api/positions")
log_api_call("/api/positions", "GET", response.status_code)
```

### Database Query Logging
```python
from tests.log_utils import log_database_query

result = db.query("SELECT * FROM positions")
log_database_query("SELECT", "positions", duration_ms=12.5)
```

### Info Messages
```python
from tests.log_utils import log_test_info

log_test_info("test_name", "Starting data validation")
```

### Use Logger Fixture
```python
def test_with_logger(logger):
    logger.info("Custom log message")
    logger.debug("Debug information")
```

## Log Files

| File | Purpose | Level | Location |
|------|---------|-------|----------|
| `test_execution.log` | Detailed trace | DEBUG | `tests/logs/` |
| `test_results.log` | Pass/fail summary | INFO | `tests/logs/` |
| `test_errors.log` | Errors only | ERROR | `tests/logs/` |

## Log Levels

- **DEBUG**: Detailed information, typically of interest only when diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: An indication that something unexpected happened
- **ERROR**: Due to a more serious problem, the software has not been able to perform some function

## Common Patterns

### Test Setup/Teardown
```python
@pytest.fixture
def my_fixture(logger):
    logger.info("Setting up fixture")
    yield resource
    logger.info("Tearing down fixture")
```

### Parameterized Tests
```python
@logged_test
@pytest.mark.parametrize("value", [1, 2, 3])
def test_params(value):
    assert value > 0
```

### Async Tests
```python
@logged_test
async def test_async():
    result = await async_function()
    assert result
```

## Tips

1. Always use `@logged_test` for simple test functions
2. Use manual logging for complex multi-step tests
3. Log API calls and database queries for debugging
4. Use sections to organize large test suites
5. Review `test_errors.log` after failures
6. Archive old logs regularly with `view_logs.sh clean`
7. Search logs with specific error messages to find patterns

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No logs appearing | Check `tests/logging_config.yaml` exists |
| Log files too large | Run `view_logs.sh clean` |
| Permission denied | Run `chmod +x scripts/test-management/view_logs.sh` |
| Missing directories | Run `mkdir -p tests/logs/{coverage,reports}` |
