#!/bin/bash
# setup.sh - Complete environment setup for K2Think API
# Sets up venv, installs dependencies, configures files
# Does NOT start the server - use start.sh for that

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "🔧 K2Think API - Environment Setup"
echo "===================================="
echo ""

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found!"
    exit 1
fi
python3 --version
log_success "Python 3 is available"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv || {
        log_warning "Failed to create venv, trying with --system-site-packages"
        python3 -m venv --system-site-packages venv
    }
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi
echo ""

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
log_info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
log_success "Dependencies installed"
echo ""

# Create data directory
log_info "Setting up data directory..."
mkdir -p data
log_success "Data directory ready"
echo ""

# Create empty data/tokens.txt if it doesn't exist (avoid '[]' which is treated as a bogus token)
if [ ! -f "data/tokens.txt" ]; then
    log_info "Creating data/tokens.txt file..."
    echo "# Tokens will be auto-generated" > data/tokens.txt
    log_success "data/tokens.txt created (will be populated by auto-update)"
else
    log_success "data/tokens.txt already exists"
fi
echo ""

# Handle credentials for accounts.txt
if [ ! -f "accounts.txt" ]; then
    log_info "Setting up K2 credentials..."
    
    # Try environment variables first
    if [ ! -z "${K2_EMAIL:-}" ] && [ ! -z "${K2_PASSWORD:-}" ]; then
        log_success "Using credentials from environment variables"
        echo "{\"email\": \"$K2_EMAIL\", \"password\": \"$K2_PASSWORD\"}" > accounts.txt
        log_success "accounts.txt created with environment credentials"
    else
        # Interactive prompt
        echo ""
        echo "🔑 K2 Account Credentials Required"
        echo "===================================="
        echo "Enter your K2 credentials (or press Ctrl+C to skip):"
        echo ""
        
        read -p "📧 Email: " user_email
        read -sp "🔒 Password: " user_password
        echo ""
        echo ""
        
        if [ ! -z "$user_email" ] && [ ! -z "$user_password" ]; then
            echo "{\"email\": \"$user_email\", \"password\": \"$user_password\"}" > accounts.txt
            log_success "accounts.txt created with your credentials"
            export K2_EMAIL="$user_email"
            export K2_PASSWORD="$user_password"
        else
            log_warning "Skipped credential input"
            log_info "You can create accounts.txt manually later:"
            echo '   Format: {"email": "your@email.com", "password": "yourpassword"}'
        fi
    fi
else
    log_success "accounts.txt already exists"
fi
echo ""

# Create .env file
if [ ! -f ".env" ]; then
    log_info "Creating .env configuration file..."
    TIMESTAMP=$(date +%s)
    
    # Check if accounts.txt exists to determine auto-update setting
    AUTO_UPDATE="false"
    if [ -f "accounts.txt" ]; then
        AUTO_UPDATE="true"
    fi
    
    cat > .env << EOF
# API Authentication
VALID_API_KEY=sk-k2think-proxy-$TIMESTAMP

# Set to true to accept any API key (recommended for local development)
ALLOW_ANY_API_KEY=true

# Server Configuration  
# PORT can be overridden by SERVER_PORT environment variable at runtime
PORT=${SERVER_PORT:-7000}

# Token Management
# Set to true if you have accounts.txt with K2 credentials
ENABLE_TOKEN_AUTO_UPDATE=$AUTO_UPDATE

# Unified token file path
TOKENS_FILE=data/tokens.txt

# Optional: Proxy settings (if needed)
# HTTP_PROXY=http://proxy:port
# HTTPS_PROXY=https://proxy:port
EOF
    log_success ".env file created (ENABLE_TOKEN_AUTO_UPDATE=$AUTO_UPDATE)"
else
    log_success ".env file already exists"
fi
echo ""

# Verify OpenAI package installation
log_info "Verifying OpenAI package..."
python3 -c "import openai" 2>/dev/null || {
    log_info "Installing openai package..."
    pip install -q openai
}
log_success "OpenAI package is installed"
echo ""

# Display summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║           ✅ SETUP COMPLETE! ✅                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
log_success "Environment is ready!"
echo ""
echo "📋 What was configured:"
echo "   • Virtual environment (venv)"
echo "   • Python dependencies"
echo "   • Configuration files (.env)"
if [ -f "accounts.txt" ]; then
    echo "   • K2 credentials (accounts.txt)"
fi
echo ""
echo "🚀 Next steps:"
echo "   • Start server: bash scripts/start.sh"
echo "   • Test API:     bash scripts/send_request.sh"
echo "   • Do everything: bash scripts/all.sh"
echo ""

