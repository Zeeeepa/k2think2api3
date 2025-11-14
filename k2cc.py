#!/usr/bin/env python3
"""
K2CC - K2Think Claude Code Complete Setup
==========================================
One-script automation to deploy complete Claude Code environment powered by K2Think inference.

This script:
1. Installs all system dependencies
2. Clones k2think2api3 repository
3. Sets up Python environment and dependencies
4. Configures K2Think server with credentials
5. Starts K2Think server
6. Installs Node.js (if needed)
7. Installs claude-code-router globally
8. Configures router to point to K2Think server
9. Starts claude-code-router service
10. Validates complete deployment

Usage:
    python3 k2cc.py
    python3 k2cc.py --email developer@pixelium.uk --password "developer123?"
"""

import os
import sys
import subprocess
import json
import time
import argparse
import shutil
from pathlib import Path

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_step(step_num, text):
    print(f"{Colors.CYAN}{Colors.BOLD}[{step_num}/10]{Colors.END} {Colors.BLUE}{text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def run_command(cmd, description="", check=True, capture_output=False, shell=True, cwd=None):
    """Run a shell command with optional output capture"""
    if description:
        print(f"   → {description}")
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                shell=shell, 
                capture_output=True, 
                text=True, 
                check=check,
                cwd=cwd
            )
            return result.stdout.strip()
        else:
            result = subprocess.run(cmd, shell=shell, check=check, cwd=cwd)
            return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {cmd}")
            if capture_output:
                print(f"Error: {e.stderr}")
            sys.exit(1)
        return False

def check_command_exists(command):
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None

def install_system_dependencies():
    """Install required system packages"""
    print_step(1, "Installing System Dependencies")
    
    # Detect package manager
    if check_command_exists('apt-get'):
        print_info("Using apt package manager")
        run_command('apt-get update -qq', "Updating package lists")
        packages = [
            'python3', 'python3-pip', 'python3-venv',
            'git', 'curl', 'wget', 'build-essential',
            'ca-certificates', 'gnupg'
        ]
        run_command(f'apt-get install -y {" ".join(packages)}', "Installing packages")
    elif check_command_exists('yum'):
        print_info("Using yum package manager")
        packages = [
            'python3', 'python3-pip', 'git', 'curl', 
            'wget', 'gcc', 'make'
        ]
        run_command(f'yum install -y {" ".join(packages)}', "Installing packages")
    else:
        print_warning("Unknown package manager. Assuming dependencies are installed.")
    
    print_success("System dependencies installed")

def install_nodejs():
    """Install Node.js if not present"""
    print_step(6, "Installing Node.js")
    
    # Check if node is already installed
    if check_command_exists('node'):
        version = run_command('node --version', capture_output=True, check=False)
        if version:
            print_success(f"Node.js already installed: {version}")
            return
    
    print_info("Installing Node.js via nvm...")
    
    # Install nvm
    nvm_install = 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash'
    run_command(nvm_install, "Downloading and installing nvm")
    
    # Source nvm and install node
    nvm_commands = """
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm use --lts
    """
    run_command(nvm_commands, "Installing Node.js LTS")
    
    print_success("Node.js installed successfully")

def clone_k2think_repo(target_dir):
    """Clone k2think2api3 repository"""
    print_step(2, "Cloning K2Think Repository")
    
    repo_url = "https://github.com/Zeeeepa/k2think2api3.git"
    
    if os.path.exists(target_dir):
        print_warning(f"Directory {target_dir} already exists")
        user_input = input("   Delete and re-clone? (y/N): ").strip().lower()
        if user_input == 'y':
            shutil.rmtree(target_dir)
            print_info("Removed existing directory")
        else:
            print_info("Using existing directory")
            return
    
    run_command(f'git clone {repo_url} {target_dir}', f"Cloning {repo_url}")
    print_success(f"Repository cloned to {target_dir}")

def setup_python_environment(repo_dir):
    """Set up Python virtual environment and install dependencies"""
    print_step(3, "Setting Up Python Environment")
    
    venv_dir = os.path.join(repo_dir, 'venv')
    
    # Create virtual environment
    if not os.path.exists(venv_dir):
        run_command(f'python3 -m venv {venv_dir}', "Creating virtual environment")
    else:
        print_info("Virtual environment already exists")
    
    # Determine pip path
    pip_path = os.path.join(venv_dir, 'bin', 'pip')
    
    # Install requirements
    requirements_file = os.path.join(repo_dir, 'requirements.txt')
    if os.path.exists(requirements_file):
        run_command(
            f'{pip_path} install --upgrade pip setuptools wheel',
            "Upgrading pip"
        )
        run_command(
            f'{pip_path} install -r {requirements_file}',
            "Installing Python dependencies"
        )
    else:
        print_warning("requirements.txt not found, installing core packages")
        packages = [
            'fastapi', 'uvicorn[standard]', 'httpx', 
            'pydantic', 'requests', 'python-dotenv'
        ]
        run_command(
            f'{pip_path} install {" ".join(packages)}',
            "Installing core packages"
        )
    
    print_success("Python environment configured")

def configure_k2think_server(repo_dir, email, password):
    """Configure K2Think server with credentials"""
    print_step(4, "Configuring K2Think Server")
    
    # Create accounts.txt
    accounts_file = os.path.join(repo_dir, 'accounts.txt')
    account_data = {"email": email, "password": password}
    
    with open(accounts_file, 'w') as f:
        json.dump(account_data, f)
    
    print_success(f"Credentials configured: {email}")
    
    # Create .env file
    env_file = os.path.join(repo_dir, '.env')
    api_key = f"sk-k2think-proxy-{int(time.time())}"
    
    env_content = f"""# K2Think API Proxy Configuration
API_KEY={api_key}
PORT=7000
HOST=0.0.0.0
LOG_LEVEL=info
TOKEN_REFRESH_INTERVAL=3600
MAX_RETRIES=3
REQUEST_TIMEOUT=120
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print_success(f"Environment configured with API key: {api_key}")
    return api_key

def extract_tokens(repo_dir):
    """Extract tokens from K2Think"""
    print_step(5, "Extracting K2Think Tokens")
    
    python_path = os.path.join(repo_dir, 'venv', 'bin', 'python')
    
    # Try get_tokens_fixed.py first, then fall back to get_tokens.py
    token_scripts = ['get_tokens_fixed.py', 'get_tokens.py', 'scripts/get_tokens.sh']
    
    for script in token_scripts:
        script_path = os.path.join(repo_dir, script)
        if os.path.exists(script_path):
            print_info(f"Using {script}")
            if script.endswith('.py'):
                result = run_command(
                    f'{python_path} {script_path}',
                    "Extracting tokens from K2Think API",
                    check=False
                )
                if result:
                    print_success("Tokens extracted successfully")
                    return True
            elif script.endswith('.sh'):
                result = run_command(
                    f'bash {script_path}',
                    "Extracting tokens",
                    check=False,
                    cwd=repo_dir
                )
                if result:
                    print_success("Tokens extracted successfully")
                    return True
    
    print_warning("Could not extract tokens automatically. Server may still work with direct API calls.")
    return False

def start_k2think_server(repo_dir):
    """Start K2Think server"""
    print_info("Starting K2Think server...")
    
    start_script = os.path.join(repo_dir, 'scripts', 'start.sh')
    
    if os.path.exists(start_script):
        # Run start script in background
        subprocess.Popen(
            ['bash', start_script],
            cwd=repo_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print_info("Start script executed")
    else:
        # Manual start using uvicorn
        python_path = os.path.join(repo_dir, 'venv', 'bin', 'python')
        proxy_file = os.path.join(repo_dir, 'k2think_proxy.py')
        
        if os.path.exists(proxy_file):
            subprocess.Popen(
                [python_path, '-m', 'uvicorn', 'k2think_proxy:app', '--host', '0.0.0.0', '--port', '7000'],
                cwd=repo_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print_info("Server started with uvicorn")
    
    # Wait for server to start
    print_info("Waiting for K2Think server to initialize...")
    time.sleep(5)
    
    # Verify server is running
    for attempt in range(5):
        try:
            import requests
            response = requests.get('http://localhost:7000/health', timeout=2)
            if response.status_code == 200:
                print_success("K2Think server is running on port 7000")
                return True
        except:
            pass
        
        # Try root endpoint
        try:
            response = requests.get('http://localhost:7000/', timeout=2)
            if response.status_code == 200:
                print_success("K2Think server is running on port 7000")
                return True
        except:
            pass
        
        if attempt < 4:
            time.sleep(2)
    
    print_warning("Could not verify K2Think server. It may still be starting up.")
    return False

def install_claude_code_router():
    """Install claude-code-router globally"""
    print_step(7, "Installing Claude Code Router")
    
    # Check if npm is available
    if not check_command_exists('npm'):
        print_error("npm not found. Node.js installation may have failed.")
        sys.exit(1)
    
    # Install claude-code-router
    run_command(
        'npm install -g @musistudio/claude-code-router',
        "Installing @musistudio/claude-code-router"
    )
    
    print_success("Claude Code Router installed")

def configure_claude_code_router(api_key):
    """Configure claude-code-router to use K2Think server"""
    print_step(8, "Configuring Claude Code Router")
    
    config_dir = os.path.expanduser('~/.claude-code-router')
    os.makedirs(config_dir, exist_ok=True)
    
    config = {
        "LOG": True,
        "LOG_LEVEL": "info",
        "API_TIMEOUT_MS": 600000,
        "NON_INTERACTIVE_MODE": False,
        "Providers": [
            {
                "name": "k2think",
                "api_base_url": "http://localhost:7000/v1/chat/completions",
                "api_key": api_key,
                "models": [
                    "MBZUAI-IFM/K2-Think",
                    "MBZUAI-IFM/K2-Think-nothink"
                ],
                "transformer": {
                    "use": []
                }
            }
        ],
        "Router": {
            "default": "k2think,MBZUAI-IFM/K2-Think",
            "background": "k2think,MBZUAI-IFM/K2-Think-nothink",
            "think": "k2think,MBZUAI-IFM/K2-Think",
            "longContext": "k2think,MBZUAI-IFM/K2-Think",
            "longContextThreshold": 60000
        }
    }
    
    config_file = os.path.join(config_dir, 'config.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_success(f"Configuration saved to {config_file}")

def start_claude_code_router():
    """Start claude-code-router service"""
    print_step(9, "Starting Claude Code Router")
    
    # Stop existing router if running
    run_command('ccr stop', "Stopping existing router", check=False)
    time.sleep(2)
    
    # Start router
    print_info("Starting claude-code-router service...")
    subprocess.Popen(
        ['ccr', 'start'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for router to start
    time.sleep(5)
    
    # Verify router is running
    for attempt in range(5):
        try:
            import requests
            response = requests.get('http://127.0.0.1:3456/health', timeout=2)
            if response.status_code == 200:
                print_success("Claude Code Router is running on port 3456")
                return True
        except:
            pass
        
        if attempt < 4:
            time.sleep(2)
    
    print_warning("Could not verify router. Check with 'ccr status'")
    return False

def validate_deployment():
    """Validate complete deployment"""
    print_step(10, "Validating Deployment")
    
    checks = {
        "K2Think Server (port 7000)": False,
        "Claude Code Router (port 3456)": False,
        "End-to-End Integration": False
    }
    
    try:
        import requests
        
        # Check K2Think server
        try:
            response = requests.get('http://localhost:7000/health', timeout=3)
            if response.status_code == 200:
                checks["K2Think Server (port 7000)"] = True
        except:
            try:
                response = requests.get('http://localhost:7000/', timeout=3)
                if response.status_code == 200:
                    checks["K2Think Server (port 7000)"] = True
            except:
                pass
        
        # Check router
        try:
            response = requests.get('http://127.0.0.1:3456/health', timeout=3)
            if response.status_code == 200:
                checks["Claude Code Router (port 3456)"] = True
        except:
            pass
        
        # Test end-to-end
        if checks["Claude Code Router (port 3456)"]:
            try:
                response = requests.post(
                    'http://127.0.0.1:3456/v1/messages',
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 100,
                        "messages": [{"role": "user", "content": "Say hello"}]
                    },
                    headers={
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    checks["End-to-End Integration"] = True
            except:
                pass
    except ImportError:
        print_warning("requests module not available for validation")
    
    # Print results
    print("\n" + "="*70)
    print(f"{Colors.BOLD}Deployment Status:{Colors.END}\n")
    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"   {color}{icon} {check_name}{Colors.END}")
    
    all_passed = all(checks.values())
    critical_passed = checks["K2Think Server (port 7000)"] and checks["Claude Code Router (port 3456)"]
    
    return all_passed, critical_passed

def print_usage_guide(repo_dir):
    """Print usage guide"""
    print("\n" + "="*70)
    print(f"{Colors.HEADER}{Colors.BOLD}🎉 Deployment Complete!{Colors.END}")
    print("="*70 + "\n")
    
    print(f"{Colors.CYAN}{Colors.BOLD}📋 Architecture:{Colors.END}")
    print("   Claude Code → claude-code-router → K2Think Server → K2Think API")
    print("                 (Port 3456)         (Port 7000)")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🚀 Quick Start:{Colors.END}")
    print(f"   {Colors.GREEN}ccr code \"Create a hello world script\"{Colors.END}")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🎯 Available Models:{Colors.END}")
    print("   • MBZUAI-IFM/K2-Think (with reasoning)")
    print("   • MBZUAI-IFM/K2-Think-nothink (without reasoning)")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🔧 Management Commands:{Colors.END}")
    print(f"   {Colors.GREEN}ccr status{Colors.END}      # Check router status")
    print(f"   {Colors.GREEN}ccr stop{Colors.END}        # Stop router")
    print(f"   {Colors.GREEN}ccr restart{Colors.END}     # Restart router")
    print(f"   {Colors.GREEN}ccr ui{Colors.END}          # Web configuration interface")
    print(f"   {Colors.GREEN}ccr model{Colors.END}       # Interactive model selector")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}📁 Installation Directory:{Colors.END}")
    print(f"   {repo_dir}")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}📝 Configuration:{Colors.END}")
    print(f"   Router: {Colors.YELLOW}~/.claude-code-router/config.json{Colors.END}")
    print(f"   Logs: {Colors.YELLOW}~/.claude-code-router/logs/{Colors.END}")
    print()

def main():
    parser = argparse.ArgumentParser(
        description='K2CC - Complete K2Think Claude Code Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--email',
        default='developer@pixelium.uk',
        help='K2Think account email (default: developer@pixelium.uk)'
    )
    parser.add_argument(
        '--password',
        default='developer123?',
        help='K2Think account password (default: developer123?)'
    )
    parser.add_argument(
        '--dir',
        default=os.path.expanduser('~/k2think2api3'),
        help='Installation directory (default: ~/k2think2api3)'
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip system dependencies installation'
    )
    
    args = parser.parse_args()
    
    print_header("K2CC - K2Think Claude Code Complete Setup")
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"   Email: {Colors.CYAN}{args.email}{Colors.END}")
    print(f"   Password: {Colors.CYAN}{'*' * len(args.password)}{Colors.END}")
    print(f"   Directory: {Colors.CYAN}{args.dir}{Colors.END}")
    print()
    
    # Confirm
    confirm = input(f"{Colors.YELLOW}Proceed with installation? (Y/n): {Colors.END}").strip().lower()
    if confirm and confirm != 'y':
        print("Installation cancelled.")
        sys.exit(0)
    
    try:
        # Step 1: Install system dependencies
        if not args.skip_deps:
            install_system_dependencies()
        else:
            print_warning("Skipping system dependencies installation")
        
        # Step 2: Clone repository
        clone_k2think_repo(args.dir)
        
        # Step 3: Setup Python environment
        setup_python_environment(args.dir)
        
        # Step 4: Configure K2Think server
        api_key = configure_k2think_server(args.dir, args.email, args.password)
        
        # Step 5: Extract tokens
        extract_tokens(args.dir)
        
        # Start K2Think server (between step 5 and 6)
        start_k2think_server(args.dir)
        
        # Step 6: Install Node.js
        install_nodejs()
        
        # Step 7: Install claude-code-router
        install_claude_code_router()
        
        # Step 8: Configure router
        configure_claude_code_router(api_key)
        
        # Step 9: Start router
        start_claude_code_router()
        
        # Step 10: Validate deployment
        all_passed, critical_passed = validate_deployment()
        
        # Print usage guide
        print_usage_guide(args.dir)
        
        if all_passed:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ All systems operational! Ready to use Claude Code with K2Think.{Colors.END}\n")
            sys.exit(0)
        elif critical_passed:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Core services are running. Some features may need manual configuration.{Colors.END}\n")
            sys.exit(0)
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ Deployment encountered issues. Check the logs above.{Colors.END}\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Installation interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Fatal error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

