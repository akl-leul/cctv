import cv2
import numpy as np
import threading
import time
import json
import os
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import qrcode
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkCameraServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secrets.token_hex(16)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Camera management
        self.active_cameras = {}
        self.camera_connections = {}
        
        # Authentication
        self.access_codes = {}
        self.valid_connections = {}
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio_events()
        
        # Create directories
        os.makedirs("network_cameras", exist_ok=True)
        os.makedirs("access_codes", exist_ok=True)
        
        logger.info("Network Camera Server initialized")
    
    def generate_access_code(self, camera_name="mobile_camera", expiry_hours=24):
        """Generate a secure access code for camera connection"""
        code = secrets.token_urlsafe(8)
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)
        
        # Store access code
        self.access_codes[code] = {
            'camera_name': camera_name,
            'expiry_time': expiry_time.isoformat(),
            'created_time': datetime.now().isoformat(),
            'used': False
        }
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"CCTV_CONNECT:{code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_path = f"access_codes/qr_{code}.png"
        img.save(qr_path)
        
        logger.info(f"Generated access code: {code} for camera: {camera_name}")
        logger.info(f"QR code saved to: {qr_path}")
        
        return {
            'code': code,
            'qr_path': qr_path,
            'expiry_time': expiry_time.isoformat(),
            'connection_url': f"http://{self.get_local_ip()}:5000/connect/{code}"
        }
    
    def get_local_ip(self):
        """Get local IP address"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def validate_access_code(self, code):
        """Validate access code"""
        if code not in self.access_codes:
            return False, "Invalid access code"
        
        access_data = self.access_codes[code]
        
        # Check expiry
        expiry_time = datetime.fromisoformat(access_data['expiry_time'])
        if datetime.now() > expiry_time:
            return False, "Access code expired"
        
        # Mark as used
        access_data['used'] = True
        access_data['used_time'] = datetime.now().isoformat()
        
        return True, "Access granted"
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/generate_code')
        def generate_code():
            camera_name = request.args.get('camera_name', 'mobile_camera')
            expiry_hours = int(request.args.get('expiry_hours', 24))
            
            code_data = self.generate_access_code(camera_name, expiry_hours)
            return jsonify(code_data)
        
        @self.app.route('/connect/<code>')
        def connect_page(code):
            valid, message = self.validate_access_code(code)
            if not valid:
                return f"<h1>Access Denied</h1><p>{message}</p>", 403
            
            return render_template('camera_connect.html', code=code)
        
        @self.app.route('/api/camera/stream/<camera_id>')
        def camera_stream(camera_id):
            valid, message = self.validate_access_code(camera_id)
            if not valid:
                return jsonify({'error': message}), 403
            
            def generate_frames():
                while camera_id in self.active_cameras:
                    frame = self.active_cameras[camera_id].get('frame')
                    if frame is not None:
                        # Encode frame to JPEG
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        frame_bytes = buffer.tobytes()
                        
                        # Create proper MJPEG streaming response
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    else:
                        # Send empty frame if no data
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + b'\xff\xd8\xff\x00\x10JFIF\x00\x01\x00\x01\x00\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x01\x00\x02\x11\x00\x03\x11\x00\x03\x11\x00\x08\xff\xc0\x00\x11\x08\x02\x11\x03\x11\x03\x11\x00\x08\xff\xc4\x00\x11\x08\x02\x11\x03\x11\x03\x11\x00\x08\xff\xc4\x00\x11\x08\x02\x11\x03\x11\x03\x11\x00\x08\xff\xc4\x00\x11\x08\x02\x11\x03\x11\x03\x11\x00\x08\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x03\x11\x00\x08\xff\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x03\x11\x00\x08\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x03\x11\x00\x08\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x03\x11\x00\x08\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x03\x11\x00\x08\xff\xd9\xff\xd9')
                    
                    time.sleep(0.033)  # ~30 FPS
            
            return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/api/camera/upload/<code>', methods=['POST'])
        def upload_frame(code):
            valid, message = self.validate_access_code(code)
            if not valid:
                return jsonify({'error': message}), 403
            
            try:
                # Get image data from request
                image_data = request.files.get('frame')
                if image_data:
                    # Read image
                    nparr = np.frombuffer(image_data.read(), np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Store frame for streaming
                        if code not in self.active_cameras:
                            self.active_cameras[code] = {}
                        
                        self.active_cameras[code]['frame'] = frame
                        self.active_cameras[code]['last_update'] = time.time()
                        
                        return jsonify({'success': True})
                
                return jsonify({'error': 'No frame data received'}), 400
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'active_cameras': len(self.active_cameras),
                'valid_connections': len(self.valid_connections),
                'server_ip': self.get_local_ip(),
                'server_time': datetime.now().isoformat()
            })
        
        @self.app.route('/api/camera/status/<camera_id>')
        def get_camera_status(camera_id):
            """Get status of a specific camera"""
            if camera_id in self.active_cameras:
                camera_data = self.active_cameras[camera_id]
                return jsonify({
                    'active': True,
                    'frame_available': camera_data.get('frame') is not None,
                    'last_update': camera_data.get('last_update', datetime.now().isoformat())
                })
            else:
                return jsonify({
                    'active': False,
                    'frame_available': False
                })
        
        @self.app.route('/api/camera/latest/<camera_id>')
        def get_latest_frame(camera_id):
            """Get latest frame from a specific camera"""
            logger.info(f"📡 Request for latest frame from camera: {camera_id}")
            
            if camera_id in self.active_cameras:
                frame = self.active_cameras[camera_id].get('frame')
                if frame is not None:
                    logger.info(f"✅ Found frame for camera {camera_id} (shape: {frame.shape})")
                    
                    # Encode frame to base64
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_bytes = buffer.tobytes()
                    frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                    
                    logger.info(f"📤 Encoded frame for camera {camera_id} (size: {len(frame_base64)} chars)")
                    
                    return jsonify({
                        'frame': frame_base64,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.warning(f"❌ No frame available for camera {camera_id}")
                    return jsonify({'error': 'No frame available'}), 404
            else:
                logger.warning(f"❌ Camera {camera_id} not found in active cameras")
                logger.info(f"Available cameras: {list(self.active_cameras.keys())}")
                return jsonify({'error': 'Camera not found'}), 404
        
        @self.app.route('/api/cameras')
        def get_all_cameras():
            """Get list of all active camera codes"""
            cameras = []
            for code in self.active_cameras.keys():
                cameras.append(code)
            
            logger.info(f"📋 Camera list requested: {cameras}")
            
            return jsonify({
                'cameras': cameras,
                'count': len(cameras)
            })
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Client connected")
            emit('status', {'message': 'Connected to CCTV Network Server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Client disconnected")
        
        @self.socketio.on('camera_register')
        def handle_camera_register(data):
            code = data.get('code')
            camera_name = data.get('camera_name', 'Unknown')
            
            valid, message = self.validate_access_code(code)
            if not valid:
                emit('error', {'message': message})
                return
            
            # Register camera
            self.valid_connections[code] = {
                'camera_name': camera_name,
                'connected_time': datetime.now().isoformat(),
                'sid': request.sid
            }
            
            emit('registered', {'message': f'Camera {camera_name} registered successfully'})
            logger.info(f"Camera {camera_name} registered with code {code}")
        
        @self.socketio.on('camera_frame')
        def handle_camera_frame(data):
            code = data.get('code')
            frame_data = data.get('frame')  # Base64 encoded frame
            
            if code not in self.valid_connections:
                emit('error', {'message': 'Camera not registered'})
                return
            
            try:
                # Validate frame data before processing
                if not frame_data or not isinstance(frame_data, str):
                    logger.warning(f"Invalid frame data received from camera {code}")
                    return
                
                # Decode base64 frame
                frame_bytes = base64.b64decode(frame_data)
                
                # Validate decoded data
                if len(frame_bytes) == 0:
                    logger.warning(f"Empty frame data received from camera {code}")
                    return
                
                nparr = np.frombuffer(frame_bytes, np.uint8)
                
                if len(nparr) == 0:
                    logger.warning(f"Invalid numpy array from camera {code}")
                    return
                
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None and frame.size > 0:
                    # Store frame
                    if code not in self.active_cameras:
                        self.active_cameras[code] = {}
                        logger.info(f"Created storage for camera {code}")
                    
                    self.active_cameras[code]['frame'] = frame
                    self.active_cameras[code]['last_update'] = time.time()
                    
                    # Log successful frame storage
                    logger.info(f"✅ Stored frame for camera {code} (shape: {frame.shape})")
                    
                    # Broadcast to all connected clients
                    self.socketio.emit('frame_update', {
                        'code': code,
                        'camera_name': self.valid_connections[code]['camera_name'],
                        'timestamp': time.time()
                    })
                else:
                    logger.warning(f"Failed to decode frame from camera {code}")
                
            except Exception as e:
                logger.error(f"Error processing camera frame: {e}")
                # Don't emit error to avoid spamming the client
                pass
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the server"""
        logger.info(f"Starting Network Camera Server on {host}:{port}")
        logger.info(f"Local IP: {self.get_local_ip()}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

# HTML Templates
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CCTV Network Camera Server</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .qr-code { text-align: center; margin: 20px 0; }
        .camera-list { max-height: 300px; overflow-y: auto; }
        .camera-item { padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 CCTV Network Camera Server</h1>
            <p>Connect mobile phone cameras to your CCTV system</p>
        </div>
        
        <div class="section">
            <h2>📱 Generate Access Code</h2>
            <label>Camera Name:</label>
            <input type="text" id="cameraName" value="mobile_camera" style="margin: 5px; padding: 5px;">
            <label>Expiry (hours):</label>
            <input type="number" id="expiryHours" value="24" min="1" max="168" style="margin: 5px; padding: 5px;">
            <button class="btn" onclick="generateCode()">Generate Code</button>
            <div id="codeResult"></div>
        </div>
        
        <div class="section">
            <h2>📊 Server Status</h2>
            <div id="serverStatus" class="status info">Loading...</div>
        </div>
        
        <div class="section">
            <h2>📹 Connected Cameras</h2>
            <div id="cameraList" class="camera-list">No cameras connected</div>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to server');
            updateStatus();
        });
        
        socket.on('frame_update', function(data) {
            console.log('Frame update from:', data.camera_name);
            updateCameraList();
        });
        
        function generateCode() {
            const cameraName = document.getElementById('cameraName').value;
            const expiryHours = document.getElementById('expiryHours').value;
            
            fetch(`/generate_code?camera_name=${cameraName}&expiry_hours=${expiryHours}`)
                .then(response => response.json())
                .then(data => {
                    displayCodeResult(data);
                })
                .catch(error => {
                    console.error('Error generating code:', error);
                });
        }
        
        function displayCodeResult(data) {
            const resultDiv = document.getElementById('codeResult');
            resultDiv.innerHTML = `
                <div class="success">
                    <h3>✅ Access Code Generated</h3>
                    <p><strong>Code:</strong> ${data.code}</p>
                    <p><strong>Connection URL:</strong> ${data.connection_url}</p>
                    <p><strong>Expires:</strong> ${new Date(data.expiry_time).toLocaleString()}</p>
                    <div class="qr-code">
                        <img src="/access_codes/qr_${data.code}.png" alt="QR Code" style="max-width: 200px;">
                        <p>Scan this QR code with your mobile device</p>
                    </div>
                </div>
            `;
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('serverStatus');
                    statusDiv.className = 'status info';
                    statusDiv.innerHTML = `
                        <strong>Server IP:</strong> ${data.server_ip}<br>
                        <strong>Active Cameras:</strong> ${data.active_cameras}<br>
                        <strong>Valid Connections:</strong> ${data.valid_connections}<br>
                        <strong>Server Time:</strong> ${new Date(data.server_time).toLocaleString()}
                    `;
                });
        }
        
        function updateCameraList() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const listDiv = document.getElementById('cameraList');
                    if (data.active_cameras > 0) {
                        listDiv.innerHTML = `<p><strong>${data.active_cameras}</strong> cameras active</p>`;
                    } else {
                        listDiv.innerHTML = 'No cameras connected';
                    }
                });
        }
        
        // Update status every 5 seconds
        setInterval(updateStatus, 5000);
        setInterval(updateCameraList, 5000);
    </script>
</body>
</html>
"""

CAMERA_CONNECT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Connect Camera - CCTV System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #333; color: white; }
        .container { max-width: 600px; margin: 0 auto; text-align: center; }
        .status { padding: 20px; margin: 20px 0; border-radius: 10px; }
        .success { background: #28a745; }
        .info { background: #17a2b8; }
        .camera-preview { width: 100%; max-width: 400px; height: 300px; background: #000; margin: 20px 0; border-radius: 10px; }
        .btn { background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px; }
        .btn:hover { background: #0056b3; }
        .btn.stop { background: #dc3545; }
        .btn.stop:hover { background: #c82333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Connect Your Camera</h1>
        
        <div class="status success">
            <h2>✅ Access Code Valid</h2>
            <p>Your camera can now connect to the CCTV system</p>
        </div>
        
        <div class="camera-preview">
            <video id="cameraPreview" autoplay playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>
        </div>
        
        <div>
            <button class="btn" onclick="startCamera()">🎥 Start Camera</button>
            <button class="btn stop" onclick="stopCamera()">⏹️ Stop Camera</button>
        </div>
        
        <div class="status info">
            <p id="connectionStatus">Ready to connect</p>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script>
        let stream = null;
        let socket = null;
        let code = "{{ code }}";
        
        socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to server');
            document.getElementById('connectionStatus').textContent = 'Connected to server';
        });
        
        socket.on('registered', function(data) {
            console.log('Camera registered:', data);
            document.getElementById('connectionStatus').textContent = data.message;
        });
        
        socket.on('error', function(data) {
            console.error('Error:', data);
            document.getElementById('connectionStatus').textContent = 'Error: ' + data.message;
        });
        
        async function startCamera() {
            try {
                // Get camera stream
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment',
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                });
                
                const video = document.getElementById('cameraPreview');
                video.srcObject = stream;
                
                // Register camera with server
                socket.emit('camera_register', {
                    code: code,
                    camera_name: navigator.userAgent || 'Mobile Camera'
                });
                
                // Start sending frames
                sendFrames();
                
                document.getElementById('connectionStatus').textContent = 'Camera active and streaming';
                
            } catch (error) {
                console.error('Error accessing camera:', error);
                document.getElementById('connectionStatus').textContent = 'Error: ' + error.message;
            }
        }
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            
            const video = document.getElementById('cameraPreview');
            video.srcObject = null;
            
            document.getElementById('connectionStatus').textContent = 'Camera stopped';
        }
        
        function sendFrames() {
            if (stream && stream.active) {
                const video = document.getElementById('cameraPreview');
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                
                ctx.drawImage(video, 0, 0);
                
                // Convert to base64
                const imageData = canvas.toDataURL('image/jpeg', 0.8);
                const base64Data = imageData.split(',')[1];
                
                // Send frame to server
                socket.emit('camera_frame', {
                    code: code,
                    frame: base64Data
                });
                
                // Send next frame
                requestAnimationFrame(sendFrames);
            }
        }
    </script>
</body>
</html>
"""

# Save templates
def save_templates():
    """Save HTML templates"""
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(INDEX_TEMPLATE)
    
    with open('templates/camera_connect.html', 'w', encoding='utf-8') as f:
        f.write(CAMERA_CONNECT_TEMPLATE)
    
    logger.info("HTML templates saved")

if __name__ == "__main__":
    save_templates()
    server = NetworkCameraServer()
    server.run()
