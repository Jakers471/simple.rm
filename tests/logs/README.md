# Test Logs Directory

This directory contains logs generated during test execution.

## Log Files

- `test_execution.log` - Detailed test execution trace (DEBUG level, rotating 10MB max)
- `test_results.log` - Test results summary (INFO level, overwritten each run)
- `test_errors.log` - Error messages only (ERROR level, append mode)

## Subdirectories

- `coverage/` - Code coverage reports (HTML and JSON)
- `reports/` - Test reports and analytics
- `archive/` - Archived logs (created by clean command)

## Viewing Logs

Use the log viewer script for quick access:

```bash
# View results summary
../scripts/test-management/view_logs.sh results

# Live tail execution log
../scripts/test-management/view_logs.sh tail-exec

# Show failures
../scripts/test-management/view_logs.sh failures

# Show errors
../scripts/test-management/view_logs.sh errors

# Search logs
../scripts/test-management/view_logs.sh search "term"
```

## Maintenance

Logs are automatically rotated when they reach 10MB. Old logs are kept with numeric suffixes (.1, .2, etc.).

To archive and clean old logs:

```bash
../scripts/test-management/view_logs.sh clean
```

## Git Ignore

All log files are excluded from version control via `.gitignore`.

---

**Note**: Logs are created automatically by pytest. No manual setup required.
