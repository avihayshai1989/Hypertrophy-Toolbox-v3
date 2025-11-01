"""
Standardized API error responses and helpers.
"""
from flask import jsonify, render_template, request, g
from typing import Optional, Dict, Any


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def get_request_id():
    """Get the current request ID from Flask g object."""
    return getattr(g, 'request_id', None)


def is_xhr_request():
    """Check if the request is an XHR/AJAX request."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        request.headers.get('Accept', '').find('application/json') != -1 or
        request.path.startswith('/api/')
    )


def success_response(data: Any = None, message: Optional[str] = None) -> Dict:
    """
    Standard success response format.
    
    Args:
        data: Response data (optional)
        message: Optional success message
    
    Returns:
        Dict with standardized success format
    """
    response = {"ok": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    
    # Add request ID if available
    request_id = get_request_id()
    if request_id:
        response["requestId"] = request_id
    
    return response


def error_response(code: str, message: str, status_code: int = 400, **kwargs) -> tuple:
    """
    Standard error response format with automatic XHR/HTML detection.
    Returns JSON for XHR requests, HTML page for browser navigation.
    
    Args:
        code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Error message
        status_code: HTTP status code
        **kwargs: Additional error details
    
    Returns:
        Tuple of (response, status_code)
    """
    request_id = get_request_id()
    
    error_data = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "requestId": request_id,
            **kwargs
        }
    }
    
    # Return JSON for XHR requests
    if is_xhr_request():
        return jsonify(error_data), status_code
    
    # Return themed HTML page for browser navigation
    return render_template(
        'error.html',
        error_code=status_code,
        error_title=get_error_title(status_code),
        error_message=message,
        error_detail_code=code,
        request_id=request_id
    ), status_code


def get_error_title(status_code: int) -> str:
    """Get a user-friendly title for the error status code."""
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        503: "Service Unavailable"
    }
    return titles.get(status_code, "Error")


# Common error codes
ERROR_CODES = {
    "VALIDATION_ERROR": 400,
    "NOT_FOUND": 404,
    "FORBIDDEN": 403,
    "INTERNAL_ERROR": 500,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "UNPROCESSABLE_ENTITY": 422,
}


def register_error_handlers(app):
    """
    Register standardized error handlers for common HTTP errors.
    
    Args:
        app: Flask application instance
    """
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request errors."""
        return error_response(
            "BAD_REQUEST",
            "The request could not be understood or was missing required parameters.",
            400
        )
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return error_response(
            "NOT_FOUND",
            "The requested resource could not be found.",
            404
        )
    
    @app.errorhandler(422)
    def unprocessable_entity(e):
        """Handle 422 Unprocessable Entity errors."""
        return error_response(
            "UNPROCESSABLE_ENTITY",
            "The request was well-formed but contained invalid data.",
            422
        )
    
    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server errors."""
        # Log the error
        app.logger.exception(f"Internal server error: {e}")
        
        return error_response(
            "INTERNAL_ERROR",
            "An internal server error occurred. Please try again later.",
            500
        )
    
    @app.errorhandler(APIError)
    def handle_api_error(e):
        """Handle custom APIError exceptions."""
        return error_response(e.code, e.message, e.status_code)
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle any unexpected exceptions."""
        # Don't handle HTTP exceptions here (they're handled above)
        if isinstance(e, HTTPException):
            return e
        
        # Log the unexpected error
        app.logger.exception(f"Unexpected error: {e}")
        
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again later.",
            500
        )

