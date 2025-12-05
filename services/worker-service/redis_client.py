"""Redis Client with Connection Pool and Error Handling.

This module provides a robust Redis client with:
- Connection pooling for better performance
- Automatic reconnection on failures
- Circuit breaker pattern for resilience
- Comprehensive error handling
- Health checks
"""
import logging
import time
from typing import Optional, Any
import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

logger = logging.getLogger(__name__)


class RedisClient:
    """Enhanced Redis client with connection pooling and error handling."""

    def __init__(
        self,
        host: str,
        port: int,
        password: Optional[str] = None,
        db: int = 0,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30
    ):
        """Initialize Redis client with connection pool.

        Args:
            host: Redis server host
            port: Redis server port
            password: Redis password (optional)
            db: Redis database number
            max_connections: Maximum number of connections in the pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Health check interval in seconds
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._is_connected = False
        self._last_health_check = 0
        self._health_check_interval = health_check_interval
        self._connection_failures = 0
        self._max_connection_failures = 3

        # Initialize connection pool
        self._init_pool(
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout
        )

    def _init_pool(
        self,
        max_connections: int,
        socket_timeout: int,
        socket_connect_timeout: int,
        retry_on_timeout: bool
    ) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = ConnectionPool(
                host=self.host,
                port=self.port,
                password=self.password if self.password else None,
                db=self.db,
                decode_responses=True,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=retry_on_timeout,
                health_check_interval=self._health_check_interval
            )

            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()
            self._is_connected = True
            self._connection_failures = 0
            logger.info(f"Redis connection pool initialized: {self.host}:{self.port}")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            self._is_connected = False
            self._connection_failures += 1
            self._client = None
            self._pool = None

    def is_connected(self) -> bool:
        """Check if Redis is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        current_time = time.time()

        # Only check if health_check_interval has passed
        if current_time - self._last_health_check < self._health_check_interval:
            return self._is_connected

        self._last_health_check = current_time

        if not self._client:
            return False

        try:
            self._client.ping()
            self._is_connected = True
            self._connection_failures = 0
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis health check failed: {e}")
            self._is_connected = False
            self._connection_failures += 1

            # Try to reconnect if failures exceed threshold
            if self._connection_failures >= self._max_connection_failures:
                logger.info("Attempting to reconnect to Redis...")
                self._reconnect()

            return False

    def _reconnect(self) -> None:
        """Attempt to reconnect to Redis."""
        try:
            if self._pool:
                self._pool.disconnect()

            self._init_pool(
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis with error handling.

        Args:
            key: Redis key
            default: Default value if key not found or error occurs

        Returns:
            Value from Redis or default value
        """
        if not self.is_connected():
            logger.debug(f"Redis not connected, returning default for key: {key}")
            return default

        try:
            value = self._client.get(key)
            return value if value is not None else default
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            self._is_connected = False
            return default
        except ResponseError as e:
            logger.error(f"Redis response error for key '{key}': {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in Redis with error handling.

        Args:
            key: Redis key
            value: Value to set
            ex: Expiration time in seconds
            px: Expiration time in milliseconds
            nx: Only set if key does not exist
            xx: Only set if key exists

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.debug(f"Redis not connected, skipping SET for key: {key}")
            return False

        try:
            result = self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            return bool(result)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            self._is_connected = False
            return False
        except ResponseError as e:
            logger.error(f"Redis response error for key '{key}': {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in Redis with error handling.

        Args:
            key: Redis key
            amount: Amount to increment by

        Returns:
            int: New value after increment, or None if error
        """
        if not self.is_connected():
            logger.debug(f"Redis not connected, skipping INCR for key: {key}")
            return None

        try:
            return self._client.incr(key, amount)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            self._is_connected = False
            return None
        except ResponseError as e:
            logger.error(f"Redis response error for key '{key}': {e}")
            return None

    def delete(self, *keys: str) -> int:
        """Delete keys from Redis with error handling.

        Args:
            *keys: Keys to delete

        Returns:
            int: Number of keys deleted, or 0 if error
        """
        if not self.is_connected():
            logger.debug(f"Redis not connected, skipping DELETE for keys: {keys}")
            return 0

        try:
            return self._client.delete(*keys)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis DELETE error for keys '{keys}': {e}")
            self._is_connected = False
            return 0
        except ResponseError as e:
            logger.error(f"Redis response error for keys '{keys}': {e}")
            return 0

    def ping(self) -> bool:
        """Ping Redis server.

        Returns:
            bool: True if ping successful, False otherwise
        """
        return self.is_connected()

    def close(self) -> None:
        """Close Redis connection pool."""
        try:
            if self._pool:
                self._pool.disconnect()
                logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
        finally:
            self._client = None
            self._pool = None
            self._is_connected = False

    def get_pool_stats(self) -> dict:
        """Get connection pool statistics.

        Returns:
            dict: Pool statistics
        """
        if not self._pool:
            return {
                'available': 0,
                'in_use': 0,
                'max_connections': 0
            }

        try:
            return {
                'available': len(self._pool._available_connections),
                'in_use': len(self._pool._in_use_connections),
                'max_connections': self._pool.max_connections
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {
                'available': 0,
                'in_use': 0,
                'max_connections': 0,
                'error': str(e)
            }


# Factory function for easier usage
def create_redis_client(
    host: str,
    port: int,
    password: Optional[str] = None,
    db: int = 0,
    **kwargs
) -> RedisClient:
    """Create and return a Redis client instance.

    Args:
        host: Redis server host
        port: Redis server port
        password: Redis password (optional)
        db: Redis database number
        **kwargs: Additional keyword arguments for RedisClient

    Returns:
        RedisClient: Configured Redis client instance
    """
    return RedisClient(
        host=host,
        port=port,
        password=password,
        db=db,
        **kwargs
    )
