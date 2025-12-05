"""Request context management with trace ID.

This module provides request context management including trace ID generation
for distributed tracing across microservices.
"""
import uuid
from flask import request, g
from functools import wraps
from typing import Optional, Callable


def generate_trace_id() -> str:
    """Generate a unique trace ID.

    Returns:
        str: UUID-based trace ID
    """
    return str(uuid.uuid4())


def get_trace_id() -> Optional[str]:
    """Get the current request's trace ID.

    Returns:
        str: Current trace ID or None
    """
    return getattr(g, 'trace_id', None)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current request.

    Args:
        trace_id: Trace ID to set
    """
    g.trace_id = trace_id


def extract_trace_id_from_request() -> str:
    """Extract or generate trace ID from request headers.

    Checks for existing trace ID in headers (X-Trace-ID, X-Request-ID)
    or generates a new one if not found.

    Returns:
        str: Trace ID for the current request
    """
    # Check for existing trace ID in headers
    trace_id = request.headers.get('X-Trace-ID')
    if not trace_id:
        trace_id = request.headers.get('X-Request-ID')

    # Generate new trace ID if not found
    if not trace_id:
        trace_id = generate_trace_id()

    return trace_id


def with_trace_id(func: Callable) -> Callable:
    """Decorator to add trace ID to function context.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not get_trace_id():
            set_trace_id(generate_trace_id())
        return func(*args, **kwargs)
    return wrapper


class RequestContextMiddleware:
    """Middleware to manage request context and trace IDs."""

    def __init__(self, app):
        """Initialize middleware.

        Args:
            app: Flask application instance
        """
        self.app = app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)

    def before_request(self):
        """Process request before handling."""
        # Extract or generate trace ID
        trace_id = extract_trace_id_from_request()
        set_trace_id(trace_id)

        # Store request start time
        g.request_start_time = __import__('time').time()

    def after_request(self, response):
        """Process response after handling.

        Args:
            response: Flask response object

        Returns:
            Flask response with trace ID header
        """
        # Add trace ID to response headers
        trace_id = get_trace_id()
        if trace_id:
            response.headers['X-Trace-ID'] = trace_id

        return response
