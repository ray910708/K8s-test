"""Rate limiting module using Redis.

This module provides rate limiting functionality to protect APIs
from abuse and ensure fair resource usage.
"""
import time
from functools import wraps
from flask import request, jsonify
from typing import Optional, Callable
from request_context import get_trace_id


class RateLimiter:
    """Rate limiter using sliding window algorithm with Redis."""

    def __init__(self, redis_client, default_limit: int = 100, default_window: int = 60):
        """Initialize rate limiter.

        Args:
            redis_client: Redis client instance
            default_limit: Default maximum requests per window
            default_window: Default time window in seconds
        """
        self.redis_client = redis_client
        self.default_limit = default_limit
        self.default_window = default_window

    def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, dict]:
        """Check if request is within rate limit.

        Args:
            key: Rate limit key (e.g., IP address, user ID)
            limit: Maximum requests allowed (uses default if None)
            window: Time window in seconds (uses default if None)

        Returns:
            tuple: (is_allowed, rate_limit_info)
        """
        limit = limit or self.default_limit
        window = window or self.default_window

        # If Redis is not connected, allow the request
        if not self.redis_client.is_connected():
            return True, {
                'limit': limit,
                'remaining': limit,
                'reset': int(time.time()) + window
            }

        redis_key = f"rate_limit:{key}"
        current_time = int(time.time())
        window_start = current_time - window

        try:
            # Remove old entries outside the current window
            self.redis_client._client.zremrangebyscore(redis_key, 0, window_start)

            # Count requests in current window
            current_count = self.redis_client._client.zcard(redis_key)

            if current_count < limit:
                # Add current request
                self.redis_client._client.zadd(redis_key, {str(current_time): current_time})
                self.redis_client._client.expire(redis_key, window)

                remaining = limit - current_count - 1
                return True, {
                    'limit': limit,
                    'remaining': remaining,
                    'reset': current_time + window
                }
            else:
                # Rate limit exceeded
                remaining = 0
                # Get the oldest request timestamp to calculate reset time
                oldest = self.redis_client._client.zrange(redis_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1]) + window if oldest else current_time + window

                return False, {
                    'limit': limit,
                    'remaining': remaining,
                    'reset': reset_time
                }
        except Exception as e:
            # On error, allow the request (fail open)
            return True, {
                'limit': limit,
                'remaining': limit,
                'reset': current_time + window,
                'error': str(e)
            }

    def get_client_identifier(self) -> str:
        """Get client identifier for rate limiting.

        Returns:
            str: Client identifier (IP address or trace ID)
        """
        # Use X-Forwarded-For if behind proxy, otherwise use remote_addr
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'

        return client_ip


def rate_limit(limit: int = 100, window: int = 60, key_func: Optional[Callable] = None):
    """Decorator to apply rate limiting to an endpoint.

    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
        key_func: Optional function to generate rate limit key

    Returns:
        Decorated function with rate limiting
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get rate limiter from app context
            from flask import current_app
            rate_limiter = getattr(current_app, 'rate_limiter', None)

            if not rate_limiter:
                # If rate limiter not configured, allow request
                return func(*args, **kwargs)

            # Get client identifier
            if key_func:
                key = key_func()
            else:
                key = rate_limiter.get_client_identifier()

            # Check rate limit
            is_allowed, rate_info = rate_limiter.check_rate_limit(key, limit, window)

            # Add rate limit headers to response
            @current_app.after_request
            def add_rate_limit_headers(response):
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                return response

            if not is_allowed:
                trace_id = get_trace_id()
                return jsonify({
                    'error': 'Rate Limit Exceeded',
                    'message': f'Too many requests. Limit: {limit} requests per {window} seconds',
                    'retry_after': rate_info['reset'] - int(time.time()),
                    'trace_id': trace_id
                }), 429

            return func(*args, **kwargs)
        return wrapper
    return decorator
