# Risk Manager Logging - Quick Start Guide

## Installation

No installation needed! The logging system uses only Python standard library.

Optional: Install PyYAML for YAML configuration support:

```bash
pip install PyYAML
```

## 5-Minute Setup

### 1. Basic Setup (2 lines of code)

```python
from risk_manager.logging import setup_logging, get_logger

# Setup once at application startup
setup_logging()

# Get logger and start logging
logger = get_logger(__name__)
logger.info("Application started")
```

### 2. With Context Tracking

```python
from risk_manager.logging import setup_logging, get_logger, log_context

setup_logging()
logger = get_logger(__name__)

# Automatic correlation IDs and context
with log_context(account_id='ACC123', event_type='trade'):
    logger.info("Processing trade")  # Includes account_id + correlation_id
```

### 3. Production Configuration

```python
from risk_manager.logging import setup_logging
import logging

setup_logging(
    log_level=logging.INFO,      # INFO for production
    enable_json=True,             # Structured JSON logs
    enable_console=False,         # No console in production
)
```

## Common Patterns

### Pattern 1: API Call Logging

```python
from risk_manager.logging import get_specialized_logger, log_performance

api_logger = get_specialized_logger('api')

# Time API calls automatically
with log_performance(api_logger, 'fetch_positions', threshold_ms=100):
    response = api.get('/positions')
    api_logger.debug("Positions fetched", extra={'count': len(response)})
```

### Pattern 2: Enforcement Logging

```python
from risk_manager.logging import get_specialized_logger, log_context

enforcement_logger = get_specialized_logger('enforcement')

with log_context(account_id='ACC123', rule_id='MAX_LOSS'):
    if current_loss > max_loss:
        enforcement_logger.warning(
            "Rule breach detected",
            extra={
                'current_loss': current_loss,
                'max_loss': max_loss,
                'action': 'flatten_positions',
            }
        )
```

### Pattern 3: Error Handling

```python
from risk_manager.logging import get_specialized_logger

error_logger = get_specialized_logger('error')

try:
    risky_operation()
except Exception as e:
    error_logger.error("Operation failed", exc_info=True, extra={
        'operation': 'risky_operation',
        'context': 'additional info',
    })
```

### Pattern 4: Daemon Lifecycle

```python
from risk_manager.logging import setup_logging, get_specialized_logger
import logging

def main():
    # Setup logging
    setup_logging(log_level=logging.INFO, enable_json=True)

    daemon_logger = get_specialized_logger('daemon')

    daemon_logger.info("Daemon starting", extra={'version': '1.0.0'})

    try:
        # Run daemon
        run_daemon()
    except KeyboardInterrupt:
        daemon_logger.info("Daemon shutting down")
    except Exception as e:
        daemon_logger.error("Daemon crashed", exc_info=True)

if __name__ == '__main__':
    main()
```

## Log Files Created

After setup, check the `logs/` directory:

```
logs/
├── daemon.log       # All daemon activity
├── enforcement.log  # Rule breaches and actions
├── api.log         # API calls and responses
└── error.log       # Errors only
```

## View Logs

### JSON Logs (Production)

```bash
# Pretty-print JSON logs
cat logs/daemon.log | jq

# Filter by correlation_id
cat logs/daemon.log | jq 'select(.context.correlation_id == "abc123")'

# Find errors
cat logs/error.log | jq 'select(.level == "ERROR")'
```

### Human-Readable Logs (Development)

```python
setup_logging(enable_json=False)  # Disable JSON for dev
```

Then:

```bash
# Tail logs
tail -f logs/daemon.log

# Search logs
grep "ACC123" logs/daemon.log
```

## Testing

Run the examples:

```bash
python examples/logging_examples.py
```

Run the tests:

```bash
python -m pytest tests/test_logging.py -v
```

## Configuration File (Optional)

Edit `config/logging.yaml`:

```yaml
log_level: "INFO"
enable_json: true
enable_console: false

rotation:
  max_mb: 10
  backup_count: 7
```

Then load it:

```python
import yaml
from pathlib import Path

with open('config/logging.yaml') as f:
    config = yaml.safe_load(f)

setup_logging(**config)
```

## Performance Tips

1. **Use threshold logging** to avoid logging fast operations:
   ```python
   log_performance(logger, 'quick_op', threshold_ms=100)  # Only log if >100ms
   ```

2. **Use appropriate log levels**:
   - DEBUG: Development only
   - INFO: Important events
   - WARNING: Issues to investigate
   - ERROR: Failures

3. **Disable console in production**:
   ```python
   setup_logging(enable_console=False)
   ```

4. **Use specialized loggers** to route logs efficiently:
   ```python
   api_logger = get_specialized_logger('api')  # Goes to api.log only
   ```

## Security Checklist

✅ Sensitive data automatically masked (API keys, passwords, tokens)
✅ Email addresses partially masked
✅ Credit cards masked
✅ Thread-safe logging
✅ JSON injection prevented

## Troubleshooting

### No logs appearing?

```python
# Enable console to see logs immediately
setup_logging(enable_console=True, log_level=logging.DEBUG)
```

### Log files not created?

```python
# Check log directory exists
from pathlib import Path
log_dir = Path("logs")
print(f"Log dir exists: {log_dir.exists()}")
print(f"Files: {list(log_dir.glob('*.log'))}")
```

### Too many logs?

```python
# Increase log level
setup_logging(log_level=logging.WARNING)

# Use thresholds for performance logs
log_performance(logger, 'op', threshold_ms=500)  # Only log if >500ms
```

## Next Steps

1. Read the full documentation: `src/risk_manager/logging/README.md`
2. Review examples: `examples/logging_examples.py`
3. Run tests: `tests/test_logging.py`
4. Configure: `config/logging.yaml`

## Support

For issues or questions, check:
- Full README: `src/risk_manager/logging/README.md`
- Examples: `examples/logging_examples.py`
- Tests: `tests/test_logging.py`

---

**You're ready to go!** The logging system is production-ready and requires minimal setup.
