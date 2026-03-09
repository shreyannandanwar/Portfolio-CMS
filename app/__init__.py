from flask import Flask
import os


def create_app(config_name=None):
    """Application factory pattern"""

    app = Flask(__name__, instance_relative_config=True)

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from app.config import config
    cfg_class = config[config_name]

    if config_name == 'production':
        cfg_class.SQLALCHEMY_DATABASE_URI = cfg_class._get_db_url()

    app.config.from_object(cfg_class)

    if config_name == 'production':
        if not app.config.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production!")
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            raise ValueError("DATABASE_URL environment variable must be set in production!")

        # Fix for Render's reverse proxy — trust the X-Forwarded-Proto header
        # so Flask knows the request came in over HTTPS even though gunicorn
        # sees HTTP internally. Without this, url_for() generates http:// URLs
        # and SESSION_COOKIE_SECURE cookies are never sent back by the browser.
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from app.extensions import db, login_manager, csrf

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from app.models.user import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    from app.utils.logging_config import setup_logging
    setup_logging(app)

    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    from app.utils.security import add_security_headers
    add_security_headers(app)

    with app.app_context():
        auto_create = os.getenv('AUTO_CREATE_DB', '').strip().lower() in ('1', 'true', 'yes')
        if config_name != 'production' or auto_create:
            db.create_all()
            app.logger.info('Database tables created/verified')
        else:
            app.logger.info(
                'Skipping db.create_all() in production. '
                'Run "python init_db.py" (or your migration tool) to initialise the schema. '
                'Set AUTO_CREATE_DB=1 to override this behaviour.'
            )

    from app.admin import admin_bp
    from app.public import public_bp
    from app.setup import setup_bp

    admin_prefix = app.config.get('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')

    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    app.register_blueprint(public_bp)
    app.register_blueprint(setup_bp)

    app.logger.info(f'Blueprints registered — Admin: {admin_prefix}, Public: /')

    @app.route('/health')
    def health_check():
        from app.extensions import db as _db
        try:
            _db.session.execute(_db.text('SELECT 1'))
            db_ok = True
        except Exception:
            db_ok = False
        status = 'healthy' if db_ok else 'degraded'
        return {'status': status, 'environment': config_name, 'db': db_ok}, 200 if db_ok else 503

    app.logger.info(f'Application initialised in {config_name} mode')

    return app