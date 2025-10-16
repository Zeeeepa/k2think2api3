#!/bin/bash
# K2Think API Proxy - One-Liner Full Deployment
# Usage: export K2_EMAIL="your@email.com" && export K2_PASSWORD="yourpass" && curl -fsSL https://gist.githubusercontent.com/... | bash

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}🚀 K2Think API Proxy - One-Liner Deployment${NC}"

# Validate environment variables
if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
    echo -e "${RED}❌ Error: K2_EMAIL and K2_PASSWORD must be set${NC}"
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  export K2_EMAIL=\"your@email.com\""
    echo -e "  export K2_PASSWORD=\"yourpassword\""
    echo -e "  curl -fsSL <gist-url> | bash"
    exit 1
fi

PORT="${SERVER_PORT:-7000}"
REPO_DIR="${HOME}/k2think2api3"

echo -e "${GREEN}✓ K2_EMAIL: ${K2_EMAIL}${NC}"
echo -e "${GREEN}✓ PORT: ${PORT}${NC}"

# Kill existing server
echo -e "${YELLOW}Stopping existing server...${NC}"
sudo lsof -ti :${PORT} | xargs -r sudo kill -9 2>/dev/null || true
sleep 1

# Clean and clone
echo -e "${YELLOW}Cloning repository...${NC}"
rm -rf "${REPO_DIR}"
git clone https://github.com/Zeeeepa/k2think2api3 "${REPO_DIR}"
cd "${REPO_DIR}"
git checkout codegen-bot/api-auth-model-override-upgrade-1760613873 2>/dev/null || git checkout main

# Setup Python environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || pip install -q fastapi uvicorn httpx python-dotenv pydantic

# Create configuration files
echo -e "${YELLOW}Creating configuration...${NC}"
mkdir -p data

cat > .env << EOF
K2THINK_API_URL=https://www.k2think.ai/api/chat/completions
VALID_API_KEY=sk-any-key-works
ALLOW_ANY_API_KEY=true
PORT=${PORT}
HOST=0.0.0.0
TOKENS_FILE=data/tokens.txt
MAX_TOKEN_FAILURES=3
ENABLE_TOKEN_AUTO_UPDATE=true
K2_EMAIL=${K2_EMAIL}
K2_PASSWORD=${K2_PASSWORD}
TOKEN_UPDATE_INTERVAL_MINUTES=30
ACCOUNTS_FILE=accounts.txt
LOG_LEVEL=INFO
EOF

cat > accounts.txt << EOF
{"email": "${K2_EMAIL}", "password": "${K2_PASSWORD}"}
EOF

echo "# Tokens will be auto-generated" > data/tokens.txt

# Generate tokens
echo -e "${YELLOW}Generating tokens...${NC}"
python get_tokens.py 2>&1 | tail -5
if [ ! -s "data/tokens.txt" ]; then
    echo -e "${RED}❌ Token generation failed${NC}"
    exit 1
fi

# Start server
echo -e "${YELLOW}Starting server...${NC}"
nohup python k2think_proxy.py > server.log 2>&1 &
SERVER_PID=$!
sleep 5

# Verify server
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Server failed to start${NC}"
    tail -20 server.log
    exit 1
fi

# Test API
echo -e "${YELLOW}Testing API...${NC}"
cat > test_quick.py << 'PYEOF'
from openai import OpenAI
try:
    client = OpenAI(api_key="sk-any", base_url="http://localhost:7000/v1")
    result = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": "Say 'OK' in 1 word"}], max_tokens=5)
    print(f"✅ API Test: SUCCESS - {result.choices[0].message.content[:20]}")
except Exception as e:
    print(f"❌ API Test: FAILED - {str(e)[:50]}")
    exit(1)
PYEOF

python test_quick.py

# Success summary
echo -e "\n${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          ✅ DEPLOYMENT SUCCESSFUL ✅                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "\n${GREEN}Server Details:${NC}"
echo -e "  URL:       http://localhost:${PORT}"
echo -e "  PID:       ${SERVER_PID}"
echo -e "  Directory: ${REPO_DIR}"
echo -e "  Logs:      ${REPO_DIR}/server.log"
echo -e "\n${YELLOW}Test Command:${NC}"
echo -e "  curl -X POST http://localhost:${PORT}/v1/chat/completions \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -H 'Authorization: Bearer sk-any' \\"
echo -e "    -d '{\"model\": \"gpt-5\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}'"
echo -e "\n${GREEN}✅ ANY API key works! ✅ ANY model name works!${NC}\n"

