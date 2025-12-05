"""Pytest configuration and shared fixtures."""
import pytest
import fakeredis
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import app modules
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

        # Mock get_pool_stats
        client.get_pool_stats = Mock(return_value={
            'available': 45,
            'in_use': 5,
            'max_connections': 50
        })

        # Mock is_connected
        client.is_connected = Mock(return_value=True)

        yield client


@pytest.fixture
def app(mock_redis_client):
    """Create Flask app for testing."""
    # Set test environment
    os.environ['APP_ENV'] = 'test'
    os.environ['DEBUG'] = 'False'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'

    # Import app after setting environment
    from app import app as flask_app
    from app import redis_client

    # Replace redis_client with mock
    import app as app_module
    app_module.redis_client = mock_redis_client

    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False

    yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing."""
    with patch('time.time', return_value=1234567890.0):
        yield 1234567890.0


@pytest.fixture
def sample_trace_id():
    """Provide a sample trace ID for testing."""
    return 'test-trace-id-12345'


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset Prometheus metrics before each test."""
    from prometheus_client import REGISTRY

    # Clear all collectors
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    yield
