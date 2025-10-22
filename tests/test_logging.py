"""
Unit tests for Risk Manager logging system

Tests:
1. Basic logging setup
2. Context management
3. Performance timing
4. Sensitive data masking
5. Specialized loggers
6. Thread safety
"""

import unittest
import logging
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from risk_manager.logging import (
    setup_logging,
    get_logger,
    get_specialized_logger,
    log_context,
    log_performance,
    timed,
    LogContext,
    StructuredFormatter,
    MaskingFilter,
    PerformanceTimer,
    get_log_context,
    get_correlation_id,
)


class TestLoggingSetup(unittest.TestCase):
    """Test logging setup and configuration"""

    def setUp(self):
        """Create temporary log directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging(self):
        """Test basic logging setup"""
        config = setup_logging(
            log_dir=self.log_dir,
            log_level=logging.DEBUG,
            enable_console=False,
        )

        self.assertIsNotNone(config)
        self.assertEqual(config.log_dir, self.log_dir)
        self.assertEqual(config.log_level, logging.DEBUG)

    def test_get_logger(self):
        """Test getting logger instance"""
        setup_logging(log_dir=self.log_dir, enable_console=False)
        logger = get_logger(__name__)

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, __name__)

    def test_specialized_loggers(self):
        """Test specialized logger creation"""
        setup_logging(log_dir=self.log_dir, enable_console=False)

        daemon_logger = get_specialized_logger('daemon')
        api_logger = get_specialized_logger('api')
        enforcement_logger = get_specialized_logger('enforcement')
        error_logger = get_specialized_logger('error')

        self.assertIsInstance(daemon_logger, logging.Logger)
        self.assertIsInstance(api_logger, logging.Logger)
        self.assertIsInstance(enforcement_logger, logging.Logger)
        self.assertIsInstance(error_logger, logging.Logger)

    def test_invalid_specialized_logger(self):
        """Test invalid specialized logger type"""
        setup_logging(log_dir=self.log_dir, enable_console=False)

        with self.assertRaises(ValueError):
            get_specialized_logger('invalid_type')

    def test_log_files_created(self):
        """Test that log files are created"""
        setup_logging(log_dir=self.log_dir, enable_console=False)

        logger = get_logger(__name__)
        logger.info("Test message")

        # Force flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Check files exist
        self.assertTrue((self.log_dir / 'daemon.log').exists())
        self.assertTrue((self.log_dir / 'api.log').exists())
        self.assertTrue((self.log_dir / 'enforcement.log').exists())
        self.assertTrue((self.log_dir / 'error.log').exists())


class TestLogContext(unittest.TestCase):
    """Test log context and correlation IDs"""

    def test_context_creation(self):
        """Test creating log context"""
        with log_context(account_id='ACC123', event_type='trade'):
            context = get_log_context()

            self.assertIsNotNone(context)
            self.assertEqual(context['account_id'], 'ACC123')
            self.assertEqual(context['event_type'], 'trade')
            self.assertIn('correlation_id', context)

    def test_correlation_id_generation(self):
        """Test automatic correlation ID generation"""
        with log_context(account_id='ACC123'):
            correlation_id = get_correlation_id()

            self.assertIsNotNone(correlation_id)
            self.assertIsInstance(correlation_id, str)
            # UUID format check
            self.assertEqual(len(correlation_id), 36)

    def test_context_nesting(self):
        """Test nested contexts merge correctly"""
        with log_context(account_id='ACC123', event_type='trade'):
            outer_correlation = get_correlation_id()

            with log_context(rule_id='RULE_001'):
                context = get_log_context()

                # Should have all fields
                self.assertEqual(context['account_id'], 'ACC123')
                self.assertEqual(context['event_type'], 'trade')
                self.assertEqual(context['rule_id'], 'RULE_001')

                # Correlation ID should be preserved from outer context
                self.assertEqual(context['correlation_id'], outer_correlation)

    def test_context_cleanup(self):
        """Test context is cleaned up after exit"""
        with log_context(account_id='ACC123'):
            self.assertIsNotNone(get_log_context())

        # Context should be cleared
        self.assertIsNone(get_log_context())

    def test_custom_correlation_id(self):
        """Test providing custom correlation ID"""
        custom_id = 'custom-correlation-123'

        with log_context(correlation_id=custom_id):
            correlation_id = get_correlation_id()
            self.assertEqual(correlation_id, custom_id)


class TestStructuredFormatter(unittest.TestCase):
    """Test structured JSON formatter"""

    def setUp(self):
        """Setup formatter"""
        self.formatter = StructuredFormatter()

    def test_json_formatting(self):
        """Test log record formatted as JSON"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
        )

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        self.assertEqual(parsed['level'], 'INFO')
        self.assertEqual(parsed['message'], 'Test message')
        self.assertEqual(parsed['line'], 42)
        self.assertIn('timestamp', parsed)

    def test_context_inclusion(self):
        """Test context included in formatted output"""
        with log_context(account_id='ACC123'):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=42,
                msg='Test message',
                args=(),
                exc_info=None,
            )

            formatted = self.formatter.format(record)
            parsed = json.loads(formatted)

            self.assertIn('context', parsed)
            self.assertEqual(parsed['context']['account_id'], 'ACC123')

    def test_extra_fields(self):
        """Test extra fields included in output"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
        )
        record.symbol = 'ES'
        record.quantity = 1

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        self.assertEqual(parsed['symbol'], 'ES')
        self.assertEqual(parsed['quantity'], 1)


class TestMaskingFilter(unittest.TestCase):
    """Test sensitive data masking"""

    def setUp(self):
        """Setup filter"""
        self.filter = MaskingFilter()

    def test_api_key_masking(self):
        """Test API key masking"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='API key: api_key=sk_live_1234567890',
            args=(),
            exc_info=None,
        )

        self.filter.filter(record)

        self.assertIn('***MASKED***', record.msg)
        self.assertNotIn('sk_live_1234567890', record.msg)

    def test_password_masking(self):
        """Test password masking"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Login with password=mysecret123',
            args=(),
            exc_info=None,
        )

        self.filter.filter(record)

        self.assertIn('***MASKED***', record.msg)
        self.assertNotIn('mysecret123', record.msg)

    def test_token_masking(self):
        """Test bearer token masking"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            args=(),
            exc_info=None,
        )

        self.filter.filter(record)

        self.assertIn('***MASKED***', record.msg)
        self.assertNotIn('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9', record.msg)

    def test_dict_masking(self):
        """Test masking in dictionary args"""
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='User data',
            args=(),
            exc_info=None,
        )
        record.user = {
            'username': 'trader123',
            'password': 'secret123',
            'api_key': 'sk_live_abcd1234',
        }

        self.filter.filter(record)

        # Password should be masked in dict
        self.assertIn('***MASKED***', str(record.user))


class TestPerformanceTiming(unittest.TestCase):
    """Test performance timing utilities"""

    def setUp(self):
        """Setup logger"""
        self.temp_dir = tempfile.mkdtemp()
        setup_logging(
            log_dir=Path(self.temp_dir),
            enable_console=False,
        )
        self.logger = get_logger(__name__)

    def tearDown(self):
        """Cleanup"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_performance_timer(self):
        """Test manual performance timer"""
        timer = PerformanceTimer(self.logger, 'test_operation')
        timer.start()

        time.sleep(0.05)

        duration = timer.stop()

        self.assertGreater(duration, 40)  # At least 40ms
        self.assertLess(duration, 100)    # Less than 100ms

    def test_performance_context_manager(self):
        """Test performance logging context manager"""
        with log_performance(self.logger, 'test_op') as timer:
            time.sleep(0.05)

        self.assertIsNotNone(timer.duration_ms)
        self.assertGreater(timer.duration_ms, 40)

    def test_timed_decorator(self):
        """Test timed decorator"""
        @timed(self.logger, operation='decorated_func')
        def slow_function():
            time.sleep(0.05)
            return 'result'

        result = slow_function()

        self.assertEqual(result, 'result')

    def test_threshold_logging(self):
        """Test threshold-based logging"""
        # Mock the logger to verify logging behavior
        with patch.object(self.logger, 'log') as mock_log:
            # Fast operation (below threshold)
            with log_performance(self.logger, 'fast_op', threshold_ms=100):
                time.sleep(0.01)

            # Should still log (no threshold check in test)
            self.assertTrue(mock_log.called)


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of logging components"""

    def test_context_thread_safety(self):
        """Test context isolation between threads"""
        import threading

        results = {}

        def thread_func(thread_id):
            with log_context(account_id=f'ACC{thread_id}'):
                time.sleep(0.01)  # Simulate work
                context = get_log_context()
                results[thread_id] = context['account_id']

        threads = [
            threading.Thread(target=thread_func, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Each thread should have its own context
        for i in range(5):
            self.assertEqual(results[i], f'ACC{i}')


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Setup"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir)
        setup_logging(
            log_dir=self.log_dir,
            enable_console=False,
            enable_json=True,
        )

    def tearDown(self):
        """Cleanup"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_workflow(self):
        """Test complete logging workflow"""
        daemon_logger = get_specialized_logger('daemon')
        api_logger = get_specialized_logger('api')
        enforcement_logger = get_specialized_logger('enforcement')

        # Simulate trade processing
        with log_context(
            account_id='ACC123',
            event_type='trade',
            symbol='ES',
        ):
            daemon_logger.info("Trade received", extra={'side': 'buy'})

            with log_performance(api_logger, 'fetch_positions'):
                api_logger.debug("Fetching positions")
                time.sleep(0.01)

            enforcement_logger.warning(
                "Rule breach",
                extra={'rule_id': 'MAX_LOSS'}
            )

        # Flush handlers
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Verify log files exist and contain data
        daemon_log = self.log_dir / 'daemon.log'
        api_log = self.log_dir / 'api.log'
        enforcement_log = self.log_dir / 'enforcement.log'

        self.assertTrue(daemon_log.exists())
        self.assertTrue(api_log.exists())
        self.assertTrue(enforcement_log.exists())

        # Verify JSON format
        with open(daemon_log) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    self.assertIn('timestamp', entry)
                    self.assertIn('level', entry)


if __name__ == '__main__':
    unittest.main()
