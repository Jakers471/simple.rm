"""
Log Context Management

Provides correlation IDs and context propagation for tracking
events through the entire pipeline.
"""

import threading
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any
from contextvars import ContextVar


# Thread-safe context storage
_log_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('log_context', default=None)


class LogContext:
    """
    Log context manager for correlation IDs and request tracking

    Automatically propagates context through async operations and threads.
    Thread-safe using contextvars.
    """

    def __init__(
        self,
        correlation_id: Optional[str] = None,
        account_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        event_type: Optional[str] = None,
        **extra: Any
    ):
        """
        Initialize log context

        Args:
            correlation_id: Unique ID to track events through pipeline
            account_id: Trading account ID
            rule_id: Risk rule ID
            event_type: Type of event (trade, breach, api_call, etc.)
            **extra: Additional context fields
        """
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.account_id = account_id
        self.rule_id = rule_id
        self.event_type = event_type
        self.extra = extra

        self._token = None
        self._previous_context = None

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate a unique correlation ID"""
        return str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        context = {
            'correlation_id': self.correlation_id,
        }

        if self.account_id is not None:
            context['account_id'] = self.account_id

        if self.rule_id is not None:
            context['rule_id'] = self.rule_id

        if self.event_type is not None:
            context['event_type'] = self.event_type

        # Add extra fields
        context.update(self.extra)

        return context

    def __enter__(self):
        """Enter context manager"""
        # Save previous context
        self._previous_context = _log_context.get()

        # Merge with previous context if exists
        if self._previous_context:
            merged_context = self._previous_context.copy()
            merged_context.update(self.to_dict())
            self._token = _log_context.set(merged_context)
        else:
            self._token = _log_context.set(self.to_dict())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        # Restore previous context
        if self._token is not None:
            _log_context.reset(self._token)

    def update(self, **kwargs: Any) -> None:
        """Update context with new fields"""
        current = _log_context.get() or {}
        current.update(kwargs)
        _log_context.set(current)

    @classmethod
    def get_current(cls) -> Optional[Dict[str, Any]]:
        """Get current log context"""
        return _log_context.get()

    @classmethod
    def clear(cls) -> None:
        """Clear current log context"""
        _log_context.set(None)


@contextmanager
def log_context(
    correlation_id: Optional[str] = None,
    account_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    event_type: Optional[str] = None,
    **extra: Any
):
    """
    Context manager for logging context

    Usage:
        >>> with log_context(account_id='ACC123', event_type='trade'):
        ...     logger.info("Processing trade")  # Will include context

    Args:
        correlation_id: Unique correlation ID
        account_id: Trading account ID
        rule_id: Risk rule ID
        event_type: Event type
        **extra: Additional context fields
    """
    ctx = LogContext(
        correlation_id=correlation_id,
        account_id=account_id,
        rule_id=rule_id,
        event_type=event_type,
        **extra
    )

    with ctx:
        yield ctx


def get_log_context() -> Optional[Dict[str, Any]]:
    """
    Get current log context

    Returns:
        Current context dict or None
    """
    return LogContext.get_current()


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID

    Returns:
        Current correlation ID or None
    """
    context = get_log_context()
    return context.get('correlation_id') if context else None


def set_log_context(**kwargs: Any) -> None:
    """
    Set or update log context fields

    Args:
        **kwargs: Context fields to set
    """
    current = get_log_context() or {}
    current.update(kwargs)
    _log_context.set(current)


class ContextAdapter(threading.local):
    """
    Thread-local context adapter for legacy threading code

    Use contextvars-based LogContext for new code.
    """

    def __init__(self):
        self.context: Dict[str, Any] = {}

    def set(self, **kwargs: Any) -> None:
        """Set context fields"""
        self.context.update(kwargs)

    def get(self) -> Dict[str, Any]:
        """Get context"""
        return self.context.copy()

    def clear(self) -> None:
        """Clear context"""
        self.context.clear()


# Global thread-local adapter for legacy code
_thread_local_context = ContextAdapter()


def get_thread_context() -> Dict[str, Any]:
    """Get thread-local context (legacy)"""
    return _thread_local_context.get()


def set_thread_context(**kwargs: Any) -> None:
    """Set thread-local context (legacy)"""
    _thread_local_context.set(**kwargs)
