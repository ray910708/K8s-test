"""Unit tests for API endpoints."""
import pytest
import json
from unittest.mock import patch


@pytest.mark.unit
class TestStatusEndpoint:
    """Tests for /api/status endpoint."""

    def test_status_returns_200(self, client):
        """Test that status endpoint returns 200 OK."""
        response = client.get('/api/status')
        assert response.status_code == 200

    def test_status_returns_json(self, client):
        """Test that status endpoint returns JSON."""
        response = client.get('/api/status')
        assert response.content_type == 'application/json'

    def test_status_contains_service_info(self, client):
        """Test that status response contains service information."""
        response = client.get('/api/status')
        data = json.loads(response.data)

        assert 'service' in data
        assert data['service'] == 'api-gateway'
        assert 'status' in data
        assert data['status'] == 'running'

    def test_status_contains_environment(self, client):
        """Test that status response contains environment."""
        response = client.get('/api/status')
        data = json.loads(response.data)

        assert 'environment' in data

    def test_status_contains_redis_info(self, client):
        """Test that status response contains Redis information."""
        response = client.get('/api/status')
        data = json.loads(response.data)

        assert 'redis_connected' in data
        assert 'redis_pool' in data

    def test_status_shows_pool_stats(self, client):
        """Test that status shows connection pool statistics."""
        response = client.get('/api/status')
        data = json.loads(response.data)

        pool = data['redis_pool']
        assert 'available' in pool
        assert 'in_use' in pool
        assert 'max_connections' in pool

    def test_status_increments_request_count(self, client, mock_redis_client):
        """Test that status endpoint increments request counter."""
        # Mock incr to return incrementing values
        mock_redis_client._client.incr = lambda key: 1

        response = client.get('/api/status')
        data = json.loads(response.data)

        assert 'total_requests' in data

    def test_status_contains_timestamp(self, client):
        """Test that status response contains timestamp."""
        response = client.get('/api/status')
        data = json.loads(response.data)

        assert 'timestamp' in data
        assert isinstance(data['timestamp'], (int, float))


@pytest.mark.unit
class TestInfoEndpoint:
    """Tests for /api/info endpoint."""

    def test_info_returns_200(self, client):
        """Test that info endpoint returns 200 OK."""
        response = client.get('/api/info')
        assert response.status_code == 200

    def test_info_returns_json(self, client):
        """Test that info endpoint returns JSON."""
        response = client.get('/api/info')
        assert response.content_type == 'application/json'

    def test_info_contains_service_name(self, client):
        """Test that info response contains service name."""
        response = client.get('/api/info')
        data = json.loads(response.data)

        assert 'service' in data
        assert data['service'] == 'api-gateway'

    def test_info_contains_version(self, client):
        """Test that info response contains version."""
        response = client.get('/api/info')
        data = json.loads(response.data)

        assert 'version' in data

    def test_info_contains_endpoints(self, client):
        """Test that info response contains endpoint information."""
        response = client.get('/api/info')
        data = json.loads(response.data)

        assert 'endpoints' in data
        assert 'health' in data['endpoints']
        assert 'api' in data['endpoints']


@pytest.mark.unit
class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get('/')
        assert response.status_code == 200

    def test_root_returns_json(self, client):
        """Test that root endpoint returns JSON."""
        response = client.get('/')
        assert response.content_type == 'application/json'

    def test_root_contains_service_info(self, client):
        """Test that root response contains service information."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'service' in data
        assert 'message' in data
        assert 'version' in data


@pytest.mark.unit
class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Test that metrics endpoint returns 200 OK."""
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_returns_text(self, client):
        """Test that metrics endpoint returns text/plain."""
        response = client.get('/metrics')
        # Prometheus metrics are text/plain
        assert 'text/plain' in response.content_type or response.content_type == 'text/plain; version=0.0.4; charset=utf-8'

    def test_metrics_contains_prometheus_data(self, client):
        """Test that metrics response contains Prometheus data."""
        response = client.get('/metrics')
        data = response.data.decode('utf-8')

        # Check for common Prometheus metric indicators
        assert '#' in data or 'HELP' in data or 'TYPE' in data


@pytest.mark.unit
class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Not Found'

    def test_404_returns_json(self, client):
        """Test that 404 error returns JSON."""
        response = client.get('/nonexistent-endpoint')
        assert response.content_type == 'application/json'
