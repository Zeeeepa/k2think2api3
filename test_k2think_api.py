#!/usr/bin/env python3
"""
K2Think API Login Debugger
Tests the login API directly with detailed debugging
"""

import requests
import json
import sys
from datetime import datetime

def test_k2think_api_login(email: str, password: str):
    """
    Test K2Think login API with detailed debugging
    """
    print("=" * 70)
    print("🔍 K2Think API Login Debugger")
    print("=" * 70)
    print()
    print(f"📧 Email: {email}")
    print(f"🔒 Password: {'*' * len(password)}")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "https://www.k2think.ai"
    login_url = f"{base_url}/api/v1/auths/signin"
    
    # Headers matching browser
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'Origin': 'https://www.k2think.ai',
        'Referer': 'https://www.k2think.ai/auth?mode=signin',
        'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    
    # Login payload
    payload = {
        "email": email,
        "password": password
    }
    
    print(f"📍 API Endpoint: {login_url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        # Make the request
        print("🌐 Sending POST request...")
        session = requests.Session()
        response = session.post(
            login_url,
            json=payload,
            headers=headers,
            timeout=30,
            allow_redirects=False
        )
        
        print(f"✅ Response received")
        print()
        print("=" * 70)
        print("📊 RESPONSE DETAILS")
        print("=" * 70)
        print(f"Status Code: {response.status_code}")
        print()
        
        # Response headers
        print("📋 Response Headers:")
        for key, value in response.headers.items():
            if 'cookie' in key.lower() or 'token' in key.lower() or 'authorization' in key.lower():
                print(f"   ⭐ {key}: {value}")
            else:
                print(f"   • {key}: {value[:100] if len(value) > 100 else value}")
        print()
        
        # Check for Set-Cookie
        if 'Set-Cookie' in response.headers:
            print("🍪 SET-COOKIE HEADER FOUND!")
            cookies_header = response.headers['Set-Cookie']
            print(f"   Value: {cookies_header}")
            
            # Try to extract token
            if 'token=' in cookies_header:
                import re
                match = re.search(r'token=([^;]+)', cookies_header)
                if match:
                    token = match.group(1)
                    print(f"\n✅ TOKEN EXTRACTED: {token[:50]}..." if len(token) > 50 else f"\n✅ TOKEN EXTRACTED: {token}")
        else:
            print("❌ No Set-Cookie header found")
        
        print()
        
        # Cookies from session
        print("🍪 Session Cookies:")
        if session.cookies:
            for cookie in session.cookies:
                print(f"   • {cookie.name}: {cookie.value[:50]}..." if len(cookie.value) > 50 else f"   • {cookie.name}: {cookie.value}")
        else:
            print("   No cookies in session")
        print()
        
        # Response body
        print("📄 Response Body:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            
            # Check for token in response body
            if isinstance(response_json, dict):
                for key in ['token', 'access_token', 'accessToken', 'jwt']:
                    if key in response_json:
                        print(f"\n✅ TOKEN FOUND IN BODY (key='{key}'): {response_json[key][:50]}...")
                
                # Check nested structures
                if 'data' in response_json and isinstance(response_json['data'], dict):
                    for key in ['token', 'access_token', 'accessToken', 'jwt']:
                        if key in response_json['data']:
                            print(f"\n✅ TOKEN FOUND IN data.{key}: {response_json['data'][key][:50]}...")
        except:
            print(f"   {response.text[:500]}")
        
        print()
        print("=" * 70)
        
        # Analysis
        print("\n📊 ANALYSIS")
        print("=" * 70)
        
        if response.status_code == 200:
            print("✅ HTTP 200 OK - Login request accepted")
        elif response.status_code == 401:
            print("❌ HTTP 401 Unauthorized - Invalid credentials")
        elif response.status_code == 403:
            print("❌ HTTP 403 Forbidden - Access denied")
        elif response.status_code >= 400:
            print(f"❌ HTTP {response.status_code} - Error occurred")
        
        # Check if we got a token
        token_found = False
        if 'Set-Cookie' in response.headers and 'token=' in response.headers['Set-Cookie']:
            token_found = True
        elif session.cookies and any('token' in c.name.lower() for c in session.cookies):
            token_found = True
        
        try:
            response_json = response.json()
            if isinstance(response_json, dict):
                if any(key in response_json for key in ['token', 'access_token', 'accessToken', 'jwt']):
                    token_found = True
        except:
            pass
        
        if token_found:
            print("✅ Token extraction appears possible")
        else:
            print("❌ No token found in response")
            print("\n🔍 Possible issues:")
            print("   1. Invalid credentials")
            print("   2. Different authentication flow (OAuth, CAPTCHA, etc.)")
            print("   3. Token in different location/format")
            print("   4. Additional headers or cookies required")
        
        print("=" * 70)
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv('K2_EMAIL', 'developer@pixelium.uk')
    password = os.getenv('K2_PASSWORD', 'developer123?')
    
    print("\n🎯 Starting K2Think API Test")
    test_k2think_api_login(email, password)
    print("\n✅ Test complete!")


if __name__ == '__main__':
    main()

