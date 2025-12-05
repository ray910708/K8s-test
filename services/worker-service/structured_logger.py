"""Structured logging module with JSON output.

This module provides structured logging with JSON formatting for better
log aggregation and analysis in production environments.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""

    def __init__(self, service_name: str):
        """Initialize JSON formatter.

        Args:
            service_name: Name of the service for log identification
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log message
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'service': self.service_name,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        if hasattr(record, 'request_method'):
            log_data['request_method'] = record.request_method

        if hasattr(record, 'request_path'):
            log_data['request_path'] = record.request_path

        if hasattr(record, 'request_duration'):
            log_data['request_duration_ms'] = record.request_duration

        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code

        # Add any custom extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'trace_id', 'user_id',
                          'request_method', 'request_path', 'request_duration',
                          'status_code']:
                if not key.startswith('_'):
                    log_data[key] = value

        return json.dumps(log_data)


def setup_logger(
    service_name: str,
    log_level: str = 'INFO',
    use_json: bool = True
) -> logging.Logger:
    """Setup and configure structured logger.

    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting (default: True)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter
    if use_json:
        formatter = JSONFormatter(service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding contextual information."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with extra context.

        Args:
            msg: Log message
            kwargs: Additional keyword arguments

        Returns:
            tuple: Processed message and kwargs
        """
        # Merge context with extra fields
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs
