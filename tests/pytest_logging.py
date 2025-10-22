"""Pytest logging configuration plugin

This plugin configures logging for all pytest test runs.
It sets up:
- Rotating file logs (10MB max, 5 backups)
- Separate console and file logging
- Test results summary log
- Error tracking log
"""
import logging
import logging.config
import yaml
from pathlib import Path
from datetime import datetime


def pytest_configure(config):
    """Configure logging at test session start"""
    # Create log directories
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    coverage_dir = log_dir / "coverage"
    coverage_dir.mkdir(exist_ok=True)

    reports_dir = log_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Load logging configuration
    config_path = Path(__file__).parent / "logging_config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            log_config = yaml.safe_load(f)
        logging.config.dictConfig(log_config)

        # Log session start
        logger = logging.getLogger("pytest")
        logger.info("=" * 80)
        logger.info(f"TEST SESSION STARTED: {datetime.now()}")
        logger.info("=" * 80)
    else:
        # Fallback to basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def pytest_sessionfinish(session, exitstatus):
    """Log session completion"""
    logger = logging.getLogger("pytest")
    logger.info("=" * 80)
    logger.info(f"TEST SESSION FINISHED: {datetime.now()}")
    logger.info(f"Exit Status: {exitstatus}")
    logger.info("=" * 80)


def pytest_runtest_setup(item):
    """Log before each test"""
    logger = logging.getLogger("pytest")
    logger.info(f"SETUP: {item.nodeid}")


def pytest_runtest_teardown(item):
    """Log after each test"""
    logger = logging.getLogger("pytest")
    logger.info(f"TEARDOWN: {item.nodeid}")


def pytest_runtest_logreport(report):
    """Log test results"""
    if report.when == "call":
        logger = logging.getLogger("pytest")

        if report.passed:
            logger.info(f"✓ PASSED: {report.nodeid}")
        elif report.failed:
            logger.error(f"✗ FAILED: {report.nodeid}")
            if report.longrepr:
                logger.error(f"  Error: {report.longrepr}")
        elif report.skipped:
            logger.warning(f"⊘ SKIPPED: {report.nodeid}")
