import os
from datetime import timedelta


class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    
    # GitHub Integration
    GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'your-github-username')
    GITHUB_CACHE_DURATION_DAYS = 30
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # Admin URL
    ADMIN_URL_PREFIX = os.getenv('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.abspath('instance'), 'portfolio.db')
    )
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """
    Production configuration — PostgreSQL only.

    Railway injects DATABASE_URL automatically when you attach a Postgres
    plugin.  The URL may start with 'postgres://' (legacy) which SQLAlchemy
    2.x rejects; we normalise it to 'postgresql://' below.
    """
    DEBUG = False
    TESTING = False

    @classmethod
    def _get_db_url(cls) -> str:
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError(
                "DATABASE_URL environment variable must be set in production. "
                "Attach a PostgreSQL plugin on Railway and it will be injected automatically."
            )
        # SQLAlchemy 2.x requires 'postgresql://', not the legacy 'postgres://'
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url

    SQLALCHEMY_DATABASE_URI = None   # set dynamically in __init_subclass__ / app factory

    SECRET_KEY = os.getenv('SECRET_KEY')

    # Security — HTTPS enforced on Render automatically
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    #Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')

    # PostgreSQL connection pool — keeps connections alive across requests
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,       # discard stale connections
        'pool_recycle': 300,         # recycle after 5 min
        'pool_size': 5,              # base pool size
        'max_overflow': 10,          # allow up to 15 total connections
        'connect_args': {
            'connect_timeout': 10,
        },
    }

    # Uploads — Railway volumes or object storage; override via env var
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')



class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    RATELIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])