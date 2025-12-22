#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Utilities for K2Think Multi-Instance Deployment
======================================================
Common functionality used by both start_docker.py and k2think_manager.py
to eliminate code duplication and ensure consistent behavior.

Modules:
- CredentialCollector: Interactive credential gathering with validation
- PortSelector: Unified port finding logic with registry awareness
- HealthChecker: Health endpoint verification with retries
- DockerHelper: Docker and Docker Compose utilities
"""

import os
import sys
import json
import socket
import subprocess
import time
import requests
from pathlib import Path
from getpass import getpass
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass

# Try to import error_handler, fall back gracefully
try:
    from src.error_handler import retry_with_backoff, ErrorCategory
    HAS_ERROR_HANDLER = True
except ImportError:
    HAS_ERROR_HANDLER = False
    # Simple fallback retry decorator
    def retry_with_backoff(**kwargs):
        def decorator(func):
            return func
        return decorator


@dataclass
class Credentials:
    """Container for K2Think credentials"""
    email: str
    password: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {"email": self.email, "k2_password": self.password}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class CredentialCollector:
    """
    Interactive credential collection with validation and multiple sources.
    
    Supports loading from:
    - Environment variables (K2_EMAIL, K2_PASSWORD)
    - Existing accounts file
    - Interactive prompt
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        return '@' in email and '.' in email.split('@')[-1]
    
    @staticmethod
    def load_from_env() -> Optional[Credentials]:
        """Load credentials from environment variables"""
        email = os.getenv('K2_EMAIL')
        password = os.getenv('K2_PASSWORD')
        
        if email and password:
            if CredentialCollector.validate_email(email):
                return Credentials(email=email, password=password)
            else:
                print(f"Warning: Invalid email format in K2_EMAIL: {email}")
        
        return None
    
    @staticmethod
    def load_from_file(file_path: Path) -> Optional[Credentials]:
        """
        Load credentials from accounts file.
        
        Args:
            file_path: Path to accounts.txt file
            
        Returns:
            Credentials if file exists and is valid, None otherwise
        """
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                
                # Parse JSON
                data = json.loads(content)
                email = data.get('email')
                password = data.get('k2_password') or data.get('password')
                
                if email and password:
                    return Credentials(email=email, password=password)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load credentials from {file_path}: {e}")
        
        return None
    
    @staticmethod
    def prompt_interactive() -> Credentials:
        """
        Interactively prompt for credentials.
        
        Returns:
            Credentials from user input
        """
        print("\n=== K2Think Credentials Required ===\n")
        
        while True:
            email = input("Email: ").strip()
            if CredentialCollector.validate_email(email):
                break
            print("Invalid email format. Please try again.")
        
        password = getpass("Password: ")
        
        return Credentials(email=email, password=password)
    
    @staticmethod
    def collect(
        accounts_file: Optional[Path] = None,
        interactive: bool = True
    ) -> Credentials:
        """
        Collect credentials from available sources with priority:
        1. Environment variables
        2. Existing accounts file
        3. Interactive prompt (if enabled)
        
        Args:
            accounts_file: Path to accounts file to check
            interactive: Whether to prompt user if no credentials found
            
        Returns:
            Credentials object
            
        Raises:
            ValueError: If no credentials available and interactive=False
        """
        # Try environment variables first
        creds = CredentialCollector.load_from_env()
        if creds:
            print(f"✓ Using credentials from environment: {creds.email}")
            return creds
        
        # Try accounts file
        if accounts_file:
            creds = CredentialCollector.load_from_file(accounts_file)
            if creds:
                print(f"✓ Using existing credentials: {creds.email}")
                return creds
        
        # Interactive prompt
        if interactive:
            return CredentialCollector.prompt_interactive()
        
        raise ValueError("No credentials available and interactive mode disabled")
    
    @staticmethod
    def save_to_file(credentials: Credentials, file_path: Path):
        """
        Save credentials to file.
        
        Args:
            credentials: Credentials to save
            file_path: Target file path
        """
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write credentials
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(credentials.to_json())
        
        # Set secure permissions (readable only by owner)
        try:
            os.chmod(file_path, 0o600)
        except Exception:
            pass  # Windows doesn't support chmod


class PortSelector:
    """
    Unified port selection with availability checking and registry awareness.
    """
    
    DEFAULT_START_PORT = 8001
    DEFAULT_END_PORT = 9000
    
    @staticmethod
    def is_port_available(port: int, host: str = '127.0.0.1') -> bool:
        """
        Check if port is available on host.
        
        Args:
            port: Port number to check
            host: Host address (default: localhost)
            
        Returns:
            True if port is available, False otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.bind((host, port))
            return True
        except (OSError, socket.error):
            return False
        finally:
            sock.close()
    
    @staticmethod
    def load_registry(registry_file: Path) -> Dict:
        """Load instance registry"""
        if not registry_file.exists():
            return {"instances": {}}
        
        try:
            with open(registry_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"instances": {}}
    
    @staticmethod
    def find_available_port(
        start_port: int = DEFAULT_START_PORT,
        end_port: int = DEFAULT_END_PORT,
        registry_file: Optional[Path] = None
    ) -> int:
        """
        Find first available port in range, checking both OS and registry.
        
        Args:
            start_port: Starting port number
            end_port: Ending port number (exclusive)
            registry_file: Optional registry file to check for allocated ports
            
        Returns:
            Available port number
            
        Raises:
            RuntimeError: If no available ports found
        """
        # Load registry to check allocated ports
        allocated_ports = set()
        if registry_file and registry_file.exists():
            registry = PortSelector.load_registry(registry_file)
            for instance in registry.get("instances", {}).values():
                if instance.get("port"):
                    allocated_ports.add(instance["port"])
        
        # Search for available port
        for port in range(start_port, end_port):
            # Skip if allocated in registry
            if port in allocated_ports:
                continue
            
            # Check OS availability
            if PortSelector.is_port_available(port):
                return port
        
        raise RuntimeError(
            f"No available ports found in range {start_port}-{end_port-1}. "
            f"Registry allocated: {sorted(allocated_ports)}"
        )
    
    @staticmethod
    def find_available_port_with_fallback(
        preferred_port: Optional[int] = None,
        registry_file: Optional[Path] = None
    ) -> Tuple[int, bool]:
        """
        Find available port, trying preferred port first.
        
        Args:
            preferred_port: Preferred port to try first
            registry_file: Registry file to check
            
        Returns:
            Tuple of (port, is_preferred) where is_preferred indicates
            whether the preferred port was used
        """
        if preferred_port:
            # Check if preferred port is available
            if PortSelector.is_port_available(preferred_port):
                # Also check registry
                if registry_file and registry_file.exists():
                    registry = PortSelector.load_registry(registry_file)
                    allocated = [
                        inst["port"] for inst in registry.get("instances", {}).values()
                        if inst.get("port") == preferred_port
                    ]
                    if not allocated:
                        return preferred_port, True
                else:
                    return preferred_port, True
        
        # Fall back to finding any available port
        port = PortSelector.find_available_port(registry_file=registry_file)
        return port, False


class HealthChecker:
    """
    Health endpoint verification with retries and timeout handling.
    """
    
    @staticmethod
    @retry_with_backoff(max_attempts=3, initial_delay=2.0)
    def check_health(
        host: str = 'localhost',
        port: int = 8001,
        timeout: int = 10
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check health endpoint.
        
        Args:
            host: Server host
            port: Server port
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_healthy, response_data)
        """
        url = f"http://{host}:{port}/health"
        
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            is_healthy = data.get('status') == 'healthy'
            
            return is_healthy, data
        except requests.RequestException as e:
            return False, {"error": str(e)}
    
    @staticmethod
    def wait_for_healthy(
        host: str = 'localhost',
        port: int = 8001,
        max_wait: int = 60,
        check_interval: int = 5
    ) -> bool:
        """
        Wait for service to become healthy.
        
        Args:
            host: Server host
            port: Server port
            max_wait: Maximum wait time in seconds
            check_interval: Interval between checks in seconds
            
        Returns:
            True if service became healthy, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            is_healthy, _ = HealthChecker.check_health(host, port, timeout=5)
            if is_healthy:
                return True
            
            time.sleep(check_interval)
        
        return False


class DockerHelper:
    """
    Docker and Docker Compose utilities.
    """
    
    @staticmethod
    def detect_compose_command() -> Optional[str]:
        """
        Detect available Docker Compose command.
        
        Returns:
            'docker compose' (v2), 'docker-compose' (v1), or None if not found
        """
        # Try Docker Compose v2 (docker compose)
        try:
            result = subprocess.run(
                ['docker', 'compose', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return 'docker compose'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try Docker Compose v1 (docker-compose)
        try:
            result = subprocess.run(
                ['docker-compose', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return 'docker-compose'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def is_docker_available() -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def get_container_status(container_name: str) -> Optional[str]:
        """
        Get Docker container status.
        
        Args:
            container_name: Name of container
            
        Returns:
            Status string ('running', 'exited', etc.) or None if not found
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                if 'Up' in status:
                    return 'running'
                elif 'Exited' in status:
                    return 'exited'
                else:
                    return 'unknown'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def execute_compose_command(
        command: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Execute Docker Compose command.
        
        Args:
            command: Compose command (e.g., ['up', '-d'])
            cwd: Working directory
            env: Environment variables
            
        Returns:
            CompletedProcess result
            
        Raises:
            RuntimeError: If Docker Compose not available
        """
        compose_cmd = DockerHelper.detect_compose_command()
        if not compose_cmd:
            raise RuntimeError("Docker Compose not found. Please install Docker Compose.")
        
        # Build full command
        if compose_cmd == 'docker compose':
            full_cmd = ['docker', 'compose'] + command
        else:
            full_cmd = ['docker-compose'] + command
        
        # Execute
        return subprocess.run(
            full_cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True
        )

