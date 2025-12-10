#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2Think API Proxy - Docker Deployment Script
============================================
Automated Docker deployment with intelligent port management,
credential setup, and token extraction.

Features:
- Interactive credential collection
- Automatic .env generation from template
- Token auto-fetch via get_tokens.py
- Smart port conflict resolution
- Docker container build and deployment
- OpenAI-compatible API endpoint
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

def check_docker_installed() -> bool:
    """Check if Docker and Docker Compose are installed"""
    try:
        subprocess.run(['docker', '--version'], 
                      capture_output=True, check=True)
        subprocess.run(['docker-compose', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def find_available_port(start_port: int = 8001, max_attempts: int = 100) -> Optional[int]:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def get_user_credentials() -> Tuple[str, str]:
    """Prompt user for K2Think credentials"""
    print_info("Please enter your K2Think account credentials:")
    
    while True:
        email = input(f"{Colors.OKCYAN}Email: {Colors.ENDC}").strip()
        if email and '@' in email:
            break
        print_error("Please enter a valid email address")
    
    while True:
        password = getpass.getpass(f"{Colors.OKCYAN}Password: {Colors.ENDC}")
        if password:
            break
        print_error("Password cannot be empty")
    
    return email, password

def create_env_file(port: int) -> bool:
    """Create .env file from .env.example template"""
    try:
        if not Path('.env.example').exists():
            print_error(".env.example not found!")
            return False
        
        # Read template
        with open('.env.example', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Update port
        env_content = env_content.replace('PORT=8001', f'PORT={port}')
        
        # Enable auto token update
        env_content = env_content.replace(
            'ENABLE_TOKEN_AUTO_UPDATE=false',
            'ENABLE_TOKEN_AUTO_UPDATE=true'
        )
        
        # Set model to always use thinking version
        if 'K2THINK_MODEL=' not in env_content:
            env_content += '\n# Model configuration (enforced)\n'
            env_content += 'K2THINK_MODEL=MBZUAI-IFM/K2-Think\n'
        
        # Write .env file
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print_success(f".env file created with port {port}")
        return True
        
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def create_accounts_file(email: str, password: str) -> bool:
    """Create accounts.txt file with user credentials"""
    try:
        # Ensure data directory exists
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Create accounts file in JSON format
        account_data = {
            "email": email,
            "k2_password": password
        }
        
        accounts_file = data_dir / 'accounts.txt'
        with open(accounts_file, 'w', encoding='utf-8') as f:
            json.dump(account_data, f)
            f.write('\n')  # Add newline for consistency
        
        print_success(f"Credentials saved to {accounts_file}")
        return True
        
    except Exception as e:
        print_error(f"Failed to save credentials: {e}")
        return False

def fetch_tokens() -> bool:
    """Execute get_tokens.py to fetch authentication tokens"""
    try:
        print_info("Fetching tokens from K2Think API...")
        
        # Check if get_tokens.py exists
        if not Path('get_tokens.py').exists():
            print_error("get_tokens.py not found!")
            return False
        
        # Execute get_tokens.py
        result = subprocess.run(
            [sys.executable, 'get_tokens.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Check if tokens.txt was created
            tokens_file = Path('data/tokens.txt')
            if tokens_file.exists():
                with open(tokens_file, 'r') as f:
                    tokens = f.readlines()
                print_success(f"Successfully fetched {len(tokens)} token(s)")
                return True
            else:
                print_error("tokens.txt was not created")
                if result.stdout:
                    print(f"Output: {result.stdout}")
                return False
        else:
            print_error(f"Token fetch failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Token fetch timed out (60 seconds)")
        return False
    except Exception as e:
        print_error(f"Failed to fetch tokens: {e}")
        return False

def update_docker_compose_port(port: int) -> bool:
    """Update docker-compose.yml with the selected port"""
    try:
        # Set environment variable for docker-compose
        os.environ['HOST_PORT'] = str(port)
        print_success(f"Docker Compose configured to use port {port}")
        return True
    except Exception as e:
        print_error(f"Failed to update docker-compose port: {e}")
        return False

def stop_existing_container() -> bool:
    """Stop and remove existing k2think-api container"""
    try:
        result = subprocess.run(
            ['docker-compose', 'down'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("Stopped existing containers")
        return True
    except Exception as e:
        print_warning(f"Could not stop existing containers: {e}")
        return True  # Continue anyway

def build_docker_image() -> bool:
    """Build Docker image using docker-compose"""
    try:
        print_info("Building Docker image (this may take a few minutes)...")
        
        result = subprocess.run(
            ['docker-compose', 'build', '--no-cache'],
            capture_output=False,  # Show output
            text=True
        )
        
        if result.returncode == 0:
            print_success("Docker image built successfully")
            return True
        else:
            print_error(f"Docker build failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print_error(f"Failed to build Docker image: {e}")
        return False

def start_docker_container(port: int) -> bool:
    """Start Docker container using docker-compose"""
    try:
        print_info("Starting Docker container...")
        
        result = subprocess.run(
            ['docker-compose', 'up', '-d'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Docker container started successfully")
            
            # Wait for container to be healthy
            print_info("Waiting for container to be ready...")
            time.sleep(5)
            
            # Check container status
            status_result = subprocess.run(
                ['docker-compose', 'ps'],
                capture_output=True,
                text=True
            )
            print(status_result.stdout)
            
            return True
        else:
            print_error(f"Failed to start container: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Failed to start Docker container: {e}")
        return False

def test_api_endpoint(port: int) -> bool:
    """Test if the API endpoint is responding"""
    try:
        import urllib.request
        
        print_info("Testing API endpoint...")
        url = f"http://localhost:{port}/health"
        
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        print_success(f"API endpoint is responding at http://localhost:{port}")
                        return True
            except:
                time.sleep(2)
        
        print_warning("API endpoint not responding yet (may need more time to start)")
        return True  # Don't fail deployment
        
    except Exception as e:
        print_warning(f"Could not test endpoint: {e}")
        return True  # Don't fail deployment

def print_summary(port: int):
    """Print deployment summary with connection details"""
    print_header("DEPLOYMENT SUCCESSFUL!")
    
    # Read API key from .env
    api_key = "sk-k2think"
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('VALID_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except:
        pass
    
    print(f"""
{Colors.OKGREEN}🚀 K2Think API Proxy is now running!{Colors.ENDC}

{Colors.BOLD}📍 Connection Details:{Colors.ENDC}
   Base URL: {Colors.OKCYAN}http://localhost:{port}/v1{Colors.ENDC}
   Health Check: {Colors.OKCYAN}http://localhost:{port}/health{Colors.ENDC}
   API Key: {Colors.OKCYAN}{api_key}{Colors.ENDC}

{Colors.BOLD}🎯 Model Configuration:{Colors.ENDC}
   Model: {Colors.OKCYAN}MBZUAI-IFM/K2-Think{Colors.ENDC} (with reasoning)
   Note: The proxy ALWAYS uses the K2-Think model with proper tokens,
         regardless of what model name is sent in requests.

{Colors.BOLD}💡 Quick Test:{Colors.ENDC}
{Colors.OKBLUE}curl http://localhost:{port}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {api_key}" \\
  -d '{{
    "model": "MBZUAI-IFM/K2-Think",
    "messages": [{{"role": "user", "content": "Hello!"}}]
  }}'{Colors.ENDC}

{Colors.BOLD}🐍 Python Example:{Colors.ENDC}
{Colors.OKBLUE}from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:{port}/v1",
    api_key="{api_key}"
)

response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{{"role": "user", "content": "Hello!"}}]
)

print(response.choices[0].message.content){Colors.ENDC}

{Colors.BOLD}📊 Container Management:{Colors.ENDC}
   View logs: {Colors.OKCYAN}docker-compose logs -f{Colors.ENDC}
   Stop: {Colors.OKCYAN}docker-compose stop{Colors.ENDC}
   Restart: {Colors.OKCYAN}docker-compose restart{Colors.ENDC}
   Remove: {Colors.OKCYAN}docker-compose down{Colors.ENDC}

{Colors.BOLD}🔧 Token Management:{Colors.ENDC}
   Tokens are automatically refreshed every hour.
   Manual refresh: {Colors.OKCYAN}python get_tokens.py{Colors.ENDC}

{Colors.OKGREEN}✨ Happy coding with K2-Think AI!{Colors.ENDC}
""")

def main():
    """Main deployment workflow"""
    print_header("K2Think API Proxy - Docker Deployment")
    
    total_steps = 8
    
    # Step 1: Check prerequisites
    print_step(1, total_steps, "Checking prerequisites...")
    if not check_docker_installed():
        print_error("Docker or Docker Compose is not installed!")
        print_info("Please install Docker Desktop or Docker Engine + Docker Compose")
        print_info("Visit: https://docs.docker.com/get-docker/")
        return 1
    print_success("Docker and Docker Compose are installed")
    
    # Step 2: Get user credentials
    print_step(2, total_steps, "Collecting K2Think credentials...")
    email, password = get_user_credentials()
    print_success("Credentials collected")
    
    # Step 3: Check and resolve port conflicts
    print_step(3, total_steps, "Checking port availability...")
    default_port = 8001
    
    if is_port_in_use(default_port):
        print_warning(f"Port {default_port} is already in use")
        alt_port = find_available_port(default_port + 1)
        
        if alt_port:
            print_info(f"Found available port: {alt_port}")
            use_alt = input(f"{Colors.OKCYAN}Use port {alt_port}? (Y/n): {Colors.ENDC}").strip().lower()
            
            if use_alt != 'n':
                port = alt_port
            else:
                custom_port = input(f"{Colors.OKCYAN}Enter custom port number: {Colors.ENDC}").strip()
                try:
                    port = int(custom_port)
                    if is_port_in_use(port):
                        print_error(f"Port {port} is also in use!")
                        return 1
                except ValueError:
                    print_error("Invalid port number")
                    return 1
        else:
            print_error("Could not find an available port")
            return 1
    else:
        port = default_port
        print_success(f"Port {port} is available")
    
    # Step 4: Create .env file
    print_step(4, total_steps, "Creating environment configuration...")
    if not create_env_file(port):
        return 1
    
    # Step 5: Save credentials
    print_step(5, total_steps, "Saving credentials...")
    if not create_accounts_file(email, password):
        return 1
    
    # Step 6: Fetch tokens
    print_step(6, total_steps, "Fetching authentication tokens...")
    if not fetch_tokens():
        print_error("Failed to fetch tokens. Please check your credentials and try again.")
        return 1
    
    # Step 7: Build and deploy Docker
    print_step(7, total_steps, "Building and deploying Docker container...")
    
    # Stop existing containers
    stop_existing_container()
    
    # Update docker-compose port
    if not update_docker_compose_port(port):
        return 1
    
    # Build image
    if not build_docker_image():
        return 1
    
    # Start container
    if not start_docker_container(port):
        return 1
    
    # Step 8: Test and verify
    print_step(8, total_steps, "Verifying deployment...")
    test_api_endpoint(port)
    
    # Print summary
    print_summary(port)
    
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

