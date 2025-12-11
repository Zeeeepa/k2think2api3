#!/usr/bin/env python3
"""
K2Think API Proxy - Docker Deployment Script
============================================
Automated deployment script that creates .env from .env.example,
collects K2Think credentials, fetches tokens, and deploys with Docker.

Usage:
    python start_docker.py
"""

import os
import sys
import subprocess
import json
import time
import socket
from pathlib import Path
from getpass import getpass

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

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(current: int, total: int, text: str):
    """Print a step indicator"""
    print(f"{Colors.OKCYAN}[{current}/{total}] {text}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}\u2713 {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}\u2717 {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}\u2139 {text}{Colors.ENDC}")

def check_python_version() -> bool:
    """Check if Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print_error(f"Python 3.7+ required. You have {sys.version}")
        return False
    print_success(f"Python {sys.version.split()[0]} detected")
    return True

def check_docker() -> bool:
    """Check if Docker and Docker Compose are installed"""
    try:
        # Check Docker
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print_error("Docker is not installed")
            return False
        
        # Check Docker Compose
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print_error("Docker Compose is not installed")
            return False
        
        print_success("Docker and Docker Compose are installed")
        return True
    except FileNotFoundError:
        print_error("Docker or Docker Compose not found")
        return False

def find_available_port(start_port: int = 8001) -> int:
    """Find an available port starting from start_port"""
    port = start_port
    while port < start_port + 100:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            port += 1
    return start_port

def load_existing_credentials() -> tuple[str, str] | None:
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

def collect_credentials() -> tuple[str, str] | None:
    """Collect or load K2Think credentials"""
    # Try to load existing credentials first
    existing = load_existing_credentials()
    if existing:
        print_header("K2Think Credentials Found")
        print_success(f"Using existing credentials: {existing[0]}")
        print_info("Delete data/accounts.txt to enter new credentials")
        return existing
    
    # Collect new credentials
    print_header("K2Think Credentials Setup")
    print_info("Please provide your K2Think account credentials")
    print_info("These will be used to fetch authentication tokens\n")
    
    try:
        email = input(f"{Colors.OKCYAN}Enter K2Think Email: {Colors.ENDC}")
        password = getpass(f"{Colors.OKCYAN}Enter K2Think Password: {Colors.ENDC}")
        confirm_password = getpass(f"{Colors.OKCYAN}Confirm Password: {Colors.ENDC}")
        
        if password != confirm_password:
            print_error("Passwords do not match")
            return None
        
        if not email or not password:
            print_error("Email and password are required")
            return None
        
        return email, password
    except KeyboardInterrupt:
        print("\n")
        print_error("Credential collection cancelled")
        return None

def create_env_file(port: int) -> bool:
    """Create .env file from .env.example"""
    try:
        env_example = Path('.env.example')
        env_file = Path('.env')
        
        if not env_example.exists():
            print_error(".env.example file not found")
            return False
        
        # Read .env.example
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update PORT
        lines = []
        for line in content.split('\n'):
            if line.startswith('PORT='):
                lines.append(f'PORT={port}')
            else:
                lines.append(line)
        
        # Write .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print_success(f"Created .env file (PORT={port}, HOST=0.0.0.0)")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def save_credentials(email: str, password: str) -> bool:
    """Save credentials to data/accounts.txt"""
    try:
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        accounts_file = data_dir / 'accounts.txt'
        credentials = {
            "email": email,
            "k2_password": password
        }
        
        with open(accounts_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(credentials))
        
        print_success("Saved credentials to data/accounts.txt")
        return True
    except Exception as e:
        print_error(f"Failed to save credentials: {e}")
        return False

def fetch_token() -> bool:
    """Run get_tokens.py to fetch authentication token"""
    try:
        print_info("Fetching authentication token from K2Think API...")
        
        if not Path('get_tokens.py').exists():
            print_error("get_tokens.py not found")
            return False
        
        result = subprocess.run(
            [sys.executable, 'get_tokens.py', 'data/accounts.txt', 'data/tokens.txt'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_success("Token fetched successfully")
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
        print_error(f"Failed to fetch token: {e}")
        return False

def deploy_docker(port: int) -> bool:
    """Deploy using Docker Compose"""
    try:
        print_info("Building and starting Docker containers...")
        
        # Set PORT environment variable for docker-compose
        env = os.environ.copy()
        env['SERVER_PORT'] = str(port)
        
        # Stop any existing containers
        subprocess.run(['docker-compose', 'down'], env=env, capture_output=True)
        
        # Build and start
        result = subprocess.run(
            ['docker-compose', 'up', '-d', '--build'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print_error(f"Docker deployment failed: {result.stderr}")
            return False
        
        print_success("Docker containers started")
        return True
    except subprocess.TimeoutExpired:
        print_error("Docker deployment timed out")
        return False
    except Exception as e:
        print_error(f"Docker deployment failed: {e}")
        return False

def verify_deployment(port: int) -> bool:
    """Verify the deployment is working"""
    try:
        print_info("Verifying deployment...")
        time.sleep(5)  # Wait for server to fully start
        
        import requests
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        
        if response.status_code == 200:
            print_success("Server is healthy and responding")
            return True
        else:
            print_error(f"Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Deployment verification failed: {e}")
        return False

def test_api(port: int) -> bool:
    """Send test request to API and print response"""
    try:
        import requests
        
        print_header("Testing API Endpoint")
        print_info('Sending test message: "hello how are you"')
        
        url = f"http://localhost:{port}/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer sk-k2think'
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
            print_error(f"API test failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API test failed: {e}")
        return False

def main():
    """Main deployment workflow"""
    total_steps = 8
    current_step = 0
    
    print_header("K2Think API Proxy - Docker Deployment")
    
    # Step 1: Check Python version
    current_step += 1
    print_step(current_step, total_steps, "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check Docker
    current_step += 1
    print_step(current_step, total_steps, "Checking Docker installation")
    if not check_docker():
        print_error("Please install Docker and Docker Compose first")
        sys.exit(1)
    
    # Step 3: Find available port
    current_step += 1
    print_step(current_step, total_steps, "Finding available port")
    target_port = find_available_port(8001)
    if target_port == 8001:
        print_success(f"Using default port: {target_port}")
    else:
        print_success(f"Using alternate port: {target_port} (default 8001 was in use)")
    
    # Step 4: Collect credentials
    current_step += 1
    print_step(current_step, total_steps, "Collecting K2Think credentials")
    credentials = collect_credentials()
    if not credentials:
        print_error("Failed to collect credentials")
        sys.exit(1)
    email, password = credentials
    
    # Step 5: Create .env
    current_step += 1
    print_step(current_step, total_steps, "Creating .env configuration")
    if not create_env_file(target_port):
        print_error("Failed to create .env file")
        sys.exit(1)
    
    if not save_credentials(email, password):
        print_error("Failed to save credentials")
        sys.exit(1)
    
    # Step 6: Fetch token
    current_step += 1
    print_step(current_step, total_steps, "Fetching authentication token")
    if not fetch_token():
        print_error("Failed to fetch token")
        sys.exit(1)
    
    # Step 7: Deploy Docker
    current_step += 1
    print_step(current_step, total_steps, "Deploying with Docker Compose")
    if not deploy_docker(target_port):
        print_error("Failed to deploy with Docker")
        sys.exit(1)
    
    if not verify_deployment(target_port):
        print_error("Deployment verification failed")
        sys.exit(1)
    
    # Step 8: Test API
    current_step += 1
    print_step(current_step, total_steps, "Testing API with sample request")
    test_api(target_port)
    
    # Print final URL
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}  \ud83d\ude80 API Ready at: http://localhost:{target_port}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Docker Management Commands:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}docker-compose logs -f{Colors.ENDC}  # View logs")
    print(f"  {Colors.OKCYAN}docker-compose ps{Colors.ENDC}        # Check status")
    print(f"  {Colors.OKCYAN}docker-compose down{Colors.ENDC}      # Stop containers")
    print(f"  {Colors.OKCYAN}docker-compose restart{Colors.ENDC}   # Restart containers\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

