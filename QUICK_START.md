# 🚀 Face Manager Web Application - Quick Start Guide

## 📋 Prerequisites
- Python 3.9+ (3.13 compatible)
- Webcam (for face registration)
- Internet connection

## ⚡ Quick Start (3 Commands)

### 1. Install Dependencies
```bash
pip install flask opencv-python pillow numpy werkzeug
```

### 2. Run Application
```bash
python run_production.py
```

### 3. Access Web Application
- **URL**: http://localhost:5000
- **Login**: admin / admin123

## 🎯 Features Available

### ✅ **Core Features**
- **User Authentication** - Secure login system
- **Face Registration** - Register users with webcam
- **User Management** - View and manage registered users
- **CCTV System** - Real-time camera monitoring
- **Face Detection** - Automatic face detection in camera feeds

### 🔧 **Web Interface**
- **Modern Dashboard** - Bootstrap 5 responsive design
- **Mobile Friendly** - Works on phones and tablets
- **Real-time Updates** - Live camera feeds
- **User Gallery** - View registered face images

## 📱 **How to Use**

### 1. **Login to System**
- Open http://localhost:5000
- Login with: **admin** / **admin123**

### 2. **Register New Users**
- Click "Register New User" button
- Enter username
- Click "Start Camera" to enable webcam
- Click "Capture" to take face photo
- Click "Register User" to save

### 3. **View Users**
- All registered users appear in the dashboard
- Click "View" to see user details and images
- See image count and registration date

### 4. **Start CCTV System**
- Click "Start CCTV" button (admin only)
- View live camera feeds with face detection
- Green boxes indicate detected faces
- Click "Stop CCTV" to stop monitoring

## 🌐 **Production Deployment**

### **Option 1: Local Server**
```bash
# Set production environment
set FLASK_ENV=production
set SECRET_KEY=your-secure-secret-key

# Run production server
python run_production.py
```

### **Option 2: Docker (Recommended)**
```bash
# Build and run with Docker
docker-compose up -d
```

### **Option 3: Cloud Hosting**
- **Heroku**: Ready for Heroku deployment
- **AWS EC2**: Use deployment guide
- **DigitalOcean**: Optimized for DO

## 🔒 **Security Features**

### **Built-in Security**
- **Password Hashing** - Secure password storage
- **Session Management** - Secure user sessions
- **Input Validation** - Protection against attacks
- **SQL Injection Protection** - Safe database queries

### **Production Security**
- **Environment Variables** - Secure configuration
- **HTTPS Support** - SSL/TLS encryption ready
- **Role-based Access** - Admin/User permissions
- **Session Timeout** - Automatic logout

## 📊 **System Requirements**

### **Minimum Requirements**
- **CPU**: 2+ cores
- **RAM**: 4GB+
- **Storage**: 10GB+
- **OS**: Windows/Linux/macOS

### **Recommended Requirements**
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **OS**: Linux (Ubuntu 20.04+)

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Install missing packages
pip install flask opencv-python pillow numpy werkzeug
```

#### **2. Camera Not Working**
- Check webcam permissions
- Ensure webcam is not used by other applications
- Try different browser (Chrome, Firefox)

#### **3. Database Errors**
```bash
# Delete and recreate database
del users.db
python run_production.py
```

#### **4. Port Already in Use**
```bash
# Use different port
set PORT=5001
python run_production.py
```

## 📞 **Getting Help**

### **Documentation**
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `README.md` - Project documentation

### **Support**
- Check console logs for error messages
- Verify all dependencies are installed
- Ensure webcam permissions are correct

---

## 🎉 **Ready to Host!**

Your Face Manager web application is now **production-ready** with:
- ✅ **Secure authentication system**
- ✅ **Modern web interface**
- ✅ **Face recognition capabilities**
- ✅ **CCTV monitoring**
- ✅ **Mobile responsive design**
- ✅ **Production security features**

**Start hosting now!** 🚀
