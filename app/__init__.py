from flask import Flask
import os


def create_app(config_name=None):
    """Application factory pattern"""

    app = Flask(__name__, instance_relative_config=True)

    # ── Determine config ────────────────────────────────────────────────────
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from app.config import config
    cfg_class = config[config_name]

    # ProductionConfig derives DATABASE_URL dynamically; resolve it here so
    # SQLAlchemy picks it up before any extension is initialised.
    if config_name == 'production':
        cfg_class.SQLALCHEMY_DATABASE_URI = cfg_class._get_db_url()

    app.config.from_object(cfg_class)

    # ── Validate secrets ────────────────────────────────────────────────────
    if config_name == 'production':
        if not app.config.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production!")
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            raise ValueError("DATABASE_URL environment variable must be set in production!")

    # ── Instance folder ─────────────────────────────────────────────────────
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ── Extensions ──────────────────────────────────────────────────────────
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

    # ── Logging ─────────────────────────────────────────────────────────────
    from app.utils.logging_config import setup_logging
    setup_logging(app)

    # ── Error handlers ──────────────────────────────────────────────────────
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ── Security headers ────────────────────────────────────────────────────
    from app.utils.security import add_security_headers
    add_security_headers(app)

    # ── Database tables ─────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created/verified')

    # ── Blueprints ──────────────────────────────────────────────────────────
    from app.admin import admin_bp
    from app.public import public_bp

    admin_prefix = app.config.get('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')

    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    app.register_blueprint(public_bp)

    app.logger.info(f'Blueprints registered — Admin: {admin_prefix}, Public: /')

    # ── Health check ────────────────────────────────────────────────────────
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring / Railway"""
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