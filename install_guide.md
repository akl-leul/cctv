# Installation Guide for CCTV Face Detection System

## Python 3.13 Compatibility Issues

Python 3.13 is very new and some packages haven't been updated yet. Here are the solutions:

## Option 1: Use Python 3.11 or 3.12 (Recommended)

The easiest solution is to use a more stable Python version:

1. **Download Python 3.11 or 3.12** from https://www.python.org/downloads/
2. **Uninstall Python 3.13** (optional, but recommended)
3. **Install Python 3.11/3.12** with these options:
   - ✅ Add to PATH
   - ✅ Install for all users

## Option 2: Install Core Packages Only (Python 3.13)

If you must use Python 3.13, install core packages first:

```bash
pip install opencv-python numpy pillow flask flask-socketio python-socketio requests qrcode pyttsx3 pyinstaller
```

Then install optional packages separately:

```bash
# Install these one by one if they fail
pip install streamlit
pip install facenet-pytorch
pip install scipy
pip install scikit-learn
pip install joblib
pip install faster-whisper
pip install TTS
pip install ollama
pip install webrtcvad
pip install pyaudio
pip install pywin32
pip install cryptography
```

## Option 3: Use Conda Environment (Recommended for Python 3.13)

1. **Install Miniconda or Anaconda**
2. **Create a new environment:**
   ```bash
   conda create -n cctv python=3.11
   conda activate cctv
   ```
3. **Install packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start Installation

### For Windows Users (Recommended):

1. **Install Python 3.11:**
   - Go to https://www.python.org/downloads/release/python-3119/
   - Download "Windows installer (64-bit)"
   - Install with "Add to PATH" checked

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python face_manager_gui.py
   ```

### For Python 3.13 Users:

1. **Install core packages:**
   ```bash
   pip install opencv-python numpy pillow flask flask-socketio python-socketio requests qrcode pyttsx3
   ```

2. **Test basic functionality:**
   ```bash
   python face_manager_gui.py
   ```

3. **Add optional packages as needed:**
   ```bash
   pip install streamlit  # For web interface
   pip install facenet-pytorch  # For advanced face recognition
   ```

## Troubleshooting

### Common Issues:

1. **"numpy build wheel failed"**
   - Solution: Use Python 3.11/3.12 or install numpy>=1.26.0

2. **"pkg_resources ImpImporter error"**
   - Solution: This is a Python 3.13 compatibility issue, use Python 3.11/3.12

3. **"Microsoft Visual C++ 14.0 is required"**
   - Solution: Install Visual Studio Build Tools or use conda

4. **"pyaudio installation failed"**
   - Solution: Install from wheel files or use conda

### Alternative Installation Methods:

#### Using pip with --no-build-isolation:
```bash
pip install --no-build-isolation numpy
```

#### Using pre-compiled wheels:
```bash
pip install --only-binary=:all: -r requirements.txt
```

#### Using conda for problematic packages:
```bash
conda install numpy scipy scikit-learn pillow opencv
pip install flask flask-socketio pyttsx3 qrcode
```

## Minimal Working Setup

If you just want to test the basic functionality:

1. **Install minimum requirements:**
   ```bash
   pip install opencv-python numpy pillow flask flask-socketio python-socketio requests qrcode pyttsx3
   ```

2. **Run basic face manager:**
   ```bash
   python face_manager_gui.py
   ```

3. **Test network camera server:**
   ```bash
   python network_camera_server.py
   ```

## Building the Desktop Application

For building the executable, use Python 3.11/3.12:

```bash
python build_app.py
```

This will create:
- `CCTV_Face_Detection_System.exe` - Standalone executable
- `CCTV_Face_Detection_System_Installer.exe` - Windows installer

## Summary

- **Best Option:** Use Python 3.11 or 3.12
- **Possible Option:** Use Python 3.13 with limited packages
- **Advanced Option:** Use conda environment
- **Quick Test:** Install core packages only

The system will work perfectly with Python 3.11/3.12, which are more stable and have better package support.
