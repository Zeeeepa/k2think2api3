#!/usr/bin/env python3
import os, sys, json, requests

def test_direct():
    # Load token
    with open("data/tokens.txt") as f:
        for line in f:
            token = line.strip()
            if token and not token.startswith('#'):
                break
    
    url = "https://www.k2think.ai/api/chat/completions"
    payload = {"model": "MBZUAI-IFM/K2-Think", "messages": [{"role": "user", "content": "test"}], "stream": False}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("Testing K2Think API...")
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("✅ SUCCESS - Direct API works!")
        return True
    print(f"❌ FAIL: {r.text[:200]}")
    return False

if __name__ == "__main__":
    result = test_direct()
    sys.exit(0 if result else 1)
