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

# Server management functions (merged from manage-server.sh)
server_start() {
    log_step "Starting K2Think API server..."
    deploy_server
}

server_stop() {
    log_step "Stopping server..."
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_command "Stopping server (PID: $pid)..."
            kill "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "Force killing server..."
                kill -9 "$pid" 2>/dev/null
            fi
            rm -f "$PID_FILE"
            log_success "Server stopped"
        else
            log_warning "Server is not running"
            rm -f "$PID_FILE"
        fi
    else
        log_warning "PID file not found"
    fi
}

server_restart() {
    log_step "Restarting server..."
    server_stop
    sleep 2
    server_start
}

server_status() {
    log_info "Checking server status..."
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        local pid
        pid=$(cat "$PID_FILE")
        log_success "Server is running (PID: $pid)"

        # Load port from .env if available
        if [ -f "$ENV_FILE" ]; then
            set -a
            source "$ENV_FILE"
            set +a
        fi
        local port=${PORT:-7001}

        # Health check
        if curl -s "http://localhost:$port/health" &> /dev/null; then
            log_success "Server health check passed"
        else
            log_warning "Server health check failed"
        fi
    else
        log_warning "Server is not running"
    fi
}

server_logs() {
    if [ -f "$SERVER_LOG" ]; then
        log_info "Showing server logs (Ctrl+C to exit)..."
        tail -f "$SERVER_LOG"
    else
        log_error "Log file not found: $SERVER_LOG"
    fi
}

server_test() {
    log_info "Testing API..."
    if [ -f "$SCRIPT_DIR/send_request.sh" ]; then
        bash "$SCRIPT_DIR/send_request.sh"
    else
        log_error "send_request.sh not found"
    fi
}

# Environment activation (merged from activate-k2.sh)
activate_environment() {
    log_step "Activating K2Think environment..."

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at $VENV_DIR"
        log_info "Please run deployment first: bash $0"
        return 1
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"

    # Load configuration
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_success "Environment variables loaded"
    else
        log_error "Environment file not found: $ENV_FILE"
        return 1
    fi

    # Set OpenAI environment variables
    export OPENAI_API_KEY="${VALID_API_KEY:-}"
    export OPENAI_BASE_URL="http://localhost:${PORT:-7001}/v1"

    echo
    echo -e "${BLUE}📋 Environment Status:${NC}"
    echo "  Python: $(which python3)"
    echo "  API Key: ${OPENAI_API_KEY:0:20}..."
    echo "  Base URL: $OPENAI_BASE_URL"
    echo
    echo -e "${BLUE}💡 Usage tips:${NC}"
    echo "  • OpenAI client will work automatically with environment variables"
    echo "  • Run Python scripts: python3 your_script.py"
    echo "  • Or use the wrapper: $0 python your_script.py"
    echo

    log_success "K2Think environment activated!"
}

# Python wrapper (merged from python-k2)
run_python() {
    # Ensure environment is set up
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found. Please run deployment first."
        exit 1
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        log_error "Failed to activate virtual environment"
        exit 1
    }

    # Load configuration
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi

    # Set OpenAI environment variables
    export OPENAI_API_KEY="${VALID_API_KEY:-}"
    export OPENAI_BASE_URL="http://localhost:${PORT:-7001}/v1"

    # Execute Python with all arguments
    log_command "Running Python with: $*"
    python3 "$@"
}

# Update quick-test.py to be standalone
update_quick_test() {
    log_step "Updating quick-test.py..."

    cat > "$PROJECT_DIR/quick-test.py" << 'EOF'
#!/usr/bin/env python3
"""
Quick K2Think API test script
Run with: bash scripts/all.sh test-quick
Or directly: python3 quick-test.py (if environment is activated)
"""

import sys
import os

def test_with_openai():
    try:
        from openai import OpenAI
        client = OpenAI()  # Uses environment variables

        print("🧪 Quick K2Think API Test")
        print("=" * 40)

        response = client.chat.completions.create(
            model="MBZUAI-IFM/K2-Think",
            messages=[{"role": "user", "content": "Hello! What are you?"}],
            max_tokens=100
        )

        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print("✅ Test successful!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_with_requests():
    try:
        import requests
        import json

        # Try to get API key from environment
        api_key = os.environ.get('VALID_API_KEY', 'sk-k2think-proxy-default')

        print("🧪 Quick K2Think API Test (Direct HTTP)")
        print("=" * 50)

        response = requests.post(
            "http://localhost:7001/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "MBZUAI-IFM/K2-Think",
                "messages": [{"role": "user", "content": "Hello! What are you?"}],
                "max_tokens": 100
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            tokens = data['usage']['total_tokens']

            print(f"Response: {content}")
            print(f"Tokens used: {tokens}")
            print("✅ Test successful!")
            return True
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("Testing K2Think API connection...")

    # Try OpenAI client first
    if test_with_openai():
        return

    # Fallback to direct requests
    print("\n🔄 Falling back to direct HTTP request...")
    if test_with_requests():
        return

    print("\n❌ All test methods failed")
    print("Please ensure:")
    print("1. Server is running: bash scripts/all.sh start")
    print("2. Environment is activated: bash scripts/all.sh activate")
    print("3. Check server logs: bash scripts/all.sh logs")
    sys.exit(1)

if __name__ == "__main__":
    main()
EOF

    chmod +x "$PROJECT_DIR/quick-test.py"
    log_success "quick-test.py updated"
}

# Quick test runner
run_quick_test() {
    log_step "Running quick API test..."

    # Ensure environment is set up for the test
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found. Please run deployment first."
        exit 1
    fi

    # Activate environment and set variables
    source "$VENV_DIR/bin/activate"
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        export OPENAI_API_KEY="${VALID_API_KEY:-}"
        export OPENAI_BASE_URL="http://localhost:${PORT:-7001}/v1"
    fi

    # Run the test
    python3 "$PROJECT_DIR/quick-test.py"
}

# Show comprehensive help
show_help() {
    echo -e "${BOLD}${CYAN}K2Think API Proxy - All-in-One Management Script${NC}"
    echo
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0                    # Full deployment"
    echo "  $0 [COMMAND]          # Run specific command"
    echo
    echo -e "${BLUE}Deployment Commands:${NC}"
    echo "  deploy                # Deploy from scratch (default)"
    echo "  setup                 # Quick setup (assumes deps installed)"
    echo
    echo -e "${BLUE}Server Management:${NC}"
    echo "  start                 # Start the server"
    echo "  stop                  # Stop the server"
    echo "  restart               # Restart the server"
    echo "  status                # Check server status"
    echo "  logs                  # View server logs"
    echo "  test                  # Test API with send_request.sh"
    echo "  test-quick            # Quick API test"
    echo
    echo -e "${BLUE}Environment Commands:${NC}"
    echo "  activate              # Activate environment (sourced)"
    echo "  python [args]         # Run Python with environment set up"
    echo "  shell                 # Start interactive shell with environment"
    echo
    echo -e "${BLUE}Utility Commands:${NC}"
    echo "  update-test           # Update quick-test.py"
    echo "  help, -h, --help      # Show this help"
    echo
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0                    # Full deployment"
    echo "  $0 start              # Start server"
    echo "  $0 test-quick         # Quick API test"
    echo "  $0 python script.py   # Run Python with environment"
    echo "  source $0 activate    # Activate environment in current shell"
    echo
}

# Interactive shell
start_shell() {
    log_step "Starting interactive shell with K2Think environment..."

    # Ensure environment is set up
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found. Please run deployment first."
        exit 1
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Load configuration
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        export OPENAI_API_KEY="${VALID_API_KEY:-}"
        export OPENAI_BASE_URL="http://localhost:${PORT:-7001}/v1"
    fi

    echo
    echo -e "${GREEN}🚀 K2Think environment loaded!${NC}"
    echo -e "${BLUE}Commands available:${NC}"
    echo "  python3 your_script.py"
    echo "  quick-test.py"
    echo "  exit  (to leave shell)"
    echo

    # Start interactive shell
    "${SHELL:-bash}"
}

# Quick setup (assumes dependencies are installed)
quick_setup() {
    log_step "Quick setup (assuming dependencies are installed)..."

    setup_project_directory
    setup_credentials
    setup_configuration
    acquire_tokens

    log_success "Quick setup completed!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "  $0 start              # Start server"
    echo "  $0 test-quick         # Test API"
    echo "  source $0 activate    # Activate environment"
}

# Main deployment function
deploy_full() {
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
    update_quick_test
    display_usage_instructions
    show_final_status
}

# Main command router
main() {
    # Parse command
    local command="${1:-deploy}"

    case "$command" in
        # Deployment commands
        "deploy"|"")
            deploy_full
            ;;
        "setup")
            echo -e "${BOLD}${CYAN}🔧 K2Think API Proxy - Quick Setup${NC}"
            echo "=" * 40
            quick_setup
            ;;
        # Server management
        "start")
            server_start
            ;;
        "stop")
            server_stop
            ;;
        "restart")
            server_restart
            ;;
        "status")
            server_status
            ;;
        "logs")
            server_logs
            ;;
        "test")
            server_test
            ;;
        "test-quick")
            run_quick_test
            ;;
        # Environment commands
        "activate")
            activate_environment
            ;;
        "python")
            shift
            run_python "$@"
            ;;
        "shell")
            start_shell
            ;;
        # Utility commands
        "update-test")
            update_quick_test
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}


# Enhanced usage instructions
display_usage_instructions() {
    echo -e "${CYAN}🚀 Usage Instructions:${NC}"
    echo ""

    echo -e "${GREEN}🎯 All-in-One Script Commands:${NC}"
    echo "   bash scripts/all.sh deploy         # Full deployment"
    echo "   bash scripts/all.sh start          # Start server"
    echo "   bash scripts/all.sh stop           # Stop server"
    echo "   bash scripts/all.sh status         # Check server status"
    echo "   bash scripts/all.sh logs           # View server logs"
    echo "   bash scripts/all.sh test           # Test API with send_request.sh"
    echo "   bash scripts/all.sh test-quick     # Quick API test"
    echo "   bash scripts/all.sh python script.py # Run Python with environment"
    echo "   source bash scripts/all.sh activate # Activate environment"
    echo ""

    echo -e "${GREEN}🐍 Python Usage:${NC}"
    echo "   bash scripts/all.sh python your_script.py"
    echo "   bash scripts/all.sh test-quick           # Quick test"
    echo "   python3 quick-test.py                    # Direct test (if env activated)"
    echo ""

    echo -e "${CYAN}📚 Python Code Examples:${NC}"
    echo ""
    echo "   # Basic usage"
    echo "   from openai import OpenAI"
    echo "   client = OpenAI()  # Uses environment variables"
    echo ""
    echo "   response = client.chat.completions.create("
    echo "       model=\"MBZUAI-IFM/K2-Think\","
    echo "       messages=[{\"role\": \"user\", \"content\": \"Hello!\"}]"
    echo "   )"
    echo "   print(response.choices[0].message.content)"
    echo ""

    echo "   # Streaming"
    echo "   stream = client.chat.completions.create("
    echo "       model=\"MBZUAI-IFM/K2-Think\","
    echo "       messages=[{\"role\": \"user\", \"content\": \"Count to 5\"}],"
    echo "       stream=True"
    echo "   )"
    echo "   for chunk in stream:"
    echo "       if chunk.choices[0].delta.content:"
    echo "           print(chunk.choices[0].delta.content, end=\"\")"
    echo ""

    echo -e "${CYAN}🌐 cURL Examples:${NC}"
    echo ""
    if [ -n "${API_KEY:-}" ]; then
        cat << EOF
   # Basic request
   curl http://localhost:${PORT:-7001}/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${API_KEY}" \
     -d '{
       "model": "MBZUAI-IFM/K2-Think",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'

   # Models list
   curl http://localhost:${PORT:-7001}/v1/models \
     -H "Authorization: Bearer ${API_KEY}"

   # Health check
   curl http://localhost:${PORT:-7001}/health
EOF
    fi
    echo ""
}

# Final status display
show_final_status() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  🌟 K2Think API Server is RUNNING and READY! 🌟          ║"
    echo "║                                                            ║"
    echo "║  Project: $PROJECT_DIR"
    echo "║  Server:  http://localhost:${PORT:-7001}/v1"
    echo "║  Health:  http://localhost:${PORT:-7001}/health"
    echo "║                                                            ║"
    echo "║  Quick Start: bash scripts/all.sh test-quick 🚀           ║"
    echo "║  Management: bash scripts/all.sh {start|stop|status}       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    echo -e "${YELLOW}📊 Quick Commands:${NC}"
    echo "   • Test API:     bash scripts/all.sh test-quick"
    echo "   • View logs:    bash scripts/all.sh logs"
    echo "   • Server info:  bash scripts/all.sh status"
    echo "   • Restart:      bash scripts/all.sh restart"
    echo ""

    echo -e "${CYAN}📚 Documentation:${NC}"
    echo "   • Full docs:    See README.md and QUICKSTART.md"
    echo "   • API reference: http://localhost:${PORT:-7001}/docs"
    echo "   • Admin panel:  http://localhost:${PORT:-7001}/admin/tokens/stats"
    echo ""
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi