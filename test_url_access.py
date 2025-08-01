#!/usr/bin/env python3

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_url_access():
    """Test if the presigned URL can be accessed"""
    
    # Get URL from command line argument
    if len(sys.argv) < 2:
        print("Usage: python test_url_access.py <URL>")
        return
    
    url = sys.argv[1]
    print(f"Testing URL access: {url[:100]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("Navigating to URL...")
            response = await page.goto(url, wait_until="load", timeout=30000)
            
            if response:
                print(f"✅ Successfully loaded page!")
                print(f"Status: {response.status}")
                print(f"URL: {page.url}")
                
                # Wait a bit to see the page
                await asyncio.sleep(3)
                
                # Take a screenshot
                await page.screenshot(path="url_test_screenshot.png")
                print("📸 Screenshot saved as url_test_screenshot.png")
                
            else:
                print("❌ No response received")
                
        except Exception as e:
            print(f"❌ Error accessing URL: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_url_access())
