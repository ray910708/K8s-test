"""API Gateway service for Microservices Health Monitor."""
import logging
import time
from flask import Flask, jsonify, request
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Redis connection
try:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
        db=Config.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info(f"Connected to Redis at {Config.REDIS_HOST}:{Config.REDIS_PORT}")
except redis.ConnectionError as e:
    logger.warning(f"Failed to connect to Redis: {e}. Service will continue without Redis.")
    redis_client = None

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_gateway_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_gateway_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

REQUESTS_IN_PROGRESS = Gauge(
    'api_gateway_requests_in_progress',
    'Number of requests currently being processed'
)

REDIS_CONNECTION_STATUS = Gauge(
    'api_gateway_redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)'
)


def update_redis_status():
    """Update Redis connection status metric."""
    if redis_client:
        try:
            redis_client.ping()
            REDIS_CONNECTION_STATUS.set(1)
            return True
        except redis.ConnectionError:
            REDIS_CONNECTION_STATUS.set(0)
            return False
    else:
        REDIS_CONNECTION_STATUS.set(0)
        return False


@app.before_request
def before_request():
    """Track request metrics before processing."""
    request.start_time = time.time()
    REQUESTS_IN_PROGRESS.inc()


@app.after_request
def after_request(response):
    """Track request metrics after processing."""
    REQUESTS_IN_PROGRESS.dec()

    # Record request duration
    duration = time.time() - request.start_time
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).observe(duration)

    # Record request count
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()

    return response


@app.route('/health/live', methods=['GET'])
def liveness():
    """Liveness probe endpoint.

    Returns:
        JSON response indicating if the service is alive
    """
    return jsonify({
        'status': 'alive',
        'service': 'api-gateway',
        'timestamp': time.time()
    }), 200


@app.route('/health/ready', methods=['GET'])
def readiness():
    """Readiness probe endpoint.

    Returns:
        JSON response indicating if the service is ready to accept requests
    """
    redis_ready = update_redis_status()

    if redis_ready or not Config.REDIS_PASSWORD:  # Allow running without Redis in dev
        return jsonify({
            'status': 'ready',
            'service': 'api-gateway',
            'redis_connected': redis_ready,
            'timestamp': time.time()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'service': 'api-gateway',
            'redis_connected': False,
            'timestamp': time.time()
        }), 503


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status.

    Returns:
        JSON response with system status information
    """
    redis_ready = update_redis_status()

    # Try to get request count from Redis
    total_requests = 0
    if redis_ready:
        try:
            total_requests = redis_client.incr('api:total_requests')
        except Exception as e:
            logger.error(f"Error incrementing request count in Redis: {e}")

    return jsonify({
        'service': 'api-gateway',
        'status': 'running',
        'environment': Config.APP_ENV,
        'redis_connected': redis_ready,
        'total_requests': total_requests,
        'timestamp': time.time()
    }), 200


@app.route('/api/info', methods=['GET'])
def get_info():
    """Get service information.

    Returns:
        JSON response with service information
    """
    return jsonify({
        'service': 'api-gateway',
        'version': '1.0.0',
        'environment': Config.APP_ENV,
        'endpoints': {
            'health': {
                'liveness': '/health/live',
                'readiness': '/health/ready'
            },
            'api': {
                'status': '/api/status',
                'info': '/api/info'
            },
            'metrics': '/metrics'
        }
    }), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/', methods=['GET'])
def root():
    """Root endpoint.

    Returns:
        JSON response with service information
    """
    return jsonify({
        'service': 'api-gateway',
        'message': 'Microservices Health Monitor API',
        'version': '1.0.0',
        'docs': '/api/info'
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting API Gateway on {Config.HOST}:{Config.PORT}")
    logger.info(f"Environment: {Config.APP_ENV}")
    logger.info(f"Debug mode: {Config.DEBUG}")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
