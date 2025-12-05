"""Input validation schemas using marshmallow.

This module provides input validation for API endpoints to ensure
data integrity and security.
"""
from marshmallow import Schema, fields, validate, ValidationError
from functools import wraps
from flask import request, jsonify


class HealthCheckQuerySchema(Schema):
    """Schema for health check query parameters."""
    detailed = fields.Boolean(missing=False)
    timeout = fields.Integer(missing=5, validate=validate.Range(min=1, max=30))


class StatusQuerySchema(Schema):
    """Schema for status query parameters."""
    include_redis = fields.Boolean(missing=True)
    include_pool_stats = fields.Boolean(missing=True)


def validate_query_params(schema_class):
    """Decorator to validate query parameters.

    Args:
        schema_class: Marshmallow schema class for validation

    Returns:
        Decorated function with validation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            schema = schema_class()
            try:
                # Validate query parameters
                validated_data = schema.load(request.args)
                # Add validated data to request context
                request.validated_query = validated_data
                return func(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Invalid query parameters',
                    'details': err.messages
                }), 400
        return wrapper
    return decorator


def validate_json(schema_class):
    """Decorator to validate JSON request body.

    Args:
        schema_class: Marshmallow schema class for validation

    Returns:
        Decorated function with validation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            schema = schema_class()
            try:
                # Validate JSON body
                if not request.is_json:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': 'Request must be JSON'
                    }), 400

                validated_data = schema.load(request.get_json())
                # Add validated data to request context
                request.validated_json = validated_data
                return func(*args, **kwargs)
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Invalid request body',
                    'details': err.messages
                }), 400
        return wrapper
    return decorator
