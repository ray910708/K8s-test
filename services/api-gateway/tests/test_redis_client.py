"""Unit tests for Redis client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from redis.exceptions import ConnectionError, TimeoutError, ResponseError


@pytest.mark.unit
class TestRedisClient:
    """Tests for RedisClient class."""

    def test_redis_client_initialization(self, mock_redis_client):
        """Test Redis client initialization."""
        assert mock_redis_client is not None
        assert hasattr(mock_redis_client, '_client')

    def test_get_returns_value(self, fake_redis_client):
        """Test that get() returns stored value."""
        fake_redis_client.set('test_key', 'test_value')
        result = fake_redis_client.get('test_key')
        assert result == 'test_value'

    def test_get_returns_default_on_missing_key(self, fake_redis_client):
        """Test that get() returns default when key doesn't exist."""
        result = fake_redis_client.get('nonexistent_key')
        assert result is None

    def test_set_stores_value(self, fake_redis_client):
        """Test that set() stores value correctly."""
        result = fake_redis_client.set('test_key', 'test_value')
        assert result is True
        assert fake_redis_client.get('test_key') == 'test_value'

    def test_incr_increments_value(self, fake_redis_client):
        """Test that incr() increments value."""
        fake_redis_client.set('counter', '5')
        result = fake_redis_client.incr('counter')
        assert result == 6

    def test_incr_creates_key_if_not_exists(self, fake_redis_client):
        """Test that incr() creates key with value 1 if it doesn't exist."""
        result = fake_redis_client.incr('new_counter')
        assert result == 1

    def test_delete_removes_key(self, fake_redis_client):
        """Test that delete() removes key."""
        fake_redis_client.set('test_key', 'test_value')
        result = fake_redis_client.delete('test_key')
        assert result == 1
        assert fake_redis_client.get('test_key') is None

    def test_delete_multiple_keys(self, fake_redis_client):
        """Test that delete() can remove multiple keys."""
        fake_redis_client.set('key1', 'value1')
        fake_redis_client.set('key2', 'value2')
        result = fake_redis_client.delete('key1', 'key2')
        assert result == 2

    def test_get_pool_stats_returns_dict(self, mock_redis_client):
        """Test that get_pool_stats() returns dictionary."""
        stats = mock_redis_client.get_pool_stats()
        assert isinstance(stats, dict)
        assert 'available' in stats
        assert 'in_use' in stats
        assert 'max_connections' in stats

    def test_is_connected_returns_boolean(self, mock_redis_client):
        """Test that is_connected() returns boolean."""
        result = mock_redis_client.is_connected()
        assert isinstance(result, bool)


@pytest.mark.unit
class TestRedisClientErrorHandling:
    """Tests for Redis client error handling."""

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        from redis_client import RedisClient

        with patch('redis.Redis') as mock_redis:
            # Simulate connection error
            mock_redis.return_value.ping.side_effect = ConnectionError("Connection failed")

            # Client should handle error gracefully
            client = RedisClient(host='localhost', port=6379)
            assert client._is_connected is False

    def test_get_with_connection_error_returns_default(self, mock_redis_client):
        """Test that get() returns default on connection error."""
        from redis_client import RedisClient

        client = RedisClient(host='localhost', port=6379)
        client._client = Mock()
        client._client.get.side_effect = ConnectionError("Connection lost")
        client._is_connected = False
        client._last_health_check = 0
        client._health_check_interval = 30

        result = client.get('test_key', default='default_value')
        assert result == 'default_value'

    def test_set_with_connection_error_returns_false(self, mock_redis_client):
        """Test that set() returns False on connection error."""
        from redis_client import RedisClient

        client = RedisClient(host='localhost', port=6379)
        client._client = Mock()
        client._client.set.side_effect = ConnectionError("Connection lost")
        client._is_connected = False
        client._last_health_check = 0
        client._health_check_interval = 30

        result = client.set('test_key', 'test_value')
        assert result is False
