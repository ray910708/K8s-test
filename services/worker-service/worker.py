"""Worker Service for background task processing."""
import logging
import time
import os
import random
import threading
from flask import Flask, jsonify
import schedule
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from redis_client import RedisClient
from structured_logger import setup_logger

# Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8081'))
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Initialize Flask app for health checks
app = Flask(__name__)

# Configure structured logging
logger = setup_logger(
    service_name='worker-service',
    log_level=LOG_LEVEL,
    use_json=True
)

# Initialize Redis connection with connection pool
redis_client = RedisClient(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    db=REDIS_DB,
    max_connections=30,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)

# Prometheus metrics
TASKS_PROCESSED = Counter(
    'worker_tasks_processed_total',
    'Total number of tasks processed',
    ['task_type', 'status']
)

TASKS_IN_PROGRESS = Gauge(
    'worker_tasks_in_progress',
    'Number of tasks currently being processed'
)

REDIS_CONNECTION_STATUS = Gauge(
    'worker_redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)'
)

LAST_TASK_TIMESTAMP = Gauge(
    'worker_last_task_timestamp',
    'Timestamp of the last processed task'
)

REDIS_POOL_AVAILABLE = Gauge(
    'worker_redis_pool_connections_available',
    'Number of available connections in the Redis pool'
)

REDIS_POOL_IN_USE = Gauge(
    'worker_redis_pool_connections_in_use',
    'Number of connections currently in use in the Redis pool'
)

REDIS_POOL_MAX = Gauge(
    'worker_redis_pool_connections_max',
    'Maximum number of connections in the Redis pool'
)


# Global state (protected by lock for thread safety)
worker_running = True
last_task_time = time.time()
state_lock = threading.Lock()


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


def process_task():
    """Simulate processing a background task."""
    global last_task_time

    TASKS_IN_PROGRESS.inc()
    task_type = random.choice(['data_processing', 'cleanup', 'health_check', 'metrics_collection'])

    try:
        logger.info(f"Processing task: {task_type}")

        # Simulate task processing
        processing_time = random.uniform(0.1, 2.0)
        time.sleep(processing_time)

        # Update Redis if connected
        if update_redis_status():
            redis_client.incr(f'worker:tasks:{task_type}')
            redis_client.set('worker:last_task', task_type)
            redis_client.set('worker:last_task_time', str(time.time()))

        # Record metrics
        TASKS_PROCESSED.labels(task_type=task_type, status='success').inc()
        with state_lock:
            last_task_time = time.time()
        LAST_TASK_TIMESTAMP.set(last_task_time)

        logger.info(f"Task {task_type} completed in {processing_time:.2f}s")

    except Exception as e:
        logger.error(f"Error processing task {task_type}: {e}")
        TASKS_PROCESSED.labels(task_type=task_type, status='error').inc()

    finally:
        TASKS_IN_PROGRESS.dec()


def run_scheduler():
    """Run the task scheduler in a separate thread."""
    # Schedule tasks
    schedule.every(10).seconds.do(process_task)

    logger.info("Scheduler started - processing tasks every 10 seconds")

    while True:
        with state_lock:
            if not worker_running:
                break
        schedule.run_pending()
        time.sleep(1)


# Flask health check endpoints

@app.route('/health/live', methods=['GET'])
def liveness():
    """Liveness probe endpoint."""
    return jsonify({
        'status': 'alive',
        'service': 'worker-service',
        'timestamp': time.time()
    }), 200


@app.route('/health/ready', methods=['GET'])
def readiness():
    """Readiness probe endpoint."""
    # Check if scheduler is running and tasks are being processed
    with state_lock:
        time_since_last_task = time.time() - last_task_time
    redis_ready = update_redis_status()

    # Consider ready if last task was within 30 seconds
    if time_since_last_task < 30:
        return jsonify({
            'status': 'ready',
            'service': 'worker-service',
            'redis_connected': redis_ready,
            'last_task_seconds_ago': round(time_since_last_task, 2),
            'timestamp': time.time()
        }), 200
    else:
        return jsonify({
            'status': 'not_ready',
            'service': 'worker-service',
            'redis_connected': redis_ready,
            'last_task_seconds_ago': round(time_since_last_task, 2),
            'message': 'No recent task processing',
            'timestamp': time.time()
        }), 503


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/status', methods=['GET'])
def status():
    """Get worker status."""
    redis_ready = update_redis_status()
    with state_lock:
        time_since_last_task = time.time() - last_task_time

    task_stats = {}
    if redis_ready:
        try:
            for task_type in ['data_processing', 'cleanup', 'health_check', 'metrics_collection']:
                count = redis_client.get(f'worker:tasks:{task_type}')
                task_stats[task_type] = int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting task stats from Redis: {e}")

    # Get connection pool statistics
    pool_stats = redis_client.get_pool_stats()

    return jsonify({
        'service': 'worker-service',
        'status': 'running',
        'environment': APP_ENV,
        'redis_connected': redis_ready,
        'last_task_seconds_ago': round(time_since_last_task, 2),
        'task_stats': task_stats,
        'redis_pool': {
            'available': pool_stats.get('available', 0),
            'in_use': pool_stats.get('in_use', 0),
            'max_connections': pool_stats.get('max_connections', 0)
        },
        'timestamp': time.time()
    }), 200


if __name__ == '__main__':
    logger.info(f"Starting Worker Service")
    logger.info(f"Environment: {APP_ENV}")
    logger.info(f"Health check server on {HOST}:{PORT}")

    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Run Flask app for health checks
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=DEBUG
        )
    except KeyboardInterrupt:
        logger.info("Shutting down worker service...")
        with state_lock:
            worker_running = False
