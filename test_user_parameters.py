#!/usr/bin/env python3
"""
Test to verify that user-provided parameters are correctly used
instead of hardcoded defaults.
"""

import asyncio
import logging
from unittest.mock import patch, MagicMock
from src.controller.custom_controller import CustomController
from browser_use.browser.browser import Browser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_user_parameters():
    """Test that user-provided parameters are used correctly"""
    
    logger.info("🧪 Testing User-Provided Parameters")
    
    # User's actual parameters from the feedback
    user_params = {
        "domain_id": "d-xxxxxxxxxxxx",
        "user_profile_name": "default-xxxxxxxx", 
        "space_name": "default",
        "region_name": "us-east-1"
    }
    
    # Mock response
    mock_response = {
        "AuthorizedUrl": "https://d-xxxxxxxxxxxx.studio.us-east-1.sagemaker.aws/jupyter/default/lab"
    }
    
    with patch('boto3.Session') as mock_session:
        # Setup boto3 mock
        mock_client = MagicMock()
        mock_client.create_presigned_domain_url.return_value = mock_response
        mock_session.return_value.client.return_value = mock_client
        
        controller = CustomController()
        browser = Browser()
        browser_context = await browser.new_context()
        
        try:
            # Mock the go_to_url action to avoid actual navigation
            with patch.object(controller.registry, 'execute_action') as mock_execute:
                mock_execute.return_value = "Navigation successful"
                
                # Get the action function
                action_func = controller.registry.registry.actions["navigate_to_sagemaker_presigned_url"].function
                
                # Execute with user's parameters
                result = await action_func(
                    domain_id=user_params["domain_id"],
                    user_profile_name=user_params["user_profile_name"],
                    space_name=user_params["space_name"],
                    browser=browser_context,
                    region_name=user_params["region_name"]
                )
                
                logger.info(f"✅ Action execution result: {result}")
                
                # Verify boto3 session was created with correct region
                mock_session.assert_called_once_with(region_name=user_params["region_name"])
                logger.info(f"✅ Boto3 session created with region: {user_params['region_name']}")
                
                # Verify SageMaker client was called with user's parameters
                expected_call = {
                    'DomainId': user_params["domain_id"],
                    'UserProfileName': user_params["user_profile_name"],
                    'SpaceName': user_params["space_name"]
                }
                
                mock_client.create_presigned_domain_url.assert_called_once_with(**expected_call)
                logger.info("✅ SageMaker client called with user parameters:")
                logger.info(f"   DomainId: {user_params['domain_id']}")
                logger.info(f"   UserProfileName: {user_params['user_profile_name']}")
                logger.info(f"   SpaceName: {user_params['space_name']}")
                
                # Verify navigation was called with generated URL
                mock_execute.assert_called_once_with(
                    "go_to_url",
                    {"url": mock_response["AuthorizedUrl"]},
                    browser=browser_context
                )
                logger.info(f"✅ Navigation called with URL: {mock_response['AuthorizedUrl']}")
                
                return True
                
        finally:
            await browser_context.close()
            await browser.close()

async def test_default_region():
    """Test that default region is used when not specified"""
    
    logger.info("🧪 Testing Default Region Parameter")
    
    user_params = {
        "domain_id": "d-test123",
        "user_profile_name": "test-user",
        "space_name": "test-space"
        # Note: no region_name specified
    }
    
    mock_response = {
        "AuthorizedUrl": "https://d-test123.studio.us-east-1.sagemaker.aws/jupyter/default/lab"
    }
    
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_client.create_presigned_domain_url.return_value = mock_response
        mock_session.return_value.client.return_value = mock_client
        
        controller = CustomController()
        browser = Browser()
        browser_context = await browser.new_context()
        
        try:
            with patch.object(controller.registry, 'execute_action') as mock_execute:
                mock_execute.return_value = "Navigation successful"
                
                action_func = controller.registry.registry.actions["navigate_to_sagemaker_presigned_url"].function
                
                # Execute without region_name (should use default)
                result = await action_func(
                    domain_id=user_params["domain_id"],
                    user_profile_name=user_params["user_profile_name"],
                    space_name=user_params["space_name"],
                    browser=browser_context
                    # region_name not specified - should default to "us-east-1"
                )
                
                # Verify default region was used
                mock_session.assert_called_once_with(region_name="us-east-1")
                logger.info("✅ Default region 'us-east-1' used when not specified")
                
                return True
                
        finally:
            await browser_context.close()
            await browser.close()

async def run_tests():
    """Run all parameter tests"""
    
    logger.info("🚀 Starting User Parameter Tests")
    
    tests = [
        ("User-Provided Parameters", test_user_parameters),
        ("Default Region Parameter", test_default_region),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- Running {test_name} ---")
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! User parameters are correctly handled.")
        logger.info("")
        logger.info("📋 Summary:")
        logger.info("✅ User-provided domain_id, user_profile_name, space_name are used")
        logger.info("✅ User-provided region_name is used")
        logger.info("✅ Default region 'us-east-1' is used when region_name not specified")
        logger.info("✅ No hardcoded values are used - all parameters are dynamic")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)
