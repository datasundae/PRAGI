"""Production configuration."""
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS_URL = 'redis://localhost:6379'
    SESSION_COOKIE_SECURE = True
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL = 'INFO' 