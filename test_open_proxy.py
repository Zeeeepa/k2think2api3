#!/usr/bin/env python3
"""
Test script to verify the open proxy mode works correctly
Tests:
1. Any API key is accepted
2. Any model name routes to K2-Think
"""
import sys
import time
from openai import OpenAI

def test_client(api_key, model_name, test_name):
    """Test a specific API key and model combination"""
    print(f"\n{'='*60}")
    print(f"🧪 Test: {test_name}")
    print(f"   API Key: {api_key}")
    print(f"   Model: {model_name}")
    print(f"{'='*60}")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="http://localhost:7000/v1"
        )
        
        # Just check if the connection works (don't actually make API call)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'test' once"}],
            max_tokens=5,
            stream=False
        )
        
        print(f"✅ SUCCESS!")
        print(f"   Response: {response.choices[0].message.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    print("\n🚀 Testing K2Think Open Proxy Mode")
    print("="*60)
    
    tests = [
        # Test different API keys
        ("sk-any", "MBZUAI-IFM/K2-Think", "Standard with 'sk-any' key"),
        ("sk-test-123", "MBZUAI-IFM/K2-Think", "Standard with custom key"),
        ("", "MBZUAI-IFM/K2-Think", "Standard with empty key"),
        
        # Test different model names
        ("sk-any", "gpt-4", "GPT-4 model name"),
        ("sk-any", "gpt-3.5-turbo", "GPT-3.5 model name"),
        ("sk-any", "claude-3", "Claude model name"),
        ("sk-any", "MODEL", "Generic MODEL name"),
        ("sk-any", "random-model-123", "Random model name"),
    ]
    
    results = []
    for api_key, model, test_name in tests:
        result = test_client(api_key, model, test_name)
        results.append((test_name, result))
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
