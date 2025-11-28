"""Configuration for API Gateway service."""
import os

class Config:
    """Application configuration."""

    # Flask
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8080'))

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))

    # Application
    APP_ENV = os.getenv('APP_ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Service discovery
    WORKER_SERVICE_URL = os.getenv('WORKER_SERVICE_URL', 'http://localhost:8081')
