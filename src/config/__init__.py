"""
Configuration module for application settings.
"""

from .config import DB_CONFIG, DEFAULT_METADATA, DOC_CONFIG
from .metadata_config import MetadataManager, Genre, SubGenre
import os
from .development import DevelopmentConfig
from .production import ProductionConfig

__all__ = [
    'DB_CONFIG',
    'DEFAULT_METADATA',
    'DOC_CONFIG',
    'MetadataManager',
    'Genre',
    'SubGenre'
]

def load_config():
    """Load the appropriate configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    
    return DevelopmentConfig

# Create a config instance
config = load_config() 