#!/usr/bin/env python3
"""
Face Manager GUI - Complete Face Recognition & CCTV System
👥 A comprehensive face management application with CCTV integration

Features:
- Face registration and management
- Live camera capture with face detection
- Image gallery for captured faces
- Multi-camera CCTV system
- Network camera server for mobile devices
- User profile management (add, delete, rename, merge)
- Data backup and statistics
- Modern dark theme UI

Requirements:
- All dependencies are listed in requirements.txt
- Camera access (webcam or built-in camera)
- Windows OS (optimized for Windows)

Usage:
    python RUN_GUI.py

Author: Face Recognition System
Version: 3.0.1 Stable
"""

import sys
import os

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'tkinter', 'cv2', 'PIL', 'numpy', 'sv_ttk', 
        'pyttsx3', 'qrcode', 'requests', 'flask', 
        'flask_socketio', 'face_data_manager'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'face_data_manager':
                import face_data_manager
            elif module == 'cv2':
                import cv2
            elif module == 'PIL':
                import PIL
            elif module == 'sv_ttk':
                import sv_ttk
            elif module == 'pyttsx3':
                import pyttsx3
            elif module == 'qrcode':
                import qrcode
            elif module == 'requests':
                import requests
            elif module == 'flask':
                import flask
            elif module == 'flask_socketio':
                import flask_socketio
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Please install missing packages using:")
        print("pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies available!")
    return True

def check_system_requirements():
    """Check system requirements"""
    print("\n🖥️  Checking system requirements...")
    
    # Check if we're on Windows
    if os.name == 'nt':
        print("✅ Windows OS detected")
    else:
        print("⚠️  Non-Windows OS detected - some features may not work optimally")
    
    # Check camera availability
    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            print("✅ Camera available")
            cap.release()
        else:
            print("⚠️  Camera not available - check camera permissions")
    except:
        print("⚠️  Camera check failed")
    
    # Check directories
    required_dirs = ['known_faces', 'cctv_recordings', 'network_cameras', 'access_codes']
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name} directory exists")
        else:
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ Created {dir_name} directory")
    
    return True

def main():
    """Main entry point"""
    print("👥 Face Manager GUI v3.0.1")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return
    
    # Check system requirements
    check_system_requirements()
    
    print("\n🚀 Starting Face Manager GUI...")
    print("Close this window to exit the application")
    print("=" * 40)
    
    try:
        # Import and run the GUI
        from face_manager_gui import main as gui_main
        gui_main()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application closed by user")
    except Exception as e:
        print(f"\n❌ Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
