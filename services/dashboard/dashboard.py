"""Dashboard service for displaying system status."""
import logging
import time
import os
from flask import Flask, render_template, jsonify
import requests
from structured_logger import setup_logger, LoggerAdapter
from request_context import RequestContextMiddleware, get_trace_id

# Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '3000'))
APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Service URLs
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://api-gateway-service:8080')
WORKER_SERVICE_URL = os.getenv('WORKER_SERVICE_URL', 'http://worker-service:8081')

# Initialize Flask app
app = Flask(__name__)

# Configure structured logging
base_logger = setup_logger(
    service_name='dashboard',
    log_level=LOG_LEVEL,
    use_json=True
)

# Create logger adapter for contextual logging
logger = LoggerAdapter(base_logger, {})

# Initialize request context middleware for trace ID management
RequestContextMiddleware(app)


def check_service_health(service_name, url):
    """Check health of a service.

    Args:
        service_name: Name of the service
        url: Health check URL

    Returns:
        dict: Service health information
    """
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return {
                'name': service_name,
                'status': 'healthy',
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'data': response.json()
            }
        else:
            return {
                'name': service_name,
                'status': 'unhealthy',
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'error': f'HTTP {response.status_code}'
            }
    except requests.RequestException as e:
        logger.error(f"Error checking {service_name} health: {e}")
        return {
            'name': service_name,
            'status': 'unreachable',
            'error': str(e)
        }


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html',
                         api_gateway_url=API_GATEWAY_URL,
                         worker_service_url=WORKER_SERVICE_URL,
                         environment=APP_ENV)


@app.route('/api/health-check')
def health_check():
    """Check health of all services."""
    services = [
        {
            'name': 'API Gateway',
            'url': f'{API_GATEWAY_URL}/health/ready'
        },
        {
            'name': 'Worker Service',
            'url': f'{WORKER_SERVICE_URL}/health/ready'
        }
    ]

    results = []
    for service in services:
        result = check_service_health(service['name'], service['url'])
        results.append(result)

    # Overall system status
    all_healthy = all(s['status'] == 'healthy' for s in results)
    system_status = 'healthy' if all_healthy else 'degraded'

    return jsonify({
        'system_status': system_status,
        'timestamp': time.time(),
        'services': results
    })


@app.route('/api/system-info')
def system_info():
    """Get detailed system information."""
    try:
        # Get API Gateway status
        api_response = requests.get(f'{API_GATEWAY_URL}/api/status', timeout=3)
        api_data = api_response.json() if api_response.status_code == 200 else {}

        # Get Worker status
        worker_response = requests.get(f'{WORKER_SERVICE_URL}/status', timeout=3)
        worker_data = worker_response.json() if worker_response.status_code == 200 else {}

        return jsonify({
            'timestamp': time.time(),
            'environment': APP_ENV,
            'api_gateway': api_data,
            'worker_service': worker_data
        })
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({
            'error': 'Failed to retrieve system information',
            'message': str(e)
        }), 500


@app.route('/health/live')
def liveness():
    """Liveness probe endpoint."""
    return jsonify({
        'status': 'alive',
        'service': 'dashboard',
        'timestamp': time.time()
    }), 200


@app.route('/health/ready')
def readiness():
    """Readiness probe endpoint."""
    # Check if we can reach API Gateway
    try:
        response = requests.get(f'{API_GATEWAY_URL}/health/live', timeout=3)
        if response.status_code == 200:
            return jsonify({
                'status': 'ready',
                'service': 'dashboard',
                'api_gateway_reachable': True,
                'timestamp': time.time()
            }), 200
    except requests.RequestException as e:
        logger.warning(f"Unable to reach API Gateway during readiness check: {e}")

    return jsonify({
        'status': 'not_ready',
        'service': 'dashboard',
        'api_gateway_reachable': False,
        'timestamp': time.time()
    }), 503


if __name__ == '__main__':
    logger.info(f"Starting Dashboard on {HOST}:{PORT}")
    logger.info(f"Environment: {APP_ENV}")
    logger.info(f"API Gateway URL: {API_GATEWAY_URL}")
    logger.info(f"Worker Service URL: {WORKER_SERVICE_URL}")

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )
