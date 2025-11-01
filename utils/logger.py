"""
Structured logging configuration with request ID support.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from utils.config import LOGS_DIR


class RequestIdFilter(logging.Filter):
    """Filter to add request ID to log records."""
    
    def filter(self, record):
        from flask import g, has_request_context
        
        # Add request ID to log record if available
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'N/A')
        else:
            record.request_id = 'N/A'
        
        return True


def setup_logging(app=None):
    """
    Configure structured logging with file and console handlers.
    Includes request ID in log messages for correlation.
    
    Args:
        app: Flask application instance (optional)
    """
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('hypertrophy_toolbox')
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Add request ID filter
    request_id_filter = RequestIdFilter()
    
    # File handler with rotation (10MB max, keep 5 backups)
    log_file = os.path.join(LOGS_DIR, 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(request_id_filter)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s [%(filename)s:%(lineno)d]'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(request_id_filter)
    console_handler.setFormatter(logging.Formatter(
        '[%(levelname)s] [%(request_id)s] %(message)s'
    ))
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Set Flask app logger if provided
    if app:
        app.logger.handlers = logger.handlers
        app.logger.setLevel(logging.DEBUG)
        
        # Log request details
        @app.before_request
        def log_request_info():
            from flask import request, g
            request_id = getattr(g, 'request_id', 'N/A')
            logger.info(f"Request: {request.method} {request.path}")
        
        @app.after_request
        def log_response_info(response):
            from flask import request, g
            request_id = getattr(g, 'request_id', 'N/A')
            logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
            return response
    
    return logger


# Global logger instance
_logger = None


def get_logger():
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger

