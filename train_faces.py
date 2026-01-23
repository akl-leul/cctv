import os
import torch
from PIL import Image
import cv2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
import joblib
import time

def capture_faces_for_person(person_name, num_images=20):
    """Capture face images from webcam for a person"""
    person_folder = os.path.join('known_faces', person_name)
    os.makedirs(person_folder, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return False
    
    print(f"📸 Capturing {num_images} images for {person_name}")
    print("Press SPACE to capture, 'q' to quit")
    
    captured_count = 0
    last_capture_time = 0
    
    while captured_count < num_images:
        ret, frame = cap.read()
        if not ret:
            break
            
        cv2.imshow(f'Capture faces for {person_name} ({captured_count}/{num_images})', frame)
        
        current_time = time.time()
        key = cv2.waitKey(1) & 0xFF
        
        # Auto-capture every 2 seconds or on spacebar
        if (key == ord(' ') or (current_time - last_capture_time > 2)) and current_time - last_capture_time > 0.5:
            img_path = os.path.join(person_folder, f'face_{captured_count:03d}.jpg')
            cv2.imwrite(img_path, frame)
            captured_count += 1
            last_capture_time = current_time
            print(f"✅ Captured image {captured_count}/{num_images}")
        
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if captured_count >= num_images:
        print(f"✅ Successfully captured {captured_count} images for {person_name}")
        return True
    else:
        print(f"⚠️ Only captured {captured_count} images (need {num_images})")
        return captured_count > 0

def add_new_person():
    """Interactive function to add a new person"""
    print("\n=== Add New Person ===")
    person_name = input("Enter person's name: ").strip()
    
    if not person_name:
        print("❌ Name cannot be empty")
        return False
    
    return capture_faces_for_person(person_name)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, margin=20, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

known_encodings = []
known_labels = []

if not os.path.exists('known_faces'):
    os.makedirs('known_faces')

# Check if there are any existing faces
has_faces = False
for user_folder in os.listdir('known_faces'):
    user_path = os.path.join('known_faces', user_folder)
    if os.path.isdir(user_path) and os.listdir(user_path):
        has_faces = True
        break

# If no faces found, offer to capture some
if not has_faces:
    print("🔍 No existing face images found!")
    choice = input("Would you like to capture face images now? (y/n): ").strip().lower()
    if choice == 'y':
        if add_new_person():
            has_faces = True
        else:
            print("❌ No face images captured. Exiting.")
            exit()
    else:
        print("❌ No face images available. Please add images manually or capture them.")
        exit()

# Process all face images
known_encodings = []
known_labels = []

for user_folder in os.listdir('known_faces'):
    user_path = os.path.join('known_faces', user_folder)
    if os.path.isdir(user_path):
        image_files = [f for f in os.listdir(user_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"📁 Processing {len(image_files)} images for {user_folder}")
        
        for img_file in image_files:
            img_path = os.path.join(user_path, img_file)
            try:
                img = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                face = mtcnn(img)
                if face is not None:
                    embedding = resnet(face.unsqueeze(0)).detach().cpu().numpy().flatten()
                    known_encodings.append(embedding)
                    known_labels.append(user_folder)
                else:
                    print(f"⚠️ No face detected in {img_file}")
            except Exception as e:
                print(f"❌ Error processing {img_file}: {e}")

if len(known_encodings) == 0:
    print("❌ No faces detected! Please check:")
    print("1. Create 'known_faces/user_name/' folders")
    print("2. Add 20+ face images each (.jpg/png)")
    print("3. Ensure images contain clear, visible faces")
    exit()

if len(set(known_labels)) < 2:
    print("❌ Need at least 2 different people for face recognition!")
    print("Currently have:", len(set(known_labels)), "person(s)")
    print("Please add face images for another person.")
    
    # Offer to add another person
    choice = input("Would you like to add another person? (y/n): ").strip().lower()
    if choice == 'y':
        if add_new_person():
            # Re-process images to include the new person
            known_encodings = []
            known_labels = []
            for user_folder in os.listdir('known_faces'):
                user_path = os.path.join('known_faces', user_folder)
                if os.path.isdir(user_path):
                    image_files = [f for f in os.listdir(user_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    print(f"📁 Processing {len(image_files)} images for {user_folder}")
                    
                    for img_file in image_files:
                        img_path = os.path.join(user_path, img_file)
                        try:
                            img = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
                            img = Image.fromarray(img)
                            face = mtcnn(img)
                            if face is not None:
                                embedding = resnet(face.unsqueeze(0)).detach().cpu().numpy().flatten()
                                known_encodings.append(embedding)
                                known_labels.append(user_folder)
                        except Exception as e:
                            print(f"❌ Error processing {img_file}: {e}")
        else:
            print("❌ No additional person added. Exiting.")
            exit()
    else:
        print("❌ Need at least 2 people for face recognition. Exiting.")
        exit()

print(f"✅ Found {len(known_encodings)} face embeddings from {len(set(known_labels))} people")

le = LabelEncoder()
le.fit(known_labels)
labels_encoded = le.transform(known_labels)
clf = SVC(probability=True, kernel='rbf')
clf.fit(known_encodings, labels_encoded)

joblib.dump({'classifier': clf, 'encoder': le}, 'face_model.pkl')
print("✅ Face model saved: face_model.pkl")
