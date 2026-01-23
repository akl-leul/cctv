#!/usr/bin/env python3
"""
Simple Production Startup Script for Face Manager Web Application
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

def check_core_dependencies():
    """Check if core dependencies are installed"""
    core_packages = ['flask', 'opencv-python', 'numpy', 'pillow', 'werkzeug']
    
    missing_packages = []
    for package in core_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'werkzeug':
                import werkzeug
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing core packages: {', '.join(missing_packages)}")
        print("Installing core packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, check=True)
            print("✅ Core packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    print("✅ All core dependencies available")
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
        # Simple database initialization
        import sqlite3
        from werkzeug.security import generate_password_hash
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin user if not exists
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            admin_password = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@facemanager.com', admin_password, 'admin'))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized with admin user")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def start_web_app():
    """Start the web application"""
    print("🚀 Starting Face Manager Web Application...")
    print("=" * 50)
    print("📍 Access: http://localhost:5000")
    print("👤 Login: admin / admin123")
    print("=" * 50)
    
    try:
        # Set environment variables
        os.environ.setdefault('FLASK_ENV', 'development')
        os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Import and run the web app
        import web_app
        
        # Start the application
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        web_app.app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🎯 Face Manager Web Application - Production Startup")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Check core dependencies
    if not check_core_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        sys.exit(1)
    
    # Start web application
    if not start_web_app():
        sys.exit(1)

if __name__ == '__main__':
    main()
