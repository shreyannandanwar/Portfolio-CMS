import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler
from flask import app, g, request, has_request_context
import os


class RequestIdFilter(logging.Filter):
    """Add request ID to log records"""
    
    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'no-request-id')
            record.ip = request.remote_addr
            record.method = request.method
            record.path = request.path
        else:
            record.request_id = 'no-request-id'
            record.ip = '-'
            record.method = '-'
            record.path = '-'
        return True


def setup_logging(app):
    """Configure application logging"""
    
    # Remove default Flask logger handlers
    app.logger.handlers.clear()
    
    # Create logs directory
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Format for logs
    log_format = (
        '[%(asctime)s] %(levelname)s [%(request_id)s] '
        '%(ip)s %(method)s %(path)s - %(name)s: %(message)s'
    )
    
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    
    # File handler - General logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    
    # File handler - Error logs only
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(RequestIdFilter())
    
    # Add handlers to app logger
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(log_level)
    
    # Log startup
    env_mode = app.config.get('ENV', 'production') # or 'testing'
    app.logger.info(f'Application starting in {env_mode} mode')
    
    # Request ID middleware
    @app.before_request
    def assign_request_id():
        """Assign unique ID to each request"""
        g.request_id = str(uuid.uuid4())[:8]
        app.logger.debug(f'Request started: {request.method} {request.path}')
    
    @app.after_request
    def log_response(response):
        """Log response status"""
        app.logger.info(
            f'Request completed: {request.method} {request.path} '
            f'-> {response.status_code}'
        )
        return response
    
    # Suppress werkzeug logging in production
    if not app.debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    return app.logger