# End-to-End Test Suite

## Overview

This directory contains 27 comprehensive end-to-end (E2E) tests for the Simple Risk Manager daemon. These tests verify complete workflows from startup to shutdown, simulating real-world trading scenarios.

## Test Coverage Summary

| File | Tests | Category | Test IDs |
|------|-------|----------|----------|
| `test_complete_trading_flow.py` | 5 | Complete trading workflows | E2E-001 to E2E-005 |
| `test_rule_violations.py` | 8 | Rule breach scenarios | E2E-006 to E2E-013 |
| `test_signalr_triggers.py` | 5 | Event-driven workflows | E2E-014 to E2E-018 |
| `test_daily_reset.py` | 3 | Daily reset operations | E2E-019 to E2E-021 |
| `test_network_recovery.py` | 4 | Network & crash recovery | E2E-022 to E2E-025 |
| `test_performance.py` | 2 | Performance & stress tests | E2E-026 to E2E-027 |
| **Total** | **27** | **Comprehensive E2E coverage** | |

## Test Categories

### 1. Complete Trading Flows (5 tests)
Tests full lifecycle workflows from daemon startup to shutdown:
- **E2E-001**: Normal trading flow (no violations)
- **E2E-002**: Trading with stop-loss placement
- **E2E-003**: Daemon restart with state recovery
- **E2E-004**: Multi-account monitoring
- **E2E-005**: Full trading day simulation (8 hours)

### 2. Rule Violations (8 tests)
Tests all major rule breach scenarios with enforcement:
- **E2E-006**: RULE-001 - Max contracts exceeded
- **E2E-007**: RULE-003 - Daily realized loss limit
- **E2E-008**: RULE-004 - Daily unrealized loss (per position)
- **E2E-009**: RULE-008 - No stop-loss grace period expired
- **E2E-010**: RULE-011 - Blocked symbol position
- **E2E-011**: RULE-006 - Trade frequency limit
- **E2E-012**: RULE-009 - Session block outside hours
- **E2E-013**: RULE-005 - Max unrealized profit

### 3. SignalR Event Triggers (5 tests)
Tests real-time event processing and rule triggering:
- **E2E-014**: Quote update triggers unrealized loss rule
- **E2E-015**: Multiple positions with different quote updates
- **E2E-016**: Order event triggers stop-loss detection
- **E2E-017**: Account event triggers auth loss guard
- **E2E-018**: High-frequency quote updates (stress test)

### 4. Daily Reset Workflows (3 tests)
Tests daily reset scheduler functionality:
- **E2E-019**: Daily reset at scheduled time
- **E2E-020**: Reset with multiple accounts
- **E2E-021**: Timezone handling for reset

### 5. Network & Recovery (4 tests)
Tests resilience and crash recovery:
- **E2E-022**: SignalR disconnection and reconnection
- **E2E-023**: Market Hub disconnection - quote recovery
- **E2E-024**: Daemon crash recovery - state preservation
- **E2E-025**: Multiple crash-recovery cycles

### 6. Performance Tests (2 tests)
Tests system performance under load:
- **E2E-026**: High volume event processing (1000+ events)
- **E2E-027**: Long-running stability test (2 hours)

## Running E2E Tests

### Run All E2E Tests
```bash
pytest tests/e2e/ -v -m e2e
```

### Run Specific Category
```bash
pytest tests/e2e/test_complete_trading_flow.py -v
pytest tests/e2e/test_rule_violations.py -v
pytest tests/e2e/test_signalr_triggers.py -v
```

### Run Specific Test
```bash
pytest tests/e2e/test_complete_trading_flow.py::TestCompleteTradingFlows::test_e2e_001_normal_trading_flow_no_violations -v
```

### Run Without Slow Tests
```bash
pytest tests/e2e/ -v -m "e2e and not slow"
```

### Run Performance Tests Only
```bash
pytest tests/e2e/test_performance.py -v -m stress
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.e2e` - All end-to-end tests
- `@pytest.mark.slow` - Tests that take > 1 minute
- `@pytest.mark.stress` - High-load stress tests
- `@pytest.mark.long_running` - Tests that take > 30 minutes
- `@pytest.mark.timeout(N)` - Tests with specific timeout limits

## Test Duration

| Category | Average Duration | Total Duration |
|----------|-----------------|----------------|
| Complete Trading Flows | ~2 min/test | ~10 minutes |
| Rule Violations | ~1 min/test | ~8 minutes |
| SignalR Triggers | ~1 min/test | ~5 minutes |
| Daily Reset | ~2 min/test | ~6 minutes |
| Network Recovery | ~2 min/test | ~8 minutes |
| Performance | ~10 min/test | ~20 minutes |
| **Total** | | **~57 minutes** |

*Performance test E2E-027 can take up to 2 hours if run at full duration*

## Test Structure

Each E2E test follows this structure:

```python
def test_e2e_XXX_description(
    self,
    test_daemon,          # Daemon test harness
    mock_api,             # Mock TopstepX REST API
    mock_signalr_user_hub,  # Mock User Hub
    mock_signalr_market_hub,  # Mock Market Hub
    test_database,        # Test SQLite database
    test_config          # Test configuration
):
    """
    E2E-XXX: Test Title

    Given: Initial conditions
    When: Actions taken
    Then: Expected outcomes

    Duration: ~X minutes
    """
    # Test implementation
```

## Fixtures Required

E2E tests require the following pytest fixtures:

- `test_daemon` - Daemon test harness for start/stop/crash simulation
- `mock_api` - Mock TopstepX REST API endpoints
- `mock_signalr_user_hub` - Mock SignalR User Hub for events
- `mock_signalr_market_hub` - Mock SignalR Market Hub for quotes
- `test_database` - Isolated SQLite test database
- `test_config` - Test configuration (accounts, risk rules)
- `time_simulator` - Time acceleration/control for scheduling tests
- `performance_monitor` - Performance metrics collection

See `tests/conftest.py` for fixture implementations.

## Expected Outcomes

All E2E tests verify:

1. **Functionality**: Complete workflows execute correctly
2. **State Management**: State persisted and recovered accurately
3. **Enforcement**: Rules trigger and actions execute correctly
4. **Resilience**: System recovers from crashes and disconnections
5. **Performance**: Acceptable latency and throughput
6. **Integration**: All components work together correctly

## Test Data

E2E tests use:

- **Mock Accounts**: 12345, 67890, 11111, 22222, 33333
- **Mock Symbols**: MNQ, ES, NQ, YM, BTC, ETH, GC
- **Mock Contract IDs**: CON.F.US.{SYMBOL}.U25
- **Test Database**: SQLite in-memory or temporary file
- **Mock Timestamps**: UTC ISO 8601 format

## Continuous Integration

E2E tests are designed for CI/CD pipelines:

```yaml
# .github/workflows/e2e-tests.yml
- name: Run E2E Tests
  run: |
    pytest tests/e2e/ -v -m "e2e and not long_running" --timeout=300
```

## Debugging E2E Tests

Enable verbose logging:

```bash
pytest tests/e2e/ -v -s --log-cli-level=DEBUG
```

Run with pdb on failure:

```bash
pytest tests/e2e/ -v --pdb
```

Generate HTML report:

```bash
pytest tests/e2e/ -v --html=report.html --self-contained-html
```

## Known Issues

- **E2E-027**: Long-running test takes 2 hours at full duration. Can be time-accelerated for faster execution.
- **E2E-026**: High-volume test may be CPU-intensive on slower systems.
- **E2E-003**: Crash simulation may leave temp files in /tmp on failure.

## Contributing

When adding new E2E tests:

1. Follow the existing test structure (Given/When/Then)
2. Use descriptive test IDs (E2E-XXX)
3. Add appropriate pytest markers
4. Document expected duration
5. Update this README with new test details

## Related Documentation

- Test specifications: `/test-specs/e2e/test_spec_e2e_workflows.md`
- Integration tests: `/tests/integration/`
- Unit tests: `/tests/unit/`
- Conftest fixtures: `/tests/conftest.py`
