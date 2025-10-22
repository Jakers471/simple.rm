# Risk Manager Logging System

Production-ready logging configuration for the Risk Manager daemon with structured logging, correlation IDs, performance timing, and sensitive data masking.

## Features

### 1. Multiple Specialized Log Files
- **daemon.log** - All daemon activity and operations
- **enforcement.log** - Rule breaches and enforcement actions
- **api.log** - TopstepX API calls and responses
- **error.log** - Errors and exceptions only

### 2. Structured Logging
- JSON format for machine parsing
- Automatic context injection
- Correlation IDs for event tracking
- Thread-safe operation

### 3. Performance Timing
- Context managers for timing operations
- Decorators for function timing
- Threshold-based logging (only log slow operations)
- Performance metrics collection

### 4. Security
- Automatic masking of sensitive data
- API keys, tokens, passwords redacted
- Email masking
- Custom pattern support

### 5. Log Rotation
- Automatic rotation at 10MB
- Keep 7 days of logs
- Compression support (gzip)

## Quick Start

### Basic Usage

```python
from risk_manager.logging import setup_logging, get_logger

# Setup once at application startup
setup_logging(log_level=logging.INFO)

# Get logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)
```

### With Context (Correlation IDs)

```python
from risk_manager.logging import get_logger, log_context

logger = get_logger(__name__)

# Context automatically adds fields to all logs
with log_context(account_id='ACC123', event_type='trade'):
    logger.info("Processing trade")  # Includes account_id and correlation_id
    logger.info("Trade completed")   # Same correlation_id
```

### Performance Timing

```python
from risk_manager.logging import get_logger, log_performance

logger = get_logger(__name__)

# Time operations with context manager
with log_performance(logger, 'api_call', threshold_ms=100):
    response = api.get_positions()

# Or use decorator
from risk_manager.logging import timed

@timed(logger, operation='fetch_data')
def fetch_data():
    return database.query()
```

### Specialized Loggers

```python
from risk_manager.logging import get_specialized_logger

# Get specialized logger for specific concerns
api_logger = get_specialized_logger('api')
enforcement_logger = get_specialized_logger('enforcement')

# Log to specific files
api_logger.debug("API call", extra={'endpoint': '/positions'})
enforcement_logger.warning("Rule breach", extra={'rule_id': 'MAX_LOSS'})
```

## Complete Example

```python
from risk_manager.logging import (
    setup_logging,
    get_logger,
    get_specialized_logger,
    log_context,
    log_performance,
)
import logging

# Setup logging system
setup_logging(
    log_level=logging.INFO,
    enable_json=True,  # Structured logging
    enable_console=True,
)

# Get loggers
daemon_logger = get_specialized_logger('daemon')
api_logger = get_specialized_logger('api')
enforcement_logger = get_specialized_logger('enforcement')

# Process trade with full tracking
with log_context(
    account_id='ACC123',
    event_type='trade_processing',
    symbol='ES',
):
    daemon_logger.info("Trade received", extra={'side': 'buy', 'qty': 1})

    # Time API call
    with log_performance(api_logger, 'fetch_positions'):
        positions = api.get_positions()

    # Check rules
    if violation_detected:
        enforcement_logger.warning(
            "Rule breach",
            extra={
                'rule_id': 'MAX_LOSS',
                'current_loss': -500,
                'max_loss': -400,
            }
        )
```

## Configuration

### Environment Variables

```bash
# Set log directory
export RISK_MANAGER_LOG_DIR="/var/log/risk-manager"

# Set log level
export RISK_MANAGER_LOG_LEVEL="DEBUG"
```

### YAML Configuration

Edit `config/logging.yaml`:

```yaml
log_dir: "logs"
log_level: "INFO"
enable_console: true
enable_json: true

rotation:
  max_mb: 10
  backup_count: 7

performance:
  threshold_ms: 100

security:
  mask_sensitive: true
```

## Log Format

### JSON Format (Production)

```json
{
  "timestamp": "2025-10-21T10:30:45.123Z",
  "level": "INFO",
  "logger": "risk_manager.daemon",
  "message": "Trade processed",
  "module": "daemon",
  "function": "process_trade",
  "line": 142,
  "context": {
    "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "account_id": "ACC123",
    "event_type": "trade"
  },
  "symbol": "ES",
  "side": "buy",
  "quantity": 1
}
```

### Human-Readable Format (Development)

```
2025-10-21 10:30:45 - INFO - Trade processed - symbol=ES side=buy qty=1
```

## Performance Monitoring

### Track Operation Performance

```python
from risk_manager.logging import PerformanceTracker

tracker = PerformanceTracker()

# Record operations
with log_performance(logger, 'api_call') as timer:
    api.call()
    tracker.record('api_call', timer.duration_ms)

# Get summary statistics
summary = tracker.get_summary('api_call')
print(f"Avg: {summary['avg_ms']:.2f}ms")
print(f"P95: {summary['p95_ms']:.2f}ms")
```

## Security

### Automatic Masking

The following patterns are automatically masked:

- API keys: `api_key=***MASKED***`
- Tokens: `Bearer ***MASKED***`
- Passwords: `password=***MASKED***`
- Authorization headers: `Authorization: ***MASKED***`
- Credit cards: `****-****-****-****`
- SSN: `***-**-****`
- Emails: `***@example.com`

### Custom Masking Patterns

```python
import re
from risk_manager.logging import MaskingFilter

# Add custom patterns
custom_filter = MaskingFilter(additional_patterns=[
    (re.compile(r'account_number=\d+'), 'account_number=***'),
])
```

## Thread Safety

All components are thread-safe:

- Context uses `contextvars` (async-safe)
- Handlers use `threading.Lock`
- Performance tracking synchronized

## Testing

Run the example:

```bash
python examples/logging_examples.py
```

Check generated logs:

```bash
ls -lh logs/
cat logs/daemon.log | jq  # Pretty-print JSON logs
```

## Integration with Daemon

```python
# daemon.py
from risk_manager.logging import setup_logging, get_specialized_logger
import logging

def main():
    # Setup logging
    setup_logging(
        log_level=logging.INFO,
        enable_json=True,
    )

    daemon_logger = get_specialized_logger('daemon')
    daemon_logger.info("Risk Manager daemon started")

    # Your daemon code here

if __name__ == '__main__':
    main()
```

## Best Practices

1. **Use correlation IDs** - Wrap operations in `log_context()` to track events
2. **Time performance** - Use `log_performance()` for critical operations
3. **Use specialized loggers** - Route logs to appropriate files
4. **Log structured data** - Use `extra={}` for machine-readable fields
5. **Don't log secrets** - Masking is automatic but avoid logging sensitive data
6. **Use appropriate levels** - DEBUG for details, INFO for events, ERROR for failures
7. **Include context** - Always log account_id, rule_id, symbol when available

## Troubleshooting

### Logs not appearing

```python
# Ensure setup is called
setup_logging()

# Check log level
setup_logging(log_level=logging.DEBUG)

# Enable console output
setup_logging(enable_console=True)
```

### Performance issues

```python
# Reduce log level in production
setup_logging(log_level=logging.INFO)

# Disable console in production
setup_logging(enable_console=False)

# Use threshold for performance logs
log_performance(logger, 'op', threshold_ms=100)
```

### Large log files

```python
# Adjust rotation settings
setup_logging(
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=3,  # Keep 3 days
)
```

## API Reference

### Functions

- `setup_logging(**kwargs)` - Initialize logging system
- `get_logger(name)` - Get module logger
- `get_specialized_logger(type)` - Get specialized logger
- `log_context(**kwargs)` - Context manager for correlation
- `log_performance(logger, operation)` - Context manager for timing
- `timed(logger, operation)` - Decorator for timing
- `get_log_context()` - Get current context dict
- `get_correlation_id()` - Get current correlation ID

### Classes

- `LogConfig` - Main configuration class
- `StructuredFormatter` - JSON formatter
- `MaskingFilter` - Sensitive data filter
- `LogContext` - Context management
- `PerformanceTimer` - Manual timing
- `PerformanceMetrics` - Metrics collection
- `PerformanceTracker` - Global metrics tracker

## License

Part of Simple Risk Manager SDK
