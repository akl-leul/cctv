# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['face_manager_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\hp\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\cv2\\data\\', 'haarcascades'), ('templates', 'templates'), ('known_faces', 'known_faces'), ('cctv_recordings', 'cctv_recordings'), ('access_codes', 'access_codes')],
    hiddenimports=['cv2', 'PIL', 'tkinter', 'sklearn', 'joblib', 'pyttsx3', 'qrcode', 'flask', 'flask_socketio', 'socketio', 'requests', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CCTV_Face_Detection_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
