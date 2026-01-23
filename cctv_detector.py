import cv2
import numpy as np
import time
import threading
import os
from datetime import datetime
import json
from PIL import Image, ImageDraw, ImageFont
import subprocess
import platform
from face_data_manager import FaceDataManager

class CCTVDetector:
    def __init__(self):
        self.running = False
        self.detection_active = True
        self.recording = False
        self.face_cascade = None
        self.known_faces = {}
        self.face_encodings = {}
        self.detection_log = []
        self.alert_threshold = 3  # Alert after 3 detections
        self.alert_cooldown = 30  # 30 seconds between alerts
        self.last_alert_time = {}
        
        # Video settings
        self.output_dir = "cctv_recordings"
        self.log_file = "cctv_log.json"
        
        # Initialize shared face data manager
        self.face_manager = FaceDataManager()
        
        # Text-to-speech availability check
        self.tts_available = False
        try:
            import pyttsx3
            self.tts_available = True
            print("✅ Text-to-speech library available")
        except ImportError:
            print("⚠️ Text-to-speech not available. Install with: pip install pyttsx3")
        
        # Text-to-speech engine
        self.tts_engine = None
        self.last_unknown_alert_time = 0
        self.unknown_alert_cooldown = 3  # 3 seconds between repeated alerts
        self.unknown_face_present = False  # Track if unknown face is currently detected
        self.last_unknown_detection_time = 0  # Track when unknown face was last seen
        self.last_face_announcement_time = {} # Track when each face was last announced
        self.face_announcement_cooldown = 20 # seconds between announcing same person
        
        if self.tts_available:
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)  # Speed of speech
                self.tts_engine.setProperty('volume', 0.9)  # Volume level
                print("✅ Text-to-speech engine initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize TTS: {e}")
                self.tts_available = False
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize face detection
        self.load_face_cascade()
        
        # Load known faces from shared manager
        self.load_known_faces()
    
    def load_face_cascade(self):
        """Load OpenCV face cascade classifier"""
        try:
            # Try to load the cascade
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            print("✅ Face cascade loaded successfully")
        except Exception as e:
            print(f"❌ Error loading face cascade: {e}")
            print("Please install OpenCV with face detection support")
            self.face_cascade = None
    
    def load_known_faces(self):
        """Load known faces from shared face manager"""
        try:
            self.known_faces = self.face_manager.get_face_encodings()
            print(f"✅ Loaded {len(self.known_faces)} known faces from shared manager")
        except Exception as e:
            print(f"❌ Error loading known faces: {e}")
            self.known_faces = {}
    
    def speak_alert(self, message):
        """Speak alert message using text-to-speech"""
        if self.tts_available and self.tts_engine:
            try:
                # Run TTS in a separate thread to avoid blocking
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
    
    def save_known_faces(self):
        """Save known faces using shared face manager"""
        return self.face_manager.save_face_data()
    
    def detect_faces(self, frame):
        """Detect faces in frame with better error handling"""
        if self.face_cascade is None:
            return []
        
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with error handling
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                maxSize=(300, 300)
            )
            
            return faces
            
        except KeyboardInterrupt:
            print("⚠️ Face detection interrupted by user")
            return []
        except Exception as e:
            print(f"⚠️ Face detection error: {e}")
            return []
    
    def recognize_faces(self, frame, faces):
        """Recognize faces using template matching with loaded face images"""
        recognized = []
        
        for (x, y, w, h) in faces:
            # Extract face ROI
            face_roi = frame[y:y+h, x:x+w]
            
            # Convert to grayscale for comparison
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            gray_face = cv2.resize(gray_face, (100, 100))
            
            # Default values
            face_id = f"person_{len(recognized) + 1}"
            confidence = 0.5  # Default confidence
            is_known = False
            
            # Try to match with known faces
            if self.known_faces and self.face_cascade is not None:
                best_match = None
                best_confidence = 0
                
                for person_name, person_data in self.known_faces.items():
                    if 'images' in person_data and person_data['images']:
                        # Compare with all stored images for this person
                        person_confidence = 0
                        
                        for known_face in person_data['images']:
                            # Use template matching
                            result = cv2.matchTemplate(gray_face, known_face, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(result)
                            
                            # Take the best match for this person
                            person_confidence = max(person_confidence, max_val)
                        
                        # Take the best match across all people
                        if person_confidence > best_confidence:
                            best_confidence = person_confidence
                            best_match = person_name
                
                # Set threshold for recognition (adjust as needed)
                if best_match and best_confidence > 0.3:  # Lowered threshold for better detection
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
    
    def draw_detections(self, frame, faces, recognized):
        """Draw detection boxes and labels on frame"""
        # Draw recognized faces with appropriate colors and labels
        for face_data in recognized:
            x, y, w, h = face_data['box']
            face_id = face_data['id']
            confidence = face_data['confidence']
            is_known = face_data['is_known']
            
            # Choose color based on whether face is known
            if is_known:
                # Orange for known faces (high visibility)
                color = (0, 255, 0)  # Orange rectangle
                status_text = "KNOWN"
                label_color = (0, 255, 200)  # Bright orange text
                bg_color = (0, 100, 50)  # Dark orange background
            else:
                # Red for unknown faces
                color = (0, 0, 255)  # Red
                status_text = "UNKNOWN"
                label_color = (0, 0, 255)  # Red text
                bg_color = (50, 0, 0)  # Dark red background
            
            # Draw rectangle with appropriate color
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
            
            # Create compact label with name and status
            if is_known:
                label = f"✓ {face_id}"
            else:
                label = f"? {face_id}"
            
            # Get text size for compact label
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
            
            # Draw compact label background with proper color
            label_bg_y = y - label_size[1] - 8  # Smaller padding
            cv2.rectangle(frame, (x, label_bg_y), (x + label_size[0] + 6, y - 2), bg_color, -1)
            
            # Draw label text with proper color
            cv2.putText(frame, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_color, 1)
            
            # Add confidence score below (smaller)
            conf_text = f"{confidence:.2f}"
            cv2.putText(frame, conf_text, (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Add status indicator (smaller)
            cv2.putText(frame, status_text, (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return frame
    
    def add_detection_log(self, recognized):
        """Add detection to log"""
        for face_data in recognized:
            log_entry = {
                'timestamp': face_data['timestamp'],
                'face_id': face_data['id'],
                'confidence': face_data['confidence'],
                'box': face_data['box']
            }
            self.detection_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.detection_log) > 1000:
            self.detection_log = self.detection_log[-1000:]
    
    def check_alerts(self, recognized):
        """Check if any alerts should be triggered"""
        alerts = []
        current_time = time.time()
        
        for face_data in recognized:
            face_id = face_data['id']
            
            # Count recent detections for this face
            recent_detections = [
                log for log in self.detection_log
                if log['face_id'] == face_id and 
                   (current_time - datetime.fromisoformat(log['timestamp']).timestamp()) < 60
            ]
            
            if len(recent_detections) >= self.alert_threshold:
                # Check cooldown
                if face_id not in self.last_alert_time or \
                   (current_time - self.last_alert_time[face_id]) > self.alert_cooldown:
                    
                    alerts.append({
                        'face_id': face_id,
                        'timestamp': datetime.now().isoformat(),
                        'detection_count': len(recent_detections),
                        'message': f"⚠️ ALERT: {face_id} detected {len(recent_detections)} times!"
                    })
                    
                    self.last_alert_time[face_id] = current_time
        
        return alerts
    
    def save_frame(self, frame, timestamp=None):
        """Save frame to recording file"""
        if not self.recording:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = f"cctv_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        
        cv2.imwrite(filepath, frame)
        return filepath
    
    def save_log(self):
        """Save detection log to file"""
        try:
            log_data = {
                'last_updated': datetime.now().isoformat(),
                'total_detections': len(self.detection_log),
                'known_faces': len(self.known_faces),
                'detections': self.detection_log[-100:]  # Last 100 detections
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving log: {e}")
    
    def create_info_panel(self, frame, recognized, alerts):
        """Create information panel for CCTV display"""
        height, width = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Info panel background
        panel_height = 160  # Increased height for unknown face status
        panel = np.zeros((panel_height, width, 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)  # Dark gray
        
        # Add title
        cv2.putText(panel, "CCTV FACE DETECTION SYSTEM", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(panel, f"Time: {timestamp}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add detection status
        status = "🟢 DETECTING" if self.detection_active else "🔴 PAUSED"
        cv2.putText(panel, f"Status: {status}", (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0) if self.detection_active else (0, 0, 255), 2)
        
        # Add recording status
        rec_status = "🔴 RECORDING" if self.recording else "⏸️ NOT RECORDING"
        cv2.putText(panel, f"Recording: {rec_status}", (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0) if self.recording else (0, 0, 255), 2)
        
        # Add unknown face status with color coding
        unknown_faces_detected = any(not face_data.get('is_known', False) for face_data in recognized)
        if unknown_faces_detected:
            unknown_status = "⚠️ UNKNOWN FACE DETECTED"
            unknown_color = (0, 0, 255)  # Red for alert
            # Add blinking effect
            if int(time.time() * 2) % 2 == 0:  # Blink every 0.5 seconds
                unknown_color = (0, 100, 255)  # Brighter red
        else:
            unknown_status = "✅ No Unknown Faces"
            unknown_color = (0, 255, 0)  # Green for safe
        
        cv2.putText(panel, f"Security: {unknown_status}", (10, 125), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, unknown_color, 2)
        
        # Count known and unknown faces
        known_count = sum(1 for face in recognized if face.get('is_known', False))
        unknown_count = len(recognized) - known_count
        
        # Add face counts
        cv2.putText(panel, f"Total Faces: {len(recognized)}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(panel, f"Known: {known_count} | Unknown: {unknown_count}", (10, 175), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if known_count > 0 else (255, 255, 255), 1)
        
        # Add known faces count
        cv2.putText(panel, f"Registered: {len(self.known_faces)}", (10, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add alerts
        if alerts:
            cv2.putText(panel, f"Alerts: {len(alerts)}", (10, 225), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Show latest alert
            latest_alert = alerts[-1]
            alert_text = latest_alert['message'][:50] + "..." if len(latest_alert['message']) > 50 else latest_alert['message']
            cv2.putText(panel, alert_text, (10, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        # Add color legend and controls reminder
        cv2.putText(panel, "Green = Known | Red = Unknown", (width - 250, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add controls reminder
        cv2.putText(panel, "Controls: q=quit d=detect r=record s=save a=add l=load R=refresh", (width - 400, 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Add input status
        cv2.putText(panel, "🔑 Keyboard Active - Press keys in camera window", (width - 350, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # Overlay panel on frame
        overlay[0:panel_height, :] = cv2.addWeighted(overlay[0:panel_height, :], 0.7, panel, 0.3, 0)
        
        return overlay
    
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
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
                
                print(f"✅ Camera {camera_index} initialized successfully with backend {backend}")
                return cap
                
            except Exception as e:
                print(f"⚠️ Backend {backend} failed: {e}")
                continue
        
        return None
    
    def run_cctv_system(self):
        """Run the CCTV face detection system"""
        # Try different camera indices and backends
        cap = None
        camera_indices = [0, 1, 2]
        
        for camera_idx in camera_indices:
            cap = self.initialize_camera(camera_idx)
            if cap is not None:
                break
        
        if cap is None:
            print("❌ No camera found! Please check:")
            print("1. Camera is connected and not in use by other apps")
            print("2. Camera permissions are granted")
            print("3. Camera drivers are installed")
            print("4. Try closing other camera applications (Zoom, Teams, etc.)")
            print("5. Restart your computer if camera was recently used")
            return
        
        print("✅ Camera initialized successfully!")
        print("🎥 CCTV Face Detection System Started")
        print("=" * 50)
        print("Controls:")
        print("  'q' - Quit")
        print("  'd' - Toggle detection on/off")
        print("  'r' - Toggle recording on/off")
        print("  's' - Save current frame")
        print("  'a' - Add current face to known faces")
        print("  'l' - Load known faces")
        print("  'R' - Refresh known faces from disk")
        print("=" * 50)
        
        self.running = True
        frame_count = 0
        consecutive_failures = 0
        max_failures = 10
        
        print("✅ System ready! Use keyboard controls in the camera window.")
        print("🔑 Make sure the camera window is active, then press keys.")
        
        while self.running:
            try:
                # Check if we should stop before trying to read frame
                if not self.running:
                    print("🛑 CCTV: Early exit - running flag is False")
                    break
                    
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    print(f"⚠️ Warning: Failed to read frame (attempt {consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        print("❌ Too many consecutive frame failures. Attempting camera reinitialization...")
                        cap.release()
                        
                        # Try to reinitialize camera
                        for camera_idx in camera_indices:
                            cap = self.initialize_camera(camera_idx)
                            if cap is not None:
                                print("✅ Camera reinitialized successfully")
                                consecutive_failures = 0
                                break
                        
                        if cap is None:
                            print("❌ Failed to reinitialize camera. Stopping system.")
                            break
                    
                    time.sleep(0.1)
                    continue
                else:
                    consecutive_failures = 0  # Reset failure counter on successful read
                
                # Check running flag again after getting frame
                if not self.running:
                    print("🛑 CCTV: Early exit after frame read - running flag is False")
                    break
                
                frame_count += 1
                
                # Check running flag before processing
                if not self.running:
                    print("🛑 CCTV: Early exit before processing - running flag is False")
                    break
                
                # Process frame
                if self.detection_active:
                    try:
                        # Detect faces
                        faces = self.detect_faces(frame)
                        
                        # Check running flag during processing
                        if not self.running:
                            print("🛑 CCTV: Early exit during face detection - running flag is False")
                            break
                        
                        # Recognize faces
                        recognized = self.recognize_faces(frame, faces)
                        
                        # Check running flag after recognition
                        if not self.running:
                            print("🛑 CCTV: Early exit after recognition - running flag is False")
                            break
                        
                        # Add to log
                        self.add_detection_log(recognized)
                        
                        # Check for alerts
                        alerts = self.check_alerts(recognized)
                        
                        # Process voice alerts for all detected faces
                        self.process_voice_alerts(recognized)
                        
                        # Check running flag before drawing
                        if not self.running:
                            print("🛑 CCTV: Early exit before drawing - running flag is False")
                            break
                        
                        # Draw detections
                        frame = self.draw_detections(frame, faces, recognized)
                        
                        # Save frame if recording
                        if self.recording and frame_count % 30 == 0:  # Save every 30 frames
                            self.save_frame(frame)
                    except KeyboardInterrupt:
                        print("⚠️ Detection interrupted - continuing...")
                        continue
                    except Exception as e:
                        print(f"⚠️ Detection error: {e}")
                        # Continue with original frame
                        pass
                else:
                    # Show paused status
                    cv2.putText(frame, "DETECTION PAUSED", (10, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                
                # Check running flag before adding info panel
                if not self.running:
                    print("🛑 CCTV: Early exit before info panel - running flag is False")
                    break
                
                # Add info panel
                frame = self.create_info_panel(frame, recognized, alerts)
                
                # Add frame counter
                cv2.putText(frame, f"Frame: {frame_count}", (10, frame.shape[0] - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Check running flag before display
                if not self.running:
                    print("🛑 CCTV: Early exit before display - running flag is False")
                    break
                
                # Display result
                cv2.imshow('CCTV Face Detection', frame)
                
                # Handle keyboard input with better debugging
                key = cv2.waitKey(1) & 0xFF
                
                # Check running flag before processing key input
                if not self.running:
                    print("🛑 CCTV: Early exit before key processing - running flag is False")
                    break
                
                # Debug: Show key pressed (if any)
                if key != 255:  # 255 means no key pressed
                    key_char = chr(key) if 32 <= key <= 126 else f"[{key}]"
                    print(f"🔑 Key pressed: {key_char} (code: {key})")
                
                if key == ord('q'):
                    print("🛑 Stopping CCTV system...")
                    self.running = False
                    break
                elif key == ord('d'):
                    self.detection_active = not self.detection_active
                    status = "activated" if self.detection_active else "deactivated"
                    print(f"🔍 Face detection {status}")
                elif key == ord('r'):
                    self.recording = not self.recording
                    status = "started" if self.recording else "stopped"
                    print(f"📹 Recording {status}")
                elif key == ord('s'):
                    filepath = self.save_frame(frame)
                    print(f"💾 Frame saved: {filepath}")
                elif key == ord('a'):
                    self.add_current_face_to_known(frame, recognized)
                elif key == ord('l'):
                    self.load_known_faces()
                elif key == ord('R'):  # Shift+R for refresh
                    self.refresh_known_faces()
                elif key == 27:  # ESC key
                    print("🛑 ESC pressed - Stopping CCTV system...")
                    self.running = False
                    break
                    
                # Small sleep to prevent CPU overload and allow other threads
                time.sleep(0.01)  # Reduced from 0.1 to 0.01 for better responsiveness
                    
            except KeyboardInterrupt:
                print("🛑 User interrupted - stopping system gracefully...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("🔄 Continuing...")
                time.sleep(0.1)
                continue
        
        # Cleanup
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        
        # Save final log
        self.save_log()
        
        print("✅ CCTV system stopped")
        print(f"📊 Total frames processed: {frame_count}")
        print(f"📁 Recordings saved: {len(os.listdir(self.output_dir))}")
        print(f"📋 Detection log saved to: {self.log_file}")
    
    def add_current_face_to_known(self, frame, recognized):
        """Add current detected face to known faces using shared manager"""
        if not recognized:
            print("❌ No faces detected to add")
            return
        
        # Get the first detected face
        face_data = recognized[0]
        x, y, w, h = face_data['box']
        
        # Prompt for name
        print(f"\n📷 Face detected at ({x}, {y}) with confidence {face_data['confidence']:.2f}")
        name = input("Enter name for this face (or 'skip'): ").strip()
        
        if name.lower() != 'skip' and name:
            try:
                face_box = [x, y, w, h]
                if self.face_manager.add_user(name, frame, face_box):
                    # Reload known faces to include the new one
                    self.load_known_faces()
                    
                    print(f"✅ Face '{name}' added successfully")
                    print(f"📁 Total images for {name}: {len(self.face_manager.get_all_users().get(name, {}).get('images', []))}")
                else:
                    print(f"❌ Failed to add face '{name}'")
                    
            except Exception as e:
                print(f"❌ Error saving face: {e}")
        else:
            print("⏭️ Skipped adding face")
    
    def refresh_known_faces(self):
        """Refresh known faces from disk"""
        try:
            self.face_manager.refresh_data()
            self.load_known_faces()
            print("✅ Known faces refreshed from disk")
        except Exception as e:
            print(f"❌ Error refreshing known faces: {e}")
    
    def get_detection_summary(self):
        """Get a summary of recent detections"""
        if not self.detection_log:
            return "No detections yet"
        
        recent_detections = self.detection_log[-10:]  # Last 10 detections
        
        summary = "Recent Detections:\n"
        for i, detection in enumerate(recent_detections, 1):
            summary += f"{i}. {detection['face_id']} at {detection['timestamp']}\n"
        
        return summary

if __name__ == "__main__":
    detector = CCTVDetector()
    detector.run_cctv_system()
