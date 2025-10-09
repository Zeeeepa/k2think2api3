#!/bin/bash
# Complete K2Think API Deployment Script
# Clone → Setup → Deploy → Validate → Monitor
# One script to rule them all!

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================
REPO_URL="https://github.com/Zeeeepa/k2think2api3.git"
PROJECT_DIR="k2think2api3"
BRANCH="${1:-main}"
PORT="${PORT:-7000}"
API_URL="http://localhost:$PORT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}============================================================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}============================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BOLD}${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# PHASE 1: CLONE & SETUP
# ============================================================================

phase_clone_setup() {
    print_header "PHASE 1: Clone & Setup"
    
    # Clone or update repository
    if [ -d "$PROJECT_DIR" ]; then
        print_info "Project directory exists, updating..."
        cd "$PROJECT_DIR"
        
        git fetch origin
        print_step "Checking out branch: $BRANCH"
        
        git checkout "$BRANCH" || {
            print_warning "Creating branch from remote..."
            git checkout -b "$BRANCH" "origin/$BRANCH" || {
                print_error "Failed to checkout branch $BRANCH"
                exit 1
            }
        }
        
        git pull origin "$BRANCH" || print_warning "Could not pull updates, continuing..."
    else
        print_step "Cloning repository..."
        git clone "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        
        if [ "$BRANCH" != "main" ]; then
            print_step "Checking out branch: $BRANCH"
            git checkout "$BRANCH" || git checkout -b "$BRANCH" "origin/$BRANCH"
        fi
    fi
    
    print_success "Repository ready!"
    
    # Run setup
    print_step "Running setup..."
    chmod +x setup.sh deploy.sh send_request.sh 2>/dev/null || true
    
    # Check if setup.sh exists
    if [ ! -f "setup.sh" ]; then
        print_error "setup.sh not found in repository!"
        exit 1
    fi
    
    bash setup.sh
    print_success "Setup complete!"
}

# ============================================================================
# PHASE 2: DEPLOY SERVER
# ============================================================================

phase_deploy() {
    print_header "PHASE 2: Deploy Server"
    
    print_step "Starting K2Think API server on port $PORT..."
    
    # Stop existing server if running
    if [ -f ".server.pid" ]; then
        OLD_PID=$(cat .server.pid)
        if kill -0 "$OLD_PID" 2>/dev/null; then
            print_info "Stopping existing server (PID: $OLD_PID)..."
            kill "$OLD_PID"
            sleep 2
        fi
    fi
    
    # Start server
    bash deploy.sh
    
    # Wait for server to be ready
    print_step "Waiting for server to initialize..."
    MAX_WAIT=30
    WAITED=0
    
    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -s "$API_URL/health" >/dev/null 2>&1; then
            print_success "Server is ready!"
            break
        fi
        sleep 1
        WAITED=$((WAITED + 1))
        echo -n "."
    done
    echo ""
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        print_error "Server failed to start within $MAX_WAIT seconds"
        print_info "Check logs: tail -f server.log"
        exit 1
    fi
}

# ============================================================================
# PHASE 3: VALIDATE WITH OPENAI API CALL
# ============================================================================

phase_validate() {
    print_header "PHASE 3: Validate Deployment"
    
    # Load API key from .env
    if [ -f ".env" ]; then
        export $(cat .env | grep VALID_API_KEY | xargs)
    fi
    
    if [ -z "$VALID_API_KEY" ]; then
        print_warning "No API key found in .env file"
        print_info "Skipping OpenAI validation (configure VALID_API_KEY in .env to enable)"
        print_success "Server is running and ready for requests"
        return 0
    fi
    
    # Check token availability
    print_step "Checking token availability..."
    TOKEN_COUNT=$(curl -s "$API_URL/health" | grep -o '"active":[0-9]*' | cut -d':' -f2 || echo "0")
    
    if [ "$TOKEN_COUNT" = "0" ]; then
        print_warning "No active tokens available (K2Think credentials may be invalid)"
        print_info "Validation will likely fail without valid tokens"
        print_info "To fix: Update accounts.txt with valid K2Think credentials"
    else
        print_success "Found $TOKEN_COUNT active token(s)"
    fi
    
    print_step "Testing OpenAI-compatible API endpoint..."
    
    # Create test script
    cat > /tmp/test_openai_complete.py << 'PYEOF'
import sys
import os
from openai import OpenAI

# Configuration
API_KEY = os.getenv("VALID_API_KEY", "sk-test-key")
BASE_URL = os.getenv("API_URL", "http://localhost:7000/v1")

print("\n" + "="*80)
print("🧪 K2Think API - OpenAI Client Validation Test")
print("="*80)

try:
    # Initialize OpenAI client
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    
    print(f"\n📡 Testing connection to: {BASE_URL}")
    print(f"🔑 Using API key: {API_KEY[:20]}...")
    
    # Send test request
    print("\n📤 Sending test message: 'What is your model name?'")
    print("⏳ Waiting for response...\n")
    
    response = client.chat.completions.create(
        model="k2-think",
        messages=[
            {"role": "user", "content": "What is your model name? Reply in one sentence."}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    # Print formatted response
    print("─"*80)
    print("📥 RESPONSE RECEIVED")
    print("─"*80)
    
    print(f"\n🤖 Model: {response.model}")
    print(f"🆔 ID: {response.id}")
    print(f"📅 Created: {response.created}")
    print(f"🎯 Finish Reason: {response.choices[0].finish_reason}")
    
    print(f"\n💬 Response Content:")
    print("┌" + "─"*78 + "┐")
    
    content = response.choices[0].message.content
    for line in content.split('\n'):
        print(f"│ {line:<76} │")
    
    print("└" + "─"*78 + "┘")
    
    print(f"\n📊 Token Usage:")
    print(f"   • Prompt tokens: {response.usage.prompt_tokens}")
    print(f"   • Completion tokens: {response.usage.completion_tokens}")
    print(f"   • Total tokens: {response.usage.total_tokens}")
    
    print("\n" + "="*80)
    print("✅ VALIDATION SUCCESSFUL!")
    print("="*80)
    print("\n🎉 K2Think API is working correctly with OpenAI client!")
    
    sys.exit(0)
    
except Exception as e:
    print("\n" + "="*80)
    print("❌ VALIDATION FAILED")
    print("="*80)
    print(f"\n🔴 Error: {str(e)}")
    print("\n💡 Troubleshooting:")
    print("   1. Check if server is running: curl http://localhost:7000/health")
    print("   2. Verify accounts.txt has valid K2Think credentials")
    print("   3. Check server logs: tail -f server.log")
    print("")
    sys.exit(1)
PYEOF
    
    # Run validation with proper environment
    export API_URL="$API_URL/v1"
    
    # Activate venv if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 /tmp/test_openai_complete.py
    VALIDATION_EXIT=$?
    
    rm -f /tmp/test_openai_complete.py
    
    if [ $VALIDATION_EXIT -eq 0 ]; then
        print_success "Validation passed!"
        return 0
    else
        print_warning "Validation failed (this is normal with test/invalid credentials)"
        print_info "Server is running but may need valid K2Think credentials"
        print_info "Update accounts.txt with valid credentials and restart: bash deploy.sh"
        return 0  # Don't fail deployment
    fi
}

# ============================================================================
# PHASE 4: CONTINUOUS MONITORING
# ============================================================================

phase_monitor() {
    print_header "PHASE 4: Server Ready - Continuous Operation"
    
    print_success "Deployment complete! Server is now running."
    echo ""
    
    # Print server information
    echo -e "${BOLD}🌐 Server Information:${NC}"
    echo -e "   ${CYAN}• API URL:${NC} $API_URL/v1"
    echo -e "   ${CYAN}• Health Check:${NC} $API_URL/health"
    echo -e "   ${CYAN}• Models Endpoint:${NC} $API_URL/v1/models"
    echo -e "   ${CYAN}• Chat Endpoint:${NC} $API_URL/v1/chat/completions"
    echo ""
    
    # Print usage examples
    echo -e "${BOLD}📝 Usage Examples:${NC}"
    echo ""
    echo -e "${YELLOW}# Python OpenAI Client:${NC}"
    cat << 'USAGE1'
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",  # From .env file
    base_url="http://localhost:7000/v1"
)

response = client.chat.completions.create(
    model="k2-think",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
USAGE1
    
    echo ""
    echo -e "${YELLOW}# cURL Request:${NC}"
    echo 'curl -X POST http://localhost:7000/v1/chat/completions \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -H "Authorization: Bearer YOUR_API_KEY" \'
    echo '  -d '"'"'{'
    echo '    "model": "k2-think",'
    echo '    "messages": [{"role": "user", "content": "Hello!"}]'
    echo '  }'"'"
    
    echo ""
    echo -e "${BOLD}🛠️  Management Commands:${NC}"
    echo -e "   ${CYAN}• View logs:${NC} tail -f $(pwd)/server.log"
    echo -e "   ${CYAN}• Stop server:${NC} kill \$(cat $(pwd)/.server.pid)"
    echo -e "   ${CYAN}• Restart:${NC} bash deploy.sh"
    echo -e "   ${CYAN}• Health check:${NC} curl $API_URL/health"
    echo ""
    
    # Show server status
    if [ -f ".server.pid" ]; then
        PID=$(cat .server.pid)
        if kill -0 "$PID" 2>/dev/null; then
            print_success "Server is running (PID: $PID)"
        else
            print_error "Server process not found!"
        fi
    fi
    
    echo ""
    print_info "Server will continue running in the background"
    print_info "Press Ctrl+C to exit this script (server will keep running)"
    echo ""
    
    # Optional: Follow logs
    if [ -f "server.log" ]; then
        echo -e "${BOLD}📊 Live Server Logs (Ctrl+C to stop viewing):${NC}"
        echo -e "${CYAN}$(printf '─%.0s' {1..80})${NC}"
        tail -f server.log
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header "🚀 K2Think API - Complete Deployment System"
    
    echo -e "${BOLD}Configuration:${NC}"
    echo -e "   ${CYAN}• Repository:${NC} $REPO_URL"
    echo -e "   ${CYAN}• Branch:${NC} $BRANCH"
    echo -e "   ${CYAN}• Port:${NC} $PORT"
    echo -e "   ${CYAN}• Working Directory:${NC} $(pwd)/$PROJECT_DIR"
    echo ""
    
    # Execute phases
    phase_clone_setup
    phase_deploy
    phase_validate
    phase_monitor
}

# Handle Ctrl+C gracefully
trap 'echo ""; print_info "Script interrupted. Server continues running."; exit 0' INT

# Run main function
main

# End of script
