#!/bin/bash

# Setup Claude Code Router with K2Think Integration
# This script configures claude-code-router to use K2Think server

set -e

echo "🚀 K2Think + Claude Code Router Integration Setup"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed!${NC}"
    echo "Please install Node.js first: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✅ Node.js $(node --version) found${NC}"
echo ""

# Check if ccr is installed
if ! command -v ccr &> /dev/null; then
    echo -e "${BLUE}📦 Installing claude-code-router...${NC}"
    npm install -g @musistudio/claude-code-router
    echo -e "${GREEN}✅ claude-code-router installed${NC}"
else
    echo -e "${GREEN}✅ claude-code-router already installed${NC}"
fi

echo ""

# Create config directory
CONFIG_DIR="$HOME/.claude-code-router"
mkdir -p "$CONFIG_DIR"
echo -e "${GREEN}✅ Config directory: $CONFIG_DIR${NC}"

# Get K2Think server info
K2THINK_URL="${K2THINK_URL:-http://localhost:7000}"
K2THINK_API_KEY="${K2THINK_API_KEY:-sk-k2think-proxy-1763083074}"

echo ""
echo -e "${BLUE}ℹ️  Configuration:${NC}"
echo "   K2Think Server: $K2THINK_URL"
echo "   API Key: $K2THINK_API_KEY"

# Create config.json
cat > "$CONFIG_DIR/config.json" <<EOF
{
  "LOG": true,
  "LOG_LEVEL": "info",
  "API_TIMEOUT_MS": 600000,
  "NON_INTERACTIVE_MODE": false,
  "Providers": [
    {
      "name": "k2think",
      "api_base_url": "${K2THINK_URL}/v1/chat/completions",
      "api_key": "${K2THINK_API_KEY}",
      "models": [
        "MBZUAI-IFM/K2-Think",
        "MBZUAI-IFM/K2-Think-nothink"
      ],
      "transformer": {
        "use": []
      }
    }
  ],
  "Router": {
    "default": "k2think,MBZUAI-IFM/K2-Think",
    "background": "k2think,MBZUAI-IFM/K2-Think-nothink",
    "think": "k2think,MBZUAI-IFM/K2-Think",
    "longContext": "k2think,MBZUAI-IFM/K2-Think",
    "longContextThreshold": 60000
  }
}
EOF

echo ""
echo -e "${GREEN}✅ Configuration file created: $CONFIG_DIR/config.json${NC}"

# Check if K2Think server is running
echo ""
echo -e "${BLUE}🔍 Checking K2Think server...${NC}"
if curl -s -f "$K2THINK_URL/health" > /dev/null 2>&1 || curl -s -f "$K2THINK_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ K2Think server is running${NC}"
else
    echo -e "${YELLOW}⚠️  K2Think server may not be running${NC}"
    echo "   Please start it with: bash scripts/start.sh"
fi

# Stop existing router if running
if ccr status 2>/dev/null | grep -q "Running"; then
    echo ""
    echo -e "${BLUE}🔄 Restarting claude-code-router...${NC}"
    ccr stop
    sleep 2
fi

# Start claude-code-router
echo ""
echo -e "${BLUE}🚀 Starting claude-code-router...${NC}"
ccr start

# Wait for router to start
sleep 3

# Check router status
echo ""
if ccr status 2>&1 | grep -q "Running"; then
    echo -e "${GREEN}✅ claude-code-router is running!${NC}"
    echo ""
    ccr status
else
    echo -e "${RED}❌ Failed to start claude-code-router${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📋 Architecture:${NC}"
echo "   Claude Code → claude-code-router → K2Think Server → K2Think API"
echo "                 (Port 3456)         (Port 7000)"
echo ""
echo -e "${BLUE}🔧 Usage:${NC}"
echo "   1. Start Claude Code with router:"
echo "      ${GREEN}ccr code${NC}"
echo ""
echo "   2. Or use Claude Code directly (set env vars):"
echo "      ${GREEN}eval \"\$(ccr activate)\"${NC}"
echo "      ${GREEN}claude \"Hello from K2Think!\"${NC}"
echo ""
echo "   3. Manage configuration via UI:"
echo "      ${GREEN}ccr ui${NC}"
echo ""
echo "   4. Switch models interactively:"
echo "      ${GREEN}ccr model${NC}"
echo ""
echo -e "${BLUE}🎯 Available Models:${NC}"
echo "   • MBZUAI-IFM/K2-Think (with reasoning)"
echo "   • MBZUAI-IFM/K2-Think-nothink (without reasoning)"
echo ""
echo -e "${BLUE}📝 Model Routing:${NC}"
echo "   • default: K2-Think (with reasoning)"
echo "   • background: K2-Think-nothink (faster)"
echo "   • think: K2-Think (for complex reasoning)"
echo "   • longContext: K2-Think (for long inputs)"
echo ""
echo -e "${BLUE}🔍 Management Commands:${NC}"
echo "   • Check status:  ${GREEN}ccr status${NC}"
echo "   • Stop router:   ${GREEN}ccr stop${NC}"
echo "   • Restart:       ${GREEN}ccr restart${NC}"
echo "   • View logs:     ${GREEN}tail -f ~/.claude-code-router/logs/ccr-*.log${NC}"
echo ""
echo -e "${YELLOW}💡 Tip:${NC} You can switch models on-the-fly in Claude Code:"
echo "   ${GREEN}/model k2think,MBZUAI-IFM/K2-Think${NC}"
echo ""

