#!/bin/bash
# K2Think API Proxy - Environment Activation Script
# Source this script to activate the K2Think environment
# Usage: source ~/k2think2api3/k2think_activate.sh

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to K2Think directory
cd "${SCRIPT_DIR}" || {
    echo -e "${RED}❌ Failed to change to K2Think directory${NC}"
    return 1
}

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    return 1
fi

# Display welcome banner
echo -e "${CYAN}"
cat << 'EOF'
╔════════════════════════════════════════════╗
║      K2Think API Proxy - Activated        ║
╚════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check server status
echo -e "${BLUE}Server Status:${NC}"
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Server is ${GREEN}running${NC} (PID: ${PID})"
        
        # Try to get port from .env
        if [ -f ".env" ]; then
            PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
            echo -e "  ${BLUE}•${NC} URL: http://localhost:${PORT}"
        fi
    else
        echo -e "  ${YELLOW}○${NC} Server is ${YELLOW}not running${NC}"
    fi
else
    echo -e "  ${YELLOW}○${NC} Server is ${YELLOW}not running${NC}"
fi

# Show available commands
echo -e "\n${CYAN}Available Commands:${NC}"
echo -e "  ${GREEN}./k2think_server.sh start${NC}   - Start the server"
echo -e "  ${GREEN}./k2think_server.sh stop${NC}    - Stop the server"
echo -e "  ${GREEN}./k2think_server.sh restart${NC} - Restart the server"
echo -e "  ${GREEN}./k2think_server.sh status${NC}  - Check server status"
echo -e "  ${GREEN}./k2think_server.sh logs${NC}    - View server logs"

echo -e "\n${GREEN}📁 Current directory: ${SCRIPT_DIR}${NC}"
echo -e "${GREEN}🐍 Python: $(python --version 2>&1)${NC}\n"

