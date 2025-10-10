#!/bin/bash

# K2Think API Proxy - Enhanced All-in-One Deployment Script
# This script handles complete setup from system preparation to running server
# Enhanced version with comprehensive functionality and professional error handling

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env"
SERVER_LOG="$PROJECT_DIR/server.log"
PID_FILE="$PROJECT_DIR/.server.pid"
GITHUB_REPO="https://github.com/Zeeeepa/k2think2api3.git"

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${CYAN}🔧 $1${NC}"; }
log_command() { echo -e "${MAGENTA}💻 $1${NC}"; }

# Progress indicator
show_progress() {
    local duration=$1
    local message=$2
    local chars=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    
    log_info "$message"
    
    for ((i = 0; i < duration * 10; i++)); do
        printf "\r${CYAN}%s${NC} %d%%" "${chars[i % 10]}" "$((i * 100 / (duration * 10)))"
        sleep 0.1
    done
    printf "\r${GREEN}✅${NC} 100%%\n"
}

# Error handling
handle_error() {
    local line_number=$1
    local command="$2"
    log_error "Script failed at line $line_number: $command"
    log_error "Please check the logs and try again"
    exit 1
}

trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# System requirements check
check_system_requirements() {
    log_step "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_success "macOS detected"
    else
        log_warning "Unsupported OS: $OSTYPE"
        log_info "Proceeding anyway..."
    fi
    
    # Check required commands
    local required_commands=(git python3 curl wget)
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_info "Please install them and try again"
        exit 1
    fi
    
    # Check Python version
    local python_version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_success "Python version: $python_version"
    
    # Check available space
    local available_space
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        log_warning "Low disk space detected (${available_space}KB available)"
    fi
    
    log_success "System requirements check passed"
}

# Setup project directory
setup_project_directory() {
    log_step "Setting up project directory..."
    
    # Create data directory
    mkdir -p "$DATA_DIR"
    
    # Create log file
    touch "$SERVER_LOG"
    
    # Set proper permissions
    chmod 755 "$PROJECT_DIR"
    chmod 700 "$DATA_DIR"
    
    log_success "Project directory setup complete"
}

# Setup credentials
setup_credentials() {
    log_step "Setting up credentials..."
    
    # Check if accounts.txt exists
    if [ ! -f "$DATA_DIR/accounts.txt" ]; then
        log_warning "accounts.txt not found in $DATA_DIR"
        log_info "Creating template accounts.txt..."
        
        cat > "$DATA_DIR/accounts.txt" << 'EOF'
[
  {
    "email": "your-email@example.com",
    "password": "your-password"
  }
]
EOF
        log_warning "Please update $DATA_DIR/accounts.txt with your K2Think credentials"
        log_info "Format: JSON array with email and password fields"
    else
        log_success "Found accounts.txt"
    fi
    
    # Generate API key
    local api_key="sk-k2think-$(openssl rand -hex 16)"
    
    # Create or update .env file
    if [ -f "$ENV_FILE" ]; then
        log_info "Updating existing .env file"
        sed -i.bak "s/^VALID_API_KEY=.*/VALID_API_KEY=$api_key/" "$ENV_FILE"
    else
        log_info "Creating new .env file"
        cat > "$ENV_FILE" << EOF
# K2Think API Proxy Configuration
VALID_API_KEY=$api_key
TOKENS_FILE=$DATA_DIR/tokens.txt
ACCOUNTS_FILE=$DATA_DIR/accounts.txt
HOST=0.0.0.0
PORT=7001
ENABLE_TOKEN_AUTO_UPDATE=true
TOKEN_UPDATE_INTERVAL=3600
EOF
    fi
    
    log_success "Credentials setup complete"
    log_info "API Key: $api_key"
}

# Setup environment
setup_environment() {
    log_step "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        log_command "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        show_progress 3 "Setting up virtual environment"
    else
        log_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    log_command "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    log_command "Upgrading pip..."
    pip install --upgrade pip &> /dev/null
    
    # Check if requirements.txt exists
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        log_command "Installing requirements..."
        pip install -r "$PROJECT_DIR/requirements.txt" &> /dev/null
        show_progress 5 "Installing requirements"
    else
        log_warning "requirements.txt not found, installing basic requirements..."
        pip install fastapi uvicorn httpx aiofiles python-multipart &> /dev/null
    fi
    
    log_success "Environment setup complete"
}

# Setup configuration
setup_configuration() {
    log_step "Setting up configuration..."
    
    # Ensure configuration files exist
    touch "$DATA_DIR/tokens.txt"
    touch "$DATA_DIR/stats.json"
    
    # Set proper permissions
    chmod 600 "$DATA_DIR/tokens.txt" 2>/dev/null || true
    chmod 644 "$DATA_DIR/stats.json"
    chmod 600 "$ENV_FILE"
    
    log_success "Configuration setup complete"
}

# Acquire tokens
acquire_tokens() {
    log_step "Acquiring K2Think tokens..."
    
    # Check if get_tokens.py exists
    if [ -f "$PROJECT_DIR/get_tokens.py" ]; then
        log_command "Running token acquisition script..."
        
        cd "$PROJECT_DIR"
        if python3 get_tokens.py &> /dev/null; then
            log_success "Token acquisition completed"
        else
            log_warning "Token acquisition failed, will continue anyway"
            log_info "You can run 'python3 get_tokens.py' later to acquire tokens"
        fi
    else
        log_warning "get_tokens.py not found"
        log_info "Tokens will need to be acquired manually"
    fi
    
    # Check if tokens file has content
    if [ -f "$DATA_DIR/tokens.txt" ] && [ -s "$DATA_DIR/tokens.txt" ]; then
        local token_count
        token_count=$(wc -l < "$DATA_DIR/tokens.txt")
        log_success "Found $token_count tokens in tokens.txt"
    else
        log_warning "No tokens found in tokens.txt"
        log_info "Please add K2Think JWT tokens to $DATA_DIR/tokens.txt"
    fi
}

# Deploy server
deploy_server() {
    log_step "Deploying K2Think API server..."
    
    # Stop existing server if running
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_command "Stopping existing server (PID: $pid)..."
            kill "$pid"
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
    
    # Start the server
    log_command "Starting K2Think API server..."
    cd "$PROJECT_DIR"
    
    # Start server in background
    nohup python3 k2think_proxy.py &> "$SERVER_LOG" &
    local server_pid=$!
    
    # Save PID
    echo "$server_pid" > "$PID_FILE"
    
    # Wait for server to start
    show_progress 3 "Starting server"
    
    # Check if server is running
    if kill -0 "$server_pid" 2>/dev/null; then
        log_success "Server started successfully (PID: $server_pid)"
        
        # Test server health
        sleep 2
        if curl -s http://localhost:7001/health &> /dev/null; then
            log_success "Server health check passed"
        else
            log_warning "Server health check failed, but server is running"
        fi
    else
        log_error "Failed to start server"
        log_info "Check logs: tail -f $SERVER_LOG"
        exit 1
    fi
}

# Create deployment summary
create_deployment_summary() {
    log_step "Creating deployment summary..."
    
    cat > "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md" << EOF
# K2Think API Proxy - Deployment Summary

**Deployed at:** $(date)
**Server URL:** http://localhost:7001
**API Key:** $(grep VALID_API_KEY "$ENV_FILE" | cut -d'=' -f2)
**Log File:** $SERVER_LOG
**PID File:** $PID_FILE

## Server Status
EOF
    
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ Server is running (PID: $(cat "$PID_FILE"))" >> "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md"
    else
        echo "❌ Server is not running" >> "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md"
    fi
    
    cat >> "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md" << EOF

## Token Status
EOF
    
    if [ -f "$DATA_DIR/tokens.txt" ] && [ -s "$DATA_DIR/tokens.txt" ]; then
        local token_count
        token_count=$(wc -l < "$DATA_DIR/tokens.txt")
        echo "✅ Found $token_count tokens" >> "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md"
    else
        echo "❌ No tokens found" >> "$PROJECT_DIR/DEPLOYMENT_SUMMARY.md"
    fi
    
    log_success "Deployment summary created"
}

# Test API with send_request
test_api_with_send_request() {
    log_step "Testing API functionality..."
    
    # Check if send_request.sh exists
    if [ -f "$SCRIPT_DIR/send_request.sh" ]; then
        log_command "Testing API with send_request.sh..."
        
        # Make script executable
        chmod +x "$SCRIPT_DIR/send_request.sh"
        
        # Run test in background with timeout
        timeout 30 bash "$SCRIPT_DIR/send_request.sh" &> /dev/null &
        local test_pid=$!
        
        # Wait for test to complete
        if wait "$test_pid" 2>/dev/null; then
            log_success "API test completed successfully"
        else
            log_warning "API test timed out or failed"
            log_info "You can test manually: bash $SCRIPT_DIR/send_request.sh"
        fi
    else
        log_warning "send_request.sh not found"
    fi
}

# Create utility scripts
create_utility_scripts() {
    log_step "Creating utility scripts..."
    
    # Create server management script
    cat > "$PROJECT_DIR/manage-server.sh" << 'EOF'
#!/bin/bash

# K2Think API Server Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

case "${1:-}" in
    start)
        log_info "Starting K2Think API server..."
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        nohup python3 k2think_proxy.py &> "$LOG_FILE" &
        echo $! > "$PID_FILE"
        log_success "Server started"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping server (PID: $pid)..."
                kill "$pid"
                rm -f "$PID_FILE"
                log_success "Server stopped"
            else
                log_warning "Server is not running"
                rm -f "$PID_FILE"
            fi
        else
            log_warning "PID file not found"
        fi
        ;;
    restart)
        "$0" stop
        sleep 2
        "$0" start
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            log_success "Server is running (PID: $(cat "$PID_FILE"))"
        else
            log_warning "Server is not running"
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            log_error "Log file not found: $LOG_FILE"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Show server status"
        echo "  logs    - Show server logs"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$PROJECT_DIR/manage-server.sh"
    
    # Create Python utility script
    cat > "$PROJECT_DIR/python-k2" << 'EOF'
#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from venv import Activation

# Activate virtual environment
activate_path = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate_this.py')
if os.path.exists(activate_path):
    with open(activate_path) as f:
        exec(f.read(), {'__file__': activate_path})

# Import and run the main application
if __name__ == "__main__":
    from k2think_proxy import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)
EOF
    
    chmod +x "$PROJECT_DIR/python-k2"
    
    # Create activation script
    cat > "$PROJECT_DIR/activate-k2.sh" << 'EOF'
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
EOF
    
    chmod +x "$PROJECT_DIR/activate-k2.sh"
    
    log_success "Utility scripts created"
}

# Display usage instructions
display_usage_instructions() {
    log_step "Displaying usage instructions..."
    
    echo
    echo -e "${BOLD}${GREEN}🎉 K2Think API Proxy Deployment Complete!${NC}"
    echo "=" * 50
    echo
    echo -e "${BLUE}📋 Server Information:${NC}"
    echo "  🌐 Server URL: http://localhost:7001"
    echo "  🔑 API Key: $(grep VALID_API_KEY "$ENV_FILE" | cut -d'=' -f2)"
    echo "  📄 Log File: $SERVER_LOG"
    echo "  🔧 PID File: $PID_FILE"
    echo
    echo -e "${BLUE}🚀 Quick Start Commands:${NC}"
    echo "  1️⃣ Activate environment: source $PROJECT_DIR/activate-k2.sh"
    echo "  2️⃣ Test API: bash $SCRIPT_DIR/send_request.sh"
    echo "  3️⃣ Manage server: $PROJECT_DIR/manage-server.sh {start|stop|restart|status|logs}"
    echo "  4️⃣ Run Python: $PROJECT_DIR/python-k2"
    echo
    echo -e "${BLUE}🔗 API Endpoints:${NC}"
    echo "  💬 Chat: http://localhost:7001/v1/chat/completions"
    echo "  📋 Models: http://localhost:7001/v1/models"
    echo "  ❤️ Health: http://localhost:7001/health"
    echo
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "  📖 Full docs: $PROJECT_DIR/CLAUDE.md"
    echo "  📊 Deployment summary: $PROJECT_DIR/DEPLOYMENT_SUMMARY.md"
    echo
}

# Show final status
show_final_status() {
    echo
    log_step "Final status check..."
    
    # Check server status
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log_success "✅ Server is running"
    else
        log_warning "⚠️ Server is not running"
    fi
    
    # Check token status
    if [ -f "$DATA_DIR/tokens.txt" ] && [ -s "$DATA_DIR/tokens.txt" ]; then
        local token_count
        token_count=$(wc -l < "$DATA_DIR/tokens.txt")
        log_success "✅ $token_count tokens available"
    else
        log_warning "⚠️ No tokens available - please add tokens to $DATA_DIR/tokens.txt"
    fi
    
    # Check configuration
    if [ -f "$ENV_FILE" ]; then
        log_success "✅ Configuration file exists"
    else
        log_warning "⚠️ Configuration file missing"
    fi
    
    log_success "Deployment process completed successfully!"
}

# Main execution flow
main() {
    echo -e "${BOLD}${CYAN}🚀 K2Think API Proxy - Enhanced Deployment Script${NC}"
    echo "=" * 60
    echo
    
    check_system_requirements
    setup_project_directory
    setup_credentials
    setup_environment
    setup_configuration
    acquire_tokens
    deploy_server
    create_deployment_summary
    test_api_with_send_request
    create_utility_scripts
    display_usage_instructions
    show_final_status
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
