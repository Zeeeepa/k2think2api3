#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K2Think Multi-Instance Deployment Manager
==========================================
Manage multiple K2Think API proxy instances with isolated credentials,
ports, and independent lifecycle management.

Usage:
    python k2think_manager.py create <instance-name> [options]
    python k2think_manager.py start <instance-name>
    python k2think_manager.py stop <instance-name>
    python k2think_manager.py list
    python k2think_manager.py endpoints
"""

import os
import sys
import json
import socket
import argparse
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from getpass import getpass

# ============================================================================
# UTF-8 ENCODING SETUP (完整中文支持)
# ============================================================================
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
os.environ.setdefault('PYTHONLEGACYWINDOWSSTDIO', '0')
os.environ.setdefault('LC_ALL', 'C.UTF-8')
os.environ.setdefault('LANG', 'C.UTF-8')

import locale
try:
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

# ============================================================================
# COLOR CODES
# ============================================================================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ============================================================================
# CONFIGURATION
# ============================================================================
INSTANCES_DIR = Path("instances")
REGISTRY_FILE = INSTANCES_DIR / "instances.json"
COMPOSE_TEMPLATE = "docker-compose.template.yml"
DEFAULT_PORT_START = 8001
DEFAULT_PORT_END = 9000

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

# ============================================================================
# INSTANCE REGISTRY
# ============================================================================
class InstanceRegistry:
    """Manages the instance registry (instances.json)"""
    
    def __init__(self):
        self.registry_file = REGISTRY_FILE
        self.instances_dir = INSTANCES_DIR
        self._ensure_directory()
        self.data = self._load()
    
    def _ensure_directory(self):
        """Ensure instances directory exists"""
        self.instances_dir.mkdir(exist_ok=True)
    
    def _load(self) -> Dict:
        """Load registry from file"""
        if not self.registry_file.exists():
            return {
                "instances": {},
                "next_port": DEFAULT_PORT_START
            }
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print_error(f"Failed to load registry: {e}")
            return {"instances": {}, "next_port": DEFAULT_PORT_START}
    
    def _save(self):
        """Save registry to file"""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print_error(f"Failed to save registry: {e}")
    
    def add_instance(self, name: str, port: int, container_name: str):
        """Add instance to registry"""
        self.data["instances"][name] = {
            "port": port,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "endpoint": f"http://localhost:{port}",
            "container_name": container_name
        }
        self._save()
    
    def update_status(self, name: str, status: str):
        """Update instance status"""
        if name in self.data["instances"]:
            self.data["instances"][name]["status"] = status
            self._save()
    
    def remove_instance(self, name: str):
        """Remove instance from registry"""
        if name in self.data["instances"]:
            del self.data["instances"][name]
            self._save()
    
    def get_instance(self, name: str) -> Optional[Dict]:
        """Get instance details"""
        return self.data["instances"].get(name)
    
    def list_instances(self) -> Dict:
        """Get all instances"""
        return self.data["instances"]
    
    def instance_exists(self, name: str) -> bool:
        """Check if instance exists"""
        return name in self.data["instances"]

# ============================================================================
# PORT MANAGER
# ============================================================================
class PortManager:
    """Manages port allocation for instances"""
    
    def __init__(self, registry: InstanceRegistry):
        self.registry = registry
    
    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        # Check registry
        for instance in self.registry.data["instances"].values():
            if instance["port"] == port:
                return False
        
        # Check OS-level availability
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return True
        except OSError:
            return False
    
    def allocate_port(self, preferred: Optional[int] = None) -> int:
        """Allocate next available port"""
        if preferred and self.is_port_available(preferred):
            return preferred
        
        # Sequential allocation
        port = self.registry.data["next_port"]
        while port < DEFAULT_PORT_END:
            if self.is_port_available(port):
                self.registry.data["next_port"] = port + 1
                self.registry._save()
                return port
            port += 1
        
        raise Exception(f"No available ports in range {DEFAULT_PORT_START}-{DEFAULT_PORT_END}")

# ============================================================================
# DOCKER COMPOSE DETECTOR
# ============================================================================
def detect_docker_compose_command() -> List[str]:
    """Detect available docker compose command"""
    # Try v2 first
    try:
        result = subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Docker Compose v2 detected")
            return ['docker', 'compose']
    except:
        pass
    
    # Try v1
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Docker Compose v1 detected")
            return ['docker-compose']
    except:
        pass
    
    return None

# ============================================================================
# INSTANCE MANAGER
# ============================================================================
class InstanceManager:
    """Manages K2Think instance lifecycle"""
    
    def __init__(self):
        self.registry = InstanceRegistry()
        self.port_manager = PortManager(self.registry)
        self.compose_cmd = detect_docker_compose_command()
        
        if not self.compose_cmd:
            print_error("Docker Compose not found!")
            print_info("Install instructions:")
            print_info("  Ubuntu/Debian: sudo apt-get install docker-compose-plugin")
            print_info("  RHEL/CentOS: sudo yum install docker-compose-plugin")
            print_info("  macOS: brew install docker-compose")
            sys.exit(1)
    
    def _validate_instance_name(self, name: str) -> bool:
        """Validate instance name (alphanumeric + dash/underscore)"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            print_error("Instance name must contain only letters, numbers, dashes, and underscores")
            return False
        return True
    
    def _get_instance_dir(self, name: str) -> Path:
        """Get instance directory path"""
        return INSTANCES_DIR / name
    
    def _create_docker_compose_file(self, instance_dir: Path, instance_name: str, port: int):
        """Create docker-compose.yml for instance"""
        compose_content = f"""version: '3.8'

services:
  k2think-api:
    image: julienol/k2think2api:latest
    container_name: k2think-{instance_name}
    ports:
      - "{port}:8001"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONIOENCODING=utf-8
      - PYTHONLEGACYWINDOWSSTDIO=0
      - LC_ALL=C.UTF-8
      - LANG=C.UTF-8
      - TOKENS_FILE=/app/data/tokens.txt
      - ACCOUNTS_FILE=/app/data/accounts.txt
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - k2think-{instance_name}

networks:
  k2think-{instance_name}:
    driver: bridge
"""
        
        compose_file = instance_dir / "docker-compose.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(compose_content)
        
        print_success(f"Created docker-compose.yml")
    
    def _create_env_file(self, instance_dir: Path, port: int):
        """Create .env file for instance"""
        env_content = f"""# K2Think API Proxy Configuration
PORT={port}
HOST=0.0.0.0

# Token Management
ENABLE_TOKEN_AUTO_UPDATE=true
TOKEN_UPDATE_INTERVAL=3600

# CORS Settings
CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
"""
        
        env_file = instance_dir / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print_success(f"Created .env (PORT={port})")
    
    def create_instance(self, name: str, port: Optional[int] = None, 
                       email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Create new instance"""
        print_header(f"Creating Instance: {name}")
        
        # Validate name
        if not self._validate_instance_name(name):
            return False
        
        # Check if exists
        if self.registry.instance_exists(name):
            print_error(f"Instance '{name}' already exists")
            return False
        
        # Allocate port
        try:
            allocated_port = self.port_manager.allocate_port(port)
            print_success(f"Allocated port: {allocated_port}")
        except Exception as e:
            print_error(f"Port allocation failed: {e}")
            return False
        
        # Create instance directory
        instance_dir = self._get_instance_dir(name)
        try:
            instance_dir.mkdir(parents=True, exist_ok=False)
            (instance_dir / "data").mkdir(exist_ok=True)
            print_success(f"Created instance directory: {instance_dir}")
        except Exception as e:
            print_error(f"Failed to create directory: {e}")
            return False
        
        # Create docker-compose.yml
        try:
            self._create_docker_compose_file(instance_dir, name, allocated_port)
        except Exception as e:
            print_error(f"Failed to create docker-compose.yml: {e}")
            shutil.rmtree(instance_dir)
            return False
        
        # Create .env
        try:
            self._create_env_file(instance_dir, allocated_port)
        except Exception as e:
            print_error(f"Failed to create .env: {e}")
            shutil.rmtree(instance_dir)
            return False
        
        # Handle credentials
        if email and password:
            accounts_file = instance_dir / "data" / "accounts.txt"
            try:
                credentials = {"email": email, "k2_password": password}
                with open(accounts_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(credentials))
                print_success("Saved credentials")
                
                # Fetch tokens
                print_info("Fetching authentication token...")
                self._fetch_tokens(instance_dir)
            except Exception as e:
                print_warning(f"Failed to save credentials: {e}")
        else:
            print_info("No credentials provided. You can add them later to data/accounts.txt")
        
        # Register instance
        container_name = f"k2think-{name}"
        self.registry.add_instance(name, allocated_port, container_name)
        
        print_success(f"Instance '{name}' created successfully!")
        print_info(f"Endpoint: http://localhost:{allocated_port}")
        print_info(f"Start with: python k2think_manager.py start {name}")
        
        return True
    
    def _fetch_tokens(self, instance_dir: Path):
        """Fetch tokens using get_tokens.py"""
        accounts_file = instance_dir / "data" / "accounts.txt"
        tokens_file = instance_dir / "data" / "tokens.txt"
        
        if not Path("get_tokens.py").exists():
            print_warning("get_tokens.py not found, skipping token fetch")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, 'get_tokens.py', str(accounts_file), str(tokens_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print_success("Token fetched successfully")
            else:
                print_warning(f"Token fetch failed: {result.stderr}")
        except Exception as e:
            print_warning(f"Token fetch error: {e}")
    
    def start_instance(self, name: str) -> bool:
        """Start instance"""
        print_header(f"Starting Instance: {name}")
        
        # Check if exists
        if not self.registry.instance_exists(name):
            print_error(f"Instance '{name}' not found")
            return False
        
        instance = self.registry.get_instance(name)
        instance_dir = self._get_instance_dir(name)
        
        # Check if port is available
        if not self.port_manager.is_port_available(instance['port']):
            # Check if it's our own container
            result = subprocess.run(
                ['docker', 'ps', '--filter', f"name={instance['container_name']}", '--format', '{{.Names}}'],
                capture_output=True, text=True
            )
            if instance['container_name'] not in result.stdout:
                print_error(f"Port {instance['port']} is in use by another process")
                return False
            else:
                print_info(f"Instance '{name}' is already running")
                return True
        
        # Start with docker-compose
        try:
            os.chdir(instance_dir)
            cmd = self.compose_cmd + ['--project-name', f'k2think-{name}', 'up', '-d']
            
            print_info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print_error(f"Failed to start instance: {result.stderr}")
                return False
            
            # Wait for health check
            print_info("Waiting for container to be healthy...")
            time.sleep(5)
            
            # Update status
            self.registry.update_status(name, "running")
            
            print_success(f"Instance '{name}' started successfully!")
            print_info(f"Endpoint: {instance['endpoint']}")
            print_info(f"OpenAI API: {instance['endpoint']}/v1/chat/completions")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to start instance: {e}")
            return False
        finally:
            os.chdir(Path(__file__).parent)
    
    def stop_instance(self, name: str) -> bool:
        """Stop instance"""
        print_header(f"Stopping Instance: {name}")
        
        if not self.registry.instance_exists(name):
            print_error(f"Instance '{name}' not found")
            return False
        
        instance_dir = self._get_instance_dir(name)
        
        try:
            os.chdir(instance_dir)
            cmd = self.compose_cmd + ['--project-name', f'k2think-{name}', 'down']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print_error(f"Failed to stop instance: {result.stderr}")
                return False
            
            self.registry.update_status(name, "stopped")
            print_success(f"Instance '{name}' stopped successfully!")
            return True
            
        except Exception as e:
            print_error(f"Failed to stop instance: {e}")
            return False
        finally:
            os.chdir(Path(__file__).parent)
    
    def restart_instance(self, name: str) -> bool:
        """Restart instance"""
        print_header(f"Restarting Instance: {name}")
        
        if self.stop_instance(name):
            time.sleep(2)
            return self.start_instance(name)
        return False
    
    def delete_instance(self, name: str, keep_data: bool = False) -> bool:
        """Delete instance"""
        print_header(f"Deleting Instance: {name}")
        
        if not self.registry.instance_exists(name):
            print_error(f"Instance '{name}' not found")
            return False
        
        # Stop first
        instance = self.registry.get_instance(name)
        if instance['status'] == 'running':
            print_info("Stopping running instance...")
            self.stop_instance(name)
        
        # Remove directory
        instance_dir = self._get_instance_dir(name)
        
        try:
            if keep_data:
                # Move data to backup
                data_dir = instance_dir / "data"
                backup_dir = instance_dir.parent / f"{name}-data-backup-{int(time.time())}"
                if data_dir.exists():
                    shutil.move(str(data_dir), str(backup_dir))
                    print_info(f"Data backed up to: {backup_dir}")
            
            # Remove instance directory
            if instance_dir.exists():
                shutil.rmtree(instance_dir)
                print_success(f"Removed instance directory")
            
            # Remove from registry
            self.registry.remove_instance(name)
            print_success(f"Instance '{name}' deleted successfully!")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to delete instance: {e}")
            return False
    
    def list_instances(self):
        """List all instances"""
        instances = self.registry.list_instances()
        
        if not instances:
            print_info("No instances found. Create one with: python k2think_manager.py create <name>")
            return
        
        print_header("K2Think Deployment Manager")
        print(f"{Colors.BOLD}Total Instances: {len(instances)}{Colors.ENDC}\n")
        
        # Table header
        print(f"{Colors.BOLD}{'NAME':<20} {'STATUS':<10} {'PORT':<6} {'ENDPOINT':<30}{Colors.ENDC}")
        print("-" * 70)
        
        # List instances
        for name, info in sorted(instances.items()):
            status_color = Colors.OKGREEN if info['status'] == 'running' else Colors.WARNING
            status_symbol = "✓" if info['status'] == 'running' else "✗"
            
            print(f"{name:<20} {status_color}{status_symbol} {info['status']:<9}{Colors.ENDC} "
                  f"{info['port']:<6} {info['endpoint']:<30}")
        
        print()
    
    def show_endpoints(self):
        """Show all active endpoints"""
        instances = self.registry.list_instances()
        running = {name: info for name, info in instances.items() if info['status'] == 'running'}
        
        if not running:
            print_info("No running instances. Start one with: python k2think_manager.py start <name>")
            return
        
        print_header("Active OpenAI-Compatible Endpoints")
        
        for name, info in sorted(running.items()):
            print(f"{Colors.OKGREEN}• {name:<20}{Colors.ENDC} {info['endpoint']}/v1/chat/completions")
        
        print()
    
    def show_status(self, name: str):
        """Show detailed instance status"""
        if not self.registry.instance_exists(name):
            print_error(f"Instance '{name}' not found")
            return
        
        instance = self.registry.get_instance(name)
        
        print_header(f"Instance Status: {name}")
        print(f"{Colors.BOLD}Port:{Colors.ENDC} {instance['port']}")
        print(f"{Colors.BOLD}Status:{Colors.ENDC} {instance['status']}")
        print(f"{Colors.BOLD}Endpoint:{Colors.ENDC} {instance['endpoint']}")
        print(f"{Colors.BOLD}Container:{Colors.ENDC} {instance['container_name']}")
        print(f"{Colors.BOLD}Created:{Colors.ENDC} {instance['created_at']}")
        
        # Check container status
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', f"name={instance['container_name']}", 
             '--format', '{{.Status}}'],
            capture_output=True, text=True
        )
        
        if result.stdout.strip():
            print(f"{Colors.BOLD}Container Status:{Colors.ENDC} {result.stdout.strip()}")
        
        print()
    
    def show_logs(self, name: str, follow: bool = False, tail: int = 100):
        """Show instance logs"""
        if not self.registry.instance_exists(name):
            print_error(f"Instance '{name}' not found")
            return
        
        instance_dir = self._get_instance_dir(name)
        
        try:
            os.chdir(instance_dir)
            cmd = self.compose_cmd + ['--project-name', f'k2think-{name}', 'logs']
            
            if follow:
                cmd.append('-f')
            
            cmd.extend(['--tail', str(tail)])
            
            print_info(f"Showing logs for instance '{name}'...")
            print_info("Press Ctrl+C to exit\n")
            
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            print("\n")
        except Exception as e:
            print_error(f"Failed to show logs: {e}")
        finally:
            os.chdir(Path(__file__).parent)

# ============================================================================
# MAIN CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="K2Think Multi-Instance Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python k2think_manager.py create prod-api --port 8001 --email user@example.com
  python k2think_manager.py start prod-api
  python k2think_manager.py list
  python k2think_manager.py endpoints
  python k2think_manager.py logs prod-api -f
  python k2think_manager.py stop prod-api
  python k2think_manager.py delete test-api --keep-data
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new instance')
    create_parser.add_argument('name', help='Instance name')
    create_parser.add_argument('--port', type=int, help='Port number (auto-allocated if not specified)')
    create_parser.add_argument('--email', help='K2Think account email')
    create_parser.add_argument('--password', help='K2Think account password')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start instance')
    start_parser.add_argument('name', help='Instance name')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop instance')
    stop_parser.add_argument('name', help='Instance name')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart instance')
    restart_parser.add_argument('name', help='Instance name')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete instance')
    delete_parser.add_argument('name', help='Instance name')
    delete_parser.add_argument('--keep-data', action='store_true', help='Backup data before deletion')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all instances')
    
    # Endpoints command
    endpoints_parser = subparsers.add_parser('endpoints', help='Show active endpoints')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show instance status')
    status_parser.add_argument('name', help='Instance name')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show instance logs')
    logs_parser.add_argument('name', help='Instance name')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow log output')
    logs_parser.add_argument('--tail', type=int, default=100, help='Number of lines to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = InstanceManager()
    
    try:
        if args.command == 'create':
            # Prompt for credentials if not provided
            email = args.email
            password = args.password
            
            if email and not password:
                password = getpass("Enter K2Think password: ")
            
            manager.create_instance(args.name, args.port, email, password)
        
        elif args.command == 'start':
            manager.start_instance(args.name)
        
        elif args.command == 'stop':
            manager.stop_instance(args.name)
        
        elif args.command == 'restart':
            manager.restart_instance(args.name)
        
        elif args.command == 'delete':
            manager.delete_instance(args.name, args.keep_data)
        
        elif args.command == 'list':
            manager.list_instances()
        
        elif args.command == 'endpoints':
            manager.show_endpoints()
        
        elif args.command == 'status':
            manager.show_status(args.name)
        
        elif args.command == 'logs':
            manager.show_logs(args.name, args.follow, args.tail)
    
    except KeyboardInterrupt:
        print("\n")
        print_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

