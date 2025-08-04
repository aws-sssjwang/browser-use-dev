#!/usr/bin/env python3
"""
Test script for the SageMaker presigned URL navigation action.
This demonstrates how to use the new custom action for initial_actions.
"""

import asyncio
import logging
from src.controller.custom_controller import CustomController
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sagemaker_action():
    """Test the SageMaker presigned URL navigation action"""
    
    # Initialize controller
    controller = CustomController()
    
    # Create a mock browser context for testing
    browser = Browser()
    browser_context = await browser.new_context()
    
    try:
        # Test the action registration
        actions = controller.registry.registry.actions
        if "navigate_to_sagemaker_presigned_url" in actions:
            logger.info("✅ SageMaker navigation action successfully registered")
            
            # Get action details
            action_info = actions["navigate_to_sagemaker_presigned_url"]
            logger.info(f"Action description: {action_info.description}")
            
            # Example of how to use this in initial_actions
            example_initial_actions = [
                {
                    "navigate_to_sagemaker_presigned_url": {
                        "domain_id": "d-9cpchwz1nnno",
                        "user_profile_name": "adam-test-user-1752279282450",
                        "space_name": "adam-space-1752279293076",
                        "region_name": "us-east-1"
                    }
                }
            ]
            
            logger.info("Example initial_actions configuration:")
            logger.info(f"{example_initial_actions}")
            
        else:
            logger.error("❌ SageMaker navigation action not found in registry")
            
    except Exception as e:
        logger.error(f"Error testing SageMaker action: {e}")
        
    finally:
        await browser_context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sagemaker_action())
