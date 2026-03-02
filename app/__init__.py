from flask import Flask
import os


def create_app(config_name=None):
    """Application factory pattern"""
    
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Validate production config
    if config_name == 'production':
        if not app.config.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production!")
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    from app.extensions import db, login_manager, csrf
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    from app.models.user import AdminUser
    
    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))
    
    # Setup logging (before blueprints to catch all logs)
    from app.utils.logging_config import setup_logging
    setup_logging(app)
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Add security headers
    from app.utils.security import add_security_headers
    add_security_headers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created/verified')
    
    # Register blueprints
    from app.admin import admin_bp
    from app.public import public_bp
    
    # Get admin URL prefix from config
    admin_prefix = app.config.get('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')
    
    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    app.register_blueprint(public_bp)
    
    app.logger.info(f'Blueprints registered - Admin: {admin_prefix}, Public: /')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return {'status': 'healthy', 'environment': config_name}, 200
    
    app.logger.info(f'Application initialized in {config_name} mode')
    
    return app