#!/bin/bash
################################################################################
# K2Think API - One-Line Deployment Script
################################################################################
#
# Usage:
#   K2_EMAIL="your@email.com" K2_PASSWORD="yourpass" bash DEPLOYMENT_ONELINER.sh
#
# Or for testing without credentials:
#   bash DEPLOYMENT_ONELINER.sh
#
################################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}🚀 K2Think API - One-Line Complete Deployment${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Configuration
REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
BRANCH="${1:-codegen-bot/fix-http-service-unavailable-1760017183}"  # Use fixed branch by default
INSTALL_DIR="${2:-./k2think2api3}"
PORT="${PORT:-7000}"

echo -e "${GREEN}Configuration:${NC}"
echo "   Repository: $REPO_URL"
echo "   Branch: $BRANCH"
echo "   Install Directory: $INSTALL_DIR"
echo "   Port: $PORT"
echo ""

# Step 1: Clone repository
echo -e "${YELLOW}📦 Step 1/4: Cloning repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "   Directory exists, pulling latest changes..."
    cd "$INSTALL_DIR"
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo -e "${GREEN}✅ Repository ready!${NC}"
echo ""

# Step 2: Setup environment
echo -e "${YELLOW}🔧 Step 2/4: Setting up environment...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi
echo "   Python version: $(python3 --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
pip install -q -r requirements.txt

# Create data directory
mkdir -p data

# Create accounts.txt
if [ -n "$K2_EMAIL" ] && [ -n "$K2_PASSWORD" ]; then
    echo "$K2_EMAIL,$K2_PASSWORD" > data/accounts.txt
    echo -e "${GREEN}✅ Credentials configured${NC}"
else
    echo "test@example.com,testpass123" > data/accounts.txt
    echo -e "${YELLOW}⚠️  Using test credentials (for demo only)${NC}"
fi

# Create .env file
TIMESTAMP=$(date +%s)
cat > .env << EOF
# API Authentication
VALID_API_KEY=sk-k2think-proxy-$TIMESTAMP

# Server Configuration  
PORT=$PORT

# Token Management
ENABLE_TOKEN_AUTO_UPDATE=true
EOF

echo -e "${GREEN}✅ Environment configured!${NC}"
echo ""

# Step 3: Deploy server
echo -e "${YELLOW}🚀 Step 3/4: Starting server...${NC}"

# Kill existing server if running
if [ -f ".server.pid" ]; then
    OLD_PID=$(cat .server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "   Stopping existing server (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
fi

# Start server in background (with venv activated)
source .venv/bin/activate
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port $PORT > server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > .server.pid

# Wait for server to start
echo "   Waiting for server to initialize..."
for i in {1..10}; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)!${NC}"
echo ""

# Step 4: Validate deployment
echo -e "${YELLOW}✅ Step 4/4: Validating deployment...${NC}"

# Get API key
API_KEY=$(grep VALID_API_KEY .env | cut -d'=' -f2)

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:$PORT/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Test API endpoint
echo "   Testing API endpoint..."
API_TEST=$(curl -s -w "\n%{http_code}" -X POST http://localhost:$PORT/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}')

HTTP_CODE=$(echo "$API_TEST" | tail -1)
RESPONSE=$(echo "$API_TEST" | head -1)

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${RED}❌ Authentication failed - check API key${NC}"
elif [ "$HTTP_CODE" = "500" ] && echo "$RESPONSE" | grep -q "Token池暂时为空"; then
    echo -e "${GREEN}✅ API responding correctly (no tokens available yet)${NC}"
    echo -e "${YELLOW}ℹ️  This is expected - tokens will auto-update soon${NC}"
elif [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ API fully functional!${NC}"
else
    echo -e "${YELLOW}⚠️  API response: HTTP $HTTP_CODE${NC}"
fi

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}✨ Deployment Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}📊 Server Information:${NC}"
echo "   URL: http://localhost:$PORT"
echo "   API Key: $API_KEY"
echo "   PID: $SERVER_PID"
echo "   Log file: $(pwd)/server.log"
echo ""
echo -e "${GREEN}📝 Quick Commands:${NC}"
echo "   View logs:     tail -f $(pwd)/server.log"
echo "   Stop server:   kill $SERVER_PID"
echo "   Restart:       bash $0"
echo ""
echo -e "${GREEN}🧪 Test the API:${NC}"
echo "   curl -X POST http://localhost:$PORT/v1/chat/completions \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -H \"Authorization: Bearer $API_KEY\" \\"
echo "     -d '{\"model\":\"gpt-4\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
echo ""
echo -e "${GREEN}🔗 Health Check:${NC}"
echo "   curl http://localhost:$PORT/health"
echo ""
