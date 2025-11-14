#!/usr/bin/env python3
"""
K2CC - K2Think Claude Code Complete Setup
==========================================
Interactive deployment automation for Claude Code environment powered by K2Think.

This script will:
1. Prompt for K2Think credentials (email/password)
2. Install all system dependencies
3. Clone/update k2think2api3 repository
4. Set up Python environment
5. Configure K2Think server with your credentials
6. Extract authentication tokens
7. Start K2Think server
8. Install Node.js and claude-code-router
9. Configure and start router
10. Add environment to bashrc
11. Validate complete deployment

Usage:
    python3 k2cc.py

Version: 3.0.0
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
VERSION = "3.0.0"
K2_REPO_URL = "https://github.com/Zeeeepa/k2think2api3.git"
K2_HOME = Path.home() / "k2think2api3"
K2_PORT = 7000
ROUTER_PORT = 3456
MAX_RETRIES = 3
RETRY_DELAY = 2
HEALTH_CHECK_TIMEOUT = 30

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

def print_step(step_num, total, text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}[{step_num}/{total}]{Colors.END} {Colors.BLUE}{text}{Colors.END}")
    logger.info(f"Step {step_num}/{total}: {text}")

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

def wait_for_service(url, timeout=30):
    """Wait for a service to become available"""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                f"curl -sf {url}",
                shell=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except:
            pass
        time.sleep(2)
    
    return False

def get_credentials():
    """Prompt user for K2Think credentials"""
    print_header(f"K2CC v{VERSION} - Interactive Setup")
    print(f"{Colors.BOLD}Please enter your K2Think credentials:{Colors.END}\n")
    
    email = input(f"{Colors.CYAN}K2Think Email: {Colors.END}").strip()
    if not email:
        print_error("Email cannot be empty!")
        sys.exit(1)
    
    password = input(f"{Colors.CYAN}K2Think Password: {Colors.END}").strip()
    if not password:
        print_error("Password cannot be empty!")
        sys.exit(1)
    
    print()
    print(f"{Colors.GREEN}✅ Credentials saved:{Colors.END}")
    print(f"  Email: {email}")
    print(f"  Password: {'*' * len(password)}")
    print()
    
    # Confirm
    confirm = input(f"{Colors.YELLOW}Continue with these credentials? (yes/no): {Colors.END}").strip().lower()
    if confirm not in ['yes', 'y']:
        print_error("Setup cancelled by user")
        sys.exit(0)
    
    logger.info(f"Credentials configured for: {email}")
    return email, password

def install_system_dependencies():
    """Install required system packages"""
    print_step(1, 11, "Installing System Dependencies")
    
    # Detect package manager
    if check_command_exists("apt-get"):
        pkg_mgr = "apt-get"
        print_info("Using apt package manager")
        run_command("sudo apt-get update -qq", "Updating package lists", retry=2)
        run_command(
            "sudo apt-get install -y python3 python3-pip python3-venv git curl wget build-essential jq",
            "Installing packages",
            retry=2
        )
    elif check_command_exists("yum"):
        pkg_mgr = "yum"
        print_info("Using yum package manager")
        run_command("sudo yum update -y -q", "Updating package lists", retry=2)
        run_command(
            "sudo yum install -y python3 python3-pip git curl wget gcc make jq",
            "Installing packages",
            retry=2
        )
    else:
        print_error("No supported package manager found (apt-get or yum)")
        return False
    
    print_success("System dependencies installed")
    return True

def clone_repository():
    """Clone or update K2Think repository"""
    print_step(2, 11, "Setting Up K2Think Repository")
    
    if K2_HOME.exists():
        print_warning(f"Directory {K2_HOME} already exists")
        print_info("Using existing directory")
        # Try to update
        run_command("git pull", "Pulling latest changes", check=False, cwd=K2_HOME)
    else:
        run_command(
            f"git clone {K2_REPO_URL} {K2_HOME}",
            "Cloning repository",
            retry=2
        )
    
    print_success("Repository ready")
    return True

def setup_python_environment():
    """Set up Python virtual environment and dependencies"""
    print_step(3, 11, "Setting Up Python Environment")
    
    venv_path = K2_HOME / "venv"
    
    if not venv_path.exists():
        run_command(f"python3 -m venv {venv_path}", "Creating virtual environment")
    else:
        print_info("Virtual environment already exists")
    
    # Upgrade pip
    run_command(
        f"{venv_path}/bin/pip install --upgrade pip -q",
        "Upgrading pip"
    )
    
    # Install requirements
    requirements_file = K2_HOME / "requirements.txt"
    if requirements_file.exists():
        run_command(
            f"{venv_path}/bin/pip install -r {requirements_file} -q",
            "Installing Python dependencies",
            retry=2
        )
    
    print_success("Python environment configured")
    return True

def configure_k2think(email, password):
    """Configure K2Think server with credentials"""
    print_step(4, 11, "Configuring K2Think Server")
    
    # Create accounts.txt
    accounts_file = K2_HOME / "accounts.txt"
    accounts_file.write_text(f"{email}\n{password}\n")
    print_success(f"Credentials configured: {email}")
    
    # Create .env file
    api_key = f"sk-k2think-proxy-{int(time.time())}"
    env_file = K2_HOME / ".env"
    env_content = f"""API_KEY={api_key}
PORT={K2_PORT}
TOKEN_UPDATE_INTERVAL=3600
"""
    env_file.write_text(env_content)
    print_success(f"Environment configured with API key: {api_key}")
    
    return api_key

def extract_tokens():
    """Extract authentication tokens from K2Think API"""
    print_step(5, 11, "Extracting K2Think Tokens")
    
    venv_path = K2_HOME / "venv"
    
    # Check which token extraction script exists
    token_script = K2_HOME / "get_tokens_fixed.py"
    if not token_script.exists():
        token_script = K2_HOME / "get_tokens.py"
    
    if token_script.exists():
        print_info(f"Using {token_script.name}")
        run_command(
            f"{venv_path}/bin/python3 {token_script}",
            "Extracting tokens",
            cwd=K2_HOME,
            retry=2
        )
    else:
        print_warning("No token extraction script found, skipping...")
    
    print_success("Tokens extracted successfully")
    return True

def start_k2think_server():
    """Start the K2Think server"""
    print_step(6, 11, "Starting K2Think Server")
    
    # Kill any existing uvicorn processes
    run_command(
        "pkill -f 'uvicorn.*k2think'",
        "Stopping existing server",
        check=False
    )
    time.sleep(2)
    
    venv_path = K2_HOME / "venv"
    start_script = K2_HOME / "scripts" / "start.sh"
    
    if start_script.exists():
        print_info("Start script executed")
        run_command(f"bash {start_script}", cwd=K2_HOME)
    else:
        # Start manually
        run_command(
            f"nohup {venv_path}/bin/uvicorn k2think_proxy:app --host 0.0.0.0 --port {K2_PORT} > server.log 2>&1 &",
            "Starting server manually",
            cwd=K2_HOME
        )
    
    # Wait for server to start
    print_info("Waiting for K2Think server to initialize...")
    time.sleep(5)
    
    # Check if server is running
    if wait_for_service(f"http://localhost:{K2_PORT}/health", HEALTH_CHECK_TIMEOUT):
        print_success(f"K2Think server is running on port {K2_PORT}")
        return True
    else:
        print_error("K2Think server failed to start")
        print_info("Check logs: tail -f ~/k2think2api3/server.log")
        return False

def install_nodejs():
    """Install Node.js if not already installed"""
    print_step(7, 11, "Installing Node.js")
    
    if check_command_exists("node"):
        node_version = run_command("node --version", capture_output=True)
        print_success(f"Node.js already installed: {node_version}")
        return True
    
    # Install via NVM
    print_info("Installing Node.js via NVM...")
    nvm_install_cmd = "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    run_command(nvm_install_cmd, "Downloading NVM", retry=2)
    
    nvm_dir = Path.home() / ".nvm"
    if nvm_dir.exists():
        run_command(
            f". {nvm_dir}/nvm.sh && nvm install --lts",
            "Installing Node.js LTS"
        )
        print_success("Node.js installed via NVM")
        return True
    
    print_error("Failed to install Node.js")
    return False

def install_claude_router():
    """Install claude-code-router globally"""
    print_step(8, 11, "Installing Claude Code Router")
    
    run_command(
        "npm install -g @musistudio/claude-code-router",
        "Installing @musistudio/claude-code-router",
        retry=2
    )
    
    print_success("Claude Code Router installed")
    return True

def configure_router(api_key):
    """Configure claude-code-router"""
    print_step(9, 11, "Configuring Claude Code Router")
    
    config_dir = Path.home() / ".claude-code-router"
    config_dir.mkdir(exist_ok=True)
    
    config = {
        "serverUrl": f"http://localhost:{K2_PORT}/v1",
        "apiKey": api_key,
        "models": {
            "claude-3-7-sonnet-20250219": "K2-Think",
            "claude-sonnet-4-20250514": "K2-Think-nothink"
        }
    }
    
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps(config, indent=2))
    
    print_success(f"Configuration saved to {config_file}")
    return True

def start_router():
    """Start claude-code-router service"""
    print_step(10, 11, "Starting Claude Code Router")
    
    # Stop existing router
    run_command("ccr stop", "Stopping existing router", check=False)
    time.sleep(2)
    
    # Start router
    print_info("Starting claude-code-router service...")
    run_command("ccr start", "Starting service")
    
    time.sleep(3)
    
    # Verify router is running
    if wait_for_service(f"http://127.0.0.1:{ROUTER_PORT}/health", HEALTH_CHECK_TIMEOUT):
        print_success(f"Claude Code Router is running on port {ROUTER_PORT}")
        return True
    else:
        print_warning("Could not verify router health, but it may still be starting")
        return True

def configure_bashrc(api_key):
    """Add K2Think environment to bashrc"""
    print_step(11, 11, "Adding Configuration to Bashrc")
    
    bashrc = Path.home() / ".bashrc"
    
    if bashrc.exists():
        content = bashrc.read_text()
        
        # Check if already configured
        if "K2THINK_HOME" in content:
            print_info(".bashrc already configured for K2Think")
            return True
        
        # Backup existing bashrc
        backup_file = Path.home() / f".bashrc.k2cc.backup.{int(time.time())}"
        shutil.copy(bashrc, backup_file)
        print_info(f"Backed up .bashrc to {backup_file}")
    
    # Add K2Think configuration
    bashrc_addition = f"""

# K2Think Environment (added by k2cc.py)
export K2THINK_HOME="{K2_HOME}"
export K2THINK_SERVER="http://localhost:{K2_PORT}"
export K2THINK_ROUTER="http://127.0.0.1:{ROUTER_PORT}"
export K2THINK_API_KEY="{api_key}"

# K2Think Aliases
alias k2-start='cd $K2THINK_HOME && bash scripts/start.sh'
alias k2-stop='pkill -f uvicorn'
alias k2-restart='k2-stop && sleep 2 && k2-start'
alias k2-status='curl -s http://localhost:{K2_PORT}/health | jq'
alias k2-logs='tail -f $K2THINK_HOME/server.log'
alias ccr-status='ccr status'

# K2Think health check function
k2check() {{
    echo "🔍 K2Think System Status"
    echo "========================"
    echo -n "K2Think Server ({K2_PORT}): "
    if curl -sf http://localhost:{K2_PORT}/health > /dev/null 2>&1; then
        echo "✅ Running"
    else
        echo "❌ Not responding"
    fi
    echo -n "Claude Router ({ROUTER_PORT}): "
    if curl -sf http://127.0.0.1:{ROUTER_PORT}/health > /dev/null 2>&1; then
        echo "✅ Running"
    else
        echo "❌ Not responding"
    fi
}}
"""
    
    with open(bashrc, 'a') as f:
        f.write(bashrc_addition)
    
    print_success("Environment configuration added to .bashrc")
    return True

def validate_deployment():
    """Validate that all services are running"""
    print_header("Validating Deployment")
    
    checks = {
        f"K2Think Server (port {K2_PORT})": wait_for_service(f"http://localhost:{K2_PORT}/health", 10),
        f"Claude Code Router (port {ROUTER_PORT})": wait_for_service(f"http://127.0.0.1:{ROUTER_PORT}/health", 10)
    }
    
    print()
    for check_name, result in checks.items():
        if result:
            print(f" {Colors.GREEN}✅ {check_name}{Colors.END}")
        else:
            print(f" {Colors.RED}❌ {check_name}{Colors.END}")
    
    return all(checks.values())

def print_final_summary():
    """Print final deployment summary"""
    print()
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}🎉 K2Think + Claude Code Deployment Complete!{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}📋 Installation Summary:{Colors.END}")
    print(f"  • K2Think Server: http://localhost:{K2_PORT}")
    print(f"  • Claude Code Router: http://127.0.0.1:{ROUTER_PORT}")
    print(f"  • Installation Directory: {K2_HOME}")
    print(f"  • Log File: {log_file}")
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

def main():
    """Main deployment function"""
    try:
        # Get credentials from user
        email, password = get_credentials()
        
        print_info(f"Installation log: {log_file}")
        print()
        
        logger.info("="*70)
        logger.info(f"K2CC v{VERSION} Deployment Started")
        logger.info(f"Email: {email}")
        logger.info("="*70)
        
        # Execute deployment steps
        steps = [
            ("System Dependencies", install_system_dependencies),
            ("Repository", clone_repository),
            ("Python Environment", setup_python_environment),
            ("K2Think Configuration", lambda: configure_k2think(email, password)),
            ("Token Extraction", extract_tokens),
            ("K2Think Server", start_k2think_server),
            ("Node.js", install_nodejs),
            ("Claude Router", install_claude_router),
        ]
        
        api_key = None
        for step_name, step_func in steps:
            if step_name == "K2Think Configuration":
                api_key = step_func()
                if not api_key:
                    print_error(f"Failed at step: {step_name}")
                    return 1
            else:
                if not step_func():
                    print_error(f"Failed at step: {step_name}")
                    return 1
        
        # Configure and start router with api_key
        if not configure_router(api_key):
            print_error("Failed to configure router")
            return 1
        
        if not start_router():
            print_error("Failed to start router")
            return 1
        
        # Configure bashrc
        configure_bashrc(api_key)
        
        # Validate deployment
        if validate_deployment():
            print_final_summary()
            logger.info("Deployment completed successfully")
            return 0
        else:
            print_error("Deployment validation failed - some services not responding")
            print_info("Check logs for details:")
            print_info(f"  - Installation log: {log_file}")
            print_info(f"  - K2Think log: {K2_HOME}/server.log")
            return 1
            
    except KeyboardInterrupt:
        print()
        print_warning("Deployment interrupted by user")
        logger.warning("Deployment interrupted by user")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error during deployment")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

