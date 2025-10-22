"""
Risk Manager Logging - Usage Examples

Demonstrates all logging features:
1. Basic logging
2. Structured logging with context
3. Performance timing
4. Specialized loggers
5. Sensitive data masking
6. Correlation IDs
"""

import logging
import time
from pathlib import Path

# Import logging system
from risk_manager.logging import (
    setup_logging,
    get_logger,
    log_context,
    log_performance,
    timed,
    PerformanceTimer,
    get_specialized_logger,
)


def example_1_basic_logging():
    """Example 1: Basic logging setup and usage"""
    print("\n=== Example 1: Basic Logging ===")

    # Setup logging (call once at application startup)
    setup_logging(
        log_level=logging.DEBUG,
        enable_console=True,
        enable_json=False,  # Human-readable for demo
    )

    # Get logger for your module
    logger = get_logger(__name__)

    # Log at different levels
    logger.debug("Debug message - detailed info")
    logger.info("Info message - general info")
    logger.warning("Warning message - something to watch")
    logger.error("Error message - something went wrong")

    # Log with extra fields
    logger.info(
        "Processing trade",
        extra={
            'symbol': 'ES',
            'quantity': 1,
            'price': 4500.0,
        }
    )


def example_2_context_logging():
    """Example 2: Context logging with correlation IDs"""
    print("\n=== Example 2: Context Logging ===")

    setup_logging(enable_console=True, enable_json=False)
    logger = get_logger(__name__)

    # Use context for automatic field injection
    with log_context(
        account_id='ACC123',
        event_type='trade_processing',
    ):
        logger.info("Started processing trade")

        # All logs within this context include account_id and correlation_id
        time.sleep(0.1)

        logger.info("Trade validated")

        # Nested contexts merge fields
        with log_context(rule_id='RULE_MAX_POSITION'):
            logger.info("Checking position limit rule")
            logger.warning("Position approaching limit")


def example_3_performance_timing():
    """Example 3: Performance timing"""
    print("\n=== Example 3: Performance Timing ===")

    setup_logging(enable_console=True, enable_json=False)
    logger = get_logger(__name__)

    # Method 1: Context manager
    with log_performance(logger, 'api_call', threshold_ms=50):
        time.sleep(0.1)  # Simulate API call

    # Method 2: Manual timer
    timer = PerformanceTimer(logger, 'database_query')
    timer.start()
    time.sleep(0.05)  # Simulate query
    duration = timer.stop()
    print(f"Query took {duration:.2f}ms")

    # Method 3: Decorator
    @timed(logger, operation='fetch_positions')
    def get_positions():
        time.sleep(0.075)
        return ['ES', 'NQ']

    positions = get_positions()


def example_4_specialized_loggers():
    """Example 4: Specialized loggers for different concerns"""
    print("\n=== Example 4: Specialized Loggers ===")

    setup_logging(enable_console=True, enable_json=False)

    # Get specialized loggers
    daemon_logger = get_specialized_logger('daemon')
    enforcement_logger = get_specialized_logger('enforcement')
    api_logger = get_specialized_logger('api')
    error_logger = get_specialized_logger('error')

    # Daemon activity
    daemon_logger.info("Daemon started", extra={'version': '1.0.0'})

    # API calls
    api_logger.debug(
        "API request",
        extra={
            'method': 'GET',
            'endpoint': '/positions',
            'status_code': 200,
        }
    )

    # Enforcement actions
    with log_context(account_id='ACC123', rule_id='MAX_LOSS'):
        enforcement_logger.warning(
            "Rule breach detected",
            extra={
                'current_loss': -500,
                'max_loss': -400,
                'action': 'flatten_positions',
            }
        )

    # Errors
    try:
        result = 1 / 0
    except Exception as e:
        error_logger.error("Calculation failed", exc_info=True)


def example_5_sensitive_data_masking():
    """Example 5: Sensitive data masking"""
    print("\n=== Example 5: Sensitive Data Masking ===")

    setup_logging(enable_console=True, enable_json=False)
    logger = get_logger(__name__)

    # These will be automatically masked
    logger.info("API key: api_key=sk_live_1234567890abcdef")
    logger.info("Password: password=mysecretpassword123")
    logger.info("Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    logger.info("Email: user@example.com")

    # Dictionary with sensitive data
    logger.info(
        "User login",
        extra={
            'username': 'trader123',
            'password': 'secret123',  # Will be masked
            'api_key': 'sk_live_abcd1234',  # Will be masked
        }
    )


def example_6_complete_workflow():
    """Example 6: Complete workflow with all features"""
    print("\n=== Example 6: Complete Workflow ===")

    # Setup with JSON logging (production mode)
    setup_logging(
        log_dir=Path("logs"),
        log_level=logging.INFO,
        enable_console=True,
        enable_json=True,  # JSON for structured logging
    )

    # Get specialized loggers
    daemon_logger = get_specialized_logger('daemon')
    api_logger = get_specialized_logger('api')
    enforcement_logger = get_specialized_logger('enforcement')

    # Start daemon
    daemon_logger.info("Risk Manager daemon started", extra={'version': '1.0.0'})

    # Process trade with full context and timing
    with log_context(
        account_id='ACC123',
        event_type='trade_received',
        symbol='ES',
    ):
        daemon_logger.info("Trade received", extra={'side': 'buy', 'qty': 1})

        # API call with timing
        with log_performance(api_logger, 'fetch_positions', threshold_ms=100):
            api_logger.debug(
                "Fetching current positions",
                extra={'endpoint': '/api/positions'}
            )
            time.sleep(0.05)  # Simulate API call
            api_logger.debug("Positions fetched", extra={'count': 3})

        # Check rules
        with log_context(rule_id='MAX_POSITION', event_type='rule_check'):
            daemon_logger.debug("Checking position limit rule")

            current_position = 5
            max_position = 3

            if current_position > max_position:
                # Rule breach
                enforcement_logger.warning(
                    "Position limit breached",
                    extra={
                        'current': current_position,
                        'limit': max_position,
                        'breach_amount': current_position - max_position,
                    }
                )

                # Take enforcement action
                with log_context(event_type='enforcement_action'):
                    enforcement_logger.info(
                        "Flattening positions",
                        extra={
                            'action': 'flatten_all',
                            'reason': 'position_limit_exceeded',
                        }
                    )


def example_7_error_handling():
    """Example 7: Error handling and exception logging"""
    print("\n=== Example 7: Error Handling ===")

    setup_logging(enable_console=True, enable_json=False)
    logger = get_logger(__name__)
    error_logger = get_specialized_logger('error')

    with log_context(account_id='ACC456', event_type='api_call'):
        try:
            logger.info("Calling API")

            # Simulate API error
            raise ConnectionError("API connection failed: timeout after 30s")

        except Exception as e:
            # Log with full traceback
            error_logger.error(
                "API call failed",
                exc_info=True,
                extra={
                    'error_type': type(e).__name__,
                    'endpoint': '/api/positions',
                }
            )


def example_8_batch_operations():
    """Example 8: Logging batch operations efficiently"""
    print("\n=== Example 8: Batch Operations ===")

    setup_logging(enable_console=True, enable_json=False)
    logger = get_logger(__name__)

    # Process multiple accounts
    accounts = ['ACC001', 'ACC002', 'ACC003']

    with log_context(event_type='batch_check'):
        logger.info(f"Starting batch check for {len(accounts)} accounts")

        for account_id in accounts:
            # Create sub-context for each account
            with log_context(account_id=account_id):
                with log_performance(logger, 'account_check', threshold_ms=50):
                    logger.debug("Checking account")
                    time.sleep(0.02)
                    logger.debug("Account check completed")

        logger.info("Batch check completed")


if __name__ == '__main__':
    print("Risk Manager Logging Examples\n")

    # Run all examples
    example_1_basic_logging()
    example_2_context_logging()
    example_3_performance_timing()
    example_4_specialized_loggers()
    example_5_sensitive_data_masking()
    example_6_complete_workflow()
    example_7_error_handling()
    example_8_batch_operations()

    print("\n=== Examples completed ===")
    print("Check the 'logs' directory for output files:")
    print("  - logs/daemon.log")
    print("  - logs/enforcement.log")
    print("  - logs/api.log")
    print("  - logs/error.log")
