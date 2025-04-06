"""Development configuration."""
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Session
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    
    # Logging
    LOG_LEVEL = 'DEBUG' 