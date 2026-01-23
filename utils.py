import torch
import os
import joblib
from facenet_pytorch import MTCNN, InceptionResnetV1
from faster_whisper import WhisperModel

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: TTS not available. Text-to-speech functionality will be disabled.")

def load_models():
    print("🔄 Loading face recognition models...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(image_size=160, margin=20, device=device)
    print("✅ MTCNN loaded")
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    print("✅ FaceNet loaded")
    
    # Check if face model exists
    if not os.path.exists('face_model.pkl'):
        print("⚠️ Face model not found. Please run 'python train_faces.py' first to train the model.")
        return None, None, None, None, None, None
    
    data = joblib.load('face_model.pkl')
    print("✅ Face classifier loaded")
    
    # Use float32 instead of float16 to avoid compatibility issues
    print("🔄 Loading Whisper model (this may take a moment)...")
    device_type = "cuda" if torch.cuda.is_available() else "cpu"
    whisper = WhisperModel("small", device=device_type, compute_type="float32")
    print("✅ Whisper loaded")
    
    if TTS_AVAILABLE:
        print("🔄 Loading TTS model...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ TTS loaded")
    else:
        tts = None
        print("⚠️ TTS not available")
    
    print("✅ All models loaded successfully!")
    return mtcnn, resnet, data['classifier'], data['encoder'], whisper, tts
