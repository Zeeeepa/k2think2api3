#!/usr/bin/env python3
"""
Quick test script for K2Think API Proxy
Provides a simple Python interface to test the API
"""

import sys
import os
import json
import time
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
API_URL = "http://localhost:7001/v1/chat/completions"
API_KEY_FILE = ".env"
DEFAULT_MESSAGE = "Hello! This is a quick test. Please respond briefly."
DEFAULT_MODEL = "MBZUAI-IFM/K2-Think"

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def log_info(msg): print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")
def log_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")
def log_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")
def log_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def load_api_key():
    """Load API key from environment file"""
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE) as f:
            for line in f:
                if line.startswith('VALID_API_KEY='):
                    return line.strip().split('=', 1)[1]
    return "sk-k2think-proxy-default"

def test_connectivity():
    """Test server connectivity"""
    try:
        import requests
        response = requests.get("http://localhost:7001/health", timeout=5)
        if response.status_code == 200:
            log_success("Server is reachable")
            return True
        else:
            log_error(f"Server returned status {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Cannot connect to server: {e}")
        return False

def make_request(message, model, stream=False, max_tokens=1000, temperature=0.7):
    """Make API request"""
    import requests
    
    api_key = load_api_key()
    
    request_data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"{Colors.MAGENTA}💻 Sending request...{Colors.NC}")
    print(f"{Colors.MAGENTA}   Model: {model}{Colors.NC}")
    print(f"{Colors.MAGENTA}   Message: {message}{Colors.NC}")
    
    start_time = time.time()
    
    try:
        if stream:
            # Streaming request
            print(f"{Colors.CYAN}🌊 Streaming Response:{Colors.NC}")
            print()
            
            response = requests.post(API_URL, headers=headers, json=request_data, stream=True, timeout=30)
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str != '[DONE]':
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        print(content, end='', flush=True)
                                        full_response += content
                            except json.JSONDecodeError:
                                continue
            
            print()
            print()
            log_success("Streaming completed")
            return full_response
            
        else:
            # Non-streaming request
            response = requests.post(API_URL, headers=headers, json=request_data, timeout=30)
            response.raise_for_status()
            
            end_time = time.time()
            duration = end_time - start_time
            
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"{Colors.CYAN}📝 Response:{Colors.NC}")
                print()
                print(content)
                print()
                
                # Show usage statistics
                if 'usage' in data:
                    usage = data['usage']
                    print(f"{Colors.MAGENTA}📊 Usage Statistics:{Colors.NC}")
                    print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                    print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")
                
                print(f"{Colors.MAGENTA}⏱️  Response Time: {duration:.2f}s{Colors.NC}")
                log_success("Request completed successfully")
                return content
            else:
                log_error("Invalid response format")
                print(f"Raw response: {json.dumps(data, indent=2)}")
                return None
                
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return None

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 K2Think API Proxy - Quick Python Test{Colors.NC}")
    print("=" * 50)
    print()
    
    # Test connectivity
    if not test_connectivity():
        log_error("Server is not running. Please start it first:")
        print("   python3 k2think_proxy.py")
        print("   Or use: bash manage-server.sh start")
        return
    
    # Parse command line arguments
    message = DEFAULT_MESSAGE
    model = DEFAULT_MODEL
    stream = False
    interactive = True
    
    if len(sys.argv) > 1 and sys.argv[1] not in ['--help', '-h', '--interactive', '-i']:
        message = " ".join(sys.argv[1:])
        interactive = False
    
    # Interactive mode
    if interactive:
        print(f"{Colors.BLUE}🎯 Interactive Mode{Colors.NC}")
        print()
        
        # Get message
        user_input = input(f"{Colors.CYAN}💬 Enter your message{Colors.YELLOW} [{message}]{Colors.NC}: ")
        if user_input.strip():
            message = user_input.strip()
        
        # Get model
        model_choice = input(f"{Colors.CYAN}🤖 Select model{Colors.YELLOW} [1]{Colors.NC}: ")
        if model_choice.strip() == "2":
            model = "MBZUAI-IFM/K2Think-nothink"
        
        # Get streaming preference
        stream_choice = input(f"{Colors.CYAN}🌊 Use streaming?{Colors.YELLOW} [y/N]{Colors.NC}: ")
        stream = stream_choice.strip().lower() in ['y', 'yes']
        
        print()
        print(f"{Colors.MAGENTA}📋 Request Summary:{Colors.NC}")
        print(f"   Message: {message}")
        print(f"   Model: {model}")
        print(f"   Streaming: {stream}")
        print()
        
        # Confirm
        confirm = input(f"{Colors.CYAN}❓ Send this request?{Colors.YELLOW} [Y/n]{Colors.NC}: ")
        if confirm.strip().lower() in ['n', 'no']:
            log_info("Request cancelled")
            return
        print()
    
    # Make the request
    result = make_request(message, model, stream)
    
    if result:
        print()
        log_success("Test completed successfully!")
    else
        log_error("Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
