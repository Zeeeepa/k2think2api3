#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2Think API Proxy - Docker Deployment Script
============================================
Automated Docker deployment with intelligent port management,
credential setup, and token extraction.

Features:
- Interactive credential collection
- Automatic .env generation from .env.example
- Token auto-fetch via get_tokens.py
- Smart port conflict resolution
- Docker container build and deployment
- OpenAI-compatible API endpoint
- Enforces K2-Think model and retrieved tokens
- Always uses thinking version
"""

import os
import sys
import json
import socket
import subprocess
import shutil
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

def get_compose_command() -> list:
    """Determine which docker compose command to use"""
    # Try docker compose v2 first
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, check=True, text=True)
        return ['docker', 'compose']
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to docker-compose v1
        try:
            subprocess.run(['docker-compose', '--version'], 
                          capture_output=True, check=True)
            return ['docker-compose']
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

def check_docker_installed() -> bool:
    """Check if Docker and Docker Compose are installed"""
    try:
        # Check Docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, check=True, text=True)
        print_success(f"Docker found: {result.stdout.strip()}")
        
        # Check Docker Compose
        compose_cmd = get_compose_command()
        if compose_cmd is None:
            print_error("Docker Compose not found")
            return False
        
        result = subprocess.run(compose_cmd + ['version'], 
                              capture_output=True, check=True, text=True)
        print_success(f"Docker Compose found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print_error(f"Docker or Docker Compose not found: {e}")
        return False

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def find_available_port(start_port: int = 8001, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def collect_credentials() -> Tuple[str, str]:
    """Collect K2Think credentials from user"""
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
        
        # Update PORT and optionally add credentials in the content
        lines = env_content.split('\n')
        updated_lines = []
        for line in lines:
            if line.startswith('PORT='):
                updated_lines.append(f'PORT={target_port}')
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
        
        print_success(f"Created .env file (PORT={target_port})")
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

def build_docker_image() -> bool:
    """Build Docker image locally"""
    try:
        print_info("Building Docker image (this may take a few minutes)...")
        
        compose_cmd = get_compose_command()
        if compose_cmd is None:
            print_error("Docker Compose command not available")
            return False
        
        # Build using docker compose
        result = subprocess.run(
            compose_cmd + ['build', '--no-cache'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Docker image built successfully")
            return True
        else:
            print_error(f"Failed to build Docker image:\n{result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error building Docker image: {e}")
        return False

def start_docker_container(port: int) -> bool:
    """Start Docker container with docker-compose"""
    try:
        print_info("Starting Docker container...")
        
        compose_cmd = get_compose_command()
        if compose_cmd is None:
            print_error("Docker Compose command not available")
            return False
        
        # Set environment variable for port
        env = os.environ.copy()
        env['HOST_PORT'] = str(port)
        
        # Stop any existing containers
        subprocess.run(
            compose_cmd + ['down'],
            capture_output=True,
            env=env
        )
        
        # Start container
        result = subprocess.run(
            compose_cmd + ['up', '-d'],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print_success("Docker container started successfully")
            
            # Wait for service to be ready
            print_info("Waiting for service to be ready...")
            time.sleep(5)
            
            return True
        else:
            print_error(f"Failed to start container:\n{result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error starting container: {e}")
        return False

def verify_deployment(port: int) -> bool:
    """Verify that the deployment is working"""
    try:
        import requests
        
        print_info("Verifying deployment...")
        
        # Try to connect to health endpoint
        url = f"http://127.0.0.1:{port}/health"
        
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_success("Service is healthy and responding")
                    return True
            except requests.exceptions.RequestException:
                if attempt < 2:
                    print_warning(f"Waiting for service... (attempt {attempt + 1}/3)")
                    time.sleep(5)
        
        print_warning("Could not verify service health, but container is running")
        return True
    except ImportError:
        print_warning("requests library not installed, skipping health check")
        return True
    except Exception as e:
        print_warning(f"Health check failed: {e}")
        return True

def print_final_info(port: int):
    """Print final deployment information"""
    print_header("Deployment Complete!")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}K2Think API Proxy is now running!{Colors.ENDC}\n")
    
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
    
    compose_cmd_str = ' '.join(get_compose_command())
    print(f"{Colors.BOLD}Management Commands:{Colors.ENDC}")
    print(f"  {Colors.OKBLUE}View logs:{Colors.ENDC}       {compose_cmd_str} logs -f")
    print(f"  {Colors.OKBLUE}Stop service:{Colors.ENDC}    {compose_cmd_str} down")
    print(f"  {Colors.OKBLUE}Restart service:{Colors.ENDC} {compose_cmd_str} restart")
    print(f"  {Colors.OKBLUE}Check status:{Colors.ENDC}    {compose_cmd_str} ps\n")

def main():
    """Main deployment function"""
    print_header("K2Think API Proxy - Docker Deployment")
    
    total_steps = 8
    current_step = 0
    
    # Step 1: Check Docker
    current_step += 1
    print_step(current_step, total_steps, "Checking Docker installation")
    if not check_docker_installed():
        print_error("Docker or Docker Compose is not installed")
        print_info("Please install Docker and Docker Compose before running this script")
        return 1
    
    # Step 2: Find available port
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
    
    # Step 3: Collect credentials first (before creating .env)
    current_step += 1
    print_step(current_step, total_steps, "Collecting K2Think credentials")
    email, password = collect_credentials()
    
    # Step 4: Create .env from template with credentials
    current_step += 1
    print_step(current_step, total_steps, "Creating .env configuration")
    if not create_env_from_example(target_port, email, password):
        print_error("Failed to create .env file")
        return 1
    
    # Step 5: Save credentials
    current_step += 1
    print_step(current_step, total_steps, "Saving credentials to accounts.txt")
    if not save_accounts(email, password):
        print_error("Failed to save credentials")
        return 1
    
    # Step 6: Fetch token
    current_step += 1
    print_step(current_step, total_steps, "Fetching authentication token")
    if not fetch_token():
        print_error("Failed to fetch token")
        return 1
    
    # Step 7: Build Docker image
    current_step += 1
    print_step(current_step, total_steps, "Building Docker image")
    if not build_docker_image():
        print_error("Failed to build Docker image")
        return 1
    
    # Step 8: Start container
    current_step += 1
    print_step(current_step, total_steps, "Starting Docker container")
    if not start_docker_container(target_port):
        print_error("Failed to start Docker container")
        return 1
    
    # Verify deployment
    verify_deployment(target_port)
    
    # Print final information
    print_final_info(target_port)
    
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
