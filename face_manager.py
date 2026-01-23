import os
import json
import shutil
import cv2
import numpy as np
from datetime import datetime
import glob

class FaceManager:
    def __init__(self):
        self.known_faces_dir = "known_faces"
        self.known_faces_json = "known_faces.json"
        self.face_data = {}
        
        # Load existing data
        self.load_face_data()
    
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
        except Exception as e:
            print(f"❌ Error saving face data: {e}")
    
    def list_all_users(self):
        """List all registered users"""
        if not self.face_data:
            print("❌ No users registered")
            return []
        
        print("\n👥 Registered Users:")
        print("=" * 40)
        for i, (user_name, user_info) in enumerate(self.face_data.items(), 1):
            image_count = user_info.get('count', 0)
            last_updated = user_info.get('last_updated', 'Never')
            print(f"{i:2d}. {user_name}")
            print(f"    Images: {image_count}")
            print(f"    Last Updated: {last_updated}")
            print("-" * 40)
        
        return list(self.face_data.keys())
    
    def rename_user(self, old_name, new_name):
        """Rename a user and update all their face images"""
        if old_name not in self.face_data:
            print(f"❌ User '{old_name}' not found")
            return False
        
        if new_name in self.face_data:
            print(f"❌ User '{new_name}' already exists")
            return False
        
        try:
            # Create new directory
            new_dir = os.path.join(self.known_faces_dir, new_name)
            os.makedirs(new_dir, exist_ok=True)
            
            # Move all images from old directory to new directory
            old_dir = os.path.join(self.known_faces_dir, old_name)
            if os.path.exists(old_dir):
                image_files = glob.glob(os.path.join(old_dir, "*.jpg")) + \
                              glob.glob(os.path.join(old_dir, "*.jpeg")) + \
                              glob.glob(os.path.join(old_dir, "*.png")) + \
                              glob.glob(os.path.join(old_dir, "*.bmp"))
                
                for image_file in image_files:
                    new_filename = image_file.replace(old_dir, new_dir)
                    shutil.move(image_file, new_filename)
                    print(f"📁 Moved: {os.path.basename(image_file)} → {new_name}/{os.path.basename(new_filename)}")
                
                # Remove old directory if empty
                try:
                    os.rmdir(old_dir)
                    print(f"🗑️ Removed empty directory: {old_name}")
                except:
                    print(f"⚠️ Could not remove directory: {old_dir}")
            
            # Update face data
            self.face_data[new_name] = self.face_data.pop(old_name)
            self.face_data[new_name]['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            self.save_face_data()
            
            print(f"✅ Successfully renamed '{old_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error renaming user: {e}")
            return False
    
    def delete_user(self, user_name):
        """Delete a user and all their face images"""
        if user_name not in self.face_data:
            print(f"❌ User '{user_name}' not found")
            return False
        
        try:
            # Delete user directory and all images
            user_dir = os.path.join(self.known_faces_dir, user_name)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
                print(f"🗑️ Deleted directory: {user_dir}")
            
            # Remove from face data
            self.face_data.pop(user_name)
            
            # Save updated data
            self.save_face_data()
            
            print(f"✅ Successfully deleted user '{user_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def merge_users(self, user1_name, user2_name, new_name, delete_originals=False):
        """Merge two users into one"""
        if user1_name not in self.face_data or user2_name not in self.face_data:
            print(f"❌ One or both users not found")
            return False
        
        if new_name in self.face_data:
            print(f"❌ User '{new_name}' already exists")
            return False
        
        try:
            # Create new directory
            new_dir = os.path.join(self.known_faces_dir, new_name)
            os.makedirs(new_dir, exist_ok=True)
            
            # Copy images from both users
            for user_name in [user1_name, user2_name]:
                user_dir = os.path.join(self.known_faces_dir, user_name)
                if os.path.exists(user_dir):
                    image_files = glob.glob(os.path.join(user_dir, "*.jpg")) + \
                                  glob.glob(os.path.join(user_dir, "*.jpeg")) + \
                                  glob.glob(os.path.join(user_dir, "*.png")) + \
                                  glob.glob(os.path.join(user_dir, "*.bmp"))
                    
                    for image_file in image_files:
                        new_filename = image_file.replace(user_dir, new_dir)
                        shutil.copy2(image_file, new_filename)
                        print(f"📋 Copied: {os.path.basename(image_file)} → {new_name}/{os.path.basename(new_filename)}")
            
            # Combine face data
            user1_data = self.face_data[user1_name]
            user2_data = self.face_data[user2_name]
            
            self.face_data[new_name] = {
                'count': user1_data.get('count', 0) + user2_data.get('count', 0),
                'face_data': {
                    'merged_from': [user1_name, user2_name],
                    'user1_data': user1_data.get('face_data', {}),
                    'user2_data': user2_data.get('face_data', {})
                },
                'last_updated': datetime.now().isoformat()
            }
            
            # Remove original users if requested
            if delete_originals:
                self.face_data.pop(user1_name, None)
                self.face_data.pop(user2_name, None)
                
                # Delete original directories
                for user_name in [user1_name, user2_name]:
                    user_dir = os.path.join(self.known_faces_dir, user_name)
                    if os.path.exists(user_dir):
                        shutil.rmtree(user_dir)
                        print(f"🗑️ Deleted original directory: {user_name}")
            
            # Save updated data
            self.save_face_data()
            
            print(f"✅ Successfully merged '{user1_name}' and '{user2_name}' into '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error merging users: {e}")
            return False
    
    def get_user_stats(self, user_name):
        """Get statistics for a specific user"""
        if user_name not in self.face_data:
            return None
        
        user_data = self.face_data[user_name]
        user_dir = os.path.join(self.known_faces_dir, user_name)
        
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
    
    def backup_database(self):
        """Create a backup of the face database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"known_faces_backup_{timestamp}.json"
            
            shutil.copy2(self.known_faces_json, backup_file)
            print(f"✅ Database backed up to: {backup_file}")
            
            # Also backup the entire known_faces directory
            backup_dir = f"known_faces_backup_{timestamp}"
            if os.path.exists(self.known_faces_dir):
                shutil.copytree(self.known_faces_dir, backup_dir)
                print(f"✅ Images backed up to: {backup_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def cleanup_duplicates(self):
        """Find and remove duplicate face images"""
        try:
            duplicates_found = 0
            
            for user_name in self.face_data:
                user_dir = os.path.join(self.known_faces_dir, user_name)
                if not os.path.exists(user_dir):
                    continue
                
                # Get all image files
                image_files = glob.glob(os.path.join(user_dir, "*.jpg")) + \
                              glob.glob(os.path.join(user_dir, "*.jpeg")) + \
                              glob.glob(os.path.join(user_dir, "*.png")) + \
                              glob.glob(os.path.join(user_dir, "*.bmp"))
                
                # Check for duplicates by comparing file contents
                unique_files = []
                duplicates = []
                
                for image_file in image_files:
                    is_duplicate = False
                    for unique_file in unique_files:
                        if os.path.exists(image_file) and os.path.exists(unique_file):
                            # Compare file sizes first (quick check)
                            if os.path.getsize(image_file) == os.path.getsize(unique_file):
                                # Compare file contents (thorough check)
                                with open(image_file, 'rb') as f1, open(unique_file, 'rb') as f2:
                                    if f1.read() == f2.read():
                                        is_duplicate = True
                                        break
                    
                    if not is_duplicate:
                        unique_files.append(image_file)
                    else:
                        duplicates.append(image_file)
                
                # Remove duplicates
                for duplicate in duplicates:
                    os.remove(duplicate)
                    duplicates_found += 1
                    print(f"🗑️ Removed duplicate: {os.path.basename(duplicate)}")
                
                # Update count in face data
                self.face_data[user_name]['count'] = len(unique_files)
            
            if duplicates_found > 0:
                self.save_face_data()
                print(f"✅ Removed {duplicates_found} duplicate images")
            else:
                print("✅ No duplicate images found")
            
            return duplicates_found
            
        except Exception as e:
            print(f"❌ Error cleaning duplicates: {e}")
            return 0
    
    def show_menu(self):
        """Display the management menu"""
        print("\n" + "="*50)
        print("👥 FACE MANAGEMENT SYSTEM")
        print("="*50)
        print("1. List all users")
        print("2. Rename user")
        print("3. Delete user")
        print("4. Merge users")
        print("5. User statistics")
        print("6. Backup database")
        print("7. Clean duplicates")
        print("8. Exit")
        print("="*50)

def main():
    """Main function for face management"""
    manager = FaceManager()
    
    while True:
        manager.show_menu()
        
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                manager.list_all_users()
            
            elif choice == '2':
                users = manager.list_all_users()
                if users:
                    old_name = input("Enter current user name: ").strip()
                    new_name = input("Enter new user name: ").strip()
                    manager.rename_user(old_name, new_name)
            
            elif choice == '3':
                users = manager.list_all_users()
                if users:
                    user_name = input("Enter user name to delete: ").strip()
                    confirm = input(f"Are you sure you want to delete '{user_name}'? (yes/no): ").strip().lower()
                    if confirm in ['yes', 'y']:
                        manager.delete_user(user_name)
            
            elif choice == '4':
                users = manager.list_all_users()
                if len(users) >= 2:
                    print("\nAvailable users:")
                    for i, user in enumerate(users, 1):
                        print(f"{i}. {user}")
                    
                    user1 = input("Enter first user number or name: ").strip()
                    user2 = input("Enter second user number or name: ")
                    
                    # Handle both number and name input
                    try:
                        user1_idx = int(user1) - 1
                        if 0 <= user1_idx < len(users):
                            user1 = users[user1_idx]
                    except:
                        pass
                    
                    try:
                        user2_idx = int(user2) - 1
                        if 0 <= user2_idx < len(users):
                            user2 = users[user2_idx]
                    except:
                        pass
                    
                    new_name = input("Enter merged user name: ").strip()
                    delete_originals = input("Delete original users? (yes/no): ").strip().lower() in ['yes', 'y']
                    
                    manager.merge_users(user1, user2, new_name, delete_originals)
                else:
                    print("❌ Need at least 2 users to merge")
            
            elif choice == '5':
                users = manager.list_all_users()
                if users:
                    user_name = input("Enter user name for statistics: ").strip()
                    stats = manager.get_user_stats(user_name)
                    if stats:
                        print(f"\n📊 Statistics for {stats['name']}:")
                        print(f"  Images: {stats['image_count']}")
                        print(f"  Total Size: {stats['total_size_mb']} MB")
                        print(f"  Last Updated: {stats['last_updated']}")
            
            elif choice == '6':
                manager.backup_database()
            
            elif choice == '7':
                manager.cleanup_duplicates()
            
            elif choice == '8':
                print("👋 Exiting face management system...")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-8.")
        
        except KeyboardInterrupt:
            print("\n👋 Exiting face management system...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
