import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import shutil
import glob
import cv2
from datetime import datetime
import threading
import time
from PIL import Image, ImageTk
from face_data_manager import FaceDataManager
import pyttsx3
import qrcode
from io import BytesIO
import numpy as np
import sv_ttk
import darkdetect
import warnings

# Suppress OpenCV warnings
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

class FaceManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("👥 Face Management & CCTV System")
        self.root.geometry("1300x900")  # Increased size for better layout
        
        # Apply modern theme
        sv_ttk.set_theme("dark")
        
        # Custom styles for modern look
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Card.TFrame", background="#2b2b2b", relief="flat")
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        
        # Initialize shared face data manager
        self.face_manager = FaceDataManager()
        
        # Load face encodings for recognition
        self.face_encodings = self.face_manager.get_face_encodings()
        
        # Camera variables
        self.camera_active = False
        self.captured_image = None
        self.camera_window = None
        self.camera_cap = None
        self.current_frame = None
        self.capture_status_var = tk.StringVar(value="Camera ready")
        
        # CCTV system variables
        self.cctv_thread = None
        self.cctv_detector = None
        self.cctv_running = False
        
        # Multi-camera display variables
        self.camera_displays = {}
        self.camera_labels = {}
        self.camera_frames = {}
        self.camera_threads = {}
        self.active_cameras = []
        self.current_camera_index = 0
        
        # Image gallery variables
        self.gallery_window = None
        self.gallery_images = []
        self.current_image_index = 0
        
        # Text-to-speech engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
        except Exception as e:
            print(f"⚠️ Text-to-speech not available: {e}")
            self.tts_engine = None
        
        # Network camera server
        self.network_server_thread = None
        self.network_server_running = False
        
        # QR code display
        self.qr_window = None
        self.current_qr_image = None
        
        # Canvas and scrolling references
        self.canvas = None
        self.scrollable_frame = None
        
        # Fullscreen camera window
        self.fullscreen_window = None
        self.fullscreen_camera_id = None
        self.fullscreen_running = False
        
        # Camera access preference
        self.camera_access_mode = tk.StringVar(value="both")  # "both", "local_only", "network_only"
        
        # Create GUI
        self.create_widgets()
        
        # Refresh user list
        self.refresh_user_list()
        
        # Configure minimum window size
        self.root.minsize(1100, 700)
        
        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)
    
    def on_window_resize(self, event):
        """Handle window resize event"""
        # Update canvas scroll region
        if self.canvas and self.scrollable_frame:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def launch_cctv_system(self):
        """Launch enhanced CCTV detection system in a separate thread"""
        if self.cctv_running:
            messagebox.showwarning("Warning", "CCTV system is already running")
            return
        
        try:
            self.cctv_running = True
            self.cctv_status_var.set("CCTV System: Starting...")
            self.status_var.set("Launching enhanced CCTV detection system...")
            
            # Start CCTV in a separate thread
            self.cctv_thread = threading.Thread(target=self.run_cctv_system)
            self.cctv_thread.daemon = True
            self.cctv_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch CCTV system: {str(e)}")
            self.cctv_running = False
            self.cctv_status_var.set("CCTV System: Error")
    
    def run_cctv_system(self):
        """Run enhanced CCTV system with shared face data"""
        try:
            from enhanced_cctv_detector import EnhancedCCTVDetector
            
            # Create enhanced CCTV detector instance
            self.cctv_detector = EnhancedCCTVDetector()
            
            # Replace the face data manager with our shared one
            self.cctv_detector.known_faces = self.face_manager.get_face_encodings()
            
            # Share TTS engine with CCTV system
            if self.tts_engine:
                self.cctv_detector.tts_engine = self.tts_engine
                self.cctv_detector.last_unknown_alert_time = 0
                self.cctv_detector.unknown_alert_cooldown = 3  # 3 seconds for continuous alerts
                self.cctv_detector.unknown_face_present = False
                self.cctv_detector.last_unknown_detection_time = 0
            
            self.cctv_status_var.set("CCTV System: Running")
            self.status_var.set("Enhanced CCTV detection system active")
            
            # Run the enhanced CCTV system
            self.cctv_detector.run_enhanced_cctv_system()
            
        except Exception as e:
            print(f"❌ CCTV System Error: {e}")
            self.cctv_status_var.set("CCTV System: Error")
        finally:
            self.cctv_running = False
            self.cctv_detector = None
            self.cctv_status_var.set("CCTV System: Stopped")
            self.status_var.set("CCTV system stopped")
    
    def stop_cctv_system(self):
        """Stop the CCTV detection system"""
        if not self.cctv_running:
            messagebox.showwarning("Warning", "CCTV system is not running")
            return
        
        try:
            self.cctv_status_var.set("CCTV System: Stopping...")
            self.status_var.set("Stopping CCTV system...")
            
            print("🛑 GUI: Sending stop signal to CCTV system...")
            
            # Set the running flag to False in the detector
            if self.cctv_detector:
                self.cctv_detector.running = False
                print("🛑 GUI: Set detector.running = False")
            
            # Also stop GUI flag
            self.cctv_running = False
            print("🛑 GUI: Set cctv_running = False")
            
            # Wait a moment for the thread to stop
            if self.cctv_thread and self.cctv_thread.is_alive():
                print("🛑 GUI: Waiting for thread to stop...")
                self.cctv_thread.join(timeout=3.0)
                
                if self.cctv_thread.is_alive():
                    print("⚠️ GUI: Thread still alive after timeout")
                else:
                    print("✅ GUI: Thread stopped successfully")
            
            # Force close OpenCV windows
            try:
                import cv2
                cv2.destroyAllWindows()
                print("✅ GUI: Closed OpenCV windows")
            except Exception as e:
                print(f"⚠️ GUI: Error closing windows: {e}")
            
            # Clear detector reference
            self.cctv_detector = None
            self.cctv_thread = None
            
            self.cctv_status_var.set("CCTV System: Stopped")
            self.status_var.set("CCTV system stopped")
            print("✅ GUI: CCTV system stop completed")
            
        except Exception as e:
            print(f"❌ GUI: Error stopping CCTV system: {e}")
            messagebox.showerror("Error", f"Failed to stop CCTV system: {str(e)}")
            # Force cleanup on error
            self.cctv_running = False
            self.cctv_detector = None
            self.cctv_thread = None
            self.cctv_status_var.set("CCTV System: Error")
            self.status_var.set("Error stopping CCTV")
    
    def start_network_server(self):
        """Start the network camera server"""
        if self.network_server_running:
            messagebox.showwarning("Warning", "Network server is already running")
            return
        
        try:
            self.network_server_running = True
            self.network_status_var.set("Network Server: Starting...")
            self.status_var.set("Starting network camera server...")
            
            # Start server in separate thread
            self.network_server_thread = threading.Thread(target=self.run_network_server)
            self.network_server_thread.daemon = True
            self.network_server_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start network server: {str(e)}")
            self.network_server_running = False
            self.network_status_var.set("Network Server: Error")
    
    def run_network_server(self):
        """Run the network camera server"""
        try:
            from network_camera_server import NetworkCameraServer
            
            server = NetworkCameraServer()
            self.network_status_var.set("Network Server: Running")
            self.status_var.set("Network camera server active")
            
            # Run the server
            server.run(host='0.0.0.0', port=5000)
            
        except Exception as e:
            print(f"❌ Network Server Error: {e}")
            self.network_status_var.set("Network Server: Error")
        finally:
            self.network_server_running = False
            self.network_status_var.set("Network Server: Stopped")
            self.status_var.set("Network camera server stopped")
    
    def generate_access_code(self):
        """Generate access code for mobile camera connection"""
        if not self.network_server_running:
            messagebox.showwarning("Warning", "Please start the network server first")
            return
        
        try:
            import requests
            
            # Generate access code from server
            response = requests.get("http://localhost:5000/generate_code", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Show access code information
                message = f"""
✅ Access Code Generated!

📱 Code: {data['code']}
🌐 Connection URL: {data['connection_url']}
⏰ Expires: {datetime.fromisoformat(data['expiry_time']).strftime('%Y-%m-%d %H:%M:%S')}

📋 Instructions:
1. Open the connection URL on your mobile device
2. Allow camera permissions when prompted
3. Click "Start Camera" to begin streaming
4. The mobile camera will appear in the CCTV system

📁 QR Code saved to: {data['qr_path']}
"""
                messagebox.showinfo("Access Code Generated", message)
                self.status_var.set(f"Access code {data['code']} generated")
                
                # Display QR code
                self.display_qr_code(data['code'], data['qr_path'])
            else:
                messagebox.showerror("Error", "Failed to generate access code")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate access code: {str(e)}")
    
    def scan_network_cameras(self):
        """Scan for available network cameras"""
        if not self.network_server_running:
            messagebox.showwarning("Warning", "Please start the network server first")
            return
        
        try:
            import requests
            
            # Get server status
            response = requests.get("http://localhost:5000/api/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                message = f"""
📡 Network Camera Status

🌐 Server IP: {data['server_ip']}
📹 Active Cameras: {data['active_cameras']}
🔗 Valid Connections: {data['valid_connections']}
⏰ Server Time: {datetime.fromisoformat(data['server_time']).strftime('%Y-%m-%d %H:%M:%S')}

{'✅ Cameras are connected and streaming!' if data['active_cameras'] > 0 else '⚠️ No cameras currently connected'}
"""
                messagebox.showinfo("Network Camera Status", message)
                self.status_var.set(f"Found {data['active_cameras']} network cameras")
            else:
                messagebox.showerror("Error", "Failed to scan network cameras")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan network cameras: {str(e)}")
    
    def display_qr_code(self, code, qr_path):
        """Display QR code in a new modern window"""
        try:
            if self.qr_window:
                self.qr_window.destroy()
            
            self.qr_window = tk.Toplevel(self.root)
            self.qr_window.title(f"📱 Mobile Camera Connection")
            self.qr_window.geometry("500x650")
            self.qr_window.configure(bg='#1c1c1c')
            
            # Title
            ttk.Label(self.qr_window, text="Mobile Connection", font=("Segoe UI", 18, "bold")).pack(pady=20)
            
            # Access code display
            code_card = ttk.Frame(self.qr_window, padding=20)
            code_card.pack(fill=tk.X, padx=30, pady=10)
            
            ttk.Label(code_card, text="ACCESS CODE", font=("Segoe UI", 10, "bold"), foreground="gray").pack()
            ttk.Label(code_card, text=code, font=("Segoe UI", 28, "bold"), foreground="#0078d4").pack(pady=10)
            
            # QR Code display
            qr_frame = ttk.Frame(self.qr_window, padding=10)
            qr_frame.pack(pady=10)
            
            if os.path.exists(qr_path):
                qr_image = Image.open(qr_path)
                qr_image = qr_image.resize((250, 250), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(qr_image)
                
                qr_label = tk.Label(qr_frame, image=photo, bg='#1c1c1c')
                qr_label.image = photo
                qr_label.pack()
                self.current_qr_image = photo
            
            # URL Display
            url_text = f"http://localhost:5000/connect/{code}"
            url_entry = ttk.Entry(self.qr_window, font=("Segoe UI", 9))
            url_entry.insert(0, url_text)
            url_entry.configure(state='readonly')
            url_entry.pack(fill=tk.X, padx=50, pady=(20, 5))
            
            ttk.Button(self.qr_window, text="📋 Copy Connection URL", 
                       command=lambda: self.copy_to_clipboard(url_text),
                       style="Accent.TButton").pack(pady=10)
            
            ttk.Button(self.qr_window, text="Close", 
                       command=self.close_qr_window).pack(pady=20)
            
            self.qr_window.transient(self.root)
            self.qr_window.grab_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display QR code: {str(e)}")
            
            # Center window
            self.qr_window.transient(self.root)
            self.qr_window.grab_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display QR code: {str(e)}")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Success", "URL copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy URL: {str(e)}")
    
    def close_qr_window(self):
        """Close QR code window"""
        if self.qr_window:
            self.qr_window.destroy()
            self.qr_window = None
            self.current_qr_image = None
    
    def launch_multi_camera_cctv(self):
        """Launch multi-camera CCTV system integrated in GUI"""
        if self.cctv_running:
            messagebox.showwarning("Warning", "CCTV system is already running")
            return
        
        try:
            # Initialize camera displays first
            self.initialize_camera_displays()
            
            # Show camera access preference dialog
            self.show_camera_access_dialog()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize camera displays: {str(e)}")
    
    def start_cctv_system(self):
        """Actually start the CCTV system after preference selection"""
        try:
            print("🚀 Starting CCTV system with preference:", self.camera_access_mode.get())
            
            self.cctv_running = True
            self.cctv_status_var.set("CCTV System: Starting...")
            self.status_var.set("Launching multi-camera CCTV system...")
            
            # Update camera displays based on preference
            mode = self.camera_access_mode.get()
            self.update_camera_displays_for_mode(mode)
            
            # Start camera threads
            self.start_camera_threads()
            
            # Start face detection thread
            self.cctv_thread = threading.Thread(target=self.run_multi_camera_cctv)
            self.cctv_thread.daemon = True
            self.cctv_thread.start()
            
            print("✅ CCTV system started successfully")
            
        except Exception as e:
            print(f"❌ Error starting CCTV system: {e}")
            messagebox.showerror("Error", f"Failed to launch multi-camera CCTV: {str(e)}")
            self.cctv_running = False
            self.cctv_status_var.set("CCTV System: Error")
    
    def initialize_camera_displays(self):
        """Initialize camera display grid with sleek borders"""
        # Clear existing displays
        for widget in self.camera_grid.winfo_children():
            widget.destroy()
        
        # Create 2x2 grid for camera displays
        self.camera_displays = {}
        self.camera_labels = {}
        
        # Grid layout
        for i in range(2):
            # Local cameras
            frame_l = ttk.Frame(self.camera_grid, style="Card.TFrame", padding=2)
            frame_l.grid(row=i, column=0, padx=5, pady=5, sticky='nsew')
            
            label_l = tk.Label(frame_l, text=f"Local Cam {i+1}\nOffline", 
                             bg='#1a1a1a', fg='#555555', font=('Segoe UI', 10, 'bold'),
                             cursor='hand2')
            label_l.pack(fill=tk.BOTH, expand=True)
            
            # Add click handler for fullscreen
            label_l.bind('<Button-1>', lambda e, cid=f'local_{i}': self.open_fullscreen_camera(cid))
            
            self.camera_displays[f'local_{i}'] = frame_l
            self.camera_labels[f'local_{i}'] = label_l
            
            # Network cameras
            frame_n = ttk.Frame(self.camera_grid, style="Card.TFrame", padding=2)
            frame_n.grid(row=i, column=1, padx=5, pady=5, sticky='nsew')
            
            label_n = tk.Label(frame_n, text=f"Network Cam {i+1}\nOffline", 
                             bg='#1a1a1a', fg='#555555', font=('Segoe UI', 10, 'bold'),
                             cursor='hand2')
            label_n.pack(fill=tk.BOTH, expand=True)
            
            # Add click handler for fullscreen
            label_n.bind('<Button-1>', lambda e, cid=f'network_{i}': self.open_fullscreen_camera(cid))
            
            self.camera_displays[f'network_{i}'] = frame_n
            self.camera_labels[f'network_{i}'] = label_n
        
        # Configure grid weights for equal distribution
        self.camera_grid.grid_rowconfigure(0, weight=1)
        self.camera_grid.grid_rowconfigure(1, weight=1)
        self.camera_grid.grid_columnconfigure(0, weight=1)
        self.camera_grid.grid_columnconfigure(1, weight=1)
        
        self.active_cameras = ['local_0', 'local_1', 'network_0', 'network_1']
        self.update_camera_info()
        
        self.active_cameras = ['local_0', 'local_1', 'network_0', 'network_1']
        self.update_camera_info()
    
    def start_camera_threads(self):
        """Start threads for each camera"""
        self.camera_threads = {}
        
        # Start local camera threads
        for i in range(2):
            camera_id = f'local_{i}'
            thread = threading.Thread(target=self.camera_worker, args=(camera_id, i))
            thread.daemon = True
            thread.start()
            self.camera_threads[camera_id] = thread
        
        # Start network camera threads
        for i in range(2):
            camera_id = f'network_{i}'
            thread = threading.Thread(target=self.network_camera_worker, args=(camera_id, i))
            thread.daemon = True
            thread.start()
            self.camera_threads[camera_id] = thread
    
    def camera_worker(self, camera_id, camera_index):
        """Worker thread for local camera with improved error handling"""
        cap = None
        try:
            # Check if local cameras are allowed
            mode = self.camera_access_mode.get()
            if mode == "network_only":
                print(f"⚠️ Local cameras disabled - mode: {mode}")
                self.update_camera_display(camera_id, f"Camera {camera_index + 1}\nDisabled", None)
                return
            
            # Use the improved camera initialization
            cap = self.initialize_camera(camera_index)
            if cap is None:
                self.update_camera_display(camera_id, f"Camera {camera_index + 1}\nNot Available", None)
                print(f"⚠️ Camera {camera_index} not available")
                return
            
            print(f"✅ Camera {camera_index} initialized successfully")
            
            consecutive_failures = 0
            max_failures = 10
            
            while self.cctv_running:
                # Check if mode changed during operation
                current_mode = self.camera_access_mode.get()
                if current_mode == "network_only":
                    print(f"⚠️ Local cameras disabled during operation")
                    break
                
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print(f"❌ Camera {camera_index} too many failures, reinitializing...")
                        cap.release()
                        
                        # Try to reinitialize camera
                        cap = self.initialize_camera(camera_index)
                        if cap is not None:
                            consecutive_failures = 0
                            print(f"✅ Camera {camera_index} reinitialized successfully")
                        else:
                            print(f"❌ Failed to reinitialize camera {camera_index}")
                            break
                    
                    self.update_camera_display(camera_id, f"Camera {camera_index + 1}\nNo Signal", None)
                    time.sleep(0.1)
                    continue
                else:
                    consecutive_failures = 0  # Reset failure counter on successful read
                
                # Process frame for face detection
                processed_frame = self.process_camera_frame(frame, camera_id)
                
                # Update display
                self.update_camera_display(camera_id, f"Camera {camera_index + 1}", processed_frame)
                
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            print(f"Camera {camera_id} error: {e}")
            self.update_camera_display(camera_id, f"Camera {camera_index + 1}\nError", None)
        finally:
            if cap:
                cap.release()
                print(f"🔌 Camera {camera_id} released")
    
    def network_camera_worker(self, camera_id, camera_index):
        """Worker thread for network camera with detailed debugging"""
        try:
            # Check if network cameras are allowed
            mode = self.camera_access_mode.get()
            if mode == "local_only":
                print(f"⚠️ Network cameras disabled - mode: {mode}")
                self.update_camera_display(camera_id, f"Network {camera_index + 1}\nDisabled", None)
                return
            
            consecutive_failures = 0
            max_failures = 10
            
            print(f"🔄 Starting network camera worker for {camera_id} (index {camera_index})")
            
            while self.cctv_running:
                # Check if mode changed during operation
                current_mode = self.camera_access_mode.get()
                if current_mode == "local_only":
                    print(f"⚠️ Network cameras disabled during operation")
                    break
                
                # Try to get network camera frame
                frame = self.get_network_camera_frame(camera_index)
                
                if frame is not None:
                    print(f"✅ Got frame from network camera {camera_index}, shape: {frame.shape}")
                    
                    # Process frame for face detection
                    processed_frame = self.process_camera_frame(frame, camera_id)
                    
                    # Update display
                    self.update_camera_display(camera_id, f"Network {camera_index + 1}", processed_frame)
                    consecutive_failures = 0  # Reset failure counter
                else:
                    consecutive_failures += 1
                    if consecutive_failures <= 3:  # Only show first few errors
                        print(f"⚠️ Network camera {camera_index} no frame (attempt {consecutive_failures})")
                        self.update_camera_display(camera_id, f"Network {camera_index + 1}\nNo Signal", None)
                    elif consecutive_failures == 4:
                        print(f"🔄 Network camera {camera_index} connecting...")
                        self.update_camera_display(camera_id, f"Network {camera_index + 1}\nConnecting...", None)
                    elif consecutive_failures == max_failures:
                        print(f"❌ Network camera {camera_index} marked as offline after {max_failures} failures")
                        self.update_camera_display(camera_id, f"Network {camera_index + 1}\nOffline", None)
                
                time.sleep(0.1)  # Check every 100ms
                
        except Exception as e:
            print(f"❌ Network camera {camera_id} error: {e}")
            self.update_camera_display(camera_id, f"Network {camera_index + 1}\nError", None)
    
    def get_network_camera_frame(self, camera_index):
        """Get frame from network camera server with proper camera mapping"""
        try:
            import requests
            
            # Check if network server is running
            if not self.network_server_running:
                return None
            
            # First, get a list of active cameras from the server
            try:
                status_response = requests.get(f"http://localhost:5000/api/status", timeout=2)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    active_cameras = status_data.get('active_cameras', 0)
                    
                    if active_cameras == 0:
                        # No cameras connected, don't try to stream
                        return None
                else:
                    return None
            except Exception as e:
                # Server might not be responding
                return None
            
            # Get the list of all active cameras and their actual codes
            try:
                # Get all available camera codes from the server
                cameras_response = requests.get(f"http://localhost:5000/api/cameras", timeout=2)
                if cameras_response.status_code == 200:
                    cameras_data = cameras_response.json()
                    available_cameras = cameras_data.get('cameras', [])
                    
                    # Debug logging
                    if camera_index == 0:  # Only log for first camera to reduce spam
                        print(f"📡 Available network cameras: {available_cameras}")
                    
                    # Map camera_index to actual camera code
                    if camera_index < len(available_cameras):
                        actual_camera_code = available_cameras[camera_index]
                        
                        if camera_index == 0:  # Only log for first camera
                            print(f"📷 Mapping network camera {camera_index} to code: {actual_camera_code}")
                        
                        # Try to get the actual frame using the correct camera code
                        frame_response = requests.get(f"http://localhost:5000/api/camera/latest/{actual_camera_code}", timeout=2)
                        if frame_response.status_code == 200:
                            frame_data = frame_response.json()
                            if 'frame' in frame_data:
                                # Decode the frame
                                import base64
                                frame_bytes = base64.b64decode(frame_data['frame'])
                                if len(frame_bytes) > 0:
                                    frame_array = np.frombuffer(frame_bytes, np.uint8)
                                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                                    if frame is not None and frame.size > 0:
                                        if camera_index == 0:  # Only log for first camera
                                            print(f"✅ Successfully retrieved frame from network camera {camera_index}")
                                        return frame
                                    else:
                                        if camera_index == 0:
                                            print(f"❌ Failed to decode frame from network camera {camera_index}")
                                else:
                                    if camera_index == 0:
                                        print(f"❌ Empty frame bytes from network camera {camera_index}")
                            else:
                                if camera_index == 0:
                                    print(f"❌ No frame in response from network camera {camera_index}")
                        else:
                            if camera_index == 0:
                                print(f"❌ Failed to get frame from network camera {camera_index}: {frame_response.status_code}")
                    else:
                        # No camera available at this index
                        if camera_index == 0:
                            print(f"⚠️ No network camera available at index {camera_index}")
                        return None
                else:
                    if camera_index == 0:
                        print(f"❌ Failed to get camera list: {cameras_response.status_code}")
                    return None
            
            except Exception as e:
                # Network camera not available or error occurred
                pass
            
            return None
                
        except Exception as e:
            # Don't print every error to avoid spam
            if camera_index == 0:  # Only print for first camera to reduce spam
                print(f"⚠️ Network camera error: {e}")
        
        return None
    
    def recognize_face(self, face_roi, camera_id):
        """Recognize face using simple template matching"""
        try:
            if not hasattr(self, 'face_encodings') or not self.face_encodings:
                return None
            
            # Resize face ROI to standard size
            face_roi = cv2.resize(face_roi, (100, 100))
            
            best_match = None
            best_score = float('inf')
            
            # Compare with known faces
            for user_name, user_data in self.face_encodings.items():
                if 'images' in user_data and user_data['images']:
                    for known_face in user_data['images']:
                        # Simple template matching
                        try:
                            # Ensure both images are same size and type
                            if known_face.shape == face_roi.shape:
                                # Calculate similarity using correlation
                                correlation = cv2.matchTemplate(face_roi, known_face, cv2.TM_CCOEFF_NORMED)
                                score = 1 - correlation[0][0]  # Convert to distance
                                
                                if score < best_score and score < 0.5:  # Threshold for recognition
                                    best_score = score
                                    best_match = user_name
                        except:
                            continue
            
            return best_match
            
        except Exception as e:
            print(f"Face recognition error: {e}")
            return None
    
    def handle_unknown_face_alert(self, camera_id, unknown_present):
        """Handle TTS alerts for unknown faces with improved logic"""
        try:
            # Initialize tracking variables if not present
            if not hasattr(self, 'unknown_face_tracking'):
                self.unknown_face_tracking = {}
            
            if camera_id not in self.unknown_face_tracking:
                self.unknown_face_tracking[camera_id] = {
                    'alerting': False,
                    'last_alert_time': 0,
                    'alert_cooldown': 5,  # Increased to 5 seconds
                    'consecutive_detections': 0,
                    'last_unknown_time': 0
                }
            
            tracking = self.unknown_face_tracking[camera_id]
            current_time = time.time()
            
            if unknown_present:
                # Unknown face detected
                tracking['consecutive_detections'] += 1
                tracking['last_unknown_time'] = current_time
                
                # Only alert if we have consecutive detections and cooldown has passed
                if (tracking['consecutive_detections'] >= 3 and 
                    not tracking['alerting'] and 
                    (current_time - tracking['last_alert_time'] > tracking['alert_cooldown'])):
                    
                    # Start alerting
                    tracking['alerting'] = True
                    tracking['last_alert_time'] = current_time
                    
                    # Trigger TTS alert
                    if self.tts_engine:
                        threading.Thread(target=self.speak_unknown_alert, args=(camera_id,), daemon=True).start()
                        print(f"🚨 Unknown face detected on {camera_id} (after {tracking['consecutive_detections']} consecutive detections)")
            else:
                # No unknown face detected
                tracking['consecutive_detections'] = 0
                
                # Only stop alerting if it's been more than 2 seconds since last unknown detection
                if tracking['alerting'] and (current_time - tracking['last_unknown_time'] > 2):
                    tracking['alerting'] = False
                    print(f"✅ Unknown face no longer detected on {camera_id}")
                    
        except Exception as e:
            print(f"Unknown face alert error: {e}")
    
    def speak_unknown_alert(self, camera_id):
        """Speak alert for unknown face"""
        try:
            if self.tts_engine:
                message = f"Warning: Unknown person detected on camera {camera_id}"
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS alert error: {e}")
    
    def process_camera_frame(self, frame, camera_id):
        """Process frame for face detection with recognition"""
        if frame is None:
            return None
        
        try:
            # Face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            
            # Track unknown faces for TTS alerts
            unknown_faces_present = False
            
            # Draw face rectangles and recognize faces
            for (x, y, w, h) in faces:
                # Try to recognize the face
                recognized_name = self.recognize_face(gray[y:y+h, x:x+w], camera_id)
                
                if recognized_name:
                    # Known face - draw with green and show name
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, recognized_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    # Unknown face - draw with red
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    unknown_faces_present = True
            
            # Handle TTS alerts for unknown faces
            self.handle_unknown_face_alert(camera_id, unknown_faces_present)
            
            # Add camera info
            cv2.putText(frame, camera_id, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            return frame
            
        except Exception as e:
            print(f"Frame processing error: {e}")
            return frame
    
    def update_camera_display(self, camera_id, text, frame):
        """Update camera display in GUI with debugging"""
        try:
            if camera_id in self.camera_labels:
                if frame is not None:
                    # Debug logging for network cameras
                    if 'network' in camera_id:
                        print(f"🖼️ Updating {camera_id} display with frame (shape: {frame.shape})")
                    
                    # Convert frame to PIL Image
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rgb_frame = cv2.resize(rgb_frame, (240, 180))  # Smaller size for fixed layout
                    pil_image = Image.fromarray(rgb_frame)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Update label with image
                    self.camera_labels[camera_id].configure(image=photo, text="")
                    self.camera_labels[camera_id].image = photo
                    
                    if 'network' in camera_id:
                        print(f"✅ {camera_id} display updated successfully")
                else:
                    # Update label with text only
                    if 'network' in camera_id:
                        print(f"📝 Updating {camera_id} display with text: '{text}'")
                    self.camera_labels[camera_id].configure(image="", text=text)
                    
        except Exception as e:
            print(f"❌ Display update error for {camera_id}: {e}")
    
    def open_fullscreen_camera(self, camera_id):
        """Open fullscreen camera view for selected camera"""
        try:
            # Close existing fullscreen window if open
            if self.fullscreen_window:
                self.close_fullscreen_camera()
            
            # Create fullscreen window
            self.fullscreen_window = tk.Toplevel(self.root)
            self.fullscreen_camera_id = camera_id
            self.fullscreen_running = True
            
            # Set window properties
            self.fullscreen_window.title(f"📹 {camera_id.replace('_', ' ').title()} - Fullscreen")
            self.fullscreen_window.geometry("1200x800")
            self.fullscreen_window.configure(bg='#000000')
            
            # Make window fullscreen
            self.fullscreen_window.attributes('-fullscreen', True)
            
            # Create main container
            main_frame = tk.Frame(self.fullscreen_window, bg='#000000')
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Camera display label
            self.fullscreen_label = tk.Label(main_frame, bg='#000000', 
                                           text=f"Loading {camera_id}...", 
                                           fg='white', font=('Segoe UI', 16))
            self.fullscreen_label.pack(fill=tk.BOTH, expand=True)
            
            # Control panel
            control_panel = tk.Frame(self.fullscreen_window, bg='#1a1a1a', height=60)
            control_panel.pack(side=tk.BOTTOM, fill=tk.X)
            control_panel.pack_propagate(False)
            
            # Control buttons
            button_frame = tk.Frame(control_panel, bg='#1a1a1a')
            button_frame.pack(pady=10)
            
            # Exit fullscreen button
            exit_btn = tk.Button(button_frame, text="❌ Exit Fullscreen (ESC)", 
                               command=self.close_fullscreen_camera,
                               bg='#ff4444', fg='white', font=('Segoe UI', 12, 'bold'),
                               padx=20, pady=10)
            exit_btn.pack(side=tk.LEFT, padx=5)
            
            # Camera info
            info_label = tk.Label(button_frame, text=f"Camera: {camera_id}", 
                                bg='#1a1a1a', fg='white', font=('Segoe UI', 12))
            info_label.pack(side=tk.LEFT, padx=20)
            
            # Bind ESC key to exit fullscreen
            self.fullscreen_window.bind('<Escape>', lambda e: self.close_fullscreen_camera())
            
            # Bind window close event
            self.fullscreen_window.protocol("WM_DELETE_WINDOW", self.close_fullscreen_camera)
            
            print(f"🖥️ Opened fullscreen view for {camera_id}")
            
            # Start fullscreen update loop
            self.update_fullscreen_camera()
            
        except Exception as e:
            print(f"❌ Error opening fullscreen camera: {e}")
            if self.fullscreen_window:
                self.fullscreen_window.destroy()
                self.fullscreen_window = None
    
    def close_fullscreen_camera(self):
        """Close fullscreen camera view"""
        try:
            if self.fullscreen_window:
                self.fullscreen_running = False
                self.fullscreen_window.destroy()
                self.fullscreen_window = None
                self.fullscreen_camera_id = None
                print("🖥️ Closed fullscreen camera view")
        except Exception as e:
            print(f"❌ Error closing fullscreen camera: {e}")
    
    def update_fullscreen_camera(self):
        """Update fullscreen camera display"""
        if not self.fullscreen_running or not self.fullscreen_window:
            return
        
        try:
            camera_id = self.fullscreen_camera_id
            
            # Get frame based on camera type
            if camera_id.startswith('local_'):
                # Local camera
                camera_index = int(camera_id.split('_')[1])
                frame = self.get_local_camera_frame_for_fullscreen(camera_index)
            else:
                # Network camera
                camera_index = int(camera_id.split('_')[1])
                frame = self.get_network_camera_frame(camera_index)
            
            if frame is not None:
                # Process frame for face detection
                processed_frame = self.process_camera_frame(frame, camera_id)
                
                # Resize for fullscreen display
                height, width = processed_frame.shape[:2]
                screen_height = self.fullscreen_window.winfo_screenheight()
                screen_width = self.fullscreen_window.winfo_screenwidth()
                
                # Calculate aspect ratio
                aspect_ratio = width / height
                
                # Fit to screen maintaining aspect ratio
                if screen_width / screen_height > aspect_ratio:
                    new_height = screen_height - 100  # Leave space for controls
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = screen_width
                    new_height = int(new_width / aspect_ratio)
                
                resized_frame = cv2.resize(processed_frame, (new_width, new_height))
                
                # Convert to PIL Image
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update display
                self.fullscreen_label.configure(image=photo, text="")
                self.fullscreen_label.image = photo
            else:
                self.fullscreen_label.configure(image="", text=f"No Signal - {camera_id}")
            
        except Exception as e:
            print(f"❌ Error updating fullscreen camera: {e}")
        
        # Schedule next update (30 FPS)
        if self.fullscreen_running:
            self.fullscreen_window.after(33, self.update_fullscreen_camera)
    
    def get_local_camera_frame_for_fullscreen(self, camera_index):
        """Get frame from local camera for fullscreen display"""
        try:
            # This is a simplified version - in production, you'd want to share the camera object
            # For now, we'll create a temporary camera connection
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return frame
        except Exception as e:
            print(f"Error getting local camera frame for fullscreen: {e}")
        
        return None
    
    def show_camera_access_dialog(self):
        """Show dialog to ask user about camera access preference"""
        # Ensure main window is fully updated first
        self.root.update_idletasks()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Camera Access Preference")
        dialog.geometry("550x500")
        dialog.configure(bg='#1c1c1c')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"550x500+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(dialog, bg='#1c1c1c')
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(main_container, text="📹 Camera Access Preference", 
                              bg='#1c1c1c', fg='white', font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = tk.Label(main_container, text="Choose which cameras you want to access:", 
                             bg='#1c1c1c', fg='white', font=("Segoe UI", 12))
        desc_label.pack(anchor=tk.W, pady=(0, 5))
        
        desc2_label = tk.Label(main_container, text="This will determine which camera feeds are available in the CCTV system.", 
                              bg='#1c1c1c', fg='#888888', font=("Segoe UI", 10))
        desc2_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Radio buttons container
        radio_container = tk.LabelFrame(main_container, text="Select Camera Access Mode:", 
                                       bg='#1c1c1c', fg='white', font=("Segoe UI", 11, "bold"),
                                       padx=20, pady=20)
        radio_container.pack(fill=tk.X, pady=(0, 20))
        
        # Radio options
        options = [
            ("📷 Both Local and Network Cameras", "both", "Access cameras connected to this PC and linked mobile cameras"),
            ("💻 Local Cameras Only", "local_only", "Only access cameras connected to this computer"),
            ("🌐 Network Cameras Only", "network_only", "Only access linked mobile cameras via network")
        ]
        
        radio_buttons = []  # Store radio buttons for Enter key binding
        
        for text, value, desc in options:
            option_frame = tk.Frame(radio_container, bg='#1c1c1c')
            option_frame.pack(fill=tk.X, pady=8)
            
            radio = tk.Radiobutton(option_frame, text=text, 
                                 variable=self.camera_access_mode, value=value,
                                 bg='#1c1c1c', fg='white', selectcolor='#2c2c2c',
                                 font=("Segoe UI", 11), activebackground='#1c1c1c',
                                 activeforeground='white')
            radio.pack(anchor=tk.W)
            
            desc_label = tk.Label(option_frame, text=desc, 
                                 bg='#1c1c1c', fg='#888888', font=("Segoe UI", 9))
            desc_label.pack(anchor=tk.W, padx=(25, 0))
            
            # Store radio button for Enter key binding
            radio_buttons.append(radio)
        
        # Separator
        separator = tk.Frame(main_container, bg='#333333', height=2)
        separator.pack(fill=tk.X, pady=(20, 20))
        
        # Button container - FORCE PROPER SIZING
        button_container = tk.Frame(main_container, bg='#1c1c1c', height=80)
        button_container.pack(fill=tk.X, pady=(10, 0))
        button_container.pack_propagate(False)  # Prevent container from shrinking
        
        print("🔧 Creating Apply button with forced sizing...")
        
        # Apply button - FORCED SIZE APPROACH
        apply_btn = tk.Button(button_container, 
                            text="✅ Apply & Start CCTV", 
                            command=lambda: self.apply_camera_preference(dialog),
                            bg='#0078d4', 
                            fg='white', 
                            font=("Segoe UI", 12, "bold"),
                            width=20,  # Force width
                            height=2,  # Force height
                            relief=tk.RAISED, 
                            bd=3,
                            cursor='hand2')
        apply_btn.pack(side=tk.RIGHT, padx=(10, 0), pady=10)
        print("✅ Apply button created with forced size")
        
        # Cancel button - FORCED SIZE APPROACH
        cancel_btn = tk.Button(button_container, 
                             text="❌ Cancel", 
                             command=dialog.destroy,
                             bg='#666666', 
                             fg='white', 
                             font=("Segoe UI", 12),
                             width=10,  # Force width
                             height=2,  # Force height
                             relief=tk.RAISED, 
                             bd=3,
                             cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=10)
        
        # Force multiple updates to ensure proper sizing
        dialog.update_idletasks()
        apply_btn.update_idletasks()
        cancel_btn.update_idletasks()
        button_container.update_idletasks()
        
        # Set focus to Apply button
        apply_btn.focus_set()
        
        # Bind Enter key to Apply button
        def handle_enter_key(event):
            """Handle Enter key press to apply preference"""
            print("⌨️ Enter key pressed - applying preference")
            self.apply_camera_preference(dialog)
        
        # Bind Enter key to dialog and all widgets
        dialog.bind('<Return>', handle_enter_key)
        dialog.bind('<KP_Enter>', handle_enter_key)  # For numpad Enter
        
        # Also bind to radio buttons and other widgets for better UX
        for widget in [main_container, radio_container, button_container]:
            widget.bind('<Return>', handle_enter_key)
            widget.bind('<KP_Enter>', handle_enter_key)
        
        # Bind Enter key to individual radio buttons
        for radio in radio_buttons:
            radio.bind('<Return>', handle_enter_key)
            radio.bind('<KP_Enter>', handle_enter_key)
        
        # Make dialog non-resizable
        dialog.resizable(False, False)
        
        # Final update
        dialog.update()
        
        print("🖼️ Camera access dialog created with forced button sizes")
        print(f"📏 Apply button size: {apply_btn.winfo_width()}x{apply_btn.winfo_height()}")
        print(f"📏 Cancel button size: {cancel_btn.winfo_width()}x{cancel_btn.winfo_height()}")
        print(f"📏 Button container size: {button_container.winfo_width()}x{button_container.winfo_height()}")
    
    def apply_camera_preference(self, dialog):
        """Apply camera preference and start CCTV system"""
        try:
            mode = self.camera_access_mode.get()
            print(f"📹 Camera access mode set to: {mode}")
            
            # Close dialog first
            dialog.destroy()
            
            # Start CCTV system with the selected mode
            self.start_cctv_system()
            
        except Exception as e:
            print(f"❌ Error applying camera preference: {e}")
            messagebox.showerror("Error", f"Failed to apply camera preference: {str(e)}")
            if dialog.winfo_exists():
                dialog.destroy()
    
    def update_camera_displays_for_mode(self, mode):
        """Update camera display labels based on access mode"""
        if mode == "local_only":
            # Hide network cameras
            for i in range(2):
                camera_id = f'network_{i}'
                if camera_id in self.camera_labels:
                    self.camera_labels[camera_id].configure(
                        text=f"Network Cam {i+1}\nDisabled", 
                        fg='#666666'
                    )
        elif mode == "network_only":
            # Hide local cameras
            for i in range(2):
                camera_id = f'local_{i}'
                if camera_id in self.camera_labels:
                    self.camera_labels[camera_id].configure(
                        text=f"Local Cam {i+1}\nDisabled", 
                        fg='#666666'
                    )
        else:  # both
            # Reset all cameras to normal state
            for i in range(2):
                local_id = f'local_{i}'
                network_id = f'network_{i}'
                
                if local_id in self.camera_labels:
                    self.camera_labels[local_id].configure(
                        text=f"Local Cam {i+1}\nOffline", 
                        fg='#555555'
                    )
                
                if network_id in self.camera_labels:
                    self.camera_labels[network_id].configure(
                        text=f"Network Cam {i+1}\nOffline", 
                        fg='#555555'
                    )
    
    def run_multi_camera_cctv(self):
        """Main multi-camera CCTV loop"""
        try:
            self.cctv_status_var.set("CCTV System: Running")
            self.status_var.set("Multi-camera CCTV system active")
            
            while self.cctv_running:
                # Update status
                active_count = len([k for k in self.camera_threads.keys() if self.camera_threads[k].is_alive()])
                self.multi_camera_status_var.set(f"{active_count} cameras active")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"Multi-camera CCTV error: {e}")
        finally:
            self.cctv_running = False
            self.cctv_status_var.set("CCTV System: Stopped")
            self.status_var.set("Multi-camera CCTV system stopped")
    
    def stop_multi_camera_cctv(self):
        """Stop all camera threads"""
        if not self.cctv_running:
            messagebox.showwarning("Warning", "CCTV system is not running")
            return
        
        try:
            self.cctv_running = False
            self.cctv_status_var.set("CCTV System: Stopping...")
            self.status_var.set("Stopping all cameras...")
            
            # Wait for threads to stop
            for camera_id, thread in self.camera_threads.items():
                if thread.is_alive():
                    thread.join(timeout=2)
            
            # Clear displays
            for label in self.camera_labels.values():
                label.configure(image="", text="Camera Stopped")
            
            self.multi_camera_status_var.set("All cameras stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop cameras: {str(e)}")
    
    def switch_previous_camera(self):
        """Switch to previous camera"""
        if len(self.active_cameras) > 0:
            self.current_camera_index = (self.current_camera_index - 1) % len(self.active_cameras)
            self.update_camera_info()
    
    def switch_next_camera(self):
        """Switch to next camera"""
        if len(self.active_cameras) > 0:
            self.current_camera_index = (self.current_camera_index + 1) % len(self.active_cameras)
            self.update_camera_info()
    
    def update_camera_info(self):
        """Update camera info display"""
        if len(self.active_cameras) > 0:
            current_camera = self.active_cameras[self.current_camera_index]
            self.camera_info_label.config(text=f"{current_camera} ({self.current_camera_index + 1}/{len(self.active_cameras)})")
    
    def monitor_multi_camera_status(self):
        """Monitor multi-camera status"""
        try:
            if self.cctv_running:
                # Update camera status
                active_count = len([k for k in self.camera_threads.keys() if self.camera_threads[k].is_alive()])
                self.multi_camera_status_var.set(f"{active_count} cameras active")
            
            # Schedule next check
            self.root.after(1000, self.monitor_multi_camera_status)
            
        except Exception as e:
            print(f"Status monitoring error: {e}")
            self.root.after(1000, self.monitor_multi_camera_status)
    
    def monitor_cctv_status(self):
        """Monitor CCTV status and update GUI"""
        try:
            if self.cctv_running and self.cctv_detector:
                # Check if detector is still running
                if hasattr(self.cctv_detector, 'running') and not self.cctv_detector.running:
                    # Detector stopped on its own
                    self.cctv_running = False
                    self.cctv_detector = None
                    self.cctv_status_var.set("CCTV System: Stopped")
                    self.status_var.set("CCTV system stopped")
            
            # Schedule next check
            self.root.after(1000, self.monitor_cctv_status)  # Check every second
            
        except Exception as e:
            print(f"⚠️ Status monitoring error: {e}")
            # Continue monitoring even if there's an error
            self.root.after(1000, self.monitor_cctv_status)
    
    def speak_alert(self, message):
        """Speak alert message using text-to-speech"""
        if self.tts_engine:
            try:
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠️ TTS Error: {e}")
    
    def open_gallery_for_selected_user(self):
        """Open gallery for the currently selected user"""
        try:
            selection = self.user_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a user first")
                return
            
            # Get the selected item text and extract user name
            item_text = self.user_listbox.get(selection[0])
            if item_text == "No users registered":
                messagebox.showinfo("Info", "No users registered")
                return
            
            # Extract user name (remove the image count part)
            user_name = item_text.split(' (')[0]
            
            # Open gallery for this user
            self.show_image_gallery(user_name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening gallery: {str(e)}")
    
    def show_image_gallery(self, user_name):
        """Show image gallery for selected user with modern UI"""
        if not user_name:
            messagebox.showwarning("Warning", "Please select a user first")
            return
            
        try:
            user_dir = os.path.join(self.face_manager.known_faces_dir, user_name)
            
            if not os.path.exists(user_dir):
                messagebox.showinfo("Info", f"No images found for {user_name}")
                return
            
            # Get all image files
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                image_files.extend(glob.glob(os.path.join(user_dir, ext)))
            
            if not image_files:
                messagebox.showinfo("Info", f"No images found for {user_name}")
                return
            
            self.gallery_images = image_files
            self.current_image_index = 0
            
            # Create gallery window
            if self.gallery_window:
                self.gallery_window.destroy()
            
            self.gallery_window = tk.Toplevel(self.root)
            self.gallery_window.title(f"{user_name} - Gallery")
            self.gallery_window.geometry("900x700")
            self.gallery_window.configure(bg='#1c1c1c')
            
            # Main container
            main_gall = ttk.Frame(self.gallery_window, padding=20)
            main_gall.pack(fill=tk.BOTH, expand=True)
            
            # Header
            header = ttk.Frame(main_gall)
            header.pack(fill=tk.X, pady=(0, 15))
            ttk.Label(header, text=f"Captured Faces: {user_name}", style="Header.TLabel").pack(side=tk.LEFT)
            ttk.Label(header, text=f"{len(image_files)} items", foreground="gray").pack(side=tk.RIGHT)
            
            # Image display area with sleek card style
            disp_card = ttk.Frame(main_gall, style="Card.TFrame", padding=2)
            disp_card.pack(fill=tk.BOTH, expand=True)
            
            self.gallery_image_label = tk.Label(disp_card, bg='#111111')
            self.gallery_image_label.pack(fill=tk.BOTH, expand=True)
            
            # Navigation & Actions
            nav_bar = ttk.Frame(main_gall, padding=(0, 20))
            nav_bar.pack(fill=tk.X)
            
            # Prev/Next
            ttk.Button(nav_bar, text="⇠ Previous", command=self.show_previous_image).pack(side=tk.LEFT, padx=5)
            self.image_counter_label = ttk.Label(nav_bar, text=f"Photo 1 of {len(image_files)}", font=("Segoe UI", 10, "bold"))
            self.image_counter_label.pack(side=tk.LEFT, expand=True)
            ttk.Button(nav_bar, text="Next ⇢", command=self.show_next_image).pack(side=tk.LEFT, padx=5)
            
            # Action buttons
            action_bar = ttk.Frame(main_gall)
            action_bar.pack(fill=tk.X)
            
            ttk.Button(action_bar, text="🗑️ Delete Photo", command=self.delete_current_image).pack(side=tk.LEFT, padx=5)
            ttk.Button(action_bar, text="Done", command=self.close_gallery).pack(side=tk.RIGHT, padx=5)
            
            # Show first image
            self.display_gallery_image()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening gallery: {str(e)}")
    
    def display_gallery_image(self):
        """Display current image in gallery"""
        if not self.gallery_images or not self.gallery_window:
            return
        
        try:
            image_path = self.gallery_images[self.current_image_index]
            
            # Load and resize image
            image = Image.open(image_path)
            
            # Get display size
            label_width = 760  # Approximate available width
            label_height = 400  # Approximate available height
            
            # Resize image to fit while maintaining aspect ratio
            img_width, img_height = image.size
            ratio = min(label_width / img_width, label_height / img_height)
            
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update label
            self.gallery_image_label.configure(image=photo)
            self.gallery_image_label.image = photo  # Keep reference
            
            # Update counter
            self.image_counter_label.configure(
                text=f"Image {self.current_image_index + 1}/{len(self.gallery_images)}"
            )
            
            # Update window title with filename
            filename = os.path.basename(image_path)
            self.gallery_window.title(f"📸 Image Gallery - {filename}")
            
        except Exception as e:
            print(f"Error displaying image: {e}")
    
    def show_previous_image(self):
        """Show previous image in gallery"""
        if self.gallery_images:
            self.current_image_index = (self.current_image_index - 1) % len(self.gallery_images)
            self.display_gallery_image()
    
    def show_next_image(self):
        """Show next image in gallery"""
        if self.gallery_images:
            self.current_image_index = (self.current_image_index + 1) % len(self.gallery_images)
            self.display_gallery_image()
    
    def delete_current_image(self):
        """Delete currently displayed image"""
        if not self.gallery_images:
            return
        
        try:
            image_path = self.gallery_images[self.current_image_index]
            filename = os.path.basename(image_path)
            
            # Confirm deletion
            result = messagebox.askyesno("Confirm Delete", 
                                         f"Are you sure you want to delete '{filename}'?")
            if not result:
                return
            
            # Delete file
            os.remove(image_path)
            
            # Remove from list
            self.gallery_images.pop(self.current_image_index)
            
            # Update face manager data
            user_name = os.path.basename(os.path.dirname(image_path))
            self.face_manager.refresh_data()
            self.refresh_user_list()
            
            # Handle empty gallery
            if not self.gallery_images:
                messagebox.showinfo("Info", "No more images. Closing gallery.")
                self.close_gallery()
                return
            
            # Adjust index if needed
            if self.current_image_index >= len(self.gallery_images):
                self.current_image_index = len(self.gallery_images) - 1
            
            # Display new image
            self.display_gallery_image()
            
            messagebox.showinfo("Success", f"Image '{filename}' deleted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting image: {str(e)}")
    
    def close_gallery(self):
        """Close image gallery window"""
        if self.gallery_window:
            self.gallery_window.destroy()
            self.gallery_window = None
            self.gallery_images = []
            self.current_image_index = 0
    
    def refresh_data(self):
        """Refresh face data from disk"""
        try:
            self.face_manager.refresh_data()
            self.refresh_user_list()
            self.status_var.set("Data refreshed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
    
    def load_face_data(self):
        """Load face data from JSON file"""
        try:
            self.face_data = self.face_manager.get_all_users()
            return True
        except Exception as e:
            print(f"❌ Error loading face data: {e}")
            self.face_data = {}
            return False
    
    def save_face_data(self):
        """Save face data to JSON file"""
        return self.face_manager.save_face_data()
    
    def create_widgets(self):
        """Create all GUI widgets with a modern, sleek layout"""
        # Main Layout: Sidebar and Content Area
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar for quick navigation and status
        sidebar_frame = ttk.Frame(self.main_paned, padding=10, style="Card.TFrame")
        self.main_paned.add(sidebar_frame, weight=1)
        
        # App Title in Sidebar
        ttk.Label(sidebar_frame, text="👥 FACE", font=("Segoe UI", 24, "bold")).pack(pady=(20, 0))
        ttk.Label(sidebar_frame, text="MANAGER 3.0", font=("Segoe UI", 10, "bold")).pack(pady=(0, 30))
        
        # Status Card in Sidebar
        status_card = ttk.LabelFrame(sidebar_frame, text="System Status", padding=10)
        status_card.pack(fill=tk.X, pady=10)
        
        self.cctv_status_var = tk.StringVar(value="CCTV: Offline")
        ttk.Label(status_card, textvariable=self.cctv_status_var, font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        self.network_status_var = tk.StringVar(value="Server: Offline")
        ttk.Label(status_card, textvariable=self.network_status_var, font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        self.multi_camera_status_var = tk.StringVar(value="Cameras: 0 Active")
        ttk.Label(status_card, textvariable=self.multi_camera_status_var, font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        # Core Controls
        ttk.Separator(sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        ttk.Label(sidebar_frame, text="CONTROLS", font=("Segoe UI", 10, "bold"), foreground="gray").pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Button(sidebar_frame, text="🚀 Launch CCTV", command=self.launch_multi_camera_cctv, style="Accent.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(sidebar_frame, text="🛑 Stop All", command=self.stop_multi_camera_cctv).pack(fill=tk.X, pady=2)
        ttk.Button(sidebar_frame, text="🌐 Start Server", command=self.start_network_server).pack(fill=tk.X, pady=2)
        ttk.Button(sidebar_frame, text="🔑 Access Code", command=self.generate_access_code).pack(fill=tk.X, pady=2)
        
        # Search & Maintenance
        ttk.Separator(sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        ttk.Label(sidebar_frame, text="SEARCH", font=("Segoe UI", 10, "bold"), foreground="gray").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_user_list())
        ttk.Entry(sidebar_frame, textvariable=self.search_var).pack(fill=tk.X, pady=5)
        
        ttk.Label(sidebar_frame, text="DATABASE TOOLS", font=("Segoe UI", 10, "bold"), foreground="gray").pack(anchor=tk.W, pady=(15, 5))
        ttk.Button(sidebar_frame, text="📦 Backup", command=self.backup_database).pack(fill=tk.X, pady=2)
        ttk.Button(sidebar_frame, text="🧹 Cleanup", command=self.cleanup_duplicates).pack(fill=tk.X, pady=2)
        ttk.Button(sidebar_frame, text="📊 Statistics", command=self.show_statistics).pack(fill=tk.X, pady=2)
        
        # Sidebar Bottom
        sb_low = ttk.Frame(sidebar_frame, style="Card.TFrame")
        sb_low.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Separator(sidebar_frame, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.theme_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sb_low, text="🌙 Dark", variable=self.theme_var, command=self.toggle_theme).pack(side=tk.LEFT, padx=5)
        ttk.Button(sb_low, text="🔄 Refresh", command=self.refresh_user_list).pack(side=tk.RIGHT, padx=5)
        
        # Main Content Area (Scrollable)
        content_container = ttk.Frame(self.main_paned, padding=1)
        self.main_paned.add(content_container, weight=4)
        
        # Scrollable Canvas
        self.canvas = tk.Canvas(content_container, highlightthickness=0, bg="#1c1c1c")
        scrollbar = ttk.Scrollbar(content_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding=20)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Make canvas width follow container width
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add mouse wheel support
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # --- Content inside scrollable frame ---
        
        # 1. Dashboard Header
        ttk.Label(self.scrollable_frame, text="Dashboard Overview", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 20))
        
        # 2. Camera Feeds Section (Cards)
        camera_section = ttk.LabelFrame(self.scrollable_frame, text="📹 LIVE CAMERA FEEDS", padding=15)
        camera_section.pack(fill=tk.X, pady=10)
        
        self.camera_grid = ttk.Frame(camera_section, height=450)
        self.camera_grid.pack(fill=tk.X, pady=10)
        self.camera_grid.pack_propagate(False)
        
        # Camera Controls Overlay
        cam_controls = ttk.Frame(camera_section)
        cam_controls.pack(fill=tk.X)
        
        self.prev_camera_btn = ttk.Button(cam_controls, text="⇠ Previous", command=self.switch_previous_camera)
        self.prev_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.camera_info_label = ttk.Label(cam_controls, text="Camera 1/1", font=("Segoe UI", 10, "bold"))
        self.camera_info_label.pack(side=tk.LEFT, padx=20, expand=True)
        
        self.next_camera_btn = ttk.Button(cam_controls, text="Next ⇢", command=self.switch_next_camera)
        self.next_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # 3. User Management Row
        row2_frame = ttk.Frame(self.scrollable_frame)
        row2_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # User List Card
        users_card = ttk.LabelFrame(row2_frame, text="📋 REGISTERED USERS", padding=15)
        users_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        list_container = ttk.Frame(users_card)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        list_scroll = ttk.Scrollbar(list_container)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.user_listbox = tk.Listbox(list_container, yscrollcommand=list_scroll.set, 
                                       font=("Segoe UI", 11), bg="#2b2b2b", fg="white",
                                       highlightthickness=0, borderwidth=0, selectbackground="#0078d4")
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.user_listbox.yview)
        
        self.info_label = ttk.Label(users_card, text="Select a user to view details", foreground="gray")
        self.info_label.pack(pady=10)
        
        # User details buttons
        btn_user_frame = ttk.Frame(users_card)
        btn_user_frame.pack(fill=tk.X)
        ttk.Button(btn_user_frame, text="🖼️ Gallery", command=self.open_gallery_for_selected_user).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_user_frame, text="✏️ Rename", command=self.show_rename_dialog).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_user_frame, text="🗑️ Delete", command=self.delete_user).pack(side=tk.LEFT, expand=True, padx=2)
        
        # Registration Card
        reg_card = ttk.LabelFrame(row2_frame, text="👤 NEW USER REGISTRATION", padding=15)
        reg_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(reg_card, text="Full Name").pack(anchor=tk.W, pady=(0, 5))
        self.new_user_entry = ttk.Entry(reg_card, font=("Segoe UI", 11))
        self.new_user_entry.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(reg_card, text="Step 2: Add Face Data").pack(anchor=tk.W, pady=(0, 5))
        
        reg_btn_frame = ttk.Frame(reg_card)
        reg_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(reg_btn_frame, text="📷 Capture Live", command=self.capture_photo, style="Accent.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(reg_btn_frame, text="📂 Upload Photo", command=self.browse_image).pack(fill=tk.X, pady=2)
        
        ttk.Separator(reg_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        ttk.Button(reg_card, text="✨ CREATE PROFILE", command=self.create_user, style="Accent.TButton").pack(fill=tk.X, pady=5)
        
        # Merge Tool Card (New)
        merge_card = ttk.LabelFrame(self.scrollable_frame, text="🔗 MERGE USER PROFILES", padding=15)
        merge_card.pack(fill=tk.X, pady=10)
        
        m_container = ttk.Frame(merge_card)
        m_container.pack(fill=tk.X)
        
        ttk.Label(m_container, text="Merge selected user with:").pack(side=tk.LEFT, padx=(0, 10))
        self.merge_user_var = tk.StringVar()
        self.merge_combo = ttk.Combobox(m_container, textvariable=self.merge_user_var, state="readonly")
        self.merge_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        ttk.Label(m_container, text="New Name:").pack(side=tk.LEFT, padx=10)
        self.merge_name_entry = ttk.Entry(m_container)
        self.merge_name_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        self.delete_originals_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(m_container, text="Delete Originals", variable=self.delete_originals_var).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(m_container, text="Merge", command=self.merge_users, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        # Status Bar
        self.status_var = tk.StringVar(value="System Ready")
        status_bar = ttk.Frame(self.root, relief=tk.FLAT, padding=(10, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        ttk.Label(status_bar, text="v3.0.1 Stable", font=("Segoe UI", 9), foreground="gray").pack(side=tk.RIGHT)
        
        # Start monitors
        self.monitor_cctv_status()
        self.monitor_multi_camera_status()
        
        # Bind listbox selection
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)

    def show_rename_dialog(self):
        """Show a modern rename dialog"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to rename")
            return
            
        old_name = self.user_listbox.get(selection[0]).split(' (')[0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename Profile")
        dialog.geometry("400x200")
        dialog.configure(bg='#1c1c1c')
        
        main_d = ttk.Frame(dialog, padding=20)
        main_d.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_d, text=f"Renaming: {old_name}", font=("Segoe UI", 12, "bold")).pack(pady=(0, 15))
        
        entry = ttk.Entry(main_d)
        entry.pack(fill=tk.X, pady=5)
        entry.insert(0, old_name)
        entry.focus()
        
        def do_rename():
            new_name = entry.get().strip()
            if not new_name: return
            if self.face_manager.rename_user(old_name, new_name):
                self.refresh_user_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Renamed to {new_name}")
            else:
                messagebox.showerror("Error", "Rename failed")
        
        ttk.Button(main_d, text="Rename", command=do_rename, style="Accent.TButton").pack(side=tk.RIGHT, pady=10)
        ttk.Button(main_d, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=10, pady=10)
    
    def capture_photo(self):
        """Open camera window to capture a photo with modern UI"""
        if self.camera_active:
            messagebox.showwarning("Warning", "Camera is already active")
            return
        
        # Start camera status
        self.camera_active = True
        self.capture_status_var.set("Initializing camera...")
        
        # Create camera window
        self.camera_window = tk.Toplevel(self.root)
        self.camera_window.title("Capture Face Data")
        self.camera_window.geometry("800x650")
        self.camera_window.configure(bg='#1c1c1c')
        
        # Main container with padding
        main_cap = ttk.Frame(self.camera_window, padding=20)
        main_cap.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_cap, text="Face Data Capture", style="Header.TLabel").pack(pady=(0, 10))
        ttk.Label(main_cap, text="Please look directly at the camera", foreground="gray").pack(pady=(0, 15))
        
        # Camera feed label in a styled frame
        feed_frame = ttk.Frame(main_cap, style="Card.TFrame", padding=2)
        feed_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(feed_frame, bg='black')
        self.camera_label.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(main_cap, padding=(0, 15))
        control_frame.pack(fill=tk.X)
        
        status_label = ttk.Label(control_frame, textvariable=self.capture_status_var, font=("Segoe UI", 10))
        status_label.pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="📷 Take Snapshot", 
                   command=self.take_photo,
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(control_frame, text="Cancel", 
                   command=self.close_camera).pack(side=tk.RIGHT, padx=5)
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self.run_camera)
        self.camera_thread.daemon = True
        self.camera_thread.start()
    
    def initialize_camera(self, camera_index=0):
        """Initialize camera with multiple backend attempts and better error handling"""
        # Try different backends in order of preference
        backends = [
            cv2.CAP_DSHOW,      # DirectShow (Windows) - most stable
            cv2.CAP_MSMF,       # Media Foundation (Windows) - fallback
            cv2.CAP_ANY,        # Auto-detect
            cv2.CAP_V4L2,       # Video4Linux2 (Linux)
            cv2.CAP_AVFOUNDATION # AVFoundation (macOS)
        ]
        
        for backend in backends:
            try:
                print(f"📷 Trying camera {camera_index} with backend {backend}...")
                cap = cv2.VideoCapture(camera_index, backend)
                
                if not cap.isOpened():
                    cap.release()
                    continue
                
                # Test camera read with timeout
                ret, test_frame = cap.read()
                if not ret or test_frame is None:
                    cap.release()
                    continue
                
                # Set camera properties with error checking
                try:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
                    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
                except:
                    print(f"⚠️ Could not set camera {camera_index} properties")
                
                # Test multiple frames to ensure stability
                stable_frames = 0
                for _ in range(3):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        stable_frames += 1
                    time.sleep(0.1)
                
                if stable_frames >= 2:  # At least 2 out of 3 frames successful
                    print(f"✅ Camera {camera_index} initialized successfully with backend {backend}")
                    return cap
                else:
                    cap.release()
                    continue
                
            except Exception as e:
                print(f"⚠️ Backend {backend} failed: {e}")
                continue
        
        print(f"❌ All backends failed for camera {camera_index}")
        return None
    
    def run_camera(self):
        """Run camera in separate thread"""
        try:
            # Try different camera indices and backends
            camera_indices = [0, 1, 2]
            
            for camera_idx in camera_indices:
                self.camera_cap = self.initialize_camera(camera_idx)
                if self.camera_cap is not None:
                    break
            
            if self.camera_cap is None:
                self.capture_status_var.set("Camera not available")
                self.camera_active = False
                return
            
            # Load face cascade once
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            self.capture_status_var.set("Camera ready - Click Capture Photo")
            consecutive_failures = 0
            max_failures = 5
            
            while self.camera_active:
                ret, frame = self.camera_cap.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("❌ Too many consecutive frame failures. Attempting camera reinitialization...")
                        self.camera_cap.release()
                        
                        # Try to reinitialize camera
                        for camera_idx in camera_indices:
                            self.camera_cap = self.initialize_camera(camera_idx)
                            if self.camera_cap is not None:
                                print("✅ Camera reinitialized successfully")
                                consecutive_failures = 0
                                break
                        
                        if self.camera_cap is None:
                            print("❌ Failed to reinitialize camera.")
                            break
                    
                    time.sleep(0.1)
                    continue
                else:
                    consecutive_failures = 0  # Reset failure counter on successful read
                
                # Store current frame for capture
                self.current_frame = frame.copy()
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Add face detection overlay
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                
                # Draw face rectangles on the frame
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Convert to RGB and resize for display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame = cv2.resize(rgb_frame, (640, 480))
                
                # Convert to PIL Image
                pil_image = Image.fromarray(rgb_frame)
                photo = ImageTk.PhotoImage(image=pil_image)
                
                # Update GUI in main thread
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
                
                # Update status
                if len(faces) > 0:
                    self.capture_status_var.set(f"{len(faces)} face(s) detected")
                else:
                    self.capture_status_var.set("No face detected - position face in camera")
                
                time.sleep(0.03)  # ~30 FPS
            
            # Release camera
            if self.camera_cap:
                self.camera_cap.release()
                self.camera_cap = None
            
        except Exception as e:
            self.capture_status_var.set(f"Camera error: {str(e)}")
            if self.camera_cap:
                self.camera_cap.release()
                self.camera_cap = None
        finally:
            self.camera_active = False
    
    def take_photo(self):
        """Capture the current frame from the active camera"""
        try:
            if not self.camera_active:
                messagebox.showerror("Error", "Camera is not active")
                return
            
            if self.current_frame is None:
                messagebox.showerror("Error", "No frame available to capture")
                return
            
            # Use the stored current frame (already flipped)
            self.captured_image = self.current_frame.copy()
            
            # Show preview
            self.show_capture_preview()
            self.capture_status_var.set("Photo captured successfully!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error capturing photo: {str(e)}")
    
    def show_capture_preview(self):
        """Show preview of captured photo in a modern window"""
        if self.captured_image is None:
            return
        
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Snapshot Preview")
        preview_window.geometry("600x650")
        preview_window.configure(bg='#1c1c1c')
        
        main_prev = ttk.Frame(preview_window, padding=20)
        main_prev.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_prev, text="Review Snapshot", style="Header.TLabel").pack(pady=(0, 20))
        
        # Image display with border
        disp_card = ttk.Frame(main_prev, style="Card.TFrame", padding=2)
        disp_card.pack(fill=tk.BOTH, expand=True)
        
        # Convert to RGB and resize for display
        rgb_frame = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
        h, w = rgb_frame.shape[:2]
        ratio = min(500 / w, 400 / h)
        rgb_frame = cv2.resize(rgb_frame, (int(w * ratio), int(h * ratio)))
        
        pil_image = Image.fromarray(rgb_frame)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        preview_label = tk.Label(disp_card, image=photo, bg='#111111')
        preview_label.image = photo
        preview_label.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_prev, text="Does this photo look clear?", foreground="gray").pack(pady=15)
        
        # Actions
        action_frame = ttk.Frame(main_prev)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="✅ Use Photo", 
                   command=lambda: self.use_captured_photo(preview_window),
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(action_frame, text="Retake", 
                   command=lambda: self.retake_photo(preview_window)).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(action_frame, text="Cancel", 
                   command=lambda: self.cancel_photo(preview_window)).pack(side=tk.LEFT, padx=5)
    
    def use_captured_photo(self, preview_window):
        """Use the captured photo for user creation"""
        preview_window.destroy()
        self.close_camera()
        self.capture_status_var.set("Photo ready for user creation")
    
    def retake_photo(self, preview_window):
        """Retake the photo"""
        preview_window.destroy()
        self.captured_image = None
        self.capture_status_var.set("Ready to capture new photo")
    
    def cancel_photo(self, preview_window):
        """Cancel the captured photo"""
        preview_window.destroy()
        self.captured_image = None
        self.capture_status_var.set("Photo cancelled")
    
    def close_camera(self):
        """Close camera window"""
        self.camera_active = False
        
        # Wait a moment for the camera thread to finish
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.join(timeout=1.0)
        
        # Release camera if still active
        if self.camera_cap:
            self.camera_cap.release()
            self.camera_cap = None
        
        if self.camera_window:
            self.camera_window.destroy()
            self.camera_window = None
        
        self.current_frame = None
        self.capture_status_var.set("Camera closed")
    
    def browse_image(self):
        """Browse for an image file (fallback option)"""
        file_path = filedialog.askopenfilename(
            title="Select Face Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Load image for use
            image = cv2.imread(file_path)
            if image is not None:
                self.captured_image = image
                self.capture_status_var.set(f"Image loaded: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Could not load the image file")
    
    def create_user(self):
        """Create a new user with the captured image"""
        user_name = self.new_user_entry.get().strip()
        
        if not user_name:
            messagebox.showwarning("Warning", "Please enter a user name")
            return
        
        if self.captured_image is None:
            messagebox.showwarning("Warning", "Please capture a photo first")
            return
        
        if user_name in self.face_manager.get_all_users():
            messagebox.showerror("Error", f"User '{user_name}' already exists")
            return
        
        try:
            # Validate that the captured image contains a face
            gray = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) == 0:
                messagebox.showerror("Error", "No face detected in the captured photo")
                return
            
            # Add user using shared face manager
            face_box = [int(x) for x in faces[0]]  # Convert to regular int list
            if self.face_manager.add_user(user_name, self.captured_image, face_box):
                messagebox.showinfo("Success", f"Successfully created user '{user_name}' with {len(faces)} face(s) detected")
                self.new_user_entry.delete(0, tk.END)
                self.captured_image = None
                self.capture_status_var.set("No camera connected")
                self.refresh_user_list()
            else:
                messagebox.showerror("Error", "Failed to create user")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error creating user: {str(e)}")
    
    def refresh_user_list(self):
        """Refresh the user list and update related UI components"""
        self.user_listbox.delete(0, tk.END)
        
        face_data = self.face_manager.get_all_users()
        user_names = sorted(face_data.keys())
        
        if not face_data:
            self.user_listbox.insert(tk.END, "No users registered")
            if hasattr(self, 'merge_combo'):
                self.merge_combo.configure(values=[])
            return
        
        # Add users to listbox
        for user_name in user_names:
            user_info = face_data[user_name]
            image_count = user_info.get('count', 0)
            display_text = f"{user_name} ({image_count} images)"
            self.user_listbox.insert(tk.END, display_text)
        
        # Update merge combobox if it exists
        if hasattr(self, 'merge_combo'):
            self.merge_combo.configure(values=user_names)
            
        # Update status
        self.status_var.set(f"Loaded {len(face_data)} registered faces")
    
    def on_user_select(self, event):
        """Handle user selection and update info panel"""
        selection = self.user_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        item_text = self.user_listbox.get(index)
        if item_text == "No users registered":
            self.info_label.config(text="No users registered")
            return
        
        # Extract user name
        user_name = item_text.split(' (')[0]
        
        # Show user info
        stats = self.get_user_stats(user_name)
        if stats:
            info_text = f"👤 Profile: {user_name}\n📸 Images: {stats['image_count']}\n💾 Data Size: {stats['total_size_mb']} MB\n🗓️ Modified: {stats['last_updated']}"
            self.info_label.config(text=info_text)
    
    def get_user_stats(self, user_name):
        """Get statistics for a specific user"""
        face_data = self.face_manager.get_all_users()
        
        if user_name not in face_data:
            return None
        
        user_data = face_data[user_name]
        user_dir = os.path.join(self.face_manager.known_faces_dir, user_name)
        
        image_count = 0
        total_size = 0
        
        if os.path.exists(user_dir):
            image_files = glob.glob(os.path.join(user_dir, "*.jpg")) + \
                          glob.glob(os.path.join(user_dir, "*.jpeg")) + \
                          glob.glob(os.path.join(user_dir, "*.png")) + \
                          glob.glob(os.path.join(user_dir, "*.bmp"))
            
            image_count = len(image_files)
            for image_file in image_files:
                total_size += os.path.getsize(image_file)
        
        return {
            'name': user_name,
            'image_count': image_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'last_updated': user_data.get('last_updated', 'Never'),
            'face_data': user_data.get('face_data', {})
        }
    
    def filter_user_list(self):
        """Filter user list based on search query"""
        query = self.search_var.get().lower()
        self.user_listbox.delete(0, tk.END)
        
        face_data = self.face_manager.get_all_users()
        for user_name in sorted(face_data.keys()):
            if query in user_name.lower():
                image_count = face_data[user_name].get('count', 0)
                self.user_listbox.insert(tk.END, f"{user_name} ({image_count} images)")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.theme_var.get():
            sv_ttk.set_theme("dark")
        else:
            sv_ttk.set_theme("light")
    
    def delete_user(self):
        """Delete selected user"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        index = selection[0]
        item_text = self.user_listbox.get(index)
        if item_text == "No users registered":
            messagebox.showwarning("Warning", "No users registered")
            return
        
        user_name = item_text.split(' (')[0]
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete '{user_name}' and all their images?")
        if not result:
            return
        
        try:
            if self.face_manager.delete_user(user_name):
                messagebox.showinfo("Success", f"Successfully deleted user '{user_name}'")
                self.refresh_user_list()
            else:
                messagebox.showerror("Error", "Failed to delete user")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting user: {str(e)}")
    
    def merge_users(self):
        """Merge selected user with another user using face_manager"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a primary user from the list")
            return
        
        user1_name = self.user_listbox.get(selection[0]).split(' (')[0]
        user2_name = self.merge_user_var.get()
        new_name = self.merge_name_entry.get().strip()
        delete_originals = self.delete_originals_var.get()
        
        if not user2_name:
            messagebox.showwarning("Warning", "Please select a user to merge with")
            return
        
        if not new_name:
            messagebox.showwarning("Warning", "Please enter a name for the merged profile")
            return
        
        if user1_name == user2_name:
            messagebox.showwarning("Warning", "Cannot merge a profile with itself")
            return
            
        try:
            # We'll use face_manager's logic if possible, or manual logic if not
            # FaceDataManager doesn't have merge_users, so we implement it here but use its paths
            
            kfd = self.face_manager.known_faces_dir
            new_dir = os.path.join(kfd, new_name)
            os.makedirs(new_dir, exist_ok=True)
            
            face_data = self.face_manager.get_all_users()
            
            # Copy images
            for u_name in [user1_name, user2_name]:
                u_dir = os.path.join(kfd, u_name)
                if os.path.exists(u_dir):
                    for img in glob.glob(os.path.join(u_dir, "*.*")):
                        if img.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                            shutil.copy2(img, os.path.join(new_dir, os.path.basename(img)))
            
            # Update data
            new_count = face_data.get(user1_name, {}).get('count', 0) + face_data.get(user2_name, {}).get('count', 0)
            face_data[new_name] = {
                'count': new_count,
                'last_updated': datetime.now().isoformat(),
                'face_data': {'merged': True, 'sources': [user1_name, user2_name]}
            }
            
            if delete_originals:
                self.face_manager.delete_user(user1_name)
                self.face_manager.delete_user(user2_name)
            
            self.face_manager.save_face_data()
            self.refresh_user_list()
            messagebox.showinfo("Success", f"Profiles merged into {new_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Merge failed: {str(e)}")

    def show_statistics(self):
        """Show statistics in a modern window"""
        selection = self.user_listbox.curselection()
        user_name = None
        if selection:
            user_name = self.user_listbox.get(selection[0]).split(' (')[0]
            
        stats_window = tk.Toplevel(self.root)
        stats_window.title("System Statistics")
        stats_window.geometry("500x450")
        stats_window.configure(bg='#1c1c1c')
        
        main_s = ttk.Frame(stats_window, padding=20)
        main_s.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_s, text="Database Insights", style="Header.TLabel").pack(pady=(0, 20))
        
        # Global Stats
        all_users = self.face_manager.get_all_users()
        total_users = len(all_users)
        total_images = sum(u.get('count', 0) for u in all_users.values())
        
        global_card = ttk.LabelFrame(main_s, text="Global Overview", padding=15)
        global_card.pack(fill=tk.X, pady=10)
        
        ttk.Label(global_card, text=f"Total Profiles: {total_users}").pack(anchor=tk.W)
        ttk.Label(global_card, text=f"Total Face Data Samples: {total_images}").pack(anchor=tk.W)
        
        # Selected User Stats
        if user_name and user_name != "No users registered":
            user_stats = self.get_user_stats(user_name)
            u_card = ttk.LabelFrame(main_s, text=f"Profile: {user_name}", padding=15)
            u_card.pack(fill=tk.X, pady=10)
            ttk.Label(u_card, text=f"Samples: {user_stats['image_count']}").pack(anchor=tk.W)
            ttk.Label(u_card, text=f"Storage: {user_stats['total_size_mb']} MB").pack(anchor=tk.W)
            ttk.Label(u_card, text=f"Last Seen: {user_stats['last_updated']}").pack(anchor=tk.W)
            
        ttk.Button(main_s, text="Done", command=stats_window.destroy).pack(side=tk.BOTTOM, pady=10)

    def backup_database(self):
        """Create a backup of the face database using face_manager paths"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            
            # Backup paths from face_manager
            json_path = self.face_manager.known_faces_json
            dir_path = self.face_manager.known_faces_dir
            
            if os.path.exists(json_path):
                shutil.copy2(json_path, f"{json_path}.{backup_name}.bak")
                
            if os.path.exists(dir_path):
                shutil.copytree(dir_path, f"{dir_path}_{backup_name}")
            
            messagebox.showinfo("Backup Success", f"All data backed up with tag: {backup_name}")
            self.status_var.set(f"System backed up: {backup_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")

    def cleanup_duplicates(self):
        """Clean up duplicate face samples using face_manager paths"""
        try:
            count = 0
            all_users = self.face_manager.get_all_users()
            kfd = self.face_manager.known_faces_dir
            
            for user in all_users:
                u_dir = os.path.join(kfd, user)
                if not os.path.exists(u_dir): continue
                
                hashes = {}
                for img in glob.glob(os.path.join(u_dir, "*.*")):
                    if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                        with open(img, "rb") as f:
                            h = hash(f.read())
                            if h in hashes:
                                os.remove(img)
                                count += 1
                            else:
                                hashes[h] = img
                
                all_users[user]['count'] = len(hashes)
                
            self.face_manager.save_face_data()
            self.refresh_user_list()
            messagebox.showinfo("Cleanup Complete", f"Removed {count} duplicate samples")
        except Exception as e:
            messagebox.showerror("Error", f"Cleanup failed: {str(e)}")

def main():
    root = tk.Tk()
    app = FaceManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
