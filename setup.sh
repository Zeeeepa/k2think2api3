#!/bin/bash
set -e

echo "🚀 K2Think API Proxy - Setup Script"
echo "===================================="

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found!"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv || {
        echo "⚠️  Failed to create venv, trying with --system-site-packages"
        python3 -m venv --system-site-packages venv
    }
fi

# Activate virtual environment
echo "✨ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Setup accounts file if K2 credentials are available
if [ ! -z "$K2_EMAIL" ] && [ ! -z "$K2_PASSWORD" ]; then
    echo "🔑 Creating accounts.txt from environment variables..."
    echo "{\"email\": \"$K2_EMAIL\", \"k2_password\": \"$K2_PASSWORD\"}" > accounts.txt
    echo "✅ accounts.txt created"
else
    if [ ! -f "accounts.txt" ]; then
        echo "⚠️  No K2_EMAIL/K2_PASSWORD env vars found"
        echo "📝 Please create accounts.txt manually:"
        echo '   {"email": "your@email.com", "k2_password": "yourpassword"}'
    fi
fi

# Create .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env configuration file..."
    TIMESTAMP=$(date +%s)
    
    # Check if accounts.txt exists to determine auto-update setting
    AUTO_UPDATE="false"
    if [ -f "accounts.txt" ]; then
        AUTO_UPDATE="true"
    fi
    
    cat > .env << EOF
# API Authentication
VALID_API_KEY=sk-k2think-proxy-$TIMESTAMP

# Server Configuration  
PORT=7000

# Token Management
# Set to true if you have accounts.txt with K2 credentials
ENABLE_TOKEN_AUTO_UPDATE=$AUTO_UPDATE

# Optional: Proxy settings (if needed)
# HTTP_PROXY=http://proxy:port
# HTTPS_PROXY=https://proxy:port
EOF
    echo "✅ .env file created (ENABLE_TOKEN_AUTO_UPDATE=$AUTO_UPDATE)"
else
    echo "ℹ️  .env file already exists"
fi

# Check if OpenAI package is installed
echo "🔍 Checking OpenAI package..."
python3 -c "import openai" 2>/dev/null || {
    echo "📦 Installing openai package for testing..."
    pip install openai
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Run ./deploy.sh to start the server"
echo "   2. Run ./send_request.sh to test the API"
echo ""
echo "💡 Optional: Enable K2 credentials auto-update"
echo "   1. Create accounts.txt with format: {\"email\": \"your@email.com\", \"k2_password\": \"yourpassword\"}"
echo "   2. Edit .env and set ENABLE_TOKEN_AUTO_UPDATE=true"
echo "   3. Restart the server with ./deploy.sh"
