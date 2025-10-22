"""
Risk Manager Daemon Example

Demonstrates complete integration of logging system with
a production daemon.
"""

import logging
import time
import signal
import sys
from typing import Optional
from pathlib import Path

# Import logging system

from risk_manager.logging import (
    setup_logging,
    get_specialized_logger,
    log_context,
    log_performance,
)


class RiskManagerDaemon:
    """
    Risk Manager Daemon with integrated logging

    Demonstrates:
    - Lifecycle logging (startup, shutdown)
    - API call logging with timing
    - Rule enforcement logging
    - Error handling
    - Graceful shutdown
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize daemon

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.running = False

        # Setup logging
        setup_logging(
            log_level=logging.INFO,
            enable_json=True,
            enable_console=True,
        )

        # Get specialized loggers
        self.daemon_logger = get_specialized_logger('daemon')
        self.api_logger = get_specialized_logger('api')
        self.enforcement_logger = get_specialized_logger('enforcement')
        self.error_logger = get_specialized_logger('error')

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def start(self) -> None:
        """Start the daemon"""
        self.daemon_logger.info(
            "Risk Manager daemon starting",
            extra={
                'version': '1.0.0',
                'config': self.config,
            }
        )

        self.running = True

        try:
            self._main_loop()
        except Exception as e:
            self.error_logger.error("Daemon crashed", exc_info=True)
            raise
        finally:
            self._shutdown()

    def _main_loop(self) -> None:
        """Main daemon loop"""
        self.daemon_logger.info("Entering main loop")

        iteration = 0
        while self.running:
            iteration += 1

            with log_context(
                event_type='daemon_iteration',
                iteration=iteration,
            ):
                try:
                    self._process_iteration()
                except Exception as e:
                    self.error_logger.error(
                        "Iteration failed",
                        exc_info=True,
                        extra={'iteration': iteration}
                    )

            # Sleep between iterations
            time.sleep(5)

    def _process_iteration(self) -> None:
        """Process one iteration"""
        self.daemon_logger.debug("Processing iteration")

        # Simulate checking multiple accounts
        accounts = ['ACC001', 'ACC002', 'ACC003']

        for account_id in accounts:
            with log_context(account_id=account_id):
                self._check_account(account_id)

    def _check_account(self, account_id: str) -> None:
        """
        Check account for rule compliance

        Args:
            account_id: Account to check
        """
        self.daemon_logger.debug(f"Checking account {account_id}")

        # Fetch positions from API
        positions = self._fetch_positions(account_id)

        # Check rules
        self._check_rules(account_id, positions)

    def _fetch_positions(self, account_id: str) -> list:
        """
        Fetch positions from TopstepX API

        Args:
            account_id: Account ID

        Returns:
            List of positions
        """
        with log_performance(
            self.api_logger,
            'fetch_positions',
            threshold_ms=100,
        ):
            self.api_logger.debug(
                "Fetching positions",
                extra={
                    'endpoint': '/api/positions',
                    'method': 'GET',
                }
            )

            # Simulate API call
            time.sleep(0.05)

            positions = [
                {'symbol': 'ES', 'quantity': 2, 'avg_price': 4500.0},
                {'symbol': 'NQ', 'quantity': 1, 'avg_price': 15000.0},
            ]

            self.api_logger.debug(
                "Positions fetched",
                extra={
                    'count': len(positions),
                    'status_code': 200,
                }
            )

            return positions

    def _check_rules(self, account_id: str, positions: list) -> None:
        """
        Check account against risk rules

        Args:
            account_id: Account ID
            positions: List of positions
        """
        # Rule 1: Check max position size
        with log_context(rule_id='MAX_POSITION', event_type='rule_check'):
            for position in positions:
                max_qty = 3
                current_qty = abs(position['quantity'])

                if current_qty > max_qty:
                    # Rule breach!
                    self.enforcement_logger.warning(
                        "Position limit breached",
                        extra={
                            'symbol': position['symbol'],
                            'current_quantity': current_qty,
                            'max_quantity': max_qty,
                            'breach_amount': current_qty - max_qty,
                        }
                    )

                    # Take enforcement action
                    self._enforce_rule(
                        account_id,
                        'MAX_POSITION',
                        position['symbol'],
                        'reduce_position',
                    )

        # Rule 2: Check max loss (simulated)
        with log_context(rule_id='MAX_LOSS', event_type='rule_check'):
            current_loss = -450  # Simulated
            max_loss = -500

            if current_loss < max_loss:
                self.enforcement_logger.warning(
                    "Max loss breached",
                    extra={
                        'current_loss': current_loss,
                        'max_loss': max_loss,
                    }
                )

                self._enforce_rule(
                    account_id,
                    'MAX_LOSS',
                    None,
                    'flatten_positions',
                )

    def _enforce_rule(
        self,
        account_id: str,
        rule_id: str,
        symbol: Optional[str],
        action: str,
    ) -> None:
        """
        Take enforcement action

        Args:
            account_id: Account ID
            rule_id: Rule that was breached
            symbol: Symbol (if applicable)
            action: Enforcement action to take
        """
        with log_context(
            rule_id=rule_id,
            event_type='enforcement_action',
        ):
            self.enforcement_logger.info(
                f"Taking enforcement action: {action}",
                extra={
                    'symbol': symbol,
                    'action': action,
                    'reason': f'{rule_id}_breach',
                }
            )

            # Simulate enforcement
            time.sleep(0.1)

            self.enforcement_logger.info(
                "Enforcement action completed",
                extra={
                    'action': action,
                    'status': 'success',
                }
            )

    def _handle_shutdown(self, signum, frame) -> None:
        """
        Handle shutdown signal

        Args:
            signum: Signal number
            frame: Stack frame
        """
        self.daemon_logger.info(
            "Shutdown signal received",
            extra={'signal': signum}
        )
        self.running = False

    def _shutdown(self) -> None:
        """Perform graceful shutdown"""
        self.daemon_logger.info("Shutting down daemon")

        # Cleanup tasks
        self.daemon_logger.info("Cleanup complete")

        self.daemon_logger.info("Daemon stopped")


def main():
    """Main entry point"""
    print("Risk Manager Daemon")
    print("=" * 50)
    print("\nStarting daemon...")
    print("Press Ctrl+C to stop\n")

    # Configuration
    config = {
        'check_interval': 5,
        'api_timeout': 30,
        'max_retries': 3,
    }

    # Create and start daemon
    daemon = RiskManagerDaemon(config)

    try:
        daemon.start()
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"\nDaemon error: {e}")
        sys.exit(1)

    print("\nDaemon stopped")


if __name__ == '__main__':
    main()
