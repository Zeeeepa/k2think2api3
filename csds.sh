#!/bin/bash
# CSDS: Clone, Setup, Deploy, and Send request
# One-command deployment and testing for K2Think API Proxy

set -e

REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
PROJECT_DIR="k2think2api3"
BRANCH="${1:-main}"  # Use provided branch or default to main

echo "🚀 K2Think API - One-Command Deployment (CSDS)"
echo "==============================================="
echo "📌 Branch: $BRANCH"
echo ""

# Clone (if not already cloned)
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory exists, updating..."
    cd "$PROJECT_DIR"
    
    # Fetch latest changes
    git fetch origin
    
    # Checkout the specified branch
    echo "🔀 Checking out branch: $BRANCH"
    git checkout "$BRANCH" || {
        echo "⚠️  Could not checkout branch $BRANCH, trying to create from remote"
        git checkout -b "$BRANCH" "origin/$BRANCH" || {
            echo "❌ Failed to checkout branch $BRANCH"
            exit 1
        }
    }
    
    # Pull latest changes
    git pull origin "$BRANCH" || echo "⚠️  Could not pull updates, continuing with existing code"
else
    echo "📦 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Checkout the specified branch if not main
    if [ "$BRANCH" != "main" ]; then
        echo "🔀 Checking out branch: $BRANCH"
        git checkout "$BRANCH" || {
            echo "⚠️  Branch $BRANCH not found, trying remote"
            git checkout -b "$BRANCH" "origin/$BRANCH" || {
                echo "❌ Failed to checkout branch $BRANCH"
                exit 1
            }
        }
    fi
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
