# Face Manager Web Application - Production Deployment Guide

## 🚀 Overview

This guide covers deploying the Face Manager web application for production use, including local deployment, cloud deployment, and Docker deployment options.

## 📋 Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ SSD
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.9+
- **Webcam**: USB or IP cameras for CCTV functionality

### Software Dependencies
- PostgreSQL (production database)
- Redis (session storage and caching)
- Nginx (reverse proxy, optional)
- Docker & Docker Compose (for containerized deployment)

## 🛠️ Installation Steps

### 1. Clone and Setup Repository

```bash
git clone <your-repository-url>
cd face-manager
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Critical settings to update:**
- `SECRET_KEY`: Generate a secure random key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `FACES_DIR`: Path to face images directory

### 4. Database Setup

#### PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE face_manager;
CREATE USER face_manager_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE face_manager TO face_manager_user;
\q
```

#### Redis Setup
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 5. Initialize Application

```bash
# Create necessary directories
mkdir -p faces models logs

# Initialize database (creates admin user)
python web_app.py
```

## 🐳 Docker Deployment (Recommended)

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Docker Configuration Files

The deployment includes:
- `Dockerfile`: Application container configuration
- `docker-compose.yml`: Multi-service orchestration
- `.env`: Environment variables

### Production Docker Commands

```bash
# Build image
docker build -t face-manager:latest .

# Run with environment variables
docker run -d \
  --name face-manager \
  -p 5000:5000 \
  -e DATABASE_URL=$DATABASE_URL \
  -e REDIS_URL=$REDIS_URL \
  -e SECRET_KEY=$SECRET_KEY \
  -v $(pwd)/faces:/app/faces \
  face-manager:latest
```

## 🌐 Cloud Deployment Options

### 1. Heroku Deployment

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create face-manager-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=postgresql://...
heroku config:set REDIS_URL=redis://...

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 2. AWS EC2 Deployment

```bash
# Launch EC2 instance (Ubuntu 20.04)
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository and deploy
git clone <your-repository-url>
cd face-manager
docker-compose up -d
```

### 3. DigitalOcean Deployment

```bash
# Create Droplet with Docker pre-installed
# SSH into Droplet
# Follow same steps as AWS EC2 deployment
```

## 🔧 Nginx Reverse Proxy Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream face_manager {
        server 127.0.0.1:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://face_manager;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /socket.io {
            proxy_pass http://face_manager;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

## 🔒 Security Considerations

### 1. SSL/TLS Configuration
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 2. Firewall Setup
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Application Security
- Use strong `SECRET_KEY`
- Enable HTTPS in production
- Regular security updates
- Monitor application logs
- Implement rate limiting

## 📊 Monitoring and Logging

### 1. Application Logs
```bash
# View application logs
tail -f logs/face_manager.log

# View Gunicorn logs
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log
```

### 2. System Monitoring
```bash
# Monitor system resources
htop
df -h
free -h
```

### 3. Database Monitoring
```bash
# Monitor PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
redis-cli info
```

## 🚀 Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

### 2. Redis Configuration
```bash
# Edit redis.conf
sudo nano /etc/redis/redis.conf

# Set max memory
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 3. Application Tuning
- Adjust Gunicorn worker count
- Enable connection pooling
- Implement caching strategies
- Use CDN for static assets

## 🔄 Backup and Recovery

### 1. Database Backup
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump face_manager > $BACKUP_DIR/face_manager_$DATE.sql
```

### 2. File System Backup
```bash
# Backup faces directory
rsync -av /path/to/faces/ /backup/faces/
```

### 3. Automated Backup
```bash
# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U face_manager_user -d face_manager
   ```

2. **Redis Connection Error**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Test connection
   redis-cli ping
   ```

3. **Camera Access Issues**
   ```bash
   # Check camera permissions
   ls -l /dev/video*
   
   # Add user to video group
   sudo usermod -a -G video $USER
   ```

4. **High Memory Usage**
   ```bash
   # Monitor memory usage
   free -h
   htop
   
   # Restart services if needed
   docker-compose restart web
   ```

## 📱 Mobile Access

The web application is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Android Chrome)
- Tablets (iPad, Android tablets)

## 🎯 Production Checklist

Before going live, ensure:

- [ ] Environment variables configured
- [ ] Database created and migrated
- [ ] Redis server running
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backup strategy in place
- [ ] Monitoring setup
- [ ] Load testing performed
- [ ] Security audit completed
- [ ] Documentation updated

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment configuration
3. Test database connectivity
4. Review system resources
5. Consult troubleshooting section

---

**Note**: This deployment guide assumes you have administrative access to the deployment environment. Adjust configurations based on your specific requirements and infrastructure.
