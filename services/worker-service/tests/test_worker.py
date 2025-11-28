"""Unit tests for Worker Service."""
import pytest
import sys
import os

# Add parent directory to path to import worker
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_liveness_probe(client):
    """Test liveness probe endpoint."""
    response = client.get('/health/live')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'alive'
    assert data['service'] == 'worker-service'


def test_readiness_probe(client):
    """Test readiness probe endpoint."""
    response = client.get('/health/ready')
    # Accept both 200 and 503 (503 if no recent tasks)
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert 'status' in data
    assert data['service'] == 'worker-service'


def test_status_endpoint(client):
    """Test status endpoint."""
    response = client.get('/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['service'] == 'worker-service'
    assert data['status'] == 'running'


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'worker_tasks_processed_total' in response.data
