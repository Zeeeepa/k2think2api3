#!/bin/bash
# CSDS: Clone, Setup, Deploy, and Send request
# One-command deployment and testing for K2Think API Proxy

set -e

REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
PROJECT_DIR="k2think2api3"

echo "🚀 K2Think API - One-Command Deployment (CSDS)"
echo "==============================================="
echo ""

# Clone (if not already cloned)
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory exists, pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull origin main || echo "⚠️  Could not pull updates, continuing with existing code"
else
    echo "📦 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo ""
echo "✨ Running setup..."
./setup.sh

echo ""
echo "🎯 Starting server..."
./deploy.sh

echo ""
echo "⏳ Waiting for server to be fully ready..."
sleep 3

echo ""
echo "📤 Sending test request..."
echo ""
./send_request.sh

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "🌐 Server is running at: http://localhost:7000"
echo "📊 View logs: tail -f $PROJECT_DIR/server.log"
echo "🛑 Stop server: kill \$(cat $PROJECT_DIR/.server.pid)"
echo ""
echo "🔥 Server will continue running in the background"
echo ""

