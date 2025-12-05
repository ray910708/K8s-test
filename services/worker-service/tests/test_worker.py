"""Unit tests for Worker Service."""
import pytest
import json
import time
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestWorkerHealthChecks:
    """Tests for worker service health check endpoints."""

    def test_liveness_returns_200(self, client):
        """Test that liveness endpoint returns 200 OK."""
        response = client.get('/health/live')
        assert response.status_code == 200

    def test_liveness_returns_json(self, client):
        """Test that liveness endpoint returns JSON."""
        response = client.get('/health/live')
        assert response.content_type == 'application/json'

    def test_liveness_contains_status(self, client):
        """Test that liveness response contains status."""
        response = client.get('/health/live')
        data = json.loads(response.data)

        assert 'status' in data
        assert data['status'] == 'alive'


@pytest.mark.unit
class TestWorkerStatus:
    """Tests for worker status endpoint."""

    def test_status_returns_200(self, client):
        """Test that status endpoint returns 200 OK."""
        response = client.get('/status')
        assert response.status_code == 200

    def test_status_contains_redis_pool_stats(self, client):
        """Test that status response contains Redis pool statistics."""
        response = client.get('/status')
        data = json.loads(response.data)

        assert 'redis_pool' in data
        pool = data['redis_pool']
        assert 'available' in pool
        assert 'in_use' in pool
        assert 'max_connections' in pool
