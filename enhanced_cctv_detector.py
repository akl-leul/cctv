import cv2
import numpy as np
import time
import threading
import os
from datetime import datetime
import json
import requests
import base64
import io
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from face_data_manager import FaceDataManager
import pyttsx3
import socket
import subprocess
import platform

class EnhancedCCTVDetector:
    def __init__(self):
        self.running = False
        self.detection_active = True
        self.recording = False
        self.face_cascade = None
        self.known_faces = {}
        self.face_encodings = {}
        self.detection_log = []
        self.alert_threshold = 3
        self.alert_cooldown = 30
        self.last_alert_time = {}
        
        # Video settings
        self.output_dir = "cctv_recordings"
        self.log_file = "cctv_log.json"
        
        # Network camera settings
        self.network_cameras = {}
        self.camera_sources = []
        self.current_camera_index = 0
        self.camera_type = "local"  # "local" or "network"
        
        # Text-to-speech
        self.tts_available = False
        try:
            import pyttsx3
            self.tts_available = True
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            print("✅ Text-to-speech engine initialized")
        except ImportError:
            print("⚠️ Text-to-speech not available. Install with: pip install pyttsx3")
        
        # Unknown face tracking
        self.unknown_face_present = False
        self.last_unknown_alert_time = 0
        self.unknown_alert_cooldown = 3
        self.last_unknown_detection_time = 0
        self.last_face_announcement_time = {} # Track when each face was last announced
        self.face_announcement_cooldown = 20 # seconds cooldown
        
        # Initialize shared face data manager
        self.face_manager = FaceDataManager()
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize face detection
        self.load_face_cascade()
        
        # Load known faces
        self.load_known_faces()
        
        # Network camera server
        self.network_server_url = None
        self.available_network_cameras = []
    
    def load_face_cascade(self):
        """Load OpenCV face cascade classifier"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("✅ Face cascade loaded successfully")
        except Exception as e:
            print(f"❌ Error loading face cascade: {e}")
            self.face_cascade = None
    
    def load_known_faces(self):
        """Load known faces from shared face manager"""
        try:
            self.known_faces = self.face_manager.get_face_encodings()
            print(f"✅ Loaded {len(self.known_faces)} known faces from shared manager")
        except Exception as e:
            print(f"❌ Error loading known faces: {e}")
            self.known_faces = {}
    
    def scan_network_cameras(self, server_url="http://localhost:5000"):
        """Scan for available network cameras"""
        try:
            response = requests.get(f"{server_url}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.network_server_url = server_url
                self.available_network_cameras = [f"network_{i}" for i in range(data.get('active_cameras', 0))]
                print(f"✅ Found {len(self.available_network_cameras)} network cameras")
                return True
        except Exception as e:
            print(f"⚠️ Could not connect to network camera server: {e}")
        return False
    
    def add_network_camera(self, camera_name, stream_url):
        """Add a network camera source"""
        self.network_cameras[camera_name] = {
            'url': stream_url,
            'type': 'network',
            'last_frame': None,
            'last_update': 0
        }
        self.camera_sources.append(('network', camera_name))
        print(f"✅ Added network camera: {camera_name}")
    
    def get_network_camera_frame(self, camera_name):
        """Get frame from network camera"""
        if camera_name not in self.network_cameras:
            return None
        
        camera = self.network_cameras[camera_name]
        
        try:
            # Try to get frame from network camera server
            if self.network_server_url:
                # Extract code from camera name if it's network_X format
                if camera_name.startswith('network_'):
                    code = camera_name.replace('network_', '')
                    response = requests.get(f"{self.network_server_url}/api/camera/stream/{code}", 
                                         stream=True, timeout=5)
                    if response.status_code == 200:
                        # Read first frame
                        bytes_data = b''
                        for chunk in response.iter_content(chunk_size=1024):
                            bytes_data += chunk
                            if b'--frame' in bytes_data[-100:]:  # Look for frame boundary
                                break
                        
                        # Parse JPEG frame
                        header = b'Content-Type: image/jpeg\r\n\r\n'
                        header_index = bytes_data.find(header)
                        if header_index != -1:
                            frame_data = bytes_data[header_index + len(header):]
                            frame_array = np.frombuffer(frame_data, np.uint8)
                            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                            if frame is not None:
                                camera['last_frame'] = frame
                                camera['last_update'] = time.time()
                                return frame
        except Exception as e:
            print(f"⚠️ Error getting network camera frame: {e}")
        
        return None
    
    def initialize_camera(self, camera_index=0):
        """Initialize camera with multiple backend attempts"""
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        
        for backend in backends:
            try:
                print(f"📷 Trying camera {camera_index} with backend {backend}...")
                cap = cv2.VideoCapture(camera_index, backend)
                
                if not cap.isOpened():
                    cap.release()
                    continue
                
                # Test camera read
                ret, test_frame = cap.read()
                if not ret or test_frame is None:
                    cap.release()
                    continue
                
                # Set camera properties
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                print(f"✅ Camera {camera_index} initialized successfully with backend {backend}")
                return cap
                
            except Exception as e:
                print(f"⚠️ Backend {backend} failed: {e}")
                continue
        
        return None
    
    def get_frame(self):
        """Get frame from current camera source"""
        if self.camera_type == "network" and self.current_camera_index < len(self.available_network_cameras):
            camera_name = self.available_network_cameras[self.current_camera_index]
            return self.get_network_camera_frame(camera_name)
        else:
            # Local camera
            if hasattr(self, 'cap') and self.cap:
                ret, frame = self.cap.read()
                if ret:
                    return frame
        return None
    
    def switch_camera(self, direction=1):
        """Switch to next/previous camera"""
        total_cameras = len(self.camera_sources)
        if total_cameras == 0:
            return
        
        self.current_camera_index = (self.current_camera_index + direction) % total_cameras
        camera_type, camera_name = self.camera_sources[self.current_camera_index]
        self.camera_type = camera_type
        
        print(f"📷 Switched to camera {self.current_camera_index}: {camera_name} ({camera_type})")
    
    def detect_faces(self, frame):
        """Detect faces in frame"""
        if self.face_cascade is None:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), maxSize=(300, 300)
            )
            return faces
        except Exception as e:
            print(f"⚠️ Face detection error: {e}")
            return []
    
    def recognize_faces(self, frame, faces):
        """Recognize faces using template matching"""
        recognized = []
        
        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray_face = cv2.resize(gray_face, (100, 100))
            
            face_id = f"person_{len(recognized) + 1}"
            confidence = 0.5
            is_known = False
            
            if self.known_faces and self.face_cascade is not None:
                best_match = None
                best_confidence = 0
                
                for person_name, person_data in self.known_faces.items():
                    if 'images' in person_data and person_data['images']:
                        person_confidence = 0
                        
                        for known_face in person_data['images']:
                            result = cv2.matchTemplate(gray_face, known_face, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(result)
                            person_confidence = max(person_confidence, max_val)
                        
                        if person_confidence > best_confidence:
                            best_confidence = person_confidence
                            best_match = person_name
                
                if best_match and best_confidence > 0.3:
                    face_id = best_match
                    confidence = best_confidence
                    is_known = True
            
            recognized.append({
                'id': face_id,
                'box': (x, y, w, h),
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'is_known': is_known
            })
        
        return recognized
    
    def process_voice_alerts(self, recognized):
        """Process recognized faces and trigger voice alerts for both known and unknown faces"""
        current_time = time.time()
        
        # 1. Handle Unknown Faces (High Priority)
        unknown_faces_detected = any(not face_data.get('is_known', False) for face_data in recognized)
        
        if unknown_faces_detected:
            if not self.unknown_face_present:
                self.unknown_face_present = True
                self.last_unknown_detection_time = current_time
                self.speak_alert("Unknown face detected")
                print("🔊 Voice alert: Unknown face detected (first time)")
            else:
                if (current_time - self.last_unknown_alert_time) > self.unknown_alert_cooldown:
                    self.speak_alert("Unknown face detected")
                    self.last_unknown_alert_time = current_time
            self.last_unknown_detection_time = current_time
        else:
            if self.unknown_face_present:
                self.unknown_face_present = False
            self.last_unknown_alert_time = 0

        # 2. Handle Known Faces (Say their names)
        for face_data in recognized:
            if face_data.get('is_known', False):
                face_id = face_data['id']
                # Check cooldown for this specific person
                last_announced = self.last_face_announcement_time.get(face_id, 0)
                if (current_time - last_announced) > self.face_announcement_cooldown:
                    self.speak_alert(f"Welcome {face_id}")
                    self.last_face_announcement_time[face_id] = current_time
                    print(f"🔊 Voice alert: Identified {face_id}")
    
    def speak_alert(self, message):
        """Speak alert message"""
        if self.tts_available and self.tts_engine:
            try:
                tts_thread = threading.Thread(target=self._speak_worker, args=(message,))
                tts_thread.daemon = True
                tts_thread.start()
            except Exception as e:
                print(f"⚠️ TTS Error: {e}")
    
    def _speak_worker(self, message):
        """Worker thread for text-to-speech"""
        try:
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"⚠️ TTS Worker Error: {e}")
    
    def run_enhanced_cctv_system(self):
        """Run the enhanced CCTV system with network camera support"""
        # Scan for network cameras first
        self.scan_network_cameras()
        
        # Add local cameras
        for i in range(3):
            cap = self.initialize_camera(i)
            if cap:
                self.camera_sources.append(('local', f'Camera {i}'))
                if not hasattr(self, 'cap'):
                    self.cap = cap
                break
        
        print(f"📹 Available cameras: {[f'{name} ({typ})' for typ, name in self.camera_sources]}")
        
        self.running = True
        frame_count = 0
        consecutive_failures = 0
        max_failures = 10
        
        print("✅ Enhanced CCTV System Started")
        print("Controls:")
        print("  'q' - Quit")
        print("  'c' - Switch camera")
        print("  'd' - Toggle detection")
        print("  'r' - Toggle recording")
        print("  's' - Save frame")
        print("  'n' - Scan network cameras")
        print("=" * 50)
        
        while self.running:
            try:
                frame = self.get_frame()
                if frame is None:
                    consecutive_failures += 1
                    print(f"⚠️ Warning: Failed to get frame (attempt {consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        print("❌ Too many consecutive failures. Trying to reinitialize...")
                        # Try to reinitialize camera
                        if self.camera_type == "local":
                            self.cap = self.initialize_camera(0)
                        consecutive_failures = 0
                    
                    time.sleep(0.1)
                    continue
                else:
                    consecutive_failures = 0
                
                frame_count += 1
                
                # Process frame
                if self.detection_active:
                    faces = self.detect_faces(frame)
                    recognized = self.recognize_faces(frame, faces)
                    self.process_voice_alerts(recognized)
                    
                    # Draw detections
                    for face_data in recognized:
                        x, y, w, h = face_data['box']
                        face_id = face_data['id']
                        is_known = face_data['is_known']
                        
                        color = (0, 255, 0) if is_known else (0, 0, 255)
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                        
                        label = f"✓ {face_id}" if is_known else f"? {face_id}"
                        cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Add camera info overlay
                camera_info = f"Camera: {self.current_camera_index + 1}/{len(self.camera_sources)} ({self.camera_type})"
                cv2.putText(frame, camera_info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Display result
                cv2.imshow('Enhanced CCTV Detection', frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("🛑 Stopping CCTV system...")
                    self.running = False
                    break
                elif key == ord('c'):
                    self.switch_camera(1)
                elif key == ord('d'):
                    self.detection_active = not self.detection_active
                    status = "activated" if self.detection_active else "deactivated"
                    print(f"🔍 Face detection {status}")
                elif key == ord('r'):
                    self.recording = not self.recording
                    status = "started" if self.recording else "stopped"
                    print(f"📹 Recording {status}")
                elif key == ord('s'):
                    filename = f"enhanced_cctv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path.join(self.output_dir, filename)
                    cv2.imwrite(filepath, frame)
                    print(f"💾 Frame saved: {filepath}")
                elif key == ord('n'):
                    self.scan_network_cameras()
                
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                print("🛑 User interrupted - stopping system gracefully...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(0.1)
                continue
        
        # Cleanup
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        print("✅ Enhanced CCTV system stopped")

if __name__ == "__main__":
    detector = EnhancedCCTVDetector()
    detector.run_enhanced_cctv_system()
