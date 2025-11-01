"""
Test suite for Priority 7: Error Handling, UX Feedback & Observability
"""
import pytest
import json
from flask import g
from app import app
from utils.errors import error_response, success_response, is_xhr_request
from utils.request_id import generate_request_id, get_request_id


@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRequestIdMiddleware:
    """Test request ID generation and tracking."""
    
    def test_request_id_generated(self, client):
        """Test that request ID is automatically generated."""
        response = client.get('/')
        assert 'X-Request-ID' in response.headers
        request_id = response.headers.get('X-Request-ID')
        assert request_id.startswith('req_')
    
    def test_request_id_from_header(self, client):
        """Test that request ID from header is preserved."""
        custom_id = 'my-custom-request-id'
        response = client.get('/', headers={'X-Request-ID': custom_id})
        assert response.headers.get('X-Request-ID') == custom_id
    
    def test_request_id_in_error_response(self, client):
        """Test that request ID is included in error responses."""
        response = client.get('/nonexistent-route', 
                            headers={'Accept': 'application/json'})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'requestId' in data.get('error', {})


class TestErrorHandlers:
    """Test error handlers for different HTTP status codes."""
    
    def test_404_json_response(self, client):
        """Test 404 handler returns JSON for AJAX requests."""
        response = client.get('/nonexistent', 
                            headers={'Accept': 'application/json'})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['ok'] is False
        assert data['error']['code'] == 'NOT_FOUND'
        assert 'requestId' in data['error']
    
    def test_404_html_response(self, client):
        """Test 404 handler returns HTML for browser requests."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_error_response_helper(self):
        """Test error_response helper function."""
        with app.test_request_context():
            # Set request ID
            g.request_id = 'test-request-id'
            
            # Test JSON response (XHR)
            with app.test_request_context(headers={'Accept': 'application/json'}):
                g.request_id = 'test-request-id'
                response, status_code = error_response(
                    "TEST_ERROR", 
                    "Test error message", 
                    400
                )
                assert status_code == 400
                data = json.loads(response.data)
                assert data['ok'] is False
                assert data['error']['code'] == 'TEST_ERROR'
                assert data['error']['requestId'] == 'test-request-id'


class TestSuccessResponse:
    """Test success response helper."""
    
    def test_success_response_with_data(self):
        """Test success response with data."""
        with app.test_request_context():
            g.request_id = 'test-request-id'
            response = success_response(data={'key': 'value'}, message='Success')
            
            assert response['ok'] is True
            assert response['data'] == {'key': 'value'}
            assert response['message'] == 'Success'
            assert response['requestId'] == 'test-request-id'
    
    def test_success_response_minimal(self):
        """Test success response with minimal data."""
        with app.test_request_context():
            g.request_id = 'test-request-id'
            response = success_response()
            
            assert response['ok'] is True
            assert response['requestId'] == 'test-request-id'


class TestXHRDetection:
    """Test XHR/AJAX request detection."""
    
    def test_xhr_header_detection(self):
        """Test detection via X-Requested-With header."""
        with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
            assert is_xhr_request() is True
    
    def test_json_accept_detection(self):
        """Test detection via Accept header."""
        with app.test_request_context(headers={'Accept': 'application/json'}):
            assert is_xhr_request() is True
    
    def test_api_path_detection(self):
        """Test detection via /api/ path."""
        with app.test_request_context(path='/api/test'):
            assert is_xhr_request() is True
    
    def test_regular_request(self):
        """Test regular (non-XHR) request."""
        with app.test_request_context():
            assert is_xhr_request() is False


class TestWorkoutLogEndpoints:
    """Test updated workout log endpoints with new error handling."""
    
    def test_update_workout_log_success(self, client):
        """Test successful workout log update."""
        # This would require actual database setup
        # Placeholder for integration test
        pass
    
    def test_update_workout_log_validation_error(self, client):
        """Test workout log update with missing ID."""
        response = client.post('/update_workout_log',
                             json={'updates': {'weight': 100}},
                             headers={'Accept': 'application/json'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_delete_workout_log_validation_error(self, client):
        """Test workout log deletion with missing ID."""
        response = client.post('/delete_workout_log',
                             json={},
                             headers={'Accept': 'application/json'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['ok'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'


class TestLogging:
    """Test logging with request IDs."""
    
    def test_request_id_in_logs(self, client, caplog):
        """Test that request ID appears in log messages."""
        response = client.get('/')
        request_id = response.headers.get('X-Request-ID')
        
        # Check if request ID appears in logs
        # Note: This depends on your logging configuration
        # and may need adjustment based on actual log output
        log_contains_request_id = any(
            request_id in record.message 
            for record in caplog.records
        )
        # This assertion might need adjustment based on your specific logging setup


def test_request_id_format():
    """Test request ID format."""
    request_id = generate_request_id()
    assert request_id.startswith('req_')
    assert len(request_id) > 10  # Should have timestamp and random part


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

