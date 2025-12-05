"""Unit tests for health check endpoints."""
import pytest
import json


@pytest.mark.unit
class TestLivenessProbe:
    """Tests for liveness probe endpoint."""

    def test_liveness_returns_200(self, client):
        """Test that liveness endpoint returns 200 OK."""
        response = client.get('/health/live')
        assert response.status_code == 200

    def test_liveness_returns_json(self, client):
        """Test that liveness endpoint returns JSON."""
        response = client.get('/health/live')
        assert response.content_type == 'application/json'

    def test_liveness_contains_status(self, client):
        """Test that liveness response contains status field."""
        response = client.get('/health/live')
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'alive'

    def test_liveness_contains_service_name(self, client):
        """Test that liveness response contains service name."""
        response = client.get('/health/live')
        data = json.loads(response.data)
        assert 'service' in data
        assert data['service'] == 'api-gateway'

    def test_liveness_contains_timestamp(self, client):
        """Test that liveness response contains timestamp."""
        response = client.get('/health/live')
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], (int, float))


@pytest.mark.unit
class TestReadinessProbe:
    """Tests for readiness probe endpoint."""

    def test_readiness_returns_200_when_redis_connected(self, client, mock_redis_client):
        """Test that readiness returns 200 when Redis is connected."""
        mock_redis_client.is_connected.return_value = True
        response = client.get('/health/ready')
        assert response.status_code == 200

    def test_readiness_returns_json(self, client):
        """Test that readiness endpoint returns JSON."""
        response = client.get('/health/ready')
        assert response.content_type == 'application/json'

    def test_readiness_contains_dependencies(self, client):
        """Test that readiness response contains dependencies info."""
        response = client.get('/health/ready')
        data = json.loads(response.data)
        assert 'dependencies' in data
        assert 'redis' in data['dependencies']

    def test_readiness_shows_redis_status(self, client, mock_redis_client):
        """Test that readiness shows Redis connection status."""
        mock_redis_client.is_connected.return_value = True
        response = client.get('/health/ready')
        data = json.loads(response.data)

        redis_dep = data['dependencies']['redis']
        assert 'status' in redis_dep
        assert 'connected' in redis_dep
        assert redis_dep['connected'] is True

    def test_readiness_shows_pool_stats(self, client):
        """Test that readiness shows connection pool statistics."""
        response = client.get('/health/ready')
        data = json.loads(response.data)

        redis_dep = data['dependencies']['redis']
        assert 'pool' in redis_dep
        assert 'available' in redis_dep['pool']
        assert 'in_use' in redis_dep['pool']
        assert 'max' in redis_dep['pool']

    def test_readiness_returns_503_when_redis_disconnected(self, client, mock_redis_client):
        """Test that readiness returns 503 when Redis is disconnected."""
        import os
        from unittest.mock import patch

        # Mock Redis as disconnected
        mock_redis_client.is_connected.return_value = False

        # Patch Config.REDIS_PASSWORD to simulate production environment where password is set
        with patch('app.Config') as mock_config:
            mock_config.REDIS_PASSWORD = 'test-password'
            mock_config.REDIS_HOST = 'localhost'
            mock_config.REDIS_PORT = 6379

            response = client.get('/health/ready')

        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
