"""
Logging Formatters and Filters

Provides:
- Structured JSON formatting
- Sensitive data masking
- Context enrichment
"""

import logging
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Pattern
from .context import get_log_context


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging

    Outputs logs in JSON format with:
    - Standard fields (timestamp, level, message, etc.)
    - Context fields (correlation_id, account_id, etc.)
    - Extra fields from log records
    """

    def __init__(self, include_context: bool = True):
        """
        Initialize formatter

        Args:
            include_context: Include context from LogContext
        """
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add context if available
        if self.include_context:
            context = get_log_context()
            if context:
                log_entry['context'] = context

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        # Skip standard fields and internal fields
        skip_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName', 'relativeCreated',
            'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
            'getMessage', 'context',
        }

        for key, value in record.__dict__.items():
            if key not in skip_fields and not key.startswith('_'):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class MaskingFilter(logging.Filter):
    """
    Filter to mask sensitive data in log records

    Masks:
    - API keys and tokens
    - Passwords
    - Authorization headers
    - Credit card numbers
    - SSN
    - Custom patterns
    """

    # Sensitive field patterns
    SENSITIVE_PATTERNS: List[tuple[Pattern, str]] = [
        # API keys and tokens
        (re.compile(r'(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]+)', re.IGNORECASE), r'\1=***MASKED***'),
        (re.compile(r'(bearer\s+)([a-zA-Z0-9_\-\.]+)', re.IGNORECASE), r'\1***MASKED***'),

        # Authorization headers
        (re.compile(r'(authorization\s*:\s*)(.*)', re.IGNORECASE), r'\1***MASKED***'),

        # Passwords
        (re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE), r'\1=***MASKED***'),

        # Credit card numbers (basic pattern)
        (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '****-****-****-****'),

        # SSN
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***-**-****'),

        # Email addresses (partial masking)
        (re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'***@\2'),
    ]

    def __init__(self, additional_patterns: List[tuple[Pattern, str]] = None):
        """
        Initialize filter

        Args:
            additional_patterns: Additional regex patterns to mask
                Format: [(pattern, replacement), ...]
        """
        super().__init__()
        self.patterns = self.SENSITIVE_PATTERNS.copy()

        if additional_patterns:
            self.patterns.extend(additional_patterns)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and mask sensitive data in log record

        Args:
            record: Log record to filter

        Returns:
            True (always allow record, just mask sensitive data)
        """
        # Mask message
        if isinstance(record.msg, str):
            record.msg = self._mask_string(record.msg)

        # Mask args
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._mask_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self._mask_value(arg) for arg in record.args)

        # Mask extra fields
        for key in list(record.__dict__.keys()):
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno'}:
                value = getattr(record, key)
                if isinstance(value, (str, dict, list)):
                    setattr(record, key, self._mask_value(value))

        return True

    def _mask_string(self, text: str) -> str:
        """Mask sensitive data in string"""
        for pattern, replacement in self.patterns:
            text = pattern.sub(replacement, text)
        return text

    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionary"""
        masked = {}
        for key, value in data.items():
            masked[key] = self._mask_value(value)
        return masked

    def _mask_value(self, value: Any) -> Any:
        """Mask sensitive data in any value type"""
        if isinstance(value, str):
            return self._mask_string(value)
        elif isinstance(value, dict):
            return self._mask_dict(value)
        elif isinstance(value, (list, tuple)):
            return [self._mask_value(v) for v in value]
        else:
            return value


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability

    Uses ANSI color codes for different log levels
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for high-frequency logs

    Uses shorter format to reduce log size
    """

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format in compact style"""
        # Add context fields inline if present
        context = get_log_context()
        if context:
            # Add important context to message
            ctx_parts = []
            if 'correlation_id' in context:
                ctx_parts.append(f"[{context['correlation_id'][:8]}]")
            if 'account_id' in context:
                ctx_parts.append(f"[{context['account_id']}]")

            if ctx_parts:
                record.msg = f"{' '.join(ctx_parts)} {record.msg}"

        return super().format(record)
