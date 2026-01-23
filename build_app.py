#!/usr/bin/env python3
"""
Desktop Application Builder for CCTV Face Detection System
Creates executable and installer for Windows
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cctv_detector.py', 'face_manager_gui.py', 'face_data_manager.py', 'enhanced_cctv_detector.py', 'network_camera_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('haarcascades', 'haarcascades'),
        ('templates', 'templates'),
        ('known_faces', 'known_faces'),
        ('cctv_recordings', 'cctv_recordings'),
        ('access_codes', 'access_codes'),
    ],
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'tkinter',
        'threading',
        'json',
        'datetime',
        'os',
        'time',
        'socket',
        'requests',
        'base64',
        'io',
        'hashlib',
        'secrets',
        'qrcode',
        'flask',
        'flask_socketio',
        'python_socketio',
        'pyttsx3',
        'scipy',
        'sklearn',
        'joblib',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=[],
    name='CCTV_Face_Detection_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    upx_include=[],
)

"""
    
    with open('CCTV_Face_Detection_System.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def create_icon():
    """Create application icon"""
    try:
        # Create a simple icon using PIL
        from PIL import Image, ImageDraw
        
        # Create a simple icon
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a camera icon
        draw.rectangle([50, 80, 206, 176], fill=(255, 255, 255, 255))
        draw.rectangle([60, 90, 196, 166], fill=(0, 0, 0, 255))
        
        # Draw lens
        draw.ellipse([80, 110, 176, 146], fill=(100, 100, 100, 255))
        draw.ellipse([90, 120, 166, 136], fill=(0, 0, 0, 0))
        
        # Draw flash
        draw.polygon([(128, 90), (138, 110), (128, 130), (118, 110)], fill=(255, 255, 0, 255))
        
        img.save('icon.ico')
        print("✅ Created application icon")
        
    except ImportError:
        print("⚠️ PIL not available, skipping icon creation")
    except Exception as e:
        print(f"⚠️ Error creating icon: {e}")

def create_installer_script():
    """Create NSIS installer script for Windows"""
    nsis_script = """
; NSIS installer script for CCTV Face Detection System

!define APPNAME "CCTV Face Detection System"
!define VERSION "1.0.0"
!define PUBLISHER "CCTV Systems"
!define URL "https://github.com/cctv-face-detection"

; Include Modern UI
!include "MUI2.nsh"
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; General settings
Name "${APPNAME}"
OutFile "CCTV_Face_Detection_System_Installer.exe"
InstallDir "$PROGRAMFILES\\${APPNAME}"
InstallDirRegKey "Software\\${APPNAME}"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Version information
VIProductVersion "${VERSION}"
VIAddVersionKey /V "${VERSION}" "${PUBLISHER}" "${APPNAME}"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; License page
!insertmacro MUI_PAGE_LICENSE
LicenseData "License Agreement"
LicenseText "This software is provided as-is without warranty. By installing this software, you agree to the terms of use."

; Components page
!insertmacro MUI_PAGE_COMPONENTS
Section "Core Components" SecCore
    SectionIn RO "Required files (do not remove)" SecCore
        SetOutPath "$INSTDIR"
        File "CCTV_Face_Detection_System.exe"
        File /r "haarcascades"
        File /r "templates"
        File /r "icon.ico"
    SectionEnd
SectionEnd

; Create shortcuts
Section "Shortcuts" SecShortcuts
    CreateShortCut "$INSTDIR\\CCTV_Face_Detection_System.exe" "$DESKTOP\\${APPNAME}.lnk"
    CreateShortCut "$INSTDIR\\CCTV_Face_Detection_System.exe" "$SMPROGRAMS\\${APPNAME}.lnk"
SectionEnd

; Registry entries for file associations
Section "File Associations" SecFileAssoc
    WriteRegStr HKCR ".jpg" "" "JPEG Image"
    WriteRegStr HKCR ".jpg\\OpenWithProgids" "CCTV_Face_Detection_System.exe" 0
    WriteRegStr HKCR "CCTV_Face_Detection_System.exe\\shell\\open\\command" "" '"$INSTDIR\\CCTV_Face_Detection_System.exe" "%1"'
SectionEnd

; Uninstaller
Section "Uninstall"
    DeleteRegKey HKCR ".jpg\\OpenWithProgids" "CCTV_Face_Detection_System.exe"
    DeleteRegKey HKCR "CCTV_Face_Detection_System.exe"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\\${APPNAME}.lnk"
SectionEnd
"""
    
    with open('installer.nsi', 'w') as f:
        f.write(nsis_script)
    
    print("✅ Created NSIS installer script")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    try:
        # Find OpenCV haarcascades directory
        import cv2
        haarcascades_path = cv2.data.haarcascades
        print(f"📁 Using OpenCV haarcascades from: {haarcascades_path}")
        
        # Run PyInstaller
        subprocess.run([
            'pyinstaller',
            '--clean',
            '--onefile',
            '--windowed',
            '--icon=icon.ico',
            '--name=CCTV_Face_Detection_System',
            f'--add-data={haarcascades_path}:haarcascades',
            '--add-data=templates:templates',
            '--add-data=known_faces:known_faces',
            '--add-data=cctv_recordings:cctv_recordings',
            '--add-data=access_codes:access_codes',
            '--hidden-import=cv2',
            '--hidden-import=PIL',
            '--hidden-import=tkinter',
            '--hidden-import=sklearn',
            '--hidden-import=joblib',
            '--hidden-import=pyttsx3',
            '--hidden-import=qrcode',
            '--hidden-import=flask',
            '--hidden-import=flask_socketio',
            '--hidden-import=socketio',
            '--hidden-import=requests',
            '--hidden-import=numpy',
            'face_manager_gui.py'
        ], check=True)
        
        print("✅ Executable built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building executable: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def build_installer():
    """Build the installer using NSIS"""
    print("📦 Building installer...")
    
    try:
        # Check if makensis is available
        subprocess.run(['makensis', 'installer.nsi'], check=True)
        print("✅ Installer built successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building installer: {e}")
        print("💡 Please install NSIS from: https://nsis.sourceforge.net/")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_startup_script():
    """Create startup script"""
    startup_script = """@echo off
title CCTV Face Detection System
echo Starting CCTV Face Detection System...
echo.

REM Check if executable exists
if not exist "CCTV_Face_Detection_System.exe" (
    echo Error: CCTV_Face_Detection_System.exe not found!
    echo Please run build_app.py first to create the executable.
    pause
    exit /b 1
)

REM Run the application
CCTV_Face_Detection_System.exe

REM If the application exits with error code, pause to see the error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    pause
)
"""
    
    with open('start_cctv.bat', 'w') as f:
        f.write(startup_script)
    
    print("✅ Created startup script: start_cctv.bat")

def create_readme():
    """Create README file"""
    readme_content = """# CCTV Face Detection System

## Overview
A comprehensive face detection and recognition system with both local and network camera support.

## Features
- Real-time face detection and recognition
- Network camera support (mobile phone cameras)
- Voice alerts for unknown faces
- Image gallery and user management
- Desktop application with installer
- Web-based camera connection interface

## Installation

### Option 1: Download Pre-built Installer
1. Download `CCTV_Face_Detection_System_Installer.exe`
2. Run the installer as administrator
3. Follow the installation wizard

### Option 2: Build from Source
1. Install Python 3.8 or higher
2. Install dependencies: `pip install -r requirements.txt`
3. Run build script: `python build_app.py`
4. Run executable: `CCTV_Face_Detection_System.exe`

## Usage

### Desktop Application
1. Launch the application from Start Menu or desktop shortcut
2. Use the GUI to manage users and launch CCTV detection
3. Add users through camera capture or image upload
4. Launch CCTV system for real-time monitoring

### Network Camera Setup
1. Start the network camera server: `python network_camera_server.py`
2. Generate access codes through the web interface
3. Scan QR code with mobile device
4. Mobile camera will stream to the desktop application

## Network Camera Connection

### From Mobile Device
1. Open the generated QR code URL in mobile browser
2. Allow camera permissions when prompted
3. Click "Start Camera" to begin streaming
4. Camera will automatically connect to CCTV system

### Requirements
- Mobile device with camera
- Same WiFi network as desktop computer
- Modern web browser (Chrome, Firefox, Safari)

## File Structure
```
CCTV_Face_Detection_System/
├── cctv_detector.py          # Main detection engine
├── face_manager_gui.py       # GUI interface
├── face_data_manager.py      # Data management
├── enhanced_cctv_detector.py  # Enhanced with network support
├── network_camera_server.py   # Network camera server
├── haarcascades/              # Face detection models
├── templates/                # Web interface templates
├── known_faces/              # User face database
├── cctv_recordings/          # Video recordings
└── access_codes/              # Generated QR codes
```

## Troubleshooting

### Camera Issues
- Ensure camera is not in use by other applications
- Check camera permissions
- Try different camera indices (0, 1, 2)
- Restart the application if camera fails

### Network Camera Issues
- Verify both devices are on same WiFi network
- Check firewall settings
- Ensure network camera server is running
- Verify access code is valid and not expired

### Performance Issues
- Close other applications using camera
- Reduce video resolution if needed
- Check system resources

## Security Notes
- Access codes expire after 24 hours by default
- Network connections are encrypted
- Local face data is stored securely
- No data is transmitted to external servers

## Support
For issues and support, please check the console output and log files in the application directory.
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Created README.md")

def main():
    """Main build function"""
    print("🚀 Building CCTV Face Detection System Desktop Application")
    print("=" * 60)
    
    # Create necessary files
    create_spec_file()
    create_icon()
    create_installer_script()
    create_startup_script()
    create_readme()
    
    # Build executable
    if build_executable():
        print("\n📦 Building installer...")
        build_installer()
    
    print("\n✅ Build process completed!")
    print("\n📂 Files created:")
    print("  - CCTV_Face_Detection_System.exe (executable)")
    print("  - start_cctv.bat (startup script)")
    print("  - README.md (documentation)")
    print("  - installer.nsi (installer script)")
    if os.path.exists('icon.ico'):
        print("  - icon.ico (application icon)")
    
    print("\n🎯 To run the application:")
    print("  1. Double-click CCTV_Face_Detection_System.exe")
    print("  2. Or run: start_cctv.bat")

if __name__ == "__main__":
    main()
