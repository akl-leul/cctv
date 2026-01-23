import json
import os
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

class FaceDataManager:
    """Shared face data management system for both CCTV detector and Face Manager GUI"""
    
    def __init__(self):
        self.known_faces_dir = "known_faces"
        self.known_faces_json = "known_faces.json"
        self.face_data = {}
        self.face_encodings = {}
        
        # Ensure directories exist
        os.makedirs(self.known_faces_dir, exist_ok=True)
        
        # Load existing data
        self.load_face_data()
        self.load_face_images()
    
    def load_face_data(self):
        """Load face data from JSON file"""
        try:
            if os.path.exists(self.known_faces_json):
                with open(self.known_faces_json, 'r') as f:
                    data = json.load(f)
                    self.face_data = data.get("faces", {})
                print(f"✅ Loaded {len(self.face_data)} users from database")
            else:
                print("⚠️ No existing face database found")
                self.face_data = {}
        except Exception as e:
            print(f"❌ Error loading face data: {e}")
            self.face_data = {}
    
    def save_face_data(self):
        """Save face data to JSON file"""
        try:
            data = {
                "faces": self.face_data,
                "last_updated": datetime.now().isoformat(),
                "total_users": len(self.face_data)
            }
            
            with open(self.known_faces_json, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved {len(self.face_data)} users to database")
            return True
        except Exception as e:
            print(f"❌ Error saving face data: {e}")
            return False
    
    def load_face_images(self):
        """Load face images from directories for recognition"""
        self.face_encodings = {}
        
        try:
            if not os.path.exists(self.known_faces_dir):
                return
            
            for person_name in os.listdir(self.known_faces_dir):
                person_dir = os.path.join(self.known_faces_dir, person_name)
                if os.path.isdir(person_dir):
                    face_images = []
                    
                    for image_file in os.listdir(person_dir):
                        if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                            image_path = os.path.join(person_dir, image_file)
                            try:
                                # Load and process face image
                                image = cv2.imread(image_path)
                                if image is not None:
                                    # Convert to grayscale
                                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                                    
                                    # Detect face in the image
                                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                                    faces = face_cascade.detectMultiScale(
                                        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                                    )
                                    
                                    if len(faces) > 0:
                                        # Use the first detected face
                                        x, y, w, h = faces[0]
                                        face_roi = gray[y:y+h, x:x+w]
                                        # Resize to standard size
                                        face_roi = cv2.resize(face_roi, (100, 100))
                                        face_images.append(face_roi)
                            except Exception as e:
                                print(f"⚠️ Error loading {image_path}: {e}")
                    
                    if face_images:
                        self.face_encodings[person_name] = {
                            'images': face_images,
                            'count': len(face_images)
                        }
                        print(f"✅ Loaded {len(face_images)} face images for {person_name}")
            
            print(f"✅ Total face encodings loaded: {len(self.face_encodings)}")
            
        except Exception as e:
            print(f"❌ Error loading face images: {e}")
            self.face_encodings = {}
    
    def add_user(self, user_name: str, image: np.ndarray, face_box: List[int] = None) -> bool:
        """Add a new user with captured image"""
        try:
            if user_name in self.face_data:
                print(f"⚠️ User '{user_name}' already exists")
                return False
            
            # Create user directory
            user_dir = os.path.join(self.known_faces_dir, user_name)
            os.makedirs(user_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_name}_{timestamp}.jpg"
            
            # Save captured image
            dest_path = os.path.join(user_dir, filename)
            cv2.imwrite(dest_path, image)
            
            # Save cropped face if face box is provided
            face_dest_path = None
            if face_box:
                x, y, w, h = face_box
                face_roi = image[y:y+h, x:x+w]
                face_filename = f"{user_name}_{timestamp}_face.jpg"
                face_dest_path = os.path.join(user_dir, face_filename)
                cv2.imwrite(face_dest_path, face_roi)
            
            # Add to face data
            self.face_data[user_name] = {
                'count': 2 if face_dest_path else 1,
                'images': [dest_path] + ([face_dest_path] if face_dest_path else []),
                'face_data': {
                    'face_box': face_box if face_box else [],
                    'image_size': image.shape[:2]
                },
                'first_detected': datetime.now().isoformat(),
                'last_detected': datetime.now().isoformat(),
                'verified': True
            }
            
            # Save updated data
            if self.save_face_data():
                # Reload face encodings
                self.load_face_images()
                print(f"✅ Successfully added user '{user_name}'")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
    
    def update_user_last_seen(self, user_name: str):
        """Update last seen timestamp for user"""
        if user_name in self.face_data:
            self.face_data[user_name]['last_detected'] = datetime.now().isoformat()
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all user data"""
        return self.face_data.copy()
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        return len(self.face_data)
    
    def get_face_encodings(self) -> Dict[str, Any]:
        """Get face encodings for recognition"""
        return self.face_encodings.copy()
    
    def delete_user(self, user_name: str) -> bool:
        """Delete a user and their images"""
        try:
            if user_name not in self.face_data:
                return False
            
            # Delete user directory
            user_dir = os.path.join(self.known_faces_dir, user_name)
            if os.path.exists(user_dir):
                import shutil
                shutil.rmtree(user_dir)
            
            # Remove from face data
            self.face_data.pop(user_name)
            
            # Remove from face encodings
            if user_name in self.face_encodings:
                self.face_encodings.pop(user_name)
            
            # Save updated data
            return self.save_face_data()
            
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def rename_user(self, old_name: str, new_name: str) -> bool:
        """Rename a user"""
        try:
            if old_name not in self.face_data:
                return False
            
            if new_name in self.face_data:
                print(f"⚠️ User '{new_name}' already exists")
                return False
            
            # Create new directory
            new_dir = os.path.join(self.known_faces_dir, new_name)
            os.makedirs(new_dir, exist_ok=True)
            
            # Move images from old directory to new directory
            old_dir = os.path.join(self.known_faces_dir, old_name)
            if os.path.exists(old_dir):
                import shutil
                import glob
                
                image_files = glob.glob(os.path.join(old_dir, "*.jpg")) + \
                              glob.glob(os.path.join(old_dir, "*.jpeg")) + \
                              glob.glob(os.path.join(old_dir, "*.png")) + \
                              glob.glob(os.path.join(old_dir, "*.bmp"))
                
                for image_file in image_files:
                    new_filename = image_file.replace(old_dir, new_dir)
                    shutil.move(image_file, new_filename)
                
                # Remove old directory if empty
                try:
                    os.rmdir(old_dir)
                except:
                    pass
            
            # Update face data
            self.face_data[new_name] = self.face_data.pop(old_name)
            self.face_data[new_name]['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            if self.save_face_data():
                # Reload face encodings
                self.load_face_images()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error renaming user: {e}")
            return False
    
    def refresh_data(self):
        """Refresh all data from disk"""
        self.load_face_data()
        self.load_face_images()
        print("✅ Face data refreshed from disk")
