#!/usr/bin/env python3
"""
Production Startup Script for Face Manager Web Application
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/face_manager.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask', 'flask_login', 'opencv-python', 'numpy', 
        'pillow', 'requests', 'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def check_environment():
    """Check environment configuration"""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    required_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("Copy .env.example to .env and configure the variables")
        return False
    
    print("✅ Environment variables configured")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['faces', 'models', 'logs', 'static', 'templates']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def initialize_database():
    """Initialize the database"""
    try:
        from web_app import init_database
        init_database()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_development_server():
    """Start development server"""
    print("🚀 Starting development server...")
    try:
        subprocess.run([sys.executable, 'web_app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return False
    return True

def start_production_server():
    """Start production server with Gunicorn"""
    print("🚀 Starting production server with Gunicorn...")
    try:
        cmd = [
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            'web_app:app'
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
        return False
    return True

def main():
    """Main startup function"""
    print("🎯 Face Manager Web Application - Production Startup")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Determine server type
    server_type = os.environ.get('FLASK_ENV', 'development')
    
    if server_type == 'production':
        # Start production server
        if not start_production_server():
            sys.exit(1)
    else:
        # Start development server
        if not start_development_server():
            sys.exit(1)

if __name__ == '__main__':
    main()
