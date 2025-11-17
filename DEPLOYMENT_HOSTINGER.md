# 🚀 Deploy FeedRanker on Hostinger VPS with Nginx + Gunicorn

Complete guide to deploy the FeedRanker application on a Hostinger VPS using Nginx as reverse proxy and Gunicorn as WSGI server.

---

## 📋 Prerequisites

- Hostinger VPS with Ubuntu 22.04 LTS (or similar)
- SSH access to your VPS
- Domain name (optional, for production)
- Basic Linux knowledge

---

## 🔧 Step 1: Initial VPS Setup

### Connect to your VPS
```bash
ssh root@your_vps_ip
```

### Update system packages
```bash
apt update && apt upgrade -y
```

### Install required packages
```bash
apt install -y \
  python3 python3-pip python3-venv \
  nodejs npm \
  nginx \
  postgresql postgresql-contrib \
  git \
  supervisor \
  curl \
  wget \
  build-essential \
  libpq-dev
```

### Verify installations
```bash
python3 --version
node --version
npm --version
nginx -v
postgresql --version
```

---

## 📁 Step 2: Clone Repository and Setup

### Create application directory
```bash
mkdir -p /var/www/feedranker
cd /var/www/feedranker
```

### Clone your repository
```bash
git clone https://github.com/Shubham-S-Bhatt/FeedRanker.git .
```

### Create Python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Python dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### Create backend environment file
```bash
cat > backend/.env << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
GRPC_HOST=localhost:50051
DATABASE_URL=postgresql://feedranker:password@localhost:5432/feedranker
CORS_ORIGINS=http://localhost,https://yourdomain.com
EOF
```

**Important:** Change `password` and `yourdomain.com` to your values!

---

## 🐘 Step 3: Setup PostgreSQL Database

### Start PostgreSQL
```bash
systemctl start postgresql
systemctl enable postgresql
```

### Create database and user
```bash
sudo -u postgres psql << 'EOF'
CREATE DATABASE feedranker;
CREATE USER feedranker WITH PASSWORD 'password';
ALTER ROLE feedranker SET client_encoding TO 'utf8';
ALTER ROLE feedranker SET default_transaction_isolation TO 'read committed';
ALTER ROLE feedranker SET default_transaction_deferrable TO on;
ALTER ROLE feedranker SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE feedranker TO feedranker;
\q
EOF
```

### Verify connection
```bash
psql -U feedranker -d feedranker -h localhost
```

---

## 🎨 Step 4: Build Frontend

### Navigate to frontend directory
```bash
cd /var/www/feedranker/frontend
```

### Install dependencies
```bash
npm install
```

### Build for production
```bash
npm run build
```

### Verify build output
```bash
ls -la dist/
```

---

## 🔧 Step 5: Configure Gunicorn

### Create Gunicorn configuration
```bash
cat > /var/www/feedranker/gunicorn_config.py << 'EOF'
import multiprocessing
import os

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 2
access_log = "/var/log/feedranker/access.log"
error_log = "/var/log/feedranker/error.log"
loglevel = "info"
EOF
```

### Create log directory
```bash
mkdir -p /var/log/feedranker
touch /var/log/feedranker/access.log
touch /var/log/feedranker/error.log
```

---

## ⚙️ Step 6: Setup Supervisor for Services

### Create systemd service for gRPC Server

```bash
cat > /etc/systemd/system/feedranker-grpc.service << 'EOF'
[Unit]
Description=FeedRanker gRPC Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/feedranker
ExecStart=/var/www/feedranker/venv/bin/python /var/www/feedranker/grpc_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/feedranker/grpc.log
StandardError=append:/var/log/feedranker/grpc.log

[Install]
WantedBy=multi-user.target
EOF
```

### Create systemd service for Backend

```bash
cat > /etc/systemd/system/feedranker-backend.service << 'EOF'
[Unit]
Description=FeedRanker Backend API
After=network.target feedranker-grpc.service

[Service]
Type=notify
User=root
WorkingDirectory=/var/www/feedranker/backend
Environment="PATH=/var/www/feedranker/venv/bin"
ExecStart=/var/www/feedranker/venv/bin/gunicorn \
    --config /var/www/feedranker/gunicorn_config.py \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    main:app
Restart=always
RestartSec=10
StandardOutput=append:/var/log/feedranker/backend.log
StandardError=append:/var/log/feedranker/backend.log

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and start services
```bash
systemctl daemon-reload
systemctl enable feedranker-grpc
systemctl enable feedranker-backend
systemctl start feedranker-grpc
systemctl start feedranker-backend
```

### Check service status
```bash
systemctl status feedranker-grpc
systemctl status feedranker-backend
```

---

## 🌐 Step 7: Configure Nginx

### Create Nginx configuration
```bash
cat > /etc/nginx/sites-available/feedranker << 'EOF'
upstream feedranker_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS (optional)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 100M;

    # Frontend - Serve static files
    location / {
        root /var/www/feedranker/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API routes - Proxy to Gunicorn
    location /api/ {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Direct API routes (without /api/ prefix)
    location ~ ^/(rank|health|status|metrics|docs) {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Logs
    access_log /var/log/nginx/feedranker_access.log;
    error_log /var/log/nginx/feedranker_error.log;
}
EOF
```

### Enable Nginx site
```bash
ln -s /etc/nginx/sites-available/feedranker /etc/nginx/sites-enabled/
```

### Test Nginx configuration
```bash
nginx -t
```

### Restart Nginx
```bash
systemctl restart nginx
```

---

## 🔒 Step 8: Setup SSL Certificate (Optional but Recommended)

### Install Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### Generate SSL certificate
```bash
certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### Update Nginx for HTTPS
```bash
cat > /etc/nginx/sites-available/feedranker << 'EOF'
upstream feedranker_backend {
    server 127.0.0.1:8000;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    # Frontend
    location / {
        root /var/www/feedranker/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API routes
    location /api/ {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location ~ ^/(rank|health|status|metrics|docs) {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    access_log /var/log/nginx/feedranker_access.log;
    error_log /var/log/nginx/feedranker_error.log;
}
EOF
```

### Test and restart Nginx
```bash
nginx -t
systemctl restart nginx
```

### Auto-renew SSL certificates
```bash
systemctl enable certbot.timer
systemctl start certbot.timer
```

---

## ✅ Step 9: Verify Deployment

### Check service status
```bash
systemctl status feedranker-grpc
systemctl status feedranker-backend
systemctl status nginx
```

### View logs
```bash
# Backend logs
tail -f /var/log/feedranker/backend.log

# gRPC logs
tail -f /var/log/feedranker/grpc.log

# Nginx logs
tail -f /var/log/nginx/feedranker_error.log
```

### Test endpoints
```bash
# Health check
curl http://yourdomain.com/health

# API docs
curl http://yourdomain.com/docs

# Ranking endpoint
curl -X POST http://yourdomain.com/rank \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "item_ids": ["item_1", "item_2"],
    "context_features": {"impressions": 10, "avg_hour": 14}
  }'
```

---

## 📊 Step 10: Monitor and Maintain

### View service logs
```bash
# Real-time backend logs
journalctl -u feedranker-backend -f

# Real-time gRPC logs
journalctl -u feedranker-grpc -f
```

### Restart services
```bash
systemctl restart feedranker-backend
systemctl restart feedranker-grpc
```

### Update application
```bash
cd /var/www/feedranker
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build
systemctl restart feedranker-backend
```

### Monitor resource usage
```bash
top -u root | grep feedranker
```

---

## 🐛 Troubleshooting

### Connection refused on localhost:8000
```bash
# Check Gunicorn is running
ps aux | grep gunicorn

# Check port 8000
netstat -tulpn | grep 8000

# Restart service
systemctl restart feedranker-backend
```

### Nginx 502 Bad Gateway
```bash
# Check backend logs
journalctl -u feedranker-backend -n 50

# Check Nginx logs
tail -f /var/log/nginx/feedranker_error.log

# Verify Gunicorn socket
curl http://127.0.0.1:8000/health
```

### gRPC connection failed
```bash
# Check gRPC server running
ps aux | grep grpc_server

# Check port 50051
netstat -tulpn | grep 50051

# Restart gRPC
systemctl restart feedranker-grpc
```

### Database connection error
```bash
# Test PostgreSQL connection
psql -U feedranker -d feedranker -h localhost

# Check backend .env
cat backend/.env | grep DATABASE_URL

# Verify PostgreSQL is running
systemctl status postgresql
```

---

## 🔐 Security Best Practices

### 1. Firewall setup
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. Fail2Ban for DDoS protection
```bash
apt install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### 3. Regular backups
```bash
# Backup database
pg_dump -U feedranker feedranker > feedranker_backup.sql

# Backup application
tar -czf feedranker_backup.tar.gz /var/www/feedranker
```

### 4. Update regularly
```bash
apt update && apt upgrade -y
```

---

## 📈 Performance Optimization

### Tune Gunicorn workers
```bash
# In gunicorn_config.py
workers = (2 × CPU_cores) + 1
```

### Enable Nginx caching
```bash
# Add to Nginx server block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;
proxy_cache api_cache;
proxy_cache_valid 200 1h;
```

### Database optimization
```bash
# Create indexes
sudo -u postgres psql feedranker << 'EOF'
CREATE INDEX idx_ranking_requests_user_id ON ranking_requests(user_id);
CREATE INDEX idx_ranking_metrics_created_at ON ranking_metrics(created_at);
\q
EOF
```

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Shubham-S-Bhatt/FeedRanker/issues)
- **Documentation**: See [README.md](../README.md)
- **Email**: shubhamsatyaprakashbhatt@gmail.com

---

Happy Deploying! 🚀
