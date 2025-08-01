#!/usr/bin/env python3
"""
Test script to verify anti-detection measures and reCAPTCHA handling
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_use.browser.browser import BrowserConfig
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_anti_detection():
    """Test anti-detection measures"""
    
    # Configure browser with anti-detection settings
    browser_config = BrowserConfig(
        headless=True,  # Use headless for testing
        disable_security=False,  # Keep security enabled
        chrome_remote_debugging_port=9222,
    )
    
    browser = CustomBrowser(config=browser_config)
    
    try:
        # Start browser and create context
        context = await browser.new_context()
        page = await context.get_current_page()
        
        # Test 1: Check if webdriver property is hidden
        logger.info("Testing webdriver property hiding...")
        webdriver_result = await page.evaluate("navigator.webdriver")
        logger.info(f"navigator.webdriver: {webdriver_result}")
        
        # Test 2: Check User-Agent
        logger.info("Testing User-Agent...")
        user_agent = await page.evaluate("navigator.userAgent")
        logger.info(f"User-Agent: {user_agent}")
        
        # Test 3: Check plugins
        logger.info("Testing plugins...")
        plugins_length = await page.evaluate("navigator.plugins.length")
        logger.info(f"Plugins length: {plugins_length}")
        
        # Test 4: Check languages
        logger.info("Testing languages...")
        languages = await page.evaluate("navigator.languages")
        logger.info(f"Languages: {languages}")
        
        # Test 5: Try accessing Google (this might trigger reCAPTCHA)
        logger.info("Testing Google access...")
        try:
            await page.goto("https://www.google.com", wait_until="networkidle")
            title = await page.title()
            logger.info(f"Google page title: {title}")
            
            # Check if reCAPTCHA is present
            recaptcha_present = await page.locator("iframe[src*='recaptcha']").count() > 0
            if recaptcha_present:
                logger.warning("reCAPTCHA detected on Google page")
            else:
                logger.info("No reCAPTCHA detected - anti-detection working!")
                
        except Exception as e:
            logger.error(f"Error accessing Google: {e}")
        
        # Test 6: Try DuckDuckGo as alternative
        logger.info("Testing DuckDuckGo as alternative...")
        try:
            await page.goto("https://duckduckgo.com", wait_until="networkidle")
            title = await page.title()
            logger.info(f"DuckDuckGo page title: {title}")
            
            # Try a search
            search_box = page.locator("input[name='q']")
            if await search_box.count() > 0:
                await search_box.fill("test search")
                await search_box.press("Enter")
                await page.wait_for_load_state("networkidle")
                logger.info("DuckDuckGo search successful!")
            
        except Exception as e:
            logger.error(f"Error with DuckDuckGo: {e}")
            
    except Exception as e:
        logger.error(f"Browser test failed: {e}")
    finally:
        await browser.close()


async def main():
    """Main test function"""
    logger.info("Starting anti-detection tests...")
    await test_anti_detection()
    logger.info("Anti-detection tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
