import os
from datetime import timedelta


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'

    GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'your-github-username')
    GITHUB_CACHE_DURATION_DAYS = 30

    POSTS_PER_PAGE = 10

    ADMIN_URL_PREFIX = os.getenv('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.abspath('instance'), 'portfolio.db')
    )
    SQLALCHEMY_ECHO = True
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """
    Production — PostgreSQL via Supabase session pooler.

    SESSION_COOKIE_SAMESITE = 'Lax':
        'Strict' causes the browser to drop the session cookie when Render's
        proxy redirects after login, logging the user out immediately.
        'Lax' keeps the cookie across same-site top-level navigations.

    SESSION_COOKIE_SECURE = True:
        Render terminates SSL at the proxy layer and forwards as HTTP internally.
        Flask-Login needs REMEMBER_COOKIE_SECURE and SESSION_COOKIE_SECURE=True
        so the cookie is only sent over HTTPS from the browser side.

    PREFERRED_URL_SCHEME = 'https':
        Tells Flask that the canonical URL scheme is https even though gunicorn
        sees http internally (Render's proxy strips SSL before forwarding).
    """
    DEBUG = False
    TESTING = False

    @classmethod
    def _get_db_url(cls) -> str:
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError(
                "DATABASE_URL must be set in production. "
                "Use the Session Pooler connection string from Supabase."
            )
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url

    SQLALCHEMY_DATABASE_URI = None  # resolved in app factory

    SECRET_KEY = os.getenv('SECRET_KEY')

    # Lax (not Strict) — prevents cookie being dropped on proxy redirects
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Tell Flask the public-facing scheme is https
    PREFERRED_URL_SCHEME = 'https'

    WTF_CSRF_ENABLED = True
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_size': 3,
        'max_overflow': 5,
        'connect_args': {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
            'sslmode': 'require',
        },
    }

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    RATELIMIT_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])