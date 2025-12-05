"""Pytest configuration and shared fixtures for Worker Service."""
import pytest
import fakeredis
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def fake_redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_redis_client(fake_redis_client):
    """Mock RedisClient with FakeRedis backend."""
    from redis_client import RedisClient

    with patch.object(RedisClient, '__init__', lambda self, **kwargs: None):
        client = RedisClient(host='localhost', port=6379)
        client._client = fake_redis_client
        client._pool = Mock()
        client._is_connected = True
        client._connection_failures = 0

        client.get_pool_stats = Mock(return_value={
            'available': 25,
            'in_use': 5,
            'max_connections': 30
        })

        client.is_connected = Mock(return_value=True)

        yield client


@pytest.fixture
def app(mock_redis_client):
    """Create Flask app for testing."""
    os.environ['APP_ENV'] = 'test'
    os.environ['DEBUG'] = 'False'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'

    from worker import app as flask_app
    import worker as worker_module

    worker_module.redis_client = mock_redis_client

    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False

    yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset Prometheus metrics before each test."""
    from prometheus_client import REGISTRY

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    yield


@pytest.fixture
def mock_scheduler():
    """Mock the schedule module."""
    with patch('schedule.every') as mock_every:
        mock_job = Mock()
        mock_every.return_value.seconds.return_value.do = Mock(return_value=mock_job)
        yield mock_every
