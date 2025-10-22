# Testing Readiness - Simple Risk Manager

**Generated:** 2025-10-22
**Purpose:** Implementation readiness assessment for testing infrastructure
**Version:** 1.0
**Status:** Implementation Ready

---

## Table of Contents

1. [Framework Selection](#framework-selection)
2. [Test Environment Setup](#test-environment-setup)
3. [Coverage Configuration](#coverage-configuration)
4. [CI/CD Integration](#cicd-integration)
5. [Test Execution Strategy](#test-execution-strategy)
6. [Reporting & Metrics](#reporting--metrics)

---

# Framework Selection

## Recommended Testing Stack

### 1. pytest (Unit & Integration Tests)

**Why pytest:**
- Industry standard for Python testing
- Excellent fixture support (critical for mock data)
- Parametrized testing (reduce code duplication)
- Rich plugin ecosystem
- Parallel execution with pytest-xdist
- Coverage integration with pytest-cov

**Installation:**
```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-timeout
```

**Version Requirements:**
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0 (for async SignalR tests)
- pytest-cov >= 4.1.0 (coverage reporting)
- pytest-xdist >= 3.3.0 (parallel execution)
- pytest-timeout >= 2.1.0 (test timeouts)

---

### 2. pytest-mock (Mocking Framework)

**Why pytest-mock:**
- Clean integration with pytest
- Simplified unittest.mock usage
- Automatic cleanup after tests
- Mock SignalR connections, REST API calls, SQLite

**Installation:**
```bash
pip install pytest-mock
```

**Usage:**
```python
def test_close_positions(mocker):
    """Test enforcement action with mocked API"""
    mock_api = mocker.patch('src.api.rest_client.RestClient.post')
    mock_api.return_value = {'success': True}

    enforcement = EnforcementActions()
    result = enforcement.close_all_positions(account_id=123)

    assert result is True
    assert mock_api.called
```

---

### 3. freezegun (Time Testing)

**Why freezegun:**
- Mock datetime for time-sensitive tests
- Essential for testing daily reset, lockout expiry, session times
- Simple API

**Installation:**
```bash
pip install freezegun
```

**Usage:**
```python
from freezegun import freeze_time

@freeze_time("2025-01-17 16:59:00")
def test_daily_reset_before():
    """Test reset logic before 5 PM"""
    scheduler = ResetScheduler()
    accounts = scheduler.check_reset_times()
    assert len(accounts) == 0  # No reset yet

@freeze_time("2025-01-17 17:00:00")
def test_daily_reset_at_time():
    """Test reset logic at 5 PM"""
    scheduler = ResetScheduler()
    accounts = scheduler.check_reset_times()
    assert len(accounts) == 1  # Reset triggered
```

---

### 4. responses (HTTP Mocking)

**Why responses:**
- Mock TopstepX REST API responses
- Intercepts requests at HTTP level
- Realistic test scenarios

**Installation:**
```bash
pip install responses
```

**Usage:**
```python
import responses

@responses.activate
def test_fetch_contract():
    """Test contract API call with mocked response"""
    responses.add(
        responses.GET,
        'https://api.topstepx.com/api/Contract/searchById',
        json={'id': 'CON.F.US.MNQ.U25', 'tickSize': 0.25},
        status=200
    )

    contract = contract_cache.fetch_contract('CON.F.US.MNQ.U25')
    assert contract.tick_size == 0.25
```

---

### 5. faker (Test Data Generation)

**Why faker:**
- Generate realistic test data (account IDs, timestamps, prices)
- Reduces fixture maintenance
- Useful for load/performance tests

**Installation:**
```bash
pip install faker
```

**Usage:**
```python
from faker import Faker

fake = Faker()

def test_with_random_data():
    """Test with generated data"""
    account_id = fake.random_int(min=100, max=999)
    pnl = fake.pyfloat(min_value=-1000, max_value=1000)

    # Use in test...
```

---

## Optional: End-to-End Testing (Future)

### Playwright (If Web UI Added)

**Installation:**
```bash
pip install playwright
playwright install
```

**Not needed for Phase 1** (CLI-only system)

---

# Test Environment Setup

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py                      # Shared pytest fixtures
│
├── fixtures/                        # Test data (see TEST_FIXTURES_PLAN.md)
│   ├── api/
│   ├── signalr/
│   ├── database/
│   └── config/
│
├── unit/                            # Unit tests
│   ├── __init__.py
│   ├── test_enforcement_actions.py
│   ├── test_lockout_manager.py
│   ├── test_pnl_tracker.py
│   └── test_rules/
│       ├── __init__.py
│       ├── test_max_contracts.py
│       └── (one file per rule)
│
├── integration/                     # Integration tests
│   ├── __init__.py
│   ├── test_api_integration.py
│   ├── test_signalr_integration.py
│   ├── test_persistence.py
│   └── test_full_workflow.py
│
├── e2e/                            # End-to-end tests
│   ├── __init__.py
│   ├── test_complete_workflows.py
│   ├── test_performance.py
│   └── test_error_handling.py
│
└── utils/                          # Test utilities
    ├── __init__.py
    ├── mock_api.py                 # Mock API server
    ├── mock_signalr.py             # Mock SignalR hub
    └── test_helpers.py             # Shared test helpers
```

---

## pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output options
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    -n auto
    --maxfail=1

# Markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require external services)
    e2e: End-to-end tests (full system)
    slow: Tests that take > 1 second
    critical: Critical path tests (run first)

# Timeouts
timeout = 300
timeout_method = thread

# Warnings
filterwarnings =
    error
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

# Coverage
[coverage:run]
source = src
omit =
    */tests/*
    */conftest.py
    */setup.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## conftest.py (Shared Fixtures)

**File:** `tests/conftest.py`

```python
"""
Shared pytest fixtures for all tests.
Loaded automatically by pytest.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

# Import fixture utilities
from tests.utils.mock_api import MockTopStepXAPI
from tests.utils.mock_signalr import MockSignalRHub


# ========================
# Configuration Fixtures
# ========================

@pytest.fixture(scope="session")
def fixture_dir():
    """Path to fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_config(fixture_dir):
    """Load test risk configuration"""
    import yaml
    config_path = fixture_dir / "config" / "risk_config_test.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def test_accounts(fixture_dir):
    """Load test accounts configuration"""
    import yaml
    config_path = fixture_dir / "config" / "accounts_test.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


# ========================
# Database Fixtures
# ========================

@pytest.fixture
def temp_database():
    """Create temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize schema
    conn = sqlite3.connect(db_path)
    # TODO: Run schema creation SQL
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def populated_database(temp_database, fixture_dir):
    """Create database with test data"""
    conn = sqlite3.connect(temp_database)

    # Load all fixture SQL files
    for sql_file in (fixture_dir / "database").glob("*.sql"):
        with open(sql_file) as f:
            conn.executescript(f.read())

    conn.commit()
    conn.close()

    return temp_database


# ========================
# API Mocking Fixtures
# ========================

@pytest.fixture
def mock_api():
    """Mock TopstepX REST API"""
    api = MockTopStepXAPI()
    api.start()
    yield api
    api.stop()


@pytest.fixture
def mock_signalr():
    """Mock SignalR WebSocket hub"""
    hub = MockSignalRHub()
    hub.start()
    yield hub
    hub.stop()


# ========================
# Module Fixtures
# ========================

@pytest.fixture
def lockout_manager(temp_database):
    """Initialized lockout manager"""
    from src.state.lockout_manager import LockoutManager
    manager = LockoutManager(database_path=temp_database)
    return manager


@pytest.fixture
def pnl_tracker(temp_database):
    """Initialized PNL tracker"""
    from src.state.pnl_tracker import PNLTracker
    tracker = PNLTracker(database_path=temp_database)
    return tracker


@pytest.fixture
def state_manager(temp_database):
    """Initialized state manager"""
    from src.state.state_manager import StateManager
    manager = StateManager(database_path=temp_database)
    return manager


# ========================
# Time Mocking Fixtures
# ========================

@pytest.fixture
def frozen_time():
    """Freeze time at 2025-01-17 14:00:00"""
    from freezegun import freeze_time
    with freeze_time("2025-01-17 14:00:00"):
        yield


@pytest.fixture
def reset_time():
    """Freeze time at daily reset (5:00 PM)"""
    from freezegun import freeze_time
    with freeze_time("2025-01-17 17:00:00"):
        yield


# ========================
# Test Account Fixtures
# ========================

@pytest.fixture
def test_account_id():
    """Standard test account ID"""
    return 123


@pytest.fixture
def test_contract_id():
    """Standard test contract ID (MNQ)"""
    return "CON.F.US.MNQ.U25"
```

---

# Coverage Configuration

## Coverage Targets

| Component | Target Coverage | Measurement Type |
|-----------|-----------------|------------------|
| Core Modules (MOD-001 to MOD-009) | 95% | Line coverage |
| Risk Rules (RULE-001 to RULE-012) | 90% | Line + branch coverage |
| API Integration | 85% | Line coverage |
| Event Router | 95% | Branch coverage |
| **Overall** | **90%** | Line coverage |

---

## Coverage Report Generation

### Command Line

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Output

```
---------- coverage: platform linux, python 3.11.0 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/__init__.py                             0      0   100%
src/core/daemon.py                        250      5    98%   123, 456-458
src/core/event_router.py                  150      3    98%   89, 145
src/enforcement/actions.py                120      2    98%   67, 89
src/state/lockout_manager.py              150      1    99%   142
src/state/pnl_tracker.py                  130      5    96%   78-82
...
---------------------------------------------------------------------
TOTAL                                    5000    100    98%
```

---

## Coverage Enforcement

**CI/CD:** Fail build if coverage drops below 90%

```yaml
# In CI/CD pipeline
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-fail-under=90
```

---

# CI/CD Integration

## GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.10", "3.11"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run unit tests
      run: |
        pytest tests/unit -m unit --cov=src --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration -m integration

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

    - name: Check coverage threshold
      run: |
        pytest --cov=src --cov-fail-under=90
```

---

## Test Dependencies

**File:** `requirements-test.txt`

```
# Testing framework
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-xdist==3.5.0
pytest-timeout==2.2.0
pytest-mock==3.12.0

# Mocking
responses==0.24.1
freezegun==1.4.0
faker==22.0.0

# Code quality
pylint==3.0.3
mypy==1.7.1
black==23.12.1
isort==5.13.2
```

---

# Test Execution Strategy

## Local Development

### Run All Tests

```bash
pytest
```

### Run Specific Test Category

```bash
# Unit tests only (fast)
pytest tests/unit -m unit

# Integration tests only
pytest tests/integration -m integration

# End-to-end tests only
pytest tests/e2e -m e2e

# Critical tests only
pytest -m critical
```

### Run Tests for Specific Module

```bash
# Test enforcement actions
pytest tests/unit/test_enforcement_actions.py

# Test specific rule
pytest tests/unit/test_rules/test_max_contracts.py
```

### Run Tests with Verbose Output

```bash
pytest -vv
```

### Run Tests in Parallel

```bash
# Use all CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
```

---

## CI/CD Execution

### Pull Request Checks

1. **Fast Tests First:** Run unit tests (< 5 minutes)
2. **Integration Tests:** Run if unit tests pass (< 15 minutes)
3. **E2E Tests:** Run if integration tests pass (< 30 minutes)
4. **Coverage Check:** Verify 90% coverage maintained

### Nightly Builds

1. **Full Test Suite:** All 201 test scenarios
2. **Performance Tests:** Load testing, memory profiling
3. **Long-Running Tests:** 24-hour daemon stability test

---

## Test Execution Order

**Prioritized Execution:**

1. **Critical Tests** (smoke tests, essential functionality)
2. **High Priority Unit Tests** (core modules)
3. **High Priority Integration Tests** (API integration)
4. **Medium Priority Tests** (edge cases)
5. **Low Priority Tests** (optional scenarios)
6. **E2E Tests** (full workflows)

---

# Reporting & Metrics

## Test Reports

### pytest HTML Report

```bash
pytest --html=reports/test-report.html --self-contained-html
```

**Output:** Single HTML file with:
- Test results (pass/fail)
- Test duration
- Error tracebacks
- Coverage summary

---

### Coverage HTML Report

```bash
pytest --cov=src --cov-report=html
```

**Output:** `htmlcov/index.html` with:
- Line-by-line coverage
- Branch coverage
- Missing lines highlighted
- Coverage trends

---

### JUnit XML (for CI/CD)

```bash
pytest --junitxml=reports/junit.xml
```

**Output:** Machine-readable test results for CI/CD dashboards

---

## Metrics Dashboard

### Key Metrics to Track

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Count** | 201+ | Total scenarios |
| **Test Pass Rate** | 100% | Tests passing |
| **Coverage** | 90%+ | Line coverage |
| **Test Duration** | < 3 hours | Full suite |
| **Flaky Tests** | 0 | Tests with intermittent failures |
| **Bug Detection Rate** | 95%+ | Bugs caught by tests |

---

### Test Execution Trends

**Track over time:**
- Test suite growth (new tests added)
- Coverage trend (increasing/stable/decreasing)
- Test duration trend (performance)
- Failure rate (stability)

---

## Continuous Monitoring

### Pre-Commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-quick
        name: Run quick tests
        entry: pytest tests/unit -m "unit and critical" --maxfail=1
        language: system
        pass_filenames: false
        always_run: true
```

---

# Implementation Checklist

## Phase 1: Setup (Week 1)

- [ ] Install pytest and dependencies
- [ ] Create `tests/` directory structure
- [ ] Configure `pytest.ini`
- [ ] Create `conftest.py` with shared fixtures
- [ ] Set up CI/CD workflow

## Phase 2: Unit Tests (Weeks 2-3)

- [ ] Implement MOD-001 tests (8 scenarios)
- [ ] Implement MOD-002 tests (10 scenarios)
- [ ] Implement MOD-003 to MOD-009 tests (49 scenarios)
- [ ] Implement RULE-001 to RULE-012 tests (56 scenarios)
- [ ] Implement Event Router tests (6 scenarios)

## Phase 3: Integration Tests (Week 4)

- [ ] Implement REST API integration tests (10 scenarios)
- [ ] Implement SignalR integration tests (10 scenarios)
- [ ] Implement database integration tests (10 scenarios)
- [ ] Implement full workflow tests (12 scenarios)

## Phase 4: E2E Tests (Week 5)

- [ ] Implement complete workflow tests (10 scenarios)
- [ ] Implement performance tests (5 scenarios)
- [ ] Implement error handling tests (10 scenarios)
- [ ] Implement security tests (5 scenarios)

## Phase 5: Coverage & Optimization (Week 6)

- [ ] Achieve 90% code coverage
- [ ] Optimize slow tests
- [ ] Add missing test scenarios
- [ ] Document test patterns
- [ ] Set up test metrics dashboard

---

# Summary

## Ready for Implementation

- **Framework:** pytest (industry standard)
- **Coverage Target:** 90% line coverage
- **Test Count:** 201 scenarios defined
- **Execution Time:** < 3 hours full suite
- **CI/CD:** GitHub Actions workflow ready
- **Fixtures:** 40+ mock data files ready

## Next Steps

1. Review test scenarios in `TEST_SCENARIO_MATRIX.md`
2. Review test fixtures in `TEST_FIXTURES_PLAN.md`
3. Install testing dependencies: `pip install -r requirements-test.txt`
4. Create `tests/` directory structure
5. Begin Phase 1 implementation (MVP unit tests)

---

**Document Complete** ✓
**Testing Infrastructure Ready** ✓
**Implementation can begin immediately** ✓
