#!/bin/bash
# K2Think API Proxy - Uninstall Script
# This script removes the K2Think installation completely

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_DIR="${HOME}/k2think2api3"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      K2Think API Proxy - Uninstall Script               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}⚠️  This will completely remove K2Think from your system${NC}"
echo -e "${YELLOW}   Including:${NC}"
echo -e "   • ${REPO_DIR} directory"
echo -e "   • Running server processes"
echo -e "   • Shell aliases (manual removal required)"
echo -e ""

read -p "Are you sure you want to proceed? (yes/no): " -r confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${GREEN}Uninstall cancelled${NC}"
    exit 0
fi

echo -e "\n${CYAN}Starting uninstall process...${NC}\n"

# Step 1: Stop server
echo -e "${YELLOW}[1/4] Stopping K2Think server...${NC}"
if pgrep -f "python.*k2think_proxy.py" > /dev/null; then
    pkill -f "python.*k2think_proxy.py"
    echo -e "${GREEN}✅ Server stopped${NC}"
else
    echo -e "${BLUE}ℹ️  Server was not running${NC}"
fi

# Step 2: Kill any processes using ports
echo -e "\n${YELLOW}[2/4] Checking for port usage...${NC}"
if [ -f "${REPO_DIR}/.env" ]; then
    PORT=$(grep "^PORT=" "${REPO_DIR}/.env" | cut -d'=' -f2 2>/dev/null)
    if [ -n "$PORT" ] && command -v lsof &> /dev/null; then
        PID=$(sudo lsof -ti :${PORT} 2>/dev/null)
        if [ -n "$PID" ]; then
            sudo kill -9 $PID 2>/dev/null
            echo -e "${GREEN}✅ Freed port ${PORT}${NC}"
        else
            echo -e "${BLUE}ℹ️  Port ${PORT} is not in use${NC}"
        fi
    fi
fi

# Step 3: Remove directory
echo -e "\n${YELLOW}[3/4] Removing installation directory...${NC}"
if [ -d "${REPO_DIR}" ]; then
    rm -rf "${REPO_DIR}"
    echo -e "${GREEN}✅ Directory removed: ${REPO_DIR}${NC}"
else
    echo -e "${BLUE}ℹ️  Directory not found${NC}"
fi

# Step 4: Check for shell aliases
echo -e "\n${YELLOW}[4/4] Checking for shell aliases...${NC}"
FOUND_ALIAS=false

for rc_file in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc_file" ] && grep -q "k2think" "$rc_file" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Found k2think alias in ${rc_file}${NC}"
        echo -e "${CYAN}   To remove manually, edit ${rc_file} and remove the line containing 'k2think'${NC}"
        FOUND_ALIAS=true
    fi
done

if [ "$FOUND_ALIAS" = false ]; then
    echo -e "${GREEN}✅ No shell aliases found${NC}"
fi

# Summary
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Uninstall Complete!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if [ "$FOUND_ALIAS" = true ]; then
    echo -e "${YELLOW}⚠️  Manual steps remaining:${NC}"
    echo -e "   1. Edit your shell config file to remove k2think alias"
    echo -e "   2. Run: source ~/.bashrc  (or ~/.zshrc)\n"
fi

echo -e "${CYAN}Thank you for using K2Think API Proxy!${NC}\n"

