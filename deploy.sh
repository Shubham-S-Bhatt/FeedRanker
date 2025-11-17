#!/bin/bash
# FeedRanker VPS Deployment Script for Ubuntu 22.04
# Usage: sudo bash deploy.sh yourdomain.com

set -e

DOMAIN=${1:-"localhost"}
APP_DIR="/var/www/feedranker"
REPO_URL="https://github.com/Shubham-S-Bhatt/FeedRanker.git"

echo "============================================"
echo "FeedRanker VPS Deployment Setup"
echo "Domain: $DOMAIN"
echo "============================================"

# 1. Update system
echo "[1/10] Updating system packages..."
apt update && apt upgrade -y

# 2. Install dependencies
echo "[2/10] Installing dependencies..."
apt install -y \
  python3 python3-pip python3-venv \
  nodejs npm \
  nginx \
  postgresql postgresql-contrib \
  git \
  curl \
  wget \
  build-essential \
  libpq-dev

# 3. Create app directory
echo "[3/10] Setting up application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# 4. Clone repository
echo "[4/10] Cloning repository..."
if [ ! -d ".git" ]; then
    git clone $REPO_URL .
else
    git pull origin main
fi

# 5. Setup Python environment
echo "[5/10] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 6. Setup PostgreSQL
echo "[6/10] Setting up PostgreSQL database..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql << 'EOF'
CREATE DATABASE IF NOT EXISTS feedranker;
CREATE USER IF NOT EXISTS feedranker WITH PASSWORD 'feedranker_default_password';
ALTER ROLE feedranker SET client_encoding TO 'utf8';
ALTER ROLE feedranker SET default_transaction_isolation TO 'read committed';
ALTER ROLE feedranker SET default_transaction_deferrable TO on;
ALTER ROLE feedranker SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE feedranker TO feedranker;
EOF

# 7. Create environment files
echo "[7/10] Creating environment files..."
mkdir -p $APP_DIR/backend
cat > $APP_DIR/backend/.env << EOF
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
GRPC_HOST=localhost:50051
DATABASE_URL=postgresql://feedranker:feedranker_default_password@localhost:5432/feedranker
CORS_ORIGINS=http://localhost,https://$DOMAIN
EOF

# 8. Build frontend
echo "[8/10] Building frontend..."
cd $APP_DIR/frontend
npm install
npm run build

# 9. Setup services
echo "[9/10] Setting up systemd services..."

# gRPC service
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

# Backend service
cat > /etc/systemd/system/feedranker-backend.service << EOF
[Unit]
Description=FeedRanker Backend API
After=network.target feedranker-grpc.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn -b 127.0.0.1:8000 -w 4 -k uvicorn.workers.UvicornWorker main:app
Restart=always
RestartSec=10
StandardOutput=append:/var/log/feedranker/backend.log
StandardError=append:/var/log/feedranker/backend.log

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
mkdir -p /var/log/feedranker
touch /var/log/feedranker/grpc.log
touch /var/log/feedranker/backend.log

# Enable and start services
systemctl daemon-reload
systemctl enable feedranker-grpc
systemctl enable feedranker-backend
systemctl start feedranker-grpc
systemctl start feedranker-backend

# 10. Configure Nginx
echo "[10/10] Configuring Nginx..."
cat > /etc/nginx/sites-available/feedranker << EOF
upstream feedranker_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 100M;

    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        expires 1h;
    }

    location /api/ {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location ~ ^/(rank|health|status|metrics|docs) {
        proxy_pass http://feedranker_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    access_log /var/log/nginx/feedranker_access.log;
    error_log /var/log/nginx/feedranker_error.log;
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/feedranker /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Setup firewall
echo "============================================"
echo "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "📋 Next Steps:"
echo "1. Update domain in DNS to point to this VPS"
echo "2. Setup SSL: sudo certbot certonly --nginx -d $DOMAIN"
echo "3. Update backend/.env with secure password"
echo "4. Check services: systemctl status feedranker-backend"
echo ""
echo "🌐 Access your app at:"
echo "   http://$DOMAIN"
echo ""
echo "📊 API Documentation:"
echo "   http://$DOMAIN/docs"
echo ""
echo "🔍 Health Check:"
echo "   curl http://$DOMAIN/health"
echo ""
echo "============================================"
