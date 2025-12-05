"""API Gateway service for Microservices Health Monitor."""
import logging
import time
from flask import Flask, jsonify, request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from config import Config
from redis_client import RedisClient
from structured_logger import setup_logger, LoggerAdapter
from request_context import RequestContextMiddleware, get_trace_id
from rate_limiter import RateLimiter, rate_limit

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure structured logging
base_logger = setup_logger(
    service_name='api-gateway',
    log_level=Config.LOG_LEVEL,
    use_json=True
)

# Create logger adapter for contextual logging
logger = LoggerAdapter(base_logger, {})

# Initialize Redis connection with connection pool
redis_client = RedisClient(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
    db=Config.REDIS_DB,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)

# Initialize rate limiter
rate_limiter = RateLimiter(
    redis_client=redis_client,
    default_limit=100,  # 100 requests
    default_window=60   # per 60 seconds
)
app.rate_limiter = rate_limiter

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

REDIS_POOL_AVAILABLE = Gauge(
    'api_gateway_redis_pool_connections_available',
    'Number of available connections in the Redis pool'
)

REDIS_POOL_IN_USE = Gauge(
    'api_gateway_redis_pool_connections_in_use',
    'Number of connections currently in use in the Redis pool'
)

REDIS_POOL_MAX = Gauge(
    'api_gateway_redis_pool_connections_max',
    'Maximum number of connections in the Redis pool'
)

# Initialize request context middleware for trace ID management
RequestContextMiddleware(app)


def update_redis_status():
    """Update Redis connection status metric and pool statistics."""
    is_connected = redis_client.is_connected()
    REDIS_CONNECTION_STATUS.set(1 if is_connected else 0)

    # Update connection pool statistics
    pool_stats = redis_client.get_pool_stats()
    REDIS_POOL_AVAILABLE.set(pool_stats.get('available', 0))
    REDIS_POOL_IN_USE.set(pool_stats.get('in_use', 0))
    REDIS_POOL_MAX.set(pool_stats.get('max_connections', 0))

    return is_connected


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
    duration_ms = duration * 1000

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

    # Log request with trace ID and metrics
    trace_id = get_trace_id()
    logger.info(
        f"{request.method} {request.path} {response.status_code}",
        extra={
            'trace_id': trace_id,
            'request_method': request.method,
            'request_path': request.path,
            'status_code': response.status_code,
            'request_duration': round(duration_ms, 2)
        }
    )

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
    """Enhanced readiness probe endpoint with dependency checks.

    Returns:
        JSON response indicating if the service is ready to accept requests
    """
    redis_ready = update_redis_status()
    pool_stats = redis_client.get_pool_stats()

    # Check dependencies
    dependencies = {
        'redis': {
            'status': 'healthy' if redis_ready else 'unhealthy',
            'connected': redis_ready,
            'pool': {
                'available': pool_stats.get('available', 0),
                'in_use': pool_stats.get('in_use', 0),
                'max': pool_stats.get('max_connections', 0)
            }
        }
    }

    # Service is ready if Redis is connected (or not required in dev)
    all_healthy = redis_ready or not Config.REDIS_PASSWORD

    if all_healthy:
        return jsonify({
            'status': 'ready',
            'service': 'api-gateway',
            'dependencies': dependencies,
            'timestamp': time.time()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'service': 'api-gateway',
            'dependencies': dependencies,
            'timestamp': time.time()
        }), 503


@app.route('/api/status', methods=['GET'])
@rate_limit(limit=60, window=60)  # 60 requests per minute
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
            result = redis_client.incr('api:total_requests')
            total_requests = result if result is not None else 0
        except Exception as e:
            logger.error(f"Error incrementing request count in Redis: {e}")

    # Get connection pool statistics
    pool_stats = redis_client.get_pool_stats()

    return jsonify({
        'service': 'api-gateway',
        'status': 'running',
        'environment': Config.APP_ENV,
        'redis_connected': redis_ready,
        'total_requests': total_requests,
        'redis_pool': {
            'available': pool_stats.get('available', 0),
            'in_use': pool_stats.get('in_use', 0),
            'max_connections': pool_stats.get('max_connections', 0)
        },
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
