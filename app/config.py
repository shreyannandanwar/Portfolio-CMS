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
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # DATABASE_URL env var is set on Render to point at the persistent disk.
    # Fallback uses /data/portfolio.db — the Render persistent disk mount path.
    # Do NOT use a relative path here; it gets wiped on every redeploy.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:////data/portfolio.db'
    )

    # Secret key — must be set via environment variable on Render
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Security — HTTPS enforced on Render automatically
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')

    # SQLite-safe pool config
    # pool_pre_ping and pool_recycle are PostgreSQL settings.
    # They are harmless with SQLite but kept here so switching to
    # PostgreSQL later requires zero config changes.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Uploads go to persistent disk so they survive redeploys
    UPLOAD_FOLDER = '/data/uploads'


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