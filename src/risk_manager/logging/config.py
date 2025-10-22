"""
Production Logging Configuration

Provides comprehensive logging setup with:
- Multiple specialized log files (daemon, enforcement, api, error)
- Structured JSON logging
- Log rotation and compression
- Thread-safe operation
- Configurable log levels
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
import sys

from .formatters import StructuredFormatter, MaskingFilter


# Default log configuration
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_LEVEL = logging.INFO
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 7  # Keep 7 days of logs

# Log file definitions
LOG_FILES = {
    'daemon': {
        'filename': 'daemon.log',
        'level': logging.DEBUG,
        'description': 'All daemon activity',
    },
    'enforcement': {
        'filename': 'enforcement.log',
        'level': logging.INFO,
        'description': 'Rule breaches and enforcement actions',
    },
    'api': {
        'filename': 'api.log',
        'level': logging.DEBUG,
        'description': 'TopstepX API calls and responses',
    },
    'error': {
        'filename': 'error.log',
        'level': logging.ERROR,
        'description': 'Errors only',
    },
}


class LogConfig:
    """Centralized logging configuration"""

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_level: int = DEFAULT_LOG_LEVEL,
        enable_console: bool = True,
        enable_json: bool = True,
        max_bytes: int = MAX_BYTES,
        backup_count: int = BACKUP_COUNT,
    ):
        """
        Initialize logging configuration

        Args:
            log_dir: Directory for log files (default: ./logs)
            log_level: Default logging level
            enable_console: Enable console output
            enable_json: Use JSON formatting for structured logs
            max_bytes: Maximum size per log file before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_json = enable_json
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_complete = False

    def setup(self) -> None:
        """Setup all loggers and handlers"""
        if self._setup_complete:
            return

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

        # Remove any existing handlers
        root_logger.handlers.clear()

        # Add console handler if enabled
        if self.enable_console:
            console_handler = self._create_console_handler()
            root_logger.addHandler(console_handler)

        # Setup specialized log files
        for log_name, config in LOG_FILES.items():
            handler = self._create_file_handler(
                filename=config['filename'],
                level=config['level'],
            )

            # Add to root logger for global logging
            root_logger.addHandler(handler)

            # Create specialized logger
            logger = logging.getLogger(f'risk_manager.{log_name}')
            logger.setLevel(config['level'])
            logger.addHandler(handler)
            logger.propagate = False  # Don't propagate to root

            self._loggers[log_name] = logger

        self._setup_complete = True

        # Log startup message
        root_logger.info(
            "Logging system initialized",
            extra={
                'log_dir': str(self.log_dir),
                'log_level': logging.getLevelName(self.log_level),
                'json_enabled': self.enable_json,
            }
        )

    def _create_file_handler(
        self,
        filename: str,
        level: int,
    ) -> logging.Handler:
        """Create a rotating file handler with compression"""
        filepath = self.log_dir / filename

        # Use RotatingFileHandler with gzip compression
        handler = logging.handlers.RotatingFileHandler(
            filename=filepath,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8',
        )

        handler.setLevel(level)

        # Add structured formatter
        if self.enable_json:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        handler.setFormatter(formatter)

        # Add masking filter
        handler.addFilter(MaskingFilter())

        return handler

    def _create_console_handler(self) -> logging.Handler:
        """Create console handler with color support"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)

        # Use simpler format for console
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(message)s',
            datefmt='%H:%M:%S'
        )

        handler.setFormatter(formatter)
        handler.addFilter(MaskingFilter())

        return handler

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance

        Args:
            name: Logger name (use __name__ for module loggers)

        Returns:
            Configured logger instance
        """
        if not self._setup_complete:
            self.setup()

        return logging.getLogger(name)

    def get_specialized_logger(self, log_type: str) -> logging.Logger:
        """
        Get a specialized logger (daemon, enforcement, api, error)

        Args:
            log_type: Type of specialized logger

        Returns:
            Specialized logger instance

        Raises:
            ValueError: If log_type is invalid
        """
        if not self._setup_complete:
            self.setup()

        if log_type not in self._loggers:
            raise ValueError(
                f"Invalid log type: {log_type}. "
                f"Valid types: {', '.join(LOG_FILES.keys())}"
            )

        return self._loggers[log_type]


# Global configuration instance
_config: Optional[LogConfig] = None


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    enable_console: bool = True,
    enable_json: bool = True,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
) -> LogConfig:
    """
    Setup logging system (call once at application startup)

    Args:
        log_dir: Directory for log files
        log_level: Default logging level
        enable_console: Enable console output
        enable_json: Use JSON formatting
        max_bytes: Max file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        LogConfig instance

    Example:
        >>> from risk_manager.logging import setup_logging, get_logger
        >>> setup_logging(log_level=logging.DEBUG)
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    global _config

    if _config is None:
        _config = LogConfig(
            log_dir=log_dir,
            log_level=log_level,
            enable_console=enable_console,
            enable_json=enable_json,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
        _config.setup()

    return _config


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing trade", extra={'symbol': 'ES'})
    """
    global _config

    if _config is None:
        # Auto-initialize with defaults
        _config = LogConfig()
        _config.setup()

    return _config.get_logger(name)


def get_specialized_logger(log_type: str) -> logging.Logger:
    """
    Get a specialized logger (daemon, enforcement, api, error)

    Args:
        log_type: Type of specialized logger

    Returns:
        Specialized logger instance

    Example:
        >>> api_logger = get_specialized_logger('api')
        >>> api_logger.debug("API call", extra={'endpoint': '/positions'})
    """
    global _config

    if _config is None:
        _config = LogConfig()
        _config.setup()

    return _config.get_specialized_logger(log_type)
