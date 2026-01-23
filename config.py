"""
Production Configuration for Face Manager Web Application
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///face_manager.db'
    
    # Redis configuration for sessions and caching
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Face recognition settings
    FACES_DIR = os.environ.get('FACES_DIR') or 'faces'
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'models/face_recognition_model.pkl'
    
    # CCTV settings
    MAX_CAMERAS = int(os.environ.get('MAX_CAMERAS', 4))
    CAMERA_QUALITY = int(os.environ.get('CAMERA_QUALITY', 80))
    CAMERA_FPS = int(os.environ.get('CAMERA_FPS', 30))
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_EXTENSIONS = os.environ.get('UPLOAD_EXTENSIONS', 'jpg,jpeg,png').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/face_manager.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_URL = 'sqlite:///face_manager_dev.db'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration"""
    # Override with production-specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Production database (PostgreSQL recommended)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Production Redis
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # Production security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production logging
    LOG_LEVEL = 'WARNING'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
