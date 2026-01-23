#!/usr/bin/env python3
"""
Production-ready Web-based Face Manager Application
Features: Authentication, Face Management, CCTV System, Network Cameras
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import cv2
import numpy as np
from datetime import datetime
import base64
import io
from PIL import Image
import sqlite3
import threading
import time
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize Face Manager
try:
    from face_data_manager import FaceDataManager
    face_manager = FaceDataManager()
    logger.info("Face Manager initialized successfully")
except ImportError as e:
    logger.warning(f"Face Manager not available: {e}")
    face_manager = None

# Global variables for CCTV system
cctv_running = False
cctv_thread = None
camera_frames = {}
camera_threads = {}

class User(UserMixin):
    def __init__(self, id, username, email, role='user'):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

# Flask-Login setup
try:
    from flask_login import LoginManager, login_user, logout_user, login_required, current_user
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[4])
        return None
except ImportError as e:
    logger.warning(f"Flask-Login not available: {e}")
    # Fallback authentication system
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    class MockUser:
        def __init__(self, id, username, email, role='user'):
            self.id = id
            self.username = username
            self.email = email
            self.role = role
            self.is_authenticated = True
    
    current_user = MockUser(1, 'admin', 'admin@test.com', 'admin')

def init_database():
    """Initialize the database with admin user"""
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
    logger.info("Database initialized with admin user")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(current_user, 'role') and current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if session.get('user_id') or (hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[3], password):
            session['user_id'] = user_data[0]
            session['username'] = user_data[1]
            session['role'] = user_data[4]
            logger.info(f"User {username} logged in")
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login'))

@app.route('/api/users')
def get_users():
    try:
        if not face_manager:
            return jsonify({'error': 'Face Manager not available'}), 500
            
        users = face_manager.get_all_users()
        user_list = []
        for user in users:
            images = face_manager.get_user_images(user)
            user_list.append({
                'name': user,
                'image_count': len(images),
                'last_updated': max([os.path.getmtime(img) for img in images]) if images else None
            })
        return jsonify({'users': user_list})
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/images')
def get_user_images(username):
    try:
        if not face_manager:
            return jsonify({'error': 'Face Manager not available'}), 500
            
        images = face_manager.get_user_images(username)
        image_data = []
        for img_path in images:
            with open(img_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
                image_data.append({
                    'filename': os.path.basename(img_path),
                    'data': img_data
                })
        return jsonify({'images': image_data})
    except Exception as e:
        logger.error(f"Error getting user images: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/register', methods=['POST'])
def register_user():
    try:
        if not face_manager:
            return jsonify({'error': 'Face Manager not available'}), 500
            
        data = request.get_json()
        username = data.get('username')
        image_data = data.get('image')
        
        if not username or not image_data:
            return jsonify({'error': 'Username and image required'}), 400
        
        # Decode and save image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save to face manager
        face_manager.create_user(username)
        image_path = os.path.join('faces', username, f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)
        
        return jsonify({'success': True, 'message': f'User {username} registered successfully'})
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cctv/start', methods=['POST'])
def start_cctv():
    global cctv_running, cctv_thread
    
    if cctv_running:
        return jsonify({'error': 'CCTV already running'}), 400
    
    try:
        cctv_running = True
        cctv_thread = threading.Thread(target=cctv_worker)
        cctv_thread.daemon = True
        cctv_thread.start()
        
        logger.info("CCTV system started")
        return jsonify({'success': True, 'message': 'CCTV system started'})
    except Exception as e:
        logger.error(f"Error starting CCTV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cctv/stop', methods=['POST'])
def stop_cctv():
    global cctv_running
    
    if not cctv_running:
        return jsonify({'error': 'CCTV not running'}), 400
    
    try:
        cctv_running = False
        logger.info("CCTV system stopped")
        return jsonify({'success': True, 'message': 'CCTV system stopped'})
    except Exception as e:
        logger.error(f"Error stopping CCTV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cctv/status')
def cctv_status():
    return jsonify({
        'running': cctv_running,
        'cameras': list(camera_frames.keys()),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/camera/<camera_id>/frame')
def get_camera_frame(camera_id):
    if camera_id in camera_frames:
        frame = camera_frames[camera_id]
        if frame is not None:
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
            
            return jsonify({
                'frame': frame_base64,
                'timestamp': datetime.now().isoformat()
            })
    
    return jsonify({'error': 'Camera frame not available'}), 404

def cctv_worker():
    """CCTV worker thread for web application"""
    global camera_frames, cctv_running
    
    # Initialize cameras
    cameras = {}
    for i in range(2):  # Support up to 2 local cameras
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            cameras[f'local_{i}'] = cap
            logger.info(f"Camera local_{i} initialized")
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    while cctv_running:
        for camera_id, cap in cameras.items():
            if cctv_running:
                ret, frame = cap.read()
                if ret:
                    # Face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
                    
                    # Draw face rectangles
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, "Face Detected", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    camera_frames[camera_id] = frame.copy()
        
        time.sleep(0.033)  # ~30 FPS
    
    # Release cameras
    for cap in cameras.values():
        cap.release()
    logger.info("CCTV worker stopped")

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Create directories
    os.makedirs('faces', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Face Manager Web App on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
