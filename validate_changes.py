#!/usr/bin/env python3
"""
Validation script to verify all changes are working correctly
WITHOUT needing to start the actual server
"""
import sys
import os

# Add project root to path
sys.path.insert(0, '.')

def test_imports():
    """Test 1: Verify all modules can be imported"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Module Imports")
    print("="*60)
    
    try:
        from src import api_handler
        from src import config
        from src import models
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_validation():
    """Test 2: Verify config doesn't require VALID_API_KEY"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Config Validation (VALID_API_KEY Optional)")
    print("="*60)
    
    try:
        # Temporarily remove VALID_API_KEY if it exists
        from src.config import Config
        
        # Save original value
        original_key = Config.VALID_API_KEY
        
        # Test with no API key
        Config.VALID_API_KEY = None
        
        # This should NOT raise an error anymore
        try:
            Config.validate()
            print("✅ Config validation passed with VALID_API_KEY=None")
            success = True
        except ValueError as e:
            if "VALID_API_KEY" in str(e):
                print(f"❌ Config still requires VALID_API_KEY: {e}")
                success = False
            else:
                # Different validation error (e.g., tokens file)
                print(f"✅ VALID_API_KEY validation bypassed (other error: {e})")
                success = True
        
        # Restore original value
        Config.VALID_API_KEY = original_key
        
        return success
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_api_handler_methods():
    """Test 3: Verify API handler methods work as expected"""
    print("\n" + "="*60)
    print("🧪 TEST 3: API Handler Methods")
    print("="*60)
    
    try:
        from src.api_handler import APIHandler
        from src.config import Config
        from src.constants import APIConstants
        
        # Create handler instance
        handler = APIHandler(Config)
        
        # Test 3a: API key validation (should always return True)
        print("\n📋 Test 3a: API Key Validation")
        test_keys = [
            "Bearer sk-any",
            "Bearer sk-test-123",
            "Bearer ",
            "",
            None
        ]
        
        all_passed = True
        for key in test_keys:
            result = handler.validate_api_key(key)
            status = "✅" if result else "❌"
            print(f"   {status} validate_api_key({repr(key)}) = {result}")
            if not result:
                all_passed = False
        
        if not all_passed:
            print("❌ Some API keys were rejected")
            return False
        
        print("✅ All API keys accepted (as expected)")
        
        # Test 3b: Model name mapping (should always return K2-Think)
        print("\n📋 Test 3b: Model Name Mapping")
        test_models = [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3",
            "MODEL",
            "MBZUAI-IFM/K2-Think",
            "random-model-123"
        ]
        
        all_passed = True
        for model in test_models:
            result = handler.get_actual_model_id(model)
            expected = APIConstants.MODEL_ID
            status = "✅" if result == expected else "❌"
            print(f"   {status} get_actual_model_id({repr(model)}) = {repr(result)}")
            if result != expected:
                all_passed = False
        
        if not all_passed:
            print("❌ Some models were not mapped to K2-Think")
            return False
        
        print("✅ All models mapped to K2-Think (as expected)")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_documentation():
    """Test 4: Verify documentation files exist"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Documentation")
    print("="*60)
    
    files = [
        ("CHANGES.md", "Change documentation"),
        ("README.md", "Main README"),
        ("test_open_proxy.py", "Test script"),
        (".env", "Environment config"),
        ("data/tokens.txt", "Tokens file")
    ]
    
    all_exist = True
    for filepath, description in files:
        exists = os.path.exists(filepath)
        status = "✅" if exists else "❌"
        print(f"   {status} {description}: {filepath}")
        if not exists:
            all_exist = False
    
    if all_exist:
        print("✅ All documentation files present")
        return True
    else:
        print("❌ Some documentation files missing")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 K2Think Open Proxy Mode - Validation")
    print("="*60)
    print("\nValidating all changes without starting the server...")
    
    tests = [
        ("Module Imports", test_imports),
        ("Config Validation", test_config_validation),
        ("API Handler Methods", test_api_handler_methods),
        ("Documentation", test_documentation)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Validation Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All validations passed! The changes are working correctly.")
        print("\n📝 Next Steps:")
        print("   1. Add real K2Think tokens to data/tokens.txt")
        print("   2. Run: bash scripts/start.sh")
        print("   3. Test with: python test_open_proxy.py")
        return 0
    else:
        print("\n❌ Some validations failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
