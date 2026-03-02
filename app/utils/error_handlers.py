from flask import render_template, request
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        app.logger.warning(f'404 error: {request.path}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors"""
        app.logger.warning(f'403 error: {request.path}')
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f'500 error: {str(error)}', exc_info=True)
        # Rollback database session on error
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions"""
        # Pass through HTTP errors
        if isinstance(error, HTTPException):
            return error
        
        # Log the error
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        
        # Return 500 error page
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500