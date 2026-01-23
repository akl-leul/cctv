import os
import json
import glob
import cv2
from datetime import datetime

def scan_known_faces_directory():
    """Scan the known_faces directory and create/update the JSON database"""
    
    known_faces_dir = "known_faces"
    known_faces_json = "known_faces.json"
    
    if not os.path.exists(known_faces_dir):
        print(f"❌ Directory '{known_faces_dir}' not found")
        return False
    
    print(f"🔍 Scanning directory: {known_faces_dir}")
    
    # Load existing JSON if it exists
    existing_data = {}
    if os.path.exists(known_faces_json):
        try:
            with open(known_faces_json, 'r') as f:
                data = json.load(f)
                existing_data = data.get("faces", {})
            print(f"✅ Loaded existing data with {len(existing_data)} users")
        except Exception as e:
            print(f"⚠️ Error loading existing JSON: {e}")
    
    # Scan directory for users
    users_found = {}
    
    for item in os.listdir(known_faces_dir):
        item_path = os.path.join(known_faces_dir, item)
        
        if os.path.isdir(item_path):
            user_name = item
            print(f"\n👤 Processing user: {user_name}")
            
            # Find all image files
            image_files = glob.glob(os.path.join(item_path, "*.jpg")) + \
                          glob.glob(os.path.join(item_path, "*.jpeg")) + \
                          glob.glob(os.path.join(item_path, "*.png")) + \
                          glob.glob(os.path.join(item_path, "*.bmp"))
            
            print(f"   📁 Found {len(image_files)} image files")
            
            # Process each image to verify it contains a face
            valid_images = []
            
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            for image_file in image_files:
                try:
                    # Load image
                    image = cv2.imread(image_file)
                    if image is None:
                        print(f"   ⚠️ Could not load: {os.path.basename(image_file)}")
                        continue
                    
                    # Convert to grayscale
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    
                    # Detect faces
                    faces = face_cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                    )
                    
                    if len(faces) > 0:
                        valid_images.append(image_file)
                        print(f"   ✅ Valid face image: {os.path.basename(image_file)}")
                    else:
                        print(f"   ❌ No face detected: {os.path.basename(image_file)}")
                        
                except Exception as e:
                    print(f"   ⚠️ Error processing {os.path.basename(image_file)}: {e}")
            
            if valid_images:
                users_found[user_name] = {
                    'count': len(valid_images),
                    'images': valid_images,
                    'face_data': existing_data.get(user_name, {}).get('face_data', {}),
                    'first_detected': existing_data.get(user_name, {}).get('first_detected', datetime.now().isoformat()),
                    'last_detected': datetime.now().isoformat(),
                    'verified': True
                }
                print(f"   ✅ User {user_name}: {len(valid_images)} valid face images")
            else:
                print(f"   ❌ User {user_name}: No valid face images found")
    
    # Save the updated database
    if users_found:
        data = {
            "faces": users_found,
            "last_updated": datetime.now().isoformat(),
            "total_users": len(users_found),
            "scan_method": "directory_scan"
        }
        
        with open(known_faces_json, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Successfully created/updated {known_faces_json}")
        print(f"📊 Total users: {len(users_found)}")
        print(f"📁 Total images: {sum(user['count'] for user in users_found.values())}")
        
        return True
    else:
        print(f"\n❌ No valid face images found in any user directories")
        return False

def show_current_status():
    """Show current status of the face database"""
    known_faces_json = "known_faces.json"
    known_faces_dir = "known_faces"
    
    print("=" * 50)
    print("📊 FACE DATABASE STATUS")
    print("=" * 50)
    
    # Check directory
    if os.path.exists(known_faces_dir):
        print(f"📁 Directory: {known_faces_dir} ✅")
        user_dirs = [d for d in os.listdir(known_faces_dir) if os.path.isdir(os.path.join(known_faces_dir, d))]
        print(f"👤 User directories found: {len(user_dirs)}")
        for user_dir in user_dirs:
            user_path = os.path.join(known_faces_dir, user_dir)
            image_files = glob.glob(os.path.join(user_path, "*.jpg")) + \
                          glob.glob(os.path.join(user_path, "*.jpeg")) + \
                          glob.glob(os.path.join(user_path, "*.png")) + \
                          glob.glob(os.path.join(user_path, "*.bmp"))
            print(f"   └─ {user_dir}: {len(image_files)} files")
    else:
        print(f"📁 Directory: {known_faces_dir} ❌")
    
    print()
    
    # Check JSON file
    if os.path.exists(known_faces_json):
        print(f"📄 JSON file: {known_faces_json} ✅")
        try:
            with open(known_faces_json, 'r') as f:
                data = json.load(f)
                faces = data.get("faces", {})
                print(f"👤 Users in database: {len(faces)}")
                for user_name, user_data in faces.items():
                    count = user_data.get('count', 0)
                    last_updated = user_data.get('last_updated', 'Unknown')
                    print(f"   └─ {user_name}: {count} images (updated: {last_updated[:10]})")
        except Exception as e:
            print(f"❌ Error reading JSON: {e}")
    else:
        print(f"📄 JSON file: {known_faces_json} ❌")
    
    print("=" * 50)

def main():
    """Main function"""
    print("🔍 FACE DATABASE SCANNER")
    print("=" * 50)
    
    # Show current status
    show_current_status()
    
    print("\n" + "=" * 50)
    print("OPTIONS:")
    print("1. Scan directory and create/update database")
    print("2. Show current status only")
    print("3. Exit")
    print("=" * 50)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        print("\n🔄 Starting directory scan...")
        success = scan_known_faces_directory()
        
        if success:
            print("\n✅ Scan completed successfully!")
            print("You can now run the face management system.")
        else:
            print("\n❌ Scan failed. Please check your directory structure.")
    
    elif choice == '2':
        print("\n📊 Current status shown above.")
    
    elif choice == '3':
        print("\n👋 Exiting...")
    
    else:
        print("\n❌ Invalid choice.")

if __name__ == "__main__":
    main()
