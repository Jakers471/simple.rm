"""Shared pytest configuration and fixtures

This file is automatically loaded by pytest and provides:
- Logging configuration
- Common fixtures
- Test setup and teardown hooks
"""
import pytest
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import logging configuration plugin
pytest_plugins = ['pytest_logging']


@pytest.fixture(scope='session', autouse=True)
def test_session_setup():
    """Setup before all tests"""
    logger = logging.getLogger('pytest')
    logger.info("Initializing test session...")

    # Ensure log directories exist
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    (log_dir / "coverage").mkdir(exist_ok=True)
    (log_dir / "reports").mkdir(exist_ok=True)

    yield

    logger.info("Cleaning up test session...")


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    # Clear any global state
    yield
    # Cleanup after test


@pytest.fixture(autouse=True)
def log_test_execution(request):
    """Automatically log each test execution"""
    logger = logging.getLogger('test_runner')
    test_name = request.node.name

    logger.debug(f"Starting test: {test_name}")

    yield

    logger.debug(f"Finished test: {test_name}")


@pytest.fixture
def logger():
    """Provide a logger instance for tests"""
    return logging.getLogger('test_runner')
