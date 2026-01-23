# 👥 Face Manager GUI - Complete Usage Guide

## 🚀 Quick Start

### Running the Application
```bash
# Method 1: Using the launcher (Recommended)
python RUN_GUI.py

# Method 2: Direct execution
python face_manager_gui.py
```

## 📋 System Overview

The Face Manager GUI is a comprehensive face recognition and CCTV management system with the following main components:

### 🎯 Core Features
- **Face Registration**: Capture and register new faces using camera or upload
- **User Management**: Add, delete, rename, and merge user profiles
- **Image Gallery**: View and manage captured face images
- **CCTV System**: Multi-camera surveillance with face detection
- **Network Camera Server**: Connect mobile devices as cameras
- **Data Management**: Backup, cleanup, and statistics

## 🖥️ Interface Layout

### Sidebar (Left Panel)
- **System Status**: Real-time status of CCTV, server, and cameras
- **Core Controls**: Launch/stop CCTV, start server, generate access codes
- **Search**: Filter users by name
- **Database Tools**: Backup, cleanup duplicates, view statistics
- **Theme Toggle**: Switch between dark/light themes

### Main Content Area
- **Live Camera Feeds**: 2x2 grid showing camera feeds
- **Registered Users**: List of all registered users with image counts
- **New User Registration**: Form to add new users
- **Merge Profiles**: Tool to combine duplicate profiles

## 🔧 Feature Usage

### 1. Face Registration

#### Method A: Camera Capture
1. Enter user name in "New User Registration" section
2. Click "📷 Capture Live" button
3. Position face in camera window (face detection overlay will show)
4. Click "📷 Take Snapshot" when ready
5. Review the captured photo
6. Click "✅ Use Photo" to confirm
7. Click "✨ CREATE PROFILE" to complete registration

#### Method B: Image Upload
1. Enter user name
2. Click "📂 Upload Photo"
3. Select image file from computer
4. Click "✨ CREATE PROFILE"

### 2. Image Gallery

#### Opening Gallery
1. Select a user from the "Registered Users" list
2. Click "🖼️ Gallery" button

#### Gallery Features
- **Navigation**: Use "⇠ Previous" and "Next ⇢" buttons
- **Deletion**: Click "🗑️ Delete Photo" to remove current image
- **Information**: Shows current image position and total count

### 3. CCTV System

#### Starting CCTV
1. Click "🚀 Launch CCTV" in sidebar
2. System will initialize up to 4 cameras:
   - Local Cam 1 & 2: Built-in/USB cameras
   - Network Cam 1 & 2: Mobile device cameras

#### Camera Controls
- **Switch Cameras**: Use "⇠ Previous" and "Next ⇢" buttons
- **Status Display**: Shows active camera count
- **Face Detection**: Real-time face detection with green boxes

#### Stopping CCTV
- Click "🛑 Stop All" to stop all cameras

### 4. Network Camera Server

#### Starting Server
1. Click "🌐 Start Server" in sidebar
2. Server starts on port 5000
3. Status shows "Network Server: Running"

#### Connecting Mobile Devices
1. Click "🔑 Access Code" button
2. QR code and connection URL will be displayed
3. On mobile device:
   - Open the connection URL
   - Allow camera permissions
   - Click "Start Camera"
4. Mobile camera will appear in CCTV grid

#### Server Status
- Click "📊 Statistics" to see connected cameras
- Monitor active connections in real-time

### 5. User Management

#### Viewing User Details
1. Select user from list
2. View stats in info panel:
   - Profile name
   - Image count
   - Storage size
   - Last updated

#### Renaming Users
1. Select user from list
2. Click "✏️ Rename" button
3. Enter new name and confirm

#### Deleting Users
1. Select user from list
2. Click "🗑️ Delete" button
3. Confirm deletion (this removes all images)

#### Merging Profiles
1. Select primary user from list
2. Choose merge target from dropdown
3. Enter new merged profile name
4. Check "Delete Originals" if desired
5. Click "Merge" button

### 6. Database Tools

#### Backup
1. Click "📦 Backup" in sidebar
2. Creates timestamped backup of all data
3. Includes JSON database and image directories

#### Cleanup Duplicates
1. Click "🧹 Cleanup" in sidebar
2. Scans for and removes duplicate images
3. Shows count of removed duplicates

#### Statistics
1. Click "📊 Statistics" in sidebar
2. View:
   - Total profiles count
   - Total face samples
   - Selected user details
   - Storage usage

## 🔍 Search and Filter

### Using Search
1. Type in search box in sidebar
2. User list filters in real-time
3. Case-insensitive partial matching
4. Shows matching users with image counts

## 🎨 Theme Customization

### Dark/Light Theme
1. Use "🌙 Dark" checkbox in sidebar
2. Instantly switches between themes
3. Preference is saved for next session

## 📱 Mobile Camera Integration

### Requirements
- Both devices on same WiFi network
- Mobile device with camera and web browser

### Connection Process
1. Start network server
2. Generate access code
3. Scan QR code or open URL on mobile
4. Grant camera permissions
5. Start streaming

### Troubleshooting Mobile Connection
- Ensure both devices on same network
- Check firewall settings on server
- Verify camera permissions on mobile
- Try refreshing mobile browser

## 🚨 Troubleshooting

### Camera Issues
- **Camera not available**: Check camera permissions and connections
- **No face detected**: Ensure good lighting and face clearly visible
- **Camera freezes**: Restart CCTV system

### Server Issues
- **Server won't start**: Check if port 5000 is available
- **Mobile can't connect**: Verify same WiFi network
- **QR code not working**: Manually enter connection URL

### Performance Issues
- **Slow response**: Close unused applications
- **High CPU usage**: Reduce camera resolution or FPS
- **Memory issues**: Use cleanup tool regularly

## 💾 Data Management

### File Locations
- **Face Images**: `known_faces/[username]/`
- **Database**: `known_faces.json`
- **CCTV Recordings**: `cctv_recordings/`
- **Network Cameras**: `network_cameras/`
- **Access Codes**: `access_codes/`

### Backup Strategy
1. Regular backups using built-in tool
2. Copy `known_faces/` directory and `.json` file
3. Store backups on separate drive/cloud

## 🔐 Security Considerations

- Face data stored locally (not cloud-based)
- Network server uses temporary access codes
- QR codes expire after 24 hours
- No data transmitted externally

## 📞 Support

### Common Issues
1. **Dependencies Missing**: Run `pip install -r requirements.txt`
2. **Camera Permission**: Allow camera access in system settings
3. **Firewall Blocking**: Allow Python through Windows Firewall
4. **Antivirus Issues**: Add exception for application folder

### Performance Tips
- Use SSD for better performance
- Ensure adequate RAM (8GB+ recommended)
- Keep graphics drivers updated
- Close unnecessary background applications

---

**Version**: 3.0.1 Stable  
**Last Updated**: 2026-01-23  
**Compatibility**: Windows 10/11  
**Requirements**: Python 3.8+, Camera, 8GB RAM recommended
