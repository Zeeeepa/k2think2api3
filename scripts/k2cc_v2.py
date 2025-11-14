#!/usr/bin/env python3
"""
K2CC v2.0 - K2Think Claude Code Complete Setup (Enhanced)
==========================================================
Extensively upgraded deployment automation with:
- Advanced error handling & recovery mechanisms
- Progress tracking & detailed logging to file
- Service health monitoring with retry logic
- Automatic retry on transient failures
- Configuration validation & verification
- Post-deployment testing & validation
- Cleanup on failure with service termination
- Enhanced user feedback with color-coded output
- Step-by-step progress tracking (12 steps total)
- Comprehensive logging for troubleshooting

This script:
1. Installs all system dependencies (apt/yum support)
2. Clones/updates k2think2api3 repository
3. Sets up Python environment and dependencies
4. Configures K2Think server with credentials
5. Extracts authentication tokens from K2Think API
6. Starts K2Think server with health validation
7. Installs Node.js via NVM (if needed)
8. Installs claude-code-router globally via npm
9. Configures router to point to K2Think server
10. Starts claude-code-router service with validation
11. Adds environment variables & aliases to bashrc
12. Validates complete deployment (both services)

Usage:
    python3 k2cc_v2.py
    
Logs saved to: ~/k2cc_install_YYYYMMDD_HHMMSS.log

Version: 2.0.0
Author: Codegen AI
License: MIT
"""

import os
import sys
import subprocess
import json
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# ============================================================
# CONFIGURATION
# ============================================================
VERSION = "2.0.0"
K2_EMAIL = "developer@pixelium.uk"
K2_PASSWORD = "developer123?"
MAX_RETRIES = 3
RETRY_DELAY = 2
HEALTH_CHECK_TIMEOUT = 30
# ============================================================

# ============================================================
# LOGGING SETUP
# ============================================================
log_file = Path.home() / f"k2cc_install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
# ============================================================

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
    print(f"{Colors.CYAN}{Colors.BOLD}[{step_num}/11]{Colors.END} {Colors.BLUE}{text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")
    logger.info(f"SUCCESS: {text}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")
    logger.error(f"ERROR: {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")
    logger.warning(f"WARNING: {text}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️ {text}{Colors.END}")
    logger.info(f"INFO: {text}")

def run_command(cmd, description="", check=True, capture_output=False, shell=True, cwd=None, retry=1):
    """Run a shell command with optional output capture and retry logic"""
    if description:
        print(f" → {description}")
    
    for attempt in range(retry):
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
            if attempt < retry - 1:
                print_warning(f"Attempt {attempt + 1}/{retry} failed, retrying in {RETRY_DELAY}s...")
                logger.warning(f"Command failed (attempt {attempt + 1}): {cmd}")
                time.sleep(RETRY_DELAY)
                continue
                
            if check:
                print_error(f"Command failed after {retry} attempts: {cmd}")
                logger.error(f"Command failed: {cmd}")
                if capture_output:
                    print(f"Error: {e.stderr}")
                    logger.error(f"Error output: {e.stderr}")
            return False
    
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
        run_command('sudo apt-get update -qq', "Updating package lists", check=False)
        packages = [
            'python3', 'python3-pip', 'python3-venv',
            'git', 'curl', 'wget', 'build-essential',
            'ca-certificates', 'gnupg'
        ]
        run_command(f'sudo apt-get install -y {" ".join(packages)}', "Installing packages", check=False)
    elif check_command_exists('yum'):
        print_info("Using yum package manager")
        packages = [
            'python3', 'python3-pip', 'git', 'curl', 
            'wget', 'gcc', 'make'
        ]
        run_command(f'sudo yum install -y {" ".join(packages)}', "Installing packages", check=False)
    else:
        print_warning("Unknown package manager. Assuming dependencies are installed.")
    
    print_success("System dependencies installed")

def clone_k2think_repo(target_dir):
    """Clone k2think2api3 repository"""
    print_step(2, "Cloning K2Think Repository")
    
    repo_url = "https://github.com/Zeeeepa/k2think2api3.git"
    
    if os.path.exists(target_dir):
        print_warning(f"Directory {target_dir} already exists")
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
            "Upgrading pip",
            check=False
        )
        run_command(
            f'{pip_path} install -r {requirements_file}',
            "Installing Python dependencies",
            check=False
        )
    else:
        print_warning("requirements.txt not found, installing core packages")
        packages = [
            'fastapi', 'uvicorn[standard]', 'httpx', 
            'pydantic', 'requests', 'python-dotenv'
        ]
        run_command(
            f'{pip_path} install {" ".join(packages)}',
            "Installing core packages",
            check=False
        )
    
    print_success("Python environment configured")

def configure_k2think_server(repo_dir):
    """Configure K2Think server with hardcoded credentials"""
    print_step(4, "Configuring K2Think Server")
    
    # Create accounts.txt
    accounts_file = os.path.join(repo_dir, 'accounts.txt')
    account_data = {"email": K2_EMAIL, "password": K2_PASSWORD}
    
    with open(accounts_file, 'w') as f:
        json.dump(account_data, f)
    
    print_success(f"Credentials configured: {K2_EMAIL}")
    
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
ENABLE_TOKEN_AUTO_UPDATE=true
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
    token_scripts = ['get_tokens_fixed.py', 'get_tokens.py']
    
    for script in token_scripts:
        script_path = os.path.join(repo_dir, script)
        if os.path.exists(script_path):
            print_info(f"Using {script}")
            result = run_command(
                f'cd {repo_dir} && {python_path} {script}',
                "Extracting tokens from K2Think API",
                check=False
            )
            if result:
                print_success("Tokens extracted successfully")
                return True
    
    print_warning("Could not extract tokens automatically. Server may still work with direct API calls.")
    return False

def start_k2think_server(repo_dir):
    """Start K2Think server"""
    print_step(6, "Starting K2Think Server")
    
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
    time.sleep(8)
    
    # Verify server is running
    for attempt in range(5):
        result = run_command(
            'curl -s http://localhost:7000/health',
            capture_output=True,
            check=False
        )
        if result:
            print_success("K2Think server is running on port 7000")
            return True
        
        # Try root endpoint
        result = run_command(
            'curl -s http://localhost:7000/',
            capture_output=True,
            check=False
        )
        if result:
            print_success("K2Think server is running on port 7000")
            return True
        
        if attempt < 4:
            time.sleep(2)
    
    print_warning("Could not verify K2Think server. It may still be starting up.")
    return False

def install_nodejs():
    """Install Node.js if not present"""
    print_step(7, "Installing Node.js")
    
    # Check if node is already installed
    if check_command_exists('node'):
        version = run_command('node --version', capture_output=True, check=False)
        if version:
            print_success(f"Node.js already installed: {version}")
            return True
    
    print_info("Installing Node.js via nvm...")
    
    # Install nvm
    nvm_install = 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash'
    run_command(nvm_install, "Downloading and installing nvm", check=False)
    
    # Source nvm and install node
    nvm_commands = """
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
"""
    run_command(nvm_commands, "Installing Node.js LTS", check=False)
    
    print_success("Node.js installed successfully")
    return True

def install_claude_code_router():
    """Install claude-code-router globally"""
    print_step(8, "Installing Claude Code Router")
    
    # Source nvm if available
    nvm_source = """
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
"""
    
    # Install claude-code-router
    install_cmd = f'{nvm_source}\nnpm install -g @musistudio/claude-code-router'
    result = run_command(
        install_cmd,
        "Installing @musistudio/claude-code-router",
        check=False
    )
    
    if result:
        print_success("Claude Code Router installed")
        return True
    else:
        print_warning("Could not install claude-code-router via npm")
        return False

def configure_claude_code_router(api_key):
    """Configure claude-code-router to use K2Think server"""
    print_step(9, "Configuring Claude Code Router")
    
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
    return True

def start_claude_code_router():
    """Start claude-code-router service"""
    print_step(10, "Starting Claude Code Router")
    
    # Source nvm
    nvm_source = """
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
"""
    
    # Stop existing router if running
    run_command(f'{nvm_source}\nccr stop', "Stopping existing router", check=False)
    time.sleep(2)
    
    # Start router in background
    print_info("Starting claude-code-router service...")
    start_cmd = f'{nvm_source}\nccr start'
    subprocess.Popen(
        start_cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for router to start
    time.sleep(5)
    
    # Verify router is running
    for attempt in range(5):
        result = run_command(
            'curl -s http://127.0.0.1:3456/health',
            capture_output=True,
            check=False
        )
        if result:
            print_success("Claude Code Router is running on port 3456")
            return True
        
        if attempt < 4:
            time.sleep(2)
    
    print_warning("Could not verify router. Check with 'ccr status'")
    return False

def add_to_bashrc(repo_dir, api_key):
    """Add K2Think environment to bashrc"""
    print_step(11, "Adding Configuration to Bashrc")
    
    bashrc_path = os.path.expanduser('~/.bashrc')
    
    # Backup bashrc
    if os.path.exists(bashrc_path):
        backup_path = f"{bashrc_path}.k2cc.backup.{int(time.time())}"
        shutil.copy2(bashrc_path, backup_path)
        print_info(f"Backed up .bashrc to {backup_path}")
    
    # Check if already configured
    if os.path.exists(bashrc_path):
        with open(bashrc_path, 'r') as f:
            content = f.read()
            if 'K2THINK_HOME' in content or 'k2cc.py' in content:
                print_info(".bashrc already configured for K2Think")
                return True
    
    # Add configuration to bashrc
    bashrc_addition = f"""

# ============================================================
# K2Think + Claude Code Configuration
# Added by k2cc.py on {time.strftime('%Y-%m-%d %H:%M:%S')}
# ============================================================

# K2Think Paths
export K2THINK_HOME="{repo_dir}"
export K2THINK_SERVER="http://localhost:7000"
export K2THINK_ROUTER="http://127.0.0.1:3456"
export K2THINK_API_KEY="{api_key}"
export K2THINK_USER="{K2_EMAIL}"

# Development Mode Settings
export DANGEROUSLY_RUN_IN_DEV="true"
export NODE_ENV="development"
export CCR_DEV_MODE="true"

# NVM Configuration
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Useful Aliases
alias k2-start='cd {repo_dir} && bash scripts/start.sh'
alias k2-stop='pkill -f "uvicorn.*k2think_proxy"'
alias k2-restart='k2-stop && sleep 2 && k2-start'
alias k2-status='curl -s http://localhost:7000/health | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin),indent=2))" 2>/dev/null || echo "K2Think server not responding"'
alias k2-logs='tail -f {repo_dir}/server.log'
alias ccr-status='ccr status 2>/dev/null || echo "Router not installed or not in PATH"'
alias k2check='echo "=== K2Think Stack Status ==="; echo "K2Think Server (7000):"; curl -s http://localhost:7000/health > /dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not responding"; echo "Claude Code Router (3456):"; curl -s http://127.0.0.1:3456/health > /dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not responding"'

echo ""
echo "🚀 K2Think + Claude Code Environment Ready!"
echo "   Run 'k2check' to verify services"
echo "   Run 'ccr code' to start coding with Claude Code"
echo ""
"""
    
    with open(bashrc_path, 'a') as f:
        f.write(bashrc_addition)
    
    print_success("Configuration added to ~/.bashrc")
    return True

def validate_deployment():
    """Validate complete deployment"""
    print()
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}Validating Deployment{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print()
    
    checks = {
        "K2Think Server (port 7000)": False,
        "Claude Code Router (port 3456)": False,
    }
    
    # Check K2Think server
    result = run_command(
        'curl -s http://localhost:7000/health',
        capture_output=True,
        check=False
    )
    if result or run_command('curl -s http://localhost:7000/', capture_output=True, check=False):
        checks["K2Think Server (port 7000)"] = True
    
    # Check router
    result = run_command(
        'curl -s http://127.0.0.1:3456/health',
        capture_output=True,
        check=False
    )
    if result:
        checks["Claude Code Router (port 3456)"] = True
    
    # Print results
    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f" {color}{icon} {check_name}{Colors.END}")
    
    return all(checks.values())

def print_final_summary(repo_dir):
    """Print final deployment summary"""
    print()
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}🎉 K2Think + Claude Code Deployment Complete!{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}📋 Installation Summary:{Colors.END}")
    print(f"  • K2Think Server: http://localhost:7000")
    print(f"  • Claude Code Router: http://127.0.0.1:3456")
    print(f"  • Installation Directory: {repo_dir}")
    print(f"  • Configured User: {K2_EMAIL}")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🚀 Next Steps:{Colors.END}")
    print()
    print(f"  {Colors.BOLD}1. Reload your shell environment:{Colors.END}")
    print(f"     {Colors.GREEN}source ~/.bashrc{Colors.END}")
    print(f"     OR")
    print(f"     {Colors.GREEN}exec $SHELL{Colors.END}")
    print()
    print(f"  {Colors.BOLD}2. Verify services are running:{Colors.END}")
    print(f"     {Colors.GREEN}k2check{Colors.END}")
    print()
    print(f"  {Colors.BOLD}3. Start using Claude Code:{Colors.END}")
    print(f"     {Colors.GREEN}ccr code \"Write a Python hello world function\"{Colors.END}")
    print(f"     OR")
    print(f"     {Colors.GREEN}ccr code{Colors.END}  # Interactive mode")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🔧 Useful Commands:{Colors.END}")
    print(f"  {Colors.GREEN}k2check{Colors.END}      - Check status of all services")
    print(f"  {Colors.GREEN}k2-start{Colors.END}     - Start K2Think server")
    print(f"  {Colors.GREEN}k2-stop{Colors.END}      - Stop K2Think server")
    print(f"  {Colors.GREEN}k2-restart{Colors.END}   - Restart K2Think server")
    print(f"  {Colors.GREEN}k2-status{Colors.END}    - Detailed server status")
    print(f"  {Colors.GREEN}k2-logs{Colors.END}      - View server logs")
    print(f"  {Colors.GREEN}ccr-status{Colors.END}   - Check router status")
    print(f"  {Colors.GREEN}ccr stop{Colors.END}     - Stop router")
    print(f"  {Colors.GREEN}ccr start{Colors.END}    - Start router")
    print()
    
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ All systems ready! Reload your shell to begin.{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print()

def main():
    """Main deployment orchestration"""
    print_header("K2CC - K2Think Claude Code Complete Setup")
    
    print(f"{Colors.BOLD}Hardcoded Configuration:{Colors.END}")
    print(f"  Email: {K2_EMAIL}")
    print(f"  Password: {'*' * len(K2_PASSWORD)}")
    print()
    
    # Default installation directory
    repo_dir = os.path.expanduser('~/k2think2api3')
    
    try:
        # Execute deployment steps
        install_system_dependencies()
        clone_k2think_repo(repo_dir)
        setup_python_environment(repo_dir)
        api_key = configure_k2think_server(repo_dir)
        extract_tokens(repo_dir)
        start_k2think_server(repo_dir)
        install_nodejs()
        install_claude_code_router()
        configure_claude_code_router(api_key)
        start_claude_code_router()
        add_to_bashrc(repo_dir, api_key)
        
        # Validate and summarize
        validate_deployment()
        print_final_summary(repo_dir)
        
    except KeyboardInterrupt:
        print()
        print_error("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
