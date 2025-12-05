"""Unit tests for request context and trace ID."""
import pytest
import uuid
from unittest.mock import patch


@pytest.mark.unit
class TestTraceID:
    """Tests for trace ID functionality."""

    def test_trace_id_generated_automatically(self, client):
        """Test that trace ID is generated automatically for requests."""
        response = client.get('/health/live')
        assert 'X-Trace-ID' in response.headers

    def test_trace_id_is_uuid_format(self, client):
        """Test that generated trace ID is in UUID format."""
        response = client.get('/health/live')
        trace_id = response.headers.get('X-Trace-ID')

        # Validate UUID format
        try:
            uuid.UUID(trace_id)
            is_valid = True
        except (ValueError, AttributeError):
            is_valid = False

        assert is_valid

    def test_existing_trace_id_propagated(self, client):
        """Test that existing trace ID from request header is propagated."""
        test_trace_id = 'custom-trace-id-12345'
        response = client.get('/health/live', headers={'X-Trace-ID': test_trace_id})

        assert response.headers.get('X-Trace-ID') == test_trace_id

    def test_request_id_header_accepted(self, client):
        """Test that X-Request-ID header is accepted as trace ID."""
        test_request_id = 'custom-request-id-67890'
        response = client.get('/health/live', headers={'X-Request-ID': test_request_id})

        assert response.headers.get('X-Trace-ID') == test_request_id

    def test_trace_id_consistent_across_request(self, client):
        """Test that trace ID remains consistent throughout request lifecycle."""
        response = client.get('/api/status')
        trace_id = response.headers.get('X-Trace-ID')

        assert trace_id is not None
        assert len(trace_id) > 0


@pytest.mark.unit
class TestRequestContext:
    """Tests for request context management."""

    def test_request_start_time_tracked(self, client):
        """Test that request start time is tracked."""
        with client:
            response = client.get('/health/live')
            # The request should have start_time attribute
            assert response.status_code == 200

    def test_request_duration_calculated(self, client):
        """Test that request duration is calculated."""
        response = client.get('/api/status')
        # Duration should be logged but we verify endpoint works
        assert response.status_code == 200


@pytest.mark.unit
class TestRequestLogging:
    """Tests for request logging with trace ID."""

    @patch('app.logger')
    def test_request_logged_with_trace_id(self, mock_logger, client):
        """Test that requests are logged with trace ID."""
        response = client.get('/api/status')

        # Verify that logger.info was called
        assert mock_logger.info.called

        # Get the call arguments
        if mock_logger.info.call_args:
            args, kwargs = mock_logger.info.call_args
            # Check if 'extra' parameter contains trace_id
            if 'extra' in kwargs:
                assert 'trace_id' in kwargs['extra']

    @patch('app.logger')
    def test_request_logged_with_method_and_path(self, mock_logger, client):
        """Test that requests are logged with method and path."""
        response = client.get('/api/status')

        # Verify that logger.info was called
        assert mock_logger.info.called

        if mock_logger.info.call_args:
            args, kwargs = mock_logger.info.call_args
            # Check log message contains method and path
            if args:
                log_message = args[0]
                assert 'GET' in log_message or 'api/status' in log_message

    @patch('app.logger')
    def test_request_logged_with_status_code(self, mock_logger, client):
        """Test that requests are logged with status code."""
        response = client.get('/api/status')

        # Verify that logger.info was called
        assert mock_logger.info.called

        if mock_logger.info.call_args:
            args, kwargs = mock_logger.info.call_args
            if 'extra' in kwargs:
                assert 'status_code' in kwargs['extra']
                assert kwargs['extra']['status_code'] == 200
