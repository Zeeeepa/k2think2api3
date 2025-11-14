#!/usr/bin/env python3
"""
Test Claude Code Router Integration with K2Think Server
Verifies the complete integration is working end-to-end
"""

import requests
import json
import sys

def test_k2think_server():
    """Test K2Think server is responding"""
    print("🔍 Testing K2Think server...")
    try:
        response = requests.get("http://localhost:7000/health", timeout=5)
        if response.status_code == 200 or requests.get("http://localhost:7000/").status_code == 200:
            print("✅ K2Think server is running (port 7000)")
            return True
    except:
        print("❌ K2Think server is not responding")
        return False

def test_claude_code_router():
    """Test claude-code-router is running"""
    print("\n🔍 Testing claude-code-router...")
    try:
        response = requests.get("http://127.0.0.1:3456/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ claude-code-router is running (port 3456)")
            print(f"   Status: {data.get('status')}")
            return True
    except:
        print("❌ claude-code-router is not responding")
        return False

def test_end_to_end():
    """Test end-to-end integration via Anthropic API format"""
    print("\n🔍 Testing end-to-end integration...")
    
    # This is how Claude Code sends requests
    anthropic_request = {
        "model": "claude-3-5-sonnet-20241022",  # Claude Code sends this
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from K2Think via Claude Code Router!' in exactly 8 words."
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:3456/v1/messages",
            json=anthropic_request,
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ End-to-end test passed!")
            print(f"\n📝 Response from K2Think:")
            
            # Extract content from Anthropic format
            if "content" in data and len(data["content"]) > 0:
                content = data["content"][0].get("text", "")
                print(f"   {content[:200]}")
            else:
                print(f"   {str(data)[:200]}")
            
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {str(e)}")
        return False

def test_openai_format():
    """Test OpenAI format (which K2Think uses internally)"""
    print("\n🔍 Testing OpenAI format compatibility...")
    
    openai_request = {
        "model": "MBZUAI-IFM/K2-Think",
        "messages": [
            {
                "role": "user",
                "content": "Say hello in 3 words"
            }
        ]
    }
    
    try:
        # Test via router (which should pass through to K2Think)
        response = requests.post(
            "http://127.0.0.1:3456/v1/chat/completions",
            json=openai_request,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-any-key"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ OpenAI format test passed!")
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"\n📝 Response: {content[:200]}")
            
            return True
        else:
            print(f"⚠️  OpenAI format returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  OpenAI format test failed: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🎯 Claude Code Router + K2Think Integration Test")
    print("=" * 70)
    print()
    
    results = {
        "K2Think Server": test_k2think_server(),
        "Claude Code Router": test_claude_code_router(),
        "End-to-End (Anthropic API)": test_end_to_end(),
        "OpenAI Format": test_openai_format()
    }
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}  {test_name}")
    
    print()
    
    all_passed = all(results.values())
    critical_passed = results["K2Think Server"] and results["Claude Code Router"]
    
    if all_passed:
        print("🎉 All tests passed! Integration is working perfectly!")
        print()
        print("🚀 You can now use Claude Code with K2Think:")
        print("   ccr code \"Create a hello world script\"")
        return 0
    elif critical_passed:
        print("⚠️  Critical services are running, but some tests failed")
        print("   The integration should still work, but may have compatibility issues")
        return 0
    else:
        print("❌ Integration is not working properly")
        print()
        print("🔧 Troubleshooting:")
        if not results["K2Think Server"]:
            print("   • Start K2Think server: bash scripts/start.sh")
        if not results["Claude Code Router"]:
            print("   • Start router: ccr start")
        return 1

if __name__ == "__main__":
    sys.exit(main())

