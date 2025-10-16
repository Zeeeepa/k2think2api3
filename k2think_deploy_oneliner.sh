#!/bin/bash
# K2Think API Proxy - Interactive Port Selection + Auto Activation
# Version: 2.0 - Full 30-Step Upgrade
# Usage: curl -fsSL <url> | bash

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPO_DIR="${HOME}/k2think2api3"
LOG_FILE="${REPO_DIR}/k2think_deployment.log"
DEFAULT_PORT=7000
MAX_PORT_RETRIES=5

# Step 1-2: Port Availability Checker Function
check_port_available() {
    local port=$1
    # Try lsof first (most reliable)
    if command -v lsof &> /dev/null; then
        if sudo lsof -ti :${port} &> /dev/null; then
            return 1  # Port is in use
        fi
    # Fallback to ss
    elif command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":${port} "; then
            return 1
        fi
    # Fallback to netstat
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":${port} "; then
            return 1
        fi
    fi
    return 0  # Port is available
}

# Get process using port
get_port_process() {
    local port=$1
    if command -v lsof &> /dev/null; then
        sudo lsof -ti :${port} 2>/dev/null | head -1
    fi
}

# Step 3: Port Validation Function
validate_port() {
    local port=$1
    # Check if numeric
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    # Check range (1024-65535, avoid privileged ports)
    if [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
        return 1
    fi
    return 0
}

# Step 10: Shell Detection
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    else
        basename "$SHELL"
    fi
}

# Deployment logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}" 2>/dev/null || true
}

# ASCII Banner (Step 17)
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ██╗  ██╗██████╗ ████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗ ║
║     ██║ ██╔╝╚════██╗╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝ ║
║     █████╔╝  █████╔╝   ██║   ███████║██║██╔██╗ ██║█████╔╝  ║
║     ██╔═██╗ ██╔═══╝    ██║   ██╔══██║██║██║╚██╗██║██╔═██╗  ║
║     ██║  ██╗███████╗   ██║   ██║  ██║██║██║ ╚████║██║  ██╗ ║
║     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ║
║                                                           ║
║            One-Liner Deployment v2.0                     ║
║         Interactive • Automated • Production-Ready        ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Main deployment starts here
show_banner

log_message "=== Deployment Started ==="

# Validate K2_EMAIL and K2_PASSWORD
if [ -z "$K2_EMAIL" ] || [ -z "$K2_PASSWORD" ]; then
    echo -e "${RED}❌ Error: K2_EMAIL and K2_PASSWORD must be set${NC}"
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  export K2_EMAIL=\"your@email.com\""
    echo -e "  export K2_PASSWORD=\"yourpassword\""
    echo -e "  curl -fsSL <gist-url> | bash"
    exit 1
fi

log_message "Environment variables validated"

# Step 23-24: Check for existing installation
if [ -d "${REPO_DIR}" ]; then
    echo -e "${YELLOW}⚠️  Existing installation detected at ${REPO_DIR}${NC}"
    
    # Check if server is running
    if pgrep -f "python.*k2think_proxy.py" > /dev/null; then
        echo -e "${YELLOW}   Server appears to be running${NC}"
    fi
    
    echo -e "${CYAN}Choose an option:${NC}"
    echo -e "  ${GREEN}1${NC}) Reinstall (delete everything and start fresh)"
    echo -e "  ${BLUE}2${NC}) Upgrade (preserve configuration)"
    echo -e "  ${RED}3${NC}) Cancel"
    
    if [ -t 0 ]; then
        read -p "Enter choice (1-3): " -n 1 -r choice
        echo
    else
        choice="1"  # Default to reinstall in non-interactive mode
    fi
    
    case $choice in
        1)
            echo -e "${YELLOW}Backing up existing installation...${NC}"
            if [ -f "${REPO_DIR}/.env" ]; then
                cp "${REPO_DIR}/.env" "${REPO_DIR}/.env.backup.$(date +%s)" 2>/dev/null || true
            fi
            echo -e "${YELLOW}Removing existing installation...${NC}"
            sudo pkill -f "python.*k2think_proxy.py" 2>/dev/null || true
            rm -rf "${REPO_DIR}"
            ;;
        2)
            echo -e "${BLUE}Preserving configuration...${NC}"
            if [ -f "${REPO_DIR}/.env" ]; then
                cp "${REPO_DIR}/.env" "/tmp/k2think.env.backup"
            fi
            ;;
        3|*)
            echo -e "${RED}Deployment cancelled${NC}"
            exit 0
            ;;
    esac
fi

# Step 2-5: Interactive Port Selection
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Port Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if SERVER_PORT is set (for automated deployments)
if [ -n "$SERVER_PORT" ]; then
    PORT="$SERVER_PORT"
    echo -e "${BLUE}ℹ️  Using SERVER_PORT from environment: ${PORT}${NC}"
else
    PORT_RETRIES=0
    while [ $PORT_RETRIES -lt $MAX_PORT_RETRIES ]; do
        # Interactive prompt
        if [ -t 0 ]; then
            echo -e "${GREEN}Enter port number (default ${DEFAULT_PORT}): ${NC}"
            read -r user_port
            PORT="${user_port:-$DEFAULT_PORT}"
        else
            PORT="${DEFAULT_PORT}"
        fi
        
        # Step 3: Validate port
        if ! validate_port "$PORT"; then
            echo -e "${RED}❌ Invalid port: ${PORT}${NC}"
            echo -e "${YELLOW}   Port must be numeric and between 1024-65535${NC}"
            PORT_RETRIES=$((PORT_RETRIES + 1))
            continue
        fi
        
        # Step 4: Check availability
        if check_port_available "$PORT"; then
            # Step 5: Confirmation
            echo -e "${GREEN}✅ Port ${PORT} is available!${NC}"
            log_message "Port ${PORT} selected and available"
            break
        else
            echo -e "${RED}❌ Port ${PORT} is already in use${NC}"
            
            # Step 25: Show process using port
            PID=$(get_port_process "$PORT")
            if [ -n "$PID" ]; then
                PROCESS_INFO=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
                echo -e "${YELLOW}   Process: ${PROCESS_INFO} (PID: ${PID})${NC}"
                
                if [ -t 0 ]; then
                    echo -e "${CYAN}Options:${NC}"
                    echo -e "  ${RED}k${NC}) Kill process and use port ${PORT}"
                    echo -e "  ${GREEN}c${NC}) Choose different port"
                    echo -e "  ${BLUE}a${NC}) Auto-select first available port"
                    read -p "Choice (k/c/a): " -n 1 -r action
                    echo
                    
                    case $action in
                        k|K)
                            echo -e "${YELLOW}Killing process ${PID}...${NC}"
                            sudo kill -9 $PID 2>/dev/null || true
                            sleep 1
                            if check_port_available "$PORT"; then
                                echo -e "${GREEN}✅ Port ${PORT} is now available!${NC}"
                                break
                            fi
                            ;;
                        a|A)
                            # Auto-select first available port
                            for test_port in $(seq 7001 7010); do
                                if check_port_available "$test_port"; then
                                    PORT=$test_port
                                    echo -e "${GREEN}✅ Auto-selected port ${PORT}${NC}"
                                    break 2
                                fi
                            done
                            ;;
                        *)
                            # Continue to prompt for different port
                            ;;
                    esac
                fi
            fi
            
            PORT_RETRIES=$((PORT_RETRIES + 1))
            if [ $PORT_RETRIES -ge $MAX_PORT_RETRIES ]; then
                echo -e "${RED}❌ Max retries reached. Using dynamic port assignment.${NC}"
                PORT=0  # Let the system choose
                break
            fi
        fi
    done
fi

export SERVER_PORT=$PORT
log_message "Final port selected: ${PORT}"

# Kill any existing server on this port
echo -e "\n${YELLOW}Checking for existing server on port ${PORT}...${NC}"
sudo lsof -ti :${PORT} | xargs -r sudo kill -9 2>/dev/null || true
sleep 1

# Clone repository
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Repository Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Cloning repository...${NC}"
git clone https://github.com/Zeeeepa/k2think2api3 "${REPO_DIR}"
cd "${REPO_DIR}"
git checkout codegen-bot/interactive-port-venv-cd-upgrade-1760647609 2>/dev/null || git checkout main

log_message "Repository cloned successfully"

# Setup Python environment
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Python Environment${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt 2>/dev/null || pip install -q fastapi uvicorn httpx python-dotenv pydantic openai

log_message "Python environment setup complete"

# Step 6-7: Create configuration files
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

mkdir -p data

# Restore preserved config if upgrading
if [ -f "/tmp/k2think.env.backup" ]; then
    echo -e "${BLUE}Restoring preserved configuration...${NC}"
    cp "/tmp/k2think.env.backup" .env
    rm "/tmp/k2think.env.backup"
else
    echo -e "${YELLOW}Creating configuration files...${NC}"
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
fi

cat > accounts.txt << EOF
{"email": "${K2_EMAIL}", "password": "${K2_PASSWORD}"}
EOF

log_message "Configuration files created with port ${PORT}"

# Generate tokens
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Token Generation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Generating K2Think tokens...${NC}"
python get_tokens.py 2>&1 | tail -10

if [ ! -s "data/tokens.txt" ]; then
    echo -e "${RED}❌ Token generation failed${NC}"
    echo -e "${YELLOW}See error recovery instructions below${NC}"
    log_message "ERROR: Token generation failed"
else
    echo -e "${GREEN}✅ Tokens generated successfully${NC}"
    log_message "Tokens generated successfully"
fi

# Start server
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Server Startup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Starting K2Think API server on port ${PORT}...${NC}"
nohup python k2think_proxy.py > server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > .server.pid

log_message "Server started with PID ${SERVER_PID}"

sleep 5

# Verify server
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Server failed to start${NC}"
    echo -e "${YELLOW}Last 20 lines of server.log:${NC}"
    tail -20 server.log
    log_message "ERROR: Server failed to start"
else
    echo -e "${GREEN}✅ Server is running (PID: ${SERVER_PID})${NC}"
    
    # Step 27: Health check
    echo -e "${YELLOW}Performing health check...${NC}"
    sleep 3
    if curl -s -f "http://localhost:${PORT}/v1/models" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API health check passed${NC}"
        log_message "Health check passed"
    else
        echo -e "${YELLOW}⚠️  Health check pending (server may still be starting)${NC}"
    fi
fi

log_message "=== Deployment Completed ==="

# Success banner and instructions
echo -e "\n${GREEN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║            ✅ DEPLOYMENT SUCCESSFUL ✅                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 20: Deployment Summary
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Deployment Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Server Details:${NC}"
echo -e "  ${BLUE}•${NC} URL:       ${GREEN}http://localhost:${PORT}${NC}"
echo -e "  ${BLUE}•${NC} PID:       ${SERVER_PID}"
echo -e "  ${BLUE}•${NC} Directory: ${REPO_DIR}"
echo -e "  ${BLUE}•${NC} Venv:      ${REPO_DIR}/venv"
echo -e "  ${BLUE}•${NC} Logs:      ${REPO_DIR}/server.log"
echo -e "  ${BLUE}•${NC} Deploy Log: ${LOG_FILE}"

# Step 11-14: Post-Deployment Instructions
DETECTED_SHELL=$(detect_shell)

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Next Steps${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}📦 Activate your environment:${NC}"
if [ "$DETECTED_SHELL" = "bash" ] || [ "$DETECTED_SHELL" = "zsh" ]; then
    echo -e "  ${GREEN}source ${REPO_DIR}/k2think_activate.sh${NC}"
else
    echo -e "  ${GREEN}source ${REPO_DIR}/k2think_activate.sh${NC}"
fi

echo -e "\n${YELLOW}🔧 Optional - Add permanent alias:${NC}"
if [ "$DETECTED_SHELL" = "bash" ]; then
    echo -e "  ${CYAN}echo 'alias k2think=\"source ${REPO_DIR}/k2think_activate.sh\"' >> ~/.bashrc${NC}"
    echo -e "  ${CYAN}source ~/.bashrc${NC}"
elif [ "$DETECTED_SHELL" = "zsh" ]; then
    echo -e "  ${CYAN}echo 'alias k2think=\"source ${REPO_DIR}/k2think_activate.sh\"' >> ~/.zshrc${NC}"
    echo -e "  ${CYAN}source ~/.zshrc${NC}"
fi

echo -e "\n${YELLOW}🧪 Test the API:${NC}"
echo -e "  ${CYAN}curl -X POST http://localhost:${PORT}/v1/chat/completions \\${NC}"
echo -e "  ${CYAN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "  ${CYAN}  -H 'Authorization: Bearer sk-any' \\${NC}"
echo -e "  ${CYAN}  -d '{\"model\": \"gpt-5\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}'${NC}"

echo -e "\n${GREEN}✨ Features:${NC}"
echo -e "  ${BLUE}•${NC} Accept ANY API key (sk-any, sk-test, etc.)"
echo -e "  ${BLUE}•${NC} Accept ANY model name (gpt-5, claude-3, etc.)"
echo -e "  ${BLUE}•${NC} Automatic token refresh enabled"
echo -e "  ${BLUE}•${NC} Interactive port selection"
echo -e "  ${BLUE}•${NC} Server management scripts included"

# Step 21: Error Recovery Instructions
if [ ! -s "data/tokens.txt" ]; then
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ⚠️  Token Generation Failed - Recovery Steps${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}1. Check credentials:${NC}"
    echo -e "   ${CYAN}export K2_EMAIL=\"your@email.com\"${NC}"
    echo -e "   ${CYAN}export K2_PASSWORD=\"yourpassword\"${NC}"
    echo -e "${YELLOW}2. Retry token generation:${NC}"
    echo -e "   ${CYAN}cd ${REPO_DIR} && source venv/bin/activate && python get_tokens.py${NC}"
    echo -e "${YELLOW}3. Check server log for errors:${NC}"
    echo -e "   ${CYAN}tail -50 ${REPO_DIR}/server.log${NC}"
fi

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Deployment complete! Enjoy your K2Think API proxy!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

