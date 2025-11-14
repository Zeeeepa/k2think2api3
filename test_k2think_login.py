#!/usr/bin/env python3
"""
K2Think Token Extraction Debugger with Playwright
Tests the actual login flow and extracts tokens
"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def test_k2think_login(email: str, password: str, headless: bool = True):
    """
    Test K2Think login with Playwright and extract token
    """
    print("=" * 70)
    print("🔍 K2Think Login Debugger with Playwright")
    print("=" * 70)
    print()
    print(f"📧 Email: {email}")
    print(f"🔒 Password: {'*' * len(password)}")
    print(f"🎭 Headless: {headless}")
    print()
    
    async with async_playwright() as p:
        # Launch browser
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to login page
            print("📍 Navigating to https://www.k2think.ai/auth?mode=signin")
            await page.goto('https://www.k2think.ai/auth?mode=signin', wait_until='networkidle', timeout=30000)
            print("✅ Page loaded")
            
            # Take screenshot of login page
            await page.screenshot(path='/tmp/k2think_login_page.png')
            print("📸 Screenshot saved: /tmp/k2think_login_page.png")
            
            # Wait for email input
            print("\n🔍 Looking for email input field...")
            email_selector = 'input[type="email"], input[name="email"], input[id*="email"], input[placeholder*="email" i]'
            await page.wait_for_selector(email_selector, timeout=10000)
            print(f"✅ Found email field: {email_selector}")
            
            # Fill email
            print(f"⌨️  Filling email: {email}")
            await page.fill(email_selector, email)
            
            # Wait for password input
            print("🔍 Looking for password input field...")
            password_selector = 'input[type="password"], input[name="password"], input[id*="password"]'
            await page.wait_for_selector(password_selector, timeout=10000)
            print(f"✅ Found password field: {password_selector}")
            
            # Fill password
            print(f"⌨️  Filling password: {'*' * len(password)}")
            await page.fill(password_selector, password)
            
            # Find and click submit button
            print("🔍 Looking for submit button...")
            button_selector = 'button[type="submit"], button:has-text("Sign in"), button:has-text("Login"), button:has-text("登录")'
            await page.wait_for_selector(button_selector, timeout=10000)
            print("✅ Found submit button")
            
            # Set up network listener to capture API requests
            api_responses = []
            
            async def handle_response(response):
                if '/api/' in response.url:
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers)
                    })
            
            page.on('response', handle_response)
            
            # Click submit
            print("🖱️  Clicking submit button...")
            await page.click(button_selector)
            
            # Wait for navigation or API response
            print("⏳ Waiting for response...")
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass
            
            # Wait a bit more for API calls
            await asyncio.sleep(3)
            
            # Take screenshot after login attempt
            await page.screenshot(path='/tmp/k2think_after_login.png')
            print("📸 Screenshot saved: /tmp/k2think_after_login.png")
            
            # Get current URL
            current_url = page.url
            print(f"\n📍 Current URL: {current_url}")
            
            # Check for cookies
            print("\n🍪 Checking cookies...")
            cookies = await context.cookies()
            token_found = False
            
            for cookie in cookies:
                if 'token' in cookie['name'].lower():
                    print(f"✅ Found token cookie: {cookie['name']}")
                    print(f"   Value: {cookie['value'][:50]}..." if len(cookie['value']) > 50 else f"   Value: {cookie['value']}")
                    token_found = True
            
            if not token_found:
                print("❌ No token cookie found")
                print("\n📋 All cookies:")
                for cookie in cookies:
                    print(f"   • {cookie['name']}: {cookie['value'][:30]}...")
            
            # Check API responses
            print("\n🌐 API Responses captured:")
            for resp in api_responses:
                print(f"   • {resp['url']}")
                print(f"     Status: {resp['status']}")
                if 'set-cookie' in resp['headers']:
                    print(f"     Set-Cookie: {resp['headers']['set-cookie'][:100]}...")
            
            # Check for error messages on page
            print("\n🔍 Checking for error messages...")
            error_selectors = [
                '[class*="error"]',
                '[class*="alert"]',
                'text=Invalid',
                'text=incorrect',
                'text=wrong'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        print(f"⚠️  Possible error: {error_text}")
                except:
                    pass
            
            # Get page content for debugging
            print("\n📄 Page title:", await page.title())
            
            # Extract local storage
            print("\n💾 Checking localStorage...")
            local_storage = await page.evaluate('() => JSON.stringify(localStorage)')
            storage_data = json.loads(local_storage)
            if storage_data:
                print("✅ LocalStorage data found:")
                for key, value in storage_data.items():
                    if 'token' in key.lower():
                        print(f"   • {key}: {value[:50]}..." if len(str(value)) > 50 else f"   • {key}: {value}")
                        token_found = True
            else:
                print("❌ No localStorage data")
            
            # Final summary
            print("\n" + "=" * 70)
            if token_found:
                print("✅ SUCCESS: Token found!")
            else:
                print("❌ FAILURE: No token extracted")
                print("\n🔍 Debugging suggestions:")
                print("   1. Check if login credentials are correct")
                print("   2. Check if K2Think uses different authentication method")
                print("   3. Check if CAPTCHA or additional verification is required")
                print("   4. Review screenshots in /tmp/")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error during login test: {e}")
            import traceback
            traceback.print_exc()
            
            # Take error screenshot
            try:
                await page.screenshot(path='/tmp/k2think_error.png')
                print("📸 Error screenshot saved: /tmp/k2think_error.png")
            except:
                pass
        
        finally:
            await browser.close()
            print("\n🏁 Browser closed")


async def main():
    # Get credentials from environment or use provided ones
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv('K2_EMAIL', 'developer@pixelium.uk')
    password = os.getenv('K2_PASSWORD', 'developer123?')
    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    
    print("\n🎯 Starting K2Think Login Test")
    print("=" * 70)
    
    await test_k2think_login(email, password, headless=headless)
    
    print("\n✅ Test complete!")


if __name__ == '__main__':
    asyncio.run(main())

