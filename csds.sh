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
chmod +x setup.sh deploy.sh send_request.sh

# Handle K2 credentials
if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
    if [ ! -f "accounts.txt" ]; then
        echo ""
        echo "🔑 K2 Account Setup Required"
        echo "================================"
        echo "Please enter your K2 credentials:"
        echo ""
        
        read -p "📧 Email login: " K2_EMAIL
        read -sp "🔒 Password: " K2_PASSWORD
        echo ""
        
        if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
            echo "❌ Error: Email and password are required!"
            exit 1
        fi
        
        # Export for setup script
        export K2_EMAIL
        export K2_PASSWORD
    fi
fi

bash setup.sh

echo ""
echo "🎯 Starting server..."
bash deploy.sh

echo ""
echo "⏳ Waiting for server to be fully ready..."
sleep 3

echo ""
echo "📤 Sending test request..."
echo ""
bash send_request.sh

echo ""
echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""

# Extract and export API key
if [ -f ".env" ]; then
    API_KEY=$(grep VALID_API_KEY .env | cut -d'=' -f2)
    if [ ! -z "$API_KEY" ]; then
        export OPENAI_API_KEY="$API_KEY"
        export OPENAI_BASE_URL="http://localhost:7000/v1"
        echo "🔑 API Key exported as environment variables:"
        echo "   export OPENAI_API_KEY=\"$API_KEY\""
        echo "   export OPENAI_BASE_URL=\"http://localhost:7000/v1\""
        echo ""
    fi
fi

echo "🌐 Server is running at: http://localhost:7000"
echo "📊 View logs: tail -f $PROJECT_DIR/server.log"
echo "🛑 Stop server: kill \$(cat $PROJECT_DIR/.server.pid)"
echo ""
echo "💡 To use in your current shell, run:"
echo "   source <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/codegen-bot/fix-deployment-auto-update-issue-f8d7be41/export_env.sh)"
echo ""
echo "🔥 Server will continue running in the background"
echo ""
