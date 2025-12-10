#!/usr/bin/env python3
"""
Test script for start_docker.py validation
Tests individual functions without requiring actual deployment
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

# Import functions from start_docker
from start_docker import (
    is_port_in_use,
    find_available_port,
    create_env_file,
    create_accounts_file,
    check_docker_installed,
    get_compose_command,
    Colors
)

def test_port_checking():
    """Test port availability checking"""
    print(f"\n{Colors.OKCYAN}Testing port checking functions...{Colors.ENDC}")
    
    # Test port 8001
    port_status = is_port_in_use(8001)
    print(f"  Port 8001 in use: {port_status}")
    
    # Find available port
    available = find_available_port(8001)
    if available:
        print(f"{Colors.OKGREEN}✓ Found available port: {available}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ No available ports found{Colors.ENDC}")
    
    return available is not None

def test_docker_detection():
    """Test Docker installation detection"""
    print(f"\n{Colors.OKCYAN}Testing Docker detection...{Colors.ENDC}")
    
    docker_installed = check_docker_installed()
    if docker_installed:
        compose_cmd = get_compose_command()
        print(f"{Colors.OKGREEN}✓ Docker installed{Colors.ENDC}")
        print(f"  Compose command: {' '.join(compose_cmd)}")
    else:
        print(f"{Colors.WARNING}⚠ Docker not installed{Colors.ENDC}")
    
    return docker_installed

def test_env_file_creation():
    """Test .env file creation"""
    print(f"\n{Colors.OKCYAN}Testing .env file creation...{Colors.ENDC}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create .env.example
        env_example = Path('.env.example')
        env_example.write_text("""
PORT=8001
ENABLE_TOKEN_AUTO_UPDATE=false
VALID_API_KEY=sk-test
""")
        
        # Test env creation
        result = create_env_file(7000)
        
        if result and Path('.env').exists():
            content = Path('.env').read_text()
            if 'PORT=7000' in content and 'ENABLE_TOKEN_AUTO_UPDATE=true' in content:
                print(f"{Colors.OKGREEN}✓ .env file created correctly{Colors.ENDC}")
                print(f"  Port updated: ✓")
                print(f"  Auto-update enabled: ✓")
                return True
        
        print(f"{Colors.FAIL}✗ .env file creation failed{Colors.ENDC}")
        return False

def test_accounts_file_creation():
    """Test accounts.txt creation"""
    print(f"\n{Colors.OKCYAN}Testing accounts.txt creation...{Colors.ENDC}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Test account creation
        result = create_accounts_file("test@example.com", "testpass123")
        
        if result and Path('data/accounts.txt').exists():
            import json
            content = Path('data/accounts.txt').read_text()
            data = json.loads(content)
            
            if data.get('email') == 'test@example.com' and data.get('k2_password') == 'testpass123':
                print(f"{Colors.OKGREEN}✓ accounts.txt created correctly{Colors.ENDC}")
                print(f"  Email: {data['email']}")
                print(f"  Password: {'*' * len(data['k2_password'])}")
                return True
        
        print(f"{Colors.FAIL}✗ accounts.txt creation failed{Colors.ENDC}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print(f"\n{Colors.OKCYAN}Checking project file structure...{Colors.ENDC}")
    
    required_files = [
        '.env.example',
        'get_tokens.py',
        'docker-compose.yml',
        'k2think_proxy.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if exists else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'start_docker.py Validation Tests':^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        # Change to project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        tests = [
            ("File Structure", test_file_structure),
            ("Docker Detection", test_docker_detection),
            ("Port Checking", test_port_checking),
            ("Environment File", test_env_file_creation),
            ("Accounts File", test_accounts_file_creation),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"{Colors.FAIL}✗ {test_name} failed with error: {e}{Colors.ENDC}")
                results.append((test_name, False))
        
        # Summary
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'Test Summary':^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
            print(f"  {status} - {test_name}")
        
        print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
        
        if passed == total:
            print(f"\n{Colors.OKGREEN}✓ All validation tests passed!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}  start_docker.py is ready for deployment.{Colors.ENDC}\n")
            return 0
        else:
            print(f"\n{Colors.WARNING}⚠ Some tests failed.{Colors.ENDC}")
            print(f"{Colors.WARNING}  Review the results above.{Colors.ENDC}\n")
            return 1
            
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    sys.exit(main())

