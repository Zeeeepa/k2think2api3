#!/bin/bash

# 🚀 K2Think API Proxy - Complete Deployment Script
# This script performs a full deployment with environment setup, 
# token generation, and server startup

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PORT="${SERVER_PORT:-7000}"
K2_EMAIL="${K2_EMAIL:-developer@pixelium.uk}"
K2_PASSWORD="${K2_PASSWORD:-developer123?}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      K2Think API Proxy - Full Deployment Script         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Kill existing server
echo -e "${YELLOW}Step 1: Stopping existing server on port ${SERVER_PORT}...${NC}"
sudo lsof -ti :${SERVER_PORT} | xargs -r sudo kill -9 2>/dev/null || true
sleep 1
echo -e "${GREEN}✓ Port ${SERVER_PORT} cleared${NC}"
echo ""

# Step 2: Navigate to repo
echo -e "${YELLOW}Step 2: Navigating to repository...${NC}"
cd "$REPO_DIR"
echo -e "${GREEN}✓ Working directory: $(pwd)${NC}"
echo ""

# Step 3: Set environment variables
echo -e "${YELLOW}Step 3: Setting environment variables...${NC}"
export K2_EMAIL="${K2_EMAIL}"
export K2_PASSWORD="${K2_PASSWORD}"
export SERVER_PORT="${SERVER_PORT}"
echo -e "${GREEN}✓ K2_EMAIL=${K2_EMAIL}${NC}"
echo -e "${GREEN}✓ SERVER_PORT=${SERVER_PORT}${NC}"
echo ""

# Step 4: Run setup script
echo -e "${YELLOW}Step 4: Running environment setup...${NC}"
bash scripts/setup.sh
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Step 5: Create accounts.txt with proper JSON format
echo -e "${YELLOW}Step 5: Creating accounts.txt...${NC}"
cat > accounts.txt << EOF
{"email": "${K2_EMAIL}", "password": "${K2_PASSWORD}"}
EOF
echo -e "${GREEN}✓ accounts.txt created${NC}"
echo ""

# Step 6: Generate tokens
echo -e "${YELLOW}Step 6: Generating K2Think tokens...${NC}"
source venv/bin/activate
python get_tokens.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tokens generated successfully${NC}"
else
    echo -e "${RED}✗ Token generation failed${NC}"
    exit 1
fi
echo ""

# Step 7: Verify token file
echo -e "${YELLOW}Step 7: Verifying token file...${NC}"
if [ -f "data/tokens.txt" ] && [ -s "data/tokens.txt" ]; then
    TOKEN_COUNT=$(wc -l < data/tokens.txt)
    echo -e "${GREEN}✓ Token file exists with ${TOKEN_COUNT} token(s)${NC}"
else
    echo -e "${RED}✗ Token file is missing or empty${NC}"
    exit 1
fi
echo ""

# Step 8: Start server
echo -e "${YELLOW}Step 8: Starting K2Think API server...${NC}"
nohup python k2think_proxy.py > server.log 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}✓ Server started with PID: ${SERVER_PID}${NC}"
echo ""

# Step 9: Wait for server to be ready
echo -e "${YELLOW}Step 9: Waiting for server to be ready...${NC}"
sleep 5

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server failed to start${NC}"
    echo -e "${RED}Last 20 lines of server.log:${NC}"
    tail -20 server.log
    exit 1
fi
echo ""

# Step 10: Test API with multiple models
echo -e "${YELLOW}Step 10: Testing API with various models...${NC}"

cat > test_deployment.py << 'PYEOF'
from openai import OpenAI
import sys

def test_api(model_name, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="http://localhost:7000/v1")
        result = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'test ok' in 2 words."}],
            max_tokens=10
        )
        print(f"✅ {model_name:20} | {api_key:15} | SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {model_name:20} | {api_key:15} | {str(e)[:30]}")
        return False

models = ["gpt-5", "gpt-4", "claude-3-opus"]
api_keys = ["sk-any", "sk-test"]

success_count = 0
total_count = len(models) * len(api_keys)

for model in models:
    for api_key in api_keys:
        if test_api(model, api_key):
            success_count += 1

print(f"\nTest Results: {success_count}/{total_count} passed")
sys.exit(0 if success_count == total_count else 1)
PYEOF

python test_deployment.py
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All API tests passed${NC}"
else
    echo -e "${RED}✗ Some API tests failed${NC}"
fi
echo ""

# Final summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║               Deployment Summary                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Server URL:${NC}      http://localhost:${SERVER_PORT}"
echo -e "${GREEN}✓ Server PID:${NC}      ${SERVER_PID}"
echo -e "${GREEN}✓ Virtual Env:${NC}     ${REPO_DIR}/venv"
echo -e "${GREEN}✓ Token File:${NC}      ${REPO_DIR}/data/tokens.txt"
echo -e "${GREEN}✓ Log File:${NC}        ${REPO_DIR}/server.log"
echo ""
echo -e "${YELLOW}Key Features:${NC}"
echo -e "  • Accept ANY OpenAI API key (sk-any, sk-test, etc.)"
echo -e "  • Accept ANY model name (gpt-5, claude-3, gemini-pro, etc.)"
echo -e "  • Automatic token refresh enabled"
echo -e "  • Cold start protection active"
echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo -e "  Check Status:    ps aux | grep 'python k2think_proxy.py'"
echo -e "  View Logs:       tail -f ${REPO_DIR}/server.log"
echo -e "  Stop Server:     sudo kill -9 ${SERVER_PID}"
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""

# Exit with test result
exit $TEST_RESULT

