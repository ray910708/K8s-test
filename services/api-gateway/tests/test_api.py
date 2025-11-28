"""Unit tests for API Gateway service."""
import pytest
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['service'] == 'api-gateway'
    assert 'version' in data


def test_liveness_probe(client):
    """Test liveness probe endpoint."""
    response = client.get('/health/live')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'alive'
    assert data['service'] == 'api-gateway'


def test_readiness_probe(client):
    """Test readiness probe endpoint."""
    response = client.get('/health/ready')
    # Accept both 200 and 503 (503 if Redis is not available)
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert 'status' in data
    assert data['service'] == 'api-gateway'


def test_status_endpoint(client):
    """Test status endpoint."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['service'] == 'api-gateway'
    assert data['status'] == 'running'


def test_info_endpoint(client):
    """Test info endpoint."""
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert data['service'] == 'api-gateway'
    assert 'version' in data
    assert 'endpoints' in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'api_gateway_requests_total' in response.data


def test_404_handler(client):
    """Test 404 error handler."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
