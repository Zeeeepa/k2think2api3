#!/bin/bash
# CSDS: Clone, Setup, Deploy, and Send request
# One-command deployment and testing for K2Think API Proxy
# Enhanced version with comprehensive error handling

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Error handler
error_exit() {
    log_error "Deployment failed: $1"
    log_info "Check the error above for details"
    log_info "Need help? See: https://github.com/Zeeeepa/k2think2api3/blob/main/DEPLOYMENT_URL_GUIDE.md"
    exit 1
}

# Validate prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for git
    if ! command -v git &> /dev/null; then
        error_exit "git is not installed. Please install git first."
    fi
    
    # Check for python3
    if ! command -v python3 &> /dev/null; then
        error_exit "python3 is not installed. Please install Python 3.8+ first."
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        error_exit "Python 3.8+ is required (you have $PYTHON_VERSION)"
    fi
    
    log_success "All prerequisites met (Python $PYTHON_VERSION)"
}

# Validate credentials
validate_credentials() {
    if [ -z "${K2_EMAIL:-}" ] || [ -z "${K2_PASSWORD:-}" ]; then
        return 1
    fi
    
    # Basic email validation
    if [[ ! "$K2_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_error "Invalid email format: $K2_EMAIL"
        return 1
    fi
    
    # Check password is not empty
    if [ ${#K2_PASSWORD} -lt 6 ]; then
        log_error "Password is too short (minimum 6 characters)"
        return 1
    fi
    
    return 0
}

# Get credentials interactively
get_credentials() {
    if [ ! -f "accounts.txt" ] && ! validate_credentials; then
        echo ""
        log_info "K2 Account Setup Required"
        echo "================================"
        echo "Please enter your K2 credentials:"
        echo ""
        
        # Read email
        read -p "📧 Email: " K2_EMAIL
        export K2_EMAIL
        
        # Read password (hidden)
        read -sp "🔒 Password: " K2_PASSWORD
        echo ""
        export K2_PASSWORD
        
        # Validate
        if ! validate_credentials; then
            error_exit "Invalid credentials provided"
        fi
        
        log_success "Credentials validated"
    fi
}

# Check port availability
check_port() {
    local port=${1:-7000}
    
    if command -v lsof &> /dev/null; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Port $port is already in use"
            log_info "To stop existing server: kill \$(lsof -ti:$port)"
            read -p "Kill existing process and continue? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                lsof -ti:$port | xargs kill -9 2>/dev/null || true
                log_success "Stopped existing process on port $port"
                sleep 2
            else
                error_exit "Cannot continue with port $port in use"
            fi
        fi
    fi
}

# Main deployment
REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
PROJECT_DIR="$HOME/k2think2api3"
BRANCH="${1:-main}"

echo "🚀 K2Think API - Enhanced One-Command Deployment"
echo "================================================="
echo "📌 Branch: $BRANCH"
echo "📁 Target: $PROJECT_DIR"
echo ""

# Step 1: Check prerequisites
check_prerequisites

# Step 2: Check port
check_port 7000

# Step 3: Clone or update repository
if [ -d "$PROJECT_DIR" ]; then
    log_info "Project directory exists, updating..."
    cd "$PROJECT_DIR"
    
    # Stash any local changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warning "Local changes detected, stashing..."
        git stash push -m "Auto-stash before csds.sh update $(date +%Y%m%d_%H%M%S)" || true
    fi
    
    # Fetch latest changes
    log_info "Fetching latest changes..."
    git fetch origin || error_exit "Failed to fetch from remote"
    
    # Checkout the specified branch
    log_info "Checking out branch: $BRANCH"
    if ! git checkout "$BRANCH" 2>/dev/null; then
        log_warning "Branch $BRANCH not found locally, trying remote..."
        if ! git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null; then
            error_exit "Failed to checkout branch $BRANCH"
        fi
    fi
    
    # Pull latest changes
    log_info "Pulling latest changes..."
    if ! git pull origin "$BRANCH"; then
        log_warning "Could not pull updates, continuing with existing code"
    else
        log_success "Repository updated"
    fi
else
    log_info "Cloning repository..."
    if ! git clone "$REPO_URL" "$PROJECT_DIR"; then
        error_exit "Failed to clone repository"
    fi
    
    cd "$PROJECT_DIR"
    
    # Checkout the specified branch if not main
    if [ "$BRANCH" != "main" ]; then
        log_info "Checking out branch: $BRANCH"
        if ! git checkout "$BRANCH"; then
            if ! git checkout -b "$BRANCH" "origin/$BRANCH"; then
                error_exit "Failed to checkout branch $BRANCH"
            fi
        fi
    fi
    
    log_success "Repository cloned"
fi

# Step 4: Validate we're in the right directory
if [ ! -f "setup.sh" ] || [ ! -f "deploy.sh" ]; then
    error_exit "Invalid repository structure (missing setup.sh or deploy.sh)"
fi

# Step 5: Make scripts executable
log_info "Setting script permissions..."
chmod +x setup.sh deploy.sh send_request.sh 2>/dev/null || error_exit "Failed to set script permissions"

# Step 6: Get credentials
get_credentials

# Step 7: Run setup
echo ""
log_info "Running setup..."
if ! bash setup.sh; then
    error_exit "Setup failed"
fi
log_success "Setup completed"

# Step 8: Deploy server
echo ""
log_info "Starting server..."
if ! bash deploy.sh; then
    error_exit "Server deployment failed"
fi
log_success "Server started"

# Step 9: Wait for server to be ready
echo ""
log_info "Waiting for server to be fully ready..."
sleep 3

# Verify server is running
if [ -f ".server.pid" ]; then
    SERVER_PID=$(cat .server.pid)
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        log_error "Server process died unexpectedly"
        log_info "Check logs: tail -50 server.log"
        exit 1
    fi
else
    log_warning "Could not find .server.pid file"
fi

# Check if server is responding
log_info "Testing server health..."
for i in {1..10}; do
    if curl -s -f http://localhost:7000/health >/dev/null 2>&1; then
        log_success "Server is responding"
        break
    fi
    if [ $i -eq 10 ]; then
        log_warning "Server health check timeout (server may still be starting)"
    else
        sleep 1
    fi
done

# Step 10: Send test request
echo ""
log_info "Sending test request..."
echo ""
if ! bash send_request.sh; then
    log_warning "Test request failed (server might still be initializing)"
    log_info "You can manually test with: cd $PROJECT_DIR && bash send_request.sh"
else
    log_success "Test request completed"
fi

# Step 11: Display summary
echo ""
echo "=============================================="
log_success "Deployment Complete!"
echo "=============================================="
echo ""

# Extract and display API key
if [ -f ".env" ]; then
    API_KEY=$(grep VALID_API_KEY .env | cut -d'=' -f2 2>/dev/null || echo "")
    if [ -n "$API_KEY" ]; then
        echo "🔑 API Key:"
        echo "   $API_KEY"
        echo ""
        echo "📋 Environment Variables (copy to use):"
        echo "   export OPENAI_API_KEY=\"$API_KEY\""
        echo "   export OPENAI_BASE_URL=\"http://localhost:7000/v1\""
        echo ""
        
        # Optionally export for current shell
        export OPENAI_API_KEY="$API_KEY"
        export OPENAI_BASE_URL="http://localhost:7000/v1"
    fi
fi

# Display management commands
echo "📊 Server Management:"
echo "   Status:  curl http://localhost:7000/health"
echo "   Logs:    tail -f $PROJECT_DIR/server.log"
echo "   Stop:    kill \$(cat $PROJECT_DIR/.server.pid)"
echo "   Restart: cd $PROJECT_DIR && bash deploy.sh"
echo ""

echo "🐍 Python Usage:"
echo "   source $PROJECT_DIR/venv/bin/activate"
echo "   python your_script.py"
echo ""

echo "📚 Documentation:"
echo "   Installation: https://github.com/Zeeeepa/k2think2api3/blob/main/INSTALL.md"
echo "   Quick Start:  https://github.com/Zeeeepa/k2think2api3/blob/main/QUICKSTART.md"
echo "   URL Guide:    https://github.com/Zeeeepa/k2think2api3/blob/main/DEPLOYMENT_URL_GUIDE.md"
echo ""

log_success "Server is running in the background at http://localhost:7000"
echo ""

