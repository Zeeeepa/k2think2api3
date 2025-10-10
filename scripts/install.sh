#!/bin/bash
# K2Think API - Foolproof Installer
# This installer ALWAYS works, regardless of URL format used

set -e

echo "🚀 K2Think API - Foolproof Installer"
echo "========================================"
echo ""

# Check if we need credentials
if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
    echo "📧 Please enter your K2 credentials:"
    read -p "Email: " K2_EMAIL
    read -sp "Password: " K2_PASSWORD
    echo ""
    echo ""
fi

# Validate credentials
if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
    echo "❌ Error: Email and password are required!"
    echo ""
    echo "Usage:"
    echo "  Method 1: With environment variables"
    echo "    export K2_EMAIL=\"your@email.com\""
    echo "    export K2_PASSWORD=\"yourpassword\""
    echo "    bash install.sh"
    echo ""
    echo "  Method 2: Interactive (script will prompt)"
    echo "    bash install.sh"
    echo ""
    exit 1
fi

# Export for use by other scripts
export K2_EMAIL
export K2_PASSWORD

PROJECT_DIR="$HOME/k2think2api3"

echo "📦 Setting up K2Think API Proxy..."
echo ""

# Clone or update repository
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory exists, updating..."
    cd "$PROJECT_DIR"
    git fetch origin
    git checkout main
    git pull origin main
else
    echo "📥 Cloning repository..."
    cd "$HOME"
    git clone https://github.com/Zeeeepa/k2think2api3.git
    cd "$PROJECT_DIR"
fi

echo ""
echo "🔧 Running setup..."
chmod +x setup.sh deploy.sh send_request.sh
bash setup.sh

echo ""
echo "🚀 Starting server..."
bash deploy.sh

echo ""
echo "✅ Installation Complete!"
echo ""
echo "📊 Server Status:"
echo "   URL: http://localhost:7000"
echo "   Logs: tail -f $PROJECT_DIR/server.log"
echo "   Stop: kill \$(cat $PROJECT_DIR/.server.pid)"
echo ""

# Get API key
if [ -f "$PROJECT_DIR/.env" ]; then
    API_KEY=$(grep VALID_API_KEY "$PROJECT_DIR/.env" | cut -d'=' -f2)
    if [ ! -z "$API_KEY" ]; then
        echo "🔑 Your API Key:"
        echo "   $API_KEY"
        echo ""
        echo "🔗 Environment Variables (copy to use):"
        echo "   export OPENAI_API_KEY=\"$API_KEY\""
        echo "   export OPENAI_BASE_URL=\"http://localhost:7000/v1\""
        echo ""
    fi
fi

echo "🧪 Testing the API..."
echo ""
bash send_request.sh

echo ""
echo "🎉 All done! Your K2Think API proxy is running!"
echo ""

