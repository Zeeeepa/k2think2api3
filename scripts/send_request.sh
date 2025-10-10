#!/bin/bash

# K2Think API Proxy - Test Script with Interactive Prompts
# Enhanced version with interactive mode and professional output

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

# Configuration
API_URL="http://localhost:7001/v1/chat/completions"
API_KEY_FILE="../.env"
DEFAULT_MESSAGE="Hello! This is a test message. Please respond with a brief greeting."
DEFAULT_MODEL="MBZUAI-IFM/K2-Think"
DEFAULT_MAX_TOKENS=1000
DEFAULT_TEMP=0.7

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_command() { echo -e "${MAGENTA}💻 $1${NC}"; }
log_response() { echo -e "${CYAN}📝 $1${NC}"; }

# Progress indicator
show_spinner() {
    local message="$1"
    local duration="$2"
    local chars=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    
    log_info "$message"
    
    for ((i = 0; i < duration * 10; i++)); do
        printf "\r${CYAN}%s${NC} %d seconds" "${chars[i % 10]}" "$((i / 10))"
        sleep 0.1
    done
    printf "\r${GREEN}✅${NC} Request completed\n"
}

# Get API key from environment file
get_api_key() {
    if [ -f "$API_KEY_FILE" ]; then
        source "$API_KEY_FILE"
        if [ -n "${VALID_API_KEY:-}" ]; then
            echo "$VALID_API_KEY"
            return
        fi
    fi
    
    # Fallback to common default
    echo "sk-k2think-proxy-default"
}

# Test server connectivity
test_connectivity() {
    log_info "Testing server connectivity..."
    
    if curl -s --max-time 5 "http://localhost:7001/health" &> /dev/null; then
        log_success "Server is reachable"
        return 0
    else
        log_error "Server is not reachable at http://localhost:7001"
        log_info "Please ensure the server is running"
        log_info "Start server: cd .. && python3 k2think_proxy.py"
        return 1
    fi
}

# Interactive prompt function
prompt_user() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -ne "${CYAN}💬 $prompt${NC}"
    if [ -n "$default" ]; then
        echo -ne " ${YELLOW}[$default]${NC}: "
    else
        echo -ne ": "
    fi
    
    read -r response
    
    if [ -z "$response" ] && [ -n "$default" ]; then
        response="$default"
    fi
    
    eval "$var_name=\"\$response\""
}

# Yes/no prompt
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    
    while true; do
        echo -ne "${CYAN}❓ $prompt${NC}"
        if [ "$default" = "y" ]; then
            echo -ne " ${YELLOW}[Y/n]${NC}: "
        else
            echo -ne " ${YELLOW}[y/N]${NC}: "
        fi
        
        read -r response
        response="${response:-$default}"
        
        case "${response,,}" in
            y|yes)
                return 0
                ;;
            n|no)
                return 1
                ;;
            *)
                echo -e "${RED}Please enter 'y' or 'n'${NC}"
                ;;
        esac
    done
}

# Select model
select_model() {
    echo -e "${BLUE}🤖 Available Models:${NC}"
    echo "  1) MBZUAI-IFM/K2-Think (shows thinking process)"
    echo "  2) MBZUAI-IFM/K2Think-nothink (hides thinking process)"
    echo
    
    while true; do
        echo -ne "${CYAN}🎯 Select model${NC} ${YELLOW}[1]${NC}: "
        read -r model_choice
        model_choice="${model_choice:-1}"
        
        case "$model_choice" in
            1)
                SELECTED_MODEL="MBZUAI-IFM/K2-Think"
                break
                ;;
            2)
                SELECTED_MODEL="MBZUAI-IFM/K2Think-nothink"
                break
                ;;
            *)
                echo -e "${RED}Please enter 1 or 2${NC}"
                ;;
        esac
    done
    
    log_success "Selected model: $SELECTED_MODEL"
}

# Make API request
make_request() {
    local message="$1"
    local model="$2"
    local stream="$3"
    local max_tokens="$4"
    local temperature="$5"
    
    local api_key
    api_key=$(get_api_key)
    
    local request_data
    request_data=$(cat << EOF
{
  "model": "$model",
  "messages": [
    {
      "role": "user",
      "content": "$message"
    }
  ],
  "max_tokens": $max_tokens,
  "temperature": $temperature,
  "stream": $stream
}
EOF
)
    
    log_command "Sending request to K2Think API..."
    log_command "Model: $model"
    log_command "Message: $message"
    
    local start_time
    start_time=$(date +%s.%N)
    
    if [ "$stream" = "true" ]; then
        # Streaming request
        local response_file
        response_file=$(mktemp)
        
        curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $api_key" \
            -d "$request_data" \
            --no-buffer > "$response_file" &
        
        local curl_pid=$!
        
        # Process streaming response
        echo -e "${CYAN}🌊 Streaming Response:${NC}"
        echo
        
        tail -f "$response_file" 2>/dev/null | while IFS= read -r line; do
            if [[ "$line" =~ ^data: ]]; then
                local data
                data="${line#data: }"
                
                if [ "$data" != "[DONE]" ]; then
                    local content
                    content=$(echo "$data" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        delta = data['choices'][0].get('delta', {})
        if 'content' in delta:
            print(delta['content'], end='')
except:
    pass
" 2>/dev/null || echo "")
                    
                    if [ -n "$content" ]; then
                        echo -n "$content"
                    fi
                fi
            fi
        done &
        
        local tail_pid=$!
        
        # Wait for request to complete
        if wait "$curl_pid" 2>/dev/null; then
            sleep 1
            kill "$tail_pid" 2>/dev/null || true
            echo
            echo
            log_success "Streaming completed"
        else
            kill "$curl_pid" 2>/dev/null || true
            kill "$tail_pid" 2>/dev/null || true
            log_error "Streaming request failed"
            return 1
        fi
        
        rm -f "$response_file"
    else
        # Non-streaming request
        local response
        response=$(curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $api_key" \
            -d "$request_data")
        
        local end_time
        end_time=$(date +%s.%N)
        local duration
        duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
        
        echo -e "${CYAN}📝 Response:${NC}"
        echo
        
        # Parse and display response
        local content
        content=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        print(data['choices'][0]['message']['content'])
    else:
        print('Error: Invalid response format')
        print('Response:', json.dumps(data, indent=2))
except json.JSONDecodeError:
    print('Error: Invalid JSON response')
    print('Response:', repr(sys.stdin.read()))
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null)
        
        if [ -n "$content" ]; then
            echo "$content"
            echo
            
            # Extract usage info
            local usage_info
            usage_info=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'usage' in data:
        usage = data['usage']
        print(f'Prompt tokens: {usage.get("prompt_tokens", "N/A")}')
        print(f'Completion tokens: {usage.get("completion_tokens", "N/A")}')
        print(f'Total tokens: {usage.get("total_tokens", "N/A")}')
except:
    pass
" 2>/dev/null)
            
            if [ -n "$usage_info" ]; then
                echo -e "${MAGENTA}📊 Usage Statistics:${NC}"
                echo "$usage_info"
            fi
            
            echo -e "${MAGENTA}⏱️  Response Time: ${duration}s${NC}"
            log_success "Request completed successfully"
        else
            echo -e "${RED}❌ Failed to parse response${NC}"
            echo "Raw response:"
            echo "$response" | head -20
            return 1
        fi
    fi
}

# Show help
show_help() {
    echo -e "${BOLD}${CYAN}K2Think API Proxy - Test Script${NC}"
    echo
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0                    # Interactive mode"
    echo "  $0 [MESSAGE]          # Send message with defaults"
    echo "  $0 --help, -h         # Show this help"
    echo "  $0 --interactive, -i  # Force interactive mode"
    echo "  $0 --quick, -q        # Quick test with defaults"
    echo
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 \"Hello, how are you?\""
    echo "  $0 --interactive"
    echo "  $0 --quick"
    echo
    echo -e "${BLUE}Configuration:${NC}"
    echo "  API URL: $API_URL"
    echo "  Default model: $DEFAULT_MODEL"
    echo "  Max tokens: $DEFAULT_MAX_TOKENS"
    echo "  Temperature: $DEFAULT_TEMP"
    echo
}

# Main execution
main() {
    # Parse command line arguments
    local user_message=""
    local interactive_mode=true
    local quick_mode=false
    
    for arg in "$@"; do
        case "$arg" in
            --help|-h)
                show_help
                exit 0
                ;;
            --interactive|-i)
                interactive_mode=true
                quick_mode=false
                ;;
            --quick|-q)
                quick_mode=true
                interactive_mode=false
                ;;
            --*)
                log_error "Unknown option: $arg"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$user_message" ]; then
                    user_message="$arg"
                    interactive_mode=false
                else
                    log_error "Too many arguments"
                    show_help
                    exit 1
                fi
                ;;
        esac
    done
    
    echo -e "${BOLD}${CYAN}🧪 K2Think API Proxy - Test Script${NC}"
    echo "=" * 40
    echo
    
    # Test connectivity
    if ! test_connectivity; then
        exit 1
    fi
    
    # Quick mode
    if [ "$quick_mode" = true ]; then
        log_info "Running quick test with defaults..."
        show_spinner "Processing request" 5
        if make_request "$DEFAULT_MESSAGE" "$DEFAULT_MODEL" "false" "$DEFAULT_MAX_TOKENS" "$DEFAULT_TEMP"; then
            log_success "Quick test completed successfully"
        else
            log_error "Quick test failed"
            exit 1
        fi
        exit 0
    fi
    
    # Interactive mode
    if [ "$interactive_mode" = true ]; then
        echo -e "${BLUE}🎯 Interactive Mode${NC}"
        echo
        
        # Get user input
        prompt_user "Enter your message" "$DEFAULT_MESSAGE" "user_message"
        echo
        
        # Select model
        select_model
        echo
        
        # Streaming preference
        local use_streaming="false"
        if prompt_yes_no "Use streaming response?" "n"; then
            use_streaming="true"
        fi
        echo
        
        # Advanced options
        if prompt_yes_no "Configure advanced options?" "n"; then
            echo
            prompt_user "Max tokens" "$DEFAULT_MAX_TOKENS" "max_tokens"
            prompt_user "Temperature (0.0-1.0)" "$DEFAULT_TEMP" "temperature"
        else
            max_tokens="$DEFAULT_MAX_TOKENS"
            temperature="$DEFAULT_TEMP"
        fi
        echo
        
        # Show request summary
        echo -e "${MAGENTA}📋 Request Summary:${NC}"
        echo "  Message: $user_message"
        echo "  Model: $SELECTED_MODEL"
        echo "  Streaming: $use_streaming"
        echo "  Max tokens: ${max_tokens:-$DEFAULT_MAX_TOKENS}"
        echo "  Temperature: ${temperature:-$DEFAULT_TEMP}"
        echo
        
        # Confirm and send
        if prompt_yes_no "Send this request?" "y"; then
            echo
            local estimated_time
            estimated_time=$((max_tokens / 10))
            show_spinner "Processing request" "$estimated_time"
            
            if make_request "$user_message" "$SELECTED_MODEL" "$use_streaming" "${max_tokens:-$DEFAULT_MAX_TOKENS}" "${temperature:-$DEFAULT_TEMP}"; then
                echo
                log_success "Request completed successfully!"
            else
                log_error "Request failed"
                exit 1
            fi
        else
            log_info "Request cancelled"
            exit 0
        fi
    else
        # Non-interactive mode with provided message
        log_info "Sending message: $user_message"
        echo
        
        if make_request "$user_message" "$DEFAULT_MODEL" "false" "$DEFAULT_MAX_TOKENS" "$DEFAULT_TEMP"; then
            echo
            log_success "Request completed successfully!"
        else
            log_error "Request failed"
            exit 1
        fi
    fi
}

# Check dependencies
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
