#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

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
        print_info("Password: " + "*" * len(existing[1]))
        print_info("Delete data/accounts.txt to enter new credentials")
        return existing
    
    # Check for environment variables
    env_email = os.environ.get('K2_EMAIL')
    env_password = os.environ.get('K2_PASSWORD')
    if env_email and env_password:
        print_header("K2Think Credentials from Environment")
        print_success(f"Using K2_EMAIL: {env_email}")
        print_success(f"Using K2_PASSWORD: {env_password}")
        return env_email, env_password
    
    # Collect new credentials
    print_header("K2Think Credentials Setup")
    print_info("Please provide your K2Think account credentials")
    print_info("These will be used to fetch authentication tokens")
    print_info("Password will be VISIBLE for verification\n")
    
    try:
        email = input(f"{Colors.OKCYAN}Enter K2Think Email: {Colors.ENDC}")
        password = input(f"{Colors.OKCYAN}Enter K2Think Password (visible): {Colors.ENDC}")
        confirm_password = input(f"{Colors.OKCYAN}Confirm Password: {Colors.ENDC}")
        
        if password != confirm_password:
            print_error("Passwords do not match")
            return None
        
        if not email or not password:
            print_error("Email and password are required")
            return None
        
        print_success(f"Credentials collected: {email} / {password}")
        return email, password
    except KeyboardInterrupt:
        print("\n")
        print_error("Credential collection cancelled")
        return None

def create_env_file(port: int) -> bool:
    """Create .env file from .env.example with Docker-optimized settings"""
    try:
        env_example = Path('.env.example')
        env_file = Path('.env')
        
        if not env_example.exists():
            print_error(".env.example file not found")
            return False
        
        # Read .env.example
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update PORT and HOST for Docker networking
        lines = []
        for line in content.split('\n'):
            if line.startswith('PORT='):
                lines.append(f'PORT={port}')
            elif line.startswith('HOST='):
                # Use 0.0.0.0 for Docker to listen on all interfaces
                lines.append('HOST=0.0.0.0')
            else:
                lines.append(line)
        
        # Write .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print_success(f"Created .env file (PORT={port}, HOST=0.0.0.0)")
        print_info(f"Docker will expose API at: http://localhost:{port}")
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
    """Deploy using Docker Compose with intelligent error handling"""
    try:
        print_info("Building and starting Docker containers...")
        
        # Set PORT environment variable for docker-compose
        env = os.environ.copy()
        env['SERVER_PORT'] = str(port)
        
        # Stop any existing containers
        subprocess.run(['docker-compose', 'down'], env=env, capture_output=True)
        
        # Try to build image locally first (avoid pull issues)
        print_info("Building Docker image locally...")
        build_result = subprocess.run(
            ['docker-compose', 'build', '--no-cache'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if build_result.returncode != 0:
            print_error(f"Docker build failed: {build_result.stderr}")
            print_info("Will try to start with existing image or pull...")
        else:
            print_success("Docker image built successfully")
        
        # Start containers
        result = subprocess.run(
            ['docker-compose', 'up', '-d'],
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_msg = result.stderr
            print_error(f"Docker deployment failed!")
            print_error(f"Error: {error_msg[:500]}")
            
            # Check for common Docker issues
            if 'docker-credential' in error_msg.lower():
                print_info("\n⚠️  Docker credential helper issue detected")
                print_info("This is a common Docker Desktop issue on WSL/Linux")
                print_info("Attempting to fix...")
                
                # Try to fix Docker credential issue
                try:
                    docker_config_path = Path.home() / '.docker' / 'config.json'
                    if docker_config_path.exists():
                        with open(docker_config_path, 'r') as f:
                            config = json.load(f)
                        
                        # Remove credsStore if it exists
                        if 'credsStore' in config:
                            config.pop('credsStore')
                            with open(docker_config_path, 'w') as f:
                                json.dump(config, f, indent=2)
                            print_success("Fixed Docker config - removed credsStore")
                            
                            # Retry deployment
                            print_info("Retrying Docker deployment...")
                            retry_result = subprocess.run(
                                ['docker-compose', 'up', '-d'],
                                env=env,
                                capture_output=True,
                                text=True,
                                timeout=120
                            )
                            
                            if retry_result.returncode == 0:
                                print_success("Docker containers started after fix")
                                return True
                except Exception as fix_error:
                    print_error(f"Fix attempt failed: {fix_error}")
            
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
        print_info(f"Testing health endpoint: http://localhost:{port}/health")
        time.sleep(5)  # Wait for server to fully start
        
        import requests
        response = requests.get(f"http://localhost:{port}/health", timeout=10)
        
        if response.status_code == 200:
            print_success("Server is healthy and responding")
            print_success(f"API endpoint confirmed: http://localhost:{port}")
            return True
        else:
            print_error(f"Server health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to http://localhost:{port}")
        print_info("Server may still be starting or port may be blocked")
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
            print(f"{Colors.OKBLUE}{'-'*70}{Colors.ENDC}")
            # Handle potential encoding issues in response
            try:
                print(f"{Colors.OKCYAN}{content}{Colors.ENDC}")
            except UnicodeEncodeError:
                # Fallback to ASCII-safe printing
                print(f"{Colors.OKCYAN}{content.encode('ascii', 'replace').decode('ascii')}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{'-'*70}{Colors.ENDC}\n")
            return True
        else:
            print_error(f"API test failed: HTTP {response.status_code}")
            # Try to print error details
            try:
                error_text = response.text[:200]
                print_info(f"Response: {error_text}")
            except:
                pass
            return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

def start_local_fallback(port: int) -> bool:
    """Fallback to local Python deployment if Docker fails"""
    try:
        print_header("🔄 Falling Back to Local Python Deployment")
        print_info("Starting server with local Python instead of Docker...")
        
        # Check if start.py exists
        if not Path('start.py').exists():
            print_error("start.py not found - cannot fallback to local deployment")
            return False
        
        print_info(f"Running: python3 start.py")
        print_info("This will start the server in the foreground...")
        print_info("Press Ctrl+C to stop the server\n")
        
        time.sleep(2)
        
        # Run start.py
        subprocess.run([sys.executable, 'start.py'])
        
        return True
    except KeyboardInterrupt:
        print("\n")
        print_info("Server stopped by user")
        return True
    except Exception as e:
        print_error(f"Local fallback failed: {e}")
        return False

def main():
    """Main deployment workflow with intelligent fallback"""
    total_steps = 8
    current_step = 0
    docker_failed = False
    
    print_header("K2Think API Proxy - Docker Deployment")
    
    # Step 1: Check Python version
    current_step += 1
    print_step(current_step, total_steps, "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Check Docker
    current_step += 1
    print_step(current_step, total_steps, "Checking Docker installation")
    docker_available = check_docker()
    if not docker_available:
        print_error("Docker is not available")
        print_info("Will attempt local Python deployment as fallback...")
        docker_failed = True
    
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
        print_info("Continuing anyway - server will try to fetch token on startup...")
    
    # Step 7: Deploy (Docker or local fallback)
    current_step += 1
    print_step(current_step, total_steps, "Deploying service")
    
    if not docker_failed:
        # Try Docker deployment
        if not deploy_docker(target_port):
            print_error("Docker deployment failed")
            print_info("\n⚠️  Docker deployment encountered errors")
            print_info("Would you like to try local Python deployment instead?")
            
            try:
                response = input(f"{Colors.OKCYAN}Use local deployment? (y/n): {Colors.ENDC}").strip().lower()
                if response == 'y' or response == 'yes':
                    docker_failed = True
                else:
                    print_error("Deployment cancelled")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\n")
                print_error("Deployment cancelled")
                sys.exit(1)
    
    if docker_failed:
        # Use local Python deployment
        print_info("\n📌 Switching to local Python deployment")
        if not start_local_fallback(target_port):
            print_error("Both Docker and local deployment failed")
            sys.exit(1)
        sys.exit(0)  # Exit after local deployment (it runs in foreground)
    
    # Verify Docker deployment
    if not verify_deployment(target_port):
        print_error("Deployment verification failed")
        print_info("Server may still be starting up...")
        print_info("Check logs with: docker-compose logs -f")
    
    # Step 8: Test API
    current_step += 1
    print_step(current_step, total_steps, "Testing API with sample request")
    test_api(target_port)
    
    # Print final URL and network configuration
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}  🚀 K2Think API Proxy - Docker Deployment Complete!{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'='*70}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}API Endpoint:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}http://localhost:{target_port}/v1/chat/completions{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Network Configuration:{Colors.ENDC}")
    print(f"  • Container: Using host network mode")
    print(f"  • Listening: 0.0.0.0:{target_port} (all interfaces)")
    print(f"  • Access: http://localhost:{target_port}")
    print(f"  • Health: http://localhost:{target_port}/health\n")
    
    print(f"{Colors.BOLD}Docker Management:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}docker-compose logs -f{Colors.ENDC}     # View real-time logs")
    print(f"  {Colors.OKCYAN}docker-compose ps{Colors.ENDC}           # Check container status")
    print(f"  {Colors.OKCYAN}docker-compose down{Colors.ENDC}         # Stop containers")
    print(f"  {Colors.OKCYAN}docker-compose restart{Colors.ENDC}      # Restart containers\n")
    
    print(f"{Colors.BOLD}Test API:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}curl http://localhost:{target_port}/health{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}curl http://localhost:{target_port}/v1/models{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        try:
            print_error(f"Unexpected error: {str(e)}")
        except:
            # Absolute fallback if even error printing fails
            print(f"ERROR: {str(e)}")
        sys.exit(1)
