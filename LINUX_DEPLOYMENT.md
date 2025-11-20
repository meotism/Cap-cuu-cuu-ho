# SOS Emergency Map Server - Linux Deployment Guide

## 🚀 Quick Start

### 1. Basic Development Server
```bash
chmod +x start_server.sh
./start_server.sh
```

### 2. Production Server (with Gunicorn)
```bash
chmod +x start_production.sh
./start_production.sh
```

### 3. Stop Server
```bash
chmod +x stop_server.sh
./stop_server.sh
```

## 📋 Prerequisites

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### CentOS/RHEL
```bash
sudo yum install -y python3 python3-pip
```

### Arch Linux
```bash
sudo pacman -S python python-pip
```

## 🔧 Installation Steps

### 1. Clone/Upload Project
```bash
cd /opt
sudo git clone <your-repo> sos-emergency-server
cd sos-emergency-server
```

### 2. Set Permissions
```bash
chmod +x *.sh
```

### 3. Run Installation
```bash
./start_server.sh
```

## 🏭 Production Deployment

### Option 1: Systemd Service (Recommended)

#### Install Service
```bash
sudo ./install_service.sh
```

#### Manage Service
```bash
# Start
sudo systemctl start sos-emergency-server

# Stop
sudo systemctl stop sos-emergency-server

# Restart
sudo systemctl restart sos-emergency-server

# Status
sudo systemctl status sos-emergency-server

# Enable auto-start on boot
sudo systemctl enable sos-emergency-server

# View logs
sudo journalctl -u sos-emergency-server -f
```

### Option 2: Production Server with Gunicorn

```bash
# Start with custom port
PORT=8080 ./start_production.sh

# Start with custom workers
WORKERS=8 ./start_production.sh

# Start with custom host
HOST=192.168.1.100 PORT=8080 ./start_production.sh
```

### Option 3: Docker (Create Dockerfile)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn eventlet

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", \
     "--bind", "0.0.0.0:5000", "map_server:app"]
```

Build and run:
```bash
docker build -t sos-emergency-server .
docker run -d -p 5000:5000 --name sos-server sos-emergency-server
```

## 🌐 Nginx Reverse Proxy

### Install Nginx
```bash
sudo apt install nginx
```

### Configure Nginx
Create `/etc/nginx/sites-available/sos-emergency`:

```nginx
upstream sos_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://sos_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://sos_backend/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/sos-emergency /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 Security (Firewall)

### UFW (Ubuntu/Debian)
```bash
sudo ufw allow 5000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Firewalld (CentOS/RHEL)
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📊 Monitoring

### Check Server Status
```bash
# Check if server is running
ps aux | grep map_server

# Check port
netstat -tlnp | grep 5000

# Check logs
tail -f logs/server.log
```

### System Resource Usage
```bash
# CPU and Memory
top -p $(pgrep -f map_server.py)

# Disk usage
df -h
du -sh map_data/
```

## 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Restart service
sudo systemctl restart sos-emergency-server

# Or restart manual server
./stop_server.sh
./start_server.sh
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
sudo lsof -i :5000
sudo kill <PID>
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/sos-emergency-server
chmod +x *.sh
```

### Database Issues
```bash
# Backup database
cp map_data/sos_posts.db map_data/sos_posts.db.backup

# Reset database (delete and restart server)
rm map_data/sos_posts.db
sudo systemctl restart sos-emergency-server
```

### Python Dependencies
```bash
# Reinstall dependencies
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

## 📝 Environment Variables

Create `.env` file:
```bash
FLASK_ENV=production
PORT=5000
HOST=0.0.0.0
SECRET_KEY=your-secret-key-here
DATABASE_PATH=./map_data/sos_posts.db
```

## 🔐 SSL/HTTPS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## 📦 Backup Strategy

### Daily Backup Script
Create `/opt/backup-sos.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backup/sos-emergency"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /opt/sos-emergency-server/map_data/sos_posts.db \
   $BACKUP_DIR/sos_posts_${DATE}.db

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

Add to crontab:
```bash
sudo crontab -e
0 2 * * * /opt/backup-sos.sh
```

## 🌍 Access from External Network

1. **Find your server IP:**
   ```bash
   hostname -I
   ```

2. **Update firewall** (allow external access)

3. **Update HTML files** - Change WebSocket URL:
   ```javascript
   const socket = io('http://YOUR_SERVER_IP:5000');
   ```

## 📞 Support

- Check logs: `sudo journalctl -u sos-emergency-server -f`
- Server status: `sudo systemctl status sos-emergency-server`
- Test API: `curl http://localhost:5000/api/health`
