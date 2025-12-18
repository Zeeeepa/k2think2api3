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

# Function to prompt for K2Think credentials
prompt_for_credentials() {
    echo ""
    echo "🔐 K2Think Account Setup"
    echo "=========================="
    echo ""
    echo "To use this API proxy, you need a K2Think account."
    echo "If you don't have one, sign up at: https://www.k2think.ai/"
    echo ""
    
    # Prompt for email
    read -p "📧 Enter your K2Think email: " K2_EMAIL
    
    # Prompt for password (show input as requested)
    echo "🔑 Enter your K2Think password (input will be visible):"
    read -p "Password: " K2_PASSWORD
    
    echo ""
    echo "💾 Saving credentials to accounts.txt..."
    echo "{\"email\": \"$K2_EMAIL\", \"k2_password\": \"$K2_PASSWORD\"}" > accounts.txt
    echo "✅ Credentials saved!"
    echo ""
}

# Setup accounts file
if [ ! -f "accounts.txt" ]; then
    # Check if credentials are in environment variables
    if [ ! -z "$K2_EMAIL" ] && [ ! -z "$K2_PASSWORD" ]; then
        echo "🔑 Creating accounts.txt from environment variables..."
        echo "{\"email\": \"$K2_EMAIL\", \"k2_password\": \"$K2_PASSWORD\"}" > accounts.txt
        echo "✅ accounts.txt created"
    else
        # No accounts.txt and no env vars - prompt user
        echo ""
        echo "⚠️  No K2Think credentials found!"
        echo ""
        read -p "Would you like to enter your credentials now? (y/n): " response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            prompt_for_credentials
        else
            echo ""
            echo "⏭️  Skipping credential setup."
            echo "📝 You can create accounts.txt manually later:"
            echo '   {"email": "your@email.com", "k2_password": "yourpassword"}'
            echo ""
            echo "⚠️  Note: The server will NOT start without valid credentials!"
            echo ""
        fi
    fi
else
    echo "✅ accounts.txt already exists"
    
    # Validate the existing file
    if grep -q "your@email.com\|yourpassword" accounts.txt 2>/dev/null; then
        echo ""
        echo "⚠️  Warning: accounts.txt contains placeholder credentials!"
        echo ""
        read -p "Would you like to update with real credentials? (y/n): " response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            prompt_for_credentials
        fi
    fi
fi

# Create .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env configuration file..."
    TIMESTAMP=$(date +%s)
    cat > .env << EOF
# API Authentication
VALID_API_KEY=sk-k2think-proxy-$TIMESTAMP

# Server Configuration  
PORT=7000

# Token Management
ENABLE_TOKEN_AUTO_UPDATE=true

# Optional: Proxy settings (if needed)
# HTTP_PROXY=http://proxy:port
# HTTPS_PROXY=https://proxy:port
EOF
    echo "✅ .env file created"
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
echo "   1. Edit accounts.txt if needed (add K2 credentials)"
echo "   2. Run ./deploy.sh to start the server"
echo "   3. Run ./send_request.sh to test the API"
