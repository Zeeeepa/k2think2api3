#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2Think API Proxy - Local Deployment Script
==========================================
Automated local deployment with intelligent port management,
credential setup, and token extraction.

Features:
- Interactive credential collection
- Automatic .env generation from .env.example
- Token auto-fetch via get_tokens.py
- Smart port conflict resolution
- Local Python server start
- OpenAI-compatible API endpoint
- Enforces K2-Think model and retrieved tokens
- Always uses thinking version
"""

import os
import sys
import json
import socket
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional, Tuple
import getpass

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(step: int, total: int, message: str):
    """Print step indicator"""
    print(f"{Colors.OKCYAN}[{step}/{total}] {message}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def check_python_version() -> bool:
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_dependencies() -> bool:
    """Check if required Python packages are installed"""
    # Map package names to their import names
    packages_map = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'httpx': 'httpx',
        'python-dotenv': 'dotenv'
    }
    missing_packages = []
    
    for package_name, import_name in packages_map.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print_error(f"Missing required packages: {', '.join(missing_packages)}")
        print_info("Installing dependencies automatically...")
        # Auto-install missing packages
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print_success("Dependencies installed successfully")
                return True
            else:
                print_error("Failed to install dependencies")
                print_info("Please run manually: pip install -r requirements.txt")
                return False
        except Exception as e:
            print_error(f"Auto-install failed: {e}")
            print_info("Please run manually: pip install -r requirements.txt")
            return False
    
    print_success("All required packages are installed")
    return True

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

def find_available_port(start_port: int = 8001, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def load_existing_credentials() -> Optional[Tuple[str, str]]:
    """Load credentials from data/accounts.txt if exists"""
    try:
        accounts_file = Path('data/accounts.txt')
        if accounts_file.exists():
            with open(accounts_file, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
                email = data.get('email')
                password = data.get('k2_password')
                if email and password:
                    return email, password
    except Exception:
        pass
    return None

def collect_credentials() -> Tuple[str, str]:
    """Collect K2Think credentials from user or load from file"""
    # Check if credentials already exist
    existing = load_existing_credentials()
    if existing:
        email, password = existing
        print_header("K2Think Credentials Found")
        print_success(f"Using existing credentials: {email}")
        print_info("Delete data/accounts.txt to enter new credentials\n")
        return email, password
    
    print_header("K2Think Credentials Setup")
    print_info("Please provide your K2Think account credentials")
    print_info("These will be used to fetch authentication tokens\n")
    
    while True:
        email = input(f"{Colors.OKCYAN}Enter K2Think Email: {Colors.ENDC}").strip()
        if email and '@' in email:
            break
        print_error("Invalid email address. Please try again.")
    
    while True:
        password = getpass.getpass(f"{Colors.OKCYAN}Enter K2Think Password: {Colors.ENDC}")
        if password:
            # Confirm password
            password_confirm = getpass.getpass(f"{Colors.OKCYAN}Confirm Password: {Colors.ENDC}")
            if password == password_confirm:
                break
            print_error("Passwords don't match. Please try again.")
        else:
            print_error("Password cannot be empty. Please try again.")
    
    return email, password

def create_env_from_example(target_port: int, email: str = None, password: str = None) -> bool:
    """Create .env file from .env.example with specified port and optional credentials"""
    try:
        env_example_path = Path('.env.example')
        env_path = Path('.env')
        
        if not env_example_path.exists():
            print_error(".env.example file not found")
            return False
        
        # Read .env.example
        with open(env_example_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Update PORT and HOST in the content
        lines = env_content.split('\n')
        updated_lines = []
        for line in lines:
            if line.startswith('PORT='):
                updated_lines.append(f'PORT={target_port}')
            elif line.startswith('HOST='):
                updated_lines.append('HOST=127.0.0.1')
            else:
                updated_lines.append(line)
        
        # Add K2Think credentials if provided (for reference, not used by proxy)
        if email and password:
            updated_lines.append('')
            updated_lines.append('# K2Think credentials (automatically added)')
            updated_lines.append(f'# K2THINK_EMAIL={email}')
            updated_lines.append(f'# K2THINK_PASSWORD=<hidden>')
        
        # Write to .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print_success(f"Created .env file (PORT={target_port}, HOST=127.0.0.1)")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def save_accounts(email: str, password: str) -> bool:
    """Save credentials to data/accounts.txt"""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Create accounts.txt with JSON format
        accounts_file = data_dir / 'accounts.txt'
        account_data = {
            "email": email,
            "k2_password": password
        }
        
        with open(accounts_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(account_data))
        
        print_success(f"Saved credentials to {accounts_file}")
        return True
    except Exception as e:
        print_error(f"Failed to save credentials: {e}")
        return False

def fetch_token() -> bool:
    """Run get_tokens.py to fetch authentication token"""
    try:
        print_info("Fetching authentication token from K2Think API...")
        
        # Check if get_tokens.py exists
        if not Path('get_tokens.py').exists():
            print_error("get_tokens.py not found")
            return False
        
        # Run get_tokens.py
        result = subprocess.run(
            [sys.executable, 'get_tokens.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_success("Token fetched successfully")
            # Print relevant output (excluding sensitive data)
            for line in result.stdout.split('\n'):
                if '成功' in line or '处理完成' in line or 'Success' in line.lower():
                    print_info(f"  {line.strip()}")
            return True
        else:
            print_error(f"Failed to fetch token: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error("Token fetch timed out")
        return False
    except Exception as e:
        print_error(f"Error fetching token: {e}")
        return False

def start_local_server(port: int) -> Optional[subprocess.Popen]:
    """Start the local Python server"""
    try:
        print_info("Starting K2Think API Proxy server...")
        
        # Check if k2think_proxy.py exists
        if not Path('k2think_proxy.py').exists():
            print_error("k2think_proxy.py not found")
            return None
        
        # Start server process
        process = subprocess.Popen(
            [sys.executable, 'k2think_proxy.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print_success("Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print_error(f"Server failed to start:\n{stderr}")
            return None
    except Exception as e:
        print_error(f"Error starting server: {e}")
        return None

def verify_server(port: int) -> bool:
    """Verify that the server is responding"""
    try:
        import requests
        
        print_info("Verifying server is responding...")
        
        # Try to connect to health endpoint
        url = f"http://127.0.0.1:{port}/health"
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_success("Server is healthy and responding")
                    return True
            except requests.exceptions.RequestException:
                if attempt < 2:
                    print_warning(f"Waiting for server... (attempt {attempt + 1}/3)")
                    time.sleep(3)
        
        print_warning("Could not verify server health, but process is running")
        return True
    except ImportError:
        print_warning("requests library not installed, skipping health check")
        return True
    except Exception as e:
        print_warning(f"Health check failed: {e}")
        return True

def test_api(port: int) -> bool:
    """Send test request to API and print response"""
    try:
        import requests
        
        print_header("Testing API Endpoint")
        print_info('Sending test message: "hello how are you"')
        
        url = f"http://127.0.0.1:{port}/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-key-12345'
        }
        data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hello how are you"}],
            "stream": False,
            "max_tokens": 150
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print_success("API test successful!")
            print(f"\n{Colors.BOLD}API Response:{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{'─'*70}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}{content}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{'─'*70}{Colors.ENDC}\n")
            return True
        else:
            print_error(f"API test failed with status {response.status_code}")
            print_warning(f"Response: {response.text[:200]}")
            return False
    except ImportError:
        print_warning("requests library not available, skipping API test")
        return True
    except Exception as e:
        print_error(f"API test error: {e}")
        return False

def print_final_info(port: int):
    """Print final deployment information"""
    print_header("Local Deployment Complete!")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}K2Think API Proxy is now running locally!{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}OpenAI-Compatible API Endpoint:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}http://127.0.0.1:{port}/v1/chat/completions{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Base URL:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}http://127.0.0.1:{port}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  {Colors.OKBLUE}• Model:{Colors.ENDC} MBZUAI-IFM/K2-Think (enforced - ignores client requests)")
    print(f"  {Colors.OKBLUE}• Token:{Colors.ENDC} Retrieved from K2Think API (enforced - ignores client tokens)")
    print(f"  {Colors.OKBLUE}• Thinking:{Colors.ENDC} Enabled (shows reasoning in <think> tags)")
    print(f"  {Colors.OKBLUE}• API Key:{Colors.ENDC} sk-k2think (from .env)\n")
    
    print(f"{Colors.BOLD}Example Usage:{Colors.ENDC}")
    print(f"{Colors.OKBLUE}curl http://127.0.0.1:{port}/v1/chat/completions \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -H 'Authorization: Bearer sk-k2think' \\")
    print(f"  -d '{{")
    print(f'    "model": "any-model-name",')
    print(f'    "messages": [{{"role": "user", "content": "Hello!"}}]')
    print(f"  }}'{Colors.ENDC}\n")
    
    print(f"{Colors.WARNING}Note: The proxy will ALWAYS use:{Colors.ENDC}")
    print(f"  • K2-Think model (regardless of 'model' parameter)")
    print(f"  • Retrieved token from K2Think API (regardless of Authorization header)")
    print(f"  • Thinking mode enabled (reasoning visible in responses)\n")
    
    print(f"{Colors.BOLD}Server Control:{Colors.ENDC}")
    print(f"  {Colors.OKBLUE}Press Ctrl+C to stop the server{Colors.ENDC}\n")

def main():
    """Main deployment function"""
    print_header("K2Think API Proxy - Local Deployment")
    
    total_steps = 8
    current_step = 0
    
    # Step 1: Check Python version
    current_step += 1
    print_step(current_step, total_steps, "Checking Python version")
    if not check_python_version():
        return 1
    
    # Step 2: Check dependencies
    current_step += 1
    print_step(current_step, total_steps, "Checking dependencies")
    if not check_dependencies():
        return 1
    
    # Step 3: Find available port
    current_step += 1
    print_step(current_step, total_steps, "Finding available port")
    default_port = 8001
    if is_port_in_use(default_port):
        print_warning(f"Port {default_port} is in use")
        target_port = find_available_port(default_port + 1)
        if target_port is None:
            print_error("Could not find an available port")
            return 1
        print_success(f"Using alternate port: {target_port}")
    else:
        target_port = default_port
        print_success(f"Using default port: {target_port}")
    
    # Step 4: Collect credentials first (before creating .env)
    current_step += 1
    print_step(current_step, total_steps, "Collecting K2Think credentials")
    email, password = collect_credentials()
    
    # Step 5: Create .env from template with credentials
    current_step += 1
    print_step(current_step, total_steps, "Creating .env configuration")
    if not create_env_from_example(target_port, email, password):
        print_error("Failed to create .env file")
        return 1
    
    # Save credentials
    if not save_accounts(email, password):
        print_error("Failed to save credentials")
        return 1
    
    # Step 6: Fetch token
    current_step += 1
    print_step(current_step, total_steps, "Fetching authentication token")
    if not fetch_token():
        print_error("Failed to fetch token")
        return 1
    
    # Step 7: Start server
    current_step += 1
    print_step(current_step, total_steps, "Starting local server")
    server_process = start_local_server(target_port)
    if server_process is None:
        print_error("Failed to start server")
        return 1
    
    # Verify server
    verify_server(target_port)
    
    # Step 8: Test API
    current_step += 1
    print_step(current_step, total_steps, "Testing API with sample request")
    test_api(target_port)
    
    # Print final information
    print_final_info(target_port)
    
    # Print final URL prominently
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}  🚀 API Ready at: http://127.0.0.1:{target_port}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}\n")
    
    # Keep server running and handle Ctrl+C
    try:
        print_info("Server is running. Logs will appear below:")
        print(f"{Colors.OKBLUE}{'='*70}{Colors.ENDC}\n")
        
        # Stream server output
        for line in server_process.stdout:
            print(line, end='')
        
        server_process.wait()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Shutting down server...{Colors.ENDC}")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print_success("Server stopped")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Deployment cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
