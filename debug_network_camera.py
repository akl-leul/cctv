#!/usr/bin/env python3
"""
Debug script to test network camera functionality step by step
Run this while the Face Manager GUI is running with CCTV launched
"""

import requests
import time
import json

def test_step_by_step():
    """Test each step of the network camera flow"""
    print("🔍 Debugging Network Camera Flow Step by Step\n")
    
    # Step 1: Check if server is running
    print("Step 1: Checking server status...")
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Server is running")
            print(f"   Active cameras: {status.get('active_cameras', 0)}")
            print(f"   Server IP: {status.get('server_ip', 'Unknown')}")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the network server is running in the GUI!")
        return
    
    # Step 2: Get list of cameras
    print("\nStep 2: Getting camera list...")
    try:
        response = requests.get("http://localhost:5000/api/cameras", timeout=5)
        if response.status_code == 200:
            cameras = response.json()
            camera_list = cameras.get('cameras', [])
            print(f"✅ Found {len(camera_list)} cameras: {camera_list}")
            
            if not camera_list:
                print("⚠️ No cameras connected!")
                print("   Connect a mobile camera using the access code first")
                return
        else:
            print(f"❌ Failed to get camera list: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting camera list: {e}")
        return
    
    # Step 3: Test each camera
    for i, camera_code in enumerate(camera_list):
        print(f"\nStep 3.{i+1}: Testing camera {camera_code}")
        
        # Test camera status
        try:
            response = requests.get(f"http://localhost:5000/api/camera/status/{camera_code}", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Camera status: {status}")
            else:
                print(f"   ❌ Status check failed: {response.status_code}")
                continue
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
            continue
        
        # Test frame retrieval
        try:
            response = requests.get(f"http://localhost:5000/api/camera/latest/{camera_code}", timeout=5)
            if response.status_code == 200:
                frame_data = response.json()
                if 'frame' in frame_data:
                    frame_size = len(frame_data['frame'])
                    print(f"   ✅ Frame retrieved (size: {frame_size} chars)")
                    
                    # Try to decode the frame
                    import base64
                    import numpy as np
                    import cv2
                    
                    try:
                        frame_bytes = base64.b64decode(frame_data['frame'])
                        frame_array = np.frombuffer(frame_bytes, np.uint8)
                        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                        
                        if frame is not None and frame.size > 0:
                            print(f"   ✅ Frame decoded successfully (shape: {frame.shape})")
                        else:
                            print(f"   ❌ Frame decode failed")
                    except Exception as e:
                        print(f"   ❌ Frame decode error: {e}")
                else:
                    print(f"   ❌ No frame in response")
            else:
                print(f"   ❌ Frame retrieval failed: {response.status_code}")
                if response.status_code == 404:
                    print(f"   (Camera {camera_code} may not be sending frames)")
        except Exception as e:
            print(f"   ❌ Frame retrieval error: {e}")
    
    print("\n" + "="*50)
    print("🎯 Debugging Complete!")
    print("\nIf you see:")
    print("✅ Server running + ✅ Cameras found + ✅ Frames retrieved")
    print("   → The issue is in GUI display updating")
    print("\n❌ Any step failed")
    print("   → Fix that step first")

if __name__ == "__main__":
    print("🚀 Network Camera Debug Tool")
    print("Make sure:")
    print("1. Face Manager GUI is running")
    print("2. CCTV system is launched")
    print("3. Network server is started")
    print("4. At least one mobile camera is connected")
    print("\n" + "="*50)
    
    test_step_by_step()
