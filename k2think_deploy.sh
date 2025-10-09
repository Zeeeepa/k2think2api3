#!/bin/bash
set -e

# ============================================
# K2Think API Proxy - One-Command Deployment Script
# OpenAI-Compatible K2-Think Model Proxy
# ============================================

BRANCH="${1:-main}"
REPO="https://github.com/Zeeeepa/k2think2api3.git"
INSTALL_DIR="k2think2api3"

echo "🚀 Starting K2Think API Proxy Deployment..."
echo "📦 Branch: $BRANCH"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Clone repository
echo ""
echo "📥 Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory $INSTALL_DIR already exists. Removing..."
    rm -rf "$INSTALL_DIR"
fi

git clone --depth 1 -b "$BRANCH" "$REPO" "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "✅ Repository cloned successfully"

# Create virtual environment
echo ""
echo "🔧 Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "✅ Virtual environment created"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo "✅ Dependencies installed successfully"

# Setup environment configuration
echo ""
echo "⚙️  Setting up environment configuration..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    
    # Configure default settings for quick start
    cat >> .env << 'EOF'

# Quick Start Configuration (Added by deployment script)
PORT=7000
DEBUG_LOGGING=false
ENABLE_TOKEN_AUTO_UPDATE=false
EOF
    
    echo ""
    echo "⚠️  IMPORTANT: Token configuration required!"
    echo ""
    echo "   Choose ONE of these methods:"
    echo "   1. Manual token management (Quick start):"
    echo "      echo 'your-k2think-token-here' > tokens.txt"
    echo ""
    echo "   2. Automated token updates (Recommended for production):"
    echo "      • Create accounts.txt with K2Think account credentials"
    echo "      • Set ENABLE_TOKEN_AUTO_UPDATE=true in .env"
    echo "      • See CREDENTIAL_SETUP.md for detailed instructions"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Create placeholder tokens file
if [ ! -f tokens.txt ]; then
    echo "placeholder_token_change_me" > tokens.txt
    echo "⚠️  Created placeholder tokens.txt - Replace with real token!"
fi

# Create start script
echo ""
echo "📝 Creating start script..."
cat > start_server.sh << 'EOFSTART'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
exec python3 k2think_proxy.py
EOFSTART
chmod +x start_server.sh

echo "✅ Start script created"

# Create systemd service file (optional)
cat > k2think-api.service << 'EOFSERVICE'
[Unit]
Description=K2Think API Proxy - OpenAI-Compatible K2-Think Model Proxy
After=network.target

[Service]
Type=simple
User=%USER%
WorkingDirectory=%WORKDIR%
ExecStart=%WORKDIR%/start_server.sh
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOFSERVICE

# Replace placeholders in service file
sed -i "s|%USER%|$USER|g" k2think-api.service
sed -i "s|%WORKDIR%|$(pwd)|g" k2think-api.service

echo "✅ Systemd service file created (k2think-api.service)"

# Print deployment summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🎉 K2Think API Proxy Deployed Successfully! 🎉         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Installation Directory: $(pwd)"
echo "🌐 Default Server URL: http://localhost:7000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Configure your K2Think tokens:"
echo ""
echo "   🎯 Quick Start (Manual tokens):"
echo "   --------------------------------"
echo "   echo 'your-k2think-token-here' > tokens.txt"
echo ""
echo "   🔄 Production Setup (Auto-update):"
echo "   -----------------------------------"
echo "   • Create accounts.txt with your K2Think credentials:"
echo "     {\"email\": \"your@email.com\", \"k2_password\": \"password\"}"
echo "   • Edit .env and set:"
echo "     ENABLE_TOKEN_AUTO_UPDATE=true"
echo "     TOKEN_UPDATE_INTERVAL=86400  # 24 hours"
echo "   • See CREDENTIAL_SETUP.md for detailed guide"
echo ""
echo "2️⃣  Start the server:"
echo "   ./start_server.sh"
echo ""
echo "   Or run in background:"
echo "   nohup ./start_server.sh > server.log 2>&1 &"
echo ""
echo "3️⃣  Test the API:"
echo "   curl http://localhost:7000/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 OPTIONAL: Install as systemd service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   sudo cp k2think-api.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable k2think-api"
echo "   sudo systemctl start k2think-api"
echo "   sudo systemctl status k2think-api"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 USEFUL COMMANDS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View logs:       tail -f server.log"
echo "Stop server:     pkill -f 'python3 k2think_proxy.py'"
echo "Restart:         ./start_server.sh"
echo "Health check:    curl http://localhost:7000/health"
echo "Token stats:     curl http://localhost:7000/admin/tokens/stats"
echo "Manual refresh:  curl -X POST http://localhost:7000/admin/tokens/reload"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentation & Features:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• Token Management:      Auto-rotation, failure detection, self-healing"
echo "• Admin API:             /admin/tokens/* for monitoring & management"
echo "• OpenAI Compatible:     Full OpenAI SDK support"
echo "• Streaming Support:     Real-time response streaming"
echo "• Tool Calling:          OpenAI Function Calling support"
echo "• File Upload:           Image and document upload support"
echo ""
echo "Full docs: https://github.com/Zeeeepa/k2think2api3"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 OpenAI-Compatible Endpoint: http://localhost:7000/v1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Example usage with OpenAI SDK:"
echo "   --------------------------------"
echo "   from openai import OpenAI"
echo ""
echo "   client = OpenAI("
echo "       api_key='sk-k2think-proxy-test',"
echo "       base_url='http://localhost:7000/v1'"
echo "   )"
echo ""
echo "   response = client.chat.completions.create("
echo "       model='MBZUAI-IFM/K2-Think',"
echo "       messages=[{"
echo "           'role': 'user',"
echo "           'content': 'Hello! What is your model name?'"
echo "       }]"
echo "   )"
echo ""
echo "   print(response.choices[0].message.content)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 Advanced Features:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• Smart Token Pool:      Automatic load balancing across multiple tokens"
echo "• Failure Recovery:      Auto-disable failed tokens, self-healing"
echo "• Consecutive Failures:  Auto-refresh when 2+ tokens fail consecutively"
echo "• Token Auto-Update:     Zero-downtime token refresh from accounts.txt"
echo "• Admin Dashboard:       Real-time monitoring via /admin endpoints"
echo "• Proxy Support:         HTTP/HTTPS proxy configuration for China users"
echo ""
echo "✨ Happy coding!"
echo ""

