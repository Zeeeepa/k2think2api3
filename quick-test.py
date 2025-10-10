#!/usr/bin/env python3
"""
Quick K2Think API test script
Run with: bash scripts/all.sh test-quick
Or directly: python3 quick-test.py (if environment is activated)
"""

import sys
import os

def test_with_openai():
    try:
        from openai import OpenAI
        client = OpenAI()  # Uses environment variables

        print("🧪 Quick K2Think API Test")
        print("=" * 40)

        response = client.chat.completions.create(
            model="MBZUAI-IFM/K2-Think",
            messages=[{"role": "user", "content": "Hello! What are you?"}],
            max_tokens=100
        )

        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print("✅ Test successful!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_with_requests():
    try:
        import requests
        import json

        # Try to get API key from environment
        api_key = os.environ.get('VALID_API_KEY', 'sk-k2think-proxy-default')

        print("🧪 Quick K2Think API Test (Direct HTTP)")
        print("=" * 50)

        response = requests.post(
            "http://localhost:7001/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "MBZUAI-IFM/K2-Think",
                "messages": [{"role": "user", "content": "Hello! What are you?"}],
                "max_tokens": 100
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            tokens = data['usage']['total_tokens']

            print(f"Response: {content}")
            print(f"Tokens used: {tokens}")
            print("✅ Test successful!")
            return True
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("Testing K2Think API connection...")

    # Try OpenAI client first
    if test_with_openai():
        return

    # Fallback to direct requests
    print("\n🔄 Falling back to direct HTTP request...")
    if test_with_requests():
        return

    print("\n❌ All test methods failed")
    print("Please ensure:")
    print("1. Server is running: bash scripts/all.sh start")
    print("2. Environment is activated: bash scripts/all.sh activate")
    print("3. Check server logs: bash scripts/all.sh logs")
    sys.exit(1)

if __name__ == "__main__":
    main()