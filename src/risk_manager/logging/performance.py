"""
Performance Logging and Timing

Provides decorators and context managers for logging execution time
and performance metrics.
"""

import logging
import time
import functools
import threading
from contextlib import contextmanager
from typing import Optional, Callable, Any
from .context import get_log_context


class PerformanceTimer:
    """
    Performance timer for measuring execution duration

    Can be used as context manager or manually.
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        level: int = logging.DEBUG,
        threshold_ms: Optional[float] = None,
    ):
        """
        Initialize performance timer

        Args:
            logger: Logger instance
            operation: Operation name for logging
            level: Log level for timing messages
            threshold_ms: Only log if duration exceeds threshold (milliseconds)
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.threshold_ms = threshold_ms

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start timing"""
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        """
        Stop timing and return duration

        Returns:
            Duration in milliseconds
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started")

        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        # Log if threshold not set or exceeded
        if self.threshold_ms is None or duration_ms >= self.threshold_ms:
            context = get_log_context() or {}
            self.logger.log(
                self.level,
                f"Operation '{self.operation}' completed in {duration_ms:.2f}ms",
                extra={
                    'operation': self.operation,
                    'duration_ms': duration_ms,
                    'performance': True,
                    **context,
                }
            )

        return duration_ms

    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds (if timer stopped)"""
        if self.start_time is None:
            return None
        if self.end_time is None:
            # Timer still running
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def __enter__(self):
        """Enter context manager"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        self.stop()


@contextmanager
def log_performance(
    logger: logging.Logger,
    operation: str,
    level: int = logging.DEBUG,
    threshold_ms: Optional[float] = None,
):
    """
    Context manager for performance logging

    Usage:
        >>> with log_performance(logger, 'api_call', threshold_ms=100):
        ...     response = api.get_positions()

    Args:
        logger: Logger instance
        operation: Operation name
        level: Log level
        threshold_ms: Only log if duration exceeds threshold
    """
    timer = PerformanceTimer(logger, operation, level, threshold_ms)
    timer.start()

    try:
        yield timer
    finally:
        timer.stop()


def timed(
    logger: Optional[logging.Logger] = None,
    operation: Optional[str] = None,
    level: int = logging.DEBUG,
    threshold_ms: Optional[float] = None,
) -> Callable:
    """
    Decorator for timing function execution

    Usage:
        >>> @timed(logger, operation='fetch_positions')
        >>> def get_positions():
        ...     return api.get_positions()

    Args:
        logger: Logger instance (uses function's module logger if not provided)
        operation: Operation name (uses function name if not provided)
        level: Log level
        threshold_ms: Only log if duration exceeds threshold
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create logger
            func_logger = logger or logging.getLogger(func.__module__)
            op_name = operation or func.__name__

            with log_performance(func_logger, op_name, level, threshold_ms):
                return func(*args, **kwargs)

        return wrapper

    return decorator


async def timed_async(
    logger: Optional[logging.Logger] = None,
    operation: Optional[str] = None,
    level: int = logging.DEBUG,
    threshold_ms: Optional[float] = None,
) -> Callable:
    """
    Decorator for timing async function execution

    Usage:
        >>> @timed_async(logger, operation='fetch_positions')
        >>> async def get_positions():
        ...     return await api.get_positions()

    Args:
        logger: Logger instance
        operation: Operation name
        level: Log level
        threshold_ms: Only log if duration exceeds threshold
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)
            op_name = operation or func.__name__

            timer = PerformanceTimer(func_logger, op_name, level, threshold_ms)
            timer.start()

            try:
                return await func(*args, **kwargs)
            finally:
                timer.stop()

        return wrapper

    return decorator


class PerformanceMetrics:
    """
    Collect performance metrics for operations

    Tracks min, max, avg, and percentiles.
    """

    def __init__(self, operation: str):
        """
        Initialize metrics collector

        Args:
            operation: Operation name
        """
        self.operation = operation
        self.durations: list[float] = []
        self.count = 0
        self.total_time = 0.0
        self.min_time: Optional[float] = None
        self.max_time: Optional[float] = None

    def record(self, duration_ms: float) -> None:
        """Record a duration"""
        self.durations.append(duration_ms)
        self.count += 1
        self.total_time += duration_ms

        if self.min_time is None or duration_ms < self.min_time:
            self.min_time = duration_ms

        if self.max_time is None or duration_ms > self.max_time:
            self.max_time = duration_ms

    @property
    def avg_time(self) -> Optional[float]:
        """Average duration"""
        return self.total_time / self.count if self.count > 0 else None

    def percentile(self, p: float) -> Optional[float]:
        """
        Calculate percentile

        Args:
            p: Percentile (0-100)

        Returns:
            Duration at percentile
        """
        if not self.durations:
            return None

        sorted_durations = sorted(self.durations)
        index = int((p / 100) * len(sorted_durations))
        index = min(index, len(sorted_durations) - 1)

        return sorted_durations[index]

    def summary(self) -> dict[str, Any]:
        """Get summary statistics"""
        return {
            'operation': self.operation,
            'count': self.count,
            'total_ms': self.total_time,
            'avg_ms': self.avg_time,
            'min_ms': self.min_time,
            'max_ms': self.max_time,
            'p50_ms': self.percentile(50),
            'p95_ms': self.percentile(95),
            'p99_ms': self.percentile(99),
        }

    def log_summary(self, logger: logging.Logger, level: int = logging.INFO) -> None:
        """Log summary statistics"""
        summary = self.summary()
        logger.log(
            level,
            f"Performance summary for '{self.operation}'",
            extra={'metrics': summary}
        )


class PerformanceTracker:
    """
    Global performance tracker for multiple operations

    Thread-safe singleton.
    """

    _instance: Optional['PerformanceTracker'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._metrics: dict[str, PerformanceMetrics] = {}
        return cls._instance

    def get_metrics(self, operation: str) -> PerformanceMetrics:
        """Get or create metrics for operation"""
        if operation not in self._metrics:
            self._metrics[operation] = PerformanceMetrics(operation)
        return self._metrics[operation]

    def record(self, operation: str, duration_ms: float) -> None:
        """Record a duration for operation"""
        metrics = self.get_metrics(operation)
        metrics.record(duration_ms)

    def get_summary(self, operation: Optional[str] = None) -> dict[str, Any]:
        """
        Get performance summary

        Args:
            operation: Specific operation or None for all

        Returns:
            Summary statistics
        """
        if operation:
            metrics = self.get_metrics(operation)
            return metrics.summary()
        else:
            return {
                op: metrics.summary()
                for op, metrics in self._metrics.items()
            }

    def log_all_summaries(
        self,
        logger: logging.Logger,
        level: int = logging.INFO
    ) -> None:
        """Log summaries for all tracked operations"""
        for metrics in self._metrics.values():
            metrics.log_summary(logger, level)

    def reset(self, operation: Optional[str] = None) -> None:
        """
        Reset metrics

        Args:
            operation: Specific operation or None for all
        """
        if operation:
            if operation in self._metrics:
                del self._metrics[operation]
        else:
            self._metrics.clear()
