#!/bin/bash

# K2Think API Environment Activation Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
ENV_FILE="$SCRIPT_DIR/.env"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Activating K2Think API environment...${NC}"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "\033[0;31m❌ Virtual environment not found${NC}"
    exit 1
fi

# Export environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
else
    echo -e "\033[0;31m❌ Environment file not found${NC}"
    exit 1
fi

# Show status
echo -e "${BLUE}📋 Environment Status:${NC}"
echo "  Python: $(which python3)"
echo "  API Key: ${VALID_API_KEY:0:20}..."
echo "  Server URL: http://localhost:${PORT:-7001}"
echo
echo -e "${BLUE}🚀 Ready to run K2Think API!${NC}"
echo "  Start server: python3 k2think_proxy.py"
echo "  Test API: bash scripts/send_request.sh"
