# Risk Manager Logging - Cheat Sheet

## 🚀 Setup (One Time)

```python
from risk_manager.logging import setup_logging
import logging

setup_logging(
    log_level=logging.INFO,    # INFO for production, DEBUG for dev
    enable_json=True,           # True for production, False for dev
    enable_console=False,       # False for production, True for dev
)
```

## 📝 Basic Logging

```python
from risk_manager.logging import get_logger

logger = get_logger(__name__)

logger.debug("Detailed info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

## 🎯 Specialized Loggers

```python
from risk_manager.logging import get_specialized_logger

daemon_logger = get_specialized_logger('daemon')
api_logger = get_specialized_logger('api')
enforcement_logger = get_specialized_logger('enforcement')
error_logger = get_specialized_logger('error')
```

## 🔗 Context & Correlation IDs

```python
from risk_manager.logging import log_context

# Automatic correlation ID tracking
with log_context(account_id='ACC123', event_type='trade'):
    logger.info("Processing")   # Includes correlation_id
    logger.info("Done")          # Same correlation_id!
```

## ⏱️ Performance Timing

```python
from risk_manager.logging import log_performance, timed

# Context manager
with log_performance(logger, 'api_call', threshold_ms=100):
    response = api.get('/data')

# Decorator
@timed(logger, operation='fetch_data')
def fetch_data():
    return database.query()
```

## 📊 Log with Extra Fields

```python
logger.info(
    "Trade processed",
    extra={
        'symbol': 'ES',
        'quantity': 1,
        'price': 4500.0,
    }
)
```

## 🔐 Security (Automatic)

API keys, passwords, and tokens are automatically masked:

```python
logger.info("API key: sk_live_12345")  # Logs as: api_key=***MASKED***
logger.info("Password: secret123")      # Logs as: password=***MASKED***
```

## 🎯 Common Patterns

### API Call

```python
api_logger = get_specialized_logger('api')

with log_performance(api_logger, 'fetch_positions'):
    api_logger.debug("Calling API", extra={'endpoint': '/positions'})
    response = api.get('/positions')
    api_logger.debug("Response received", extra={'status': 200})
```

### Enforcement

```python
enforcement_logger = get_specialized_logger('enforcement')

with log_context(account_id='ACC123', rule_id='MAX_LOSS'):
    enforcement_logger.warning(
        "Rule breach",
        extra={'current_loss': -500, 'max_loss': -400}
    )
```

### Error Handling

```python
error_logger = get_specialized_logger('error')

try:
    risky_operation()
except Exception:
    error_logger.error("Operation failed", exc_info=True)
```

## 📂 Log Files

After setup, logs go to:
- `logs/daemon.log` - All daemon activity
- `logs/enforcement.log` - Rule breaches
- `logs/api.log` - API calls
- `logs/error.log` - Errors only

## 🔍 View Logs

### JSON (Production)

```bash
# Pretty print
cat logs/daemon.log | jq

# Filter by account
cat logs/daemon.log | jq 'select(.context.account_id == "ACC123")'

# Find errors
cat logs/error.log | jq 'select(.level == "ERROR")'

# Track correlation ID
cat logs/*.log | jq 'select(.context.correlation_id == "abc-123")'
```

### Text (Development)

```bash
# Tail logs
tail -f logs/daemon.log

# Search
grep "ACC123" logs/daemon.log
```

## ⚙️ Configuration

### Python

```python
setup_logging(
    log_dir=Path("logs"),
    log_level=logging.INFO,
    enable_console=False,
    enable_json=True,
    max_bytes=10*1024*1024,  # 10MB
    backup_count=7,           # 7 days
)
```

### YAML

Edit `config/logging.yaml`:

```yaml
log_level: "INFO"
enable_json: true
enable_console: false
rotation:
  max_mb: 10
  backup_count: 7
```

## 🧪 Testing

```bash
# Run examples
python examples/logging_examples.py

# Run tests
python -m pytest tests/test_logging.py -v

# Quick test
python3 -c "
import sys; sys.path.insert(0, 'src')
from risk_manager.logging import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)
logger.info('Works!')
"
```

## 💡 Best Practices

1. **Always use context** for tracking
2. **Time critical operations** with thresholds
3. **Use specialized loggers** for routing
4. **Include extra fields** for structured data
5. **Use appropriate levels** (DEBUG/INFO/ERROR)
6. **Let masking handle secrets** automatically

## 🚨 Troubleshooting

### No logs?

```python
setup_logging(enable_console=True, log_level=logging.DEBUG)
```

### Too many logs?

```python
setup_logging(log_level=logging.WARNING)
```

### Slow logging?

```python
log_performance(logger, 'op', threshold_ms=500)  # Only log if >500ms
```

## 📚 More Info

- Quick Start: `LOGGING_QUICK_START.md`
- Full Docs: `src/risk_manager/logging/README.md`
- Examples: `examples/logging_examples.py`
- Implementation: `LOGGING_IMPLEMENTATION.md`
