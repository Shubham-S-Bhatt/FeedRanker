#!/bin/bash
# FeedRanker Update Script - Run this to pull latest changes and restart services

set -e

APP_DIR="/var/www/feedranker"

echo "============================================"
echo "FeedRanker Update Script"
echo "============================================"

cd $APP_DIR

echo "[1/5] Pulling latest changes..."
git pull origin main

echo "[2/5] Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "[3/5] Updating frontend..."
cd frontend
npm install
npm run build
cd ..

echo "[4/5] Restarting services..."
systemctl restart feedranker-backend
systemctl restart feedranker-grpc

echo "[5/5] Waiting for services to start..."
sleep 3

echo ""
echo "✅ Update Complete!"
echo ""
echo "Service Status:"
systemctl status feedranker-backend --no-pager
systemctl status feedranker-grpc --no-pager
echo ""
echo "============================================"
