import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///smart_port.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = False
    # Without this, Flask-JWT-Extended never calls token_in_blocklist_loader
    # at all (it defaults to False) -- logout/session-revocation would look
    # like it worked (Session.is_revoked gets set) but every still-unexpired
    # token would keep authorizing requests regardless.
    JWT_BLOCKLIST_ENABLED = True
    JWT_BLOCKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    BCRYPT_LOG_ROUNDS = 12
    
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@smartport.gov.in')
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000,http://127.0.0.1:5500').split(',')

    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5501')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Flask enforces this on every request regardless of whether a dedicated
    # upload endpoint exists -- kept as a real defensive limit, unlike the
    # other settings that were removed here for being read nowhere in the app
    # (UPLOAD_FOLDER/ALLOWED_EXTENSIONS with no upload endpoint,
    # PAGINATION_DEFAULT_PER_PAGE/MAX_PER_PAGE and API_PREFIX with every
    # blueprint hardcoding its own values instead, LOG_LEVEL/LOG_FORMAT never
    # wired to the logging setup, and DEFAULT_ROLES/DEFAULT_PERMISSIONS -- a
    # stale 4-role vocabulary from before the 9-role port-domain model in
    # app/models/user.py::UserRole existed).
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    JWT_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # In-memory SQLite uses StaticPool, which doesn't accept the QueuePool-only
    # options (pool_size/max_overflow) set on the base Config for Postgres.
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    JWT_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    LOG_LEVEL = 'WARNING'

    # Use Redis only when one is actually configured (e.g. a paid add-on).
    # Defaulting to a Redis URL that points nowhere when REDIS_URL is unset
    # meant this silently fell back to a no-op cache and put rate-limit
    # storage at risk of connection errors on any free-tier deploy that
    # never provisions Redis -- fall back to the same in-process storage
    # the base Config already uses instead.
    _redis_url = os.getenv('REDIS_URL')
    if _redis_url:
        RATELIMIT_STORAGE_URL = _redis_url
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = _redis_url


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}