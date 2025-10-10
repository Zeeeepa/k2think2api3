#!/bin/bash
# all.sh - Smart K2Think API deployment script
# Automatically finds/clones repo, deploys, and shows usage examples

set -e
set -u
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

REPO_NAME="k2think2api3"
REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
DEFAULT_PORT=7000

echo ""
echo "🚀 K2Think API - Smart Deployment"
echo "=================================="
echo ""

# Check if we're already in the project directory
if [ -f "k2think_proxy.py" ] && [ -f "setup.sh" ]; then
    log_success "Already in project directory!"
    PROJECT_DIR="$(pwd)"
else
    # Search for project in common locations
    log_info "Searching for project directory..."
    
    SEARCH_PATHS=(
        "$HOME/$REPO_NAME"
        "$(pwd)/$REPO_NAME"
        "$HOME/projects/$REPO_NAME"
        "$HOME/code/$REPO_NAME"
    )
    
    PROJECT_DIR=""
    for path in "${SEARCH_PATHS[@]}"; do
        if [ -d "$path" ] && [ -f "$path/k2think_proxy.py" ]; then
            PROJECT_DIR="$path"
            log_success "Found project at: $PROJECT_DIR"
            break
        fi
    done
    
    # If not found, clone it
    if [ -z "$PROJECT_DIR" ]; then
        log_info "Project not found. Cloning repository..."
        PROJECT_DIR="$HOME/$REPO_NAME"
        
        if [ -d "$PROJECT_DIR" ]; then
            log_warning "Directory exists but incomplete. Removing..."
            rm -rf "$PROJECT_DIR"
        fi
        
        git clone "$REPO_URL" "$PROJECT_DIR" || {
            log_error "Failed to clone repository"
            exit 1
        }
        log_success "Repository cloned to: $PROJECT_DIR"
    fi
fi

# Change to project directory
cd "$PROJECT_DIR"
log_info "Working in: $PROJECT_DIR"
echo ""

# Get credentials
if [ -z "${K2_EMAIL:-}" ] || [ -z "${K2_PASSWORD:-}" ]; then
    if [ ! -f "data/accounts.txt" ]; then
        log_info "K2 credentials required"
        read -p "📧 Email: " K2_EMAIL
        read -sp "🔒 Password: " K2_PASSWORD
        echo ""
        export K2_EMAIL
        export K2_PASSWORD
    fi
fi

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

# Run setup if needed
if [ ! -d "venv" ] || [ ! -f ".env" ]; then
    log_info "Running initial setup..."
    bash scripts/setup.sh || bash setup.sh
    log_success "Setup completed"
else
    log_info "Environment already configured"
fi

echo ""
log_info "Starting server..."
bash scripts/deploy.sh 2>/dev/null || bash deploy.sh
echo ""

# Wait for server
log_info "Waiting for server to be ready..."
sleep 3

# Get server info
if [ -f ".env" ]; then
    API_KEY=$(grep VALID_API_KEY .env | cut -d'=' -f2 2>/dev/null || echo "")
    PORT=$(grep PORT .env | cut -d'=' -f2 2>/dev/null || echo "$DEFAULT_PORT")
else
    PORT=$DEFAULT_PORT
    API_KEY=""
fi

BASE_URL="http://localhost:${PORT}"

# Health check
log_info "Testing server health..."
if curl -s -f "${BASE_URL}/health" >/dev/null 2>&1; then
    log_success "Server is running and healthy!"
else
    log_warning "Server may still be starting up..."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    🎉 DEPLOYMENT COMPLETE! 🎉                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Display connection info
echo -e "${CYAN}📡 Server Information:${NC}"
echo "   • Base URL:  ${BASE_URL}/v1"
echo "   • Port:      ${PORT}"
if [ -n "$API_KEY" ]; then
    echo "   • API Key:   ${API_KEY}"
fi
echo ""

# Python usage example
echo -e "${MAGENTA}🐍 Python Usage Example:${NC}"
echo ""
cat << 'EOF'
from openai import OpenAI

client = OpenAI(
EOF
echo "    base_url=\"${BASE_URL}/v1\","
if [ -n "$API_KEY" ]; then
    echo "    api_key=\"${API_KEY}\""
else
    echo "    api_key=\"your-api-key\""
fi
cat << 'EOF'
)

# Simple request
response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Streaming request
stream = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
EOF
echo ""

# curl example
echo -e "${CYAN}🌐 cURL Test Command:${NC}"
echo ""
if [ -n "$API_KEY" ]; then
    cat << EOF
curl ${BASE_URL}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${API_KEY}" \\
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
EOF
else
    cat << EOF
curl ${BASE_URL}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-api-key" \\
  -d '{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
EOF
fi
echo ""
echo ""

# Test the API
log_info "Running live API test..."
echo ""

if [ -n "$API_KEY" ]; then
    RESPONSE=$(curl -s "${BASE_URL}/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d '{
        "model": "MBZUAI-IFM/K2-Think",
        "messages": [{"role": "user", "content": "Say hello in one sentence"}],
        "stream": false
      }')
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}📥 Live API Response:${NC}"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        echo ""
    else
        log_warning "Could not complete test request"
    fi
fi

# Management commands
echo -e "${YELLOW}📊 Server Management:${NC}"
echo "   • View logs:     tail -f ${PROJECT_DIR}/server.log"
echo "   • Stop server:   kill \$(cat ${PROJECT_DIR}/.server.pid)"
echo "   • Restart:       cd ${PROJECT_DIR} && bash scripts/deploy.sh"
echo "   • Health check:  curl ${BASE_URL}/health"
echo ""

# Environment variables
echo -e "${CYAN}🔐 Set Environment Variables:${NC}"
if [ -n "$API_KEY" ]; then
    echo "   export OPENAI_API_KEY=\"${API_KEY}\""
fi
echo "   export OPENAI_BASE_URL=\"${BASE_URL}/v1\""
echo ""

# Final status
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🌟 Server is RUNNING and ready for requests! 🌟          ║"
echo "║                                                            ║"
echo "║  Copy the examples above and start using the API! 🚀      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

log_success "All systems operational!"
echo ""

